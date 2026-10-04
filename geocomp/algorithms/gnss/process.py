# SPDX-License-Identifier: GPL-2.0-or-later
"""The four GNSS processing modes (FR-600, FR-601, FR-604).

``specs/11-module-gnss.md`` section 1 and section 3. One class per menu leaf:

=========================  ==================================================
Relative → Static          The workhorse: a baseline with its 3x3 covariance
Relative → Kinematic       Post-processed RTK; a trajectory, not a network
Absolute → Static          Static PPP, carrying the FR-604 notice
Absolute → Kinematic       Kinematic PPP, likewise
=========================  ==================================================

They differ by three things and share everything else, so they are one base
class with three class attributes. Writing four near-identical algorithms would
have made the differences hard to see and the shared behaviour easy to diverge.

**The Absolute pair carries FR-604's notice in three places** -- the help text,
a log line at the start of every run, and the algorithm's short description --
because the requirement's words are "state this in the UI rather than silently
producing a degraded result", and a notice only in the help is a notice only for
the user who already suspected something.
"""

from __future__ import annotations

import shutil
import tempfile
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
    QgsProcessingParameterString,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import (
    base_coordinates,
    configured_profile,
    engine_record,
    frame_choices,
    gnss_engine,
    ppp_limitation_notice,
    run_frame,
    session_products,
    timeout_parameter,
    translate_error,
)
from geocomp.algorithms.layer_outputs import POINT_SOURCE_TYPE, write_styled_sink
from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.engines.rtklib import RtklibJob
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder
from geocomp.layers.builders import GNSS_HORIZON_CRS, gnss_trajectory_features

FOLDER = "FOLDER"
BASE_STATION = "BASE_STATION"
FRAME = "FRAME"
ROVER_STATION = "ROVER_STATION"
ELEVATION_MASK = "ELEVATION_MASK"
KEEP_WORK_DIR = "KEEP_WORK_DIR"
TIMEOUT = "TIMEOUT"
OUTPUT_POS = "OUTPUT_POS"
OUTPUT_JSON = "OUTPUT_JSON"
OUTPUT_LAYER = "OUTPUT_LAYER"


#: The shared body's own words. Through ``self.tr`` they were looked up under
#: each mode's context and filed under none of them, so the four modes' common
#: parameters and help never translated (found by P12c's audit).
_CONTEXT = "GeoCompGnssProcess"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


class _GnssProcessAlgorithm(GeoCompAlgorithm):
    """Shared body of the four modes.

    Subclasses set :attr:`profile_name`, :attr:`is_absolute` and the display
    strings. Everything else -- discovery, configuration, the run, the report --
    is identical by construction rather than by discipline.
    """

    #: Which entry of ``engines.rtklib.config.PROFILES`` this mode is.
    profile_name = ""
    #: Whether this is a PPP mode, and so carries the FR-604 notice.
    is_absolute = False

    def help_body(self) -> str:
        body = _tr(
            "<p>Processes a folder of RINEX observations with <code>rnx2rtkp</code>. "
            "Sessions are discovered from the file headers, not their names, and "
            "only sessions that actually overlap in time are processed together.</p>"
            "<p>Processing options come from Global Settings → GNSS unless a "
            "parameter here overrides them: elevation mask, ephemeris source, "
            "atmospheric models and the ambiguity ratio threshold.</p>"
            "<p>Outputs the engine's <code>.pos</code> solution and a JSON summary "
            "of the run's quality indicators: solution status per epoch, the "
            "fraction of epochs with resolved ambiguities, satellite counts and "
            "the ambiguity ratio.</p>"
        )
        if self.is_absolute:
            return ppp_limitation_notice() + body
        return body

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                _tr("Folder of RINEX observations"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        if not self.is_absolute:
            self.addParameter(
                QgsProcessingParameterString(
                    BASE_STATION, _tr("Base station"), optional=True
                )
            )
            # specs/11 §7: a base in the reference-station database is held at
            # its published coordinates, brought into this frame.
            self.addAdvancedParameter(
                QgsProcessingParameterEnum(
                    FRAME,
                    _tr("Frame of the results"),
                    options=frame_choices(),
                    defaultValue=0,
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                ROVER_STATION, _tr("Rover station"), optional=True
            )
        )
        # Default -1 means "use the Global Settings value". A default that
        # duplicated the setting's number here is exactly how 36 settings came
        # to be read by nothing (specs/15 section 2.3).
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ELEVATION_MASK,
                _tr("Elevation mask, degrees (-1 uses Global Settings)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=-1.0,
                minValue=-1.0,
                maxValue=45.0,
            )
        )
        self.addAdvancedParameter(timeout_parameter(TIMEOUT))
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                KEEP_WORK_DIR,
                _tr("Keep the engine's working directory"),
                defaultValue=True,
            )
        )
        for name, label, filter_text in (
            (OUTPUT_POS, _tr("Solution"), _tr("RTKLIB solution (*.pos)")),
            (OUTPUT_JSON, _tr("Quality summary"), _tr("JSON files (*.json)")),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_LAYER,
                _tr("Solution epochs (layer)"),
                type=POINT_SOURCE_TYPE,
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
        import json

        from geocomp.engines.rtklib.baseline import quality_from_solution
        from geocomp.engines.rtklib.trajectory import trajectory_from_solution

        if self.is_absolute:
            # FR-604: at the top of the log, before any result exists to be
            # mistaken for a good one.
            feedback.pushWarning(_tr(
                "Absolute (PPP) processing in RTKLIB is limited and typically "
                "decimetre-level. Prefer Relative processing where a base "
                "station is available."
            ))

        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        rover_name = (self.parameterAsString(parameters, ROVER_STATION, context) or "").strip()
        base_name = (
            (self.parameterAsString(parameters, BASE_STATION, context) or "").strip()
            if not self.is_absolute
            else ""
        )
        mask = self.parameterAsDouble(parameters, ELEVATION_MASK, context)

        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc

        # Both are (file, reason) pairs -- FR-166's rule that a scan reports
        # every file it could not use rather than stopping at the first.
        for path, reason in scan.skipped:
            feedback.pushWarning(
                _tr("Skipped %1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        for path, reason in scan.warnings:
            feedback.pushWarning(
                _tr("%1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        if not scan.sessions:
            raise QgsProcessingException(
                _tr("No RINEX observation sessions were found in %1").replace(
                    "%1", str(folder)
                )
            )
        feedback.setProgress(20)

        by_station = {session.station_id: session for session in scan.sessions}
        rover = self._pick(by_station, rover_name, "rover")
        overrides: dict[str, Any] = {}
        if mask >= 0:
            overrides["elevation_mask"] = mask
        job_kwargs: dict[str, Any] = {}

        if not self.is_absolute:
            groups = overlapping_groups(scan.sessions)
            if not any(len(group) >= 2 for group in groups):
                raise QgsProcessingException(
                    _tr(
                        "Relative processing needs two sessions that observed at the "
                        "same time; the folder's sessions do not overlap."
                    )
                )
            base = self._pick(
                {s.station_id: s for group in groups if len(group) >= 2 for s in group},
                base_name,
                "base",
                exclude=rover.station_id,
            )
            job_kwargs["base"] = base
            feedback.pushInfo(
                _tr("Base %1 → rover %2")
                .replace("%1", base.station_id)
                .replace("%2", rover.station_id)
            )
            held, base_record = base_coordinates(
                base, run_frame(self.parameterAsEnum(parameters, FRAME, context)), feedback
            )
            overrides.update(held)

        configuration = configured_profile(self.profile_name, **overrides)
        # The products the sessions need for their own days -- an orbit when
        # `configuration.ephemeris` asks for precise, navigation when the folder
        # has none -- from the cache, the directory or a service (FR-352). A
        # missing one stops the run here rather than in the engine.
        products = session_products(
            [rover, *([job_kwargs["base"]] if "base" in job_kwargs else [])],
            configuration.ephemeris,
            configuration.navigation_systems,
            feedback,
        )
        feedback.setProgress(35)

        # Beside the solution when there is one; a run whose solution is not
        # saved used to put it in QGIS's own working directory.
        destination = self.parameterAsFileOutput(parameters, OUTPUT_POS, context)
        temporary = None if destination else Path(tempfile.mkdtemp(prefix="geocomp-gnss-"))
        work_dir = (temporary or Path(destination).parent) / (
            f"{self.profile_name}-{rover.station_id}"
        )
        engine = gnss_engine(feedback)
        try:
            result = engine.run(
                RtklibJob(
                    rover=rover,
                    config=configuration,
                    products=products.paths,
                    timeout=self.parameterAsDouble(parameters, TIMEOUT, context),
                    **job_kwargs,
                ),
                work_dir=work_dir,
            )
        except GeoCompError as exc:
            # Kept whatever KEEP_WORK_DIR says: the refusal names it, and the
            # engine's configuration and output are what the user diagnoses
            # from (specs/08 section 9).
            raise QgsProcessingException(translate_error(exc)) from exc
        feedback.setProgress(80)

        quality = quality_from_solution(result.solution, session_id=rover.station_id)
        feedback.pushInfo(
            _tr("%1 epochs, %2% with resolved ambiguities")
            .replace("%1", str(quality.epochs))
            .replace("%2", localised(f"{quality.fixed_fraction * 100:.1f}"))
        )

        outputs: dict[str, Any] = {}
        if destination:
            Path(destination).write_bytes(result.output_file.read_bytes())
            outputs[OUTPUT_POS] = destination
        summary = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if summary:
            Path(summary).write_text(
                json.dumps(
                    {
                        "profile": self.profile_name,
                        "rover": rover.station_id,
                        **({"base": job_kwargs["base"].station_id} if "base" in job_kwargs else {}),
                        # FR-832: where the base was held, in what frame, and
                        # the transformation that put it there.
                        **({"base_coordinates": base_record} if "base" in job_kwargs else {}),
                        "quality": quality.to_dict(),
                        # FR-302: which engine, at which version, and whether
                        # this release was tested against it.
                        "engine": engine_record(engine),
                        # FR-036: the command line, exit code, wall time and
                        # the ends of stdout and stderr, as for every engine.
                        "run": result.run.to_dict(),
                        "configuration": configuration.to_dict(),
                        # FR-134: a GNSS solution is not reproducible without
                        # knowing which orbit produced it (specs/08 section 5).
                        "products": products.provenance(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = summary

        # FR-357's other half: one point per epoch, categorised by solution
        # status. Built for every mode, not only the kinematic pair -- a static
        # run's epochs are its filter converging, which is worth being able to
        # look at, and the alternative is a parameter that exists on two of four
        # near-identical algorithms.
        outputs[OUTPUT_LAYER] = write_styled_sink(
            self,
            parameters,
            context,
            OUTPUT_LAYER,
            style="gnss_trajectory",
            geometry=QgsWkbTypes.Type.Point,
            crs=QgsCoordinateReferenceSystem(GNSS_HORIZON_CRS),
            features=lambda: gnss_trajectory_features(
                trajectory_from_solution(result.solution)
            ),
            layer_name=_tr("GNSS trajectory"),
        )

        # Until P12c-11 this parameter was read by nothing, and the directory
        # was kept whatever it said. A failed run never reaches here.
        if self.parameterAsBoolean(parameters, KEEP_WORK_DIR, context):
            feedback.pushInfo(
                _tr("The engine's working files are in %1.").replace("%1", str(work_dir))
            )
        else:
            shutil.rmtree(temporary or work_dir, ignore_errors=True)
        feedback.setProgress(100)
        return outputs

    def _pick(self, sessions: dict, name: str, role: str, *, exclude: str = ""):
        """Choose a session by name, or the only candidate there is.

        Guessing between two candidates is refused: a mis-assigned base yields a
        baseline that is confidently wrong in the opposite direction, which
        ``specs/11`` section 4 rule 1 names as the thing not to do.
        """
        candidates = {k: v for k, v in sessions.items() if k != exclude}
        if name:
            if name not in candidates:
                raise QgsProcessingException(
                    _tr("No %1 session for station %2; found: %3")
                    .replace("%1", role)
                    .replace("%2", name)
                    .replace("%3", ", ".join(sorted(candidates)) or "none")
                )
            return candidates[name]
        if len(candidates) != 1:
            raise QgsProcessingException(
                _tr("Name the %1 station explicitly; the folder holds: %2")
                .replace("%1", role)
                .replace("%2", ", ".join(sorted(candidates)))
            )
        return next(iter(candidates.values()))


class RelativeStaticAlgorithm(_GnssProcessAlgorithm):
    """Relative → Static: a baseline between two simultaneously observing stations."""

    TR_CONTEXT = "RelativeStaticAlgorithm"
    profile_name = "relative-static"

    def displayName(self) -> str:
        return self.tr("Relative — Static")

    def shortDescription(self) -> str:
        return self.tr("A static baseline between two simultaneously observing stations.")


class RelativeKinematicAlgorithm(_GnssProcessAlgorithm):
    """Relative → Kinematic: post-processed RTK, a trajectory rather than a network."""

    TR_CONTEXT = "RelativeKinematicAlgorithm"
    profile_name = "relative-kinematic"

    def displayName(self) -> str:
        return self.tr("Relative — Kinematic")

    def shortDescription(self) -> str:
        return self.tr("Post-processed kinematic positioning against a base station.")


class AbsoluteStaticAlgorithm(_GnssProcessAlgorithm):
    """Absolute → Static: static PPP, with FR-604's notice."""

    TR_CONTEXT = "AbsoluteStaticAlgorithm"
    profile_name = "absolute-static"
    is_absolute = True

    def displayName(self) -> str:
        return self.tr("Absolute — Static")

    def shortDescription(self) -> str:
        return self.tr("Static PPP. RTKLIB's PPP is limited — see the notice in the help.")


class AbsoluteKinematicAlgorithm(_GnssProcessAlgorithm):
    """Absolute → Kinematic: kinematic PPP, with FR-604's notice."""

    TR_CONTEXT = "AbsoluteKinematicAlgorithm"
    profile_name = "absolute-kinematic"
    is_absolute = True

    def displayName(self) -> str:
        return self.tr("Absolute — Kinematic")

    def shortDescription(self) -> str:
        return self.tr("Kinematic PPP. RTKLIB's PPP is limited — see the notice in the help.")
