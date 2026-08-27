# SPDX-License-Identifier: GPL-2.0-or-later
"""Ellipse and vector geometry, against closed-form values.

``specs/19`` section 3 calls stating the exaggeration factor the single most
important rule in the document. Most of what is checked here is therefore not
the arithmetic -- which is a parametrised ellipse -- but that the factor cannot
be lost: it has no default, it travels with the vertices it produced, and a
factor that would *shrink* an ellipse is refused, because understating an
uncertainty is the failure the rule exists to prevent.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.models import ErrorEllipse
from geocomp.core.visualization import (
    DrawnEllipse,
    default_exaggeration,
    displacement_arrow,
    ellipse_ring,
    nice_factor,
    scale_reference_ring,
)

CENTRE = (1000.0, 2000.0)


def _circle(radius: float) -> ErrorEllipse:
    return ErrorEllipse(semi_major=radius, semi_minor=radius, orientation=0.0)


class TestTheRing:
    def test_a_circle_stays_a_circle_at_every_vertex(self):
        drawn = ellipse_ring(CENTRE, _circle(0.010), exaggeration=1.0, vertices=36)
        for east, north in drawn.ring:
            assert math.hypot(east - CENTRE[0], north - CENTRE[1]) == pytest.approx(
                0.010, abs=1e-12
            )

    def test_the_ring_closes(self):
        drawn = ellipse_ring(CENTRE, _circle(0.010), exaggeration=1.0)
        assert drawn.ring[0] == drawn.ring[-1]
        assert len(drawn.ring) == 73

    def test_the_semi_major_axis_points_along_its_azimuth(self):
        """Orientation is an azimuth from north, clockwise, as every other part
        of GeoComp reports it. A ring drawn on the mathematical convention
        instead would be mirrored about the 45 degree line -- plausible-looking
        and wrong."""
        ellipse = ErrorEllipse(
            semi_major=0.020, semi_minor=0.005, orientation=math.radians(30.0)
        )
        drawn = ellipse_ring(CENTRE, ellipse, exaggeration=1.0, vertices=360)
        furthest = max(drawn.ring, key=lambda p: math.hypot(p[0] - CENTRE[0], p[1] - CENTRE[1]))
        azimuth = math.atan2(furthest[0] - CENTRE[0], furthest[1] - CENTRE[1]) % math.pi
        assert azimuth == pytest.approx(math.radians(30.0), abs=1e-6)

    def test_the_extreme_distances_are_the_two_semi_axes(self):
        ellipse = ErrorEllipse(
            semi_major=0.020, semi_minor=0.005, orientation=math.radians(115.0)
        )
        drawn = ellipse_ring(CENTRE, ellipse, exaggeration=1.0, vertices=720)
        radii = [math.hypot(e - CENTRE[0], n - CENTRE[1]) for e, n in drawn.ring]
        assert max(radii) == pytest.approx(0.020, rel=1e-5)
        assert min(radii) == pytest.approx(0.005, rel=1e-4)

    def test_the_ring_is_centred_on_the_station(self):
        ellipse = ErrorEllipse(
            semi_major=0.020, semi_minor=0.005, orientation=math.radians(70.0)
        )
        drawn = ellipse_ring(CENTRE, ellipse, exaggeration=250.0, vertices=360)
        east = sum(point[0] for point in drawn.ring[:-1]) / (len(drawn.ring) - 1)
        north = sum(point[1] for point in drawn.ring[:-1]) / (len(drawn.ring) - 1)
        assert (east, north) == pytest.approx(CENTRE, abs=1e-9)


class TestTheExaggerationCannotBeLost:
    def test_it_has_no_default(self):
        """The signature is the enforcement. A call site that forgets the factor
        does not silently draw at 1:1 -- it does not run."""
        with pytest.raises(TypeError):
            ellipse_ring(CENTRE, _circle(0.010))  # type: ignore[call-arg]

    def test_it_travels_with_the_vertices_it_produced(self):
        drawn = ellipse_ring(CENTRE, _circle(0.010), exaggeration=500.0)
        assert isinstance(drawn, DrawnEllipse)
        assert drawn.exaggeration == 500.0
        assert drawn.is_exaggerated

    def test_the_true_semi_axes_survive_alongside_the_drawn_ones(self):
        """A layer has to be able to report what the ellipse actually is, not
        only what was drawn, or the attribute table repeats the exaggeration."""
        drawn = ellipse_ring(CENTRE, _circle(0.010), exaggeration=500.0)
        assert drawn.semi_major == 0.010
        radii = [math.hypot(e - CENTRE[0], n - CENTRE[1]) for e, n in drawn.ring]
        assert max(radii) == pytest.approx(5.0, rel=1e-9)

    @pytest.mark.parametrize("bad", (0.0, -1.0, float("nan"), float("inf")))
    def test_a_factor_that_is_not_a_positive_number_is_refused(self, bad):
        with pytest.raises(ValidationError):
            ellipse_ring(CENTRE, _circle(0.010), exaggeration=bad)

    def test_a_vector_needs_one_too(self):
        with pytest.raises(TypeError):
            displacement_arrow(CENTRE, (0.01, 0.02))  # type: ignore[call-arg]


class TestTheFirstView:
    def test_the_largest_ellipse_lands_near_the_target_fraction(self):
        factor = default_exaggeration((2000.0, 1000.0), [0.010, 0.004])
        drawn_diameter = 2.0 * 0.010 * factor
        assert drawn_diameter <= 0.05 * 1000.0
        assert drawn_diameter > 0.5 * 0.05 * 1000.0

    def test_the_factor_is_a_number_a_legend_can_state(self):
        factor = default_exaggeration((2000.0, 1000.0), [0.010, 0.004])
        assert factor in {
            1.0,
            2.0,
            5.0,
            10.0,
            20.0,
            50.0,
            100.0,
            200.0,
            500.0,
            1000.0,
            2000.0,
            5000.0,
        }

    def test_the_shorter_side_of_the_extent_governs(self):
        """Scaling off the longer side would run the ellipses off the top and
        bottom of a wide view."""
        wide = default_exaggeration((10000.0, 1000.0), [0.010])
        square = default_exaggeration((1000.0, 1000.0), [0.010])
        assert wide == square

    def test_ellipses_that_are_already_visible_are_not_shrunk(self):
        """Never below 1. Shrinking an ellipse understates the uncertainty,
        which is exactly the misrepresentation this module exists to prevent."""
        assert default_exaggeration((100.0, 100.0), [50.0]) == 1.0

    def test_a_design_with_no_uncertainty_yet_asks_for_no_exaggeration(self):
        assert default_exaggeration((1000.0, 1000.0), []) == 1.0
        assert default_exaggeration((1000.0, 1000.0), [0.0, 0.0]) == 1.0

    @pytest.mark.parametrize("extent", ((0.0, 100.0), (100.0, 0.0), (-1.0, 100.0)))
    def test_an_extent_with_no_area_is_refused(self, extent):
        with pytest.raises(ValidationError):
            default_exaggeration(extent, [0.010])

    @pytest.mark.parametrize(
        ("value", "expected"),
        (
            (1.0, 1.0),
            (1.9, 1.0),
            (2.0, 2.0),
            (4.999, 2.0),
            (7.5, 5.0),
            (9.99, 5.0),
            (10.0, 10.0),
            (487.3, 200.0),
            (0.4, 1.0),
        ),
    )
    def test_the_rounding_goes_down_to_a_one_two_five_value(self, value, expected):
        assert nice_factor(value) == expected


class TestVectorsAndTheScaleReference:
    def test_a_vector_tip_is_the_exaggerated_displacement(self):
        start, tip = displacement_arrow((10.0, 20.0), (0.003, -0.004), exaggeration=1000.0)
        assert start == (10.0, 20.0)
        assert tip == pytest.approx((13.0, 16.0))

    def test_the_scale_reference_is_a_circle_of_the_stated_true_size(self):
        """Drawn at the same factor as everything else, or it is not a
        reference for anything."""
        drawn = scale_reference_ring(CENTRE, 0.010, exaggeration=500.0)
        radii = [math.hypot(e - CENTRE[0], n - CENTRE[1]) for e, n in drawn.ring]
        assert max(radii) == pytest.approx(5.0, rel=1e-9)
        assert drawn.semi_major == drawn.semi_minor == 0.010
        assert drawn.exaggeration == 500.0

    def test_a_reference_of_no_size_is_refused(self):
        with pytest.raises(ValidationError):
            scale_reference_ring(CENTRE, 0.0, exaggeration=500.0)
