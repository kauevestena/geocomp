# SPDX-License-Identifier: GPL-2.0-or-later
"""The requirement register covers every requirement, and cites what exists (specs/20 section 11).

The acceptance register (``test_acceptance_register.py``) holds every acceptance
criterion to a test. P12c-11 found two *requirements* broken while every
criterion was green: FR-302 and FR-304 had no criterion of their own. This holds
each requirement of ``specs/02`` to a row, by the same rules: one row per
requirement, a test behind every **met** -- directly, or through "As NN.N" to a
met acceptance row -- a reason behind everything else, and no citation of a test
that does not exist.

The register is written a block at a time. :data:`UNAUDITED` lists the blocks
still to come, and **may only shrink**: a block leaves it in the pull request
that audits it.
"""

from __future__ import annotations

import re
from functools import cache

import pytest

from tests.structural.test_acceptance_register import (
    CITATION,
    REGISTER,
    SAME_AS,
    SPECS,
    STATES,
)
from tests.structural.test_acceptance_register import _rows as _acceptance_rows
from tests.structural.test_acceptance_register import (
    test_every_citation_exists as _check_citation,
)

REQUIREMENTS = SPECS / "02-requirements.md"

#: The blocks of specs/02 with no rows yet. Each leaves in the pull request that
#: audits it, and nothing is ever added.
UNAUDITED = frozenset({"6xx", "7xx", "8xx", "9xx", "NFR"})

#: A row: | FR-001 | **state** | evidence |
ROW = re.compile(
    r"^\| (?P<id>N?FR-\d{3}) \| \*\*(?P<state>[a-z ]+)\*\* \| (?P<evidence>.*) \|$"
)


def _block(requirement: str) -> str:
    if requirement.startswith("NFR"):
        return "NFR"
    return f"{requirement[3]}xx"


@cache
def _requirements() -> tuple[str, ...]:
    """Every requirement ID specs/02 states, the withdrawn ones excepted."""
    text = REQUIREMENTS.read_text(encoding="utf-8").split("## Withdrawn requirements", 1)[0]
    return tuple(re.findall(r"^\| (N?FR-\d{3}) \|", text, re.M))


@cache
def _rows() -> tuple[dict[str, str], ...]:
    text = REGISTER.read_text(encoding="utf-8")
    section = text.split("## 11. Requirement register", 1)[1]
    return tuple(match.groupdict() for line in section.splitlines() if (match := ROW.match(line)))


def test_the_requirements_are_found():
    """Guards the parser: a changed table layout would make every other test vacuous."""
    assert len(_requirements()) > 150
    assert {_block(r) for r in _requirements()} >= UNAUDITED | {"0xx", "1xx", "2xx", "3xx", "4xx", "5xx"}


def test_every_audited_requirement_has_exactly_one_row():
    ids = [row["id"] for row in _rows()]
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicated, f"requirements with more than one row: {duplicated}"
    expected = {r for r in _requirements() if _block(r) not in UNAUDITED}
    assert sorted(expected - set(ids)) == [], "audited requirements with no row"
    assert sorted(set(ids) - set(_requirements())) == [], "rows for requirements that do not exist"


def test_no_unaudited_block_has_rows():
    """A block with rows is audited, and leaves UNAUDITED in the same change."""
    early = sorted(row["id"] for row in _rows() if _block(row["id"]) in UNAUDITED)
    assert not early, f"rows for a block still listed as unaudited: {early}"


def test_every_state_is_one_of_the_four():
    assert {row["state"] for row in _rows()} <= STATES


def test_a_met_row_cites_a_test():
    """Directly, or through "As NN.N" to an acceptance row that is itself met."""
    acceptance = {(row["spec"], int(row["number"])): row for row in _acceptance_rows()}
    for row in _rows():
        if row["state"] != "met":
            continue
        cited = CITATION.findall(row["evidence"])
        borrowed = [acceptance.get((spec, int(n))) for spec, n in SAME_AS.findall(row["evidence"])]
        assert cited or borrowed, f"{row['id']} is met and cites nothing"
        for other in borrowed:
            assert other is not None and other["state"] == "met", (
                f"{row['id']} borrows the evidence of an acceptance row that is missing or not met"
            )


def test_a_row_that_is_not_met_says_why():
    for row in _rows():
        if row["state"] != "met":
            assert len(row["evidence"].strip()) > 20, f"{row['id']} gives no reason"


def test_the_summary_counts_the_table():
    text = REGISTER.read_text(encoding="utf-8").split("## 11. Requirement register", 1)[1]
    stated = re.findall(r"(\d+) met, (\d+) partly met, (\d+) open, (\d+) manual, of (\d+)\.", text)
    assert stated, "the register's summary sentence is missing"
    counts = {state: sum(row["state"] == state for row in _rows()) for state in STATES}
    assert tuple(map(int, stated[-1])) == (
        counts["met"],
        counts["partly met"],
        counts["open"],
        counts["manual"],
        len(_rows()),
    )


@pytest.mark.parametrize(
    "cited", sorted({cited for row in _rows() for cited in CITATION.findall(row["evidence"])})
)
def test_every_citation_exists(cited):
    _check_citation(cited)
