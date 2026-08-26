# SPDX-License-Identifier: GPL-2.0-or-later
"""Datum definition: what the observations leave undetermined, and how to fix it.

``specs/06-adjustment-core.md`` section 3.

A network of *relative* observations determines shape but not position: height
differences fix no height, distances and angles fix no origin or orientation.
The undetermined directions are the **datum defect**, and how they are removed
changes the answer.

Getting this wrong is the classic way to produce a beautiful adjustment of the
wrong thing, so GeoComp computes the defect from the observation content rather
than assuming it, and records both the defect and its removal on the solution.

Inner constraints matter specifically for monitoring (FR-835). If the datum is
defined by holding a station that has itself moved, that station's motion is
redistributed across the whole network and appears as *everything else* moving
-- the opposite of the truth, arrived at confidently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from geocomp.core.adjustment.parameters import Frame, ParameterLayout
from geocomp.core.errors import ValidationError
from geocomp.core.models import Observation, ObservationType

__all__ = [
    "DatumDefect",
    "DefectComponent",
    "constraint_matrix",
    "detect_defect",
]


class DefectComponent(Enum):
    """One degree of freedom a network of relative observations leaves free."""

    TRANSLATION_E = "translation_e"
    TRANSLATION_N = "translation_n"
    TRANSLATION_U = "translation_u"
    #: Rotation about the vertical, the only one a 2D network can have.
    ROTATION_U = "rotation_u"
    ROTATION_E = "rotation_e"
    ROTATION_N = "rotation_n"
    SCALE = "scale"


#: Which components each observation type *removes* from the defect. An entry
#: absent from this table removes nothing, which is the correct default: a
#: relative observation constrains shape, not placement.
_FIXES: dict[ObservationType, set[DefectComponent]] = {
    # Distances fix scale but nothing else.
    ObservationType.HORIZONTAL_DISTANCE: {DefectComponent.SCALE},
    ObservationType.SLOPE_DISTANCE: {DefectComponent.SCALE},
    ObservationType.ELLIPSOID_DISTANCE: {DefectComponent.SCALE},
    # An azimuth fixes orientation about the vertical.
    ObservationType.AZIMUTH: {DefectComponent.ROTATION_U},
    ObservationType.ASTRONOMIC_AZIMUTH: {DefectComponent.ROTATION_U},
    # A height observed directly fixes the vertical translation.
    ObservationType.ORTHOMETRIC_HEIGHT: {DefectComponent.TRANSLATION_U},
    ObservationType.ELLIPSOIDAL_HEIGHT: {DefectComponent.TRANSLATION_U},
    # A GNSS baseline is a vector in a defined frame: scale and all rotations.
    ObservationType.GNSS_BASELINE: {
        DefectComponent.SCALE,
        DefectComponent.ROTATION_U,
        DefectComponent.ROTATION_E,
        DefectComponent.ROTATION_N,
    },
    # An absolute position fixes everything.
    ObservationType.GNSS_POINT: set(DefectComponent),
    ObservationType.GEODETIC_LATITUDE: set(DefectComponent),
    ObservationType.GEODETIC_LONGITUDE: set(DefectComponent),
    # Absolute gravity fixes the gravity datum.
    ObservationType.GRAVITY: {DefectComponent.TRANSLATION_U},
}

#: The components that exist at all, per frame.
_POSSIBLE: dict[Frame, tuple[DefectComponent, ...]] = {
    Frame.HEIGHT_1D: (DefectComponent.TRANSLATION_U,),
    Frame.GRAVITY_1D: (DefectComponent.TRANSLATION_U,),
    Frame.PLANE_2D: (
        DefectComponent.TRANSLATION_E,
        DefectComponent.TRANSLATION_N,
        DefectComponent.ROTATION_U,
        DefectComponent.SCALE,
    ),
    Frame.SPACE_3D: (
        DefectComponent.TRANSLATION_E,
        DefectComponent.TRANSLATION_N,
        DefectComponent.TRANSLATION_U,
        DefectComponent.ROTATION_E,
        DefectComponent.ROTATION_N,
        DefectComponent.ROTATION_U,
        DefectComponent.SCALE,
    ),
}


@dataclass(frozen=True)
class DatumDefect:
    """What the observations leave undetermined."""

    frame: Frame
    components: tuple[DefectComponent, ...]

    @property
    def size(self) -> int:
        return len(self.components)

    def describe(self) -> str:
        if not self.components:
            return "none: the observations determine the datum"
        names = ", ".join(component.value for component in self.components)
        return f"{self.size} ({names})"


def detect_defect(observations: list[Observation], frame: Frame) -> DatumDefect:
    """Compute the datum defect from the observation content (``specs/06`` section 3).

    A 2D network of angles and distances has defect 4 -- two translations, one
    rotation, one scale -- and 3 once a distance fixes scale. Computing it
    rather than assuming it is what lets the result state how the datum was
    removed.
    """
    possible = set(_POSSIBLE[frame])
    for observation in observations:
        possible -= _FIXES.get(observation.type, set())
    ordered = [component for component in _POSSIBLE[frame] if component in possible]
    return DatumDefect(frame=frame, components=tuple(ordered))


def constraint_matrix(
    layout: ParameterLayout,
    approximate: dict[str, dict[str, float]],
    defect: DatumDefect,
    *,
    station_ids: list[str] | None = None,
) -> np.ndarray:
    """Build the **G** matrix for an inner- or minimum-constraint solution.

    The columns span the undetermined directions; the bordered normal system
    then imposes ``G^T x = 0``, which is the trace-minimum condition: the
    solution closest to the approximate coordinates in a least-squares sense,
    with no station privileged.

    Args:
        layout: Supplies the column of each unknown.
        approximate: Current coordinates, ``{station: {component: value}}``.
        defect: Which directions to constrain.
        station_ids: The stations defining the datum. Defaults to every station
            with a column. **For deformation analysis this is the stable
            reference block** (FR-835), which is the whole reason it is a
            parameter rather than always "all of them".

    Coordinates are reduced to their centroid before forming the rotation and
    scale columns: without that the columns are dominated by the coordinate
    origin, which in a projected system can be hundreds of kilometres away and
    ruins the conditioning of the bordered system.
    """
    if defect.size == 0:
        return np.zeros((layout.size, 0))

    stations = station_ids if station_ids is not None else layout.station_ids()
    stations = [s for s in stations if layout.station_columns(s)]
    if not stations:
        raise ValidationError(
            "no_stations_for_datum",
            expected="at least one estimated station to define the datum on",
        )

    centroid = {
        component: float(np.mean([approximate[s][component] for s in stations]))
        for component in layout.frame.components
    }

    columns: list[np.ndarray] = []
    for component in defect.components:
        column = np.zeros(layout.size)
        for station_id in stations:
            available = layout.station_columns(station_id)
            reduced = {
                name: approximate[station_id][name] - centroid[name]
                for name in layout.frame.components
            }
            for name, value in _direction_terms(component, reduced, layout.frame).items():
                index = available.get(name)
                if index is not None:
                    column[index] = value
        norm = float(np.linalg.norm(column))
        if norm > 0.0:
            columns.append(column / norm)

    if not columns:  # pragma: no cover - defect non-empty implies a column
        return np.zeros((layout.size, 0))
    return np.column_stack(columns)


def _direction_terms(
    component: DefectComponent, reduced: dict[str, float], frame: Frame
) -> dict[str, float]:
    """How one station moves under one undetermined direction.

    A translation moves every station identically; a rotation moves each
    station perpendicular to its radius from the centroid; a scale moves each
    station along that radius.
    """
    height_component = "h" if frame is Frame.HEIGHT_1D else ("g" if frame is Frame.GRAVITY_1D else "u")

    if component is DefectComponent.TRANSLATION_E:
        return {"e": 1.0}
    if component is DefectComponent.TRANSLATION_N:
        return {"n": 1.0}
    if component is DefectComponent.TRANSLATION_U:
        return {height_component: 1.0}
    if component is DefectComponent.ROTATION_U:
        return {"e": -reduced.get("n", 0.0), "n": reduced.get("e", 0.0)}
    if component is DefectComponent.ROTATION_E:
        return {"n": -reduced.get("u", 0.0), "u": reduced.get("n", 0.0)}
    if component is DefectComponent.ROTATION_N:
        return {"e": reduced.get("u", 0.0), "u": -reduced.get("e", 0.0)}
    if component is DefectComponent.SCALE:
        return {name: reduced.get(name, 0.0) for name in frame.components}
    raise ValidationError("unknown_defect_component", received=component.value)
