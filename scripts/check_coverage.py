# SPDX-License-Identifier: GPL-2.0-or-later
"""Coverage of ``geocomp/core``, and every public function in it reached (specs/20 criterion 6);
and every module of the plugin with a test that runs it (NFR-011).

Run after ``coverage run --source=geocomp -m pytest``::

    python3 scripts/check_coverage.py            # report, and fail on an unreached function
    python3 scripts/check_coverage.py --report   # report only

"Every public function has at least one test" is checked as: every public
function and method of ``core/`` has at least one line of its body executed by
the suite. Executed is not the same as asserted on -- a function called on the
way to something else counts -- so this is the floor the criterion sets, not a
proof of it; but a function nothing executes is certainly untested, and that is
what this finds.

Public: a module-level function or a method of a module-level class, neither
named with a leading underscore (dunders aside). Not counted: overloads,
abstract methods, protocol stubs whose body is ``...``, and bodies that only
raise ``NotImplementedError``.

"Every module MUST have automated tests" (NFR-011) is checked the same way and
more loosely, since a module's own lines run when it is imported: every module
of ``geocomp/`` that defines a function has at least one function body
executed. Until P12c-13 only ``core/`` was measured, and nothing said whether
an algorithm, a dialog or an engine adapter was run by any test at all.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "geocomp"
CORE = PACKAGE / "core"

#: Functions the suite does not reach, each with the reason that is acceptable.
#: An entry here is a decision, reviewed like code; an unexplained one is a gap.
ALLOWED: dict[str, str] = {}

#: Modules no function of which runs under coverage, each with the reason that
#: is acceptable. The same rule as :data:`ALLOWED`.
ALLOWED_MODULES: dict[str, str] = {
    "geocomp/__init__.py": (
        "classFactory is what QGIS calls to load the plugin; "
        "tests/qgis/test_plugin_lifecycle.py calls it in a QGIS of its own, "
        "a process coverage does not follow"
    ),
}


def _is_stub(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    decorators = {
        d.id if isinstance(d, ast.Name) else d.attr if isinstance(d, ast.Attribute) else ""
        for d in node.decorator_list
    }
    if decorators & {"overload", "abstractmethod"}:
        return True
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]  # the docstring
    if len(body) != 1:
        return False
    only = body[0]
    if isinstance(only, ast.Expr) and isinstance(only.value, ast.Constant) and only.value.value is Ellipsis:
        return True
    if isinstance(only, ast.Raise) and only.exc is not None:
        target = only.exc.func if isinstance(only.exc, ast.Call) else only.exc
        return isinstance(target, ast.Name) and target.id == "NotImplementedError"
    return False


def _body_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[int]:
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:] or body
    return {
        line
        for statement in body
        for line in range(statement.lineno, (statement.end_lineno or statement.lineno) + 1)
    }


def public_functions(path: Path):
    """``(qualified name, body lines)`` for each public function in *path*."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module = ".".join(path.relative_to(REPO).with_suffix("").parts)

    def public(name: str) -> bool:
        return not name.startswith("_") or (
            name.startswith("__") and name.endswith("__") and name != "__init__"
        )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            if not _is_stub(node):
                yield f"{module}.{node.name}", _body_lines(node)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            for item in node.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and public(item.name)
                    and not item.name.startswith("__")
                    and not _is_stub(item)
                ):
                    yield f"{module}.{node.name}.{item.name}", _body_lines(item)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", action="store_true", help="report without failing")
    parser.add_argument("--data-file", default=str(REPO / ".coverage"))
    arguments = parser.parse_args(argv)

    import coverage

    measured = coverage.Coverage(data_file=arguments.data_file)
    measured.load()
    data = measured.get_data()
    total = measured.report(file=_Null(), show_missing=False, include=[str(CORE / "*")])
    whole = measured.report(file=_Null(), show_missing=False, include=[str(PACKAGE / "*")])

    unreached: list[str] = []
    counted = 0
    for path in sorted(CORE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        executed = set(data.lines(str(path)) or ())
        for name, lines in public_functions(path):
            counted += 1
            if not (lines & executed) and name not in ALLOWED:
                unreached.append(name)

    untested = [name for name in untested_modules(data) if name not in ALLOWED_MODULES]

    print(f"core/ line coverage: {total:.1f}%")
    print(f"public functions: {counted}, reached: {counted - len(unreached)}, unreached: {len(unreached)}")
    for name in unreached:
        print(f"  not reached: {name}")
    stale = sorted(set(ALLOWED) - {name for path in CORE.rglob("*.py") for name, _ in public_functions(path)})
    for name in stale:
        print(f"  allowed but no longer exists: {name}")
    print(f"geocomp/ line coverage: {whole:.1f}%")
    print(f"modules no test runs a function of: {len(untested)}")
    for name in untested:
        print(f"  not run: {name}")
    gone = sorted(name for name in ALLOWED_MODULES if not (REPO / name).is_file())
    for name in gone:
        print(f"  module allowed but no longer exists: {name}")
    if arguments.report:
        return 0
    return 1 if unreached or stale or untested or gone else 0


def untested_modules(data) -> list[str]:
    """Modules of ``geocomp/`` that define functions, none of whose bodies ran."""
    untested = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = [
            node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        if not functions:
            continue
        executed = set(data.lines(str(path)) or ())
        if not any(_body_lines(function) & executed for function in functions):
            untested.append(path.relative_to(REPO).as_posix())
    return untested


class _Null:
    def write(self, _text: str) -> None:
        pass

    def flush(self) -> None:
        pass


if __name__ == "__main__":
    sys.exit(main())
