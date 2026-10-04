# SPDX-License-Identifier: GPL-2.0-or-later
"""An engine that runs out of time says so (FR-304; P12c-11).

``specs/07`` section 7 and ``specs/08`` section 9 both require a timeout to be
reported with the elapsed time and the configured limit, the working directory
retained. Until P12c-11 neither adapter looked at ``EngineRun.timed_out``: a
killed ``rnx2rtkp`` was "stopped with exit code -9", and a killed DynAdjust
stage the same, which sends a user looking for something wrong with their data
when what ran out was the time.

The process handling -- that a timeout is detected and the group killed -- is
``tests/test_engines.py``'s. Here ``run_process`` is replaced by one that
returns the run a timeout produces, so no engine is needed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from geocomp.core.errors import ComputationError, EngineError
from geocomp.engines.base import EngineRun, EngineVersion
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

DATA = Path(__file__).parent / "data"


def _killed(command, *, work_dir, program="", timeout=0.0, **_ignored) -> EngineRun:
    """What ``run_process`` returns for a run it had to kill."""
    return EngineRun(
        program=program,
        command=tuple(command),
        exit_code=-9,
        stdout="",
        stderr="processing : 2005/04/02 03:12:30.0 Q=0\n",
        seconds=timeout + 0.4,
        work_dir=work_dir,
        timed_out=True,
    )


def _failed(command, *, work_dir, program="", **_ignored) -> EngineRun:
    return EngineRun(
        program=program,
        command=tuple(command),
        exit_code=1,
        stdout="",
        stderr="- Error: station BM12 has no coordinates (line 14)",
        seconds=0.2,
        work_dir=work_dir,
    )


class TestRtklib:
    @pytest.fixture
    def job(self):
        from geocomp.engines.rtklib import RtklibJob

        scan = scan_folder(DATA / "rtklib")
        pair = next(group for group in overlapping_groups(scan.sessions) if len(group) == 2)
        base, rover = sorted(pair, key=lambda session: session.station_id)
        return RtklibJob(rover=rover, base=base, timeout=45.0)

    @pytest.fixture
    def engine(self, monkeypatch, tmp_path):
        from geocomp.engines.rtklib import RtklibEngine
        from geocomp.engines.rtklib import engine as module

        monkeypatch.setattr(module, "run_process", _killed)
        engine = RtklibEngine()
        engine._version = EngineVersion(
            name="RTKLIB-EX", version="2.5.1", path=tmp_path / "rnx2rtkp"
        )
        return engine

    def test_it_is_reported_as_a_timeout(self, engine, job, tmp_path):
        with pytest.raises(EngineError) as raised:
            engine.run(job, work_dir=tmp_path / "run")
        assert raised.value.code == "engine.rtklib_timed_out"

    def test_with_how_long_it_ran_and_the_limit(self, engine, job, tmp_path):
        with pytest.raises(EngineError) as raised:
            engine.run(job, work_dir=tmp_path / "run")
        context = raised.value.context
        assert context["limit"] == "45"
        assert context["elapsed"] == "45"
        assert "exit_code" not in context

    def test_and_where_its_files_are(self, engine, job, tmp_path):
        with pytest.raises(EngineError) as raised:
            engine.run(job, work_dir=tmp_path / "run")
        work_dir = Path(raised.value.context["work_dir"])
        assert work_dir == tmp_path / "run"
        assert (work_dir / "rnx2rtkp.conf").is_file()


class TestDynAdjust:
    @pytest.fixture
    def prepared(self, tmp_path):
        from geocomp.core.models.epoch import Epoch
        from geocomp.engines.dynadjust.engine import DynAdjustEngine, DynAdjustJob
        from geocomp.engines.dynadjust.read_dynaml import read_dynaml

        network = read_dynaml(
            DATA / "dynadjust" / "sample-stn.xml", DATA / "dynadjust" / "sample-msr.xml"
        ).network
        network.epoch = Epoch.from_decimal_year(2020.0)
        return DynAdjustEngine().prepare(
            DynAdjustJob(network=network, name="run", target_frame="GDA2020"), tmp_path
        )

    @pytest.fixture
    def engine(self, monkeypatch):
        from geocomp.engines.dynadjust import engine as module

        engine = module.DynAdjustEngine()
        monkeypatch.setattr(engine, "detect", lambda: None)
        monkeypatch.setattr(engine, "locate", lambda program: Path("/opt/dynadjust") / program)
        return engine

    def test_a_stage_that_runs_out_of_time_says_so(self, engine, prepared, monkeypatch):
        from geocomp.engines.dynadjust import engine as module

        monkeypatch.setattr(module, "run_process", _killed)
        with pytest.raises(ComputationError) as raised:
            engine.run(prepared, timeout=1800.0)
        error = raised.value
        assert error.code == "computation.dynadjust_stage_timed_out"
        assert error.context["program"] == "dnaimport"
        assert error.context["limit"] == "1800"
        assert error.context["elapsed"] == "1800"
        assert error.context["work_dir"] == str(prepared.work_dir)
        assert "exit_code" not in error.context

    def test_a_failed_stage_names_its_command_and_working_directory(
        self, engine, prepared, monkeypatch
    ):
        """``specs/07`` section 7: exit code, full command line and working
        directory, for a stage that says nothing about why."""
        from geocomp.engines.dynadjust import engine as module

        monkeypatch.setattr(module, "run_process", _failed)
        with pytest.raises(ComputationError) as raised:
            engine.run(prepared)
        error = raised.value
        assert error.code == "computation.dynadjust_stage_failed"
        assert error.context["command"].startswith(str(Path("/opt/dynadjust") / "dnaimport"))
        assert error.context["work_dir"] == str(prepared.work_dir)
