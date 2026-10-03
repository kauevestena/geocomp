# SPDX-License-Identifier: GPL-2.0-or-later
"""What the engine manager records, and how the plugin finds what it installed (specs/21 §4; P12c-6).

``specs/21`` section 4 item 2: the manager downloads, verifies, extracts *and
records the version*. Until P12c-6 it recorded nothing, and nothing looked in
the directory it installed into: an engine it had installed and verified was
invisible to every algorithm. Tier 1, as ``tests/test_engines.py`` is: the
recording and the finding are where an installation becomes usable or not, and
they are the same code on every operating system.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.engines.dynadjust.engine import DynAdjustEngine
from geocomp.engines.manager import (
    MANIFEST,
    PINNED,
    EngineRelease,
    current_platform,
    install,
    install_pinned,
    installed,
    managed_directories,
)


def _release(tmp_path: Path, *, version: str = "1.4.0", nested: str = "dynadjust-linux-static/"):
    archive = tmp_path / f"source-{version}.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for name in ("dnaimport", "dnaadjust"):
            handle.writestr(f"{nested}{name}", b"#!/bin/sh\n")
    payload = archive.read_bytes()
    release = EngineRelease(
        engine="dynadjust",
        version=version,
        platform="linux-x86_64",
        url=f"https://example.org/dynadjust-{version}.zip",
        sha256=hashlib.sha256(payload).hexdigest(),
        members=("dnaimport", "dnaadjust"),
    )
    return release, (lambda url, path: path.write_bytes(payload))


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("linux", "x86_64", "linux-x86_64"),
        ("darwin", "arm64", "macos-arm64"),
        ("win32", "AMD64", "windows-x86_64"),
        # Named, so install_pinned refuses them by name rather than handing them
        # a build for a different processor.
        ("linux", "aarch64", "linux-arm64"),
        ("darwin", "x86_64", "macos-x86_64"),
    ],
)
def test_this_machine_is_named_as_the_pins_name_platforms(monkeypatch, system, machine, expected):
    monkeypatch.setattr("geocomp.engines.manager.sys.platform", system)
    monkeypatch.setattr("geocomp.engines.manager._platform.machine", lambda: machine)
    assert current_platform() == expected


def test_every_pinned_platform_is_one_a_machine_can_be():
    assert {release.platform for release in PINNED} <= {
        "linux-x86_64",
        "macos-arm64",
        "windows-x86_64",
    }


def test_an_install_records_what_it_installed(tmp_path):
    release, fetch = _release(tmp_path)
    root = tmp_path / "engines"
    where = install(release, root=root, fetch=fetch)

    found = installed("dynadjust", root)
    assert found is not None
    assert found.version == "1.4.0"
    assert found.platform == "linux-x86_64"
    assert found.url == release.url
    assert found.sha256 == release.sha256
    assert found.directory == where.resolve()
    assert found.installed.endswith("+00:00")
    # Relative in the file, so a profile that moves keeps its engines.
    stored = json.loads((root / "dynadjust" / MANIFEST).read_text(encoding="utf-8"))
    assert stored["directory"] == "1.4.0/dynadjust-linux-static"


def test_a_profile_that_moves_takes_its_engines_with_it(tmp_path):
    release, fetch = _release(tmp_path)
    install(release, root=tmp_path / "before", fetch=fetch)
    shutil.copytree(tmp_path / "before", tmp_path / "after")
    shutil.rmtree(tmp_path / "before")
    (directory,) = managed_directories("dynadjust", tmp_path / "after")
    assert directory == (tmp_path / "after" / "dynadjust" / "1.4.0" / "dynadjust-linux-static").resolve()


def test_a_later_install_replaces_the_record(tmp_path):
    root = tmp_path / "engines"
    first, fetch_first = _release(tmp_path, version="1.4.0")
    second, fetch_second = _release(tmp_path, version="1.4.1")
    install(first, root=root, fetch=fetch_first)
    install(second, root=root, fetch=fetch_second)
    assert installed("dynadjust", root).version == "1.4.1"


def test_a_failed_install_leaves_the_previous_record(tmp_path):
    """The record is written last, so it only ever names an installation that verified."""
    root = tmp_path / "engines"
    good, fetch = _release(tmp_path)
    install(good, root=root, fetch=fetch)
    tampered = EngineRelease(
        engine="dynadjust",
        version="1.4.1",
        platform="linux-x86_64",
        url="https://example.org/tampered.zip",
        sha256=hashlib.sha256(b"what was vetted").hexdigest(),
        members=("dnaadjust",),
    )
    with pytest.raises(DataError) as caught:
        install(tampered, root=root, fetch=lambda url, path: path.write_bytes(b"not that"))
    assert caught.value.code == "data.engine_archive_digest_mismatch"
    assert installed("dynadjust", root).version == "1.4.0"


def test_nothing_installed_is_no_directories(tmp_path):
    assert installed("dynadjust", tmp_path) is None
    assert managed_directories("dynadjust", tmp_path) == ()


@pytest.mark.parametrize(
    "damage",
    ["not json at all", json.dumps({"engine": "dynadjust"}), json.dumps([1, 2, 3])],
)
def test_a_damaged_record_is_nothing_installed_rather_than_an_error(tmp_path, damage):
    """The user is offered an install, not an error about a file GeoComp wrote."""
    (tmp_path / "dynadjust").mkdir()
    (tmp_path / "dynadjust" / MANIFEST).write_text(damage, encoding="utf-8")
    assert installed("dynadjust", tmp_path) is None


def test_a_record_whose_programs_were_removed_is_nothing_installed(tmp_path):
    release, fetch = _release(tmp_path)
    where = install(release, root=tmp_path / "engines", fetch=fetch)
    shutil.rmtree(where)
    assert managed_directories("dynadjust", tmp_path / "engines") == ()


def test_a_record_naming_a_directory_outside_its_own_is_refused(tmp_path):
    """A record edited to point elsewhere must not make GeoComp run what is there."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    home = tmp_path / "engines" / "dynadjust"
    home.mkdir(parents=True)
    (home / MANIFEST).write_text(
        json.dumps(
            {
                "engine": "dynadjust",
                "version": "1.4.0",
                "platform": "linux-x86_64",
                "url": "https://example.org/x.zip",
                "sha256": "0" * 64,
                "directory": "../../elsewhere",
                "installed": "2026-10-03T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    assert installed("dynadjust", tmp_path / "engines") is None


def test_a_record_for_another_engine_is_not_this_ones(tmp_path):
    release, fetch = _release(tmp_path)
    install(release, root=tmp_path / "engines", fetch=fetch)
    (tmp_path / "engines" / "dynadjust").rename(tmp_path / "engines" / "rtklib")
    assert installed("rtklib", tmp_path / "engines") is None


def test_the_managed_installation_is_found_and_a_configured_one_wins(tmp_path):
    """ADR-0003 rule 4: what the user named, then GeoComp's own, then the path."""
    release, fetch = _release(tmp_path)
    install(release, root=tmp_path / "engines", fetch=fetch)
    managed = managed_directories("dynadjust", tmp_path / "engines")

    found = DynAdjustEngine(extra_directories=managed).locate("dnaimport")
    assert found.parent == managed[0]

    own = tmp_path / "own-build"
    shutil.copytree(managed[0], own)
    found = DynAdjustEngine(configured_directory=own, extra_directories=managed).locate("dnaimport")
    assert found.parent == own


def test_a_platform_without_a_pin_is_refused_by_name_and_readably(tmp_path):
    with pytest.raises(ValidationError) as caught:
        install_pinned("dynadjust", "linux-arm64", root=tmp_path, fetch=lambda url, path: None)
    assert caught.value.code == "validation.engine_release_not_pinned"
    available = caught.value.context["available"]
    assert "dynadjust linux-x86_64" in available
    assert all(isinstance(item, str) for item in available)
