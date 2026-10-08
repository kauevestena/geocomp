# SPDX-License-Identifier: GPL-2.0-or-later
"""The core's enums and tokens in words, in the language (FR-091, P12c-42).

The core names things by machine values -- ``minimum_constraint``, ``plane_2d``,
``slope_distance``, ``levelling`` -- which a JSON document, a provenance record
and a test compare against, and which never change with the language. Until
P12c-42 the reports and log lines showed them as they stood: a Portuguese
report's datum read "minimum_constraint". This module is where a value becomes
words, so a report, a log line and a dialog say the same thing.

The values stay what they are in the documents GeoComp writes; only what a
reader is shown goes through here.
"""

from __future__ import annotations

from enum import Enum

from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.adjustment.datum import DatumDefect, DefectComponent
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models.observation import ObservationType
from geocomp.core.models.position import HeightType
from geocomp.core.models.solution import DatumDefinition, SolutionKind
from geocomp.core.models.station import ConstraintMode
from geocomp.core.techniques.total_station.survey import TraverseAdjustment, TraverseKind
from geocomp.core.uncertainty import UncertaintyMode
from geocomp.io.levelbook import Layout
from geocomp.io.mapping import AngleFormat

__all__ = [
    "LABELLED",
    "closure_kind_label",
    "defect_words",
    "engine_label",
    "in_words",
    "solver_label",
    "technique_label",
    "test_name_label",
]

_CONTEXT = "GeoCompLabels"

#: Every enum a reader is shown, each member of which :func:`in_words` words.
LABELLED: tuple[type[Enum], ...] = (
    AngleFormat,
    ConstraintMode,
    DatumDefinition,
    DefectComponent,
    Frame,
    HeightType,
    Layout,
    ObservationType,
    SolutionKind,
    TraverseAdjustment,
    TraverseKind,
    UncertaintyMode,
)


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def _labels() -> dict[Enum, str]:
    # Built at each call, not at import: the words are the language installed
    # when they are asked for, and a translator can be installed later.
    return {
        AngleFormat.DECIMAL_DEGREES: _tr("decimal degrees"),
        AngleFormat.SEXAGESIMAL_TEXT: _tr("degrees, minutes and seconds in one column"),
        AngleFormat.SEXAGESIMAL_TRIPLE: _tr("degrees, minutes and seconds in three columns"),
        AngleFormat.GON: _tr("gon"),
        AngleFormat.RADIANS: _tr("radians"),
        ConstraintMode.FREE: _tr("free"),
        ConstraintMode.FIXED: _tr("fixed"),
        ConstraintMode.WEIGHTED: _tr("weighted"),
        DatumDefinition.MINIMUM_CONSTRAINT: _tr("minimum constraints"),
        DatumDefinition.INNER_CONSTRAINT: _tr("inner constraints (free network)"),
        DatumDefinition.CONSTRAINED: _tr("constrained"),
        DatumDefinition.FIXED: _tr("fixed stations"),
        DatumDefinition.NONE: _tr("no datum"),
        DefectComponent.TRANSLATION_E: _tr("translation in easting"),
        DefectComponent.TRANSLATION_N: _tr("translation in northing"),
        DefectComponent.TRANSLATION_U: _tr("translation in height"),
        DefectComponent.ROTATION_U: _tr("rotation about the vertical"),
        DefectComponent.ROTATION_E: _tr("rotation about the easting axis"),
        DefectComponent.ROTATION_N: _tr("rotation about the northing axis"),
        DefectComponent.SCALE: _tr("scale"),
        Frame.HEIGHT_1D: _tr("1D heights"),
        Frame.PLANE_2D: _tr("2D plane"),
        Frame.SPACE_3D: _tr("3D local"),
        Frame.GRAVITY_1D: _tr("1D gravity"),
        Frame.GEOCENTRIC_3D: _tr("3D geocentric"),
        HeightType.ELLIPSOIDAL: _tr("ellipsoidal"),
        HeightType.ORTHOMETRIC: _tr("orthometric"),
        HeightType.NORMAL: _tr("normal"),
        HeightType.NONE: _tr("none"),
        Layout.READING: _tr("one row per reading"),
        Layout.SETUP: _tr("one row per setup"),
        ObservationType.DIRECTION: _tr("direction"),
        ObservationType.HORIZONTAL_ANGLE: _tr("horizontal angle"),
        ObservationType.AZIMUTH: _tr("azimuth"),
        ObservationType.ASTRONOMIC_AZIMUTH: _tr("astronomic azimuth"),
        ObservationType.ZENITH_ANGLE: _tr("zenith angle"),
        ObservationType.VERTICAL_ANGLE: _tr("vertical angle"),
        ObservationType.SLOPE_DISTANCE: _tr("slope distance"),
        ObservationType.HORIZONTAL_DISTANCE: _tr("horizontal distance"),
        ObservationType.ELLIPSOID_DISTANCE: _tr("ellipsoidal distance"),
        ObservationType.HEIGHT_DIFFERENCE: _tr("height difference"),
        ObservationType.ORTHOMETRIC_HEIGHT: _tr("orthometric height"),
        ObservationType.ELLIPSOIDAL_HEIGHT: _tr("ellipsoidal height"),
        ObservationType.GEODETIC_LATITUDE: _tr("geodetic latitude"),
        ObservationType.GEODETIC_LONGITUDE: _tr("geodetic longitude"),
        ObservationType.ASTRONOMIC_LATITUDE: _tr("astronomic latitude"),
        ObservationType.ASTRONOMIC_LONGITUDE: _tr("astronomic longitude"),
        ObservationType.GNSS_BASELINE: _tr("GNSS baseline"),
        ObservationType.GNSS_POINT: _tr("GNSS point"),
        ObservationType.GRAVITY: _tr("gravity"),
        ObservationType.GRAVITY_DIFFERENCE: _tr("gravity difference"),
        SolutionKind.ADJUSTMENT: _tr("adjustment"),
        SolutionKind.GNSS_PROCESSING: _tr("GNSS processing"),
        SolutionKind.PREANALYSIS: _tr("pre-analysis"),
        SolutionKind.TRANSFORMATION: _tr("transformation"),
        TraverseAdjustment.COMPASS: _tr("compass (Bowditch) rule"),
        TraverseAdjustment.TRANSIT: _tr("transit rule"),
        TraverseAdjustment.NONE: _tr("not distributed"),
        TraverseKind.CLOSED: _tr("closed"),
        TraverseKind.CONNECTED: _tr("connected"),
        TraverseKind.OPEN: _tr("open"),
        UncertaintyMode.RIGOROUS: _tr("rigorous"),
        UncertaintyMode.APPROXIMATE: _tr("approximate"),
    }


def in_words(member: Enum) -> str:
    """*member* in words. Every member of :data:`LABELLED` has them, which a test holds."""
    words = _labels().get(member)
    return words if words is not None else str(member.value)


def technique_label(token: str) -> str:
    """A technique, or a variance-component group named after one, in words.

    A group a user named is not a technique and is shown as named.
    """
    labels = {
        "gnss": _tr("GNSS"),
        "total_station": _tr("Total station"),
        "levelling": _tr("Levelling"),
        "gravimetry": _tr("Gravimetry"),
        "astro_geodetic": _tr("Astro-geodetic"),
        "constraints": _tr("Weighted constraints"),
        "geoid": _tr("Geoid priors"),
    }
    return labels.get(token, token)


def closure_kind_label(kind: str) -> str:
    """A levelling closure's kind -- ``line``, ``loop``, ``section`` -- in words."""
    return {
        "line": _tr("line between benchmarks"),
        "loop": _tr("loop"),
        "section": _tr("section, forward and back"),
    }.get(kind, kind)


def test_name_label(name: str) -> str:
    """A statistical test's name in words: the core calls the global test ``global``."""
    return {"global": _tr("global test")}.get(name, name)


def solver_label(method: str) -> str:
    """How the normal equations were solved, as the core records it, in words."""
    return {
        "cholesky": _tr("Cholesky factorisation"),
        "qr": _tr("QR factorisation"),
        "bordered": _tr("bordered system (minimum constraints)"),
        "sparse-lu": _tr("sparse LU factorisation"),
        "sparse-bordered": _tr("sparse bordered system (minimum constraints)"),
    }.get(method, method)


def engine_label(engine: str) -> str:
    """The engine a combination was routed to, in words."""
    return {"in_house": _tr("GeoComp's own adjustment"), "dynadjust": "DynAdjust"}.get(engine, engine)


def defect_words(defect: DatumDefect) -> str:
    """The datum defect in words: its size and the components it is made of.

    ``DatumDefect.describe()`` says the same in English, for logs and documents.
    """
    if not defect.components:
        return _tr("none; the observations determine the datum")
    return (
        _tr("%1 (%2)")
        .replace("%1", str(defect.size))
        .replace("%2", ", ".join(in_words(component) for component in defect.components))
    )
