# SPDX-License-Identifier: GPL-2.0-or-later
"""Geoid and height models (FR-165, FR-804, FR-204).

``specs/17-persistence-and-interoperability.md`` section 5.5 and
``specs/13-module-integration.md`` section 3.

A geoid model relates the two height systems that geodesy measures with
different instruments::

    h = H + N

with *h* ellipsoidal, from GNSS; *H* orthometric, from levelling; and *N* the
geoid undulation. Getting this wrong is not a subtle error: across much of
Brazil *N* is tens of metres, and the resulting heights look entirely
reasonable. That is why ``specs/13`` section 3 makes combining height types
without a model a **refusal** rather than a warning, and why the model that was
used is recorded on the solution -- two solutions computed with different geoid
models are not comparable, and the record is what makes that visible.

**Three things this module insists on.**

*A model has an identity.* Id, version and coverage, all required. A geoid
undulation with no idea which model produced it cannot be compared with another,
and a monitoring series that silently changed model mid-way has a step in it
that looks like ground movement.

*A model has an uncertainty, and so does the interpolation.* FR-204. The model's
own accuracy is a property of the model and is required at construction. The
**interpolation's** uncertainty is computed from the grid itself: a bilinear
interpolant's truncation error follows the local curvature and the cell size,
and both are present in the data. That is estimation from what is there, not
invention -- and it correctly goes to zero at a grid node, which a flat "assume
a centimetre" figure would not.

*A model does not extrapolate.* Asking for an undulation outside the grid is
refused. A geoid model quoted beyond its coverage is the most confident wrong
number in geodesy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = ["Coverage", "GeoidModel", "combine_height"]


@dataclass(frozen=True)
class Coverage:
    """The area a model is valid over, in radians.

    Stored rather than derived from the grid so that a model whose grid is
    larger than its stated validity -- which happens, because grids are padded --
    refuses outside the *stated* area rather than the padded one.
    """

    south: float
    north: float
    west: float
    east: float

    def __post_init__(self) -> None:
        if not self.south < self.north:
            raise ValidationError(
                "coverage_not_ordered",
                received=[self.south, self.north],
                expected="south < north, in radians",
            )
        if not self.west < self.east:
            raise ValidationError(
                "coverage_not_ordered",
                received=[self.west, self.east],
                expected="west < east, in radians",
            )

    def contains(self, latitude: float, longitude: float) -> bool:
        return (
            self.south <= latitude <= self.north
            and self.west <= longitude <= self.east
        )

    def describe_degrees(self) -> str:
        return (
            f"{math.degrees(self.south):.4f} to {math.degrees(self.north):.4f} north, "
            f"{math.degrees(self.west):.4f} to {math.degrees(self.east):.4f} east"
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "south": self.south,
            "north": self.north,
            "west": self.west,
            "east": self.east,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, float]) -> Coverage:
        return cls(
            south=float(payload["south"]),
            north=float(payload["north"]),
            west=float(payload["west"]),
            east=float(payload["east"]),
        )


@dataclass(frozen=True)
class GeoidModel:
    """A regular grid of geoid undulations, with its identity and accuracy.

    Attributes:
        values: Undulations in metres, shape ``(rows, columns)``, row 0 at
            :attr:`coverage`'s **south** edge and column 0 at its west edge.
            South-up because that is the order a grid is naturally iterated in
            and the order the text format writes; a model whose rows are
            reversed is wrong by twice the north-south variation, which in
            Brazil is metres.
        sigma: The model's own stated accuracy, metres. **Required.** An
            undulation without an uncertainty is a number pretending to be
            exact, and in a combined adjustment the geoid is often the limiting
            factor on the height solution (``specs/13`` section 3, item 4).
    """

    id: str
    values: np.ndarray
    coverage: Coverage
    sigma: float
    name: str = ""
    version: str = ""
    source: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError(
                "geoid_without_id",
                expected="an id; a solution records which model produced it (FR-804)",
            )
        grid = np.asarray(self.values, dtype=float)
        object.__setattr__(self, "values", grid)

        if grid.ndim != 2 or grid.shape[0] < 2 or grid.shape[1] < 2:
            raise DataError(
                "geoid_grid_too_small",
                geoid=self.id,
                shape=list(grid.shape),
                expected="a two-dimensional grid of at least 2x2 nodes",
            )
        if not np.all(np.isfinite(grid)):
            raise DataError(
                "geoid_grid_not_finite",
                geoid=self.id,
                expected=(
                    "every node finite. A grid with a no-data sentinel in it "
                    "interpolates that sentinel into a plausible-looking height"
                ),
            )
        if self.sigma <= 0.0:
            raise ValidationError(
                "geoid_without_sigma",
                geoid=self.id,
                received=self.sigma,
                expected=(
                    "a positive stated accuracy in metres. A geoid model is not "
                    "exact and its uncertainty is often what limits a combined "
                    "height solution (FR-204)"
                ),
            )

    # -- geometry --------------------------------------------------------

    @property
    def rows(self) -> int:
        return int(self.values.shape[0])

    @property
    def columns(self) -> int:
        return int(self.values.shape[1])

    @property
    def spacing(self) -> tuple[float, float]:
        """Node spacing in radians, north-south then east-west."""
        return (
            (self.coverage.north - self.coverage.south) / (self.rows - 1),
            (self.coverage.east - self.coverage.west) / (self.columns - 1),
        )

    @property
    def label(self) -> str:
        base = self.name or self.id
        return f"{base} {self.version}".strip()

    # -- interpolation ---------------------------------------------------

    def undulation(self, latitude: float, longitude: float) -> Quantity:
        """The geoid undulation at a point, with its uncertainty (FR-204).

        Bilinear, which is what ``specs/17`` section 5.5 specifies as the
        default. The returned uncertainty is::

            sigma^2 = sigma_model^2 + sigma_interpolation^2

        where the second term comes from the grid's own local curvature -- see
        :meth:`interpolation_sigma`. It is tagged
        :attr:`~geocomp.core.uncertainty.Strategy.DOMINANT_TERM`, because the
        model's stated accuracy is itself a summary figure rather than a
        propagated one.

        Raises:
            ValidationError: ``geoid_outside_coverage``, naming the area. A
                geoid model quoted beyond its coverage is the most confident
                wrong number in geodesy, so this is a refusal and not a clamp.
        """
        if not self.coverage.contains(latitude, longitude):
            raise ValidationError(
                "geoid_outside_coverage",
                geoid=self.id,
                received=[math.degrees(latitude), math.degrees(longitude)],
                expected=f"a point within {self.coverage.describe_degrees()}",
            )

        row, column, weight_row, weight_column = self._cell(latitude, longitude)
        grid = self.values
        south_west = grid[row, column]
        south_east = grid[row, column + 1]
        north_west = grid[row + 1, column]
        north_east = grid[row + 1, column + 1]

        south = south_west + (south_east - south_west) * weight_column
        north = north_west + (north_east - north_west) * weight_column
        value = south + (north - south) * weight_row

        interpolation = self.interpolation_sigma(latitude, longitude)
        return Quantity.approximate(
            float(value),
            math.sqrt(self.sigma**2 + interpolation**2),
            Unit.METRE,
            Strategy.DOMINANT_TERM,
        )

    def _cell(self, latitude: float, longitude: float) -> tuple[int, int, float, float]:
        """The cell containing a point, and the fractional position within it."""
        d_lat, d_lon = self.spacing
        row = (latitude - self.coverage.south) / d_lat
        column = (longitude - self.coverage.west) / d_lon
        index_row = min(max(math.floor(row), 0), self.rows - 2)
        index_column = min(max(math.floor(column), 0), self.columns - 2)
        return index_row, index_column, row - index_row, column - index_column

    def interpolation_sigma(self, latitude: float, longitude: float) -> float:
        """The bilinear interpolation's own truncation uncertainty, in metres.

        A bilinear interpolant is exact at the nodes and departs from the true
        surface in proportion to its curvature. Along one axis the linear
        interpolation error over a cell of width *h* at fractional position *t*
        is::

            e = -(1/2) * f'' * h^2 * t * (1 - t)

        and a bilinear interpolant of a separable surface is exactly the sum of
        the two axes' linear interpolants, so the two terms add::

            sigma = (1/2) * (hx^2 * |Nxx| * tx * (1 - tx)
                             + hy^2 * |Nyy| * ty * (1 - ty))

        Both second derivatives are estimable from the grid itself, by central
        differences over the neighbouring nodes. **That is information already
        in the data**, not a figure invented to fill a field -- and it behaves
        correctly where a constant guess would not: it is zero at a node, it is
        largest at the cell centre, and it grows where the geoid curves sharply,
        which is exactly where a bilinear interpolant is worst.

        There is no cross-derivative term, and that is not an omission: a
        bilinear interpolant reproduces the ``xy`` term of a surface exactly, so
        the cross curvature contributes nothing to its error.

        **What this is and is not.** For a separable quadratic it is not a bound
        but the error itself, exactly. For a general surface it is an estimate:
        the second derivative comes from a discrete difference at the nodes, so
        where the curvature varies within a cell the figure can fall a little
        short of the true error -- a few tenths of a percent on a grid fine
        enough to be worth interpolating, converging to exact as the grid
        refines. It is a standard deviation, and it is treated as one:
        :meth:`undulation` combines it in quadrature with the model's own stated
        accuracy, which is very often the larger of the two.
        """
        row, column, weight_row, weight_column = self._cell(latitude, longitude)
        d_lat, d_lon = self.spacing

        along_lat = d_lat**2 * self._curvature(row, column, axis=0)
        along_lon = d_lon**2 * self._curvature(row, column, axis=1)

        return 0.5 * (
            along_lat * weight_row * (1.0 - weight_row)
            + along_lon * weight_column * (1.0 - weight_column)
        )

    def _curvature(self, row: int, column: int, *, axis: int) -> float:
        """The largest second derivative over a cell, per radian squared.

        The classical truncation bound takes the **maximum** curvature over the
        cell, not its value at one corner, so every grid line bounding the cell
        is examined. Sampling a single corner was wrong in a way that mattered:
        a cell with a flat edge and a sharp interior reported no interpolation
        uncertainty at all, which is precisely the cell where the interpolant is
        least trustworthy.

        Central where there is room and clamped to the interior at the edge,
        which is the honest treatment: an edge cell genuinely has less
        information about its curvature, and a grid only two nodes across an
        axis has none, so that axis contributes nothing rather than a guess.
        """
        grid = self.values
        d_lat, d_lon = self.spacing
        step, extent = (d_lat, self.rows) if axis == 0 else (d_lon, self.columns)
        if extent < 3:
            return 0.0

        varying = row if axis == 0 else column
        fixed = column if axis == 0 else row
        other_extent = self.columns if axis == 0 else self.rows

        worst = 0.0
        for offset in (0, 1):
            centre = min(max(varying + offset, 1), extent - 2)
            for across in (fixed, min(fixed + 1, other_extent - 1)):
                if axis == 0:
                    line = grid[centre - 1 : centre + 2, across]
                else:
                    line = grid[across, centre - 1 : centre + 2]
                second = (float(line[0]) - 2.0 * float(line[1]) + float(line[2])) / step**2
                worst = max(worst, abs(second))
        return worst

    # -- height systems --------------------------------------------------

    def to_orthometric(
        self, ellipsoidal: Quantity, latitude: float, longitude: float
    ) -> Quantity:
        """``H = h - N``, with the geoid's uncertainty propagated in."""
        _require_metres(ellipsoidal, "ellipsoidal height")
        return ellipsoidal - self.undulation(latitude, longitude)

    def to_ellipsoidal(
        self, orthometric: Quantity, latitude: float, longitude: float
    ) -> Quantity:
        """``h = H + N``, with the geoid's uncertainty propagated in."""
        _require_metres(orthometric, "orthometric height")
        return orthometric + self.undulation(latitude, longitude)

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "sigma": self.sigma,
            "coverage": self.coverage.to_dict(),
            "rows": self.rows,
            "columns": self.columns,
            "values": [float(value) for value in self.values.ravel()],
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GeoidModel:
        rows, columns = int(payload["rows"]), int(payload["columns"])
        return cls(
            id=payload["id"],
            values=np.asarray(payload["values"], dtype=float).reshape(rows, columns),
            coverage=Coverage.from_dict(payload["coverage"]),
            sigma=float(payload["sigma"]),
            name=payload.get("name", ""),
            version=payload.get("version", ""),
            source=payload.get("source", ""),
            meta=dict(payload.get("meta", {})),
        )


def _require_metres(quantity: Quantity, what: str) -> None:
    if quantity.unit is not Unit.METRE:
        raise ValidationError(
            "height_wrong_unit",
            parameter=what,
            received=quantity.unit.name,
            expected=Unit.METRE.name,
        )


def combine_height(
    quantity: Quantity,
    height_type: str,
    target: str,
    *,
    geoid: GeoidModel | None,
    latitude: float,
    longitude: float,
) -> tuple[Quantity, str | None]:
    """Bring a height into *target*'s system, or refuse (FR-802, FR-804).

    Returns the height and the id of the model that was applied, or ``None``
    when none was needed.

    Raises:
        ValidationError: ``incompatible_height_types`` when the two differ and
            no geoid model was supplied. **A refusal, not a warning** -- the
            resulting numbers would be wrong by the geoid undulation, tens of
            metres in much of Brazil, and would look entirely reasonable.
    """
    if height_type == target:
        return quantity, None

    if geoid is None:
        raise ValidationError(
            "incompatible_height_types",
            received=[height_type, target],
            expected=(
                "heights of the same type, or a geoid model to relate them. "
                "Differencing an ellipsoidal height against an orthometric one is "
                "wrong by the geoid undulation and produces a plausible-looking answer"
            ),
        )

    pair = (height_type, target)
    if pair == ("ellipsoidal", "orthometric"):
        return geoid.to_orthometric(quantity, latitude, longitude), geoid.id
    if pair == ("orthometric", "ellipsoidal"):
        return geoid.to_ellipsoidal(quantity, latitude, longitude), geoid.id

    raise ValidationError(
        "height_conversion_unsupported",
        received=list(pair),
        expected=(
            "a conversion between ellipsoidal and orthometric. Normal heights "
            "need a quasi-geoid rather than a geoid, which is a different model "
            "and is not treated as interchangeable here"
        ),
    )
