# SPDX-License-Identifier: GPL-2.0-or-later
"""An engine's failure, packaged for its developers (FR-955; P12c-48).

Two halves. Every run an engine makes leaves its command, how it ended and its
whole output in its working folder -- until P12c-48 the folder held the inputs
and outputs only, and ``EngineRun.to_dict`` said the full logs were there when
nothing wrote them. And :func:`package_problem` puts that folder in one zip
with a README the engine's developers can read. The "engines" here are this
interpreter, named as DynAdjust's and RTKLIB's programs are, so the test needs
neither.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

from geocomp.core.errors import ValidationError
from geocomp.engines.base import RUN_RECORD, run_process
from geocomp.engines.report import README, UPSTREAM, package_problem
from tests.conftest import requires_dynadjust

FAILING = (
    "import sys; print('reading the station file'); "
    "print('line 12: no such station', file=sys.stderr); sys.exit(3)"
)
SUCCEEDING = "print('done')"


def _run(work_dir: Path, program: str, code: str, **kwargs):
    return run_process([sys.executable, "-c", code], work_dir=work_dir, program=program, **kwargs)


def _records(work_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (work_dir / RUN_RECORD).read_text(encoding="utf-8").splitlines()]


class TestEveryRunLeavesItsRecord:
    def test_the_whole_output_and_the_command_are_in_the_folder(self, tmp_path):
        run = _run(tmp_path, "dnaimport", FAILING)
        assert run.exit_code == 3
        out, err = (tmp_path / f"geocomp-dnaimport.{stream}.txt" for stream in ("stdout", "stderr"))
        assert out.read_text(encoding="utf-8") == "reading the station file\n"
        assert err.read_text(encoding="utf-8") == "line 12: no such station\n"
        (record,) = _records(tmp_path)
        assert record["program"] == "dnaimport"
        assert record["command"] == [sys.executable, "-c", FAILING]
        assert record["exit_code"] == 3 and record["timed_out"] is False

    def test_the_output_is_whole_where_the_record_keeps_its_ends(self, tmp_path):
        """Provenance keeps the first and last forty lines; the folder keeps all of them."""
        code = "for i in range(500): print(f'line {i}')"
        run = _run(tmp_path, "dnaadjust", code)
        assert "line 250" not in run.to_dict()["stdout"]
        assert "line 250\n" in (tmp_path / "geocomp-dnaadjust.stdout.txt").read_text(encoding="utf-8")

    def test_each_run_adds_a_line(self, tmp_path):
        _run(tmp_path, "dnaimport", SUCCEEDING)
        _run(tmp_path, "dnaadjust", FAILING)
        assert [record["program"] for record in _records(tmp_path)] == ["dnaimport", "dnaadjust"]

    def test_a_version_probe_leaves_nothing_behind(self, tmp_path):
        """Probes run in QGIS's working directory or beside a bundled program, where a record is litter.

        As first written, every detection of DynAdjust left three files wherever QGIS was
        started -- and a test run left them in the repository, where they were committed.
        """
        _run(tmp_path, "dnaadjust", SUCCEEDING, record=False)
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.skipif(sys.platform == "win32", reason="the stand-in programs are shell scripts")
    def test_detecting_either_engine_writes_nowhere(self, tmp_path, monkeypatch):
        from geocomp.engines.dynadjust.engine import DynAdjustEngine
        from geocomp.engines.rtklib.engine import RtklibEngine

        programs = tmp_path / "bin"
        programs.mkdir()
        banners = {"dnaadjust": "+ Version:      1.4.0, Release", "rnx2rtkp": "rnx2rtkp ver.2.4.3 b34"}
        for name, banner in banners.items():
            script = programs / name
            script.write_text(f"#!/bin/sh\necho '{banner}'\n", encoding="utf-8")
            script.chmod(0o755)
        caller = tmp_path / "qgis-started-here"
        caller.mkdir()
        monkeypatch.chdir(caller)
        DynAdjustEngine(configured_directory=programs).detect()
        RtklibEngine(configured=programs / "rnx2rtkp").version()
        assert list(caller.iterdir()) == []
        assert sorted(path.name for path in programs.iterdir()) == ["dnaadjust", "rnx2rtkp"]

    def test_the_environment_is_not_written_down(self, tmp_path):
        """NFR-010: an environment passed to an engine is the caller's, and may hold a secret."""
        _run(tmp_path, "rnx2rtkp", SUCCEEDING, environment={"SOME_TOKEN": "s3cr3t"})
        for path in tmp_path.iterdir():
            assert "s3cr3t" not in path.read_text(encoding="utf-8"), path.name


class TestThePackage:
    def test_it_holds_the_folder_and_a_readme_for_the_developers(self, tmp_path):
        work = tmp_path / "job"
        work.mkdir()
        (work / "job-stn.xml").write_text("<stations/>", encoding="utf-8")
        (work / "sub").mkdir()
        (work / "sub" / "extra.txt").write_text("x", encoding="utf-8")
        _run(work, "dnaimport", SUCCEEDING)
        _run(work, "dnaadjust", FAILING)
        package = package_problem(work, tmp_path / "report.zip", geocomp="0.1.0", qgis="3.40")
        assert package.engine == "DynAdjust" and package.runs == 2 and package.failed == ("dnaadjust",)
        with zipfile.ZipFile(package.path) as archive:
            names = set(archive.namelist())
            readme = archive.read(README).decode("utf-8")
        assert {"job-stn.xml", "sub/extra.txt", RUN_RECORD, "geocomp-dnaadjust.stderr.txt"} <= names
        assert "Engine: DynAdjust" in readme and UPSTREAM["DynAdjust"] in readme
        assert "GeoComp 0.1.0 (QGIS 3.40)" in readme
        assert readme.index("dnaimport") < readme.index("exit code 3")
        assert "Remove what may not be shared" in readme

    def test_a_package_written_inside_the_folder_does_not_hold_itself(self, tmp_path):
        _run(tmp_path, "rnx2rtkp", FAILING)
        package = package_problem(tmp_path, tmp_path / "report.zip")
        assert package.engine == "RTKLIB"
        with zipfile.ZipFile(package.path) as archive:
            assert "report.zip" not in archive.namelist()

    def test_a_run_stopped_at_its_limit_is_said_so(self, tmp_path):
        _run(tmp_path, "dnaadjust", "import time; time.sleep(5)", timeout=0.5)
        package = package_problem(tmp_path, tmp_path / "report.zip")
        with zipfile.ZipFile(package.path) as archive:
            assert "stopped at its time limit" in archive.read(README).decode("utf-8")
        assert package.failed == ("dnaadjust",)

    def test_a_program_it_does_not_know_is_not_given_a_name(self, tmp_path):
        _run(tmp_path, "something-else", SUCCEEDING)
        package = package_problem(tmp_path, tmp_path / "report.zip")
        assert package.engine == ""
        with zipfile.ZipFile(package.path) as archive:
            assert "Engine: not recognised" in archive.read(README).decode("utf-8")

    def test_a_folder_no_engine_ran_in_is_refused(self, tmp_path):
        with pytest.raises(ValidationError) as caught:
            package_problem(tmp_path, tmp_path / "report.zip")
        assert caught.value.code == "validation.engine_run_record_missing"
        assert not (tmp_path / "report.zip").exists()


@requires_dynadjust
class TestARealDynAdjustFailure:
    """DynAdjust itself refusing a station file, and the folder it leaves packaged for its developers."""

    def test_the_package_holds_what_reproduces_it(self, tmp_path):
        from geocomp.core.errors import GeoCompError
        from geocomp.core.models import Epoch
        from geocomp.engines.dynadjust.engine import DynAdjustEngine, DynAdjustJob
        from geocomp.engines.dynadjust.read_dynaml import read_dynaml

        data = Path(__file__).parent / "data" / "dynadjust"
        network = read_dynaml(data / "sample-stn.xml", data / "sample-msr.xml").network
        engine = DynAdjustEngine()
        prepared = engine.prepare(
            DynAdjustJob(
                network=network,
                name="broken",
                target_frame="GDA2020",
                target_epoch=Epoch.from_decimal_year(2020.0),
            ),
            tmp_path / "job",
        )
        prepared.station_file.write_text("<?xml version='1.0'?><DnaXmlFormat><DnaStation>", encoding="utf-8")
        with pytest.raises(GeoCompError):
            engine.run(prepared)

        package = package_problem(prepared.work_dir, tmp_path / "report.zip", geocomp="test", qgis="none")
        assert package.engine == "DynAdjust"
        assert package.failed, "the failed stage is recorded as failed"
        with zipfile.ZipFile(package.path) as archive:
            names = set(archive.namelist())
            readme = archive.read(README).decode("utf-8")
        assert prepared.station_file.name in names and prepared.measurement_file.name in names
        assert f"geocomp-{package.failed[0]}.stdout.txt" in names
        assert "dnaimport" in readme and "Engine: DynAdjust -- " in readme
