# SPDX-License-Identifier: GPL-2.0-or-later
"""Public interfaces between modules are documented and annotated (NFR-012).

An interface *between modules* is what another module of ``geocomp/`` imports:
a module-level function, or a class and its public methods. Each must carry a
docstring and annotate its parameters and its return.

Until P12c-13 nothing checked it. Its first count, of 1,347 such classes,
functions and methods, found 399 with no docstring and 51 not fully annotated --
most of the first are serialisation methods and the QGIS methods every algorithm
overrides, ``displayName`` and the like. Both were frozen in lists that **may
only shrink**: a name left when it was put right, and a new interface arrived
documented and annotated. This is P12c-7's ratchet, which took 457 unworded
error codes to none.

P12c-31 and P12c-32 documented all 399 and P12c-33 annotated all 51, so both
lists are gone and the rule is now plain: every interface has a docstring and
annotates its parameters and its return.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from functools import cache

from tests.conftest import REPO_ROOT

PACKAGE = REPO_ROOT / "geocomp"


@cache
def _modules() -> dict[str, ast.Module]:
    modules = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        dotted = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
        modules[dotted.removesuffix(".__init__")] = ast.parse(path.read_text(encoding="utf-8"))
    return modules


@cache
def _imported() -> dict[str, frozenset[str]]:
    """For each module, the names other modules import from it."""
    names: dict[str, set[str]] = defaultdict(set)
    for dotted, tree in _modules().items():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module
                and node.module.startswith("geocomp")
                and node.module != dotted
            ):
                names[node.module].update(alias.name for alias in node.names)
    return {module: frozenset(found) for module, found in names.items()}


def _interfaces():
    """(qualified name, node) for every interface between modules."""
    for dotted, tree in _modules().items():
        wanted = _imported().get(dotted, frozenset())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name in wanted:
                yield f"{dotted}.{node.name}", node
            elif isinstance(node, ast.ClassDef) and node.name in wanted:
                yield f"{dotted}.{node.name}", node
                for member in node.body:
                    if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef) and (
                        not member.name.startswith("_") or member.name == "__init__"
                    ):
                        yield f"{dotted}.{node.name}.{member.name}", member


def _undocumented() -> set[str]:
    return {
        name
        for name, node in _interfaces()
        if not name.endswith(".__init__") and ast.get_docstring(node) is None
    }


def _unannotated() -> set[str]:
    found = set()
    for name, node in _interfaces():
        if isinstance(node, ast.ClassDef):
            continue
        arguments = node.args
        parameters = [
            argument
            for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
            if argument.arg not in {"self", "cls"}
        ]
        starred = [star for star in (arguments.vararg, arguments.kwarg) if star is not None]
        if (
            any(parameter.annotation is None for parameter in (*parameters, *starred))
            or (node.returns is None and not name.endswith(".__init__"))
        ):
            found.add(name)
    return found


def test_the_interfaces_are_found():
    """Guards the scan: one that found none would pass everything."""
    names = {name for name, _node in _interfaces()}
    assert len(names) > 1000
    assert "geocomp.core.adjustment.least_squares.adjust" in names


def test_every_interface_is_documented():
    missing = sorted(_undocumented())
    assert not missing, f"interfaces between modules with no docstring: {missing}"


def test_every_interface_is_annotated():
    missing = sorted(_unannotated())
    assert not missing, f"interfaces between modules not fully annotated: {missing}"
