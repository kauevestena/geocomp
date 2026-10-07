# SPDX-License-Identifier: GPL-2.0-or-later
"""Deformation as a field: rigid-body motion separated from strain (``specs/14`` section 6).

A set of object points that moved can have moved as a block -- translated and
turned, a dam that has settled whole -- or deformed: stretched, sheared, the
distances between its points changed. The two are different findings, and
reading them off a list of independent point displacements is not possible.

This fits the horizontal displacements of the object points, in the reference
block's datum and with their full covariance, twice:

* as a **rigid body**: ``d = t + omega k x (x - x0)``, a translation and a rotation;
* as a **homogeneous strain**: ``d = t + A (x - x0)``, the displacement gradient
  ``A`` carrying the strain tensor and the rotation.

The drop in the weighted squared residual from the first to the second, over
the three strain parameters, is F-tested with the pooled variance factor: if
significant, the points did not move as a block. The strain parameters come
with their standard deviations, propagated through the linearised relations.

**Where the configuration supports it** (section 6): three object points at
least, and not in a line. Fewer is refused rather than fitted to nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.models import TestResult
from geocomp.core.monitoring.congruency import DeformationAnalysis
from geocomp.core.statistics.distributions import chi2_quantile, f_quantile

__all__ = ["Strain", "strain"]


@dataclass(frozen=True)
class Strain:
    """A homogeneous strain over a set of points, and its rigid-body part.

    Attributes:
        translation: East and north, metres.
        rotation: Radians, anticlockwise positive, from the strain fit.
        dilatation: ``e_ee + e_nn``, the relative change in area.
        shear: The maximum shear strain, ``gamma``.
        principal: The two principal strains, extension first.
        azimuth: Of the principal extension, radians from north, clockwise.
        std_devs: Of each of the above, by name.
        rigid: Translation and rotation when the points are fitted as a block.
        strain_test: Whether the strain is significant beyond rigid motion.
    """

    stations: tuple[str, ...]
    translation: tuple[float, float]
    rotation: float
    strain_tensor: tuple[float, float, float]
    dilatation: float
    shear: float
    principal: tuple[float, float]
    azimuth: float
    std_devs: dict[str, float]
    rigid_translation: tuple[float, float]
    rigid_rotation: float
    strain_test: TestResult

    @property
    def deforming(self) -> bool:
        """Whether the strain test rejected 'no deformation'."""
        return not self.strain_test.passed


def strain(analysis: DeformationAnalysis, stations: Sequence[str] | None = None) -> Strain:
    """Fit rigid-body motion and a homogeneous strain to *stations* (by default
    the object points).

    Raises:
        ValidationError: ``monitoring_strain_configuration`` for fewer than three
            stations, points in a line, or a network without a plan.
    """
    comparison = analysis.comparison
    components = comparison.components
    if "e" not in components or "n" not in components:
        raise ValidationError(
            "monitoring_strain_configuration",
            reason="the network has no plan",
            expected="east and north components",
        )
    stations = tuple(stations) if stations is not None else analysis.objects
    if len(stations) < 3:
        raise ValidationError(
            "monitoring_strain_configuration",
            stations=list(stations),
            expected="three object points at least: a strain has three parameters beyond rigid motion",
        )
    k = comparison.dimension
    e, n = components.index("e"), components.index("n")
    position = {s: i for i, s in enumerate(comparison.stations)}
    rows = [position[s] * k + c for s in stations for c in (e, n)]
    d = analysis.difference[rows]
    q = analysis.cofactor[np.ix_(rows, rows)]
    xy = np.array([comparison.coordinates[position[s]] for s in stations])
    centred = xy - xy.mean(axis=0)
    if np.linalg.matrix_rank(centred, tol=1e-6 * (np.abs(centred).max() or 1.0)) < 2:
        raise ValidationError(
            "monitoring_strain_configuration",
            stations=list(stations),
            expected="points spanning an area, not a line",
        )
    weight = np.linalg.pinv(q, hermitian=True)

    # Full model: t_e, t_n, a11 (de/de), a12 (de/dn), a21 (dn/de), a22 (dn/dn).
    full = np.zeros((len(rows), 6))
    full[0::2, 0] = 1.0
    full[1::2, 1] = 1.0
    full[0::2, 2] = centred[:, 0]
    full[0::2, 3] = centred[:, 1]
    full[1::2, 4] = centred[:, 0]
    full[1::2, 5] = centred[:, 1]
    # Rigid model: t_e, t_n, omega (anticlockwise).
    rigid = np.zeros((len(rows), 3))
    rigid[0::2, 0] = 1.0
    rigid[1::2, 1] = 1.0
    rigid[0::2, 2] = -centred[:, 1]
    rigid[1::2, 2] = centred[:, 0]

    p_full, n_full, omega_full = _fit(full, weight, d)
    p_rigid, _, omega_rigid = _fit(rigid, weight, d)

    a11, a12, a21, a22 = p_full[2:]
    rotation = (a21 - a12) / 2.0
    exx, eyy, exy = a11, a22, (a12 + a21) / 2.0
    dilatation = exx + eyy
    gamma1, gamma2 = exx - eyy, 2.0 * exy
    shear = float(np.hypot(gamma1, gamma2))
    principal = ((dilatation + shear) / 2.0, (dilatation - shear) / 2.0)
    # The principal extension's direction: the eigenvector of [[exx, exy], [exy, eyy]].
    values, vectors = np.linalg.eigh(np.array([[exx, exy], [exy, eyy]]))
    major = vectors[:, int(np.argmax(values))]
    azimuth = float(np.arctan2(major[0], major[1]) % np.pi)

    covariance = comparison.variance_factor * np.linalg.inv(n_full)
    gradients = {
        "rotation": np.array([0, 0, 0, -0.5, 0.5, 0]),
        "e_ee": np.array([0, 0, 1, 0, 0, 0]),
        "e_nn": np.array([0, 0, 0, 0, 0, 1]),
        "e_en": np.array([0, 0, 0, 0.5, 0.5, 0]),
        "dilatation": np.array([0, 0, 1, 0, 0, 1]),
        "translation_e": np.array([1, 0, 0, 0, 0, 0]),
        "translation_n": np.array([0, 1, 0, 0, 0, 0]),
    }
    if shear > 0.0:
        gradients["shear"] = np.array([0, 0, gamma1, gamma2, gamma2, -gamma1]) / shear
    std_devs = {name: float(np.sqrt(max(g @ covariance @ g, 0.0))) for name, g in gradients.items()}

    return Strain(
        stations=stations,
        translation=(float(p_full[0]), float(p_full[1])),
        rotation=float(rotation),
        strain_tensor=(float(exx), float(eyy), float(exy)),
        dilatation=float(dilatation),
        shear=shear,
        principal=(float(principal[0]), float(principal[1])),
        azimuth=azimuth,
        std_devs=std_devs,
        rigid_translation=(float(p_rigid[0]), float(p_rigid[1])),
        rigid_rotation=float(p_rigid[2]),
        strain_test=_strain_test(omega_rigid - omega_full, comparison, analysis.confidence),
    )


def _fit(design: np.ndarray, weight: np.ndarray, d: np.ndarray):
    normal = design.T @ weight @ design
    parameters = np.linalg.solve(normal, design.T @ weight @ d)
    residual = d - design @ parameters
    return parameters, normal, float(residual @ weight @ residual)


def _strain_test(reduction: float, comparison, confidence: float) -> TestResult:
    """Three strain parameters beyond rigid motion, against their noise."""
    f = comparison.degrees_of_freedom
    if f > 0:
        statistic = max(reduction, 0.0) / (3 * comparison.variance_factor)
        critical = f_quantile(confidence, 3, f)
        note = f"F(3, {f}): strain beyond rigid-body motion"
    else:
        statistic = max(reduction, 0.0)
        critical = chi2_quantile(confidence, 3)
        note = "chi-square(3): strain beyond rigid-body motion"
    return TestResult(
        name="strain beyond rigid-body motion",
        statistic=statistic,
        critical_high=critical,
        confidence=confidence,
        passed=statistic <= critical,
        note=note,
    )
