# SPDX-License-Identifier: GPL-2.0-or-later
"""Geoid models: interpolation, its uncertainty, and the height-type conversion.

FR-165, FR-804 and FR-204; ``specs/13-module-integration.md`` section 3 and
``specs/17-persistence-and-interoperability.md`` section 5.5.

Two things here are worth more than the arithmetic checks. The first is that
the bilinear interpolation's own uncertainty is *derived from the grid*, so a
point sitting on a node gets zero and a point in a sharply curving cell gets
more -- a constant guess would get both wrong. The second is that the
conversion between height systems is refused without a model, because a
difference of ellipsoidal and orthometric heights is wrong by tens of metres in
Brazil and looks entirely reasonable.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.geoid import Coverage, GeoidModel, combine_height
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

#: A one-degree cell in southern Brazil, where the undulation really is around
#: -5 m and changing by metres over the area.
COVERAGE = Coverage(
    south=math.radians(-26.0),
    north=math.radians(-24.0),
    west=math.radians(-51.0),
    east=math.radians(-49.0),
)


def planar_model(**kwargs: object) -> GeoidModel:
    """A grid that is exactly a plane, so bilinear interpolation is exact."""
    rows, columns = 3, 3
    grid = np.array(
        [[2.0 + 0.5 * row + 0.25 * column for column in range(columns)] for row in range(rows)]
    )
    defaults: dict[str, object] = {
        "id": "PLANE-1",
        "values": grid,
        "coverage": COVERAGE,
        "sigma": 0.05,
        "name": "Test plane",
        "version": "2020",
    }
    defaults.update(kwargs)
    return GeoidModel(**defaults)  # type: ignore[arg-type]


def curved_model(curvature: float = 4.0) -> GeoidModel:
    """A grid with real curvature, so the truncation bound is not zero."""
    grid = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, curvature, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )
    return GeoidModel(id="BUMP-1", values=grid, coverage=COVERAGE, sigma=0.02)


# -- identity and validation ---------------------------------------------


def test_model_requires_an_id() -> None:
    """FR-804: a solution records *which* model produced its heights."""
    with pytest.raises(ValidationError) as excinfo:
        planar_model(id="  ")
    assert excinfo.value.code == "validation.geoid_without_id"


def test_model_requires_a_stated_accuracy() -> None:
    """FR-204: in a combined adjustment the geoid is often the limiting factor."""
    with pytest.raises(ValidationError) as excinfo:
        planar_model(sigma=0.0)
    assert excinfo.value.code == "validation.geoid_without_sigma"


def test_grid_smaller_than_a_cell_is_refused() -> None:
    with pytest.raises(DataError) as excinfo:
        planar_model(values=np.array([[1.0, 2.0]]))
    assert excinfo.value.code == "data.geoid_grid_too_small"


def test_no_data_sentinel_is_refused() -> None:
    """A NaN node interpolates into a plausible-looking height."""
    grid = np.array([[1.0, 2.0, 3.0], [4.0, math.nan, 6.0], [7.0, 8.0, 9.0]])
    with pytest.raises(DataError) as excinfo:
        planar_model(values=grid)
    assert excinfo.value.code == "data.geoid_grid_not_finite"


def test_coverage_must_be_ordered() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Coverage(south=0.1, north=0.0, west=0.0, east=0.1)
    assert excinfo.value.code == "validation.coverage_not_ordered"


def test_label_carries_name_and_version() -> None:
    assert planar_model().label == "Test plane 2020"
    assert planar_model(name="", version="").label == "PLANE-1"


# -- interpolation --------------------------------------------------------


def test_grid_is_south_up() -> None:
    """Row 0 is the southern edge; a reversed grid is wrong by the whole range."""
    model = planar_model()
    south = model.undulation(COVERAGE.south, COVERAGE.west)
    north = model.undulation(COVERAGE.north, COVERAGE.west)
    assert south.value == pytest.approx(2.0)
    assert north.value == pytest.approx(3.0)


def test_nodes_are_reproduced_exactly() -> None:
    model = planar_model()
    d_lat, d_lon = model.spacing
    for row in range(model.rows):
        for column in range(model.columns):
            latitude = COVERAGE.south + row * d_lat
            longitude = COVERAGE.west + column * d_lon
            assert model.undulation(latitude, longitude).value == pytest.approx(
                float(model.values[row, column])
            )


def test_bilinear_is_exact_on_a_plane() -> None:
    """The interpolant reproduces a bilinear surface, by construction."""
    model = planar_model()
    d_lat, d_lon = model.spacing
    latitude = COVERAGE.south + 1.37 * d_lat
    longitude = COVERAGE.west + 0.62 * d_lon
    expected = 2.0 + 0.5 * 1.37 + 0.25 * 0.62
    assert model.undulation(latitude, longitude).value == pytest.approx(expected)


def test_bilinear_matches_an_independent_formulation() -> None:
    """Checked against the tensor-product form, not against itself."""
    rng = np.random.default_rng(20260828)
    grid = rng.normal(-5.0, 1.5, size=(5, 4))
    coverage = COVERAGE
    model = GeoidModel(id="RNG-1", values=grid, coverage=coverage, sigma=0.03)
    d_lat, d_lon = model.spacing

    for _ in range(60):
        u = rng.uniform(0.0, model.rows - 1)
        v = rng.uniform(0.0, model.columns - 1)
        row, column = int(u), int(v)
        fu, fv = u - row, v - column
        expected = (
            grid[row, column] * (1 - fu) * (1 - fv)
            + grid[row, column + 1] * (1 - fu) * fv
            + grid[row + 1, column] * fu * (1 - fv)
            + grid[row + 1, column + 1] * fu * fv
        )
        got = model.undulation(coverage.south + u * d_lat, coverage.west + v * d_lon)
        assert got.value == pytest.approx(float(expected))


def test_outside_coverage_is_refused_not_clamped() -> None:
    """A geoid quoted beyond its coverage is the most confident wrong number."""
    model = planar_model()
    with pytest.raises(ValidationError) as excinfo:
        model.undulation(COVERAGE.north + 1e-4, COVERAGE.west)
    assert excinfo.value.code == "validation.geoid_outside_coverage"
    assert "north" in str(excinfo.value)


# -- interpolation uncertainty (FR-204) -----------------------------------


def test_interpolation_uncertainty_is_zero_at_a_node() -> None:
    """The interpolant is exact at the nodes, so it contributes nothing there."""
    model = curved_model()
    d_lat, d_lon = model.spacing
    assert model.interpolation_sigma(
        COVERAGE.south + d_lat, COVERAGE.west + d_lon
    ) == pytest.approx(0.0, abs=1e-12)
    assert model.undulation(
        COVERAGE.south + d_lat, COVERAGE.west + d_lon
    ).std_dev == pytest.approx(model.sigma)


def test_interpolation_uncertainty_is_zero_on_a_plane() -> None:
    """No curvature, no truncation error -- whatever the point."""
    model = planar_model()
    d_lat, d_lon = model.spacing
    assert model.interpolation_sigma(
        COVERAGE.south + 0.5 * d_lat, COVERAGE.west + 0.5 * d_lon
    ) == pytest.approx(0.0)


def test_interpolation_uncertainty_grows_with_curvature() -> None:
    """It is estimated from the grid, so a sharper geoid gets a larger figure."""
    d_lat, d_lon = curved_model().spacing
    middle = (COVERAGE.south + 0.5 * d_lat, COVERAGE.west + 0.5 * d_lon)
    gentle = curved_model(curvature=1.0).interpolation_sigma(*middle)
    sharp = curved_model(curvature=4.0).interpolation_sigma(*middle)
    assert gentle > 0.0
    assert sharp == pytest.approx(4.0 * gentle)


def test_a_flat_cell_beside_a_sharp_one_is_not_reported_as_certain() -> None:
    """The curvature is the cell's worst, not the value at one of its corners.

    This is the case that caught a real defect: the south-west cell of the bump
    grid has an entirely flat western edge, so a curvature read at that corner
    is zero and the cell is reported as interpolating perfectly -- when it is
    the cell straddling the bump and is where the interpolant is least
    trustworthy.
    """
    model = curved_model()
    d_lat, d_lon = model.spacing
    centre = model.interpolation_sigma(COVERAGE.south + 0.5 * d_lat, COVERAGE.west + 0.5 * d_lon)
    assert centre > 0.0


def _quadratic_model(a: float, b: float, rows: int = 9, columns: int = 9) -> tuple[GeoidModel, Any]:
    """A separable quadratic surface sampled onto a grid, with its analytic form."""
    coverage = COVERAGE
    d_lat = (coverage.north - coverage.south) / (rows - 1)
    d_lon = (coverage.east - coverage.west) / (columns - 1)

    def surface(latitude: float, longitude: float) -> float:
        x = latitude - coverage.south
        y = longitude - coverage.west
        return -5.0 + a * x * x + b * y * y

    grid = np.array(
        [
            [surface(coverage.south + r * d_lat, coverage.west + c * d_lon) for c in range(columns)]
            for r in range(rows)
        ]
    )
    return GeoidModel(id="QUAD-1", values=grid, coverage=coverage, sigma=1e-12), surface


def test_interpolation_uncertainty_matches_the_real_error_exactly() -> None:
    """For a separable quadratic the estimate is not a bound but the error itself.

    A bilinear interpolant of ``g(x) + p(y)`` is exactly the sum of the two
    axes' linear interpolants, so its error is the sum of the two linear
    truncation errors -- which is precisely what
    :meth:`GeoidModel.interpolation_sigma` computes. Agreement to machine
    precision at arbitrary points inside the cells, not merely at their centres,
    is a much sharper check than "the bound was not exceeded".
    """
    model, surface = _quadratic_model(a=3.0, b=2.0)
    rng = np.random.default_rng(4171)
    d_lat, d_lon = model.spacing

    largest = 0.0
    for _ in range(200):
        u = rng.uniform(0.0, model.rows - 1)
        v = rng.uniform(0.0, model.columns - 1)
        latitude = COVERAGE.south + u * d_lat
        longitude = COVERAGE.west + v * d_lon
        error = abs(model.undulation(latitude, longitude).value - surface(latitude, longitude))
        assert model.interpolation_sigma(latitude, longitude) == pytest.approx(error, abs=1e-12)
        largest = max(largest, error)
    assert largest > 1e-6  # the surface really is curved, so the test has teeth


def test_interpolation_uncertainty_tracks_a_surface_it_cannot_match_exactly() -> None:
    """On a surface with varying curvature it is an estimate, and a close one.

    The second derivative is a discrete difference at the nodes, so where the
    curvature varies *within* a cell the figure can fall slightly short of the
    true error. This test measures by how much rather than asserting a bound
    that does not hold: the estimate stays within a few percent of the truth in
    the middle of the distribution and never drops materially below it, and it
    converges as the grid refines. Claiming a strict upper bound here would be
    claiming something the arithmetic does not deliver.
    """
    coverage = COVERAGE
    span_lat = coverage.north - coverage.south
    span_lon = coverage.east - coverage.west

    def surface(latitude: float, longitude: float) -> float:
        x = (latitude - coverage.south) / span_lat
        y = (longitude - coverage.west) / span_lon
        return -5.0 + 2.0 * math.sin(2.0 * x) + 1.5 * math.cos(1.5 * y) + 0.7 * x * y

    def ratios(size: int) -> np.ndarray:
        d_lat, d_lon = span_lat / (size - 1), span_lon / (size - 1)
        grid = np.array(
            [
                [
                    surface(coverage.south + r * d_lat, coverage.west + c * d_lon)
                    for c in range(size)
                ]
                for r in range(size)
            ]
        )
        model = GeoidModel(id="WAVY-1", values=grid, coverage=coverage, sigma=1e-12)
        rng = np.random.default_rng(90125)
        found = []
        for _ in range(2000):
            u, v = rng.uniform(0.0, size - 1), rng.uniform(0.0, size - 1)
            latitude, longitude = coverage.south + u * d_lat, coverage.west + v * d_lon
            error = abs(model.undulation(latitude, longitude).value - surface(latitude, longitude))
            if error > 1e-9:
                found.append(model.interpolation_sigma(latitude, longitude) / error)
        return np.array(found)

    coarse, fine = ratios(5), ratios(21)

    # Never materially short of the truth, on either grid.
    assert coarse.min() > 0.9
    assert fine.min() > 0.99
    # Typically within a few percent, and closer on the finer grid.
    assert abs(float(np.median(coarse)) - 1.0) < 0.2
    assert abs(float(np.median(fine)) - 1.0) < 0.05
    assert abs(float(np.median(fine)) - 1.0) < abs(float(np.median(coarse)) - 1.0)


def test_undulation_combines_both_uncertainties_in_quadrature() -> None:
    model = curved_model()
    d_lat, d_lon = model.spacing
    latitude, longitude = COVERAGE.south + 0.5 * d_lat, COVERAGE.west + 0.5 * d_lon
    interpolation = model.interpolation_sigma(latitude, longitude)
    quantity = model.undulation(latitude, longitude)
    assert quantity.std_dev == pytest.approx(math.hypot(model.sigma, interpolation))
    assert quantity.unit is Unit.METRE
    assert Strategy.DOMINANT_TERM in quantity.strategies


# -- height systems -------------------------------------------------------


def test_orthometric_from_ellipsoidal() -> None:
    """H = h - N, with the geoid's uncertainty propagated in (FR-204)."""
    model = planar_model()
    height = Quantity.approximate(812.345, 0.012, Unit.METRE, Strategy.NOMINAL_PRECISION)
    result = model.to_orthometric(height, COVERAGE.south, COVERAGE.west)
    assert result.value == pytest.approx(812.345 - 2.0)
    assert result.std_dev == pytest.approx(math.hypot(0.012, 0.05))


def test_ellipsoidal_from_orthometric_is_the_inverse() -> None:
    model = planar_model()
    d_lat, d_lon = model.spacing
    latitude, longitude = COVERAGE.south + 0.4 * d_lat, COVERAGE.west + 0.9 * d_lon
    height = Quantity.approximate(812.345, 0.012, Unit.METRE, Strategy.NOMINAL_PRECISION)
    there = model.to_orthometric(height, latitude, longitude)
    back = model.to_ellipsoidal(there, latitude, longitude)
    assert back.value == pytest.approx(height.value)
    # The geoid's uncertainty enters twice, because the round trip really did
    # use the model twice; it does not cancel.
    assert back.std_dev > height.std_dev


def test_height_in_the_wrong_unit_is_refused() -> None:
    model = planar_model()
    with pytest.raises(ValidationError) as excinfo:
        angle = Quantity.approximate(1.0, 0.1, Unit.RADIAN, Strategy.NOMINAL_PRECISION)
        model.to_orthometric(angle, 0.0, 0.0)
    assert excinfo.value.code == "validation.height_wrong_unit"


# -- combine_height (FR-802, FR-804) --------------------------------------


def test_same_type_needs_no_model() -> None:
    height = Quantity.approximate(100.0, 0.01, Unit.METRE, Strategy.NOMINAL_PRECISION)
    result, applied = combine_height(
        height, "orthometric", "orthometric", geoid=None, latitude=0.0, longitude=0.0
    )
    assert result is height
    assert applied is None


def test_mixed_types_without_a_model_are_refused() -> None:
    """A refusal, not a warning: the error is metres and looks reasonable."""
    height = Quantity.approximate(100.0, 0.01, Unit.METRE, Strategy.NOMINAL_PRECISION)
    with pytest.raises(ValidationError) as excinfo:
        combine_height(
            height, "ellipsoidal", "orthometric", geoid=None, latitude=0.0, longitude=0.0
        )
    assert excinfo.value.code == "validation.incompatible_height_types"


def test_mixed_types_with_a_model_convert_and_name_it() -> None:
    model = planar_model()
    height = Quantity.approximate(812.345, 0.012, Unit.METRE, Strategy.NOMINAL_PRECISION)
    result, applied = combine_height(
        height,
        "ellipsoidal",
        "orthometric",
        geoid=model,
        latitude=COVERAGE.south,
        longitude=COVERAGE.west,
    )
    assert result.value == pytest.approx(812.345 - 2.0)
    assert applied == "PLANE-1"


def test_normal_heights_are_not_treated_as_orthometric() -> None:
    """A quasi-geoid is a different model; interchanging them is not offered."""
    model = planar_model()
    with pytest.raises(ValidationError) as excinfo:
        combine_height(
            Quantity.approximate(100.0, 0.01, Unit.METRE, Strategy.NOMINAL_PRECISION),
            "normal",
            "ellipsoidal",
            geoid=model,
            latitude=COVERAGE.south,
            longitude=COVERAGE.west,
        )
    assert excinfo.value.code == "validation.height_conversion_unsupported"


# -- serialisation --------------------------------------------------------


def test_round_trip_through_a_dictionary() -> None:
    model = curved_model()
    restored = GeoidModel.from_dict(model.to_dict())
    assert restored.id == model.id
    assert restored.sigma == model.sigma
    assert restored.coverage == model.coverage
    np.testing.assert_array_equal(restored.values, model.values)
