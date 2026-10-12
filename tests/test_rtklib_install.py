# SPDX-License-Identifier: GPL-2.0-or-later
"""RTKLIB installations use verified prebuilt programs on every supported OS."""

from __future__ import annotations

import hashlib
import io
import zipfile

import pytest

from geocomp.core.errors import DataError
from geocomp.engines.manager import PINNED, EngineRelease, install, installed, releases_for


def test_every_rtklib_download_is_a_prebuilt_program():
    releases = [release for release in PINNED if release.engine == "rtklib"]
    assert {release.platform for release in releases} == {
        "linux-x86_64", "windows-x86_64", "macos-arm64", "macos-x86_64",
    }
    for release in releases:
        assert release.url.endswith(".zip")
        assert "rnx2rtkp-" in release.url
        assert release.members == (("rnx2rtkp.exe",) if release.platform.startswith("windows-")
                                   else ("rnx2rtkp",))
    assert releases_for("rtklib", "linux-arm64") == ()


def test_binary_install_requires_no_build_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("rnx2rtkp", b"\x7fELFprebuilt-program")
    data = payload.getvalue()
    release = EngineRelease(
        engine="rtklib", version="2.5.1", platform="linux-x86_64", url="https://example.org/rnx2rtkp.zip",
        sha256=hashlib.sha256(data).hexdigest(), members=("rnx2rtkp",),
    )
    root = tmp_path / "profile"
    directory = install(release, root=root, fetch=lambda url, path: path.write_bytes(data))
    assert (directory / "rnx2rtkp").read_bytes() == b"\x7fELFprebuilt-program"
    assert (directory / "RTKLIB-license.txt").is_file()
    assert installed("rtklib", root).directory == directory.resolve()


def test_source_archive_is_rejected_instead_of_compiled(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("src/main.c", "int main(void) { return 0; }")
        archive.writestr("makefile", "all:\n\tcc src/main.c -o rnx2rtkp\n")
    data = payload.getvalue()
    release = EngineRelease(
        engine="rtklib", version="2.5.1", platform="linux-x86_64", url="https://example.org/source.zip",
        sha256=hashlib.sha256(data).hexdigest(), members=("rnx2rtkp",),
    )
    root = tmp_path / "profile"
    with pytest.raises(DataError) as raised:
        install(release, root=root, fetch=lambda url, path: path.write_bytes(data))
    assert raised.value.code == "data.engine_archive_missing_programs"
    assert installed("rtklib", root) is None
