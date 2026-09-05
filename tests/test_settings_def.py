# SPDX-License-Identifier: GPL-2.0-or-later
"""Setting declarations (specs/15 section 2)."""

from __future__ import annotations

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.settings_def import (
    SECTIONS,
    SETTINGS,
    Scope,
    SettingDef,
    SettingType,
    setting,
    settings_in_section,
)


class TestDeclarations:
    def test_every_setting_belongs_to_a_declared_section(self):
        section_ids = {section.id for section in SECTIONS}
        for definition in SETTINGS:
            assert definition.section in section_ids, definition.key

    def test_setting_keys_are_unique(self):
        keys = [definition.key for definition in SETTINGS]
        assert len(keys) == len(set(keys))

    def test_every_setting_cites_a_requirement(self):
        """Traceability is checkable only if each declaration carries its id."""
        for definition in SETTINGS:
            assert definition.requirement.startswith(("FR-", "NFR-")), definition.key

    def test_sections_are_ordered_equipment_first(self):
        """specs/15 section 2: equipment sections precede the cross-cutting ones."""
        ordered = sorted(SECTIONS, key=lambda section: section.order)
        equipment_flags = [section.is_equipment for section in ordered]
        assert equipment_flags == sorted(equipment_flags, reverse=True)

    def test_the_six_menu_relevant_equipment_sections_exist(self):
        ids = {section.id for section in SECTIONS}
        assert {"total_station", "level", "gnss", "gravimeter"} <= ids

    def test_interface_section_is_populated_in_this_phase(self):
        """FR-067 is closed by P0; the other sections fill in later phases."""
        assert settings_in_section("interface")

    def test_key_must_be_prefixed_with_its_section(self):
        with pytest.raises(ValueError):
            SettingDef(
                key="wrong.name",
                section="interface",
                type=SettingType.BOOL,
                default=True,
                requirement="FR-067",
            )

    def test_choice_default_must_be_among_the_choices(self):
        with pytest.raises(ValueError):
            SettingDef(
                key="interface.x",
                section="interface",
                type=SettingType.CHOICE,
                default="nope",
                choices=("a", "b"),
                requirement="FR-067",
            )


class TestScopes:
    def test_precedence_order_is_run_project_global_default(self):
        assert [scope.name for scope in Scope] == ["RUN", "PROJECT", "GLOBAL", "DEFAULT"]
        assert Scope.RUN.precedence < Scope.PROJECT.precedence < Scope.GLOBAL.precedence
        assert Scope.GLOBAL.precedence < Scope.DEFAULT.precedence

    def test_default_is_never_a_settable_scope(self):
        for definition in SETTINGS:
            assert Scope.DEFAULT not in definition.scopes, definition.key

    def test_language_is_global_only(self):
        """A per-project UI language would be surprising and serves no use case."""
        assert setting("interface.language").scopes == frozenset({Scope.GLOBAL})

    def test_mode_may_be_overridden_per_project_and_per_run(self):
        scopes = setting("interface.mode").scopes
        assert Scope.PROJECT in scopes and Scope.RUN in scopes


class TestValidation:
    def test_choice_rejects_an_unlisted_value(self):
        with pytest.raises(ValidationError) as caught:
            setting("interface.mode").validate("wizard")
        assert caught.value.code == "validation.setting_not_a_choice"

    def test_int_range_is_enforced_at_both_ends(self):
        definition = setting("interface.coordinate_decimals")
        with pytest.raises(ValidationError) as high:
            definition.validate(99)
        assert high.value.code == "validation.setting_above_maximum"
        with pytest.raises(ValidationError) as low:
            definition.validate(-1)
        assert low.value.code == "validation.setting_below_minimum"

    def test_bool_setting_rejects_a_non_bool(self):
        with pytest.raises(ValidationError):
            setting("interface.show_toolbar").validate("yes")

    def test_bool_is_not_accepted_as_an_int(self):
        """True == 1 in Python; a bool reaching an int setting is a bug, not a value."""
        with pytest.raises(ValidationError):
            setting("interface.coordinate_decimals").validate(True)

    def test_every_declared_default_validates(self):
        """A default that fails its own validation is a latent crash."""
        for definition in SETTINGS:
            definition.validate(definition.default)


def test_unknown_key_raises_key_error_not_geocomp_error():
    """An unknown key is a programming mistake, not something to show a user."""
    with pytest.raises(KeyError):
        setting("interface.does_not_exist")
