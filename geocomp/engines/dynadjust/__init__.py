# SPDX-License-Identifier: GPL-2.0-or-later
"""The DynAdjust adapter: input writers, pipeline driver, output parsers.

``specs/07-engine-dynadjust.md``. DynAdjust is Geoscience Australia's
least-squares suite, Apache-2.0, and the engine that makes continental-scale
adjustment reachable from GeoComp -- its credentials are the GDA2020 adjustment,
330,000 stations and 2.4 million observations.

**It is a suite of programs, not one executable**: ``dnaimport``,
``dnareftran``, ``dnageoid``, ``dnasegment``, ``dnaadjust`` and ``dnaplot``.
GeoComp drives a pipeline over them, recording an
:class:`~geocomp.engines.base.EngineRun` per stage.

Everything in this package is QGIS-free, so the writers and parsers are tested
wherever Python runs rather than only where QGIS does.
"""

from __future__ import annotations

from geocomp.engines.dynadjust.crossvalidation import Agreement, Comparison, compare
from geocomp.engines.dynadjust.dynaml import (
    DynaMLDocument,
    station_names,
    write_measurement_file,
    write_station_file,
)
from geocomp.engines.dynadjust.engine import (
    DynAdjustEngine,
    DynAdjustJob,
    PreparedJob,
    Stage,
    plan,
)
from geocomp.engines.dynadjust.formats import (
    format_metres,
    format_variance,
    hp_to_radians,
    radians_to_hp,
    radians_to_seconds,
    seconds_to_radians,
)
from geocomp.engines.dynadjust.read_dna import read_dna, read_dna_stations
from geocomp.engines.dynadjust.read_dynaml import ReadReport, read_dynaml, read_station_file
from geocomp.engines.dynadjust.read_output import (
    AdjustedMeasurement,
    AngularFormat,
    CoordinateRow,
    OutputPreamble,
    StationCorrection,
    StationUncertainty,
    match_observations,
    read_adj,
    read_apu,
    read_cor,
    read_measurements,
    read_statistics,
    read_xyz,
)
from geocomp.engines.dynadjust.solution import read_solution

__all__ = [
    "AdjustedMeasurement",
    "Agreement",
    "AngularFormat",
    "Comparison",
    "CoordinateRow",
    "DynAdjustEngine",
    "DynAdjustJob",
    "DynaMLDocument",
    "OutputPreamble",
    "PreparedJob",
    "ReadReport",
    "Stage",
    "StationCorrection",
    "StationUncertainty",
    "compare",
    "format_metres",
    "format_variance",
    "hp_to_radians",
    "match_observations",
    "plan",
    "radians_to_hp",
    "radians_to_seconds",
    "read_adj",
    "read_apu",
    "read_cor",
    "read_dna",
    "read_dna_stations",
    "read_dynaml",
    "read_measurements",
    "read_solution",
    "read_station_file",
    "read_statistics",
    "read_xyz",
    "seconds_to_radians",
    "station_names",
    "write_measurement_file",
    "write_station_file",
]
