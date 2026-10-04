# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-102: no observation is made without saying where it came from.

``specs/04-data-model.md`` section 2.5. P12c-19 and P12c-20 gave every place
that makes an observation its provenance. Behavioural tests check what each
records; this keeps a new one from forgetting. Every ``Observation(...)`` call
in the plugin passes ``provenance=``, or sits in a module that stamps what it
made afterwards with :meth:`~geocomp.core.models.Network.record_provenance`,
as the file readers do once they know which line each observation came from.
"""

from __future__ import annotations

import ast
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "geocomp"


def _constructions(tree: ast.AST):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Observation"
        ):
            yield node


def _stamps_afterwards(tree: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Attribute) and node.attr == "record_provenance"
        for node in ast.walk(tree)
    )


def test_every_observation_made_says_where_it_came_from():
    unstated = []
    for path in sorted(PLUGIN.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _stamps_afterwards(tree):
            continue
        for call in _constructions(tree):
            if not any(keyword.arg == "provenance" for keyword in call.keywords):
                unstated.append(f"{path.relative_to(PLUGIN.parent)}:{call.lineno}")
    assert not unstated, "observations made with no provenance (FR-102): " + ", ".join(unstated)


def test_the_check_finds_the_constructions_it_is_about():
    """Not vacuous: there are observations being made, and readers that stamp."""
    made = stamped = 0
    for path in PLUGIN.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found = sum(1 for _ in _constructions(tree))
        made += found
        stamped += bool(found and _stamps_afterwards(tree))
    assert made >= 20
    assert stamped == 4  # DNA, DynaML, Krumm and Adjust
