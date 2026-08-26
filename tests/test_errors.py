# SPDX-License-Identifier: GPL-2.0-or-later
"""The exception hierarchy (specs/03 section 3.6)."""

from __future__ import annotations

import pytest

from geocomp.core.errors import (
    ComputationError,
    DataError,
    EngineError,
    EngineMissingError,
    GeoCompError,
    StorageError,
    ValidationError,
)


class TestCodes:
    def test_bare_code_is_namespaced_by_the_subclass(self):
        assert ValidationError("missing_epoch").code == "validation.missing_epoch"
        assert DataError("unknown_station").code == "data.unknown_station"
        assert ComputationError("singular").code == "computation.singular"
        assert StorageError("locked").code == "storage.locked"

    def test_an_already_namespaced_code_is_left_alone(self):
        """Lets a module own a finer namespace without double-prefixing."""
        assert ValidationError("import.bad_row").code == "import.bad_row"

    def test_engine_missing_shares_the_engine_namespace(self):
        """It is a kind of engine failure; its code space should say so."""
        assert EngineMissingError("not_installed").code == "engine.not_installed"
        assert isinstance(EngineMissingError("x"), EngineError)

    def test_empty_code_is_rejected(self):
        with pytest.raises(ValueError):
            ValidationError("")


class TestContext:
    def test_context_is_preserved(self):
        error = ValidationError("bad", parameter="epoch", expected="a date", received=None)
        assert error.context == {"parameter": "epoch", "expected": "a date", "received": None}

    def test_str_is_deterministic_regardless_of_keyword_order(self):
        """str() feeds logs and diffs; unstable ordering would make both noisy."""
        first = ValidationError("bad", b=2, a=1)
        second = ValidationError("bad", a=1, b=2)
        assert str(first) == str(second)

    def test_str_without_context_is_just_the_code(self):
        assert str(ValidationError("bad")) == "validation.bad"

    def test_to_dict_round_trips_for_provenance(self):
        error = EngineError("failed", engine="dynadjust", exit_code=2)
        assert error.to_dict() == {
            "type": "EngineError",
            "code": "engine.failed",
            "context": {"engine": "dynadjust", "exit_code": 2},
        }

    def test_context_view_does_not_alias_the_context(self):
        error = ValidationError("bad", parameter="epoch")
        error.context_view["parameter"] = "tampered"
        assert error.context["parameter"] == "epoch"


class TestHierarchy:
    @pytest.mark.parametrize(
        "cls", [ValidationError, DataError, ComputationError, EngineError, StorageError]
    )
    def test_every_error_is_catchable_as_the_base(self, cls):
        """One except clause must be able to catch anything GeoComp raises."""
        with pytest.raises(GeoCompError):
            raise cls("boom")

    def test_geocomp_errors_are_exceptions(self):
        assert issubclass(GeoCompError, Exception)
