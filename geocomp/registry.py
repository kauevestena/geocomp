# SPDX-License-Identifier: GPL-2.0-or-later
"""The registry: algorithms and menu windows, declared once.

ADR-0005 requires that every capability exist exactly once, as a Processing
algorithm. ADR-0010 keeps that and changes what the GeoComp menu is: its items
are **interactive windows** in which observations are typed, and a window
computes nothing -- it runs the algorithms declared here (FR-005, FR-011).

This module is the single source of both. It is deliberately **pure data**: it
names algorithms and windows by module path and class name rather than
importing them. The consequences are the point:

* ``geocomp.provider`` imports and instantiates each :class:`AlgorithmSpec`.
* ``geocomp.gui.menu`` builds the GeoComp menu from :func:`entries_in_menu`, so
  a menu item cannot point at nothing.
* a :class:`WindowSpec` names the algorithms its window runs, and the window is
  refused any other (``geocomp.services.chain_runner``), so a window cannot
  acquire a computation of its own without the registry saying so.
* ``tests/structural/test_menu_window_parity.py`` checks the correspondence
  **without a QGIS runtime**, because nothing here imports ``qgis``.

**The menu is being rebuilt group by group (ROADMAP phase P14).** Until a
group's windows exist, its algorithms keep the item they have had since
ADR-0005: a *legacy launcher*, which opens the algorithm's Processing dialog.
:attr:`AlgorithmSpec.menu` now means exactly that, and the set of algorithms
that have one may only shrink (``tests/test_registry.py`` pins it).

Adding an algorithm means adding an :class:`AlgorithmSpec` here. Forgetting to
is caught by the parity test, not discovered by a user.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ALGORITHMS",
    "CUSTOM_DIALOGS",
    "MENU_GROUPS",
    "NESTING_MENUS",
    "PROCESSING_GROUPS",
    "PROVIDER_ID",
    "TOOLBOX_ONLY_JUSTIFICATIONS",
    "WINDOWS",
    "AlgorithmSpec",
    "MenuGroup",
    "ProcessingGroup",
    "WindowSpec",
    "algorithms_in_group",
    "algorithms_in_menu",
    "algorithms_in_submenu",
    "algorithms_run_by_windows",
    "entries_in_menu",
    "entries_in_submenu",
    "submenus_in_menu",
    "window_named",
    "windows_in_menu",
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
        """The message code of the menu group's label."""
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
        menu: The :class:`MenuGroup` id its **legacy launcher** appears under:
            a menu item that opens the algorithm's Processing dialog, as every
            item did under ADR-0005. ``None`` for an algorithm that has none,
            which since ADR-0010 is where every algorithm is heading: the menu
            holds windows, and an algorithm is reached from the toolbox, the
            modeller, batch and PyQGIS, and is run by the windows declared in
            :data:`WINDOWS`. An algorithm with neither a launcher nor a window
            that runs it must say why in :data:`TOOLBOX_ONLY_JUSTIFICATIONS`.
        requirement: The requirement id this algorithm satisfies.
        menu_order: Position within its submenu.
        submenu: A second level *inside* the menu group, or ``None`` for an
            entry directly under it. Added in phase P7c for the one place the
            specifications ask for one: ``specs/15`` section 1.1 and
            ``specs/11`` section 1 both draw GNSS as Absolute (Static ·
            Kinematic) and Relative (Static · Kinematic), because "Static" means
            nothing without the branch above it. Flattening that to
            "Absolute — Static" was the alternative and it reads worse in a
            menu, where the branch is what the eye scans for.

            **It stays an exception.** Every other group is one level, and a
            second level that spread would undo what ADR-0005 bought: a menu
            you can see the whole of. ``tests/test_registry.py`` holds the set
            of groups allowed to nest.
    """

    operation: str
    group: str
    module: str
    class_name: str
    requirement: str
    menu: str | None = None
    menu_order: int = 0
    submenu: str | None = None

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
        """The message code of the algorithm's label."""
        return f"algorithm.{self.name}.label"


@dataclass(frozen=True)
class WindowSpec:
    """One interactive window of the GeoComp menu (ADR-0010, FR-010).

    Attributes:
        name: Stable and English. The menu item's object name, the key of the
            window's record in a job file and the folder of its results are
            all made from it, so renaming one orphans what was saved under it.
        menu: The :class:`MenuGroup` id it appears under.
        menu_order: Position within its submenu, on the scale the legacy
            launchers use, so a group can be rebuilt one window at a time
            without its order changing.
        module / class_name: Where the window lives. Named as strings so this
            module stays importable without QGIS, and so a window is imported
            when it is first opened rather than when the plugin loads.
        algorithms: The names of the algorithms the window runs, in the order
            it runs them. **The only ones it may run**: the chain runner
            refuses any other, which is what makes "a window computes nothing"
            a property the registry states rather than a habit.
        requirement: The requirement the window's own behaviour satisfies.
        technique: Whose job file it works on. Windows of one technique share
            one job -- one field book (FR-013).
        submenu: A second level inside the menu group; see
            :attr:`AlgorithmSpec.submenu`.
    """

    name: str
    menu: str
    menu_order: int
    module: str
    class_name: str
    algorithms: tuple[str, ...]
    requirement: str
    technique: str
    submenu: str | None = None

    @property
    def algorithm_ids(self) -> tuple[str, ...]:
        """The fully qualified ids of the algorithms the window runs."""
        return tuple(f"{PROVIDER_ID}:{name}" for name in self.algorithms)

    @property
    def label_code(self) -> str:
        """The message code of the window's label."""
        return f"window.{self.name}.label"


#: The interactive windows. Phase P14a contributed the first four: the Total
#: Station field book and the three computations of ``specs/09`` section 1 that
#: need nothing typed beyond it and a few known points.
#:
#: Their positions are the ones the same operations' launchers had, so the
#: Total Station submenu reads in the order it always did while half of it is
#: windows and half still launchers.
WINDOWS: tuple[WindowSpec, ...] = (
    WindowSpec(
        name="totalstation_fieldbook",
        menu="total_station",
        menu_order=10,
        module="geocomp.gui.windows.totalstation.fieldbook",
        class_name="FieldBookWindow",
        algorithms=("totalstation_import_fieldbook",),
        requirement="FR-012",
        technique="total_station",
    ),
    WindowSpec(
        name="totalstation_preprocess",
        menu="total_station",
        menu_order=20,
        module="geocomp.gui.windows.totalstation.preprocess",
        class_name="PreprocessWindow",
        algorithms=("totalstation_import_fieldbook", "totalstation_preprocess"),
        requirement="FR-011",
        technique="total_station",
    ),
    WindowSpec(
        name="totalstation_traverse",
        menu="total_station",
        menu_order=30,
        module="geocomp.gui.windows.totalstation.traverse",
        class_name="TraverseWindow",
        algorithms=(
            "totalstation_import_fieldbook",
            "totalstation_preprocess",
            "totalstation_traverse",
        ),
        requirement="FR-011",
        technique="total_station",
    ),
    WindowSpec(
        name="totalstation_radiation",
        menu="total_station",
        menu_order=80,
        module="geocomp.gui.windows.totalstation.radiation",
        class_name="RadiationWindow",
        algorithms=(
            "totalstation_import_fieldbook",
            "totalstation_preprocess",
            "totalstation_radiation",
        ),
        requirement="FR-011",
        technique="total_station",
    ),
)

#: Why an algorithm that has neither a legacy launcher nor a window running it
#: is reachable from the toolbox only. An entry here is a deliberate, reviewed
#: statement, not a default.
#:
#: **Empty**, and since ADR-0010 for a different reason than before. Under
#: ADR-0005 it held the exceptions to "every algorithm has a menu item", and
#: emptied in phase P5 when the Project entry gave six of them a home. Now an
#: algorithm without a menu item is the rule -- the menu holds windows -- and
#: what this list holds is the algorithm *no window runs either*: one whose
#: whole purpose is a file the menu has no business typing. FR-015 expects a
#: few as the groups are rebuilt; none exists yet, because the one file reader
#: P14a took out of the menu, *Import field book*, is also what the Total
#: Station windows read the typed book with.
TOOLBOX_ONLY_JUSTIFICATIONS: dict[str, str] = {}

#: Algorithms that open a custom dialog *before* the standard Processing one,
#: to collect parameters the standard dialog cannot. Each entry records why,
#: mirroring the enumerated table in ``specs/15`` section 3 -- the set is
#: deliberately small, because every custom dialog is a place the generated UI
#: stops being generated and starts having to be maintained.
#:
#: The custom dialog does not replace the algorithm or reimplement it
#: (ADR-0005). It fills in parameters and hands them to the same Processing
#: dialog a launcher opens, so the algorithm stays the one thing that runs,
#: whether reached from the menu, the toolbox or the modeller.
#:
#: Since P14a the field-book mapping preview is opened from Plugins ▸ GeoComp
#: rather than from the GeoComp menu, whose Total Station items are windows: it
#: belongs to the file route (FR-015), and it is kept because FR-160's preview
#: is the only way to map an instrument's columns by looking at them.
CUSTOM_DIALOGS: dict[str, str] = {
    "analysis_network_preanalysis": (
        "A design is edited on the canvas and re-evaluated in a loop, which is "
        "the whole reason pre-analysis belongs in a GIS: a surveyor watches the "
        "ellipses shrink as they drag a station onto ground the orthophoto "
        "tells them is accessible. The dialog builds the design and hands it to "
        "this same algorithm for the full report (FR-272)."
    ),
    "monitoring_compare_epochs": (
        "Two epochs in different frames, processed by different engines or with a "
        "station one of them lacks are comparable, but a user should decide to compare "
        "them knowing it; and two that cannot be compared should be refused before the "
        "parameters are filled in, not after. The dialog shows the compatibility "
        "findings first and hands the two files to this algorithm (FR-831)."
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
    # -- Phase P12c-6: the engine manager, reachable --------------------
    #
    # Under Project for the reason the system report is: installing a program
    # belongs to no survey technique, and DynAdjust serves Analysis and
    # Integration alike. Global Settings opens it from Paths and engines.
    AlgorithmSpec(
        operation="install_engine",
        group="project",
        module="geocomp.algorithms.engines.install_engine",
        class_name="InstallEngineAlgorithm",
        requirement="FR-301",
        menu="project",
        menu_order=70,
    ),
    # An engine's failure, packaged for the engine's developers (P12c-48). Beside
    # Install an engine, the other thing a user does about an engine as such.
    AlgorithmSpec(
        operation="package_engine_problem",
        group="project",
        module="geocomp.algorithms.engines.report_problem",
        class_name="PackageEngineProblemAlgorithm",
        requirement="FR-955",
        menu="project",
        menu_order=75,
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
    # Phase P11: the two mode switches of specs/17 section 4, beside the store
    # they move a project into and out of.
    AlgorithmSpec(
        operation="export_postgis",
        group="project",
        module="geocomp.algorithms.project.postgis",
        class_name="ExportToPostgisAlgorithm",
        requirement="FR-132",
        menu="project",
        menu_order=32,
    ),
    AlgorithmSpec(
        operation="import_postgis",
        group="project",
        module="geocomp.algorithms.project.postgis",
        class_name="ImportFromPostgisAlgorithm",
        requirement="FR-132",
        menu="project",
        menu_order=34,
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
    # Phase P12b: the print layouts of specs/19 section 6, beside the base map
    # they are drawn over.
    AlgorithmSpec(
        operation="print_layout",
        group="project",
        module="geocomp.algorithms.project.print_layout",
        class_name="PrintLayoutAlgorithm",
        requirement="FR-931",
        menu="project",
        menu_order=42,
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
    # -- Phase P6: the same two operations, through DynAdjust ------------
    #
    # Under the *analysis* menu beside the in-house adjustment rather than in
    # an "engines" group of their own. Which engine ran is an implementation
    # choice about one operation, not a different kind of work: a user who
    # wants their network adjusted looks under Analysis, and a menu organised
    # by engine would ask them to know which one they wanted before they knew
    # what they wanted done.
    AlgorithmSpec(
        operation="dynadjust_adjust",
        group="analysis",
        module="geocomp.algorithms.engines.dynadjust_adjust",
        class_name="DynAdjustAdjustAlgorithm",
        requirement="FR-321",
        menu="analysis",
        menu_order=40,
    ),
    # FR-325 (P12c-21): the second half of a job Adjust network (DynAdjust)
    # stopped before running, after its input was inspected or edited.
    AlgorithmSpec(
        operation="dynadjust_run_prepared",
        group="analysis",
        module="geocomp.algorithms.engines.dynadjust_run_prepared",
        class_name="DynAdjustRunPreparedAlgorithm",
        requirement="FR-325",
        menu="analysis",
        menu_order=45,
    ),
    AlgorithmSpec(
        operation="dynadjust_compare",
        group="analysis",
        module="geocomp.algorithms.engines.dynadjust_compare",
        class_name="DynAdjustCompareAlgorithm",
        requirement="FR-323",
        menu="analysis",
        menu_order=50,
    ),
    # -- Total Station (phase P3). The order mirrors the workflow, which is the
    # order specs/09 section 1 lists them in: get the data in, reduce it, then
    # compute with it.
    #
    # P14a: the import, the pre-processing, the traverse and the radiation have
    # no launcher any more. The menu items of those names are windows
    # (``WINDOWS``), which run these same four on a typed field book.
    AlgorithmSpec(
        operation="import_fieldbook",
        group="totalstation",
        module="geocomp.algorithms.totalstation.import_fieldbook",
        class_name="ImportFieldBookAlgorithm",
        requirement="FR-160",
    ),
    AlgorithmSpec(
        operation="preprocess",
        group="totalstation",
        module="geocomp.algorithms.totalstation.preprocess",
        class_name="PreprocessAlgorithm",
        requirement="FR-400",
    ),
    AlgorithmSpec(
        operation="traverse",
        group="totalstation",
        module="geocomp.algorithms.totalstation.traverse",
        class_name="TraverseAlgorithm",
        requirement="FR-406",
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
# -- Phase P7c: GNSS ------------------------------------------------
    #
    # The four modes are the two branches `specs/11` section 1 draws; the four
    # supporting operations sit directly under GNSS beside them, which is what
    # `specs/15` section 1.1 lists after the parenthesised pairs.
    AlgorithmSpec(
        operation="scan_sessions",
        group="gnss",
        module="geocomp.algorithms.gnss.scan",
        class_name="ScanSessionsAlgorithm",
        requirement="FR-351",
        menu="gnss",
        menu_order=10,
    ),
    # P10c. After the scan because it reads the scan's days, and before the
    # processing modes because it is what lets them run offline.
    AlgorithmSpec(
        operation="download_products",
        group="gnss",
        module="geocomp.algorithms.gnss.download",
        class_name="DownloadProductsAlgorithm",
        requirement="FR-352",
        menu="gnss",
        menu_order=15,
    ),
    AlgorithmSpec(
        operation="absolute_static",
        group="gnss",
        module="geocomp.algorithms.gnss.process",
        class_name="AbsoluteStaticAlgorithm",
        requirement="FR-600",
        menu="gnss",
        menu_order=20,
        submenu="absolute",
    ),
    AlgorithmSpec(
        operation="absolute_kinematic",
        group="gnss",
        module="geocomp.algorithms.gnss.process",
        class_name="AbsoluteKinematicAlgorithm",
        requirement="FR-600",
        menu="gnss",
        menu_order=30,
        submenu="absolute",
    ),
    AlgorithmSpec(
        operation="relative_static",
        group="gnss",
        module="geocomp.algorithms.gnss.process",
        class_name="RelativeStaticAlgorithm",
        requirement="FR-601",
        menu="gnss",
        menu_order=40,
        submenu="relative",
    ),
    AlgorithmSpec(
        operation="relative_kinematic",
        group="gnss",
        module="geocomp.algorithms.gnss.process",
        class_name="RelativeKinematicAlgorithm",
        requirement="FR-601",
        menu="gnss",
        menu_order=50,
        submenu="relative",
    ),
    AlgorithmSpec(
        operation="build_baselines",
        group="gnss",
        module="geocomp.algorithms.gnss.baselines",
        class_name="BuildBaselinesAlgorithm",
        requirement="FR-602",
        menu="gnss",
        menu_order=60,
    ),
    AlgorithmSpec(
        operation="batch",
        group="gnss",
        module="geocomp.algorithms.gnss.batch_process",
        class_name="BatchProcessAlgorithm",
        requirement="FR-355",
        menu="gnss",
        menu_order=70,
    ),
    AlgorithmSpec(
        operation="compare_configurations",
        group="gnss",
        module="geocomp.algorithms.gnss.compare",
        class_name="CompareConfigurationsAlgorithm",
        requirement="FR-359",
        menu="gnss",
        menu_order=80,
    ),
    # -- Phase P8b: Gravimetry --------------------------------------------
    #
    # The two entries of `specs/12` section 2, in the order they are run.
    AlgorithmSpec(
        operation="preprocess",
        group="gravimetry",
        module="geocomp.algorithms.gravimetry.preprocess",
        class_name="GravimetryPreprocessAlgorithm",
        requirement="FR-701",
        menu="gravimetry",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="network",
        group="gravimetry",
        module="geocomp.algorithms.gravimetry.network_adjust",
        class_name="GravimetryNetworkAlgorithm",
        requirement="FR-700",
        menu="gravimetry",
        menu_order=20,
    ),
    # -- P9b: the four Integration presets, in the order specs/13 section 1
    # lists them. One capability, four sets of defaults and validation.
    AlgorithmSpec(
        operation="gnss_total_station",
        group="integration",
        module="geocomp.algorithms.integration.presets",
        class_name="GnssTotalStationAlgorithm",
        requirement="FR-800",
        menu="integration",
        menu_order=10,
    ),
    AlgorithmSpec(
        operation="total_station_level",
        group="integration",
        module="geocomp.algorithms.integration.presets",
        class_name="TotalStationLevelAlgorithm",
        requirement="FR-801",
        menu="integration",
        menu_order=20,
    ),
    AlgorithmSpec(
        operation="gnss_level",
        group="integration",
        module="geocomp.algorithms.integration.presets",
        class_name="GnssLevelAlgorithm",
        requirement="FR-802",
        menu="integration",
        menu_order=30,
    ),
    AlgorithmSpec(
        operation="multiple",
        group="integration",
        module="geocomp.algorithms.integration.presets",
        class_name="MultipleTechniquesAlgorithm",
        requirement="FR-803",
        menu="integration",
        menu_order=40,
    ),
    # -- Monitoring (phase P10b, specs/14). In the Monitoring toolbox group and
    # under Analysis in the menu, where specs/15 section 1.1 places multi-epoch
    # comparison and the monitoring report: they analyse adjusted solutions,
    # whatever technique produced them, as Adjust network does. In the order of
    # specs/14 section 8: two epochs, then a series, then the report of either.
    AlgorithmSpec(
        operation="compare_epochs",
        group="monitoring",
        module="geocomp.algorithms.monitoring.compare_epochs",
        class_name="MonitoringCompareEpochsAlgorithm",
        requirement="FR-834",
        menu="analysis",
        menu_order=60,
    ),
    AlgorithmSpec(
        operation="time_series",
        group="monitoring",
        module="geocomp.algorithms.monitoring.time_series",
        class_name="MonitoringTimeSeriesAlgorithm",
        requirement="FR-838",
        menu="analysis",
        menu_order=70,
    ),
    AlgorithmSpec(
        operation="report",
        group="monitoring",
        module="geocomp.algorithms.monitoring.report",
        class_name="MonitoringReportAlgorithm",
        requirement="FR-932",
        menu="analysis",
        menu_order=80,
    ),
)

#: Menu groups permitted a second level. One entry, and the reason is in
#: :class:`AlgorithmSpec`'s ``submenu``: GNSS's four modes are two branches of
#: two, and "Static" alone names nothing. A group absent from here may not nest,
#: which ``tests/test_registry.py`` enforces so the exception cannot spread by
#: imitation.
NESTING_MENUS: frozenset[str] = frozenset({"gnss"})


def submenus_in_menu(menu_id: str) -> tuple[str, ...]:
    """The second-level names under *menu_id*, in the order they first appear.

    Declaration order rather than alphabetical: ``specs/11`` draws Absolute
    before Relative, and a menu that reordered the specification's own figure
    would be a small lie about which is primary.
    """
    seen: list[str] = []
    for spec in entries_in_menu(menu_id):
        if spec.submenu and spec.submenu not in seen:
            seen.append(spec.submenu)
    return tuple(seen)


def windows_in_menu(menu_id: str) -> tuple[WindowSpec, ...]:
    """The windows shown under *menu_id*, in menu order."""
    return tuple(
        sorted(
            (spec for spec in WINDOWS if spec.menu == menu_id),
            key=lambda spec: (spec.menu_order, spec.name),
        )
    )


def entries_in_menu(menu_id: str) -> tuple[WindowSpec | AlgorithmSpec, ...]:
    """Everything shown under *menu_id*, windows and legacy launchers, in menu order.

    What ``geocomp.gui.menu`` builds a submenu from, so the menu is by
    construction what the registry declares.
    """
    entries: list[WindowSpec | AlgorithmSpec] = [
        *windows_in_menu(menu_id),
        *algorithms_in_menu(menu_id),
    ]
    return tuple(sorted(entries, key=lambda entry: (entry.menu_order, entry.name)))


def entries_in_submenu(
    menu_id: str, submenu: str | None
) -> tuple[WindowSpec | AlgorithmSpec, ...]:
    """The entries under one second level, or, for ``None``, directly under the group."""
    return tuple(entry for entry in entries_in_menu(menu_id) if entry.submenu == submenu)


def window_named(name: str) -> WindowSpec | None:
    """The window of that name, or ``None``."""
    return next((spec for spec in WINDOWS if spec.name == name), None)


def algorithms_run_by_windows() -> frozenset[str]:
    """The names of the algorithms some window runs."""
    return frozenset(name for spec in WINDOWS for name in spec.algorithms)


def algorithms_in_submenu(menu_id: str, submenu: str | None) -> tuple[AlgorithmSpec, ...]:
    """Algorithms under one second level, or directly under the group."""
    return tuple(
        spec for spec in algorithms_in_menu(menu_id) if spec.submenu == submenu
    )


def algorithms_in_menu(menu_id: str) -> tuple[AlgorithmSpec, ...]:
    """Return the algorithms that still have a legacy launcher under *menu_id*, in menu order."""
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
    by_window = algorithms_run_by_windows()
    seen: set[str] = set()
    for spec in ALGORITHMS:
        if spec.group not in group_ids:
            raise ValueError(
                f"algorithm {spec.name!r} names unknown processing group {spec.group!r}"
            )
        if spec.menu is not None and spec.menu not in menu_ids:
            raise ValueError(f"algorithm {spec.name!r} names unknown menu group {spec.menu!r}")
        if (
            spec.menu is None
            and spec.name not in by_window
            and spec.name not in TOOLBOX_ONLY_JUSTIFICATIONS
        ):
            raise ValueError(
                f"algorithm {spec.name!r} has no menu launcher and no window runs it, and it "
                "declares no justification; name it in a WindowSpec's algorithms or add the "
                "reason to TOOLBOX_ONLY_JUSTIFICATIONS"
            )
        if spec.name in seen:
            raise ValueError(f"duplicate algorithm name {spec.name!r}")
        seen.add(spec.name)
    windows: set[str] = set()
    for window in WINDOWS:
        if window.menu not in menu_ids:
            raise ValueError(f"window {window.name!r} names unknown menu group {window.menu!r}")
        if window.name in windows:
            raise ValueError(f"duplicate window name {window.name!r}")
        windows.add(window.name)
        if not window.algorithms:
            raise ValueError(
                f"window {window.name!r} runs no algorithm. A window computes nothing itself "
                "(ADR-0010), so one that runs nothing does nothing"
            )
        unknown = [name for name in window.algorithms if name not in seen]
        if unknown:
            raise ValueError(f"window {window.name!r} names unregistered algorithms {unknown!r}")
    for action_menu in (group for group in MENU_GROUPS if group.is_action):
        if entries_in_menu(action_menu.id):
            raise ValueError(
                f"menu entry {action_menu.id!r} is a leaf action and cannot hold algorithms"
            )
    for spec in (*ALGORITHMS, *WINDOWS):
        if spec.submenu and spec.menu not in NESTING_MENUS:
            raise ValueError(
                f"{spec.name!r} declares submenu {spec.submenu!r} under menu "
                f"{spec.menu!r}, which is not in NESTING_MENUS. specs/15 section 1 allows "
                "a second level only where the first names nothing on its own; add the "
                "menu to NESTING_MENUS with the reason, or flatten the entry"
            )


_validate_module()
