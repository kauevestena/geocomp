# SPDX-License-Identifier: GPL-2.0-or-later
"""``services/task_service.py`` -- the FR-008 threading layer.

**Written by the pre-P7 review**, which found this module at **0% coverage with
no caller anywhere in the plugin**. It is not dead by accident: everything that
takes real time in GeoComp is a Processing algorithm, and Processing threads
its own algorithms and supplies its own `QgsProcessingFeedback`, so nothing has
needed a `QgsTask` of its own yet -- `specs/16` §7 names that as the FR-008
mechanism there. The one main-thread computation the plugin does have is the
pre-analysis dialog's `DesignSession.evaluate()`, on networks of a few dozen
stations.

That leaves an untested module implementing an architectural rule
(`specs/03` §3.5) that the first caller will rely on. The rule is the valuable
part -- no QGIS mutation off the main thread, cancellation cooperative through
a plain token -- and it is exactly the kind of thing that is subtly wrong the
first time it is used and hard to debug then. So the behaviour is tested here,
without going through the task manager: `run` and `finished` are called
directly, which is what the manager does and what makes the sequencing
assertable.
"""

from __future__ import annotations

import pytest

from geocomp.core.cancellation import Cancelled
from geocomp.core.errors import ComputationError

pytestmark = pytest.mark.qgis


@pytest.fixture
def task_service(qgis_app):
    del qgis_app
    from geocomp.services import task_service

    return task_service


class TestItRunsTheWork:
    def test_the_result_reaches_on_success(self, task_service):
        seen = []
        task = task_service.GeoCompTask(
            "compute", lambda cancellation, progress: 42, on_success=seen.append
        )
        assert task.run() is True
        task.finished(True)
        assert seen == [42]

    def test_the_work_is_given_no_qgis_object_to_mutate(self, task_service):
        """``specs/03`` §3.5, enforced by the shape of the module: the callable
        receives a cancellation token and a progress function, and nothing
        else."""
        captured = {}

        def work(cancellation, progress):
            captured["cancellation"] = cancellation
            captured["progress"] = progress
            return None

        task_service.GeoCompTask("compute", work).run()
        assert isinstance(captured["cancellation"], task_service.TaskCancellation)
        assert callable(captured["progress"])
        assert not hasattr(captured["cancellation"], "addTask")


class TestProgress:
    def test_a_fraction_becomes_a_percentage(self, task_service):
        task = task_service.GeoCompTask(
            "compute", lambda cancellation, progress: progress(0.25)
        )
        task.run()
        assert task.progress() == pytest.approx(25.0)

    @pytest.mark.parametrize(("fraction", "expected"), [(-1.0, 0.0), (2.0, 100.0)])
    def test_a_fraction_outside_the_range_is_clamped(self, task_service, fraction, expected):
        """QgsTask takes 0..100 and a core function that miscounts its own work
        should not put the task manager into an undefined state."""
        task = task_service.GeoCompTask(
            "compute", lambda cancellation, progress: progress(fraction)
        )
        task.run()
        assert task.progress() == pytest.approx(expected)

    def test_an_indeterminate_step_leaves_the_progress_alone(self, task_service):
        """FR-008 asks for determinate progress *where the work is countable*.
        Passing ``None`` is how a step says it is not."""
        def work(cancellation, progress):
            progress(0.5)
            progress(None, "still_going")

        task = task_service.GeoCompTask("compute", work)
        task.run()
        assert task.progress() == pytest.approx(50.0)


class TestCancellation:
    def test_the_token_reports_what_the_task_reports(self, task_service):
        task = task_service.GeoCompTask("compute", lambda cancellation, progress: None)
        token = task_service.TaskCancellation(task)
        assert token.is_cancelled() is False
        task.cancel()
        assert token.is_cancelled() is True

    def test_raising_cancelled_is_not_an_error(self, task_service):
        """The distinction that matters at the other end: a cancelled run must
        not be reported to the user as a failure."""
        errors, cancels = [], []

        def work(cancellation, progress):
            raise Cancelled()

        task = task_service.GeoCompTask(
            "compute", work, on_error=errors.append, on_cancel=lambda: cancels.append(True)
        )
        assert task.run() is False
        task.finished(False)
        assert errors == []
        assert cancels == [True]


class TestFailure:
    def test_the_exception_is_re_raised_to_the_main_thread(self, task_service):
        """Not swallowed on the worker thread, where nothing can report it."""
        seen = []
        failure = ComputationError("singular_normal_matrix")

        def work(cancellation, progress):
            raise failure

        task = task_service.GeoCompTask("compute", work, on_error=seen.append)
        assert task.run() is False
        task.finished(False)
        assert seen == [failure]

    def test_a_failure_with_no_handler_is_logged_not_lost(self, task_service, monkeypatch):
        logged = []
        monkeypatch.setattr(
            task_service.log, "exception", lambda exc, **kw: logged.append((exc, kw))
        )

        def work(cancellation, progress):
            raise ComputationError("singular_normal_matrix")

        task = task_service.GeoCompTask("compute", work)
        task.run()
        task.finished(False)
        assert len(logged) == 1
        assert "task failed" in logged[0][1]["message"]

    def test_an_unexpected_failure_says_so(self, task_service, monkeypatch):
        """A ``GeoCompError`` is a diagnosed condition; anything else is a bug,
        and the log must not present the two the same way."""
        logged = []
        monkeypatch.setattr(
            task_service.log, "exception", lambda exc, **kw: logged.append((exc, kw))
        )

        def work(cancellation, progress):
            raise ZeroDivisionError("division by zero")

        task = task_service.GeoCompTask("compute", work)
        task.run()
        task.finished(False)
        assert "unexpectedly" in logged[0][1]["message"]

    def test_a_cancellation_with_no_handler_is_logged_at_info(self, task_service, monkeypatch):
        logged = []
        monkeypatch.setattr(task_service.log, "info", lambda msg, **kw: logged.append(msg))
        task = task_service.GeoCompTask("compute", lambda c, p: (_ for _ in ()).throw(Cancelled()))
        task.run()
        task.finished(False)
        assert logged == ["task cancelled"]


class TestSubmission:
    def test_run_task_hands_it_to_the_manager_and_returns_it(self, task_service, qgis_app):
        """The return value is the point: the caller must keep a reference, or
        the task can be collected before ``finished`` runs."""
        del qgis_app
        task = task_service.GeoCompTask("compute", lambda cancellation, progress: 1)
        assert task_service.run_task(task) is task
        task.cancel()
