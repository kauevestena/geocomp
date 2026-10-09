# SPDX-License-Identifier: GPL-2.0-or-later
"""Turn processed sessions into baseline observations (FR-602, FR-104, FR-357).

``specs/11-module-gnss.md`` section 4. The step that connects the GNSS module to
the adjustment: a folder of ``.pos`` solutions becomes a cluster of
``GNSS_BASELINE`` observations with their covariance intact, ready for either
engine.

**The independent subset is the default** (``gnss.independent_baselines_only``).
*n* simultaneously observing stations give *n(n-1)/2* baselines of which only
*n-1* carry new information; feeding all of them to an adjustment as though they
were independent inflates its redundancy and understates every uncertainty that
follows. Advanced mode may take the full set, and the dependent ones are
**marked rather than discarded** so a report can say which they were.

**The network document** (P9b) is what the Integration menu combines: the
baselines, each at its session's mid-epoch, and each mark's starting position --
the base's from the ``% ref pos`` header, a rover's from its last epoch. It
needs the frame the base coordinates were given in, which a ``.pos`` file does
not state and GeoComp does not assume (FR-105): without it the document is
refused, because a vector with no frame cannot be brought into another.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMatrix,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import (
    INDEPENDENT_BASELINES_ONLY,
    gnss_setting,
    translate_error,
)
from geocomp.algorithms.layer_outputs import LINE_SOURCE_TYPE, write_styled_sink
from geocomp.algorithms.layer_sources import cell_text
from geocomp.core.errors import GeoCompError
from geocomp.core.geodesy.frames import FRAME_NAMES
from geocomp.core.models import CoordinateSystem, Epoch, HeightType, Network, Position, Station
from geocomp.core.techniques.gnss import (
    AntennaOffset,
    closing_loops,
    independent_subset,
    loop_closure,
    reduce_to_marks,
    to_cluster,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.engines.rtklib.baseline import baseline_from_solution, quality_from_solution
from geocomp.engines.rtklib.read_pos import read_pos
from geocomp.io.mapping import parse_number
from geocomp.layers.builders import GNSS_HORIZON_CRS, gnss_baseline_features

FOLDER = "FOLDER"
INDEPENDENT_ONLY = "INDEPENDENT_ONLY"
BASE_HEIGHT = "BASE_HEIGHT"
ROVER_HEIGHT = "ROVER_HEIGHT"
STATION_HEIGHTS = "STATION_HEIGHTS"
HEIGHT_SIGMA = "HEIGHT_SIGMA"
FRAME = "FRAME"
OUTPUT_JSON = "OUTPUT_JSON"
OUTPUT_NETWORK = "OUTPUT_NETWORK"
OUTPUT_LAYER = "OUTPUT_LAYER"

#: A starting position is only a start; this says so in its uncertainty.
_START_SIGMA = 1.0

#: The range *Base antenna height* and *Rover antenna height* accept, which a
#: station's own height is held to as well.
_MAX_HEIGHT = 10.0


class BuildBaselinesAlgorithm(GeoCompAlgorithm):
    """Build adjustment-ready baselines from processed GNSS solutions."""

    TR_CONTEXT = "BuildBaselinesAlgorithm"

    def displayName(self) -> str:
        return self.tr("Build baselines")

    def shortDescription(self) -> str:
        return self.tr("Turn processed sessions into baseline observations with covariance.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Reads every ECEF <code>.pos</code> solution in a folder and builds "
            "the baseline each determined: the vector between the two marks, with "
            "its full 3x3 covariance.</p>"
            "<p><b>Antenna heights are reduced once.</b> The vector the engine "
            "determined is between antenna reference points; the adjustment wants "
            "the vector between the marks. Applying the reduction twice is "
            "detected and refused.</p>"
            "<p><b>Only the independent subset is kept by default.</b> Processing "
            "every pair of n simultaneously observing stations yields n(n-1)/2 "
            "baselines of which only n-1 are independent; using them all inflates "
            "the apparent redundancy of the adjustment. The dependent ones are "
            "marked in the output rather than discarded.</p>"
            "<p>The result is a cluster: the observations share one covariance "
            "matrix and reach DynAdjust as a G or X measurement with it intact.</p>"
            "<p><b>The optional layer draws every baseline that was built</b>, "
            "including the dependent ones when they were not kept, because "
            "seeing which pairs carried no new information is the point of "
            "drawing them at all. The <code>independent</code> column and the "
            "dashed symbol say which is which; the JSON output carries only "
            "what was kept.</p>"
            "<p><b>The network document</b> is what the Integration menu combines "
            "with other techniques: the baselines at their sessions' mid-epochs "
            "and each mark's starting position. It needs <i>Frame of the base "
            "coordinates</i>, which a <code>.pos</code> file does not state and "
            "GeoComp will not assume.</p>"
        ) + self.tr(
            "<p><b>Every loop is closed.</b> Each dependent baseline joins two "
            "stations the independent ones already connect, so it closes a loop "
            "through them: the vectors summed round it should come back to zero. "
            "The log gives each loop's misclosure, and the JSON output its "
            "components and their propagated uncertainty, which assumes the legs "
            "independent and so understates it. A closure needs no published "
            "coordinate: it asks whether the baselines agree with each other. It "
            "cannot see an error common to every baseline at one station, which "
            "enters the loop twice with opposite signs and cancels, so a loop that "
            "closes does not show that its stations are right.</p>"
        ) + self.tr(
            "<p><b>A station has one antenna height.</b> In a network a station is "
            "the base of one baseline and the rover of another, and its mark has to "
            "be put in the same place on both, or every loop through it misses by "
            "the difference. Give each station's height in <i>Antenna height by "
            "station</i>. A station not listed takes the base height where it is "
            "the base and the rover height where it is the rover, and one that "
            "would take both, when they differ, is refused. Once any height is "
            "given, every baseline is reduced, by zero where that is the height, "
            "because a loop of reduced and unreduced baselines cannot be closed.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                self.tr("Folder of .pos solutions"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                BASE_HEIGHT,
                self.tr("Base antenna height above the mark (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=_MAX_HEIGHT,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                ROVER_HEIGHT,
                self.tr("Rover antenna height above the mark (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=_MAX_HEIGHT,
            )
        )
        self.addParameter(
            QgsProcessingParameterMatrix(
                STATION_HEIGHTS,
                self.tr("Antenna height by station"),
                hasFixedNumberRows=False,
                headers=[self.tr("Station"), self.tr("Antenna height above the mark (m)")],
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                HEIGHT_SIGMA,
                self.tr("Uncertainty of each antenna height (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.002,
                minValue=0.0,
                maxValue=1.0,
            )
        )
        # Default None means "use the Global Settings value"; QGIS renders a
        # tri-state only awkwardly, so the setting is read when the user leaves
        # this at its default and the parameter wins when they change it.
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                INDEPENDENT_ONLY,
                self.tr("Keep only the independent subset"),
                defaultValue=bool(gnss_setting(INDEPENDENT_BASELINES_ONLY)),
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                FRAME,
                self.tr("Frame of the base coordinates"),
                options=[self.tr("Not stated"), *FRAME_NAMES],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Baselines"),
                self.tr("JSON files (*.json)"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_NETWORK,
                self.tr("Network"),
                self.tr("GeoComp network (*.json)"),
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_LAYER,
                self.tr("Baselines (layer)"),
                type=LINE_SOURCE_TYPE,
                optional=True,
                createByDefault=False,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        independent_only = self.parameterAsBool(parameters, INDEPENDENT_ONLY, context)
        base_height = self.parameterAsDouble(parameters, BASE_HEIGHT, context)
        rover_height = self.parameterAsDouble(parameters, ROVER_HEIGHT, context)
        listed = self._station_heights(parameters, context)
        sigma = self.parameterAsDouble(parameters, HEIGHT_SIGMA, context)
        # Every baseline or none: a loop of reduced and unreduced legs is refused
        # (specs/11 section 4.1.1), so a zero height, once any height is given,
        # is a reduction by zero rather than none.
        reducing = bool(listed) or bool(base_height) or bool(rover_height)
        frame_index = self.parameterAsEnum(parameters, FRAME, context)
        frame = FRAME_NAMES[frame_index - 1] if frame_index > 0 else ""
        network_path = self.parameterAsFileOutput(parameters, OUTPUT_NETWORK, context)
        if network_path and not frame:
            raise QgsProcessingException(
                self.about_input(
                    FRAME,
                    self.tr(
                        "The network document needs the frame the base coordinates were given "
                        "in. A .pos file does not state it and GeoComp does not assume one: a "
                        "vector with no frame cannot be brought into another's. Choose the frame they "
                        "were given in."
                    ),
                )
            )

        solutions = sorted(folder.glob("*.pos"))
        if not solutions:
            raise QgsProcessingException(
                self.tr("No .pos solutions were found in %1. Choose the folder the GNSS "
                        "processing wrote them to.").replace("%1", str(folder))
            )

        built = []
        heights: dict[str, float] = {}
        floating: list[str] = []
        quality: dict[str, dict[str, Any]] = {}
        sessions: dict[str, _Session] = {}
        for index, path in enumerate(solutions):
            if feedback.isCanceled():
                return {}
            feedback.setProgress(10 + 60 * index // len(solutions))
            try:
                solution = read_pos(path)
                stations = _stations_from(solution, path)
                baseline = baseline_from_solution(
                    solution, base_station=stations[0], rover_station=stations[1]
                )
                if reducing:
                    # A station listed has its own height at either end; one
                    # not listed takes the height of the end it is (P13-19).
                    ends = (
                        listed.get(stations[0], base_height),
                        listed.get(stations[1], rover_height),
                    )
                    baseline = reduce_to_marks(
                        baseline,
                        *(
                            AntennaOffset(
                                up=Quantity.from_std_dev(height, sigma, Unit.METRE),
                                method="vertical",
                            )
                            for height in ends
                        ),
                    )
                # FR-603: the quality is part of the answer, not a diagnostic.
                # The fraction of epochs that fixed travels on the baseline
                # because that is where a reader of the map or of the JSON will
                # be looking -- a baseline reported without it looks the same
                # whether its ambiguities resolved or not.
                summary = quality_from_solution(solution, session_id=baseline.id)
                baseline = replace(
                    baseline,
                    meta={**baseline.meta, "fixed_fraction": summary.fixed_fraction},
                )
                quality[baseline.id] = summary.to_dict()
                sessions[baseline.id] = _session(solution, baseline)
                # The baseline is the last epoch, so its last epoch's status is
                # the baseline's (P13-18). Until then a float one was taken in
                # silence, and specs/22 §5.1 measured one 872 mm wrong whose
                # covariance said 7.6 mm.
                last = solution.last()
                if not last.is_ambiguity_fixed:
                    floating.append(baseline.id)
                    feedback.pushWarning(
                        self.tr(
                            "%1 is taken from an epoch whose ambiguities were not fixed (ambiguity "
                            "ratio %2). A float baseline can be wrong by far more than its covariance "
                            "says: process the session again, over a longer span, or leave it out."
                        )
                        .replace("%1", baseline.id)
                        .replace("%2", f"{last.ratio:.1f}")
                    )
            except GeoCompError as exc:
                # One unreadable solution does not lose the rest (FR-166).
                feedback.pushWarning(
                    self.tr("Skipped %1: %2")
                    .replace("%1", path.name)
                    .replace("%2", translate_error(exc))
                )
                continue
            built.append(baseline)
            if reducing:
                heights.update(zip(stations, ends, strict=True))

        if not built:
            raise QgsProcessingException(
                self.tr("No baseline could be built from the solutions in %1. Check the "
                        "log for why each was refused.").replace(
                    "%1", str(folder)
                )
            )

        self._one_height_each(built, listed, base_height, rover_height)
        unused = sorted(set(listed) - {s for b in built for s in (b.base_station, b.rover_station)})
        if unused:
            feedback.pushWarning(
                self.tr(
                    "No baseline has %1, so the height given for it in %2 was not used. "
                    "Check the name against the stations the solutions name."
                )
                .replace("%1", ", ".join(unused))
                .replace("%2", self.parameterDefinition(STATION_HEIGHTS).description())
            )

        independent, dependent = independent_subset(built)
        feedback.pushInfo(
            self.tr("%1 baseline(s): %2 independent, %3 dependent")
            .replace("%1", str(len(built)))
            .replace("%2", str(len(independent)))
            .replace("%3", str(len(dependent)))
        )
        if dependent and not independent_only:
            feedback.pushWarning(
                self.tr(
                    "Keeping %1 dependent baseline(s). They carry no new information, "
                    "and an adjustment that treats them as independent will report an "
                    "uncertainty smaller than the data supports."
                ).replace("%1", str(len(dependent)))
            )

        closures = self._close_loops(independent, dependent, feedback)

        # The marked copies, not the originals: `independent_subset` returns
        # every baseline with `is_independent` set, and it is those the layer
        # must draw -- an unmarked baseline renders as "not assessed".
        marked = [*independent, *dependent]
        kept = independent if independent_only else marked
        observations, cluster = to_cluster(kept, cluster_id="gnss")
        feedback.setProgress(90)

        outputs: dict[str, Any] = {}
        destination = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if destination:
            Path(destination).write_text(
                json.dumps(
                    {
                        "observations": [o.to_dict() for o in observations],
                        "cluster": cluster.to_dict(),
                        "independent": [b.id for b in independent],
                        "dependent": [b.id for b in dependent],
                        "independent_only": independent_only,
                        "quality": quality,
                        "closures": closures,
                        "float": floating,
                        "antenna_heights": dict(sorted(heights.items())),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = destination

        if network_path:
            network = _network(kept, observations, cluster, sessions, frame)
            Path(network_path).write_text(
                json.dumps(network.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            outputs[OUTPUT_NETWORK] = network_path

        # Every baseline that was built, kept or not (FR-357). The dependent
        # ones are what the layer is most worth looking at for: the style draws
        # them dashed, so a glance says which pairs carried no new information.
        outputs[OUTPUT_LAYER] = write_styled_sink(
            self,
            parameters,
            context,
            OUTPUT_LAYER,
            style="gnss_baselines",
            geometry=QgsWkbTypes.Type.LineString,
            crs=QgsCoordinateReferenceSystem(GNSS_HORIZON_CRS),
            features=lambda: gnss_baseline_features(marked),
            layer_name=self.tr("GNSS baselines"),
        )
        feedback.setProgress(100)
        return outputs

    def _station_heights(self, parameters, context) -> dict[str, float]:
        """Each listed station's antenna height, by the station's name in upper case.

        The names a solution gives its stations are its input files' first four
        characters in upper case (``_stations_from``), so a name is matched in
        upper case too. A row left empty is skipped; anything else that is not a
        station and a height in range is refused, since a height silently not
        applied is a baseline wrong by it.
        """
        matrix = self.parameterAsMatrix(parameters, STATION_HEIGHTS, context)
        cells = [cell_text(cell).strip() for cell in matrix]
        if not any(cells):
            # Left out, Processing gives one null cell rather than none.
            return {}
        if len(cells) % 2:
            raise QgsProcessingException(
                self.about_input(STATION_HEIGHTS, self.tr("Give each row a station and its height."))
            )
        heights: dict[str, float] = {}
        for station, text in zip(cells[::2], cells[1::2], strict=True):
            if not station and not text:
                continue
            try:
                height = parse_number(text, "auto")
            except ValueError:
                height = None
            if not station or height is None or not 0.0 <= height <= _MAX_HEIGHT:
                raise QgsProcessingException(
                    self.about_input(
                        STATION_HEIGHTS,
                        self.tr(
                            "The row %1 is not a station and an antenna height from 0 to %2 m. "
                            "Correct it, or clear the row."
                        )
                        .replace("%1", f"{station} {text}".strip())
                        .replace("%2", f"{_MAX_HEIGHT:g}"),
                    )
                )
            station = station.upper()
            if heights.get(station, height) != height:
                raise QgsProcessingException(
                    self.about_input(
                        STATION_HEIGHTS,
                        self.tr("%1 is given two heights, %2 m and %3 m. Give it one.")
                        .replace("%1", station)
                        .replace("%2", f"{heights[station]:g}")
                        .replace("%3", f"{height:g}"),
                    )
                )
            heights[station] = height
        return heights

    def _one_height_each(self, built, listed, base_height: float, rover_height: float) -> None:
        """Refuse a station the base and rover heights would reduce by two heights.

        A station not listed takes *Base antenna height* where it is the base and
        *Rover antenna height* where it is the rover. When it is both, on two
        baselines, and the two differ, its mark is put in two places, and every
        loop through it misses by the difference -- which reads as a measurement
        error (specs/11 section 4.2).
        """
        both = ({b.base_station for b in built} & {b.rover_station for b in built}) - set(listed)
        if base_height == rover_height or not both:
            return
        station = min(both)
        raise QgsProcessingException(
            self.tr(
                "%1 is the base of %2 and the rover of %3, so it would be reduced by %4 m "
                "on one and %5 m on the other, and every loop through it would miss by the "
                "difference. Give its height in %6."
            )
            .replace("%1", station)
            .replace("%2", next(b.id for b in built if b.base_station == station))
            .replace("%3", next(b.id for b in built if b.rover_station == station))
            .replace("%4", f"{base_height:g}")
            .replace("%5", f"{rover_height:g}")
            .replace("%6", self.parameterDefinition(STATION_HEIGHTS).description())
        )

    def _close_loops(self, independent, dependent, feedback) -> list[dict[str, Any]]:
        """Close the loop each dependent baseline makes, and say how well it closed.

        specs/11 section 4.1.1. Whether a dependent baseline is kept is a
        question for the adjustment; whether it agrees with the others is a
        check, and is made either way.
        """
        closures = []
        for loop, legs in closing_loops(independent, dependent):
            circuit = " → ".join((*loop, loop[0]))
            try:
                closure = loop_closure(legs, loop)
            except GeoCompError as exc:
                feedback.pushWarning(
                    self.tr("Loop %1 could not be closed: %2")
                    .replace("%1", circuit)
                    .replace("%2", translate_error(exc))
                )
                continue
            feedback.pushInfo(
                self.tr("Loop %1 closes to %2 mm over %3 m of baselines (%4 ppm).")
                .replace("%1", circuit)
                .replace("%2", f"{closure.magnitude_m * 1000:.2f}")
                .replace("%3", f"{closure.perimeter_m:.1f}")
                .replace("%4", f"{closure.parts_per_million:.2f}")
            )
            closures.append(closure.to_dict())
        if not closures:
            feedback.pushInfo(
                self.tr(
                    "No loop was closed: a loop needs a baseline between two stations "
                    "the others already join through a third."
                )
            )
        return closures


@dataclass(frozen=True)
class _Session:
    """What a baseline's session says beyond the vector: when, and where its
    two ends started."""

    epoch: Epoch
    base: tuple[float, float, float]
    rover: tuple[float, float, float]


def _session(solution, baseline) -> _Session:
    """The session's mid-epoch, and the base and rover positions it printed.

    The rover's is its antenna's, not its mark's: a start, a metre or two off at
    most, which is what the adjustment linearises about and nothing more.
    """
    start = solution.obs_start or solution.epochs[0].time
    end = solution.obs_end or solution.epochs[-1].time
    middle = start + (end - start) / 2
    if middle.tzinfo is None:
        # GPS time, which is within a minute of UTC: a decimal year to 1e-7.
        middle = middle.replace(tzinfo=UTC)
    return _Session(
        epoch=Epoch.from_datetime(middle),
        base=tuple(float(v) for v in solution.reference_position),
        rover=tuple(float(v) for v in solution.last().position),
    )


def _network(baselines, observations, cluster, sessions, frame: str) -> Network:
    """The network document: every kept baseline at its epoch, every mark with
    its first stated start, all free -- the datum is the combination's to set."""
    epochs = [sessions[b.id].epoch.decimal_year for b in baselines]
    network = Network(id="gnss", crs=frame, epoch=Epoch.from_decimal_year(sum(epochs) / len(epochs)))
    for baseline in baselines:
        session = sessions[baseline.id]
        for station, xyz in ((baseline.base_station, session.base), (baseline.rover_station, session.rover)):
            if station not in network.stations:
                network.add_station(Station(id=station, approx_position=_start(xyz, frame, session.epoch)))
    for baseline, observation in zip(baselines, observations, strict=True):
        network.add_observation(replace(observation, epoch=sessions[baseline.id].epoch))
    network.add_cluster(cluster)
    return network


def _start(xyz, frame: str, epoch: Epoch) -> Position:
    return Position(
        values=tuple(Quantity.from_std_dev(v, _START_SIGMA, Unit.METRE) for v in xyz),
        system=CoordinateSystem.CARTESIAN,
        crs=frame,
        epoch=epoch,
        height_type=HeightType.ELLIPSOIDAL,
    )


def _stations_from(solution, path: Path) -> tuple[str, str]:
    """Name the two ends from the solution's own input files.

    ``rnx2rtkp`` writes the rover first and the base second, so the order is the
    file's rather than a guess -- getting it backwards yields the negated
    baseline, which every length check passes and every component check fails.
    """
    inputs = [Path(name).stem[:4].upper() for name in solution.inputs[:2]]
    if len(inputs) == 2 and inputs[0] != inputs[1]:
        return inputs[1], inputs[0]
    stem = path.stem.upper()
    return f"{stem}-BASE", f"{stem}-ROVER"
