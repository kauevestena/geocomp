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

from datetime import UTC, datetime
from pathlib import Path

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
