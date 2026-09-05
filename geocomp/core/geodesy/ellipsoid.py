# SPDX-License-Identifier: GPL-2.0-or-later
"""Reference ellipsoids, and the radii of curvature everything else needs.

``specs/09-module-total-station.md`` section 2.6 and ``specs/07-engine-dynadjust.md``
section 4.4. Until now GeoComp had no ellipsoid at all: the distance reductions
in ``techniques/total_station/reductions.py`` take a *mean Earth radius* and a
*given* point scale factor, which is enough to shorten a distance and not enough
to say where a station is. That gap is why a projected network cannot reach
DynAdjust (``specs/07`` section 4.4) and why four of Krumm's Leick networks are
refused (``specs/22`` section 2.2).

**An ellipsoid is defined by two numbers and everything else is derived from
them.** Which two matters: *a* and 1/*f* are the defining constants of GRS80 and
WGS84, and *b* is a derived quantity that no standard states independently. This
module therefore stores *a* and the inverse flattening exactly as published and
computes the rest, rather than carrying a table of pre-rounded derived values
that would disagree with itself in the eleventh digit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from geocomp.core.errors import ValidationError

__all__ = ["ELLIPSOIDS", "Ellipsoid", "ellipsoid_by_name"]


@dataclass(frozen=True)
class Ellipsoid:
    """A biaxial reference ellipsoid, from its two defining constants.

    Attributes:
        name: As the defining authority writes it, because it is what gets
            recorded in provenance and shown to the user.
        semi_major_axis: *a*, in metres.
        inverse_flattening: 1/*f*. A sphere is ``math.inf``, which the
            derived quantities handle without a special case.
        authority: Where the two numbers come from, so a wrong one can be
            traced rather than argued about.
    """

    name: str
    semi_major_axis: float
    inverse_flattening: float
    authority: str = ""

    def __post_init__(self) -> None:
        if self.semi_major_axis <= 0.0:
            raise ValidationError(
                "ellipsoid_semi_major_axis_not_positive",
                ellipsoid=self.name,
                received=self.semi_major_axis,
            )
        if self.inverse_flattening <= 1.0:
            raise ValidationError(
                "ellipsoid_inverse_flattening_invalid",
                ellipsoid=self.name,
                received=self.inverse_flattening,
                expected="1/f greater than 1; a sphere is math.inf, not 0",
            )

    # -- derived constants -------------------------------------------------

    @property
    def flattening(self) -> float:
        """*f* = (a - b) / a."""
        return 1.0 / self.inverse_flattening

    @property
    def semi_minor_axis(self) -> float:
        """*b* = a(1 - f). Derived, never stored: no standard defines it."""
        return self.semi_major_axis * (1.0 - self.flattening)

    @property
    def eccentricity_squared(self) -> float:
        """*e²* = 2f - f², written this way rather than as 1 - b²/a².

        The two are equal in exact arithmetic and not in floating point: for
        GRS80, ``1 - b**2 / a**2`` loses about four significant figures to
        cancellation, because b²/a² is 0.9933 and the difference from 1 is what
        is wanted.
        """
        f = self.flattening
        return f * (2.0 - f)

    @property
    def second_eccentricity_squared(self) -> float:
        """*e'²* = e² / (1 - e²), which is what Bowring's latitude uses."""
        e2 = self.eccentricity_squared
        return e2 / (1.0 - e2)

    @property
    def third_flattening(self) -> float:
        """*n* = f / (2 - f), the series parameter of the Krüger projection."""
        f = self.flattening
        return f / (2.0 - f)

    @property
    def mean_radius(self) -> float:
        """*R₁* = (2a + b)/3, the IUGG arithmetic mean."""
        return (2.0 * self.semi_major_axis + self.semi_minor_axis) / 3.0

    # -- radii of curvature ------------------------------------------------

    def prime_vertical_radius(self, latitude: float) -> float:
        """*N*, the radius of curvature in the prime vertical, in metres.

        Args:
            latitude: Geodetic latitude, in **radians**.
        """
        sin_latitude = math.sin(latitude)
        return self.semi_major_axis / math.sqrt(
            1.0 - self.eccentricity_squared * sin_latitude * sin_latitude
        )

    def meridian_radius(self, latitude: float) -> float:
        """*M*, the radius of curvature in the meridian, in metres."""
        e2 = self.eccentricity_squared
        sin_latitude = math.sin(latitude)
        w = 1.0 - e2 * sin_latitude * sin_latitude
        return self.semi_major_axis * (1.0 - e2) / (w * math.sqrt(w))

    def gaussian_radius(self, latitude: float) -> float:
        """*R* = sqrt(MN), the mean radius of curvature at a point.

        This is the radius a distance reduction should use, rather than a global
        mean: at 30 degrees latitude on GRS80 the two differ by about 6 km, which
        is 1 part in a thousand of the reduction.
        """
        return math.sqrt(self.meridian_radius(latitude) * self.prime_vertical_radius(latitude))


#: The ellipsoids GeoComp knows, by the name its authority uses.
#:
#: Every pair is the **defining** pair, transcribed from the authority rather
#: than back-computed from a published *b*. SIRGAS2000 and GDA2020 are not
#: separate ellipsoids: both are realisations on GRS80, and giving each its own
#: entry with its own rounding is how two frames come to disagree by a
#: millimetre for no physical reason.
ELLIPSOIDS: dict[str, Ellipsoid] = {
    "GRS80": Ellipsoid(
        "GRS80", 6378137.0, 298.257222101,
        "IUGG 1980; the ellipsoid of SIRGAS2000, GDA2020, ETRS89 and NAD83",
    ),
    "WGS84": Ellipsoid(
        "WGS84", 6378137.0, 298.257223563,
        "NIMA TR8350.2. Differs from GRS80 in 1/f only, by 1.6e-9 -- about "
        "0.1 mm in the semi-minor axis",
    ),
    "GRS67": Ellipsoid("GRS67", 6378160.0, 298.247167427, "IUGG 1967"),
    "SAD69": Ellipsoid(
        "SAD69", 6378160.0, 298.25,
        "South American Datum 1969: GRS67's axis with 1/f rounded to 298.25. "
        "Brazil's legal datum before SIRGAS2000",
    ),
    "International1924": Ellipsoid(
        "International1924", 6378388.0, 297.0, "Hayford 1909, adopted IUGG 1924",
    ),
    "Bessel1841": Ellipsoid("Bessel1841", 6377397.155, 299.1528128, "Bessel 1841"),
    "Clarke1866": Ellipsoid("Clarke1866", 6378206.4, 294.9786982, "Clarke 1866; NAD27"),
    "Airy1830": Ellipsoid(
        "Airy1830", 6377563.396, 299.3249646,
        "Airy 1830; OSGB36, and the ellipsoid of the worked example in EPSG "
        "Guidance Note 7-2",
    ),
}


def ellipsoid_by_name(name: str) -> Ellipsoid:
    """Look one up, case-insensitively and ignoring spaces and hyphens.

    ``GRS 80``, ``grs-80`` and ``GRS80`` are the same ellipsoid written three
    ways, and a caller reading a CRS string will meet all three.
    """
    def normalise(text: str) -> str:
        return text.replace(" ", "").replace("-", "").replace("_", "").upper()

    wanted = normalise(name)
    for key, ellipsoid in ELLIPSOIDS.items():
        if normalise(key) == wanted:
            return ellipsoid
    raise ValidationError(
        "ellipsoid_unknown",
        received=name,
        expected=sorted(ELLIPSOIDS),
        hint=(
            "GeoComp carries the ellipsoids its supported frames use, not a "
            "projection database; an unlisted one has to be added deliberately, "
            "with its defining constants and their source"
        ),
    )
