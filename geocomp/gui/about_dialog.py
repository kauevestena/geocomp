# SPDX-License-Identifier: GPL-2.0-or-later
"""The About dialog (specs/21 section 8).

Shows GeoComp's licence, the engine versions in use, and the third-party
attributions. Attribution to Geoscience Australia and to the RTKLIB authors goes
beyond licence obligation: GeoComp is built on their work, and the research
project commits to feeding defects and improvements back upstream.
"""

from __future__ import annotations

import html

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

    @staticmethod
    def _engines() -> list[str]:
        """Each engine with its licence, its authors and the version installed.

        specs/21 criterion 8 asks for the versions *in use*; until P12c the
        dialog named the licences, no version, and said engine integration was
        still to come -- three phases after it had arrived.
        """
        from geocomp.engines.status import engine_status

        items = []
        for engine in engine_status():
            found = (
                _tr("version %1, at %2")
                .replace("%1", html.escape(engine.version.version, quote=False))
                .replace("%2", html.escape(str(engine.version.path), quote=False))
                if engine.version is not None
                else _tr("not installed")
            )
            items.append(
                f"<li><b>{engine.name}</b> — {engine.attribution} — {engine.licence} — "
                f'<a href="{engine.url}">{engine.url}</a><br>{found}</li>'
            )
        return items

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
                *self._engines(),
                "</ul>",
                f"<h3>{_tr('Source code')}</h3>",
                '<p><a href="https://github.com/kauevestena/geocomp">',
                "github.com/kauevestena/geocomp</a></p>",
            ]
        )
