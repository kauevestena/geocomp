# SPDX-License-Identifier: GPL-2.0-or-later
"""Compare one dataset processed several ways (FR-359).

``specs/11-module-gnss.md`` section 6. Runs the same session pair under several
configurations and presents the solutions side by side with the significance of
each difference, given the covariances, and each configuration's quality.

A configuration is either an elevation mask or an RTKLIB options file of the
user's own (FR-070) -- a named profile, shareable as a file. With files given,
each is a configuration, named by the file; without, the masks are swept.

**The elevation-mask sweep is the parameter worth sweeping first**, and this is
not a guess: it is what attributed RD-06's discrepancy (``specs/22`` §5). Below
25 degrees two independent days of the same 76 m baseline disagreed by 11 mm in
east; at 25 and above they agreed to 0.14 mm. A comparison that only printed the
coordinates would have shown twelve numbers and no finding.

**Side by side is the report** (P12c-43). ``specs/15`` listed a custom dialog
for this; what the user needs to see is the result, one column per
configuration, and that is what the HTML report is -- opened by Processing's
results viewer like every other report, from the menu, the toolbox or a model
alike. A dialog that ran the configurations itself would be a second way to
run them (ADR-0005), and one that only collected parameters would add nothing
the Processing dialog lacks.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.defaults import working_directory
from geocomp.algorithms.gnss.common import (
    configured_profile,
    engine_record,
    gnss_engine,
    session_products,
    timeout_parameter,
    translate_error,
)
from geocomp.algorithms.inputs import file_list_type
from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.core.techniques.gnss.comparison import (
    DEFAULT_CONFIDENCE,
    ConfigurationComparison,
    compare_baselines,
)
from geocomp.engines.rtklib import RtklibJob
from geocomp.engines.rtklib.baseline import baseline_from_solution, quality_from_solution
from geocomp.engines.rtklib.config import read_user_options
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder

FOLDER = "FOLDER"
MASKS = "MASKS"
CONFIGURATIONS = "CONFIGURATIONS"
CONFIDENCE = "CONFIDENCE"
OUTPUT_CSV = "OUTPUT_CSV"
OUTPUT_JSON = "OUTPUT_JSON"
OUTPUT_HTML = "OUTPUT_HTML"
TIMEOUT = "TIMEOUT"

#: The sweep that attributed RD-06. Straddles the point where the answer stops
#: depending on which satellites were used.
DEFAULT_MASKS = "10,15,20,25,30,35"

_CONTEXT = "GeoCompGnssComparison"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


class CompareConfigurationsAlgorithm(GeoCompAlgorithm):
    """Process one baseline several ways and compare the results."""

    TR_CONTEXT = "CompareConfigurationsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Compare configurations")

    def shortDescription(self) -> str:
        return self.tr("Process the same data several ways and compare, with significance.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Processes one pair of simultaneously observing sessions several ways, and "
            "compares the baselines they determine, side by side in the report.</p>"
            "<p><b>The configurations</b> are either elevation masks, swept, or RTKLIB "
            "configuration files of your own: give two or more files, and each is a "
            "configuration named by its file, compared at the settings it states over "
            "Global Settings. The first is the reference the others are measured "
            "against.</p>"
            "<p><b>The comparison is by significance, not by size.</b> A 3 mm "
            "difference is large when both solutions are good to 0.5 mm and "
            "nothing at all when they are good to 5 mm, so each difference is "
            "tested against the combined covariance of the two solutions.</p>"
            "<p>The two runs share their observations, so treating them as "
            "independent overstates the difference's uncertainty and "
            "under-reports significance. That is the conservative direction for "
            "a test whose job is to stop a parameter being called important when "
            "it is not, and the assumption is recorded on the result.</p>"
            "<p>A difference reported as <i>not significant</i> is the "
            "informative answer: it says the parameter changed nothing this data "
            "can resolve.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                self.tr("Folder of RINEX observations"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                MASKS, self.tr("Elevation masks to compare (degrees)"), defaultValue=DEFAULT_MASKS
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                CONFIGURATIONS,
                self.tr("RTKLIB configuration files to compare, in place of the masks"),
                layerType=file_list_type(),
                optional=True,
            )
        )
        self.addAdvancedParameter(
            QgsProcessingParameterNumber(
                CONFIDENCE,
                self.tr("Confidence for the significance test"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=DEFAULT_CONFIDENCE,
                minValue=0.5,
                maxValue=0.999,
            )
        )
        self.addAdvancedParameter(timeout_parameter(TIMEOUT))
        for name, label, filter_text in (
            (OUTPUT_HTML, self.tr("Comparison report"), self.tr("HTML files (*.html)")),
            (OUTPUT_CSV, self.tr("Comparison table"), self.tr("CSV files (*.csv)")),
            (OUTPUT_JSON, self.tr("Comparison"), self.tr("JSON files (*.json)")),
        ):
            self.addParameter(
                QgsProcessingParameterFileDestination(
                    name, label, filter_text, optional=True, createByDefault=True
                )
            )

    def _configurations(self, parameters, context) -> list[tuple[str, dict[str, Any]]]:
        """Each configuration's name and what it sets: a file's options, or a mask."""
        # Unset, QGIS answers with one empty entry rather than none.
        files = [path for path in self.parameterAsFileList(parameters, CONFIGURATIONS, context) if path]
        if files:
            if len(files) < 2:
                raise QgsProcessingException(
                    self.about_input(
                        CONFIGURATIONS,
                        self.tr("Give at least two configuration files to compare."),
                    )
                )
            configurations: list[tuple[str, dict[str, Any]]] = []
            for path in files:
                try:
                    options = read_user_options(path)
                except GeoCompError as exc:
                    raise QgsProcessingException(
                        self.about_input(CONFIGURATIONS, translate_error(exc))
                    ) from exc
                name = Path(path).stem
                taken = {existing for existing, _ in configurations}
                if name in taken:
                    name = f"{name} ({len(configurations) + 1})"
                configurations.append((name, {"file": str(path), "user_options": options}))
            return configurations

        raw = self.parameterAsString(parameters, MASKS, context) or DEFAULT_MASKS
        try:
            masks = [float(piece) for piece in raw.replace(";", ",").split(",") if piece.strip()]
        except ValueError as exc:
            raise QgsProcessingException(
                self.tr("Could not read the elevation masks from %1. Give them as numbers "
                        "of degrees separated by commas.").replace("%1", raw)
            ) from exc
        if len(masks) < 2:
            raise QgsProcessingException(
                self.tr("Give at least two elevation masks to compare.")
            )
        return [
            (self.tr("mask %1°").replace("%1", f"{mask:g}"), {"elevation_mask": mask})
            for mask in masks
        ]

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        folder = Path(self.parameterAsFile(parameters, FOLDER, context))
        confidence = self.parameterAsDouble(parameters, CONFIDENCE, context)
        configurations = self._configurations(parameters, context)

        try:
            scan = scan_folder(folder)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
        pair = next((g for g in overlapping_groups(scan.sessions) if len(g) == 2), None)
        if pair is None:
            raise QgsProcessingException(
                self.about_input(
                    FOLDER,
                    self.tr(
                        "Comparison needs exactly one pair of simultaneously observing "
                        "sessions in the folder. Choose a folder that holds two sessions observed at "
                        "the same time."
                    ),
                )
            )
        base, rover = sorted(pair, key=lambda s: s.station_id)
        feedback.pushInfo(
            self.tr("Base %1 → rover %2")
            .replace("%1", base.station_id)
            .replace("%2", rover.station_id)
        )

        # One resolution for every configuration: the comparison varies the
        # processing, and one whose runs used different orbits would be comparing those.
        reference = configured_profile("relative-static", output_format="xyz")
        products = session_products(
            [rover, base], reference.ephemeris, reference.navigation_systems, feedback
        )

        work_root = working_directory("geocomp-compare-")
        engine = gnss_engine(feedback)
        timeout = self.parameterAsDouble(parameters, TIMEOUT, context)
        baselines = {}
        qualities = {}
        masks: dict[str, float] = {}
        runs: dict[str, Any] = {}
        recorded: dict[str, Any] = {}
        for index, (name, settings) in enumerate(configurations):
            if feedback.isCanceled():
                return {}
            feedback.setProgress(10 + 70 * index // len(configurations))
            overrides = (
                {"elevation_mask": settings["elevation_mask"]} if "elevation_mask" in settings else {}
            )
            configuration = configured_profile(
                "relative-static",
                user_options=settings.get("user_options"),
                output_format="xyz",
                **overrides,
            )
            try:
                result = engine.run(
                    RtklibJob(
                        rover=rover,
                        base=base,
                        config=configuration,
                        products=products.paths,
                        timeout=timeout,
                    ),
                    work_dir=work_root / f"configuration-{index + 1}",
                )
                runs[name] = result.run.to_dict()
                baselines[name] = baseline_from_solution(
                    result.solution,
                    base_station=base.station_id,
                    rover_station=rover.station_id,
                )
                qualities[name] = quality_from_solution(result.solution, session_id=rover.station_id)
                masks[name] = configuration.elevation_mask
                recorded[name] = {
                    "elevation_mask": configuration.elevation_mask,
                    **({"file": settings["file"], "options": settings["user_options"]}
                       if "file" in settings else {}),
                }
            except GeoCompError as exc:
                feedback.pushWarning(
                    self.tr("%1 failed: %2")
                    .replace("%1", name)
                    .replace("%2", translate_error(exc))
                )

        if len(baselines) < 2:
            raise QgsProcessingException(
                self.tr("Fewer than two configurations produced a baseline to compare. "
                        "Check the log for why the others produced none.")
            )

        try:
            comparison = compare_baselines(baselines, confidence=confidence)
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc

        for line in comparison_lines(comparison):
            feedback.pushInfo(line)
        feedback.pushInfo(verdict(comparison))

        outputs: dict[str, Any] = {}
        html_path = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if html_path:
            Path(html_path).write_text(
                comparison_report(
                    comparison,
                    baselines,
                    qualities,
                    masks,
                    base=base.station_id,
                    rover=rover.station_id,
                ),
                encoding="utf-8",
            )
            outputs[OUTPUT_HTML] = html_path
        csv_path = self.parameterAsFileOutput(parameters, OUTPUT_CSV, context)
        if csv_path:
            # An export for another program (FR-162): its header is the data's
            # own, the same in every language, as the JSON's keys are.
            Path(csv_path).write_text(
                "\n".join(",".join(row) for row in comparison.table()) + "\n", encoding="utf-8"
            )
            outputs[OUTPUT_CSV] = csv_path
        json_path = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if json_path:
            Path(json_path).write_text(
                json.dumps(
                    {
                        **comparison.to_dict(),
                        # What each configuration set, and how its run went (specs/11 §5).
                        "configurations": recorded,
                        "quality": {name: quality.to_dict() for name, quality in qualities.items()},
                        "products": products.provenance(),
                        # FR-302: the engine version every configuration ran with.
                        "engine": engine_record(engine),
                        # FR-036: each configuration's run, as for every engine.
                        "runs": runs,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            outputs[OUTPUT_JSON] = json_path
        feedback.setProgress(100)
        return outputs


def comparison_lines(comparison: ConfigurationComparison) -> list[str]:
    """One line per configuration, in words: its difference from the reference and whether it matters.

    ``ConfigurationComparison.table()`` is the export's rows, with the data's own
    English header; until P12c-43 the log showed it as it stood.
    """
    lines = []
    for row in comparison.rows:
        lines.append(
            (
                _tr("%1: %2 mm in 3D from %3; test statistic %4, significant.")
                if row.is_significant
                else _tr("%1: %2 mm in 3D from %3; test statistic %4, not significant.")
            )
            .replace("%1", row.name)
            .replace("%2", format_number(row.magnitude * 1000.0, 1))
            .replace("%3", comparison.reference)
            .replace("%4", format_number(row.statistic, 2))
        )
    return lines


def verdict(comparison: ConfigurationComparison) -> str:
    """What the comparison found, in one sentence."""
    confidence = localised(f"{100.0 * comparison.confidence:g}")
    significant = [row.name for row in comparison.rows if row.is_significant]
    if not significant:
        return _tr(
            "No difference is significant at %1% confidence: over this data, the "
            "configurations changed nothing that can be resolved."
        ).replace("%1", confidence)
    return (
        _tr(
            "At %1% confidence, these configurations changed the baseline by more than the "
            "solutions' uncertainties explain: %2."
        )
        .replace("%1", confidence)
        .replace("%2", ", ".join(significant))
    )


def comparison_report(
    comparison: ConfigurationComparison,
    baselines: dict[str, Any],
    qualities: dict[str, Any],
    masks: dict[str, float],
    *,
    base: str,
    rover: str,
) -> str:
    """The configurations side by side, one column each, the reference first (FR-359).

    The differences and their significance from the comparison, each
    configuration's baseline and its quality indicators from its own run
    (``specs/11`` sections 5 and 6).
    """
    names = list(baselines)
    rows = {row.name: row for row in comparison.rows}
    dash = "—"

    def difference(name: str, index: int) -> str:
        row = rows.get(name)
        return dash if row is None else format_number(row.difference[index] * 1000.0, 1)

    def tested(name: str, cell) -> str:
        row = rows.get(name)
        return dash if row is None else cell(row)

    def quality(name: str, cell) -> str:
        indicators = qualities.get(name)
        return dash if indicators is None else cell(indicators)

    def significance(row) -> str:
        if row.is_significant:
            return f'<span class="fail">{escape(_tr("significant"))}</span>'
        return f'<span class="pass">{escape(_tr("not significant"))}</span>'

    def length(name: str) -> str:
        return format_number(baselines[name].length.value, 4)

    def length_deviation(name: str) -> str:
        return format_number(1000.0 * math.sqrt(baselines[name].length.variance), 1)

    def dop(indicators) -> str:
        median = indicators.dilution_of_precision
        return dash if median is None else format_number(median.position, 1)

    def counted(value) -> str:
        return dash if value is None else str(value)

    table_rows = [
        (_tr("Elevation mask (°)"), lambda name: format_number(masks[name], 1)),
        (_tr("Baseline length (m)"), length),
        (_tr("Length standard deviation (mm)"), length_deviation),
        (_tr("Difference in X (mm)"), lambda name: difference(name, 0)),
        (_tr("Difference in Y (mm)"), lambda name: difference(name, 1)),
        (_tr("Difference in Z (mm)"), lambda name: difference(name, 2)),
        (
            _tr("Difference in 3D (mm)"),
            lambda name: tested(name, lambda row: format_number(row.magnitude * 1000.0, 1)),
        ),
        (
            _tr("Difference in length (mm)"),
            lambda name: tested(name, lambda row: format_number(row.length_difference * 1000.0, 1)),
        ),
        (
            _tr("Test statistic"),
            lambda name: tested(name, lambda row: format_number(row.statistic, 2)),
        ),
        (_tr("Decision"), lambda name: tested(name, significance)),
        (_tr("Epochs"), lambda name: quality(name, lambda q: str(q.epochs))),
        (
            _tr("Fixed epochs (%)"),
            lambda name: quality(name, lambda q: format_number(100.0 * q.fixed_fraction, 1)),
        ),
        (
            _tr("Ratio, median"),
            lambda name: quality(name, lambda q: format_number(q.ratio_median, 1)),
        ),
        (
            _tr("Satellites, fewest to most"),
            lambda name: quality(
                name,
                lambda q: _tr("%1 to %2")
                .replace("%1", str(q.satellites_least))
                .replace("%2", str(q.satellites_most)),
            ),
        ),
        (_tr("PDOP, median"), lambda name: quality(name, dop)),
        (_tr("Cycle slips"), lambda name: quality(name, lambda q: counted(q.cycle_slips))),
        (
            _tr("Rejected observations"),
            lambda name: quality(name, lambda q: counted(q.rejections)),
        ),
    ]
    headers = [escape(_tr("Configuration"))] + [
        escape(
            _tr("%1 (reference)").replace("%1", name) if name == comparison.reference else name
        )
        for name in names
    ]
    body = [
        f"<p>{escape(_tr('Baseline %1 → %2.').replace('%1', base).replace('%2', rover))}</p>",
        f"<h2>{escape(_tr('Side by side'))}</h2>",
        render_table(
            headers,
            [[escape(label)] + [cell(name) for name in names] for label, cell in table_rows],
        ),
        render_note(verdict(comparison)),
        render_note(
            _tr(
                "Each difference is the configuration's baseline minus the reference's, tested "
                "against the two solutions' covariances together. The runs share their "
                "observations but are tested as if independent, which overstates each "
                "difference's uncertainty: a difference reported significant is significant, "
                "and one reported not significant may still hide a small real one."
            ),
            label=_tr("How to read it"),
        ),
    ]
    return render_document(_tr("Configurations compared"), body)
