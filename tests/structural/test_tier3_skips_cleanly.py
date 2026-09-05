# SPDX-License-Identifier: GPL-2.0-or-later
"""Every tier-3 module must **skip** without QGIS, never error.

``specs/20-testing-and-validation.md`` section 2: seven of the nine CI jobs have
no QGIS runtime, and they run the whole suite. A tier-3 test that cannot run
there must skip; one that raises `ModuleNotFoundError` turns those jobs red for
a reason that has nothing to do with the change being tested.

**This exists because it happened.** `tests/qgis/test_adjustment_report.py`
carried `pytestmark = pytest.mark.qgis`, which is a *label* and not a skip.
Every other tier-3 module reaches QGIS through the `qgis_app` or
`geocomp_provider` fixture, both of which call `pytest.skip` when there is no
runtime, so the label being inert never mattered. That module's fixtures did not
need the provider, nothing skipped, and its lazy `from geocomp.reports import
...` raised inside fixture setup: twenty-five errors in seven jobs, on a commit
whose own subject was unrelated.

The check is structural rather than a matter of running the suite twice, because
the failure only appears in an environment this one is not: here and in the QGIS
job, QGIS is either present or the fixtures skip, and in both cases a module
missing its guard looks fine.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TIER3 = Path(__file__).resolve().parents[1] / "qgis"

#: A module is guarded if its `pytestmark` includes `requires_qgis`, or if every
#: test in it takes a fixture that skips. The first is checkable from the source
#: and is what this asks for; the second is what the older modules do, so their
#: use of a skipping fixture in every test is accepted as equivalent.
SKIPPING_FIXTURES = {"qgis_app", "geocomp_provider"}


def _modules() -> list[Path]:
    return sorted(path for path in TIER3.glob("test_*.py"))


def _has_requires_qgis(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in node.targets
        ):
            continue
        if any(
            isinstance(inner, ast.Name) and inner.id == "requires_qgis"
            for inner in ast.walk(node.value)
        ):
            return True
    return False


def _is_autouse(node: ast.FunctionDef) -> bool:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        for keyword in decorator.keywords:
            if keyword.arg == "autouse" and getattr(keyword.value, "value", False) is True:
                return True
    return False


def _tests_without_a_skipping_fixture(tree: ast.AST) -> list[str]:
    """Test functions that reach no fixture known to skip.

    Fixtures defined in the module are followed, so a test taking ``adjusted``
    is covered if ``adjusted`` itself takes ``qgis_app``. An **autouse** fixture
    that reaches one covers every test in the module without appearing in any
    signature -- which is how the algorithm modules guard themselves, and a
    check that missed it would report them and teach everyone to ignore it.
    """
    fixtures = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("test_")
    ]
    fixture_args = {node.name: {a.arg for a in node.args.args} for node in fixtures}

    def covered(names: set[str], depth: int = 3) -> bool:
        if names & SKIPPING_FIXTURES:
            return True
        if depth == 0:
            return False
        return any(covered(fixture_args.get(name, set()), depth - 1) for name in names)

    if any(_is_autouse(node) and covered(fixture_args[node.name]) for node in fixtures):
        return []

    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
        and not covered({argument.arg for argument in node.args.args})
    ]


def test_there_are_tier3_modules_to_check():
    """Guards the glob: a path typo would make every check below vacuous."""
    assert len(_modules()) >= 5


@pytest.mark.parametrize("path", _modules(), ids=lambda p: p.name)
def test_the_module_skips_without_qgis(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    if _has_requires_qgis(tree):
        return

    unguarded = _tests_without_a_skipping_fixture(tree)
    assert not unguarded, (
        f"{path.name} would error rather than skip in the seven CI jobs without QGIS.\n"
        "Add `requires_qgis` from tests.conftest to its `pytestmark` -- "
        "`pytest.mark.qgis` only labels, it does not skip -- or give these tests a "
        "fixture that skips:\n" + "\n".join(unguarded)
    )
