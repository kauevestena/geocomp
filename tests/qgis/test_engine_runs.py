# SPDX-License-Identifier: GPL-2.0-or-later
"""What the engine algorithms do around a run (FR-302, FR-304; P12c-11).

Four defects, each in the algorithms rather than the adapters, so each needs
Processing to show:

* nothing that runs RTKLIB warned about an untested version, though FR-302
  says GeoComp MUST, and DynAdjust's adjustment always had;
* the GNSS results did not record which RTKLIB produced them;
* the RTKLIB time limit was the adapter's fixed ten minutes, though FR-304 says
  configurable, and *Keep the engine's working directory* was read by nothing;
* *Adjust network (DynAdjust)* deleted its temporary working directory as a
  refusal propagated, so the files the message pointed at were gone.

``rnx2rtkp`` and DynAdjust are tier 4; a stand-in for each is enough to show
what the algorithm does with what it is given.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT
from tests.qgis.conftest import requires_modern_field_api

pytestmark = pytest.mark.qgis

RINEX = REPO_ROOT / "tests" / "data" / "rtklib"
SOLUTION = RINEX / "pos" / "xyz.pos"
GNSS_IDS = (
    "geocomp:gnss_relative_static",
    "geocomp:gnss_relative_kinematic",
    "geocomp:gnss_absolute_static",
    "geocomp:gnss_absolute_kinematic",
    "geocomp:gnss_batch",
    "geocomp:gnss_compare_configurations",
)


def _feedback():
    from qgis.core import QgsProcessingFeedback

    class Recording(QgsProcessingFeedback):
        def __init__(self) -> None:
            super().__init__()
            self.warnings: list[str] = []
            self.infos: list[str] = []

        def pushWarning(self, text: str) -> None:  # noqa: N802 -- Qt's name
            self.warnings.append(text)
            super().pushWarning(text)

        def pushInfo(self, text: str) -> None:  # noqa: N802 -- Qt's name
            self.infos.append(text)
            super().pushInfo(text)

    return Recording()


class _Rtklib:
    """Stands in for ``RtklibEngine``: answers with the committed solution."""

    def __init__(self, *, tested: bool = True) -> None:
        from geocomp.engines.base import EngineVersion

        self.jobs: list = []
        self._version = EngineVersion(
            name="RTKLIB-EX",
            version="2.5.1" if tested else "2.6.0",
            path=Path("/opt/rtklib/rnx2rtkp"),
            tested=tested,
        )

    def version(self):
        return self._version

    def run(self, job, *, work_dir, on_progress=None):
        from geocomp.engines.base import EngineRun
        from geocomp.engines.rtklib import RtklibResult
        from geocomp.engines.rtklib.read_pos import read_pos

        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        self.jobs.append(job)
        output = work_dir / f"{job.rover.id}.pos"
        shutil.copyfile(SOLUTION, output)
        config = work_dir / "rnx2rtkp.conf"
        config.write_text("", encoding="utf-8")
        run = EngineRun(
            program="rnx2rtkp",
            command=("rnx2rtkp",),
            exit_code=0,
            stdout="",
            stderr="",
            seconds=1.0,
            work_dir=work_dir,
            version=self._version,
        )
        return RtklibResult(
            run=run, solution=read_pos(output), config_file=config, output_file=output
        )


@pytest.fixture
def rtklib(monkeypatch):
    from geocomp.services import engines

    def install(*, tested: bool = True) -> _Rtklib:
        engine = _Rtklib(tested=tested)
        monkeypatch.setattr(engines, "rtklib_engine", lambda: engine)
        return engine

    return install


def _process(tmp_path: Path, **extra):
    from qgis.core import QgsApplication, QgsProcessingContext

    folder = tmp_path / "rinex"
    folder.mkdir()
    for path in RINEX.iterdir():
        if path.is_file() and path.suffix != ".md":
            shutil.copy(path, folder)
    out = tmp_path / "out"
    out.mkdir()
    parameters = {
        "FOLDER": str(folder),
        "BASE_STATION": "3040",
        "ROVER_STATION": "0759",
        "OUTPUT_POS": str(out / "solution.pos"),
        "OUTPUT_JSON": str(out / "summary.json"),
        **extra,
    }
    algorithm = QgsApplication.processingRegistry().algorithmById(
        "geocomp:gnss_relative_static"
    ).create({})
    feedback = _feedback()
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), feedback, catchExceptions=False
    )
    assert ok
    return results, feedback, out


class TestTheVersion:
    def test_an_untested_rtklib_is_warned_about(self, geocomp_provider, rtklib, tmp_path):
        """FR-302: warn, proceed, and record."""
        rtklib(tested=False)
        _results, feedback, _out = _process(tmp_path)
        assert any("2.6.0" in warning for warning in feedback.warnings)

    def test_a_tested_one_is_not(self, geocomp_provider, rtklib, tmp_path):
        rtklib(tested=True)
        _results, feedback, _out = _process(tmp_path)
        assert not any("2.5.1" in warning for warning in feedback.warnings)
        assert any("2.5.1" in info for info in feedback.infos)

    def test_the_summary_records_which_engine_produced_it(
        self, geocomp_provider, rtklib, tmp_path
    ):
        rtklib(tested=False)
        _results, _feedback, out = _process(tmp_path)
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary["engine"]["name"] == "RTKLIB-EX"
        assert summary["engine"]["version"] == "2.6.0"
        assert summary["engine"]["tested"] is False

    def test_and_what_the_engine_was_asked_and_said(self, geocomp_provider, rtklib, tmp_path):
        """FR-036: the command line, the exit code and both streams, as for
        DynAdjust. Until P12c-13 the summary had none of them."""
        rtklib()
        _results, _feedback, out = _process(tmp_path)
        run = json.loads((out / "summary.json").read_text(encoding="utf-8"))["run"]
        assert run["command"] == ["rnx2rtkp"]
        assert run["exit_code"] == 0
        assert {"stdout", "stderr", "seconds", "version"} <= set(run)


class TestTheTimeLimit:
    @pytest.mark.parametrize("algorithm_id", GNSS_IDS)
    def test_every_algorithm_that_runs_rtklib_offers_it(self, geocomp_provider, algorithm_id):
        from qgis.core import QgsApplication, QgsProcessingParameterDefinition

        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        parameter = algorithm.parameterDefinition("TIMEOUT")
        assert parameter is not None
        assert parameter.flags() & QgsProcessingParameterDefinition.FlagAdvanced
        assert parameter.defaultValue() == 600.0

    def test_it_reaches_the_run(self, geocomp_provider, rtklib, tmp_path):
        engine = rtklib()
        _process(tmp_path, TIMEOUT=77.0)
        (job,) = engine.jobs
        assert job.timeout == 77.0


class TestTheWorkingDirectory:
    def test_it_is_kept_and_said_where(self, geocomp_provider, rtklib, tmp_path):
        rtklib()
        _results, feedback, out = _process(tmp_path, KEEP_WORK_DIR=True)
        work_dir = out / "relative-static-0759"
        assert (work_dir / "rnx2rtkp.conf").is_file()
        assert any(str(work_dir) in info for info in feedback.infos)

    def test_it_is_removed_when_not_wanted(self, geocomp_provider, rtklib, tmp_path):
        """Until P12c-11 unchecking the box changed nothing."""
        rtklib()
        _results, _feedback, out = _process(tmp_path, KEEP_WORK_DIR=False)
        assert not (out / "relative-static-0759").exists()
        assert (out / "solution.pos").is_file()


# -- DynAdjust -------------------------------------------------------------


# -- RTKLIB: an options file of the user's own (FR-070, P12c-21) ------------

RTKLIB_RUNS = tuple(i for i in GNSS_IDS if i != "geocomp:gnss_compare_configurations")


def _options(tmp_path: Path, text: str) -> str:
    path = tmp_path / "mine.conf"
    path.write_text(text, encoding="utf-8")
    return str(path)


class TestAUsersOwnRtklibOptions:
    @pytest.mark.parametrize("algorithm_id", RTKLIB_RUNS)
    def test_every_algorithm_that_processes_offers_it_in_advanced(
        self, geocomp_provider, algorithm_id
    ):
        from qgis.core import QgsApplication, QgsProcessingParameterDefinition

        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        parameter = algorithm.parameterDefinition("CONFIGURATION")
        assert parameter is not None
        assert parameter.flags() & QgsProcessingParameterDefinition.FlagAdvanced
        assert parameter.flags() & QgsProcessingParameterDefinition.FlagOptional

    def test_its_options_reach_the_run_and_the_summary(self, geocomp_provider, rtklib, tmp_path):
        engine = rtklib()
        conf = _options(tmp_path, "pos2-arlockcnt =7\npos1-elmask =10 # (deg)\n")
        _results, feedback, out = _process(tmp_path, CONFIGURATION=conf)
        (job,) = engine.jobs
        assert job.config.extra["pos2-arlockcnt"] == "7"
        assert job.config.elevation_mask == 10.0
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert summary["user_configuration"] == {
            "file": conf,
            "options": {"pos2-arlockcnt": "7", "pos1-elmask": "10"},
        }
        assert summary["configuration"]["settings"]["pos2-arlockcnt"] == "7"
        assert any("pos2-arlockcnt = 7" in info for info in feedback.infos)

    def test_the_parameters_here_come_over_the_file(self, geocomp_provider, rtklib, tmp_path):
        engine = rtklib()
        conf = _options(tmp_path, "pos1-elmask =10\n")
        _process(tmp_path, CONFIGURATION=conf, ELEVATION_MASK=20.0)
        (job,) = engine.jobs
        assert job.config.elevation_mask == 20.0

    def test_without_one_nothing_is_recorded(self, geocomp_provider, rtklib, tmp_path):
        rtklib()
        _results, _feedback, out = _process(tmp_path)
        assert "user_configuration" not in json.loads(
            (out / "summary.json").read_text(encoding="utf-8")
        )

    def test_an_option_geocomp_reads_the_result_by_is_refused_before_any_run(
        self, geocomp_provider, rtklib, tmp_path
    ):
        from qgis.core import QgsProcessingException

        engine = rtklib()
        conf = _options(tmp_path, "out-timesys =utc\n")
        with pytest.raises(QgsProcessingException) as caught:
            _process(tmp_path, CONFIGURATION=conf)
        assert "RTKLIB configuration file" in str(caught.value)
        assert "out-timesys" in str(caught.value)
        assert engine.jobs == []

    def test_a_file_that_sets_nothing_is_refused_against_the_parameter(
        self, geocomp_provider, rtklib, tmp_path
    ):
        from qgis.core import QgsProcessingException

        rtklib()
        conf = _options(tmp_path, "# only a comment\n")
        with pytest.raises(QgsProcessingException) as caught:
            _process(tmp_path, CONFIGURATION=conf)
        assert "RTKLIB configuration file" in str(caught.value)
        assert "mine.conf" in str(caught.value)

    def test_a_batch_runs_every_session_with_it_and_records_it(
        self, geocomp_provider, rtklib, tmp_path
    ):
        from qgis.core import QgsApplication, QgsProcessingContext

        engine = rtklib()
        conf = _options(tmp_path, "pos2-arlockcnt =7\n")
        folder = tmp_path / "rinex"
        folder.mkdir()
        for path in RINEX.iterdir():
            if path.is_file() and path.suffix != ".md":
                shutil.copy(path, folder)
        report = tmp_path / "batch.json"
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:gnss_batch"
        ).create({})
        _results, ok = algorithm.run(
            {
                "FOLDER": str(folder),
                "BASE_STATION": "3040",
                "PROFILE": 0,
                "CONFIGURATION": conf,
                "OUTPUT_JSON": str(report),
            },
            QgsProcessingContext(),
            _feedback(),
            catchExceptions=False,
        )
        assert ok
        assert engine.jobs
        assert all(job.config.extra["pos2-arlockcnt"] == "7" for job in engine.jobs)
        recorded = json.loads(report.read_text(encoding="utf-8"))
        assert recorded["user_configuration"]["options"] == {"pos2-arlockcnt": "7"}
        assert recorded["configuration"]["settings"]["pos2-arlockcnt"] == "7"


class _DynAdjust:
    """Stands in for ``DynAdjustEngine``: prepares, then fails as told."""

    def __init__(self, failure) -> None:
        self.failure = failure
        self.work_dir: Path | None = None

    def detect(self):
        from geocomp.engines.base import EngineVersion

        return EngineVersion(name="DynAdjust", version="1.2.8", path=Path("/opt/dynadjust"))

    def prepare(self, job, work_dir):
        from types import SimpleNamespace

        self.work_dir = Path(work_dir)
        (self.work_dir / "run-stn.xml").write_text("<DnaXmlFormat/>", encoding="utf-8")
        return SimpleNamespace(skipped=(), included=(), stages=())

    def run(self, prepared, *, timeout, on_progress=None):
        raise self.failure(self.work_dir)


def _adjust(tmp_path: Path, monkeypatch, failure) -> tuple[str, Path]:
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingException

    from geocomp.algorithms.engines import dynadjust_adjust
    from tests.networks import trilateration

    engine = _DynAdjust(failure)
    monkeypatch.setattr(dynadjust_adjust, "dynadjust_engine", lambda directory=None: engine)
    network = tmp_path / "network.json"
    network.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
    algorithm = QgsApplication.processingRegistry().algorithmById(
        "geocomp:analysis_dynadjust_adjust"
    ).create({})
    with pytest.raises(QgsProcessingException) as raised:
        algorithm.run(
            {
                "NETWORK": str(network),
                "FRAME": "GDA2020",
                "EPOCH": 2020.0,
                "OUTPUT_SOLUTION": str(tmp_path / "s.json"),
            },
            QgsProcessingContext(),
            _feedback(),
            catchExceptions=False,
        )
    assert engine.work_dir is not None, str(raised.value)
    return str(raised.value), engine.work_dir


class TestADynAdjustRefusal:
    def test_a_timeout_keeps_the_files_it_points_at(self, geocomp_provider, tmp_path, monkeypatch):
        """``specs/07`` section 7: the process group terminated, the working
        directory retained, the elapsed time and the limit reported."""
        from geocomp.core.errors import ComputationError

        def timed_out(work_dir):
            return ComputationError(
                "dynadjust_stage_timed_out",
                program="dnaadjust",
                elapsed="1801",
                limit="1800",
                completed=["dnaimport"],
                work_dir=str(work_dir),
            )

        message, work_dir = _adjust(tmp_path, monkeypatch, timed_out)
        assert (work_dir / "run-stn.xml").is_file()
        assert str(work_dir) in message
        assert "1800" in message
        assert "exit code" not in message
        shutil.rmtree(work_dir)

    def test_a_refusal_that_names_no_files_leaves_none_behind(
        self, geocomp_provider, tmp_path, monkeypatch
    ):
        from geocomp.core.errors import ComputationError

        def refused(work_dir):
            return ComputationError(
                "dynadjust_output_missing", expected="run.simult.adj"
            )

        _message, work_dir = _adjust(tmp_path, monkeypatch, refused)
        assert not work_dir.exists()


# -- DynAdjust's result on the map (FR-324) ------------------------------


class _SolvingDynAdjust(_DynAdjust):
    """A DynAdjust that answers with the committed sample's own output files.

    The solution is DynAdjust's -- parsed from the ``.adj`` and ``.apu`` it
    wrote for this network -- so what reaches the layers is what the engine
    would have produced.
    """

    def __init__(self, network) -> None:
        super().__init__(failure=None)
        self.network = network

    def run(self, prepared, *, timeout, on_progress=None):
        return []

    def parse(self, runs, prepared):
        from geocomp.engines.dynadjust.read_output import AngularFormat
        from geocomp.engines.dynadjust.solution import read_solution

        output = REPO_ROOT / "tests" / "data" / "dynadjust" / "output"
        return read_solution(
            output / "sample.adj",
            network=self.network,
            apu_path=output / "sample.apu",
            cor_path=output / "sample.cor",
            angular_format=AngularFormat.HP,
        )


@requires_modern_field_api
class TestADynAdjustResultOnTheMap:
    def test_its_stations_and_ellipses_arrive_as_layers(
        self, geocomp_provider, tmp_path, monkeypatch
    ):
        """FR-324: until P12c-13 *Adjust network (DynAdjust)* wrote its solution
        document and offered no layer, though the in-house adjustment did."""
        from qgis.core import (
            QgsApplication,
            QgsProcessing,
            QgsProcessingContext,
            QgsProcessingUtils,
        )

        from geocomp.algorithms.engines import dynadjust_adjust
        from geocomp.engines.dynadjust.read_dynaml import read_dynaml

        data = REPO_ROOT / "tests" / "data" / "dynadjust"
        network = read_dynaml(data / "sample-stn.xml", data / "sample-msr.xml").network
        engine = _SolvingDynAdjust(network)
        monkeypatch.setattr(dynadjust_adjust, "dynadjust_engine", lambda directory=None: engine)
        document = tmp_path / "network.json"
        document.write_text(json.dumps(network.to_dict()), encoding="utf-8")

        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_adjust"
        ).create({})
        context = QgsProcessingContext()
        results, ok = algorithm.run(
            {
                "NETWORK": str(document),
                "FRAME": "GDA2020",
                "EPOCH": 2020.0,
                "OUTPUT_SOLUTION": str(tmp_path / "solution.json"),
                "OUTPUT_STATION_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
                "OUTPUT_ELLIPSE_LAYER": QgsProcessing.TEMPORARY_OUTPUT,
            },
            context,
            _feedback(),
            catchExceptions=False,
        )
        assert ok
        stations = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_STATION_LAYER"], context)
        ellipses = QgsProcessingUtils.mapLayerFromString(results["OUTPUT_ELLIPSE_LAYER"], context)
        assert stations is not None and ellipses is not None
        assert stations.featureCount() == 11
        assert ellipses.featureCount() > 0


# -- DynAdjust: stop, edit, run later (FR-325, P12c-21) -------------------


class _NeverDetected:
    """The real engine's prepare; detecting it would mean the stop needed DynAdjust."""

    def __init__(self) -> None:
        from geocomp.engines.dynadjust.engine import DynAdjustEngine

        self._engine = DynAdjustEngine()

    def prepare(self, job, work_dir):
        return self._engine.prepare(job, work_dir)

    def detect(self):
        raise AssertionError("stopping before running must not need DynAdjust")


class _RunsWhatWasPrepared(_DynAdjust):
    """Runs nothing; reads the committed sample's output with the job's own provenance."""

    def __init__(self) -> None:
        super().__init__(failure=None)
        self.ran = None

    def run(self, prepared, *, timeout, on_progress=None):
        self.ran = prepared
        return []

    def parse(self, runs, prepared):
        from geocomp.engines.dynadjust.engine import provenance
        from geocomp.engines.dynadjust.read_output import AngularFormat
        from geocomp.engines.dynadjust.solution import read_solution

        output = REPO_ROOT / "tests" / "data" / "dynadjust" / "output"
        return read_solution(
            output / "sample.adj",
            network=prepared.job.network,
            apu_path=output / "sample.apu",
            cor_path=output / "sample.cor",
            angular_format=AngularFormat.HP,
            provenance=provenance(runs, prepared),
        )


class TestStopEditAndRunLater:
    @pytest.fixture
    def network_document(self, tmp_path):
        from geocomp.engines.dynadjust.read_dynaml import read_dynaml

        data = REPO_ROOT / "tests" / "data" / "dynadjust"
        network = read_dynaml(data / "sample-stn.xml", data / "sample-msr.xml").network
        document = tmp_path / "network.json"
        document.write_text(json.dumps(network.to_dict()), encoding="utf-8")
        return document

    @staticmethod
    def _stop(tmp_path, monkeypatch, network_document, configuration=None):
        from qgis.core import QgsApplication, QgsProcessingContext

        from geocomp.algorithms.engines import dynadjust_adjust

        monkeypatch.setattr(
            dynadjust_adjust, "dynadjust_engine", lambda directory=None: _NeverDetected()
        )
        parameters = {
            "NETWORK": str(network_document),
            "FRAME": "GDA2020",
            "EPOCH": 2020.0,
            "STOP_BEFORE_RUNNING": True,
            "OUTPUT_WORK_DIR": str(tmp_path / "job"),
            "OUTPUT_SOLUTION": str(tmp_path / "unwritten.json"),
        }
        if configuration is not None:
            path = tmp_path / "dynadjust.json"
            path.write_text(json.dumps(configuration), encoding="utf-8")
            parameters["CONFIGURATION"] = str(path)
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_adjust"
        ).create({})
        results, ok = algorithm.run(
            parameters, QgsProcessingContext(), _feedback(), catchExceptions=False
        )
        assert ok
        return results

    def test_it_stops_with_the_input_written_and_needs_no_dynadjust(
        self, geocomp_provider, tmp_path, monkeypatch, network_document
    ):
        from geocomp.engines.dynadjust.engine import MANIFEST

        results = self._stop(
            tmp_path, monkeypatch, network_document, {"dnaadjust": ["--free-stn-sd", "10"]}
        )
        job = Path(results["OUTPUT_WORK_DIR"])
        assert job == tmp_path / "job"
        manifest = json.loads((job / MANIFEST).read_text(encoding="utf-8"))
        assert (job / manifest["station_file"]).is_file()
        assert (job / manifest["measurement_file"]).is_file()
        adjust = next(s for s in manifest["stages"] if s["program"] == "dnaadjust")
        assert adjust["arguments"][-2:] == ["--free-stn-sd", "10"]
        assert not (tmp_path / "unwritten.json").exists()

    def test_an_option_geocomp_sets_is_refused_naming_the_configuration(
        self, geocomp_provider, tmp_path, monkeypatch, network_document
    ):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as refused:
            self._stop(
                tmp_path, monkeypatch, network_document, {"dnaadjust": ["--max-iterations", "3"]}
            )
        assert "--max-iterations" in str(refused.value)

    def test_the_edited_input_runs_and_the_solution_says_it_was_edited(
        self, geocomp_provider, tmp_path, monkeypatch, network_document
    ):
        from qgis.core import QgsApplication, QgsProcessingContext

        from geocomp.algorithms.engines import dynadjust_run_prepared
        from geocomp.engines.dynadjust.engine import MANIFEST

        job = Path(self._stop(tmp_path, monkeypatch, network_document)["OUTPUT_WORK_DIR"])
        manifest = json.loads((job / MANIFEST).read_text(encoding="utf-8"))
        measurements = job / manifest["measurement_file"]
        edited = measurements.read_text(encoding="utf-8") + "<!-- edited -->\n"
        measurements.write_text(edited, encoding="utf-8")

        engine = _RunsWhatWasPrepared()
        monkeypatch.setattr(dynadjust_run_prepared, "dynadjust_engine", lambda directory=None: engine)
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_run_prepared"
        ).create({})
        results, ok = algorithm.run(
            {"PREPARED": str(job), "OUTPUT_SOLUTION": str(tmp_path / "solution.json")},
            QgsProcessingContext(),
            _feedback(),
            catchExceptions=False,
        )
        assert ok
        assert engine.ran is not None and engine.ran.work_dir == job
        assert results["EDITED_INPUTS"] == measurements.name
        recorded = json.loads((tmp_path / "solution.json").read_text(encoding="utf-8"))
        parameters = recorded["provenance"]["parameters"]
        assert parameters["resumed"] is True
        assert parameters["edited_inputs"] == [measurements.name]
        assert job.is_dir()  # the user's folder, never removed

    def _run_prepared(self, tmp_path, monkeypatch, job):
        from qgis.core import QgsApplication, QgsProcessingContext

        from geocomp.algorithms.engines import dynadjust_run_prepared

        engine = _RunsWhatWasPrepared()
        monkeypatch.setattr(dynadjust_run_prepared, "dynadjust_engine", lambda directory=None: engine)
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_run_prepared"
        ).create({})
        feedback = _feedback()
        _results, ok = algorithm.run(
            {"PREPARED": str(job), "OUTPUT_SOLUTION": str(tmp_path / "solution.json")},
            QgsProcessingContext(),
            feedback,
            catchExceptions=False,
        )
        assert ok
        return engine, feedback

    def test_a_measurement_flagged_ignore_is_said_to_be_set_aside(
        self, geocomp_provider, tmp_path, monkeypatch, network_document
    ):
        """P12c-22: the edit a user most wants. The measurement's observations
        are set aside in what the result is read back against."""
        from geocomp.engines.dynadjust.engine import MANIFEST

        job = Path(self._stop(tmp_path, monkeypatch, network_document)["OUTPUT_WORK_DIR"])
        manifest = json.loads((job / MANIFEST).read_text(encoding="utf-8"))
        measurements = job / manifest["measurement_file"]
        text = measurements.read_text(encoding="utf-8")
        measurements.write_text(text.replace("<Ignore />", "<Ignore>*</Ignore>", 1), encoding="utf-8")

        engine, feedback = self._run_prepared(tmp_path, monkeypatch, job)
        held = manifest["elements"][0]
        assert engine.ran.ignored == tuple(held)
        assert any(all(identifier in info for identifier in held) for info in feedback.infos)
        excluded = engine.ran.adjusted_network.observations
        assert all(not excluded[identifier].is_active for identifier in held)

    def test_a_measurement_removed_by_hand_is_refused_before_anything_runs(
        self, geocomp_provider, tmp_path, monkeypatch, network_document
    ):
        from qgis.core import QgsProcessingException

        from geocomp.engines.dynadjust.engine import MANIFEST

        job = Path(self._stop(tmp_path, monkeypatch, network_document)["OUTPUT_WORK_DIR"])
        manifest = json.loads((job / MANIFEST).read_text(encoding="utf-8"))
        measurements = job / manifest["measurement_file"]
        text = measurements.read_text(encoding="utf-8")
        first = text.index("<DnaMeasurement>")
        second = text.index("<DnaMeasurement>", first + 1)
        measurements.write_text(text[:first] + text[second:], encoding="utf-8")

        with pytest.raises(QgsProcessingException) as refused:
            self._run_prepared(tmp_path, monkeypatch, job)
        assert "Ignore" in str(refused.value)
        assert measurements.name in str(refused.value)

    def test_a_folder_nothing_prepared_is_refused(self, geocomp_provider, tmp_path):
        from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingException

        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_run_prepared"
        ).create({})
        with pytest.raises(QgsProcessingException) as refused:
            algorithm.run(
                {"PREPARED": str(tmp_path)},
                QgsProcessingContext(),
                _feedback(),
                catchExceptions=False,
            )
        assert "Stop after writing the input" in str(refused.value)
