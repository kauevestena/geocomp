# SPDX-License-Identifier: GPL-2.0-or-later
"""The GeoComp exception hierarchy.

Specified in ``specs/03-architecture.md`` section 3.6 (NFR-006).

Errors carry a stable machine-readable ``code`` and a ``context`` mapping, not a
sentence. The core cannot produce a user-facing string: it has no access to the
translation layer (NFR-002), and phrasing an error is a presentation concern
(``specs/18-i18n-and-profiles.md`` section 2). ``geocomp.services.messages``
turns a code plus its context into a translated message.

``str(exc)`` yields a *developer-facing* diagnostic for logs and tracebacks. It
is deliberately not the text shown to a user.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = [
    "ComputationError",
    "DataError",
    "EngineError",
    "EngineMissingError",
    "GeoCompError",
    "StorageError",
    "ValidationError",
]


class GeoCompError(Exception):
    """Base class for every error GeoComp raises deliberately.

    Args:
        code: Stable identifier, ``lower_snake_case``, unique across the
            project. It is part of the public interface: it appears in
            provenance records and is the key used to look up a translated
            message, so renaming one is a breaking change.
        **context: Structured detail the presentation layer interpolates into
            the translated message, and that the log records verbatim. Values
            must be plain data (str, numbers, sequences, mappings) so they
            survive serialisation into a provenance record.
    """

    #: Prefix applied to bare codes, so that ``ValidationError("missing_crs")``
    #: yields ``"validation.missing_crs"``. Subclasses override it.
    code_namespace = "geocomp"

    def __init__(self, code: str, **context: Any) -> None:
        if not code:
            raise ValueError("GeoCompError requires a non-empty code")
        self.code = code if "." in code else f"{self.code_namespace}.{code}"
        self.context: dict[str, Any] = dict(context)
        super().__init__(self.code)

    def __str__(self) -> str:
        if not self.context:
            return self.code
        detail = ", ".join(f"{key}={value!r}" for key, value in sorted(self.context.items()))
        return f"{self.code} ({detail})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, context={self.context!r})"

    def to_dict(self) -> dict[str, Any]:
        """Serialise for a log entry or a provenance record."""
        return {"type": type(self).__name__, "code": self.code, "context": dict(self.context)}

    @property
    def context_view(self) -> Mapping[str, Any]:
        """Read-only view of the context."""
        return dict(self.context)


class ValidationError(GeoCompError):
    """An input failed a precondition.

    Context should name the offending input, what was expected, and what was
    received -- the three things NFR-006 requires a message to convey.
    """

    code_namespace = "validation"


class DataError(GeoCompError):
    """Data is internally inconsistent or references something that is absent.

    Context should identify the offending records, by id or by row number, so
    the user can find them. Raised by importers per-record without aborting the
    whole import (FR-166).
    """

    code_namespace = "data"


class ComputationError(GeoCompError):
    """The mathematics failed.

    A singular normal matrix or a non-converged iteration is this, and the
    context must carry a *diagnosis* -- which stations, which observations --
    rather than only the numerical symptom (FR-226).
    """

    code_namespace = "computation"


class EngineError(GeoCompError):
    """An external engine ran and failed.

    Context carries the engine name and version, the command line, the exit
    code, and the engine's own diagnostic output, which FR-305 requires be
    surfaced rather than replaced by a generic message.
    """

    code_namespace = "engine"


class EngineMissingError(EngineError):
    """A required engine is not installed.

    Distinct from :class:`EngineError` because the response differs: the
    operation is disabled with an offer to install it, not reported as a
    failure (FR-306).
    """

    code_namespace = "engine"


class StorageError(GeoCompError):
    """Reading from or writing to a project store failed."""

    code_namespace = "storage"
