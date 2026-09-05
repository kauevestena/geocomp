# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading DynaML into a GeoComp network (FR-163).

``specs/07-engine-dynadjust.md`` section 4.1: GeoComp reads DynAdjust's formats
so that a user with an existing project can open it, visualise it and inspect it
without converting anything by hand. That is worth having on its own, and it is
also what makes cross-validation possible on a network whose meaning both
engines already agree on -- rather than one GeoComp constructed and then
translated, where a disagreement could be the translation rather than the
mathematics.

**Reading is the inverse of writing, and shares its conventions module.** HP
notation, seconds-of-arc standard deviations and ``dd.mm.yyyy`` epochs all come
from :mod:`geocomp.engines.dynadjust.formats`, so a reader and a writer cannot
drift apart -- which they otherwise do, invisibly, until someone tests a round
trip.

**What cannot be represented is reported, not guessed.** DynAdjust's ``M``
(mean sea level arc) has no GeoComp counterpart, and a file containing one is
read with that measurement listed in :attr:`ReadReport.skipped` rather than
quietly turned into an ellipsoid distance -- which over a long line is a
metre-scale error in something the user never asked to have converted.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    ObservationStatus,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.formats import hp_to_radians, seconds_to_radians

__all__ = ["ReadReport", "read_dynaml", "read_measurement_file", "read_station_file"]

METRE, RADIAN = Unit.METRE, Unit.RADIAN

#: DynAdjust code to GeoComp observation type. The inverse of the registry's
#: ``dynadjust_code``, built by hand rather than inverted from it because the
#: mapping is not injective in that direction: ``C`` and ``E`` are both
#: ``ELLIPSOID_DISTANCE`` on the way out, and reading has to choose one.
BY_CODE: dict[str, ObservationType] = {
    "A": ObservationType.HORIZONTAL_ANGLE,
    "B": ObservationType.AZIMUTH,
    "C": ObservationType.ELLIPSOID_DISTANCE,
    "D": ObservationType.DIRECTION,
    "E": ObservationType.ELLIPSOID_DISTANCE,
    "G": ObservationType.GNSS_BASELINE,
    "H": ObservationType.ORTHOMETRIC_HEIGHT,
    "I": ObservationType.ASTRONOMIC_LATITUDE,
    "J": ObservationType.ASTRONOMIC_LONGITUDE,
    "K": ObservationType.ASTRONOMIC_AZIMUTH,
    "L": ObservationType.HEIGHT_DIFFERENCE,
    "P": ObservationType.GEODETIC_LATITUDE,
    "Q": ObservationType.GEODETIC_LONGITUDE,
    "R": ObservationType.ELLIPSOIDAL_HEIGHT,
    "S": ObservationType.SLOPE_DISTANCE,
    "V": ObservationType.ZENITH_ANGLE,
    "X": ObservationType.GNSS_BASELINE,
    "Y": ObservationType.GNSS_POINT,
    "Z": ObservationType.VERTICAL_ANGLE,
}

#: ``M`` is deliberately absent above. A mean-sea-level arc is reduced to a
#: surface GeoComp does not model; mapping it to ``ELLIPSOID_DISTANCE`` would be
#: a metre-scale error over a long line, silently applied.
UNMAPPED = {"M": "mean sea level arc distance: GeoComp models no MSL surface"}

#: Codes whose measurements are correlated and must be read as a cluster
#: (FR-104). Reading one of these as independent scalars would discard the
#: correlation that the file went to the trouble of carrying.
CLUSTERED = {"D", "X", "Y"}

_COORD_SYSTEMS = {
    "XYZ": CoordinateSystem.CARTESIAN,
    "LLH": CoordinateSystem.GEODETIC,
    "LLh": CoordinateSystem.GEODETIC,
    "UTM": CoordinateSystem.PROJECTED,
}


@dataclass
class ReadReport:
    """What was read, and what could not be.

    Attributes:
        skipped: ``(measurement description, reason)``. **Never empty for a
            file GeoComp could not fully represent**: FR-166 requires an import
            to report every bad record rather than stopping at the first, and a
            measurement silently absent from a network is a different network.
    """

    network: Network | None = None
    frame: str = ""
    epoch: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    skipped: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_frame": self.frame,
            "epoch": self.epoch,
            "measurement_counts": dict(self.counts),
            "skipped": [{"measurement": m, "reason": r} for m, r in self.skipped],
        }


def _root(path: str | Path, expected: str) -> ET.Element:
    path = Path(path)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise DataError(
            "dynaml_unreadable",
            path=str(path),
            reason=str(error),
            expected="a DynaML (DynAdjust XML) file",
        ) from error
    if root.tag != "DnaXmlFormat":
        raise DataError(
            "dynaml_wrong_root",
            path=str(path),
            received=root.tag,
            expected="a DnaXmlFormat root element",
        )
    kind = root.get("type", "")
    if expected not in kind and kind != "Combined File":
        raise DataError(
            "dynaml_wrong_file_type",
            path=str(path),
            received=kind,
            expected=f"a {expected} (or a Combined File)",
        )
    return root


def read_station_file(path: str | Path, *, crs: str = "", network: Network | None = None) -> ReadReport:
    """Read a DynaML station file into a network."""
    root = _root(path, "Station File")
    frame = root.get("referenceframe", "")
    epoch = root.get("epoch", "")
    network = network if network is not None else Network(id=Path(path).stem, crs=crs or frame)

    for element in root.findall("DnaStation"):
        name = (element.findtext("Name") or "").strip()
        if not name:
            continue
        coordinate_type = (element.findtext("Type") or "XYZ").strip()
        system = _COORD_SYSTEMS.get(coordinate_type)
        if system is None:
            raise DataError(
                "dynaml_unknown_coordinate_type",
                station=name,
                received=coordinate_type,
                expected=sorted(_COORD_SYSTEMS),
            )

        coord = element.find("StationCoord")
        position = _position(coord, system, crs or frame)
        constraints = (element.findtext("Constraints") or "FFF").strip().upper()
        network.add_station(
            Station(
                id=name,
                approx_position=position,
                constraint=_constraint(constraints, position, system),
                description=(element.findtext("Description") or "").strip(),
            )
        )

    return ReadReport(network=network, frame=frame, epoch=epoch)


def _position(coord: ET.Element | None, system: CoordinateSystem, crs: str) -> Position:
    if coord is None:
        raise DataError("dynaml_station_without_coordinates", expected="a StationCoord element")

    first = (coord.findtext("XAxis") or "0").strip()
    second = (coord.findtext("YAxis") or "0").strip()
    height = float((coord.findtext("Height") or "0").strip())

    if system is CoordinateSystem.GEODETIC:
        # Latitude and longitude arrive in HP notation (Guide Table B.2).
        values = (
            Quantity.exact(hp_to_radians(first), RADIAN),
            Quantity.exact(hp_to_radians(second), RADIAN),
            Quantity.exact(height, METRE),
        )
    else:
        values = (
            Quantity.exact(float(first), METRE),
            Quantity.exact(float(second), METRE),
            Quantity.exact(height, METRE),
        )

    return Position(
        values=values,
        system=system,
        crs=crs or "LOCAL",
        height_type=HeightType.ELLIPSOIDAL,
    )


def _constraint(constraints: str, position: Position, system: CoordinateSystem) -> ConstraintSpec:
    """A DNA constraint string to a :class:`ConstraintSpec`.

    ``FFF`` is free; anything with a ``C`` is fixed on those components. There
    is no weighted case to read, because DynAdjust has no way to express one --
    which is the same asymmetry the writer refuses in the other direction.
    """
    names = position.system.component_names
    held = frozenset(
        name for name, flag in zip(names, constraints.ljust(3, "F"), strict=False) if flag == "C"
    )
    if not held:
        return ConstraintSpec(mode=ConstraintMode.FREE)
    return ConstraintSpec(
        mode=ConstraintMode.FIXED,
        components=held,
        position=position,
    )


def read_measurement_file(
    path: str | Path, network: Network, *, report: ReadReport | None = None
) -> ReadReport:
    """Read a DynaML measurement file into an existing *network*."""
    root = _root(path, "Measurement File")
    report = report or ReadReport(network=network)
    report.frame = report.frame or root.get("referenceframe", "")
    report.epoch = report.epoch or root.get("epoch", "")

    for index, element in enumerate(root.findall("DnaMeasurement")):
        code = (element.findtext("Type") or "").strip().upper()
        label = f"{code or '?'}#{index}"

        if code in UNMAPPED:
            report.skipped.append((label, UNMAPPED[code]))
            continue
        observation_type = BY_CODE.get(code)
        if observation_type is None:
            report.skipped.append((label, f"unknown DynAdjust measurement type {code!r}"))
            continue

        if code in CLUSTERED or code == "G":
            _read_cluster(element, code, observation_type, network, index, report)
        else:
            _read_scalar(element, code, observation_type, network, index, report)
        report.counts[code] = report.counts.get(code, 0) + 1

    return report


def _status(element: ET.Element) -> ObservationStatus:
    flag = (element.findtext("Ignore") or "").strip()
    return ObservationStatus.EXCLUDED if flag == "*" else ObservationStatus.ACTIVE


def _stations(element: ET.Element) -> tuple[str, ...]:
    found = []
    for tag in ("First", "Second", "Third"):
        text = element.findtext(tag)
        if text and text.strip():
            found.append(text.strip())
    return tuple(found)


def _read_scalar(
    element: ET.Element,
    code: str,
    observation_type: ObservationType,
    network: Network,
    index: int,
    report: ReadReport,
) -> None:
    value_text = (element.findtext("Value") or "").strip()
    sigma_text = (element.findtext("StdDev") or "").strip()
    if not value_text or not sigma_text:
        report.skipped.append((f"{code}#{index}", "measurement has no Value or StdDev"))
        return

    angular = observation_type in _ANGULAR
    if angular:
        value = hp_to_radians(value_text)
        sigma = seconds_to_radians(sigma_text)
        unit = RADIAN
    else:
        value = float(value_text)
        sigma = float(sigma_text)
        unit = METRE

    meta: dict[str, Any] = {}
    for tag, key in (("InstHeight", "instrument_height"), ("TargHeight", "target_height")):
        text = element.findtext(tag)
        if text and text.strip():
            meta[key] = float(text)

    network.add_observation(
        Observation(
            id=f"{code}{index}",
            type=observation_type,
            stations=_stations(element),
            values=(Quantity.from_std_dev(value, sigma, unit),),
            status=_status(element),
            meta=meta,
        )
    )


#: Types whose value is an angle, and therefore arrives in HP notation with a
#: standard deviation in seconds of arc rather than in the value's own unit.
_ANGULAR = {
    ObservationType.HORIZONTAL_ANGLE,
    ObservationType.AZIMUTH,
    ObservationType.ASTRONOMIC_AZIMUTH,
    ObservationType.ZENITH_ANGLE,
    ObservationType.VERTICAL_ANGLE,
    ObservationType.DIRECTION,
    ObservationType.GEODETIC_LATITUDE,
    ObservationType.GEODETIC_LONGITUDE,
    ObservationType.ASTRONOMIC_LATITUDE,
    ObservationType.ASTRONOMIC_LONGITUDE,
}


def _read_cluster(
    element: ET.Element,
    code: str,
    observation_type: ObservationType,
    network: Network,
    index: int,
    report: ReadReport,
) -> None:
    """A G, X, Y or D measurement, with its correlation preserved (FR-104)."""
    if code == "D":
        _read_direction_set(element, network, index)
        return

    tag = "GPSBaseline" if code in {"G", "X"} else "Clusterpoint"
    blocks = element.findall(tag)
    if not blocks:
        report.skipped.append((f"{code}#{index}", f"no {tag} elements"))
        return

    # For X the station pair changes per member, so First/Second repeat; for G
    # and Y there is one header pair.
    firsts = [e.text.strip() for e in element.findall("First") if e.text]
    seconds = [e.text.strip() for e in element.findall("Second") if e.text]

    scale = _variance_scale(element, f"{code}#{index}")
    observations: list[Observation] = []
    own: list[np.ndarray] = []
    cross: dict[tuple[int, int], np.ndarray] = {}

    for position, block in enumerate(blocks):
        components = tuple(
            Quantity.exact(float((block.findtext(name) or "0").strip()), METRE)
            for name in ("X", "Y", "Z")
        )
        matrix = np.array(
            [
                [_sigma(block, "SigmaXX"), _sigma(block, "SigmaXY"), _sigma(block, "SigmaXZ")],
                [_sigma(block, "SigmaXY"), _sigma(block, "SigmaYY"), _sigma(block, "SigmaYZ")],
                [_sigma(block, "SigmaXZ"), _sigma(block, "SigmaYZ"), _sigma(block, "SigmaZZ")],
            ]
        ) * scale
        own.append(matrix)

        covariance_tag = "GPSCovariance" if tag == "GPSBaseline" else "PointCovariance"
        for offset, sub in enumerate(block.findall(covariance_tag), start=1):
            cross[(position, position + offset)] = (
                np.array(
                    [
                        [float(sub.findtext(f"m{r}{c}") or 0.0) for c in (1, 2, 3)]
                        for r in (1, 2, 3)
                    ]
                )
                * scale
            )

        origin = firsts[position] if position < len(firsts) else firsts[0]
        stations = (origin,)
        if code in {"G", "X"}:
            target = seconds[position] if position < len(seconds) else seconds[0]
            stations = (origin, target)

        values = tuple(
            Quantity.from_std_dev(q.value, float(np.sqrt(max(matrix[k][k], 0.0))), METRE)
            for k, q in enumerate(components)
        )
        observations.append(
            Observation(
                id=f"{code}{index}-{position}",
                type=observation_type,
                stations=stations,
                values=values,
                status=_status(element),
                cluster_id=f"{code}{index}",
                # Recorded so provenance can say the variances carry a scale
                # from the source file rather than being the raw observation's.
                meta={"dynadjust_v_scale": scale} if scale != 1.0 else {},
            )
        )

    for observation in observations:
        network.add_observation(observation)
    network.add_cluster(
        Cluster(
            id=f"{code}{index}",
            kind=ClusterKind.GNSS_BASELINE
            if code in {"G", "X"}
            else ClusterKind.GNSS_POINT,
            observation_ids=tuple(o.id for o in observations),
            covariance=_assemble(own, cross),
        )
    )


def _sigma(block: ET.Element, name: str) -> float:
    return float((block.findtext(name) or "0").strip())


def _variance_scale(element: ET.Element, label: str) -> float:
    """The V-scale multiplying this measurement's variance matrix (Table B.8).

    **Applied on read, not ignored.** A file may declare a baseline's covariance
    scaled by 10 or 100 -- upstream's own GNSS sample does, across eight
    distinct factors -- and a reader that drops the scalar hands the adjustment
    a weight the file never claimed. Ignoring a V-scale of 100 makes GeoComp
    trust that baseline a hundred times more than its author said to, which is
    not a formatting detail: it changes the solution, the residuals and every
    statistic computed from them. The imported network here reproduced
    DynAdjust's own sigma-zero only once this was applied.

    ``P``, ``L`` and ``H`` scale the north-south, east-west and vertical
    directions of the **local** frame, which means rotating the covariance into
    that frame, scaling, and rotating back. That is implementable but not
    verifiable against anything to hand -- upstream's samples use 1 throughout
    -- so a file using them is **refused** rather than read with the scaling
    quietly dropped.
    """
    for tag in ("Pscale", "Lscale", "Hscale"):
        text = (element.findtext(tag) or "1").strip()
        if text and abs(float(text) - 1.0) > 1e-12:
            raise DataError(
                "dynaml_directional_variance_scale_unsupported",
                measurement=label,
                received={tag: text},
                expected=(
                    "P-, L- and H-scale of 1. These scale single directions of the "
                    "local frame, which needs a rotation GeoComp cannot yet verify "
                    "against a reference; reading the file while dropping them would "
                    "silently change every weight it sets"
                ),
            )
    return float((element.findtext("Vscale") or "1").strip() or 1.0)


def _assemble(
    own: list[np.ndarray], cross: dict[tuple[int, int], np.ndarray]
) -> Covariance:
    """Build the full ``3n x 3n`` from the per-member and between-member blocks.

    The between-member blocks are written only above the diagonal, so the lower
    triangle is filled by transposition -- which is what makes the result
    symmetric, and what a reader that only filled the upper triangle would get
    wrong in a way ``Covariance`` would then refuse.
    """
    count = len(own)
    size = 3 * count
    matrix = np.zeros((size, size))
    for index, block in enumerate(own):
        matrix[3 * index : 3 * index + 3, 3 * index : 3 * index + 3] = block
    for (i, j), block in cross.items():
        matrix[3 * i : 3 * i + 3, 3 * j : 3 * j + 3] = block
        matrix[3 * j : 3 * j + 3, 3 * i : 3 * i + 3] = block.T

    labels = tuple(f"m{i}.{c}" for i in range(count) for c in ("x", "y", "z"))
    return Covariance(matrix=matrix, labels=labels, units=(METRE,) * size)


def _read_direction_set(element: ET.Element, network: Network, index: int) -> None:
    """A direction set: the header is the reference, then one per target."""
    origin = (element.findtext("First") or "").strip()
    reference_target = (element.findtext("Second") or "").strip()
    members: list[Observation] = []

    def add(position: int, target: str, value: str, sigma: str) -> None:
        members.append(
            Observation(
                id=f"D{index}-{position}",
                type=ObservationType.DIRECTION,
                stations=(origin, target),
                values=(
                    Quantity.from_std_dev(
                        hp_to_radians(value), seconds_to_radians(sigma), RADIAN
                    ),
                ),
                status=_status(element),
                cluster_id=f"D{index}",
            )
        )

    add(0, reference_target, element.findtext("Value") or "0", element.findtext("StdDev") or "1")
    for position, direction in enumerate(element.findall("Directions"), start=1):
        add(
            position,
            (direction.findtext("Target") or "").strip(),
            direction.findtext("Value") or "0",
            direction.findtext("StdDev") or "1",
        )

    for observation in members:
        network.add_observation(observation)
    size = len(members)
    network.add_cluster(
        Cluster(
            id=f"D{index}",
            kind=ClusterKind.DIRECTION_SET,
            observation_ids=tuple(o.id for o in members),
            covariance=Covariance(
                matrix=np.diag([o.values[0].variance for o in members]),
                labels=tuple(o.id for o in members),
                units=(RADIAN,) * size,
            ),
        )
    )


def read_dynaml(
    station_path: str | Path,
    measurement_path: str | Path | None = None,
    *,
    network_id: str = "",
    crs: str = "",
) -> ReadReport:
    """Read a DynAdjust project's DynaML files into one network."""
    report = read_station_file(station_path, crs=crs)
    if report.network is not None and network_id:
        report.network.id = network_id
    if measurement_path is not None and report.network is not None:
        read_measurement_file(measurement_path, report.network, report=report)
    return report
