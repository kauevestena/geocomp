# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:totalstation_radiation`` -- 3D radiation (FR-411).

``specs/09-module-total-station.md`` section 4.6.

Three-dimensional coordinates of a point from one setup: the reduced direction,
the zenith angle, the slope distance, the two heights and the setup's
orientation.

**The full 3x3 covariance is the result, not an extra.** The three coordinates
come from one pointing and are strongly correlated through it; treating them as
independent is wrong. This is the routine production case -- a detail survey
radiates hundreds of points from one setup -- so getting it right matters more
here than anywhere else in the module.

**The orientation is derived from the pointings themselves** wherever the setup
sighted a station whose coordinates are known, which is how a surveyor orients
one: sight a known point, and everything else follows.
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
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.reporting import (
    escape,
    exact,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.algorithms.totalstation.common import load_json, read_reductions
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.total_station import radiate
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit, circular_mean

__all__ = ["RadiationAlgorithm"]

_CONTEXT = "RadiationAlgorithm"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


REDUCTIONS = "REDUCTIONS"
STATIONS = "STATIONS"
ORIENTATIONS = "ORIENTATIONS"
INSTRUMENT_HEIGHT = "INSTRUMENT_HEIGHT"
TARGET_HEIGHT = "TARGET_HEIGHT"
CORRELATION = "CORRELATION"
OUTPUT_POINTS = "OUTPUT_POINTS"
OUTPUT_HTML = "OUTPUT_HTML"
OUTPUT_CSV = "OUTPUT_CSV"
POINT_COUNT = "POINT_COUNT"
WORST_UNCERTAINTY = "WORST_UNCERTAINTY"


class RadiationAlgorithm(GeoCompAlgorithm):
    """Three-dimensional coordinates of detail points from one setup."""

    TR_CONTEXT = "RadiationAlgorithm"

    def displayName(self) -> str:
        return self.tr("3D radiation")

    def shortDescription(self) -> str:
        return self.tr(
            "Compute 3D coordinates of every point radiated from a known, oriented setup."
        )

    def help_body(self) -> str:
        return self.tr(
            "<p>Computes three-dimensional coordinates for every point a setup sighted, from "
            "the reduced direction, the zenith angle, the slope distance, the two heights "
            "and the setup's orientation. Batch radiation of many detail points from one "
            "setup is the routine production case and is what this is built for.</p>"
            "<p><b>The full 3&times;3 covariance is the result, not an extra.</b> The three "
            "coordinates come from one pointing and are strongly correlated through it, and "
            "treating them as independent is wrong. The CSV carries the covariance so "
            "nothing downstream has to assume otherwise.</p>"
            "<p><b>The orientation is derived from the pointings wherever it can be.</b> "
            "Any target whose coordinates are known gives the setup's orientation directly, "
            "which is how a surveyor orients one: sight a known point and everything else "
            "follows. Where several are known the orientations they imply are averaged "
            "circularly and their spread is reported &mdash; a large spread means one of the "
            "known points is not where it is supposed to be. Where none is known the "
            "orientation must be given explicitly.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Reduced observations</b> &mdash; the document Generalised pre-processing "
            "produced. <b>Known stations</b> &mdash; a JSON object mapping station names to "
            "<code>[easting, northing, up]</code> in metres. A setup must appear here for "
            "its points to be radiated.</p>"
            "<p><b>Orientations</b> &mdash; an optional JSON object mapping a setup to its "
            "orientation in degrees, for setups that sighted no known point.</p>"
            "<p><b>Instrument height</b> and <b>target height</b> (m) &mdash; used where the "
            "readings carry none of their own.</p>"
            "<p><b>Distance/zenith correlation</b> &mdash; between -1 and 1, or -2 for "
            "unknown, which is recorded as an assumption rather than silently treated as "
            "zero.</p>"
            "<h3>Outputs</h3>"
            "<p><b>Points</b> &mdash; JSON, in the shape Classical network takes as "
            "approximate coordinates. <b>Report</b> &mdash; HTML. <b>Points table</b> &mdash; "
            "CSV with the full covariance. Scalars: <code>POINT_COUNT</code> and "
            "<code>WORST_UNCERTAINTY</code> in metres.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                REDUCTIONS, self.tr("Reduced observations"), extension="json"
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(STATIONS, self.tr("Known stations"), extension="json")
        )
        self.addParameter(
            QgsProcessingParameterFile(
                ORIENTATIONS, self.tr("Orientations"), extension="json", optional=True
            )
        )
        for name, label, default in (
            (INSTRUMENT_HEIGHT, self.tr("Instrument height (m)"), 1.500),
            (TARGET_HEIGHT, self.tr("Target height (m)"), 1.500),
        ):
            self.addParameter(
                QgsProcessingParameterNumber(
                    name,
                    label,
                    type=QgsProcessingParameterNumber.Type.Double,
                    defaultValue=default,
                    minValue=0.0,
                    maxValue=100.0,
                )
            )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CORRELATION,
                self.tr("Distance/zenith correlation (-2 = unknown)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=-2.0,
                minValue=-2.0,
                maxValue=1.0,
            )
        )
        for name, label, filter_text, by_default in (
            (OUTPUT_POINTS, self.tr("Points"), self.tr("GeoComp coordinates (*.json)"), True),
            (OUTPUT_HTML, self.tr("Report"), self.tr("HTML files (*.html)"), True),
            (OUTPUT_CSV, self.tr("Points table"), self.tr("CSV files (*.csv)"), False),
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
        stations = _known_stations(self.parameterAsFile(parameters, STATIONS, context))
        given = _orientations(self.parameterAsFile(parameters, ORIENTATIONS, context))

        correlation = self.parameterAsDouble(parameters, CORRELATION, context)
        instrument_height = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, INSTRUMENT_HEIGHT, context), 0.001, Unit.METRE
        )
        target_height = Quantity.from_std_dev(
            self.parameterAsDouble(parameters, TARGET_HEIGHT, context), 0.001, Unit.METRE
        )

        rows: list[dict[str, Any]] = []
        orientation_rows: list[list[str]] = []

        for index, result in enumerate(results, start=1):
            if result.station not in stations:
                feedback.pushInfo(
                    self.tr(
                        "Station '%1' has no known coordinates; its points were skipped."
                    ).replace("%1", result.station)
                )
                continue

            orientation, spread, source = self._orientation(result, stations, given, feedback)
            if orientation is None:
                feedback.pushWarning(
                    self.tr(
                        "Station '%1' sighted no known point and has no orientation given; "
                        "its points were skipped."
                    ).replace("%1", result.station)
                )
                continue
            orientation_rows.append(
                [
                    escape(result.station),
                    format_number(math.degrees(orientation), 6),
                    format_number(
                        math.degrees(spread) * 3600.0 if spread is not None else None, 1
                    ),
                    escape(source),
                ]
            )

            origin = stations[result.station]
            for pointing in result.usable:
                if pointing.reduction.distance is None or pointing.target in stations:
                    continue
                try:
                    outcome = radiate(
                        pointing.target,
                        origin,
                        Quantity.exact(orientation, Unit.RADIAN),
                        pointing.reduction.horizontal,
                        pointing.reduction.zenith,
                        pointing.reduction.distance,
                        instrument_height,
                        target_height,
                        correlation=None if correlation < -1.0 else correlation,
                    )
                except GeoCompError as exc:
                    from geocomp.services.messages import message_for

                    raise QgsProcessingException(message_for(exc)) from exc
                rows.append({"station": result.station, "result": outcome})

            feedback.setProgress(70.0 * index / max(len(results), 1))

        if not rows:
            raise QgsProcessingException(
                self.tr(
                    "No point could be radiated. A setup needs known coordinates, an "
                    "orientation, and at least one pointing with a distance to a station "
                    "that is not itself known."
                )
            )

        feedback.pushInfo(
            self.tr("%1 point(s) radiated from %2 setup(s).")
            .replace("%1", str(len(rows)))
            .replace("%2", str(len(orientation_rows)))
        )

        feedback.setProgress(85)
        outputs = self._write(parameters, context, rows, orientation_rows)
        feedback.setProgress(100)

        return {
            POINT_COUNT: len(rows),
            WORST_UNCERTAINTY: max(
                max(q.std_dev for q in row["result"].position) for row in rows
            ),
            **outputs,
        }

    # -- orientation -----------------------------------------------------

    def _orientation(self, result, stations, given, feedback):
        """The setup's orientation, from known points where possible.

        Returns the orientation, the spread of the estimates that produced it,
        and where it came from. The spread is what tells a user that one of the
        known points is not where it is supposed to be: several known points
        should imply the same orientation to within the pointing precision.

        The spread is the **range** of the estimates about their mean, so with
        two known points it is the whole disagreement between them. Taking the
        range of their *absolute* deviations instead would report zero for
        every pair, since two estimates always sit symmetrically about their
        own mean -- and a pair is the commonest case in a detail survey.

        ``None`` for the spread means there is none to report: one known point,
        or an orientation that was given rather than derived. That is a
        different thing from zero, which means the estimates agreed, and the
        report renders the two differently.
        """
        origin = stations[result.station]
        estimates = []
        sigmas = []
        for pointing in result.usable:
            target = stations.get(pointing.target)
            if target is None:
                continue
            azimuth = math.atan2(
                target[0].value - origin[0].value, target[1].value - origin[1].value
            )
            estimates.append(azimuth - pointing.reduction.horizontal.value)
            sigmas.append(pointing.reduction.horizontal.std_dev)

        if estimates:
            orientation = circular_mean(estimates)
            spread = None
            if len(estimates) > 1:
                from geocomp.core.units import angular_difference

                deviations = [angular_difference(e, orientation) for e in estimates]
                spread = max(deviations) - min(deviations)
                self._warn_if_control_disagrees(result.station, spread, sigmas, feedback)
            return orientation, spread, self.tr("from known points")

        if result.station in given:
            return given[result.station], None, self.tr("given")
        return None, None, ""

    def _warn_if_control_disagrees(self, station, spread, sigmas, feedback):
        """Two known points that imply different orientations disagree about
        where they are, and radiating off either one propagates that.

        The threshold is three times the precision of the two pointings taken
        together, so it scales with the instrument rather than being a fixed
        number of arcseconds that is generous for a one-second instrument and
        punitive for a hand-held one.
        """
        allowed = 3.0 * math.hypot(max(sigmas), min(sigmas))
        if allowed <= 0.0 or abs(spread) <= allowed:
            return
        feedback.pushWarning(
            self.tr(
                "The known points sighted from '%1' imply orientations spread over %2 "
                "arcsec, against %3 expected from the pointing precision. One of them is "
                "probably not where it is recorded, and every point radiated from this "
                "setup carries that error."
            )
            .replace("%1", station)
            .replace("%2", format_number(math.degrees(abs(spread)) * 3600.0, 1))
            .replace("%3", format_number(math.degrees(allowed) * 3600.0, 1))
        )

    # -- outputs ---------------------------------------------------------

    def _write(self, parameters, context, rows, orientation_rows) -> dict[str, Any]:
        points = self.parameterAsFileOutput(parameters, OUTPUT_POINTS, context)
        if points:
            with open(points, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        row["result"].target: [q.value for q in row["result"].position]
                        for row in rows
                    },
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

        html_target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_target:
            with open(html_target, "w", encoding="utf-8") as handle:
                handle.write(self._render(rows, orientation_rows))

        csv_target = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_target:
            with open(csv_target, "w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "point",
                        "from",
                        "easting",
                        "northing",
                        "up",
                        "sigma_e",
                        "sigma_n",
                        "sigma_u",
                        "cov_en",
                        "cov_eu",
                        "cov_nu",
                    ]
                )
                for row in rows:
                    outcome = row["result"]
                    matrix = outcome.covariance.matrix
                    writer.writerow(
                        [outcome.target, row["station"]]
                        + [exact(q.value) for q in outcome.position]
                        + [exact(q.std_dev) for q in outcome.position]
                        + [exact(matrix[0, 1]), exact(matrix[0, 2]), exact(matrix[1, 2])]
                    )

        return {OUTPUT_POINTS: points, OUTPUT_HTML: html_target, OUTPUT_CSV: csv_target}

    def _render(self, rows, orientation_rows) -> str:
        body = [
            f"<h2>{escape(self.tr('Setup orientations'))}</h2>",
            render_table(
                [
                    escape(self.tr("Station")),
                    escape(self.tr("Orientation (°)")),
                    escape(self.tr('Spread (")')),
                    escape(self.tr("Source")),
                ],
                orientation_rows,
            ),
            render_note(
                self.tr(
                    "Where a setup sighted several known points they should all imply the "
                    "same orientation. A large spread means one of them is not where it is "
                    "supposed to be."
                )
            ),
            f"<h2>{escape(self.tr('Radiated points'))}</h2>",
            render_table(
                [
                    escape(self.tr("Point")),
                    escape(self.tr("From")),
                    escape(self.tr("Easting (m)")),
                    escape(self.tr("Northing (m)")),
                    escape(self.tr("Up (m)")),
                    escape(self.tr("Std dev E (mm)")),
                    escape(self.tr("Std dev N (mm)")),
                    escape(self.tr("Std dev U (mm)")),
                    escape(self.tr("Correlation E,N")),
                ],
                [
                    [
                        escape(row["result"].target),
                        escape(row["station"]),
                        format_number(row["result"].position[0].value),
                        format_number(row["result"].position[1].value),
                        format_number(row["result"].position[2].value),
                        format_number(row["result"].position[0].std_dev * 1000.0, 2),
                        format_number(row["result"].position[1].std_dev * 1000.0, 2),
                        format_number(row["result"].position[2].std_dev * 1000.0, 2),
                        format_number(row["result"].covariance.to_correlation()[0, 1], 3),
                    ]
                    for row in rows
                ],
            ),
            render_note(
                self.tr(
                    "The three coordinates of a radiated point come from one pointing and "
                    "are correlated through it. The CSV carries the full covariance so "
                    "nothing downstream has to assume they are independent."
                )
            ),
        ]

        return render_document(
            self.tr("3D radiation report"),
            body,
            footer=escape(self.tr("Generated by GeoComp — geocomp:totalstation_radiation")),
        )


def _known_stations(path: str) -> dict[str, tuple[Quantity, Quantity, Quantity]]:
    payload = load_json(path, parameter=STATIONS)
    stations: dict[str, tuple[Quantity, Quantity, Quantity]] = {}
    for name, values in payload.items():
        try:
            easting, northing, up = (float(v) for v in list(values)[:3])
        except (TypeError, ValueError) as exc:
            raise QgsProcessingException(
                _tr("Station '%1' is not three numbers.").replace("%1", str(name))
            ) from exc
        stations[str(name)] = (
            Quantity.exact(easting, Unit.METRE),
            Quantity.exact(northing, Unit.METRE),
            Quantity.exact(up, Unit.METRE),
        )
    if not stations:
        raise QgsProcessingException(_tr("The known stations document is empty."))
    return stations


def _orientations(path: str) -> dict[str, float]:
    if not path:
        return {}
    payload = load_json(path, parameter=ORIENTATIONS)
    try:
        return {str(name): math.radians(float(value)) for name, value in payload.items()}
    except (TypeError, ValueError) as exc:
        raise QgsProcessingException(
            _tr("The orientations document must map each station to a number of degrees.")
        ) from exc
