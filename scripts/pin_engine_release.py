#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Download an engine release, hash it, and print the row to pin (ADR-0003).

``geocomp.engines.manager.PINNED`` holds a SHA-256 for every engine build
GeoComp will install. The digest must be computed from an archive somebody
actually fetched and checked -- not copied from a checksum published beside the
download, which proves only that the transfer was not corrupted, and certainly
not invented.

Run this on a machine that can reach the upstream releases page::

    python3 scripts/pin_engine_release.py \\
        --engine dynadjust --platform linux-x86_64 --version 1.4.0 \\
        --url https://github.com/GeoscienceAustralia/DynAdjust/releases/download/v1.4.0/dynadjust-linux-openblas-static.zip

It prints an :class:`~geocomp.engines.manager.EngineRelease` to paste into
``PINNED``, having listed the archive's contents so the ``members`` tuple states
what was really in it rather than what someone expected.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BLOCK = 1024 * 1024


def download(url: str, destination: Path) -> None:
    print(f"fetching {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as response, destination.open("wb") as handle:
        while block := response.read(BLOCK):
            handle.write(block)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(BLOCK):
            hasher.update(block)
    return hasher.hexdigest()


#: Suffixes that are never a program. ``.dll`` and ``.so`` matter as much as the
#: documentation ones: DynAdjust's Windows archive ships ``dnaadjust.dll`` beside
#: ``adjust.exe``, and listing the library as a member would have ``install``
#: check for the wrong file.
NOT_PROGRAMS = {".txt", ".md", ".xsd", ".json", ".pdf", ".dll", ".so", ".dylib", ".lib", ".a"}


def executables(path: Path) -> list[str]:
    """Archive members that look like programs rather than documentation.

    A Unix build names its programs without a suffix; a Windows one gives every
    program ``.exe``. An earlier version of this excluded any name containing a
    dot, which is correct for the first case and silently returns **nothing**
    for the second -- so the two Windows archives were pinned with an empty
    ``members`` tuple, and ``install`` would have verified that an archive
    contained none of the files it was asked to check.
    """
    with zipfile.ZipFile(path) as archive:
        names = [Path(info.filename).name for info in archive.infolist() if not info.is_dir()]
    return sorted(
        {
            name
            for name in names
            if Path(name).suffix.lower() not in NOT_PROGRAMS
            and (Path(name).suffix.lower() == ".exe" or "." not in name)
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--platform", required=True, help="e.g. linux-x86_64, macos-arm64, windows-x86_64")
    parser.add_argument("--version", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--archive", help="use a local archive instead of downloading")
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory() as directory:
        path = Path(arguments.archive) if arguments.archive else Path(directory) / "engine.zip"
        if not arguments.archive:
            download(arguments.url, path)

        found = digest(path)
        members = executables(path)
        size = path.stat().st_size

    print(f"\n# {size / 1048576:.1f} MB, {len(members)} programs", file=sys.stderr)
    print("    EngineRelease(")
    print(f'        engine="{arguments.engine}",')
    print(f'        version="{arguments.version}",')
    print(f'        platform="{arguments.platform}",')
    print(f'        url="{arguments.url}",')
    print(f'        sha256="{found}",')
    print(f"        members={tuple(members)!r},")
    print("    ),")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
