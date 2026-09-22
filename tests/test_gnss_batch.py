# SPDX-License-Identifier: GPL-2.0-or-later
"""A batch that survives a bad session (FR-355).

``specs/11-module-gnss.md`` acceptance criterion: *a batch with one broken
session completes and reports it*. That sentence is the first test here, and the
rest pin the boundaries around it -- what is caught, what is deliberately not,
and the distinction between a session that failed and one that ran and produced
nothing.
"""

from __future__ import annotations

import pytest

from geocomp.core.cancellation import Cancelled
from geocomp.core.errors import DataError, EngineError
from geocomp.core.techniques.gnss.batch import BatchOutcome, run_batch


class TestOneBadSessionDoesNotAbortTheBatch:
    """The acceptance criterion, stated as a test."""

    def test_the_batch_completes_and_names_the_failure(self):
        def work(key):
            if key == "s31":
                raise DataError("rinex_file_empty", file=f"{key}.obs")
            return key.upper()

        report = run_batch([f"s{n}" for n in range(1, 51)], work)

        assert len(report.results) == 50
        assert report.summary() == {"succeeded": 49, "failed": 1, "rejected": 0}
        assert [r.key for r in report.failed] == ["s31"]
        assert report.failed[0].code == "data.rinex_file_empty"
        assert "s31.obs" in report.failed[0].detail
        assert len(report.values) == 49

    def test_the_results_keep_the_input_order(self):
        """A user scanning a campaign looks for session 31, not for the failures."""
        def work(key):
            if key in ("b", "d"):
                raise DataError("rinex_file_empty", file=key)
            return key

        report = run_batch(list("abcde"), work)
        assert [r.key for r in report.results] == list("abcde")

    def test_every_failure_is_reported_not_just_the_first(self):
        def work(key):
            raise DataError("rinex_file_empty", file=key)

        report = run_batch(list("abc"), work)
        assert len(report.failed) == 3
        assert report.all_succeeded is False


class TestRanButSolvedNothing:
    """``specs/07`` §4.3 and ``specs/08``: an exit code of zero is not success."""

    def test_a_rejected_row_is_neither_a_success_nor_a_failure(self):
        report = run_batch(
            ["good", "empty"],
            lambda key: {"epochs": 0 if key == "empty" else 120},
            accept=lambda value: value["epochs"] > 0,
        )
        assert report.summary() == {"succeeded": 1, "failed": 0, "rejected": 1}
        outcomes = {r.key: r.outcome for r in report.results}
        assert outcomes["good"] is BatchOutcome.SUCCEEDED
        assert outcomes["empty"] is BatchOutcome.REJECTED
        assert report.failed[0].key == "empty"
        assert not report.all_succeeded

    def test_a_rejected_row_keeps_its_value_for_inspection(self):
        report = run_batch(["empty"], lambda k: {"epochs": 0}, accept=lambda v: False)
        assert report.results[0].value == {"epochs": 0}


class TestWhatIsDeliberatelyNotCaught:
    def test_cancellation_propagates_rather_than_becoming_a_row(self):
        """The user asked the batch to stop; continuing would ignore them."""
        class Token:
            def __init__(self):
                self.calls = 0

            def is_cancelled(self):
                self.calls += 1
                return self.calls > 2

        token = Token()
        with pytest.raises(Cancelled):
            run_batch(list("abcde"), lambda k: k, token=token)

    def test_an_unexpected_exception_propagates(self):
        """A defect in GeoComp is a bug report, not a data-quality note."""
        def work(key):
            raise ZeroDivisionError("a defect, not a bad session")

        with pytest.raises(ZeroDivisionError):
            run_batch(["a"], work)

    def test_an_engine_error_is_caught_like_any_other_core_error(self):
        report = run_batch(
            ["a"], lambda k: (_ for _ in ()).throw(EngineError("rtklib_produced_no_solution"))
        )
        assert report.failed[0].code == "engine.rtklib_produced_no_solution"


class TestProgressAndReporting:
    def test_progress_runs_from_zero_to_one(self):
        seen = []
        run_batch(list("abcd"), lambda k: k, progress=lambda f, c=None: seen.append(f))
        assert seen[0] == 0.0
        assert seen[-1] == 1.0
        assert seen == sorted(seen)

    def test_an_empty_batch_is_not_a_success(self):
        """Nothing attempted is not everything succeeded."""
        report = run_batch([], lambda k: k)
        assert report.results == ()
        assert report.all_succeeded is False

    def test_the_dictionary_carries_the_summary_and_every_row(self):
        report = run_batch(
            ["ok", "bad"],
            lambda k: k if k == "ok" else (_ for _ in ()).throw(DataError("rinex_file_empty")),
        )
        payload = report.to_dict()
        assert payload["summary"]["succeeded"] == 1
        assert payload["summary"]["failed"] == 1
        assert [row["key"] for row in payload["results"]] == ["ok", "bad"]
        assert payload["results"][1]["code"] == "data.rinex_file_empty"

    def test_each_row_records_how_long_it_took(self):
        report = run_batch(["a"], lambda k: k)
        assert report.results[0].seconds >= 0.0
