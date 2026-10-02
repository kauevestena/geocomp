# SPDX-License-Identifier: GPL-2.0-or-later
"""Which thematic quality maps each result layer offers (FR-902; phase P12b).

The table behind :mod:`geocomp.layers.themes`, kept free of QGIS so the
pairing of each map with the layers it styles is checked where QGIS is not
installed (``tests/structural/test_layer_styles.py``): a map whose field its
layer lacks draws every feature in the fallback symbol, and looks styled.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["THEMES", "Theme"]


@dataclass(frozen=True)
class Theme:
    """One thematic map: its QML, and how its classes are made.

    Attributes:
        id: The QML's name in ``resources/styles/themes``, and the key of its
            label in :func:`geocomp.layers.themes.theme_labels`.
        fit: ``"quartiles"`` to fit the data classes' bounds to the values of
            ``field``; ``"categories"`` to make one category per value of it;
            empty when the file's classes stand.
        field: The attribute the classes are fitted to.
        unit: The unit the fitted bounds are stated in, for the legend.
        unit_field: A column naming the unit instead, where the layer carries
            it per row (a gravity layer in mGal or µGal).
    """

    id: str
    fit: str = ""
    field: str = ""
    unit: str = ""
    unit_field: str = ""


#: The thematic maps each result layer offers, keyed by its default style.
THEMES: dict[str, tuple[Theme, ...]] = {
    "stations": (
        Theme("positional_uncertainty", "quartiles", "positional_uncertainty", unit="m"),
    ),
    "residuals": (
        Theme("standardised_residual"),
        Theme("redundancy"),
        Theme("mdb_displacement", "quartiles", "mdb_displacement", unit="m"),
        Theme("external_reliability", "quartiles", "external_reliability", unit="m"),
    ),
    "observations": (Theme("epoch", "categories", "epoch"),),
    "gnss_baselines": (Theme("baseline_status"),),
    "gravity_differences": (
        Theme("standardised_residual"),
        Theme("redundancy"),
        Theme("gravity_mdb", "quartiles", "mdb", unit_field="unit"),
    ),
}
