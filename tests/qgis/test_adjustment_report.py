# SPDX-License-Identifier: GPL-2.0-or-later
"""The adjustment report (FR-930, FR-931).

``specs/19-visualization.md`` section 7. Here rather than in the fast tier
because the report phrases user-facing text, which needs Qt's translation
machinery (``specs/18`` section 2). The template mechanics, which need nothing,
are tested in ``tests/test_report_templates.py``.

The report is meant to be **defensible**: a reader should see exactly what was
computed, from what, with what assumptions. Most of what follows asserts the
parts a report could omit and still look finished.
"""

from __future__ import annotations

import pytest

import tests.networks as nets
from geocomp.core.adjustment import Frame
from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.models import DatumDefinition, HeightType
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.solution import Provenance
from geocomp.core.statistics.reliability import reliability
from geocomp.core.statistics.tests import data_snooping, global_test
from geocomp.core.uncertainty import Strategy, UncertaintyMode
from tests.conftest import requires_qgis

# **Both marks, and the skipif is the load-bearing one.** ``pytest.mark.qgis``
# only labels; it does not skip. Every other file here reaches QGIS through the
# ``qgis_app`` or ``geocomp_provider`` fixture, which skips when there is no
# runtime -- but this module's fixtures do not need the provider, so nothing
# skipped, the lazy ``from geocomp.reports import ...`` inside them raised
# ``ModuleNotFoundError``, and twenty-five tests **errored** rather than being
# skipped in the seven CI jobs without QGIS.
pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture(scope="module")
def adjusted():
    reference = nets.levelling_loop()
    run = adjust(
        reference.network,
        AdjustmentOptions(frame=Frame.HEIGHT_1D, datum=DatumDefinition.CONSTRAINED),
    )
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
        degrees_of_freedom=run.degrees_of_freedom,
    )
    report = reliability(
        run.cofactor_residuals,
        run.system.weight,
        run.system.design,
        run.cofactor_parameters,
        run.system.row_labels,
    )
    solution = to_solution(
        run,
        reference.network,
        solution_id="s1",
        crs="EPSG:31982",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.CONSTRAINED,
        height_type=HeightType.ORTHOMETRIC,
        observation_results=to_observation_results(
            run, snooping=snooping, reliability=report
        ),
        global_test=global_test(run.variance_factor_aposteriori, run.degrees_of_freedom),
        provenance=Provenance.now(
            algorithm_id="geocomp:analysis_network_adjust",
            source="test",
            parameters={"frame": "height_1d", "confidence": "0.95"},
            input_ids=("L0", "L1"),
            input_digests={"L0": "abc123", "L1": "def456"},
        ),
    )
    return reference.network, solution


@pytest.fixture
def context(adjusted):
    from geocomp.reports import ReportContext

    network, _solution = adjusted
    return ReportContext(
        network=network,
        qgis_version="3.34",
        parameter_scopes={
            "stochastic.confidence_level": ("0.95", "default"),
            "level.weighting": ("length", "this project"),
        },
    )


def _render(solution, context):
    from geocomp.reports import render_adjustment_report

    return render_adjustment_report(solution, context)


class TestItCarriesEverySection:
    def test_the_shipped_template_omits_nothing(self, adjusted, context):
        _network, solution = adjusted
        _html, omitted = _render(solution, context)
        assert omitted == []

    @pytest.mark.parametrize(
        "heading",
        [
            "Identification",
            "Inputs",
            "Parameters",
            "Adjusted coordinates",
            "Statistics",
            "Observation results",
            "Reliability",
            "Error ellipses",
            "Provenance",
            "Software",
        ],
    )
    def test_each_section_is_present(self, adjusted, context, heading):
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert heading in html

    def test_it_is_a_complete_html_document(self, adjusted, context):
        """A report is attached to an email or a client deliverable; one that
        needs a stylesheet from the plugin directory arrives unstyled."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert html.startswith("<!doctype html>")
        assert "<style>" in html
        assert html.rstrip().endswith("</html>")


class TestItIsDefensible:
    def test_the_uncertainty_mode_is_stated(self, adjusted, context):
        """FR-203. Presenting a heuristic figure as a rigorously propagated one
        misrepresents the quality of a survey."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert "Uncertainty" in html
        assert "rigorously" in html

    def test_an_approximate_solution_names_its_strategies(self, adjusted, context):
        """"Approximate" alone does not tell a reader *what* was approximated."""
        import dataclasses

        from geocomp.core.uncertainty import Covariance

        _network, solution = adjusted
        stations = []
        for station in solution.adjusted_stations:
            covariance = station.covariance
            if covariance is not None:
                covariance = Covariance(
                    matrix=covariance.matrix,
                    labels=covariance.labels,
                    units=covariance.units,
                    mode=UncertaintyMode.APPROXIMATE,
                    strategies=frozenset({Strategy.NOMINAL_PRECISION}),
                )
            stations.append(dataclasses.replace(station, covariance=covariance))

        approximate = dataclasses.replace(
            solution,
            uncertainty_mode=UncertaintyMode.APPROXIMATE,
            adjusted_stations=tuple(stations),
        )
        html, _omitted = _render(approximate, context)
        assert "APPROXIMATE" in html
        assert "nominal_precision" in html

    def test_the_parameter_scopes_are_shown(self, adjusted, context):
        """FR-068: the same value reached from a project override and from the
        built-in default are different statements to somebody repeating it."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert "this project" in html
        assert "stochastic.confidence_level" in html

    def test_provenance_shows_inputs_by_digest(self, adjusted, context):
        """FR-134. The digest is what turns "reproduce this" into something
        checkable: the same id with different content is a different run."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert "abc123" in html
        assert "def456" in html

    def test_uncheckable_observations_are_listed_either_way(self, adjusted, context):
        """A network full of observations with redundancy near zero passes every
        test while being wrong. A report that shows only the tests that passed
        is the one that hides it."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert "Uncheckable observations" in html

    def test_a_failed_global_test_is_explained_rather_than_declared(self, adjusted, context):
        import dataclasses

        _network, solution = adjusted
        test = solution.statistics.global_test
        failed = dataclasses.replace(
            solution,
            statistics=dataclasses.replace(
                solution.statistics,
                global_test=dataclasses.replace(test, passed=False),
            ),
        )
        html, _omitted = _render(failed, context)
        assert "FAILED" in html
        assert "the weights are wrong" in html

    def test_the_software_versions_are_recorded(self, adjusted, context):
        from geocomp.core.version import __version__

        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert __version__ in html
        assert "3.34" in html


class TestItIsDeterministic:
    def test_the_same_solution_renders_identically(self, adjusted, context):
        """NFR-007. A report whose bytes change every time cannot be diffed,
        checksummed, or attached to a claim that two runs agreed."""
        _network, solution = adjusted
        first, _ = _render(solution, context)
        second, _ = _render(solution, context)
        assert first == second

    def test_nothing_in_it_reads_the_clock(self, adjusted, context):
        """The only time in the document is the provenance's own, which belongs
        to the run rather than to the rendering."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert html.count(solution.provenance.created.isoformat()) == 1


class TestATemplateCanChangeTheLayout:
    def test_an_organisation_template_is_used(self, adjusted, context, tmp_path):
        import dataclasses

        (tmp_path / "adjustment.html").write_text(
            "<html><body><h1>Acme</h1>{{statistics}}</body></html>", encoding="utf-8"
        )
        _network, solution = adjusted
        html, _omitted = _render(
            solution, dataclasses.replace(context, template_directory=str(tmp_path))
        )
        assert "Acme" in html
        assert "Statistics" in html

    def test_the_sections_it_leaves_out_are_reported(self, adjusted, context, tmp_path):
        import dataclasses

        (tmp_path / "adjustment.html").write_text("{{statistics}}", encoding="utf-8")
        _network, solution = adjusted
        _html, omitted = _render(
            solution, dataclasses.replace(context, template_directory=str(tmp_path))
        )
        assert "reliability" in omitted
        assert "provenance" in omitted

    def test_the_report_says_which_template_produced_it(self, adjusted, context, tmp_path):
        import dataclasses

        (tmp_path / "adjustment.html").write_text("{{software}}", encoding="utf-8")
        _network, solution = adjusted
        html, _omitted = _render(
            solution, dataclasses.replace(context, template_directory=str(tmp_path))
        )
        assert str(tmp_path) in html


class TestOneDimensionIsNotAnOmission:
    def test_a_height_has_an_uncertainty_not_an_ellipse(self, adjusted, context):
        """The section says so rather than appearing empty, which would read as
        a computation that failed."""
        _network, solution = adjusted
        html, _omitted = _render(solution, context)
        assert "A one-dimensional adjustment has" in html
