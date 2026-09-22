# SPDX-License-Identifier: GPL-2.0-or-later
"""Batch processing that survives a bad session (FR-355).

``specs/11-module-gnss.md`` section 2. The requirement's exact words are
"per-session error reporting **that does not abort the batch**", and that
clause is the entire design. A campaign is fifty sessions collected over a
fortnight; one of them has a truncated file because a battery died, and a batch
that stops there has wasted the night it ran in and told the user about one
problem when there may be three.

So every session is attempted, every failure is caught **by kind**, and the
outcome is a report in which a failure is a first-class row rather than an
absence. ``specs/11`` acceptance criterion: *a batch with one broken session
completes and reports it*.

**Two things are deliberately not caught.** :class:`~geocomp.core.cancellation.Cancelled`
propagates, because the user asked for the batch to stop and continuing would
be ignoring them. Anything that is not a :class:`~geocomp.core.errors.GeoCompError`
propagates too: an unexpected exception is a defect in GeoComp, and swallowing
it into a per-session row would turn a bug report into a data-quality note. The
batch catches the failures it *understands* and lets the rest reach the surface.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

from geocomp.core.cancellation import (
    CancellationToken,
    Cancelled,
    ProgressCallback,
    raise_if_cancelled,
)
from geocomp.core.errors import GeoCompError

__all__ = ["BatchOutcome", "BatchReport", "BatchResult", "run_batch"]

T = TypeVar("T")


class BatchOutcome(Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    #: Attempted, ran, and produced something GeoComp will not call a solution.
    #: Distinct from FAILED because the engine did not error -- ``specs/07``
    #: section 4.3 records the lesson that an exit code of zero is not success.
    REJECTED = "rejected"


@dataclass(frozen=True)
class BatchResult(Generic[T]):
    """One session's outcome, whichever way it went."""

    key: str
    outcome: BatchOutcome
    value: T | None = None
    code: str = ""
    detail: str = ""
    seconds: float = 0.0

    @property
    def ok(self) -> bool:
        return self.outcome is BatchOutcome.SUCCEEDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "outcome": self.outcome.value,
            "code": self.code,
            "detail": self.detail,
            "seconds": round(self.seconds, 3),
        }


@dataclass
class BatchReport(Generic[T]):
    """What the batch did, in full.

    ``results`` keeps the input order rather than grouping by outcome: a user
    scanning a campaign wants to find session 31, not to find the failures.
    """

    results: tuple[BatchResult[T], ...] = ()
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> tuple[BatchResult[T], ...]:
        return tuple(r for r in self.results if r.outcome is BatchOutcome.SUCCEEDED)

    @property
    def failed(self) -> tuple[BatchResult[T], ...]:
        return tuple(r for r in self.results if r.outcome is not BatchOutcome.SUCCEEDED)

    @property
    def values(self) -> list[T]:
        """Just the successes' payloads, for the common next step."""
        return [r.value for r in self.results if r.value is not None]

    @property
    def all_succeeded(self) -> bool:
        return bool(self.results) and not self.failed

    def summary(self) -> dict[str, int]:
        counts = dict.fromkeys((o.value for o in BatchOutcome), 0)
        for result in self.results:
            counts[result.outcome.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "results": [r.to_dict() for r in self.results],
            **({"meta": dict(self.meta)} if self.meta else {}),
        }


def run_batch(
    keys: Sequence[str],
    work: Callable[[str], T],
    *,
    token: CancellationToken | None = None,
    progress: ProgressCallback | None = None,
    accept: Callable[[T], bool] | None = None,
) -> BatchReport[T]:
    """Run *work* over every key, reporting failures rather than raising them.

    Args:
        accept: Optional check applied to a successful return. Where it says no,
            the row is :attr:`BatchOutcome.REJECTED` rather than succeeded --
            for the case an engine exits cleanly having solved nothing, which
            ``specs/08`` records as a real behaviour of ``rnx2rtkp``.

    Raises:
        Cancelled: when *token* is cancelled, checked before each session so a
            long batch stops promptly rather than at the end.
    """
    results: list[BatchResult[T]] = []
    total = len(keys)
    for index, key in enumerate(keys):
        raise_if_cancelled(token)
        if progress is not None:
            progress(index / total if total else None, "batch.session_started")

        started = time.monotonic()
        try:
            value = work(key)
        except Cancelled:
            # The user's decision, not a session's failure. Let it out.
            raise
        except GeoCompError as error:
            results.append(
                BatchResult(
                    key=key,
                    outcome=BatchOutcome.FAILED,
                    code=error.code,
                    detail=str(error),
                    seconds=time.monotonic() - started,
                )
            )
            continue

        elapsed = time.monotonic() - started
        if accept is not None and not accept(value):
            results.append(
                BatchResult(
                    key=key,
                    outcome=BatchOutcome.REJECTED,
                    value=value,
                    code="batch.session_rejected",
                    detail="the session ran but its result did not qualify",
                    seconds=elapsed,
                )
            )
            continue
        results.append(
            BatchResult(key=key, outcome=BatchOutcome.SUCCEEDED, value=value, seconds=elapsed)
        )

    if progress is not None:
        progress(1.0, "batch.finished")
    return BatchReport(results=tuple(results))
