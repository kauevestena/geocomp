# SPDX-License-Identifier: GPL-2.0-or-later
"""RD-02 -- reference cases for covariance propagation.

``specs/20-testing-and-validation.md`` section 3 lists RD-02 as "worked
variance-propagation examples from Ghilani (2010) and Gemael".

**What this file actually contains, stated plainly.** These are *not*
transcriptions from those books, which are not available to the author of this
module. They are reference cases built from the geodetic operations GeoComp
performs, each validated three independent ways:

1. a **closed-form** expression derived by hand and written out in the test;
2. the module's **first-order propagation**, which is what production code runs;
3. a **Monte Carlo** simulation, which assumes nothing about the derivative at
   all and so catches a sign error that (1) and (2) could share.

Agreement between (1) and (2) checks the implementation against the formula.
Agreement of both with (3) checks the *formula itself*, which is the part a
reviewer cannot verify by reading code. That triangle is stronger evidence than
matching a printed answer, because a transcription error in a book's input value
would be invisible.

**Still outstanding**, and flagged for the project coordinator: transcribing the
actual published worked examples from Ghilani and Gemael, so GeoComp can state
agreement with the standard references by name. That needs the books. Until it
is done, RD-02 is complete as validation but incomplete as *citation*.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from geocomp.core.uncertainty import Covariance, Quantity, propagate
from geocomp.core.units import Unit

METRE, RADIAN = Unit.METRE, Unit.RADIAN

#: Fixed so results are reproducible (NFR-007).
SEED = 20260826

#: 200k samples puts the sampling error of an estimated standard deviation at
#: about 1/sqrt(2N) = 0.16%, so 1% is a comfortable tolerance that still fails
#: loudly on a wrong derivative (which would be wrong by far more).
SAMPLES = 200_000
MONTE_CARLO_TOLERANCE = 0.01


def monte_carlo_std_dev(function, mean, covariance_matrix, samples=SAMPLES):
    """Standard deviation of ``function`` by sampling the input distribution.

    Deliberately makes no use of derivatives: it is the independent check on the
    Jacobians the other two methods share.
    """
    rng = np.random.default_rng(SEED)
    draws = rng.multivariate_normal(np.asarray(mean, dtype=float), covariance_matrix, size=samples)
    return float(np.std(np.apply_along_axis(function, 1, draws), ddof=1))


class TestSlopeDistanceReduction:
    """RD-02.1 -- horizontal distance from a slope distance and a zenith angle.

    ``dh = d sin(z)``. The worked illustration in ``specs/05`` section 4.1.
    """

    D = 250.0
    Z = math.radians(87.5)
    SIGMA_D = 0.005
    SIGMA_Z = math.radians(3.0 / 3600.0)

    def analytic_std_dev(self, rho: float) -> float:
        """sigma_dh^2 = sin^2(z) sigma_d^2 + d^2cos^2(z) sigma_z^2 + 2 d sin(z)cos(z) sigma_dz."""
        return math.sqrt(
            math.sin(self.Z) ** 2 * self.SIGMA_D**2
            + (self.D * math.cos(self.Z)) ** 2 * self.SIGMA_Z**2
            + 2.0 * math.sin(self.Z) * self.D * math.cos(self.Z) * rho * self.SIGMA_D * self.SIGMA_Z
        )

    def propagated_std_dev(self, rho: float) -> float:
        off_diagonal = rho * self.SIGMA_D * self.SIGMA_Z
        covariance = Covariance(
            np.array([[self.SIGMA_D**2, off_diagonal], [off_diagonal, self.SIGMA_Z**2]]),
            ("d", "z"),
            (METRE, RADIAN),
        )
        jacobian = np.array([[math.sin(self.Z), self.D * math.cos(self.Z)]])
        return math.sqrt(propagate(jacobian, covariance, ["dh"], [METRE]).variance("dh"))

    @pytest.mark.parametrize("rho", [0.0, 0.5, -0.5, 0.9])
    def test_propagation_matches_the_closed_form(self, rho):
        assert self.propagated_std_dev(rho) == pytest.approx(self.analytic_std_dev(rho), rel=1e-13)

    @pytest.mark.parametrize("rho", [0.0, 0.5, -0.5])
    def test_both_match_monte_carlo(self, rho):
        off_diagonal = rho * self.SIGMA_D * self.SIGMA_Z
        sampled = monte_carlo_std_dev(
            lambda v: v[0] * math.sin(v[1]),
            [self.D, self.Z],
            np.array([[self.SIGMA_D**2, off_diagonal], [off_diagonal, self.SIGMA_Z**2]]),
        )
        assert self.propagated_std_dev(rho) == pytest.approx(sampled, rel=MONTE_CARLO_TOLERANCE)

    def test_the_scalar_api_reproduces_the_uncorrelated_case(self):
        """The convenient path and the rigorous path must agree where the
        convenient path's independence assumption actually holds."""
        from geocomp.core.uncertainty import sin as q_sin

        d = Quantity.from_std_dev(self.D, self.SIGMA_D, METRE)
        z = Quantity.from_std_dev(self.Z, self.SIGMA_Z, RADIAN)
        assert (d * q_sin(z)).std_dev == pytest.approx(self.analytic_std_dev(0.0), rel=1e-13)

    def test_ignoring_a_real_correlation_understates_the_uncertainty(self):
        """Why FR-208 exists. Here the effect is small, which is itself the
        point: it is small enough to go unnoticed and large enough to matter in
        a tolerance calculation."""
        assert self.propagated_std_dev(0.0) < self.propagated_std_dev(0.9)


class TestTrigonometricHeightDifference:
    """RD-02.2 -- ``dH = d cos(z) + hi - hs``, four inputs.

    The instrument and target heights are usually the dominant error source on a
    short sight, which the propagation should show.
    """

    D, Z, HI, HS = 13.204, math.radians(88.129861), 1.500, 1.495
    SIGMA_D, SIGMA_Z, SIGMA_HI, SIGMA_HS = 0.003, math.radians(5.0 / 3600.0), 0.002, 0.002

    def test_matches_the_closed_form_and_monte_carlo(self):
        variances = [self.SIGMA_D**2, self.SIGMA_Z**2, self.SIGMA_HI**2, self.SIGMA_HS**2]
        covariance = Covariance(
            np.diag(variances), ("d", "z", "hi", "hs"), (METRE, RADIAN, METRE, METRE)
        )
        jacobian = np.array([[math.cos(self.Z), -self.D * math.sin(self.Z), 1.0, -1.0]])
        propagated = math.sqrt(propagate(jacobian, covariance, ["dH"], [METRE]).variance("dH"))

        closed_form = math.sqrt(
            math.cos(self.Z) ** 2 * self.SIGMA_D**2
            + (self.D * math.sin(self.Z)) ** 2 * self.SIGMA_Z**2
            + self.SIGMA_HI**2
            + self.SIGMA_HS**2
        )
        sampled = monte_carlo_std_dev(
            lambda v: v[0] * math.cos(v[1]) + v[2] - v[3],
            [self.D, self.Z, self.HI, self.HS],
            np.diag(variances),
        )

        assert propagated == pytest.approx(closed_form, rel=1e-13)
        assert propagated == pytest.approx(sampled, rel=MONTE_CARLO_TOLERANCE)

    def test_the_height_readings_dominate_on_a_short_sight(self):
        """Not a numerical assertion about the library so much as a statement
        the library must be able to support: propagation makes the dominant
        term visible instead of assumed."""
        from_heights = math.sqrt(self.SIGMA_HI**2 + self.SIGMA_HS**2)
        from_angle = self.D * math.sin(self.Z) * self.SIGMA_Z
        from_distance = abs(math.cos(self.Z)) * self.SIGMA_D
        assert from_heights > from_angle
        assert from_heights > from_distance


class TestPolarToCartesian:
    """RD-02.3 -- a two-output case, where the *correlation created* by the
    transformation matters as much as the variances.

    Radiating a point from a station produces easting and northing that are
    correlated even when the range and bearing were independent. Anything
    downstream that differences two such points needs the full 2x2, which is why
    :class:`Covariance` exists rather than a pair of standard deviations.
    """

    R, THETA = 250.0, math.radians(37.5)
    SIGMA_R, SIGMA_THETA = 0.005, math.radians(5.0 / 3600.0)

    @pytest.fixture
    def result(self):
        covariance = Covariance(
            np.diag([self.SIGMA_R**2, self.SIGMA_THETA**2]), ("r", "theta"), (METRE, RADIAN)
        )
        jacobian = np.array(
            [
                [math.cos(self.THETA), -self.R * math.sin(self.THETA)],
                [math.sin(self.THETA), self.R * math.cos(self.THETA)],
            ]
        )
        return propagate(jacobian, covariance, ["E", "N"], [METRE, METRE])

    def test_component_variances_match_the_closed_form(self, result):
        expected_e = (
            math.cos(self.THETA) ** 2 * self.SIGMA_R**2
            + (self.R * math.sin(self.THETA)) ** 2 * self.SIGMA_THETA**2
        )
        expected_n = (
            math.sin(self.THETA) ** 2 * self.SIGMA_R**2
            + (self.R * math.cos(self.THETA)) ** 2 * self.SIGMA_THETA**2
        )
        assert result.variance("E") == pytest.approx(expected_e, rel=1e-13)
        assert result.variance("N") == pytest.approx(expected_n, rel=1e-13)

    def test_the_transformation_creates_a_correlation(self, result):
        """Independent inputs, correlated outputs. Treating E and N as
        independent downstream would be wrong even though the inputs were not."""
        assert abs(result.to_correlation()[0, 1]) > 0.1

    def test_components_match_monte_carlo(self, result):
        covariance_matrix = np.diag([self.SIGMA_R**2, self.SIGMA_THETA**2])
        for label, component in (("E", 0), ("N", 1)):
            sampled = monte_carlo_std_dev(
                lambda v, c=component: (v[0] * math.cos(v[1]), v[0] * math.sin(v[1]))[c],
                [self.R, self.THETA],
                covariance_matrix,
            )
            assert math.sqrt(result.variance(label)) == pytest.approx(
                sampled, rel=MONTE_CARLO_TOLERANCE
            )

    def test_the_output_covariance_matches_monte_carlo(self, result):
        """The off-diagonal too, not only the variances: a sign error there is
        exactly the kind of defect the Monte Carlo check exists to catch."""
        rng = np.random.default_rng(SEED)
        draws = rng.multivariate_normal(
            [self.R, self.THETA], np.diag([self.SIGMA_R**2, self.SIGMA_THETA**2]), size=SAMPLES
        )
        eastings = draws[:, 0] * np.cos(draws[:, 1])
        northings = draws[:, 0] * np.sin(draws[:, 1])
        sampled = np.cov(np.vstack([eastings, northings]))
        assert result.matrix[0, 1] == pytest.approx(sampled[0, 1], rel=0.02)


class TestLinearisationLimit:
    """RD-02.4 -- the documented limit of first-order propagation.

    ``specs/05`` section 6, limit 1: propagation linearises, so for a strongly
    non-linear function over a large input uncertainty the first-order result
    understates the true dispersion. GeoComp does not hide this; the test
    records where the method stops being adequate so the limit is a measured
    fact rather than a caveat in prose.
    """

    def test_first_order_is_excellent_for_a_small_relative_uncertainty(self):
        mean, sigma = 2.0, 0.01
        first_order = 3.0 * mean**2 * sigma
        sampled = monte_carlo_std_dev(lambda v: v[0] ** 3, [mean], np.array([[sigma**2]]))
        assert first_order == pytest.approx(sampled, rel=0.01)

    def test_first_order_understates_for_a_large_relative_uncertainty(self):
        mean, sigma = 2.0, 0.8
        first_order = 3.0 * mean**2 * sigma
        sampled = monte_carlo_std_dev(lambda v: v[0] ** 3, [mean], np.array([[sigma**2]]))
        assert first_order < sampled
        # Documented magnitude at this input, so a future change to the method
        # would be visible rather than silently shifting the limit.
        assert sampled / first_order > 1.1
