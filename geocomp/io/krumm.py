# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading the *Krumm format* of published network-adjustment examples.

``specs/22-reference-data-sources.md`` section 2. Friedhelm Krumm's *Geodetic
Network Adjustment Examples* (Geodätisches Institut, Universität Stuttgart,
Rev. 3.5, 2020) collects 61 worked networks from the standard textbooks -- Ghilani,
Niemeier, Benning, Wolf, Leick, Strang and Borre among them -- each in a small
line-oriented text format, and **45 of them are published together with their
adjusted coordinates**.

That is what this reader is for. GeoComp's own reference networks
(``specs/20`` section 3, RD-02 to RD-04) are validated but *uncited*: they were built
from the operations under test rather than transcribed from a book, so the
project cannot yet say it agrees with the standard references by name. These
files close that gap, and they do it for the terrestrial plane networks that
DynAdjust cannot take from GeoComp at all (``specs/07`` sections 4.2 and 4.4).

**The rules below come from GNU Gama's own converter**, ``lib/krumm/input.cpp``
at commit ``963c309``, not from reading the samples. Two of them are invisible
in a sample and would be got wrong by inspection:

* **A standard deviation persists until the next one is given.** A section's
  first row states a sigma and later rows omit it; every one of them carries the
  last value stated, not a default. Reading an omitted sigma as "missing" turns
  eight equally weighted angles into one weighted angle and seven with the
  fallback weight.
* **Units are declared in the section header, not by the values.** ``[Angles]``
  is gon and ``[Angles,dms,s]`` is degrees-minutes-seconds with the standard
  deviation in **seconds of arc**. The values look alike; ``50.001`` is a
  plausible reading in either.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.models import (
    Cluster,
    ClusterKind,
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

__all__ = ["KrummReport", "read_krumm"]

#: One gon is a four-hundredth of a turn. Krumm's default angular unit.
GON = math.tau / 400.0

#: Sigmas that apply when a section states none at all, from ``common.h``:
#: 10 cc for angles (a cc is a ten-thousandth of a gon), 1 mgon for directions,
#: 10 mm for levelled height differences.
DEFAULT_ANGLE_SIGMA = 10.0 * GON / 1e4
DEFAULT_DIRECTION_SIGMA = 0.0010 * GON
DEFAULT_HEIGHT_SIGMA = 0.010

#: ``D°M'S"``, as the ``,dms`` sections write angles. The minutes and seconds are
#: optional: ``240°0'0"`` and ``240°`` both occur.
_DMS = re.compile(
    r"^(?P<sign>[-+]?)\s*(?P<d>\d+(?:\.\d+)?)\s*°"
    r"(?:\s*(?P<m>\d+(?:\.\d+)?)\s*'"
    r"(?:\s*(?P<s>\d+(?:\.\d+)?)\s*\")?)?$"
)

#: Section headers this reader understands, mapped to a handler name and the
#: units the header declares. German synonyms are Krumm's own -- ``Quelle`` for
#: ``Source``, ``Winkel`` for ``Angles``.
SECTIONS: dict[str, tuple[str, str]] = {
    "[Project]": ("project", ""),
    "[Source]": ("source", ""),
    "[Quelle]": ("source", ""),
    "[Graphics]": ("ignore", ""),
    "[Coordinates]": ("coordinates", ""),
    "[Datum]": ("datum", ""),
    "[Sigma0]": ("sigma0", ""),
    "[Distances]": ("distance", "m"),
    "[HorizontalDistances]": ("horizontal_distance", "m"),
    "[SpatialDistances]": ("spatial_distance", "m"),
    "[Directions]": ("direction", "gon"),
    "[Direction]": ("direction", "gon"),
    "[Angles]": ("angle", "gon"),
    "[Angles,dms]": ("angle", "dms"),
    "[Angles,dms,s]": ("angle", "dms"),
    "[Winkel,dms,s]": ("angle", "dms"),
    "[Azimuth]": ("azimuth", "gon"),
    "[Azimuth,dms]": ("azimuth", "dms"),
    "[GridBearings,dms,s]": ("azimuth", "dms"),
    "[ZenithAngles]": ("zenith_angle", "gon"),
    "[VerticalAngles]": ("vertical_angle", "gon"),
    "[LevelledHeightDifferences]": ("levelled_height", "m"),
    "[TrigonometricHeightDifferences]": ("trigonometric_height", "m"),
    # Starting values, not observations. GNU Gama seeds a direction set's
    # orientation from ``[ApproximateOrientation]``; GeoComp estimates the same
    # quantity from the approximate coordinates
    # (``least_squares._initial_orientations``), so the section is information
    # the adjustment already has. Scale and additive constant are for models
    # this reader does not build.
    "[ApproximateOrientation]": ("ignore", ""),
    "[ApproximateScale]": ("ignore", ""),
    "[ApproximateAdditiveConstant]": ("ignore", ""),
}

#: Sections that describe something GeoComp cannot represent, each refused by
#: name rather than skipped. A network read with an observation quietly dropped
#: is a different network, adjusted without anybody saying so.
UNSUPPORTED = {
    "[Ellipsoid,dms]": "an ellipsoidal network; GeoComp has no geodetic reductions yet",
    "[Coordinates,Bdms,Ldms]": "geodetic coordinates; GeoComp has no geodetic reductions yet",
    "[3DBaseline]": "a GNSS baseline with a covariance this format states differently",
    "[3DBasislinie]": "a GNSS baseline with a covariance this format states differently",
    "[CorrelatedDistances]": "distances with a full covariance matrix",
    "[Restrictions]": "constraints between parameters, which the adjustment core does not take",
    "[PositionAngles]": "position angles, which GNU Gama's own converter also leaves out",
}


@dataclass
class KrummReport:
    """A network, and what the file said about where it came from.

    Attributes:
        source: The ``[Source]`` block verbatim -- the textbook, edition and
            page. This is the citation the whole exercise is for, so it travels
            with the network rather than being left in the file.
        sigma0: The a priori standard deviation of unit weight, when stated.
        title: The ``[Project]`` line.
    """

    network: Network
    title: str = ""
    source: str = ""
    sigma0: float | None = None
    #: Sections seen and understood, in order, for a caller that wants to know
    #: what a file actually exercised.
    sections: tuple[str, ...] = ()
    #: 1, 2 or 3: the smallest adjustment dimensionality every observation in
    #: the file is valid in, so a caller can pick the frame without guessing.
    dimension: int = 2
    #: True when ``[Datum]`` says ``free``. The file is then stating that it
    #: wants a free-network solution, and adjusting it with a fixed datum -- the
    #: default -- makes the normal matrix singular rather than wrong, which is
    #: at least loud. The caller still chooses; the reader only reports.
    free: bool = False
    #: The stations a free network's datum is defined on, when the file names
    #: fewer than all of them. ``AdjustmentOptions.datum_stations`` takes it
    #: verbatim. This is not a detail: ``LotherStrehle_Direction4`` is
    #: ``LotherStrehle_Direction3`` with one station left out of the datum, and
    #: the two published answers differ by 3.6 mm.
    datum_stations: tuple[str, ...] | None = None


@dataclass
class _State:
    """The sticky standard deviations, one per section kind."""

    sigmas: dict[str, float] = field(default_factory=dict)
    counter: int = 0

    def identifier(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}{self.counter}"


def parse_angle(text: str, units: str, *, line: str) -> float:
    """One angular value, in whichever unit its section declared, to radians."""
    if units == "dms":
        match = _DMS.match(text.strip())
        if not match:
            raise DataError(
                "krumm_angle_unreadable",
                received=text,
                expected="degrees, minutes and seconds as D°M'S\"",
                line=line.strip()[:120],
            )
        degrees = float(match.group("d"))
        minutes = float(match.group("m") or 0.0)
        seconds = float(match.group("s") or 0.0)
        value = math.radians(degrees + minutes / 60.0 + seconds / 3600.0)
        return -value if match.group("sign") == "-" else value
    return _number(text, line=line) * GON


#: Trailing unit symbols a value or sigma may carry -- ``10"`` for ten seconds.
_UNIT_SUFFIX = re.compile(r"[\"\'°]+$|\s*(?:gon|mgon|cc|m|mm|cm)$")


def _number(text: str, *, line: str) -> float:
    text = _UNIT_SUFFIX.sub("", text.strip())
    try:
        return float(text)
    except ValueError as error:
        raise DataError(
            "krumm_value_not_a_number", received=text, line=line.strip()[:120]
        ) from error


#: A comment marker at the start of a token. ``%`` always is; ``#`` only when it
#: begins one, because a station name may contain one -- Leick's ``Six#Mile``.
_COMMENT = re.compile(r"(?:^|(?<=\s))[%#]")


def _strip_comment(line: str) -> str:
    """Everything before the first comment marker.

    ``#`` needs the token-initial rule. It introduces a comment in some files
    and sits inside a station name in others (``Six#Mile``), and treating it as
    a comment everywhere silently truncates those names to ``Six``.
    """
    match = _COMMENT.search(line)
    return (line[: match.start()] if match else line).rstrip()


def read_krumm(path: str | Path, *, network_id: str = "") -> KrummReport:
    """Read one network in Krumm format.

    The result is an ordinary :class:`~geocomp.core.models.Network` with a
    projected frame, so it goes straight into the adjustment core with nothing
    in between -- which is the point: these networks are plane, and the core
    works in a plane.

    Args:
        path: The ``.dat`` file.
        network_id: Defaults to the file's stem, which is how the examples are
            named after their source (``Ghilani14_5_Distance_fix``).
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    network = Network(id=network_id or path.stem, crs="LOCAL")
    report = KrummReport(network=network)

    state = _State()
    handler, units = "", ""
    seen: list[str] = []
    project: list[str] = []
    source: list[str] = []
    datum: list[str] = []
    heights: dict[str, float] = {}

    for raw in text.splitlines():
        line = _strip_comment(raw)
        stripped = line.strip()

        if stripped.startswith("["):
            header = stripped.split()[0] if " " in stripped else stripped
            if header in UNSUPPORTED:
                raise DataError(
                    "krumm_section_unsupported",
                    section=header,
                    reason=UNSUPPORTED[header],
                    path=str(path),
                    hint=(
                        "the network is not read at all rather than read without it: "
                        "an example missing one of its observations is a different "
                        "example, and would compare against the published answer for "
                        "a network nobody adjusted"
                    ),
                )
            if header not in SECTIONS:
                raise DataError(
                    "krumm_section_unknown",
                    section=header,
                    path=str(path),
                    known=sorted(SECTIONS)[:8],
                )
            handler, units = SECTIONS[header]
            if handler not in {"ignore", "project", "source"}:
                seen.append(header)
            continue

        if not stripped or not handler:
            continue

        if handler == "ignore":
            continue
        if handler == "project":
            project.append(stripped)
        elif handler == "source":
            source.append(stripped)
        elif handler == "sigma0":
            report.sigma0 = _number(stripped.split()[0], line=raw)
        elif handler == "datum":
            datum.extend(stripped.split())
        elif handler == "coordinates":
            _coordinate(network, heights, stripped)
        else:
            _observation(network, state, handler, units, stripped)

    _direction_sets(network)
    _require_known_stations(network, path=path)
    report.title = " ".join(project)
    report.source = "\n".join(source)
    report.sections = tuple(seen)
    report.dimension = _dimension(network)
    report.free, report.datum_stations = _apply_datum(network, datum, path=path)
    return report


def _dimension(network: Network) -> int:
    """The smallest of 1D, 2D and 3D every observation is valid in.

    Not read from the file: nothing in the format declares it. A levelling
    network is three columns short of a 3D one and a plane network is one, but
    the *observations* say it exactly -- a height difference is not a 2D
    quantity and a slope distance is not a 1D one -- so the answer comes from
    them. Smallest wins because a plane network of distances is also valid in
    3D, and adjusting it there would leave every height undetermined.
    """
    observations = list(network.observations.values())
    if not observations:
        return 2
    for dimension in (1, 2, 3):
        if all(observation.supports_dimension(dimension) for observation in observations):
            return dimension
    raise DataError(
        "krumm_mixed_dimensionality",
        network=network.id,
        hint=(
            "no single adjustment dimensionality is valid for every observation "
            "in the file"
        ),
    )


def _require_known_stations(network: Network, *, path: Path) -> None:
    """Refuse a file whose observations reach a station ``[Coordinates]`` omits.

    Krumm's traverses do this deliberately: ``Krumm_Traverse1`` gives an azimuth
    from B to a point A that has no coordinates anywhere, and expects the reader
    to understand that the azimuth to A and an angle turned from A together
    define an azimuth to C. That is a reduction, not a network, and GNU Gama
    excludes the same three files from its own suite for the same reason
    (``tests/krumm/CMakeLists.txt``). Saying so here beats letting the
    adjustment fail on a missing parameter column.
    """
    missing: dict[str, list[str]] = {}
    for observation in network.observations.values():
        for station_id in observation.stations:
            if station_id not in network.stations:
                missing.setdefault(station_id, []).append(observation.id)
    if not missing:
        return
    raise DataError(
        "krumm_observation_station_unknown",
        path=str(path),
        received=sorted(missing),
        expected="every observed station to appear in [Coordinates]",
        hint=(
            "an azimuth or angle to a point with no approximate coordinates "
            "defines a direction, not a position; it has to be reduced before "
            "the network can be adjusted"
        ),
    )


def _direction_sets(network: Network) -> None:
    """Gather the directions of each setup into one cluster (FR-104).

    The covariance is diagonal. That is the model these examples state -- each
    direction carries its own standard deviation and nothing correlates them --
    and it is not a simplification GeoComp is making: what couples a set is the
    orientation unknown, which the adjustment estimates rather than the
    stochastic model expressing.
    """
    sets: dict[str, list[Observation]] = {}
    for observation in network.observations.values():
        if observation.type is ObservationType.DIRECTION and observation.cluster_id:
            sets.setdefault(observation.cluster_id, []).append(observation)

    for cluster_id, members in sets.items():
        network.add_cluster(
            Cluster(
                id=cluster_id,
                kind=ClusterKind.DIRECTION_SET,
                observation_ids=tuple(member.id for member in members),
                covariance=Covariance(
                    matrix=np.diag([member.values[0].variance for member in members]),
                    labels=tuple(member.id for member in members),
                    units=(Unit.RADIAN,) * len(members),
                ),
            )
        )


def _coordinate(network: Network, heights: dict[str, float], line: str) -> None:
    """One approximate-coordinate row: ``name x y [H]``.

    **``x`` is the easting and ``y`` the northing.** That is what GNU Gama's
    converter declares for every one of these files -- it emits
    ``axes-xy="en"``, meaning the first axis points east -- and it is worth
    stating because the opposite convention is at least as common in the
    literature this data comes from. For a network of distances and angles it
    changes nothing; for an azimuth it changes everything.
    """
    tokens = line.split()
    if len(tokens) < 2:
        raise DataError("krumm_coordinate_row_too_short", line=line[:120])
    name = tokens[0]
    values = [float(token) for token in tokens[1:]]
    if len(values) == 1:
        # A 1D network states only a height.
        easting = northing = 0.0
        height = values[0]
    else:
        easting, northing = values[0], values[1]
        height = values[2] if len(values) > 2 else 0.0
    heights[name] = height

    network.stations[name] = Station(
        id=name,
        approx_position=Position(
            values=(
                Quantity.exact(easting, Unit.METRE),
                Quantity.exact(northing, Unit.METRE),
                Quantity.exact(height, Unit.METRE),
            ),
            system=CoordinateSystem.PROJECTED,
            crs="LOCAL",
            height_type=HeightType.ORTHOMETRIC if len(values) != 2 else HeightType.NONE,
        ),
    )


def _sticky(state: _State, kind: str, tokens: list[str], index: int, default: float,
            convert) -> float:
    """The row's standard deviation, or the last one this section stated.

    The persistence is the whole reason this helper exists. ``input.cpp`` keeps
    one sigma per section and overwrites it only when a row supplies one, so a
    section whose first row says ``2.1`` gives 2.1 to every row after it.
    """
    if len(tokens) > index and tokens[index]:
        state.sigmas[kind] = convert(tokens[index])
    return state.sigmas.get(kind, default)


def _observation(
    network: Network,
    state: _State,
    handler: str,
    units: str,
    line: str,
) -> None:
    tokens = line.split()
    angle = lambda text: parse_angle(text, units, line=line)  # noqa: E731
    metres = lambda text: _number(text, line=line)  # noqa: E731

    if handler in {"distance", "horizontal_distance"}:
        # from to value [sigma_c [sigma_s]] -- the distance-dependent term is
        # read but not used: GeoComp's stochastic model states it per
        # instrument profile rather than per observation.
        _require(tokens, 3, handler, line)
        sigma = _sticky(state, handler, tokens, 3, 0.010, metres)
        _add(network, state, ObservationType.HORIZONTAL_DISTANCE, tokens[:2],
             metres(tokens[2]), sigma, Unit.METRE, "d")
    elif handler == "spatial_distance":
        _require(tokens, 3, handler, line)
        _refuse_setup_heights(tokens, handler, line)
        sigma = _sticky(state, handler, tokens, 3, 0.010, metres)
        _add(network, state, ObservationType.SLOPE_DISTANCE, tokens[:2],
             metres(tokens[2]), sigma, Unit.METRE, "s")
    elif handler == "direction":
        _require(tokens, 3, handler, line)
        sigma = _sticky(state, handler, tokens, 3, DEFAULT_DIRECTION_SIGMA,
                        lambda t: _number(t, line=line) * GON)
        # A direction belongs to the set observed from its station, and that
        # gives it two ids, not one. The cluster keeps the set's rows together
        # so FR-104 has something to hold their correlation; the *setup* is what
        # the adjustment keys the orientation unknown on
        # (``least_squares._with_orientation_unknowns``). Without the setup id a
        # direction is read as an absolute azimuth, and the network solves --
        # to the wrong coordinates, by whatever the unmodelled orientation is.
        _add(network, state, ObservationType.DIRECTION, tokens[:2],
             angle(tokens[2]), sigma, Unit.RADIAN, "r",
             cluster_id=f"set:{tokens[0]}", setup_id=tokens[0])
    elif handler == "angle":
        # from backsight foresight value [sigma]
        _require(tokens, 4, handler, line)
        sigma = _sticky(state, handler, tokens, 4, DEFAULT_ANGLE_SIGMA,
                        _sigma_converter(units, line))
        _add(network, state, ObservationType.HORIZONTAL_ANGLE, tokens[:3],
             angle(tokens[3]), sigma, Unit.RADIAN, "a")
    elif handler == "azimuth":
        _require(tokens, 3, handler, line)
        sigma = _sticky(state, handler, tokens, 3, DEFAULT_ANGLE_SIGMA,
                        _sigma_converter(units, line))
        _add(network, state, ObservationType.AZIMUTH, tokens[:2],
             angle(tokens[2]), sigma, Unit.RADIAN, "b")
    elif handler == "zenith_angle":
        _require(tokens, 3, handler, line)
        _refuse_setup_heights(tokens, handler, line)
        sigma = _sticky(state, handler, tokens, 3, DEFAULT_ANGLE_SIGMA,
                        _sigma_converter(units, line))
        _add(network, state, ObservationType.ZENITH_ANGLE, tokens[:2],
             angle(tokens[2]), sigma, Unit.RADIAN, "z")
    elif handler == "vertical_angle":
        _require(tokens, 3, handler, line)
        sigma = _sticky(state, handler, tokens, 3, DEFAULT_ANGLE_SIGMA,
                        _sigma_converter(units, line))
        _add(network, state, ObservationType.VERTICAL_ANGLE, tokens[:2],
             angle(tokens[2]), sigma, Unit.RADIAN, "v")
    elif handler == "levelled_height":
        # from to value length [sigma]. The sigma column is **per kilometre**
        # and the length is in metres, so the line's own standard deviation is
        # sigma * sqrt(L / 1000) -- the classical levelling model, and the one
        # GNU Gama's converter applies (``input.cpp``, ``levelled_height_-
        # differences``). Taking the stated sigma as the line's would weight a
        # 1.2 km line and a 0.44 km line alike, which is not the model any of
        # these examples was adjusted under.
        _require(tokens, 4, handler, line)
        per_kilometre = _sticky(state, handler, tokens, 4, DEFAULT_HEIGHT_SIGMA, metres)
        length = metres(tokens[3])
        if length <= 0.0:
            raise DataError(
                "krumm_levelling_length_not_positive",
                received=tokens[3],
                expected="the levelled line length in metres, which weights the line",
            )
        _add(network, state, ObservationType.HEIGHT_DIFFERENCE, tokens[:2],
             metres(tokens[2]), per_kilometre * math.sqrt(length / 1000.0),
             Unit.METRE, "h")
    elif handler == "trigonometric_height":
        _require(tokens, 3, handler, line)
        sigma = _sticky(state, handler, tokens, 3, DEFAULT_HEIGHT_SIGMA, metres)
        _add(network, state, ObservationType.HEIGHT_DIFFERENCE, tokens[:2],
             metres(tokens[2]), sigma, Unit.METRE, "t")
    else:  # pragma: no cover - SECTIONS and this dispatch are written together
        raise DataError("krumm_handler_unimplemented", handler=handler)


def _refuse_setup_heights(tokens: list[str], handler: str, line: str) -> None:
    """Refuse a spatial distance or zenith angle measured instrument-to-target.

    ``from to value sigma instrument_height target_height`` is the six-column
    form (``input.cpp``, ``spatial_distances``). Those two heights are not a
    correction the reader can apply: the measurement runs from the instrument's
    trunnion axis to the reflector, and reducing it to the marks needs the
    coordinates the adjustment is solving for. GNU Gama carries them into the
    observation equation as ``from_dh`` and ``to_dh``; GeoComp's
    :class:`~geocomp.core.models.Observation` has nowhere to put them, so the
    file is refused rather than adjusted 7 mm out with no sign of it.
    """
    if len(tokens) <= 4:
        return
    raise DataError(
        "krumm_setup_heights_unsupported",
        section=handler,
        line=line[:120],
        received=tokens[4:6],
        expected=(
            "a row without instrument and target heights; reducing them to the "
            "marks is part of the observation equation, not of reading the file"
        ),
    )


def _sigma_converter(units: str, line: str):
    """How a section's sigma column reaches radians.

    ``,dms`` sections state the value in degrees-minutes-seconds and the
    **standard deviation in seconds of arc** -- the ``,s`` in the header says
    so. Plain sections state both in gon.

    Note for anyone comparing with GNU Gama: its converter passes a ``,dms``
    section's sigma through unchanged into a field whose unit is cc, where 1 cc
    is 0.324″. This reader follows the header instead.
    """
    if units == "dms":
        return lambda text: math.radians(_number(text, line=line) / 3600.0)
    return lambda text: _number(text, line=line) * GON


def _require(tokens: list[str], count: int, handler: str, line: str) -> None:
    if len(tokens) < count:
        raise DataError(
            "krumm_row_too_short",
            section=handler,
            expected=count,
            received=len(tokens),
            line=line[:120],
        )


def _add(
    network: Network,
    state: _State,
    observation_type: ObservationType,
    stations: list[str],
    value: float,
    sigma: float,
    unit: Unit,
    prefix: str,
    cluster_id: str | None = None,
    setup_id: str | None = None,
) -> None:
    identifier = state.identifier(prefix)
    network.observations[identifier] = Observation(
        id=identifier,
        type=observation_type,
        stations=tuple(stations),
        values=(Quantity(value, sigma**2, unit),),
        cluster_id=cluster_id,
        setup_id=setup_id,
    )


def _apply_datum(
    network: Network, tokens: list[str], *, path: Path
) -> tuple[bool, tuple[str, ...] | None]:
    """Turn the ``[Datum]`` line into per-station constraints.

    ``fix xA yA xB yB`` holds those components of those stations. ``free`` holds
    nothing, but the names that follow it are not decoration: they are the
    stations the free network's datum is defined on, and leaving one out moves
    the whole solution. A ``dyn`` datum -- a weighted one, given by a covariance
    matrix over several following lines -- is refused: DynAdjust cannot express
    a weighted constraint either (``specs/07`` section 4.3 rule 4), and holding
    loosely-weighted coordinates exactly would turn a stated uncertainty into an
    assertion of certainty.

    Returns:
        ``(free, datum_stations)``. *free* says the file asked for a free
        network, so the caller knows to solve it under inner constraints rather
        than discovering the datum defect as a singular normal matrix;
        *datum_stations* is the set those constraints are over, or ``None`` for
        all of them.
    """
    if not tokens:
        return False, None
    first = tokens[0].lower()
    if first == "dyn":
        raise DataError(
            "krumm_dynamic_datum_unsupported",
            path=str(path),
            hint=(
                "a dynamic datum weights the held coordinates by a covariance "
                "matrix; reading it as a fixed one would assert certainty the "
                "example does not claim"
            ),
        )
    if first not in {"fix", "free"}:
        raise DataError("krumm_datum_unknown", received=tokens[0], expected=["fix", "free"])

    components = _datum_components(network, tokens[1:])

    if first == "free":
        if not components:
            return True, None
        held = {frozenset(axes) for axes in components.values()}
        if len(held) != 1:
            raise DataError(
                "krumm_free_datum_partial",
                path=str(path),
                expected=(
                    "the same components named for every station in a free "
                    "datum; an inner constraint over some components of one "
                    "station and all of another is not a datum GeoComp forms"
                ),
                received=sorted(
                    f"{name}:{','.join(sorted(axes))}"
                    for name, axes in components.items()
                ),
            )
        return True, tuple(sorted(components))

    for station_id, axes in components.items():
        station = network.stations[station_id]
        network.stations[station_id] = Station(
            id=station.id,
            name=station.name,
            description=station.description,
            approx_position=station.approx_position,
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset(axes),
                position=station.approx_position,
            ),
            station_type=station.station_type,
        )

    return False, None


def _datum_components(network: Network, tokens: list[str]) -> dict[str, set[str]]:
    """``xA yA B`` to ``{"A": {easting, northing}, "B": {every component}}``."""
    names = {"x": "easting", "y": "northing", "z": "up", "h": "up"}
    components: dict[str, set[str]] = {}
    for token in tokens:
        # A bare station name means the whole station. A 1D network writes its
        # datum that way -- `fix 4 6 8` -- because a height network has one
        # component and no axis to name it by. Checked before the axis rule, so
        # a station actually called `x14` is not read as the x of station 14.
        if token in network.stations:
            components.setdefault(token, set()).update(names.values())
            continue
        axis, station = token[0].lower(), token[1:]
        if axis not in names or station not in network.stations:
            raise DataError(
                "krumm_datum_token_unreadable",
                received=token,
                expected="a station name, or an axis letter and a station name (xA)",
                known=sorted(network.stations)[:10],
            )
        components.setdefault(station, set()).add(names[axis])
    return components
