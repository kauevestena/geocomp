# SPDX-License-Identifier: GPL-2.0-or-later
"""Public interfaces between modules are documented and annotated (NFR-012).

An interface *between modules* is what another module of ``geocomp/`` imports:
a module-level function, or a class and its public methods. Each must carry a
docstring and annotate its parameters and its return.

Until P12c-13 nothing checked it. Its first count, of 1,347 such classes,
functions and methods, found 399 with no docstring and 51 not fully annotated --
most of the first are serialisation methods and the QGIS methods every algorithm
overrides, ``displayName`` and the like. They are frozen
below, in two lists that **may only shrink**: a name leaves when it is put
right, and a new interface arrives documented and annotated. This is P12c-7's
ratchet, which took 457 unworded error codes to none.
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


def test_no_new_interface_is_undocumented():
    new = sorted(_undocumented() - UNDOCUMENTED)
    assert not new, f"interfaces between modules with no docstring: {new}"


def test_no_new_interface_is_unannotated():
    new = sorted(_unannotated() - UNANNOTATED)
    assert not new, f"interfaces between modules not fully annotated: {new}"


def test_the_baselines_only_shrink():
    """A name put right, renamed or removed leaves its list in the same change."""
    assert not sorted(UNDOCUMENTED - _undocumented()), "documented now: remove from UNDOCUMENTED"
    assert not sorted(UNANNOTATED - _unannotated()), "annotated now: remove from UNANNOTATED"


#: Frozen at P12c-13's first count. May only shrink.
UNDOCUMENTED = frozenset(
    {
        "geocomp.algorithms.analysis.common.datum_of",
        "geocomp.algorithms.analysis.common.frame_of",
        "geocomp.algorithms.base.GeoCompAlgorithm.createInstance",
        "geocomp.algorithms.base.GeoCompAlgorithm.displayName",
        "geocomp.algorithms.base.GeoCompAlgorithm.group",
        "geocomp.algorithms.base.GeoCompAlgorithm.groupId",
        "geocomp.algorithms.base.GeoCompAlgorithm.initAlgorithm",
        "geocomp.algorithms.base.GeoCompAlgorithm.tr",
        "geocomp.algorithms.gnss.common.SessionProducts.missing",
        "geocomp.algorithms.gravimetry.common.display_decimals",
        "geocomp.algorithms.gravimetry.common.source_name",
        "geocomp.algorithms.gravimetry.network_adjust.GravimetryNetworkAlgorithm.displayName",
        "geocomp.algorithms.gravimetry.network_adjust.GravimetryNetworkAlgorithm.help_body",
        "geocomp.algorithms.gravimetry.network_adjust.GravimetryNetworkAlgorithm.initAlgorithm",
        "geocomp.algorithms.gravimetry.network_adjust.GravimetryNetworkAlgorithm.processAlgorithm",
        "geocomp.algorithms.gravimetry.network_adjust.GravimetryNetworkAlgorithm.shortDescription",
        "geocomp.algorithms.integration.common._CombinedAdjustmentAlgorithm.common_help",
        "geocomp.algorithms.integration.common._CombinedAdjustmentAlgorithm.initAlgorithm",
        "geocomp.algorithms.integration.common._CombinedAdjustmentAlgorithm.processAlgorithm",
        "geocomp.algorithms.levelling.common.reduction_to_dict",
        "geocomp.algorithms.levelling.common.setup_to_dict",
        "geocomp.algorithms.monitoring.common.datum_of",
        "geocomp.algorithms.monitoring.common.read_optional_network",
        "geocomp.algorithms.monitoring.common.read_solutions",
        "geocomp.algorithms.monitoring.common.read_thresholds",
        "geocomp.algorithms.monitoring.common.write_json",
        "geocomp.algorithms.reporting.escape",
        "geocomp.algorithms.transaction.FeedbackCancellation.is_cancelled",
        "geocomp.core.adjustment.blocks.BlockDiagonal.T",
        "geocomp.core.adjustment.blocks.BlockDiagonal.diagonal",
        "geocomp.core.adjustment.blocks.BlockDiagonal.entry",
        "geocomp.core.adjustment.blocks.BlockDiagonal.inverse",
        "geocomp.core.adjustment.blocks.BlockDiagonal.same_structure",
        "geocomp.core.adjustment.blocks.BlockDiagonal.shape",
        "geocomp.core.adjustment.blocks.BlockDiagonal.to_dense",
        "geocomp.core.adjustment.blocks.BlockDiagonal.transpose",
        "geocomp.core.adjustment.datum.DatumDefect.describe",
        "geocomp.core.adjustment.datum.DatumDefect.size",
        "geocomp.core.adjustment.difference_network.ApproximateValues.is_connected",
        "geocomp.core.adjustment.equations.EquationRow.to_dense",
        "geocomp.core.adjustment.equations.supports",
        "geocomp.core.adjustment.geocentric.evaluate_geocentric",
        "geocomp.core.adjustment.normal_equations.LinearisedSystem.normal_matrix",
        "geocomp.core.adjustment.normal_equations.LinearisedSystem.normal_vector",
        "geocomp.core.adjustment.normal_equations.LinearisedSystem.observation_count",
        "geocomp.core.adjustment.normal_equations.LinearisedSystem.parameter_count",
        "geocomp.core.adjustment.normal_equations.NullSpaceFinding.describe",
        "geocomp.core.adjustment.normal_equations._condition_number",
        "geocomp.core.adjustment.parameters.Frame.component_units",
        "geocomp.core.adjustment.parameters.Frame.components",
        "geocomp.core.adjustment.parameters.ParameterLayout.is_fixed",
        "geocomp.core.adjustment.parameters.ParameterLayout.labels",
        "geocomp.core.adjustment.parameters.ParameterLayout.size",
        "geocomp.core.adjustment.parameters.ParameterLayout.station_ids",
        "geocomp.core.adjustment.parameters.ParameterSlot.label",
        "geocomp.core.adjustment.parameters.WeightedConstraint.size",
        "geocomp.core.adjustment.variance_components.VarianceComponents.factor",
        "geocomp.core.adjustment.weighting.DifferenceWeighting.from_dict",
        "geocomp.core.adjustment.weighting.DifferenceWeighting.to_dict",
        "geocomp.core.adjustment.weighting.ExtentKind.accumulates",
        "geocomp.core.basemaps.BaseMapService.from_dict",
        "geocomp.core.basemaps.BaseMapService.needs_authentication",
        "geocomp.core.findings.Finding.is_blocking",
        "geocomp.core.geodesy.frames.TransformationRecord.accuracy",
        "geocomp.core.geodesy.frames.TransformationRecord.is_identity",
        "geocomp.core.geodesy.frames.TransformationRecord.to_dict",
        "geocomp.core.geodesy.frames.TransformationStep.to_dict",
        "geocomp.core.geoid.Coverage.contains",
        "geocomp.core.geoid.Coverage.describe_degrees",
        "geocomp.core.geoid.Coverage.from_dict",
        "geocomp.core.geoid.Coverage.to_dict",
        "geocomp.core.geoid.GeoidModel.columns",
        "geocomp.core.geoid.GeoidModel.from_dict",
        "geocomp.core.geoid.GeoidModel.label",
        "geocomp.core.geoid.GeoidModel.rows",
        "geocomp.core.geoid.GeoidModel.to_dict",
        "geocomp.core.instruments.gravimeter.CalibrationTable.from_dict",
        "geocomp.core.instruments.gravimeter.CalibrationTable.to_dict",
        "geocomp.core.instruments.gravimeter.GravimeterProfile.from_dict",
        "geocomp.core.instruments.gravimeter.GravimeterProfile.label",
        "geocomp.core.instruments.gravimeter.GravimeterProfile.to_dict",
        "geocomp.core.instruments.level.LevelProfile.from_dict",
        "geocomp.core.instruments.level.LevelProfile.label",
        "geocomp.core.instruments.level.LevelProfile.reading_sigma",
        "geocomp.core.instruments.level.LevelProfile.to_dict",
        "geocomp.core.instruments.level.LevellingClass.from_dict",
        "geocomp.core.instruments.level.LevellingClass.label",
        "geocomp.core.instruments.level.LevellingClass.to_dict",
        "geocomp.core.instruments.profiles.EdmSpecification.from_dict",
        "geocomp.core.instruments.profiles.EdmSpecification.to_dict",
        "geocomp.core.instruments.profiles.InstrumentProfile.distance_quantity",
        "geocomp.core.instruments.profiles.InstrumentProfile.from_dict",
        "geocomp.core.instruments.profiles.InstrumentProfile.instrument_height_quantity",
        "geocomp.core.instruments.profiles.InstrumentProfile.label",
        "geocomp.core.instruments.profiles.InstrumentProfile.target_height_quantity",
        "geocomp.core.instruments.profiles.InstrumentProfile.to_dict",
        "geocomp.core.instruments.profiles.InstrumentProfile.zenith_quantity",
        "geocomp.core.instruments.profiles.ProfileLibrary.add_gravimeter",
        "geocomp.core.instruments.profiles.ProfileLibrary.add_instrument",
        "geocomp.core.instruments.profiles.ProfileLibrary.add_level",
        "geocomp.core.instruments.profiles.ProfileLibrary.add_levelling_class",
        "geocomp.core.instruments.profiles.ProfileLibrary.add_reflector",
        "geocomp.core.instruments.profiles.ProfileLibrary.from_dict",
        "geocomp.core.instruments.profiles.ProfileLibrary.rename_instrument",
        "geocomp.core.instruments.profiles.ProfileLibrary.to_dict",
        "geocomp.core.instruments.profiles.ReflectorProfile.from_dict",
        "geocomp.core.instruments.profiles.ReflectorProfile.label",
        "geocomp.core.instruments.profiles.ReflectorProfile.to_dict",
        "geocomp.core.instruments.stochastic.StochasticDefaults.sigma",
        "geocomp.core.instruments.stochastic.StochasticDefaults.with_default",
        "geocomp.core.models.epoch.Epoch.from_decimal_year",
        "geocomp.core.models.epoch.Epoch.from_dict",
        "geocomp.core.models.epoch.Epoch.to_dict",
        "geocomp.core.models.network.Campaign.from_dict",
        "geocomp.core.models.network.Campaign.to_dict",
        "geocomp.core.models.network.GnssSession.duration_seconds",
        "geocomp.core.models.network.GnssSession.from_dict",
        "geocomp.core.models.network.GnssSession.to_dict",
        "geocomp.core.models.network.Network.active_observations",
        "geocomp.core.models.network.Network.add_cluster",
        "geocomp.core.models.network.Network.add_observation",
        "geocomp.core.models.network.Network.add_station",
        "geocomp.core.models.network.Network.constrained_stations",
        "geocomp.core.models.network.Network.from_dict",
        "geocomp.core.models.network.Network.observations_at",
        "geocomp.core.models.network.Network.station_ids",
        "geocomp.core.models.network.Network.to_dict",
        "geocomp.core.models.network.Project.add_campaign",
        "geocomp.core.models.network.Project.add_gnss_session",
        "geocomp.core.models.network.Project.add_network",
        "geocomp.core.models.network.Project.from_dict",
        "geocomp.core.models.network.Project.to_dict",
        "geocomp.core.models.observation.Cluster.from_dict",
        "geocomp.core.models.observation.Cluster.to_dict",
        "geocomp.core.models.observation.ClusterKind",
        "geocomp.core.models.observation.Observation.from_dict",
        "geocomp.core.models.observation.Observation.is_active",
        "geocomp.core.models.observation.Observation.spec",
        "geocomp.core.models.observation.Observation.supports_dimension",
        "geocomp.core.models.observation.Observation.to_dict",
        "geocomp.core.models.observation.RejectionRecord.from_dict",
        "geocomp.core.models.observation.RejectionRecord.to_dict",
        "geocomp.core.models.observation.observation_type_spec",
        "geocomp.core.models.position.CoordinateSystem.component_names",
        "geocomp.core.models.position.CoordinateSystem.component_units",
        "geocomp.core.models.position.Position.from_dict",
        "geocomp.core.models.position.Position.has_height",
        "geocomp.core.models.position.Position.height",
        "geocomp.core.models.position.Position.std_devs",
        "geocomp.core.models.position.Position.to_dict",
        "geocomp.core.models.solution.AdjustedStation.from_dict",
        "geocomp.core.models.solution.AdjustedStation.to_dict",
        "geocomp.core.models.solution.AdjustmentStatistics.from_dict",
        "geocomp.core.models.solution.AdjustmentStatistics.to_dict",
        "geocomp.core.models.solution.ErrorEllipse.from_dict",
        "geocomp.core.models.solution.ErrorEllipse.to_dict",
        "geocomp.core.models.solution.ObservationResult.from_dict",
        "geocomp.core.models.solution.ObservationResult.to_dict",
        "geocomp.core.models.solution.Provenance.from_dict",
        "geocomp.core.models.solution.Provenance.now",
        "geocomp.core.models.solution.Provenance.to_dict",
        "geocomp.core.models.solution.Solution.from_dict",
        "geocomp.core.models.solution.Solution.is_approximate",
        "geocomp.core.models.solution.Solution.is_superseded",
        "geocomp.core.models.solution.Solution.station",
        "geocomp.core.models.solution.Solution.to_dict",
        "geocomp.core.models.solution.SolutionKind",
        "geocomp.core.models.solution.TestResult.from_dict",
        "geocomp.core.models.solution.TestResult.to_dict",
        "geocomp.core.models.station.ConstraintMode",
        "geocomp.core.models.station.ConstraintSpec.constrains",
        "geocomp.core.models.station.ConstraintSpec.from_dict",
        "geocomp.core.models.station.ConstraintSpec.is_free",
        "geocomp.core.models.station.ConstraintSpec.to_dict",
        "geocomp.core.models.station.Station.display_name",
        "geocomp.core.models.station.Station.from_dict",
        "geocomp.core.models.station.Station.is_reference",
        "geocomp.core.models.station.Station.to_dict",
        "geocomp.core.models.station.StationType",
        "geocomp.core.monitoring.alerts.AlertKind",
        "geocomp.core.monitoring.alerts.AlertThreshold.applies_to",
        "geocomp.core.monitoring.compare.Comparison.dimension",
        "geocomp.core.monitoring.compare.Finding.to_dict",
        "geocomp.core.monitoring.congruency.Congruency.passed",
        "geocomp.core.monitoring.congruency.DeformationAnalysis.displacement",
        "geocomp.core.monitoring.congruency.DeformationAnalysis.significant",
        "geocomp.core.monitoring.congruency.Displacement.component",
        "geocomp.core.monitoring.congruency.Displacement.decision",
        "geocomp.core.monitoring.congruency.Displacement.horizontal_magnitude",
        "geocomp.core.monitoring.congruency.Displacement.magnitude",
        "geocomp.core.monitoring.congruency.Displacement.significant",
        "geocomp.core.monitoring.congruency.Displacement.std_devs",
        "geocomp.core.monitoring.congruency.Displacement.vertical_magnitude",
        "geocomp.core.monitoring.congruency.ReferenceCheck.implicated",
        "geocomp.core.monitoring.congruency.ReferenceCheck.passed",
        "geocomp.core.monitoring.series.StationSeries.horizontal_speed",
        "geocomp.core.monitoring.series.StationSeries.velocity_std_devs",
        "geocomp.core.monitoring.strain.Strain.deforming",
        "geocomp.core.preanalysis.inspection.InspectionReport.blocking",
        "geocomp.core.preanalysis.inspection.InspectionReport.can_adjust",
        "geocomp.core.preanalysis.inspection.InspectionReport.is_connected",
        "geocomp.core.preanalysis.inspection.InspectionReport.warnings",
        "geocomp.core.preanalysis.session.DesignSession.can_redo",
        "geocomp.core.preanalysis.session.DesignSession.can_undo",
        "geocomp.core.preanalysis.session.DesignSession.redo",
        "geocomp.core.preanalysis.session.DesignSession.remove_observation",
        "geocomp.core.preanalysis.session.DesignSession.set_datum",
        "geocomp.core.preanalysis.session.DesignSession.undo",
        "geocomp.core.settings_def.SectionDef.label_code",
        "geocomp.core.settings_resolution.ResolvedSetting.is_default",
        "geocomp.core.statistics.reliability.ReliabilityReport.by_observation",
        "geocomp.core.statistics.reliability.ReliabilityReport.note",
        "geocomp.core.statistics.reliability.ReliabilityReport.uncheckable",
        "geocomp.core.statistics.reliability.ReliabilityResult.is_uncheckable",
        "geocomp.core.statistics.tests.OutlierCandidate.is_uncheckable",
        "geocomp.core.statistics.tests.OutlierCandidate.to_test_result",
        "geocomp.core.statistics.tests.SnoopingReport.multiple_exceedances",
        "geocomp.core.statistics.tests.SnoopingReport.note",
        "geocomp.core.statistics.tests.SnoopingReport.worst",
        "geocomp.core.techniques.gnss.baselines.AntennaOffset.is_eccentric",
        "geocomp.core.techniques.gnss.baselines.AntennaReduction.is_eccentric",
        "geocomp.core.techniques.gnss.baselines.Baseline.component_names",
        "geocomp.core.techniques.gnss.products.Fetcher.exists",
        "geocomp.core.techniques.gnss.products.Fetcher.get",
        "geocomp.core.techniques.gnss.products.ProductKind",
        "geocomp.core.techniques.gnss.products.ProductRecord.from_dict",
        "geocomp.core.techniques.gnss.products.ProductRecord.to_dict",
        "geocomp.core.techniques.gnss.products.ProductService.urls",
        "geocomp.core.techniques.gnss.products.Resolution.paths",
        "geocomp.core.techniques.gnss.products.Resolution.records",
        "geocomp.core.techniques.gnss.quality.SessionQuality.duration_seconds",
        "geocomp.core.techniques.gnss.quality.SessionQuality.is_wholly_fixed",
        "geocomp.core.techniques.gnss.quality.SessionQuality.to_dict",
        "geocomp.core.techniques.gnss.stations.StationDatabase.add",
        "geocomp.core.techniques.gnss.stations.StationDatabase.from_dict",
        "geocomp.core.techniques.gnss.stations.StationDatabase.get",
        "geocomp.core.techniques.gnss.stations.StationDatabase.read",
        "geocomp.core.techniques.gnss.stations.StationDatabase.to_dict",
        "geocomp.core.techniques.gnss.stations.StationDatabase.write",
        "geocomp.core.techniques.gnss.trajectory.TrajectoryPoint.latitude_degrees",
        "geocomp.core.techniques.gnss.trajectory.TrajectoryPoint.longitude_degrees",
        "geocomp.core.techniques.gravimetry.network.GravityNetworkResult.gravity",
        "geocomp.core.techniques.gravimetry.readings.GravityReading.from_dict",
        "geocomp.core.techniques.gravimetry.readings.GravityReading.to_dict",
        "geocomp.core.techniques.gravimetry.readings.ReducedReading.from_dict",
        "geocomp.core.techniques.gravimetry.readings.ReducedReading.tide_system",
        "geocomp.core.techniques.gravimetry.readings.ReducedReading.to_dict",
        "geocomp.core.techniques.integration.combine.AppliedTransformation.to_dict",
        "geocomp.core.techniques.integration.techniques.Technique",
        "geocomp.core.techniques.levelling.line.LevellingLine.from_station",
        "geocomp.core.techniques.levelling.line.LevellingLine.has_distances",
        "geocomp.core.techniques.levelling.line.LevellingLine.setup_count",
        "geocomp.core.techniques.levelling.line.LevellingLine.to_station",
        "geocomp.core.techniques.levelling.orthometric.OrthometricCorrection.millimetres",
        "geocomp.core.techniques.levelling.readings.LevelSetup.mode",
        "geocomp.core.techniques.levelling.readings.StaffReading.has_distance",
        "geocomp.core.techniques.levelling.readings.ThreeWireReading.from_dict",
        "geocomp.core.techniques.levelling.readings.ThreeWireReading.to_dict",
        "geocomp.core.techniques.total_station.face.FaceReduction.blunder_candidates",
        "geocomp.core.techniques.total_station.face.FaceReduction.is_clean",
        "geocomp.core.techniques.total_station.levelling.Sight.horizontal_distance",
        "geocomp.core.techniques.total_station.pipeline.SetupResult.all_findings",
        "geocomp.core.techniques.total_station.pipeline.SetupResult.severity",
        "geocomp.core.techniques.total_station.pipeline.SetupResult.usable",
        "geocomp.core.techniques.total_station.readings.Face.is_direct",
        "geocomp.core.techniques.total_station.readings.FacePair.has_distance",
        "geocomp.core.techniques.total_station.readings.FacePair.target",
        "geocomp.core.techniques.total_station.readings.Setup.is_empty",
        "geocomp.core.techniques.total_station.survey.ResectionResult.is_reliable",
        "geocomp.core.uncertainty.Covariance.from_dict",
        "geocomp.core.uncertainty.Covariance.index",
        "geocomp.core.uncertainty.Covariance.size",
        "geocomp.core.uncertainty.Covariance.std_devs",
        "geocomp.core.uncertainty.Covariance.to_dict",
        "geocomp.core.uncertainty.Covariance.variance",
        "geocomp.core.uncertainty.Quantity.from_dict",
        "geocomp.core.uncertainty.Quantity.is_exact",
        "geocomp.core.uncertainty.Quantity.is_rigorous",
        "geocomp.core.uncertainty.Quantity.std_dev",
        "geocomp.core.units.Unit.symbol",
        "geocomp.core.visualization.geometry.DrawnEllipse.is_exaggerated",
        "geocomp.core.visualization.results.observation_rows",
        "geocomp.core.visualization.results.run_summary",
        "geocomp.core.visualization.results.station_rows",
        "geocomp.engines.base.EngineRun.ok",
        "geocomp.engines.base.EngineVersion.to_dict",
        "geocomp.engines.dynadjust.columns.Column.header",
        "geocomp.engines.dynadjust.columns.ColumnPlan.header",
        "geocomp.engines.dynadjust.columns.ColumnPlan.index",
        "geocomp.engines.dynadjust.columns.ColumnPlan.offsets",
        "geocomp.engines.dynadjust.columns.ColumnPlan.value",
        "geocomp.engines.dynadjust.columns.ColumnPlan.width",
        "geocomp.engines.dynadjust.crossvalidation.Agreement.difference",
        "geocomp.engines.dynadjust.crossvalidation.Comparison.disagreements",
        "geocomp.engines.dynadjust.crossvalidation.Comparison.largest_coordinate_difference",
        "geocomp.engines.dynadjust.dynaml.DynaMLDocument.to_dict",
        "geocomp.engines.dynadjust.engine.DynAdjustJob.epoch",
        "geocomp.engines.dynadjust.engine.PreparedJob.included",
        "geocomp.engines.dynadjust.engine.PreparedJob.output",
        "geocomp.engines.dynadjust.formats.format_metres",
        "geocomp.engines.dynadjust.read_dynaml.ReadReport.to_dict",
        "geocomp.engines.dynadjust.read_dynaml._position",
        "geocomp.engines.dynadjust.read_output.OutputPreamble.angular_coordinates",
        "geocomp.engines.manager.EngineStatus.available",
        "geocomp.engines.manager.EngineStatus.to_dict",
        "geocomp.engines.manager.Installation.to_dict",
        "geocomp.engines.manager.releases_for",
        "geocomp.engines.rtklib.config.RtklibConfig.to_dict",
        "geocomp.engines.rtklib.config.RtklibConfig.with_options",
        "geocomp.engines.rtklib.engine.RtklibEngine.locate",
        "geocomp.engines.rtklib.engine.RtklibEngine.version",
        "geocomp.engines.rtklib.engine.RtklibResult.ok",
        "geocomp.engines.rtklib.engine.RtklibResult.to_dict",
        "geocomp.engines.rtklib.read_pos.PosEpoch.is_ambiguity_fixed",
        "geocomp.engines.rtklib.read_pos.PosFormat",
        "geocomp.engines.rtklib.read_pos.PosFormat.layout",
        "geocomp.engines.rtklib.read_pos.PosSolution.components",
        "geocomp.engines.rtklib.read_pos.PosSolution.fixed_epochs",
        "geocomp.engines.rtklib.read_pos.PosSolution.to_dict",
        "geocomp.gui.basemap_offer.BaseMapOffer.layers_added",
        "geocomp.gui.basemap_offer.BaseMapOffer.unload",
        "geocomp.gui.compare_dialog.CompatibilityDialog.check",
        "geocomp.gui.compare_dialog.CompatibilityDialog.parameters",
        "geocomp.gui.menu.GeoCompMenu.menu",
        "geocomp.gui.results_panel.ResultsPanel.current",
        "geocomp.gui.results_panel.detach_from_project",
        "geocomp.gui.time_series_panel.TimeSeriesPanel.export_image",
        "geocomp.gui.time_series_panel.TimeSeriesPanel.refresh",
        "geocomp.gui.time_series_panel.TimeSeriesPanel.selected_stations",
        "geocomp.gui.time_series_panel.TimeSeriesPanel.set_document",
        "geocomp.gui.time_series_panel.detach_from_project",
        "geocomp.io.adjust.AdjustReport.counts_agree",
        "geocomp.io.fieldbook.ImportResult.is_clean",
        "geocomp.io.fieldbook.ImportResult.rejected_rows",
        "geocomp.io.levelbook.LevelImportResult.is_clean",
        "geocomp.io.levelbook.LevelImportResult.rejected_rows",
        "geocomp.io.levelbook.LevelMapping.for_field",
        "geocomp.io.levelbook.LevelMapping.from_dict",
        "geocomp.io.levelbook.LevelMapping.mapped_fields",
        "geocomp.io.levelbook.LevelMapping.parse_number",
        "geocomp.io.levelbook.LevelMapping.source_columns",
        "geocomp.io.levelbook.LevelMapping.to_dict",
        "geocomp.io.levelbook.LevelMapping.unrecognised",
        "geocomp.io.mapping.ColumnMapping.from_dict",
        "geocomp.io.mapping.ColumnMapping.to_dict",
        "geocomp.io.mapping.FieldMapping.for_field",
        "geocomp.io.mapping.FieldMapping.from_dict",
        "geocomp.io.mapping.FieldMapping.mapped_fields",
        "geocomp.io.mapping.FieldMapping.source_columns",
        "geocomp.io.mapping.FieldMapping.to_dict",
        "geocomp.io.mapping_editor.MappingEditor.constant_for",
        "geocomp.io.mapping_editor.MappingEditor.set_unit",
        "geocomp.io.mapping_editor.MappingEditor.unit_for",
        "geocomp.io.rinex.RinexHeader.is_observation",
        "geocomp.io.store.base.ProjectStore.close",
        "geocomp.io.store.base.ProjectStore.read_solutions",
        "geocomp.io.store.base.ProjectStore.schema_version",
        "geocomp.io.store.base.ProjectStore.tables",
        "geocomp.io.store.base._now",
        "geocomp.io.store.geopackage.GeoPackageStore.close",
        "geocomp.io.store.geopackage.GeoPackageStore.connection",
        "geocomp.io.store.geopackage.GeoPackageStore.migration_target",
        "geocomp.io.store.geopackage.GeoPackageStore.tables",
        "geocomp.io.store.migrations.MigrationReport.migrated",
        "geocomp.io.store.migrations.SqliteTarget.execute",
        "geocomp.io.store.migrations.SqliteTarget.transaction",
        "geocomp.io.store.postgis.PostgisStore.close",
        "geocomp.io.store.postgis.PostgisStore.connection",
        "geocomp.io.store.postgis.PostgisStore.migration_target",
        "geocomp.io.store.postgis.PostgisStore.tables",
        "geocomp.io.store.schema.Table.column",
        "geocomp.io.store.schema.Table.primary_key",
        "geocomp.io.store.schema.physical_type",
        "geocomp.io.store.schema.table",
        "geocomp.io.store.schema.table_names",
        "geocomp.io.store.transfer.CopyReport.identical",
        "geocomp.io.store.transfer.CopyReport.total",
        "geocomp.layers.builders.correction_layer_name",
        "geocomp.layers.builders.displacement_ellipse_layer_name",
        "geocomp.layers.builders.displacement_layer_name",
        "geocomp.layers.builders.velocity_layer_name",
        "geocomp.plugin.GeoCompPlugin.open_about",
        "geocomp.plugin.GeoCompPlugin.open_results_panel",
        "geocomp.plugin.GeoCompPlugin.open_series_panel",
        "geocomp.plugin.GeoCompPlugin.open_settings",
        "geocomp.plugin.GeoCompPlugin.run_again",
        "geocomp.provider.GeoCompProvider.icon",
        "geocomp.provider.GeoCompProvider.longName",
        "geocomp.provider.GeoCompProvider.name",
        "geocomp.provider.GeoCompProvider.tr",
        "geocomp.provider.GeoCompProvider.versionInfo",
        "geocomp.registry.AlgorithmSpec.label_code",
        "geocomp.registry.MenuGroup.label_code",
        "geocomp.reports.templates.Template.is_shipped",
        "geocomp.reports.templates.Template.tokens",
        "geocomp.services.downloads.QgisFetcher.exists",
        "geocomp.services.downloads.QgisFetcher.get",
        "geocomp.services.logging.LogLevel.qgis_level",
        "geocomp.services.messages.MessageTemplate.render",
    }
)

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
