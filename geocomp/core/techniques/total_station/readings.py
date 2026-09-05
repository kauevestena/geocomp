# SPDX-License-Identifier: GPL-2.0-or-later
"""What comes out of a field book, before anything has been reduced.

``specs/09-module-total-station.md`` section 5 gives RD-01's layout as the
reference case, and this module is its in-memory form.

Every reading is a :class:`~geocomp.core.uncertainty.Quantity` from the moment
it enters GeoComp (FR-200). That is a deliberate choice about *where* the
stochastic model is applied: at import, by
:func:`~geocomp.core.instruments.stochastic.resolve_sigma`, rather than somewhere
downstream. A raw circle reading with no sigma is a value that could still
silently reach an adjustment, and the whole point of the rule is that it cannot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from geocomp.core.errors import ValidationError
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = ["Face", "FacePair", "FaceReading", "Setup"]


class Face(Enum):
    """Which face of the instrument a pointing was taken on.

    ``DIRECT`` is *posição directa* (PD), ``REVERSE`` is *posição inversa* (PI),
    matching RD-01's ``pos`` column. English ids, because they are stored.
    """

    DIRECT = "direct"
    REVERSE = "reverse"

    @property
    def is_direct(self) -> bool:
        return self is Face.DIRECT


@dataclass(frozen=True)
class FaceReading:
    """One pointing at one target, on one face.

    Attributes:
        target: Station or detail point sighted.
        face: Which face.
        horizontal: Horizontal circle reading, radians, as read. **Not** a
            direction: the circle's zero is arbitrary until the setup is
            oriented.
        zenith: Zenith angle, radians, measured from the upward vertical.
        distance: Slope distance, metres, or ``None`` for an angles-only
            pointing.
        target_height: Height of the target above its station mark, metres.
        set_number: Which set of repetitions this pointing belongs to.
    """

    target: str
    face: Face
    horizontal: Quantity
    zenith: Quantity
    distance: Quantity | None = None
    target_height: Quantity | None = None
    set_number: int = 1
    #: Free-form, carried through from the source record so an importer can
    #: round-trip a column it did not interpret rather than discarding it
    #: (``specs/09`` section 5).
    extra: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_unit(self.horizontal, Unit.RADIAN, "horizontal")
        _require_unit(self.zenith, Unit.RADIAN, "zenith")
        if self.distance is not None:
            _require_unit(self.distance, Unit.METRE, "distance")
        if self.target_height is not None:
            _require_unit(self.target_height, Unit.METRE, "target_height")
        if not self.target:
            raise ValidationError(
                "reading_without_target",
                expected="the identifier of the station or point sighted",
            )
        if self.set_number < 1:
            raise ValidationError(
                "non_positive_set_number", received=self.set_number, expected="at least 1"
            )


@dataclass(frozen=True)
class FacePair:
    """A direct and a reverse pointing at the same target.

    The pair is the unit of reduction: combining the two faces is what cancels
    collimation, horizontal-axis tilt and vertical index error to first order,
    and it is also what makes the diagnostics of ``specs/09`` section 2.1
    available at all.
    """

    direct: FaceReading
    reverse: FaceReading

    def __post_init__(self) -> None:
        if self.direct.face is not Face.DIRECT or self.reverse.face is not Face.REVERSE:
            raise ValidationError(
                "face_pair_wrong_faces",
                received=[self.direct.face.value, self.reverse.face.value],
                expected="one direct and one reverse pointing, in that order",
            )
        if self.direct.target != self.reverse.target:
            raise ValidationError(
                "face_pair_different_targets",
                received=[self.direct.target, self.reverse.target],
                expected="both faces pointing at the same target",
            )

    @property
    def target(self) -> str:
        return self.direct.target

    @property
    def has_distance(self) -> bool:
        return self.direct.distance is not None and self.reverse.distance is not None


@dataclass
class Setup:
    """One instrument station: everything observed without moving the tripod.

    A setup is the correlation unit for directions (they share the setup's
    unknown orientation) and the unit over which the instrumental diagnostics
    should be stable -- a collimation that drifts within one setup means the
    instrument moved, and that is worth saying.

    Attributes:
        station: The occupied station.
        instrument_height: Height of the trunnion axis above the mark, metres.
        instrument_id / reflector_id: Which profiles apply.
        pairs: Face pairs observed from here, in observation order.
        singles: Pointings with no opposite face. Kept separate because they
            need the instrument's collimation and index corrections applied
            explicitly -- the pair would have cancelled them.
    """

    station: str
    instrument_height: Quantity
    pairs: list[FacePair] = field(default_factory=list)
    singles: list[FaceReading] = field(default_factory=list)
    instrument_id: str | None = None
    reflector_id: str | None = None
    #: Atmospheric conditions at the setup, when they were recorded.
    temperature: Quantity | None = None
    pressure: Quantity | None = None
    humidity: Quantity | None = None

    def __post_init__(self) -> None:
        _require_unit(self.instrument_height, Unit.METRE, "instrument_height")
        if not self.station:
            raise ValidationError(
                "setup_without_station", expected="the identifier of the occupied station"
            )

    @property
    def targets(self) -> tuple[str, ...]:
        """Every target sighted from this setup, in order, without duplicates."""
        seen: dict[str, None] = {}
        for pair in self.pairs:
            seen.setdefault(pair.target, None)
        for single in self.singles:
            seen.setdefault(single.target, None)
        return tuple(seen)

    @property
    def is_empty(self) -> bool:
        return not self.pairs and not self.singles


def _require_unit(quantity: Quantity, unit: Unit, name: str) -> None:
    if quantity.unit is not unit:
        raise ValidationError(
            "reading_wrong_unit", parameter=name, received=quantity.unit.name, expected=unit.name
        )
