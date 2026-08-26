# SPDX-License-Identifier: GPL-2.0-or-later
"""NFR-009: every source file carries its licence identifier.

``specs/21-packaging-ci-release-licensing.md`` section 7.3. A file without one
is ambiguous the moment it is copied out of the repository, which for a
GPL project is precisely the situation the licence exists to govern.
"""

from __future__ import annotations

from tests.conftest import REPO_ROOT, python_sources

EXPECTED = "SPDX-License-Identifier: GPL-2.0-or-later"
ROOTS = ("geocomp", "tests", "scripts")


def test_every_python_source_declares_its_licence():
    missing: list[str] = []
    for root in ROOTS:
        directory = REPO_ROOT / root
        if not directory.is_dir():
            continue
        for path in python_sources(directory):
            head = path.read_text(encoding="utf-8")[:400]
            if EXPECTED not in head:
                missing.append(str(path.relative_to(REPO_ROOT)))
    assert not missing, (
        f"These files lack '{EXPECTED}' in their first lines:\n" + "\n".join(missing)
    )
