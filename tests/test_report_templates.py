# SPDX-License-Identifier: GPL-2.0-or-later
"""Report templates (FR-931, FR-066).

``specs/19-visualization.md`` section 7.3. Templates are the half of the
reporting work that needs no Qt, so it is tested in the fast tier; the report
body itself phrases user-facing text and is tested in ``tests/qgis``.
"""

from __future__ import annotations

import pytest

from geocomp.core.errors import ValidationError
from geocomp.reports.templates import (
    TEMPLATE_DIR,
    Template,
    load_template,
    render,
    unused_sections,
)


class TestLoading:
    def test_the_shipped_template_exists_and_is_found(self):
        template = load_template("adjustment.html")
        assert template.is_shipped
        assert "{{statistics}}" in template.text

    def test_a_users_directory_wins(self, tmp_path):
        (tmp_path / "adjustment.html").write_text("<p>{{title}}</p>", encoding="utf-8")
        template = load_template("adjustment.html", directory=tmp_path)
        assert not template.is_shipped
        assert template.text == "<p>{{title}}</p>"

    def test_it_falls_back_to_the_shipped_one(self, tmp_path):
        template = load_template("adjustment.html", directory=tmp_path)
        assert template.is_shipped

    def test_an_unknown_template_is_refused_and_lists_what_exists(self):
        with pytest.raises(ValidationError) as caught:
            load_template("nonesuch.html")
        assert caught.value.code == "validation.template_not_found"
        assert "adjustment.html" in str(caught.value)

    @pytest.mark.parametrize(
        "name", ["../adjustment.html", "sub/adjustment.html", ".hidden", "a\\b.html"]
    )
    def test_a_template_name_must_be_bare(self, name):
        """A configuration value that can name ``../../etc/passwd`` is a way to
        read a file the user did not intend to publish into a report."""
        with pytest.raises(ValidationError) as caught:
            load_template(name)
        assert caught.value.code == "validation.template_name_not_bare"

    def test_the_shipped_directory_holds_only_html(self):
        assert {path.suffix for path in TEMPLATE_DIR.iterdir()} == {".html"}


class TestSubstitution:
    def test_tokens_are_replaced(self):
        template = Template("<h1>{{title}}</h1><p>{{body}}</p>")
        assert render(template, {"title": "T", "body": "B"}) == "<h1>T</h1><p>B</p>"

    def test_whitespace_inside_a_token_is_tolerated(self):
        assert render(Template("{{ title }}"), {"title": "T"}) == "T"

    def test_an_unknown_token_is_refused(self):
        """Not an empty string: a template that silently drops the statistics
        produces a report that looks complete and is not."""
        with pytest.raises(ValidationError) as caught:
            render(Template("{{nowhere}}"), {"title": "T"})
        assert caught.value.code == "validation.template_unknown_token"
        assert "nowhere" in str(caught.value)

    def test_css_braces_survive(self):
        """The reason this is not ``str.format``: a report template is full of
        CSS, and CSS is full of braces."""
        template = Template("<style>body{margin:0}</style>{{title}}")
        assert render(template, {"title": "T"}) == "<style>body{margin:0}</style>T"

    def test_there_is_no_expression_language(self):
        """A template is a file the user supplies. A template *language* is an
        execution engine pointed at it."""
        template = Template("{{title.upper()}}")
        assert template.tokens == frozenset()
        assert render(template, {"title": "t"}) == "{{title.upper()}}"

    def test_a_section_the_template_omits_is_reported(self):
        """An organisation's template that leaves out reliability is making an
        editorial choice, and it should be a visible one."""
        template = Template("{{title}}")
        assert unused_sections(template, {"title": "T", "reliability": "R"}) == [
            "reliability"
        ]

    def test_the_shipped_template_places_every_section(self):
        """Guards the shipped default against losing a section by an edit."""
        template = load_template("adjustment.html")
        expected = {
            "title",
            "style",
            "identification",
            "uncertainty_notice",
            "inputs",
            "parameters",
            "results",
            "statistics",
            "observation_results",
            "reliability",
            "ellipses",
            "provenance",
            "software",
        }
        assert template.tokens == expected
