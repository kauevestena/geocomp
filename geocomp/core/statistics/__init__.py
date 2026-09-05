# SPDX-License-Identifier: GPL-2.0-or-later
"""Statistical validation of an adjustment.

``specs/06-adjustment-core.md`` section 4. The research project requires this so
that results "possuam integridade e possam ser utilizados com seguranca em
aplicacoes como obras de engenharia e cadastro".

The organising rule, from ``specs/06`` section 7: **every reported statistic is
accompanied by its critical value, its confidence level and its decision** --
never a bare pass or fail. A student learns nothing from "the test passed", and
a professional has nothing to defend with it.
"""

from __future__ import annotations

from geocomp.core.statistics.distributions import (
    USING_SCIPY,
    chi2_cdf,
    chi2_quantile,
    f_cdf,
    f_quantile,
    non_centrality,
    normal_cdf,
    normal_quantile,
    t_cdf,
    t_quantile,
)
from geocomp.core.statistics.ellipses import (
    confidence_scale,
    error_ellipse,
    positional_uncertainty,
    relative_ellipse,
)
from geocomp.core.statistics.reliability import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    ReliabilityReport,
    ReliabilityResult,
    reliability,
)
from geocomp.core.statistics.tests import (
    GLOBAL_TEST_CAUSES,
    OutlierCandidate,
    SnoopingReport,
    data_snooping,
    global_test,
)

__all__ = [
    "DEFAULT_ALPHA",
    "DEFAULT_BETA",
    "GLOBAL_TEST_CAUSES",
    "USING_SCIPY",
    "OutlierCandidate",
    "ReliabilityReport",
    "ReliabilityResult",
    "SnoopingReport",
    "chi2_cdf",
    "chi2_quantile",
    "confidence_scale",
    "data_snooping",
    "error_ellipse",
    "f_cdf",
    "f_quantile",
    "global_test",
    "non_centrality",
    "normal_cdf",
    "normal_quantile",
    "positional_uncertainty",
    "relative_ellipse",
    "reliability",
    "t_cdf",
    "t_quantile",
]
