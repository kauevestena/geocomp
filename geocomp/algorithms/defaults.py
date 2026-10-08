# SPDX-License-Identifier: GPL-2.0-or-later
"""Parameter defaults from the Global Settings (FR-068, FR-071; phase P12a).

``specs/15-ui-menu-and-settings.md`` section 2.3: before P12a, 36 declared
settings were read by nothing. The window let a user change the default
meteorology, the levelling tolerance or the confidence level, stored and
resolved the value correctly -- and every algorithm went on using a literal of
its own, so nothing changed. The numbers agreed at the defaults, which is why
nobody noticed.

**A parameter's default *is* its setting.** Each algorithm declares the
parameter with ``defaultValue=configured("section.key")``, read when the
algorithm is instantiated -- which Processing does for every dialog and every
run -- through the run, project and global scopes (FR-068). There is one value,
not a setting and a literal that happen to agree, and so:

* changing the setting changes what a run that does not override it computes;
* a parameter hidden in Basic mode runs at the setting, exactly as it would in
  Advanced mode left untouched (FR-071) -- the Basic/Advanced identity holds by
  construction, and ``tests/qgis/test_basic_advanced_identity.py`` checks it
  for every algorithm.

Keys are written out in full at each use, never composed: the structural test
that finds a setting's readers searches for the literal key.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.number_format import localised

if TYPE_CHECKING:
    from qgis.core import QgsProcessingFeedback

    from geocomp.core.models.epoch import Epoch
    from geocomp.core.models.network import Network
    from geocomp.core.models.solution import Solution

__all__ = [
    "configured",
    "configured_epoch",
    "recorded_epoch",
    "report_template",
    "run_epoch",
    "working_directory",
]

_CONTEXT = "GeoCompDefaults"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def configured(key: str) -> Any:
    """The effective value of the setting *key*, to be used as a parameter default."""
    from geocomp.services.settings_service import settings

    return settings.value(key)


def working_directory(prefix: str) -> Path:
    """A new folder for an engine's working files (FR-066; P12c-46).

    Under ``paths.working_directory`` when one is set, created if it is not
    there yet; under the system's temporary directory otherwise, as before.
    Whether the folder is kept afterwards is each algorithm's to say.

    Raises:
        QgsProcessingException: when the configured directory cannot be
            created or written in, naming it and where it is set.
    """
    from qgis.core import QgsProcessingException

    base = str(configured("paths.working_directory") or "").strip()
    try:
        if base:
            Path(base).mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=prefix, dir=base or None))
    except OSError as error:
        raise QgsProcessingException(
            _tr("The working directory '%1' set in Global Settings cannot be written in (%2). "
                "Choose another under Paths and engines, or clear it.")
            .replace("%1", base)
            .replace("%2", error.strerror or str(error))
        ) from error


def report_template(path: str, default: str) -> tuple[str, str]:
    """The folder and the name of a report's template (FR-931, FR-066; P12c-46).

    The template the run names, *path*, when it names one; otherwise *default*
    -- ``adjustment.html``, say -- from the folder ``paths.report_templates``
    sets, which an organisation keeps its own layouts in. A name that folder
    does not hold falls back to the shipped template, as it always has
    (``geocomp.reports.templates.load_template``).
    """
    if path:
        return str(Path(path).parent), Path(path).name
    return str(configured("paths.report_templates") or "").strip(), default


def configured_epoch(fallback: float) -> float:
    """The stated default reference epoch as a decimal year, or *fallback* when none is.

    ``reference_systems.default_epoch`` is zero until a user states one
    (``specs/15`` section 2.1: GeoComp does not assume an epoch). An algorithm
    whose parameter has always had a literal default keeps it as the fallback,
    so an unconfigured installation computes what it always did.
    """
    stated = float(configured("reference_systems.default_epoch") or 0.0)
    return stated if stated > 0.0 else fallback


def run_epoch(stated: float, network: Network | None, fallback: float) -> tuple[Epoch, str]:
    """An adjustment's reference epoch, and where it came from (FR-105; P12c).

    *stated* is the run's parameter, whose default is
    ``reference_systems.default_epoch``; 0 means none was stated. Then the
    network's own epoch, when it carries one. Only when neither says anything
    does *fallback* -- the epoch the algorithm always defaulted to -- apply,
    and it is returned as ``assumed`` so the solution can say so and a
    comparison can refuse it.

    Returns:
        The epoch, and ``"stated"``, ``"network"`` or
        :data:`~geocomp.core.models.solution.EPOCH_ASSUMED`.
    """
    from geocomp.core.models.epoch import Epoch
    from geocomp.core.models.solution import EPOCH_ASSUMED

    if stated and stated > 0.0:
        return Epoch.from_decimal_year(stated), "stated"
    if getattr(network, "epoch", None) is not None:
        return network.epoch, "network"
    return Epoch.from_decimal_year(fallback), EPOCH_ASSUMED


def recorded_epoch(
    solution: Solution, origin: str, feedback: QgsProcessingFeedback | None
) -> Solution:
    """*solution* with its epoch's origin in the provenance, and a word if it was assumed."""
    from dataclasses import replace

    from geocomp.core.models.solution import EPOCH_ASSUMED

    if solution.provenance is not None:
        solution = replace(
            solution,
            provenance=replace(
                solution.provenance,
                parameters={**solution.provenance.parameters, "epoch_origin": origin},
            ),
        )
    if origin == EPOCH_ASSUMED and feedback is not None:
        feedback.pushWarning(
            _tr(
                "No reference epoch was stated, by the run or its network, so the solution "
                "carries %1, assumed. It cannot enter a comparison of epochs (FR-105)."
            ).replace("%1", localised(f"{solution.epoch.decimal_year:.4f}"))
        )
    return solution

