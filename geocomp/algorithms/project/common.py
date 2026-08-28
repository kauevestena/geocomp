# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared helpers for the project-level algorithms (P5).

The four algorithms this phase adds -- export, report, store and base map -- all
begin the same way: read a solution document written by an earlier algorithm.
Doing that in one place means one error message when a file is not a solution,
rather than four that differ in wording and in how much they tell the user.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError
from geocomp.core.models import Network, Solution

__all__ = ["read_json", "read_network", "read_solution"]


def read_json(path: str, what: str) -> dict[str, Any]:
    """Parse a GeoComp JSON document, naming the file when it is not one."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DataError(
            "document_unreadable",
            path=path,
            expected=f"a readable JSON {what} document",
            reason=str(error),
        ) from error
    if not isinstance(payload, dict):
        raise DataError(
            "document_not_an_object",
            path=path,
            expected=f"a JSON object describing a {what}",
        )
    return payload


def read_solution(path: str) -> Solution:
    """Read a solution document written by an adjustment algorithm.

    The distinction the message draws matters: a user who fed in a *network*
    document -- the other JSON GeoComp writes, and the one sitting beside it in
    the same folder -- gets told which they gave rather than a schema complaint
    about a missing key.
    """
    payload = read_json(path, "solution")
    if "adjusted_stations" not in payload and "stations" in payload:
        raise DataError(
            "network_given_where_a_solution_was_expected",
            path=path,
            expected=(
                "a solution document, which an adjustment algorithm writes. This "
                "file is a network: it has stations but no adjusted stations, so "
                "it has not been adjusted yet"
            ),
        )
    try:
        return Solution.from_dict(payload)
    except (KeyError, TypeError, ValueError) as error:
        raise DataError(
            "solution_document_malformed",
            path=path,
            reason=str(error),
            expected="a solution document as GeoComp writes it",
        ) from error


def read_network(path: str) -> Network | None:
    """Read a network document, or ``None`` when no path was given."""
    if not path:
        return None
    payload = read_json(path, "network")
    try:
        return Network.from_dict(payload)
    except (KeyError, TypeError, ValueError) as error:
        raise DataError(
            "network_document_malformed",
            path=path,
            reason=str(error),
            expected="a network document as GeoComp writes it",
        ) from error
