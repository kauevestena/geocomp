# SPDX-License-Identifier: GPL-2.0-or-later
"""What ``rnx2rtkp`` writes beside its solution about each epoch (FR-603, P12c-35, P12c-36).

With ``out-outstat = residual`` the engine writes ``<solution>.stat`` next to
the ``.pos``: per epoch, a ``$POS`` line, clock and velocity lines, and one
``$SAT`` line per satellite and frequency it processed. None of what GeoComp
reads here is in the ``.pos`` file in any of its formats (``specs/08`` section
7.1):

* **The geometry** -- each used satellite's azimuth and elevation, which is
  what dilution of precision is defined from. A satellite counts for an epoch
  when its first frequency is flagged valid, as the solution used it; the
  engine's elevation mask has already decided which satellites have lines.
* **Cycle slips** -- the signals the engine detected a slip on at that epoch:
  the slip flag's first bit (``LLI_SLIP``) on a line flagged valid. The flag
  alone is not enough. RTKLIB clears it each epoch only for satellites both
  receivers observe, so a satellite the base has lost carries its last flag
  forward on every line until it returns -- and is not valid on any of them.
* **Rejected observations** -- the signals the engine rejected as outliers at
  that epoch. RTKLIB keeps a per-signal counter that it raises on each
  rejection -- up to three times an epoch, once for each pass over the
  residuals -- and resets to zero when it restarts the signal's ambiguity,
  after a slip or a second rejection. The counter itself is therefore not a
  count of anything a user can name; *a change to a value other than zero* is
  one rejected signal at one epoch. It misses a rejection only where the
  engine reset the counter and rejected that signal as many times again
  within the same epoch.

The ``$SAT`` layout is RTKLIB's ``outsolstat`` in ``src/rtkpos.c`` at the pinned
commit: week, time of week, satellite, frequency (from 1), azimuth and elevation
in degrees, the code and carrier residuals, the valid-data flag, signal
strength, ambiguity flag, slip flag, lock count, outage count, slip count and
rejection count. A signal is named by the satellite and that frequency number,
``G20/1``: the number is RTKLIB's index into the frequencies processed, not a
band, and it means a different band for different constellations.

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
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from geocomp.core.errors import DataError

__all__ = [
    "EpochStatus",
    "SatelliteSighting",
    "read_satellite_geometry",
    "read_status",
    "to_millisecond",
]

#: GPS time began at 1980-01-06 00:00:00; weeks and seconds-of-week count from
#: it. The same origin as the ``.pos`` reader's, so an epoch here and an epoch
#: there are the same datetime.
_GPS_EPOCH = datetime(1980, 1, 6, tzinfo=UTC)

#: The fields a ``$SAT`` line must have, up to the rejection count, for it to be read.
_FIELDS = 16

#: The slip flag's first bit: a slip detected at this epoch. The second marks a
#: half-cycle ambiguity, which is not a slip.
_LLI_SLIP = 1

#: What a malformed ``$SAT`` line was expected to look like, for the refusal.
_SAT_LAYOUT = (
    "$SAT,week,time of week,satellite,frequency,azimuth,elevation,code residual,"
    "carrier residual,valid flag,signal strength,ambiguity flag,slip flag,lock count,"
    "outage count,slip count,rejection count,..."
)


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


@dataclass(frozen=True)
class EpochStatus:
    """What the engine reported about one epoch beyond its position.

    Attributes:
        sightings: The satellites the solution used, for the geometry.
        slips: The signals a cycle slip was detected on, as ``G20/1``.
        rejections: The signals rejected as outliers, as ``G19/2``.
    """

    sightings: tuple[SatelliteSighting, ...] = ()
    slips: tuple[str, ...] = ()
    rejections: tuple[str, ...] = ()


def read_status(path: str | Path) -> dict[datetime, EpochStatus]:
    """Each epoch's status, keyed by the epoch's GPS time to the millisecond.

    One pass over a file that can run to hundreds of megabytes. Lines other
    than ``$POS`` and ``$SAT`` are skipped, and so is a second block for an
    epoch already read (a combined solution's backward pass).

    Raises:
        DataError: ``rtklib_status_malformed`` for a ``$POS`` or ``$SAT`` line
            whose fields cannot be read, naming the file and the line. A status
            read from a file that changed shape would give a DOP of the wrong
            satellites, or slips on the wrong ones, which look exactly as
            plausible as the right ones.
    """
    path = Path(path)
    epochs: dict[datetime, _Epoch] = {}
    counters: dict[str, int] = {}
    repeated = False
    with path.open(encoding="ascii", errors="replace") as handle:
        for number, line in enumerate(handle, start=1):
            if line.startswith("$POS,"):
                time = _epoch(line, path, number)
                repeated = time in epochs
                epochs.setdefault(time, _Epoch())
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
                slip, rejected = int(fields[11]), int(fields[15])
            except ValueError as error:
                raise DataError(
                    "rtklib_status_malformed",
                    file=str(path),
                    line=number,
                    reason=str(error),
                    expected=_SAT_LAYOUT,
                ) from None
            time = to_millisecond(_GPS_EPOCH + timedelta(weeks=week, seconds=seconds))
            epoch = epochs.setdefault(time, _Epoch())
            signal = f"{fields[2]}/{frequency}"
            if valid == 1 and slip & _LLI_SLIP:
                epoch.slips.append(signal)
            if rejected not in (0, counters.get(signal, 0)):
                epoch.rejections.append(signal)
            counters[signal] = rejected
            if frequency == 1 and valid == 1:
                epoch.sightings.append(
                    SatelliteSighting(fields[2], math.radians(azimuth), math.radians(elevation))
                )
    return {
        time: EpochStatus(tuple(epoch.sightings), tuple(epoch.slips), tuple(epoch.rejections))
        for time, epoch in epochs.items()
    }


def read_satellite_geometry(path: str | Path) -> dict[datetime, tuple[SatelliteSighting, ...]]:
    """Each epoch's used satellites, keyed by the epoch's GPS time to the millisecond.

    :func:`read_status`, reduced to the geometry.
    """
    return {time: status.sightings for time, status in read_status(path).items()}


@dataclass
class _Epoch:
    """An epoch's status while its lines are being read."""

    sightings: list[SatelliteSighting] = field(default_factory=list)
    slips: list[str] = field(default_factory=list)
    rejections: list[str] = field(default_factory=list)


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
