# SPDX-License-Identifier: GPL-2.0-or-later
"""The copy of an engine that ships inside the plugin (ADR-0009).

Tier 1: the search order, the executable bit a ZIP library drops, and the build
refusing to carry a program without its licence.
"""

from __future__ import annotations

import os
import stat
import sys
import zipfile
from pathlib import Path

import pytest

from geocomp.engines import manager
from geocomp.engines.base import discover
from scripts import build

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="the executable bit is a POSIX notion")


def _plant(plugin: Path, engine: str = "rtklib", name: str = "rnx2rtkp", mode: int = 0o644) -> Path:
    directory = plugin / "resources" / "engines" / manager.current_platform() / engine
    directory.mkdir(parents=True)
    program = directory / name
    program.write_bytes(b"#!/bin/sh\nexit 0\n")
    program.chmod(mode)
    return program


class TestWhereTheBundledCopyIs:
    def test_a_build_with_none_has_no_directory(self, tmp_path):
        assert manager.bundled_directories("rtklib", tmp_path) == ()

    def test_a_build_with_one_names_its_directory(self, tmp_path):
        program = _plant(tmp_path)
        assert manager.bundled_directories("rtklib", tmp_path) == (program.parent,)

    def test_another_engine_is_not_found_in_it(self, tmp_path):
        _plant(tmp_path)
        assert manager.bundled_directories("dynadjust", tmp_path) == ()

    @posix_only
    def test_a_zip_that_dropped_the_executable_bit_is_put_right(self, tmp_path):
        program = _plant(tmp_path, mode=0o644)
        assert not os.access(program, os.X_OK)
        manager.bundled_directories("rtklib", tmp_path)
        assert os.access(program, os.X_OK)

    @posix_only
    def test_a_read_only_directory_does_not_raise(self, tmp_path):
        program = _plant(tmp_path, mode=0o444)
        program.parent.chmod(0o555)
        try:
            manager.bundled_directories("rtklib", tmp_path)
        finally:
            program.parent.chmod(0o755)


class TestTheSearchOrder:
    def test_the_bundled_copy_is_found_and_says_so(self, tmp_path):
        program = _plant(tmp_path)
        found, source = discover(
            "rnx2rtkp", bundled_directories=manager.bundled_directories("rtklib", tmp_path)
        )
        assert (found, source) == (program, "bundled")

    def test_a_managed_installation_beats_it(self, tmp_path):
        _plant(tmp_path / "plugin")
        managed = tmp_path / "managed"
        managed.mkdir()
        (managed / "rnx2rtkp").write_bytes(b"")
        found, source = discover(
            "rnx2rtkp",
            extra_directories=(managed,),
            bundled_directories=manager.bundled_directories("rtklib", tmp_path / "plugin"),
        )
        assert (found, source) == (managed / "rnx2rtkp", "managed")

    def test_a_configured_path_beats_it(self, tmp_path):
        _plant(tmp_path / "plugin")
        mine = tmp_path / "mine"
        mine.write_bytes(b"")
        found, source = discover(
            "rnx2rtkp",
            configured=mine,
            bundled_directories=manager.bundled_directories("rtklib", tmp_path / "plugin"),
        )
        assert (found, source) == (mine, "configured")

    def test_it_beats_the_system_path(self, tmp_path, monkeypatch):
        program = _plant(tmp_path / "plugin")
        system = tmp_path / "system"
        system.mkdir()
        other = system / "rnx2rtkp"
        other.write_bytes(b"")
        other.chmod(0o755)
        monkeypatch.setenv("PATH", str(system))
        found, source = discover(
            "rnx2rtkp",
            bundled_directories=manager.bundled_directories("rtklib", tmp_path / "plugin"),
        )
        assert (found, source) == (program, "bundled")


class TestTheBuild:
    def _program(self, tmp_path: Path) -> Path:
        program = tmp_path / "rnx2rtkp"
        program.write_bytes(b"\x7fELF not really")
        return program

    def test_it_is_stored_executable_beside_its_licence(self, tmp_path):
        target = tmp_path / "geocomp.zip"
        engine = build.parse_engine(f"rtklib=linux-x86_64:{self._program(tmp_path)}")
        build.write_zip(target, build.collect_files(), [engine])
        build.verify(target)
        with zipfile.ZipFile(target) as archive:
            info = archive.getinfo("geocomp/resources/engines/linux-x86_64/rtklib/rnx2rtkp")
            assert stat.S_IMODE(info.external_attr >> 16) == 0o755
            assert "geocomp/resources/engines/licences/RTKLIB-license.txt" in archive.namelist()

    def test_the_licence_is_the_bsd_notice(self):
        text = (build.PLUGIN_DIR / build.ENGINE_LICENCES["rtklib"]).read_text(encoding="utf-8")
        assert "BSD 2-clause" in text and "T. Takasu" in text

    def test_two_builds_are_byte_identical(self, tmp_path):
        engine = build.parse_engine(f"rtklib=linux-x86_64:{self._program(tmp_path)}")
        files = build.collect_files()
        build.write_zip(tmp_path / "a.zip", files, [engine])
        build.write_zip(tmp_path / "b.zip", files, [engine])
        assert (tmp_path / "a.zip").read_bytes() == (tmp_path / "b.zip").read_bytes()

    def test_an_engine_with_no_recorded_licence_is_refused(self, tmp_path):
        with pytest.raises(build.BuildError, match="no licence"):
            build.parse_engine(f"dynadjust=linux-x86_64:{self._program(tmp_path)}")

    def test_a_missing_program_is_refused(self, tmp_path):
        with pytest.raises(build.BuildError, match="not found"):
            build.parse_engine(f"rtklib=linux-x86_64:{tmp_path / 'absent'}")

    def test_a_malformed_spec_is_refused(self):
        with pytest.raises(build.BuildError, match="NAME=PLATFORM:PATH"):
            build.parse_engine("rtklib")

    def test_a_program_without_its_licence_is_refused(self, tmp_path):
        target = tmp_path / "geocomp.zip"
        files = [f for f in build.collect_files() if f.name != "RTKLIB-license.txt"]
        engine = build.parse_engine(f"rtklib=linux-x86_64:{self._program(tmp_path)}")
        build.write_zip(target, files, [engine])
        with pytest.raises(build.BuildError, match="without its licence"):
            build.verify(target)


REAL_PROGRAM = os.environ.get("GEOCOMP_BUNDLED_RNX2RTKP", "")


@pytest.mark.skipif(
    not REAL_PROGRAM, reason="GEOCOMP_BUNDLED_RNX2RTKP names no built rnx2rtkp to check"
)
class TestARealBuildOnThisSystem:
    """The program a release carries, run the way the plugin runs it, on the OS it was built for.

    The ``build`` workflow sets ``GEOCOMP_BUNDLED_RNX2RTKP`` on each runner to
    the program it has just built. Planted as a ZIP library leaves it -- not
    executable -- under this machine's platform name, it must be found as the
    bundled copy, run, and report the version GeoComp was checked against.
    """

    def test_it_is_found_run_and_recognised(self, tmp_path):
        from geocomp.engines.rtklib.engine import RtklibEngine

        source = Path(REAL_PROGRAM)
        plugin = tmp_path / "plugin"
        directory = plugin / "resources" / "engines" / manager.current_platform() / "rtklib"
        directory.mkdir(parents=True)
        program = directory / source.name
        program.write_bytes(source.read_bytes())
        if sys.platform != "win32":
            program.chmod(0o644)

        engine = RtklibEngine(bundled_directories=manager.bundled_directories("rtklib", plugin))
        path, where = engine.locate()
        assert (path, where) == (program, "bundled")
        version = engine.version()
        assert version is not None, "the bundled program did not run"
        assert version.tested, f"{version.name} {version.version} is not the version checked against"
        assert version.source == "bundled"
