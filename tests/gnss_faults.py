# SPDX-License-Identifier: GPL-2.0-or-later
"""Faults put into a real RINEX 2 observation file, so the engine has something to find.

RTKLIB's sample baseline (``tests/data/rtklib``) has no cycle slip and no
outlier in it -- 120 epochs, every signal clean -- so a reader of the engine's
slip and rejection reports has nothing to read there. This module puts known
ones in: it shifts chosen observations of chosen satellites from a chosen epoch,
and the test then asks whether the engine found each one where it was put.

A **cycle slip** is a jump of whole cycles in the carrier phase that stays: the
phase is shifted from one epoch to the end. Five cycles on L1 and three on L2
move the geometry-free combination by 5 x 0.1903 - 3 x 0.2442 = 0.219 m, over
four times the 0.05 m RTKLIB takes as a slip (``pos2-slipthres``). No
loss-of-lock flag is set, so the engine has to find it from the phase alone.

An **outlier** is one bad epoch: 500 m on both pseudoranges of one satellite,
far beyond the 30 m RTKLIB rejects a code residual at (``pos2-rejcode``), and
the ten times that it allows just after a satellite's ambiguity restarts.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SLIP_AND_OUTLIER", "Fault", "with_faults"]

#: RINEX 2 puts at most this many satellites on an epoch line, and this many
#: observations on a data line, before continuing on the next.
_SATELLITES_PER_LINE = 12
_OBSERVATIONS_PER_LINE = 5
#: Each observation: F14.3, then a loss-of-lock and a signal-strength digit.
_WIDTH = 16


@dataclass(frozen=True)
class Fault:
    """Add *delta* to one observation of one satellite, over a run of epochs.

    Attributes:
        satellite: ``G20`` and the like.
        observation: The RINEX 2 type, ``L1``, ``C1``, ``P2``...
        delta: In the observation's own unit: cycles for phase, metres for code.
        first: The first epoch shifted, counting the file's epochs from 0.
        last: The last epoch shifted, inclusive; ``None`` for every one after.
    """

    satellite: str
    observation: str
    delta: float
    first: int
    last: int | None = None

    def covers(self, epoch: int) -> bool:
        """Whether this fault shifts the observation at *epoch*."""
        return epoch >= self.first and (self.last is None or epoch <= self.last)


#: A slip on G20 from 00:30 and an outlier on G19 at 00:45 of the sample rover.
SLIP_AND_OUTLIER = (
    Fault("G20", "L1", 5.0, 60),
    Fault("G20", "L2", 3.0, 60),
    Fault("G19", "C1", 500.0, 90, 90),
    Fault("G19", "P2", 500.0, 90, 90),
)


def with_faults(text: str, faults: tuple[Fault, ...]) -> str:
    """*text*, a RINEX 2 observation file, with *faults* applied.

    Raises:
        ValueError: For an epoch flag of 6 (cycle-slip records, which this does
            not parse), or an observation type the header does not list. Event
            records -- flags 2 to 5, header lines in place of observations --
            are passed over and do not count as epochs.
    """
    lines = text.splitlines(keepends=True)
    end = next(i for i, line in enumerate(lines) if line[60:73] == "END OF HEADER")
    types = _observation_types(lines[:end])
    for fault in faults:
        if fault.observation not in types:
            raise ValueError(f"{fault.observation} is not observed in this file: {types}")
    rows = -(-len(types) // _OBSERVATIONS_PER_LINE)

    index, epoch = end + 1, 0
    while index < len(lines) and lines[index].strip():
        head = lines[index]
        flag, count = head[28], int(head[29:32])
        if flag in "2345":
            # An event: *count* header lines follow, and no observations.
            index += 1 + count
            continue
        if flag not in "01":
            raise ValueError(f"epoch flag {flag!r} at line {index + 1}")
        satellites: list[str] = []
        while len(satellites) < count:
            row = lines[index].rstrip("\r\n")[32:68]
            satellites += [row[k : k + 3].replace(" ", "0") for k in range(0, len(row), 3)]
            index += 1
        for satellite in satellites[:count]:
            for fault in faults:
                if fault.satellite == satellite and fault.covers(epoch):
                    row, column = divmod(types.index(fault.observation), _OBSERVATIONS_PER_LINE)
                    lines[index + row] = _shifted(lines[index + row], column, fault.delta)
            index += rows
        epoch += 1
    return "".join(lines)


def _observation_types(header: list[str]) -> list[str]:
    """The ``# / TYPES OF OBSERV`` list, across its continuation lines."""
    types: list[str] = []
    count = 0
    for line in header:
        if line[60:79] == "# / TYPES OF OBSERV":
            if not types:
                count = int(line[:6])
            types += line[6:60].split()
    return types[:count]


def _shifted(line: str, column: int, delta: float) -> str:
    """*line* with the observation in *column* shifted by *delta*, flags kept."""
    body, ending = line.rstrip("\r\n"), line[len(line.rstrip("\r\n")) :]
    start = _WIDTH * column
    value = float(body[start : start + 14]) + delta
    return f"{body[:start]}{value:14.3f}{body[start + 14 :]}{ending}"
