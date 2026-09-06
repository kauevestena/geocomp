# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-12: five surveying networks, adjusted (specs/20 section 3, specs/22 section 4).

Tier 2. ``tests/data/adjust/`` holds the networks of a public dataset converted
into GeoComp's own serialisation -- the data is CC BY 4.0, the *Adjust* format
it was published in is not this repository's to carry, and
``PROVENANCE.md`` beside them records both.

What makes this corpus worth having is not that it is large but that it is the
**same ground surveyed three ways**: twelve free stations, three traverses and a
triangulateration over one set of four control points. The differences between
them are the thing, and two of them are defects in the publication that this
file pins so they cannot quietly change.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models import ConstraintMode, ConstraintSpec, ObservationType, Station
from geocomp.core.models.network import Network
from geocomp.core.models.solution import DatumDefinition

from .conftest import ADJUST_DIR, adjust_sources, requires_adjust_sources

#: Every vendored network, with what GeoComp measures on it. Written down rather
#: than computed so that a change in the adjustment core shows up here as a
#: number that moved, with the size of the move visible.
EXPECTED = {
    "free-stations": {"observations": 103, "dof": 47, "variance_factor": 0.00276817, "worst": 0.0904},
    "traverse-ac": {"observations": 13, "dof": 3, "variance_factor": 845.45, "worst": 19.66},
    "traverse-ad": {"observations": 11, "dof": 3, "variance_factor": 1195.39, "worst": 15.31},
    "traverse-bc": {"observations": 17, "dof": 3, "variance_factor": 481.852, "worst": 12.08},
    "triangulateration": {
        "observations": 109, "dof": 77, "variance_factor": 8.55469e6, "worst": 12039.5,
    },
    "triangulateration-corrected": {
        "observations": 109, "dof": 77, "variance_factor": 61.4629, "worst": 8.275,
    },
}


def load(name: str) -> tuple[dict, Network]:
    payload = json.loads((ADJUST_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return payload, Network.from_dict(payload["network"])


def solve(network: Network, *, datum=DatumDefinition.CONSTRAINED):
    return adjust(network, AdjustmentOptions(frame=Frame.PLANE_2D, datum=datum))


def worst_standardised(run) -> float:
    return max(
        abs(float(run.residuals[index])) / observation.value.std_dev
        for index, observation in enumerate(run.observations)
    )


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_network_adjusts_to_the_recorded_figures(name):
    expected = EXPECTED[name]
    _payload, network = load(name)
    assert len(network.observations) == expected["observations"]

    run = solve(network)
    assert run.converged
    assert run.degrees_of_freedom == expected["dof"]
    assert run.variance_factor_aposteriori == pytest.approx(expected["variance_factor"], rel=1e-3)
    assert worst_standardised(run) == pytest.approx(expected["worst"], rel=0.05)


def test_the_control_is_weighted_not_held():
    """The format states two standard deviations per control station, and
    holding one exactly would assert a certainty the file does not."""
    payload, network = load("free-stations")
    assert payload["control"] == ["A", "B", "C", "D"]
    for station_id in payload["control"]:
        constraint = network.stations[station_id].constraint
        assert constraint.mode is ConstraintMode.WEIGHTED
        assert constraint.covariance.std_devs()["easting"] == pytest.approx(0.010)


class TestWhatTheThreeMethodsShow:
    """The dataset's own comparison, reproduced rather than described."""

    def test_the_free_station_network_fits_its_own_uncertainties(self):
        """0.1 of a standard deviation at worst, over 103 observations."""
        _payload, network = load("free-stations")
        run = solve(network)
        assert run.variance_factor_aposteriori < 0.01
        assert worst_standardised(run) < 1.0

    def test_a_traverse_has_no_redundancy_of_its_own(self):
        """Freed of its control it adjusts with **negative** degrees of freedom.

        Thirteen observations against fourteen estimable parameters. Every one
        of a traverse's degrees of freedom comes from the weighted control, so
        its variance factor measures how far the traverse misses that control --
        not how well its observations agree among themselves. Worth pinning,
        because reading 845 as "these angles disagree with each other" is the
        obvious mistake and it is the wrong conclusion.
        """
        _payload, network = load("traverse-ac")
        for station_id, station in list(network.stations.items()):
            network.stations[station_id] = Station(
                id=station.id,
                approx_position=station.approx_position,
                constraint=ConstraintSpec(),
            )
        run = solve(network, datum=DatumDefinition.INNER_CONSTRAINT)
        assert run.degrees_of_freedom < 0


class TestTheTwoDefectsInThePublishedFiles:
    """Both are recorded in PROVENANCE.md; these keep them from drifting."""

    def test_the_rotated_round_is_still_in_the_faithful_copy(self):
        """Six angles at station 9, each carrying the next row's value.

        The faithful copy is not repaired, deliberately: it is the reference
        case for blunder detection, and a real blunder of unknown provenance is
        worth more than a synthetic one.
        """
        _payload, network = load("triangulateration")
        run = solve(network)
        at_nine = [
            index
            for index, observation in enumerate(run.observations)
            if observation.type is ObservationType.HORIZONTAL_ANGLE
            and observation.stations[0] == "9"
        ]
        assert len(at_nine) == 6
        ratios = [
            abs(float(run.residuals[index])) / run.observations[index].value.std_dev
            for index in at_nine
        ]
        assert min(ratios) > 1000.0

        # But they are **not** cleanly the worst six, and that is the lesson.
        # Least squares spreads a blunder this large across the network: the
        # largest residual elsewhere is over 8000 standard deviations, against
        # 1334 for the smallest of the six that are actually wrong. Ranking by
        # residual would accuse the wrong observations, which is why the
        # corrected copy exists rather than a "drop the worst six" rule.
        elsewhere = [
            abs(float(run.residuals[index])) / run.observations[index].value.std_dev
            for index in range(len(run.observations))
            if index not in set(at_nine)
        ]
        assert max(elsewhere) > min(ratios)

    def test_a_closure_check_cannot_see_it(self):
        """The round still sums to 360 degrees: rotating it leaves the sum alone.

        This is why the blunder survived publication, and why the corrected copy
        exists at all.
        """
        _payload, network = load("triangulateration")
        total = sum(
            observation.value.value
            for observation in network.observations.values()
            if observation.type is ObservationType.HORIZONTAL_ANGLE
            and observation.stations[0] == "9"
        )
        assert math.degrees(total) == pytest.approx(360.0, abs=1e-3)

    def test_undoing_the_rotation_recovers_a_network_that_fits(self):
        """Five orders of magnitude, which is what says the diagnosis was right."""
        _payload, faithful = load("triangulateration")
        _payload, corrected = load("triangulateration-corrected")
        before = solve(faithful).variance_factor_aposteriori
        after = solve(corrected).variance_factor_aposteriori
        assert before / after > 1e4
        assert worst_standardised(solve(corrected)) < 10

    def test_the_correction_does_not_claim_more_than_it_achieved(self):
        """It fixes the blunder. It does not make the network fit its stated
        sigmas, and PROVENANCE.md says so rather than implying otherwise."""
        _payload, corrected = load("triangulateration-corrected")
        assert solve(corrected).variance_factor_aposteriori > 10


class TestTheCorpusIsTestDataOnly:
    def test_the_plugin_package_carries_none_of_it(self):
        """``collect_files`` decides the archive's contents. Ask it directly."""
        import importlib.util

        from .conftest import REPO_ROOT

        specification = importlib.util.spec_from_file_location(
            "geocomp_build_adjust", REPO_ROOT / "scripts" / "build.py"
        )
        build = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(build)

        shipped = build.collect_files()
        assert shipped, "the build would produce an empty archive"
        corpus = ADJUST_DIR.resolve()
        offending = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in shipped
            if corpus in path.resolve().parents
        ]
        assert not offending, (
            "the Adjust corpus reached the plugin package. It is redistributed "
            "here as CC BY 4.0 test data; putting it in the artefact users "
            "install is a different question from the one PROVENANCE.md answers."
        )


@requires_adjust_sources
class TestAgainstTheOriginalFiles:
    """Read the published ``.Adat`` files when someone has them.

    Skipped by default -- they are not in the repository. Point
    ``GEOCOMP_ADJUST_DIR`` at a directory holding them and the reader is checked
    against the publication rather than against this project's own conversion.
    """

    def test_the_converted_networks_match_the_originals(self):
        from geocomp.io.adjust import read_adjust
        from scripts.convert_adjust_corpus import ACCEPT_COUNT_MISMATCH, NETWORKS

        source = adjust_sources()
        assert source is not None
        for stem, name in NETWORKS.items():
            report = read_adjust(
                Path(source) / f"{stem}.Adat",
                accept_count_mismatch=stem in ACCEPT_COUNT_MISMATCH,
            )
            _payload, vendored = load(name)
            assert set(report.network.stations) == set(vendored.stations)
            assert len(report.network.observations) == len(vendored.observations)
            for identifier, observation in report.network.observations.items():
                other = vendored.observations[identifier]
                assert observation.stations == other.stations
                assert observation.value.value == pytest.approx(other.value.value)

    def test_the_miscounted_file_is_refused_by_default(self):
        from geocomp.core.errors import DataError
        from geocomp.io.adjust import read_adjust

        source = adjust_sources()
        assert source is not None
        with pytest.raises(DataError) as caught:
            read_adjust(Path(source) / "MMEL dados.Adat")
        assert caught.value.code == "data.adjust_declared_counts_disagree"
        assert caught.value.context["declared"]["angles"] == 51
        assert caught.value.context["found"]["angles"] == 52
