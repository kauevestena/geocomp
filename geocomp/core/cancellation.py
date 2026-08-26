# SPDX-License-Identifier: GPL-2.0-or-later
"""Cancellation and progress protocols for long-running core operations.

``specs/03-architecture.md`` section 3.5: core functions are synchronous and
cancellation-aware through an injected callback. They know nothing about
``QgsTask``; wrapping them in one is the service layer's job. That separation is
what lets the whole computation layer be tested without a QGIS runtime.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = [
    "NULL_CANCELLATION",
    "CancellationToken",
    "Cancelled",
    "NullCancellation",
    "ProgressCallback",
]


class Cancelled(Exception):  # noqa: N818 - not an error; see the docstring
    """Raised inside a core operation when cancellation has been requested.

    Not a :class:`~geocomp.core.errors.GeoCompError`: cancellation is a normal
    outcome the user asked for, not a failure to report.
    """


@runtime_checkable
class CancellationToken(Protocol):
    """Something a core operation can poll to learn it should stop."""

    def is_cancelled(self) -> bool:
        """Return ``True`` once cancellation has been requested."""
        ...


@runtime_checkable
class ProgressCallback(Protocol):
    """Reports progress out of a core operation.

    Args:
        fraction: Completion in ``[0.0, 1.0]``, or ``None`` when the work is not
            countable and progress should read as indeterminate.
        message_code: A stable message code, never a phrased sentence -- the
            core does not compose user-facing text (NFR-002).
    """

    def __call__(self, fraction: float | None, message_code: str | None = None) -> None: ...


class NullCancellation:
    """A token that is never cancelled, for callers with nothing to cancel."""

    __slots__ = ()

    def is_cancelled(self) -> bool:
        return False


NULL_CANCELLATION = NullCancellation()


def raise_if_cancelled(token: CancellationToken | None) -> None:
    """Raise :class:`Cancelled` if *token* reports cancellation.

    ``None`` is accepted so callers need not construct a null token.
    """
    if token is not None and token.is_cancelled():
        raise Cancelled()
