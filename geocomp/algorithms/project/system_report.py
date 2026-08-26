# SPDX-License-Identifier: GPL-2.0-or-later
"""``geocomp:project_system_report`` -- report the GeoComp environment.

Phase P0's algorithm. It exists to prove the registry -> provider -> menu path
end to end, but it is not a placeholder: it answers the first question asked of
any support request -- which versions, which engines, which settings, and *where
each setting came from*.

Reporting the origin scope of every setting (FR-068) is the part that earns its
place. "It works on my machine" is usually a settings-scope difference, and
without the origin there is no way to see one.
"""

from __future__ import annotations

import html
import platform
import sys
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFileDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.core.settings_def import SECTIONS, settings_in_section
from geocomp.core.version import __version__

__all__ = ["SystemReportAlgorithm"]

OUTPUT_HTML = "OUTPUT_HTML"


class SystemReportAlgorithm(GeoCompAlgorithm):
    """Collects version, engine and settings information into an HTML report."""

    TR_CONTEXT = "SystemReportAlgorithm"

    def displayName(self) -> str:
        return self.tr("GeoComp system report")

    def shortDescription(self) -> str:
        return self.tr("Report GeoComp versions, engine availability and effective settings.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Produces a report describing the GeoComp installation: plugin and QGIS "
            "versions, the Python runtime, availability and versions of the external "
            "processing engines, and every GeoComp setting with its effective value and "
            "the scope that value came from.</p>"
            "<p>Attach this report to a bug report or a support request. Because settings "
            "resolve through run, project and global scopes in that order, the origin "
            "column is usually what explains a result that differs between two machines.</p>"
            "<h3>Parameters</h3>"
            "<p><b>Report</b> &mdash; destination HTML file. Leave empty to write to a "
            "temporary file.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_HTML,
                self.tr("Report"),
                self.tr("HTML files (*.html)"),
                optional=True,
                createByDefault=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        # Orchestration only: this method gathers and renders, it computes
        # nothing geodetic (specs/16 section 7).
        feedback.pushInfo(self.tr("Collecting environment information…"))
        environment = self._collect_environment()

        feedback.setProgress(40)
        feedback.pushInfo(self.tr("Resolving settings…"))
        resolved = self._collect_settings(feedback)

        feedback.setProgress(70)
        engines = self._collect_engines()

        for line in (
            f"GeoComp {environment['geocomp_version']}",
            f"QGIS {environment['qgis_version']}",
            f"Python {environment['python_version']}",
        ):
            feedback.pushInfo(line)

        target = self.parameterAsFileOutput(parameters, OUTPUT_HTML, context)
        if target:
            feedback.setProgress(90)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(self._render(environment, engines, resolved))
            feedback.pushInfo(self.tr("Report written."))

        feedback.setProgress(100)
        return {OUTPUT_HTML: target}

    # -- collection ------------------------------------------------------

    def _collect_environment(self) -> dict[str, str]:
        return {
            "geocomp_version": __version__,
            "qgis_version": Qgis.QGIS_VERSION,
            "qgis_release_name": Qgis.QGIS_RELEASE_NAME,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.machine(),
        }

    def _collect_engines(self) -> list[tuple[str, str, str]]:
        """Engine name, status and version.

        P0 has no engine adapters yet; the DynAdjust and RTKLIB rows appear in
        P6 and P7. Reporting them as not yet supported is honest, and it is what
        makes the report useful from the first release rather than misleading.
        """
        not_yet = self.tr("Not integrated yet")
        return [
            ("DynAdjust", not_yet, self.tr("Arrives in phase P6")),
            ("RTKLIB (rnx2rtkp)", not_yet, self.tr("Arrives in phase P7")),
        ]

    def _collect_settings(
        self, feedback: QgsProcessingFeedback
    ) -> dict[str, list[tuple[str, Any, str, bool]]]:
        """Resolve every setting, grouped by section.

        Each entry is ``(key, value, origin scope, is_overridden)``.
        """
        from geocomp.services.settings_service import settings

        by_section: dict[str, list[tuple[str, Any, str, bool]]] = {}
        all_resolved = settings.all_resolved()
        for section in SECTIONS:
            rows: list[tuple[str, Any, str, bool]] = []
            for definition in settings_in_section(section.id):
                item = all_resolved.get(definition.key)
                if item is None:  # pragma: no cover - defensive
                    continue
                rows.append((definition.key, item.value, item.scope.value, item.is_overridden))
            if rows:
                by_section[section.id] = rows
            elif feedback.isCanceled():  # pragma: no cover
                break
        return by_section

    # -- rendering -------------------------------------------------------

    def _render(
        self,
        environment: dict[str, str],
        engines: list[tuple[str, str, str]],
        resolved: dict[str, list[tuple[str, Any, str, bool]]],
    ) -> str:
        def esc(value: Any) -> str:
            return html.escape(str(value))

        parts: list[str] = [
            "<!doctype html>",
            '<html><head><meta charset="utf-8">',
            f"<title>{esc(self.tr('GeoComp system report'))}</title>",
            "<style>"
            "body{font-family:sans-serif;margin:2rem;line-height:1.5}"
            "table{border-collapse:collapse;margin-bottom:2rem;width:100%}"
            "th,td{border:1px solid #ccc;padding:.4rem .6rem;text-align:left;vertical-align:top}"
            "th{background:#f2f2f2}"
            "code{font-family:monospace}"
            ".overridden{font-weight:bold}"
            "</style></head><body>",
            f"<h1>{esc(self.tr('GeoComp system report'))}</h1>",
            f"<h2>{esc(self.tr('Environment'))}</h2><table>",
        ]
        labels = {
            "geocomp_version": self.tr("GeoComp version"),
            "qgis_version": self.tr("QGIS version"),
            "qgis_release_name": self.tr("QGIS release"),
            "python_version": self.tr("Python version"),
            "platform": self.tr("Platform"),
            "processor": self.tr("Architecture"),
        }
        for key, value in environment.items():
            parts.append(f"<tr><th>{esc(labels.get(key, key))}</th><td>{esc(value)}</td></tr>")
        parts.append("</table>")

        parts.append(f"<h2>{esc(self.tr('Processing engines'))}</h2><table>")
        parts.append(
            f"<tr><th>{esc(self.tr('Engine'))}</th><th>{esc(self.tr('Status'))}</th>"
            f"<th>{esc(self.tr('Detail'))}</th></tr>"
        )
        for name, status, detail in engines:
            parts.append(f"<tr><td>{esc(name)}</td><td>{esc(status)}</td><td>{esc(detail)}</td></tr>")
        parts.append("</table>")

        parts.append(f"<h2>{esc(self.tr('Settings'))}</h2>")
        resolution_note = self.tr(
            "Settings resolve in the order: run parameter, project, global, built-in default. "
            "The origin column shows which scope supplied the effective value."
        )
        parts.append(f"<p>{esc(resolution_note)}</p>")
        for section_id, rows in resolved.items():
            parts.append(f"<h3><code>{esc(section_id)}</code></h3><table>")
            parts.append(
                f"<tr><th>{esc(self.tr('Setting'))}</th><th>{esc(self.tr('Effective value'))}</th>"
                f"<th>{esc(self.tr('Origin'))}</th></tr>"
            )
            for key, value, origin, overridden in rows:
                css = ' class="overridden"' if overridden else ""
                parts.append(
                    f"<tr><td><code>{esc(key)}</code></td><td>{esc(value)}</td>"
                    f"<td{css}>{esc(origin)}</td></tr>"
                )
            parts.append("</table>")

        parts.append("</body></html>")
        return "\n".join(parts)
