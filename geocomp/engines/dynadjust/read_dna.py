# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading DynAdjust's DNA ``.stn`` and ``.msr`` files (FR-163).

``specs/07-engine-dynadjust.md`` section 4.1. GeoComp *writes* DynaML, for the
reasons in [`adr/0004`](../../../specs/adr/0004-dynadjust-interchange-format.md),
but it **reads** DNA too, because a user with an existing DynAdjust project has
those files and should not have to convert them by hand before GeoComp will
show them.

**DNA is column-oriented, and that is the whole difficulty.** Fields are at
fixed positions and adjacent values run together with no separator -- a real
line from upstream's own sample reads
``12647.1455-1.0467927495000e-05``, which is a coordinate and a variance
abutting. Splitting on whitespace produces one impossible number instead of two
correct ones, so every field here is taken by slice, from the column table in
Appendix B of the User's Guide, and never by tokenising. This fragility is
exactly what ADR-0004 cites for writing XML instead.

Two details that are easy to miss and cost an afternoon each. The Guide notes
values *"can be positioned anywhere within the respective fields without the
need for right or left justification"*, so every slice is stripped rather than
assumed aligned. And upstream's own files mix line endings -- their ``.stn`` is
CRLF and their ``.msr`` is LF -- so a reader that trusts one strips a station
name of its last character on the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    CoordinateSystem,
    Network,
    Observation,
    ObservationStatus,
    ObservationType,
    Station,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.formats import hp_to_radians, seconds_to_radians
from geocomp.engines.dynadjust.read_dynaml import (
    _ANGULAR,
    BY_CODE,
    UNMAPPED,
    ReadReport,
    _constraint,
)
from geocomp.engines.dynadjust.read_dynaml import _position as _dynaml_position

__all__ = ["DnaHeader", "read_dna", "read_dna_measurements", "read_dna_stations"]

METRE, RADIAN = Unit.METRE, Unit.RADIAN


def _field(line: str, start: int, end: int) -> str:
    """Columns *start*..*end* inclusive, 1-based as the Guide numbers them.

    One-based and inclusive because that is how Appendix B's tables read, and
    translating them to Python slices at every call site is where the
    off-by-ones come from. A short line yields an empty field rather than an
    error: trailing optional fields are routinely absent.
    """
    return line[start - 1 : end].strip()


@dataclass(frozen=True)
class DnaHeader:
    """The ``!#=DNA`` first line: version, file type, frame, epoch, count.

    The frame and epoch here are the file's defaults; a measurement may name its
    own, and does in upstream's GNSS sample. Reading only the per-measurement
    ones would leave every measurement that omits them frameless.
    """

    version: str = ""
    kind: str = ""
    date: str = ""
    frame: str = ""
    epoch: str = ""
    count: int = 0


def _read_lines(path: str | Path) -> list[str]:
    """Every line, with line endings normalised.

    ``newline=""`` plus an explicit strip rather than text-mode translation,
    because upstream ships a CRLF ``.stn`` beside an LF ``.msr`` and a reader
    that handles only one loses the last character of every fixed-width field on
    the other -- which for a station name is a different station.
    """
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise DataError(
            "dna_unreadable", path=str(path), reason=str(error), expected="a DNA file"
        ) from error
    return [line.rstrip("\r\n") for line in text.splitlines()]


def _header(lines: list[str], path: str | Path) -> DnaHeader:
    for line in lines:
        if line.startswith("!#=DNA"):
            # Guide Table B.1, confirmed against upstream's own files: the
            # fields are 7-12, 13-15, 16-29, 30-43, 44-57, 58-67. Guessed
            # boundaries put the frame at "DA2020    01.0" -- wrong in a way
            # that reads as data rather than as a parse failure.
            return DnaHeader(
                version=_field(line, 7, 12),
                kind=_field(line, 13, 15),
                date=_field(line, 16, 29),
                frame=_field(line, 30, 43),
                epoch=_field(line, 44, 57),
                count=int(_field(line, 58, 67) or 0),
            )
    raise DataError(
        "dna_header_missing",
        path=str(path),
        expected="a first line beginning !#=DNA, as DynAdjust writes it",
    )


def _content(lines: list[str]) -> list[str]:
    """Data lines: not the header, not a ``*`` comment, not blank."""
    return [
        line
        for line in lines
        if line.strip() and not line.startswith("*") and not line.startswith("!#=")
    ]


def read_dna_stations(
    path: str | Path, *, crs: str = "", network: Network | None = None
) -> ReadReport:
    """Read a DNA ``.stn`` file (Guide Table B.2)."""
    lines = _read_lines(path)
    header = _header(lines, path)
    network = network if network is not None else Network(
        id=Path(path).stem, crs=crs or header.frame
    )
    report = ReadReport(network=network, frame=header.frame, epoch=header.epoch)

    for line in _content(lines):
        name = _field(line, 1, 20)
        if not name:
            continue
        constraints = (_field(line, 21, 23) or "FFF").upper()
        coordinate_type = _field(line, 25, 27).upper()
        system = {
            "XYZ": CoordinateSystem.CARTESIAN,
            "LLH": CoordinateSystem.GEODETIC,
            "UTM": CoordinateSystem.PROJECTED,
        }.get(coordinate_type)
        if system is None:
            report.skipped.append((name, f"unknown coordinate type {coordinate_type!r}"))
            continue

        first, second = _field(line, 28, 47), _field(line, 48, 67)
        height = _field(line, 68, 87)
        description = _field(line, 92, len(line)) if len(line) >= 92 else ""

        position = _make_position(first, second, height, system, crs or header.frame)
        network.add_station(
            Station(
                id=name,
                approx_position=position,
                constraint=_constraint(constraints, position, system),
                description=description,
            )
        )
    return report


def _make_position(first: str, second: str, height: str, system, crs: str):
    """Build a position from three DNA coordinate fields.

    Reuses the DynaML reader's construction by handing it the same three
    strings, so the HP-notation handling for LLH exists once rather than twice.
    """
    import xml.etree.ElementTree as ET

    coord = ET.Element("StationCoord")
    for tag, value in (("XAxis", first), ("YAxis", second), ("Height", height or "0")):
        child = ET.SubElement(coord, tag)
        child.text = value or "0"
    return _dynaml_position(coord, system, crs)


def read_dna_measurements(
    path: str | Path, network: Network, *, report: ReadReport | None = None
) -> ReadReport:
    """Read a DNA ``.msr`` file (Guide Tables B.3 to B.10)."""
    lines = _read_lines(path)
    header = _header(lines, path)
    report = report or ReadReport(network=network)
    report.frame = report.frame or header.frame
    report.epoch = report.epoch or header.epoch

    rows = _content(lines)
    index = 0
    counter = 0
    while index < len(rows):
        line = rows[index]
        code = _field(line, 1, 1).upper()
        label = f"{code or '?'}#{counter}"

        if code in UNMAPPED:
            report.skipped.append((label, UNMAPPED[code]))
            index += 1 + _continuation_count(code, line)
            counter += 1
            continue

        observation_type = BY_CODE.get(code)
        if observation_type is None:
            report.skipped.append((label, f"unknown DynAdjust measurement type {code!r}"))
            index += 1
            counter += 1
            continue

        if code in {"G", "X", "Y"}:
            index = _read_gnss(rows, index, code, observation_type, network, counter, report)
        elif code == "D":
            index = _read_directions(rows, index, network, counter)
        else:
            _read_scalar(line, code, observation_type, network, counter)
            index += 1
        report.counts[code] = report.counts.get(code, 0) + 1
        counter += 1

    return report


def _continuation_count(code: str, line: str) -> int:
    """How many lines after the header a measurement of this code occupies."""
    if code in {"G"}:
        return 3
    if code in {"X", "Y"}:
        total = int(_field(line, 43, 62) or 1)
        return 3 * total
    return 0


def _status(line: str) -> ObservationStatus:
    return ObservationStatus.EXCLUDED if _field(line, 2, 2) == "*" else ObservationStatus.ACTIVE


def _read_scalar(
    line: str,
    code: str,
    observation_type: ObservationType,
    network: Network,
    counter: int,
) -> None:
    """A one-line measurement (Guide Tables B.4 to B.7)."""
    stations = [_field(line, 3, 22)]
    if code not in {"H", "I", "J", "P", "Q", "R"}:
        second = _field(line, 23, 42)
        if second:
            stations.append(second)
    if code == "A":
        third = _field(line, 43, 62)
        if third:
            stations.append(third)

    if observation_type in _ANGULAR:
        degrees = _field(line, 77, 80) or "0"
        minutes = _field(line, 81, 82) or "0"
        seconds = _field(line, 83, 90) or "0"
        # Reassembled into HP so the single HP implementation in `formats` is
        # used, rather than a second degrees/minutes/seconds path here that can
        # drift from it. DNA splits the angle across three columns; DynaML packs
        # it into one; both must produce the same radians.
        negative = degrees.strip().startswith("-")
        hp = (
            f"{'-' if negative else ''}{abs(int(degrees))}"
            f".{int(minutes):02d}{float(seconds):08.5f}".replace(" ", "0")
        )
        value = hp_to_radians(hp)
        sigma = seconds_to_radians(_field(line, 91, 99) or "1")
        unit = RADIAN
    else:
        value = float(_field(line, 63, 82) or _field(line, 77, 90) or "0")
        sigma = float(_field(line, 83, 102) or _field(line, 91, 99) or "1")
        unit = METRE

    meta = {}
    for key, (start, end) in (
        ("instrument_height", (100, 106)),
        ("target_height", (107, 113)),
    ):
        text = _field(line, start, end)
        if text:
            meta[key] = float(text)

    network.add_observation(
        Observation(
            id=f"{code}{counter}",
            type=observation_type,
            stations=tuple(stations),
            values=(Quantity.from_std_dev(value, sigma, unit),),
            status=_status(line),
            meta=meta,
        )
    )


def _read_gnss(
    rows: list[str],
    index: int,
    code: str,
    observation_type: ObservationType,
    network: Network,
    counter: int,
    report: ReadReport,
) -> int:
    """A G, X or Y measurement with its full covariance (FR-104).

    **DNA lays a cluster out differently from DynaML**, and the difference is
    the kind that silently produces four clusters where there is one. Each
    member gets its **own header line** repeating the measurement code, and only
    the *first* carries the cluster count; a member is then three component
    lines followed by three lines for each *subsequent* member, holding the
    cross-covariance blocks -- the same upper-triangular convention DynaML
    writes as repeated ``GPSCovariance`` elements.

    So a four-baseline cluster occupies 13 + 10 + 7 + 4 lines, and a reader that
    assumed three lines per member walks into the middle of the next block. The
    first draft did exactly that, turning one X cluster into four and one Y into
    six -- and it was only obvious because the DynaML reader of the same network
    reported one of each.
    """
    header_line = rows[index]
    total = int(_field(header_line, 43, 62) or 1) if code in {"X", "Y"} else 1

    scale = float(_field(header_line, 63, 72) or "1")
    for start, end, tag in ((73, 82, "P"), (83, 92, "L"), (93, 102, "H")):
        text = _field(header_line, start, end)
        if text and abs(float(text) - 1.0) > 1e-12:
            raise DataError(
                "dna_directional_variance_scale_unsupported",
                measurement=f"{code}#{counter}",
                received={f"{tag}scale": text},
                expected="P-, L- and H-scale of 1; see the DynaML reader for why",
            )

    observations: list[Observation] = []
    own: list[np.ndarray] = []
    cross: dict[tuple[int, int], np.ndarray] = {}
    cursor = index

    for member in range(total):
        if cursor >= len(rows):
            report.skipped.append((f"{code}#{counter}", "truncated cluster"))
            return len(rows)
        member_header = rows[cursor]
        cursor += 1

        if cursor + 3 > len(rows):
            report.skipped.append((f"{code}#{counter}", "truncated GNSS component block"))
            return len(rows)
        block = rows[cursor : cursor + 3]
        cursor += 3

        components = [float(_field(line, 63, 82) or "0") for line in block]
        matrix = np.zeros((3, 3))
        matrix[0][0] = float(_field(block[0], 83, 102) or "0")
        matrix[1][0] = matrix[0][1] = float(_field(block[1], 83, 102) or "0")
        matrix[1][1] = float(_field(block[1], 103, 122) or "0")
        matrix[2][0] = matrix[0][2] = float(_field(block[2], 83, 102) or "0")
        matrix[2][1] = matrix[1][2] = float(_field(block[2], 103, 122) or "0")
        matrix[2][2] = float(_field(block[2], 123, 142) or "0")
        own.append(matrix * scale)

        # Three lines per subsequent member: the block correlating this member
        # with that one. Dropping them leaves a block-diagonal matrix, which is
        # the correlation FR-104 exists to keep.
        for other in range(member + 1, total):
            if cursor + 3 > len(rows):
                break
            sub = rows[cursor : cursor + 3]
            cursor += 3
            # Columns 83-102, 103-122, 123-142 -- the *variance* columns, not
            # 63-82, which holds the measurement value and is blank on a
            # covariance line. Reading from 63 gives a matrix that is not
            # positive semi-definite, which Covariance refuses; that refusal is
            # what caught the mistake rather than a wrong answer surviving.
            cross[(member, other)] = (
                np.array(
                    [
                        [
                            float(_field(sub[r], 83 + 20 * c, 102 + 20 * c) or "0")
                            for c in range(3)
                        ]
                        for r in range(3)
                    ]
                )
                * scale
            )

        origin = _field(member_header, 3, 22)
        target = _field(member_header, 23, 42) if code in {"G", "X"} else ""
        stations = (origin, target) if code in {"G", "X"} else (origin,)

        observations.append(
            Observation(
                id=f"{code}{counter}-{member}",
                type=observation_type,
                stations=stations,
                values=tuple(
                    Quantity.from_std_dev(
                        components[k], float(np.sqrt(max(own[-1][k][k], 0.0))), METRE
                    )
                    for k in range(3)
                ),
                status=_status(header_line),
                cluster_id=f"{code}{counter}",
                meta={"dynadjust_v_scale": scale} if scale != 1.0 else {},
            )
        )

    for observation in observations:
        network.add_observation(observation)

    size = 3 * len(own)
    matrix = np.zeros((size, size))
    for member, block in enumerate(own):
        matrix[3 * member : 3 * member + 3, 3 * member : 3 * member + 3] = block
    for (i, j), block in cross.items():
        matrix[3 * i : 3 * i + 3, 3 * j : 3 * j + 3] = block
        matrix[3 * j : 3 * j + 3, 3 * i : 3 * i + 3] = block.T

    network.add_cluster(
        Cluster(
            id=f"{code}{counter}",
            kind=ClusterKind.GNSS_BASELINE if code in {"G", "X"} else ClusterKind.GNSS_POINT,
            observation_ids=tuple(o.id for o in observations),
            covariance=Covariance(
                matrix=matrix,
                labels=tuple(f"m{i}.{c}" for i in range(len(own)) for c in ("x", "y", "z")),
                units=(METRE,) * size,
            ),
        )
    )
    return cursor


def _read_directions(rows: list[str], index: int, network: Network, counter: int) -> int:
    """A direction set: header, then ``Total`` further directions."""
    header_line = rows[index]
    origin = _field(header_line, 3, 22)
    total = int(_field(header_line, 43, 62) or 0)

    members: list[Observation] = []

    def add(position: int, line: str) -> None:
        degrees = int(_field(line, 77, 80) or 0)
        minutes = int(_field(line, 81, 82) or 0)
        seconds = float(_field(line, 83, 90) or 0.0)
        hp = f"{degrees}.{minutes:02d}{seconds:08.5f}".replace(" ", "0")
        members.append(
            Observation(
                id=f"D{counter}-{position}",
                type=ObservationType.DIRECTION,
                stations=(origin, _field(line, 23, 42)),
                values=(
                    Quantity.from_std_dev(
                        hp_to_radians(hp),
                        seconds_to_radians(_field(line, 91, 99) or "1"),
                        RADIAN,
                    ),
                ),
                status=_status(header_line),
                cluster_id=f"D{counter}",
            )
        )

    add(0, header_line)
    cursor = index + 1
    for position in range(1, total + 1):
        if cursor >= len(rows):
            break
        add(position, rows[cursor])
        cursor += 1

    for observation in members:
        network.add_observation(observation)
    network.add_cluster(
        Cluster(
            id=f"D{counter}",
            kind=ClusterKind.DIRECTION_SET,
            observation_ids=tuple(o.id for o in members),
            covariance=Covariance(
                matrix=np.diag([o.values[0].variance for o in members]),
                labels=tuple(o.id for o in members),
                units=(RADIAN,) * len(members),
            ),
        )
    )
    return cursor


def read_dna(
    station_path: str | Path,
    measurement_path: str | Path | None = None,
    *,
    network_id: str = "",
    crs: str = "",
) -> ReadReport:
    """Read a DynAdjust DNA project into one network."""
    report = read_dna_stations(station_path, crs=crs)
    if report.network is not None and network_id:
        report.network.id = network_id
    if measurement_path is not None and report.network is not None:
        read_dna_measurements(measurement_path, report.network, report=report)
    return report
