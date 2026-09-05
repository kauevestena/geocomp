# SPDX-License-Identifier: GPL-2.0-or-later
"""Translation loading (FR-090, FR-092).

Source strings are English; pt-BR and es ship as compiled ``.qm`` files built
from the ``.ts`` sources at packaging time
(``specs/18-i18n-and-profiles.md`` section 4).

Language follows the QGIS UI language, with an explicit override in Global
Settings -- FR-092 requires the override so a user need not go hunting through
QGIS's own preferences to read GeoComp in their language.
"""

from __future__ import annotations

from pathlib import Path

from qgis.core import QgsSettings
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator

from geocomp.core.settings_def import LANGUAGE_SYSTEM

__all__ = ["I18N_DIR", "SUPPORTED_LOCALES", "install_translator", "resolve_locale"]

I18N_DIR = Path(__file__).parent

#: Locales GeoComp ships. ``en`` is the source locale and needs no catalogue.
SUPPORTED_LOCALES = ("en", "pt_BR", "es")


def resolve_locale(override: str | None = None) -> str:
    """Return the locale GeoComp should use.

    Args:
        override: The ``interface.language`` value. ``None`` or the ``system``
            sentinel defers to QGIS, then to the operating system.

    The QGIS user-locale setting is read directly rather than through
    ``SettingsService`` because translations install before the plugin's own
    services exist.
    """
    if override and override != LANGUAGE_SYSTEM:
        return override

    settings = QgsSettings()
    if settings.value("locale/overrideFlag", False, type=bool):
        locale = settings.value("locale/userLocale", "", type=str)
        if locale:
            return _normalise(locale)
    return _normalise(QLocale.system().name())


def _normalise(locale: str) -> str:
    """Map a Qt locale name onto a shipped catalogue.

    Any Portuguese variant maps to ``pt_BR`` and any Spanish variant to ``es``:
    a European Portuguese user is far better served by the Brazilian catalogue
    than by falling back to English.
    """
    locale = locale.replace("-", "_")
    if locale in SUPPORTED_LOCALES:
        return locale
    language = locale.split("_", 1)[0].lower()
    return {"pt": "pt_BR", "es": "es"}.get(language, "en")


def install_translator(override: str | None = None) -> QTranslator | None:
    """Load and install the catalogue for the effective locale.

    Returns the installed translator so the caller can remove it on unload
    (FR-006), or ``None`` when the source locale is in use or no catalogue is
    present. A missing catalogue is not an error: English is the source
    language, so the UI stays correct.
    """
    locale = resolve_locale(override)
    if locale == "en":
        return None

    qm_file = I18N_DIR / f"geocomp_{locale}.qm"
    if not qm_file.exists():
        return None

    translator = QTranslator()
    if not translator.load(str(qm_file)):
        return None
    QCoreApplication.installTranslator(translator)
    return translator
