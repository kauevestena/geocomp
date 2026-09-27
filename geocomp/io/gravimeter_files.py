# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading relative gravimeter files (FR-160, FR-701).

``specs/12-module-gravimetry.md`` section 3. Three formats, each turned into
:class:`~geocomp.core.techniques.gravimetry.readings.GravityReading` records
with every value in SI:

* **Scintrex CG-5** text exports -- a ``/``-prefixed header, then one line per
  reading. The header states the survey's location, the offset of its clock
  from GMT, and whether the instrument removed the tide itself.
* **ZLS Burris** exports, in the space-separated layout USGS's GSadjust reads:
  station, operator, meter, date, time, reading, dial, feedback, tide, four
  unused columns, elevation, latitude, longitude. A zero tide column means the
  meter applied none, and leaves the question to the gravimeter profile.
* **A plain CSV** with named columns, for every other instrument.

**What the instrument already did is kept, not repeated.** A CG-5 with *Tide
Correction: YES* and a Burris with a non-zero tide column have removed the tide
from their readings; the records say so (``tide_applied``) and the reduction
honours it. Asking for GeoComp's own tide instead is ``replace_tide=True``,
which adds the instrument's correction back first -- never both.

**The clock.** A CG-5 records local time and a ``GMT DIFF.``; which way the
difference runs is not something this module assumes. When GeoComp computes the
tide it needs UTC, so the reader lets the file settle it: the instrument's own
tide column is compared with Longman's under both readings of the offset, and
the one that agrees to a few microgal is used. A file that cannot settle it --
no tide column, or neither reading agrees -- is refused unless the offset is
given explicitly. When the instrument's tide is kept, only elapsed time matters
and the offset cancels.

**Precision.** A CG-5 reading's ``SD`` is the scatter of the samples it
averaged over ``DUR`` seconds, so its standard error is ``SD / sqrt(DUR)``
(Hector and Hinderer, 2016). That figure knows nothing of tilt, temperature or
transport, so a floor is added in quadrature, passed in as ``additive_sigma``;
any precision that includes one is labelled approximate. A Burris records no
precision at all and takes the floor alone, or the gravimeter profile's nominal
precision when there is no floor.
"""

from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.techniques.gravimetry.readings import GravityReading
from geocomp.core.techniques.gravimetry.tides import tidal_correction
from geocomp.core.uncertainty import Quantity, Strategy
from geocomp.core.units import METRES_PER_SECOND_SQUARED_PER_MGAL as MGAL
from geocomp.core.units import Unit

__all__ = [
    "CSV_COLUMNS",
    "GravimeterFile",
    "GravimeterFormat",
    "detect_format",
    "read_burris",
    "read_cg5",
    "read_gravimeter_file",
    "read_gravity_csv",
]

#: Agreement between an instrument's tide column and Longman's that settles the
#: clock's offset: the CG-5 firmware and Longman agree to 1.5 microgal at worst
#: (``specs/12`` section 4.2), and a wrong offset of even an hour misses by tens.
OFFSET_AGREEMENT = 3.0e-8

#: The columns of the plain CSV. ``station``, ``time`` and ``reading_mgal`` are
#: required; ``time`` is ISO 8601 and must carry its offset (``Z`` or
#: ``+hh:mm``), because a naive time is a guess at the tide.
CSV_COLUMNS = (
    "station",
    "time",
    "reading_mgal",
    "sd_mgal",
    "instrument",
    "session",
    "latitude_deg",
    "longitude_deg",
    "height_m",
    "sensor_height_m",
    "tide_applied",
)


class GravimeterFormat(Enum):
    CG5 = "cg5"
    BURRIS = "burris"
    CSV = "csv"


@dataclass(frozen=True)
class GravimeterFile:
    """What a file held, and what reading it assumed.

    Attributes:
        readings: In file order.
        instruments: Every instrument the readings name.
        notes: Facts about the file a user should see -- what the instrument
            had already applied, which clock offset was used and how it was
            decided. Plain sentences, for the algorithm to report.
    """

    format: GravimeterFormat
    readings: tuple[GravityReading, ...]
    instruments: tuple[str, ...]
    notes: tuple[str, ...]


def detect_format(text: str) -> GravimeterFormat:
    """Which of the three formats *text* is, from its content, not its name."""
    if re.search(r"^/\s*CG-5", text, re.M) or re.search(r"^/\s*Instrument S/N", text, re.M):
        return GravimeterFormat.CG5
    first = next((line for line in text.splitlines() if line.strip()), "")
    if "," in first and "station" in first.lower():
        return GravimeterFormat.CSV
    if len(first.split()) >= 16 and re.match(r"\d{4}/\d{2}/\d{2}$", first.split()[3]):
        return GravimeterFormat.BURRIS
    raise DataError(
        "gravimeter_format_unknown",
        expected=(
            "a Scintrex CG-5 export (a header of '/' lines), a ZLS Burris export "
            "(16 space-separated columns, date as YYYY/MM/DD), or a CSV whose header "
            f"names {', '.join(CSV_COLUMNS[:3])}"
        ),
    )


def read_gravimeter_file(
    path: str | Path,
    *,
    source: str | None = None,
    additive_sigma: float = 0.0,
    replace_tide: bool = False,
    utc_offset_hours: float | None = None,
) -> GravimeterFile:
    """Read any of the three formats, detected from the content."""
    text = Path(path).read_text(encoding="latin-1")
    name = source or Path(path).name
    kind = detect_format(text)
    if kind is GravimeterFormat.CG5:
        return read_cg5(
            text,
            source=name,
            additive_sigma=additive_sigma,
            replace_tide=replace_tide,
            utc_offset_hours=utc_offset_hours,
        )
    if kind is GravimeterFormat.BURRIS:
        return read_burris(
            text,
            source=name,
            additive_sigma=additive_sigma,
            replace_tide=replace_tide,
            utc_offset_hours=utc_offset_hours,
        )
    return read_gravity_csv(text, source=name, additive_sigma=additive_sigma)


def _reading(value: float, sigma: float, floor: float) -> Quantity:
    """A reading with the precision its file gave, labelled for what it rests on.

    Zero means the file gave none, and the profile's nominal precision is left
    to supply it (or to refuse). A floor is a nominal figure, so any precision
    that includes one is approximate and says so (FR-203); what is left is the
    instrument's own statistic.
    """
    if sigma <= 0.0:
        return Quantity.exact(value, Unit.ACCELERATION)
    if floor > 0.0:
        return Quantity.approximate(value, sigma, Unit.ACCELERATION, Strategy.NOMINAL_PRECISION)
    return Quantity.from_std_dev(value, sigma, Unit.ACCELERATION)


# -- Scintrex CG-5 ---------------------------------------------------------


@dataclass
class _Cg5Row:
    line: int
    station: str
    height: float
    gravity_mgal: float
    sd_mgal: float
    tide_mgal: float
    duration_s: int
    local: datetime
    instrument: str
    latitude: float
    longitude: float
    gmt_diff: float
    tide_applied: bool


def read_cg5(
    text: str,
    *,
    source: str = "cg5",
    additive_sigma: float = 0.0,
    replace_tide: bool = False,
    utc_offset_hours: float | None = None,
) -> GravimeterFile:
    """A Scintrex CG-5 text export.

    Args:
        additive_sigma: m/s^2, added in quadrature to each reading's
            ``SD / sqrt(DUR)``.
        replace_tide: Add the instrument's tide back and let GeoComp remove its
            own. Needs UTC, so it settles the clock offset first.
        utc_offset_hours: Local time minus UTC, when the header's ``GMT DIFF.``
            is to be overridden rather than interpreted.
    """
    rows = _cg5_rows(text, source)
    if not rows:
        raise DataError(
            "gravimeter_file_empty", source=source, expected="at least one CG-5 reading line"
        )

    notes: list[str] = []
    applied = {row.tide_applied for row in rows}
    if applied == {True}:
        fate = "its correction was added back for GeoComp's to replace it." if replace_tide else "it is kept."
        notes.append("The instrument removed the tide itself (Tide Correction: YES); " + fate)
    offset = _cg5_offset(rows, replace_tide, utc_offset_hours, notes)

    readings = []
    for row in rows:
        value = row.gravity_mgal * MGAL
        tide_applied = row.tide_applied
        if replace_tide and tide_applied:
            value -= row.tide_mgal * MGAL
            tide_applied = False
        standard_error = row.sd_mgal * MGAL / math.sqrt(max(row.duration_s, 1))
        instant = (row.local - offset).replace(tzinfo=UTC)
        readings.append(
            GravityReading(
                id=f"{source}:{row.line}",
                station=row.station,
                instant=instant,
                value=_reading(value, math.hypot(standard_error, additive_sigma), additive_sigma),
                instrument=row.instrument,
                session=f"{row.instrument} {row.local.date().isoformat()}",
                latitude=math.radians(row.latitude),
                longitude=math.radians(row.longitude),
                height=row.height,
                tide_applied=tide_applied,
            )
        )
    notes.append(
        f"Each reading's precision is SD / sqrt(DUR), with a floor of {additive_sigma / MGAL * 1000.0:g} "
        "microgal added in quadrature."
        if additive_sigma > 0.0
        else "Each reading's precision is SD / sqrt(DUR) alone. It knows nothing of tilt, "
        "temperature or transport, so a floor is usually worth adding."
    )
    return GravimeterFile(
        GravimeterFormat.CG5,
        tuple(readings),
        tuple(sorted({r.instrument for r in readings})),
        tuple(notes),
    )


def _cg5_rows(text: str, source: str) -> list[_Cg5Row]:
    header: dict[str, str] = {}
    rows: list[_Cg5Row] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("/"):
            found = re.match(r"^/\s*([^:]+?):\s*(.*)$", line)
            if found:
                header[found.group(1).strip().upper()] = found.group(2).strip()
            continue
        fields = line.split()
        if len(fields) != 15 or not fields[0][0].isdigit():
            continue
        try:
            station = float(fields[1])
            local = datetime.strptime(f"{fields[14]} {fields[11]}", "%Y/%m/%d %H:%M:%S")
            rows.append(
                _Cg5Row(
                    line=number,
                    station=str(int(station)) if station.is_integer() else fields[1],
                    height=float(fields[2]),
                    gravity_mgal=float(fields[3]),
                    sd_mgal=float(fields[4]),
                    tide_mgal=float(fields[8]),
                    duration_s=int(fields[9]),
                    local=local,
                    instrument=f"CG-5 {header.get('INSTRUMENT S/N', 'unknown')}".strip(),
                    latitude=_hemisphere(header.get("LAT", ""), source, "LAT"),
                    longitude=_hemisphere(header.get("LONG", ""), source, "LONG"),
                    gmt_diff=float(header.get("GMT DIFF.", "0") or 0.0),
                    tide_applied=header.get("TIDE CORRECTION", "NO").upper().startswith("Y"),
                )
            )
        except ValueError as error:
            raise DataError(
                "gravimeter_line_unreadable",
                source=source,
                line=number,
                received=raw,
                expected="a CG-5 reading line of fifteen columns",
            ) from error
    return rows


def _hemisphere(value: str, source: str, label: str) -> float:
    parts = value.split()
    if len(parts) != 2 or parts[1] not in ("N", "S", "E", "W"):
        raise DataError(
            "gravimeter_header_location",
            source=source,
            field=label,
            received=value,
            expected="a CG-5 header value such as '9.7000000 N'; the tide needs the survey's location",
        )
    return float(parts[0]) * (-1.0 if parts[1] in ("S", "W") else 1.0)


def _cg5_offset(
    rows: list[_Cg5Row], replace_tide: bool, override: float | None, notes: list[str]
) -> timedelta:
    """Local time minus UTC: given, zero, or settled by the file's own tide column."""
    if override is not None:
        notes.append(f"Times were taken as UTC{override:+g} h, as given.")
        return timedelta(hours=override)
    stated = {row.gmt_diff for row in rows}
    # GeoComp computes a tide -- and so needs UTC -- for every reading whose
    # instrument did not, and for every reading when asked to replace it.
    needs_utc = replace_tide or not all(row.tide_applied for row in rows)
    if stated == {0.0}:
        if needs_utc and all(row.tide_applied for row in rows):
            notes.append(
                "The header's GMT difference is zero, so the times were taken as UTC; the "
                "instrument's own tide agrees with Longman's to "
                f"{_tide_misfit(rows, timedelta(0)) / 1e-8:.1f} microgal under that reading."
            )
        elif needs_utc:
            notes.append(
                "The header's GMT difference is zero, so the times were taken as UTC. If the "
                "instrument's clock kept local time, give the offset explicitly: the tide "
                "depends on it."
            )
        return timedelta(0)
    if not needs_utc:
        notes.append(
            "The header states a GMT difference; with the instrument's tide kept only "
            "elapsed time matters, so it was not needed."
        )
        return timedelta(hours=next(iter(stated)))
    if len(stated) > 1 or not all(row.tide_applied for row in rows):
        raise ValidationError(
            "gravimeter_clock_unsettled",
            received=sorted(stated),
            expected=(
                "an explicit UTC offset. GeoComp's tide needs UTC, the header's GMT "
                "difference can be read two ways, and this file has no single tide column "
                "to decide between them"
            ),
        )
    diff = next(iter(stated))
    misfits = {sign: _tide_misfit(rows, timedelta(hours=sign * diff)) for sign in (1.0, -1.0)}
    agreeing = [sign for sign, worst in misfits.items() if worst <= OFFSET_AGREEMENT]
    if len(agreeing) != 1:
        raise ValidationError(
            "gravimeter_clock_unsettled",
            received={"local minus GMT": misfits[1.0], "GMT minus local": misfits[-1.0]},
            expected=(
                "one reading of the header's GMT difference under which the instrument's "
                "tide agrees with Longman's to a few microgal; give the UTC offset explicitly"
            ),
        )
    sign = agreeing[0]
    notes.append(
        f"The header's GMT difference of {diff:g} h was read as local "
        f"{'minus' if sign > 0 else 'plus'} UTC, the reading under which the instrument's own "
        f"tide agrees with Longman's to {misfits[sign] / 1e-8:.1f} microgal."
    )
    return timedelta(hours=sign * diff)


def _tide_misfit(rows: list[_Cg5Row], offset: timedelta) -> float:
    """The worst disagreement, m/s^2, between the instrument's tide and Longman's
    when the file's local times are *offset* ahead of UTC -- over a sample of
    twenty readings, which is plenty to tell an hour's error from none."""
    sample = rows[:: max(1, len(rows) // 20)]
    return max(
        abs(
            row.tide_mgal * MGAL
            - tidal_correction(
                (row.local - offset).replace(tzinfo=UTC),
                math.radians(row.latitude),
                math.radians(row.longitude),
                row.height,
            ).value
        )
        for row in sample
    )


# -- ZLS Burris ------------------------------------------------------------


def read_burris(
    text: str,
    *,
    source: str = "burris",
    additive_sigma: float = 0.0,
    replace_tide: bool = False,
    utc_offset_hours: float | None = None,
) -> GravimeterFile:
    """A ZLS Burris export, in the layout USGS's GSadjust reads.

    The file states no time zone. Its times are UTC unless *utc_offset_hours*
    says otherwise; that matters only if GeoComp computes the tide.
    """
    offset = timedelta(hours=utc_offset_hours or 0.0)
    notes = [
        "Burris exports state no precision: each reading takes the precision floor, or the "
        "profile's nominal precision when no floor is given.",
        "Burris exports state no time zone: times were taken as "
        + (f"UTC{utc_offset_hours:+g} h." if utc_offset_hours else "UTC."),
    ]
    readings = []
    for number, raw in enumerate(text.splitlines(), start=1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) < 16:
            raise DataError(
                "gravimeter_line_unreadable",
                source=source,
                line=number,
                received=raw,
                expected="a Burris line of sixteen columns",
            )
        try:
            local = datetime.strptime(f"{fields[3]} {fields[4]}", "%Y/%m/%d %H:%M:%S")
            value = float(fields[5]) * MGAL
            tide = float(fields[8]) * MGAL
            height, latitude, longitude = float(fields[13]), float(fields[14]), float(fields[15])
        except ValueError as error:
            raise DataError(
                "gravimeter_line_unreadable",
                source=source,
                line=number,
                received=raw,
                expected="numbers in the reading, tide, elevation, latitude and longitude columns",
            ) from error
        # A non-zero tide column is a correction already in the reading. A zero
        # one says only that the meter applied none -- its correction was off,
        # or the file is synthetic and tide-free -- so the gravimeter profile
        # decides, and without one GeoComp removes the tide.
        applied: bool | None = True if tide != 0.0 else None
        if replace_tide and applied:
            value -= tide
            applied = False
        readings.append(
            GravityReading(
                id=f"{source}:{number}",
                station=fields[0],
                instant=(local - offset).replace(tzinfo=UTC),
                value=_reading(value, additive_sigma, additive_sigma),
                instrument=fields[2],
                session=f"{fields[2]} {local.date().isoformat()}",
                latitude=math.radians(latitude),
                longitude=math.radians(longitude),
                height=height,
                tide_applied=applied,
            )
        )
    if not readings:
        raise DataError("gravimeter_file_empty", source=source, expected="at least one Burris line")
    return GravimeterFile(
        GravimeterFormat.BURRIS,
        tuple(readings),
        tuple(sorted({r.instrument for r in readings})),
        tuple(notes),
    )


# -- plain CSV ------------------------------------------------------------


def read_gravity_csv(text: str, *, source: str = "csv", additive_sigma: float = 0.0) -> GravimeterFile:
    """A CSV with the columns of :data:`CSV_COLUMNS`, readings in mGal."""
    table = csv.DictReader(io.StringIO(text))
    names = {name.strip().lower() for name in (table.fieldnames or ())}
    missing = [name for name in CSV_COLUMNS[:3] if name not in names]
    if missing:
        raise DataError(
            "gravimeter_csv_columns",
            source=source,
            received=sorted(names),
            expected=f"columns including {', '.join(CSV_COLUMNS[:3])}",
        )
    readings = []
    for number, record in enumerate(table, start=2):
        row = {key.strip().lower(): (value or "").strip() for key, value in record.items() if key}
        try:
            instant = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            value = float(row["reading_mgal"]) * MGAL
            sd = float(row["sd_mgal"]) * MGAL if row.get("sd_mgal") else 0.0
        except ValueError as error:
            raise DataError(
                "gravimeter_line_unreadable",
                source=source,
                line=number,
                received=record,
                expected="an ISO 8601 time with its offset and a reading in mGal",
            ) from error
        if instant.tzinfo is None:
            raise DataError(
                "gravimeter_csv_naive_time",
                source=source,
                line=number,
                received=row["time"],
                expected="a time with its UTC offset, such as 2013-09-15T05:57:01Z",
            )
        sigma = math.hypot(sd, additive_sigma)
        instrument = row.get("instrument") or "gravimeter"
        height = row.get("sensor_height_m")
        readings.append(
            GravityReading(
                id=f"{source}:{number}",
                station=row["station"],
                instant=instant.astimezone(UTC),
                value=_reading(value, sigma, additive_sigma),
                instrument=instrument,
                session=row.get("session") or f"{instrument} {instant.date().isoformat()}",
                latitude=math.radians(float(row["latitude_deg"])) if row.get("latitude_deg") else None,
                longitude=math.radians(float(row["longitude_deg"])) if row.get("longitude_deg") else None,
                height=float(row["height_m"]) if row.get("height_m") else None,
                sensor_height=Quantity.exact(float(height), Unit.METRE) if height else None,
                tide_applied=(row.get("tide_applied", "").lower() in ("1", "true", "yes"))
                if row.get("tide_applied")
                else None,
            )
        )
    if not readings:
        raise DataError("gravimeter_file_empty", source=source, expected="at least one data row")
    return GravimeterFile(
        GravimeterFormat.CSV,
        tuple(readings),
        tuple(sorted({r.instrument for r in readings})),
        (),
    )
