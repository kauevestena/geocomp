# SPDX-License-Identifier: GPL-2.0-or-later
"""A declared Processing parameter must be read by the run (P12c-12).

The same defect as the 36 settings ``test_settings_are_honoured.py`` guards,
one level down. A parameter is declared in ``initAlgorithm``. Processing then
draws it, translates its label, stores its value in a model and passes it to
the run. Nothing makes the run read it. P12c-11 found one in that state: the
GNSS modes' *Keep the engine's working directory*, which had been offered since
P7 and changed nothing whichever way it was set.

Two checks, both by parsing the sources (the algorithm modules import QGIS, and
this runs without it). Both rely on the convention every algorithm follows, a
module constant ``NAME = "NAME"`` for each parameter:

* every such constant named in an ``initAlgorithm`` is **read**. That means it
  is passed to ``parameterAs...``, used as a key of ``parameters``, or handed
  to a call that also receives ``parameters``, which is how
  ``write_styled_sink`` and the readers in ``common`` modules take it.
  Appearing anywhere else does not count. A constant used only in a result
  dictionary or in a log line is a value the run does not read.
* every output added with ``addOutput`` appears as a key the run returns.

Like the settings check, this cannot prove a parameter is honoured *correctly*.
It can only prove that the run asks for its value, and KEEP_WORK_DIR failed even
that.
"""

from __future__ import annotations

import ast
import re
from functools import cache
from pathlib import Path

import pytest

from tests.conftest import PLUGIN_DIR

ALGORITHMS = PLUGIN_DIR / "algorithms"
MODULES = sorted(ALGORITHMS.rglob("*.py"))

#: specs/16 section 4: upper snake case, the convention of QGIS's own algorithms.
PARAMETER_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")


@cache
def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(PLUGIN_DIR.parent).with_suffix("").parts)


def _keys(tree: ast.Module) -> set[str]:
    """Module constants following ``NAME = "NAME"``: the parameter keys."""
    return {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and node.value.value == node.targets[0].id
    }


def _initialisers(tree: ast.Module) -> list[ast.FunctionDef]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "initAlgorithm"
    ]


def _added_outputs(tree: ast.Module) -> set[str]:
    """Names given to ``addOutput`` -- results, which the run returns, not reads."""
    outputs: set[str] = set()
    for function in _initialisers(tree):
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "addOutput"
            ):
                outputs |= {name.id for name in ast.walk(node) if isinstance(name, ast.Name)}
    return outputs


def declared(tree: ast.Module) -> set[str]:
    """The parameter keys an ``initAlgorithm`` names, outputs excepted."""
    keys = _keys(tree)
    named = {
        node.id
        for function in _initialisers(tree)
        for node in ast.walk(function)
        if isinstance(node, ast.Name)
    }
    return (named & keys) - _added_outputs(tree)


def read(tree: ast.Module) -> set[str]:
    """Names the code reads as parameter values."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
            names = {argument.id for argument in arguments if isinstance(argument, ast.Name)}
            function = node.func
            called = (
                function.attr
                if isinstance(function, ast.Attribute)
                else function.id
                if isinstance(function, ast.Name)
                else ""
            )
            on_parameters = (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and function.value.id == "parameters"
            )
            if called.startswith("parameterAs") or "parameters" in names or on_parameters:
                found |= names
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "parameters"
            and isinstance(node.slice, ast.Name)
        ):
            found.add(node.slice.id)
    return found


def returned(tree: ast.Module) -> set[str]:
    """Keys of the dictionaries a run builds: literal keys, and assigned ones."""
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys |= {key.id for key in node.keys if isinstance(key, ast.Name)}
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.ctx, ast.Store)
            and isinstance(node.slice, ast.Name)
        ):
            keys.add(node.slice.id)
    return keys


@cache
def _imported_from() -> dict[str, set[Path]]:
    """For each module name, the modules that import something from it."""
    importers: dict[str, set[Path]] = {}
    for path in MODULES:
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ImportFrom) and node.module:
                importers.setdefault(node.module, set()).add(path)
    return importers


@cache
def _read_by(path: Path) -> frozenset[str]:
    return frozenset(read(_tree(path)))


def _readers(path: Path) -> set[str]:
    """What this module reads, and what every module importing from it reads.

    A shared base class declares in one module and is run from another, and a
    ``common`` module's helper reads what the algorithm module declares.
    """
    found = set(_read_by(path))
    for other in _imported_from().get(_module_name(path), ()):
        found |= _read_by(other)
    return found


@pytest.mark.parametrize("path", MODULES, ids=lambda path: _module_name(path))
def test_every_declared_parameter_is_read(path: Path):
    unread = declared(_tree(path)) - _readers(path)
    assert not unread, (
        f"{_module_name(path)} declares {sorted(unread)} and nothing reads it: "
        "the user can set it and the run ignores it"
    )


@pytest.mark.parametrize("path", MODULES, ids=lambda path: _module_name(path))
def test_every_declared_output_is_returned(path: Path):
    tree = _tree(path)
    missing = (_added_outputs(tree) & _keys(tree)) - returned(tree)
    assert not missing, f"{_module_name(path)} declares outputs {sorted(missing)} it never returns"


def test_every_parameter_name_is_upper_snake_case():
    """specs/16 section 4, as built: ``INPUT``, not ``input``."""
    wrong = sorted(
        f"{_module_name(path)}: {key}"
        for path in MODULES
        for key in _keys(_tree(path))
        if key in declared(_tree(path)) and not PARAMETER_NAME.match(key)
    )
    assert not wrong, wrong


# -- the checks find what they claim to ------------------------------------


def test_the_scan_finds_the_parameters():
    """Guards the tests above, which pass vacuously if they find nothing."""
    total = sum(len(declared(_tree(path))) for path in MODULES)
    assert total > 150


PLANTED = '''
FOLDER = "FOLDER"
KEEP = "KEEP"
OUTPUT = "OUTPUT"
COUNT = "COUNT"

class Algorithm:
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(FOLDER, "Folder"))
        self.addParameter(QgsProcessingParameterBoolean(KEEP, "Keep"))
        self.addParameter(QgsProcessingParameterFileDestination(OUTPUT, "Out"))
        self.addOutput(QgsProcessingOutputNumber(COUNT, "Count"))

    def processAlgorithm(self, parameters, context, feedback):
        folder = self.parameterAsFile(parameters, FOLDER, context)
        write(self, parameters, context, OUTPUT)
        feedback.pushInfo(KEEP)
        return {OUTPUT: folder}
'''


def test_a_parameter_named_but_not_read_is_caught():
    """KEEP_WORK_DIR's shape: declared, mentioned, never read. Naming a key in a
    log line is not reading its value, and an output never returned is caught."""
    tree = ast.parse(PLANTED)
    assert declared(tree) == {"FOLDER", "KEEP", "OUTPUT"}
    assert declared(tree) - read(tree) == {"KEEP"}
    assert (_added_outputs(tree) & _keys(tree)) - returned(tree) == {"COUNT"}
