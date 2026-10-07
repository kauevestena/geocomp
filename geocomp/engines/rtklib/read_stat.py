# SPDX-License-Identifier: GPL-2.0-or-later
"""The satellite geometry ``rnx2rtkp`` writes beside its solution (FR-603, P12c-35).

With ``out-outstat = residual`` the engine writes ``<solution>.stat`` next to
the ``.pos``: per epoch, a ``$POS`` line, clock and velocity lines, and one
``$SAT`` line per satellite and frequency it used. GeoComp reads the ``$SAT``
lines for one thing -- each satellite's azimuth and elevation -- because that
geometry is what dilution of precision is defined from, and the ``.pos`` file
carries no DOP in any of its formats (``specs/08`` section 7.1).

The ``$SAT`` layout is RTKLIB's ``outsolstat`` in ``src/rtkpos.c`` at the pinned
commit: week, time of week, satellite, frequency (from 1), azimuth and elevation
in degrees, the code and carrier residuals, then the valid-data flag. A
satellite counts for an epoch when its first frequency is flagged valid, as the
solution used it; the engine's elevation mask has already decided which
satellites have lines at all.

**A combined solution writes every epoch twice.** With ``pos1-soltype =
combined`` the engine runs a forward pass and then a backward one, and both
write to the same file: each epoch's block, opened by its ``$POS`` line, comes
once in time order and again, later, in reverse. Read as they come, the two
would double every epoch's satellites and shrink its DOP by the square root of
two. The first block of an epoch -- the forward pass's -- is the one read; a
block for an epoch already read is skipped whole. Keying on the ``$POS`` line
rather than on a change of time matters: the backward pass begins on the very
epoch the forward pass ended on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from geocomp.core.errors import DataError

__all__ = ["SatelliteSighting", "read_satellite_geometry", "to_millisecond"]

#: GPS time began at 1980-01-06 00:00:00; weeks and seconds-of-week count from
#: it. The same origin as the ``.pos`` reader's, so an epoch here and an epoch
#: there are the same datetime.
_GPS_EPOCH = datetime(1980, 1, 6, tzinfo=UTC)

#: The fields a ``$SAT`` line must have for its geometry to be read.
_FIELDS = 9


def to_millisecond(time: datetime) -> datetime:
    """*time* rounded to the millisecond: how the solution and its status file agree on an epoch.

    Both print the time of week to three decimals, but the ``.pos`` file may print
    a calendar date instead, and a float second converted two ways can differ in
    the last microsecond.
    """
    rounded = round(time.microsecond / 1000) * 1000
    if rounded == 1_000_000:
        return time.replace(microsecond=0) + timedelta(seconds=1)
    return time.replace(microsecond=rounded)


@dataclass(frozen=True)
class SatelliteSighting:
    """One satellite as the solution saw it at one epoch.

    Attributes:
        satellite: RTKLIB's identifier, ``G07`` and the like.
        azimuth: Radians, clockwise from north.
        elevation: Radians above the horizon.
    """

    satellite: str
    azimuth: float
    elevation: float


def read_satellite_geometry(path: str | Path) -> dict[datetime, tuple[SatelliteSighting, ...]]:
    """Each epoch's used satellites, keyed by the epoch's GPS time to the millisecond.

    Lines other than ``$POS`` and ``$SAT`` are skipped, and so are
    frequencies after the first, satellites flagged not valid, and a second
    block for an epoch already read (a combined solution's backward pass).

    Raises:
        DataError: ``rtklib_status_malformed`` for a ``$POS`` or ``$SAT`` line
            whose fields cannot be read, naming the file and the line. A geometry read from
            a file that changed shape would give a DOP of the wrong satellites,
            which looks exactly as plausible as the right one.
    """
    path = Path(path)
    epochs: dict[datetime, list[SatelliteSighting]] = {}
    repeated = False
    with path.open(encoding="ascii", errors="replace") as handle:
        for number, line in enumerate(handle, start=1):
            if line.startswith("$POS,"):
                time = _epoch(line, path, number)
                repeated = time in epochs
                epochs.setdefault(time, [])
                continue
            if repeated or not line.startswith("$SAT,"):
                continue
            fields = line.strip().split(",")[1:]
            try:
                if len(fields) < _FIELDS:
                    raise ValueError(f"{len(fields)} fields")
                week, seconds = int(fields[0]), float(fields[1])
                frequency, valid = int(fields[3]), int(fields[8])
                azimuth, elevation = float(fields[4]), float(fields[5])
            except ValueError as error:
                raise DataError(
                    "rtklib_status_malformed",
                    file=str(path),
                    line=number,
                    reason=str(error),
                    expected=(
                        "$SAT,week,time of week,satellite,frequency,azimuth,elevation,"
                        "code residual,carrier residual,valid flag,..."
                    ),
                ) from None
            time = to_millisecond(_GPS_EPOCH + timedelta(weeks=week, seconds=seconds))
            sightings = epochs.setdefault(time, [])
            if frequency != 1 or valid != 1:
                continue
            sightings.append(
                SatelliteSighting(fields[2], math.radians(azimuth), math.radians(elevation))
            )
    return {time: tuple(sightings) for time, sightings in epochs.items()}


def _epoch(line: str, path: Path, number: int) -> datetime:
    """The epoch a ``$POS`` line opens, to the millisecond."""
    fields = line.strip().split(",")[1:]
    try:
        if len(fields) < 2:
            raise ValueError(f"{len(fields)} fields")
        week, seconds = int(fields[0]), float(fields[1])
    except ValueError as error:
        raise DataError(
            "rtklib_status_malformed",
            file=str(path),
            line=number,
            reason=str(error),
            expected="$POS,week,time of week,solution status,x,y,z,...",
        ) from None
    return to_millisecond(_GPS_EPOCH + timedelta(weeks=week, seconds=seconds))
