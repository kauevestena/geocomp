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
from geocomp.core.errors import GeoCompError
from geocomp.core.geodesy.frames import FRAME_NAMES
from geocomp.core.models import CoordinateSystem, Epoch, HeightType, Network, Position, Station
from geocomp.core.techniques.gnss import (
    AntennaOffset,
    independent_subset,
    reduce_to_marks,
    to_cluster,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.engines.rtklib.baseline import baseline_from_solution, quality_from_solution
from geocomp.engines.rtklib.read_pos import read_pos
from geocomp.layers.builders import GNSS_HORIZON_CRS, gnss_baseline_features

FOLDER = "FOLDER"
INDEPENDENT_ONLY = "INDEPENDENT_ONLY"
BASE_HEIGHT = "BASE_HEIGHT"
ROVER_HEIGHT = "ROVER_HEIGHT"
HEIGHT_SIGMA = "HEIGHT_SIGMA"
FRAME = "FRAME"
OUTPUT_JSON = "OUTPUT_JSON"
OUTPUT_NETWORK = "OUTPUT_NETWORK"
OUTPUT_LAYER = "OUTPUT_LAYER"

#: A starting position is only a start; this says so in its uncertainty.
_START_SIGMA = 1.0


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
                maxValue=10.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                ROVER_HEIGHT,
                self.tr("Rover antenna height above the mark (m)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=10.0,
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
        sigma = self.parameterAsDouble(parameters, HEIGHT_SIGMA, context)
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
                        "vector with no frame cannot be brought into another's."
                    ),
                )
            )

        solutions = sorted(folder.glob("*.pos"))
        if not solutions:
            raise QgsProcessingException(
                self.tr("No .pos solutions were found in %1").replace("%1", str(folder))
            )

        built = []
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
                if base_height or rover_height:
                    baseline = reduce_to_marks(
                        baseline,
                        AntennaOffset(
                            up=Quantity.from_std_dev(base_height, sigma, Unit.METRE),
                            method="vertical",
                        ),
                        AntennaOffset(
                            up=Quantity.from_std_dev(rover_height, sigma, Unit.METRE),
                            method="vertical",
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
            except GeoCompError as exc:
                # One unreadable solution does not lose the rest (FR-166).
                feedback.pushWarning(
                    self.tr("Skipped %1: %2")
                    .replace("%1", path.name)
                    .replace("%2", translate_error(exc))
                )
                continue
            built.append(baseline)

        if not built:
            raise QgsProcessingException(
                self.tr("No baseline could be built from the solutions in %1").replace(
                    "%1", str(folder)
                )
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
