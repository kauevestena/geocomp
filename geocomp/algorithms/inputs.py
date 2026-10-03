# SPDX-License-Identifier: GPL-2.0-or-later
"""Inputs checked before a run computes anything, and refusals that name them (specs/16 §7).

Criterion 7 of ``specs/16``: every algorithm validates its inputs before
computing, and its failure names the offending parameter. P12c's audit found
the second half met nowhere for files: of 38 file and folder inputs given a
path that did not exist, none was named. Most refusals gave the path alone --
which of three documents it was, the user had to work out -- and four gave
less: a traceback, an internal error code with its context, or "could not
complete the operation".

Two rules, applied to every algorithm by :class:`~geocomp.algorithms.base.GeoCompAlgorithm`:

* **Before the run**, every file and folder input is checked to exist, and
  every mandatory input to be given; a refusal names the parameter by the
  label the dialog shows (:func:`input_problem`). QGIS's dialog and
  ``processing.run`` ask through ``checkParameterValues``; a run from PyQGIS
  does not, so the wrapper around ``processAlgorithm`` asks again.
* **During the run**, a refusal whose message carries the path of one of the
  run's inputs -- a document of the wrong kind, a file that will not parse --
  is prefixed with that input's label (:func:`naming_the_input`). A core error
  that reached the wrapper unconverted is rendered through its template rather
  than shown as a code.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

from qgis.core import (
    QgsProcessingException,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFile,
    QgsProcessingParameterMultipleLayers,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError

__all__ = ["input_problem", "naming_the_input", "validated"]

_CONTEXT = "GeoCompAlgorithm"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def _given(value: Any) -> bool:
    return value is not None and not (isinstance(value, str) and not value.strip())


def _paths(algorithm, definition, parameters: dict[str, Any], context) -> list[str]:
    """The files an input names: one for a file input, each of a list's."""
    if isinstance(definition, QgsProcessingParameterFile):
        path = algorithm.parameterAsFile(parameters, definition.name(), context)
        return [path] if path else []
    if isinstance(definition, QgsProcessingParameterMultipleLayers):
        value = parameters.get(definition.name())
        items = value if isinstance(value, (list, tuple)) else [value]
        # A list of files is given as paths; a layer given as an object has
        # no path to check, and QGIS has checked it already.
        return [str(item) for item in items if isinstance(item, str) and item]
    return []


def input_problem(algorithm, parameters: dict[str, Any], context) -> str | None:
    """The first input that cannot be used, said with its label; ``None`` when all can."""
    for definition in algorithm.parameterDefinitions():
        if definition.isDestination():
            continue
        optional = bool(definition.flags() & QgsProcessingParameterDefinition.FlagOptional)
        value = parameters.get(definition.name())
        if not _given(value):
            if not optional and definition.defaultValue() is None:
                return _tr("%1 is required, and none was given.").replace("%1", definition.description())
            continue
        if isinstance(definition, QgsProcessingParameterMultipleLayers):
            for item in _paths(algorithm, definition, parameters, context):
                if not Path(item).exists() and ("/" in item or "\\" in item or Path(item).suffix):
                    return (
                        _tr("%1: the file '%2' does not exist.")
                        .replace("%1", definition.description())
                        .replace("%2", item)
                    )
            continue
        if not isinstance(definition, QgsProcessingParameterFile):
            continue
        path = Path(algorithm.parameterAsFile(parameters, definition.name(), context))
        if definition.behavior() == QgsProcessingParameterFile.Folder:
            if not path.is_dir():
                return (
                    _tr("%1: the folder '%2' does not exist.")
                    .replace("%1", definition.description())
                    .replace("%2", str(path))
                )
        elif not path.is_file():
            return (
                _tr("%1: the file '%2' does not exist.")
                .replace("%1", definition.description())
                .replace("%2", str(path))
            )
    return None


def naming_the_input(algorithm, parameters: dict[str, Any], context, message: str) -> str:
    """*message*, prefixed with the label of the one input whose path it carries.

    Unchanged when it names no input's path, names several, or already carries
    the label.
    """
    carried = []
    for definition in algorithm.parameterDefinitions():
        if definition.isDestination() or not _given(parameters.get(definition.name())):
            continue
        if any(path in message for path in _paths(algorithm, definition, parameters, context)):
            carried.append(definition.description())
    if len(carried) != 1 or carried[0] in message:
        return message
    return _tr("%1: %2").replace("%1", carried[0]).replace("%2", message)


def validated(process):
    """Wrap a ``processAlgorithm`` with both rules of this module."""
    if getattr(process, "_geocomp_validated", False):
        return process

    @functools.wraps(process)
    def run(self, parameters, context, feedback):
        problem = input_problem(self, parameters, context)
        if problem is not None:
            raise QgsProcessingException(problem)
        try:
            return process(self, parameters, context, feedback)
        except QgsProcessingException as error:
            named = naming_the_input(self, parameters, context, str(error))
            if named == str(error):
                raise
            raise QgsProcessingException(named) from error
        except GeoCompError as error:
            from geocomp.services.messages import message_for

            raise QgsProcessingException(
                naming_the_input(self, parameters, context, message_for(error))
            ) from error

    run._geocomp_validated = True
    return run
