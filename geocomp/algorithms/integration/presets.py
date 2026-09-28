# SPDX-License-Identifier: GPL-2.0-or-later
"""The four Integration menu items (``specs/13`` section 1, FR-800 to FR-803).

Presets over :class:`~geocomp.algorithms.integration.common._CombinedAdjustmentAlgorithm`:
which networks each takes, whether it combines geocentrically or in the inputs'
own system, and what each needs said about it.
"""

from __future__ import annotations

from geocomp.algorithms.integration.common import (
    GNSS,
    LEVELLING,
    TOTAL_STATION,
    _CombinedAdjustmentAlgorithm,
)

__all__ = [
    "GnssLevelAlgorithm",
    "GnssTotalStationAlgorithm",
    "MultipleTechniquesAlgorithm",
    "TotalStationLevelAlgorithm",
]


class GnssTotalStationAlgorithm(_CombinedAdjustmentAlgorithm):
    """FR-800."""

    TR_CONTEXT = "CombinedAdjustmentAlgorithm"
    INPUTS = ((GNSS, True), (TOTAL_STATION, True))
    GEOCENTRIC = True

    def displayName(self) -> str:
        return self.tr("GNSS and total station")

    def shortDescription(self) -> str:
        return self.tr("Adjust GNSS baselines and total-station observations together.")

    def help_body(self) -> str:
        return (
            self.tr(
                "<p>Combines a GNSS network and a total-station network in one geocentric "
                "frame at one epoch, each observation at its own station's vertical.</p>"
                "<p>The total-station network may be in a UTM or Transverse Mercator "
                "projection of SIRGAS 2000 or an ITRF: its starting coordinates are read "
                "through it. Its measurements belong to no frame and are not transformed. "
                "Hold control through the GNSS input: a point held in grid coordinates is "
                "refused, because its height is not the ellipsoidal one.</p>"
                "<p>A geoid model is needed only if orthometric heights take part.</p>"
            )
            + self.common_help()
        )


class TotalStationLevelAlgorithm(_CombinedAdjustmentAlgorithm):
    """FR-801."""

    TR_CONTEXT = "CombinedAdjustmentAlgorithm"
    INPUTS = ((TOTAL_STATION, True), (LEVELLING, True))
    GEOCENTRIC = False

    def displayName(self) -> str:
        return self.tr("Total station and level")

    def shortDescription(self) -> str:
        return self.tr("Adjust total-station and levelling observations together.")

    def help_body(self) -> str:
        return (
            self.tr(
                "<p>Combines a total-station network and a levelling network in the "
                "total station's own coordinate reference system. Nothing is transformed: "
                "neither technique measures a position in a frame.</p>"
                "<p>When the total-station network holds only height differences, the "
                "combination is adjusted in heights alone; otherwise in three dimensions, "
                "where a mark reached only by levelling is refused by name, because nothing "
                "places it horizontally.</p>"
                "<p>A benchmark held by the levelling network and a control point held by the "
                "total station are the same hold if they agree in height.</p>"
            )
            + self.common_help()
        )


class GnssLevelAlgorithm(_CombinedAdjustmentAlgorithm):
    """FR-802: the height-systems case, so the geoid is required."""

    TR_CONTEXT = "CombinedAdjustmentAlgorithm"
    INPUTS = ((GNSS, True), (LEVELLING, True))
    GEOCENTRIC = True
    GEOID_REQUIRED = True

    def displayName(self) -> str:
        return self.tr("GNSS and level")

    def shortDescription(self) -> str:
        return self.tr("Adjust GNSS baselines and levelled height differences together, through a geoid.")

    def help_body(self) -> str:
        return (
            self.tr(
                "<p>GNSS gives ellipsoidal heights and levelling orthometric ones; they are "
                "related by the geoid, h = H + N. The geoid model is <b>required</b>, is "
                "named in the solution and the report, and its uncertainty takes part: each "
                "station's undulation is estimated with the model as its prior.</p>"
                "<p>The <b>geoid residuals</b> in the report are the survey's test of the model "
                "over the project area.</p>"
                "<p>A levelling benchmark enters as an orthometric height observation with its "
                "uncertainty; one held exactly is refused, because it would make the geoid "
                "exact there. Every levelled mark must also be occupied by GNSS, or nothing "
                "places it horizontally.</p>"
            )
            + self.common_help()
        )


class MultipleTechniquesAlgorithm(_CombinedAdjustmentAlgorithm):
    """FR-803: three or more techniques, gravity among them if given."""

    TR_CONTEXT = "CombinedAdjustmentAlgorithm"
    INPUTS = ((GNSS, False), (TOTAL_STATION, False), (LEVELLING, False))
    GEOCENTRIC = None
    GRAVITY = True
    MINIMUM_TECHNIQUES = 3

    def displayName(self) -> str:
        return self.tr("Multiple techniques")

    def shortDescription(self) -> str:
        return self.tr("Adjust three or more techniques together, gravity included.")

    def help_body(self) -> str:
        return (
            self.tr(
                "<p>Three or more of GNSS, total station, levelling and gravimetry. With GNSS "
                "the combination is geocentric; without it, in the inputs' own system.</p>"
                "<p><b>Gravity is adjusted beside the geometry</b>, by the in-house core with "
                "its drift model: nothing in the combination relates gravity to position, so "
                "adjusting it inside would give the same answer. It is never dropped, and "
                "asking for DynAdjust with gravity present keeps the whole combination "
                "in-house, with the reason in the report.</p>"
            )
            + self.common_help()
        )
