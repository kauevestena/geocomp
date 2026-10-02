# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS products: what a session needs, where it comes from, and the record of it
(FR-352, FR-353, NFR-010; ``specs/08`` section 5, phase P10c).

**Resolution order**, for each product a session needs: the local cache, then the
configured product directory, then a configured service. A product found in the
cache or the directory costs no network call -- a second run with the same
products is offline (``specs/08`` §10 criterion 6).

**The cache is keyed** by product kind, latency class, analysis centre and day,
so a re-run with final products where rapid ones were used before is a
deliberate, visible change rather than an accident of what happened to be on
disk. Each cached product carries a record: the service and URL it came from and
the SHA-256 of what was downloaded and of what is used.

**Services are templates.** A service is a set of URL templates, one or more per
product, tried in order, with the date fields a product name needs: ``{yyyy}``,
``{yy}``, ``{doy}``, GPS ``{week}`` and day-of-week ``{dow}``. One is shipped:
NOAA's CORS open-data archive on Amazon S3 (``noaa-ncn``), anonymous, whose day
folders hold the IGS final, rapid and ultra-rapid orbits and the GPS and GLONASS
broadcast navigation -- its URLs are the ones RD-06 already pins by hash. Other
archives (IGS, CDDIS, BKG, IBGE) are added by the user in a services file; their
templates are **not** shipped, because none of them is reachable from the
environment GeoComp is developed in and a template nobody could test is a claim
(``specs/23`` W-14).

**Credentials never appear here** (FR-353, NFR-010). A service that needs a login
names a QGIS authentication configuration (``authcfg``) -- an identifier, not a
secret -- and the QGIS network stack applies it. A template carrying a user name
or password, or a query parameter that looks like a token, is refused when the
service is read, so no URL GeoComp records, logs or exports can carry one.

**Ultra-rapid orbits are not offered.** Each is a two-day file issued four times a
day, half observed and half predicted; which issue covers a given session, and
whether its predicted half is acceptable, is a decision this module does not yet
make well. Final and rapid are.

Pure: no network and no QGIS. The fetching is an injected :class:`Fetcher`, so
everything here is tested without either.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlsplit

from geocomp.core.errors import DataError, ValidationError

__all__ = [
    "BUILTIN_SERVICES",
    "NOAA",
    "Availability",
    "Fetcher",
    "Latency",
    "ProductKind",
    "ProductRecord",
    "ProductRequest",
    "ProductService",
    "Resolution",
    "ResolvedProduct",
    "check_availability",
    "days_of",
    "fetch_with_retry",
    "gps_week",
    "local_record",
    "needed_for",
    "read_services",
    "requests_for",
    "resolve",
    "safe_url",
    "sp3_span",
]

GPS_EPOCH = date(1980, 1, 6)


class ProductKind(Enum):
    #: Precise orbit with satellite clocks, SP3.
    ORBIT = "orbit"
    #: GPS broadcast navigation, RINEX 2.
    GPS_NAVIGATION = "gps_navigation"
    #: GLONASS broadcast navigation, RINEX 2.
    GLONASS_NAVIGATION = "glonass_navigation"


class Latency(Enum):
    """How long after the day a product is published, and how good it is."""

    FINAL = "final"
    RAPID = "rapid"
    #: Broadcast navigation: what the satellites themselves transmitted.
    BROADCAST = "broadcast"


#: The latency classes an orbit falls back through, best first.
ORBIT_LATENCIES = (Latency.FINAL, Latency.RAPID)


def gps_week(day: date) -> tuple[int, int]:
    """GPS week and day of week (Sunday 0) of *day*."""
    days = (day - GPS_EPOCH).days
    return days // 7, days % 7


@dataclass(frozen=True)
class ProductRequest:
    """One product for one day."""

    kind: ProductKind
    day: date
    latency: Latency
    centre: str = "IGS"

    @property
    def key(self) -> str:
        """``kind/latency``: what a service template is keyed by."""
        return f"{self.kind.value}/{self.latency.value}"

    def fields(self) -> dict[str, str]:
        week, dow = gps_week(self.day)
        return {
            "yyyy": f"{self.day.year:04d}",
            "yy": f"{self.day.year % 100:02d}",
            "doy": f"{self.day.timetuple().tm_yday:03d}",
            "week": f"{week:04d}",
            "dow": str(dow),
            "centre": self.centre,
            "centre_lower": self.centre.lower(),
        }

    def cache_directory(self, root: Path) -> Path:
        f = self.fields()
        return root / self.kind.value / self.latency.value / self.centre / f["yyyy"] / f["doy"]

    def describe(self) -> str:
        return f"{self.kind.value} {self.latency.value} {self.day.isoformat()}"

    def with_latency(self, latency: Latency) -> ProductRequest:
        return ProductRequest(self.kind, self.day, latency, self.centre)


_SECRET_KEYS = ("token", "key", "password", "passwd", "pwd", "secret", "signature", "auth", "session")


def safe_url(url: str, *, service: str = "") -> str:
    """*url* if it carries no credential; refused otherwise (NFR-010).

    A user name or password in the authority, or a query parameter named like a
    token, would travel into every record, log line and export the URL reaches.
    Credentials go in a QGIS authentication configuration instead.
    """
    parts = urlsplit(url)
    if parts.username or parts.password:
        raise ValidationError(
            "product_service_credential_in_url",
            service=service,
            expected=(
                "a URL without a user name or password; name a QGIS authentication configuration instead"
            ),
        )
    for name, _value in parse_qsl(parts.query, keep_blank_values=True):
        if any(secret in name.lower() for secret in _SECRET_KEYS):
            raise ValidationError(
                "product_service_credential_in_url",
                service=service,
                expected=(
                    "a URL without a token in its query; name a QGIS authentication configuration instead"
                ),
            )
    if parts.scheme not in ("https", "http", "file"):
        raise ValidationError(
            "product_service_scheme",
            service=service,
            received=parts.scheme,
            expected="https, http or file",
        )
    return url


@dataclass(frozen=True)
class ProductService:
    """Where products come from: URL templates per ``kind/latency``, tried in order.

    Attributes:
        authcfg: The QGIS authentication configuration to apply, by its id; empty
            for an anonymous service. A reference to a credential, never one.
    """

    id: str
    name: str
    templates: dict[str, tuple[str, ...]]
    authcfg: str = ""

    def __post_init__(self) -> None:
        for template in (t for ts in self.templates.values() for t in ts):
            safe_url(template, service=self.id)

    def urls(self, request: ProductRequest) -> tuple[str, ...]:
        fields = request.fields()
        return tuple(t.format(**fields) for t in self.templates.get(request.key, ()))


_NOAA_DAY = "https://noaa-cors-pds.s3.amazonaws.com/rinex/{yyyy}/{doy}/"

#: NOAA's CORS open-data archive (NODD, ``registry.opendata.aws/noaa-ncn``): each
#: day's folder carries the IGS orbits and the broadcast navigation, anonymously.
#: Long product names since GPS week 2238 (late 2022); the legacy short names
#: before that, and alongside them since.
NOAA = ProductService(
    id="noaa-ncn",
    name="NOAA CORS Network open data (Amazon S3)",
    templates={
        "orbit/final": (
            _NOAA_DAY + "IGS0OPSFIN_{yyyy}{doy}0000_01D_15M_ORB.SP3.gz",
            _NOAA_DAY + "igs{week}{dow}.sp3.gz",
        ),
        "orbit/rapid": (
            _NOAA_DAY + "IGS0OPSRAP_{yyyy}{doy}0000_01D_15M_ORB.SP3.gz",
            _NOAA_DAY + "igr{week}{dow}.sp3.gz",
        ),
        "gps_navigation/broadcast": (_NOAA_DAY + "brdc{doy}0.{yy}n.gz",),
        "glonass_navigation/broadcast": (_NOAA_DAY + "brdc{doy}0.{yy}g.gz",),
    },
)

BUILTIN_SERVICES: dict[str, ProductService] = {NOAA.id: NOAA}

def read_services(payload: dict[str, Any]) -> dict[str, ProductService]:
    """User-defined services from a services document.

    ``{"services": [{"id", "name", "authcfg", "templates": {"orbit/final": [...]}}]}``
    """
    services: dict[str, ProductService] = {}
    for entry in payload.get("services", []):
        try:
            identifier = str(entry["id"]).strip()
            templates = {
                str(key): tuple(value if isinstance(value, list) else [value])
                for key, value in dict(entry["templates"]).items()
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValidationError(
                "product_service_malformed",
                received=str(entry)[:80],
                expected='{"id": ..., "name": ..., "templates": {"orbit/final": ["https://..."]}}',
            ) from error
        if not identifier or identifier in BUILTIN_SERVICES:
            raise ValidationError(
                "product_service_id",
                received=identifier,
                expected="a non-empty id that is not a built-in service's",
            )
        unknown = sorted(set(templates) - {f"{k.value}/{lat.value}" for k in ProductKind for lat in Latency})
        if unknown:
            raise ValidationError("product_service_template_key", service=identifier, received=unknown)
        services[identifier] = ProductService(
            id=identifier,
            name=str(entry.get("name") or identifier),
            templates={k: tuple(str(t) for t in v) for k, v in templates.items()},
            authcfg=str(entry.get("authcfg") or ""),
        )
    return services


# -- fetching -----------------------------------------------------------------


class Fetcher(Protocol):
    """How bytes are fetched: the QGIS network stack in the plugin, a stub in tests.

    Both raise :class:`~geocomp.core.errors.DataError` with code
    ``product_not_found``, ``product_authentication_failed`` or
    ``product_network_failed`` -- three different things for a user to do.
    """

    def exists(self, url: str, authcfg: str) -> bool: ...

    def get(self, url: str, authcfg: str) -> bytes: ...


def fetch_with_retry(
    fetcher: Fetcher,
    url: str,
    authcfg: str,
    *,
    attempts: int = 3,
    delay: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    """Fetch, retrying a network failure with backoff (``specs/08`` §9).

    A missing product and a refused login are not retried: neither changes by
    asking again, and repeating a refused login can lock an account.
    """
    for attempt in range(1, attempts + 1):
        try:
            return fetcher.get(url, authcfg)
        except DataError as error:
            if not error.code.endswith("product_network_failed") or attempt == attempts:
                raise
            sleep(delay * 2 ** (attempt - 1))
    raise AssertionError("unreachable")  # pragma: no cover


# -- records ------------------------------------------------------------------


@dataclass(frozen=True)
class ProductRecord:
    """What a product used was, and where it came from (FR-134, NFR-007).

    ``url`` is credential-free by construction; ``origin`` is ``download``,
    ``cache`` or ``directory``; ``sha256`` is of the file the engine reads.
    """

    name: str
    kind: str
    latency: str
    day: str
    origin: str
    service: str = ""
    url: str = ""
    sha256: str = ""
    downloaded_sha256: str = ""
    size: int = 0
    retrieved: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProductRecord:
        return cls(**{k: payload[k] for k in cls.__dataclass_fields__ if k in payload})


@dataclass(frozen=True)
class ResolvedProduct:
    request: ProductRequest
    path: Path
    record: ProductRecord


@dataclass(frozen=True)
class Resolution:
    """What a set of requests resolved to.

    ``substituted`` pairs a request with the lower latency used in its place;
    it is recorded, never silent (``specs/08`` §5).
    """

    resolved: tuple[ResolvedProduct, ...] = ()
    missing: tuple[tuple[ProductRequest, str], ...] = ()
    substituted: tuple[tuple[ProductRequest, Latency], ...] = ()

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(str(p.path) for p in self.resolved)

    @property
    def records(self) -> tuple[ProductRecord, ...]:
        return tuple(p.record for p in self.resolved)

    def to_dict(self) -> dict[str, Any]:
        """The provenance entry: every product used, and every substitution made."""
        return {
            "products": [record.to_dict() for record in self.records],
            "substituted": [
                {"product": request.describe(), "used": latency.value}
                for request, latency in self.substituted
            ],
            "missing": [
                {"product": request.describe(), "reason": reason} for request, reason in self.missing
            ],
        }


@dataclass(frozen=True)
class Availability:
    """Whether a product can be had, and from where, before anything is fetched."""

    request: ProductRequest
    source: str = ""
    url: str = ""
    fallback: Latency | None = None
    reason: str = ""

    @property
    def available(self) -> bool:
        return bool(self.source)


# -- what a session needs -----------------------------------------------------------


def days_of(spans: Iterable[tuple[datetime | None, datetime | None]]) -> list[date]:
    """Every day the observation spans touch, in order.

    A session across midnight needs both days' orbits; a span with no end is
    taken as its first day.
    """
    days: set[date] = set()
    for start, end in spans:
        if start is None:
            continue
        last = (end or start).date()
        day = start.date()
        while day <= last:
            days.add(day)
            day += timedelta(days=1)
    return sorted(days)


def requests_for(
    days: Sequence[date],
    kinds: Sequence[ProductKind],
    *,
    latency: Latency = Latency.FINAL,
) -> list[ProductRequest]:
    """One request per day and kind; navigation is always broadcast."""
    return [
        ProductRequest(kind, day, latency if kind is ProductKind.ORBIT else Latency.BROADCAST)
        for day in days
        for kind in kinds
    ]


def needed_for(
    sessions: Sequence[Any],
    *,
    precise: bool,
    glonass: bool = False,
    latency: Latency = Latency.FINAL,
) -> list[ProductRequest]:
    """What a set of sessions processed together needs from outside the folder.

    An orbit for every day the sessions touch when the precise ephemeris is
    selected; broadcast navigation only when **no** session brought its own --
    a campaign folder with navigation files keeps using them, so a run that
    worked offline before P10c still does. GLONASS navigation is asked for only
    when GLONASS is among the systems processed.

    *sessions* need ``start``, ``end`` and ``nav_files``, which
    :class:`~geocomp.core.models.network.GnssSession` has.
    """
    kinds: list[ProductKind] = []
    if precise:
        kinds.append(ProductKind.ORBIT)
    if not any(session.nav_files for session in sessions):
        kinds.append(ProductKind.GPS_NAVIGATION)
        if glonass:
            kinds.append(ProductKind.GLONASS_NAVIGATION)
    if not kinds:
        return []
    return requests_for(days_of((s.start, s.end) for s in sessions), kinds, latency=latency)


def local_record(path: Path, kind: str) -> ProductRecord:
    """The record of a file used as it is, from the product directory.

    For what this module does not resolve by day -- clock and ionosphere files
    the user placed in the directory -- so that they are named and checksummed
    in provenance like every other input (FR-134).
    """
    data = Path(path).read_bytes()
    return ProductRecord(
        name=Path(path).name,
        kind=kind,
        latency="",
        day="",
        origin="directory",
        sha256=_sha256(data),
        size=len(data),
    )


def sp3_span(head: bytes | str) -> tuple[datetime, datetime] | None:
    """The first and last epoch an SP3 file states in its first two header lines.

    ``#cP2025  1  1  0  0  0.00000000      96 ORBIT IGS20 HLM  IGS`` gives the
    first epoch and the number of epochs; ``## 2347      0.00000000   900.00000000 ...``
    gives the interval. ``None`` for anything that is not an SP3 header.
    """
    text = head.decode("ascii", "replace") if isinstance(head, bytes) else head
    lines = text.splitlines()
    if len(lines) < 2 or not lines[0].startswith("#") or not lines[1].startswith("##"):
        return None
    try:
        fields = lines[0][3:].split()
        first = datetime(*(int(v) for v in fields[:5]), int(float(fields[5])))
        count = int(fields[6])
        interval = float(lines[1].split()[3])
    except (IndexError, ValueError):
        return None
    if count < 1 or interval <= 0:
        return None
    return first, first + timedelta(seconds=interval * (count - 1))


# -- resolution -----------------------------------------------------------------------


def check_availability(
    requests: Sequence[ProductRequest],
    *,
    cache: Path | None,
    directory: Path | None,
    services: Sequence[ProductService],
    fetcher: Fetcher | None,
    fallback: bool = False,
) -> list[Availability]:
    """What can be had for each request, before a batch starts (``specs/08`` §5).

    A product unavailable at its latency is offered at a lower one when
    *fallback* allows it -- reported, so the user decides before a long batch
    rather than learning afterwards.
    """
    report = []
    for request in requests:
        found = _available(request, cache, directory, services, fetcher)
        if found.available or not fallback or request.kind is not ProductKind.ORBIT:
            report.append(found)
            continue
        start = ORBIT_LATENCIES.index(request.latency)
        lower = ORBIT_LATENCIES[start + 1 :]
        for latency in lower:
            alternative = _available(request.with_latency(latency), cache, directory, services, fetcher)
            if alternative.available:
                report.append(
                    Availability(request, alternative.source, alternative.url, fallback=latency)
                )
                break
        else:
            report.append(found)
    return report


def resolve(
    requests: Sequence[ProductRequest],
    *,
    cache: Path,
    directory: Path | None,
    services: Sequence[ProductService],
    fetcher: Fetcher | None,
    fallback: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = datetime.now,
) -> Resolution:
    """Each request from the cache, the directory, or a service, in that order.

    Downloads land in the cache, decompressed, with their record beside them. A
    request nothing can satisfy is returned in ``missing`` with the reason --
    the caller decides whether a run can proceed without it.
    """
    resolved: list[ResolvedProduct] = []
    missing: list[tuple[ProductRequest, str]] = []
    substituted: list[tuple[ProductRequest, Latency]] = []
    for request in requests:
        candidates = [request]
        if fallback and request.kind is ProductKind.ORBIT:
            start = ORBIT_LATENCIES.index(request.latency)
            candidates += [request.with_latency(lat) for lat in ORBIT_LATENCIES[start + 1 :]]
        reasons: list[str] = []
        for candidate in candidates:
            product = _local(candidate, cache, directory)
            if product is None and fetcher is not None:
                try:
                    product = _download(candidate, cache, services, fetcher, sleep, now)
                except DataError as error:
                    if not error.code.endswith("product_not_found"):
                        raise
                    reasons.append(error.code.split(".")[-1])
            if product is not None:
                resolved.append(product)
                if candidate.latency is not request.latency:
                    substituted.append((request, candidate.latency))
                break
        else:
            reason = "not found" if reasons or fetcher is not None else "no download service"
            missing.append((request, reason))
    return Resolution(tuple(resolved), tuple(missing), tuple(substituted))


# -- internals ------------------------------------------------------------------------


def _names(request: ProductRequest, services: Sequence[ProductService]) -> list[str]:
    """The file names a request may have, decompressed: from every template."""
    names = []
    for service in [*services, NOAA]:
        for url in service.urls(request):
            name = _decompressed(url.rsplit("/", 1)[-1])
            if name not in names:
                names.append(name)
    return names


def _decompressed(name: str) -> str:
    return name[:-3] if name.lower().endswith(".gz") else name


def _local(request: ProductRequest, cache: Path | None, directory: Path | None) -> ResolvedProduct | None:
    if cache is not None:
        folder = request.cache_directory(cache)
        if folder.is_dir():
            for path in sorted(folder.iterdir()):
                record_path = path.with_name(path.name + ".json")
                if path.suffix == ".json" or not record_path.is_file():
                    continue
                record = ProductRecord.from_dict(json.loads(record_path.read_text(encoding="utf-8")))
                if _sha256(path.read_bytes()) != record.sha256:
                    continue  # a damaged cache entry is fetched again, not used
                return ResolvedProduct(request, path, _replace(record, origin="cache"))
    if directory is not None and directory.is_dir():
        candidate = _in_directory(request, directory)
        if candidate is not None:
            return _from_directory(request, candidate, cache)
    return None


def _in_directory(request: ProductRequest, directory: Path) -> Path | None:
    """The directory's file for *request*: by IGS name, else an orbit by its header.

    The name comes first because it is cheap and exact. An orbit under another
    analysis centre's name (``COD0OPSFIN_...``, ``com23470.sp3``) is then found
    by the span its header states -- the file must cover at least 23 hours of
    the day -- which replaces P7's rule of handing the engine every SP3 in the
    directory whatever its day.
    """
    for name in _names(request, ()):
        for candidate in (directory / name, directory / (name + ".gz")):
            if candidate.is_file():
                return candidate
    if request.kind is not ProductKind.ORBIT:
        return None
    day = datetime(request.day.year, request.day.month, request.day.day)
    for candidate in sorted(directory.iterdir()):
        lowered = candidate.name.lower()
        if not candidate.is_file() or not lowered.endswith((".sp3", ".sp3.gz")):
            continue
        try:
            opener = gzip.open if lowered.endswith(".gz") else open
            with opener(candidate, "rb") as stream:
                span = sp3_span(stream.readline() + stream.readline())
        except (OSError, EOFError):
            continue
        if span is None:
            continue
        overlap = min(span[1], day + timedelta(days=1)) - max(span[0], day)
        if overlap >= timedelta(hours=23):
            return candidate
    return None


def _from_directory(request: ProductRequest, candidate: Path, cache: Path | None) -> ResolvedProduct:
    """A directory product, inflated into the cache when it is compressed.

    The engine reads an SP3 by its extension and skips ``.gz`` (``readsp3``,
    ``src/preceph.c`` at the pinned commit), so a compressed orbit handed over
    as it is would be loaded by nothing -- with no error. The
    inflated copy goes in the cache with its record; the original is untouched.
    Without a cache (an availability check) the compressed file is reported as
    it is.
    """
    raw = candidate.read_bytes()
    record = ProductRecord(
        name=candidate.name,
        kind=request.kind.value,
        latency=request.latency.value,
        day=request.day.isoformat(),
        origin="directory",
        sha256=_sha256(raw),
        size=len(raw),
    )
    if cache is None or not candidate.name.lower().endswith(".gz"):
        return ResolvedProduct(request, candidate, record)
    data = _inflate(raw, candidate.name)
    path = _store(request, cache, _decompressed(candidate.name), data)
    record = _replace(
        record, name=path.name, sha256=_sha256(data), downloaded_sha256=_sha256(raw), size=len(data)
    )
    _write_record(path, record)
    return ResolvedProduct(request, path, record)


def _store(request: ProductRequest, cache: Path, name: str, data: bytes) -> Path:
    folder = request.cache_directory(cache)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    temporary = path.with_name(path.name + ".part")
    temporary.write_bytes(data)
    temporary.replace(path)
    return path


def _write_record(path: Path, record: ProductRecord) -> None:
    path.with_name(path.name + ".json").write_text(
        json.dumps(record.to_dict(), indent=1, sort_keys=True), encoding="utf-8"
    )


def _available(
    request: ProductRequest,
    cache: Path | None,
    directory: Path | None,
    services: Sequence[ProductService],
    fetcher: Fetcher | None,
) -> Availability:
    local = _local(request, cache, directory)
    if local is not None:
        return Availability(request, local.record.origin, "")
    if fetcher is None:
        return Availability(request, reason="no download service")
    for service in services:
        for url in service.urls(request):
            if fetcher.exists(url, service.authcfg):
                return Availability(request, service.id, url)
    return Availability(request, reason="not found")


def _download(
    request: ProductRequest,
    cache: Path,
    services: Sequence[ProductService],
    fetcher: Fetcher,
    sleep: Callable[[float], None],
    now: Callable[[], datetime],
) -> ResolvedProduct:
    for service in services:
        for url in service.urls(request):
            try:
                raw = fetch_with_retry(fetcher, url, service.authcfg, sleep=sleep)
            except DataError as error:
                if error.code.endswith("product_not_found"):
                    continue
                raise
            name = url.rsplit("/", 1)[-1]
            data = _inflate(raw, name)
            path = _store(request, cache, _decompressed(name), data)
            record = ProductRecord(
                name=path.name,
                kind=request.kind.value,
                latency=request.latency.value,
                day=request.day.isoformat(),
                origin="download",
                service=service.id,
                url=safe_url(url, service=service.id),
                sha256=_sha256(data),
                downloaded_sha256=_sha256(raw),
                size=len(data),
                retrieved=now().astimezone().isoformat(timespec="seconds"),
            )
            _write_record(path, record)
            return ResolvedProduct(request, path, record)
    raise DataError("product_not_found", product=request.describe(), services=[s.id for s in services])


def _inflate(raw: bytes, name: str) -> bytes:
    if name.lower().endswith(".gz"):
        try:
            return gzip.decompress(raw)
        except (OSError, EOFError) as error:
            raise DataError("product_corrupt", product=name, reason=str(error)) from error
    if name.endswith(".Z"):
        raise DataError(
            "product_compression_unsupported",
            product=name,
            expected="a .gz or uncompressed product; Unix compress (.Z) is not read",
        )
    return raw


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _replace(record: ProductRecord, **changes: Any) -> ProductRecord:
    return ProductRecord(**{**record.to_dict(), **changes})

