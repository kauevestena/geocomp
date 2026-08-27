# SPDX-License-Identifier: GPL-2.0-or-later
"""The shipped QML styles, and the rule that outranks them.

Two things are checked here, neither of which needs QGIS.

**The exaggeration factor cannot be dropped.** ``specs/19`` section 3 calls an
unstated exaggeration the one thing that turns a quality visualisation into a
misrepresentation. The defence is in the signatures: wherever a function takes
an ``exaggeration``, it takes it keyword-only and without a default, so no
call site can omit it and silently draw at 1:1. A default added later would
undo that quietly, which is what this test exists to stop.

**A style cannot reference a field its layer does not have.** QGIS does not
fail on a categorised renderer whose attribute is missing; it draws every
feature in the fallback symbol. The map then looks styled and says nothing,
which is a worse failure than an error. Renaming a field on either side breaks
the pairing here instead.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_DIR = REPO_ROOT / "geocomp" / "resources" / "styles"
BUILDERS = REPO_ROOT / "geocomp" / "layers" / "builders.py"
DRAWING_SOURCES = sorted(
    [*(REPO_ROOT / "geocomp" / "core" / "visualization").glob("*.py"), BUILDERS]
)

#: Fields a QGIS expression may reference that no builder creates.
EXPRESSION_BUILTINS = frozenset({"value", "type", "name"})


def _layer_fields() -> dict[str, set[str]]:
    """The ``LAYER_FIELDS`` table, read by parsing rather than importing.

    ``geocomp.layers.builders`` imports QGIS, and the whole point of this check
    is that it runs where QGIS is not installed.
    """
    tree = ast.parse(BUILDERS.read_text(encoding="utf-8"), filename=str(BUILDERS))
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "LAYER_FIELDS" or not isinstance(node.value, ast.Dict):
            continue
        table: dict[str, set[str]] = {}
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            names = {
                element.elts[0].value
                for element in value.elts
                if isinstance(element, ast.Tuple) and isinstance(element.elts[0], ast.Constant)
            }
            table[key.value] = names
        return table
    raise AssertionError("builders.py declares no LAYER_FIELDS table")


def _style_field_references(path: Path) -> set[str]:
    """Every layer field a QML names: renderer attribute, label, expression."""
    root = ElementTree.parse(path).getroot()
    referenced: set[str] = set()

    for renderer in root.iter("renderer-v2"):
        attribute = renderer.get("attr")
        if attribute:
            referenced.add(attribute)
    for style in root.iter("text-style"):
        field = style.get("fieldName")
        if field:
            referenced.add(field)
    for option in root.iter("Option"):
        if option.get("name") == "expression":
            expression = option.get("value") or ""
            referenced.update(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"', expression))

    return referenced - EXPRESSION_BUILTINS


@pytest.fixture(scope="module")
def layer_fields() -> dict[str, set[str]]:
    return _layer_fields()


def test_the_field_table_parses(layer_fields):
    """Guards the parsing: were the table restructured, every pairing check
    below would pass by comparing against nothing."""
    assert len(layer_fields) >= 5
    assert "station" in layer_fields["stations"]
    assert "decision" in layer_fields["residuals"]


@pytest.mark.parametrize("name", sorted(_layer_fields()))
def test_every_style_is_well_formed_xml_with_a_renderer(name):
    root = ElementTree.parse(STYLE_DIR / f"{name}.qml").getroot()
    assert root.tag == "qgis"
    renderers = list(root.iter("renderer-v2"))
    assert len(renderers) == 1
    assert list(renderers[0].iter("symbol")), "a renderer with no symbol draws nothing"


@pytest.mark.parametrize("name", sorted(_layer_fields()))
def test_every_field_a_style_names_is_one_its_layer_has(name, layer_fields):
    """A categorised renderer whose attribute is missing does not fail -- it
    draws everything in the fallback symbol, so the map looks styled and
    conveys nothing. That is worse than an error, because nobody investigates
    a map that rendered."""
    missing = _style_field_references(STYLE_DIR / f"{name}.qml") - layer_fields[name]
    assert not missing, f"{name}.qml references {sorted(missing)}, which its layer lacks"


@pytest.mark.parametrize("name", sorted(_layer_fields()))
def test_every_category_a_style_declares_has_a_symbol(name):
    root = ElementTree.parse(STYLE_DIR / f"{name}.qml").getroot()
    symbols = {symbol.get("name") for symbol in root.iter("symbol")}
    for category in root.iter("category"):
        assert category.get("symbol") in symbols, (
            f"{name}.qml category {category.get('value')!r} names symbol "
            f"{category.get('symbol')!r}, which is not defined"
        )


def test_the_styles_and_the_layers_are_one_to_one():
    """A style with no layer is dead weight; a layer with no style is
    unstyled, which FR-905 forbids. Either way the names must match exactly."""
    shipped = {path.stem for path in STYLE_DIR.glob("*.qml")}
    assert shipped == set(_layer_fields())


def _functions_taking_an_exaggeration(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        positional = [a.arg for a in node.args.args] + [a.arg for a in node.args.posonlyargs]
        keyword = dict(
            zip([a.arg for a in node.args.kwonlyargs], node.args.kw_defaults, strict=True)
        )
        if "exaggeration" in positional or "exaggeration" in keyword:
            yield node, positional, keyword


@pytest.mark.parametrize("path", DRAWING_SOURCES, ids=lambda p: p.name)
def test_no_function_defaults_an_exaggeration(path):
    """FR-901's enforcement, checked where it lives: in the signatures. This
    half has no exceptions. A default is exactly the mechanism by which a
    factor gets lost -- the call site stops mentioning it, and the number in
    the legend stops being the number the geometry used."""
    offenders = []
    for node, _positional, keyword in _functions_taking_an_exaggeration(path):
        if keyword.get("exaggeration") is not None:
            offenders.append(f"{path.name}:{node.lineno}: {node.name} defaults 'exaggeration'")
        defaults = dict(
            zip([a.arg for a in node.args.args][::-1], node.args.defaults[::-1], strict=False)
        )
        if "exaggeration" in defaults:
            offenders.append(f"{path.name}:{node.lineno}: {node.name} defaults 'exaggeration'")
    assert not offenders, "\n".join(offenders) + (
        "\n-- a drawn result must state the factor it was drawn with (FR-901)"
    )


#: The two functions that take an exaggeration positionally, and why each is
#: not a drawing function. Anything else that draws must take it keyword-only,
#: so a caller cannot slide a confidence level or a vertex count into its place.
POSITIONAL_JUSTIFICATIONS: dict[str, str] = {
    "exaggeration_label": (
        "Formats a factor for a legend rather than drawing with one. It takes "
        "the number as its subject, the way str() takes a value."
    ),
    "_check_exaggeration": (
        "Validates a factor and returns nothing. It is the guard the drawing "
        "functions call, not one of them."
    ),
}


@pytest.mark.parametrize("path", DRAWING_SOURCES, ids=lambda p: p.name)
def test_every_drawing_function_takes_the_exaggeration_keyword_only(path):
    offenders = [
        f"{path.name}:{node.lineno}: {node.name} takes 'exaggeration' positionally"
        for node, positional, _keyword in _functions_taking_an_exaggeration(path)
        if "exaggeration" in positional and node.name not in POSITIONAL_JUSTIFICATIONS
    ]
    assert not offenders, "\n".join(offenders)


def test_every_justified_exception_still_exists():
    """A justification for a function nobody wrote is a stale exception that
    would silently cover a future one of the same name."""
    names = {
        node.name
        for path in DRAWING_SOURCES
        for node, _positional, _keyword in _functions_taking_an_exaggeration(path)
    }
    assert set(POSITIONAL_JUSTIFICATIONS) <= names


def test_something_actually_takes_an_exaggeration():
    """Otherwise the checks above pass on a codebase that lost the argument
    entirely, which is the failure they are meant to catch."""
    drawing = [
        node.name
        for path in DRAWING_SOURCES
        for node, _positional, keyword in _functions_taking_an_exaggeration(path)
        if "exaggeration" in keyword
    ]
    assert len(drawing) >= 4
