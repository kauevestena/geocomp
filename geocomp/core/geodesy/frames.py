# SPDX-License-Identifier: GPL-2.0-or-later
"""Reference frames, and the transformations between them (FR-832).

``specs/13`` section 5, ``specs/14`` section 3. Observations of different
techniques arrive in different frames and at different epochs -- GNSS in a
global frame at the day it was observed, control in the national frame at its
reference epoch -- and a combination that ignores the difference absorbs a
datum shift into the residuals: a plausible adjustment of the wrong thing.

**What this holds.** The IERS transformations between the ITRF realisations
from ITRF2000 on, and the one that defines SIRGAS 2000, with the parameters and
codes of the EPSG Geodetic Parameter Dataset v11.004 (2024-02-24):

========  ==============================  =========  ==========
EPSG      Transformation                  Epoch      Accuracy
========  ==============================  =========  ==========
9991      ITRF2014 to ITRF2020 (1)        2015.0     1 mm
9992      ITRF2008 to ITRF2020 (1)        2015.0     1 cm
9993      ITRF2005 to ITRF2020 (1)        2015.0     1 cm
9994      ITRF2000 to ITRF2020 (1)        2015.0     1 cm
7790      ITRF2008 to ITRF2014 (1)        2010.0     1 cm
8079      ITRF2005 to ITRF2014 (1)        2010.0     1 cm
8078      ITRF2000 to ITRF2014 (1)        2010.0     1 cm
6389      ITRF2005 to ITRF2008 (2)        2000.0     1 cm
6300      ITRF2000 to ITRF2008 (1)        2000.0     1 cm
6302      ITRF2000 to ITRF2005 (1)        2000.0     1 cm
9052      ITRF2000 to SIRGAS 2000 (1)     2000.4     1 cm
========  ==============================  =========  ==========

Every pair of ITRF realisations has its own published transformation, and it
is the one used -- never a composition through ITRF2020, which differs from the
direct one by up to a few tenths of a millimetre and is not what PROJ does.
They are every non-deprecated EPSG transformation between these frames.

The ITRF ones are **time-dependent** (EPSG method 1053, position vector
convention): fourteen parameters, the seven of a similarity transformation and
their rates, evaluated at the epoch of the coordinates. The last is
**time-specific** (method 1065): SIRGAS 2000 *is* ITRF2000 at epoch 2000.4, so
the transformation is the identity and valid only at that epoch. Reaching it
from any other epoch means moving the point along its velocity -- which is why
a transformation into SIRGAS 2000 from a GNSS survey of 2024 needs one, and why
it is refused without.

**Why in-house rather than through PROJ.** PROJ has the same parameters and
QGIS ships it; but the combination needs the transformation's Jacobian to carry
covariances, needs to move velocities with the positions, and needs to record
what it did in a form provenance can hold -- none of which a PROJ pipeline
string returns. The arithmetic is small, and it is checked against PROJ itself:
``scripts/check_frames.py`` computes the same points with pyproj, and the
``reference`` workflow fails if the two disagree by a micrometre.

**What it does not do.** WGS 84 is refused rather than equated with an ITRF:
its realisations differ by decimetres and a bare "WGS84" does not say which. A
plate-motion or deformation model (VEMOS, for SIRGAS) is not held; a station
without a velocity cannot change epoch, and says so.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from geocomp.core.errors import ValidationError

__all__ = [
    "FRAMES",
    "FRAME_NAMES",
    "TRANSFORMATIONS",
    "Helmert",
    "TransformationRecord",
    "TransformationStep",
    "TransformedPoint",
    "canonical_frame",
    "transform_point",
    "transform_vector",
    "transformation_path",
]

_MM = 1.0e-3
_MAS = math.pi / (180.0 * 3600.0 * 1000.0)
_PPB = 1.0e-9

#: Canonical frame name for each name or EPSG code a frame is known by. Only the
#: CRSs of *one* datum map to one name -- geocentric, geographic 3D and 2D of
#: the same realisation -- which is an identity, not an equivalence someone
#: judged close enough. Codes from the EPSG dataset v11.004.
FRAMES: dict[str, str] = {}
for _name, _codes in {
    "ITRF2000": (4919, 7909, 8997),
    "ITRF2005": (4896, 7910, 8998),
    "ITRF2008": (5332, 7911, 8999),
    "ITRF2014": (7789, 7912, 9000),
    "ITRF2020": (9988, 9989, 9990),
    "SIRGAS2000": (4988, 4989, 4674),
}.items():
    FRAMES[_name] = _name
    for _code in _codes:
        FRAMES[f"EPSG:{_code}"] = _name
FRAMES["SIRGAS 2000"] = "SIRGAS2000"

#: The frames themselves, newest realisation first, for a choice offered to a
#: user. Appending is safe; a saved model stores the index, so reordering is not.
FRAME_NAMES: tuple[str, ...] = ("ITRF2020", "ITRF2014", "ITRF2008", "ITRF2005", "ITRF2000", "SIRGAS2000")


def canonical_frame(name: str) -> str:
    """The frame *name* denotes, or a refusal naming the ones that are known.

    Raises:
        ValidationError: ``frame_unknown`` -- including for WGS 84, whose
            realisations differ by decimetres.
    """
    key = (name or "").strip().upper().replace("EPSG::", "EPSG:")
    if key in FRAMES:
        return FRAMES[key]
    raise ValidationError(
        "frame_unknown",
        received=name,
        expected=sorted(set(FRAMES.values())),
        hint=(
            "a frame GeoComp holds transformations for. WGS 84 is not one of them: "
            "it has had several realisations, decimetres apart, and the name alone "
            "does not say which"
        ),
    )


@dataclass(frozen=True)
class Helmert:
    """A similarity transformation between two frames, possibly time-dependent.

    Position-vector convention (EPSG methods 1053 and 1065, and the IERS's)::

        X_target = T + (1 + D) (I + R) X_source

    with ``R`` the skew matrix of the rotations ``(rx, ry, rz)`` -- the
    small-angle form PROJ uses too -- and every parameter evaluated at the
    coordinates' epoch ``t`` as ``p(t) = p + p_dot (t - reference_epoch)``.

    Attributes:
        translation: Metres. rotation: Radians. scale: Dimensionless.
        *_rate: The same, per year.
        time_specific: Valid only at ``reference_epoch`` (method 1065).
        accuracy: EPSG's stated accuracy of the transformation, metres.
    """

    code: str
    name: str
    source: str
    target: str
    reference_epoch: float
    accuracy: float
    translation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 0.0
    translation_rate: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_rate: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale_rate: float = 0.0
    time_specific: bool = False

    def at(self, epoch: float) -> tuple[np.ndarray, np.ndarray]:
        """``(T, M)`` at *epoch*, so that ``X_target = T + M X_source``."""
        if self.time_specific and abs(epoch - self.reference_epoch) > 1e-9:
            raise ValidationError(
                "transformation_time_specific",
                transformation=self.code,
                received=epoch,
                expected=(
                    f"coordinates at epoch {self.reference_epoch}; {self.name} holds "
                    "only there, and reaching it from another epoch needs a velocity"
                ),
            )
        dt = 0.0 if self.time_specific else epoch - self.reference_epoch
        t = np.array(self.translation) + np.array(self.translation_rate) * dt
        rx, ry, rz = np.array(self.rotation) + np.array(self.rotation_rate) * dt
        d = self.scale + self.scale_rate * dt
        rotation = np.array([[1.0, -rz, ry], [rz, 1.0, -rx], [-ry, rx, 1.0]])
        return t, (1.0 + d) * rotation

    def rates(self) -> tuple[np.ndarray, np.ndarray]:
        """``(T_dot, M_dot)``: how the transformation itself changes per year,
        which a velocity crosses the transformation with (IERS convention)."""
        rx, ry, rz = self.rotation_rate
        skew = np.array([[self.scale_rate, -rz, ry], [rz, self.scale_rate, -rx], [-ry, rx, self.scale_rate]])
        return np.array(self.translation_rate), skew

    def forward(self, xyz: np.ndarray, epoch: float) -> np.ndarray:
        t, m = self.at(epoch)
        return t + m @ np.asarray(xyz, dtype=float)

    def backward(self, xyz: np.ndarray, epoch: float) -> np.ndarray:
        """The exact inverse -- not the sign-flipped parameters, whose error is
        second order and would be the one place this disagreed with PROJ."""
        t, m = self.at(epoch)
        return np.linalg.solve(m, np.asarray(xyz, dtype=float) - t)


def _itrf(code, name, source, target, epoch, accuracy, t, d, t_dot, d_dot, r=(0, 0, 0), r_dot=(0, 0, 0)):
    return Helmert(
        code=f"EPSG:{code}",
        name=name,
        source=source,
        target=target,
        reference_epoch=epoch,
        accuracy=accuracy,
        translation=tuple(v * _MM for v in t),
        rotation=tuple(v * _MAS for v in r),
        scale=d * _PPB,
        translation_rate=tuple(v * _MM for v in t_dot),
        rotation_rate=tuple(v * _MAS for v in r_dot),
        scale_rate=d_dot * _PPB,
    )


#: Every transformation held, from the EPSG dataset v11.004. Parameters as EPSG
#: publishes them: millimetres, milliarcseconds and parts per billion, and their
#: rates per year. The ITRF sets have no rotations and no rotation rates.
TRANSFORMATIONS: tuple[Helmert, ...] = (
    _itrf(9991, "ITRF2014 to ITRF2020 (1)", "ITRF2014", "ITRF2020", 2015.0, 0.001,
          (1.4, 0.9, -1.4), 0.42, (0.0, 0.1, -0.2), 0.0),
    _itrf(9992, "ITRF2008 to ITRF2020 (1)", "ITRF2008", "ITRF2020", 2015.0, 0.01,
          (-0.2, -1.0, -3.3), 0.29, (0.0, 0.1, -0.1), -0.03),
    _itrf(9993, "ITRF2005 to ITRF2020 (1)", "ITRF2005", "ITRF2020", 2015.0, 0.01,
          (-2.7, -0.1, 1.4), -0.65, (-0.3, 0.1, -0.1), -0.03),
    _itrf(9994, "ITRF2000 to ITRF2020 (1)", "ITRF2000", "ITRF2020", 2015.0, 0.01,
          (0.2, -0.8, 34.2), -2.25, (-0.1, 0.0, 1.7), -0.11),
    _itrf(7790, "ITRF2008 to ITRF2014 (1)", "ITRF2008", "ITRF2014", 2010.0, 0.01,
          (-1.6, -1.9, -2.4), 0.02, (0.0, 0.0, 0.1), -0.03),
    _itrf(8079, "ITRF2005 to ITRF2014 (1)", "ITRF2005", "ITRF2014", 2010.0, 0.01,
          (-2.6, -1.0, 2.3), -0.92, (-0.3, 0.0, 0.1), -0.03),
    _itrf(8078, "ITRF2000 to ITRF2014 (1)", "ITRF2000", "ITRF2014", 2010.0, 0.01,
          (-0.7, -1.2, 26.1), -2.12, (-0.1, -0.1, 1.9), -0.11),
    _itrf(6389, "ITRF2005 to ITRF2008 (2)", "ITRF2005", "ITRF2008", 2000.0, 0.01,
          (2.0, 0.9, 4.7), -0.94, (-0.3, 0.0, 0.0), 0.0),
    _itrf(6300, "ITRF2000 to ITRF2008 (1)", "ITRF2000", "ITRF2008", 2000.0, 0.01,
          (1.9, 1.7, 10.5), -1.34, (-0.1, -0.1, 1.8), -0.08),
    _itrf(6302, "ITRF2000 to ITRF2005 (1)", "ITRF2000", "ITRF2005", 2000.0, 0.01,
          (-0.1, 0.8, 5.8), -0.40, (0.2, -0.1, 1.8), -0.08),
    Helmert(
        code="EPSG:9052",
        name="ITRF2000 to SIRGAS 2000 (1)",
        source="ITRF2000",
        target="SIRGAS2000",
        reference_epoch=2000.4,
        accuracy=0.01,
        time_specific=True,
    ),
)  # fmt: skip


@dataclass(frozen=True)
class TransformationStep:
    """One thing done to a coordinate, for the record (FR-832, FR-134)."""

    kind: str  # "helmert" or "epoch"
    description: str
    code: str = ""
    inverse: bool = False
    epoch: float | None = None
    from_epoch: float | None = None
    to_epoch: float | None = None
    accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """The step as provenance stores it, leaving out fields that are empty or zero."""
        payload: dict[str, Any] = {"kind": self.kind, "description": self.description}
        for key in ("code", "epoch", "from_epoch", "to_epoch"):
            value = getattr(self, key)
            if value not in (None, ""):
                payload[key] = value
        if self.inverse:
            payload["inverse"] = True
        if self.accuracy:
            payload["accuracy"] = self.accuracy
        return payload


@dataclass(frozen=True)
class TransformationRecord:
    """What was applied to bring a coordinate from one frame and epoch to another.

    ``accuracy`` is the root-sum-square of the steps' stated accuracies: the
    transformation's own uncertainty, which is **common to every point it is
    applied to** -- a shift of the whole network, not noise between its
    stations. It is recorded rather than added to each station's covariance,
    where it would appear as independent scatter and falsify every relative
    position; a comparison of absolute positions (``specs/14``) adds it where
    it belongs.
    """

    source: str
    target: str
    source_epoch: float
    target_epoch: float
    steps: tuple[TransformationStep, ...] = field(default_factory=tuple)

    @property
    def accuracy(self) -> float:
        """The root-sum-square of the steps' stated accuracies, in metres; zero for the identity."""
        return math.sqrt(sum(step.accuracy**2 for step in self.steps))

    @property
    def is_identity(self) -> bool:
        """Whether nothing was applied: source and target frame and epoch already agreed."""
        return not self.steps

    def to_dict(self) -> dict[str, Any]:
        """The record as provenance stores it, with the combined accuracy and every step."""
        return {
            "source": self.source,
            "target": self.target,
            "source_epoch": self.source_epoch,
            "target_epoch": self.target_epoch,
            "accuracy": self.accuracy,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(frozen=True)
class TransformedPoint:
    xyz: np.ndarray
    covariance: np.ndarray | None
    velocity: np.ndarray | None
    record: TransformationRecord


def transformation_path(source: str, target: str) -> list[tuple[Helmert, bool]]:
    """The transformations from *source* to *target*, each with its direction.

    Shortest path through the held transformations, so a direct one (ITRF2008
    to ITRF2014) is used where it exists rather than a composition through
    ITRF2020 -- the two differ at the tenth of a millimetre, and a direct
    published transformation is what PROJ would choose too.

    Raises:
        ValidationError: ``frame_transformation_unavailable`` when none joins them.
    """
    source, target = canonical_frame(source), canonical_frame(target)
    if source == target:
        return []
    queue = deque([(source, [])])
    seen = {source}
    while queue:
        frame, path = queue.popleft()
        for helmert in TRANSFORMATIONS:
            directions = ((helmert.source, helmert.target, False), (helmert.target, helmert.source, True))
            for start, end, inverse in directions:
                if start != frame or end in seen:
                    continue
                extended = [*path, (helmert, inverse)]
                if end == target:
                    return extended
                seen.add(end)
                queue.append((end, extended))
    raise ValidationError(
        "frame_transformation_unavailable",
        received=[source, target],
        expected="two frames joined by the transformations GeoComp holds",
    )


def transform_point(
    xyz: ArrayLike,
    *,
    source: str,
    target: str,
    epoch: float,
    target_epoch: float | None = None,
    covariance: ArrayLike | None = None,
    velocity: ArrayLike | None = None,
    velocity_covariance: ArrayLike | None = None,
) -> TransformedPoint:
    """Bring one geocentric point from (*source*, *epoch*) to (*target*, *target_epoch*).

    The Helmert steps run at the coordinates' current epoch; a change of epoch
    moves the point along its *velocity*, in whichever frame it is in at the
    time, and the velocity crosses each Helmert step with the transformation's
    own rates. A time-specific step (SIRGAS 2000) first moves the point to the
    step's epoch, so ``target_epoch`` need not be given for it.

    The covariance is carried through the Jacobian of each step, and a change
    of epoch adds the velocity's uncertainty times the interval squared.

    Raises:
        ValidationError: ``epoch_change_without_velocity`` when the epoch must
            change and no velocity was given. Zero is a real assumption -- a
            decimetre in a decade in most of Brazil -- and not GeoComp's to make.
    """
    source_frame, target_frame = canonical_frame(source), canonical_frame(target)
    x = np.asarray(xyz, dtype=float)
    sigma = None if covariance is None else np.asarray(covariance, dtype=float)
    v = None if velocity is None else np.asarray(velocity, dtype=float)
    sigma_v = None if velocity_covariance is None else np.asarray(velocity_covariance, dtype=float)
    now = float(epoch)
    steps: list[TransformationStep] = []

    def move(to: float) -> None:
        nonlocal x, sigma, now
        if abs(to - now) <= 1e-9:
            return
        if v is None:
            raise ValidationError(
                "epoch_change_without_velocity",
                received=[now, to],
                expected=(
                    "a velocity for the point. Moving it between epochs without one "
                    "assumes it does not move -- a decimetre a decade in most of Brazil"
                ),
            )
        interval = to - now
        x = x + v * interval
        if sigma is not None and sigma_v is not None:
            sigma = sigma + sigma_v * interval**2
        steps.append(
            TransformationStep(
                kind="epoch",
                description=f"moved along its velocity from {now:.4f} to {to:.4f}",
                from_epoch=now,
                to_epoch=to,
            )
        )
        now = to

    for helmert, inverse in transformation_path(source_frame, target_frame):
        if helmert.time_specific:
            move(helmert.reference_epoch)
        _t, m = helmert.at(now)
        if inverse:
            x = helmert.backward(x, now)
            jacobian = np.linalg.inv(m)
        else:
            x = helmert.forward(x, now)
            jacobian = m
        if sigma is not None:
            sigma = jacobian @ sigma @ jacobian.T
        if v is not None:
            t_dot, m_dot = helmert.rates()
            sign = -1.0 if inverse else 1.0
            v = jacobian @ v + sign * (t_dot + m_dot @ x)
        steps.append(
            TransformationStep(
                kind="helmert",
                description=helmert.name + (" (inverse)" if inverse else ""),
                code=helmert.code,
                inverse=inverse,
                epoch=now,
                accuracy=helmert.accuracy,
            )
        )
    if target_epoch is not None:
        move(float(target_epoch))

    return TransformedPoint(
        xyz=x,
        covariance=sigma,
        velocity=v,
        record=TransformationRecord(
            source=source_frame,
            target=target_frame,
            source_epoch=float(epoch),
            target_epoch=now,
            steps=tuple(steps),
        ),
    )


def transform_vector(
    dxyz: ArrayLike, *, source: str, target: str, epoch: float, covariance: ArrayLike | None = None
) -> tuple[np.ndarray, np.ndarray | None, TransformationRecord]:
    """A baseline between two points of one frame, carried to another.

    The translation cancels between the two ends and only ``M`` -- scale and
    rotation, parts per billion -- acts, so this is a millimetre over 1000 km.
    The epoch is not changed: a baseline changes with epoch only by the
    difference of its ends' velocities, which is a question about two stations,
    not about the vector.
    """
    d = np.asarray(dxyz, dtype=float)
    sigma = None if covariance is None else np.asarray(covariance, dtype=float)
    steps: list[TransformationStep] = []
    for helmert, inverse in transformation_path(source, target):
        if helmert.time_specific:
            helmert.at(epoch)  # refuses a baseline at any other epoch, as for a point
        _t, m = helmert.at(epoch)
        jacobian = np.linalg.inv(m) if inverse else m
        d = jacobian @ d
        if sigma is not None:
            sigma = jacobian @ sigma @ jacobian.T
        steps.append(
            TransformationStep(
                kind="helmert",
                description=helmert.name + (" (inverse)" if inverse else ""),
                code=helmert.code,
                inverse=inverse,
                epoch=epoch,
            )
        )
    record = TransformationRecord(
        source=canonical_frame(source),
        target=canonical_frame(target),
        source_epoch=float(epoch),
        target_epoch=float(epoch),
        steps=tuple(steps),
    )
    return d, sigma, record
