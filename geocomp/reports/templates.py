# SPDX-License-Identifier: GPL-2.0-or-later
"""Template loading and substitution for reports (FR-931, FR-066).

``specs/19-visualization.md`` section 7.3: reports are template-driven from the
templates directory configured in Global Settings, so an organisation can apply
its own layout and branding.

**The substitution is deliberately not a template language.** Tokens are
``{{name}}`` and nothing else -- no expressions, no loops, no conditionals, no
attribute access. Three reasons, in order of weight:

1. A template is a *file the user supplies*. A template language is an
   execution engine, and pointing one at a file from an organisation's shared
   drive is a way to run whatever is in that file.
2. ``str.format`` cannot be used at all: a report template is full of CSS, and
   CSS is full of braces.
3. A report is a technical deliverable. The parts that vary are sections of
   already-rendered HTML, and a template that could *compute* would invite
   putting the computation there instead of in the code that is tested.

An unknown token is an error rather than an empty string: a template that
silently drops the statistics section produces a report that looks complete and
is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from geocomp.core.errors import ValidationError

__all__ = [
    "TEMPLATE_DIR",
    "Template",
    "load_template",
    "render",
]

#: Where the shipped templates live. A user's own directory, from Global
#: Settings, is searched first.
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "resources" / "templates"

_TOKEN = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")


@dataclass(frozen=True)
class Template:
    """One template: its text, and where it came from.

    The source is carried because a report rendered from an organisation's
    template and one rendered from the shipped default are different documents,
    and a reader should be able to tell which they are holding.
    """

    text: str
    source: Path | None = None

    @property
    def tokens(self) -> frozenset[str]:
        return frozenset(_TOKEN.findall(self.text))

    @property
    def is_shipped(self) -> bool:
        return self.source is None or self.source.parent == TEMPLATE_DIR


def load_template(name: str, *, directory: str | Path | None = None) -> Template:
    """Load *name* from *directory*, falling back to the shipped template.

    Args:
        name: A bare file name such as ``adjustment.html``. Anything with a path
            separator is refused: a template name is configuration, and a
            configuration value that can name ``../../etc/passwd`` is a way to
            read a file the user did not intend to publish into a report.
    """
    if "/" in name or "\\" in name or name.startswith("."):
        raise ValidationError(
            "template_name_not_bare",
            received=name,
            expected="a bare file name such as 'adjustment.html', with no path",
        )

    if directory:
        candidate = Path(directory) / name
        if candidate.is_file():
            return Template(candidate.read_text(encoding="utf-8"), candidate)

    shipped = TEMPLATE_DIR / name
    if not shipped.is_file():
        raise ValidationError(
            "template_not_found",
            received=name,
            expected=(
                f"a template in the configured directory or among the shipped ones: "
                f"{', '.join(sorted(p.name for p in TEMPLATE_DIR.glob('*.html'))) or '(none)'}"
            ),
        )
    return Template(shipped.read_text(encoding="utf-8"), shipped)


def render(template: Template, sections: dict[str, str]) -> str:
    """Substitute *sections* into *template*.

    Raises:
        ValidationError: ``template_unknown_token`` when the template asks for a
            section that does not exist. Not an empty string: a template that
            silently drops the statistics produces a report that looks complete
            and is not.
    """
    missing = sorted(template.tokens - set(sections))
    if missing:
        raise ValidationError(
            "template_unknown_token",
            source=str(template.source) if template.source else "(inline)",
            received=missing,
            expected=f"tokens among: {', '.join(sorted(sections))}",
        )

    def replace(match: re.Match[str]) -> str:
        return sections[match.group(1)]

    return _TOKEN.sub(replace, template.text)


def unused_sections(template: Template, sections: dict[str, str]) -> list[str]:
    """Sections the template does not place.

    Reported rather than ignored: an organisation's template that omits the
    reliability section is making an editorial choice, and it should be a
    visible one -- ``specs/19`` section 7.1 lists reliability among the sections
    a defensible report carries.
    """
    return sorted(set(sections) - template.tokens)
