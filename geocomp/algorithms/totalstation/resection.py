# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_resection`` -- fix the occupied station (FR-407).

``specs/09-module-total-station.md`` section 4.2.

Coordinates of the occupied station from directions to known points, by least
squares over *n* points with the setup's orientation as a third unknown.

**The danger circle is detected and reported, not solved.** When the occupied
station lies on the circle through three known points the problem is
indeterminate -- every point on that circle sees the three in the same
directions -- and a number returned from there looks exactly like a coordinate
and is not one.
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
from geocomp.algorithms.totalstation.common import load_json, read_reductions
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.total_station import resection
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["ResectionAlgorithm"]

_CONTEXT = "ResectionAlgorithm"


def _tr(text: str) -> str:
    """Module-level translation, for the helpers outside the class."""
    return QCoreApplication.translate(_CONTEXT, text)


REDUCTIONS = "REDUCTIONS"
STATION = "STATION"
KNOWN = "KNOWN"
APPROX_EASTING = "APPROX_EASTING"
APPROX_NORTHING = "APPROX_NORTHING"
OUTPUT_POSITION = "OUTPUT_POSITION"
OUTPUT_HTML = "OUTPUT_HTML"
EASTING = "EASTING"
NORTHING = "NORTHING"
SIGMA_EASTING = "SIGMA_EASTING"
SIGMA_NORTHING = "SIGMA_NORTHING"
ORIENTATION = "ORIENTATION"


class ResectionAlgorithm(GeoCompAlgorithm):
    """Coordinates of the occupied station from directions to known points."""

    TR_CONTEXT = "ResectionAlgorithm"

    def displayName(self) -> str:
        return self.tr("Resection")

    def shortDescription(self) -> str:
        return self.tr(
            "Fix the occupied station from directions to three or more known points."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes the coordinates of the occupied station from the directions it "
            "observed to known points, by least squares over any number of them with the "
            "setup's orientation estimated as a third unknown. Three points give a unique "
            "solution; more give residuals and a covariance.</p>"
            "<p><b>The danger circle is detected and refused, not solved.</b> When the "
            "occupied station lies on the circle through three known points, every point on "
            "that circle sees the three in the same directions, so they do not determine a "
            "position there. A number returned from that configuration looks exactly like a "
            "coordinate and is not one, so GeoComp refuses and names the three points "
            "involved. Add a fourth point off the circle, or a distance.</p>"
            "<p>Three known points in a straight line define no circle at all, which is a "
            "different impossibility and gets its own message.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced observations</b> &mdash; the document Generalised pre-processing "
            "produced. <b>Occupied station</b> &mdash; which setup in it to resect.</p>"
            "<p><b>Known points</b> &mdash; a JSON object mapping each known station to "
            "<code>[easting, northing]</code> in metres. Only the points the setup actually "
            "sighted are used.</p>"
            "<p><b>Approximate easting</b> and <b>northing</b> (m) &mdash; a starting point "
            "for the iteration, and what the danger-circle check is evaluated at before any "
            "computation begins. Leave both at 0 to start from the centroid of the known "
            "points, which converges from anywhere inside the figure.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Position</b> &mdash; a JSON document in the same shape Classical network "
            "takes as approximate coordinates. <b>Report</b> &mdash; HTML. Scalars: "
            "<code>EASTING</code>, <code>NORTHING</code>, <code>SIGMA_EASTING</code>, "
            "<code>SIGMA_NORTHING</code> in metres and <code>ORIENTATION</code> in "
            "degrees.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REDUCTIONS, self.tr("Reduced observations"), extension="json"
            )
        )
        self.addParameter(QgsProcessingParameterString(STATION, self.tr("Occupied station")))
        self.addParameter(
            QgsProcessingParameterFile(KNOWN, self.tr("Known points"), extension="json")
        )
        for name, label in (
            (APPROX_EASTING, self.tr("Approximate easting (m)")),
            (APPROX_NORTHING, self.tr("Approximate northing (m)")),
        ):
            self.addAdvancedParameter(
                QgsProcessingParameterNumber(
                    name, label, type=QgsProcessingParameterNumber.Type.Double, defaultValue=0.0
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
        results = read_reductions(self.parameterAsFile(parameters, REDUCTIONS, context))
        station = self.parameterAsString(parameters, STATION, context).strip()
        setup = next((r for r in results if r.station == station), None)
        if setup is None:
            raise QgsProcessingException(
                self.tr("The reduced observations contain no setup at station '%1'.").replace(
                    "%1", station
                )
            )

        known = _known_points(self.parameterAsFile(parameters, KNOWN, context))
        directions = {
            pointing.target: pointing.reduction.horizontal
            for pointing in setup.usable
            if pointing.target in known
        }
        if len(directions) < 3:
            raise QgsProcessingException(
                self.tr(
                    "Station '%1' sighted only %2 of the known points. A resection needs at "
                    "least three: two directions cannot fix a position and an orientation."
                )
                .replace("%1", station)
                .replace("%2", str(len(directions)))
            )
        feedback.pushInfo(
            self.tr("Resecting station '%1' from %2 known point(s).")
            .replace("%1", station)
            .replace("%2", str(len(directions)))
        )

        approximate = (
            self.parameterAsDouble(parameters, APPROX_EASTING, context),
            self.parameterAsDouble(parameters, APPROX_NORTHING, context),
        )
        feedback.setProgress(40)
        try:
            result = resection(
                {name: known[name] for name in directions},
                directions,
                approximate=None if approximate == (0.0, 0.0) else approximate,
            )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        easting, northing = result.position
        feedback.setProgress(80)
        feedback.pushInfo(
            self.tr("E %1 ± %2 mm, N %3 ± %4 mm.")
            .replace("%1", format_number(easting.value))
            .replace("%2", format_number(easting.std_dev * 1000.0, 1))
            .replace("%3", format_number(northing.value))
            .replace("%4", format_number(northing.std_dev * 1000.0, 1))
        )

        outputs = self._write(parameters, context, station, result)
        feedback.setProgress(100)
        return {
            EASTING: easting.value,
            NORTHING: northing.value,
            SIGMA_EASTING: easting.std_dev,
            SIGMA_NORTHING: northing.std_dev,
            ORIENTATION: math.degrees(result.orientation.value),
            **outputs,
        }

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, station, result) -> dict[str, Any]:
        easting, northing = result.position
        position = self.parameterAsFileOutput(parameters, OUTPUT_POSITION, context)
        if position:
            with open(position, "w", encoding="utf-8") as handle:
                json.dump(
                    {station: [easting.value, northing.value, 0.0]},
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(station, result))

        return {OUTPUT_POSITION: position, OUTPUT_HTML: html_target}

    def _render(self, station, result) -> str:
        easting, northing = result.position
        correlation = result.covariance.to_correlation()
        summary = [
            [escape(self.tr("Station")), escape(station)],
            [escape(self.tr("Easting (m)")), format_number(easting.value)],
            [escape(self.tr("Northing (m)")), format_number(northing.value)],
            [escape(self.tr("Std dev E (mm)")), format_number(easting.std_dev * 1000.0, 2)],
            [escape(self.tr("Std dev N (mm)")), format_number(northing.std_dev * 1000.0, 2)],
            [escape(self.tr("Correlation")), format_number(correlation[0, 1], 3)],
            [
                escape(self.tr("Setup orientation (°)")),
                format_number(math.degrees(result.orientation.value), 6),
            ],
        ]

        body = [
            f"<h2>{escape(self.tr('Resection'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary),
            f"<h2>{escape(self.tr('Residuals'))}</h2>",
            render_table(
                [escape(self.tr("Known point")), escape(self.tr('Residual (")'))],
                [
                    [escape(point), format_number(math.degrees(value) * 3600.0, 2)]
                    for point, value in sorted(result.residuals.items())
                ],
            ),
        ]
        if len(result.residuals) == 3:
            body.append(
                render_note(
                    self.tr(
                        "Three known points give a unique solution, so the residuals are "
                        "zero by construction and say nothing about the quality of the "
                        "observations. A fourth point is what makes them informative."
                    )
                )
            )

        return render_document(
            self.tr("Resection report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_resection")),
        )


def _known_points(path: str) -> dict[str, tuple[Quantity, Quantity]]:
    """Read known coordinates, held exactly: they are the datum."""
    payload = load_json(path, parameter=KNOWN)
    points: dict[str, tuple[Quantity, Quantity]] = {}
    for name, values in payload.items():
        try:
            easting, northing = (float(v) for v in list(values)[:2])
        except (TypeError, ValueError) as exc:
            raise QgsProcessingException(
                _tr("Known point '%1' is not a pair of numbers.").replace("%1", str(name))
            ) from exc
        points[str(name)] = (
            Quantity.exact(easting, Unit.METRE),
            Quantity.exact(northing, Unit.METRE),
        )
    if not points:
        raise QgsProcessingException(_tr("The known points document is empty."))
    return points
