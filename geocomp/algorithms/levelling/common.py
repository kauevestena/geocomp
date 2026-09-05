# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared plumbing for the levelling algorithms.

The same three needs the total-station algorithms have -- a profile library, a
document to read, and one way of presenting findings -- plus the two records
levelling adds: the level profile and the accuracy class.

Documents are JSON, and the chain is deliberately explicit: the importer writes
setups and lines, the reductions read them and write height differences, the
closure and the network read those. Each step's output is a file a user can
open, which is what ``specs/01`` section 3 means by every intermediate being
visible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.reporting import escape, render_table
from geocomp.core.errors import GeoCompError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments import LevellingClass, LevelProfile, ProfileLibrary
from geocomp.core.instruments.stochastic import STAFF_READING, StochasticDefaults
from geocomp.core.techniques.levelling import (
    LevellingLine,
    LevelSetup,
    LineReduction,
    StaffReading,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = [
    "default_level",
    "findings_table",
    "level_from_parameters",
    "levelling_class_from_parameters",
    "load_json",
    "load_level_library",
    "read_lines",
    "read_reductions",
    "reduction_from_dict",
    "reduction_to_dict",
    "setup_to_dict",
    "severity_label",
    "staff_defaults",
    "summarise_findings",
    "write_document",
]

_CONTEXT = "GeoCompLevelling"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def load_json(path: str, *, parameter: str) -> dict:
    """Read a JSON document, failing with a message that names the parameter."""
    if not path:
        raise QgsProcessingException(
            _tr("No file was given for parameter '%1'.").replace("%1", parameter)
        )
    source = Path(path)
    if not source.is_file():
        raise QgsProcessingException(
            _tr("The file '%1' does not exist.").replace("%1", str(source))
        )
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QgsProcessingException(
            _tr("'%1' is not valid JSON: %2").replace("%1", str(source)).replace("%2", str(exc))
        ) from exc
    if not isinstance(payload, dict):
        raise QgsProcessingException(
            _tr(
                "'%1' does not contain a GeoComp document: its top level is not an object."
            ).replace("%1", str(source))
        )
    return payload


def write_document(path: str, payload: dict[str, Any]) -> None:
    """Write a GeoComp JSON document, reproducibly (NFR-007)."""
    if not path:
        return
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def default_level() -> LevelProfile:
    """A generic modern automatic level, for users who have configured none.

    Half a millimetre on a staff reading, 0.7 mm per root kilometre, 0.3 mm per
    setup, and a stadia constant of 100. **Nominal figures from no particular
    manufacturer**, which is why everything computed from them is
    ``APPROXIMATE`` with ``NOMINAL_PRECISION`` and why the reports say so. It
    exists so a first run works, not so a real survey uses it.

    The collimation is an exact zero -- not "we assume it is small" but "no
    two-peg test was supplied, so no correction is applied and the imbalance is
    reported instead". Which of those two happened is visible in the report.
    """
    return LevelProfile(
        id="generic",
        name="Generic automatic level (0.7 mm per root km)",
        sigma_reading=0.0005,
        sigma_per_km=0.0007,
        sigma_per_setup=0.0003,
        stadia_factor=100.0,
    )


def load_level_library(path: str) -> ProfileLibrary:
    """Read a profile library, or return one holding :func:`default_level`."""
    if not path:
        library = ProfileLibrary()
        library.add_level(default_level())
        return library
    try:
        return ProfileLibrary.from_dict(load_json(path, parameter="PROFILES"))
    except GeoCompError as exc:
        from geocomp.services.messages import message_for

        raise QgsProcessingException(
            _tr("'%1' could not be read as an instrument profile library. %2")
            .replace("%1", path)
            .replace("%2", message_for(exc))
        ) from exc


def level_from_parameters(
    *,
    profiles: str,
    level_id: str,
    collimation: float,
    collimation_sigma: float,
) -> LevelProfile:
    """The level to reduce with, from the run's parameters.

    A collimation given on the run overrides the library's, because a two-peg
    test done this morning is better evidence than a profile written last year.
    """
    library = load_level_library(profiles)
    try:
        level = library.level(level_id or None)
    except GeoCompError as exc:
        from geocomp.services.messages import message_for

        raise QgsProcessingException(message_for(exc)) from exc

    if collimation == 0.0 and collimation_sigma == 0.0:
        return level
    from dataclasses import replace

    return replace(
        level,
        collimation=Quantity.from_std_dev(collimation, collimation_sigma, Unit.RADIAN)
        if collimation_sigma > 0.0
        else Quantity.exact(collimation, Unit.RADIAN),
        applies_collimation=False,
    )


def levelling_class_from_parameters(
    *,
    coefficient: float,
    max_sight_length: float,
    max_sight_imbalance: float,
    max_accumulated_imbalance: float,
) -> LevellingClass | None:
    """The class to judge against, or ``None`` when nothing was configured.

    ``None`` rather than a permissive class: a closure with no tolerance is
    reported without a verdict, and inventing one to have something to compare
    against would be worse than saying nothing (``specs/10`` section 3).
    """
    if not any(
        (coefficient, max_sight_length, max_sight_imbalance, max_accumulated_imbalance)
    ):
        return None
    return LevellingClass(
        id="run",
        name=_tr("Configured for this run"),
        tolerance_coefficient=coefficient,
        max_sight_length=max_sight_length,
        max_sight_imbalance=max_sight_imbalance,
        max_accumulated_imbalance=max_accumulated_imbalance,
        source=_tr("entered on the algorithm's parameters"),
    )


def staff_defaults(sigma_reading: float) -> StochasticDefaults | None:
    """A staff-reading type default from the run, or ``None`` for none.

    Zero means "not configured", matching the settings default: the resolution
    then refuses rather than weighting a reading with a standard deviation of
    zero, which would give it infinite weight.
    """
    if sigma_reading <= 0.0:
        return None
    return StochasticDefaults().with_default(STAFF_READING, sigma_reading)


# -- documents ------------------------------------------------------------


def _quantity(quantity: Quantity | None) -> dict[str, Any] | None:
    return quantity.to_dict() if quantity is not None else None


def _reading_to_dict(reading: StaffReading) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "station": reading.station,
        "reading": reading.reading.to_dict(),
    }
    if reading.distance is not None:
        payload["distance"] = reading.distance.to_dict()
    if reading.three_wire is not None:
        payload["three_wire"] = reading.three_wire.to_dict()
    if reading.meta:
        payload["meta"] = dict(reading.meta)
    return payload


def setup_to_dict(setup: LevelSetup) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": setup.id,
        "backsight": _reading_to_dict(setup.backsight),
        "foresights": [_reading_to_dict(sight) for sight in setup.foresights],
    }
    if setup.level_id:
        payload["level_id"] = setup.level_id
    return payload


def _reading_from_dict(payload: dict[str, Any]) -> StaffReading:
    from geocomp.core.techniques.levelling import ThreeWireReading

    wires = payload.get("three_wire")
    return StaffReading(
        station=payload["station"],
        reading=Quantity.from_dict(payload["reading"]),
        distance=Quantity.from_dict(payload["distance"]) if payload.get("distance") else None,
        three_wire=ThreeWireReading.from_dict(wires) if wires else None,
        meta=dict(payload.get("meta", {})),
    )


def _setup_from_dict(payload: dict[str, Any]) -> LevelSetup:
    return LevelSetup(
        id=payload["id"],
        backsight=_reading_from_dict(payload["backsight"]),
        foresights=tuple(_reading_from_dict(p) for p in payload["foresights"]),
        level_id=payload.get("level_id"),
    )


def read_lines(path: str, *, parameter: str = "SETUPS") -> list[LevellingLine]:
    """Read the lines an import wrote."""
    payload = load_json(path, parameter=parameter)
    if "lines" not in payload:
        raise QgsProcessingException(
            _tr(
                "'%1' holds no levelling lines. Run 'Import levelling field book' first."
            ).replace("%1", path)
        )
    try:
        return [
            LevellingLine(
                id=line["id"],
                setups=tuple(_setup_from_dict(s) for s in line["setups"]),
                level_id=line.get("level_id"),
                levelling_class_id=line.get("levelling_class_id"),
            )
            for line in payload["lines"]
        ]
    except (GeoCompError, KeyError, TypeError, ValueError) as exc:
        raise QgsProcessingException(
            _tr("'%1' could not be read as levelling lines: %2")
            .replace("%1", path)
            .replace("%2", str(exc))
        ) from exc


def reduction_to_dict(reduction: LineReduction) -> dict[str, Any]:
    return {
        "line_id": reduction.line_id,
        "from_station": reduction.from_station,
        "to_station": reduction.to_station,
        "height_difference": reduction.height_difference.to_dict(),
        "raw_height_difference": reduction.raw_height_difference.to_dict(),
        "length_km": reduction.length_km,
        "setup_count": reduction.setup_count,
        "accumulated_imbalance": reduction.accumulated_imbalance,
        "collimation": _quantity(reduction.collimation),
        "setup_ids": [setup.setup_id for setup in reduction.setups],
        "side_shots": [
            {
                "setup_id": shot.setup_id,
                "from_station": shot.from_station,
                "to_station": shot.to_station,
                "height_difference": shot.height_difference.to_dict(),
            }
            for shot in reduction.side_shots
        ],
    }


def read_reductions(path: str, *, parameter: str = "REDUCTIONS") -> list[dict[str, Any]]:
    """Read the line reductions a reduction wrote, as plain dictionaries.

    Plain dictionaries rather than :class:`LineReduction` objects: the closure
    and the network need the height difference, the length and the setup count,
    and rebuilding the per-setup covariances to reach them would be work in
    service of nothing.
    """
    payload = load_json(path, parameter=parameter)
    lines = payload.get("lines")
    if not isinstance(lines, list) or not lines:
        raise QgsProcessingException(
            _tr(
                "'%1' holds no reduced levelling lines. Run 'Equal sights' first."
            ).replace("%1", path)
        )
    for line in lines:
        if "height_difference" not in line:
            raise QgsProcessingException(
                _tr("'%1' is not a levelling reduction document.").replace("%1", path)
            )
    return lines


# -- findings -------------------------------------------------------------


def severity_label(severity: Severity) -> tuple[str, str]:
    return {
        Severity.BLOCKING: (_tr("Blocking"), "blocking"),
        Severity.WARNING: (_tr("Warning"), "warning"),
        Severity.INFO: (_tr("Information"), ""),
    }[severity]


def findings_table(findings: tuple[Finding, ...]) -> str:
    """One findings table, the same in every levelling report."""
    if not findings:
        return f"<p>{escape(_tr('Nothing to report.'))}</p>"

    rows = []
    for finding in findings:
        label, css = severity_label(finding.severity)
        marker = f'<span class="{css}">{escape(label)}</span>' if css else escape(label)
        involves = ", ".join(finding.stations + finding.observations)
        rows.append(
            [
                marker,
                f"<code>{escape(finding.code)}</code>",
                escape(finding.message),
                escape(involves) or "—",
            ]
        )
    return render_table(
        [
            escape(_tr("Severity")),
            escape(_tr("Code")),
            escape(_tr("Finding")),
            escape(_tr("Involves")),
        ],
        rows,
    )


def summarise_findings(findings: tuple[Finding, ...], feedback) -> tuple[int, int]:
    """Push every finding to the log and return the blocking and warning counts."""
    blocking = warnings = 0
    for finding in findings:
        line = f"[{finding.code}] {finding.message}"
        if finding.severity is Severity.BLOCKING:
            blocking += 1
            feedback.pushWarning(line)
        elif finding.severity is Severity.WARNING:
            warnings += 1
            feedback.pushWarning(line)
        else:
            feedback.pushInfo(line)
    if not findings:
        feedback.pushInfo(_tr("Nothing to report."))
    return blocking, warnings


def reduction_from_dict(payload: dict[str, Any]) -> LineReduction:
    """Rebuild the parts of a line reduction a closure needs.

    The per-setup covariances are not rebuilt: a closure needs the height
    difference, the length and the setup count, and the setups only to name the
    shares. A :class:`SetupReduction` carrying an empty difference list would be
    a lie, so the shares carry no per-setup sigma when read back from a document
    -- the report shows a dash rather than a fabricated ratio.
    """
    from geocomp.core.techniques.levelling.schemes import SetupReduction
    from geocomp.core.uncertainty import Covariance

    empty = Covariance(matrix=[[0.0]], labels=("none",), units=(Unit.METRE,))
    setups = tuple(
        SetupReduction(
            setup_id=setup_id,
            from_station=payload["from_station"],
            to_stations=(),
            height_differences=(),
            covariance=empty,
        )
        for setup_id in payload.get("setup_ids", ())
    )
    return LineReduction(
        line_id=payload["line_id"],
        from_station=payload["from_station"],
        to_station=payload["to_station"],
        height_difference=Quantity.from_dict(payload["height_difference"]),
        raw_height_difference=Quantity.from_dict(
            payload.get("raw_height_difference", payload["height_difference"])
        ),
        setups=setups,
        length_km=payload.get("length_km"),
        setup_count=int(payload.get("setup_count", len(setups))),
        accumulated_imbalance=payload.get("accumulated_imbalance"),
    )
