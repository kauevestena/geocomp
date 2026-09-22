# SPDX-License-Identifier: GPL-2.0-or-later
"""Comparing the same data processed several ways (FR-359).

``specs/11-module-gnss.md`` section 6. Two questions a surveyor actually asks —
*does this parameter matter for my data?* and, in teaching, *what does an
elevation mask actually do?* — are the same question, and neither is answered by
putting two coordinates side by side. The answer needs the **covariances**: a
3 mm difference between two solutions is large when both are good to 0.5 mm and
nothing at all when they are good to 5 mm.

**The significance test is the whole point of this module.** The difference of
two solutions of the same baseline has covariance ``Sigma_a + Sigma_b`` when the
two runs are independent, and that is the assumption under which the statistic
below is a chi-square. It is **not** true here, and the module says so rather
than quietly benefiting from the smaller variance: two configurations over the
*same observations* share almost everything, so their difference is far better
determined than independent covariances suggest. Treating them as independent is
therefore **conservative** — it inflates the difference's uncertainty and so
under-reports significance — which is the safe direction for a test whose job is
to stop someone claiming a parameter matters when it does not.

That assumption is carried on the result as
:attr:`~geocomp.core.uncertainty.Strategy.INDEPENDENCE_ASSUMED` (FR-202,
FR-203), so a report can say which simplification was made rather than merely
that the answer is approximate.

The RD-06 elevation-mask sweep is exactly this comparison run over one
parameter, and its numbers are the worked example: at masks below 25 degrees the
two days differ by 11 mm with formal sigmas near 0.5 mm, which is overwhelming;
above it they agree to 0.14 mm, which is not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.statistics.distributions import chi2_cdf, chi2_quantile
from geocomp.core.techniques.gnss.baselines import Baseline
from geocomp.core.uncertainty import Covariance, Strategy, UncertaintyMode
from geocomp.core.units import Unit

__all__ = [
    "ComparisonRow",
    "ConfigurationComparison",
    "compare_baselines",
]

#: Default confidence for the significance decision. 95% is the convention
#: ``specs/06`` section 4 uses for every other test in the project, and using a
#: different one here purely for GNSS would make two numbers in one report
#: incomparable.
DEFAULT_CONFIDENCE = 0.95


@dataclass(frozen=True)
class ComparisonRow:
    """One configuration measured against the reference configuration.

    Attributes:
        difference: This configuration's baseline minus the reference's, per
            component, in metres.
        covariance: The difference's covariance under the independence
            assumption the module docstring describes.
        statistic: ``d^T (Sigma_a + Sigma_b)^-1 d``, chi-square with 3 degrees
            of freedom under the null hypothesis that the two configurations
            determine the same vector.
        probability: ``P(chi2_3 <= statistic)`` -- how surprising this
            difference is if the two are really the same.
        is_significant: Whether *probability* exceeds the confidence asked for.
            **A false here is the informative case**: it says the parameter
            changed nothing the data can resolve.
    """

    name: str
    difference: tuple[float, float, float]
    covariance: Covariance
    statistic: float
    probability: float
    is_significant: bool
    length_difference: float

    @property
    def magnitude(self) -> float:
        """The 3D size of the difference, in metres."""
        return float(math.sqrt(sum(d * d for d in self.difference)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "difference_m": list(self.difference),
            "magnitude_m": self.magnitude,
            "length_difference_m": self.length_difference,
            "statistic": self.statistic,
            "probability": self.probability,
            "is_significant": self.is_significant,
        }


@dataclass
class ConfigurationComparison:
    """The whole side-by-side (FR-359), exportable as a table (FR-162)."""

    reference: str
    confidence: float
    rows: tuple[ComparisonRow, ...] = ()
    critical_value: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def any_significant(self) -> bool:
        return any(row.is_significant for row in self.rows)

    def table(self) -> list[list[str]]:
        """Rows for a report or a CSV export, header first.

        Formatted in millimetres: every number this comparison produces is a
        difference between two determinations of one vector, and those are
        millimetre-scale or they are a blunder.
        """
        header = ["configuration", "dX mm", "dY mm", "dZ mm", "3D mm", "chi2", "significant"]
        out = [header]
        for row in self.rows:
            out.append([
                row.name,
                *(f"{d * 1000:.3f}" for d in row.difference),
                f"{row.magnitude * 1000:.3f}",
                f"{row.statistic:.2f}",
                "yes" if row.is_significant else "no",
            ])
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "confidence": self.confidence,
            "critical_value": self.critical_value,
            "any_significant": self.any_significant,
            "rows": [row.to_dict() for row in self.rows],
        }


def compare_baselines(
    baselines: dict[str, Baseline],
    *,
    reference: str = "",
    confidence: float = DEFAULT_CONFIDENCE,
) -> ConfigurationComparison:
    """Compare several configurations' determinations of one baseline.

    Args:
        baselines: Configuration name to the baseline it produced. Every one
            must be the same station pair in the same frame -- comparing two
            different baselines is not a configuration comparison, and getting
            that wrong silently would make a meaningless table look like a
            meaningful one.
        reference: Which configuration the others are measured against. Defaults
            to the first given, which for an ordered mapping is the one the
            caller listed first.

    Raises:
        DataError: if fewer than two configurations are given, if they are not
            all the same station pair, if they do not share a frame, or if
            *reference* is not among them.
    """
    if len(baselines) < 2:
        raise DataError(
            "comparison_needs_two_configurations",
            received=len(baselines),
            expected="at least two configurations; comparing one with itself says nothing",
        )
    names = list(baselines)
    chosen = reference or names[0]
    if chosen not in baselines:
        raise DataError(
            "comparison_reference_not_found",
            received=chosen,
            expected=f"one of {names}",
        )

    pairs = {(b.base_station, b.rover_station) for b in baselines.values()}
    if len(pairs) != 1:
        raise DataError(
            "comparison_mixed_station_pairs",
            received=sorted(f"{a}-{b}" for a, b in pairs),
            expected=(
                "one station pair across every configuration. Comparing two "
                "different baselines measures the network, not the configuration"
            ),
        )
    frames = {b.frame for b in baselines.values()}
    if len(frames) != 1:
        raise DataError(
            "comparison_mixed_frames",
            received=sorted(f.value for f in frames),
            expected="one frame across every configuration",
        )

    base = baselines[chosen]
    base_values = np.array([q.value for q in base.components])
    critical = chi2_quantile(confidence, 3)

    rows: list[ComparisonRow] = []
    for name in names:
        if name == chosen:
            continue
        other = baselines[name]
        difference = np.array([q.value for q in other.components]) - base_values
        combined = base.covariance.matrix + other.covariance.matrix
        statistic = float(difference @ np.linalg.solve(combined, difference))
        probability = chi2_cdf(statistic, 3)
        rows.append(
            ComparisonRow(
                name=name,
                difference=tuple(float(d) for d in difference),  # type: ignore[arg-type]
                covariance=Covariance(
                    matrix=combined,
                    labels=base.covariance.labels,
                    units=(Unit.METRE,) * 3,
                    mode=UncertaintyMode.APPROXIMATE,
                    strategies=frozenset({Strategy.INDEPENDENCE_ASSUMED}),
                ),
                statistic=statistic,
                probability=probability,
                is_significant=statistic > critical,
                length_difference=other.length.value - base.length.value,
            )
        )

    return ConfigurationComparison(
        reference=chosen,
        confidence=confidence,
        rows=tuple(rows),
        critical_value=critical,
        meta={"station_pair": f"{base.base_station}-{base.rover_station}"},
    )
