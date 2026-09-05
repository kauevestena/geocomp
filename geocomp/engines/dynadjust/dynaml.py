# SPDX-License-Identifier: GPL-2.0-or-later
"""Writing DynaML, DynAdjust's XML interchange format (FR-320, FR-163).

``specs/07-engine-dynadjust.md`` section 4 and
[`adr/0004-dynadjust-interchange-format.md`](../../../specs/adr/0004-dynadjust-interchange-format.md).
DynaML rather than DNA because DNA is column-oriented and unforgiving of a
one-character misalignment, while XML generation can be tested by reading the
result back.

**The single most important rule here is that clusters stay clusters** (FR-104,
``specs/07`` section 4.3 rule 1). A GNSS baseline is one measurement with a 3x3
covariance, written as a ``G`` with its ``SigmaXX``…``SigmaZZ``. Splitting it
into three independent scalars discards the correlation, and the adjustment then
reports an uncertainty that is wrong in a direction nobody checks -- too small.
The type registry marks these types ``always_clustered`` and this writer honours
it; the tests assert the covariance survives to full double precision.

**Station names are checked, and mapped when they must be.** DynAdjust's station
field is 20 characters (Guide Table B.3). A longer GeoComp identifier is
rewritten to a generated one, the mapping is recorded in the returned
:class:`DynaMLDocument`, and the readers reverse it -- so the user never sees a
renamed station (``specs/07`` section 4.3 rule 3). Truncating instead would be
the obvious shortcut and is how two distinct stations silently become one.

**Frame and epoch are always written, never inferred** (FR-105, rule 5). They
are attributes of the root element, so a file that reached DynAdjust without
them would be adjusted in whatever frame it defaults to, which is a datum shift
absorbed into the residuals.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.projection import (
    ProjectionParameters,
    inverse_transverse_mercator,
)
from geocomp.core.models import (
    Cluster,
    ConstraintMode,
    Network,
    Observation,
    ObservationType,
    Station,
)
from geocomp.core.models.observation import OBSERVATION_TYPES
from geocomp.core.models.position import CoordinateSystem, HeightType
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.formats import (
    format_metres,
    format_variance,
    radians_to_hp,
    radians_to_seconds,
)

__all__ = [
    "MAX_STATION_NAME",
    "DynaMLDocument",
    "station_names",
    "write_measurement_file",
    "write_station_file",
]

#: Guide Table B.3: the station name field is 20 characters wide in DNA, and
#: DynaML inherits the DNA field definitions.
MAX_STATION_NAME = 20

#: DynAdjust station coordinate types, by the system the position is actually
#: in. ``<Type>`` is a *declaration* about the three numbers beside it, so it
#: has to follow them rather than be chosen once.
#:
#: This was a single constant ``"XYZ"`` until it was tested with a network that
#: was not cartesian, and the reasoning recorded for it -- that GeoComp's frames
#: "are cartesian or projected already" -- contained the defect: a projected
#: easting is not a geocentric X. A UTM 22S station written as ``XYZ`` lands
#: 845 km above the Earth's surface, and DynAdjust accepts it. In a network of
#: absolute observations that goes unnoticed, because DynAdjust computes its own
#: approximates and discards the nonsense; in a relative network -- a traverse, a
#: levelling line -- the approximates set the datum, and the answer is wrong in a
#: way that looks fine.
COORD_TYPES = {
    CoordinateSystem.CARTESIAN: "XYZ",
    CoordinateSystem.GEODETIC: "LLH",
}

#: The ``<Coords>`` of a ``Y`` cluster, which is a different question: it
#: declares the frame of the *measurement's* components, and this writer always
#: emits those as cartesian X, Y and Z. Fixed on purpose, and named separately
#: so it cannot drift with the station type above.
CLUSTER_COORD_TYPE = "XYZ"

#: The per-component constraint string: three characters, each ``C``
#: (constrained) or ``F`` (free), as upstream's own sample stations use.
CONSTRAINED, FREE = "C", "F"


@dataclass
class DynaMLDocument:
    """What was written, and the decisions taken while writing it.

    Attributes:
        renamed: ``{geocomp id: dynadjust name}`` for every station whose
            identifier could not be represented. Empty in the ordinary case.
            Recorded rather than logged because the readers need it to reverse
            the mapping, and provenance needs it to explain the file.
        skipped: Observations DynAdjust has no measurement type for, with the
            reason. **Never silently dropped**: a gravity observation vanishing
            from an exported network is a difference in the adjustment that the
            user did not ask for and cannot see.
    """

    station_path: Path | None = None
    measurement_path: Path | None = None
    frame: str = ""
    epoch: str = ""
    renamed: dict[str, str] = field(default_factory=dict)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_file": str(self.station_path) if self.station_path else None,
            "measurement_file": str(self.measurement_path) if self.measurement_path else None,
            "reference_frame": self.frame,
            "epoch": self.epoch,
            "renamed_stations": dict(self.renamed),
            "skipped": [{"observation": o, "reason": r} for o, r in self.skipped],
            "measurement_counts": dict(self.counts),
        }


def station_names(network: Network) -> dict[str, str]:
    """Map every GeoComp station id to a DynAdjust-representable name.

    Identity for the ordinary case. A name too long, or one that collides with
    another after being shortened, gets a generated ``STN00001`` form -- never a
    truncation, because two stations truncated to the same 20 characters become
    one station and the adjustment silently changes shape.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    generated = 0

    for station_id in sorted(network.station_ids()):
        candidate = station_id.strip()
        if candidate and len(candidate) <= MAX_STATION_NAME and candidate not in used:
            mapping[station_id] = candidate
            used.add(candidate)
            continue
        while True:
            generated += 1
            candidate = f"STN{generated:05d}"
            if candidate not in used:
                break
        mapping[station_id] = candidate
        used.add(candidate)
    return mapping


def _root(kind: str, frame: str, epoch: str) -> ET.Element:
    return ET.Element(
        "DnaXmlFormat",
        {
            "type": kind,
            "referenceframe": frame,
            "epoch": epoch,
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "DynaML.xsd",
        },
    )


def _text(parent: ET.Element, tag: str, value: Any) -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = str(value)
    return element


def _constraints(station: Station) -> str:
    """The three-character constraint string for a station.

    ``specs/07`` section 4.3 rule 4: a constraint GeoComp cannot express exactly
    is a refusal, never an approximation. DynAdjust's per-component model is
    constrained-or-free; a **weighted** constraint has no equivalent, and
    writing it as ``C`` would hold exactly what the user asked to be held
    loosely -- turning a stated uncertainty into an assertion of certainty.
    """
    constraint = station.constraint
    if constraint.mode is ConstraintMode.FREE:
        return FREE * 3

    if constraint.mode is ConstraintMode.WEIGHTED:
        raise ValidationError(
            "dynadjust_cannot_express_weighted_constraint",
            station=station.id,
            expected=(
                "a fixed or free constraint. DynAdjust holds a station component "
                "exactly or not at all, so a weighted constraint cannot be written "
                "without changing what it means. Adjust it with the in-house core, "
                "which supports weighted constraints, or fix the station instead"
            ),
        )

    # The component names come from the constraining position's own coordinate
    # system, not from a fixed list: a cartesian position names them x, y, z
    # while a projected one names them easting, northing, up, and a hard-coded
    # triple silently reports every cartesian station as free.
    position = constraint.position
    names = (
        position.system.component_names
        if position is not None
        else ("easting", "northing", "up")
    )
    return "".join(
        CONSTRAINED if constraint.constrains(name) else FREE for name in names
    )


def write_station_file(
    network: Network,
    path: str | Path,
    *,
    frame: str,
    epoch: str,
    names: dict[str, str] | None = None,
    projection: ProjectionParameters | None = None,
    undulations: dict[str, float] | None = None,
) -> DynaMLDocument:
    """Write the DynaML station file for *network*.

    Args:
        projection: Required when the network's positions are **projected**, and
            meaningless otherwise. DynAdjust has no way to take a grid
            coordinate, so the stations are inverse-projected to geodetic and
            written ``LLH``; without this the writer refuses rather than putting
            an easting where a latitude belongs (``specs/07`` section 4.4).
        undulations: ``{station id: N}`` in metres, for a projected network
            whose heights are **orthometric**. DynaML's ``LLH`` height is *h*
            above the ellipsoid, and the difference is tens of metres in Brazil
            (FR-804).
    """
    if not frame or not epoch:
        raise ValidationError(
            "dynadjust_frame_or_epoch_missing",
            received={"frame": frame, "epoch": epoch},
            expected=(
                "an explicit reference frame and epoch. A DynAdjust run whose frame "
                "GeoComp inferred rather than knew is a datum shift absorbed into the "
                "residuals (FR-105)"
            ),
        )

    names = names or station_names(network)
    root = _root("Station File", frame, epoch)

    for station_id in sorted(network.station_ids()):
        station = network.stations[station_id]
        element = ET.SubElement(root, "DnaStation")
        _text(element, "Name", names[station_id])
        _text(element, "Constraints", _constraints(station))
        coord_type, first, second, height = _coordinates(station, projection, undulations)
        _text(element, "Type", coord_type)

        coord = ET.SubElement(element, "StationCoord")
        _text(coord, "Name", names[station_id])
        _text(coord, "XAxis", first)
        _text(coord, "YAxis", second)
        _text(coord, "Height", height)
        if station_id != names[station_id]:
            _text(element, "Description", station_id)

    path = Path(path)
    _write(root, path)
    return DynaMLDocument(
        station_path=path,
        frame=frame,
        epoch=epoch,
        renamed={k: v for k, v in names.items() if k != v},
    )


def _coordinates(
    station: Station,
    projection: ProjectionParameters | None = None,
    undulations: dict[str, float] | None = None,
) -> tuple[str, str, str]:
    """A station's ``<Type>`` and its three coordinate strings.

    The type follows the position, because ``<Type>`` is a declaration *about*
    the three numbers beside it. A geodetic position is written ``LLH`` with
    latitude and longitude in HP notation (Guide Table B.2), which is what
    upstream's own station files use and what
    :mod:`~geocomp.engines.dynadjust.read_dynaml` reads back.

    A **projected** position is inverse-projected to geodetic and written
    ``LLH`` -- but only when *projection* says which projection it is. That
    parameter is not a convenience: a projected position carries a CRS string,
    and deriving a zone and a hemisphere from a string needs a projection
    database GeoComp does not carry (``specs/07`` section 4.4). Without it the
    station is refused, because the alternative is writing the easting into
    ``XAxis`` under some other type, and a UTM 22S station so written sits
    845 km above the Earth -- which DynAdjust accepts without complaint.
    """
    position = station.approx_position or (
        station.constraint.position if station.constraint else None
    )
    if position is None:
        # Zeros, and cartesian: DynAdjust computes approximate coordinates for
        # stations that have none, and refusing here would reject networks it
        # can perfectly well adjust.
        return COORD_TYPES[CoordinateSystem.CARTESIAN], *(format_metres(0.0),) * 3

    if position.system is CoordinateSystem.PROJECTED:
        return _from_projected(station, position, projection, undulations)

    coord_type = COORD_TYPES[position.system]
    values = [quantity.value for quantity in position.values]
    if position.system is CoordinateSystem.GEODETIC:
        return coord_type, radians_to_hp(values[0]), radians_to_hp(values[1]), format_metres(values[2])
    return coord_type, *(format_metres(value) for value in values)


def _from_projected(
    station: Station,
    position,
    projection: ProjectionParameters | None,
    undulations: dict[str, float] | None,
) -> tuple[str, str, str]:
    """Inverse-project a grid coordinate into the ``LLH`` DynAdjust wants."""
    if projection is None:
        raise ValidationError(
            "dynadjust_cannot_write_projected_coordinates",
            station=station.id,
            received=position.system.value,
            crs=position.crs,
            expected="a geodetic or geocentric position, or a stated projection",
            hint=(
                "GeoComp can invert a Transverse Mercator projection now "
                "(core.geodesy.projection), but not derive which one a CRS "
                "string names -- that needs a projection database. Pass "
                "`projection=` to say, or the easting goes into XAxis and puts "
                "the station in the wrong place entirely"
            ),
        )

    easting, northing, up = (quantity.value for quantity in position.values)
    latitude, longitude = inverse_transverse_mercator(easting, northing, projection)

    height = _ellipsoidal_height(station, position, up, undulations)
    return (
        COORD_TYPES[CoordinateSystem.GEODETIC],
        radians_to_hp(latitude),
        radians_to_hp(longitude),
        format_metres(height),
    )


def _ellipsoidal_height(
    station: Station, position, up: float, undulations: dict[str, float] | None
) -> float:
    """``h``, which is what DynAdjust's ``LLH`` height means.

    An **orthometric** height is not it, and the difference is tens of metres in
    Brazil. Applying a geoid model is FR-804's business and needs a model this
    writer has not got, so an orthometric height without an undulation is
    refused by name rather than written as though it were ellipsoidal.
    """
    if position.height_type is HeightType.ELLIPSOIDAL:
        return up
    if position.height_type is HeightType.NONE:
        # A genuinely two-dimensional network. The height is not a height, and
        # the conversion does not use it, so zero says so honestly.
        return 0.0

    undulation = (undulations or {}).get(station.id)
    if undulation is None:
        raise ValidationError(
            "dynadjust_orthometric_height_needs_a_geoid_model",
            station=station.id,
            received=position.height_type.value,
            expected="an ellipsoidal height, or a geoid undulation for this station",
            hint=(
                "DynaML's LLH height is h above the ellipsoid. Writing H above "
                "the geoid there is an error of the undulation itself -- tens of "
                "metres in Brazil (FR-804)"
            ),
        )
    return up + undulation


def _approximate(station: Station) -> tuple[float, float, float]:
    """A station's approximate coordinates, or zeros for a station with none.

    Zeros rather than a refusal: DynAdjust computes approximate coordinates
    itself for stations that need them, and requiring GeoComp to supply them
    would refuse networks DynAdjust can perfectly well adjust.
    """
    position = station.approx_position or (
        station.constraint.position if station.constraint else None
    )
    if position is None:
        return (0.0, 0.0, 0.0)
    return tuple(q.value for q in position.values)  # type: ignore[return-value]


def write_measurement_file(
    network: Network,
    path: str | Path,
    *,
    frame: str,
    epoch: str,
    names: dict[str, str] | None = None,
) -> DynaMLDocument:
    """Write the DynaML measurement file for *network*.

    Clustered types are written once per cluster, with their covariance intact;
    everything else once per observation. An observation of a type DynAdjust
    does not have is **reported in** :attr:`DynaMLDocument.skipped`, not dropped.
    """
    names = names or station_names(network)
    root = _root("Measurement File", frame, epoch)
    document = DynaMLDocument(measurement_path=Path(path), frame=frame, epoch=epoch)
    document.renamed = {k: v for k, v in names.items() if k != v}

    written_ids: set[str] = set()
    counts: dict[str, int] = {}

    for cluster in network.clusters.values():
        members = [network.observations[o] for o in cluster.observation_ids if o in network.observations]
        if not members:
            continue
        code = _code_for(members[0], document)
        if code is None:
            written_ids.update(o.id for o in members)
            continue
        # The code the *cluster writer* used, not the registry's: a cluster of
        # several baselines is written as X and a single one as G, so counting
        # the registry code would report a file that does not exist.
        written = _write_cluster(root, cluster, members, names, frame, epoch)
        written_ids.update(o.id for o in members)
        for used in written:
            counts[used] = counts.get(used, 0) + 1

    for observation in network.active_observations:
        if observation.id in written_ids:
            continue
        code = _code_for(observation, document)
        if code is None:
            continue
        _write_measurement(root, observation, code, names, frame, epoch)
        counts[code] = counts.get(code, 0) + 1

    document.counts = counts
    _write(root, Path(path))
    return document


def _code_for(observation: Observation, document: DynaMLDocument) -> str | None:
    spec = OBSERVATION_TYPES[observation.type]
    if spec.dynadjust_code is None:
        document.skipped.append(
            (
                observation.id,
                f"DynAdjust has no measurement type for {observation.type.value}",
            )
        )
        return None
    return spec.dynadjust_code


def _stations(observation: Observation, names: dict[str, str]) -> list[str]:
    return [names.get(s, s) for s in observation.stations]


def _write_measurement(
    root: ET.Element,
    observation: Observation,
    code: str,
    names: dict[str, str],
    frame: str,
    epoch: str,
) -> None:
    element = ET.SubElement(root, "DnaMeasurement")
    _text(element, "Type", code)
    _text(element, "Ignore", "*" if not observation.is_active else "")

    stations = _stations(observation, names)
    for tag, index in (("First", 0), ("Second", 1), ("Third", 2)):
        if index < len(stations):
            _text(element, tag, stations[index])

    if observation.type is ObservationType.GNSS_BASELINE:
        _write_gnss_components(
            element, observation, "GPSBaseline", frame, epoch,
            block=_diagonal_block(observation),
        )
        return

    quantity = observation.values[0]
    if quantity.unit is Unit.RADIAN:
        _text(element, "Value", radians_to_hp(quantity.value))
        _text(element, "StdDev", radians_to_seconds(quantity.std_dev))
    else:
        _text(element, "Value", format_metres(quantity.value))
        _text(element, "StdDev", format_metres(quantity.std_dev))

    heights = observation.meta or {}
    if "instrument_height" in heights:
        _text(element, "InstHeight", format_metres(float(heights["instrument_height"])))
    if "target_height" in heights:
        _text(element, "TargHeight", format_metres(float(heights["target_height"])))


def _write_gnss_components(
    element: ET.Element,
    observation: Observation,
    tag: str,
    frame: str,
    epoch: str,
    *,
    block: list[list[float]],
    cross: list[list[list[float]]] = (),
    header: bool = True,
) -> None:
    """One GNSS measurement, with its covariance whole (FR-104).

    ``block`` is this measurement's own 3x3 variance matrix, written as the
    upper triangle ``SigmaXX``…``SigmaZZ``. ``cross`` is its covariance with
    each *subsequent* member of the same cluster, written as the repeated
    ``GPSCovariance`` elements the schema allows -- so an X or Y cluster carries
    the whole block matrix and not merely its diagonal.

    This is rule 1 of ``specs/07`` section 4.3 and the one thing in this module
    that must not be got wrong. The correlation between the components of a
    baseline, and between baselines observed in the same session, is real; an
    adjustment given independent scalars instead reports an uncertainty that is
    wrong in the direction nobody checks, which is too small.
    """
    if header:
        _text(element, "ReferenceFrame", frame)
        _text(element, "Epoch", epoch)
        for scale in ("Vscale", "Pscale", "Lscale", "Hscale"):
            _text(element, scale, "1.000")

    node = ET.SubElement(element, tag)
    for name, quantity in zip(("X", "Y", "Z"), observation.values, strict=True):
        _text(node, name, format_metres(quantity.value))

    for row, column, name in (
        (0, 0, "SigmaXX"), (0, 1, "SigmaXY"), (0, 2, "SigmaXZ"),
        (1, 1, "SigmaYY"), (1, 2, "SigmaYZ"), (2, 2, "SigmaZZ"),
    ):
        _text(node, name, format_variance(float(block[row][column])))

    covariance_tag = "GPSCovariance" if tag == "GPSBaseline" else "PointCovariance"
    for other in cross:
        sub = ET.SubElement(node, covariance_tag)
        for row in range(3):
            for column in range(3):
                _text(sub, f"m{row + 1}{column + 1}", format_variance(float(other[row][column])))


def _diagonal_block(observation: Observation) -> list[list[float]]:
    """A 3x3 from the observation's own per-component variances.

    Used only when no cluster carries a covariance for it. The off-diagonals are
    zero, which states "uncorrelated" -- what the data actually says -- rather
    than inventing a correlation.
    """
    return [
        [observation.values[i].variance if i == j else 0.0 for j in range(3)]
        for i in range(3)
    ]


def _cluster_blocks(
    cluster: Cluster | None, members: list[Observation]
) -> tuple[list[list[list[float]]], dict[tuple[int, int], list[list[float]]]]:
    """Split a cluster's covariance into per-member and between-member blocks.

    The cluster's matrix is ``3n x 3n`` over its members in their stated order
    (``Cluster.observation_ids`` documents that the order *is* the covariance
    ordering), so member *i* owns rows ``3i…3i+2``.
    """
    if cluster is None:
        return [_diagonal_block(o) for o in members], {}

    matrix = cluster.covariance.matrix
    count = len(members)
    if matrix.shape[0] != 3 * count:
        raise ValidationError(
            "dynadjust_cluster_covariance_shape",
            cluster=cluster.id,
            received=list(matrix.shape),
            expected=f"{3 * count}x{3 * count} for {count} three-component members",
        )

    def sub(i: int, j: int) -> list[list[float]]:
        return [
            [float(matrix[3 * i + r][3 * j + c]) for c in range(3)] for r in range(3)
        ]

    own = [sub(i, i) for i in range(count)]
    between = {(i, j): sub(i, j) for i in range(count) for j in range(i + 1, count)}
    return own, between


def _write_cluster(
    root: ET.Element,
    cluster: Cluster,
    members: list[Observation],
    names: dict[str, str],
    frame: str,
    epoch: str,
) -> list[str]:
    """A clustered measurement: X (baseline cluster), Y (point cluster) or D.

    A single-member GNSS baseline cluster is written as ``G`` rather than ``X``.
    Both are correct and both carry the same 3x3; ``G`` is what upstream's own
    files use for the one-baseline case, so a GeoComp file put beside one of
    theirs is diffable, which is worth more than uniformity here.
    """
    first = members[0]
    if first.type is ObservationType.GNSS_BASELINE:
        own, between = _cluster_blocks(cluster, members)
        if len(members) == 1:
            element = ET.SubElement(root, "DnaMeasurement")
            _text(element, "Type", "G")
            _text(element, "Ignore", "*" if not first.is_active else "")
            stations = _stations(first, names)
            _text(element, "First", stations[0])
            _text(element, "Second", stations[1])
            _write_gnss_components(
                element, first, "GPSBaseline", frame, epoch, block=own[0]
            )
            return ["G"]
        _write_gnss_cluster(root, members, "X", names, frame, epoch, own, between)
        return ["X"]
    if first.type is ObservationType.GNSS_POINT:
        own, between = _cluster_blocks(cluster, members)
        _write_gnss_cluster(root, members, "Y", names, frame, epoch, own, between)
        return ["Y"]
    if first.type is ObservationType.DIRECTION:
        _write_direction_set(root, members, names)
        return ["D"]
    used = []
    for observation in members:
        code = OBSERVATION_TYPES[observation.type].dynadjust_code
        if code:
            _write_measurement(root, observation, code, names, frame, epoch)
            used.append(code)
    return used


def _write_gnss_cluster(
    root: ET.Element,
    members: list[Observation],
    code: str,
    names: dict[str, str],
    frame: str,
    epoch: str,
    own: list[list[list[float]]],
    between: dict[tuple[int, int], list[list[float]]],
) -> None:
    element = ET.SubElement(root, "DnaMeasurement")
    _text(element, "Type", code)
    _text(element, "Ignore", "")
    _text(element, "ReferenceFrame", frame)
    _text(element, "Epoch", epoch)
    for scale in ("Vscale", "Pscale", "Lscale", "Hscale"):
        _text(element, scale, "1.000")
    if code == "Y":
        _text(element, "Coords", CLUSTER_COORD_TYPE)
    _text(element, "Total", str(len(members)))

    block_tag = "GPSBaseline" if code == "X" else "Clusterpoint"
    for index, observation in enumerate(members):
        stations = _stations(observation, names)
        _text(element, "First", stations[0])
        if code == "X" and len(stations) > 1:
            _text(element, "Second", stations[1])
        cross = [between[(index, j)] for j in range(index + 1, len(members))]
        _write_gnss_components(
            element,
            observation,
            block_tag,
            frame,
            epoch,
            block=own[index],
            cross=cross,
            header=False,
        )


def _write_direction_set(
    root: ET.Element, members: list[Observation], names: dict[str, str]
) -> None:
    """A direction set: one header record, then a ``Directions`` per target.

    The first direction is the **reference** and the rest follow it, which is
    what the format means by a set (Guide B.1.4). Written as a set rather than
    as independent azimuths because a direction's orientation unknown is shared
    across the set, and splitting them would give each its own -- inventing
    parameters the survey does not have.
    """
    reference, *rest = members
    element = ET.SubElement(root, "DnaMeasurement")
    _text(element, "Type", "D")
    _text(element, "Ignore", "")

    stations = _stations(reference, names)
    _text(element, "First", stations[0])
    _text(element, "Second", stations[1])
    _text(element, "Value", radians_to_hp(reference.values[0].value))
    _text(element, "StdDev", radians_to_seconds(reference.values[0].std_dev))
    _text(element, "Total", str(len(rest)))

    for observation in rest:
        direction = ET.SubElement(element, "Directions")
        _text(direction, "Ignore", "")
        _text(direction, "Target", _stations(observation, names)[1])
        _text(direction, "Value", radians_to_hp(observation.values[0].value))
        _text(direction, "StdDev", radians_to_seconds(observation.values[0].std_dev))


def _write(root: ET.Element, path: Path) -> None:
    """Serialise, indented, with the XML declaration DynAdjust's files carry."""
    ET.indent(root, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
