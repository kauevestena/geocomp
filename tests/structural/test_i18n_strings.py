# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-091: string discipline, enforced from the first commit.

``specs/18-i18n-and-profiles.md`` section 2. Wrapping a string as you write it
costs nothing; finding and wrapping several thousand across a finished codebase
is a large, error-prone task that is invariably deferred -- which is exactly
what the archived roadmap did by scheduling i18n for its phase 9.

Two rules, both chosen because they catch real, silent breakage rather than
style:

1. **No raw literal into a user-facing Qt setter.** That string reaches the user
   untranslated, in every locale.
2. **No f-string or ``+`` concatenation inside a translation call.** The
   extractor cannot see a runtime-composed string, so the entry never reaches
   the catalogue, and word order that works in English breaks elsewhere.
"""

from __future__ import annotations

import ast

from tests.conftest import PLUGIN_DIR, python_sources

#: Methods whose string argument is displayed to a user.
UI_SETTERS = {
    "setText",
    "setWindowTitle",
    "setToolTip",
    "setStatusTip",
    "setWhatsThis",
    "setPlaceholderText",
    "setTitle",
    "setLabelText",
    "setInformativeText",
}

#: Constructors whose first positional argument is a displayed label.
UI_CONSTRUCTORS = {
    "QAction",
    "QLabel",
    "QMenu",
    "QPushButton",
    "QCheckBox",
    "QGroupBox",
    "QToolButton",
    "QRadioButton",
}

#: Calls that perform translation.
TRANSLATION_CALLS = {"tr", "translate", "_tr", "tranlate"}

#: Packages that face the user. ``core`` is excluded by construction: it cannot
#: import Qt at all (NFR-002), so it cannot phrase a user-facing string.
UI_PACKAGES = ("gui", "algorithms", "services")
UI_MODULES = ("plugin.py", "provider.py")


def _is_translation_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in TRANSLATION_CALLS
    if isinstance(func, ast.Attribute):
        return func.attr in TRANSLATION_CALLS
    return False


def _is_raw_display_string(node: ast.AST) -> bool:
    """A non-empty string literal, not produced by a translation call."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip() != ""


def _ui_sources():
    for package in UI_PACKAGES:
        yield from python_sources(PLUGIN_DIR / package)
    for module in UI_MODULES:
        path = PLUGIN_DIR / module
        if path.exists():
            yield path


def test_no_raw_literal_reaches_a_user_facing_setter():
    offenders: list[str] = []

    for path in _ui_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name is None:
                continue

            if name in UI_SETTERS:
                args = node.args
            elif name in UI_CONSTRUCTORS:
                args = node.args[:1]
            else:
                continue

            for arg in args:
                if _is_raw_display_string(arg):
                    offenders.append(
                        f"{path.relative_to(PLUGIN_DIR.parent)}:{node.lineno}: "
                        f"{name}({arg.value!r}) is not translated"
                    )

    assert not offenders, (
        "User-facing strings must pass through the translation layer (FR-091).\n"
        "Wrap them in tr() / QCoreApplication.translate().\n" + "\n".join(offenders)
    )


def test_no_composed_string_inside_a_translation_call():
    offenders: list[str] = []

    for path in _ui_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not _is_translation_call(node):
                continue
            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):
                    offenders.append(
                        f"{path.relative_to(PLUGIN_DIR.parent)}:{node.lineno}: "
                        "f-string inside a translation call"
                    )
                elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    offenders.append(
                        f"{path.relative_to(PLUGIN_DIR.parent)}:{node.lineno}: "
                        "concatenation inside a translation call"
                    )

    assert not offenders, (
        "A translation call must receive a plain literal so the extractor can see it, "
        "and so translators can reorder the sentence. Use %1 placeholders instead.\n"
        + "\n".join(offenders)
    )


def test_the_core_package_phrases_nothing_for_users():
    """NFR-002 makes this structural: no Qt import means no tr(), so the core
    cannot phrase a message even by accident. Asserted so the reasoning is
    recorded next to the rule it depends on."""
    for path in python_sources(PLUGIN_DIR / "core"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            assert not _is_translation_call(node), (
                f"{path.name}: the core must raise structured errors, not phrase messages"
            )
