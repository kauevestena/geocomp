# SPDX-License-Identifier: GPL-2.0-or-later
"""Solutions and provenance (FR-106, FR-134, FR-323).

``specs/04-data-model.md`` sections 2.8 to 2.10.

**One :class:`Solution` type for every producer** -- the in-house adjustment,
DynAdjust, and ``rnx2rtkp`` all fill it. That is what makes everything
downstream engine-agnostic (``specs/03-architecture.md`` section 3.2), and it is
what turns the DynAdjust integration in phase P6 into a cross-validation rather
than a second pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.models.position import Position
from geocomp.core.uncertainty import Covariance, UncertaintyMode
from geocomp.core.version import __version__

__all__ = [
    "AdjustedStation",
    "AdjustmentStatistics",
    "DatumDefinition",
    "ErrorEllipse",
    "ObservationResult",
    "Provenance",
    "Solution",
    "SolutionKind",
    "TestResult",
]


class SolutionKind(Enum):
    ADJUSTMENT = "adjustment"
    GNSS_PROCESSING = "gnss_processing"
    PREANALYSIS = "preanalysis"
    TRANSFORMATION = "transformation"


class DatumDefinition(Enum):
    """How the datum defect was removed (FR-222).

    Recorded on the solution because a minimum-constraint solution and a
    constrained solution of the same data are **not** comparable -- differencing
    them across epochs measures the constraint, not motion
    (``specs/14-multi-epoch-monitoring.md`` section 2).
    """

    MINIMUM_CONSTRAINT = "minimum_constraint"
    INNER_CONSTRAINT = "inner_constraint"
    CONSTRAINED = "constrained"
    FIXED = "fixed"
    #: A solution that defines no datum, e.g. a single GNSS session result.
    NONE = "none"


@dataclass(frozen=True)
class ErrorEllipse:
    """A confidence region for an adjusted position (FR-254).

    ``confidence`` is stored because an ellipse without its confidence level is
    uninterpretable.

    The **exaggeration** an ellipse is drawn at is deliberately *not* here. It
    belongs to a drawing, not to a confidence region: the same ellipse shown on
    two maps at two scales is one ellipse. It lives instead on
    :class:`~geocomp.core.visualization.DrawnEllipse`, where it is a required
    argument, so that a drawn ellipse cannot exist without stating the factor
    it was drawn at (FR-901) while the region itself stays scale-free.
    """

    semi_major: float
    semi_minor: float
    orientation: float
    confidence: float = 0.95
    semi_vertical: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "semi_major": self.semi_major,
            "semi_minor": self.semi_minor,
            "orientation": self.orientation,
            "confidence": self.confidence,
        }
        if self.semi_vertical is not None:
            payload["semi_vertical"] = self.semi_vertical
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ErrorEllipse:
        return cls(
            semi_major=float(payload["semi_major"]),
            semi_minor=float(payload["semi_minor"]),
            orientation=float(payload["orientation"]),
            confidence=float(payload.get("confidence", 0.95)),
            semi_vertical=payload.get("semi_vertical"),
        )


@dataclass(frozen=True)
class TestResult:
    """A statistical test outcome.

    Carries the statistic, its critical values, the confidence level and the
    decision. ``specs/06`` section 7 makes this mandatory: a bare pass/fail
    tells a student nothing and gives a professional nothing to defend.
    """

    name: str
    statistic: float
    critical_low: float | None = None
    critical_high: float | None = None
    confidence: float = 0.95
    passed: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        # Every field here is computed from NumPy scalars, and only one of them
        # is dangerous: ``np.float64`` subclasses ``float`` and serialises
        # silently, while ``np.bool_`` does **not** subclass ``bool`` and the
        # JSON encoder refuses it. The failure then surfaces far from here, when
        # a solution is written out, as an error naming neither the field nor
        # the test it came from -- which is exactly what happened.
        #
        # So all of them are coerced, not just the bool. Leaving the floats as
        # NumPy would keep the silent half of the leak alive, and the silent
        # half is what let the loud one through unnoticed.
        object.__setattr__(self, "passed", bool(self.passed))
        object.__setattr__(self, "statistic", float(self.statistic))
        for name in ("critical_low", "critical_high", "confidence"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, float(value))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "statistic": self.statistic,
            "confidence": self.confidence,
            "passed": self.passed,
        }
        for key, value in (
            ("critical_low", self.critical_low),
            ("critical_high", self.critical_high),
            ("note", self.note),
        ):
            if value is not None and value != "":
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TestResult:
        return cls(
            name=payload["name"],
            statistic=float(payload["statistic"]),
            critical_low=payload.get("critical_low"),
            critical_high=payload.get("critical_high"),
            confidence=float(payload.get("confidence", 0.95)),
            passed=bool(payload["passed"]),
            note=payload.get("note", ""),
        )


@dataclass(frozen=True)
class AdjustedStation:
    """One station's estimated coordinates and their quality."""

    station_id: str
    position: Position
    covariance: Covariance | None = None
    ellipse: ErrorEllipse | None = None
    positional_uncertainty: float | None = None
    correction: tuple[float, float, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "station_id": self.station_id,
            "position": self.position.to_dict(),
        }
        for key, value in (
            ("covariance", self.covariance.to_dict() if self.covariance else None),
            ("ellipse", self.ellipse.to_dict() if self.ellipse else None),
            ("positional_uncertainty", self.positional_uncertainty),
            ("correction", list(self.correction) if self.correction else None),
        ):
            if value is not None:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AdjustedStation:
        covariance = payload.get("covariance")
        ellipse = payload.get("ellipse")
        correction = payload.get("correction")
        return cls(
            station_id=payload["station_id"],
            position=Position.from_dict(payload["position"]),
            covariance=Covariance.from_dict(covariance) if covariance else None,
            ellipse=ErrorEllipse.from_dict(ellipse) if ellipse else None,
            positional_uncertainty=payload.get("positional_uncertainty"),
            correction=tuple(correction) if correction else None,  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ObservationResult:
    """What the adjustment concluded about one observation (FR-225, FR-251, FR-252).

    ``redundancy`` deserves attention: an observation with a redundancy number
    near zero is **uncheckable** -- no blunder in it is detectable at all -- and a
    network full of them can pass every statistical test while being wrong.
    """

    observation_id: str
    residual: float
    standardised_residual: float | None = None
    redundancy: float | None = None
    w_test: TestResult | None = None
    minimal_detectable_bias: float | None = None
    external_reliability: float | None = None
    adjusted_value: float | None = None

    def __post_init__(self) -> None:
        # As on :class:`TestResult`: these arrive from NumPy, and the document
        # this ends up in must contain built-in types only. See the note there
        # for why the silently-serialisable ones are coerced too.
        object.__setattr__(self, "residual", float(self.residual))
        for name in (
            "standardised_residual",
            "redundancy",
            "minimal_detectable_bias",
            "external_reliability",
            "adjusted_value",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, float(value))

    @property
    def is_uncheckable(self, threshold: float = 0.01) -> bool:
        """Whether the network can detect a blunder in this observation at all."""
        return self.redundancy is not None and self.redundancy < threshold

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "observation_id": self.observation_id,
            "residual": self.residual,
        }
        for key, value in (
            ("standardised_residual", self.standardised_residual),
            ("redundancy", self.redundancy),
            ("w_test", self.w_test.to_dict() if self.w_test else None),
            ("minimal_detectable_bias", self.minimal_detectable_bias),
            ("external_reliability", self.external_reliability),
            ("adjusted_value", self.adjusted_value),
        ):
            if value is not None:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ObservationResult:
        w_test = payload.get("w_test")
        return cls(
            observation_id=payload["observation_id"],
            residual=float(payload["residual"]),
            standardised_residual=payload.get("standardised_residual"),
            redundancy=payload.get("redundancy"),
            w_test=TestResult.from_dict(w_test) if w_test else None,
            minimal_detectable_bias=payload.get("minimal_detectable_bias"),
            external_reliability=payload.get("external_reliability"),
            adjusted_value=payload.get("adjusted_value"),
        )


@dataclass(frozen=True)
class AdjustmentStatistics:
    """Global statistics of one adjustment (specs/04 section 2.9)."""

    n_observations: int = 0
    n_parameters: int = 0
    n_constraints: int = 0
    degrees_of_freedom: int = 0
    variance_factor_apriori: float = 1.0
    variance_factor_aposteriori: float | None = None
    global_test: TestResult | None = None
    iterations: int = 0
    converged: bool = False
    max_correction: float | None = None
    condition_number: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "n_observations": self.n_observations,
            "n_parameters": self.n_parameters,
            "n_constraints": self.n_constraints,
            "degrees_of_freedom": self.degrees_of_freedom,
            "variance_factor_apriori": self.variance_factor_apriori,
            "iterations": self.iterations,
            "converged": self.converged,
        }
        for key, value in (
            ("variance_factor_aposteriori", self.variance_factor_aposteriori),
            ("global_test", self.global_test.to_dict() if self.global_test else None),
            ("max_correction", self.max_correction),
            ("condition_number", self.condition_number),
        ):
            if value is not None:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AdjustmentStatistics:
        global_test = payload.get("global_test")
        return cls(
            n_observations=int(payload.get("n_observations", 0)),
            n_parameters=int(payload.get("n_parameters", 0)),
            n_constraints=int(payload.get("n_constraints", 0)),
            degrees_of_freedom=int(payload.get("degrees_of_freedom", 0)),
            variance_factor_apriori=float(payload.get("variance_factor_apriori", 1.0)),
            variance_factor_aposteriori=payload.get("variance_factor_aposteriori"),
            global_test=TestResult.from_dict(global_test) if global_test else None,
            iterations=int(payload.get("iterations", 0)),
            converged=bool(payload.get("converged", False)),
            max_correction=payload.get("max_correction"),
            condition_number=payload.get("condition_number"),
        )


@dataclass(frozen=True)
class Provenance:
    """Everything needed to reproduce a result (FR-134, NFR-007).

    **Rule (NFR-010):** never records a credential, a token, or a URL containing
    one. Provenance is exported, attached to bug reports and shown to clients.
    """

    created: datetime
    source: str = ""
    algorithm_id: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    engine: str = ""
    engine_version: str = ""
    command_line: str = ""
    exit_code: int | None = None
    input_ids: tuple[str, ...] = ()
    input_digests: dict[str, str] = field(default_factory=dict)
    geocomp_version: str = __version__
    qgis_version: str = ""
    uncertainty_mode: UncertaintyMode = UncertaintyMode.RIGOROUS

    @classmethod
    def now(cls, **kwargs: Any) -> Provenance:
        return cls(created=datetime.now(UTC), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "created": self.created.astimezone(UTC).isoformat(),
            "geocomp_version": self.geocomp_version,
            "uncertainty_mode": self.uncertainty_mode.name,
        }
        for key, value in (
            ("source", self.source),
            ("algorithm_id", self.algorithm_id),
            ("parameters", dict(self.parameters) if self.parameters else None),
            ("engine", self.engine),
            ("engine_version", self.engine_version),
            ("command_line", self.command_line),
            ("exit_code", self.exit_code),
            ("input_ids", list(self.input_ids) if self.input_ids else None),
            ("input_digests", dict(self.input_digests) if self.input_digests else None),
            ("qgis_version", self.qgis_version),
        ):
            if value is not None and value != "":
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Provenance:
        return cls(
            created=datetime.fromisoformat(payload["created"]),
            source=payload.get("source", ""),
            algorithm_id=payload.get("algorithm_id", ""),
            parameters=dict(payload.get("parameters", {})),
            engine=payload.get("engine", ""),
            engine_version=payload.get("engine_version", ""),
            command_line=payload.get("command_line", ""),
            exit_code=payload.get("exit_code"),
            input_ids=tuple(payload.get("input_ids", ())),
            input_digests=dict(payload.get("input_digests", {})),
            geocomp_version=payload.get("geocomp_version", ""),
            qgis_version=payload.get("qgis_version", ""),
            uncertainty_mode=UncertaintyMode[payload.get("uncertainty_mode", "RIGOROUS")],
        )


@dataclass(frozen=True)
class Solution:
    """The output of one adjustment or processing run (FR-106).

    Filled identically by every producer, so visualisation, reporting,
    multi-epoch analysis and storage are written once and are engine-agnostic.

    ``superseded_by`` rather than deletion: nothing that produced a result is
    removed while the result exists (FR-135).
    """

    id: str
    network_id: str
    kind: SolutionKind
    crs: str
    epoch: Epoch
    datum_definition: DatumDefinition = DatumDefinition.NONE
    adjusted_stations: tuple[AdjustedStation, ...] = ()
    parameter_covariance: Covariance | None = None
    observation_results: tuple[ObservationResult, ...] = ()
    statistics: AdjustmentStatistics = field(default_factory=AdjustmentStatistics)
    uncertainty_mode: UncertaintyMode = UncertaintyMode.RIGOROUS
    provenance: Provenance | None = None
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        # FR-105: a solution without an epoch cannot enter a comparison, so it
        # cannot be created without one either.
        if self.epoch is None:
            raise ValidationError(
                "solution_without_epoch",
                solution=self.id,
                expected="a reference epoch; GeoComp will not assume one (FR-105)",
            )
        if not self.crs:
            raise ValidationError("solution_without_crs", solution=self.id)

    @property
    def is_superseded(self) -> bool:
        return self.superseded_by is not None

    @property
    def is_approximate(self) -> bool:
        return self.uncertainty_mode is UncertaintyMode.APPROXIMATE

    def station(self, station_id: str) -> AdjustedStation:
        for adjusted in self.adjusted_stations:
            if adjusted.station_id == station_id:
                return adjusted
        raise ValidationError(
            "station_not_in_solution",
            solution=self.id,
            station=station_id,
            expected=[a.station_id for a in self.adjusted_stations],
        )

    def uncheckable_observations(self) -> list[ObservationResult]:
        """Observations whose blunders the network cannot detect (specs/06 section 4.2)."""
        return [result for result in self.observation_results if result.is_uncheckable]

    def is_comparable_with(self, other: Solution) -> list[str]:
        """Reasons *self* and *other* cannot be differenced (FR-831).

        Returns a list of findings rather than a boolean: the user needs to know
        *what* is incompatible, and an epoch difference is resolvable by
        transformation while a datum-definition difference is not.
        """
        findings: list[str] = []
        if self.crs != other.crs:
            findings.append(f"different reference frames: {self.crs} and {other.crs}")
        if self.epoch.decimal_year != other.epoch.decimal_year:
            findings.append(
                f"different epochs: {self.epoch.decimal_year} and {other.epoch.decimal_year}"
            )
        if self.datum_definition is not other.datum_definition:
            findings.append(
                "different datum definitions: "
                f"{self.datum_definition.value} and {other.datum_definition.value}; "
                "a coordinate transformation cannot reconcile these"
            )
        return findings

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "network_id": self.network_id,
            "kind": self.kind.name,
            "crs": self.crs,
            "epoch": self.epoch.to_dict(),
            "datum_definition": self.datum_definition.name,
            "adjusted_stations": [a.to_dict() for a in self.adjusted_stations],
            "observation_results": [r.to_dict() for r in self.observation_results],
            "statistics": self.statistics.to_dict(),
            "uncertainty_mode": self.uncertainty_mode.name,
        }
        for key, value in (
            (
                "parameter_covariance",
                self.parameter_covariance.to_dict() if self.parameter_covariance else None,
            ),
            ("provenance", self.provenance.to_dict() if self.provenance else None),
            ("superseded_by", self.superseded_by),
        ):
            if value is not None:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Solution:
        covariance = payload.get("parameter_covariance")
        provenance = payload.get("provenance")
        return cls(
            id=payload["id"],
            network_id=payload["network_id"],
            kind=SolutionKind[payload["kind"]],
            crs=payload["crs"],
            epoch=Epoch.from_dict(payload["epoch"]),
            datum_definition=DatumDefinition[payload["datum_definition"]],
            adjusted_stations=tuple(
                AdjustedStation.from_dict(a) for a in payload.get("adjusted_stations", ())
            ),
            parameter_covariance=Covariance.from_dict(covariance) if covariance else None,
            observation_results=tuple(
                ObservationResult.from_dict(r) for r in payload.get("observation_results", ())
            ),
            statistics=AdjustmentStatistics.from_dict(payload.get("statistics", {})),
            uncertainty_mode=UncertaintyMode[payload["uncertainty_mode"]],
            provenance=Provenance.from_dict(provenance) if provenance else None,
            superseded_by=payload.get("superseded_by"),
        )
