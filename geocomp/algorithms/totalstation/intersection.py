# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_intersection`` -- forward intersection (FR-408).

``specs/09-module-total-station.md`` section 4.3.

Coordinates of a sighted point from two or more oriented stations. With more
than the minimum, by least squares with residuals and an error ellipse.

**Weak geometry is reported through the ellipse's shape** rather than left for
the user to discover. Near-parallel rays do not determine a point however
precise each individual sighting is, and the ellipse is where that shows.
"""

from __future__ import annotations

import json
import math
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import load_json
from geocomp.core.errors import GeoCompError
from geocomp.core.statistics.ellipses import error_ellipse
from geocomp.core.techniques.total_station import forward_intersection
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["IntersectionAlgorithm"]

_CONTEXT = "IntersectionAlgorithm"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


SIGHTINGS = "SIGHTINGS"
TARGET = "TARGET"
SIGMA_AZIMUTH = "SIGMA_AZIMUTH"
CONFIDENCE = "CONFIDENCE"
OUTPUT_POSITION = "OUTPUT_POSITION"
OUTPUT_HTML = "OUTPUT_HTML"
EASTING = "EASTING"
NORTHING = "NORTHING"
SEMI_MAJOR = "SEMI_MAJOR"
SEMI_MINOR = "SEMI_MINOR"
WEAK_GEOMETRY = "WEAK_GEOMETRY"


class IntersectionAlgorithm(GeoCompAlgorithm):
    """Coordinates of a point sighted from two or more known stations."""

    TR_CONTEXT = "IntersectionAlgorithm"

    def displayName(self) -> str:
        return self.tr("Forward intersection")

    def shortDescription(self) -> str:
        return self.tr("Fix a sighted point from two or more oriented known stations.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes the coordinates of a point sighted from two or more known stations "
            "whose orientation is known, by least squares. Two stations give a unique "
            "solution; more give residuals and a covariance.</p>"
            "<p><b>Weak geometry is reported rather than left to be discovered.</b> "
            "Near-parallel rays do not determine a point however precise each sighting is, "
            "and the error ellipse is where that shows: when it comes out more than ten "
            "times longer than it is wide, the run says so. Rays that are exactly parallel "
            "are refused, because there is no intersection to return.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Sightings</b> &mdash; a JSON object mapping each observing station to its "
            "position and the azimuth it observed:</p>"
            '<pre>{"A": {"position": [0, 0], "azimuth": 57.99},\n'
            ' "B": {"position": [1000, 0], "azimuth": 300.02}}</pre>'
            "<p>Positions in metres, azimuths in degrees from north, clockwise. Azimuths "
            "rather than circle readings: an intersection is computed from <i>oriented</i> "
            "stations, and where the orientation is unknown the station has to be resected "
            "first.</p>"
            "<p><b>Target</b> &mdash; the name to give the computed point. <b>Azimuth "
            "precision</b> (degrees) &mdash; applied to every sighting that does not state "
            "its own, and what the resulting ellipse is scaled by.</p>"
            "<p><b>Confidence level</b> &mdash; for the reported ellipse.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Position</b> &mdash; a JSON document in the shape Classical network takes "
            "as approximate coordinates. <b>Report</b> &mdash; HTML. Scalars: "
            "<code>EASTING</code>, <code>NORTHING</code>, <code>SEMI_MAJOR</code>, "
            "<code>SEMI_MINOR</code> in metres and <code>WEAK_GEOMETRY</code>.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(SIGHTINGS, self.tr("Sightings"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterString(TARGET, self.tr("Target name"), defaultValue="P")
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                SIGMA_AZIMUTH,
                self.tr("Azimuth precision (°)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=5.0 / 3600.0,
                minValue=1e-9,
                maxValue=5.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence level"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.95,
                minValue=0.5,
                maxValue=0.9999,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_POSITION,
                self.tr("Position"),
                self.tr("GeoComp coordinates (*.json)"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_HTML,
                self.tr("Report"),
                self.tr("HTML files (*.html)"),
                optional=True,
                createByDefault=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        default_sigma = math.radians(self.parameterAsDouble(parameters, SIGMA_AZIMUTH, context))
        sightings = _read_sightings(
            self.parameterAsFile(parameters, SIGHTINGS, context), default_sigma
        )
        target = self.parameterAsString(parameters, TARGET, context).strip() or "P"
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)

        feedback.setProgress(30)
        feedback.pushInfo(
            self.tr("Intersecting '%1' from %2 station(s).")
            .replace("%1", target)
            .replace("%2", str(len(sightings)))
        )
        try:
            result = forward_intersection(target, sightings)
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        easting, northing = result.position
        ellipse = error_ellipse(
            result.covariance.matrix,
            confidence=confidence,
            degrees_of_freedom=max(len(sightings) - 2, 0) or None,
        )

        feedback.setProgress(70)
        feedback.pushInfo(
            self.tr("E %1, N %2; ellipse %3 by %4 mm.")
            .replace("%1", format_number(easting.value))
            .replace("%2", format_number(northing.value))
            .replace("%3", format_number(ellipse.semi_major * 1000.0, 1))
            .replace("%4", format_number(ellipse.semi_minor * 1000.0, 1))
        )
        for finding in result.findings:
            feedback.pushWarning(f"[{finding.code}] {finding.message}")

        outputs = self._write(parameters, context, target, result, ellipse, confidence)
        feedback.setProgress(100)

        return {
            EASTING: easting.value,
            NORTHING: northing.value,
            SEMI_MAJOR: ellipse.semi_major,
            SEMI_MINOR: ellipse.semi_minor,
            WEAK_GEOMETRY: bool(result.findings),
            **outputs,
        }

    # -- outputs ---------------------------------------------------------

    def _write(
        self, parameters, context, target, result, ellipse, confidence
    ) -> dict[str, Any]:
        easting, northing = result.position
        position = self.parameterAsFileOutput(parameters, OUTPUT_POSITION, context)
        if position:
            with open(position, "w", encoding="utf-8") as handle:
                json.dump(
                    {target: [easting.value, northing.value, 0.0]},
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(target, result, ellipse, confidence))

        return {OUTPUT_POSITION: position, OUTPUT_HTML: html_target}

    def _render(self, target, result, ellipse, confidence) -> str:
        easting, northing = result.position
        summary = [
            [escape(self.tr("Point")), escape(target)],
            [escape(self.tr("Easting (m)")), format_number(easting.value)],
            [escape(self.tr("Northing (m)")), format_number(northing.value)],
            [escape(self.tr("Semi-major (mm)")), format_number(ellipse.semi_major * 1000.0, 2)],
            [escape(self.tr("Semi-minor (mm)")), format_number(ellipse.semi_minor * 1000.0, 2)],
            [
                escape(self.tr("Ellipse azimuth (°)")),
                format_number(math.degrees(ellipse.azimuth), 2),
            ],
            [escape(self.tr("Confidence level")), format_number(confidence, 3)],
        ]

        body = [
            f"<h2>{escape(self.tr('Forward intersection'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary),
            f"<h2>{escape(self.tr('Residuals'))}</h2>",
            render_table(
                [escape(self.tr("Station")), escape(self.tr('Residual (")'))],
                [
                    [escape(station), format_number(math.degrees(value) * 3600.0, 2)]
                    for station, value in sorted(result.residuals.items())
                ],
            ),
        ]
        for finding in result.findings:
            body.append(render_note(finding.message, label=self.tr("Geometry")))

        return render_document(
            self.tr("Forward intersection report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_intersection")),
        )


def _read_sightings(path: str, default_sigma: float):
    """Read the sightings document: station -> (position, azimuth)."""
    payload = load_json(path, parameter=SIGHTINGS)
    sightings: dict[str, tuple[tuple[Quantity, Quantity], Quantity]] = {}

    for name, entry in payload.items():
        if not isinstance(entry, dict) or "position" not in entry or "azimuth" not in entry:
            raise QgsProcessingException(
                _tr(
                    "Sighting '%1' must be an object with a 'position' pair and an 'azimuth'."
                ).replace("%1", str(name))
            )
        try:
            easting, northing = (float(v) for v in list(entry["position"])[:2])
            azimuth = math.radians(float(entry["azimuth"]))
        except (TypeError, ValueError) as exc:
            raise QgsProcessingException(
                _tr("Sighting '%1' does not hold numbers.").replace("%1", str(name))
            ) from exc

        sigma = entry.get("sigma")
        sigma = math.radians(float(sigma)) if sigma is not None else default_sigma
        sightings[str(name)] = (
            (Quantity.exact(easting, Unit.METRE), Quantity.exact(northing, Unit.METRE)),
            Quantity.from_std_dev(azimuth, sigma, Unit.RADIAN),
        )

    if len(sightings) < 2:
        raise QgsProcessingException(
            _tr("At least two sightings are needed; the document holds %1.").replace(
                "%1", str(len(sightings))
            )
        )
    return sightings
