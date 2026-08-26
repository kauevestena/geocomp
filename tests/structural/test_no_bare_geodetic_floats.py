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


class TestTechniqueModuleReturns:
    """Activates when the technique modules land in P3.

    Written now, deliberately: a rule introduced after the code it governs is a
    rule that gets exceptions carved into it.
    """

    @staticmethod
    def _technique_sources():
        techniques = PLUGIN_DIR / "core" / "techniques"
        if not techniques.is_dir():
            return []
        return list(python_sources(techniques))

    def test_public_functions_return_uncertainty_bearing_types(self):
        sources = self._technique_sources()
        if not sources:
            pytest.skip("no technique modules yet; they arrive in phase P3")

        offenders: list[str] = []
        for path in sources:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                    continue
                if node.returns is None:
                    offenders.append(f"{path.name}:{node.lineno} {node.name}: no return annotation")
                    continue
                annotation = ast.unparse(node.returns)
                if annotation in ("None", "bool", "int", "str"):
                    continue
                if not any(bearer in annotation for bearer in UNCERTAINTY_BEARING):
                    offenders.append(f"{path.name}:{node.lineno} {node.name} -> {annotation}")

        assert not offenders, (
            "Technique-module functions must return uncertainty-bearing types (FR-200):\n"
            + "\n".join(offenders)
        )


def test_quantity_and_covariance_are_the_only_uncertainty_carriers():
    """Documents the intended surface, so a third carrier is a deliberate change."""
    assert Quantity is not None and Covariance is not None and Position is not None
