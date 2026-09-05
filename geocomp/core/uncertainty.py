# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncertainty: the property that defines this project.

The research project's change notes state the central idea plainly:

    *"para todas as medidas e variaveis seja possivel realizar estimativa de
    seus niveis de incerteza, tanto por abordagens aproximadas/heuristicas como
    por abordagens rigorosas"*

So **no measured or derived geodetic quantity exists in GeoComp without an
uncertainty attached** (FR-200). :class:`Quantity` is therefore the most-used
type in the core, and this module is the one every technique module depends on.

Specified in ``specs/05-uncertainty-and-covariance.md``.

## The two paths, and the boundary between them

Scalar :class:`Quantity` arithmetic assumes independence. That is correct and
convenient for most of what a technique module does, and wrong the moment two
operands are correlated -- which happens constantly in geodesy, because a
distance and a zenith angle measured in one pointing share a stochastic model.

The vector path (:class:`Covariance` plus an explicit Jacobian) handles
correlation properly. To stop the two being confused, a quantity extracted from
a covariance carries a tag identifying it, and combining two quantities with the
**same tag** through the scalar path raises. That converts the most dangerous
silent error in the system into a loud one.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.units import Unit

__all__ = [
    "Covariance",
    "Quantity",
    "Strategy",
    "UncertaintyMode",
    "acos",
    "asin",
    "atan",
    "atan2",
    "combine_modes",
    "cos",
    "exp",
    "hypot",
    "log",
    "propagate",
    "sin",
    "sqrt",
    "tan",
]


class UncertaintyMode(Enum):
    """Whether an uncertainty was propagated rigorously or estimated.

    FR-203: the distinction must survive to every display, export and report.
    Presenting a heuristic figure as a rigorously propagated one misrepresents
    the quality of a survey, and monitoring decisions are made on exactly these
    numbers.
    """

    RIGOROUS = "rigorous"
    APPROXIMATE = "approximate"


class Strategy(Enum):
    """A named approximate-uncertainty strategy (FR-202).

    ``specs/05`` section 2.3. Each records *how* an uncertainty was estimated
    when rigorous propagation was not possible, so a report can say which
    simplification was made rather than merely that one was.
    """

    #: Input sigma from the instrument's manufacturer specification.
    NOMINAL_PRECISION = "nominal_precision"
    #: Input sigma from the configured default for the observation type.
    TYPE_DEFAULT = "type_default"
    #: Unknown correlations ignored; inputs treated as independent.
    INDEPENDENCE_ASSUMED = "independence_assumed"
    #: Only the dominant contributions propagated.
    DOMINANT_TERM = "dominant_term"
    #: An a priori model scaled by an empirically determined factor.
    EMPIRICAL_SCALING = "empirical_scaling"
    #: A derivative obtained by finite differences rather than analytically.
    NUMERIC_DERIVATIVE = "numeric_derivative"
    #: The uncertainty implied by how many digits were written down. A value
    #: recorded as ``32.4`` is somewhere in ``[32.35, 32.45)``, so its standard
    #: deviation is ``0.05 / sqrt(3)`` under the uniform distribution that
    #: rounding produces. Added in phase P4 for sight distances, and it is not
    #: an invention: the information is genuinely in the file, in the number of
    #: digits the observer chose to write. Use it only where nothing better
    #: exists *and* the quantity is not load-bearing -- never for an observation
    #: whose sigma becomes an adjustment weight.
    RECORDED_PRECISION = "recorded_precision"


def combine_modes(*quantities: Quantity) -> tuple[UncertaintyMode, frozenset[Strategy]]:
    """Combine the modes of several operands.

    Mode is contagious: one approximate input makes the result approximate.
    There is no partial credit, because a chain is no more rigorous than its
    weakest link, and the union of strategies records why.
    """
    strategies: set[Strategy] = set()
    mode = UncertaintyMode.RIGOROUS
    for quantity in quantities:
        strategies |= quantity.strategies
        if quantity.mode is UncertaintyMode.APPROXIMATE:
            mode = UncertaintyMode.APPROXIMATE
    return mode, frozenset(strategies)


@dataclass(frozen=True)
class Quantity:
    """A value with its variance, its unit, and the provenance of its uncertainty.

    Immutable: every operation returns a new value. Variance rather than
    standard deviation is stored because variance is what composes linearly;
    keeping sigma invites a forgotten square.

    Attributes:
        value: The value, in SI (metres, radians, m/s^2).
        variance: sigma squared, in the square of ``unit``. Never negative.
        unit: Checked by arithmetic -- a metre plus a radian raises.
        mode: Rigorous or approximate (FR-203).
        strategies: Which approximations were used. Empty when rigorous.
        covariance_ref: Identifies the :class:`Covariance` this was extracted
            from, if any. See the module docstring.
    """

    value: float
    variance: float = 0.0
    unit: Unit = Unit.DIMENSIONLESS
    mode: UncertaintyMode = UncertaintyMode.RIGOROUS
    strategies: frozenset[Strategy] = field(default_factory=frozenset)
    covariance_ref: str | None = None

    def __post_init__(self) -> None:
        # Coerce to float so the declared types are honest. Without this a
        # Quantity built from an int literal stores an int, and a serialisation
        # round trip is not idempotent -- 0 goes out, 0.0 comes back -- which
        # breaks the bit-identical reproducibility NFR-007 requires.
        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "variance", float(self.variance))

        if self.variance < 0.0:
            raise ValidationError("negative_variance", value=self.value, variance=self.variance)
        if self.mode is UncertaintyMode.RIGOROUS and self.strategies:
            raise ValidationError(
                "rigorous_with_strategies",
                strategies=sorted(s.value for s in self.strategies),
                expected="an approximate quantity, since strategies were supplied",
            )

    # -- construction ----------------------------------------------------

    @classmethod
    def exact(cls, value: float, unit: Unit = Unit.DIMENSIONLESS) -> Quantity:
        """A constant with no uncertainty -- a defined conversion factor, a count.

        Not a shortcut for "uncertainty unknown". An unknown uncertainty must be
        supplied or refused (``specs/05`` section 5); calling it zero silently
        claims perfect knowledge.
        """
        return cls(value=value, variance=0.0, unit=unit)

    @classmethod
    def from_std_dev(
        cls,
        value: float,
        std_dev: float,
        unit: Unit = Unit.DIMENSIONLESS,
        *,
        mode: UncertaintyMode = UncertaintyMode.RIGOROUS,
        strategies: Iterable[Strategy] = (),
    ) -> Quantity:
        """Build from a standard deviation, which is how instruments quote precision."""
        return cls(
            value=value,
            variance=float(std_dev) ** 2,
            unit=unit,
            mode=mode,
            strategies=frozenset(strategies),
        )

    @classmethod
    def approximate(cls, value: float, std_dev: float, unit: Unit, *strategies: Strategy) -> Quantity:
        """Build an explicitly approximate quantity, naming the strategies used."""
        if not strategies:
            raise ValidationError(
                "approximate_without_strategy",
                value=value,
                expected="at least one Strategy naming how the uncertainty was estimated",
            )
        return cls.from_std_dev(
            value, std_dev, unit, mode=UncertaintyMode.APPROXIMATE, strategies=strategies
        )

    # -- inspection ------------------------------------------------------

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    @property
    def is_exact(self) -> bool:
        return self.variance == 0.0

    @property
    def is_rigorous(self) -> bool:
        return self.mode is UncertaintyMode.RIGOROUS

    def relative_std_dev(self) -> float:
        """sigma / |value|. Raises for a zero value, where it is undefined."""
        if self.value == 0.0:
            raise ValidationError("relative_uncertainty_of_zero")
        return self.std_dev / abs(self.value)

    def with_strategy(self, *strategies: Strategy) -> Quantity:
        """Return a copy marked approximate, with *strategies* added."""
        return replace(
            self,
            mode=UncertaintyMode.APPROXIMATE,
            strategies=self.strategies | frozenset(strategies),
        )

    def detached(self) -> Quantity:
        """Return a copy with no covariance tag.

        Deliberately explicit: it disables the correlation guard for this value,
        so a caller that reaches for it is stating that treating the quantity as
        independent is intended. Callers should normally add
        :attr:`Strategy.INDEPENDENCE_ASSUMED` at the same time.
        """
        return replace(self, covariance_ref=None)

    def __repr__(self) -> str:
        mode = "" if self.is_rigorous else f", {self.mode.value}"
        return f"Quantity({self.value!r} +/- {self.std_dev:.6g} {self.unit.symbol}{mode})"

    # -- arithmetic ------------------------------------------------------

    def _check_correlated(self, other: Quantity, operation: str) -> None:
        if self.covariance_ref is not None and self.covariance_ref == other.covariance_ref:
            raise ValidationError(
                "correlated_scalar_path",
                operation=operation,
                covariance=self.covariance_ref,
                expected=(
                    "these quantities come from the same covariance matrix and are "
                    "correlated; combine them with propagate() and an explicit "
                    "Jacobian, or call .detached() to state that treating them as "
                    "independent is intended"
                ),
            )

    def _check_same_unit(self, other: Quantity, operation: str) -> None:
        if self.unit is not other.unit:
            raise ValidationError(
                "incompatible_units",
                operation=operation,
                received=[self.unit.name, other.unit.name],
                expected="both operands in the same unit",
            )

    def __add__(self, other: Quantity | float | int) -> Quantity:
        other = _as_quantity(other, self.unit)
        self._check_same_unit(other, "add")
        self._check_correlated(other, "add")
        mode, strategies = combine_modes(self, other)
        return Quantity(
            self.value + other.value, self.variance + other.variance, self.unit, mode, strategies
        )

    __radd__ = __add__

    def __sub__(self, other: Quantity | float | int) -> Quantity:
        other = _as_quantity(other, self.unit)
        self._check_same_unit(other, "subtract")
        self._check_correlated(other, "subtract")
        mode, strategies = combine_modes(self, other)
        return Quantity(
            self.value - other.value, self.variance + other.variance, self.unit, mode, strategies
        )

    def __rsub__(self, other: Quantity | float | int) -> Quantity:
        return _as_quantity(other, self.unit).__sub__(self)

    def __neg__(self) -> Quantity:
        return replace(self, value=-self.value)

    def __mul__(self, other: Quantity | float | int) -> Quantity:
        other = _as_quantity(other, Unit.DIMENSIONLESS)
        self._check_correlated(other, "multiply")
        unit = _product_unit(self.unit, other.unit, "multiply")
        mode, strategies = combine_modes(self, other)
        # var(xy) = y^2 var(x) + x^2 var(y), to first order.
        variance = other.value**2 * self.variance + self.value**2 * other.variance
        return Quantity(self.value * other.value, variance, unit, mode, strategies)

    __rmul__ = __mul__

    def __truediv__(self, other: Quantity | float | int) -> Quantity:
        other = _as_quantity(other, Unit.DIMENSIONLESS)
        if other.value == 0.0:
            raise ValidationError("division_by_zero", numerator=self.value)
        self._check_correlated(other, "divide")
        unit = _quotient_unit(self.unit, other.unit, "divide")
        mode, strategies = combine_modes(self, other)
        # var(x/y) = var(x)/y^2 + x^2 var(y)/y^4, to first order.
        variance = self.variance / other.value**2 + self.value**2 * other.variance / other.value**4
        return Quantity(self.value / other.value, variance, unit, mode, strategies)

    def __rtruediv__(self, other: Quantity | float | int) -> Quantity:
        return _as_quantity(other, Unit.DIMENSIONLESS).__truediv__(self)

    def __pow__(self, exponent: float) -> Quantity:
        if self.unit is not Unit.DIMENSIONLESS and exponent != 1.0:
            raise ValidationError(
                "power_of_dimensioned_quantity",
                unit=self.unit.name,
                exponent=exponent,
                expected="a dimensionless quantity; GeoComp does not track compound units",
            )
        derivative = exponent * self.value ** (exponent - 1.0)
        return Quantity(
            self.value**exponent,
            derivative**2 * self.variance,
            self.unit,
            self.mode,
            self.strategies,
        )

    # -- comparison ------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Equality of value, variance, unit and mode -- not of the covariance tag."""
        if not isinstance(other, Quantity):
            return NotImplemented
        return (
            self.value == other.value
            and self.variance == other.variance
            and self.unit is other.unit
            and self.mode is other.mode
        )

    def __hash__(self) -> int:
        return hash((self.value, self.variance, self.unit, self.mode))

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Full-precision and locale-independent (specs/04 section 6, FR-095)."""
        payload: dict[str, Any] = {
            "value": self.value,
            "variance": self.variance,
            "unit": self.unit.name,
            "mode": self.mode.name,
        }
        if self.strategies:
            payload["strategies"] = sorted(s.name for s in self.strategies)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Quantity:
        return cls(
            value=float(payload["value"]),
            variance=float(payload["variance"]),
            unit=Unit[payload["unit"]],
            mode=UncertaintyMode[payload["mode"]],
            strategies=frozenset(Strategy[name] for name in payload.get("strategies", ())),
        )


# -- unit algebra --------------------------------------------------------


def _as_quantity(value: Quantity | float | int, unit: Unit) -> Quantity:
    """Promote a plain number to an exact quantity in *unit*."""
    if isinstance(value, Quantity):
        return value
    if isinstance(value, (int, float)):
        return Quantity.exact(float(value), unit)
    raise ValidationError("not_a_quantity", received=type(value).__name__)


def _product_unit(left: Unit, right: Unit, operation: str) -> Unit:
    """Unit of a product.

    GeoComp does not track compound units: there is no square metre. That is a
    deliberate limit, because the geodetic operations that matter here are
    scaling by a dimensionless factor and taking trigonometric ratios. Anything
    else is refused rather than assigned a plausible-looking wrong unit.
    """
    if left is Unit.DIMENSIONLESS:
        return right
    if right is Unit.DIMENSIONLESS:
        return left
    raise ValidationError(
        "compound_unit_not_supported",
        operation=operation,
        received=[left.name, right.name],
        expected="at least one dimensionless operand",
    )


def _quotient_unit(left: Unit, right: Unit, operation: str) -> Unit:
    if right is Unit.DIMENSIONLESS:
        return left
    if left is right:
        return Unit.DIMENSIONLESS
    raise ValidationError(
        "compound_unit_not_supported",
        operation=operation,
        received=[left.name, right.name],
        expected="a dimensionless divisor, or operands of the same unit",
    )


# -- elementary functions ------------------------------------------------


def _unary(
    quantity: Quantity,
    function: Callable[[float], float],
    derivative: Callable[[float], float],
    in_unit: Unit | None,
    out_unit: Unit,
    name: str,
) -> Quantity:
    if in_unit is not None and quantity.unit is not in_unit:
        raise ValidationError(
            "incompatible_units",
            operation=name,
            received=quantity.unit.name,
            expected=in_unit.name,
        )
    slope = derivative(quantity.value)
    return Quantity(
        function(quantity.value),
        slope**2 * quantity.variance,
        out_unit,
        quantity.mode,
        quantity.strategies,
        quantity.covariance_ref,
    )


def sin(q: Quantity) -> Quantity:
    return _unary(q, math.sin, math.cos, Unit.RADIAN, Unit.DIMENSIONLESS, "sin")


def cos(q: Quantity) -> Quantity:
    return _unary(q, math.cos, lambda x: -math.sin(x), Unit.RADIAN, Unit.DIMENSIONLESS, "cos")


def tan(q: Quantity) -> Quantity:
    return _unary(
        q, math.tan, lambda x: 1.0 / math.cos(x) ** 2, Unit.RADIAN, Unit.DIMENSIONLESS, "tan"
    )


def asin(q: Quantity) -> Quantity:
    return _unary(
        q,
        math.asin,
        lambda x: 1.0 / math.sqrt(1.0 - x**2),
        Unit.DIMENSIONLESS,
        Unit.RADIAN,
        "asin",
    )


def acos(q: Quantity) -> Quantity:
    return _unary(
        q,
        math.acos,
        lambda x: -1.0 / math.sqrt(1.0 - x**2),
        Unit.DIMENSIONLESS,
        Unit.RADIAN,
        "acos",
    )


def atan(q: Quantity) -> Quantity:
    return _unary(
        q, math.atan, lambda x: 1.0 / (1.0 + x**2), Unit.DIMENSIONLESS, Unit.RADIAN, "atan"
    )


def exp(q: Quantity) -> Quantity:
    return _unary(q, math.exp, math.exp, Unit.DIMENSIONLESS, Unit.DIMENSIONLESS, "exp")


def log(q: Quantity) -> Quantity:
    if q.value <= 0.0:
        raise ValidationError("log_of_non_positive", value=q.value)
    return _unary(q, math.log, lambda x: 1.0 / x, Unit.DIMENSIONLESS, Unit.DIMENSIONLESS, "log")


def sqrt(q: Quantity) -> Quantity:
    """Square root of a dimensionless quantity.

    Restricted to dimensionless input because GeoComp does not track squared
    units, so the square root of a length would have no defensible result unit.
    For the common geodetic case -- the length of a vector from its components
    -- use :func:`hypot`, which is dimensionally coherent.
    """
    if q.value < 0.0:
        raise ValidationError("sqrt_of_negative", value=q.value)
    if q.value == 0.0:
        raise ValidationError(
            "sqrt_at_zero",
            expected="a positive value; the derivative of sqrt is singular at zero",
        )
    return _unary(
        q, math.sqrt, lambda x: 0.5 / math.sqrt(x), Unit.DIMENSIONLESS, Unit.DIMENSIONLESS, "sqrt"
    )


def atan2(y: Quantity, x: Quantity) -> Quantity:
    """Two-argument arctangent, returning radians.

    Both operands must share a unit -- the ratio is what matters. Correct across
    all four quadrants, which is why it is used rather than ``atan(y / x)``.
    """
    if y.unit is not x.unit:
        raise ValidationError(
            "incompatible_units", operation="atan2", received=[y.unit.name, x.unit.name]
        )
    y._check_correlated(x, "atan2")
    denominator = x.value**2 + y.value**2
    if denominator == 0.0:
        raise ValidationError("atan2_at_origin")
    mode, strategies = combine_modes(y, x)
    # d/dy = x / (x^2 + y^2);  d/dx = -y / (x^2 + y^2)
    dy, dx = x.value / denominator, -y.value / denominator
    return Quantity(
        math.atan2(y.value, x.value),
        dy**2 * y.variance + dx**2 * x.variance,
        Unit.RADIAN,
        mode,
        strategies,
    )


def hypot(x: Quantity, y: Quantity) -> Quantity:
    """Euclidean length of a two-component vector, preserving the unit."""
    if x.unit is not y.unit:
        raise ValidationError(
            "incompatible_units", operation="hypot", received=[x.unit.name, y.unit.name]
        )
    x._check_correlated(y, "hypot")
    length = math.hypot(x.value, y.value)
    if length == 0.0:
        raise ValidationError("hypot_at_origin")
    mode, strategies = combine_modes(x, y)
    dx, dy = x.value / length, y.value / length
    return Quantity(length, dx**2 * x.variance + dy**2 * y.variance, x.unit, mode, strategies)


# -- correlated quantities -----------------------------------------------


@dataclass(frozen=True)
class Covariance:
    """A full covariance matrix over a set of *named* quantities.

    Attributes:
        matrix: Symmetric, positive semi-definite, shape ``(n, n)``.
        labels: Names the ordering. **Mandatory**: a covariance matrix silently
            reordered relative to its observations is a catastrophic and nearly
            invisible defect, and requiring labels makes the ordering explicit
            at every boundary.
        units: One per component.
        mode: Rigorous or approximate, as for :class:`Quantity`.
        strategies: Which approximations were used.
    """

    matrix: np.ndarray
    labels: tuple[str, ...]
    units: tuple[Unit, ...]
    mode: UncertaintyMode = UncertaintyMode.RIGOROUS
    strategies: frozenset[Strategy] = field(default_factory=frozenset)

    #: Relative tolerances for the symmetry and positive-semi-definiteness checks.
    SYMMETRY_TOLERANCE = 1e-10
    EIGENVALUE_TOLERANCE = 1e-12

    def __post_init__(self) -> None:
        matrix = np.asarray(self.matrix, dtype=float)
        object.__setattr__(self, "matrix", matrix)

        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise DataError("covariance_not_square", shape=list(matrix.shape))
        if len(self.labels) != matrix.shape[0]:
            raise DataError(
                "covariance_label_count",
                labels=len(self.labels),
                size=int(matrix.shape[0]),
                expected="one label per component",
            )
        if len(set(self.labels)) != len(self.labels):
            raise DataError("covariance_duplicate_labels", labels=list(self.labels))
        if len(self.units) != matrix.shape[0]:
            raise DataError(
                "covariance_unit_count", units=len(self.units), size=int(matrix.shape[0])
            )

        scale = max(float(np.max(np.abs(matrix))), 1.0) if matrix.size else 1.0
        asymmetry = float(np.max(np.abs(matrix - matrix.T))) if matrix.size else 0.0
        if asymmetry > self.SYMMETRY_TOLERANCE * scale:
            worst = np.unravel_index(int(np.argmax(np.abs(matrix - matrix.T))), matrix.shape)
            raise DataError(
                "covariance_not_symmetric",
                asymmetry=asymmetry,
                at=[self.labels[worst[0]], self.labels[worst[1]]],
            )

        # A non-PSD input covariance is a data problem that would otherwise
        # surface much later as a nonsensical adjustment. Report it here.
        if matrix.size:
            eigenvalues = np.linalg.eigvalsh((matrix + matrix.T) / 2.0)
            smallest = float(eigenvalues[0])
            if smallest < -self.EIGENVALUE_TOLERANCE * scale:
                raise DataError(
                    "covariance_not_positive_semidefinite",
                    smallest_eigenvalue=smallest,
                    labels=list(self.labels),
                    expected="a positive semi-definite matrix",
                )

    # -- identity --------------------------------------------------------

    @property
    def ref(self) -> str:
        """A deterministic identifier for this covariance.

        Derived from the labels and the matrix content rather than from object
        identity, so it is stable across a serialisation round trip and
        reproducible between runs (NFR-007). Two covariances with identical
        content share a ref, which is the conservative outcome: quantities drawn
        from either are treated as correlated.
        """
        digest = hashlib.blake2b(digest_size=8)
        digest.update(" ".join(self.labels).encode("utf-8"))
        digest.update(np.ascontiguousarray(self.matrix, dtype=">f8").tobytes())
        return digest.hexdigest()

    @property
    def size(self) -> int:
        return len(self.labels)

    def index(self, label: str) -> int:
        try:
            return self.labels.index(label)
        except ValueError:
            raise ValidationError(
                "unknown_covariance_label", label=label, expected=list(self.labels)
            ) from None

    # -- extraction ------------------------------------------------------

    def variance(self, label: str) -> float:
        position = self.index(label)
        return float(self.matrix[position, position])

    def std_devs(self) -> dict[str, float]:
        return {
            label: math.sqrt(max(float(self.matrix[i, i]), 0.0))
            for i, label in enumerate(self.labels)
        }

    def quantity(self, label: str, value: float) -> Quantity:
        """Extract one component as a :class:`Quantity`, tagged with this covariance.

        The tag is what makes the correlation guard work: two quantities drawn
        from the same covariance cannot be combined through scalar arithmetic.
        """
        position = self.index(label)
        return Quantity(
            value=value,
            variance=float(self.matrix[position, position]),
            unit=self.units[position],
            mode=self.mode,
            strategies=self.strategies,
            covariance_ref=self.ref,
        )

    def quantities(self, values: Sequence[float]) -> dict[str, Quantity]:
        """Extract every component, given the values in label order."""
        if len(values) != self.size:
            raise ValidationError("value_count_mismatch", received=len(values), expected=self.size)
        return {label: self.quantity(label, float(values[i])) for i, label in enumerate(self.labels)}

    def sub(self, labels: Sequence[str]) -> Covariance:
        """The sub-covariance over *labels*, preserving their correlations."""
        positions = [self.index(label) for label in labels]
        return Covariance(
            matrix=self.matrix[np.ix_(positions, positions)],
            labels=tuple(labels),
            units=tuple(self.units[p] for p in positions),
            mode=self.mode,
            strategies=self.strategies,
        )

    def to_correlation(self) -> np.ndarray:
        """The correlation matrix. Zero-variance components give zero correlation."""
        sigma = np.sqrt(np.clip(np.diag(self.matrix), 0.0, None))
        with np.errstate(divide="ignore", invalid="ignore"):
            outer = np.outer(sigma, sigma)
            correlation = np.where(outer > 0.0, self.matrix / outer, 0.0)
        np.fill_diagonal(correlation, np.where(sigma > 0.0, 1.0, 0.0))
        return correlation

    def transform(
        self,
        jacobian: np.ndarray,
        out_labels: Sequence[str],
        out_units: Sequence[Unit],
        *,
        strategies: Iterable[Strategy] = (),
    ) -> Covariance:
        """Propagate through a linear map: ``Sigma_out = A Sigma A^T`` (FR-201)."""
        return propagate(jacobian, self, out_labels, out_units, strategies=strategies)

    # -- construction ----------------------------------------------------

    @classmethod
    def diagonal(
        cls,
        variances: dict[str, float],
        units: dict[str, Unit],
        *,
        mode: UncertaintyMode = UncertaintyMode.RIGOROUS,
        strategies: Iterable[Strategy] = (),
    ) -> Covariance:
        """Build an uncorrelated covariance.

        Convenient, and worth using consciously: a diagonal matrix asserts that
        the components are uncorrelated, which is a modelling claim rather than
        a default.
        """
        labels = tuple(variances)
        return cls(
            matrix=np.diag([float(variances[label]) for label in labels]),
            labels=labels,
            units=tuple(units[label] for label in labels),
            mode=mode,
            strategies=frozenset(strategies),
        )

    @classmethod
    def from_quantities(
        cls,
        quantities: dict[str, Quantity],
        correlations: dict[tuple[str, str], float] | None = None,
    ) -> Covariance:
        """Build from independent quantities plus explicit correlation coefficients."""
        labels = tuple(quantities)
        sigma = np.array([quantities[label].std_dev for label in labels])
        matrix = np.diag(sigma**2)

        for (first, second), rho in (correlations or {}).items():
            if not -1.0 <= rho <= 1.0:
                raise ValidationError("correlation_out_of_range", pair=[first, second], value=rho)
            i, j = labels.index(first), labels.index(second)
            matrix[i, j] = matrix[j, i] = rho * sigma[i] * sigma[j]

        mode, strategies = combine_modes(*quantities.values())
        return cls(
            matrix=matrix,
            labels=labels,
            units=tuple(quantities[label].unit for label in labels),
            mode=mode,
            strategies=strategies,
        )

    # -- serialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "labels": list(self.labels),
            "units": [unit.name for unit in self.units],
            "mode": self.mode.name,
            # The full matrix, not a packed triangle: the storage form must be
            # unambiguous (specs/04 section 6), and n is small.
            "matrix": [[float(v) for v in row] for row in self.matrix],
        }
        if self.strategies:
            payload["strategies"] = sorted(s.name for s in self.strategies)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Covariance:
        return cls(
            matrix=np.array(payload["matrix"], dtype=float),
            labels=tuple(payload["labels"]),
            units=tuple(Unit[name] for name in payload["units"]),
            mode=UncertaintyMode[payload["mode"]],
            strategies=frozenset(Strategy[name] for name in payload.get("strategies", ())),
        )

    def __repr__(self) -> str:
        return f"Covariance({list(self.labels)}, {self.mode.value})"


def propagate(
    jacobian: np.ndarray,
    covariance: Covariance,
    out_labels: Sequence[str],
    out_units: Sequence[Unit],
    *,
    strategies: Iterable[Strategy] = (),
) -> Covariance:
    """Rigorous covariance propagation, ``Sigma_out = A Sigma_in A^T`` (FR-201).

    Args:
        jacobian: **A**, shape ``(m, n)`` with *n* matching ``covariance.size``.
        covariance: **Sigma_in**.
        out_labels: Names the *m* outputs, in Jacobian row order.
        out_units: The dimension of each output.
        strategies: Any approximation this propagation introduced -- for example
            :attr:`Strategy.NUMERIC_DERIVATIVE` when **A** came from finite
            differences.

    Correlations in the input are carried into the output, which is the whole
    point: reducing the input to independent standard deviations first is a
    *different* computation, and GeoComp performs it only when asked (FR-208).
    """
    matrix = np.asarray(jacobian, dtype=float)
    if matrix.ndim != 2:
        raise ValidationError("jacobian_not_2d", shape=list(matrix.shape))
    if matrix.shape[1] != covariance.size:
        raise ValidationError(
            "jacobian_shape_mismatch",
            jacobian=list(matrix.shape),
            covariance=covariance.size,
            expected=f"a jacobian with {covariance.size} columns",
        )
    if matrix.shape[0] != len(out_labels):
        raise ValidationError(
            "output_label_count",
            rows=int(matrix.shape[0]),
            labels=len(out_labels),
            expected="one output label per Jacobian row",
        )
    if len(out_units) != len(out_labels):
        raise ValidationError("output_unit_count", units=len(out_units), labels=len(out_labels))

    result = matrix @ covariance.matrix @ matrix.T
    # A Sigma A^T is symmetric mathematically, but the matrix product introduces
    # asymmetry in the last bit, which would trip the validation partway along a
    # long propagation chain (specs/05 section 6, limit 4).
    result = (result + result.T) / 2.0

    extra = frozenset(strategies)
    mode = (
        UncertaintyMode.APPROXIMATE
        if extra or covariance.mode is UncertaintyMode.APPROXIMATE
        else UncertaintyMode.RIGOROUS
    )
    return Covariance(
        matrix=result,
        labels=tuple(out_labels),
        units=tuple(out_units),
        mode=mode,
        strategies=covariance.strategies | extra,
    )
