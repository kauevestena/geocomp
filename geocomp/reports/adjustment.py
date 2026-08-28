# SPDX-License-Identifier: GPL-2.0-or-later
"""The adjustment report (FR-930, FR-931).

``specs/19-visualization.md`` section 7.

One comprehensive report, built from a :class:`~geocomp.core.models.Solution`
and nothing else. That constraint is what makes it engine-agnostic: DynAdjust's
parser fills the same Solution in phase P6, so the same report renders a
DynAdjust run without knowing it (``specs/03`` section 3.2).

**It is intended to be defensible.** ``specs/19`` section 7.1: *a reader should
be able to see exactly what was computed, from what, with what assumptions.* So
three things are never omitted, whatever the template does with the rest:

* the **uncertainty mode**, and the strategies where it is approximate (FR-203) --
  presenting a heuristic figure as a rigorously propagated one misrepresents the
  quality of a survey, and monitoring decisions are made on these numbers;
* the **provenance** -- inputs by id and digest, parameters, engine and version;
* the **uncheckable observations** -- a network full of observations with a
  redundancy near zero can pass every statistical test while being wrong, and a
  report that shows only the tests that passed is the one that hides it.

**Deterministic** (NFR-007): the same solution renders byte-identically. Nothing
here reads the clock -- the only time in the document is the provenance's own
``created``, which belongs to the run rather than to the rendering. A report
whose bytes change every time cannot be diffed, checksummed or attached to a
claim that two runs agreed.

**No map.** ``specs/19`` section 7.1 lists one among the sections. Rendering a
map needs a QGIS map canvas and a layout engine; embedding a picture of the
network is worth doing and belongs with the visualisation work that has one.
Saying so beats a placeholder that looks like a missing image.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.reporting import (
    _STYLE,
    escape,
    format_number,
    render_note,
    render_table,
)
from geocomp.core.models import Network, Solution
from geocomp.core.uncertainty import UncertaintyMode
from geocomp.core.version import __version__
from geocomp.reports.templates import Template, load_template, render, unused_sections

__all__ = ["ReportContext", "build_sections", "render_adjustment_report"]

_CONTEXT = "GeoCompAdjustmentReport"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


@dataclass
class ReportContext:
    """Everything the report says beyond what the solution carries.

    Attributes:
        parameter_scopes: ``{key: (value, scope)}`` -- the effective settings
            **and where each came from** (FR-068). The scope is the part that
            matters: "confidence 0.99" and "confidence 0.99, from this project"
            are different statements to somebody reproducing the run.
        qgis_version: Recorded for the software section.
    """

    network: Network | None = None
    parameter_scopes: dict[str, tuple[Any, str]] = field(default_factory=dict)
    qgis_version: str = ""
    template_directory: str = ""
    template_name: str = "adjustment.html"


def _heading(text: str) -> str:
    return f"<h2>{escape(text)}</h2>"


def _identification(solution: Solution) -> str:
    rows = [
        [escape(_tr("Solution")), escape(solution.id)],
        [escape(_tr("Network")), escape(solution.network_id or "—")],
        [escape(_tr("Kind")), escape(solution.kind.value)],
        [escape(_tr("Coordinate reference system")), escape(solution.crs)],
        [escape(_tr("Epoch")), format_number(solution.epoch.decimal_year, 4)],
        [escape(_tr("Datum definition")), escape(solution.datum_definition.value)],
    ]
    if solution.is_superseded:
        rows.append([escape(_tr("Superseded by")), escape(solution.superseded_by)])
    return _heading(_tr("Identification")) + render_table(
        [escape(_tr("Field")), escape(_tr("Value"))], rows
    )


def _uncertainty_notice(solution: Solution) -> str:
    """FR-203, and the section that is never omitted.

    An approximate result presented as a rigorous one misrepresents the quality
    of a survey. The notice names the strategies, not merely the mode, because
    "approximate" alone does not tell a reader *what* was approximated.
    """
    if solution.uncertainty_mode is UncertaintyMode.RIGOROUS:
        return render_note(
            _tr(
                "Every uncertainty in this report was propagated rigorously: no "
                "approximate strategy was used at any step."
            ),
            label=_tr("Uncertainty"),
        )

    strategies = sorted(
        {
            strategy.value
            for station in solution.adjusted_stations
            if station.covariance is not None
            for strategy in station.covariance.strategies
        }
    )
    named = ", ".join(strategies) if strategies else _tr("(not recorded)")
    return render_note(
        _tr(
            "Some uncertainties in this report are APPROXIMATE. The strategies used "
            "were: %1. An approximate figure presented as a rigorously propagated "
            "one misrepresents the quality of the survey, which is why this notice "
            "cannot be removed by a template."
        ).replace("%1", named),
        label=_tr("Uncertainty"),
    )


def _inputs(solution: Solution, network: Network | None) -> str:
    if network is None:
        return _heading(_tr("Inputs")) + render_note(
            _tr(
                "The network was not supplied to the report, so the input summary "
                "is limited to what the solution records."
            ),
            label=_tr("Inputs"),
        ) + render_table(
            [escape(_tr("Quantity")), escape(_tr("Count"))],
            [
                [escape(_tr("Adjusted stations")), str(len(solution.adjusted_stations))],
                [
                    escape(_tr("Observation results")),
                    str(len(solution.observation_results)),
                ],
            ],
        )

    by_type: dict[str, int] = {}
    for observation in network.active_observations:
        by_type[observation.type.value] = by_type.get(observation.type.value, 0) + 1

    constrained = network.constrained_stations()
    summary = render_table(
        [escape(_tr("Quantity")), escape(_tr("Count"))],
        [
            [escape(_tr("Stations")), str(len(network.stations))],
            [escape(_tr("Constrained stations")), str(len(constrained))],
            [escape(_tr("Active observations")), str(len(network.active_observations))],
            [escape(_tr("Correlated clusters")), str(len(network.clusters))],
        ],
    )
    types = render_table(
        [escape(_tr("Observation type")), escape(_tr("Count"))],
        [[escape(name), str(count)] for name, count in sorted(by_type.items())],
    )
    constraints = render_table(
        [
            escape(_tr("Station")),
            escape(_tr("Constraint")),
            escape(_tr("Components")),
        ],
        [
            [
                escape(station.id),
                escape(station.constraint.mode.value),
                escape(", ".join(sorted(station.constraint.components))),
            ]
            for station in sorted(constrained, key=lambda s: s.id)
        ],
    )
    return (
        _heading(_tr("Inputs"))
        + summary
        + f"<h3>{escape(_tr('Observations by type'))}</h3>"
        + types
        + f"<h3>{escape(_tr('Constraints'))}</h3>"
        + constraints
    )


def _parameters(context: ReportContext) -> str:
    """FR-068: the effective value **and the scope it came from**."""
    if not context.parameter_scopes:
        return _heading(_tr("Parameters")) + render_note(
            _tr("No effective parameters were recorded for this run."),
            label=_tr("Parameters"),
        )
    rows = [
        [escape(key), escape(value), escape(scope)]
        for key, (value, scope) in sorted(context.parameter_scopes.items())
    ]
    return (
        _heading(_tr("Parameters"))
        + render_table(
            [escape(_tr("Setting")), escape(_tr("Effective value")), escape(_tr("From"))],
            rows,
        )
        + render_note(
            _tr(
                "The scope column is what makes a run reproducible: the same value "
                "reached from a project override and from the built-in default are "
                "different statements to somebody repeating the work."
            ),
            label=_tr("Where each value came from"),
        )
    )


def _results(solution: Solution) -> str:
    if not solution.adjusted_stations:
        return _heading(_tr("Results")) + render_note(
            _tr("This solution adjusted no station."), label=_tr("Results")
        )
    rows = []
    for station in sorted(solution.adjusted_stations, key=lambda s: s.station_id):
        values = station.position.values
        rows.append(
            [
                escape(station.station_id),
                *[format_number(quantity.value, 5) for quantity in values],
                *[format_number(quantity.std_dev * 1000.0, 2) for quantity in values],
                format_number(
                    station.positional_uncertainty * 1000.0
                    if station.positional_uncertainty is not None
                    else None,
                    2,
                ),
            ]
        )
    names = solution.adjusted_stations[0].position.system.component_names
    headers = [
        escape(_tr("Station")),
        *[escape(name) for name in names],
        *[escape(_tr("sigma %1 (mm)").replace("%1", name)) for name in names],
        escape(_tr("Positional uncertainty (mm)")),
    ]
    return _heading(_tr("Adjusted coordinates")) + render_table(headers, rows)


def _statistics(solution: Solution) -> str:
    statistics = solution.statistics
    rows = [
        [escape(_tr("Observations")), str(statistics.n_observations)],
        [escape(_tr("Parameters")), str(statistics.n_parameters)],
        [escape(_tr("Constraints")), str(statistics.n_constraints)],
        [escape(_tr("Degrees of freedom")), str(statistics.degrees_of_freedom)],
        [
            escape(_tr("Variance factor a priori")),
            format_number(statistics.variance_factor_apriori, 6),
        ],
        [
            escape(_tr("Variance factor a posteriori")),
            format_number(statistics.variance_factor_aposteriori, 6),
        ],
        [escape(_tr("Iterations")), str(statistics.iterations)],
        [
            escape(_tr("Converged")),
            escape(_tr("yes") if statistics.converged else _tr("NO")),
        ],
        [
            escape(_tr("Largest correction")),
            format_number(statistics.max_correction, 6),
        ],
        [
            escape(_tr("Condition number")),
            format_number(statistics.condition_number, 3),
        ],
    ]
    body = _heading(_tr("Statistics")) + render_table(
        [escape(_tr("Quantity")), escape(_tr("Value"))], rows
    )

    test = statistics.global_test
    if test is None:
        return body + render_note(
            _tr("No global test was run for this solution."), label=_tr("Global test")
        )

    verdict = _tr("passed") if test.passed else _tr("FAILED")
    body += render_table(
        [
            escape(_tr("Test")),
            escape(_tr("Statistic")),
            escape(_tr("Lower critical")),
            escape(_tr("Upper critical")),
            escape(_tr("Confidence")),
            escape(_tr("Decision")),
        ],
        [
            [
                escape(test.name),
                format_number(test.statistic, 5),
                format_number(test.critical_low, 5),
                format_number(test.critical_high, 5),
                format_number(test.confidence, 3),
                f'<span class="{"pass" if test.passed else "fail"}">{escape(verdict)}</span>',
            ]
        ],
    )
    if not test.passed:
        body += render_note(
            _tr(
                "The global test failed. Either the observations disagree with each "
                "other more than their weights allow, or the weights are wrong — the "
                "test cannot distinguish the two, and reporting it as "
                "&quot;the adjustment failed&quot; would."
            ),
            label=_tr("What a failed global test means"),
        )
    return body


def _observation_results(solution: Solution) -> str:
    if not solution.observation_results:
        return _heading(_tr("Observation results")) + render_note(
            _tr("This solution recorded no per-observation results."),
            label=_tr("Observation results"),
        )
    rows = []
    for index, result in enumerate(solution.observation_results):
        test = result.w_test
        decision = ""
        if test is not None:
            marker = "pass" if test.passed else "fail"
            label = _tr("accepted") if test.passed else _tr("CANDIDATE")
            decision = f'<span class="{marker}">{escape(label)}</span>'
        rows.append(
            [
                str(index),
                escape(result.observation_id),
                format_number(result.residual, 6),
                format_number(result.standardised_residual, 3),
                format_number(result.redundancy, 4),
                format_number(result.minimal_detectable_bias, 6),
                format_number(result.external_reliability, 6),
                decision or "—",
            ]
        )
    return _heading(_tr("Observation results")) + render_table(
        [
            escape(_tr("Row")),
            escape(_tr("Observation")),
            escape(_tr("Residual")),
            escape(_tr("Standardised")),
            escape(_tr("Redundancy")),
            escape(_tr("MDB")),
            escape(_tr("External effect")),
            escape(_tr("w-test")),
        ],
        rows,
    )


def _reliability(solution: Solution) -> str:
    """The section a report that only showed passing tests would omit."""
    uncheckable = [
        result for result in solution.observation_results if result.is_uncheckable
    ]
    candidates = [
        result
        for result in solution.observation_results
        if result.w_test is not None and not result.w_test.passed
    ]

    body = _heading(_tr("Reliability")) + render_table(
        [escape(_tr("Quantity")), escape(_tr("Count"))],
        [
            [escape(_tr("Observations")), str(len(solution.observation_results))],
            [escape(_tr("Outlier candidates")), str(len(candidates))],
            [escape(_tr("Uncheckable observations")), str(len(uncheckable))],
        ],
    )

    if uncheckable:
        body += render_table(
            [escape(_tr("Observation")), escape(_tr("Redundancy"))],
            [
                [escape(result.observation_id), format_number(result.redundancy, 5)]
                for result in uncheckable
            ],
        )
        body += render_note(
            _tr(
                "An observation with a redundancy number near zero is uncheckable: "
                "no blunder in it is detectable at all. A network full of them can "
                "pass every statistical test while being wrong, so they are listed "
                "here whether or not anything else in this report looks amiss."
            ),
            label=_tr("Uncheckable observations"),
        )
    else:
        body += render_note(
            _tr("Every observation in this adjustment is checkable."),
            label=_tr("Uncheckable observations"),
        )

    if candidates:
        body += render_note(
            _tr(
                "Candidates, not rejections. GeoComp never removes an observation on "
                "its own: in a monitoring network the displacement being measured is "
                "exactly what an automatic outlier remover would delete."
            ),
            label=_tr("Data snooping"),
        )
    return body


def _ellipses(solution: Solution) -> str:
    rows = [
        [
            escape(station.station_id),
            format_number(station.ellipse.semi_major * 1000.0, 3),
            format_number(station.ellipse.semi_minor * 1000.0, 3),
            format_number(station.ellipse.orientation, 5),
            format_number(station.ellipse.confidence, 3),
        ]
        for station in sorted(solution.adjusted_stations, key=lambda s: s.station_id)
        if station.ellipse is not None
    ]
    if not rows:
        return _heading(_tr("Error ellipses")) + render_note(
            _tr(
                "No error ellipse was computed. A one-dimensional adjustment has "
                "none: a height has an uncertainty, not an ellipse."
            ),
            label=_tr("Error ellipses"),
        )
    return _heading(_tr("Error ellipses")) + render_table(
        [
            escape(_tr("Station")),
            escape(_tr("Semi-major (mm)")),
            escape(_tr("Semi-minor (mm)")),
            escape(_tr("Orientation (rad)")),
            escape(_tr("Confidence")),
        ],
        rows,
    )


def _provenance(solution: Solution) -> str:
    provenance = solution.provenance
    if provenance is None:
        return _heading(_tr("Provenance")) + render_note(
            _tr(
                "This solution carries no provenance record, so what produced it "
                "cannot be reproduced from this report."
            ),
            label=_tr("Provenance"),
        )

    rows = [
        [escape(_tr("Created")), escape(provenance.created.isoformat())],
        [escape(_tr("Algorithm")), escape(provenance.algorithm_id or "—")],
        [escape(_tr("Source")), escape(provenance.source or "—")],
        [escape(_tr("Engine")), escape(provenance.engine or _tr("GeoComp in-house core"))],
        [escape(_tr("Engine version")), escape(provenance.engine_version or "—")],
    ]
    if provenance.command_line:
        rows.append([escape(_tr("Command line")), f"<code>{escape(provenance.command_line)}</code>"])
    if provenance.exit_code is not None:
        rows.append([escape(_tr("Exit code")), str(provenance.exit_code)])

    body = _heading(_tr("Provenance")) + render_table(
        [escape(_tr("Field")), escape(_tr("Value"))], rows
    )

    if provenance.parameters:
        body += render_table(
            [escape(_tr("Parameter")), escape(_tr("Value"))],
            [
                [escape(key), escape(value)]
                for key, value in sorted(provenance.parameters.items())
            ],
        )
    if provenance.input_ids or provenance.input_digests:
        body += render_table(
            [escape(_tr("Input")), escape(_tr("Digest"))],
            [
                [escape(name), f"<code>{escape(provenance.input_digests.get(name, '—'))}</code>"]
                for name in sorted(
                    set(provenance.input_ids) | set(provenance.input_digests)
                )
            ],
        )
        body += render_note(
            _tr(
                "Inputs are recorded by id and by content digest. The digest is what "
                "turns &quot;reproduce this&quot; into something checkable: the same "
                "id with different content is a different run."
            ),
            label=_tr("Inputs"),
        )
    return body


def _software(solution: Solution, context: ReportContext, template: Template) -> str:
    rows = [
        [escape(_tr("GeoComp")), escape(__version__)],
        [escape(_tr("QGIS")), escape(context.qgis_version or "—")],
        [
            escape(_tr("Uncertainty mode")),
            escape(solution.uncertainty_mode.value),
        ],
        [
            escape(_tr("Report template")),
            escape(
                _tr("shipped with GeoComp")
                if template.is_shipped
                else str(template.source)
            ),
        ],
    ]
    return _heading(_tr("Software")) + render_table(
        [escape(_tr("Component")), escape(_tr("Version"))], rows
    )


def build_sections(
    solution: Solution, context: ReportContext | None = None
) -> dict[str, str]:
    """Every section of the report, keyed by the token a template places it with."""
    context = context or ReportContext()
    template = load_template(context.template_name, directory=context.template_directory)
    return {
        "title": _tr("Adjustment report"),
        "style": _STYLE,
        "identification": _identification(solution),
        "uncertainty_notice": _uncertainty_notice(solution),
        "inputs": _inputs(solution, context.network),
        "parameters": _parameters(context),
        "results": _results(solution),
        "statistics": _statistics(solution),
        "observation_results": _observation_results(solution),
        "reliability": _reliability(solution),
        "ellipses": _ellipses(solution),
        "provenance": _provenance(solution),
        "software": _software(solution, context, template),
    }


def render_adjustment_report(
    solution: Solution, context: ReportContext | None = None
) -> tuple[str, list[str]]:
    """Render the report, and say which sections the template left out.

    Returns:
        The HTML, and the sections the template does not place. The second half
        is not a warning to be swallowed: ``specs/19`` section 7.1 lists what a
        defensible report carries, and a template that omits the reliability
        section is making an editorial choice that should be visible.
    """
    context = context or ReportContext()
    template = load_template(context.template_name, directory=context.template_directory)
    sections = build_sections(solution, context)
    return render(template, sections), unused_sections(template, sections)
