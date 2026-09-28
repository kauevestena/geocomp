# SPDX-License-Identifier: GPL-2.0-or-later
"""The saved results of a monitoring run (``specs/14`` section 8.2, phase P10b).

Two documents, each plain JSON:

* **comparison** -- two epochs analysed: the epochs' metadata, every
  transformation and finding, the reference block's test and its localisation,
  every displacement with its covariance and tests, the global congruency test,
  the strain and the alerts. Or, when the block moved, the refusal itself: the
  block's test and every localisation step, and no displacements.
* **series** -- a station's offsets across every epoch with their
  uncertainties, and its velocity.

**Why a document rather than the objects.** The report, the map layers and the
time-series panel are three readers of one result, and a monitoring programme
reads it again at the next epoch. A document written once and read by all of
them means the report cannot say one thing while the map shows another, and
that a report rendered next year from the saved file says what it said today
(NFR-007). Nothing in either document reads the clock.

**Where to draw.** Each document carries the stations' plan positions in a map
CRS (``display``). A projected or local solution is drawn where it is. A
geocentric one is drawn in the UTM grid of its own frame, as the adjustment
layers are (``specs/19`` section 1.1), and each station carries the grid's
bearing of geodetic north, which turns an east/north displacement onto the
grid -- the displacement itself stays in the station's horizon.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from geocomp.core.adjustment.geocentric import ELLIPSOID
from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.cartesian import cartesian_to_geodetic
from geocomp.core.models import CoordinateSystem, Network, Solution, TestResult
from geocomp.core.monitoring.alerts import Alert, AlertThreshold
from geocomp.core.monitoring.compare import Comparison
from geocomp.core.monitoring.congruency import (
    Congruency,
    DeformationAnalysis,
    Displacement,
    ReferenceCheck,
)
from geocomp.core.monitoring.series import StationSeries
from geocomp.core.monitoring.strain import Strain

__all__ = [
    "COMPARISON_KIND",
    "SERIES_KIND",
    "VERSION",
    "comparison_document",
    "epoch_metadata",
    "read_comparison_document",
    "read_series_document",
    "refused_document",
    "series_document",
]

COMPARISON_KIND = "geocomp.monitoring.comparison"
SERIES_KIND = "geocomp.monitoring.series"
VERSION = 1

#: ``status`` of a comparison document.
ANALYSED = "analysed"
REFERENCE_BLOCK_UNSTABLE = "reference_block_unstable"


# -- building ------------------------------------------------------------------


def epoch_metadata(solution: Solution) -> dict[str, Any]:
    """What ``specs/14`` section 2 says a comparison has to know about an epoch."""
    provenance = solution.provenance
    return {
        "solution": solution.id,
        "network": solution.network_id,
        "epoch": solution.epoch.decimal_year,
        "crs": solution.crs,
        "datum": solution.datum_definition.value,
        "height_types": sorted({s.position.height_type.name for s in solution.adjusted_stations}),
        "geoid_models": sorted(
            {s.position.geoid_model for s in solution.adjusted_stations if s.position.geoid_model}
        ),
        "engine": (provenance.engine if provenance else "") or "in_house",
        "engine_version": provenance.engine_version if provenance else "",
        "uncertainty_mode": solution.uncertainty_mode.value,
        "variance_factor": solution.statistics.variance_factor_aposteriori,
        "degrees_of_freedom": solution.statistics.degrees_of_freedom,
    }


def comparison_document(
    analysis: DeformationAnalysis,
    first: Solution,
    second: Solution,
    *,
    strain: Strain | None = None,
    strain_note: str = "",
    thresholds: Sequence[AlertThreshold] = (),
    alerts: Sequence[Alert] = (),
    network: Network | None = None,
) -> dict[str, Any]:
    """Two epochs analysed, as a document every reader of the result shares.

    Args:
        strain_note: Why there is no strain, when there is none: the code of the
            refusal (``monitoring_strain_configuration``) or ``"not_requested"``.
        network: Where to draw stations a heights-only solution does not place.
    """
    comparison = analysis.comparison
    document = _common(comparison, first, second, network)
    document.update(
        {
            "status": ANALYSED,
            "confidence": analysis.confidence,
            "datum": analysis.datum,
            "reference": list(analysis.reference),
            "objects": list(analysis.objects),
            "reference_check": _reference_check(analysis.reference_check),
            "global_test": _congruency(analysis.global_test),
            "displacements": [_displacement(d) for d in analysis.displacements],
            "strain": _strain(strain) if strain is not None else None,
            "strain_note": "" if strain is not None else strain_note,
            "thresholds": [_threshold(t) for t in thresholds],
            "alerts": [_alert(a) for a in alerts],
        }
    )
    return document


def refused_document(
    comparison: Comparison,
    check: ReferenceCheck,
    first: Solution,
    second: Solution,
    *,
    reference: Sequence[str],
    datum: str,
    confidence: float,
    network: Network | None = None,
) -> dict[str, Any]:
    """The analysis that did not proceed, because the reference block moved.

    Kept as a document because the refusal *is* the result: which stations the
    localisation implicates, at which step, by how much -- what the user needs
    to decide which pillars to trust at the next run (``specs/14`` section 5).
    """
    document = _common(comparison, first, second, network)
    document.update(
        {
            "status": REFERENCE_BLOCK_UNSTABLE,
            "confidence": confidence,
            "datum": datum,
            "reference": list(reference),
            "objects": [],
            "reference_check": _reference_check(check),
            "global_test": None,
            "displacements": [],
            "strain": None,
            "strain_note": "",
            "thresholds": [],
            "alerts": [],
        }
    )
    return document


def series_document(
    stations: Sequence[StationSeries],
    solutions: Sequence[Solution],
    *,
    reference: Sequence[str] | None,
    datum: str,
    confidence: float,
    thresholds: Sequence[AlertThreshold] = (),
    alerts: Sequence[Alert] = (),
    network: Network | None = None,
) -> dict[str, Any]:
    """Every station's series and velocity, as a document."""
    ordered = sorted(solutions, key=lambda s: s.epoch.decimal_year)
    components = stations[0].components if stations else ()
    return {
        "kind": SERIES_KIND,
        "version": VERSION,
        "epochs": [epoch_metadata(s) for s in ordered],
        "components": list(components),
        "reference": list(reference) if reference else [],
        "datum": datum,
        "confidence": confidence,
        "mode": stations[0].mode.value if stations else "approximate",
        "strategies": sorted(s.value for s in stations[0].strategies) if stations else [],
        "display": _display(ordered[0], network),
        "stations": [_station_series(s) for s in stations],
        "thresholds": [_threshold(t) for t in thresholds],
        "alerts": [_alert(a) for a in alerts],
    }


# -- reading -------------------------------------------------------------------


_COMPARISON_KEYS = (
    "status",
    "epochs",
    "components",
    "reference",
    "reference_check",
    "displacements",
    "confidence",
    "display",
)
_SERIES_KEYS = ("epochs", "components", "stations", "confidence", "display")


def read_comparison_document(payload: Any) -> dict[str, Any]:
    """*payload* checked to be a comparison document this version reads.

    Raises:
        ValidationError: ``monitoring_document_kind`` when it is something else.
    """
    return _read(payload, COMPARISON_KIND, _COMPARISON_KEYS)


def read_series_document(payload: Any) -> dict[str, Any]:
    """*payload* checked to be a series document this version reads."""
    return _read(payload, SERIES_KIND, _SERIES_KEYS)


def _read(payload: Any, kind: str, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("kind") != kind:
        received = payload.get("kind") if isinstance(payload, dict) else type(payload).__name__
        raise ValidationError(
            "monitoring_document_kind",
            received=received or "(no kind)",
            expected=kind,
        )
    if payload.get("version") != VERSION:
        raise ValidationError(
            "monitoring_document_version",
            received=payload.get("version"),
            expected=VERSION,
        )
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValidationError("monitoring_document_incomplete", missing=missing, expected=list(keys))
    return payload


# -- internals -----------------------------------------------------------------


def _common(
    comparison: Comparison, first: Solution, second: Solution, network: Network | None
) -> dict[str, Any]:
    return {
        "kind": COMPARISON_KIND,
        "version": VERSION,
        "epochs": [epoch_metadata(first), epoch_metadata(second)],
        "frame": comparison.frame,
        "geocentric": comparison.geocentric,
        "components": list(comparison.components),
        "stations": list(comparison.stations),
        "mode": comparison.mode.value,
        "strategies": sorted(s.value for s in comparison.strategies),
        "variance_factor": comparison.variance_factor,
        "degrees_of_freedom": comparison.degrees_of_freedom,
        "transformations": [
            {**record.to_dict(), "accuracy": record.accuracy} for record in comparison.transformations
        ],
        "findings": [finding.to_dict() for finding in comparison.findings],
        "display": _display(first, network),
    }


def _display(solution: Solution, network: Network | None) -> dict[str, Any]:
    """Where each station is drawn, and how its horizon turns onto the map."""
    systems = {s.position.system for s in solution.adjusted_stations}
    if systems == {CoordinateSystem.CARTESIAN}:
        from geocomp.core.geodesy.projection import transverse_mercator
        from geocomp.core.visualization.display import display_grid, grid_bearing_of_north

        xyz = np.array([[q.value for q in s.position.values] for s in solution.adjusted_stations])
        latitude, longitude, _ = cartesian_to_geodetic(*xyz.mean(axis=0), ELLIPSOID)
        grid = display_grid(solution.crs, latitude, longitude)
        positions: dict[str, list[float]] = {}
        rotations: dict[str, float] = {}
        for station, point in zip(solution.adjusted_stations, xyz, strict=True):
            lat, lon, _h = cartesian_to_geodetic(*point, ELLIPSOID)
            east, north = transverse_mercator(lat, lon, grid.projection)
            positions[station.station_id] = [float(east), float(north)]
            rotations[station.station_id] = float(grid_bearing_of_north(lat, lon, grid.projection))
        return {"crs": grid.crs, "name": grid.name, "positions": positions, "rotations": rotations}

    positions = {}
    for station in solution.adjusted_stations:
        values = station.position.values
        east, north = float(values[0].value), float(values[1].value)
        if east == 0.0 and north == 0.0 and network is not None:
            placed = _network_plan(network, station.station_id)
            if placed is None:
                continue
            east, north = placed
        positions[station.station_id] = [east, north]
    if positions and all(p == [0.0, 0.0] for p in positions.values()):
        # A heights-only solution with nothing to place it: no map rather than
        # every station drawn on top of the others at the origin.
        positions = {}
    return {"crs": solution.crs, "name": solution.crs, "positions": positions, "rotations": {}}


def _network_plan(network: Network, station_id: str) -> tuple[float, float] | None:
    station = network.stations.get(station_id)
    position = None if station is None else (station.approx_position or station.constraint.position)
    if position is None or position.system is not CoordinateSystem.PROJECTED:
        return None
    east, north = position.values[0].value, position.values[1].value
    return (float(east), float(north)) if (east, north) != (0.0, 0.0) else None


def _test(test: TestResult | None) -> dict[str, Any] | None:
    return None if test is None else test.to_dict()


def _congruency(congruency: Congruency | None) -> dict[str, Any] | None:
    if congruency is None:
        return None
    return {
        "stations": list(congruency.stations),
        "omega": congruency.omega,
        "rank": congruency.rank,
        "test": congruency.test.to_dict(),
        "passed": congruency.passed,
    }


def _reference_check(check: ReferenceCheck) -> dict[str, Any]:
    return {
        "test": _congruency(check.test),
        "passed": check.passed,
        "steps": [
            {
                "test": _congruency(step.test),
                "contributions": {k: float(v) for k, v in step.contributions.items()},
                "removed": step.removed,
            }
            for step in check.steps
        ],
        "stable": list(check.stable),
        "final": _congruency(check.final),
        "implicated": list(check.implicated),
    }


def _displacement(d: Displacement) -> dict[str, Any]:
    return {
        "station": d.station_id,
        "role": d.role,
        "components": list(d.components),
        "values": [float(v) for v in d.values],
        "std_devs": [float(v) for v in d.std_devs],
        "covariance": np.asarray(d.covariance, dtype=float).tolist(),
        "test": _test(d.test),
        "horizontal": _test(d.horizontal),
        "vertical": _test(d.vertical),
        "ellipse": None if d.ellipse is None else d.ellipse.to_dict(),
        "decision": d.decision,
        "significant": d.significant,
        "magnitude": d.magnitude,
        "horizontal_magnitude": d.horizontal_magnitude,
        "vertical_magnitude": d.vertical_magnitude,
    }


def _strain(s: Strain) -> dict[str, Any]:
    return {
        "stations": list(s.stations),
        "translation": list(s.translation),
        "rotation": s.rotation,
        "strain_tensor": list(s.strain_tensor),
        "dilatation": s.dilatation,
        "shear": s.shear,
        "principal": list(s.principal),
        "azimuth": s.azimuth,
        "std_devs": {k: float(v) for k, v in s.std_devs.items()},
        "rigid_translation": list(s.rigid_translation),
        "rigid_rotation": s.rigid_rotation,
        "strain_test": s.strain_test.to_dict(),
        "deforming": s.deforming,
    }


def _threshold(t: AlertThreshold) -> dict[str, Any]:
    return {
        "kind": t.kind.value,
        "limit": t.limit,
        "stations": None if t.stations is None else sorted(t.stations),
        "group": t.group,
    }


def _alert(a: Alert) -> dict[str, Any]:
    return {
        "station": a.station_id,
        "kind": a.threshold.kind.value,
        "limit": a.threshold.limit,
        "group": a.threshold.group,
        "value": a.value,
        "exceeded": a.exceeded,
        "significant": a.significant,
    }


def _station_series(s: StationSeries) -> dict[str, Any]:
    covariance = None if s.velocity_covariance is None else np.asarray(s.velocity_covariance).tolist()
    return {
        "station": s.station_id,
        "components": list(s.components),
        "points": [
            {
                "solution": p.solution_id,
                "epoch": p.epoch,
                "offsets": [float(v) for v in p.offsets],
                "std_devs": [float(v) for v in p.std_devs],
            }
            for p in s.points
        ],
        "velocity": None if s.velocity is None else [float(v) for v in s.velocity],
        "velocity_std_devs": None if s.velocity_std_devs is None else list(s.velocity_std_devs),
        "velocity_covariance": covariance,
        "velocity_test": _test(s.velocity_test),
        "speed": s.speed,
        "degrees_of_freedom": s.degrees_of_freedom,
        "weighted_squares": s.weighted_squares,
    }
