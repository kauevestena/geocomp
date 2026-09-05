# SPDX-License-Identifier: GPL-2.0-or-later
"""The specifications must stay internally consistent.

``specs/20-testing-and-validation.md`` section 2 lists these as build-breaking
checks. They were run by hand once, when the specification set was written; a
one-off audit decays, so they are tests.

The point is not tidiness. Traceability is the mechanism by which a requirement
from the research project cannot be quietly dropped: if every requirement must
appear in exactly one roadmap phase, then adding one without planning it, or
deleting a phase that owned some, fails the build.
"""

from __future__ import annotations

import re
from collections import Counter

from tests.conftest import SPECS_DIR

REQUIREMENT_ROW = re.compile(r"^\| ((?:FR|NFR)-\d+)", re.MULTILINE)
REQUIREMENT_ANY = re.compile(r"(?:FR|NFR)-\d+")
PHASE_CLOSES = re.compile(r"\*\*Closes\.\*\*(.*?)\n\n", re.DOTALL)
RELATIVE_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)#]+)(?:#[^)]*)?\)")


def _declared_requirements() -> set[str]:
    text = (SPECS_DIR / "02-requirements.md").read_text(encoding="utf-8")
    return set(REQUIREMENT_ROW.findall(text))


def _phase_assignments() -> list[str]:
    text = (SPECS_DIR / "ROADMAP.md").read_text(encoding="utf-8")
    return [rid for block in PHASE_CLOSES.findall(text) for rid in REQUIREMENT_ANY.findall(block)]


def test_requirements_are_declared():
    """Guards the parser: a regex that silently matches nothing would make every
    other check in this file pass vacuously."""
    assert len(_declared_requirements()) > 100


def test_every_requirement_is_planned_into_exactly_one_phase():
    declared = _declared_requirements()
    assigned = _phase_assignments()
    counts = Counter(assigned)

    unplanned = sorted(declared - set(assigned))
    duplicated = sorted(rid for rid, count in counts.items() if count > 1)
    phantom = sorted(set(assigned) - declared)

    assert not unplanned, (
        "These requirements exist but no roadmap phase closes them:\n" + "\n".join(unplanned)
    )
    assert not duplicated, (
        "These requirements are claimed by more than one phase, so ownership is ambiguous:\n"
        + "\n".join(duplicated)
    )
    assert not phantom, (
        "The roadmap closes requirements that are not declared:\n" + "\n".join(phantom)
    )


def test_every_requirement_carries_a_source():
    """Each row must cite an objective or a section of the research project, or
    be marked derived with its reason -- otherwise it is unattributable scope."""
    text = (SPECS_DIR / "02-requirements.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| ((?:FR|NFR)-\d+) \| (.+?) \| (.+?) \|\s*$", text, re.MULTILINE)
    assert len(rows) == len(_declared_requirements()), "a requirement row is malformed"
    for rid, _requirement, source in rows:
        assert source.strip(), f"{rid} has an empty Source column"


def test_every_requirement_is_referenced_by_a_specification():
    """A requirement no document implements is a gap between plan and design."""
    corpus = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SPECS_DIR.rglob("*.md"))
        if path.name != "02-requirements.md"
    )
    orphans = sorted(rid for rid in _declared_requirements() if rid not in corpus)
    assert not orphans, (
        "These requirements appear nowhere outside the requirement list:\n" + "\n".join(orphans)
    )


def test_all_relative_links_between_documents_resolve():
    broken: list[str] = []
    checked = 0
    for path in sorted(SPECS_DIR.rglob("*.md")):
        for target in RELATIVE_LINK.findall(path.read_text(encoding="utf-8")):
            checked += 1
            if not (path.parent / target.strip()).resolve().exists():
                broken.append(f"{path.relative_to(SPECS_DIR)} -> {target}")
    assert checked > 200, "link regex matched suspiciously few links"
    assert not broken, "Broken relative links:\n" + "\n".join(broken)


def test_every_specification_declares_a_status():
    """specs/README.md requires a status line so a reader knows whether a
    document has been reviewed."""
    missing: list[str] = []
    for path in sorted(SPECS_DIR.glob("*.md")):
        if path.name in ("README.md", "ROADMAP.md", "traceability.md"):
            continue
        head = path.read_text(encoding="utf-8")[:600]
        if "**Status:**" not in head:
            missing.append(path.name)
    assert not missing, "Specifications without a status line:\n" + "\n".join(missing)


def test_every_adr_is_listed_in_the_adr_index():
    index = (SPECS_DIR / "adr" / "README.md").read_text(encoding="utf-8")
    missing = [
        path.name
        for path in sorted((SPECS_DIR / "adr").glob("*.md"))
        if path.name != "README.md" and path.name not in index
    ]
    assert not missing, "ADRs missing from adr/README.md:\n" + "\n".join(missing)


def test_the_storage_schema_matches_the_specification():
    """``specs/17`` section 2 lists the tables; the code declares them.

    Two lists of table names in two files drift the moment one is edited
    alone, and the drift is invisible: the code still runs and the spec still
    reads correctly. Phase P5 added this when the schema arrived.

    ``gc_cluster_member`` is deliberately absent from the code. The spec pairs
    it with ``gc_cluster``, but a cluster's membership is already carried by
    ``gc_observation.cluster_id`` and its ordering by ``cluster_index`` -- a
    separate membership table would be a second place for the same fact, and
    two places for one fact is how they come to disagree.
    """
    from geocomp.io.store import table_names

    spec = (SPECS_DIR / "17-persistence-and-interoperability.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"`(gc_[a-z_]+)`", spec))
    declared = set(table_names())

    undocumented = sorted(declared - documented)
    assert not undocumented, (
        "these tables exist in the code but are not in specs/17 section 2: "
        f"{undocumented}"
    )

    unimplemented = sorted(documented - declared - {"gc_cluster_member"})
    assert not unimplemented, (
        "specs/17 section 2 lists these tables and the code does not declare them: "
        f"{unimplemented}"
    )
