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
which every report and panel showed whatever the language. The findings in that
state were frozen in a list that could only shrink; two pull requests later it
was empty and was removed. A finding, like an error, arrives with its words.

Since P12c-37 it holds NFR-006's third part: a refusal says *what the user can
do about it*, not only what failed and why. "The relative humidity must lie
between 0 and 1; 1.4 was given" tells the user the rule; "Give it as a fraction,
not a percentage" tells them what to change. The test reads a remedy as a clause
that begins with an imperative -- "Give ...", "Check ...", "..., or turn the
correction off" -- which is how GeoComp's templates already say it where they
say it. It cannot judge whether the remedy is a good one, only that there is
one; that is still the review's job. When P12c-37 first counted, 322 of 641
refusals had none; they were frozen in a list that could only shrink, and four
pull requests later it was empty and was removed. There is no exemption: a new
refusal arrives with its remedy. Findings are not refusals -- a report's
observations about a result -- and are not held to it.
"""

from __future__ import annotations

import ast
import functools
import re
from collections import defaultdict

import pytest

from tests.conftest import PLUGIN_DIR, python_sources

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

PLACEHOLDERS = tuple(f"%{index}" for index in range(1, 10))

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
    """NFR-006 and FR-091: a code with no template reaches the user as the code
    itself, and a finding with none as the core's English.

    No exemption remains. P12c-7 froze the 457 error codes it found without
    words, and P12c-8 the 65 findings, each in a list that could only shrink;
    both lists were removed once empty.
    """
    declared = _declared_templates()
    without = sorted(code for code in _raised_codes() if code not in declared)
    assert not without, (
        "Raised or reported with no MessageTemplate, so a user would read the code itself, "
        "or a finding's English (NFR-006, FR-091). Write its template beside the algorithms "
        "that show it:\n" + "\n".join(without)
    )


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


#: A value written as text with at least this many words is a sentence, not data.
PROSE_WORDS = 3


def _prose(value: ast.expr) -> str | None:
    """The English a context value spells out at its raise site, or ``None`` if it is data."""
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        text = value.value
    elif isinstance(value, ast.JoinedStr):
        text = " ".join(part.value for part in value.values if isinstance(part, ast.Constant))
    else:
        return None
    return text if len(text.split()) >= PROSE_WORDS else None


@functools.cache
def _prose_keys() -> dict[str, dict[str, str]]:
    """Map code -> {key: "file:line"} for each context key some site fills with English prose."""
    found: dict[str, dict[str, str]] = defaultdict(dict)
    for path in python_sources(PLUGIN_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        where = str(path.relative_to(PLUGIN_DIR.parent))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            namespace = NAMESPACES.get(node.func.id)
            if namespace is not None and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    code = first.value if "." in first.value else f"{namespace}.{first.value}"
                    for keyword in node.keywords:
                        if keyword.arg and _prose(keyword.value):
                            found[code].setdefault(keyword.arg, f"{where}:{node.lineno}")
            elif node.func.id == "Finding" and _imports_finding(tree):
                code = _finding_template(node)
                keywords = {k.arg: k.value for k in node.keywords if k.arg}
                context = keywords.get("context")
                if code and isinstance(context, ast.Dict):
                    for key, value in zip(context.keys, context.values, strict=True):
                        if isinstance(key, ast.Constant) and _prose(value):
                            found[code].setdefault(key.value, f"{where}:{node.lineno}")
    return dict(found)


def test_no_template_interpolates_english_from_the_core():
    """FR-091: a translated sentence with the core's English inside it is half translated.

    Until P12c-9, 29 templates interpolated ``expected`` or a similar key that
    a raise site filled with a sentence -- "a whole number from 0 to 6", "a
    line starting or ending at B" -- so a Portuguese message carried an English
    clause. The template says the sentence; the core passes only data: ids,
    counts, numbers, lists. A key may still carry English for the developer's
    diagnostic, as long as no template reads it.
    """
    prose = _prose_keys()
    problems = []
    for code, (_source, keys, path) in sorted(_declared_templates().items()):
        for key in keys:
            if key in prose.get(code, {}):
                problems.append(
                    f"{path}: template for {code} interpolates '{key}', which "
                    f"{prose[code][key]} fills with English prose"
                )
    assert not problems, "\n".join(problems)


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


#: The verbs a remedy begins with in GeoComp's templates. A list rather than a
#: grammar because English imperatives look like every other verb; extend it
#: when a remedy is written with a verb it does not have, never by matching a
#: verb anywhere in the sentence.
REMEDY_VERBS = (
    "add", "adjust", "align", "allow", "apply", "ask", "assign", "attach", "bring", "build", "change",
    "check",
    "choose", "clear", "close", "compare", "complete", "compute", "configure", "connect", "convert",
    "copy", "correct", "decompress",
    "define", "delete", "disable", "do", "download", "drop", "edit", "enable", "enter",
    "exclude", "export", "fetch", "fill", "find", "fix", "free", "give", "grant", "hold",
    "import", "include", "increase", "inspect", "install", "keep", "leave", "let", "list",
    "load", "look", "lower", "make", "map", "mark", "measure", "merge", "move", "name", "observe",
    "open", "pass", "pick", "place", "point", "prepare", "process", "provide", "put", "raise",
    "re-activate",
    "re-export", "re-import", "re-measure", "re-run", "read", "reconnect", "record",
    "rebuild", "reduce", "remove", "rename", "repeat", "replace", "report", "reprocess",
    "rerun", "resolve", "restart", "restore", "retry", "rotate", "run", "save", "select", "set",
    "sight", "split", "start", "state", "supply", "survey", "swap", "tick", "transform", "treat",
    "try", "turn",
    "update", "use", "wait", "write",
)

#: An imperative where a clause starts: a sentence, or after a semicolon, a
#: colon, a dash, or "or"/"and" joining a second instruction. "Please" may lead.
_REMEDY = re.compile(
    r"(?:^|[.!?]\s+|;\s*|:\s+|--\s*|\u2014\s*|\bor\s+|\band\s+)(?:please\s+)?(?:"
    + "|".join(re.escape(verb) for verb in REMEDY_VERBS)
    + r")\b",
    re.IGNORECASE,
)

def _refusals() -> dict[str, str]:
    """Every error template, by code: what NFR-006 holds to a remedy."""
    return {
        code: source
        for code, (source, _keys, _file) in _declared_templates().items()
        if not code.startswith("finding.")
    }


def test_every_refusal_says_what_the_user_can_do():
    """NFR-006: what failed, why, *and what the user can do about it*."""
    without = sorted(
        code
        for code, source in _refusals().items()
        if not _REMEDY.search(source)
    )
    assert not without, (
        "These templates say what failed but not what the user can do about it "
        "(NFR-006). Add a clause that tells them -- 'Give ...', 'Check ...', "
        "'..., or ...' -- in the template and its translations:\n" + "\n".join(without)
    )


@pytest.mark.parametrize(
    ("source", "found"),
    [
        ("UTM zone %1 does not exist; give a zone from 1 to 60.", True),
        ("The file '%1' is empty. Check that it is the export you meant.", True),
        ("Connect them to a benchmark, or turn the correction off.", True),
        ("This is an internal error; please report it.", True),
        ("The relative humidity must lie between 0 and 1; %1 was given.", False),
        ("There is no instrument profile '%1'; expected %2.", False),
        # A verb inside a sentence is not an instruction.
        ("The engine could not open the file it was given.", False),
    ],
)
def test_a_remedy_is_an_imperative_where_a_clause_starts(source: str, found: bool):
    assert bool(_REMEDY.search(source)) is found
