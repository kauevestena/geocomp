# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared plumbing for the GNSS algorithms.

The same needs the levelling package has -- a document to read, settings to
resolve, one way of presenting findings -- plus the two GNSS adds: a
configuration built from the Global Settings (FR-063) and the FR-604 notice.

**Every default here comes from the settings service, not from a literal.** The
pre-P7 review found 36 settings that the Global Settings window offered and
nothing read, because each algorithm declared its own hard-coded Processing
default; `specs/15` section 2.3 records it. The GNSS settings are wired from the
first commit that declares them so they never join that list.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.gnss.stations import StationDatabase
from geocomp.engines.rtklib.config import PROFILES, RtklibConfig

__all__ = [
    "PPP_NOTICE_CODE",
    "configured_profile",
    "gnss_setting",
    "ppp_limitation_notice",
    "product_files",
    "reference_stations",
    "translate_error",
]

# The settings this module reads, written out in full rather than composed from
# a prefix. `tests/structural/test_settings_are_honoured.py` scans the sources
# for each declared key, so an f-string like f"gnss.{name}" would make a wired
# setting look unwired -- and, worse, would turn a typo in the name into a
# silent miss at run time instead of a NameError here.
ANTENNA_FILE = "gnss.antenna_file"
PRODUCT_DIRECTORY = "gnss.product_directory"
REFERENCE_STATION_DATABASE = "gnss.reference_station_database"
ELEVATION_MASK = "gnss.elevation_mask"
EPHEMERIS = "gnss.ephemeris"
IONOSPHERE = "gnss.ionosphere"
TROPOSPHERE = "gnss.troposphere"
AMBIGUITY_THRESHOLD = "gnss.ambiguity_threshold"
INDEPENDENT_BASELINES_ONLY = "gnss.independent_baselines_only"

_CONTEXT = "GeoCompGnss"

#: The message code for FR-604's notice. A code rather than a sentence, because
#: this module is imported by the core-facing helpers too and the phrasing lives
#: with the translations.
PPP_NOTICE_CODE = "gnss.ppp_limitation"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def gnss_setting(key: str) -> Any:
    """Resolve a full setting key through the run/project/global scopes (FR-068).

    Takes the whole dotted key -- one of the constants above -- rather than a
    suffix, for the reason recorded there.
    """
    from geocomp.services.settings_service import settings

    return settings.value(key)


def configured_profile(profile_name: str, **overrides: Any) -> RtklibConfig:
    """A named profile with the user's Global Settings applied (FR-063, FR-358).

    The profile fixes what the *mode* requires -- a static run is static -- and
    the settings supply what the *user* chose: mask, ephemeris source,
    atmospheric models, ambiguity threshold. Explicit ``overrides`` win over
    both, which is how a Processing parameter beats a global default without
    either having to know about the other.
    """
    if profile_name not in PROFILES:
        raise QgsProcessingException(
            _tr("Unknown processing profile: %1").replace("%1", profile_name)
        )
    configured: dict[str, Any] = {
        "elevation_mask": float(gnss_setting(ELEVATION_MASK)),
        "ephemeris": gnss_setting(EPHEMERIS),
        "ionosphere": gnss_setting(IONOSPHERE),
        "troposphere": gnss_setting(TROPOSPHERE),
        "ambiguity_threshold": float(gnss_setting(AMBIGUITY_THRESHOLD)),
    }

    # The antenna calibration, when the user has configured one. Both keys are
    # set together because RTKLIB reads receiver and satellite corrections from
    # the same ANTEX, and `pos1-posopt2` is what actually switches receiver PCV
    # on -- supplying the file without it loads a model the engine then ignores,
    # which is the quietest possible way to think you have calibrated a run.
    antenna_file = gnss_setting(ANTENNA_FILE)
    if antenna_file:
        location = Path(antenna_file)
        if not location.is_file():
            raise QgsProcessingException(
                _tr("The configured antenna file does not exist: %1").replace(
                    "%1", str(location)
                )
            )
        configured["extra"] = {
            "file-rcvantfile": str(location),
            "file-satantfile": str(location),
            "pos1-posopt2": "on",
        }

    configured.update(overrides)
    return PROFILES[profile_name].with_options(**configured)


def product_files(*names: str) -> tuple[str, ...]:
    """Locate precise products in the configured directory (FR-063, FR-358).

    Returns only what exists. A missing product is not an error here: the
    ephemeris setting decides whether precise products are *wanted*, and the
    engine reports what it could not use -- so a caller that silently dropped a
    file the user expected to be used would be the problem, not this.

    **GeoComp does not download them.** FR-352 was re-planned into P10 when
    every candidate archive proved unreachable from the development
    environment (``specs/22`` §5); until then products arrive on disk and this
    is how they are found.
    """
    directory = gnss_setting(PRODUCT_DIRECTORY)
    if not directory:
        return ()
    root = Path(directory)
    if not root.is_dir():
        raise QgsProcessingException(
            _tr("The configured product directory does not exist: %1").replace("%1", str(root))
        )
    if names:
        return tuple(str(root / name) for name in names if (root / name).is_file())
    return tuple(
        str(path)
        for pattern in ("*.SP3", "*.sp3", "*.CLK", "*.clk", "*.ION", "*.ionex")
        for path in sorted(root.glob(pattern))
    )


def reference_stations() -> StationDatabase:
    """The configured reference-station database (FR-063), empty when unset.

    An unset path is not an error: a user processing their own campaign has no
    CORS to look up, and demanding a database they do not need would be a
    worse default than an empty one.
    """
    path = gnss_setting(REFERENCE_STATION_DATABASE)
    if not path:
        return StationDatabase()
    try:
        return StationDatabase.read(path)
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc


def ppp_limitation_notice() -> str:
    """FR-604's notice, stated where the mode is chosen.

    ``specs/08`` section 3 records what the limitation is: ``rnx2rtkp``'s PPP is
    not competitive with a dedicated PPP service, and a user who picks Absolute
    expecting one would get a degraded result presented as a normal one. The
    requirement's words are that GeoComp "MUST state this in the UI rather than
    silently producing a degraded result", so it is in the algorithm's help and
    pushed to the log at run time -- not in documentation nobody opens.
    """
    return _tr(
        "<p><b>Absolute (PPP) processing in RTKLIB is limited.</b> Its precise "
        "point positioning is not equivalent to a dedicated PPP service: "
        "convergence is slower, the ambiguity handling is simpler, and the "
        "result is typically decimetre-level rather than centimetre-level. "
        "Prefer Relative processing where a base station is available, and "
        "treat an Absolute solution as indicative unless you have checked it "
        "against an independent determination.</p>"
    )


def translate_error(error: GeoCompError) -> str:
    """Phrase a core error for Processing, at the boundary where phrasing is allowed."""
    from geocomp.services.messages import message_for

    return message_for(error)
