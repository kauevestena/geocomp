# SPDX-License-Identifier: GPL-2.0-or-later
"""Where an observation's sigma comes from (FR-064).

``specs/05-uncertainty-and-covariance.md`` section 5 fixes the precedence:

1. **Stated in the data.** An imported per-observation sigma is used as given.
2. **Instrument model.** From the instrument profile (FR-061, FR-069).
3. **Type default.** From Global Settings (FR-064).
4. **Refuse.**

Step 4 is the one that matters, and it is why this module exists rather than a
dictionary lookup with a fallback. **GeoComp does not invent a sigma.** A
fabricated weight does not fail; it silently corrupts the variance factor, every
standardised residual, every error ellipse and every significance decision
downstream. Refusing is the only safe answer, and the refusal names the
observation and lists the three ways to fix it.

The resolved value carries :class:`SigmaSource`, so a report can say where each
weight came from -- which is the difference between a defensible adjustment and
a plausible one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.level import LevelProfile
from geocomp.core.instruments.profiles import InstrumentProfile
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import Unit

__all__ = ["SigmaSource", "StochasticDefaults", "resolve_sigma"]


class SigmaSource(Enum):
    """Which step of the precedence supplied a sigma.

    Recorded rather than inferred: a network where every weight came from a type
    default is a different object from one where every weight came from a
    calibrated instrument, and the statistics do not distinguish them.
    """

    STATED = "stated"
    INSTRUMENT = "instrument"
    TYPE_DEFAULT = "type_default"


#: Observation kinds this module knows how to weight. Strings rather than the
#: ``ObservationType`` enum because pre-processing works on readings that are not
#: yet observations -- a raw circle reading has no ``Observation`` around it.
DIRECTION = "direction"
ZENITH_ANGLE = "zenith_angle"
SLOPE_DISTANCE = "slope_distance"
HORIZONTAL_DISTANCE = "horizontal_distance"
HORIZONTAL_ANGLE = "horizontal_angle"
HEIGHT_DIFFERENCE = "height_difference"
INSTRUMENT_HEIGHT = "instrument_height"
TARGET_HEIGHT = "target_height"
#: One reading of a levelling staff, and the sight distance to it. Added in
#: phase P4: the same precedence governs them, and a levelling importer that
#: invented a reading sigma would corrupt the network exactly as a total-station
#: one would.
STAFF_READING = "staff_reading"
SIGHT_DISTANCE = "sight_distance"

_ANGULAR = frozenset({DIRECTION, ZENITH_ANGLE, HORIZONTAL_ANGLE})
_LINEAR = frozenset(
    {
        SLOPE_DISTANCE,
        HORIZONTAL_DISTANCE,
        HEIGHT_DIFFERENCE,
        INSTRUMENT_HEIGHT,
        TARGET_HEIGHT,
        STAFF_READING,
        SIGHT_DISTANCE,
    }
)


@dataclass(frozen=True)
class StochasticDefaults:
    """Per-type default standard deviations, from Global Settings (FR-064).

    Empty by default, and deliberately so: an empty set of defaults means step 3
    of the precedence supplies nothing and the resolution refuses, which is the
    behaviour a fresh installation should have. Filling this in is a decision
    the user makes knowingly.
    """

    values: dict[str, float] = field(default_factory=dict)

    def sigma(self, kind: str) -> float | None:
        return self.values.get(kind)

    def with_default(self, kind: str, sigma: float) -> StochasticDefaults:
        if sigma < 0.0:
            raise ValidationError(
                "default_sigma_negative",
                kind=kind,
                received=sigma,
                expected="a non-negative standard deviation",
            )
        return StochasticDefaults(values={**self.values, kind: sigma})


def unit_for(kind: str) -> Unit:
    """The dimension a given observation kind is measured in."""
    if kind in _ANGULAR:
        return Unit.RADIAN
    if kind in _LINEAR:
        return Unit.METRE
    raise ValidationError(
        "unknown_observation_kind",
        kind=kind,
        expected=f"one of: {', '.join(sorted(_ANGULAR | _LINEAR))}",
    )


def resolve_sigma(
    kind: str,
    value: float,
    *,
    stated: float | None = None,
    instrument: InstrumentProfile | None = None,
    level: LevelProfile | None = None,
    defaults: StochasticDefaults | None = None,
    sets: int = 1,
    observation_id: str = "",
) -> tuple[Quantity, SigmaSource]:
    """Attach an uncertainty to a reading, by the precedence above.

    Args:
        kind: One of the module-level observation-kind constants.
        value: The reading itself, in SI. Some models depend on it -- an EDM's
            sigma grows with the distance being measured.
        stated: A per-observation sigma from the imported data, if any.
        instrument: The instrument profile, if one is available.
        level: The level profile, for the levelling kinds. A separate argument
            rather than a union because the two records answer different
            questions and an operation that has one rarely has the other; both
            feed the same step 2 of the precedence.
        defaults: The Global Settings type defaults, if any.
        sets: Number of independent sets averaged; angular precision improves
            as ``1 / sqrt(sets)``.
        observation_id: Used only to make a refusal name the offending record.

    Returns:
        The reading as a :class:`Quantity`, and which step supplied its sigma.

    Raises:
        ValidationError: ``missing_stochastic_model`` when no step yields a
            value. The message lists all three ways to supply one.
    """
    unit = unit_for(kind)
    if sets < 1:
        raise ValidationError(
            "non_positive_set_count", received=sets, expected="at least one set"
        )
    scale = sets**0.5

    if stated is not None:
        if stated < 0.0:
            raise ValidationError(
                "stated_sigma_negative",
                observation=observation_id,
                received=stated,
                expected="a non-negative standard deviation",
            )
        return Quantity.from_std_dev(value, stated, unit), SigmaSource.STATED

    if instrument is not None or level is not None:
        sigma = None
        if instrument is not None:
            sigma = _from_instrument(kind, value, instrument)
        if sigma is None and level is not None:
            sigma = _from_level(kind, level)
        if sigma is not None:
            # APPROXIMATE, not RIGOROUS: specs/05 section 2.3 lists
            # NOMINAL_PRECISION among the approximate strategies, and says there
            # is no partial credit -- one approximate input makes the result
            # approximate. A manufacturer's brochure figure is not a measurement.
            return (
                Quantity.approximate(
                    value, sigma / scale, unit, Strategy.NOMINAL_PRECISION
                ),
                SigmaSource.INSTRUMENT,
            )

    if defaults is not None:
        sigma = defaults.sigma(kind)
        if sigma is not None:
            return (
                Quantity.approximate(value, sigma / scale, unit, Strategy.TYPE_DEFAULT),
                SigmaSource.TYPE_DEFAULT,
            )

    raise ValidationError(
        "missing_stochastic_model",
        observation=observation_id,
        kind=kind,
        expected=(
            "a standard deviation from one of: the imported data, an instrument profile, "
            "or the per-type defaults in Global Settings. GeoComp does not invent one, "
            "because a fabricated weight corrupts every statistic computed from it"
        ),
    )


def _from_instrument(kind: str, value: float, instrument: InstrumentProfile) -> float | None:
    """The instrument model's sigma for *kind*, or ``None`` if it has none.

    ``None`` rather than zero: an instrument profile that says nothing about
    height differences has not claimed they are perfect.
    """
    if kind == DIRECTION:
        return instrument.sigma_direction
    if kind == HORIZONTAL_ANGLE:
        # An angle is the difference of two directions from one setup. The two
        # share the setup's orientation, which cancels, but their pointing
        # errors do not -- hence sqrt(2), not 2 and not 1.
        return instrument.sigma_direction * (2.0**0.5)
    if kind == ZENITH_ANGLE:
        return instrument.zenith_sigma(value)
    if kind in (SLOPE_DISTANCE, HORIZONTAL_DISTANCE):
        return instrument.distance_sigma(value)
    if kind == INSTRUMENT_HEIGHT:
        return instrument.sigma_instrument_height
    if kind == TARGET_HEIGHT:
        return instrument.sigma_target_height
    return None


def _from_level(kind: str, level: LevelProfile) -> float | None:
    """The level profile's sigma for *kind*, or ``None`` if it has none.

    Height differences are deliberately absent. A levelling height difference is
    weighted by line length or by setup count
    (:mod:`geocomp.core.adjustment.weighting`), and neither is derivable from the
    height difference itself -- returning some other sigma here would answer a
    question this function was not asked.
    """
    if kind == STAFF_READING:
        return level.reading_sigma
    if kind == SIGHT_DISTANCE:
        stadia = level.stadia_sigma
        if stadia is None:
            return None
        # Distance is factor * (upper - lower); two independent readings, so the
        # interval's sigma is sqrt(2) times one reading's, then scaled.
        return level.stadia_factor * stadia * (2.0**0.5)
    return None
