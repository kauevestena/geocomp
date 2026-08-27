# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared plumbing for the three analysis algorithms.

Three things they all need and none of them should own privately: reading a
network document, choosing a coordinate frame and a datum definition, and
rendering an HTML report.

**Why the input is a JSON network document.** Phase P2 has no importer yet (CSV
and XLSX arrive in P3) and no project store (GeoPackage arrives in P5). The
domain model already serialises itself losslessly through
:meth:`~geocomp.core.models.Network.to_dict`, so that document *is* the network
reference ``specs/16`` section 4 asks algorithms to accept. When the store
arrives, these algorithms gain a second input rather than changing their first:
the parameter name ``NETWORK`` stays, and a stored-network reference resolves to
the same :class:`~geocomp.core.models.Network`.

Report rendering lives here rather than in ``core/`` because phrasing is a
presentation concern: ``core`` cannot import Qt at all (NFR-002), so it cannot
translate a heading (``specs/18`` section 2).
"""

from __future__ import annotations

import json
from pathlib import Path

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.algorithms.reporting import (
    escape,
    format_number,
    render_document,
    render_note,
    render_table,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import GeoCompError
from geocomp.core.models import DatumDefinition, Network, network_from_document

#: Re-exported so the analysis algorithms keep one import. The helpers
#: themselves moved to :mod:`geocomp.algorithms.reporting` in phase P3, when the
#: total-station algorithms needed them too.
__all__ = [
    "DATUM_ORDER",
    "FRAME_ORDER",
    "datum_labels",
    "datum_of",
    "escape",
    "format_number",
    "frame_labels",
    "frame_of",
    "load_network",
    "render_document",
    "render_note",
    "render_table",
    "station_list",
]

_CONTEXT = "GeoCompAnalysis"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


#: Frame choices, in the order they appear in the parameter's combo box. The
#: *index* is what a saved model stores, so this order is as permanent as an
#: algorithm id: appending is safe, reordering silently changes saved models.
FRAME_ORDER: tuple[Frame, ...] = (
    Frame.PLANE_2D,
    Frame.HEIGHT_1D,
    Frame.SPACE_3D,
    Frame.GRAVITY_1D,
)

#: Datum choices, same permanence rule. ``NONE`` is not offered: an adjustment
#: has to define its datum somehow, and offering "none" would produce a singular
#: system with no diagnosis worth reading.
DATUM_ORDER: tuple[DatumDefinition, ...] = (
    DatumDefinition.CONSTRAINED,
    DatumDefinition.INNER_CONSTRAINT,
    DatumDefinition.MINIMUM_CONSTRAINT,
    DatumDefinition.FIXED,
)


def frame_labels() -> list[str]:
    """Translated frame names, in :data:`FRAME_ORDER`."""
    labels = {
        Frame.PLANE_2D: _tr("2D — planimetric (easting, northing)"),
        Frame.HEIGHT_1D: _tr("1D — heights only"),
        Frame.SPACE_3D: _tr("3D — easting, northing, up"),
        Frame.GRAVITY_1D: _tr("1D — gravity values"),
    }
    return [labels[frame] for frame in FRAME_ORDER]


def datum_labels() -> list[str]:
    """Translated datum names, in :data:`DATUM_ORDER`."""
    labels = {
        DatumDefinition.CONSTRAINED: _tr("Constrained — hold the stations the network fixes"),
        DatumDefinition.INNER_CONSTRAINT: _tr("Inner constraint — free network, trace minimum"),
        DatumDefinition.MINIMUM_CONSTRAINT: _tr("Minimum constraint — over chosen stations"),
        DatumDefinition.FIXED: _tr("Fixed — hold the constrained stations exactly"),
    }
    return [labels[datum] for datum in DATUM_ORDER]


def frame_of(index: int) -> Frame:
    return FRAME_ORDER[index]


def datum_of(index: int) -> DatumDefinition:
    return DATUM_ORDER[index]


def station_list(raw: str) -> list[str] | None:
    """Parse a comma-separated station list, or ``None`` when empty.

    ``None`` and the empty list mean different things to the datum code -- all
    stations versus no stations -- so the distinction is preserved rather than
    collapsed.
    """
    stations = [item.strip() for item in (raw or "").split(",") if item.strip()]
    return stations or None


def load_network(path: str, *, parameter: str) -> Network:
    """Read a GeoComp network document, failing with a message that names it.

    FR-035: validate before computing, and say which input was wrong. A
    truncated JSON file and a JSON file that is not a network are different
    mistakes and get different messages.

    The structural work is :func:`~geocomp.core.models.network_from_document`,
    which is why it is testable without QGIS; this function owns only the
    file-level failures and the phrasing.
    """
    if not path:
        raise QgsProcessingException(
            _tr("No network document was given for parameter '%1'.").replace("%1", parameter)
        )

    source = Path(path)
    if not source.is_file():
        raise QgsProcessingException(
            _tr("The network document '%1' does not exist.").replace("%1", str(source))
        )

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QgsProcessingException(
            _tr("'%1' is not valid JSON: %2").replace("%1", str(source)).replace("%2", str(exc))
        ) from exc
    except OSError as exc:  # pragma: no cover - filesystem dependent
        raise QgsProcessingException(
            _tr("'%1' could not be read: %2").replace("%1", str(source)).replace("%2", str(exc))
        ) from exc

    try:
        return network_from_document(payload)
    except GeoCompError as exc:
        raise QgsProcessingException(
            _tr("'%1' could not be read as a GeoComp network. %2")
            .replace("%1", str(source))
            .replace("%2", _describe(exc))
        ) from exc


def _describe(exc: Exception) -> str:
    """A user-facing description of a core error.

    Core errors carry a code and a context rather than a sentence, and
    :mod:`geocomp.services.messages` owns the phrasing; falling back to the
    developer-facing form is better than showing nothing when a code has no
    template yet.
    """
    if isinstance(exc, GeoCompError):
        from geocomp.services.messages import message_for

        return message_for(exc)
    return str(exc)
