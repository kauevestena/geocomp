# SPDX-License-Identifier: GPL-2.0-or-later
"""Process a whole campaign, reporting failures rather than stopping (FR-355).

``specs/11-module-gnss.md`` section 2. The requirement's exact words are
"batch processing with progress monitoring and per-session error reporting
**that does not abort the batch**", and the acceptance criterion is that *a
batch with one broken session completes and reports it*.

The logic lives in :func:`geocomp.core.techniques.gnss.batch.run_batch`, which
is QGIS-free and tested without one; this is the Processing surface over it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import working_directory
from geocomp.algorithms.gnss.common import (
    SessionProducts,
    base_coordinates,
    configuration_help,
    configuration_parameter,
    configured_profile,
    engine_record,
    frame_choices,
    gather_products,
    gnss_engine,
    missing_products_message,
    report_scan,
    run_frame,
    say_joined,
    session_span,
    sessions_by_station,
    timeout_parameter,
    translate_error,
    user_configuration,
)
from geocomp.core.errors import ComputationError, GeoCompError
from geocomp.core.techniques.gnss.batch import run_batch
from geocomp.engines.rtklib import RtklibJob
from geocomp.engines.rtklib.baseline import quality_from_solution
from geocomp.io.gnss_discovery import join_sessions, overlapping_groups, scan_folder

FOLDER = "FOLDER"
BASE_STATION = "BASE_STATION"
FRAME = "FRAME"
PROFILE = "PROFILE"
OUTPUT_DIR = "OUTPUT_DIR"
OUTPUT_JSON = "OUTPUT_JSON"
TIMEOUT = "TIMEOUT"
CONFIGURATION = "CONFIGURATION"

_PROFILES = ("relative-static", "relative-kinematic", "absolute-static", "absolute-kinematic")


class BatchProcessAlgorithm(GeoCompAlgorithm):
    """Process every session in a folder against one base."""

    TR_CONTEXT = "BatchProcessAlgorithm"

    def displayName(self) -> str:
        return self.tr("Batch processing")

    def shortDescription(self) -> str:
        return self.tr("Process every session in a folder; one failure does not stop the rest.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Processes every rover session in a folder against one base "
            "station, with the same configuration.</p>"
            "<p><b>A session that fails does not stop the batch.</b> Each is "
            "attempted, each failure is reported with the reason, and the summary "
            "lists what succeeded, what failed and what ran but produced no "
            "usable solution. A campaign of fifty sessions with one truncated "
            "file finishes and tells you which one it was.</p>"
            "<p>Cancelling stops the batch promptly: the remaining sessions are "
            "not attempted, and what has already run is kept.</p>"
            "<p><b>Products are checked before the batch starts.</b> The orbits "
            "and navigation every session needs are resolved first -- from the "
            "cache, the product directory or a download service -- and a batch "
            "that lacks any is refused, naming each session and product, before "
            "a long run begins. A download that fails is reported against its "
            "session, and the batch continues.</p>"
        ) + configuration_help()

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                self.tr("Folder of RINEX observations"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(BASE_STATION, self.tr("Base station"), optional=True)
        )
        # specs/11 §7: a base in the reference-station database is held at its
        # published coordinates, brought into this frame. Relative modes only.
        self.addAdvancedParameter(
            QgsProcessingParameterEnum(
                FRAME,
                self.tr("Frame of the results (relative modes)"),
                options=frame_choices(),
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                PROFILE,
                self.tr("Processing mode"),
                options=[
                    self.tr("Relative — Static"),
                    self.tr("Relative — Kinematic"),
                    self.tr("Absolute — Static"),
                    self.tr("Absolute — Kinematic"),
                ],
                defaultValue=0,
            )
        )
        self.addAdvancedParameter(configuration_parameter(CONFIGURATION))
        self.addAdvancedParameter(timeout_parameter(TIMEOUT))
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Batch report"),
                self.tr("JSON files (*.json)"),
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
        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        base_name = (self.parameterAsString(parameters, BASE_STATION, context) or "").strip()
        profile_name = _PROFILES[self.parameterAsEnum(parameters, PROFILE, context)]
        is_absolute = profile_name.startswith("absolute")
        user = user_configuration(self, parameters, CONFIGURATION, context)

        if is_absolute:
            feedback.pushWarning(self.tr(
                "Absolute (PPP) processing in RTKLIB is limited and typically "
                "decimetre-level. Prefer Relative processing where a base "
                "station is available."
            ))

        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        report_scan(feedback, scan)
        if not scan.sessions:
            raise QgsProcessingException(
                self.tr("No RINEX observation sessions were found in %1. Choose the "
                        "folder that holds the observation files.").replace(
                    "%1", str(folder)
                )
            )

        by_station = sessions_by_station(scan.sessions)
        base = None
        if not is_absolute:
            overlapping = {
                s.station_id
                for group in overlapping_groups(scan.sessions)
                if len(group) >= 2
                for s in group
            }
            if base_name:
                if base_name not in by_station:
                    raise QgsProcessingException(
                        self.tr("No session for base station %1. Check the base station's "
                                "name against the folder's sessions.").replace("%1", base_name)
                    )
                base = by_station[base_name][0]
            elif len(overlapping) == 2:
                base = by_station[sorted(overlapping)[0]][0]
            else:
                raise QgsProcessingException(
                    self.tr("Name the base station explicitly; the folder holds: %1").replace(
                        "%1", ", ".join(sorted(by_station))
                    )
                )
            feedback.pushInfo(self.tr("Base: %1").replace("%1", base.station_id))

        # Every session with the same configuration, the user's options included,
        # but for where the base is held: that is each base session's own (below).
        configuration = configured_profile(
            profile_name, user_options=user["options"] if user else None
        )
        rovers = [s for s in scan.sessions if base is None or s.station_id != base.station_id]
        # One row per session, not per station (P13-16): a campaign observes a
        # mark on several days, and keyed by station every row but the last
        # was lost and the last processed in their place.
        keys = {
            id(session): session.station_id
            if len(by_station[session.station_id]) == 1
            else f"{session.station_id} {session_span(session)}"
            for session in rovers
        }
        by_key = {keys[id(session)]: session for session in rovers}
        # Each session against the base session it observed with. The base's
        # first session is no longer every rover's, observed then or not.
        partners: dict[str, Any] = {}
        unreachable: dict[str, GeoCompError] = {}
        joined: dict[tuple[str, ...], Any] = {}
        made: list[Path] = []

        def work_root() -> Path:
            # Made when first needed, so a batch refused before it leaves no folder.
            if not made:
                made.append(working_directory("geocomp-batch-"))
            return made[0]

        if base is not None:
            bases = by_station[base.station_id]
            for key, session in by_key.items():
                overlapping = [candidate for candidate in bases if candidate.overlaps(session)]
                if len(overlapping) == 1:
                    partners[key] = overlapping[0]
                elif not overlapping:
                    unreachable[key] = ComputationError(
                        "gnss_batch_no_base_session",
                        base=base.station_id,
                        session=session_span(session),
                    )
                else:
                    # The base logged this session in several files, as a receiver
                    # logging hourly does (P13-26). Until then the row was refused,
                    # and the user told to join them; they are joined here, once
                    # for every row they serve.
                    files = tuple(sorted(candidate.obs_file for candidate in overlapping))
                    try:
                        if files not in joined:
                            joined[files] = join_sessions(
                                overlapping, work_root() / "joined" / str(len(joined) + 1)
                            )
                            say_joined(feedback, joined[files], session)
                        partners[key] = joined[files]
                    except GeoCompError as exc:
                        unreachable[key] = exc
        # Each base session at its own epoch (P13-23). Until then every row held the
        # base where the first session put it: over a campaign of days, the
        # published velocity times the days between, on every row but the first.
        frame = run_frame(self.parameterAsEnum(parameters, FRAME, context))
        held_at, held_record = self._held(partners, profile_name, user, frame, feedback)

        # specs/08 section 5: availability is checked before the batch starts.
        # Every session's products are resolved now; what nothing can supply is
        # refused for all sessions at once, and a download that failed is held
        # against its session for the batch to report (section 9).
        products: dict[str, SessionProducts] = {}
        lacking: list[str] = []
        for key, session in by_key.items():
            if key in unreachable:
                continue
            try:
                found = gather_products(
                    [session, *([partners[key]] if key in partners else [])],
                    configuration.ephemeris,
                    configuration.navigation_systems,
                    feedback,
                )
            except GeoCompError as exc:
                unreachable[key] = exc
                continue
            products[key] = found
            lacking += [f"{key}: {item}" for item in found.missing()]
        if lacking:
            raise QgsProcessingException(missing_products_message(lacking))

        engine = gnss_engine(feedback)
        timeout = self.parameterAsDouble(parameters, TIMEOUT, context)

        def process(key: str):
            if key in unreachable:
                raise unreachable[key]
            session = by_key[key]
            kwargs = {"base": partners[key]} if key in partners else {}
            partner = id(partners[key]) if key in partners else None
            result = engine.run(
                RtklibJob(
                    rover=session,
                    config=held_at.get(partner, configuration),
                    products=products[key].paths,
                    timeout=timeout,
                    **kwargs,
                ),
                # A name a file system takes: the key's span has a colon and a slash.
                work_dir=work_root() / "".join(c if c.isalnum() else "-" for c in key),
            )
            return {
                "station": session.station_id,
                **({"session": session_span(session)} if key != session.station_id else {}),
                **({"base_coordinates": held_record[partner]} if partner in held_record else {}),
                "quality": quality_from_solution(result.solution, session_id=key).to_dict(),
                "solution": str(result.output_file),
                "products": products[key].provenance(),
                # FR-036: what was run for this session, and what it said.
                "run": result.run.to_dict(),
            }

        def report(fraction: float | None, code: str | None = None) -> None:
            if fraction is not None:
                feedback.setProgress(int(fraction * 100))

        outcome = run_batch(
            list(by_key),
            process,
            token=_Feedback(feedback),
            progress=report,
            # An engine that exits cleanly having fixed nothing has not produced
            # a solution worth the name -- specs/08's lesson, applied per row.
            accept=lambda row: row["quality"]["epochs"] > 0,
        )

        for row in outcome.results:
            if row.ok:
                feedback.pushInfo(
                    self.tr("%1: %2 epochs")
                    .replace("%1", row.key)
                    .replace("%2", str(row.value["quality"]["epochs"] if row.value else 0))
                )
            elif row.error is not None:
                # The template, with the engine's own message where it has one
                # (FR-305).
                feedback.pushWarning(
                    self.tr("%1 failed: %2")
                    .replace("%1", row.key)
                    .replace("%2", translate_error(row.error))
                )
            else:
                # Ran, and refused by `accept` above: no epoch solved. Until
                # P12c-41 this showed the batch's English ``detail``.
                feedback.pushWarning(
                    self.tr(
                        "%1 ran, but no epoch was solved. Check in the log that the base station "
                        "observed over the same time, and that the navigation data covers the session."
                    ).replace("%1", row.key)
                )
        counts = outcome.summary()
        feedback.pushInfo(
            self.tr("%1 succeeded, %2 failed, %3 rejected")
            .replace("%1", str(counts["succeeded"]))
            .replace("%2", str(counts["failed"]))
            .replace("%3", str(counts["rejected"]))
        )

        outputs: dict[str, Any] = {}
        destination = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if destination:
            Path(destination).write_text(
                json.dumps(
                    {
                        "profile": profile_name,
                        **({"base": base.station_id} if base else {}),
                        # FR-302: the engine version every session was run with.
                        "engine": engine_record(engine),
                        # The configuration every session ran with, and the
                        # user's own options in it (FR-070). Where the base was
                        # held is each session's, under its base_coordinates.
                        "configuration": configuration.to_dict(),
                        **({"user_configuration": user} if user else {}),
                        **outcome.to_dict(),
                        "sessions": [r.value for r in outcome.succeeded if r.value],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = destination
        return outputs

    @staticmethod
    def _held(partners, profile_name, user, frame, feedback) -> tuple[dict[int, Any], dict[int, Any]]:
        """The configuration and record for each base session a row runs against.

        Keyed by the session's ``id``, as ``partners`` holds them. A base not in
        the reference-station database is held where its header puts it,
        whatever the epoch, so it is decided once and said once.
        """
        configurations: dict[int, Any] = {}
        records: dict[int, Any] = {}
        unique = {id(session): session for session in partners.values()}
        header_only: tuple[dict[str, Any], dict[str, Any]] | None = None
        for key, session in sorted(unique.items(), key=lambda item: str(item[1].start)):
            if header_only is not None:
                held, record = header_only
            else:
                held, record = base_coordinates(session, frame, feedback)
                if not held:  # no coordinates to give: RTKLIB reads the header
                    header_only = held, record
            configurations[key] = configured_profile(
                profile_name, user_options=user["options"] if user else None, **held
            )
            records[key] = {**record, "session": session_span(session)}
        return configurations, records


class _Feedback:
    """Adapts a Processing feedback to the core's cancellation protocol.

    The core knows nothing about QGIS (NFR-002), so cancellation crosses the
    boundary as a protocol with one method rather than as a QGIS type.
    """

    __slots__ = ("_feedback",)

    def __init__(self, feedback: QgsProcessingFeedback) -> None:
        self._feedback = feedback

    def is_cancelled(self) -> bool:
        return bool(self._feedback.isCanceled())
