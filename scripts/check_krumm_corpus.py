#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prove that ``tests/data/krumm/`` is GNU Gama's files, unchanged.

``tests/data/krumm/PROVENANCE.md`` claims the directory is a verbatim copy of
``tests/krumm/input/`` from GNU Gama at a named commit. That claim is the whole
basis on which the data is redistributed here -- attribution to a source you
have quietly edited is not attribution -- so it is checked rather than trusted.

Usage::

    python3 scripts/check_krumm_corpus.py                 # clone and compare
    python3 scripts/check_krumm_corpus.py --upstream DIR  # compare against a
                                                          # checkout you have

Exits non-zero and names every file that differs, is missing, or is extra.
``PROVENANCE.md`` is GeoComp's own and is excluded from the comparison; the
upstream ``README.md`` is not, and must match.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDORED = REPO_ROOT / "tests" / "data" / "krumm"

UPSTREAM_URL = "https://github.com/Geo-Linux-Calculations/gnu-gama.git"
#: GNU Gama 2.24. Must equal the commit named in PROVENANCE.md and pinned as
#: GAMA_COMMIT in .github/workflows/reference.yml.
UPSTREAM_COMMIT = "963c3099054594922716786f92119732f12d714e"
UPSTREAM_PATH = "tests/krumm/input"

#: GeoComp's own, not upstream's, so it has no counterpart to compare against.
OURS = {"PROVENANCE.md"}


def digests(root: Path) -> dict[str, str]:
    """Every file under *root*, by relative path, with its SHA-256."""
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in OURS or "__pycache__" in relative:
            continue
        found[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def fetch(destination: Path) -> Path:
    """Sparse-clone just the corpus at the pinned commit."""
    run = lambda *args: subprocess.run(args, check=True, capture_output=True)  # noqa: E731
    run("git", "clone", "--filter=blob:none", "--no-checkout", UPSTREAM_URL, str(destination))
    run("git", "-C", str(destination), "sparse-checkout", "init", "--cone")
    run("git", "-C", str(destination), "sparse-checkout", "set", UPSTREAM_PATH)
    run("git", "-C", str(destination), "checkout", "--detach", UPSTREAM_COMMIT)
    return destination / UPSTREAM_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upstream",
        type=Path,
        help="an existing gnu-gama checkout's tests/krumm/input, instead of cloning",
    )
    arguments = parser.parse_args()

    if arguments.upstream:
        upstream_root = arguments.upstream
        if not (upstream_root / "2D").is_dir():
            print(f"not a Krumm corpus: {upstream_root}", file=sys.stderr)
            return 2
        return compare(upstream_root)

    with tempfile.TemporaryDirectory() as workspace:
        return compare(fetch(Path(workspace) / "gnu-gama"))


def compare(upstream_root: Path) -> int:
    ours, theirs = digests(VENDORED), digests(upstream_root)

    missing = sorted(set(theirs) - set(ours))
    extra = sorted(set(ours) - set(theirs))
    changed = sorted(name for name in set(ours) & set(theirs) if ours[name] != theirs[name])

    for name in missing:
        print(f"MISSING  {name}  (upstream has it, tests/data/krumm does not)")
    for name in extra:
        print(f"EXTRA    {name}  (not upstream's, and not listed as GeoComp's)")
    for name in changed:
        print(f"CHANGED  {name}")

    if missing or extra or changed:
        print(
            f"\n{len(missing) + len(extra) + len(changed)} file(s) differ from GNU Gama "
            f"at {UPSTREAM_COMMIT[:7]}.\n"
            "PROVENANCE.md claims this directory is a verbatim copy. Either restore the "
            "file, or -- if upstream itself moved -- update the pin here, in "
            "PROVENANCE.md and in .github/workflows/reference.yml together, and say in "
            "the commit message what changed.",
            file=sys.stderr,
        )
        return 1

    print(f"{len(ours)} files identical to GNU Gama at {UPSTREAM_COMMIT[:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
