# SPDX-License-Identifier: GPL-2.0-or-later
"""Instrument and reflector profiles, and the stochastic models they carry.

``specs/15-ui-menu-and-settings.md`` section 2.2 (FR-061, FR-069) and
``specs/05-uncertainty-and-covariance.md`` section 5 (FR-064).

Profiles are **named**, not a single set of values: a department owns several
total stations, and a value that is "the" instrument constant is wrong for all
but one of them. Observations reference an instrument by id, so a later
calibration correction can be traced to exactly the observations it affects.
"""

from __future__ import annotations

from geocomp.core.instruments.profiles import (
    AtmosphericModel,
    EdmSpecification,
    InstrumentProfile,
    ProfileLibrary,
    ReflectorProfile,
    angular_specification,
)
from geocomp.core.instruments.stochastic import (
    SigmaSource,
    StochasticDefaults,
    resolve_sigma,
)

__all__ = [
    "AtmosphericModel",
    "EdmSpecification",
    "InstrumentProfile",
    "ProfileLibrary",
    "ReflectorProfile",
    "SigmaSource",
    "StochasticDefaults",
    "angular_specification",
    "resolve_sigma",
]
