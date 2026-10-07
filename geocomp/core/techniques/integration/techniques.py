# SPDX-License-Identifier: GPL-2.0-or-later
"""Which technique an observation came from (``specs/13`` sections 4 and 6).

A combined adjustment reports per technique -- residuals, redundancy, variance
components -- and needs to know which rows are whose. An observation says so
explicitly when its producer knew (``meta["technique"]``, set when technique
networks are combined); otherwise its type decides, which is right for every
type but one: a height difference may have been levelled or computed
trigonometrically, and only the producer knows which. It defaults to levelling,
and the Krumm reader and the total-station pipeline say otherwise where it is
not.
"""

from __future__ import annotations

from enum import Enum

from geocomp.core.models import Observation, ObservationType

__all__ = ["TECHNIQUE_KEY", "Technique", "technique_of"]

#: Where an observation records its technique, when its producer knew it.
TECHNIQUE_KEY = "technique"


class Technique(Enum):
    """The survey techniques a combination distinguishes, for routing and per-technique reports."""
    GNSS = "gnss"
    TOTAL_STATION = "total_station"
    LEVELLING = "levelling"
    GRAVIMETRY = "gravimetry"
    ASTRO_GEODETIC = "astro_geodetic"


_BY_TYPE = {
    ObservationType.GNSS_BASELINE: Technique.GNSS,
    ObservationType.GNSS_POINT: Technique.GNSS,
    ObservationType.ELLIPSOIDAL_HEIGHT: Technique.GNSS,
    ObservationType.DIRECTION: Technique.TOTAL_STATION,
    ObservationType.HORIZONTAL_ANGLE: Technique.TOTAL_STATION,
    ObservationType.AZIMUTH: Technique.TOTAL_STATION,
    ObservationType.ZENITH_ANGLE: Technique.TOTAL_STATION,
    ObservationType.VERTICAL_ANGLE: Technique.TOTAL_STATION,
    ObservationType.SLOPE_DISTANCE: Technique.TOTAL_STATION,
    ObservationType.HORIZONTAL_DISTANCE: Technique.TOTAL_STATION,
    ObservationType.ELLIPSOID_DISTANCE: Technique.TOTAL_STATION,
    ObservationType.HEIGHT_DIFFERENCE: Technique.LEVELLING,
    ObservationType.ORTHOMETRIC_HEIGHT: Technique.LEVELLING,
    ObservationType.GRAVITY: Technique.GRAVIMETRY,
    ObservationType.GRAVITY_DIFFERENCE: Technique.GRAVIMETRY,
    ObservationType.ASTRONOMIC_AZIMUTH: Technique.ASTRO_GEODETIC,
    ObservationType.ASTRONOMIC_LATITUDE: Technique.ASTRO_GEODETIC,
    ObservationType.ASTRONOMIC_LONGITUDE: Technique.ASTRO_GEODETIC,
    ObservationType.GEODETIC_LATITUDE: Technique.ASTRO_GEODETIC,
    ObservationType.GEODETIC_LONGITUDE: Technique.ASTRO_GEODETIC,
}


def technique_of(observation: Observation) -> str:
    """The technique's value: the one recorded on the observation, else its type's."""
    recorded = (observation.meta or {}).get(TECHNIQUE_KEY)
    if recorded:
        return Technique(recorded).value
    return _BY_TYPE[observation.type].value
