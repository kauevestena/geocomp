# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading and writing the *Adjust* network format (FR-161).

``specs/17-persistence-and-interoperability.md`` section 5.2. The format
accompanies Charles Ghilani's *Adjust* teaching software, and this requirement
was re-planned out of three phases for want of a single example file: no
published grammar, no sample, and a name collision with an unrelated NGS
program of the same name that a search returns instead.

**The grammar here is inferred from ten example files, not transcribed from a
specification**, and that is worth stating plainly because it bounds what the
reader may assume. What makes the inference solid rather than hopeful is that
the format carries its own check: the second line declares how many
observations of each kind follow, so a misparse does not produce a plausible
network -- it produces a count that disagrees, immediately, on every file.

The conventions were confirmed by arithmetic rather than by eye
(``specs/22`` section 4). Reading the coordinate pair as **x = easting,
y = northing** and each angle as **clockwise from backsight to foresight**, the
angles implied by the files' own approximate coordinates agree with the angles
they state to a median of 0.000 degrees over 143 angles in five networks. No
other reading of either convention comes close.

## The layout

.. code-block:: text

    POLIGONAL AC                      <- title
    6 7 0 4 9                         <- distances, angles, azimuths, control, stations
    A 382.0000 1214.0000 0.010 0.010  <- control:  name x y sigma_x sigma_y
    5 538.0000 1202.0000              <- unknown:  name x y
    A 5 156.066 0.004                 <- distance: from to value sigma
    B A 5 53 17 04 9.1                <- angle:    backsight at foresight D M S sigma

Distances and their sigmas are metres; an angle is degrees, minutes and seconds
with its sigma in **seconds of arc**. A control station's two extra numbers are
standard deviations, so control is *weighted* rather than held --
``ConstraintMode.WEIGHTED``, which is what the file says and not the fixed
constraint it would be convenient to assume.

## Two halves of a pair

Each network in the reference corpus arrives twice: once with values and once
without, the second listing the same observations as bare station pairs and
triples. The valueless half is a **plan** -- the observation programme, with
nothing measured yet -- so it yields stations and a topology and no
observations, which is exactly what pre-analysis takes (FR-273). Reading both
is what lets the two be compared, and comparing them is what found a real
defect in the published corpus (``specs/22`` section 4.2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.models import (
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit

__all__ = ["AdjustReport", "read_adjust", "write_adjust"]

@dataclass
class AdjustReport:
    """A network read from an *Adjust* file, and what the file said about itself.

    Attributes:
        network: Stations always; observations only when the file states values.
        title: The first line, verbatim.
        has_values: False for the plan half of a pair.
        declared: The header's counts, ``(distances, angles, azimuths)``.
        found: The rows actually present, in the same order. Equal to
            *declared* in a well-formed file; the two are reported separately
            because one published file disagrees with itself.
        plan: Every observation the file lists, as ``(kind, stations)``, whether
            or not it carries a value. This is the half that can be compared
            between a pair.
    """

    network: Network
    title: str = ""
    has_values: bool = False
    declared: tuple[int, int, int] = (0, 0, 0)
    found: tuple[int, int, int] = (0, 0, 0)
    plan: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: Stations the header counted as control, in file order.
    control: tuple[str, ...] = ()

    @property
    def counts_agree(self) -> bool:
        return self.declared == self.found


def _lines(path: Path) -> list[str]:
    """The file's non-blank lines, decoded and stripped of line endings.

    The corpus is CRLF and Latin-1 -- Portuguese network names carry accents --
    so neither is assumed. UTF-8 is tried first because a file written today
    will be UTF-8 whatever the corpus is.
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return [line.strip() for line in text.replace("\r\n", "\n").split("\n") if line.strip()]


def _number(token: str, *, what: str, line: str, path: Path) -> float:
    try:
        return float(token)
    except ValueError:
        raise DataError(
            "adjust_not_a_number",
            path=str(path),
            field=what,
            received=token,
            line=line[:120],
        ) from None


def read_adjust(path: str | Path, *, accept_count_mismatch: bool = False) -> AdjustReport:
    """Read one *Adjust* file.

    Args:
        accept_count_mismatch: Read the rows the file actually holds even when
            the header's counts disagree with them. **Off by default**: the
            counts are the format's own check, and a file that fails it cannot
            say which reading was intended. It is a parameter rather than a
            refusal because one published file in the reference corpus fails it
            for a knowable reason, and the observations are still there.

    The rows are parsed **by shape rather than by the header's counts** -- a
    distance names two stations and an angle three, which separates the sections
    without trusting the numbers being checked. Counting them afterwards is then
    an independent test rather than a restatement of the input.
    """
    path = Path(path)
    lines = _lines(path)
    if len(lines) < 2:
        raise DataError(
            "adjust_file_too_short",
            path=str(path),
            received=len(lines),
            expected="a title line and a counts line at least",
        )

    title, header = lines[0], lines[1].split()
    if len(header) != 5:
        raise DataError(
            "adjust_header_not_five_counts",
            path=str(path),
            received=lines[1][:120],
            expected="distances, angles, azimuths, control stations, total stations",
        )
    try:
        n_dist, n_ang, n_azi, n_control, n_total = (int(token) for token in header)
    except ValueError:
        raise DataError(
            "adjust_header_not_integers", path=str(path), received=lines[1][:120]
        ) from None

    if n_azi:
        # No file in the reference corpus carries one, so the row layout cannot
        # be pinned. Guessing it would be the same error the specification warns
        # against for the format as a whole.
        raise DataError(
            "adjust_azimuths_unsupported",
            path=str(path),
            received=n_azi,
            expected=(
                "a file without azimuth observations; no example of an azimuth "
                "row exists to pin its layout against, and a guessed layout "
                "reads a plausible wrong number"
            ),
        )

    body = lines[2:]
    if len(body) < n_total:
        raise DataError(
            "adjust_fewer_stations_than_declared",
            path=str(path),
            received=len(body),
            expected=n_total,
        )

    network = Network(id=path.stem, crs="LOCAL")
    control: list[str] = []
    for index, row in enumerate(body[:n_total]):
        tokens = row.split()
        if len(tokens) < 3:
            raise DataError(
                "adjust_station_row_too_short",
                path=str(path),
                line=row[:120],
                expected="a name and two coordinates",
            )
        name = tokens[0]
        position = Position(
            values=(
                Quantity.exact(_number(tokens[1], what="x", line=row, path=path), Unit.METRE),
                Quantity.exact(_number(tokens[2], what="y", line=row, path=path), Unit.METRE),
                Quantity.exact(0.0, Unit.METRE),
            ),
            system=CoordinateSystem.PROJECTED,
            crs="LOCAL",
            height_type=HeightType.NONE,
        )
        constraint = ConstraintSpec()
        if index < n_control:
            sigmas = tokens[3:5]
            if len(sigmas) != 2:
                raise DataError(
                    "adjust_control_without_sigmas",
                    path=str(path),
                    station=name,
                    line=row[:120],
                    expected=(
                        "two standard deviations after the coordinates; a control "
                        "station in this format is weighted, not held, and holding "
                        "it exactly would assert a certainty the file does not"
                    ),
                )
            sigma_x = _number(sigmas[0], what="sigma_x", line=row, path=path)
            sigma_y = _number(sigmas[1], what="sigma_y", line=row, path=path)
            control.append(name)
            constraint = ConstraintSpec(
                mode=ConstraintMode.WEIGHTED,
                components=frozenset({"easting", "northing"}),
                position=position,
                covariance=Covariance(
                    matrix=np.diag([sigma_x**2, sigma_y**2]),
                    # The bare component names, which is what
                    # ``parameters.weighted_constraints`` looks the block up by.
                    labels=("easting", "northing"),
                    units=(Unit.METRE, Unit.METRE),
                ),
            )
        network.add_station(Station(id=name, approx_position=position, constraint=constraint))

    known = set(network.stations)
    rows = body[n_total:]
    plan: list[tuple[str, tuple[str, ...]]] = []
    distances = angles = 0
    valued = 0

    for row in rows:
        tokens = row.split()
        if len(tokens) in (2, 4):
            kind, names, distances = "distance", tuple(tokens[:2]), distances + 1
        elif len(tokens) in (3, 7):
            kind, names, angles = "angle", tuple(tokens[:3]), angles + 1
        else:
            raise DataError(
                "adjust_observation_row_unrecognised",
                path=str(path),
                line=row[:120],
                received=len(tokens),
                expected=(
                    "2 or 4 tokens for a distance (from to [value sigma]), or "
                    "3 or 7 for an angle (backsight at foresight [D M S sigma])"
                ),
            )
        unknown = sorted(set(names) - known)
        if unknown:
            raise DataError(
                "adjust_observation_station_unknown",
                path=str(path),
                line=row[:120],
                received=unknown,
                expected="stations listed in the coordinate block",
            )
        plan.append((kind, names))

        if len(tokens) == 4:
            valued += 1
            identifier = f"d{distances}"
            value = _number(tokens[2], what="distance", line=row, path=path)
            sigma = _number(tokens[3], what="distance sigma", line=row, path=path)
            network.add_observation(
                Observation(
                    id=identifier,
                    type=ObservationType.HORIZONTAL_DISTANCE,
                    stations=names,
                    values=(Quantity.from_std_dev(value, sigma, Unit.METRE),),
                )
            )
        elif len(tokens) == 7:
            valued += 1
            identifier = f"a{angles}"
            degrees = _number(tokens[3], what="degrees", line=row, path=path)
            minutes = _number(tokens[4], what="minutes", line=row, path=path)
            seconds = _number(tokens[5], what="seconds", line=row, path=path)
            sigma = _number(tokens[6], what="angle sigma", line=row, path=path)
            if not 0 <= minutes < 60 or not 0 <= seconds < 60:
                raise DataError(
                    "adjust_angle_out_of_range",
                    path=str(path),
                    line=row[:120],
                    received=[minutes, seconds],
                    expected="minutes and seconds below 60",
                )
            network.add_observation(
                Observation(
                    id=identifier,
                    type=ObservationType.HORIZONTAL_ANGLE,
                    # The file names the backsight first; the observation
                    # equation takes the occupied station first
                    # (``equations._horizontal_angle``). Passing the row's order
                    # through unchanged computes the angle at the backsight,
                    # which is a different angle and a converging adjustment.
                    stations=(names[1], names[0], names[2]),
                    values=(
                        Quantity.from_std_dev(
                            math.radians(degrees + minutes / 60.0 + seconds / 3600.0),
                            math.radians(sigma / 3600.0),
                            Unit.RADIAN,
                        ),
                    ),
                )
            )

    if valued not in (0, len(rows)):
        raise DataError(
            "adjust_file_half_valued",
            path=str(path),
            received=valued,
            expected=(
                f"either every one of the {len(rows)} observation rows carrying a "
                "value, or none of them; a file that mixes the two is neither a "
                "plan nor a set of measurements"
            ),
        )

    found = (distances, angles, 0)
    declared = (n_dist, n_ang, n_azi)
    if found != declared and not accept_count_mismatch:
        raise DataError(
            "adjust_declared_counts_disagree",
            path=str(path),
            declared={"distances": n_dist, "angles": n_ang, "azimuths": n_azi},
            found={"distances": distances, "angles": angles, "azimuths": 0},
            expected=(
                "a header whose counts match the rows below it. The counts are "
                "this format's own check, so a disagreement means the file "
                "cannot say which reading was intended; pass "
                "accept_count_mismatch to read the rows that are actually there"
            ),
        )

    return AdjustReport(
        network=network,
        title=title,
        has_values=bool(valued),
        declared=declared,
        found=found,
        plan=tuple(plan),
        control=tuple(control),
    )


def _dms(radians: float) -> tuple[int, int, float]:
    """Degrees, minutes and seconds, carrying properly at both boundaries."""
    total = math.degrees(radians) % 360.0
    degrees = int(total)
    minutes_float = (total - degrees) * 60.0
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60.0
    # Rounding the seconds to the printed precision can carry into the minutes,
    # and the minutes into the degrees. Doing it here rather than in the format
    # string is what keeps 59.9999 from being written as 60 (specs/07 §5.5 is
    # the same defect, in DynAdjust's printer).
    if round(seconds, 2) >= 60.0:
        seconds, minutes = 0.0, minutes + 1
    if minutes >= 60:
        minutes, degrees = 0, degrees + 1
    return degrees % 360, minutes, seconds


def write_adjust(network: Network, path: str | Path, *, title: str = "") -> Path:
    """Write *network* as an *Adjust* file (FR-161's other half).

    Only what the format can hold: a plane network of horizontal distances and
    horizontal angles over weighted or free control. Anything else is refused by
    name rather than dropped -- a network written without its zenith angles is a
    different network, and the file gives no sign of it.
    """
    path = Path(path)
    stations = list(network.stations.values())
    control = [s for s in stations if not s.constraint.is_free]
    free = [s for s in stations if s.constraint.is_free]

    distances = [
        o for o in network.active_observations
        if o.type is ObservationType.HORIZONTAL_DISTANCE
    ]
    angles = [
        o for o in network.active_observations
        if o.type is ObservationType.HORIZONTAL_ANGLE
    ]
    written = {o.id for o in distances} | {o.id for o in angles}
    refused = sorted(
        {o.type.value for o in network.active_observations if o.id not in written}
    )
    if refused:
        raise DataError(
            "adjust_cannot_express_observation",
            path=str(path),
            received=refused,
            expected=(
                "a plane network of horizontal distances and horizontal angles; "
                "the Adjust format has no row for the other types, and writing "
                "the file without them would export a different network"
            ),
        )

    lines = [title or network.id, f"{len(distances)} {len(angles)} 0 {len(control)} {len(stations)}"]
    for station in control + free:
        east, north = (q.value for q in station.approx_position.values[:2])
        row = f"{station.id} {east:.4f} {north:.4f}"
        if station in control:
            sigmas = station.constraint.covariance
            if sigmas is None:
                raise DataError(
                    "adjust_control_without_covariance",
                    path=str(path),
                    station=station.id,
                    expected=(
                        "a weighted constraint carrying its covariance; the "
                        "format states a control station's two standard "
                        "deviations and has nowhere to say 'held exactly'"
                    ),
                )
            deviations = sigmas.std_devs()
            row += " " + " ".join(f"{deviations[label]:.3f}" for label in sigmas.labels[:2])
        lines.append(row)

    for observation in distances:
        quantity = observation.value
        lines.append(
            f"{observation.stations[0]} {observation.stations[1]} "
            f"{quantity.value:.3f} {quantity.std_dev:.3f}"
        )
    for observation in angles:
        at, backsight, foresight = observation.stations
        quantity = observation.value
        degrees, minutes, seconds = _dms(quantity.value)
        lines.append(
            f"{backsight} {at} {foresight} {degrees} {minutes:02d} {seconds:05.2f} "
            f"{math.degrees(quantity.std_dev) * 3600.0:.1f}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
