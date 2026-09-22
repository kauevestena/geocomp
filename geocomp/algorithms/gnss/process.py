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

from pathlib import Path
from typing import Any

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsWkbTypes,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import (
    configured_profile,
    ppp_limitation_notice,
    product_files,
    translate_error,
)
from geocomp.algorithms.layer_outputs import POINT_SOURCE_TYPE, write_styled_sink
from geocomp.core.errors import GeoCompError
from geocomp.engines.rtklib import RtklibEngine, RtklibJob
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder
from geocomp.layers.builders import GNSS_HORIZON_CRS, gnss_trajectory_features

FOLDER = "FOLDER"
BASE_STATION = "BASE_STATION"
ROVER_STATION = "ROVER_STATION"
ELEVATION_MASK = "ELEVATION_MASK"
KEEP_WORK_DIR = "KEEP_WORK_DIR"
OUTPUT_POS = "OUTPUT_POS"
OUTPUT_JSON = "OUTPUT_JSON"
OUTPUT_LAYER = "OUTPUT_LAYER"


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
        body = self.tr(
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
                self.tr("Folder of RINEX observations"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        if not self.is_absolute:
            self.addParameter(
                QgsProcessingParameterString(
                    BASE_STATION, self.tr("Base station"), optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                ROVER_STATION, self.tr("Rover station"), optional=True
            )
        )
        # Default -1 means "use the Global Settings value". A default that
        # duplicated the setting's number here is exactly how 36 settings came
        # to be read by nothing (specs/15 section 2.3).
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                ELEVATION_MASK,
                self.tr("Elevation mask, degrees (-1 uses Global Settings)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=-1.0,
                minValue=-1.0,
                maxValue=45.0,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterBoolean(
                KEEP_WORK_DIR,
                self.tr("Keep the engine's working directory"),
                defaultValue=True,
            )
        )
        for name, label, filter_text in (
            (OUTPUT_POS, self.tr("Solution"), self.tr("RTKLIB solution (*.pos)")),
            (OUTPUT_JSON, self.tr("Quality summary"), self.tr("JSON files (*.json)")),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                OUTPUT_LAYER,
                self.tr("Solution epochs (layer)"),
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
            feedback.pushWarning(self.tr(
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
                self.tr("Skipped %1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        for path, reason in scan.warnings:
            feedback.pushWarning(
                self.tr("%1: %2").replace("%1", str(path)).replace("%2", reason)
            )
        if not scan.sessions:
            raise QgsProcessingException(
                self.tr("No RINEX observation sessions were found in %1").replace(
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
                    self.tr(
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
                self.tr("Base %1 → rover %2")
                .replace("%1", base.station_id)
                .replace("%2", rover.station_id)
            )

        configuration = configured_profile(self.profile_name, **overrides)
        # Precise products, where the user configured a directory holding them.
        # `configuration.ephemeris` decides whether they are wanted; this
        # decides whether any are there (FR-358).
        products = product_files() if configuration.ephemeris == "precise" else ()
        if products:
            feedback.pushInfo(
                self.tr("Using %1 precise product file(s)").replace("%1", str(len(products)))
            )
        feedback.setProgress(35)

        work_dir = Path(self.parameterAsFileOutput(parameters, OUTPUT_POS, context) or ".").parent
        try:
            result = RtklibEngine().run(
                RtklibJob(
                    rover=rover, config=configuration, products=products, **job_kwargs
                ),
                work_dir=work_dir / f"{self.profile_name}-{rover.station_id}",
            )
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        feedback.setProgress(80)

        quality = quality_from_solution(result.solution, session_id=rover.station_id)
        feedback.pushInfo(
            self.tr("%1 epochs, %2% with resolved ambiguities")
            .replace("%1", str(quality.epochs))
            .replace("%2", f"{quality.fixed_fraction * 100:.1f}")
        )

        outputs: dict[str, Any] = {}
        destination = self.parameterAsFileOutput(parameters, OUTPUT_POS, context)
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
                        "quality": quality.to_dict(),
                        "configuration": configuration.to_dict(),
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
            layer_name=self.tr("GNSS trajectory"),
        )

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
                    self.tr("No %1 session for station %2; found: %3")
                    .replace("%1", role)
                    .replace("%2", name)
                    .replace("%3", ", ".join(sorted(candidates)) or "none")
                )
            return candidates[name]
        if len(candidates) != 1:
            raise QgsProcessingException(
                self.tr("Name the %1 station explicitly; the folder holds: %2")
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
