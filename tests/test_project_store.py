# SPDX-License-Identifier: GPL-2.0-or-later
"""The project store (FR-130, FR-133, FR-134, FR-135).

``specs/17-persistence-and-interoperability.md`` section 6 lists nine acceptance
criteria; the ones that do not need a PostgreSQL server are here, and they run
in the fast tier because the store is built on the standard library's ``sqlite3``
rather than on GDAL.

The heaviest of them is criterion 9: **covariance stored and reloaded is
bit-identical**. A store that rounds a covariance is a store that silently
changes every statistic computed from it afterwards, and the failure is
invisible -- the numbers still look like covariances.
"""

from __future__ import annotations

import sqlite3
import struct

import numpy as np
import pytest

import tests.networks as nets
from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models import (
    Campaign,
    DatumDefinition,
    GnssSession,
    HeightType,
    Network,
    Project,
)
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.solution import (
    ObservationResult,
    Provenance,
    Solution,
    SolutionKind,
)
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.io.store import SCHEMA, SCHEMA_VERSION, open_store, table_names
from geocomp.io.store.geopackage import APPLICATION_ID
from geocomp.io.store.migrations import (
    MIGRATIONS,
    backup_path,
    check_version,
    migrate,
    register,
)
from geocomp.io.store.schema import ColumnKind, ddl, quoted


@pytest.fixture
def reference():
    """RD-03's levelling loop, adjusted, with its solution."""
    network = nets.levelling_loop()
    run = adjust(
        network.network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED),
    )
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
    )
    solution = to_solution(
        run,
        network.network,
        solution_id="s1",
        crs="EPSG:31982",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.CONSTRAINED,
        height_type=HeightType.ORTHOMETRIC,
        observation_results=to_observation_results(run, snooping=snooping),
        global_test=global_test(run.variance_factor_aposteriori, run.degrees_of_freedom),
        provenance=Provenance.now(
            algorithm_id="geocomp:analysis_network_adjust",
            source="test",
            parameters={"frame": "height_1d"},
            input_ids=("L0", "L1"),
            input_digests={"L0": "abc123"},
        ),
    )
    project = Project(id="rd03", name="RD-03", default_crs="EPSG:31982")
    project.add_network(network.network)
    return project, solution, network.network


@pytest.fixture
def stored(tmp_path, reference):
    project, solution, network = reference
    path = tmp_path / "project.gpkg"
    with open_store(path, create=True) as store:
        store.write(project)
        store.write_solution(solution)
    return path, project, solution, network


class TestItIsAGeoPackage:
    def test_the_file_carries_the_gpkg_application_id(self, stored):
        path, *_ = stored
        with open(path, "rb") as handle:
            header = handle.read(72)
        assert struct.unpack(">I", header[68:72])[0] == APPLICATION_ID

    def test_the_required_metadata_tables_exist(self, stored):
        path, *_ = stored
        with open_store(path) as store:
            names = set(store.tables())
        assert {"gpkg_spatial_ref_sys", "gpkg_contents", "gpkg_geometry_columns"} <= names

    def test_every_schema_table_is_announced_in_gpkg_contents(self, stored):
        """A table QGIS cannot see is a table that might as well not be there."""
        path, *_ = stored
        with open_store(path) as store:
            announced = {
                row[0]
                for row in store.connection.execute(
                    "SELECT table_name FROM gpkg_contents"
                ).fetchall()
            }
        assert set(table_names()) <= announced

    def test_the_feature_tables_have_geometry_registered(self, stored):
        path, *_ = stored
        with open_store(path) as store:
            rows = dict(
                store.connection.execute(
                    "SELECT table_name, geometry_type_name FROM gpkg_geometry_columns"
                ).fetchall()
            )
        assert rows["gc_station"] == "POINT"
        assert rows["gc_observation"] == "LINESTRING"

    def test_stations_and_observations_are_drawn(self, stored):
        """Geometry is derived from the numbers and exists for display."""
        path, *_ = stored
        with open_store(path) as store:
            drawn = store.connection.execute(
                'SELECT COUNT(*) FROM "gc_station" WHERE geom IS NOT NULL'
            ).fetchone()[0]
        assert drawn > 0

    def test_a_geometry_blob_starts_with_the_gpkg_magic(self, stored):
        path, *_ = stored
        with open_store(path) as store:
            blob = store.connection.execute(
                'SELECT geom FROM "gc_station" WHERE geom IS NOT NULL LIMIT 1'
            ).fetchone()[0]
        assert blob[:2] == b"GP"


class TestARoundTrip:
    def test_the_project_comes_back(self, stored):
        path, project, _solution, _network = stored
        with open_store(path) as store:
            back = store.read()
        assert back.id == project.id
        assert back.name == project.name
        assert back.default_crs == project.default_crs
        assert back.schema_version == SCHEMA_VERSION

    def test_every_station_and_observation_comes_back(self, stored):
        path, _project, _solution, network = stored
        with open_store(path) as store:
            back = store.read().networks[network.id]
        assert back.station_ids() == network.station_ids()
        assert set(back.observations) == set(network.observations)

    def test_an_observation_value_is_exact(self, stored):
        """Not "close": a measurement that changed in storage is a different
        measurement."""
        path, _project, _solution, network = stored
        with open_store(path) as store:
            back = store.read().networks[network.id]
        for identifier, observation in network.observations.items():
            for original, restored in zip(
                observation.values, back.observations[identifier].values, strict=True
            ):
                assert restored.value == original.value
                assert restored.variance == original.variance
                assert restored.unit is original.unit

    def test_a_constraint_survives(self, stored):
        path, _project, _solution, network = stored
        with open_store(path) as store:
            back = store.read().networks[network.id]
        for identifier, station in network.stations.items():
            assert back.stations[identifier].constraint == station.constraint

    def test_the_network_validates_after_reloading(self, stored):
        path, _project, _solution, network = stored
        with open_store(path) as store:
            assert store.read().networks[network.id].validate() == []

    def test_campaigns_and_sessions_round_trip(self, tmp_path):
        project = Project(id="p")
        project.add_campaign(
            Campaign(id="c1", name="October", epoch=Epoch.from_decimal_year(2026.75), crew="KV")
        )
        project.add_gnss_session(
            GnssSession(
                id="g1",
                station_id="A",
                receiver="Trimble",
                antenna_height=Quantity.from_std_dev(1.532, 0.002, Unit.METRE),
                antenna_height_method="slant",
            )
        )
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as store:
            store.write(project)
        with open_store(path) as store:
            back = store.read()
        assert back.campaigns["c1"].crew == "KV"
        assert back.campaigns["c1"].epoch.decimal_year == pytest.approx(2026.75)
        assert back.gnss_sessions["g1"].antenna_height.value == pytest.approx(1.532)
        assert back.gnss_sessions["g1"].antenna_height_method == "slant"

    def test_settings_round_trip_with_their_types(self, tmp_path):
        project = Project(id="p", settings={"level.weighting": "length", "n": 3, "on": True})
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as store:
            store.write(project)
        with open_store(path) as store:
            assert store.read().settings == project.settings

    def test_writing_twice_replaces_rather_than_accumulates(self, stored):
        path, project, _solution, network = stored
        with open_store(path) as store:
            store.write(project)
            back = store.read().networks[network.id]
        assert len(back.observations) == len(network.observations)


class TestTheSolution:
    def test_it_comes_back_whole(self, stored):
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert back.id == solution.id
        assert back.kind is solution.kind
        assert back.datum_definition is solution.datum_definition
        assert len(back.adjusted_stations) == len(solution.adjusted_stations)
        assert len(back.observation_results) == len(solution.observation_results)

    def test_the_covariance_is_bit_identical(self, stored):
        """specs/17 acceptance criterion 9, and the reason the matrix is stored
        as big-endian float64 rather than as text."""
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]

        assert np.array_equal(
            back.parameter_covariance.matrix, solution.parameter_covariance.matrix
        )
        original = {s.station_id: s for s in solution.adjusted_stations}
        for station in back.adjusted_stations:
            expected = original[station.station_id].covariance
            if expected is not None:
                assert np.array_equal(station.covariance.matrix, expected.matrix)
                assert station.covariance.labels == expected.labels
                assert station.covariance.units == expected.units

    def test_the_statistics_come_back(self, stored):
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert back.statistics.degrees_of_freedom == solution.statistics.degrees_of_freedom
        assert back.statistics.n_observations == solution.statistics.n_observations
        assert back.statistics.global_test.passed == solution.statistics.global_test.passed

    def test_every_design_matrix_row_survives(self, tmp_path):
        """One result per *row*, and a GNSS baseline is three rows under one
        observation id. Keying the table on the observation would have kept the
        last of the three and lost two silently -- which the first draft did."""
        from geocomp.core.models import Observation, ObservationType, Station

        network = Network(id="n", crs="EPSG:4326")
        for name in ("A", "B"):
            network.add_station(Station(id=name))
        network.add_observation(
            Observation(
                id="B1",
                type=ObservationType.GNSS_BASELINE,
                stations=("A", "B"),
                values=tuple(
                    Quantity.from_std_dev(value, 0.002, Unit.METRE)
                    for value in (100.0, 200.0, 300.0)
                ),
                cluster_id="c1",
            )
        )
        from geocomp.core.models import Cluster, ClusterKind
        from geocomp.core.uncertainty import Covariance

        network.add_cluster(
            Cluster(
                id="c1",
                kind=ClusterKind.GNSS_BASELINE,
                observation_ids=("B1",),
                covariance=Covariance(
                    matrix=np.eye(1) * 4e-6, labels=("B1",), units=(Unit.METRE,)
                ),
            )
        )
        project = Project(id="p")
        project.add_network(network)
        solution = Solution(
            id="s",
            network_id="n",
            kind=SolutionKind.ADJUSTMENT,
            crs="EPSG:4326",
            epoch=Epoch.from_decimal_year(2026.0),
            observation_results=tuple(
                ObservationResult(observation_id="B1", residual=value)
                for value in (0.001, 0.002, 0.003)
            ),
        )
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as store:
            store.write(project)
            store.write_solution(solution)
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert [result.residual for result in back.observation_results] == [
            0.001,
            0.002,
            0.003,
        ]

    def test_a_solution_for_an_unknown_network_is_refused(self, tmp_path):
        """The reference is the store's, not a check somebody wrote."""
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as store:
            store.write(Project(id="p"))
            with pytest.raises(sqlite3.IntegrityError):
                store.write_solution(
                    Solution(
                        id="s",
                        network_id="nowhere",
                        kind=SolutionKind.ADJUSTMENT,
                        crs="EPSG:4326",
                        epoch=Epoch.from_decimal_year(2026.0),
                    )
                )


class TestProvenance:
    def test_it_is_stored_and_returned(self, stored):
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert back.provenance is not None
        assert back.provenance.algorithm_id == solution.provenance.algorithm_id
        assert back.provenance.parameters == solution.provenance.parameters
        assert back.provenance.geocomp_version == solution.provenance.geocomp_version

    def test_the_input_digests_survive(self, stored):
        """FR-134: provenance references its inputs by id *and* content digest,
        which is what makes "reproduce it" checkable rather than aspirational."""
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert back.provenance.input_ids == solution.provenance.input_ids
        assert back.provenance.input_digests == solution.provenance.input_digests

    def test_the_created_instant_is_exact(self, stored):
        """A provenance record whose timestamp shifted is not provenance."""
        path, _project, solution, _network = stored
        with open_store(path) as store:
            back = store.read_solutions()[0]
        assert back.provenance.created == solution.provenance.created


class TestNothingThatProducedAResultIsDeleted:
    def test_deleting_an_observation_a_solution_used_is_refused(self, stored):
        """specs/17 acceptance criterion 3, FR-135."""
        path, _project, _solution, network = stored
        target = sorted(network.observations)[0]
        with open_store(path) as store:
            with pytest.raises(ValidationError) as caught:
                store.delete_observation(target)
            assert caught.value.code == "validation.observation_has_results"
            assert store.solutions_using(target) == ["s1"]

    def test_the_refusal_names_the_solutions(self, stored):
        path, _project, _solution, network = stored
        target = sorted(network.observations)[0]
        with open_store(path) as store:
            with pytest.raises(ValidationError) as caught:
                store.delete_observation(target)
        assert "s1" in str(caught.value)

    def test_deleting_a_solution_keeps_the_observations(self, stored):
        path, _project, _solution, network = stored
        with open_store(path) as store:
            store.delete_solution("s1")
            assert store.read_solutions() == []
            back = store.read().networks[network.id]
        assert len(back.observations) == len(network.observations)
        assert len(back.stations) == len(network.stations)

    def test_an_observation_no_solution_used_can_go(self, stored):
        path, _project, _solution, network = stored
        target = sorted(network.observations)[0]
        with open_store(path) as store:
            store.delete_solution("s1")
            store.delete_observation(target)
            back = store.read().networks[network.id]
        assert target not in back.observations
        assert len(back.observations) == len(network.observations) - 1

    def test_superseding_keeps_both(self, stored):
        path, _project, solution, _network = stored
        with open_store(path) as store:
            store.write_solution(
                Solution(
                    id="s2",
                    network_id=solution.network_id,
                    kind=SolutionKind.ADJUSTMENT,
                    crs=solution.crs,
                    epoch=Epoch.from_decimal_year(2027.0),
                )
            )
            store.supersede_solution("s1", "s2")
            found = {entry.id: entry for entry in store.read_solutions()}
        assert found["s1"].superseded_by == "s2"
        assert found["s1"].is_superseded
        assert found["s2"].superseded_by is None

    def test_superseding_an_unknown_solution_is_refused(self, stored):
        path, *_ = stored
        with open_store(path) as store, pytest.raises(ValidationError) as caught:
            store.supersede_solution("s1", "nowhere")
        assert caught.value.code == "validation.unknown_solution"

    def test_a_solution_cannot_supersede_itself(self, stored):
        path, *_ = stored
        with open_store(path) as store, pytest.raises(ValidationError) as caught:
            store.supersede_solution("s1", "s1")
        assert caught.value.code == "validation.solution_supersedes_itself"


class TestVersioning:
    def test_the_version_is_recorded(self, stored):
        path, *_ = stored
        with open_store(path) as store:
            assert store.schema_version == SCHEMA_VERSION

    def test_a_newer_schema_is_refused(self, stored):
        """specs/17 acceptance criterion 2, FR-133. Reading a schema you do not
        understand silently corrupts it on the next save."""
        path, *_ = stored
        connection = sqlite3.connect(path)
        connection.execute('UPDATE "gc_project" SET schema_version = ?', (SCHEMA_VERSION + 1,))
        connection.commit()
        connection.close()

        with pytest.raises(DataError) as caught:
            open_store(path)
        assert caught.value.code == "data.store_schema_too_new"
        assert str(SCHEMA_VERSION) in str(caught.value)

    def test_an_older_schema_is_not_migrated_unasked(self, stored):
        """Migrating rewrites the user's file, which is their decision."""
        path, *_ = stored
        connection = sqlite3.connect(path)
        connection.execute('UPDATE "gc_project" SET schema_version = 0')
        connection.commit()
        connection.close()
        with pytest.raises(DataError) as caught:
            open_store(path)
        assert caught.value.code == "data.store_schema_invalid"

    def test_check_version_accepts_the_current_one(self):
        check_version(SCHEMA_VERSION)

    def test_the_backup_sits_beside_the_original(self, tmp_path):
        """Not in a temporary directory: a backup the user cannot find when they
        need it is not a backup."""
        target = backup_path(tmp_path / "project.gpkg")
        assert target.parent == tmp_path
        assert target.suffix == ".gpkg"
        assert "backup-" in target.name

    def test_the_migration_chain_starts_empty_and_says_so(self):
        """Version 1 is the first released schema, so there is nothing to
        migrate *to* it. An invented migration from a version that never
        existed is a step that has never run against real data."""
        assert MIGRATIONS == {}
        assert SCHEMA_VERSION == 1

    def test_the_machinery_runs_a_registered_migration(self, stored, monkeypatch):
        """The chain is empty today, so the machinery is exercised with a
        migration registered for the test. Dead code that has never run is not
        a migration path."""
        path, *_ = stored
        applied: list[str] = []

        monkeypatch.setattr("geocomp.io.store.migrations.SCHEMA_VERSION", 2)
        monkeypatch.setitem(
            MIGRATIONS,
            2,
            ("adds a column nobody needs", lambda connection: applied.append("ran")),
        )

        connection = sqlite3.connect(path)
        report = migrate(connection, path, found=1)
        connection.close()

        assert applied == ["ran"]
        assert report.migrated
        assert report.steps == ["2: adds a column nobody needs"]
        assert report.backup is not None and report.backup.is_file()

    def test_a_gap_in_the_chain_is_refused(self, stored, monkeypatch):
        path, *_ = stored
        monkeypatch.setattr("geocomp.io.store.migrations.SCHEMA_VERSION", 3)
        connection = sqlite3.connect(path)
        with pytest.raises(ValidationError) as caught:
            migrate(connection, path, found=1)
        connection.close()
        assert caught.value.code == "validation.store_migration_missing"

    def test_registering_beyond_the_schema_version_is_refused(self):
        """A migration to a version the schema does not declare would run and
        then be undone by the next open."""
        with pytest.raises(ValueError):
            register(SCHEMA_VERSION + 5, "premature")(lambda connection: None)


class TestOpening:
    def test_a_missing_file_is_refused_unless_creating(self, tmp_path):
        with pytest.raises(DataError) as caught:
            open_store(tmp_path / "absent.gpkg")
        assert caught.value.code == "data.project_store_not_found"

    def test_a_foreign_database_is_refused_by_name(self, tmp_path):
        path = tmp_path / "other.gpkg"
        connection = sqlite3.connect(path)
        connection.execute("CREATE TABLE something (id TEXT)")
        connection.commit()
        connection.close()
        with pytest.raises(DataError) as caught:
            open_store(path)
        assert caught.value.code == "data.project_store_not_geocomp"

    def test_creating_twice_opens_rather_than_overwrites(self, stored):
        """The one way to lose a project would be a create that truncated."""
        path, _project, _solution, network = stored
        with open_store(path, create=True) as store:
            assert len(store.read().networks[network.id].observations) == len(
                network.observations
            )

    def test_an_empty_store_reports_itself(self, tmp_path):
        path = tmp_path / "empty.gpkg"
        with open_store(path, create=True) as store, pytest.raises(DataError) as caught:
            store.read()
        assert caught.value.code == "data.project_store_empty"


class TestTheSchemaIsDeclaredOnce:
    def test_every_table_creates_in_sqlite(self):
        """Reserved words are the failure this catches: ``values`` and ``end``
        are the natural names for an observation's components and a session's
        end, and both are SQL keywords."""
        connection = sqlite3.connect(":memory:")
        for entry in SCHEMA:
            connection.execute(ddl(entry))
        connection.close()

    def test_every_reference_resolves(self):
        names = set(table_names())
        for entry in SCHEMA:
            for column in entry.columns:
                if column.references is None:
                    continue
                target, target_column = column.references.split(".", 1)
                assert target in names, f"{entry.name}.{column.name} -> {target}"
                from geocomp.io.store import table as lookup

                lookup(target).column(target_column)

    def test_the_postgres_dialect_is_generated_too(self):
        """ADR-0006: one schema definition drives both stores. The PostGIS
        backend is not built and this does not claim it is -- it asserts only
        that the mapping exists, so the two cannot drift before it arrives."""
        for entry in SCHEMA:
            statement = ddl(entry, "postgres")
            assert "double precision" in statement or "text" in statement
            assert "REAL" not in statement

    def test_identifiers_are_quoted(self):
        assert quoted("values") == '"values"'
        assert 'CREATE TABLE "gc_observation"' in ddl(SCHEMA[8])

    def test_covariance_is_a_blob_not_a_number_column(self):
        """Rule 2 of specs/17 section 2: a matrix, never flattened to standard
        deviations and never rounded through text."""
        from geocomp.io.store import table as lookup

        assert lookup("gc_cluster").column("matrix").kind is ColumnKind.BLOB

    def test_results_restrict_deletion_of_their_inputs(self):
        """FR-135 as a foreign key rather than as a habit."""
        from geocomp.io.store import table as lookup

        column = lookup("gc_observation_result").column("observation_id")
        assert column.references == "gc_observation.id"
        assert column.restrict
