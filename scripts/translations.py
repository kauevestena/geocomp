# SPDX-License-Identifier: GPL-2.0-or-later
"""Translation extraction and catalogue maintenance (specs/18 section 4).

Qt's ``lupdate`` is the reference extractor and is used when it is installed.
When it is not -- a contributor's machine, or a CI job that runs only the
QGIS-free tier -- this module falls back to an AST extractor that finds the same
``tr()`` / ``translate()`` calls.

The fallback is not a workaround for a broken toolchain. FR-091 requires that an
untranslated string be caught **at the commit that introduces it**, and a check
that only runs where Qt's tools happen to be installed would not do that.
"""

from __future__ import annotations

import ast
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

__all__ = [
    "TRANSLATION_FUNCTIONS",
    "catalogue_path",
    "compile_catalogue",
    "completeness",
    "extract_sources",
    "have_qt_tools",
    "read_catalogue",
    "write_catalogue",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "geocomp"
I18N_DIR = PLUGIN_DIR / "i18n"

#: Locales GeoComp ships. ``en`` is the source locale and has no catalogue.
TARGET_LOCALES = ("pt_BR", "es")

TRANSLATION_FUNCTIONS = {"tr", "_tr", "translate"}

#: ``MessageTemplate`` wraps ``QCoreApplication.translate`` internally, so its
#: first argument is a source string even though the call is not a tr() call.
TEMPLATE_FACTORIES = {"MessageTemplate"}

DEFAULT_CONTEXT = "GeoComp"


def catalogue_path(locale: str) -> Path:
    return I18N_DIR / f"geocomp_{locale}.ts"


def have_qt_tools() -> bool:
    return shutil.which("lupdate") is not None or shutil.which("pylupdate5") is not None


# -- extraction ----------------------------------------------------------


def _module_context(tree: ast.AST) -> str | None:
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id in ("_TR_CONTEXT", "_CONTEXT")
                    and isinstance(node.value, ast.Constant)
                ):
                    return str(node.value.value)
    return None


def _class_contexts(tree: ast.AST) -> dict[int, str]:
    """Map each class body line range onto its ``TR_CONTEXT``."""
    contexts: dict[int, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            for target in statement.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "TR_CONTEXT"
                    and isinstance(statement.value, ast.Constant)
                ):
                    end = getattr(node, "end_lineno", node.lineno)
                    for line in range(node.lineno, end + 1):
                        contexts[line] = str(statement.value.value)
    return contexts


def extract_sources(root: Path | None = None) -> dict[str, set[str]]:
    """Return ``{context: {source string}}`` found in the plugin sources."""
    root = root or PLUGIN_DIR
    found: dict[str, set[str]] = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_context = _module_context(tree)
        class_contexts = _class_contexts(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)

            if name in TEMPLATE_FACTORIES:
                if node.args and isinstance(node.args[0], ast.Constant):
                    found["GeoCompMessages"].add(str(node.args[0].value))
                continue

            if name not in TRANSLATION_FUNCTIONS:
                continue

            local = class_contexts.get(node.lineno) or module_context or DEFAULT_CONTEXT

            if name == "translate" and len(node.args) >= 2:
                context_arg, source_arg = node.args[0], node.args[1]
                context = (
                    str(context_arg.value) if isinstance(context_arg, ast.Constant) else local
                )
            elif node.args:
                context, source_arg = local, node.args[0]
            else:
                continue

            if isinstance(source_arg, ast.Constant) and isinstance(source_arg.value, str):
                found[context].add(source_arg.value)

    return dict(found)


# -- catalogues ----------------------------------------------------------


def read_catalogue(path: Path) -> dict[str, dict[str, str]]:
    """Read a ``.ts`` file into ``{context: {source: translation}}``.

    An unfinished entry reads as an empty translation, which is what
    :func:`completeness` counts.
    """
    if not path.exists():
        return {}
    tree = ET.parse(path)
    catalogue: dict[str, dict[str, str]] = {}
    for context in tree.getroot().findall("context"):
        name_node = context.find("name")
        name = name_node.text if name_node is not None and name_node.text else DEFAULT_CONTEXT
        entries: dict[str, str] = {}
        for message in context.findall("message"):
            source = message.findtext("source") or ""
            translation_node = message.find("translation")
            text = "" if translation_node is None else (translation_node.text or "")
            if translation_node is not None and translation_node.get("type") == "unfinished":
                text = text or ""
            entries[source] = text
        catalogue[name] = entries
    return catalogue


def write_catalogue(path: Path, language: str, catalogue: dict[str, dict[str, str]]) -> None:
    """Write ``catalogue`` as a Qt ``.ts`` file, sorted for a stable diff."""
    root = ET.Element("TS", version="2.1", language=language)
    for context_name in sorted(catalogue):
        context = ET.SubElement(root, "context")
        ET.SubElement(context, "name").text = context_name
        for source in sorted(catalogue[context_name]):
            message = ET.SubElement(context, "message")
            ET.SubElement(message, "source").text = source
            translation = ET.SubElement(message, "translation")
            text = catalogue[context_name][source]
            if text:
                translation.text = text
            else:
                translation.set("type", "unfinished")
    ET.indent(root, space="    ")
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n",
        encoding="utf-8",
    )


def merge(sources: dict[str, set[str]], existing: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Merge freshly extracted sources into an existing catalogue.

    Keeps every translation whose source string still exists, and drops the
    rest -- a translation of a string that no longer appears in the code is dead
    weight that makes completeness reporting lie.
    """
    merged: dict[str, dict[str, str]] = {}
    for context, strings in sources.items():
        previous = existing.get(context, {})
        merged[context] = {source: previous.get(source, "") for source in strings}
    return merged


def completeness(catalogue: dict[str, dict[str, str]]) -> tuple[int, int]:
    """Return ``(translated, total)``."""
    total = sum(len(entries) for entries in catalogue.values())
    translated = sum(1 for entries in catalogue.values() for text in entries.values() if text)
    return translated, total


def compile_catalogue(ts_path: Path) -> Path | None:
    """Compile a ``.ts`` to ``.qm`` with ``lrelease``.

    Returns the ``.qm`` path, or ``None`` when ``lrelease`` is unavailable. The
    caller decides whether that is fatal: it is for a release build, and it is
    not for a developer running the test suite.
    """
    lrelease = shutil.which("lrelease") or shutil.which("lrelease-qt6")
    if lrelease is None:
        return None
    qm_path = ts_path.with_suffix(".qm")
    subprocess.run([lrelease, str(ts_path), "-qm", str(qm_path)], check=True)
    return qm_path
