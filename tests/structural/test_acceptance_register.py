# SPDX-License-Identifier: GPL-2.0-or-later
"""The acceptance register covers every criterion, and cites what exists (specs/20 section 10).

``specs/20`` criterion 8: *every acceptance criterion in every other
specification document has a corresponding automated test, or a documented
reason why it must be manual.* Until P12c that was a sentence nobody could
check, and the audit that wrote the register found criteria recorded as met
whose tests asserted something nearby. This holds the register to the
documents: one row per criterion, a test behind every **met**, a reason
behind everything else, and no citation of a test that does not exist.
"""

from __future__ import annotations

import ast
import re
from functools import cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "specs"
REGISTER = SPECS / "20-testing-and-validation.md"

#: The documents whose criteria the register covers: every specification with
#: an acceptance section except the register's own, whose criteria it covers too.
FIRST, LAST = 5, 21

STATES = {"met", "partly met", "open", "manual"}

#: A row: | 05 | 1 | abridged criterion | **state** | evidence |
ROW = re.compile(
    r"^\| (?P<spec>\d\d) \| (?P<number>\d+) \| (?P<criterion>[^|]+?) \| "
    r"\*\*(?P<state>[a-z ]+)\*\* \| (?P<evidence>.*) \|$"
)

#: A citation: a test file, a workflow or a script, with optional ``::`` parts.
CITATION = re.compile(r"`((?:tests|\.github/workflows|scripts)/[^`\s]+?)`")

#: "As 06.6": the evidence is another row's, which must itself be met.
SAME_AS = re.compile(r"\bAs (\d\d)\.(\d+)\b")


def _criteria(document: Path) -> int:
    """How many numbered criteria the document's acceptance section has."""
    text = document.read_text(encoding="utf-8")
    match = re.search(
        r"^## [0-9.]*\s*Acceptance criteria[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    if match is None:
        return 0
    # Only the section's own numbered list: a later "### State after ..."
    # subsection belongs to the history, not to the criteria.
    body = re.split(r"^### ", match.group(1), maxsplit=1, flags=re.M)[0]
    return len(re.findall(r"^\d+\. ", body, re.M))


def _documents() -> dict[str, int]:
    found = {}
    for number in range(FIRST, LAST + 1):
        (path,) = SPECS.glob(f"{number:02d}-*.md")
        found[f"{number:02d}"] = _criteria(path)
    return found


@cache
def _rows() -> list[dict[str, str]]:
    text = REGISTER.read_text(encoding="utf-8")
    section = text.split("## 10. Acceptance register", 1)[1]
    return [match.groupdict() for line in section.splitlines() if (match := ROW.match(line))]


def _key(row: dict[str, str]) -> tuple[str, int]:
    return row["spec"], int(row["number"])


def test_every_specification_states_its_criteria():
    """Guards the parser: a heading renamed would make every other test vacuous."""
    documents = _documents()
    assert all(count > 0 for count in documents.values()), documents


def test_every_criterion_has_exactly_one_row():
    expected = {(spec, n) for spec, count in _documents().items() for n in range(1, count + 1)}
    keys = [_key(row) for row in _rows()]
    duplicated = sorted({key for key in keys if keys.count(key) > 1})
    assert not duplicated, f"criteria with more than one row: {duplicated}"
    assert sorted(expected - set(keys)) == [], "criteria with no row in the register"
    assert sorted(set(keys) - expected) == [], "rows for criteria that do not exist"


def test_every_state_is_one_of_the_four():
    assert {row["state"] for row in _rows()} <= STATES


def test_a_met_row_cites_a_test():
    """Directly, or through "As NN.N" to a row that is itself met."""
    by_key = {_key(row): row for row in _rows()}
    for row in _rows():
        if row["state"] != "met":
            continue
        cited = CITATION.findall(row["evidence"])
        borrowed = [by_key.get((spec, int(n))) for spec, n in SAME_AS.findall(row["evidence"])]
        assert cited or borrowed, f"{_key(row)} is met and cites nothing"
        for other in borrowed:
            assert other is not None and other["state"] == "met", (
                f"{_key(row)} borrows the evidence of a row that is missing or not met"
            )


def test_a_row_that_is_not_met_says_why():
    for row in _rows():
        if row["state"] != "met":
            assert len(row["evidence"].strip()) > 20, f"{_key(row)} gives no reason"


def test_the_summary_counts_the_table():
    """The sentence above the table states the counts; it must not drift."""
    text = REGISTER.read_text(encoding="utf-8")
    counts = {state: sum(row["state"] == state for row in _rows()) for state in STATES}
    stated = re.search(
        r"(\d+) met, (\d+) partly met, (\d+) open, (\d+) manual, of (\d+)\.", text
    )
    assert stated is not None, "the register's summary sentence is missing"
    met, partly, open_, manual, total = map(int, stated.groups())
    assert (met, partly, open_, manual, total) == (
        counts["met"],
        counts["partly met"],
        counts["open"],
        counts["manual"],
        len(_rows()),
    )


def _citations() -> list[str]:
    return sorted({cited for row in _rows() for cited in CITATION.findall(row["evidence"])})


@pytest.mark.parametrize("cited", _citations())
def test_every_citation_exists(cited):
    path, *names = cited.split("::")
    target = REPO_ROOT / path
    assert target.exists(), f"{path} does not exist"
    if not names:
        return
    scope: list[ast.stmt] = ast.parse(target.read_text(encoding="utf-8")).body
    for name in names:
        found = next(
            (
                node
                for node in scope
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name
            ),
            None,
        )
        assert found is not None, f"{cited}: no {name} in {path}"
        scope = found.body if isinstance(found, ast.ClassDef) else []
