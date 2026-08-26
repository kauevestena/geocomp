# SPDX-License-Identifier: GPL-2.0-or-later
"""Reference epochs (FR-105, FR-830).

``specs/04-data-model.md`` section 2.2. An epoch is a first-class value, not a
bare float, because comparing two coordinate sets is only meaningful when both
carry one.

**The rule that matters:** any operation requiring an epoch rejects a coordinate
set that has none, rather than assuming a default. A silently assumed epoch
produces a displacement that is wrong by however much the assumption missed --
with full apparent confidence, in a module whose outputs inform decisions about
dams and bridges.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from geocomp.core.errors import ValidationError

__all__ = ["Epoch"]

#: Days in a Julian year, the conversion used between an instant and a decimal
#: year. Consistent with how reference-frame epochs are quoted (2020.0).
DAYS_PER_YEAR = 365.25


@dataclass(frozen=True)
class Epoch:
    """A reference epoch: a decimal year, optionally an instant, and a label.

    Attributes:
        decimal_year: For example ``2020.0``.
        instant: The precise moment, when known. Timezone-aware and UTC.
        label: Human-readable, e.g. ``"Epoch 3 - Oct 2026"``.
    """

    decimal_year: float
    instant: datetime | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(self.decimal_year):
            raise ValidationError("epoch_not_finite", received=self.decimal_year)
        if self.instant is not None and self.instant.tzinfo is None:
            raise ValidationError(
                "epoch_instant_naive",
                received=self.instant.isoformat(),
                expected="a timezone-aware datetime; GeoComp stores UTC",
            )

    @classmethod
    def from_datetime(cls, instant: datetime, label: str = "") -> Epoch:
        """Build from an instant, deriving the decimal year."""
        if instant.tzinfo is None:
            raise ValidationError(
                "epoch_instant_naive",
                expected="a timezone-aware datetime; GeoComp stores UTC",
            )
        instant = instant.astimezone(UTC)
        year_start = datetime(instant.year, 1, 1, tzinfo=UTC)
        next_year_start = datetime(instant.year + 1, 1, 1, tzinfo=UTC)
        fraction = (instant - year_start) / (next_year_start - year_start)
        return cls(decimal_year=instant.year + fraction, instant=instant, label=label)

    @classmethod
    def from_decimal_year(cls, decimal_year: float, label: str = "") -> Epoch:
        return cls(decimal_year=decimal_year, label=label)

    def years_since(self, other: Epoch) -> float:
        """Signed interval in years, for velocity and plate-motion terms."""
        return self.decimal_year - other.decimal_year

    def __str__(self) -> str:
        return self.label or f"{self.decimal_year:.4f}"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"decimal_year": self.decimal_year}
        if self.instant is not None:
            payload["instant"] = self.instant.astimezone(UTC).isoformat()
        if self.label:
            payload["label"] = self.label
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Epoch:
        instant = payload.get("instant")
        return cls(
            decimal_year=float(payload["decimal_year"]),
            instant=datetime.fromisoformat(instant) if instant else None,
            label=payload.get("label", ""),
        )


def require_epoch(epoch: Epoch | None, *, operation: str, subject: str = "") -> Epoch:
    """Return *epoch*, or raise if it is absent.

    The single place the "never assume an epoch" rule is enforced, so that every
    call site reads the same and none of them can quietly grow a default.
    """
    if epoch is None:
        raise ValidationError(
            "epoch_required",
            operation=operation,
            subject=subject,
            expected=(
                "a reference epoch; GeoComp will not assume one, because an "
                "assumed epoch produces a confidently wrong displacement"
            ),
        )
    return epoch
