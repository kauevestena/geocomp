# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared plumbing for the total-station algorithms.

Three things they all need: an instrument profile library, a field-book or
network document, and a consistent way to present findings. Findings in
particular: every one of these algorithms can produce them, and a user who has
learnt to read the table in one report should not have to re-learn it in the
next.
"""

from __future__ import annotations

import json
from pathlib import Path

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.reporting import escape, render_note, render_table
from geocomp.core.errors import GeoCompError
from geocomp.core.findings import Finding, Severity
from geocomp.core.instruments import InstrumentProfile, ProfileLibrary
from geocomp.core.instruments.stochastic import StochasticDefaults
from geocomp.core.techniques.total_station.readings import (
    Face,
    FacePair,
    FaceReading,
    Setup,
)
from geocomp.core.uncertainty import Quantity
from geocomp.io import FieldMapping, infer_mapping

__all__ = [
    "default_library",
    "findings_table",
    "load_json",
    "load_mapping",
    "load_profiles",
    "read_readings",
    "severity_label",
    "stochastic_defaults",
    "summarise_findings",
]

_CONTEXT = "GeoCompTotalStation"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def load_json(path: str, *, parameter: str) -> dict:
    """Read a JSON document, failing with a message that names the parameter.

    FR-035: validate before computing, and say which input was wrong.
    """
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
            _tr("'%1' does not contain a GeoComp document: its top level is not an object.")
            .replace("%1", str(source))
        )
    return payload


def load_profiles(path: str) -> ProfileLibrary:
    """Read an instrument profile library, or return the built-in default.

    An empty path is legitimate: a user with no calibrated instrument still has
    to be able to run something, and :func:`default_library` says plainly what
    it assumed.
    """
    if not path:
        return default_library()
    try:
        return ProfileLibrary.from_dict(load_json(path, parameter="PROFILES"))
    except GeoCompError as exc:
        from geocomp.services.messages import message_for

        raise QgsProcessingException(
            _tr("'%1' could not be read as an instrument profile library. %2")
            .replace("%1", path)
            .replace("%2", message_for(exc))
        ) from exc


def default_library() -> ProfileLibrary:
    """A generic modern total station, for users who have configured none.

    Two millimetres plus two parts per million on distance, five arcseconds on
    angles, one millimetre on the heights. Nominal figures from no particular
    manufacturer, which is why everything computed from them is marked
    ``APPROXIMATE`` with :attr:`Strategy.NOMINAL_PRECISION` and why the
    algorithms say so in their reports. It exists so that a first run works, not
    so that a real survey uses it.
    """
    library = ProfileLibrary()
    library.add_instrument(
        InstrumentProfile(id="generic", name="Generic total station (2 mm + 2 ppm, 5 arcsec)")
    )
    return library


def stochastic_defaults(
    direction: float, zenith: float, distance: float
) -> StochasticDefaults | None:
    """Per-type defaults from the run's parameters, or ``None`` for none.

    Zero means "not configured", matching the settings defaults: the resolution
    then falls through to refusing rather than weighting an observation with a
    standard deviation of zero, which would give it infinite weight.
    """
    values = {
        "direction": direction,
        "zenith_angle": zenith,
        "slope_distance": distance,
        "horizontal_distance": distance,
    }
    configured = {kind: value for kind, value in values.items() if value > 0.0}
    return StochasticDefaults(values=configured) if configured else None


def load_mapping(path: str, header: list[str]) -> FieldMapping:
    """Read a saved field mapping, or infer one from the header.

    Inference is a starting point a user reviews in the dialog (FR-160). Here,
    where there is no dialog, it is what makes a first run possible on a layout
    GeoComp recognises -- and the report states which columns it mapped, so an
    inferred mapping is never silently trusted.
    """
    if not path:
        return infer_mapping(header, name="inferred")
    try:
        return FieldMapping.from_dict(load_json(path, parameter="MAPPING"))
    except (GeoCompError, KeyError, TypeError, ValueError) as exc:
        raise QgsProcessingException(
            _tr("'%1' could not be read as a field mapping: %2")
            .replace("%1", path)
            .replace("%2", str(exc))
        ) from exc


def severity_label(severity: Severity) -> tuple[str, str]:
    """Translated name and CSS class for a severity."""
    return {
        Severity.BLOCKING: (_tr("Blocking"), "blocking"),
        Severity.WARNING: (_tr("Warning"), "warning"),
        Severity.INFO: (_tr("Information"), ""),
    }[severity]


def findings_table(findings: tuple[Finding, ...]) -> str:
    """One findings table, the same in every total-station report."""
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
    """Push every finding to the log and return the blocking and warning counts.

    Blocking findings go through ``pushWarning`` so they are visible even when
    the run is allowed to succeed: a problem that only appears in an output file
    nobody opens has not been reported.
    """
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


def note(text: str) -> str:
    """A call-out box. Thin wrapper so the algorithms import one module."""
    return render_note(text)


def read_readings(path: str, *, parameter: str = "READINGS") -> list[Setup]:
    """Read the document :mod:`~geocomp.algorithms.totalstation.import_fieldbook` writes.

    A file rather than an in-memory hand-off because ``specs/16`` section 9
    requires the steps to chain in the graphical modeller, and a file is the only
    thing a modeller can pass between two algorithms.
    """
    payload = load_json(path, parameter=parameter)
    if payload.get("kind") != "geocomp.readings":
        raise QgsProcessingException(
            _tr(
                "'%1' is not a GeoComp readings document. Run Import field book first, or "
                "choose the file it produced."
            ).replace("%1", path)
        )

    setups: list[Setup] = []
    for entry in payload.get("setups", ()):
        try:
            setup = Setup(
                station=entry["station"],
                instrument_height=Quantity.from_dict(entry["instrument_height"]),
                instrument_id=entry.get("instrument_id"),
                reflector_id=entry.get("reflector_id"),
            )
            for pair in entry.get("pairs", ()):
                setup.pairs.append(
                    FacePair(_reading(pair["direct"]), _reading(pair["reverse"]))
                )
            for single in entry.get("singles", ()):
                setup.singles.append(_reading(single))
        except (GeoCompError, KeyError, TypeError, ValueError) as exc:
            raise QgsProcessingException(
                _tr("'%1' could not be read as readings: %2")
                .replace("%1", path)
                .replace("%2", str(exc))
            ) from exc
        setups.append(setup)

    if not setups:
        raise QgsProcessingException(
            _tr("'%1' contains no setups, so there is nothing to process.").replace("%1", path)
        )
    return setups


def _reading(payload: dict) -> FaceReading:
    return FaceReading(
        target=payload["target"],
        face=Face.DIRECT if payload["face"] == "direct" else Face.REVERSE,
        horizontal=Quantity.from_dict(payload["horizontal"]),
        zenith=Quantity.from_dict(payload["zenith"]),
        distance=(
            Quantity.from_dict(payload["distance"]) if "distance" in payload else None
        ),
        target_height=(
            Quantity.from_dict(payload["target_height"])
            if "target_height" in payload
            else None
        ),
        set_number=int(payload.get("set_number", 1)),
        extra=dict(payload.get("extra", {})),
    )
