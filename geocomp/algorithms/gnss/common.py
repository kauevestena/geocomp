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

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qgis.core import (
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.core.techniques.gnss.products import (
    BUILTIN_SERVICES,
    Fetcher,
    ProductRecord,
    ProductService,
    Resolution,
    local_record,
    needed_for,
    read_services,
    resolve,
)
from geocomp.core.techniques.gnss.stations import StationDatabase
from geocomp.engines.base import DEFAULT_TIMEOUT
from geocomp.engines.rtklib.config import (
    PROFILES,
    RtklibConfig,
    read_user_options,
    with_user_options,
)

if TYPE_CHECKING:
    from geocomp.core.models import GnssSession
    from geocomp.engines.rtklib.engine import RtklibEngine

__all__ = [
    "PPP_NOTICE_CODE",
    "SessionProducts",
    "base_coordinates",
    "configuration_help",
    "configuration_parameter",
    "configured_profile",
    "engine_record",
    "frame_choices",
    "gather_products",
    "gnss_engine",
    "gnss_setting",
    "missing_products_message",
    "ppp_limitation_notice",
    "product_cache",
    "product_directory",
    "product_services",
    "reference_stations",
    "run_frame",
    "session_products",
    "timeout_parameter",
    "translate_error",
    "user_configuration",
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
PRODUCT_SERVICES = "gnss.product_services"
SERVICE_DEFINITIONS = "gnss.service_definitions"
PRODUCT_CACHE = "gnss.product_cache"
PRODUCT_FALLBACK = "gnss.product_fallback"

#: RTKLIB's bit for GLONASS in ``pos1-navsys``.
_GLONASS = 4

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


def configured_profile(
    profile_name: str,
    *,
    user_options: Mapping[str, str] | None = None,
    **overrides: Any,
) -> RtklibConfig:
    """A named profile with the user's Global Settings applied (FR-063, FR-358).

    The profile fixes what the *mode* requires -- a static run is static -- and
    the settings supply what the *user* chose: mask, ephemeris source,
    atmospheric models, ambiguity threshold. ``user_options``, from an options
    file of the user's own (FR-070), come over the settings, and explicit
    ``overrides`` win over all of them, which is how a Processing parameter beats
    a global default without either having to know about the other.
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

    configuration = PROFILES[profile_name].with_options(**configured)
    if user_options:
        try:
            configuration = with_user_options(configuration, user_options)
        except GeoCompError as exc:
            raise QgsProcessingException(
                _tr("%1: %2")
                .replace("%1", _configuration_label())
                .replace("%2", translate_error(exc))
            ) from exc
    return configuration.with_options(**overrides)


def _configuration_label() -> str:
    return _tr("RTKLIB configuration file")


def configuration_parameter(name: str) -> QgsProcessingParameterFile:
    """An options file of the user's own, for Advanced mode (FR-070, P12c-21).

    The same on every algorithm that runs ``rnx2rtkp``, as the timeout is.
    """
    return QgsProcessingParameterFile(
        name,
        _configuration_label(),
        optional=True,
        fileFilter=_tr("RTKLIB options (*.conf);;All files (*)"),
    )


def configuration_help() -> str:
    """What :func:`configuration_parameter` takes, for each algorithm's help."""
    return _tr(
        "<p><b>RTKLIB configuration file</b> (Advanced) &mdash; options of your own for "
        "<code>rnx2rtkp</code>, as <code>key = value</code> lines in RTKLIB's own "
        "format: any option it reads, including those GeoComp offers no parameter for. "
        "They come over Global Settings, and the parameters here come over them. Three "
        "things stay GeoComp's, and a file that sets one is refused: the positioning "
        "mode, which is the menu item; the base station's position "
        "(<code>ant2-postype</code> and <code>ant2-pos1</code> to <code>ant2-pos3</code>), "
        "which GeoComp holds; and every <code>out-</code> option, because the solution "
        "is read back by them. The summary records the file and the options taken from "
        "it.</p>"
    )


def user_configuration(
    algorithm: Any, parameters: dict[str, Any], name: str, context: Any
) -> dict[str, Any] | None:
    """The options file given to *name*, read, as the summary records it.

    ``{"file": ..., "options": {...}}``, or ``None`` when none was given. A file
    that cannot be read, or sets nothing, is refused against the parameter.
    """
    path = algorithm.parameterAsFile(parameters, name, context)
    if not path:
        return None
    try:
        options = read_user_options(path)
    except GeoCompError as exc:
        raise QgsProcessingException(algorithm.about_input(name, translate_error(exc))) from exc
    return {"file": str(path), "options": options}


def product_directory() -> Path | None:
    """The configured product directory (FR-063), or ``None`` when unset."""
    directory = gnss_setting(PRODUCT_DIRECTORY)
    if not directory:
        return None
    root = Path(directory)
    if not root.is_dir():
        raise QgsProcessingException(
            _tr("The configured product directory does not exist: %1").replace("%1", str(root))
        )
    return root


def product_cache() -> Path:
    """Where downloaded products are kept (FR-352).

    Unset, it is ``geocomp/products`` in the QGIS profile folder: a cache that
    works without configuration and is never written inside a project.
    """
    configured = gnss_setting(PRODUCT_CACHE)
    if configured:
        return Path(configured)
    from qgis.core import QgsApplication

    return Path(QgsApplication.qgisSettingsDirPath()) / "geocomp" / "products"


def product_services() -> list[ProductService]:
    """The configured download services, in priority order (FR-352, FR-353).

    Ids come from the setting; the shipped service is known by its id, others
    from the services file. An id that names nothing is refused by name rather
    than skipped -- a typo would otherwise read as "the archive has no product".
    """
    raw = str(gnss_setting(PRODUCT_SERVICES) or "")
    names = [name.strip() for name in raw.replace(";", ",").split(",") if name.strip()]
    known: dict[str, ProductService] = dict(BUILTIN_SERVICES)
    definitions = gnss_setting(SERVICE_DEFINITIONS)
    if definitions:
        path = Path(definitions)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise QgsProcessingException(
                _tr("Could not read the download services file %1: %2")
                .replace("%1", str(path))
                .replace("%2", str(exc))
            ) from exc
        try:
            known.update(read_services(payload))
        except GeoCompError as exc:
            raise QgsProcessingException(translate_error(exc)) from exc
    unknown = [name for name in names if name not in known]
    if unknown:
        raise QgsProcessingException(
            _tr("Unknown download service: %1. Known services: %2")
            .replace("%1", ", ".join(unknown))
            .replace("%2", ", ".join(sorted(known)))
        )
    return [known[name] for name in names]


@dataclass(frozen=True)
class SessionProducts:
    """What a run hands the engine besides its observations, and the record of it."""

    paths: tuple[str, ...] = ()
    resolution: Resolution = field(default_factory=Resolution)
    #: Clock and ionosphere files used from the directory as they are.
    extras: tuple[ProductRecord, ...] = ()

    def provenance(self) -> dict[str, Any]:
        """Every product by name, origin and checksum (FR-134, ``specs/08`` §5)."""
        entry = self.resolution.to_dict()
        entry["products"] += [record.to_dict() for record in self.extras]
        return entry

    def missing(self) -> list[str]:
        """Every product that could not be resolved, described with the reason."""
        return [f"{request.describe()} ({reason})" for request, reason in self.resolution.missing]


def session_products(
    sessions: Sequence[Any],
    ephemeris: str,
    navigation_systems: int,
    feedback: Any,
    *,
    fetcher: Fetcher | None = None,
) -> SessionProducts:
    """Resolve what *sessions* need, or refuse before the engine starts (FR-352).

    An orbit for each day the sessions touch when the precise ephemeris is
    selected, and broadcast navigation when the folder brought none; each from
    the cache, the product directory, then the configured services. A product
    nothing can supply stops the run here, naming it -- the engine's alternative
    is no solution and a message about something else.
    """
    try:
        found = gather_products(sessions, ephemeris, navigation_systems, feedback, fetcher=fetcher)
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc
    if found.resolution.missing:
        raise QgsProcessingException(missing_products_message(found.missing()))
    return found


def gather_products(
    sessions: Sequence[Any],
    ephemeris: str,
    navigation_systems: int,
    feedback: Any,
    *,
    fetcher: Fetcher | None = None,
) -> SessionProducts:
    """:func:`session_products` without the refusal, for a batch to decide.

    What is missing stays in the resolution; a download that failed -- the
    network, a refused login -- raises its :class:`GeoCompError`, so a batch can
    report it against the session and go on (``specs/08`` §9). A lower-latency
    orbit is used in place of a missing final one only when the fallback
    setting allows it, and the substitution is logged and recorded.
    """
    precise = ephemeris == "precise"
    requests = needed_for(sessions, precise=precise, glonass=bool(navigation_systems & _GLONASS))
    directory = product_directory()
    extras = tuple(_directory_extras(directory)) if precise else ()
    if not requests:
        return SessionProducts(paths=tuple(str(path) for path, _ in extras), extras=_records(extras))
    services = product_services()
    if services and fetcher is None:
        from geocomp.services.downloads import QgisFetcher

        fetcher = QgisFetcher(feedback)
    resolution = resolve(
        requests,
        cache=product_cache(),
        directory=directory,
        services=services,
        fetcher=fetcher if services else None,
        fallback=bool(gnss_setting(PRODUCT_FALLBACK)),
    )
    for request, latency in resolution.substituted:
        feedback.pushWarning(
            _tr("%1: used the %2 orbit, as Global Settings allow; recorded in provenance.")
            .replace("%1", request.describe())
            .replace("%2", latency.value)
        )
    for record in resolution.records:
        feedback.pushInfo(
            _tr("Product %1 (%2)").replace("%1", record.name).replace("%2", record.origin)
        )
    return SessionProducts(
        paths=(*resolution.paths, *(str(path) for path, _ in extras)),
        resolution=resolution,
        extras=_records(extras),
    )


def missing_products_message(missing: Sequence[str]) -> str:
    """The refusal for products nothing could supply, with the three ways out."""
    return _tr(
        "Products this run needs are not available: %1. Place them in the "
        "product directory, add a download service in Global Settings → GNSS, "
        "or -- for a recent session whose final orbit is not yet published -- "
        "allow rapid orbits there."
    ).replace("%1", "; ".join(missing))


def _directory_extras(directory: Path | None) -> list[tuple[Path, str]]:
    """Clock and ionosphere files in the directory, which P10c does not resolve by day."""
    if directory is None:
        return []
    # Keyed by path: on a case-insensitive file system both patterns of a pair
    # match the same file, and it must reach the engine once.
    found: dict[Path, str] = {}
    for kind, patterns in (("clock", ("*.CLK", "*.clk")), ("ionosphere", ("*.ION", "*.ionex"))):
        for pattern in patterns:
            for path in sorted(directory.glob(pattern)):
                if path.is_file():
                    found.setdefault(path.resolve(), kind)
    return list(found.items())


def _records(extras: Sequence[tuple[Path, str]]) -> tuple[ProductRecord, ...]:
    return tuple(local_record(path, kind) for path, kind in extras)


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


def frame_choices() -> list[str]:
    """How the frame a relative run's results are in is chosen (specs/11 §7).

    The order is stored by saved models as an index: appending is safe,
    reordering is not.
    """
    from geocomp.core.geodesy.frames import FRAME_NAMES

    return [
        _tr("The project's: the preferred CRS's frame"),
        _tr("As the base station publishes it"),
        *FRAME_NAMES,
    ]


def run_frame(index: int) -> str | None:
    """The frame chosen by *index* in :func:`frame_choices`, or ``None`` for the base's own.

    The project's frame is the datum of ``reference_systems.preferred_crs``,
    read through its geographic CRS, so a UTM zone of SIRGAS 2000 names SIRGAS
    2000. ``None`` when no CRS is preferred, or it names a datum no
    transformation is held for: the base is then used in its own frame, and
    the run says so.
    """
    from geocomp.core.geodesy.frames import FRAME_NAMES, canonical_frame

    if index >= 2:
        return FRAME_NAMES[index - 2]
    if index == 1:
        return None
    from qgis.core import QgsCoordinateReferenceSystem

    from geocomp.algorithms.defaults import configured

    preferred = str(configured("reference_systems.preferred_crs") or "")
    crs = QgsCoordinateReferenceSystem(preferred) if preferred else None
    if crs is None or not crs.isValid():
        return None
    for name in (crs.authid(), _datum_crs_name(crs)):
        try:
            return canonical_frame(name)
        except GeoCompError:
            continue
    return None


def _datum_crs_name(crs) -> str:
    """The name of *crs*'s geographic base: ``SIRGAS 2000`` for a SIRGAS 2000 UTM zone.

    Read from the WKT2, because QGIS's ``toGeographicCrs()`` returns the base
    with its axes normalised for display, which has no authority code.
    """
    import re

    from qgis.core import Qgis, QgsCoordinateReferenceSystem

    # QGIS 4 spells the variant Qgis.CrsWktVariant.Wkt2_2019; QGIS 3 kept it on
    # the CRS class. Neither found, the default WKT1 names the datum too.
    variant = None
    for owner, name in (
        (getattr(Qgis, "CrsWktVariant", None), "Wkt2_2019"),
        (getattr(QgsCoordinateReferenceSystem, "WktVariant", None), "WKT2_2019"),
    ):
        if owner is not None and hasattr(owner, name):
            variant = getattr(owner, name)
            break
    wkt = crs.toWkt(variant) if variant is not None else crs.toWkt()
    found = re.search(r'(?:BASEGEOGCRS|BASEGEODCRS|GEOGCRS|GEODCRS|GEOGCS)\["([^"]+)"', wkt)
    return found.group(1) if found else ""


def base_coordinates(
    session: GnssSession, frame: str | None, feedback: QgsProcessingFeedback
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Where RTKLIB is to hold the base, and the record of how that was decided (FR-832).

    A base in the reference-station database (FR-063) is held at its published
    coordinates, in *frame* -- its own when ``None`` -- at the session's epoch:
    transformed and moved along its velocity as needed, with every step
    recorded. What cannot be done is refused before the engine runs.

    A base not in the database is held where its RINEX header puts it, as
    before. That position is approximate and in no stated frame, and the record
    says so, so nothing downstream can mistake the result for a framed one.

    Returns:
        RTKLIB option overrides, and the record for the run's summary.
    """
    from geocomp.core.models.epoch import Epoch

    database = reference_stations()
    if session.station_id not in database.stations:
        feedback.pushInfo(
            _tr(
                "Base %1 is not in the reference-station database, so RTKLIB holds it at the "
                "approximate position in its RINEX header, and the results are in no stated frame."
            ).replace("%1", session.station_id)
        )
        return {}, {"station": session.station_id, "source": "RINEX header", "frame": None}

    if session.start is None:
        raise QgsProcessingException(
            _tr(
                "The session of base %1 states no start time, so its published coordinates cannot "
                "be brought to the epoch it was observed at."
            ).replace("%1", session.station_id)
        )
    published = database.get(session.station_id)
    at = Epoch.from_datetime(session.start)
    try:
        held = database.resolve(
            session.station_id,
            frame=frame or published.frame,
            epoch=at,
            operation="relative processing",
        )
    except GeoCompError as exc:
        raise QgsProcessingException(translate_error(exc)) from exc

    transformation = held.meta.get("transformation")
    if transformation:
        feedback.pushInfo(
            _tr("Base %1: published in %2 at %3, transformed to %4 at %5 for this run.")
            .replace("%1", session.station_id)
            .replace("%2", published.frame)
            .replace("%3", localised(f"{transformation['source_epoch']:.4f}"))
            .replace("%4", held.frame)
            .replace("%5", localised(f"{at.decimal_year:.4f}"))
        )
    record = {
        "station": session.station_id,
        "source": published.source or "reference-station database",
        "frame": held.frame,
        "epoch": at.decimal_year,
        "xyz": list(held.xyz),
        "published": {
            "frame": published.frame,
            "epoch": None if published.epoch is None else published.epoch.decimal_year,
            "xyz": list(published.xyz),
        },
    }
    if transformation:
        record["transformation"] = transformation
    if "propagated_years" in held.meta:
        record["propagated_years"] = held.meta["propagated_years"]
    return {"base_position": held.xyz, "base_position_type": "xyz"}, record


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


def gnss_engine(feedback: QgsProcessingFeedback) -> RtklibEngine:
    """The RTKLIB the algorithms run, warned about when it is untested (FR-302).

    The engine detects its version and caches it; warning is the plugin's job,
    because a warning nothing shows is not one. Until P12c-11 DynAdjust's
    adjustment warned and nothing that runs RTKLIB did. The engine's absence is
    not handled here: the run refuses it, in words (FR-306).
    """
    from geocomp.services.engines import rtklib_engine

    engine = rtklib_engine()
    version = engine.version()
    if version is not None:
        if not version.tested:
            feedback.pushWarning(
                _tr(
                    "%1 %2 has not been checked against this GeoComp release. It will "
                    "be used, but if its output format has changed the solution may be "
                    "refused when it is read back."
                )
                .replace("%1", version.name)
                .replace("%2", version.version)
            )
        feedback.pushInfo(
            _tr("Using %1 %2 from %3.")
            .replace("%1", version.name)
            .replace("%2", version.version)
            .replace("%3", str(version.path))
        )
    return engine


def engine_record(engine: RtklibEngine) -> dict[str, Any] | None:
    """The engine version that produced a result, for its summary (FR-302)."""
    version = engine.version()
    return version.to_dict() if version is not None else None


def timeout_parameter(name: str) -> QgsProcessingParameterNumber:
    """The time limit on each ``rnx2rtkp`` run, which FR-304 requires be configurable.

    Until P12c-11 it was the engine layer's fixed ten minutes: a long session at
    a high rate could not be processed at all, and the refusal could not say
    what to change.
    """
    return QgsProcessingParameterNumber(
        name,
        _tr("Timeout per run (s)"),
        type=QgsProcessingParameterNumber.Type.Double,
        defaultValue=DEFAULT_TIMEOUT,
        minValue=1.0,
    )


def translate_error(error: GeoCompError) -> str:
    """Phrase a core error for Processing, at the boundary where phrasing is allowed."""
    from geocomp.services.messages import message_for

    return message_for(error)
