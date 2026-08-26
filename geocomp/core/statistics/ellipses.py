# SPDX-License-Identifier: GPL-2.0-or-later
"""Error ellipses, ellipsoids and positional uncertainty.

``specs/06-adjustment-core.md`` sections 4.4 and 4.5.

The **relative** ellipse is the one that usually answers the user's real
question. An absolute ellipse describes a station's position with respect to the
datum, which in a minimum-constraint solution is partly an artefact of where the
datum was pinned. A relative ellipse describes one station with respect to
another, from the joint covariance, and that is what tells you whether a
*baseline* is well determined.

Two scalings are offered and the result records which was used:

* the **standard** ellipse, at one sigma, whose axes are the square roots of the
  eigenvalues;
* the **confidence** ellipse, scaled by ``sqrt(2 F_{2,dof})`` for a stated
  probability -- larger than the naive ``sqrt(chi2)`` scaling because the
  variance factor was estimated from the same adjustment.
"""

from __future__ import annotations

import math

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.models import ErrorEllipse
from geocomp.core.statistics.distributions import chi2_quantile, f_quantile

__all__ = [
    "confidence_scale",
    "error_ellipse",
    "positional_uncertainty",
    "relative_ellipse",
]


def confidence_scale(
    confidence: float, *, degrees_of_freedom: int | None = None, dimension: int = 2
) -> float:
    """The factor by which the standard ellipse is scaled.

    Args:
        confidence: The probability the region should contain the true point.
        degrees_of_freedom: Of the adjustment. When given, the F-distribution
            scaling is used, which accounts for the variance factor having been
            estimated rather than known. When ``None``, the chi-square scaling
            is used, appropriate when sigma_0 is known a priori.
        dimension: 2 for an ellipse, 3 for an ellipsoid.

    Returning the scale rather than applying it lets the caller state it, which
    FR-901 requires wherever an ellipse is drawn.
    """
    if not 0.0 < confidence < 1.0:
        raise ValidationError(
            "confidence_out_of_range", received=confidence, expected="0 < confidence < 1"
        )
    if degrees_of_freedom is None or degrees_of_freedom < 1:
        return math.sqrt(chi2_quantile(confidence, dimension))
    return math.sqrt(dimension * f_quantile(confidence, dimension, degrees_of_freedom))


def error_ellipse(
    covariance: np.ndarray,
    *,
    confidence: float | None = 0.95,
    degrees_of_freedom: int | None = None,
) -> ErrorEllipse:
    """The error ellipse (2x2) or ellipsoid (3x3) of one adjusted station.

    From the eigen-decomposition: the eigenvalues are the squared semi-axes and
    the eigenvector of the largest gives the orientation.

    Orientation is reported as an **azimuth from north, clockwise**, matching the
    survey convention used throughout GeoComp, with the covariance ordered
    (easting, northing).

    Args:
        confidence: ``None`` for the standard one-sigma ellipse.
        degrees_of_freedom: Enables the F scaling; see :func:`confidence_scale`.
    """
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape not in ((2, 2), (3, 3)):
        raise ValidationError(
            "ellipse_wrong_dimension",
            shape=list(matrix.shape),
            expected="a 2x2 or 3x3 covariance block",
        )

    dimension = matrix.shape[0]
    plan = matrix[:2, :2]
    eigenvalues, eigenvectors = np.linalg.eigh(plan)
    order = np.argsort(-eigenvalues)
    eigenvalues = np.clip(eigenvalues[order], 0.0, None)
    eigenvectors = eigenvectors[:, order]

    scale = (
        1.0
        if confidence is None
        else confidence_scale(confidence, degrees_of_freedom=degrees_of_freedom, dimension=dimension)
    )

    semi_major = scale * math.sqrt(eigenvalues[0])
    semi_minor = scale * math.sqrt(eigenvalues[1])
    # Eigenvector components are (easting, northing); azimuth = atan2(dE, dN).
    orientation = math.atan2(eigenvectors[0, 0], eigenvectors[1, 0]) % math.pi

    semi_vertical = None
    if dimension == 3:
        semi_vertical = scale * math.sqrt(max(float(matrix[2, 2]), 0.0))

    return ErrorEllipse(
        semi_major=semi_major,
        semi_minor=semi_minor,
        orientation=orientation,
        confidence=confidence if confidence is not None else 0.6827,
        semi_vertical=semi_vertical,
    )


def relative_ellipse(
    covariance: np.ndarray,
    first: list[int],
    second: list[int],
    *,
    confidence: float | None = 0.95,
    degrees_of_freedom: int | None = None,
) -> ErrorEllipse:
    """The error ellipse of the *vector* between two stations.

    Built from the joint covariance of both stations:

        Sigma_d = Sigma_11 + Sigma_22 - Sigma_12 - Sigma_12^T

    The cross-covariance is what makes this different from adding the two
    absolute ellipses. Two stations determined by the same observations are
    strongly correlated, and ignoring that **overstates** the uncertainty of the
    baseline between them -- often by a large factor, which is why a network can
    look poor in absolute terms and be excellent relatively.

    Args:
        first / second: Column indices of each station's components, in the same
            component order.
    """
    if len(first) != len(second):
        raise ValidationError(
            "relative_ellipse_dimension_mismatch",
            first=len(first),
            second=len(second),
            expected="the same number of components for both stations",
        )

    matrix = np.asarray(covariance, dtype=float)
    sigma_11 = matrix[np.ix_(first, first)]
    sigma_22 = matrix[np.ix_(second, second)]
    sigma_12 = matrix[np.ix_(first, second)]
    difference = sigma_11 + sigma_22 - sigma_12 - sigma_12.T

    return error_ellipse(
        difference, confidence=confidence, degrees_of_freedom=degrees_of_freedom
    )


def positional_uncertainty(
    covariance: np.ndarray,
    *,
    confidence: float = 0.95,
    degrees_of_freedom: int | None = None,
) -> float:
    """A single scalar summarising a station's positional quality.

    The radius of the circle at *confidence* containing the true position,
    taken from the semi-major axis of the confidence ellipse. Comparable with
    the values DynAdjust reports in its ``.apu`` output, which is what makes the
    two engines' results directly comparable in the phase P6 cross-validation
    (``specs/06`` section 4.5).
    """
    ellipse = error_ellipse(
        covariance, confidence=confidence, degrees_of_freedom=degrees_of_freedom
    )
    return ellipse.semi_major
