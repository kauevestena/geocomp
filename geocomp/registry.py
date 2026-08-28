# SPDX-License-Identifier: GPL-2.0-or-later
"""The algorithm registry: one declaration, three consumers.

ADR-0005 requires that every capability exist exactly once, as a Processing
algorithm, and that the GeoComp menu be *generated* from the algorithm set
rather than hand-built alongside it (FR-005).

This module is that single source. It is deliberately **pure data**: it names
algorithms by module path and class name rather than importing them. Three
consequences follow, and all three are the point:

* ``geocomp.provider`` imports and instantiates each entry.
* ``geocomp.gui.menu`` builds the GeoComp menu from the same entries, so a menu
  item cannot point at nothing and an algorithm cannot go unreachable.
* ``tests/structural/test_menu_algorithm_parity.py`` checks the correspondence
  **without a QGIS runtime**, because nothing here imports ``qgis``.

Adding an algorithm means adding an :class:`AlgorithmSpec` here. Forgetting to
is caught by the parity test, not discovered by a user.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ALGORITHMS",
    "CUSTOM_DIALOGS",
    "MENU_GROUPS",
    "PROCESSING_GROUPS",
    "PROVIDER_ID",
    "AlgorithmSpec",
    "MenuGroup",
    "ProcessingGroup",
    "algorithms_in_group",
    "algorithms_in_menu",
]

#: Provider id (FR-030). Stable: saved models and scripts store it.
PROVIDER_ID = "geocomp"


@dataclass(frozen=True)
class ProcessingGroup:
    """A group in the Processing toolbox (specs/16 section 2)."""

    id: str
    order: int

    @property
    def label_code(self) -> str:
        return f"group.{self.id}.label"


@dataclass(frozen=True)
class MenuGroup:
    """An entry in the GeoComp menu (specs/15 section 1, FR-003).

    Attributes:
        separator_before: Renders a separator above this entry. Only Global
            Settings sets it, matching ``fig/menu_estrutura.png``.
        is_action: The entry is a leaf action rather than a submenu.
    """

    id: str
    order: int
    separator_before: bool = False
    is_action: bool = False

    @property
    def label_code(self) -> str:
        return f"menu.{self.id}.label"


#: Processing toolbox groups, per specs/16 section 2. Ids are English and
#: stable; displayed names are translated.
PROCESSING_GROUPS: tuple[ProcessingGroup, ...] = (
    ProcessingGroup("totalstation", 10),
    ProcessingGroup("levelling", 20),
    ProcessingGroup("gnss", 30),
    ProcessingGroup("gravimetry", 40),
    ProcessingGroup("integration", 50),
    ProcessingGroup("analysis", 60),
    ProcessingGroup("monitoring", 70),
    ProcessingGroup("project", 80),
    ProcessingGroup("visualization", 90),
)

#: The GeoComp menu entries, in the order FR-003 specifies. The technique
#: submenus are populated by the phase that implements each module; they are
#: present but empty until then, which is why ``menu.py`` disables an empty one
#: rather than hiding it -- a user should be able to see that Gravimetry is
#: coming, not wonder whether it exists.
#:
#: **Project is the eighth entry, added in phase P5.** Six algorithms had
#: accumulated with no menu home: the system report, the tutorial dataset, and
#: P5's export, report, store and base map. Each was individually justifiable as
#: toolbox-only, and ``tests/test_registry.py`` was right to fail when the sixth
#: arrived -- six exceptions are not exceptions, they are a category, and the
#: honest answer to a category is an entry rather than a longer list of reasons
#: it does not need one.
#:
#: They share a description that is not a stretch: **operations on a project's
#: results rather than on one technique's observations.** Exporting, reporting
#: and storing a solution are identical whether it came from a total station, a
#: level, or P6's DynAdjust; a base map is context for any of them; and the
#: system report and tutorial dataset are the project's own housekeeping. Filing
#: any of them under a technique would say something false, and repeating them
#: under all five would break the one-item-per-algorithm correspondence
#: ADR-0005 rests on -- the same argument that produced the Analysis entry.
#:
#: Discoverability is the other half. A user who has just adjusted a network
#: wants the report; leaving it reachable only from the Processing toolbox is a
#: worse menu, not a purer one, in exactly the way ``specs/15`` section 1.1 says
#: of "Import field book".
#:
#: **Analysis is the seventh entry, added in phase P2.** ``specs/15`` section 1.1
#: left its placement open: network pre-analysis, inspection and the statistical
#: operations belong to no single survey technique, so filing them under one of
#: the five technique submenus would say something false about them. Placing
#: them under any *one* technique would also hide them from users of the other
#: four, and duplicating them across all five would break the one-item-per-
#: algorithm correspondence ADR-0005 rests on. A seventh entry is the only
#: option that leaves both intact, and FR-003 is amended to say seven rather
#: than being quietly contradicted by the code.
MENU_GROUPS: tuple[MenuGroup, ...] = (
    MenuGroup("total_station", 10),
    MenuGroup("level", 20),
    MenuGroup("gnss", 30),
    MenuGroup("gravimetry", 40),
    MenuGroup("integration", 50),
    MenuGroup("analysis", 60),
    MenuGroup("project", 65),
    MenuGroup("global_settings", 70, separator_before=True, is_action=True),
)


@dataclass(frozen=True)
class AlgorithmSpec:
    """One registered Processing algorithm.

    Attributes:
        group: A :class:`ProcessingGroup` id -- where it appears in the toolbox.
        operation: The operation part of the algorithm id.
        module / class_name: Where the implementation lives. Named as strings so
            this module stays importable without QGIS.
        menu: The :class:`MenuGroup` id it appears under, or ``None`` for a
            toolbox-only algorithm. ``None`` is permitted only for diagnostics
            and maintenance operations that belong to no survey technique; the
            parity test holds the exception list to exactly those declared in
            :data:`TOOLBOX_ONLY_JUSTIFICATIONS`.
        requirement: The requirement id this algorithm satisfies.
        menu_order: Position within its submenu.
    """

    operation: str
    group: str
    module: str
    class_name: str
    requirement: str
    menu: str | None = None
    menu_order: int = 0

    @property
    def name(self) -> str:
        """The algorithm name within the provider, e.g. ``project_system_report``."""
        return f"{self.group}_{self.operation}"

    @property
    def id(self) -> str:
        """The fully qualified id, e.g. ``geocomp:project_system_report`` (FR-032)."""
        return f"{PROVIDER_ID}:{self.name}"

    @property
    def label_code(self) -> str:
        return f"algorithm.{self.name}.label"


#: Why each toolbox-only algorithm has no menu entry. An entry here is a
#: deliberate, reviewed exception to ADR-0005's menu generation, not a default.
#:
#: **Empty since phase P5**, and the way it emptied is the point. It held two
#: entries after P0, and P5's four project-level algorithms would have taken it
#: to six -- at which point ``test_the_toolbox_only_list_stays_small`` failed,
#: exactly as it was written to. Six exceptions are not exceptions; they are a
#: category with no home. The Project menu entry is that home, and the list went
#: from five to none rather than from three to six. The guard stays, at the same
#: threshold, for the next time.
TOOLBOX_ONLY_JUSTIFICATIONS: dict[str, str] = {}

#: Algorithms whose menu item opens a custom dialog *before* the standard
#: Processing one, to collect parameters the standard dialog cannot. Each entry
#: records why, mirroring the enumerated table in ``specs/15`` section 3 -- the
#: set is deliberately small, because every custom dialog is a place the
#: generated UI stops being generated and starts having to be maintained.
#:
#: The custom dialog does not replace the algorithm or reimplement it
#: (ADR-0005). It fills in parameters and hands them to the same Processing
#: dialog every other menu item opens, so the algorithm stays the one thing
#: that runs, whether reached from the menu, the toolbox or the modeller.
CUSTOM_DIALOGS: dict[str, str] = {
    "analysis_network_preanalysis": (
        "A design is edited on the canvas and re-evaluated in a loop, which is "
        "the whole reason pre-analysis belongs in a GIS: a surveyor watches the "
        "ellipses shrink as they drag a station onto ground the orthophoto "
        "tells them is accessible. The dialog builds the design and hands it to "
        "this same algorithm for the full report (FR-272)."
    ),
    "totalstation_import_fieldbook": (
        "Mapping columns onto fields is impossible without seeing the data in "
        "them. A combo box offering 'HS' and 'hs' tells a user nothing; a "
        "preview showing 48 under one and 1.500 under the other tells them "
        "everything, and those two columns of RD-01 mean entirely different "
        "things (FR-160)."
    ),
}

#: Every algorithm GeoComp registers. Phase P0 contributed one, enough to prove
#: the registry -> provider -> menu path end to end; P2 added the three that
#: expose the adjustment core, P3 the eight of the total-station chain, and P4
#: the six of the levelling chain.
ALGORITHMS: tuple[AlgorithmSpec, ...] = (
    AlgorithmSpec(
        operation="system_report",
        group="project",
        module="geocomp.algorithms.project.system_report",
        class_name="SystemReportAlgorithm",
        requirement="FR-030",
        menu="project",
        menu_order=50,
    ),
    AlgorithmSpec(
        operation="tutorial_dataset",
        group="project",
        module="geocomp.algorithms.project.tutorial_dataset",
        class_name="TutorialDatasetAlgorithm",
        requirement="FR-952",
        menu="project",
        menu_order=60,
    ),
    # -- Phase P5: what the persistence work made reachable --------------
    #
    # All four are toolbox-only. They belong to no survey technique, which is
    # the same reason system_report and tutorial_dataset are, and an eighth menu
    # entry for "things you do with a result" would be a worse answer than the
    # toolbox: a user reaches them from the Processing panel where they already
    # have the algorithm that produced the solution, and from the model builder,
    # which is where exporting and storing every run actually belongs.
    AlgorithmSpec(
        operation="export",
        group="project",
        module="geocomp.algorithms.project.export_tables",
        class_name="ProjectExportAlgorithm",
        requirement="FR-162",
        menu="project",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="report",
        group="project",
        module="geocomp.algorithms.project.adjustment_report",
        class_name="ProjectReportAlgorithm",
        requirement="FR-930",
        menu="project",
        menu_order=20,
    ),
    AlgorithmSpec(
        operation="store",
        group="project",
        module="geocomp.algorithms.project.store",
        class_name="ProjectStoreAlgorithm",
        requirement="FR-130",
        menu="project",
        menu_order=30,
    ),
    AlgorithmSpec(
        operation="basemap",
        group="project",
        module="geocomp.algorithms.project.basemap",
        class_name="ProjectBaseMapAlgorithm",
        requirement="FR-167",
        menu="project",
        menu_order=40,
    ),
    AlgorithmSpec(
        operation="network_inspect",
        group="analysis",
        module="geocomp.algorithms.analysis.network_inspect",
        class_name="NetworkInspectAlgorithm",
        requirement="FR-273",
        menu="analysis",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="network_preanalysis",
        group="analysis",
        module="geocomp.algorithms.analysis.network_preanalysis",
        class_name="NetworkPreAnalysisAlgorithm",
        requirement="FR-270",
        menu="analysis",
        menu_order=20,
    ),
    AlgorithmSpec(
        operation="network_adjust",
        group="analysis",
        module="geocomp.algorithms.analysis.network_adjust",
        class_name="NetworkAdjustAlgorithm",
        requirement="FR-220",
        menu="analysis",
        menu_order=30,
    ),
    # -- Total Station (phase P3). The order mirrors the workflow, which is the
    # order specs/09 section 1 lists them in: get the data in, reduce it, then
    # compute with it.
    AlgorithmSpec(
        operation="import_fieldbook",
        group="totalstation",
        module="geocomp.algorithms.totalstation.import_fieldbook",
        class_name="ImportFieldBookAlgorithm",
        requirement="FR-160",
        menu="total_station",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="preprocess",
        group="totalstation",
        module="geocomp.algorithms.totalstation.preprocess",
        class_name="PreprocessAlgorithm",
        requirement="FR-400",
        menu="total_station",
        menu_order=20,
    ),
    AlgorithmSpec(
        operation="traverse",
        group="totalstation",
        module="geocomp.algorithms.totalstation.traverse",
        class_name="TraverseAlgorithm",
        requirement="FR-406",
        menu="total_station",
        menu_order=30,
    ),
    AlgorithmSpec(
        operation="resection",
        group="totalstation",
        module="geocomp.algorithms.totalstation.resection",
        class_name="ResectionAlgorithm",
        requirement="FR-407",
        menu="total_station",
        menu_order=40,
    ),
    AlgorithmSpec(
        operation="intersection",
        group="totalstation",
        module="geocomp.algorithms.totalstation.intersection",
        class_name="IntersectionAlgorithm",
        requirement="FR-408",
        menu="total_station",
        menu_order=50,
    ),
    AlgorithmSpec(
        operation="network",
        group="totalstation",
        module="geocomp.algorithms.totalstation.network",
        class_name="ClassicalNetworkAlgorithm",
        requirement="FR-409",
        menu="total_station",
        menu_order=60,
    ),
    AlgorithmSpec(
        operation="trig_levelling",
        group="totalstation",
        module="geocomp.algorithms.totalstation.trig_levelling",
        class_name="TrigonometricLevellingAlgorithm",
        requirement="FR-410",
        menu="total_station",
        menu_order=70,
    ),
    AlgorithmSpec(
        operation="radiation",
        group="totalstation",
        module="geocomp.algorithms.totalstation.radiation",
        class_name="RadiationAlgorithm",
        requirement="FR-411",
        menu="total_station",
        menu_order=80,
    ),
    # -- Level (phase P4). The order of the work: get the book in, reduce it by
    # the scheme it was observed with, check the closures, adjust the network.
    #
    # Equal and extreme sights share an implementation and are still two
    # entries, because they answer different questions and produce different
    # things: equal sights reduces a *line* to one height difference between two
    # marks, extreme sights reduces a *setup* to several that are correlated
    # with each other -- which is the whole point of that scheme and is
    # invisible in a line reduction.
    AlgorithmSpec(
        operation="import",
        group="levelling",
        module="geocomp.algorithms.levelling.import_book",
        class_name="ImportLevelBookAlgorithm",
        requirement="FR-160",
        menu="level",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="equal_sights",
        group="levelling",
        module="geocomp.algorithms.levelling.equal_sights",
        class_name="EqualSightsAlgorithm",
        requirement="FR-500",
        menu="level",
        menu_order=20,
    ),
    AlgorithmSpec(
        operation="equidistant_sights",
        group="levelling",
        module="geocomp.algorithms.levelling.equidistant_sights",
        class_name="EquidistantSightsAlgorithm",
        requirement="FR-501",
        menu="level",
        menu_order=30,
    ),
    AlgorithmSpec(
        operation="extreme_sights",
        group="levelling",
        module="geocomp.algorithms.levelling.extreme_sights",
        class_name="ExtremeSightsAlgorithm",
        requirement="FR-502",
        menu="level",
        menu_order=40,
    ),
    AlgorithmSpec(
        operation="closures",
        group="levelling",
        module="geocomp.algorithms.levelling.closures",
        class_name="LevellingClosureAlgorithm",
        requirement="FR-503",
        menu="level",
        menu_order=50,
    ),
    AlgorithmSpec(
        operation="network",
        group="levelling",
        module="geocomp.algorithms.levelling.network_adjust",
        class_name="LevellingNetworkAlgorithm",
        requirement="FR-504",
        menu="level",
        menu_order=60,
    ),
)


def algorithms_in_menu(menu_id: str) -> tuple[AlgorithmSpec, ...]:
    """Return the algorithms shown under *menu_id*, in menu order."""
    return tuple(
        sorted(
            (spec for spec in ALGORITHMS if spec.menu == menu_id),
            key=lambda spec: (spec.menu_order, spec.operation),
        )
    )


def algorithms_in_group(group_id: str) -> tuple[AlgorithmSpec, ...]:
    """Return the algorithms in Processing group *group_id*."""
    return tuple(spec for spec in ALGORITHMS if spec.group == group_id)


def _validate_module() -> None:
    """Catch a malformed registry at import, not at menu-build time."""
    group_ids = {group.id for group in PROCESSING_GROUPS}
    menu_ids = {group.id for group in MENU_GROUPS}
    seen: set[str] = set()
    for spec in ALGORITHMS:
        if spec.group not in group_ids:
            raise ValueError(
                f"algorithm {spec.name!r} names unknown processing group {spec.group!r}"
            )
        if spec.menu is not None and spec.menu not in menu_ids:
            raise ValueError(f"algorithm {spec.name!r} names unknown menu group {spec.menu!r}")
        if spec.menu is None and spec.name not in TOOLBOX_ONLY_JUSTIFICATIONS:
            raise ValueError(
                f"algorithm {spec.name!r} is toolbox-only but declares no justification; "
                "add one to TOOLBOX_ONLY_JUSTIFICATIONS or give it a menu group"
            )
        if spec.name in seen:
            raise ValueError(f"duplicate algorithm name {spec.name!r}")
        seen.add(spec.name)
    for action_menu in (group for group in MENU_GROUPS if group.is_action):
        if algorithms_in_menu(action_menu.id):
            raise ValueError(
                f"menu entry {action_menu.id!r} is a leaf action and cannot hold algorithms"
            )


_validate_module()
