# SPDX-License-Identifier: GPL-2.0-or-later
"""Turning a folder of RINEX into sessions (FR-351, FR-350).

``specs/08-engine-rtklib.md`` section 4. Scanning produces
:class:`~geocomp.core.models.GnssSession` objects -- which mark, which receiver,
which antenna, over what span, at what interval -- and says which of them
observed *simultaneously*, because that is what decides which pairs can form a
baseline at all.

**Three rules, each of which exists because the alternative fails silently.**

*The header decides, the name is a cross-check.* A session attributed to the
wrong mark by its file name produces a baseline that is confidently wrong and
nothing downstream can detect it, so the marker comes from inside the file and a
disagreement with the name is **reported**, never resolved by preference.

*A file that cannot be read is reported, not skipped* (FR-166). A scan that
quietly drops what it cannot open reports a campaign as smaller than it was, and
the missing session looks like a field failure rather than a software one.

*Pairing that fell back says so.* Navigation files are matched to observation
sessions by date where the names carry one. Where they do not -- a
``brdc`` file, a campaign with its own naming -- every navigation file in the
scan is offered instead, and the session records that this is what happened.
Silently attaching the wrong day's ephemeris is a solution that converges to the
wrong place.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError, GeoCompError
from geocomp.core.findings import Finding, Severity
from geocomp.core.models import GnssSession
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit
from geocomp.io.rinex import (
    Compression,
    HeightMethod,
    RinexHeader,
    compression_of,
    name_hints,
    read_last_epoch,
    read_rinex_header,
)

__all__ = [
    "SessionScan",
    "join_sessions",
    "overlapping_groups",
    "scan_folder",
    "session_from_header",
]

METRE = Unit.METRE

#: Suffixes worth opening. A scan runs over whatever a user points it at, and
#: opening every file in a project folder to discover it is a shapefile is slow
#: and noisy. Anything matching is opened; anything else is passed over in
#: silence, which is different from being *skipped* -- see :class:`SessionScan`.
_CANDIDATE_SUFFIXES = (
    ".rnx", ".crx",                      # RINEX 3 long names
    ".gz", ".z", ".zip",                 # wrappers, judged on the inner name
    ".o", ".d", ".n", ".g", ".l", ".h", ".p", ".m", ".c", ".f",  # RINEX 2 short
)


@dataclass
class SessionScan:
    """What a scan found, and what it could not read.

    Both lists hold :class:`~geocomp.core.findings.Finding` objects, each with
    the file in ``context["file"]``: a code and the values to word it with, as
    everything the core reports. Until P12c-41 they were ``(file, reason)``
    pairs whose reason was this module's English -- "navigation files paired
    by fallback: ..." -- and the algorithms put it into a translated sentence.

    Attributes:
        skipped: One finding for every candidate that could not be read.
            **Never silently empty**: FR-166 requires a scan to report every bad
            file rather than stopping at the first, and a session missing from
            this list and from ``sessions`` both is a session nobody knows about.
        warnings: One finding for each file that was read but says something
            inconsistent -- a marker that disagrees with the name, a navigation
            file paired by fallback. Not errors: the data is usable and the
            user is the one who can say whether it is right.
    """

    sessions: tuple[GnssSession, ...] = ()
    navigation: tuple[Path, ...] = ()
    skipped: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """The scan as JSON: the reasons by code, with the developer's sentence beside each."""
        return {
            "sessions": [session.to_dict() for session in self.sessions],
            "navigation": [str(path) for path in self.navigation],
            "skipped": [_noted(finding) for finding in self.skipped],
            "warnings": [_noted(finding) for finding in self.warnings],
        }


def _noted(finding: Finding) -> dict[str, str]:
    return {"file": finding.context["file"], "code": finding.code, "reason": finding.message}


def scan_folder(folder: str | Path, *, recursive: bool = False) -> SessionScan:
    """Scan *folder* for RINEX and return the sessions it holds.

    Raises:
        DataError: only if *folder* is not a directory. A folder with nothing
            readable in it is an empty scan, not an error -- the caller pointed
            somewhere reasonable and deserves to be told it was empty rather
            than handed an exception.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise DataError(
            "gnss_scan_not_a_directory",
            path=str(folder),
            expected="a directory of RINEX observation and navigation files",
        )

    scan = SessionScan()
    observations: list[tuple[Path, RinexHeader]] = []
    navigation: list[tuple[Path, RinexHeader]] = []

    paths = sorted(folder.rglob("*") if recursive else folder.glob("*"))
    for path in paths:
        if not path.is_file() or not _is_candidate(path):
            continue
        try:
            header = read_rinex_header(path)
        except GeoCompError as error:
            scan.skipped.append(
                Finding(
                    "rinex_unreadable",
                    Severity.WARNING,
                    _reason(error),
                    context={"file": str(path)},
                    error=error,
                )
            )
            continue
        if header.is_observation:
            observations.append((path, header))
        elif header.is_navigation:
            navigation.append((path, header))
        else:
            scan.skipped.append(
                Finding(
                    "rinex_neither_observation_nor_navigation",
                    Severity.WARNING,
                    f"RINEX file type {header.file_type!r} is neither observation nor navigation",
                    context={"file": str(path), "type": header.file_type},
                )
            )

    scan.navigation = tuple(path for path, _ in navigation)
    scan.sessions = tuple(
        session_from_header(path, header, navigation=navigation, scan=scan)
        for path, header in observations
    )
    return scan


def session_from_header(
    path: Path,
    header: RinexHeader,
    *,
    navigation: list[tuple[Path, RinexHeader]] | None = None,
    scan: SessionScan | None = None,
) -> GnssSession:
    """One observation file as a session, cross-checking its name.

    *scan* collects the warnings. Passing none is legitimate for a caller that
    wants a single session and will not act on them; passing one is how
    :func:`scan_folder` surfaces them.
    """
    hints = name_hints(path)
    station = header.marker_name or (hints.station if hints else "") or path.stem

    if scan is not None and hints is not None:
        _cross_check(path, header, hints, scan)

    nav_files, fell_back = _navigation_for(header, hints, navigation or [])
    if scan is not None and fell_back and nav_files:
        scan.warnings.append(
            Finding(
                "navigation_paired_by_fallback",
                Severity.WARNING,
                "navigation files paired by fallback: no file name stated a matching date, "
                f"so all {len(nav_files)} navigation files in the scan are offered",
                context={"file": str(path), "count": len(nav_files)},
            )
        )

    # TIME OF LAST OBS is optional and RTKLIB's own sample files omit it. Two
    # sessions with no end cannot be tested for simultaneity at all, so the very
    # pair that forms a baseline would come back as two unrelated files -- which
    # is what this scan is for. The tail read turns that unknown into a
    # measurement; where it cannot (a compressed file), the end stays None and
    # the session is grouped alone rather than grouped wrongly.
    end = header.last_observation
    if end is None:
        end = read_last_epoch(path, header)
        if scan is not None and end is None and header.first_observation is not None:
            scan.warnings.append(
                Finding(
                    "session_span_unknown",
                    Severity.WARNING,
                    "neither TIME OF LAST OBS nor a readable final epoch, so the session's "
                    "span is unknown and it cannot be matched with simultaneous sessions",
                    context={"file": str(path)},
                )
            )

    height = header.antenna_delta.height if header.antenna_delta else None
    return GnssSession(
        id=path.name,
        station_id=station,
        obs_file=str(path),
        nav_files=tuple(str(item) for item in nav_files),
        start=header.first_observation,
        end=end,
        interval=header.interval,
        receiver=header.receiver.type,
        antenna=header.antenna_type,
        antenna_height=Quantity.exact(height.value, METRE) if height is not None else None,
        # The file states a distance and not how it was measured, so the session
        # records that it is unstated rather than leaving the field empty --
        # "unstated" is a value a later step can act on, "" is an absence that
        # looks like nobody filled the form in. See io/rinex.py.
        antenna_height_method=(
            header.antenna_delta.method.value if header.antenna_delta else HeightMethod.UNSTATED.value
        ),
        meta=_meta(path, header, hints),
    )


def overlapping_groups(sessions: tuple[GnssSession, ...]) -> list[tuple[GnssSession, ...]]:
    """Sessions grouped by simultaneity: which of them could form a baseline.

    Transitive by construction -- A overlapping B and B overlapping C puts all
    three in one group even where A and C do not themselves overlap, because
    that is a connected observing period and the engine is what decides which
    pairs within it are worth processing. Sessions whose span the header did not
    state cannot be grouped at all (:meth:`GnssSession.overlaps` is false for
    them) and come back alone.
    """
    remaining = list(sessions)
    groups: list[tuple[GnssSession, ...]] = []
    while remaining:
        group = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            for candidate in list(remaining):
                if any(candidate.overlaps(member) for member in group):
                    group.append(candidate)
                    remaining.remove(candidate)
                    changed = True
        groups.append(tuple(group))
    return groups


def join_sessions(sessions: list[GnssSession], directory: Path) -> GnssSession:
    """One station's sessions, logged in several files, as one session in one file (P13-26).

    A receiver that logs a file an hour leaves a rover session overlapped by
    several of the base's, and ``rnx2rtkp`` reads one base file. They are
    joined as RINEX allows: the first file's header, its ``TIME OF LAST OBS``
    the last file's, then every file's observations in the order they were
    made. An epoch two files both hold is read twice, and RTKLIB keeps one.

    Only files one receiver recorded one way are joined: the same RINEX
    version and observation types, receiver, antenna, height and eccentricity.
    A station set up twice is two sessions, and joining them would put one mark
    in two places with no error to show for it.

    Raises:
        DataError: the sessions are of different stations
            (``gnss_join_different_stations``); one states no first observation,
            so cannot be put in order (``gnss_join_span_unknown``); one is
            compressed in a form whose observations GeoComp cannot read
            (``rinex_compression_unsupported``); or two were not recorded the
            same way (``gnss_join_setups_differ``).
    """
    stations = sorted({session.station_id for session in sessions})
    if len(stations) != 1:
        raise DataError(
            "gnss_join_different_stations",
            stations=", ".join(stations),
            expected="the sessions of one station",
        )
    for session in sessions:
        if session.start is None:
            raise DataError(
                "gnss_join_span_unknown",
                file=Path(session.obs_file).name,
                expected="a TIME OF FIRST OBS, which puts the file in order",
            )
        compression = compression_of(session.obs_file)
        if compression not in {Compression.NONE, Compression.GZIP}:
            raise DataError(
                "rinex_compression_unsupported",
                file=str(session.obs_file),
                compression=compression.value,
                expected="an uncompressed or gzip-compressed file; decompress it first",
            )
    ordered = sorted(sessions, key=lambda session: (session.start, session.obs_file))
    first = ordered[0]
    for other in ordered[1:]:
        for name, mine, theirs in _setup_of(first, other):
            if mine != theirs:
                raise DataError(
                    "gnss_join_setups_differ",
                    file=Path(first.obs_file).name,
                    other=Path(other.obs_file).name,
                    field=name,
                    first=str(mine),
                    second=str(theirs),
                    expected="files one receiver recorded one way",
                )

    heads, bodies = zip(*(_header_and_body(Path(s.obs_file)) for s in ordered), strict=True)
    last_record = next(
        (line for line in heads[-1] if line[60:].strip() == "TIME OF LAST OBS"), None
    )
    header = [line for line in heads[0] if line[60:].strip() not in {"TIME OF LAST OBS", "END OF HEADER"}]
    if last_record is not None:
        header.append(last_record)
    header.append(f"{f'GEOCOMP: JOINED FROM {len(ordered)} FILES':<60}COMMENT")
    header.append(f"{'':<60}END OF HEADER")

    suffix = Path(first.obs_file).name.removesuffix(".gz").removesuffix(".GZ")
    name = f"{first.station_id}-{first.start:%Y%m%d%H%M}-joined{Path(suffix).suffix}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    with path.open("w", encoding="ascii", errors="replace", newline="\n") as handle:
        for line in header:
            handle.write(line + "\n")
        for body in bodies:
            for line in body:
                handle.write(line + "\n")

    meta = {key: value for key, value in first.meta.items() if key not in {"compression", "needs_crx2rnx"}}
    meta["joined_from"] = [Path(session.obs_file).name for session in ordered]
    navigation = []
    for session in ordered:
        navigation += [item for item in session.nav_files if item not in navigation]
    return replace(
        first,
        id=name,
        obs_file=str(path),
        nav_files=tuple(navigation),
        end=ordered[-1].end if ordered[-1].end is not None else first.end,
        meta=meta,
    )


def _setup_of(first: GnssSession, other: GnssSession) -> list[tuple[str, Any, Any]]:
    """What must be the same in two files for them to be one session's."""

    def height(session: GnssSession) -> float | None:
        return session.antenna_height.value if session.antenna_height is not None else None

    return [
        ("RINEX VERSION / TYPE", first.meta.get("rinex_version"), other.meta.get("rinex_version")),
        ("REC # / TYPE / VERS", first.receiver, other.receiver),
        ("ANT # / TYPE", first.antenna, other.antenna),
        ("ANTENNA: DELTA H/E/N", height(first), height(other)),
        (
            "ANTENNA: DELTA H/E/N",
            first.meta.get("antenna_eccentricity"),
            other.meta.get("antenna_eccentricity"),
        ),
        (
            "# / TYPES OF OBSERV",
            first.meta.get("observation_types"),
            other.meta.get("observation_types"),
        ),
    ]


def _header_and_body(path: Path) -> tuple[list[str], list[str]]:
    """The file's header records, up to and including ``END OF HEADER``, and the rest."""
    opener = gzip.open if compression_of(path) is Compression.GZIP else open
    with opener(path, "rt", encoding="ascii", errors="replace") as handle:  # type: ignore[operator]
        lines = [line.rstrip("\n").rstrip("\r") for line in handle]
    for index, line in enumerate(lines):
        if line[60:].strip() == "END OF HEADER":
            return lines[: index + 1], lines[index + 1 :]
    raise DataError("rinex_header_unterminated", file=str(path), expected="an END OF HEADER record")


# -- internals ------------------------------------------------------------


def _is_candidate(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith((".rnx", ".crx")):
        return True
    for wrapper in (".gz", ".z", ".zip"):
        if name.endswith(wrapper):
            name = name[: -len(wrapper)]
            break
    # RINEX 2 short names end in a two-digit year plus one type letter.
    stem = name.rsplit(".", 1)
    return (
        len(stem) == 2
        and len(stem[1]) == 3
        and stem[1][:2].isdigit()
        and f".{stem[1][2]}" in _CANDIDATE_SUFFIXES
    ) or name.endswith((".rnx", ".crx"))


def _reason(error: GeoCompError) -> str:
    expected = error.context.get("expected", "")
    return f"{error.code}: {expected}" if expected else error.code


def _cross_check(path: Path, header: RinexHeader, hints: Any, scan: SessionScan) -> None:
    """Compare what the name claims against what the header states."""
    if header.marker_name and hints.station:
        # Long names carry a nine-character identifier whose first four are the
        # station; a short name carries exactly four. Comparing the shorter
        # against the start of the longer is the only comparison that means
        # anything across both conventions.
        marker, claimed = header.marker_name.upper(), hints.station.upper()
        width = min(len(marker), len(claimed), 4)
        if marker[:width] != claimed[:width]:
            scan.warnings.append(
                Finding(
                    "file_name_claims_another_station",
                    Severity.WARNING,
                    f"the file name claims station {hints.station!r} and the header states "
                    f"marker {header.marker_name!r}; the header is used",
                    context={
                        "file": str(path),
                        "claimed": hints.station,
                        "marker": header.marker_name,
                    },
                )
            )

    if hints.has_date and header.first_observation is not None:
        named = datetime(hints.year, 1, 1, tzinfo=UTC) + timedelta(days=hints.day_of_year - 1)
        if named.date() != header.first_observation.date():
            scan.warnings.append(
                Finding(
                    "file_name_claims_another_day",
                    Severity.WARNING,
                    f"the file name claims {named.date().isoformat()} and the first observation "
                    f"is {header.first_observation.date().isoformat()}; the header is used",
                    context={
                        "file": str(path),
                        "claimed": named.date().isoformat(),
                        "observed": header.first_observation.date().isoformat(),
                    },
                )
            )


def _navigation_for(
    header: RinexHeader,
    hints: Any,
    navigation: list[tuple[Path, RinexHeader]],
) -> tuple[list[Path], bool]:
    """Navigation files for one observation session, and whether it fell back."""
    if not navigation:
        return [], False

    day = header.first_observation.date() if header.first_observation else None
    matched: list[Path] = []
    for path, _ in navigation:
        nav_hints = name_hints(path)
        if nav_hints is None or not nav_hints.has_date or day is None:
            continue
        named = (datetime(nav_hints.year, 1, 1, tzinfo=UTC)
                 + timedelta(days=nav_hints.day_of_year - 1)).date()
        if named == day:
            matched.append(path)
    if matched:
        return matched, False
    return [path for path, _ in navigation], True


def _meta(path: Path, header: RinexHeader, hints: Any) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "rinex_version": header.version,
        "observation_types": {
            system: list(codes) for system, codes in header.observation_types.items()
        },
    }
    if header.compression is not Compression.NONE:
        meta["compression"] = header.compression.value
    if header.approximate_position is not None:
        meta["approximate_position"] = list(header.approximate_position)
    if header.marker_number:
        meta["marker_number"] = header.marker_number
    if header.time_system:
        meta["time_system"] = header.time_system
    if header.antenna_delta is not None and header.antenna_delta.is_eccentric:
        meta["antenna_eccentricity"] = [
            header.antenna_delta.east.value,
            header.antenna_delta.north.value,
        ]
    if hints is not None and hints.station:
        meta["name_claims_station"] = hints.station
    if compression_of(path) in {Compression.HATANAKA, Compression.HATANAKA_GZIP}:
        # The header is readable but the observations are not, and rnx2rtkp
        # wants them: saying so here is cheaper than a failed run later.
        meta["needs_crx2rnx"] = True
    return meta
