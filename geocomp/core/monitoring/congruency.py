# SPDX-License-Identifier: GPL-2.0-or-later
"""Has anything moved, and what (``specs/14`` sections 4.1, 5 and 6; FR-834 to FR-836).

The analysis follows the congruency approach common to the Hannover,
Karlsruhe and Delft methods (Pelzer 1971, Niemeier 1981, Caspary 2000): the
difference of the two epochs is referred to a **datum defined by the reference
block** through an S-transformation, the block is tested for congruency --
have its stations moved relative to one another? -- and only then are the
object points' displacements and their significance read off.

**The S-transformation** takes the difference vector and its cofactor into the
datum in which the reference stations' displacements are smallest in the
least-squares sense, over the datum parameters the network leaves undetermined:

    S = I - G (G^T W G)^-1 G^T W

with ``G`` the datum basis (translations; a rotation about the vertical for a
terrestrial network; a scale where asked) and ``W`` selecting the reference
components. Nothing held or free in either epoch survives it as an artefact:
both epochs' datum choices are replaced by the one the block defines.

**The congruency test.** Over a set of stations, ``Omega = d^T Q^+ d`` in that
set's own datum, ``h`` its rank. With the pooled variance factor over ``f``
degrees of freedom ``Omega / (h sigma^2)`` is F(h, f) under "nothing moved";
with none (``f = 0``) the a-priori factor stands and ``Omega`` is chi-square(h).

**A block that fails is not analysed on** (criterion 5). :func:`check_reference`
localises it step by step -- at each step the station whose removal reduces
``Omega`` most, with every step's statistic and every station's contribution
recorded -- and :func:`analyse` refuses, naming the implicated stations. Finding
"the subset that makes the answer come out stable" automatically is a real
methodological hazard (section 5, item 4), so the stable subset is proposed,
never adopted: the user re-runs the analysis with the reference block they
accept.

**Not significant is not zero** (section 4.1). Every displacement is reported
with its value, its covariance, its confidence ellipse and its test; one that
does not pass is labelled *not significant* and keeps its value.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.models import ErrorEllipse, TestResult
from geocomp.core.monitoring.compare import Comparison
from geocomp.core.statistics.distributions import chi2_quantile, f_quantile
from geocomp.core.statistics.ellipses import error_ellipse

__all__ = [
    "DATUM_CHOICES",
    "Congruency",
    "DeformationAnalysis",
    "Displacement",
    "LocalisationStep",
    "ReferenceCheck",
    "analyse",
    "check_reference",
    "congruency",
    "datum_basis",
    "default_datum",
    "s_matrix",
    "s_transform",
]

TRANSLATION = "translation"
TRANSLATION_ROTATION = "translation_rotation"
SIMILARITY = "similarity"
DATUM_CHOICES = (TRANSLATION, TRANSLATION_ROTATION, SIMILARITY)

SIGNIFICANT = "significant"
NOT_SIGNIFICANT = "not significant"

#: Singular values below this fraction of the largest are the datum's null space.
_RANK_TOLERANCE = 1e-9


@dataclass(frozen=True)
class Congruency:
    """One congruency test over a set of stations, in that set's own datum."""

    stations: tuple[str, ...]
    omega: float
    rank: int
    test: TestResult

    @property
    def passed(self) -> bool:
        """Whether the global congruency test passed: no significant deformation detected."""
        return self.test.passed


@dataclass(frozen=True)
class LocalisationStep:
    """One step of localising an unstable block: the test on what was left,
    each station's share of ``Omega``, and the one removed."""

    test: Congruency
    contributions: dict[str, float]
    removed: str


@dataclass(frozen=True)
class ReferenceCheck:
    """The reference block's congruency, and where it fails, why.

    Attributes:
        test: The test on the block as declared.
        steps: The localisation, empty when the block passed.
        stable: What remained congruent -- a proposal, never adopted silently.
    """

    test: Congruency
    steps: tuple[LocalisationStep, ...] = ()
    stable: tuple[str, ...] = ()
    final: Congruency | None = None

    @property
    def passed(self) -> bool:
        """Whether the reference block passed its congruency test as declared."""
        return self.test.passed

    @property
    def implicated(self) -> tuple[str, ...]:
        """The reference stations the localisation removed, one per step."""
        return tuple(step.removed for step in self.steps)


@dataclass(frozen=True)
class Displacement:
    """One station's displacement in the reference block's datum (FR-833, FR-834).

    Attributes:
        values: Per component, metres; reported whatever the test decides.
        covariance: Of the displacement, pooled variance factor times cofactor.
        test: The joint test of all components; ``passed`` means *no motion
            detected*, never *no motion*.
        horizontal, vertical: The component tests, when the station has both.
        ellipse: The horizontal displacement's confidence ellipse, drawn at the
            displacement's tip so a reader sees whether zero lies inside it.
    """

    station_id: str
    role: str
    components: tuple[str, ...]
    values: tuple[float, ...]
    covariance: np.ndarray
    test: TestResult
    horizontal: TestResult | None = None
    vertical: TestResult | None = None
    ellipse: ErrorEllipse | None = None

    @property
    def significant(self) -> bool:
        """Whether the displacement's test rejected 'no movement'."""
        return not self.test.passed

    @property
    def decision(self) -> str:
        """The test's decision in the words a report and an export use."""
        return SIGNIFICANT if self.significant else NOT_SIGNIFICANT

    @property
    def std_devs(self) -> tuple[float, ...]:
        """The standard deviation of each component, from the covariance's diagonal."""
        return tuple(float(np.sqrt(max(v, 0.0))) for v in np.diag(self.covariance))

    def component(self, name: str) -> float | None:
        """The displacement in component *name*, or ``None`` when it was not compared in it."""
        return self.values[self.components.index(name)] if name in self.components else None

    @property
    def horizontal_magnitude(self) -> float | None:
        """The length of the horizontal part; ``None`` without both ``e`` and ``n``."""
        e, n = self.component("e"), self.component("n")
        return None if e is None or n is None else float(np.hypot(e, n))

    @property
    def vertical_magnitude(self) -> float | None:
        """The absolute vertical displacement, ``u`` or ``h``; ``None`` when neither was compared.
        """
        up = self.component("u") if "u" in self.components else self.component("h")
        return None if up is None else abs(up)

    @property
    def magnitude(self) -> float:
        """The length of the whole displacement vector."""
        return float(np.linalg.norm(self.values))


@dataclass(frozen=True)
class DeformationAnalysis:
    """Two epochs analysed against a stable reference block (FR-833 to FR-836)."""

    comparison: Comparison
    reference: tuple[str, ...]
    objects: tuple[str, ...]
    datum: str
    confidence: float
    reference_check: ReferenceCheck
    global_test: Congruency
    displacements: tuple[Displacement, ...]
    difference: np.ndarray
    cofactor: np.ndarray

    def displacement(self, station_id: str) -> Displacement:
        """The displacement of *station_id*, refusing a station that was not compared."""
        for displacement in self.displacements:
            if displacement.station_id == station_id:
                return displacement
        raise ValidationError(
            "monitoring_station_not_compared", stations=[station_id], expected=list(self.comparison.stations)
        )

    @property
    def significant(self) -> tuple[str, ...]:
        """The stations whose displacement is significant, in comparison order."""
        return tuple(d.station_id for d in self.displacements if d.significant)


# -- the datum --------------------------------------------------------------


def default_datum(comparison: Comparison) -> str:
    """What a network of this kind leaves undetermined.

    Heights: a shift. Terrestrial plan or 3D: the translations and a rotation
    about the vertical -- distances fix the scale, zenith angles the vertical.
    Geocentric (GNSS): the translations; vectors fix orientation and scale.
    """
    if comparison.components == ("h",) or comparison.geocentric:
        return TRANSLATION
    return TRANSLATION_ROTATION


def datum_basis(comparison: Comparison, datum: str | None = None) -> np.ndarray:
    """``G``: one column per datum parameter over every compared component."""
    datum = datum or default_datum(comparison)
    if datum not in DATUM_CHOICES:
        raise ValidationError("monitoring_datum_unknown", received=datum, expected=list(DATUM_CHOICES))
    components = comparison.components
    k, n = len(components), len(comparison.stations)
    columns = []
    for c in range(k):
        column = np.zeros(n * k)
        column[c::k] = 1.0
        columns.append(column)
    horizontal = "e" in components and "n" in components
    if datum != TRANSLATION:
        if not horizontal:
            raise ValidationError(
                "monitoring_datum_needs_plan",
                received=datum,
                expected="a translation datum for a network of heights",
            )
        centred = comparison.coordinates - comparison.coordinates.mean(axis=0)
        scale = float(np.sqrt((centred**2).sum(axis=1).mean())) or 1.0
        e, north = components.index("e"), components.index("n")
        rotation = np.zeros(n * k)
        rotation[e::k] = -centred[:, 1] / scale
        rotation[north::k] = centred[:, 0] / scale
        columns.append(rotation)
        if datum == SIMILARITY:
            dilation = np.zeros(n * k)
            dilation[e::k] = centred[:, 0] / scale
            dilation[north::k] = centred[:, 1] / scale
            columns.append(dilation)
    return np.column_stack(columns)


def s_matrix(comparison: Comparison, reference: Sequence[str], datum: str | None = None) -> np.ndarray:
    """``S``, taking any vector over the compared components into the datum
    *reference* defines."""
    basis = datum_basis(comparison, datum)
    weight = np.zeros(len(comparison.difference))
    weight[comparison.indices(reference)] = 1.0
    normal = basis.T @ (weight[:, None] * basis)
    if np.linalg.matrix_rank(normal) < normal.shape[0]:
        raise ValidationError(
            "monitoring_reference_block_too_small",
            stations=list(reference),
            datum=datum or default_datum(comparison),
            expected=(
                "enough reference stations to define the datum: one for a shift, two "
                "for a shift and a rotation"
            ),
        )
    return np.eye(len(weight)) - basis @ np.linalg.solve(normal, basis.T * weight)


def s_transform(comparison: Comparison, reference: Sequence[str], datum: str | None = None):
    """The difference and its cofactor in the datum *reference* defines."""
    transform = s_matrix(comparison, reference, datum)
    return transform @ comparison.difference, transform @ comparison.cofactor @ transform.T


# -- tests ------------------------------------------------------------------


def congruency(
    comparison: Comparison,
    stations: Sequence[str],
    *,
    datum: str | None = None,
    confidence: float = 0.95,
) -> Congruency:
    """Have *stations* moved relative to one another?"""
    stations = tuple(stations)
    difference, cofactor = s_transform(comparison, stations, datum)
    rows = comparison.indices(stations)
    omega, rank = _quadratic(difference[rows], cofactor[np.ix_(rows, rows)])
    test = _test(
        f"congruency of {len(stations)} station(s)",
        omega,
        rank,
        comparison,
        confidence,
    )
    return Congruency(stations=stations, omega=omega, rank=rank, test=test)


def check_reference(
    comparison: Comparison,
    reference: Sequence[str],
    *,
    datum: str | None = None,
    confidence: float = 0.95,
) -> ReferenceCheck:
    """Test the reference block and, if it fails, localise the failure.

    At each step the station whose removal reduces ``Omega`` most is set
    aside, until what remains is congruent or too small to define the datum.
    Every step is kept.
    """
    current = list(dict.fromkeys(reference))
    first = congruency(comparison, current, datum=datum, confidence=confidence)
    if first.passed:
        return ReferenceCheck(test=first, stable=tuple(current), final=first)
    steps: list[LocalisationStep] = []
    test = first
    while not test.passed:
        contributions: dict[str, float] = {}
        for station in current:
            rest = [s for s in current if s != station]
            try:
                remaining = congruency(comparison, rest, datum=datum, confidence=confidence)
            except ValidationError:
                continue
            if remaining.rank < 1:
                continue
            contributions[station] = test.omega - remaining.omega
        if not contributions:
            break
        worst = max(contributions, key=lambda s: contributions[s])
        steps.append(LocalisationStep(test=test, contributions=contributions, removed=worst))
        current.remove(worst)
        test = congruency(comparison, current, datum=datum, confidence=confidence)
    return ReferenceCheck(
        test=first,
        steps=tuple(steps),
        stable=tuple(current) if test.passed else (),
        final=test,
    )


def analyse(
    comparison: Comparison,
    reference: Sequence[str],
    *,
    objects: Sequence[str] | None = None,
    datum: str | None = None,
    confidence: float = 0.95,
) -> DeformationAnalysis:
    """The displacements of every compared station, against *reference*.

    Raises:
        ValidationError: ``monitoring_reference_block_unstable`` naming the
            stations the localisation implicates, with its steps -- the analysis
            does not proceed on a block that has itself moved.
    """
    reference = tuple(dict.fromkeys(reference))
    if not reference:
        raise ValidationError(
            "monitoring_reference_block_empty",
            expected="the stations assumed stable, against which movement is measured",
        )
    check = check_reference(comparison, reference, datum=datum, confidence=confidence)
    if not check.passed:
        raise ValidationError(
            "monitoring_reference_block_unstable",
            stations=list(check.implicated),
            statistic=round(check.test.test.statistic, 4),
            critical=round(check.test.test.critical_high or 0.0, 4),
            stable=list(check.stable),
            steps=[
                {
                    "stations": list(step.test.stations),
                    "statistic": step.test.test.statistic,
                    "removed": step.removed,
                    "contributions": step.contributions,
                }
                for step in check.steps
            ],
            expected=(
                "a reference block whose stations have not moved relative to one another; "
                "the ones named moved -- analyse again with them set among the object points"
            ),
        )
    objects = (
        tuple(objects) if objects is not None else tuple(s for s in comparison.stations if s not in reference)
    )
    difference, cofactor = s_transform(comparison, reference, datum)
    displacements = tuple(
        _displacement(
            comparison,
            station,
            difference,
            cofactor,
            confidence,
            "reference" if station in reference else "object",
        )
        for station in comparison.stations
        if station in reference or station in objects
    )
    return DeformationAnalysis(
        comparison=comparison,
        reference=reference,
        objects=objects,
        datum=datum or default_datum(comparison),
        confidence=confidence,
        reference_check=check,
        global_test=congruency(comparison, comparison.stations, datum=datum, confidence=confidence),
        displacements=displacements,
        difference=difference,
        cofactor=cofactor,
    )


# -- internals ---------------------------------------------------------------


def _quadratic(vector: np.ndarray, cofactor: np.ndarray) -> tuple[float, int]:
    """``v^T Q^+ v`` and the rank of ``Q``, the datum's null space excluded."""
    u, singular, _ = np.linalg.svd(cofactor, hermitian=True)
    if singular.size == 0 or singular[0] <= 0.0:
        return 0.0, 0
    keep = singular > _RANK_TOLERANCE * singular[0]
    projected = u[:, keep].T @ vector
    return float(np.sum(projected**2 / singular[keep])), int(keep.sum())


def _test(name: str, omega: float, rank: int, comparison: Comparison, confidence: float) -> TestResult:
    """Omega against F(h, f) with the pooled factor, or chi-square(h) without one."""
    if rank < 1:
        return TestResult(
            name=name,
            statistic=0.0,
            critical_high=None,
            confidence=confidence,
            passed=True,
            note="nothing left to test: the stations only define the datum",
        )
    f = comparison.degrees_of_freedom
    if f > 0:
        statistic = omega / (rank * comparison.variance_factor)
        critical = f_quantile(confidence, rank, f)
        note = f"F({rank}, {f}) with the pooled variance factor {comparison.variance_factor:.4g}"
    else:
        statistic = omega
        critical = chi2_quantile(confidence, rank)
        note = f"chi-square({rank}) with the a-priori variance factor"
    return TestResult(
        name=name,
        statistic=statistic,
        critical_high=critical,
        confidence=confidence,
        passed=statistic <= critical,
        note=note,
    )


def _displacement(comparison, station, difference, cofactor, confidence, role) -> Displacement:
    rows = comparison.indices([station])
    vector = difference[rows]
    q = cofactor[np.ix_(rows, rows)]
    components = comparison.components
    omega, rank = _quadratic(vector, q)
    test = _test(f"displacement of {station}", omega, rank, comparison, confidence)
    horizontal = vertical = None
    ellipse = None
    if "e" in components and "n" in components:
        plan = [components.index("e"), components.index("n")]
        h_omega, h_rank = _quadratic(vector[plan], q[np.ix_(plan, plan)])
        horizontal = _test(f"horizontal displacement of {station}", h_omega, h_rank, comparison, confidence)
        scaled = comparison.variance_factor * q[np.ix_(plan, plan)]
        if np.all(np.isfinite(scaled)) and np.trace(scaled) > 0.0:
            ellipse = error_ellipse(
                scaled,
                confidence=confidence,
                degrees_of_freedom=comparison.degrees_of_freedom or None,
            )
        up = [components.index(c) for c in ("u",) if c in components]
        if up:
            v_omega, v_rank = _quadratic(vector[up], q[np.ix_(up, up)])
            vertical = _test(f"vertical displacement of {station}", v_omega, v_rank, comparison, confidence)
    return Displacement(
        station_id=station,
        role=role,
        components=components,
        values=tuple(float(v) for v in vector),
        covariance=comparison.variance_factor * q,
        test=test,
        horizontal=horizontal,
        vertical=vertical,
        ellipse=ellipse,
    )
