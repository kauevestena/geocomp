# SPDX-License-Identifier: GPL-2.0-or-later
"""The PostGIS project store, against a real PostgreSQL with PostGIS (phase P11).

``specs/17-persistence-and-interoperability.md`` section 6, criterion 1: *a
complete project round-trips GeoPackage → PostGIS → GeoPackage with every table
identical* -- plus the P11 exit's other two: migration works on both backends,
and a concurrent modification is detected on save rather than overwritten.

P5 could not build this backend because no environment it ran in had a
PostgreSQL server. These tests need one, and say so rather than pass without
it: set ``GEOCOMP_TEST_POSTGRES`` to a libpq connection string for a database
with the PostGIS extension, and install ``psycopg2``. The ``test`` workflow
runs them against a PostGIS service container. Each test works in a schema of
its own, dropped afterwards, so the database is left as it was found.
"""

from __future__ import annotations

import dataclasses
import math
import os
import uuid

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
    CoordinateSystem,
    DatumDefinition,
    GnssSession,
    HeightType,
    Network,
    Position,
    Project,
    Station,
)
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.solution import Provenance
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.io.store import (
    SCHEMA,
    SCHEMA_VERSION,
    copy_store,
    differences,
    open_postgis_store,
    open_store,
)
from geocomp.io.store.transfer import logical_rows

try:
    import psycopg2
except ImportError:  # pragma: no cover - depends on the environment
    psycopg2 = None

DSN = os.environ.get("GEOCOMP_TEST_POSTGRES", "")

pytestmark = pytest.mark.skipif(
    not DSN or psycopg2 is None,
    reason=(
        "needs a PostgreSQL server with PostGIS: set GEOCOMP_TEST_POSTGRES to a libpq "
        "connection string and install psycopg2"
    ),
)


# -- fixtures ---------------------------------------------------------------------


@pytest.fixture
def schema():
    """A schema of this test's own, and every backup taken of it, dropped afterwards."""
    name = "gc_test_" + uuid.uuid4().hex[:12]
    yield name
    connection = psycopg2.connect(DSN)
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE %s",
            (name + "%",),
        )
        for (found,) in cursor.fetchall():
            cursor.execute(f'DROP SCHEMA "{found}" CASCADE')
    connection.close()


def _open(schema: str, **options):
    return open_postgis_store(DSN, schema, label=f"test {schema}", **options)


def _solve(reference, frame: Frame, solution_id: str, *, crs: str = "EPSG:31982"):
    run = adjust(
        reference.network, AdjustmentOptions(frame=frame, datum=DatumDefinition.CONSTRAINED)
    )
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
    )
    return to_solution(
        run,
        reference.network,
        solution_id=solution_id,
        crs=crs,
        epoch=Epoch.from_decimal_year(2026.5),
        datum=DatumDefinition.CONSTRAINED,
        height_type=HeightType.ORTHOMETRIC,
        observation_results=to_observation_results(run, snooping=snooping),
        global_test=global_test(run.variance_factor_aposteriori, run.degrees_of_freedom),
        provenance=Provenance.now(
            algorithm_id="geocomp:analysis_network_adjust",
            source="test",
            parameters={"frame": frame.value},
            input_ids=("L0", "L1"),
            input_digests={"L0": "abc123"},
        ),
    )


def _local_grid() -> Network:
    """Two stations in a local grid: geometry with the undefined spatial reference."""
    network = Network(id="local-grid", crs="LOCAL")
    for identifier, (east, north) in {"P1": (10.0, 20.0), "P2": (35.5, -4.25)}.items():
        network.add_station(
            Station(
                id=identifier,
                approx_position=Position(
                    values=(
                        Quantity.from_std_dev(east, 0.01, Unit.METRE),
                        Quantity.from_std_dev(north, 0.01, Unit.METRE),
                        Quantity.exact(0.0, Unit.METRE),
                    ),
                    system=CoordinateSystem.PROJECTED,
                    crs="LOCAL",
                    height_type=HeightType.ORTHOMETRIC,
                ),
            )
        )
    return network


@pytest.fixture(scope="module")
def complete():
    """Everything a store holds: three networks, a campaign, a session, settings,
    and solutions -- one superseded by another, one with no redundancy, whose
    global test stores NaN as its statistic."""
    levelling = nets.levelling_loop()
    trilateration = nets.trilateration()
    project = Project(
        id="p11",
        name="P11",
        default_crs="EPSG:31982",
        default_epoch=Epoch.from_decimal_year(2026.5),
        settings={"gnss.elevation_mask": 15.0, "interface.mode": "advanced"},
    )
    project.add_network(levelling.network)
    project.add_network(trilateration.network)
    project.add_network(_local_grid())
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
            nav_files=("brdc0010.25n",),
        )
    )
    level = _solve(levelling, Frame.HEIGHT_1D, "level-1")
    plane = _solve(trilateration, Frame.PLANE_2D, "plane-1")
    later = dataclasses.replace(plane, id="plane-2")
    exact = dataclasses.replace(
        level,
        id="level-exact",
        statistics=dataclasses.replace(
            level.statistics, degrees_of_freedom=0, global_test=global_test(1.0, 0)
        ),
    )
    assert math.isnan(exact.statistics.global_test.statistic)
    return project, [level, plane, later, exact]


def _fill(store, complete) -> None:
    project, solutions = complete
    store.write(project)
    for solution in solutions:
        store.write_solution(solution)
    store.supersede_solution("plane-1", "plane-2")


# -- the store itself ---------------------------------------------------------------


class TestTheSchema:
    def test_every_table_is_created_and_the_store_starts_empty(self, schema):
        with _open(schema, create=True) as store:
            assert {entry.name for entry in SCHEMA} <= set(store.tables())
            assert store.schema_version_or_none() is None

    def test_text_sorts_byte_by_byte_as_sqlite_does(self, schema):
        """``COLLATE "C"`` on every text column: a project must not read back in
        a different order because of the database's locale."""
        with _open(schema, create=True) as store:
            rows = store._execute(
                "SELECT DISTINCT collation_name FROM information_schema.columns "
                "WHERE table_schema = ? AND data_type = 'text'",
                (schema,),
            ).fetchall()
        assert {row[0] for row in rows} == {"C"}

    def test_geometry_is_postgis_geometry(self, schema):
        with _open(schema, create=True) as store:
            rows = store._execute(
                "SELECT f_table_name, type FROM geometry_columns WHERE f_table_schema = ?",
                (schema,),
            ).fetchall()
        kinds = {row[0]: row[1] for row in rows}
        assert kinds["gc_station"] == "POINT"
        assert kinds["gc_observation"] == "LINESTRING"

    def test_a_missing_schema_is_refused_unless_creating(self, schema):
        with pytest.raises(DataError) as caught:
            _open(schema)
        assert caught.value.code == "data.project_store_not_found"

    def test_a_foreign_schema_is_refused_by_name(self, schema):
        connection = psycopg2.connect(DSN)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA "{schema}"')
            cursor.execute(f'CREATE TABLE "{schema}"."something_else" (id int)')
        connection.close()
        with pytest.raises(DataError) as caught:
            _open(schema)
        assert caught.value.code == "data.project_store_not_geocomp"

    def test_the_label_names_the_store_and_the_connection_string_does_not(self, schema):
        """NFR-010: the connection string may hold a password, so it is never
        what a message calls the store."""
        with _open(schema, create=True) as store:
            assert store.location == f"test {schema}"
            assert DSN not in store.location


class TestARoundTrip:
    def test_the_project_comes_back_in_its_order(self, schema, complete):
        project, _ = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
        with _open(schema) as store:
            back = store.read()
        assert list(back.networks) == sorted(project.networks)
        for identifier, network in project.networks.items():
            assert list(back.networks[identifier].stations) == list(network.stations)
            assert list(back.networks[identifier].observations) == list(network.observations)
        assert back.settings == project.settings
        assert back.campaigns["c1"].crew == "KV"
        assert back.gnss_sessions["g1"].nav_files == ("brdc0010.25n",)

    def test_every_observation_value_is_exact(self, schema, complete):
        project, _ = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
            back = store.read()
        for identifier, network in project.networks.items():
            for key, observation in network.observations.items():
                again = back.networks[identifier].observations[key]
                assert [q.to_dict() for q in again.values] == [
                    q.to_dict() for q in observation.values
                ]

    def test_the_covariance_is_bit_identical(self, schema, complete):
        """Criterion 9 on PostGIS: a covariance stored and reloaded is the same bytes."""
        _, solutions = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
            back = {solution.id: solution for solution in store.read_solutions()}
        for solution in solutions:
            if solution.parameter_covariance is None:
                continue
            again = back[solution.id].parameter_covariance
            assert again.matrix.tobytes() == np.asarray(
                solution.parameter_covariance.matrix, dtype=float
            ).tobytes()

    def test_a_global_test_with_no_redundancy_survives(self, schema, complete):
        """NaN is a legitimate statistic here, and ``jsonb`` cannot hold it --
        which is why JSON is text in PostgreSQL too."""
        with _open(schema, create=True) as store:
            _fill(store, complete)
            back = {solution.id: solution for solution in store.read_solutions()}
        assert math.isnan(back["level-exact"].statistics.global_test.statistic)

    def test_superseding_is_kept(self, schema, complete):
        with _open(schema, create=True) as store:
            _fill(store, complete)
            back = {solution.id: solution for solution in store.read_solutions()}
        assert back["plane-1"].superseded_by == "plane-2"


class TestNothingThatProducedAResultIsDeleted:
    def test_deleting_an_observation_a_solution_used_is_refused(self, schema, complete):
        """Criterion 3 (FR-135) on PostGIS."""
        _, solutions = complete
        used = solutions[0].observation_results[0].observation_id
        with _open(schema, create=True) as store:
            _fill(store, complete)
            with pytest.raises(ValidationError) as caught:
                store.delete_observation(used)
            assert caught.value.code == "validation.observation_has_results"
            assert store.solutions_using(used)


class TestConcurrentSaves:
    """The P11 exit: a concurrent modification is detected on save rather than overwritten."""

    def test_a_save_after_someone_elses_is_refused(self, schema, complete):
        _, solutions = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
        mine, theirs = _open(schema), _open(schema)
        try:
            mine.read()
            theirs.read()
            theirs.delete_solution("level-exact")
            with pytest.raises(DataError) as caught:
                mine.write_solution(solutions[0])
            assert caught.value.code == "data.store_modified_concurrently"
        finally:
            mine.close()
            theirs.close()
        with _open(schema) as store:
            assert "level-exact" not in {s.id for s in store.read_solutions()}

    def test_reading_again_accepts_what_was_saved(self, schema, complete):
        _, solutions = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
        mine, theirs = _open(schema), _open(schema)
        try:
            theirs.delete_solution("level-exact")
            mine.read()
            mine.write_solution(solutions[0])
            assert mine.revision == theirs.revision + 1
        finally:
            mine.close()
            theirs.close()

    def test_every_save_advances_the_revision(self, schema, complete):
        _, solutions = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
            before = store.revision
            store.write_solution(solutions[0])
            assert store.revision == before + 1
            assert store._stored_revision() == store.revision


class TestVersioning:
    def test_a_newer_schema_is_refused(self, schema, complete):
        with _open(schema, create=True) as store:
            _fill(store, complete)
            store._execute(f'UPDATE "gc_project" SET schema_version = {SCHEMA_VERSION + 1}')
        with pytest.raises(DataError) as caught:
            _open(schema)
        assert caught.value.code == "data.store_schema_too_new"

    def test_an_older_store_is_migrated_after_a_backup_schema(self, schema, complete):
        """The P11 exit: migration works on both backends. No PostGIS store
        older than schema 4 was ever written, so one is made by taking schema
        4's additions back out of a current store."""
        project, _ = complete
        with _open(schema, create=True) as store:
            _fill(store, complete)
            store._execute('ALTER TABLE "gc_project" DROP COLUMN "revision"')
            store._execute('ALTER TABLE "gc_network_member" DROP COLUMN "ordinal"')
            store._execute('ALTER TABLE "gc_provenance" DROP COLUMN "strategies"')
            store._execute('UPDATE "gc_project" SET schema_version = 3')

        with pytest.raises(DataError) as caught:
            _open(schema)
        assert caught.value.code == "data.store_schema_older"

        with _open(schema, migrate_older=True) as store:
            report = store.migration
            back = store.read()
            backup = report.backup
            kept = store._execute(f'SELECT schema_version FROM "{backup}"."gc_project"').fetchone()
            revision = store._stored_revision()
        assert report.steps == [
            "4: gc_project gains revision; gc_network_member gains ordinal",
            "5: gc_provenance gains strategies",
        ]
        assert backup.startswith(schema + "_backup_")
        assert kept[0] == 3
        assert revision == 0
        assert set(back.networks) == set(project.networks)


# -- mode switching ------------------------------------------------------------------


class TestModeSwitching:
    """``specs/17`` section 4 and acceptance criterion 1."""

    def test_geopackage_to_postgis_to_geopackage_loses_nothing(self, schema, complete, tmp_path):
        first = tmp_path / "first.gpkg"
        second = tmp_path / "second.gpkg"
        with open_store(first, create=True) as source:
            _fill(source, complete)
        with open_store(first) as source, _open(schema, create=True) as database:
            out = copy_store(source, database)
        with _open(schema) as database, open_store(second, create=True) as target:
            back = copy_store(database, target)
        with open_store(first) as a, open_store(second) as b:
            final = differences(a, b)
            rows = logical_rows(a)

        assert out.identical and back.identical and not final
        assert out.total == back.total == sum(len(v) for v in rows.values())
        assert all(rows[name] for name in ("gc_station", "gc_observation", "gc_solution"))

    def test_geometry_crosses_with_its_reference(self, schema, complete, tmp_path):
        """EPSG:31982 stays 31982; the undefined reference is -1 in a GeoPackage
        and 0 in PostGIS, and comes back as -1."""
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as source:
            _fill(source, complete)
        with open_store(path) as source, _open(schema, create=True) as database:
            copy_store(source, database)
            srids = {
                row[0]: row[1]
                for row in database._execute(
                    'SELECT "id", ST_SRID("geom") FROM "gc_station" WHERE "geom" IS NOT NULL'
                ).fetchall()
            }
            stations = {
                row["id"]: row["geom"]
                for row in logical_rows(database)["gc_station"]
                if row["geom"] is not None
            }
        assert srids["P1"] == 0 and srids["B"] == 31982
        assert stations["P1"][0] == -1 and stations["B"][0] == 31982

    def test_the_project_reads_the_same_from_either(self, schema, complete, tmp_path):
        """Transparent, the specification's word: what a consumer reads does not
        depend on which store it came from."""
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as source:
            _fill(source, complete)
        with open_store(path) as source, _open(schema, create=True) as database:
            copy_store(source, database)
            from_file, from_database = source.read(), database.read()
            solutions_file = [s.to_dict() for s in source.read_solutions()]
            solutions_database = [s.to_dict() for s in database.read_solutions()]
        assert list(from_file.networks) == list(from_database.networks)
        for identifier, network in from_file.networks.items():
            assert network.to_dict() == from_database.networks[identifier].to_dict()
        assert _comparable(solutions_file) == _comparable(solutions_database)

    def test_a_target_that_already_holds_a_project_is_refused(self, schema, complete, tmp_path):
        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as source:
            _fill(source, complete)
        with open_store(path) as source, _open(schema, create=True) as database:
            copy_store(source, database)
            with pytest.raises(DataError) as caught:
                copy_store(source, database)
        assert caught.value.code == "data.store_copy_target_not_empty"


def _comparable(value):
    """Documents with NaN made comparable: NaN != NaN, and these are equal."""
    if isinstance(value, float) and math.isnan(value):
        return "NaN"
    if isinstance(value, dict):
        return {key: _comparable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_comparable(item) for item in value]
    return value


class TestACancelledExport:
    """``specs/17`` criterion 6, on the backend where a copy creates its target."""

    class _CancelAfter:
        def __init__(self, n: int):
            self.asked, self.n = 0, n

        def is_cancelled(self) -> bool:
            self.asked += 1
            return self.asked >= self.n

    @staticmethod
    def _exists(schema: str) -> bool:
        connection = psycopg2.connect(DSN)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (schema,)
                )
                return cursor.fetchone() is not None
        finally:
            connection.close()

    def test_the_rows_roll_back_and_the_schema_it_made_goes(self, schema, complete, tmp_path):
        from geocomp.core.cancellation import Cancelled

        path = tmp_path / "p.gpkg"
        with open_store(path, create=True) as source:
            _fill(source, complete)
        with open_store(path) as source, _open(schema, create=True) as database:
            assert database.created_schema
            with pytest.raises(Cancelled):
                copy_store(source, database, self._CancelAfter(3))
            assert database.schema_version_or_none() is None
            database.remove_what_was_created()
        assert not self._exists(schema)

    def test_a_schema_that_was_there_keeps_existing(self, schema):
        """Only what this store created is taken away."""
        connection = psycopg2.connect(DSN)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA "{schema}"')
        connection.close()
        with _open(schema, create=True) as database:
            assert not database.created_schema and database.created_tables
            database.remove_what_was_created()
            assert database.tables() == []
        assert self._exists(schema)
