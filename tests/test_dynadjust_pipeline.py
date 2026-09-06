# SPDX-License-Identifier: GPL-2.0-or-later
"""The DynAdjust pipeline: which stages run, and driving a real engine.

Two tiers in one file, deliberately kept together because they are two halves
of one claim.

**Tier 1** is the plan: which programs a job runs, in what order, and why. That
is a decision GeoComp makes and can be checked without any engine, and it is
where the interesting reasoning lives -- a transformation that runs when the
frames match, or one that does not run when they differ, is a defect the engine
would never reveal because both produce a plausible answer.

**Tier 4** is the run: that DynAdjust accepts the files GeoComp writes and that
the pipeline drives it to a solution. Only a real engine can show that, and it
is marked ``engines`` and skipped without one.
"""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.position import CoordinateSystem, HeightType, Position
from geocomp.core.models.station import Station
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.engine import (
    DynAdjustEngine,
    DynAdjustJob,
    dynadjust_epoch,
    parse_version,
    plan,
)
from geocomp.engines.dynadjust.read_dynaml import read_dynaml
from geocomp.engines.dynadjust.solution import read_solution

from .conftest import requires_dynadjust

DATA = Path(__file__).parent / "data" / "dynadjust"
EPOCH_2020 = Epoch.from_datetime(datetime(2020, 1, 1, tzinfo=UTC), label="01.01.2020")
EPOCH_2026 = Epoch.from_datetime(datetime(2026, 1, 1, tzinfo=UTC), label="01.01.2026")


@pytest.fixture
def network():
    read = read_dynaml(DATA / "sample-stn.xml", DATA / "sample-msr.xml").network
    read.epoch = EPOCH_2020
    return read


def stage(job: DynAdjustJob, program: str):
    return next(item for item in plan(job) if item.program == program)


class TestTheJob:
    def test_a_job_without_a_frame_or_epoch_is_refused(self, network) -> None:
        """FR-105, and refused at construction rather than half way through
        writing the input files."""
        network.crs = ""
        network.epoch = None
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustJob(network=network)
        assert excinfo.value.code == "validation.dynadjust_job_frame_or_epoch_missing"

    def test_the_job_falls_back_to_the_networks_own_frame(self, network) -> None:
        job = DynAdjustJob(network=network)
        assert job.frame == network.crs
        assert job.epoch is EPOCH_2020

    def test_an_impossible_confidence_is_refused(self, network) -> None:
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustJob(network=network, confidence=1.0)
        assert excinfo.value.code == "validation.dynadjust_confidence_out_of_range"


class TestThePlan:
    def test_every_stage_appears_whether_it_runs_or_not(self, network) -> None:
        """A plan that listed only what ran could not distinguish a
        transformation that was unnecessary from one that was forgotten."""
        programs = [item.program for item in plan(DynAdjustJob(network=network))]
        assert programs == ["dnaimport", "dnareftran", "dnageoid", "dnasegment", "dnaadjust"]
        assert all(item.reason for item in plan(DynAdjustJob(network=network)))

    def test_import_and_adjust_always_run(self, network) -> None:
        planned = plan(DynAdjustJob(network=network))
        assert {item.program for item in planned if item.included} >= {"dnaimport", "dnaadjust"}

    def test_no_transformation_when_the_frame_and_epoch_match(self, network) -> None:
        job = DynAdjustJob(network=network, target_frame=network.crs, target_epoch=EPOCH_2020)
        assert not stage(job, "dnareftran").included

    def test_a_transformation_when_the_frame_differs(self, network) -> None:
        job = DynAdjustJob(network=network, target_frame="ITRF2020", target_epoch=EPOCH_2020)
        reftran = stage(job, "dnareftran")
        assert reftran.included
        assert "ITRF2020" in reftran.arguments
        assert "the frame differs" in reftran.reason

    def test_a_transformation_when_the_epoch_differs(self, network) -> None:
        job = DynAdjustJob(network=network, target_epoch=EPOCH_2026)
        reftran = stage(job, "dnareftran")
        assert reftran.included
        assert "01.01.2026" in reftran.arguments
        assert "the epoch differs" in reftran.reason

    def test_an_unstated_input_frame_is_not_a_different_frame(self, network) -> None:
        """The subtle one. Transforming out of a frame nobody recorded applies a
        shift computed from a guess, which is exactly what FR-105 forbids -- so
        the target is taken as a statement of what the data already is.
        """
        network.crs = ""
        job = DynAdjustJob(network=network, target_frame="GDA2020", target_epoch=EPOCH_2020)
        reftran = stage(job, "dnareftran")
        assert not reftran.included
        assert "states no frame" in reftran.reason

    def test_no_geoid_when_every_height_is_ellipsoidal(self, network) -> None:
        assert not stage(DynAdjustJob(network=network), "dnageoid").included

    def test_a_geoid_when_orthometric_heights_take_part(self, network) -> None:
        station = next(iter(network.stations.values()))
        network.stations[station.id] = Station(
            id=station.id,
            approx_position=Position(
                values=tuple(Quantity.exact(0.0, Unit.METRE) for _ in range(3)),  # type: ignore[arg-type]
                system=CoordinateSystem.PROJECTED,
                crs="GDA2020",
                epoch=EPOCH_2020,
                height_type=HeightType.ORTHOMETRIC,
            ),
        )
        geoid = stage(DynAdjustJob(network=network, geoid_grid="g.gsb"), "dnageoid")
        assert geoid.included
        assert "FR-804" in geoid.reason

    def test_orthometric_heights_without_a_grid_are_refused(self, network, tmp_path) -> None:
        """Better here than as an ellipsoidal answer nobody asked for."""
        station = next(iter(network.stations.values()))
        network.stations[station.id] = Station(
            id=station.id,
            approx_position=Position(
                values=tuple(Quantity.exact(0.0, Unit.METRE) for _ in range(3)),  # type: ignore[arg-type]
                system=CoordinateSystem.PROJECTED,
                crs="GDA2020",
                epoch=EPOCH_2020,
                height_type=HeightType.ORTHOMETRIC,
            ),
        )
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustEngine().prepare(DynAdjustJob(network=network), tmp_path)
        assert excinfo.value.code == "validation.dynadjust_geoid_grid_required"

    def test_a_small_network_adjusts_simultaneously(self, network) -> None:
        job = DynAdjustJob(network=network)
        assert not stage(job, "dnasegment").included
        assert "--simultaneous-adjustment" in stage(job, "dnaadjust").arguments

    def test_a_large_network_is_segmented_and_phased(self, network) -> None:
        job = DynAdjustJob(network=network, segmentation_threshold=2)
        assert stage(job, "dnasegment").included
        assert "--phased-adjustment" in stage(job, "dnaadjust").arguments

    def test_phasing_can_be_asked_for_outright(self, network) -> None:
        job = DynAdjustJob(network=network, phased=True)
        assert stage(job, "dnasegment").included
        assert "asked for" in stage(job, "dnasegment").reason

    def test_the_adjustment_asks_for_everything_the_parsers_read(self, network) -> None:
        """All of these are off by default, and each one absent costs a part of
        the Solution."""
        arguments = stage(DynAdjustJob(network=network), "dnaadjust").arguments
        for option in (
            "--output-adj-msr",
            "--output-pos-uncertainty",
            "--output-all-covariances",
            "--output-corrections-file",
            "--stn-corrections",
        ):
            assert option in arguments

    def test_the_angular_format_is_stated_rather_than_left_to_the_default(
        self, network
    ) -> None:
        """The ``.xyz`` and ``.apu`` record no command line, so the only way
        they can be read without guessing is for GeoComp to have asked."""
        arguments = stage(DynAdjustJob(network=network), "dnaadjust").arguments
        assert "--angular-stn-type" in arguments

    def test_no_requested_precision_can_overflow_a_column(self, network) -> None:
        """GeoComp controls the flags it passes, so this is its own to get right.

        ``--precision-stn-angular 7`` makes DynAdjust print a 15-character
        latitude into a 14-character field, and the row stops being sliceable
        (``specs/07`` section 5.5). GeoComp asks for no angular precision at all
        and takes DynAdjust's default of 5; if it ever does ask, 6 is the last value
        that fits.
        """
        arguments = stage(DynAdjustJob(network=network), "dnaadjust").arguments
        if "--precision-stn-angular" in arguments:
            requested = int(arguments[arguments.index("--precision-stn-angular") + 1])
            assert requested <= 6, "a 15-character angle does not fit a 14-character column"

    def test_the_confidence_reaches_the_command_line(self, network) -> None:
        arguments = stage(DynAdjustJob(network=network, confidence=0.99), "dnaadjust").arguments
        assert arguments[arguments.index("--conf-interval") + 1] == "99"


class TestPrepare:
    def test_it_writes_both_input_files_and_starts_nothing(self, network, tmp_path) -> None:
        prepared = DynAdjustEngine().prepare(DynAdjustJob(network=network, name="p"), tmp_path)
        assert prepared.station_file.is_file()
        assert prepared.measurement_file.is_file()
        assert prepared.station_file.name == "p-stn.xml"
        assert "GDA2020" in prepared.station_file.read_text()

    def test_the_output_paths_follow_the_adjustment_mode(self, network, tmp_path) -> None:
        engine = DynAdjustEngine()
        simultaneous = engine.prepare(DynAdjustJob(network=network, name="p"), tmp_path)
        assert simultaneous.mode == "simult"
        assert simultaneous.output("adj").name == "p.simult.adj"
        phased = engine.prepare(
            DynAdjustJob(network=network, name="p", phased=True), tmp_path
        )
        assert phased.output("adj").name == "p.phased.adj"

    def test_it_keeps_the_name_mapping_the_parsers_need(self, network, tmp_path) -> None:
        prepared = DynAdjustEngine().prepare(DynAdjustJob(network=network), tmp_path)
        assert set(prepared.names) == set(network.stations)


class TestTheImportCheck:
    def test_the_counts_are_read_from_dynadjusts_own_report(self) -> None:
        from geocomp.engines.dynadjust.engine import imported_counts

        stdout = (
            "  sample-stn.xml...       Done. Loaded 11 stations in 0.002s\n"
            "  sample-msr.xml...       Done. Loaded 36 measurements in 0.002s\n"
        )
        assert imported_counts(stdout) == {"stations": 11, "measurements": 36}

    def test_several_input_files_are_summed(self) -> None:
        from geocomp.engines.dynadjust.engine import imported_counts

        stdout = "Loaded 4 stations\nLoaded 7 stations\nLoaded 12 measurements\n"
        assert imported_counts(stdout) == {"stations": 11, "measurements": 12}

    def test_output_with_no_counts_reads_as_nothing_rather_than_zero(self) -> None:
        """A version that phrases it differently must not read as "imported
        nothing" -- that would reject it over its wording."""
        from geocomp.engines.dynadjust.engine import imported_counts

        assert imported_counts("+ Done.") == {"stations": 0, "measurements": 0}


class TestVersionDetection:
    def test_the_banner_is_read(self) -> None:
        version = parse_version(
            "+ Version:      1.4.0, Release with OpenBLAS", path=Path("/opt/dnaadjust")
        )
        assert version is not None
        assert version.version == "1.4.0"
        assert version.tested is True

    def test_an_untested_version_is_a_warning_not_a_refusal(self) -> None:
        """FR-302: a user with a newer DynAdjust should be told the parsers may
        not match it, not stopped from running it."""
        version = parse_version("+ Version:      9.9.0, Release", path=Path("/x"))
        assert version is not None
        assert version.tested is False

    def test_a_banner_with_no_version_yields_nothing(self) -> None:
        assert parse_version("no version here", path=Path("/x")) is None


class TestTheEpochFormat:
    def test_an_instant_gives_its_own_day(self) -> None:
        assert dynadjust_epoch(EPOCH_2020) == "01.01.2020"

    def test_a_decimal_year_converts_by_definition(self) -> None:
        assert dynadjust_epoch(Epoch.from_decimal_year(2020.0)) == "01.01.2020"
        assert dynadjust_epoch(Epoch.from_decimal_year(2020.5)) == "02.07.2020"


@pytest.mark.engines
@requires_dynadjust
class TestAgainstARealEngine:
    """Tier 4: what only a running DynAdjust can show."""

    def test_it_reports_the_installed_version(self) -> None:
        version = DynAdjustEngine().detect()
        assert version is not None
        assert version.version

    def test_the_whole_pipeline_reaches_a_solution(self, network, tmp_path) -> None:
        """The claim the fixtures cannot make: that DynAdjust accepts the files
        GeoComp writes, and that the pipeline drives it through to a Solution."""
        job = DynAdjustJob(network=network, name="run", target_frame="GDA2020")
        solution = DynAdjustEngine().adjust(job, tmp_path)
        assert len(solution.adjusted_stations) == 11
        assert len(solution.observation_results) == 36
        assert solution.statistics.converged
        assert solution.statistics.degrees_of_freedom == 3
        assert solution.parameter_covariance is not None

    def test_the_provenance_records_every_stage_and_why(self, network, tmp_path) -> None:
        job = DynAdjustJob(network=network, name="run")
        solution = DynAdjustEngine().adjust(job, tmp_path)
        provenance = solution.provenance
        assert provenance is not None
        assert provenance.engine == "dynadjust"
        assert provenance.engine_version
        stages = provenance.parameters["stages"]
        assert [item["program"] for item in stages] == [
            "dnaimport",
            "dnareftran",
            "dnageoid",
            "dnasegment",
            "dnaadjust",
        ]
        assert all(item["reason"] for item in stages)
        assert "dnaimport" in provenance.command_line

    def test_an_unparsed_measurement_file_is_caught_despite_a_zero_exit(
        self, network, tmp_path
    ) -> None:
        """``dnaimport`` exits 0 on a measurement file it could not parse.

        It warns on stdout -- "some files were not parsed", "there are no
        measurements to process" -- and returns success. Trusting the exit code
        alone would carry an empty network into ``dnaadjust``; worse, when only
        *part* of a file fails to parse, into an adjustment of fewer
        observations than intended whose variance factor looks perfectly
        healthy. The count check is what catches it.
        """
        from geocomp.core.errors import ComputationError

        engine = DynAdjustEngine()
        prepared = engine.prepare(DynAdjustJob(network=network, name="bad"), tmp_path)
        prepared.measurement_file.write_text("<DnaXmlFormat>not a measurement file</DnaXmlFormat>")
        with pytest.raises(ComputationError) as excinfo:
            engine.run(prepared)
        assert excinfo.value.code == "computation.dynadjust_import_incomplete"
        assert excinfo.value.context["expected"]["measurements"] == 36
        assert excinfo.value.context["received"]["measurements"] == 0

    def test_a_failing_stage_surfaces_dynadjusts_own_diagnostic(
        self, network, tmp_path
    ) -> None:
        """FR-305: DynAdjust's messages name the file and the reason, and are
        more use than anything GeoComp could write about them."""
        from geocomp.core.errors import ComputationError

        engine = DynAdjustEngine()
        prepared = engine.prepare(DynAdjustJob(network=network, name="bad"), tmp_path)
        prepared.station_file.write_text("<DnaXmlFormat>not a station file</DnaXmlFormat>")
        with pytest.raises(ComputationError) as excinfo:
            engine.run(prepared)
        assert excinfo.value.context["diagnostic"]


class TestAPartialNetwork:
    """Three GeoComp observation types have no DynAdjust type, and one of them
    -- ``HORIZONTAL_DISTANCE`` -- is the dominant type in a plane trilateration
    or traverse. Adjusting what is left answers a different question.
    """

    @staticmethod
    def _mixed() -> object:
        from geocomp.core.models import Network, Observation, ObservationType

        network = Network(id="mixed", crs="GDA2020", epoch=EPOCH_2020)
        for name, lat, lon in (("A", -25.45, -49.23), ("B", -25.46, -49.22)):
            network.stations[name] = Station(
                id=name,
                approx_position=Position(
                    values=(
                        Quantity.exact(math.radians(lat), Unit.RADIAN),
                        Quantity.exact(math.radians(lon), Unit.RADIAN),
                        Quantity.exact(915.0, Unit.METRE),
                    ),
                    system=CoordinateSystem.GEODETIC,
                    crs="GDA2020",
                    height_type=HeightType.ELLIPSOIDAL,
                ),
            )
        network.observations["s1"] = Observation(
            id="s1",
            type=ObservationType.SLOPE_DISTANCE,
            stations=("A", "B"),
            values=(Quantity(1421.331, 0.005**2, Unit.METRE),),
        )
        network.observations["h1"] = Observation(
            id="h1",
            type=ObservationType.HORIZONTAL_DISTANCE,
            stations=("A", "B"),
            values=(Quantity(1421.000, 0.005**2, Unit.METRE),),
        )
        return network

    def test_it_is_refused_by_default(self, tmp_path) -> None:
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustEngine().prepare(DynAdjustJob(network=self._mixed()), tmp_path)
        assert excinfo.value.code == "validation.dynadjust_network_would_be_partial"
        assert excinfo.value.context["skipped"] == 1
        assert excinfo.value.context["of"] == 2

    def test_the_refusal_names_what_could_not_be_written(self, tmp_path) -> None:
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustEngine().prepare(DynAdjustJob(network=self._mixed()), tmp_path)
        assert "horizontal_distance" in " ".join(excinfo.value.context["reasons"])

    def test_it_can_be_accepted_explicitly(self, tmp_path) -> None:
        """Not a lint to silence: turning it on is a statement that a partial
        network is what was wanted, and the skipped list still reports which."""
        prepared = DynAdjustEngine().prepare(
            DynAdjustJob(network=self._mixed(), allow_partial=True), tmp_path
        )
        assert len(prepared.skipped) == 1
        assert prepared.measurement_file.is_file()

    def test_a_network_that_maps_completely_is_untouched_by_this(
        self, network, tmp_path
    ) -> None:
        prepared = DynAdjustEngine().prepare(DynAdjustJob(network=network), tmp_path)
        assert prepared.skipped == ()


@pytest.mark.engines
@requires_dynadjust
class TestAProjectedNetworkCrossValidates:
    """The second cross-validation network P6's exit criterion asks for.

    Before ``core/geodesy/``, no projected network could reach DynAdjust at all:
    the writer refused, correctly, because a grid easting written under any
    DynaML coordinate type puts the station somewhere it is not. That refusal is
    why the criterion had one network of three (``specs/ROADMAP.md`` P6).

    A levelling loop is the case that clears the *other* obstacle too. Its
    height differences map to DynAdjust's ``L``, so the whole network imports --
    unlike a trilateration, whose horizontal distances have no DynAdjust
    equivalent (``specs/07`` section 4.2) and still refuse.
    """

    @staticmethod
    def projected(reference, projection, *, easting=670000.0, northing=7185000.0):
        """Place a local plane network inside SIRGAS 2000 / UTM 22S."""
        network = reference.network
        for index, (station_id, station) in enumerate(list(network.stations.items())):
            east, north, up = (q.value for q in station.approx_position.values)
            network.stations[station_id] = Station(
                id=station.id,
                name=station.name,
                description=station.description,
                approx_position=Position(
                    values=(
                        Quantity.exact(easting + east + index * 300.0, Unit.METRE),
                        Quantity.exact(northing + north + index * 250.0, Unit.METRE),
                        Quantity.exact(up, Unit.METRE),
                    ),
                    system=CoordinateSystem.PROJECTED,
                    crs="EPSG:31982",
                    height_type=station.approx_position.height_type,
                ),
                constraint=station.constraint,
                station_type=station.station_type,
            )
        del projection
        return network

    def test_a_projected_levelling_network_adjusts(self, tmp_path) -> None:
        """The heights come back agreeing with GeoComp's own to the printed 0.1 mm.

        The comparison adds the geoid undulation back, and that is not a fudge:
        GeoComp's heights are orthometric, the writer converts them to *h* for
        DynaML (FR-804), and DynAdjust with **no geoid model loaded** prints
        ``H(Ortho)`` equal to ``h(Ellipse)`` -- it has nothing to separate them
        with. Differencing the two columns directly would show a constant offset
        that looks like a datum error and is not one.
        """
        from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
        from geocomp.core.adjustment.parameters import Frame
        from geocomp.core.geodesy import (
            ELLIPSOIDS,
            cartesian_to_geodetic,
            utm_parameters,
        )
        from tests import networks as reference_networks

        undulation = -4.0
        projection = utm_parameters(22, southern_hemisphere=True,
                                    ellipsoid=ELLIPSOIDS["GRS80"])

        in_house = adjust(
            reference_networks.levelling_loop().network,
            AdjustmentOptions(frame=Frame.HEIGHT_1D),
        )
        expected = {
            station_id: (
                float(in_house.parameters[in_house.layout.column(station_id, "h")])
                if in_house.layout.column(station_id, "h") is not None
                else in_house.layout.fixed_values[(station_id, "h")]
            )
            for station_id in reference_networks.levelling_loop().network.stations
        }

        network = self.projected(reference_networks.levelling_loop(), projection)
        job = DynAdjustJob(
            network=network,
            name="levelled",
            target_frame="GDA2020",
            target_epoch=Epoch.from_decimal_year(2020.0),
            projection=projection,
            geoid_undulations=dict.fromkeys(network.stations, undulation),
        )
        engine = DynAdjustEngine()
        prepared = engine.prepare(job, tmp_path)
        runs = engine.run(prepared)
        assert all(run.exit_code == 0 for run in runs), [run.diagnostic for run in runs]

        solution = read_solution(
            prepared.output("adj"),
            network=network,
            apu_path=prepared.output("apu"),
            cor_path=prepared.output("cor"),
        )
        rows = {station.station_id: station for station in solution.adjusted_stations}
        assert set(rows) == set(expected)

        # The pipeline asks for PLHhXYZ, so the row comes back geocentric. Turning
        # it into a height uses the other half of core/geodesy, which makes this
        # a round trip through the whole of it: GeoComp's grid coordinates ->
        # geodetic (inverse projection) -> DynAdjust -> geocentric -> back to h.
        for station_id, row in rows.items():
            assert row.position.system is CoordinateSystem.CARTESIAN
            _, _, ellipsoidal = cartesian_to_geodetic(
                *(quantity.value for quantity in row.position.values),
                ELLIPSOIDS["GRS80"],
            )
            assert ellipsoidal - undulation == pytest.approx(
                expected[station_id], abs=2e-4
            ), station_id

    def test_the_near_singular_covariance_is_conditioned_and_labelled(self, tmp_path) -> None:
        """The whole ``Solution`` reads back, and says what it cost.

        A levelling network determines no horizontal position, so each station's
        cartesian covariance has an eigenvalue that ought to be zero. DynAdjust
        prints ten significant figures, which is not enough to keep it there:
        station A comes back at ``-3e-9``, which :class:`Covariance` refuses,
        and before ``covariance_from_printed`` that made the file unreadable as
        a solution at all.

        What is asserted here is the whole chain: the matrix is repaired, the
        repair is named on the covariance, and the name reaches the
        ``Solution``'s own mode -- because that is what a report prints (FR-203).
        """
        from geocomp.core.geodesy import ELLIPSOIDS, utm_parameters
        from geocomp.core.uncertainty import Strategy, UncertaintyMode
        from tests import networks as reference_networks

        projection = utm_parameters(22, southern_hemisphere=True,
                                    ellipsoid=ELLIPSOIDS["GRS80"])
        network = self.projected(reference_networks.levelling_loop(), projection)
        engine = DynAdjustEngine()
        prepared = engine.prepare(
            DynAdjustJob(
                network=network,
                name="conditioned",
                target_frame="GDA2020",
                target_epoch=Epoch.from_decimal_year(2020.0),
                projection=projection,
                geoid_undulations=dict.fromkeys(network.stations, -4.0),
            ),
            tmp_path,
        )
        assert all(run.exit_code == 0 for run in engine.run(prepared))

        solution = read_solution(
            prepared.output("adj"),
            network=network,
            apu_path=prepared.output("apu"),
            cor_path=prepared.output("cor"),
        )

        carried = [
            station.covariance
            for station in solution.adjusted_stations
            if station.covariance is not None
        ]
        assert len(carried) == len(solution.adjusted_stations)
        conditioned = [
            covariance
            for covariance in carried
            if Strategy.ROUNDING_CONDITIONED in covariance.strategies
        ]
        assert conditioned, "the printed matrix used to be indefinite; it should need repair"

        # Every matrix that came back is usable, repaired or not.
        for covariance in carried:
            scale = max(float(np.max(np.abs(covariance.matrix))), 1.0)
            smallest = float(np.linalg.eigvalsh(covariance.matrix)[0])
            assert smallest >= -covariance.EIGENVALUE_TOLERANCE * scale

        # The label survives to the Solution, and only when it was earned.
        assert solution.uncertainty_mode is UncertaintyMode.APPROXIMATE
        assert all(
            covariance.mode is UncertaintyMode.APPROXIMATE for covariance in conditioned
        )

        # The full parameter matrix assembles too, which is what needed the
        # cross blocks' precision as well as each station's own.
        assert solution.parameter_covariance is not None
        assert solution.parameter_covariance.size == 3 * len(solution.adjusted_stations)

    def test_a_projected_network_without_a_projection_is_still_refused(self, tmp_path) -> None:
        from geocomp.core.geodesy import ELLIPSOIDS, utm_parameters
        from tests import networks as reference_networks

        projection = utm_parameters(22, southern_hemisphere=True,
                                    ellipsoid=ELLIPSOIDS["GRS80"])
        network = self.projected(reference_networks.levelling_loop(), projection)
        job = DynAdjustJob(
            network=network,
            name="unstated",
            target_frame="GDA2020",
            target_epoch=Epoch.from_decimal_year(2020.0),
            # Undulations, so that the *projection* refusal is what is under
            # test rather than the geoid one that would otherwise fire first.
            geoid_undulations=dict.fromkeys(network.stations, -4.0),
        )
        with pytest.raises(ValidationError) as excinfo:
            DynAdjustEngine().adjust(job, tmp_path)
        assert excinfo.value.code == "validation.dynadjust_cannot_write_projected_coordinates"


@pytest.mark.engines
@requires_dynadjust
class TestATerrestrialNetworkCrossValidates:
    """RD-01 against DynAdjust: the third network P6's exit criterion asks for.

    The first two are a GNSS slice and a projected levelling loop, both of which
    exercise one observation type. RD-01 is the terrestrial case -- **directions,
    zenith angles and slope distances together**, measured from the instrument
    rather than from the mark -- and it is the author's own field data rather
    than anything written to be adjustable.

    Nothing in it had ever reached the engine, and nothing had ever adjusted it
    in three dimensions either; ``dimension=3`` appears in no other test. Four
    defects sat on the path, each of which produced a plausible wrong answer
    rather than an error, and they are covered by name in the tier-1 tests.
    """

    UNDULATION = -4.0
    EASTING, NORTHING, HEIGHT = 670000.0, 7185000.0, 100.0

    @classmethod
    def network(cls):
        """RD-01 in three dimensions, placed in SIRGAS 2000 / UTM 22S.

        The datum is the one DynAdjust can express. RD-01 has no azimuth and no
        known point, so its defect is three translations and a rotation about
        the vertical -- and DynAdjust has no inner constraints, only fixed or
        free per axis. Station 1 is held in all three and station 2 in easting
        alone: four constraints for a four-parameter defect, which is a minimum
        constraint rather than an over-constrained solution.
        """
        from geocomp.core.models import ConstraintMode, ConstraintSpec
        from geocomp.core.techniques.total_station import build_network, preprocess_setup
        from tests import reference_rd01 as rd01

        profiles = rd01.library()
        results = [preprocess_setup(setup, profiles) for _id, setup in sorted(rd01.setups().items())]
        network = build_network(
            results, rd01.approximate_coordinates(), crs="EPSG:31982", dimension=3
        )
        held = {"1": frozenset({"easting", "northing", "up"}), "2": frozenset({"easting"})}
        for station_id, station in list(network.stations.items()):
            east, north, up = (q.value for q in station.approx_position.values)
            position = Position(
                values=(
                    Quantity.exact(cls.EASTING + east, Unit.METRE),
                    Quantity.exact(cls.NORTHING + north, Unit.METRE),
                    Quantity.exact(cls.HEIGHT + up, Unit.METRE),
                ),
                system=CoordinateSystem.PROJECTED,
                crs="EPSG:31982",
                height_type=HeightType.ORTHOMETRIC,
            )
            components = held.get(station_id)
            network.stations[station_id] = Station(
                id=station.id,
                name=station.name,
                description=station.description,
                approx_position=position,
                constraint=(
                    ConstraintSpec(
                        mode=ConstraintMode.FIXED, components=components, position=position
                    )
                    if components
                    else ConstraintSpec()
                ),
                station_type=station.station_type,
            )
        return network

    @staticmethod
    def in_house(network):
        from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
        from geocomp.core.adjustment.parameters import Frame
        from geocomp.core.models.solution import DatumDefinition

        run = adjust(
            network,
            AdjustmentOptions(frame=Frame.SPACE_3D, datum=DatumDefinition.CONSTRAINED),
        )
        assert run.converged, "the in-house adjustment is the thing being compared against"
        return run, {
            station_id: tuple(
                float(run.parameters[run.layout.column(station_id, component)])
                if run.layout.column(station_id, component) is not None
                else run.layout.fixed_values[(station_id, component)]
                for component in ("e", "n", "u")
            )
            for station_id in network.stations
        }

    def engine_solution(self, network, tmp_path):
        from geocomp.core.geodesy import ELLIPSOIDS, utm_parameters

        projection = utm_parameters(22, southern_hemisphere=True, ellipsoid=ELLIPSOIDS["GRS80"])
        engine = DynAdjustEngine()
        prepared = engine.prepare(
            DynAdjustJob(
                network=network,
                name="rd01",
                target_frame="GDA2020",
                target_epoch=Epoch.from_decimal_year(2020.0),
                projection=projection,
                geoid_undulations=dict.fromkeys(network.stations, self.UNDULATION),
                # The one skipped observation is station 3's direction set of
                # one, which carries its own orientation unknown and therefore
                # no information at all -- asserted below rather than assumed.
                allow_partial=True,
            ),
            tmp_path,
        )
        assert [identifier for identifier, _reason in prepared.skipped] == ["3-dir-1"]
        runs = engine.run(prepared)
        assert all(run.exit_code == 0 for run in runs), [run.diagnostic for run in runs]
        return prepared, read_solution(
            prepared.output("adj"),
            network=network,
            apu_path=prepared.output("apu"),
            cor_path=prepared.output("cor"),
        )

    def test_the_lone_direction_set_carries_no_information(self) -> None:
        """What licenses ``allow_partial`` here, and it is a fact, not a hope.

        A direction set of one is one observation and one orientation unknown,
        so it adds a row and a column and changes nothing. DynAdjust cannot
        express it -- its ``D`` is a reference direction plus the directions
        measured from it, and ``dnaimport`` refuses a set that declares zero --
        so the writer reports it as skipped. That is only acceptable because
        removing it leaves the adjustment identical, which is asserted here.
        """
        from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
        from geocomp.core.adjustment.parameters import Frame
        from geocomp.core.models.solution import DatumDefinition

        full = self.network()
        trimmed = self.network()
        for cluster_id, cluster in list(trimmed.clusters.items()):
            if len(cluster.observation_ids) < 2:
                for identifier in cluster.observation_ids:
                    del trimmed.observations[identifier]
                del trimmed.clusters[cluster_id]
        assert len(trimmed.observations) == len(full.observations) - 1

        options = AdjustmentOptions(
            frame=Frame.SPACE_3D, datum=DatumDefinition.CONSTRAINED
        )
        with_it, without = adjust(full, options), adjust(trimmed, options)
        assert with_it.degrees_of_freedom == without.degrees_of_freedom
        for station_id in full.stations:
            for component in ("e", "n", "u"):
                a, b = (
                    with_it.layout.column(station_id, component),
                    without.layout.column(station_id, component),
                )
                if a is None or b is None:
                    continue
                assert float(with_it.parameters[a]) == pytest.approx(
                    float(without.parameters[b]), abs=1e-9
                )

    def test_the_two_engines_agree_on_the_triangle(self, tmp_path) -> None:
        """The criterion itself: same network, two adjustments, sub-millimetre.

        The comparison is on the **shape** -- the three side lengths -- and on
        the heights. Comparing coordinates directly would compare the round trip
        through the projection as well, which `specs/07` section 4.5 measures
        separately and which is a quarter of a millimetre at these latitudes.
        """
        import itertools

        from geocomp.core.geodesy import ELLIPSOIDS, cartesian_to_geodetic

        network = self.network()
        _run, in_house = self.in_house(network)
        _prepared, solution = self.engine_solution(network, tmp_path)

        engine = {}
        for station in solution.adjusted_stations:
            assert station.position.system is CoordinateSystem.CARTESIAN
            engine[station.station_id] = np.array(
                [quantity.value for quantity in station.position.values]
            )
        assert set(engine) == set(in_house)

        for first, second in itertools.combinations(sorted(engine), 2):
            theirs = float(np.linalg.norm(engine[first] - engine[second]))
            ours = math.dist(in_house[first], in_house[second])
            assert theirs == pytest.approx(ours, abs=5e-4), f"side {first}-{second}"

        for station_id, point in engine.items():
            _lat, _lon, ellipsoidal = cartesian_to_geodetic(*point, ELLIPSOIDS["GRS80"])
            assert ellipsoidal - self.UNDULATION == pytest.approx(
                in_house[station_id][2], abs=2e-4
            ), station_id

    def test_the_partial_constraint_reaches_the_right_axis(self, tmp_path) -> None:
        """Station 2 is held in **easting**, which is a longitude.

        The writer converts a projected position to geodetic and puts latitude
        in ``XAxis``, so a constraint stated on the grid has to be reordered
        before it is written. Without that, ``CFF`` holds the latitude -- the
        perpendicular axis -- and the network is constrained in a direction
        nobody asked for, which still adjusts and still converges.
        """
        prepared, _solution = self.engine_solution(self.network(), tmp_path)
        written = prepared.station_file.read_text()
        constraints = re.findall(r"<Constraints>(\w+)</Constraints>", written)
        assert constraints == ["CCC", "FCF", "FFF"]
