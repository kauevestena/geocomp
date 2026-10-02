# SPDX-License-Identifier: GPL-2.0-or-later
"""Class boundaries for the thematic quality maps (FR-902; phase P12b).

``specs/19-visualization.md`` section 4. Two kinds of attribute are mapped,
and they are classified differently on purpose.

**Quantities with a meaning of their own** -- a standardised residual, a
redundancy number -- are drawn in fixed bands that the style file states: a
``|w|`` of 3 means the same in every network. Nothing here touches them.

**Quantities whose scale is the network's** -- a positional uncertainty, an
MDB, an external reliability -- run from tenths of a millimetre on a deformation
monument to decimetres on a GNSS densification. No fixed band suits both, so
the bounds are fitted to the values present, by quantile: each class holds
about the same number of features, and the map shows *where this network is
weakest*, with the legend stating every bound in its unit. It is a relative
map, and it says so; the absolute numbers are the attribute table's.

This module is QGIS-free: the bounds are arithmetic, and the style says how
each class looks.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np

from geocomp.core.units import Unit

__all__ = ["fitted_bounds", "mdb_displacement"]


def fitted_bounds(values: Iterable[float | None], classes: int) -> tuple[float, ...]:
    """The edges of up to *classes* quantile classes over the finite *values*.

    Returns ``classes + 1`` ascending edges -- fewer when the values have fewer
    distinct levels than that, because two classes with the same bounds would
    be one class drawn twice. Empty when there is nothing finite to classify.
    The outer edges are the smallest and largest value, so every value falls in
    a class.
    """
    finite = np.array(
        [float(value) for value in values if value is not None and math.isfinite(value)]
    )
    if finite.size == 0 or classes < 1:
        return ()
    edges = np.quantile(finite, np.linspace(0.0, 1.0, classes + 1))
    unique: list[float] = []
    for edge in (float(edge) for edge in edges):
        if not unique or edge > unique[-1]:
            unique.append(edge)
    if len(unique) == 1:
        # Every value equal: one class, of zero width, which still draws.
        return (unique[0], unique[0])
    return tuple(unique)


def mdb_displacement(mdb: float | None, unit: Unit, length: float | None) -> float | None:
    """An MDB as the displacement it would put at the observation's far end, metres.

    The thematic MDB map has to compare a direction's MDB, in radians, with a
    distance's, in metres, on one scale -- a graduated map over the raw values
    would rank a 2-arcsecond MDB below a 1 mm one. A length observation's MDB
    already is a displacement. An angle's becomes one at the sight it was
    measured over: an undetectable blunder of *MDB* radians moves the target
    sideways by the MDB times the length. Any other unit has no displacement, and
    ``None`` says so rather than inventing one.
    """
    if mdb is None or not math.isfinite(mdb):
        return None
    if unit is Unit.METRE:
        return mdb
    if unit is Unit.RADIAN and length is not None and length > 0.0:
        return mdb * length
    return None
