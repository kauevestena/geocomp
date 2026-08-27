# SPDX-License-Identifier: GPL-2.0-or-later
"""Every key the QGIS tests use must be one an algorithm actually declares.

The tier-3 tests only run where QGIS does, which is CI. A mistyped parameter
name in one of them is invisible here and, in CI, arrives as a failure that
looks like a defect in the algorithm rather than in the test that names it.

Processing's own behaviour makes this worse rather than better: an unrecognised
key in a parameter dictionary is not an error, it is simply ignored, so a
mistyped input silently becomes a default and the test fails somewhere else
entirely.

So the names are checked here, by parsing rather than importing -- the
algorithm modules import QGIS, and the point of this check is that it runs
without it. Both sides use the same convention, ``NAME = "NAME"`` at module
level, which is what makes the comparison possible at all.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALGORITHM_ROOT = REPO_ROOT / "geocomp" / "algorithms"
TIER_THREE = sorted((REPO_ROOT / "tests" / "qgis").glob("test_*.py"))

#: A key: all upper case, at least three characters. Shorter than that is a
#: station name in a fixture, not a parameter.
KEY = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

#: Keys that belong to QGIS or to a test fixture rather than to a GeoComp
#: algorithm, each with the reason it is not declared in this repository.
FOREIGN_KEYS: dict[str, str] = {
    "OUTPUT": "Processing's own conventional output name, defined by QGIS.",
}


def _declared_constants(path: Path) -> set[str]:
    """Module-level ``NAME = "NAME"`` assignments -- the parameter idiom."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    declared: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and target.id == value.value
        ):
            declared.add(target.id)
    return declared


def _used_keys(path: Path) -> dict[str, int]:
    """Every key-shaped string literal in a test module, with its line."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    used: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if KEY.match(node.value):
                used.setdefault(node.value, node.lineno)
    return used


@pytest.fixture(scope="module")
def declared() -> set[str]:
    names: set[str] = set(FOREIGN_KEYS)
    for path in ALGORITHM_ROOT.rglob("*.py"):
        names |= _declared_constants(path)
    return names


def test_the_algorithm_modules_declare_their_parameters_this_way(declared):
    """Guards the check itself: if the convention were abandoned the set would
    empty out and every assertion below would pass vacuously."""
    assert {"REDUCTIONS", "OUTPUT_HTML", "STATION"} <= declared
    assert len(declared) > 50


def _parameter_dictionaries(path: Path) -> list[tuple[str, str, int]]:
    """(algorithm id, key, line) for every parameter dictionary passed to a run.

    Two call shapes appear in the tier-3 tests: ``_run("geocomp:x", {...})``,
    where the id is right there, and ``_algorithm("geocomp:x").create({}).run({...})``
    spread over a few statements, where it is not. For the second the id is
    taken from the enclosing function, and only when that function names
    exactly one algorithm -- an unattributable call is skipped rather than
    guessed at.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, str, int]] = []

    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef):
            continue
        mentioned = {
            node.args[0].value
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"_run", "_algorithm"}
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }

        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "_run":
                if len(node.args) < 2 or not isinstance(node.args[0], ast.Constant):
                    continue
                algorithm_id, mapping = node.args[0].value, node.args[1]
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                if len(mentioned) != 1 or not node.args:
                    continue
                algorithm_id, mapping = next(iter(mentioned)), node.args[0]
            else:
                continue

            if not isinstance(mapping, ast.Dict):
                continue
            for key in mapping.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    found.append((algorithm_id, key.value, key.lineno))

    return found


def _geocomp_imports(path: Path) -> set[Path]:
    """The GeoComp modules *path* imports names from.

    A shared parameter helper declares real parameters of every algorithm that
    calls it -- the five result-layer sinks live in ``layer_outputs.py``
    precisely so both adjustments offer the same ones -- so the constants an
    algorithm module imports count as its own.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if not node.module.startswith("geocomp."):
                continue
            candidate = REPO_ROOT / Path(*node.module.split(".")).with_suffix(".py")
            if candidate.is_file():
                imported.add(candidate)
    return imported


@pytest.fixture(scope="module")
def declared_by_algorithm() -> dict[str, set[str]]:
    from geocomp.registry import ALGORITHMS

    by_id: dict[str, set[str]] = {}
    for spec in ALGORITHMS:
        path = REPO_ROOT / Path(*spec.module.split(".")).with_suffix(".py")
        names = set(FOREIGN_KEYS) | _declared_constants(path)
        for helper in _geocomp_imports(path):
            names |= _declared_constants(helper)
        by_id[spec.id] = names
    return by_id


@pytest.mark.parametrize("path", TIER_THREE, ids=lambda p: p.name)
def test_every_parameter_goes_to_the_algorithm_that_declares_it(path, declared_by_algorithm):
    """A key that some *other* algorithm declares is still the wrong key here,
    and Processing would ignore it in silence."""
    wrong = [
        (algorithm_id, key, line)
        for algorithm_id, key, line in _parameter_dictionaries(path)
        if key not in declared_by_algorithm.get(algorithm_id, set())
    ]
    assert not wrong, "\n".join(
        f"{path.name}:{line}: {algorithm_id} declares no parameter '{key}'"
        for algorithm_id, key, line in sorted(wrong, key=lambda item: item[2])
    )


def test_at_least_one_parameter_dictionary_was_found_in_each_module():
    """Guards the parsing: a call shape this stopped recognising would make the
    check above pass by finding nothing."""
    for path in TIER_THREE:
        assert _parameter_dictionaries(path), path.name


@pytest.mark.parametrize("path", TIER_THREE, ids=lambda p: p.name)
def test_every_key_a_qgis_test_uses_is_declared_by_an_algorithm(path, declared):
    """The wider net, which catches result keys too -- those are read by
    subscripting a fixture, so there is no call to attribute them to."""
    unknown = {name: line for name, line in _used_keys(path).items() if name not in declared}
    assert not unknown, "\n".join(
        f"{path.name}:{line}: '{name}' is not declared by any algorithm"
        for name, line in sorted(unknown.items(), key=lambda item: item[1])
    )


def test_there_are_qgis_tests_to_check():
    assert TIER_THREE
