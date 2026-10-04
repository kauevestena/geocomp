# SPDX-License-Identifier: GPL-2.0-or-later
"""The coverage check's module rule finds what it says it finds (NFR-011).

``scripts/check_coverage.py`` runs once, after the QGIS job's suite, where a
rule that found nothing would pass silently. This holds the rule to a stand-in
for the coverage data: a module none of whose function bodies ran is named, one
whose body ran is not, and lines that run on import -- the ``def`` itself --
do not count as a test.
"""

from __future__ import annotations

import ast
import importlib.util

from tests.conftest import REPO_ROOT

_spec = importlib.util.spec_from_file_location("check_coverage", REPO_ROOT / "scripts" / "check_coverage.py")
check_coverage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_coverage)

PLUGIN = REPO_ROOT / "geocomp" / "plugin.py"


class _Executed:
    """Coverage data in which only *lines* of *path* ran."""

    def __init__(self, path=None, lines=()):
        self.path, self.executed = (str(path) if path else None), set(lines)

    def lines(self, path):
        return sorted(self.executed) if path == self.path else []


def _first_function(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def test_a_module_none_of_whose_functions_ran_is_named():
    assert "geocomp/plugin.py" in check_coverage.untested_modules(_Executed())


def test_one_body_line_run_is_enough():
    body = check_coverage._body_lines(_first_function(PLUGIN))
    untested = check_coverage.untested_modules(_Executed(PLUGIN, [min(body)]))
    assert "geocomp/plugin.py" not in untested


def test_the_def_line_running_on_import_is_not_a_test():
    function = _first_function(PLUGIN)
    untested = check_coverage.untested_modules(_Executed(PLUGIN, [function.lineno]))
    assert "geocomp/plugin.py" in untested


def test_every_exemption_names_a_module_that_exists():
    for name in check_coverage.ALLOWED_MODULES:
        assert (REPO_ROOT / name).is_file(), name
