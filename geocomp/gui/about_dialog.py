# SPDX-License-Identifier: GPL-2.0-or-later
"""The About dialog (specs/21 section 8).

Shows GeoComp's licence, the engine versions in use, and the third-party
attributions. Attribution to Geoscience Australia and to the RTKLIB authors goes
beyond licence obligation: GeoComp is built on their work, and the research
project commits to feeding defects and improvements back upstream.
"""

from __future__ import annotations

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from geocomp.core.version import __version__

__all__ = ["AboutDialog"]

_TR_CONTEXT = "GeoCompAbout"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class AboutDialog(QDialog):
    """Licence, versions and attributions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("geocompAboutDialog")
        self.setWindowTitle(_tr("About GeoComp"))
        self.resize(560, 460)

        text = QLabel(self._body(), self)
        text.setWordWrap(True)
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setOpenExternalLinks(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(text, stretch=1)
        layout.addWidget(buttons)

    def _body(self) -> str:
        return "".join(
            [
                f"<h2>GeoComp {__version__}</h2>",
                "<p>",
                _tr(
                    "A framework for pre-analysis, GNSS processing and adjustment of "
                    "geodetic networks inside QGIS."
                ),
                "</p><p>",
                _tr(
                    "Developed at the Departamento de Geomática, Setor de Ciências da "
                    "Terra, Universidade Federal do Paraná."
                ),
                "</p>",
                f"<h3>{_tr('Licence')}</h3><p>",
                _tr(
                    "GeoComp is free software under the GNU General Public License, "
                    "version 2 or later. You may use it, including commercially, study "
                    "it, modify it and redistribute it."
                ),
                "</p>",
                f"<h3>{_tr('Processing engines')}</h3><p>",
                _tr(
                    "GeoComp runs external engines as separate programs. They are not "
                    "part of GeoComp and carry their own licences:"
                ),
                "</p><ul>",
                "<li><b>DynAdjust</b> — Geoscience Australia — Apache License 2.0 — ",
                '<a href="https://github.com/GeoscienceAustralia/DynAdjust">',
                "github.com/GeoscienceAustralia/DynAdjust</a></li>",
                "<li><b>RTKLIB</b> — T. Takasu, and the RTKLIB-EX contributors — ",
                '<a href="https://www.rtklib.com/">rtklib.com</a></li>',
                "</ul><p>",
                _tr("Engine integration arrives in later development phases."),
                "</p>",
                f"<h3>{_tr('Source code')}</h3>",
                '<p><a href="https://github.com/kauevestena/geocomp">',
                "github.com/kauevestena/geocomp</a></p>",
            ]
        )
