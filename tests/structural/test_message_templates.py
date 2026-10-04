# SPDX-License-Identifier: GPL-2.0-or-later
"""NFR-006: a message template must actually be able to say what it promises.

The core raises errors carrying a stable ``code`` and a ``context`` mapping and
never phrases a sentence; the presentation layer owns the wording
(``specs/18-i18n-and-profiles.md`` section 2). That split has one silent failure
mode: a template interpolating a context key the raising site never supplies.
Nothing raises, nothing is logged -- the user simply reads

    Station '(not set)' has no approximate (not set)

which is worse than the bare code, because it looks like a finished sentence.

This test closes that gap without a QGIS runtime, by reading both sides as
source: every ``*Error("code", key=...)`` call in ``geocomp/``, and every
``MessageTemplate`` declared in the presentation layer.

Since P12c-7 it also holds the opposite gap shut: a code with no template at
all, which the user reads as "could not complete the operation (code)". When
P12c-7 first counted, 457 codes were in that state; they were frozen in a list
that could only shrink, and eight pull requests later it was empty and was
removed. There is no exemption now: a new code arrives with its words.

Since P12c-8 it reads findings too. A ``Finding`` is worded by the template
``finding.<wording or code>``, from the keys of its ``context`` -- a dict
literal, so this test can read them -- and from ``reason`` when it carries the
refusal it reports. Until P12c-8 a finding carried only an English sentence,
which every report and panel showed whatever the language. The codes still in
that state are frozen in ``unworded_findings.py``, and that list may only
shrink.
"""

from __future__ import annotations

import ast
import functools
from collections import defaultdict

from tests.conftest import PLUGIN_DIR, python_sources
from tests.structural.unworded_findings import UNWORDED

#: ``GeoCompError`` subclass -> the namespace it prefixes bare codes with,
#: mirroring ``code_namespace`` in :mod:`geocomp.core.errors`.
NAMESPACES = {
    "GeoCompError": "geocomp",
    "ValidationError": "validation",
    "DataError": "data",
    "ComputationError": "computation",
    "EngineError": "engine",
    "EngineMissingError": "engine",
    "EngineAbsentError": "computation",
    "StorageError": "storage",
    # The field book's per-row refusal, a DataError reported as a finding.
    "_RowError": "data",
}

PLACEHOLDERS = ("%1", "%2", "%3", "%4", "%5", "%6")

#: Templates written ahead of the code that raises them, with the phase that
#: will. Deliberately narrow: a template with no raiser is usually a typo in the
#: code string, and "it is for later" has to be claimed rather than assumed.
#: Held honest from both sides -- an entry here whose code *is* now raised fails
#: the test too, so the list cannot quietly outlive its reason.
PLANNED_CODES = {
    "engine.not_installed": (
        "Raised by the engine adapters, which arrive in phase P6 (DynAdjust) and P7 "
        "(RTKLIB). The wording exists from P0 because FR-306 requires the missing-engine "
        "path to be a disabled operation with an offer to install, not a crash."
    ),
}


@functools.cache
def _raised_codes() -> dict[str, list[set[str]]]:
    """Map ``namespace.code`` to the context keys supplied at each raising site.

    A list rather than a union: two sites raising the same code with different
    context is exactly the case a template can get wrong.
    """
    found: dict[str, list[set[str]]] = defaultdict(list)
    # The whole package. It grew a directory at a time -- `io` in P8b, whose
    # templates were reported stale because only `core` was read; `services` in
    # P10c; `algorithms` and the engine manager in P12c-6 -- and each time the
    # directories left out held codes a user read as a code. Since P12c-7,
    # when the engine package's 81 got templates, nothing is left out.
    sources = python_sources(PLUGIN_DIR)
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            namespace = NAMESPACES.get(node.func.id)
            if namespace is None or not node.args:
                continue
            first = node.args[0]
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            code = first.value if "." in first.value else f"{namespace}.{first.value}"
            found[code].append({keyword.arg for keyword in node.keywords if keyword.arg})
        for code, keys in _finding_sites(tree):
            found[code].append(keys)
    return dict(found)


def _imports_finding(tree: ast.AST) -> bool:
    """Whether the module's ``Finding`` is :class:`geocomp.core.findings.Finding`.

    The monitoring comparison has a ``Finding`` of its own, worded by
    ``reports/monitoring.py``; it is not this one.
    """
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "geocomp.core.findings"
        and any(alias.name == "Finding" for alias in node.names)
        for node in ast.walk(tree)
    )


def _finding_template(node: ast.Call) -> str | None:
    """``finding.<wording or code>`` for a ``Finding(...)`` call, or ``None`` if unreadable."""
    keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
    for candidate in (keywords.get("wording"), keywords.get("code"), *node.args[:1]):
        if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
            return f"finding.{candidate.value}"
    return None


def _finding_keys(node: ast.Call) -> set[str] | None:
    """The context keys a ``Finding(...)`` call supplies, or ``None`` if unreadable."""
    keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
    context = keywords.get("context")
    keys: set[str] = set()
    if context is not None:
        if not isinstance(context, ast.Dict) or not all(
            isinstance(key, ast.Constant) and isinstance(key.value, str) for key in context.keys
        ):
            return None
        keys = {key.value for key in context.keys}
    if "error" in keywords:
        keys.add("reason")
    return keys


def _finding_sites(tree: ast.AST):
    if not _imports_finding(tree):
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code, keys = _finding_template(node), _finding_keys(node)
            if code is not None and keys is not None:
                yield code, keys


@functools.cache
def _unreadable_findings() -> list[str]:
    """``Finding(...)`` calls whose template or context keys the source does not show."""
    problems = []
    for path in python_sources(PLUGIN_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if not _imports_finding(tree):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Finding":
                if _finding_template(node) is None or _finding_keys(node) is None:
                    problems.append(f"{path.relative_to(PLUGIN_DIR.parent)}:{node.lineno}")
    return problems


@functools.cache
def _declared_templates() -> dict[str, tuple[str, tuple[str, ...], str]]:
    """Map code -> (source string, interpolated keys, file) from the sources.

    Read as source rather than imported because the presentation layer imports
    Qt, and this check must run in the QGIS-free tier where a missing template
    is cheapest to notice.
    """
    templates: dict[str, tuple[str, tuple[str, ...], str]] = {}
    for path in python_sources(PLUGIN_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values, strict=True):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                if not (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Name)
                    and value.func.id == "MessageTemplate"
                ):
                    continue
                arguments = [a.value for a in value.args if isinstance(a, ast.Constant)]
                if not arguments:
                    continue
                templates[key.value] = (
                    arguments[0],
                    tuple(str(a) for a in arguments[1:]),
                    str(path.relative_to(PLUGIN_DIR.parent)),
                )
    return templates


def test_the_extractors_find_both_sides():
    """Guards the test itself: both halves must find something, or every
    assertion below passes vacuously."""
    assert len(_raised_codes()) > 20
    assert len(_declared_templates()) > 20


def test_every_template_interpolates_keys_the_raising_site_supplies():
    problems: list[str] = []
    raised = _raised_codes()

    for code, (_source, keys, path) in sorted(_declared_templates().items()):
        sites = raised.get(code)
        if sites is None:
            # Covered by its own test below; not a key problem.
            continue
        for supplied in sites:
            unsupplied = [key for key in keys if key not in supplied]
            if unsupplied:
                problems.append(
                    f"{path}: template for {code} interpolates {unsupplied}, which one of "
                    f"its raising sites does not supply (it supplies {sorted(supplied)}). "
                    "The user would read '(not set)' there."
                )

    assert not problems, "\n".join(problems)


def test_every_template_has_one_placeholder_per_key():
    """``%1``..``%n`` and the key list are positional; a mismatch either drops a
    value or renders a literal '%3'."""
    problems: list[str] = []
    for code, (source, keys, path) in sorted(_declared_templates().items()):
        used = [token for token in PLACEHOLDERS if token in source]
        expected = [f"%{index}" for index in range(1, len(keys) + 1)]
        if used != expected:
            problems.append(
                f"{path}: template for {code} names {len(keys)} key(s) {list(keys)} but its "
                f"text uses {used}; expected exactly {expected}"
            )
    assert not problems, "\n".join(problems)


def test_no_template_exists_for_a_code_nothing_raises():
    """A stale template is dead weight that still has to be translated."""
    raised = _raised_codes()
    stale = [
        f"{path}: {code}"
        for code, (_source, _keys, path) in sorted(_declared_templates().items())
        if code not in raised and code not in PLANNED_CODES
    ]
    assert not stale, (
        "Templates for codes no code raises. Remove them, fix the code they name, or -- if "
        "the raiser genuinely arrives in a later phase -- record that in PLANNED_CODES:\n"
        + "\n".join(stale)
    )


def test_the_planned_list_does_not_outlive_its_reason():
    """Once the phase lands and the code is raised, the exemption must go."""
    raised = _raised_codes()
    arrived = sorted(code for code in PLANNED_CODES if code in raised)
    assert not arrived, (
        "These codes are now raised, so their PLANNED_CODES entries are obsolete: "
        + ", ".join(arrived)
    )


def test_every_code_raised_has_words():
    """NFR-006: a code with no template reaches the user as the code itself.

    No exemption remains for an error. P12c-7 froze the 457 codes it found
    without words in a list that could only shrink, and removed the list once
    it was empty. A finding's code is exempt only while it is in
    ``unworded_findings.py``, P12c-8's own shrinking list.
    """
    declared = _declared_templates()
    without = sorted(
        code for code in _raised_codes() if code not in declared and code not in UNWORDED
    )
    assert not without, (
        "Raised or reported with no MessageTemplate, so a user would read the code itself, "
        "or a finding's English (NFR-006, FR-091). Write its template beside the algorithms "
        "that show it:\n" + "\n".join(without)
    )


def test_the_unworded_findings_only_shrink():
    """An entry whose finding gained a template, or is no longer made, must go."""
    declared = _declared_templates()
    made = set(_raised_codes())
    worded = sorted(code for code in UNWORDED if code in declared)
    gone = sorted(code for code in UNWORDED if code not in made)
    assert not worded, "Worded now; remove from unworded_findings.py: " + ", ".join(worded)
    assert not gone, "No longer made; remove from unworded_findings.py: " + ", ".join(gone)


def test_every_finding_shows_its_template_and_keys():
    """The checks above read a finding's template and context from its source.

    A code computed at run time, or a context built elsewhere and passed in,
    would let a finding escape them. Name the template with ``wording=``, and
    write the context as a dict literal.
    """
    assert not _unreadable_findings(), (
        "Findings whose template or context keys this test cannot read:\n"
        + "\n".join(_unreadable_findings())
    )


#: Context keys that carry an engine's own last word.
DIAGNOSTIC_KEYS = ("diagnostic", "message")


def test_an_engine_failure_shows_the_engines_own_message():
    """FR-305 and ``specs/08`` section 9: the engine's diagnostic reaches the user.

    Until P12c-7 *GNSS processing* rendered RTKLIB's run failures through a
    template that did not exist, and the message the engine adapter had
    carefully extracted was on the error and nowhere on the screen. A code
    whose every raise site carries one must have a template that shows it.
    """
    declared = _declared_templates()
    problems = []
    for code, sites in sorted(_raised_codes().items()):
        carried = [key for key in DIAGNOSTIC_KEYS if all(key in site for site in sites)]
        if not carried:
            continue
        template = declared.get(code)
        if template is None or not any(key in template[1] for key in carried):
            problems.append(f"{code}: carries {carried}, which its template does not show")
    assert not problems, "\n".join(problems)


def test_the_engine_failures_are_found():
    """Guards the test above: it passes vacuously if it finds nothing."""
    carriers = {
        code
        for code, sites in _raised_codes().items()
        if any(all(key in site for site in sites) for key in DIAGNOSTIC_KEYS)
    }
    assert {"engine.rtklib_run_failed", "computation.dynadjust_stage_failed"} <= carriers
