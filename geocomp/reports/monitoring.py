# SPDX-License-Identifier: GPL-2.0-or-later
"""The monitoring report (FR-932; ``specs/19`` section 7.2, phase P10b).

Displacement table with the significance decisions; the reference block's
stability test and, when it failed, every localisation step; the global
congruency test; the deformation summary; the alerts; a displacement map; the
time series and velocities; and the epoch metadata and every transformation
applied, for each epoch compared.

Built from the monitoring documents (:mod:`geocomp.core.monitoring.document`)
and nothing else -- the same ones the map layers and the time-series panel read
-- so a report rendered next year from the saved files says what it says today
(NFR-007), and cannot say something the map does not show.

**Never omitted, whatever the template does with the rest:** the uncertainty
mode with the strategies and the direction of their bias (FR-203); the
compatibility findings and transformations, because a displacement across a
frame change is only as good as the transformation (``specs/14`` section 3);
and the reference block's test, because every displacement is measured against
it (section 5). A report that showed the decisions without the premise they rest
on would be the report that misleads.

Numbers are in millimetres, because that is the size of the motion; the
documents keep metres.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.reporting import _STYLE, escape, format_number, render_note, render_table
from geocomp.core.statistics.distributions import normal_quantile
from geocomp.core.version import __version__
from geocomp.core.visualization.monitoring import ALERT, displacement_exaggeration, series_limits
from geocomp.core.visualization.svg import MapText, PlotText, displacement_map, series_plot
from geocomp.reports.templates import load_template, render, unused_sections

__all__ = [
    "MonitoringReportContext",
    "build_monitoring_sections",
    "describe_finding",
    "render_monitoring_report",
]

_CONTEXT = "GeoCompMonitoringReport"

#: Sections placed whatever the template says -- see the module docstring.
ALWAYS = ("uncertainty_notice", "compatibility", "reference_block")


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


@dataclass
class MonitoringReportContext:
    """Everything the report says beyond what the documents carry.

    Attributes:
        exaggeration: The map's factor; 0 fits it to the network, as the layers do.
    """

    qgis_version: str = ""
    template_directory: str = ""
    template_name: str = "monitoring.html"
    exaggeration: float = 0.0


# -- words -------------------------------------------------------------------------


def _decision(decision: str | None) -> str:
    if decision == "significant":
        return f'<span class="fail">{escape(_tr("significant"))}</span>'
    if decision == "not significant":
        return f'<span class="pass">{escape(_tr("not significant"))}</span>'
    return "—"


def _test_decision(test: dict[str, Any] | None) -> str:
    if not test:
        return "—"
    return _decision("not significant" if test["passed"] else "significant")


def _passed(passed: bool) -> str:
    verdict = _tr("passed") if passed else _tr("FAILED")
    return f'<span class="{"pass" if passed else "fail"}">{escape(verdict)}</span>'


def _datum_label(datum: str) -> str:
    return {
        "translation": _tr("translation"),
        "translation_rotation": _tr("translation and rotation"),
        "similarity": _tr("translation, rotation and scale"),
    }.get(datum, datum)


def _role(role: str) -> str:
    return {"reference": _tr("reference"), "object": _tr("object")}.get(role, role)


def _kind(kind: str) -> str:
    return {
        "magnitude": _tr("displacement magnitude"),
        "horizontal": _tr("horizontal displacement"),
        "vertical": _tr("vertical displacement"),
        "velocity": _tr("speed"),
        "significance": _tr("significant motion"),
    }.get(kind, kind)


def _component(name: str) -> str:
    return {
        "e": _tr("east"),
        "n": _tr("north"),
        "u": _tr("up"),
        "h": _tr("height"),
    }.get(name, name)


def describe_finding(finding: dict[str, Any]) -> str:
    """A comparison finding in the reader's language."""
    context = finding.get("context", {})
    code = finding.get("code", "")
    if code == "engines_differ":
        return (
            _tr("The epochs were processed by different engines or versions: %1 and %2.")
            .replace("%1", str(context.get("first", "")))
            .replace("%2", str(context.get("second", "")))
        )
    if code == "datums_both_free":
        return (
            _tr(
                "The datum definitions differ (%1 and %2); both are free, and they are related by the "
                "S-transformation onto the reference block."
            )
            .replace("%1", str(context.get("first", "")))
            .replace("%2", str(context.get("second", "")))
        )
    if code == "stations_in_one_epoch":
        return _tr("Stations in one epoch only, not compared: %1.").replace(
            "%1", ", ".join(context.get("stations", []))
        )
    return code


def _mm(value: float | None, decimals: int = 2) -> str:
    return "—" if value is None else format_number(1000.0 * value, decimals)


def _heading(text: str) -> str:
    return f"<h2>{escape(text)}</h2>"


# -- sections -----------------------------------------------------------------------


def _identification(documents: list[dict[str, Any]]) -> str:
    epochs: dict[str, dict[str, Any]] = {}
    for document in documents:
        for epoch in document["epochs"]:
            epochs.setdefault(epoch["solution"], epoch)
    rows = []
    for epoch in sorted(epochs.values(), key=lambda e: e["epoch"]):
        engine = " ".join(filter(None, (epoch.get("engine") or "", epoch.get("engine_version") or "")))
        rows.append(
            [
                escape(epoch["solution"]),
                format_number(epoch["epoch"], 4),
                escape(epoch["crs"]),
                escape(epoch["datum"]),
                escape(", ".join(epoch.get("height_types", [])) or "—"),
                escape(", ".join(epoch.get("geoid_models", [])) or "—"),
                escape(engine or "—"),
                escape(epoch.get("uncertainty_mode", "")),
            ]
        )
    return _heading(_tr("Epochs")) + render_table(
        [
            escape(_tr("Solution")),
            escape(_tr("Epoch")),
            escape(_tr("Coordinate reference system")),
            escape(_tr("Datum definition")),
            escape(_tr("Heights")),
            escape(_tr("Geoid model")),
            escape(_tr("Engine")),
            escape(_tr("Uncertainty mode")),
        ],
        rows,
    )


def _uncertainty_notice(documents: list[dict[str, Any]]) -> str:
    """FR-203: the mode, the strategies, and which way the approximation errs."""
    strategies = sorted({s for d in documents for s in d.get("strategies", [])})
    if all(d.get("mode") == "rigorous" for d in documents) and not strategies:
        return render_note(
            _tr(
                "The displacements' uncertainties were propagated rigorously, with the "
                "correlation between the epochs."
            ),
            label=_tr("Uncertainty"),
        )
    text = _tr("Approximate: %1.").replace("%1", ", ".join(strategies) or _tr("(not recorded)"))
    if "independence_assumed" in strategies:
        text += " " + _tr(
            "The epochs were taken as independent. If they share reference stations, a datum "
            "definition or GNSS products, they are positively correlated: each displacement's "
            "true uncertainty is smaller than the one stated here, so the significance of real "
            "motion is understated, not overstated."
        )
    return render_note(text, label=_tr("Uncertainty"))


def _compatibility(comparison: dict[str, Any] | None) -> str:
    body = _heading(_tr("Compatibility and transformations"))
    if comparison is None:
        return body + render_note(
            _tr(
                "Each epoch of the series was compared with the first under the same checks: "
                "frames, epochs, datum definitions, height types and geoid models."
            )
        )
    findings = comparison.get("findings", [])
    if findings:
        body += "<ul>" + "".join(f"<li>{escape(describe_finding(f))}</li>" for f in findings) + "</ul>"
    else:
        body += render_note(
            _tr(
                "Both epochs agree in frame, datum definition, height type, geoid model and "
                "engine; nothing was found that would put a systematic difference into the "
                "displacements."
            )
        )
    transformations = comparison.get("transformations", [])
    if not transformations:
        return body + render_note(_tr("No transformation was applied: both epochs are in one frame."))
    rows = [
        [
            escape(t["source"]),
            escape(t["target"]),
            format_number(t["source_epoch"], 4),
            format_number(t["target_epoch"], 4),
            str(len(t.get("steps", []))),
            _mm(t.get("accuracy")),
        ]
        for t in transformations
    ]
    body += render_table(
        [
            escape(_tr("From")),
            escape(_tr("To")),
            escape(_tr("At epoch")),
            escape(_tr("To epoch")),
            escape(_tr("Steps")),
            escape(_tr("Accuracy (mm)")),
        ],
        rows,
    )
    return body + render_note(
        _tr(
            "The transformation's accuracy enters every station alike, as a common translation: "
            "it cancels in displacements measured against the reference block and remains in an "
            "absolute one."
        )
    )


def _parameters(comparison: dict[str, Any] | None, series: dict[str, Any] | None) -> str:
    document = comparison or series
    assert document is not None
    rows = [
        [escape(_tr("Confidence level")), format_number(document["confidence"], 4)],
        [escape(_tr("Datum of the displacements")), escape(_datum_label(document.get("datum", "")))],
        [escape(_tr("Reference stations")), escape(", ".join(document.get("reference", [])) or "—")],
    ]
    if comparison is not None:
        rows += [
            [escape(_tr("Object stations")), escape(", ".join(comparison.get("objects", [])) or "—")],
            [escape(_tr("Pooled variance factor")), format_number(comparison.get("variance_factor"), 4)],
            [escape(_tr("Degrees of freedom")), str(comparison.get("degrees_of_freedom"))],
        ]
    return _heading(_tr("Parameters")) + render_table(
        [escape(_tr("Parameter")), escape(_tr("Value"))], rows
    )


def _congruency_row(label: str, congruency: dict[str, Any]) -> list[str]:
    test = congruency["test"]
    return [
        escape(label),
        escape(", ".join(congruency["stations"])),
        format_number(congruency["omega"], 4),
        str(congruency["rank"]),
        format_number(test["statistic"], 3),
        format_number(test.get("critical_high"), 3),
        _passed(congruency["passed"]),
    ]


_CONGRUENCY_HEADERS = (
    "Test",
    "Stations",
    "Omega",
    "Rank",
    "Statistic",
    "Critical value",
    "Decision",
)


def _congruency_headers() -> list[str]:
    return [escape(_tr(h)) for h in _CONGRUENCY_HEADERS]


def _reference_block(comparison: dict[str, Any] | None) -> str:
    """The premise every displacement rests on: that the reference block did not move."""
    body = _heading(_tr("Reference block"))
    if comparison is None:
        return body + render_note(
            _tr("Every epoch of the series is referred to the reference block by an S-transformation.")
        )
    check = comparison["reference_check"]
    body += render_table(
        _congruency_headers(), [_congruency_row(_tr("Reference block congruency"), check["test"])]
    )
    if check["passed"]:
        return body + render_note(
            _tr(
                "The reference stations have not moved relative to one another at this confidence: "
                "the block is a sound datum for the displacements."
            )
        )
    steps = []
    for number, step in enumerate(check["steps"], start=1):
        largest = sorted(step["contributions"].items(), key=lambda item: -item[1])[:3]
        steps.append(
            [
                str(number),
                escape(", ".join(step["test"]["stations"])),
                format_number(step["test"]["test"]["statistic"], 3),
                format_number(step["test"]["test"].get("critical_high"), 3),
                escape(", ".join(f"{s} {format_number(v, 3)}" for s, v in largest)),
                f"<b>{escape(step['removed'])}</b>",
            ]
        )
    body += render_table(
        [
            escape(_tr("Step")),
            escape(_tr("Stations tested")),
            escape(_tr("Statistic")),
            escape(_tr("Critical value")),
            escape(_tr("Largest contributions")),
            escape(_tr("Removed")),
        ],
        steps,
    )
    return body + render_note(
        _tr(
            "The reference block moved. The localisation implicates %1; the stations that remain "
            "stable together are %2. This subset is proposed, not adopted: the analysis did not "
            "proceed, because a moved block spreads its motion over every other station. Check "
            "the implicated pillars, then analyse again with them among the object points."
        )
        .replace("%1", ", ".join(check["implicated"]) or "—")
        .replace("%2", ", ".join(check["stable"]) or "—"),
        label=_tr("Analysis refused"),
    )


def _global_test(comparison: dict[str, Any] | None) -> str:
    if comparison is None or comparison.get("global_test") is None:
        return ""
    return _heading(_tr("Global congruency")) + render_table(
        _congruency_headers(),
        [_congruency_row(_tr("All compared stations"), comparison["global_test"])],
    )


def _displacements(comparison: dict[str, Any] | None) -> str:
    if comparison is None or not comparison.get("displacements"):
        return ""
    components = comparison["components"]
    headers = [escape(_tr("Station")), escape(_tr("Role"))]
    for name in components:
        headers.append(escape(_tr("%1 (mm)").replace("%1", _component(name))))
    for name in components:
        headers.append(escape(_tr("Std. dev. %1 (mm)").replace("%1", _component(name))))
    headers += [
        escape(_tr("Statistic")),
        escape(_tr("Critical value")),
        escape(_tr("Decision")),
    ]
    plan = "e" in components and "n" in components
    if plan:
        headers.append(escape(_tr("Horizontal")))
    if "u" in components:
        headers.append(escape(_tr("Vertical")))
    rows = []
    for d in comparison["displacements"]:
        row = [escape(d["station"]), escape(_role(d["role"]))]
        row += [_mm(v) for v in d["values"]]
        row += [_mm(v) for v in d["std_devs"]]
        row += [
            format_number(d["test"]["statistic"], 3),
            format_number(d["test"].get("critical_high"), 3),
            _decision(d["decision"]),
        ]
        if plan:
            row.append(_test_decision(d["horizontal"]))
        if "u" in components:
            row.append(_test_decision(d["vertical"]))
        rows.append(row)
    return (
        _heading(_tr("Displacements"))
        + render_table(headers, rows)
        + render_note(
            _tr(
                "Each displacement is tested against its own covariance at the confidence level "
                "above. Not significant is not zero: the value is kept, with its uncertainty, "
                "because we could not detect motion is a different statement from there is no motion."
            )
        )
    )


def _displacement_map(comparison: dict[str, Any] | None, context: MonitoringReportContext) -> str:
    if comparison is None or not comparison.get("displacements"):
        return ""
    factor = context.exaggeration or displacement_exaggeration(comparison)
    text = MapText(
        caption=_tr("arrows and ellipses exaggerated %1x; ellipses at %2% confidence")
        .replace("%1", f"{factor:g}")
        .replace("%2", f"{100.0 * comparison['confidence']:g}"),
        legend={
            ALERT: _tr("alert"),
            "significant": _tr("significant"),
            "not significant": _tr("not significant"),
        },
        reference=_tr("reference"),
        obj=_tr("object"),
    )
    svg = displacement_map(comparison, exaggeration=factor, text=text)
    if not svg:
        return _heading(_tr("Displacement map")) + render_note(
            _tr("The stations have no plan position to draw them at; see the table above.")
        )
    return _heading(_tr("Displacement map")) + f'<div class="figure">{svg}</div>'


def _deformation(comparison: dict[str, Any] | None) -> str:
    if comparison is None or comparison.get("status") != "analysed":
        return ""
    strain = comparison.get("strain")
    body = _heading(_tr("Deformation"))
    if strain is None:
        note = comparison.get("strain_note", "")
        reason = (
            _tr("Strain was not requested.")
            if note == "not_requested"
            else _tr(
                "Strain was not computed: it needs three object points at least, spread over an area."
            )
        )
        return body + render_note(reason)
    sd = strain["std_devs"]
    rows = [
        [escape(_tr("Stations")), escape(", ".join(strain["stations"]))],
        [
            escape(_tr("Rigid translation east, north (mm)")),
            f"{_mm(strain['rigid_translation'][0])}, {_mm(strain['rigid_translation'][1])}",
        ],
        [escape(_tr("Rigid rotation (µrad)")), format_number(1e6 * strain["rigid_rotation"], 2)],
        [
            escape(_tr("Dilatation (ppm)")),
            _plus_minus(strain["dilatation"], sd.get("dilatation")),
        ],
        [
            escape(_tr("Maximum shear (ppm)")),
            _plus_minus(strain["shear"], sd.get("shear")),
        ],
        [
            escape(_tr("Principal strains (ppm)")),
            ", ".join(format_number(1e6 * value, 2) for value in strain["principal"]),
        ],
        [
            escape(_tr("Azimuth of the first principal strain (°)")),
            format_number(math.degrees(strain["azimuth"]), 2),
        ],
        [
            escape(_tr("Strain test")),
            f"{format_number(strain['strain_test']['statistic'], 3)} / "
            f"{format_number(strain['strain_test'].get('critical_high'), 3)} "
            + (
                f'<span class="fail">{escape(_tr("deforming"))}</span>'
                if strain["deforming"]
                else f'<span class="pass">{escape(_tr("moving as a rigid block"))}</span>'
            ),
        ],
    ]
    return body + render_table([escape(_tr("Quantity")), escape(_tr("Value"))], rows)


def _plus_minus(value: float, sigma: float | None) -> str:
    """A strain in parts per million, with its standard deviation when known."""
    text = format_number(1e6 * value, 2)
    return text if sigma is None else f"{text} ± {format_number(1e6 * sigma, 2)}"


def _alerts(documents: list[dict[str, Any]]) -> str:
    thresholds = [t for d in documents for t in d.get("thresholds", [])]
    alerts = [a for d in documents for a in d.get("alerts", [])]
    body = _heading(_tr("Alerts"))
    if not thresholds:
        return body + render_note(_tr("No alert thresholds were set for this analysis."))
    body += render_table(
        [escape(_tr("Criterion")), escape(_tr("Limit")), escape(_tr("Stations")), escape(_tr("Group"))],
        [
            [
                escape(_kind(t["kind"])),
                "—" if t["kind"] == "significance" else _limit(t["kind"], t["limit"]),
                escape(", ".join(t["stations"]) if t["stations"] else _tr("all")),
                escape(t.get("group") or "—"),
            ]
            for t in thresholds
        ],
    )
    crossed = [a for a in alerts if a["exceeded"]]
    if not crossed:
        return body + render_note(
            _tr("No station crossed a threshold. %1 station checks were made.").replace(
                "%1", str(len(alerts))
            )
        )
    rows = [
        [
            f'<span class="fail">{escape(a["station"])}</span>',
            escape(_kind(a["kind"])),
            "—" if a["value"] is None else _limit(a["kind"], a["value"]),
            "—" if a["kind"] == "significance" else _limit(a["kind"], a["limit"]),
            {True: escape(_tr("yes")), False: escape(_tr("no")), None: "—"}[a.get("significant")],
        ]
        for a in crossed
    ]
    return (
        body
        + render_table(
            [
                escape(_tr("Station")),
                escape(_tr("Criterion")),
                escape(_tr("Value")),
                escape(_tr("Limit")),
                escape(_tr("Significant")),
            ],
            rows,
        )
        + render_note(
            _tr(
                "A station over its limit is flagged whether or not its motion is significant: the "
                "owner's criterion is not silenced by the survey's precision."
            )
        )
    )


def _limit(kind: str, value: float) -> str:
    text = _mm(value)
    return f"{text} mm/a" if kind == "velocity" else f"{text} mm"


def _time_series(series: dict[str, Any] | None) -> str:
    if series is None:
        return ""
    factor = normal_quantile(0.5 + series["confidence"] / 2.0)
    body = _heading(_tr("Time series"))
    body += render_note(
        _tr(
            "Offsets from the first epoch, referred to the reference block, with a band of %1 "
            "standard deviations (%2% confidence) and the fitted velocity line."
        )
        .replace("%1", format_number(factor, 2))
        .replace("%2", f"{100.0 * series['confidence']:g}")
    )
    for record in series["stations"]:
        for component in record["components"]:
            limits = series_limits(series, record["station"], component)
            body += '<div class="figure">' + series_plot(
                record,
                component,
                band_factor=factor,
                thresholds=limits,
                text=PlotText(
                    title=f"{record['station']} — {_component(component)}",
                    x_label=_tr("epoch (decimal year)"),
                    y_label=_tr("offset (mm)"),
                    band=_tr("band"),
                    fit=_tr("fitted line"),
                    threshold=_tr("alert limit"),
                ),
            ) + "</div>"
    return body


def _velocities(series: dict[str, Any] | None) -> str:
    if series is None:
        return ""
    components = series["components"]
    headers = [escape(_tr("Station")), escape(_tr("Epochs"))]
    headers += [escape(_tr("v %1 (mm/a)").replace("%1", _component(c))) for c in components]
    headers += [escape(_tr("Std. dev. %1 (mm/a)").replace("%1", _component(c))) for c in components]
    headers += [escape(_tr("Speed (mm/a)")), escape(_tr("Statistic")), escape(_tr("Decision"))]
    rows = []
    for record in series["stations"]:
        velocity = record.get("velocity") or [None] * len(components)
        sigmas = record.get("velocity_std_devs") or [None] * len(components)
        test = record.get("velocity_test")
        rows.append(
            [escape(record["station"]), str(len(record["points"]))]
            + [_mm(v) for v in velocity]
            + [_mm(v) for v in sigmas]
            + [
                _mm(record.get("speed")),
                "—" if test is None else format_number(test["statistic"], 3),
                _test_decision(test),
            ]
        )
    return _heading(_tr("Velocities")) + render_table(headers, rows)


def _software(context: MonitoringReportContext, template) -> str:
    rows = [
        [escape(_tr("GeoComp")), escape(__version__)],
        [escape(_tr("QGIS")), escape(context.qgis_version or "—")],
        [
            escape(_tr("Report template")),
            escape(_tr("shipped with GeoComp") if template.is_shipped else str(template.source)),
        ],
    ]
    return _heading(_tr("Software")) + render_table(
        [escape(_tr("Component")), escape(_tr("Version"))], rows
    )


# -- assembly --------------------------------------------------------------------------


def build_monitoring_sections(
    comparison: dict[str, Any] | None,
    series: dict[str, Any] | None = None,
    context: MonitoringReportContext | None = None,
) -> dict[str, str]:
    """Every section, keyed by the token a template places it with."""
    if comparison is None and series is None:
        raise ValueError("a monitoring report needs a comparison, a series, or both")
    context = context or MonitoringReportContext()
    template = load_template(context.template_name, directory=context.template_directory)
    documents = [d for d in (comparison, series) if d is not None]
    return {
        "title": _tr("Monitoring report"),
        "style": _STYLE + ".figure{margin:1rem 0}.figure svg{max-width:100%;height:auto}",
        "identification": _identification(documents),
        "uncertainty_notice": _uncertainty_notice(documents),
        "compatibility": _compatibility(comparison),
        "parameters": _parameters(comparison, series),
        "reference_block": _reference_block(comparison),
        "global_test": _global_test(comparison),
        "displacements": _displacements(comparison),
        "displacement_map": _displacement_map(comparison, context),
        "deformation": _deformation(comparison),
        "alerts": _alerts(documents),
        "time_series": _time_series(series),
        "velocities": _velocities(series),
        "software": _software(context, template),
    }


def render_monitoring_report(
    comparison: dict[str, Any] | None,
    series: dict[str, Any] | None = None,
    context: MonitoringReportContext | None = None,
) -> tuple[str, list[str]]:
    """Render the report, and say which sections the template left out.

    The three sections of :data:`ALWAYS` are placed even by a template that
    leaves them out -- appended at its end -- because a report of decisions
    without their premise is the one that misleads.
    """
    context = context or MonitoringReportContext()
    template = load_template(context.template_name, directory=context.template_directory)
    sections = build_monitoring_sections(comparison, series, context)
    html = render(template, sections)
    omitted = unused_sections(template, sections)
    forced = [name for name in ALWAYS if name in omitted]
    if forced:
        extra = "".join(sections[name] for name in forced)
        html = html.replace("</body>", extra + "\n</body>") if "</body>" in html else html + extra
    return html, [name for name in omitted if name not in forced]
