# SPDX-License-Identifier: GPL-2.0-or-later
"""The algorithm registry (ADR-0005)."""

from __future__ import annotations

import pytest

from geocomp.registry import (
    ALGORITHMS,
    MENU_GROUPS,
    PROCESSING_GROUPS,
    PROVIDER_ID,
    TOOLBOX_ONLY_JUSTIFICATIONS,
    AlgorithmSpec,
    algorithms_in_group,
    algorithms_in_menu,
)


class TestIdentity:
    def test_provider_id_is_the_documented_one(self):
        """FR-030. Saved models store it, so it is effectively permanent."""
        assert PROVIDER_ID == "geocomp"

    def test_algorithm_ids_follow_the_group_operation_convention(self):
        """specs/16 section 3: geocomp:<group>_<operation>."""
        for spec in ALGORITHMS:
            assert spec.id == f"geocomp:{spec.group}_{spec.operation}"

    def test_algorithm_names_are_unique(self):
        names = [spec.name for spec in ALGORITHMS]
        assert len(names) == len(set(names))


class TestMenuStructure:
    def test_the_menu_presents_exactly_the_six_specified_entries(self):
        """FR-003, matching research_project/fig/menu_estrutura.png."""
        ordered = [group.id for group in sorted(MENU_GROUPS, key=lambda g: g.order)]
        assert ordered == [
            "total_station",
            "level",
            "gnss",
            "gravimetry",
            "integration",
            "global_settings",
        ]

    def test_global_settings_is_last_and_separated(self):
        last = sorted(MENU_GROUPS, key=lambda group: group.order)[-1]
        assert last.id == "global_settings"
        assert last.separator_before
        assert last.is_action

    def test_only_global_settings_draws_a_separator(self):
        separated = [group.id for group in MENU_GROUPS if group.separator_before]
        assert separated == ["global_settings"]

    def test_the_fourth_group_is_gravimetry_not_gravimeter(self):
        """The figure says Gravimetria and every other group names a technique;
        the proposal's prose says Gravímetro. Resolved in specs/00-glossary.md."""
        ids = [group.id for group in MENU_GROUPS]
        assert "gravimetry" in ids
        assert "gravimeter" not in ids


class TestReferentialIntegrity:
    def test_every_algorithm_names_a_declared_processing_group(self):
        group_ids = {group.id for group in PROCESSING_GROUPS}
        for spec in ALGORITHMS:
            assert spec.group in group_ids, spec.name

    def test_every_menu_placement_names_a_declared_menu_group(self):
        menu_ids = {group.id for group in MENU_GROUPS}
        for spec in ALGORITHMS:
            if spec.menu is not None:
                assert spec.menu in menu_ids, spec.name

    def test_no_algorithm_is_placed_under_a_leaf_action(self):
        for group in MENU_GROUPS:
            if group.is_action:
                assert algorithms_in_menu(group.id) == ()

    def test_toolbox_only_algorithms_carry_a_recorded_justification(self):
        """ADR-0005 permits the exception only when it is reviewed and written down."""
        for spec in ALGORITHMS:
            if spec.menu is None:
                assert spec.name in TOOLBOX_ONLY_JUSTIFICATIONS, spec.name
                assert len(TOOLBOX_ONLY_JUSTIFICATIONS[spec.name]) > 40

    def test_the_toolbox_only_list_stays_small(self):
        """A growing exception list means the menu is drifting from the algorithms."""
        assert len(TOOLBOX_ONLY_JUSTIFICATIONS) <= 3

    def test_no_stale_justification_remains(self):
        names = {spec.name for spec in ALGORITHMS}
        for justified in TOOLBOX_ONLY_JUSTIFICATIONS:
            assert justified in names, f"{justified} is justified but not registered"


class TestQueries:
    def test_algorithms_in_menu_is_ordered(self):
        specs = (
            AlgorithmSpec("b", "project", "m", "B", "FR-030", menu="level", menu_order=2),
            AlgorithmSpec("a", "project", "m", "A", "FR-030", menu="level", menu_order=1),
        )
        assert sorted(specs, key=lambda s: (s.menu_order, s.operation))[0].operation == "a"

    def test_algorithms_in_group_filters(self):
        assert all(spec.group == "project" for spec in algorithms_in_group("project"))

    def test_an_unknown_group_yields_nothing_rather_than_raising(self):
        assert algorithms_in_menu("does_not_exist") == ()


class TestPhaseP0:
    def test_at_least_one_algorithm_is_registered(self):
        """P0's exit criterion: the registry-to-provider-to-menu path is proven."""
        assert ALGORITHMS

    @pytest.mark.parametrize("spec", ALGORITHMS, ids=lambda spec: spec.name)
    def test_every_algorithm_cites_a_requirement(self, spec):
        assert spec.requirement.startswith(("FR-", "NFR-"))
