# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading the ``rnx2rtkp`` solution file (FR-356, FR-206).

``specs/08-engine-rtklib.md`` section 7 carried P7's only **[C]** claim: *the
exact column set depends on the selected output format and MUST be confirmed
against the RTKLIB manual*. It is confirmed here against something better than
the manual -- the source that writes the file, ``src/solution.c`` at the pinned
commit (``outecef``, ``outpos``, ``outenu``, ``outsolheads``), cross-checked
against files a real ``rnx2rtkp`` produced. Three facts came out of that, and
each of them is a way to read this file wrongly without any error appearing.

## 1. The cross columns are signed square roots, not covariances

``sqvar()`` is ``covar < 0 ? -sqrt(-covar) : sqrt(covar)``. So a printed
``-0.6097`` is **not** a covariance of -0.6097 and **not** a correlation: it is
the signed root of one, and the covariance is ``-0.6097**2 = -0.3717``.
Rebuilding the matrix therefore needs ``sign(v) * v**2``. Squaring without
restoring the sign turns every negative correlation positive; using the value
as a covariance is wrong by a square. **This is the whole of FR-206 for this
engine, and nothing in the file says it.**

## 2. Every format is fourteen columns of the same shape, ordered differently

| Format | Positions | deviation triple | Cross triple, as written |
|---|---|---|---|
| LLH (default) | lat, lon, h | n, e, u | N-E, E-U, N-U |
| LLH with ``-g`` | lat, lon as deg/min/sec | n, e, u | N-E, E-U, N-U |
| XYZ (``-e``) | x, y, z | x, y, z | X-Y, Y-Z, Z-X |
| ENU (``-a``) | e, n, u baseline | e, n, u | E-N, N-U, E-U |

The deviation triple and the cross triple do not run in the same order as each
other in any format, and the cross triple's order differs between them.

## 3. One of the headers is wrong upstream, so the labels cannot be trusted

``specs/08`` §7 says to read the file's own header rather than assume a column
order. Necessary, and **not sufficient**: with ``-g``, RTKLIB labels the third
cross column ``sdue`` while writing the same ``sqvar(Q[5])`` -- the **N-U**
covariance -- that the default format correctly calls ``sdun``. And ``sdue``
genuinely means E-U in the ENU format. A parser that believes labels transposes
two components between one run and the next.

So the header decides the **format**, and the format decides the **meaning** of
each column. The labels are then checked against what the format says they
should be, and a disagreement is reported in
:attr:`PosSolution.header_anomalies` rather than obeyed.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = [
    "PosEpoch",
    "PosFormat",
    "PosSolution",
    "SolutionStatus",
    "read_pos",
]

METRE = Unit.METRE

#: GPS time began at 1980-01-06 00:00:00 UTC. Weeks and seconds-of-week in the
#: file are GPS time, which does not observe leap seconds; the conversion to a
#: civil instant is therefore approximate by the current offset and is *not*
#: done here -- the epoch is reported as GPS time and labelled as such.
_GPS_EPOCH = datetime(1980, 1, 6, tzinfo=UTC)


class SolutionStatus(Enum):
    """RTKLIB's ``Q``. Never discarded: a float solution presented without it
    is a misrepresentation (``specs/08`` §7)."""

    FIXED = 1
    FLOAT = 2
    SBAS = 3
    DGPS = 4
    SINGLE = 5
    PPP = 6

    @property
    def is_ambiguity_fixed(self) -> bool:
        """The distinction that decides whether a baseline is millimetre or
        decimetre work."""
        return self is SolutionStatus.FIXED


@dataclass(frozen=True)
class _Layout:
    """What one output format means, by position rather than by label."""

    #: Columns before Q: three for a position, seven where ``-g`` splits the
    #: latitude and longitude into degrees, minutes and seconds.
    position_columns: int
    #: Component names in the order the standard deviations are written.
    components: tuple[str, str, str]
    #: Which pair each cross column is, as indices into ``components`` and in
    #: the order the file writes them.
    cross_pairs: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]
    #: What ``outsolheads`` labels those cross columns. Checked, never obeyed.
    expected_cross_labels: tuple[str, str, str]


class PosFormat(Enum):
    LLH = "llh"
    LLH_DMS = "llh_dms"
    XYZ = "xyz"
    ENU = "enu"

    @property
    def layout(self) -> _Layout:
        return _LAYOUTS[self]


_LAYOUTS = {
    PosFormat.LLH: _Layout(
        position_columns=3,
        components=("n", "e", "u"),
        cross_pairs=((0, 1), (1, 2), (0, 2)),
        expected_cross_labels=("sdne", "sdeu", "sdun"),
    ),
    PosFormat.LLH_DMS: _Layout(
        position_columns=7,
        components=("n", "e", "u"),
        cross_pairs=((0, 1), (1, 2), (0, 2)),
        # Upstream writes "sdue" here for the N-U covariance. Recorded as the
        # expectation so the check below does not fire on every such file, and
        # documented as the defect it is rather than silently accommodated.
        expected_cross_labels=("sdne", "sdeu", "sdue"),
    ),
    PosFormat.XYZ: _Layout(
        position_columns=3,
        components=("x", "y", "z"),
        cross_pairs=((0, 1), (1, 2), (2, 0)),
        expected_cross_labels=("sdxy", "sdyz", "sdzx"),
    ),
    PosFormat.ENU: _Layout(
        position_columns=3,
        components=("e", "n", "u"),
        cross_pairs=((0, 1), (1, 2), (0, 2)),
        expected_cross_labels=("sden", "sdnu", "sdue"),
    ),
}

#: ``% antenna1  : <type>              ( 0.0000  0.0000  0.0000)``. The type is
#: left-padded to 21 characters and followed by the antenna delta in brackets,
#: so the bracket is what ends it -- an antenna name can contain spaces, and
#: splitting on whitespace would truncate ``AOAD/M_T JPLA`` to ``AOAD/M_T``,
#: which is the very distinction this line exists to show.
_ANTENNA = re.compile(r"^%\s*antenna(?P<index>[12])\s*:\s*(?P<type>.*?)\s*\(")

#: How the column header names the first position column, per format.
_FORMAT_BY_HEADER = (
    ("latitude(d'\")", PosFormat.LLH_DMS),
    ("latitude(deg)", PosFormat.LLH),
    ("x-ecef(m)", PosFormat.XYZ),
    ("e-baseline(m)", PosFormat.ENU),
)


@dataclass(frozen=True)
class PosEpoch:
    """One solution epoch, with its covariance whole."""

    time: datetime
    position: tuple[float, ...]
    status: SolutionStatus
    satellites: int
    covariance: Covariance
    age: float = 0.0
    ratio: float = 0.0

    @property
    def is_ambiguity_fixed(self) -> bool:
        return self.status.is_ambiguity_fixed

    @property
    def decimal_position(self) -> tuple[float, float, float]:
        """The position as three numbers, whatever the file wrote it as.

        ``-g`` splits the latitude and the longitude into degrees, minutes and
        seconds, so :attr:`position` holds **seven** numbers rather than three
        and its last three are ``(longitude minutes, longitude seconds,
        height)`` -- a triple that looks like a position and is not. The raw
        seven are kept on :attr:`position` because that is what the file says;
        this is what a caller that wants a coordinate should use.

        The same trap is handled for the ``% ref pos`` header by
        :func:`_reference_position`, whose docstring names it. Below the header
        it went unhandled until phase P7c, when the trajectory layer needed a
        real coordinate per epoch.
        """
        if len(self.position) == 7:
            return (
                _sexagesimal(list(self.position[0:3])),
                _sexagesimal(list(self.position[3:6])),
                self.position[6],
            )
        return (self.position[0], self.position[1], self.position[2])

    @property
    def is_geodetic(self) -> bool:
        """Whether the position is a latitude and longitude rather than metres.

        Read from the covariance's labels, which the layout table sets per
        format: ``(n, e, u)`` is one of the two geodetic formats, ``(e, n, u)``
        is the ENU baseline and ``(x, y, z)`` is ECEF. The epoch does not carry
        its format, and this is the one thing about it that changes what its
        numbers mean.
        """
        return self.covariance.labels == ("n", "e", "u")

    def quantities(self) -> tuple[Quantity, ...]:
        """The three components with their standard deviations, in metres.

        The covariance is the authority; this is for callers that want a
        component at a time and accept losing the correlations in doing so.

        Raises:
            DataError: for a geodetic epoch. Its first two components are
                **degrees** while the deviations beside them are **metres** on
                the ground, so a :class:`Quantity` pairing them would carry a
                value and an uncertainty in different quantities under one unit
                -- and would read as a coordinate with a 1.5 m sigma that is
                really 1.5 m of northing against a number of degrees. Use
                :attr:`decimal_position` and :attr:`covariance` separately, or
                an ECEF run, which is what a baseline wants anyway.
        """
        if self.is_geodetic:
            raise DataError(
                "pos_quantities_are_geodetic",
                received=f"components {self.covariance.labels}",
                expected=(
                    "an ECEF or ENU epoch, whose components are metres like "
                    "their deviations"
                ),
            )
        deviations = np.sqrt(np.diag(self.covariance.matrix))
        return tuple(
            Quantity.from_std_dev(value, float(sigma), METRE)
            for value, sigma in zip(self.decimal_position, deviations, strict=True)
        )


@dataclass
class PosSolution:
    """A parsed ``.pos`` file.

    Attributes:
        header_anomalies: Where the file's own column labels disagreed with what
            its format means. Not obeyed -- see the module docstring -- but
            reported, because a user comparing two runs deserves to know that
            one of them labelled a column wrongly.
    """

    path: Path
    format: PosFormat
    epochs: tuple[PosEpoch, ...] = ()
    program: str = ""
    reference_position: tuple[float, float, float] | None = None
    obs_start: datetime | None = None
    obs_end: datetime | None = None
    inputs: tuple[str, ...] = ()
    header_anomalies: list[str] = field(default_factory=list)
    comments: tuple[str, ...] = ()

    @property
    def components(self) -> tuple[str, str, str]:
        return self.format.layout.components

    def fixed_epochs(self) -> tuple[PosEpoch, ...]:
        return tuple(epoch for epoch in self.epochs if epoch.is_ambiguity_fixed)

    @property
    def fixed_fraction(self) -> float:
        """The single most informative summary of a kinematic run
        (``specs/11`` §5)."""
        return len(self.fixed_epochs()) / len(self.epochs) if self.epochs else 0.0

    def last(self) -> PosEpoch:
        """The final epoch -- for a static run, the solution.

        A static ``rnx2rtkp`` run writes the filter's state at every epoch and
        the last one is the converged answer; taking the first, or averaging
        them, would mix a converging filter's early guesses into the result.
        """
        if not self.epochs:
            raise DataError(
                "pos_file_has_no_solutions",
                file=str(self.path),
                expected="at least one solution epoch",
            )
        return self.epochs[-1]

    @property
    def antennas(self) -> dict[int, str]:
        """Which receiver antenna the engine **resolved**, by position (1 = rover).

        ``specs/08`` §7.5. This is not the antenna that was *configured*: when
        ``pos1-posopt2`` is on, ``rnx2rtkp`` looks the configured name up in the
        ANTEX and, on a miss, **clears the name and carries on with no
        calibration for that receiver**. The warning goes to a trace file that
        is off by default, so the run succeeds, the solution looks ordinary, and
        it is wrong by that antenna's phase-centre offset -- centimetres for
        some antennas.

        What the engine writes here is the entry it matched, because it copies
        the matched entry's own name over the configured one. So an empty string
        means no calibration was applied, and a name that differs from the one
        configured means it matched something else -- ``searchpcv`` falls back
        to the antenna without its radome, which is a different calibration.

        Absent for a run whose header was not written, or a single-point mode
        where the engine writes no antenna lines at all.
        """
        resolved: dict[int, str] = {}
        for line in self.comments:
            match = _ANTENNA.match(line)
            if match is not None:
                resolved[int(match["index"])] = match["type"].strip()
        return resolved

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format.value,
            "program": self.program,
            "epochs": len(self.epochs),
            "fixed_epochs": len(self.fixed_epochs()),
            "inputs": list(self.inputs),
            "antennas": {str(index): name for index, name in self.antennas.items()},
            "header_anomalies": list(self.header_anomalies),
        }


def read_pos(path: str | Path) -> PosSolution:
    """Parse the ``.pos`` file at *path*.

    Raises:
        DataError: if no column header is present to identify the format, or if
            a solution record does not have the column count its format
            requires. Both are refusals rather than best-effort reads: a
            mis-assigned column in a covariance is exactly the silent, invisible
            error this module exists to prevent.
    """
    path = Path(path)
    text = path.read_text(encoding="ascii", errors="replace")
    lines = text.splitlines()

    comments = tuple(line for line in lines if line.startswith("%"))
    column_header = _column_header(comments, path)
    solution_format = _format_of(column_header, path)
    layout = solution_format.layout

    result = PosSolution(
        path=path,
        format=solution_format,
        comments=comments,
        program=_after(comments, "% program"),
        inputs=tuple(
            _after((line,), "% inp file") for line in comments if line.startswith("% inp file")
        ),
        obs_start=_comment_epoch(comments, "% obs start"),
        obs_end=_comment_epoch(comments, "% obs end"),
        reference_position=_reference_position(comments, solution_format),
    )
    result.header_anomalies = _check_labels(column_header, layout)

    epochs = []
    for line in lines:
        if line.startswith("%") or not line.strip():
            continue
        epochs.append(_epoch(line, layout, path))
    result.epochs = tuple(epochs)
    return result


# -- the header -----------------------------------------------------------


def _column_header(comments: tuple[str, ...], path: Path) -> str:
    """The ``%  GPST  latitude(deg) ...`` record that names the columns."""
    for line in comments:
        if any(marker in line for marker, _ in _FORMAT_BY_HEADER):
            return line
    raise DataError(
        "pos_column_header_missing",
        file=str(path),
        expected="a '%' record naming the columns, written when outhead is on",
    )


def _format_of(column_header: str, path: Path) -> PosFormat:
    for marker, solution_format in _FORMAT_BY_HEADER:
        if marker in column_header:
            return solution_format
    raise DataError(
        "pos_format_unrecognised",
        file=str(path),
        received=column_header.strip()[:80],
        expected="a column header naming lat/lon, x-ecef or e-baseline positions",
    )


def _check_labels(column_header: str, layout: _Layout) -> list[str]:
    """Compare the file's cross-column labels against what its format means.

    Reported, never obeyed. The known upstream mislabel is already in
    ``expected_cross_labels``, so this fires on something new rather than on
    every ``-g`` file.
    """
    labels = [token.split("(")[0] for token in column_header.replace("%", " ").split()]
    found = tuple(label for label in labels if label.startswith("sd") and len(label) == 4)
    if len(found) != 3:
        return []
    if found != layout.expected_cross_labels:
        return [
            f"the column header labels the cross-covariance columns {found} where this "
            f"format writes {layout.expected_cross_labels}; the format's meaning is used"
        ]
    return []


def _after(comments: tuple[str, ...], prefix: str) -> str:
    for line in comments:
        if line.startswith(prefix):
            _, _, value = line.partition(":")
            return value.strip()
    return ""


def _comment_epoch(comments: tuple[str, ...], prefix: str) -> datetime | None:
    """``% obs start : 2005/04/02 00:00:00.0 GPST (week1316 518400.0s)``."""
    text = _after(comments, prefix)
    if not text:
        return None
    try:
        return datetime.strptime(" ".join(text.split()[:2]), "%Y/%m/%d %H:%M:%S.%f").replace(
            tzinfo=UTC
        )
    except ValueError:
        return None


def _reference_position(
    comments: tuple[str, ...], solution_format: PosFormat
) -> tuple[float, float, float] | None:
    """``% ref pos``, which is written in the same representation as the solution.

    That includes the ``-g`` case, where the latitude and longitude are three
    fields each and the line carries **seven** numbers rather than three. Taking
    the first three there yields ``(35.0, 7.0, 55.42909)`` -- a plausible-looking
    triple that is a latitude's degrees, minutes and seconds masquerading as a
    position.
    """
    parts = _after(comments, "% ref pos").split()
    expected = 7 if solution_format is PosFormat.LLH_DMS else 3
    if len(parts) < expected:
        return None
    try:
        numbers = [float(part) for part in parts[:expected]]
    except ValueError:
        return None
    if solution_format is PosFormat.LLH_DMS:
        return (_sexagesimal(numbers[0:3]), _sexagesimal(numbers[3:6]), numbers[6])
    return (numbers[0], numbers[1], numbers[2])


def _sexagesimal(parts: list[float]) -> float:
    """Degrees, minutes and seconds to degrees, with the sign on the degrees."""
    degrees, minutes, seconds = parts
    magnitude = abs(degrees) + minutes / 60.0 + seconds / 3600.0
    return math.copysign(magnitude, degrees)


# -- solution records -----------------------------------------------------


def _epoch(line: str, layout: _Layout, path: Path) -> PosEpoch:
    tokens = line.split()
    # Two tokens of time whichever time format is in force: a GPS week and a
    # second-of-week, or a date and a time.
    required = 2 + layout.position_columns + 2 + 3 + 3 + 2
    if len(tokens) < required:
        raise DataError(
            "pos_record_too_short",
            file=str(path),
            received=f"{len(tokens)} columns",
            expected=f"at least {required} for the {layout.components} format",
        )

    time = _epoch_time(tokens[0], tokens[1], path)
    cursor = 2
    position = tuple(_float(token, path) for token in tokens[cursor : cursor + layout.position_columns])
    cursor += layout.position_columns

    status = _status(tokens[cursor], path)
    satellites = int(_float(tokens[cursor + 1], path))
    cursor += 2

    deviations = [_float(token, path) for token in tokens[cursor : cursor + 3]]
    cursor += 3
    crosses = [_float(token, path) for token in tokens[cursor : cursor + 3]]
    cursor += 3
    age, ratio = _float(tokens[cursor], path), _float(tokens[cursor + 1], path)

    return PosEpoch(
        time=time,
        position=position,
        status=status,
        satellites=satellites,
        covariance=_covariance(deviations, crosses, layout),
        age=age,
        ratio=ratio,
    )


def _covariance(
    deviations: list[float], crosses: list[float], layout: _Layout
) -> Covariance:
    """Assemble the 3x3, restoring the sign the square root carried.

    ``sqvar`` writes ``sign(c) * sqrt(|c|)``, so the covariance is
    ``sign(v) * v**2``. Squaring alone loses every negative correlation, which
    is most of them: in a levelled GNSS solution the north-up and east-up terms
    are routinely negative, and dropping their sign makes a position ellipse
    lean the wrong way.
    """
    matrix = np.zeros((3, 3), dtype=float)
    for index, sigma in enumerate(deviations):
        matrix[index, index] = sigma * sigma
    for (first, second), value in zip(layout.cross_pairs, crosses, strict=True):
        covariance = math.copysign(value * value, value)
        matrix[first, second] = covariance
        matrix[second, first] = covariance
    return Covariance(
        matrix=matrix,
        labels=layout.components,
        units=(METRE, METRE, METRE),
    )


def _epoch_time(first: str, second: str, path: Path) -> datetime:
    """A GPS week and second-of-week, or a calendar date and time.

    GPS time does not observe leap seconds and this does not pretend otherwise:
    a week/second pair is converted on the GPS scale, so the result is GPS time
    expressed as a ``datetime``, not UTC. Applying an offset here would bake in
    whatever leap-second table this build happened to hold.
    """
    if "/" in first or "-" in first:
        for pattern in ("%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(f"{first} {second}", pattern).replace(tzinfo=UTC)
            except ValueError:
                continue
        raise DataError(
            "pos_epoch_time_unreadable",
            file=str(path),
            received=f"{first} {second}",
            expected="a GPS week and second-of-week, or a date and time",
        )
    week, seconds = _float(first, path), _float(second, path)
    return _GPS_EPOCH + timedelta(weeks=int(week), seconds=seconds)


def _status(token: str, path: Path) -> SolutionStatus:
    try:
        return SolutionStatus(int(token))
    except ValueError as error:
        raise DataError(
            "pos_solution_status_unknown",
            file=str(path),
            received=token,
            expected="Q in 1..6 (1 fix, 2 float, 3 sbas, 4 dgps, 5 single, 6 ppp)",
        ) from error


def _float(token: str, path: Path) -> float:
    try:
        return float(token)
    except ValueError as error:
        raise DataError(
            "pos_value_not_a_number",
            file=str(path),
            received=token,
            expected="a number",
        ) from error
