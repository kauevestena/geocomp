# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading RINEX headers (FR-164).

``specs/08-engine-rtklib.md`` section 4 states the rule this module exists to
enforce: **read the header, do not trust the file name.** A session attributed
to the wrong station by its file name produces a baseline that is confidently
wrong, and nothing downstream can detect it. So every fact GeoComp uses about a
session -- which mark, which receiver, which antenna, how high, over what span,
at what interval -- comes from inside the file, and the name is a cross-check
that raises a warning when it disagrees.

**Only the header is read.** A day of 1 s observations is hundreds of megabytes
and session discovery scans whole folders of them; stopping at ``END OF HEADER``
keeps a scan proportional to the number of files rather than to their size.
``TIME OF LAST OBS`` is optional in the format, so a span that the header does
not state is reported as unknown rather than guessed -- ``rnx2rtkp`` reads the
body itself and knows better than a heuristic here would.

**The header is fixed-format, and that is the whole difficulty.** The label
lives in columns 61-80 and the value in 1-60, subdivided differently per label.
Reading it by splitting on whitespace works on most files and then silently
mis-reads a marker name containing a space, an empty antenna serial, or a
receiver type that abuts its version. Every field below is taken by column.

## RINEX 2 and RINEX 3

Both are read. The differences that matter to a header scan are few: RINEX 3
names observation types per constellation (``SYS / # / OBS TYPES``) where
RINEX 2 has one list for the file (``# / TYPES OF OBSERV``), adds
``MARKER TYPE``, and writes a four-character version like ``3.04`` where 2.x
writes ``2.10``. The version is read from the file rather than from the
extension, because the extension is a convention and the header is a statement.

## What RINEX cannot tell you

``ANTENNA: DELTA H/E/N`` is **by definition the vertical offset from the mark to
the antenna reference point**. If the field crew measured a slant height to the
antenna edge, someone reduced it to vertical before it reached this file, and
the file does not record that they did, or to which reference point. So the
*method* ``specs/08`` section 4 requires be recorded cannot be recovered here:
:attr:`AntennaDelta.method` is :attr:`HeightMethod.UNSTATED` for every file, and
it is the session -- the user, or an import mapping -- that must say otherwise.
Defaulting it to "vertical" would be this module inventing the fact that
``specs/08`` calls one of the most common sources of a systematic height error.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from geocomp.core.errors import DataError
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

__all__ = [
    "AntennaDelta",
    "Compression",
    "HeightMethod",
    "ReceiverInfo",
    "RinexHeader",
    "compression_of",
    "read_rinex_header",
]

METRE = Unit.METRE

#: The label occupies columns 61-80 of every header record; the value, 1-60.
_LABEL = slice(60, 80)
_VALUE = slice(0, 60)

#: **The two versions list observation types at different strides**, and this is
#: the kind of detail a reader gets silently wrong. RINEX 2's
#: ``# / TYPES OF OBSERV`` is ``I6, 9(4X,A2)`` -- six characters per entry from
#: column 7. RINEX 3's ``SYS / # / OBS TYPES`` is ``A1, 2X, I3, 13(1X,A3)`` --
#: **four**. Reading a RINEX 3 list at stride 6 does not fail; it returns a
#: shorter list of codes chopped across their boundaries, which looks like a
#: file with fewer observables rather than like a parser defect.
_TYPE_WIDTH_2 = 6
_TYPE_WIDTH_3 = 4

_END_OF_HEADER = "END OF HEADER"

#: Generous. A real header is tens of records; this only has to stop a
#: truncated or corrupt file from pulling a day of observations into memory.
_MAX_HEADER_RECORDS = 20000


class HeightMethod(Enum):
    """How an antenna height was measured.

    ``UNSTATED`` is not a failure and not a default -- it is what a RINEX file
    actually tells you, which is nothing. See the module docstring.
    """

    UNSTATED = "unstated"
    VERTICAL = "vertical"
    SLANT = "slant"


class Compression(Enum):
    """How a RINEX file is wrapped, if it is.

    Detected and reported rather than silently handled, because a scan that
    quietly skips what it cannot open reports a campaign as smaller than it is
    (FR-166). ``HATANAKA`` is the RINEX-specific observation compression, which
    needs ``CRX2RNX`` and is orthogonal to the byte-level wrappers.
    """

    NONE = "none"
    GZIP = "gzip"
    UNIX_COMPRESS = "unix_compress"
    ZIP = "zip"
    HATANAKA = "hatanaka"
    HATANAKA_GZIP = "hatanaka_gzip"


@dataclass(frozen=True)
class ReceiverInfo:
    number: str = ""
    type: str = ""
    version: str = ""


@dataclass(frozen=True)
class AntennaDelta:
    """``ANTENNA: DELTA H/E/N`` -- marker to antenna reference point."""

    height: Quantity
    east: Quantity
    north: Quantity
    method: HeightMethod = HeightMethod.UNSTATED

    @property
    def is_eccentric(self) -> bool:
        """Whether the antenna stood off the mark horizontally.

        Worth asking separately from the height: a non-zero east or north offset
        is rare enough that it is usually either deliberate or a mistake, and
        either way it must not pass unnoticed.
        """
        return bool(self.east.value) or bool(self.north.value)


@dataclass(frozen=True)
class RinexHeader:
    """What a RINEX header states, and nothing inferred."""

    path: Path
    version: float
    file_type: str
    satellite_system: str = ""
    marker_name: str = ""
    marker_number: str = ""
    marker_type: str = ""
    receiver: ReceiverInfo = field(default_factory=ReceiverInfo)
    antenna_number: str = ""
    antenna_type: str = ""
    antenna_delta: AntennaDelta | None = None
    approximate_position: tuple[float, float, float] | None = None
    interval: float | None = None
    first_observation: datetime | None = None
    last_observation: datetime | None = None
    time_system: str = ""
    observation_types: dict[str, tuple[str, ...]] = field(default_factory=dict)
    program: str = ""
    run_by: str = ""
    compression: Compression = Compression.NONE

    @property
    def is_observation(self) -> bool:
        return self.file_type == "O"

    @property
    def is_navigation(self) -> bool:
        """RINEX 2 spells the navigation types per constellation; 3 uses ``N``."""
        return self.file_type in {"N", "G", "L", "H", "J", "C", "E", "I"}

    @property
    def span(self) -> float | None:
        """Seconds from the first to the last observation, or ``None``.

        ``None`` where the header omits ``TIME OF LAST OBS``, which the format
        permits. A caller that needs the true span must read the body.
        """
        if self.first_observation is None or self.last_observation is None:
            return None
        return (self.last_observation - self.first_observation).total_seconds()


#: Long RINEX 3 names end ``.rnx``/``.crx``; short RINEX 2 names end in a
#: two-digit year plus a type letter, lower case for observation data.
_SHORT_NAME = re.compile(r"^(?P<station>[A-Za-z0-9]{4})(?P<day>\d{3})(?P<session>[0-9a-zA-Z])"
                         r"\.(?P<year>\d{2})(?P<type>[oOdDnNgGlLhHpPmMcC])$")
_LONG_NAME = re.compile(r"^(?P<station>[A-Z0-9]{9})_(?P<source>[RSU])_"
                        r"(?P<start>\d{11})_(?P<span>\d{2}[A-Z])_?(?P<rest>.*)"
                        r"\.(?P<ext>rnx|crx)$", re.IGNORECASE)


def compression_of(path: str | Path) -> Compression:
    """How *path* is wrapped, from its suffixes.

    By name rather than by content, deliberately: this runs over every file in a
    scanned folder, and the answer decides whether the file is worth opening at
    all. A file whose name lies about its compression fails at the read with a
    message naming the file, which is the same outcome as any other unreadable
    file (FR-166).
    """
    name = Path(path).name.lower()
    if name.endswith(".zip"):
        return Compression.ZIP
    hatanaka = _is_hatanaka_name(name.removesuffix(".gz").removesuffix(".z"))
    if name.endswith(".gz"):
        return Compression.HATANAKA_GZIP if hatanaka else Compression.GZIP
    if name.endswith(".z"):
        return Compression.UNIX_COMPRESS
    return Compression.HATANAKA if hatanaka else Compression.NONE


def _is_hatanaka_name(name: str) -> bool:
    """``.crx`` (long names) or a ``d`` where the type letter would be (short)."""
    if name.endswith(".crx"):
        return True
    match = _SHORT_NAME.match(Path(name).name)
    return bool(match) and match.group("type").lower() == "d"


def read_rinex_header(path: str | Path) -> RinexHeader:
    """Read the header of the RINEX file at *path*.

    Raises:
        DataError: if the first record is not ``RINEX VERSION / TYPE``, if the
            file is compressed in a form this reader does not unwrap, or if the
            header never ends. Each names the file and what was expected.
    """
    path = Path(path)
    compression = compression_of(path)
    records = _header_records(path, compression)

    first = next(records)

    # Validated before the rest is read, and that order is the point: a file
    # that is not RINEX has no END OF HEADER either, so checking termination
    # first reported every such file as a truncated RINEX header -- naming the
    # wrong problem, and sending the reader looking for a missing line in a file
    # that was never RINEX at all.
    version, file_type, satellite_system = _version_record(first, path)
    header = _Accumulator(version)
    for line in records:
        header.take(line)

    return RinexHeader(
        path=path,
        version=version,
        file_type=file_type,
        satellite_system=satellite_system,
        compression=compression,
        **header.fields(),
    )


def _header_records(path: Path, compression: Compression) -> Iterator[str]:
    """Yield records up to and including ``END OF HEADER``.

    A generator rather than a list so that the caller can validate the first
    record before the rest is read; see :func:`read_rinex_header`.

    Hatanaka-compressed files keep a readable header -- the compression applies
    to the observation records -- so the scan works on one, and only the body
    would need ``CRX2RNX``. ``.Z`` and ``.zip`` are refused here rather than
    half-read: Python's stdlib does not unwrap ``compress(1)``, and a zip may
    hold several files, which is a session-discovery question, not a header one.
    """
    if compression in {Compression.UNIX_COMPRESS, Compression.ZIP}:
        raise DataError(
            "rinex_compression_unsupported",
            file=str(path),
            compression=compression.value,
            expected="an uncompressed or gzip-compressed file; decompress it first",
        )

    opener = gzip.open if compression in {Compression.GZIP, Compression.HATANAKA_GZIP} else open
    seen = 0
    with opener(path, "rt", encoding="ascii", errors="replace") as handle:  # type: ignore[operator]
        for line in handle:
            record = line.rstrip("\n").rstrip("\r")
            seen += 1
            yield record
            if record[_LABEL].strip() == _END_OF_HEADER:
                return
            if seen > _MAX_HEADER_RECORDS:
                raise DataError(
                    "rinex_header_unterminated",
                    file=str(path),
                    expected=f"an END OF HEADER record within {_MAX_HEADER_RECORDS} lines",
                )
    if seen == 0:
        raise DataError("rinex_file_empty", file=str(path), expected="a RINEX header")
    raise DataError(
        "rinex_header_unterminated",
        file=str(path),
        expected="an END OF HEADER record",
        received="end of file",
    )


def _version_record(line: str, path: Path) -> tuple[float, str, str]:
    """``RINEX VERSION / TYPE`` -- the one record whose absence is fatal."""
    if line[_LABEL].strip() != "RINEX VERSION / TYPE":
        raise DataError(
            "rinex_header_missing",
            file=str(path),
            expected="RINEX VERSION / TYPE as the first record",
            received=line[_LABEL].strip() or line[:20].strip(),
        )
    try:
        version = float(line[0:9].strip())
    except ValueError as error:
        raise DataError(
            "rinex_version_malformed",
            file=str(path),
            received=line[0:9].strip(),
            expected="a version number such as 2.11 or 3.04",
        ) from error
    # The type and the system are single letters at fixed positions; RINEX 2
    # spells them out afterwards ("OBSERVATION DATA", "G (GPS)") and RINEX 3
    # does too, so only the letter is taken.
    return version, line[20:21].strip().upper(), line[40:41].strip().upper()


class _Accumulator:
    """Collects header records, dispatching on the label in columns 61-80."""

    def __init__(self, version: float) -> None:
        self.version = version
        self._fields: dict[str, object] = {}
        self._observation_types: dict[str, list[str]] = {}
        #: RINEX 2 continues a long observation-type list on unlabelled records,
        #: so the reader has to remember it is in one.
        self._pending_types: int = 0

    def take(self, line: str) -> None:
        label = line[_LABEL].strip()
        value = line[_VALUE]
        handler = _HANDLERS.get(label)
        if handler is not None:
            self._pending_types = 0
            handler(self, value)
        elif self._pending_types and not label:
            self._continue_types_2(value)

    # -- individual records -------------------------------------------------

    def _marker_name(self, value: str) -> None:
        # Columns 1-60 entire: a marker name may contain spaces, so this is one
        # of the fields that splitting on whitespace gets wrong.
        self._fields["marker_name"] = value.strip()

    def _marker_number(self, value: str) -> None:
        self._fields["marker_number"] = value[0:20].strip()

    def _marker_type(self, value: str) -> None:
        self._fields["marker_type"] = value[0:20].strip()

    def _program(self, value: str) -> None:
        self._fields["program"] = value[0:20].strip()
        self._fields["run_by"] = value[20:40].strip()

    def _receiver(self, value: str) -> None:
        self._fields["receiver"] = ReceiverInfo(
            number=value[0:20].strip(), type=value[20:40].strip(), version=value[40:60].strip()
        )

    def _antenna(self, value: str) -> None:
        self._fields["antenna_number"] = value[0:20].strip()
        self._fields["antenna_type"] = value[20:40].strip()

    def _approx_position(self, value: str) -> None:
        numbers = _floats(value, 3, width=14)
        if numbers is not None:
            self._fields["approximate_position"] = numbers

    def _antenna_delta(self, value: str) -> None:
        numbers = _floats(value, 3, width=14)
        if numbers is None:
            return
        height, east, north = numbers
        self._fields["antenna_delta"] = AntennaDelta(
            height=Quantity.exact(height, METRE),
            east=Quantity.exact(east, METRE),
            north=Quantity.exact(north, METRE),
            method=HeightMethod.UNSTATED,
        )

    def _interval(self, value: str) -> None:
        try:
            self._fields["interval"] = float(value[0:10].strip())
        except ValueError:
            return

    def _first_obs(self, value: str) -> None:
        moment, system = _epoch(value)
        if moment is not None:
            self._fields["first_observation"] = moment
        if system:
            self._fields["time_system"] = system

    def _last_obs(self, value: str) -> None:
        moment, system = _epoch(value)
        if moment is not None:
            self._fields["last_observation"] = moment
        if system and "time_system" not in self._fields:
            self._fields["time_system"] = system

    def _types_2(self, value: str) -> None:
        """RINEX 2 ``# / TYPES OF OBSERV``: one list for the whole file.

        Stored under ``""`` -- the empty constellation key -- so that a caller
        can treat both versions uniformly without pretending RINEX 2 said
        something per-system that it did not.

        A blank count field means this is a continuation of the previous record.
        RINEX 2.11 repeats the label on continuation lines and earlier versions
        leave it blank, so both forms arrive here or at
        :meth:`_continue_types_2`, and both must work.
        """
        count = _int_or_none(value[0:6])
        if count is None:
            self._append_types(value[6:60], key="", width=_TYPE_WIDTH_2)
            return
        self._observation_types.setdefault("", [])
        self._pending_types = count
        self._append_types(value[6:60], key="", width=_TYPE_WIDTH_2)

    def _continue_types_2(self, value: str) -> None:
        self._append_types(value[6:60], key="", width=_TYPE_WIDTH_2)

    def _types_3(self, value: str) -> None:
        """RINEX 3 ``SYS / # / OBS TYPES``: one record per constellation."""
        system = value[0:1].strip().upper()
        if system:
            self._current_system = system
            count = _int_or_none(value[3:6])
            self._observation_types.setdefault(system, [])
            self._pending_types = count or 0
        else:
            system = getattr(self, "_current_system", "")
            if not system:
                return
        self._append_types(value[6:60], key=system, width=_TYPE_WIDTH_3)

    def _append_types(self, text: str, *, key: str, width: int) -> None:
        collected = self._observation_types.setdefault(key, [])
        for start in range(0, len(text) - 1, width):
            code = text[start : start + width].strip()
            if code:
                collected.append(code)

    # -- result -------------------------------------------------------------

    def fields(self) -> dict[str, object]:
        result = dict(self._fields)
        result["observation_types"] = {
            system: tuple(codes) for system, codes in self._observation_types.items()
        }
        return result


def _floats(value: str, count: int, *, width: int) -> tuple[float, ...] | None:
    """*count* fixed-width floats, or ``None`` if any is blank or malformed.

    All-or-nothing on purpose: two of three coordinates is not a position, and a
    partially read triple is worse than an absent one.
    """
    numbers: list[float] = []
    for index in range(count):
        text = value[index * width : (index + 1) * width].strip()
        if not text:
            return None
        try:
            numbers.append(float(text))
        except ValueError:
            return None
    return tuple(numbers)


def _int_or_none(text: str) -> int | None:
    try:
        return int(text.strip())
    except ValueError:
        return None


def _epoch(value: str) -> tuple[datetime | None, str]:
    """``TIME OF FIRST/LAST OBS``: six numbers then a time-system code.

    The seconds field carries fractions, and the record states its own time
    system (GPS, GLO, GAL, ...). RINEX 2 leaves the system blank on a GPS-only
    file, where the format defines the default as GPS; that default is applied
    by the caller that needs it, not invented here.
    """
    numbers = [_int_or_none(value[index * 6 : (index + 1) * 6]) for index in range(5)]
    if any(part is None for part in numbers):
        return None, value[43:51].strip().upper()
    try:
        seconds = float(value[30:43].strip())
    except ValueError:
        return None, value[43:51].strip().upper()

    year, month, day, hour, minute = (int(part) for part in numbers)  # type: ignore[arg-type]
    whole = int(seconds)
    microseconds = round((seconds - whole) * 1_000_000)
    try:
        moment = datetime(year, month, day, hour, minute, whole, microseconds, tzinfo=UTC)
    except ValueError:
        return None, value[43:51].strip().upper()
    return moment, value[43:51].strip().upper()


_HANDLERS = {
    "MARKER NAME": _Accumulator._marker_name,
    "MARKER NUMBER": _Accumulator._marker_number,
    "MARKER TYPE": _Accumulator._marker_type,
    "PGM / RUN BY / DATE": _Accumulator._program,
    "REC # / TYPE / VERS": _Accumulator._receiver,
    "ANT # / TYPE": _Accumulator._antenna,
    "APPROX POSITION XYZ": _Accumulator._approx_position,
    "ANTENNA: DELTA H/E/N": _Accumulator._antenna_delta,
    "INTERVAL": _Accumulator._interval,
    "TIME OF FIRST OBS": _Accumulator._first_obs,
    "TIME OF LAST OBS": _Accumulator._last_obs,
    "# / TYPES OF OBSERV": _Accumulator._types_2,
    "SYS / # / OBS TYPES": _Accumulator._types_3,
}
