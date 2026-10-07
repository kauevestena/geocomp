# SPDX-License-Identifier: GPL-2.0-or-later
"""Public interfaces between modules are documented and annotated (NFR-012).

An interface *between modules* is what another module of ``geocomp/`` imports:
a module-level function, or a class and its public methods. Each must carry a
docstring and annotate its parameters and its return.

Until P12c-13 nothing checked it. Its first count, of 1,347 such classes,
functions and methods, found 399 with no docstring and 51 not fully annotated --
most of the first are serialisation methods and the QGIS methods every algorithm
overrides, ``displayName`` and the like. Both were frozen in lists that **may
only shrink**: a name leaves when it is put right, and a new interface arrives
documented and annotated. This is P12c-7's ratchet, which took 457 unworded
error codes to none.

P12c-31 and P12c-32 documented all 399, so the first list is gone and the rule
is now plain: every interface has a docstring.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from functools import cache

from tests.conftest import REPO_ROOT

PACKAGE = REPO_ROOT / "geocomp"


@cache
def _modules() -> dict[str, ast.Module]:
    modules = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        dotted = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
        modules[dotted.removesuffix(".__init__")] = ast.parse(path.read_text(encoding="utf-8"))
    return modules


@cache
def _imported() -> dict[str, frozenset[str]]:
    """For each module, the names other modules import from it."""
    names: dict[str, set[str]] = defaultdict(set)
    for dotted, tree in _modules().items():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module
                and node.module.startswith("geocomp")
                and node.module != dotted
            ):
                names[node.module].update(alias.name for alias in node.names)
    return {module: frozenset(found) for module, found in names.items()}


def _interfaces():
    """(qualified name, node) for every interface between modules."""
    for dotted, tree in _modules().items():
        wanted = _imported().get(dotted, frozenset())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name in wanted:
                yield f"{dotted}.{node.name}", node
            elif isinstance(node, ast.ClassDef) and node.name in wanted:
                yield f"{dotted}.{node.name}", node
                for member in node.body:
                    if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef) and (
                        not member.name.startswith("_") or member.name == "__init__"
                    ):
                        yield f"{dotted}.{node.name}.{member.name}", member


def _undocumented() -> set[str]:
    return {
        name
        for name, node in _interfaces()
        if not name.endswith(".__init__") and ast.get_docstring(node) is None
    }


def _unannotated() -> set[str]:
    found = set()
    for name, node in _interfaces():
        if isinstance(node, ast.ClassDef):
            continue
        arguments = node.args
        parameters = [
            argument
            for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
            if argument.arg not in {"self", "cls"}
        ]
        starred = [star for star in (arguments.vararg, arguments.kwarg) if star is not None]
        if (
            any(parameter.annotation is None for parameter in (*parameters, *starred))
            or (node.returns is None and not name.endswith(".__init__"))
        ):
            found.add(name)
    return found


def test_the_interfaces_are_found():
    """Guards the scan: one that found none would pass everything."""
    names = {name for name, _node in _interfaces()}
    assert len(names) > 1000
    assert "geocomp.core.adjustment.least_squares.adjust" in names


def test_every_interface_is_documented():
    missing = sorted(_undocumented())
    assert not missing, f"interfaces between modules with no docstring: {missing}"


def test_no_new_interface_is_unannotated():
    new = sorted(_unannotated() - UNANNOTATED)
    assert not new, f"interfaces between modules not fully annotated: {new}"


def test_the_baselines_only_shrink():
    """A name put right, renamed or removed leaves the list in the same change."""
    assert not sorted(UNANNOTATED - _unannotated()), "annotated now: remove from UNANNOTATED"


#: Frozen at P12c-13's first count. May only shrink.
UNANNOTATED = frozenset(
    {
        "geocomp.algorithms.base.GeoCompAlgorithm.checkParameterValues",
        "geocomp.algorithms.defaults.recorded_epoch",
        "geocomp.algorithms.defaults.run_epoch",
        "geocomp.algorithms.gnss.common.base_coordinates",
        "geocomp.algorithms.gnss.common.engine_record",
        "geocomp.algorithms.gnss.common.gnss_engine",
        "geocomp.algorithms.gnss.common.timeout_parameter",
        "geocomp.algorithms.inputs.input_problem",
        "geocomp.algorithms.inputs.validated",
        "geocomp.algorithms.layer_outputs.add_result_layer_parameters",
        "geocomp.algorithms.layer_outputs.write_result_layers",
        "geocomp.algorithms.layer_outputs.write_styled_sink",
        "geocomp.algorithms.levelling.common.summarise_findings",
        "geocomp.algorithms.monitoring.common.read_document",
        "geocomp.algorithms.totalstation.common.summarise_findings",
        "geocomp.core.adjustment.blocks.BlockDiagonal.locate",
        "geocomp.core.adjustment.blocks.BlockDiagonal.quadratic",
        "geocomp.core.adjustment.blocks.inverse_diagonal",
        "geocomp.core.adjustment.blocks.product_diagonal",
        "geocomp.core.adjustment.blocks.quadratic_form",
        "geocomp.core.adjustment.geocentric.evaluate_geocentric",
        "geocomp.core.adjustment.least_squares.to_observation_results",
        "geocomp.core.adjustment.least_squares.to_solution",
        "geocomp.core.adjustment.parameters.geocentric_component",
        "geocomp.core.adjustment.parameters.orientation_owner",
        "geocomp.core.adjustment.undulations.geoid_residuals",
        "geocomp.core.geodesy.frames.transform_point",
        "geocomp.core.geodesy.frames.transform_vector",
        "geocomp.core.monitoring.congruency.s_transform",
        "geocomp.core.techniques.integration.adjustment.adjust_combination",
        "geocomp.core.techniques.integration.breakdown.technique_breakdown",
        "geocomp.core.techniques.levelling.network.add_height_differences",
        "geocomp.core.visualization.relative.relative_ellipses",
        "geocomp.engines.dynadjust.read_output.match_observations",
        "geocomp.engines.dynadjust.read_output.printed_rows",
        "geocomp.engines.status.engine_status",
        "geocomp.gui.compare_dialog.CompatibilityDialog.check",
        "geocomp.gui.menu.GeoCompMenu.build",
        "geocomp.gui.preanalysis_dialog.PreAnalysisDialog.__init__",
        "geocomp.gui.preanalysis_dialog.PreAnalysisDialog.network",
        "geocomp.gui.results_panel.ResultsPanel.layers_added",
        "geocomp.gui.time_series_panel.TimeSeriesPanel.layers_added",
        "geocomp.layers.builders.gnss_baseline_features",
        "geocomp.layers.builders.gnss_trajectory_features",
        "geocomp.layers.builders.relative_ellipse_features",
        "geocomp.layers.builders.relative_ellipse_layer_name",
        "geocomp.layers.styles.apply_style",
        "geocomp.layers.themes.add_thematic_styles",
        "geocomp.plugin.GeoCompPlugin.__init__",
        "geocomp.services.downloads.QgisFetcher.__init__",
        "geocomp.services.engines.install_engine",
    }
)
