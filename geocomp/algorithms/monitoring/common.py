# SPDX-License-Identifier: GPL-2.0-or-later
"""What the three monitoring algorithms share (``specs/14``, phase P10b).

**Which stations are the reference block.** Named in the run, or -- when the
run names none -- read from the network document, where ``monitoring_role`` is
kept (``specs/04`` section 2.3). A monitoring project marks its pillars once, in
the network, and every epoch's analysis finds them there. Never guessed: a block
chosen by the software is exactly the "find the subset that makes the answer
come out stable" hazard ``specs/14`` section 5 warns about.

**Alert thresholds** are a CSV file the project keeps (``specs/14`` section 7):
``kind, limit, stations, group``, limits in metres, or metres a year for a
velocity.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.analysis.common import station_list
from geocomp.algorithms.project.common import read_json, read_network, read_solution
from geocomp.core.errors import GeoCompError
from geocomp.core.models import MonitoringRole, Network, Solution
from geocomp.core.monitoring import DATUM_CHOICES, AlertThreshold, thresholds_from_rows

__all__ = [
    "DATUM_OPTIONS",
    "datum_labels",
    "datum_of",
    "fail",
    "read_document",
    "read_optional_network",
    "read_solutions",
    "read_thresholds",
    "roles",
    "write_json",
]

_CONTEXT = "GeoCompMonitoring"

#: The datum choices, index as a saved model stores it: the first is "the
#: analysis's own default", which is not one of the core's names.
DATUM_OPTIONS: tuple[str | None, ...] = (None, *DATUM_CHOICES)


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def datum_labels() -> list[str]:
    """Translated datum names, in :data:`DATUM_OPTIONS` order."""
    return [
        _tr("From the network: translation and rotation for a plan, translation for heights"),
        _tr("Translation"),
        _tr("Translation and rotation"),
        _tr("Similarity: translation, rotation and scale"),
    ]


def datum_of(index: int) -> str | None:
    """The monitoring datum at a position of the datum parameter's choices; ``None`` for the first.
    """
    return DATUM_OPTIONS[index]


def fail(error: GeoCompError) -> QgsProcessingException:
    """A core refusal as the exception Processing shows, in the user's words."""
    from geocomp.services.messages import message_for

    return QgsProcessingException(message_for(error))


def read_solutions(paths: list[str]) -> list[Solution]:
    """Read every solution document, refusing in the user's words if any cannot be read."""
    try:
        return [read_solution(path) for path in paths]
    except GeoCompError as error:
        raise fail(error) from error


def read_optional_network(path: str) -> Network | None:
    """Read a network document, or ``None`` when no path was given, refusing in the user's words."""
    try:
        return read_network(path)
    except GeoCompError as error:
        raise fail(error) from error


def read_document(path: str, reader) -> dict[str, Any]:
    """A monitoring document, checked by *reader* to be the kind expected."""
    try:
        return reader(read_json(path, "monitoring"))
    except GeoCompError as error:
        raise fail(error) from error


def roles(
    network: Network | None, reference_text: str, objects_text: str, *, required: bool = True
) -> tuple[tuple[str, ...], tuple[str, ...] | None]:
    """The reference block and the object points: named, or from the network.

    Returns the reference stations and the object stations, the second ``None``
    for "every compared station that is not a reference one". With
    *required* false an empty block is allowed and returned empty.
    """
    reference = station_list(reference_text)
    objects = station_list(objects_text)
    if reference is None and network is not None:
        reference = [s.id for s in network.stations.values() if s.monitoring_role is MonitoringRole.REFERENCE]
    if objects is None and network is not None:
        marked = [s.id for s in network.stations.values() if s.monitoring_role is MonitoringRole.OBJECT]
        objects = marked or None
    if not reference and not required:
        return (), (tuple(objects) if objects else None)
    if not reference:
        raise QgsProcessingException(
            _tr(
                "Name the reference stations -- the pillars assumed stable, against which movement "
                "is measured -- or mark them REFERENCE in the network document. GeoComp does not "
                "choose them: a block picked by the software is picked to make the answer stable."
            )
        )
    return tuple(reference), (tuple(objects) if objects else None)


def read_thresholds(path: str) -> tuple[AlertThreshold, ...]:
    """Read alert thresholds from a CSV file; none when no path was given.

    An unreadable file and a malformed one are each refused in the user's words.
    """
    if not path:
        return ()
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return thresholds_from_rows(list(csv.reader(handle)))
    except OSError as error:
        raise QgsProcessingException(
            _tr("The alert thresholds file '%1' could not be read: %2")
            .replace("%1", path)
            .replace("%2", str(error))
        ) from error
    except GeoCompError as error:
        raise fail(error) from error


def write_json(path: str, payload: dict[str, Any]) -> str:
    """Write a document as JSON when a path was given, and return the path."""
    if path:
        Path(path).write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    return path
