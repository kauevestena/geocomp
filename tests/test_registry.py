# SPDX-License-Identifier: GPL-2.0-or-later
"""The registry: algorithms and menu windows (ADR-0005, ADR-0010)."""

from __future__ import annotations

import pytest

from geocomp.registry import (
    ALGORITHMS,
    MENU_GROUPS,
    NESTING_MENUS,
    PROCESSING_GROUPS,
    PROVIDER_ID,
    TOOLBOX_ONLY_JUSTIFICATIONS,
    WINDOWS,
    AlgorithmSpec,
    WindowSpec,
    algorithms_in_group,
    algorithms_in_menu,
    algorithms_in_submenu,
    algorithms_run_by_windows,
    entries_in_menu,
    entries_in_submenu,
    submenus_in_menu,
    window_named,
    windows_in_menu,
)

#: Every algorithm id published so far (FR-032). Saved models, scripts and batch
#: files store these, so one leaving this set breaks a user's saved work. **An id
#: is removed from here only together with a deprecated alias that still
#: resolves it**, which GeoComp has not needed yet: none has been renamed.
PUBLISHED_IDS = frozenset(
    {
        "analysis_dynadjust_adjust",
        "analysis_dynadjust_compare",
        "analysis_dynadjust_run_prepared",
        "analysis_network_adjust",
        "analysis_network_inspect",
        "analysis_network_preanalysis",
        "gnss_absolute_kinematic",
        "gnss_absolute_static",
        "gnss_batch",
        "gnss_build_baselines",
        "gnss_compare_configurations",
        "gnss_download_products",
        "gnss_relative_kinematic",
        "gnss_relative_static",
        "gnss_scan_sessions",
        "gravimetry_network",
        "gravimetry_preprocess",
        "integration_gnss_level",
        "integration_gnss_total_station",
        "integration_multiple",
        "integration_total_station_level",
        "levelling_closures",
        "levelling_equal_sights",
        "levelling_equidistant_sights",
        "levelling_extreme_sights",
        "levelling_import",
        "levelling_network",
        "monitoring_compare_epochs",
        "monitoring_report",
        "monitoring_time_series",
        "project_basemap",
        "project_export",
        "project_export_postgis",
        "project_import_postgis",
        "project_install_engine",
        "project_package_engine_problem",
        "project_print_layout",
        "project_report",
        "project_store",
        "project_system_report",
        "project_tutorial_dataset",
        "totalstation_import_fieldbook",
        "totalstation_intersection",
        "totalstation_network",
        "totalstation_preprocess",
        "totalstation_radiation",
        "totalstation_resection",
        "totalstation_traverse",
        "totalstation_trig_levelling",
    }
)


class TestIdentity:
    def test_no_published_id_has_gone(self):
        """FR-032: an id once published stays. A new one is added here when it
        arrives; one that disappears needs an alias first."""
        names = {spec.name for spec in ALGORITHMS}
        assert sorted(PUBLISHED_IDS - names) == []
        assert sorted(names - PUBLISHED_IDS) == [], "a new algorithm: add its id to PUBLISHED_IDS"

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
    def test_the_menu_presents_exactly_the_specified_entries(self):
        """FR-003, matching research_project/fig/menu_estrutura.png plus the two
        entries the requirement was amended to include.

        The figure shows five technique submenus and Global Settings. **Analysis**
        (P2) holds the operations belonging to no single technique -- inspection,
        pre-analysis, adjustment -- which specs/15 section 1.1 left unplaced.
        **Project** (P5) holds operations on a project's *results* rather than on
        one technique's observations: export, report, store, base map, and the
        system report and tutorial dataset that had been toolbox-only since P0.
        Both were appended rather than inserted, so the figure's order is intact.
        """
        ordered = [group.id for group in sorted(MENU_GROUPS, key=lambda g: g.order)]
        assert ordered == [
            "total_station",
            "level",
            "gnss",
            "gravimetry",
            "integration",
            "analysis",
            "project",
            "global_settings",
        ]

    def test_the_five_technique_submenus_come_first_and_in_the_figure_order(self):
        """Analysis was appended, not inserted: the figure's order is intact."""
        ordered = [group.id for group in sorted(MENU_GROUPS, key=lambda g: g.order)]
        assert ordered[:5] == ["total_station", "level", "gnss", "gravimetry", "integration"]

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
        """An algorithm no window runs and no launcher opens is reviewed and written down."""
        by_window = algorithms_run_by_windows()
        for spec in ALGORITHMS:
            if spec.menu is None and spec.name not in by_window:
                assert spec.name in TOOLBOX_ONLY_JUSTIFICATIONS, spec.name
                assert len(TOOLBOX_ONLY_JUSTIFICATIONS[spec.name]) > 40

    def test_the_toolbox_only_list_stays_small(self):
        """A growing exception list means the menu is drifting from the algorithms."""
        assert len(TOOLBOX_ONLY_JUSTIFICATIONS) <= 3

    def test_no_stale_justification_remains(self):
        names = {spec.name for spec in ALGORITHMS}
        for justified in TOOLBOX_ONLY_JUSTIFICATIONS:
            assert justified in names, f"{justified} is justified but not registered"


#: The algorithms that still have a legacy launcher: a menu item opening their
#: Processing dialog, as every item did under ADR-0005. ROADMAP phase P14
#: rebuilds the menu group by group, and this set **may only shrink**: an item
#: leaves it when a window takes its place, and an algorithm added from now on
#: is reached through a window, not given a launcher.
LEGACY_LAUNCHERS = frozenset(
    {
        "analysis_dynadjust_adjust",
        "analysis_dynadjust_compare",
        "analysis_dynadjust_run_prepared",
        "analysis_network_adjust",
        "analysis_network_inspect",
        "analysis_network_preanalysis",
        "gnss_absolute_kinematic",
        "gnss_absolute_static",
        "gnss_batch",
        "gnss_build_baselines",
        "gnss_compare_configurations",
        "gnss_download_products",
        "gnss_relative_kinematic",
        "gnss_relative_static",
        "gnss_scan_sessions",
        "gravimetry_network",
        "gravimetry_preprocess",
        "integration_gnss_level",
        "integration_gnss_total_station",
        "integration_multiple",
        "integration_total_station_level",
        "monitoring_compare_epochs",
        "monitoring_report",
        "monitoring_time_series",
        "project_basemap",
        "project_export",
        "project_export_postgis",
        "project_import_postgis",
        "project_install_engine",
        "project_package_engine_problem",
        "project_print_layout",
        "project_report",
        "project_store",
        "project_system_report",
        "project_tutorial_dataset",
    }
)


class TestWindows:
    """ADR-0010: the menu's items are windows, each running declared algorithms."""

    def test_the_legacy_launchers_only_shrink(self):
        launched = {spec.name for spec in ALGORITHMS if spec.menu is not None}
        added = launched - LEGACY_LAUNCHERS
        assert not added, (
            f"{sorted(added)} gained a menu launcher. Since ADR-0010 an algorithm is reached "
            "from the menu through a window that runs it."
        )
        assert launched == LEGACY_LAUNCHERS, (
            "a launcher was replaced: take it out of LEGACY_LAUNCHERS as well, which is the "
            f"record of the menu's rebuilding ({sorted(LEGACY_LAUNCHERS - launched)})"
        )

    def test_phases_p14a_and_p14b_made_the_total_station_menu_windows(self):
        """P14a built four, P14b the other four: no Total Station item is a launcher."""
        assert [spec.name for spec in windows_in_menu("total_station")] == [
            "totalstation_fieldbook",
            "totalstation_preprocess",
            "totalstation_traverse",
            "totalstation_resection",
            "totalstation_intersection",
            "totalstation_network",
            "totalstation_trig_levelling",
            "totalstation_radiation",
        ]
        assert not [spec for spec in ALGORITHMS if spec.menu == "total_station"]

    def test_phase_p14c_made_the_level_menu_windows(self):
        """The Level submenu, in the order its launchers stood: no item is a launcher."""
        assert [spec.name for spec in windows_in_menu("level")] == [
            "levelling_fieldbook",
            "levelling_equal_sights",
            "levelling_equidistant_sights",
            "levelling_extreme_sights",
            "levelling_closures",
            "levelling_network",
        ]
        assert not [spec for spec in ALGORITHMS if spec.menu == "level"]

    def test_the_total_station_menu_keeps_its_order_once_rebuilt(self):
        """The windows take the positions their operations' launchers had."""
        assert [entry.name for entry in entries_in_menu("total_station")] == [
            "totalstation_fieldbook",
            "totalstation_preprocess",
            "totalstation_traverse",
            "totalstation_resection",
            "totalstation_intersection",
            "totalstation_network",
            "totalstation_trig_levelling",
            "totalstation_radiation",
        ]

    @pytest.mark.parametrize("spec", WINDOWS, ids=lambda spec: spec.name)
    def test_a_window_runs_registered_algorithms_and_cites_a_requirement(self, spec):
        names = {algorithm.name for algorithm in ALGORITHMS}
        assert spec.algorithms and set(spec.algorithms) <= names
        assert spec.requirement.startswith("FR-")
        assert all(algorithm_id.startswith(f"{PROVIDER_ID}:") for algorithm_id in spec.algorithm_ids)

    @pytest.mark.parametrize("spec", WINDOWS, ids=lambda spec: spec.name)
    def test_a_window_runs_its_techniques_algorithms_only(self, spec):
        """A Total Station window that ran a GNSS algorithm would be a second
        route into another technique's job, which the job files cannot hold."""
        groups = {algorithm.name: algorithm.group for algorithm in ALGORITHMS}
        group = {"total_station": "totalstation", "levelling": "levelling"}[spec.technique]
        assert {groups[name] for name in spec.algorithms} == {group}

    def test_the_windows_of_a_technique_share_its_job(self):
        assert {spec.technique for spec in windows_in_menu("total_station")} == {"total_station"}
        assert {spec.technique for spec in windows_in_menu("level")} == {"levelling"}

    def test_names_are_unique_across_windows_and_algorithms(self):
        """The menu item's object name is made from it, whichever kind it is."""
        windows = [spec.name for spec in WINDOWS]
        assert len(set(windows)) == len(windows)

    def test_lookups(self):
        assert window_named("totalstation_traverse").class_name == "TraverseWindow"
        assert window_named("does_not_exist") is None
        assert entries_in_submenu("gnss", "absolute") == tuple(
            algorithms_in_submenu("gnss", "absolute")
        )
        assert windows_in_menu("gnss") == ()

    def test_a_window_needs_an_algorithm(self):
        spec = WindowSpec("w", "level", 1, "m", "C", (), "FR-010", "level")
        assert spec.algorithm_ids == ()


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


class TestNesting:
    """specs/15 section 1: the GeoComp menu is one level deep, with one
    exception.

    GNSS has four processing modes that are two branches of two -- absolute and
    relative, each static and kinematic -- and a flat menu would have to read
    "Absolute static", "Absolute kinematic" and so on, four entries whose first
    word is the only thing distinguishing them in pairs. The second level is
    there because "Static" alone names nothing; it is not there because nesting
    is tidier.

    An exception nobody guards is an exception that spreads by imitation, so
    the rule is enforced twice: :func:`geocomp.registry._validate_module` raises
    at import, and this holds the permitted set small and justified.
    """

    def test_only_declared_menus_may_nest(self):
        offenders = [
            spec.name
            for spec in ALGORITHMS
            if spec.submenu and spec.menu not in NESTING_MENUS
        ]
        assert not offenders, (
            "these algorithms nest under a menu not listed in NESTING_MENUS: "
            f"{sorted(offenders)}"
        )

    def test_the_exception_is_one_menu(self):
        """If this needs raising, the flat-menu rule has stopped being the
        rule and specs/15 section 1 should say so instead."""
        assert NESTING_MENUS == frozenset({"gnss"})

    def test_a_nesting_menu_actually_nests(self):
        """A menu declared able to nest but nesting nothing is a permission
        granted for no reason -- and one the next algorithm would inherit."""
        for menu_id in NESTING_MENUS:
            assert submenus_in_menu(menu_id), f"{menu_id} nests nothing"

    def test_the_gnss_submenus_are_the_two_the_specification_draws(self):
        """specs/11 puts absolute before relative, and the menu follows its
        figure rather than alphabetical order -- which here agree, so the
        order this asserts is the declaration's."""
        assert submenus_in_menu("gnss") == ("absolute", "relative")

    def test_every_nested_algorithm_is_reachable_through_its_submenu(self):
        """The two halves of the registry's nesting API have to agree: an
        algorithm carrying a submenu name that ``algorithms_in_submenu`` does
        not return under it would be declared and unreachable."""
        for menu_id in NESTING_MENUS:
            nested = {
                spec.name for spec in algorithms_in_menu(menu_id) if spec.submenu
            }
            reachable = {
                spec.name
                for submenu in submenus_in_menu(menu_id)
                for spec in algorithms_in_submenu(menu_id, submenu)
            }
            assert nested == reachable

    def test_algorithms_directly_under_a_nesting_menu_are_still_reachable(self):
        """Nesting is per algorithm, not per menu: Scan sessions, Download
        products, Build baselines, Batch process and Compare sit at the GNSS
        group's own level and must not disappear because four of their
        siblings nest."""
        flat = {spec.name for spec in algorithms_in_submenu("gnss", None)}
        assert flat == {
            "gnss_scan_sessions",
            "gnss_download_products",
            "gnss_build_baselines",
            "gnss_batch",
            "gnss_compare_configurations",
        }
