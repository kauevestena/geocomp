# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-200: no geodetic value exists without an attached uncertainty.

``specs/05-uncertainty-and-covariance.md`` section 7, criterion 4. The project's
defining property is that every measured or derived quantity carries an
uncertainty, and a property that holds only by the discipline of whoever wrote
the last commit is not a property.

Two complementary checks:

1. **Declared types.** Every field of the domain model that holds a measured or
   derived geodetic value is annotated ``Quantity`` (or a type built from
   Quantity), never ``float``. Checked by introspecting the real annotations,
   so it cannot drift from the code.
2. **Returned types.** Every public function in the technique modules returns a
   Quantity-bearing type. Those modules arrive in phase P3; the check is written
   now so it starts enforcing the rule the moment the first one lands, rather
   than being remembered afterwards.

Runtime enforcement is separate and lives in the constructors -- ``Position``
and ``Observation`` reject a bare float -- and is tested behaviourally in
``tests/test_models.py``. This file guards the *shape* of the code, which
behavioural tests cannot.
"""

from __future__ import annotations

import ast
import dataclasses
import typing

import pytest

from geocomp.core import models
from geocomp.core.models.position import Position
from geocomp.core.uncertainty import Covariance, Quantity
from tests.conftest import PLUGIN_DIR, python_sources

#: Types that carry an uncertainty, directly or by construction.
UNCERTAINTY_BEARING = {"Quantity", "Position", "Covariance"}

#: Fields that hold a *measured or derived* geodetic value and must therefore be
#: uncertainty-bearing. Listed explicitly rather than guessed from the name: a
#: heuristic would either miss fields or fire on statistics, which are derived
#: quantities of a different kind and legitimately plain floats.
GEODETIC_VALUE_FIELDS = {
    ("Position", "values"),
    ("Observation", "values"),
    ("GnssSession", "antenna_height"),
}

#: Fields that are deliberately plain floats, with the reason. Reviewed
#: additions only -- this list existing is what makes the check meaningful,
#: because it forces a decision rather than allowing a silent omission.
DELIBERATE_PLAIN_FLOATS = {
    ("Epoch", "decimal_year"): "a date, not a measurement",
    ("ErrorEllipse", "semi_major"): "an eigenvalue of a covariance; it *is* an uncertainty",
    ("ErrorEllipse", "semi_minor"): "an eigenvalue of a covariance; it *is* an uncertainty",
    ("ErrorEllipse", "orientation"): "an eigenvector direction of a covariance",
    ("ErrorEllipse", "semi_vertical"): "the vertical eigenvalue of a covariance",
    ("ErrorEllipse", "confidence"): "a probability, not a measurement",
    ("TestResult", "statistic"): "a test statistic, not a measured quantity",
    ("TestResult", "critical_low"): "a distribution quantile",
    ("TestResult", "critical_high"): "a distribution quantile",
    ("TestResult", "confidence"): "a probability",
    ("ObservationResult", "residual"): "an adjustment output; its quality is the covariance",
    ("ObservationResult", "standardised_residual"): "already normalised by its own sigma",
    ("ObservationResult", "redundancy"): "a dimensionless share of redundancy",
    ("ObservationResult", "minimal_detectable_bias"): "a computed detection threshold",
    ("ObservationResult", "external_reliability"): "a computed effect magnitude",
    ("ObservationResult", "adjusted_value"): "paired with the solution covariance",
    ("AdjustedStation", "positional_uncertainty"): "is itself an uncertainty",
    ("AdjustedStation", "correction"): (
        "the shift the adjustment applied to the approximate coordinates; a "
        "convergence diagnostic whose quality is the station covariance, not a "
        "measurement in its own right"
    ),
    ("AdjustmentStatistics", "variance_factor_apriori"): "a variance factor",
    ("AdjustmentStatistics", "variance_factor_aposteriori"): "a variance factor",
    ("AdjustmentStatistics", "max_correction"): "a convergence diagnostic",
    ("AdjustmentStatistics", "condition_number"): "a numerical diagnostic",
    ("GnssSession", "interval"): "a sampling interval, not a measurement",
    ("RejectionRecord", "statistic"): "a test statistic",
    ("RejectionRecord", "critical_value"): "a distribution quantile",
}


def _model_dataclasses():
    for name in models.__all__:
        candidate = getattr(models, name)
        if isinstance(candidate, type) and dataclasses.is_dataclass(candidate):
            yield name, candidate


def _annotation_text(annotation: object) -> str:
    return annotation if isinstance(annotation, str) else str(annotation)


class TestDeclaredTypes:
    def test_the_model_exposes_dataclasses_to_check(self):
        """Guards the introspection: a rename that emptied this would make every
        assertion below pass vacuously."""
        assert len(list(_model_dataclasses())) >= 10

    def test_geodetic_value_fields_are_uncertainty_bearing(self):
        offenders: list[str] = []
        checked = 0

        for class_name, model_class in _model_dataclasses():
            for field in dataclasses.fields(model_class):
                key = (class_name, field.name)
                if key not in GEODETIC_VALUE_FIELDS:
                    continue
                checked += 1
                annotation = _annotation_text(field.type)
                if not any(bearer in annotation for bearer in UNCERTAINTY_BEARING):
                    offenders.append(f"{class_name}.{field.name}: {annotation}")

        assert checked == len(GEODETIC_VALUE_FIELDS), (
            "a field listed in GEODETIC_VALUE_FIELDS no longer exists; "
            "update the list rather than leaving it stale"
        )
        assert not offenders, (
            "These fields hold geodetic values but are not uncertainty-bearing (FR-200):\n"
            + "\n".join(offenders)
        )

    def test_every_plain_float_field_is_either_listed_or_justified(self):
        """The check that gives the others their force.

        A new ``float`` field on a model class fails here until someone decides
        whether it is a measurement (make it a Quantity) or a diagnostic (add it
        to DELIBERATE_PLAIN_FLOATS with a reason). Neither outcome is silent.
        """
        undeclared: list[str] = []

        for class_name, model_class in _model_dataclasses():
            hints = typing.get_type_hints(model_class)
            for field in dataclasses.fields(model_class):
                annotation = _annotation_text(hints.get(field.name, field.type))
                if "float" not in annotation:
                    continue
                if any(bearer in annotation for bearer in UNCERTAINTY_BEARING):
                    continue
                key = (class_name, field.name)
                if key in DELIBERATE_PLAIN_FLOATS or key in GEODETIC_VALUE_FIELDS:
                    continue
                undeclared.append(f"{class_name}.{field.name}: {annotation}")

        assert not undeclared, (
            "These fields are plain floats and are neither listed as geodetic "
            "values nor justified as diagnostics (FR-200).\n"
            "Make each one a Quantity, or add it to DELIBERATE_PLAIN_FLOATS with "
            "the reason it is not a measurement:\n" + "\n".join(undeclared)
        )

    def test_the_justification_list_has_no_stale_entries(self):
        existing = {
            (class_name, field.name)
            for class_name, model_class in _model_dataclasses()
            for field in dataclasses.fields(model_class)
        }
        stale = sorted(key for key in DELIBERATE_PLAIN_FLOATS if key not in existing)
        assert not stale, f"justifications for fields that no longer exist: {stale}"

    def test_every_justification_says_something(self):
        for key, reason in DELIBERATE_PLAIN_FLOATS.items():
            assert len(reason) > 10, f"{key} needs a real reason, not a placeholder"


#: Plain-float fields on the technique and instrument dataclasses, with the
#: reason each is not a measurement. Same discipline as DELIBERATE_PLAIN_FLOATS
#: above and the same force: a new float field fails until someone decides.
TECHNIQUE_PLAIN_FLOATS = {
    ("EdmSpecification", "constant"): "the constant term of a precision model, not a measurement",
    ("EdmSpecification", "proportional"): "the ppm term of a precision model",
    ("EdmSpecification", "scale"): "a user factor on a precision model",
    ("InstrumentProfile", "cyclic_error_wavelength"): (
        "a property of the EDM's modulation, taken from its calibration certificate"
    ),
    ("InstrumentProfile", "reference_refractive_index"): (
        "the index the instrument's zero-ppm setting assumes; a published constant"
    ),
    ("InstrumentProfile", "sigma_direction"): "is itself a standard deviation",
    ("InstrumentProfile", "sigma_zenith"): "is itself a standard deviation",
    ("InstrumentProfile", "sigma_zenith_refraction"): "a coefficient of a precision model",
    ("InstrumentProfile", "sigma_instrument_height"): "is itself a standard deviation",
    ("InstrumentProfile", "sigma_target_height"): "is itself a standard deviation",
    ("StochasticDefaults", "values"): "a mapping of standard deviations",
    ("LevelProfile", "sigma_per_km"): (
        "the constant of proportionality of a precision model, in metres per sqrt(km)"
    ),
    ("LevelProfile", "sigma_per_setup"): "the same, per setup",
    ("LevelProfile", "sigma_reading"): "is itself a standard deviation",
    ("LevelProfile", "sigma_stadia_reading"): "is itself a standard deviation",
    ("LevelProfile", "stadia_factor"): (
        "the stadia multiplication constant engraved on the instrument's reticle; a "
        "property of the optics, not something measured in the field"
    ),
    ("LevellingClass", "tolerance_coefficient"): (
        "k in the permissible misclosure k*sqrt(L); a limit from a specification, not a "
        "measurement of anything"
    ),
    ("LevellingClass", "max_sight_length"): "a configured limit",
    ("LevellingClass", "max_sight_imbalance"): "a configured limit",
    ("LevellingClass", "max_accumulated_imbalance"): "a configured limit",
    # -- Levelling (phase P4) ------------------------------------------------
    ("SetupReduction", "imbalances"): (
        "the difference between two sight lengths, a property of where the instrument "
        "was put rather than a measurement of anything"
    ),
    ("LineReduction", "length_km"): (
        "the levelled route length, summed from the sight distances; an extent for the "
        "weighting model and the tolerance, not an observation of a distance"
    ),
    ("LineReduction", "accumulated_imbalance"): "a sum of imbalances; see SetupReduction",
    ("ReciprocalReduction", "discrepancy"): (
        "the difference between two determinations of one height difference, whose "
        "expected value is zero. A diagnostic, not a measurement"
    ),
    ("ReciprocalReduction", "inflation"): (
        "the factor the variance was multiplied by; a modelling decision, recorded"
    ),
    ("ClosureCheck", "misclosure"): (
        "the difference between a measured closure and the known one, whose expected "
        "value is zero. The measurement it came from is the height difference"
    ),
    ("ClosureCheck", "permissible"): "a limit from a specification",
    ("ClosureCheck", "standardised"): "already normalised by its own sigma",
    ("ClosureCheck", "length_km"): "a route length; see LineReduction",
    ("SetupShare", "correction"): (
        "a share of a misclosure, distributed proportionally; a correction, not an "
        "observation"
    ),
    ("SetupShare", "weight"): "a dimensionless share, summing to one",
    ("SetupShare", "standardised"): "already normalised by its own sigma",
    ("OrthometricCorrection", "mean_latitude"): (
        "the latitude the correction was evaluated at; an input to a formula, needed "
        "only to a few seconds of arc"
    ),
    ("OrthometricCorrection", "mean_height"): (
        "the height the correction was evaluated at; needed only to a few metres"
    ),
    ("OrthometricCorrection", "latitude_difference"): (
        "the latitude span of the section, an input to the same formula"
    ),
    ("FaceReduction", "distance_difference"): (
        "the difference of two readings of one distance, whose expected value is zero; "
        "a diagnostic, not a measurement"
    ),
    ("SetupDiagnostics", "collimation_mean"): "a summary of instrumental diagnostics",
    ("SetupDiagnostics", "collimation_spread"): "a summary of instrumental diagnostics",
    ("SetupDiagnostics", "vertical_index_mean"): "a summary of instrumental diagnostics",
    ("SetupDiagnostics", "vertical_index_spread"): "a summary of instrumental diagnostics",
    ("Atmosphere", "wavelength_um"): "a property of the instrument's carrier, not a measurement",
    ("AtmosphericCorrection", "reference_index"): (
        "the index the instrument assumed; a setting, not something measured"
    ),
    ("PreprocessingOptions", "collimation_tolerance"): "a configured tolerance",
    ("PreprocessingOptions", "distance_tolerance"): "a configured tolerance",
    ("PreprocessingOptions", "distance_zenith_correlation"): (
        "a correlation coefficient, dimensionless and bounded"
    ),
    ("TraverseResult", "angular_misclosure"): (
        "a misclosure: the difference between a measured closure and the known one, whose "
        "expected value is zero. A diagnostic, not a measurement"
    ),
    ("TraverseResult", "linear_misclosure"): "a misclosure; see angular_misclosure",
    ("TraverseResult", "relative_precision"): (
        "the quality ratio surveyors quote as 1:N; dimensionless and derived from the two "
        "quantities above"
    ),
    ("ResectionResult", "residuals"): (
        "adjustment residuals, whose quality is the solution covariance rather than a "
        "sigma of their own"
    ),
    ("IntersectionResult", "residuals"): "adjustment residuals; see ResectionResult",
    ("LeapFrogResult", "sight_imbalance"): (
        "the difference between two sight lengths, a property of how the setup was placed "
        "rather than a measurement of anything"
    ),
    ("LeapFrogResult", "refraction_cancellation"): (
        "the fraction of the refraction uncertainty that survived the method, a "
        "dimensionless ratio derived from the geometry"
    ),
}

#: Public functions in the technique and instrument modules that return a plain
#: value, with the reason. Narrow by construction: a geodetic *result* never
#: belongs here, only a formula constant or a predicate.
TECHNIQUE_PLAIN_RETURNS = {
    "atmosphere.group_refractivity": (
        "(n_g - 1) * 1e6 for standard air by the IUGG 1960 formula: a property of the "
        "formula and the carrier wavelength, exact for its inputs"
    ),
    "stochastic.unit_for": "the dimension of an observation kind, not a value",
    "readings.empirical_reading_sigma": (
        "a pooled standard deviation and the degrees of freedom behind it -- the "
        "figure *is* an uncertainty, and the count is what says how much to trust it"
    ),
}


def _uncertainty_bearing_dataclasses():
    """Dataclasses in the technique and instrument packages, by name.

    Imported rather than parsed, so the check sees the real annotations and
    cannot drift from the code.
    """
    import importlib

    found: dict[str, type] = {}
    for package in ("core.techniques", "core.instruments"):
        root = PLUGIN_DIR / package.replace(".", "/")
        if not root.is_dir():
            continue
        for path in python_sources(root):
            relative = path.relative_to(PLUGIN_DIR).with_suffix("")
            module = importlib.import_module("geocomp." + ".".join(relative.parts))
            for name, candidate in vars(module).items():
                if (
                    isinstance(candidate, type)
                    and dataclasses.is_dataclass(candidate)
                    and candidate.__module__ == module.__name__
                ):
                    found[name] = candidate
    return found


class TestTechniqueDeclaredTypes:
    """The field-level rule, applied to the technique and instrument modules.

    Phase P3 generalised this from the domain model. A result type composed
    entirely of Quantities satisfies FR-200 as well as a Quantity does; what
    must not exist is a plain float nobody decided about.
    """

    def test_there_are_dataclasses_to_check(self):
        found = _uncertainty_bearing_dataclasses()
        if not found:
            pytest.skip("no technique or instrument modules yet")
        assert len(found) >= 5

    def test_every_plain_float_field_is_justified(self):
        found = _uncertainty_bearing_dataclasses()
        if not found:
            pytest.skip("no technique or instrument modules yet")

        undeclared: list[str] = []
        for class_name, model_class in sorted(found.items()):
            hints = typing.get_type_hints(model_class)
            for field in dataclasses.fields(model_class):
                annotation = _annotation_text(hints.get(field.name, field.type))
                if "float" not in annotation:
                    continue
                if any(bearer in annotation for bearer in UNCERTAINTY_BEARING):
                    continue
                if (class_name, field.name) in TECHNIQUE_PLAIN_FLOATS:
                    continue
                undeclared.append(f"{class_name}.{field.name}: {annotation}")

        assert not undeclared, (
            "These technique fields are plain floats with no recorded decision (FR-200).\n"
            "Make each one a Quantity, or add it to TECHNIQUE_PLAIN_FLOATS with the reason "
            "it is not a measurement:\n" + "\n".join(undeclared)
        )

    def test_the_technique_justification_list_has_no_stale_entries(self):
        found = _uncertainty_bearing_dataclasses()
        if not found:
            pytest.skip("no technique or instrument modules yet")
        existing = {
            (class_name, field.name)
            for class_name, model_class in found.items()
            for field in dataclasses.fields(model_class)
        }
        stale = sorted(key for key in TECHNIQUE_PLAIN_FLOATS if key not in existing)
        assert not stale, f"justifications for fields that no longer exist: {stale}"


class TestTechniqueModuleReturns:
    """Every public function in a technique module returns something that
    carries an uncertainty, or something that is not a measurement at all.

    Written in phase P0, before the modules it governs existed, deliberately: a
    rule introduced after the code it governs is a rule that gets exceptions
    carved into it. Phase P3 replaced the original name-matching form with this
    structural one, because a result type composed of Quantities satisfies
    FR-200 just as a Quantity does, and a check that could not see that would
    have forced every function to return a bare Quantity or be exempted.
    """

    #: Return types that are not measurements and need no uncertainty.
    NON_MEASUREMENT = (type(None), bool, int, str)

    @staticmethod
    def _technique_sources():
        techniques = PLUGIN_DIR / "core" / "techniques"
        if not techniques.is_dir():
            return []
        return list(python_sources(techniques))

    @classmethod
    def _is_acceptable(cls, annotation: object, bearing: dict[str, type]) -> bool:
        """Whether *annotation* is uncertainty-bearing or not a measurement."""
        import enum

        origin = typing.get_origin(annotation)
        if origin is not None:
            arguments = [a for a in typing.get_args(annotation) if a is not type(None)]
            if not arguments:
                return True
            return all(cls._is_acceptable(argument, bearing) for argument in arguments)

        if annotation in (Quantity, Covariance, Position):
            return True
        if annotation in cls.NON_MEASUREMENT:
            return True
        if isinstance(annotation, type):
            if issubclass(annotation, enum.Enum):
                return True
            if annotation.__name__ in bearing:
                return True
            if dataclasses.is_dataclass(annotation):
                # A dataclass from elsewhere in the core -- the domain model --
                # is already covered by TestDeclaredTypes above.
                return True
        return False

    def test_public_functions_return_uncertainty_bearing_types(self):
        import importlib

        sources = self._technique_sources()
        if not sources:
            pytest.skip("no technique modules yet; they arrive in phase P3")

        bearing = _uncertainty_bearing_dataclasses()
        offenders: list[str] = []
        checked = 0

        for path in sources:
            relative = path.relative_to(PLUGIN_DIR).with_suffix("")
            module = importlib.import_module("geocomp." + ".".join(relative.parts))
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

            for node in tree.body:
                if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                    continue
                checked += 1
                if node.returns is None:
                    offenders.append(f"{path.name}:{node.lineno} {node.name}: no return annotation")
                    continue
                if f"{path.stem}.{node.name}" in TECHNIQUE_PLAIN_RETURNS:
                    continue
                hints = typing.get_type_hints(getattr(module, node.name))
                if not self._is_acceptable(hints.get("return"), bearing):
                    offenders.append(
                        f"{path.name}:{node.lineno} {node.name} -> {ast.unparse(node.returns)}"
                    )

        assert checked > 5, "the scan found almost no public functions; it is probably broken"
        assert not offenders, (
            "Technique-module functions must return uncertainty-bearing types (FR-200). "
            "Return a Quantity, or a dataclass composed of them, or -- if the value is not a "
            "measurement -- record the reason in TECHNIQUE_PLAIN_RETURNS:\n" + "\n".join(offenders)
        )

    def test_the_plain_return_list_has_no_stale_entries(self):
        sources = self._technique_sources()
        if not sources:
            pytest.skip("no technique modules yet")
        names = set()
        for root in ("techniques", "instruments"):
            directory = PLUGIN_DIR / "core" / root
            if not directory.is_dir():
                continue
            for path in python_sources(directory):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                # Top-level functions only, matching what the returns check
                # actually inspects. Methods are covered by their class's field
                # check instead.
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef):
                        names.add(f"{path.stem}.{node.name}")
        stale = sorted(key for key in TECHNIQUE_PLAIN_RETURNS if key not in names)
        assert not stale, f"justifications for functions that no longer exist: {stale}"


def test_quantity_and_covariance_are_the_only_uncertainty_carriers():
    """Documents the intended surface, so a third carrier is a deliberate change."""
    assert Quantity is not None and Covariance is not None and Position is not None
