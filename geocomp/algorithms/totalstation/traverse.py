# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_traverse`` -- open, closed and connected traverses (FR-406).

``specs/09-module-total-station.md`` section 4.1.

Computes the angular and linear misclosure, compares them against the configured
tolerances, and distributes the misclosure by a classical rule.

**Both adjustment paths are offered and clearly distinguished.** The compass
(Bowditch) and transit rules are what students are taught and what many
specifications still require; they are *not* least squares, they produce no
residuals and no rigorous covariance, and their results are labelled
``APPROXIMATE``. The rigorous path is Classical network, and running the same
traverse both ways is directly pedagogically valuable -- the student sees what
the classical rule approximates.

An **open** traverse has no misclosure, which is not the same as a misclosure of
zero: nothing about it can be checked, and a blunder anywhere in it is
invisible. GeoComp says so rather than reporting a perfect closure.
"""

from __future__ import annotations

import csv
import json
import math
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import findings_table, read_reductions
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.total_station import (
    Leg,
    TraverseAdjustment,
    TraverseKind,
    adjust_traverse,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit, wrap_to_2pi

__all__ = ["TraverseAlgorithm"]

REDUCTIONS = "REDUCTIONS"
ROUTE = "ROUTE"
BACKSIGHT = "BACKSIGHT"
START_EASTING = "START_EASTING"
START_NORTHING = "START_NORTHING"
START_AZIMUTH = "START_AZIMUTH"
KIND = "KIND"
CLOSE_EASTING = "CLOSE_EASTING"
CLOSE_NORTHING = "CLOSE_NORTHING"
CLOSE_AZIMUTH = "CLOSE_AZIMUTH"
METHOD = "METHOD"
ANGULAR_TOLERANCE = "ANGULAR_TOLERANCE"
RELATIVE_LIMIT = "RELATIVE_LIMIT"
OUTPUT_COORDINATES = "OUTPUT_COORDINATES"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
ANGULAR_MISCLOSURE = "ANGULAR_MISCLOSURE"
LINEAR_MISCLOSURE = "LINEAR_MISCLOSURE"
RELATIVE_PRECISION = "RELATIVE_PRECISION"
WITHIN_TOLERANCE = "WITHIN_TOLERANCE"

#: Enum order is stored in saved models, so it is as permanent as an algorithm id.
_KINDS = (TraverseKind.CLOSED, TraverseKind.CONNECTED, TraverseKind.OPEN)
_METHODS = (
    TraverseAdjustment.COMPASS,
    TraverseAdjustment.TRANSIT,
    TraverseAdjustment.NONE,
)


class TraverseAlgorithm(GeoCompAlgorithm):
    """Compute and adjust a traverse from reduced pointings."""

    TR_CONTEXT = "TraverseAlgorithm"

    def displayName(self) -> str:
        return self.tr("Traverse")

    def shortDescription(self) -> str:
        return self.tr(
            "Compute a traverse's misclosures and distribute them by a classical rule."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Walks a traverse through the reduced pointings, computes its angular and "
            "linear misclosure, compares them against the configured tolerances, and "
            "distributes the misclosure by the compass (Bowditch) or transit rule.</p>"
            "<p><b>The classical rules are not least squares.</b> They produce no residuals, "
            "no redundancy numbers and no rigorous covariance, so their coordinates are "
            "labelled approximate and the uncertainties reported are the misclosure spread "
            "over the traverse rather than a propagated variance. For the rigorous path use "
            "Classical network. Running the same data both ways is the point: the student "
            "sees what the classical rule approximates.</p>"
            "<p><b>An open traverse has no misclosure at all</b>, which is different from a "
            "misclosure of zero. Nothing about it can be checked and a blunder anywhere in "
            "it is invisible, so GeoComp reports that rather than a perfect closure.</p>"
            "<p>Whichever rule is used, the result is also a good set of approximate "
            "coordinates for a rigorous network adjustment, which is the other reason to "
            "run it.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced observations</b> &mdash; the document Generalised pre-processing "
            "produced. <b>Route</b> &mdash; the stations in order, comma-separated, for "
            "example <code>1,2,3,4,1</code>. <b>Initial backsight</b> &mdash; the station "
            "the first setup sighted before turning the angle.</p>"
            "<p><b>Start easting</b>, <b>start northing</b> (m) and <b>start azimuth</b> "
            "(degrees) &mdash; the known point and the orientation of the initial "
            "backsight.</p>"
            "<p><b>Kind</b> &mdash; closed (returns to its start), connected (arrives at "
            "another known point) or open. <b>Closing easting</b>, <b>closing northing</b> "
            "and <b>closing azimuth</b> &mdash; for a connected traverse.</p>"
            "<p><b>Distribution</b> &mdash; compass, transit, or none to report the "
            "misclosure without absorbing it, which is what a check measurement is for.</p>"
            "<p><b>Angular tolerance per station</b> (degrees) and <b>required relative "
            "precision</b> (the N in 1:N).</p>"
            "<h3>Outputs</h3>"
            "<p><b>Coordinates</b> &mdash; a JSON document ready to use as the approximate "
            "coordinates for Classical network. <b>Report</b> &mdash; HTML. <b>Stations</b> "
            "&mdash; CSV. Scalars: <code>ANGULAR_MISCLOSURE</code> in degrees, "
            "<code>LINEAR_MISCLOSURE</code> in metres, <code>RELATIVE_PRECISION</code> and "
            "<code>WITHIN_TOLERANCE</code>.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REDUCTIONS, self.tr("Reduced observations"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterString(ROUTE, self.tr("Route (comma-separated stations)"))
        )
        self.addParameter(
            QgsProcessingParameterString(BACKSIGHT, self.tr("Initial backsight station"))
        )
        for name, label, default in (
            (START_EASTING, self.tr("Start easting (m)"), 0.0),
            (START_NORTHING, self.tr("Start northing (m)"), 0.0),
            (START_AZIMUTH, self.tr("Start azimuth (°)"), 0.0),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                KIND,
                self.tr("Kind"),
                options=[self.tr("Closed"), self.tr("Connected"), self.tr("Open")],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                METHOD,
                self.tr("Distribution"),
                options=[
                    self.tr("Compass (Bowditch)"),
                    self.tr("Transit"),
                    self.tr("None — report the misclosure only"),
                ],
                defaultValue=0,
            )
        )
        for name, label in (
            (CLOSE_EASTING, self.tr("Closing easting (m)")),
            (CLOSE_NORTHING, self.tr("Closing northing (m)")),
            (CLOSE_AZIMUTH, self.tr("Closing azimuth (°)")),
        ):
            self.addAdvancedParameter(
                QgsProcessingParameterNumber(
                    name, label, type=QgsProcessingParameterNumber.Type.Double, defaultValue=0.0
                )
            )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ANGULAR_TOLERANCE,
                self.tr("Angular tolerance per station (°)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=30.0 / 3600.0,
                minValue=0.0,
                maxValue=5.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                RELATIVE_LIMIT,
                self.tr("Required relative precision (1:N)"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=5000,
                minValue=100,
                maxValue=1000000,
            )
        )
        for name, label, filter_text, by_default in (
            (
                OUTPUT_COORDINATES,
                self.tr("Coordinates"),
                self.tr("GeoComp coordinates (*.json)"),
                True,
            ),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Stations"), self.tr("CSV files (*.csv)"), False),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=by_default
                )
            )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        results = read_reductions(self.parameterAsFile(parameters, REDUCTIONS, context))
        route = [
            name.strip()
            for name in self.parameterAsString(parameters, ROUTE, context).split(",")
            if name.strip()
        ]
        if len(route) < 2:
            raise QgsProcessingException(
                self.tr("A traverse needs at least two stations in its route.")
            )

        backsight = self.parameterAsString(parameters, BACKSIGHT, context).strip()
        if not backsight:
            raise QgsProcessingException(
                self.tr(
                    "The initial backsight station is required: it is what the start azimuth refers to."
                )
            )

        kind = _KINDS[self.parameterAsEnum(parameters, KIND, context)]
        method = _METHODS[self.parameterAsEnum(parameters, METHOD, context)]

        feedback.setProgress(20)
        legs = self._legs(results, route, backsight)
        feedback.pushInfo(
            self.tr("%1 leg(s) over %2 station(s).")
            .replace("%1", str(len(legs)))
            .replace("%2", str(len(route)))
        )

        start = (
            _metres(self.parameterAsDouble(parameters, START_EASTING, context)),
            _metres(self.parameterAsDouble(parameters, START_NORTHING, context)),
        )
        close_to = None
        if kind is TraverseKind.CONNECTED:
            close_to = (
                _metres(self.parameterAsDouble(parameters, CLOSE_EASTING, context)),
                _metres(self.parameterAsDouble(parameters, CLOSE_NORTHING, context)),
            )
        close_azimuth = self._close_azimuth(
            parameters, context, kind, route, backsight, feedback
        )

        try:
            result = adjust_traverse(
                legs,
                start,
                _radians(self.parameterAsDouble(parameters, START_AZIMUTH, context)),
                kind=kind,
                close_to=close_to,
                close_azimuth=close_azimuth,
                method=method,
                angular_tolerance_per_station=math.radians(
                    self.parameterAsDouble(parameters, ANGULAR_TOLERANCE, context)
                ),
                relative_precision_limit=float(
                    self.parameterAsInt(parameters, RELATIVE_LIMIT, context)
                ),
            )
        except GeoCompError as exc:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(message_for(exc)) from exc

        feedback.setProgress(70)
        self._push_summary(result, feedback)
        outputs = self._write(parameters, context, result)
        feedback.setProgress(100)

        return {
            ANGULAR_MISCLOSURE: (
                math.degrees(result.angular_misclosure)
                if result.angular_misclosure is not None
                else float("nan")
            ),
            LINEAR_MISCLOSURE: (
                result.linear_misclosure
                if result.linear_misclosure is not None
                else float("nan")
            ),
            # A relative precision is absent for two opposite reasons, and one
            # sentinel for both would read as the worst possible closure in the
            # case that is in fact the best. An exact closure has no ratio
            # because the misclosure is zero; an open traverse has none because
            # there is nothing to compare against at all.
            RELATIVE_PRECISION: (
                result.relative_precision
                if result.relative_precision is not None
                else (float("inf") if result.linear_misclosure == 0.0 else float("nan"))
            ),
            WITHIN_TOLERANCE: not result.findings,
            **outputs,
        }

    def _close_azimuth(self, parameters, context, kind, route, backsight, feedback):
        """The azimuth the traverse must arrive on, or ``None`` if there is none.

        Left blank on a loop, this used to fall through to zero, and an
        untouched field then produced an angular misclosure of a few hundred
        degrees that looked like a catastrophic survey. A loop that backsights
        the station it will return from arrives on the very line its start
        azimuth refers to, so that case is inferred instead. Any other blank
        means the closure genuinely cannot be checked, and saying so is better
        than checking it against zero.
        """
        if kind is TraverseKind.OPEN:
            return None
        if parameters.get(CLOSE_AZIMUTH) is not None:
            return _radians(self.parameterAsDouble(parameters, CLOSE_AZIMUTH, context))
        if kind is TraverseKind.CLOSED and backsight == route[-2]:
            feedback.pushInfo(
                self.tr(
                    "No closing azimuth was given. This loop backsights '%1' and returns "
                    "from it, so it closes on the line the start azimuth refers to, and "
                    "that is what the angular misclosure is measured against."
                ).replace("%1", backsight)
            )
            return _radians(self.parameterAsDouble(parameters, START_AZIMUTH, context))
        feedback.pushWarning(
            self.tr(
                "No closing azimuth was given and none can be inferred, so the angular "
                "misclosure is not computed and the angles are not checked. Give the "
                "closing azimuth to check them."
            )
        )
        return None

    # -- inputs ----------------------------------------------------------

    def _legs(self, results, route: list[str], backsight: str) -> list[Leg]:
        """Derive the legs from the reduced pointings along the route.

        At each station the angle is the foresight direction less the backsight
        direction, and the distance is the horizontal one to the foresight. Both
        come from the same setup, so the setup's unknown orientation cancels --
        which is why a traverse can be computed from directions at all.
        """
        by_station = {result.station: result for result in results}
        legs: list[Leg] = []

        for index in range(len(route) - 1):
            occupied = route[index]
            foresight = route[index + 1]
            back = backsight if index == 0 else route[index - 1]

            setup = by_station.get(occupied)
            if setup is None:
                raise QgsProcessingException(
                    self.tr(
                        "The reduced observations contain no setup at station '%1'."
                    ).replace("%1", occupied)
                )
            pointings = {p.target: p for p in setup.usable}
            for needed in (back, foresight):
                if needed not in pointings:
                    raise QgsProcessingException(
                        self.tr("Station '%1' has no usable pointing to '%2'.")
                        .replace("%1", occupied)
                        .replace("%2", needed)
                    )

            angle = pointings[foresight].reduction.horizontal - (
                pointings[back].reduction.horizontal.detached()
            )
            angle = Quantity(
                value=wrap_to_2pi(angle.value),
                variance=angle.variance,
                unit=Unit.RADIAN,
                mode=angle.mode,
                strategies=angle.strategies,
            )

            basic = pointings[foresight].basic
            if basic is None:
                raise QgsProcessingException(
                    self.tr("The pointing from '%1' to '%2' carries no distance.")
                    .replace("%1", occupied)
                    .replace("%2", foresight)
                )
            legs.append(
                Leg(
                    origin=occupied,
                    target=foresight,
                    angle=angle,
                    distance=basic.horizontal_distance.detached(),
                )
            )
        return legs

    # -- feedback --------------------------------------------------------

    def _push_summary(self, result, feedback) -> None:
        feedback.pushInfo(
            self.tr("Perimeter %1 m.").replace("%1", format_number(result.perimeter.value, 3))
        )
        if result.angular_misclosure is not None:
            feedback.pushInfo(
                self.tr("Angular misclosure %1 arcsec.").replace(
                    "%1", format_number(math.degrees(result.angular_misclosure) * 3600.0, 1)
                )
            )
        if result.relative_precision is not None:
            feedback.pushInfo(
                self.tr("Closes to 1:%1.").replace(
                    "%1", format_number(result.relative_precision, 0)
                )
            )
        for finding in result.findings:
            feedback.pushWarning(f"[{finding.code}] {finding.message}")

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, result) -> dict[str, Any]:
        coordinates = self.parameterAsFileOutput(parameters, OUTPUT_COORDINATES, context)
        if coordinates:
            with open(coordinates, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        station: [easting.value, northing.value, 0.0]
                        for station, (easting, northing) in sorted(result.coordinates.items())
                    },
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(result))

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            with open(csv_target, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["station", "easting", "northing", "sigma"])
                for station, (easting, northing) in sorted(result.coordinates.items()):
                    writer.writerow(
                        [
                            station,
                            repr(easting.value),
                            repr(northing.value),
                            repr(easting.std_dev),
                        ]
                    )

        return {
            OUTPUT_COORDINATES: coordinates,
            OUTPUT_HTML: html_target,
            OUTPUT_CSV: csv_target,
        }

    def _render(self, result) -> str:
        summary = [
            [escape(self.tr("Kind")), escape(result.kind.value)],
            [escape(self.tr("Distribution")), escape(result.method.value)],
            [escape(self.tr("Perimeter (m)")), format_number(result.perimeter.value, 3)],
            [
                escape(self.tr('Angular misclosure (")')),
                format_number(math.degrees(result.angular_misclosure) * 3600.0, 1)
                if result.angular_misclosure is not None
                else "—",
            ],
            [
                escape(self.tr("Linear misclosure (m)")),
                format_number(result.linear_misclosure, 4)
                if result.linear_misclosure is not None
                else "—",
            ],
            [
                escape(self.tr("Relative precision")),
                f"1:{format_number(result.relative_precision, 0)}"
                if result.relative_precision is not None
                else "—",
            ],
        ]

        body = [
            f"<h2>{escape(self.tr('Traverse'))}</h2>",
            render_table([escape(self.tr("Property")), escape(self.tr("Value"))], summary),
            render_note(
                self.tr(
                    "A classical distribution is not least squares: it produces no residuals "
                    "and no rigorous covariance, so these coordinates are approximate. For "
                    "the rigorous path, use Classical network on the same data."
                )
            ),
            f"<h2>{escape(self.tr('Stations'))}</h2>",
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("Easting (m)")),
                    escape(self.tr("Northing (m)")),
                ],
                [
                    [
                        escape(station),
                        format_number(easting.value),
                        format_number(northing.value),
                    ]
                    for station, (easting, northing) in sorted(result.coordinates.items())
                ],
            ),
            f"<h2>{escape(self.tr('Findings'))}</h2>",
            findings_table(result.findings),
        ]

        return render_document(
            self.tr("Traverse report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_traverse")),
        )


def _metres(value: float) -> Quantity:
    """A known coordinate, held exactly: it is the datum, not a measurement."""
    return Quantity.exact(value, Unit.METRE)


def _radians(degrees: float) -> Quantity:
    return Quantity.exact(math.radians(degrees), Unit.RADIAN)
