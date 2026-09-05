# SPDX-License-Identifier: GPL-2.0-or-later
"""Layered settings resolution, FR-068 (specs/15 section 2.3).

The rule under test: ``run -> project -> global -> built-in default``, with the
origin scope recoverable. The origin is what makes a result explicable months
later, so it is tested as carefully as the value.
"""

from __future__ import annotations

from geocomp.core.settings_def import Scope
from geocomp.core.settings_resolution import resolve, resolve_value


def readers(run=None, project=None, global_=None):
    """Build a reader mapping from plain dicts, omitting absent scopes."""
    mapping = {}
    if run is not None:
        mapping[Scope.RUN] = run.get
    if project is not None:
        mapping[Scope.PROJECT] = project.get
    if global_ is not None:
        mapping[Scope.GLOBAL] = global_.get
    return mapping


KEY = "interface.coordinate_decimals"


class TestPrecedence:
    def test_falls_back_to_the_built_in_default(self):
        result = resolve(KEY, readers(run={}, project={}, global_={}))
        assert result.value == 4
        assert result.scope is Scope.DEFAULT
        assert result.is_default

    def test_global_beats_the_default(self):
        result = resolve(KEY, readers(global_={KEY: 6}))
        assert (result.value, result.scope) == (6, Scope.GLOBAL)

    def test_project_beats_global(self):
        result = resolve(KEY, readers(project={KEY: 3}, global_={KEY: 6}))
        assert (result.value, result.scope) == (3, Scope.PROJECT)

    def test_run_beats_everything(self):
        result = resolve(KEY, readers(run={KEY: 1}, project={KEY: 3}, global_={KEY: 6}))
        assert (result.value, result.scope) == (1, Scope.RUN)

    def test_a_missing_scope_reader_is_simply_skipped(self):
        """A caller with no project open omits the project reader."""
        result = resolve(KEY, readers(global_={KEY: 6}))
        assert (result.value, result.scope) == (6, Scope.GLOBAL)


class TestOriginTracking:
    def test_overridden_records_every_contributing_scope_in_order(self):
        result = resolve(KEY, readers(project={KEY: 3}, global_={KEY: 6}))
        assert result.overridden == ((Scope.PROJECT, 3), (Scope.GLOBAL, 6))
        assert result.is_overridden

    def test_a_single_contributor_is_not_an_override(self):
        result = resolve(KEY, readers(global_={KEY: 6}))
        assert not result.is_overridden

    def test_the_default_alone_is_not_an_override(self):
        result = resolve(KEY, readers(global_={}))
        assert not result.is_overridden


class TestScopeRestrictions:
    def test_a_global_only_setting_ignores_a_project_value(self):
        """interface.language is global-only; a project value must not leak in."""
        result = resolve(
            "interface.language",
            readers(project={"interface.language": "es"}, global_={"interface.language": "pt_BR"}),
        )
        assert (result.value, result.scope) == ("pt_BR", Scope.GLOBAL)

    def test_a_global_only_setting_with_only_a_project_value_falls_to_default(self):
        result = resolve("interface.language", readers(project={"interface.language": "es"}))
        assert (result.value, result.scope) == ("system", Scope.DEFAULT)


class TestCorruptValues:
    def test_an_invalid_value_falls_through_to_the_next_scope(self):
        """A corrupt entry in one scope must not make the setting unreadable."""
        result = resolve(KEY, readers(project={KEY: 999}, global_={KEY: 6}))
        assert (result.value, result.scope) == (6, Scope.GLOBAL)

    def test_an_invalid_value_in_every_scope_falls_through_to_the_default(self):
        result = resolve(KEY, readers(project={KEY: 999}, global_={KEY: -5}))
        assert (result.value, result.scope) == (4, Scope.DEFAULT)

    def test_validation_can_be_disabled_for_diagnostics(self):
        result = resolve(KEY, readers(global_={KEY: 999}), validate=False)
        assert (result.value, result.scope) == (999, Scope.GLOBAL)

    def test_none_means_unset_not_a_stored_value(self):
        result = resolve(KEY, readers(project={KEY: None}, global_={KEY: 6}))
        assert (result.value, result.scope) == (6, Scope.GLOBAL)


def test_resolve_value_returns_only_the_value():
    assert resolve_value(KEY, readers(global_={KEY: 6})) == 6
