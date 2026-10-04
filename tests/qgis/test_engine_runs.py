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
