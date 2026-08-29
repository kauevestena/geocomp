# SPDX-License-Identifier: GPL-2.0-or-later
"""Joining DynAdjust's output files into one :class:`Solution` (FR-323).

``specs/07-engine-dynadjust.md`` section 5. Each file holds a different part of
the answer -- the ``.adj`` the coordinates, residuals and statistics, the
``.apu`` the covariances and ellipses, the ``.cor`` the shifts from the initial
coordinates -- and none of them is a solution on its own. This module is where
they become one, in the same type the in-house core produces, which is what
makes P6 a cross-validation rather than a second pipeline (specs/03 section 3.2).

The joining is by station name, which is the identifier DynAdjust round-trips.
It is checked rather than assumed: a station in one file and not the other is
reported, because a silently half-populated solution -- coordinates without
their covariance -- looks fine and is not.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError
from geocomp.core.models.network import Network
from geocomp.core.models.solution import (
    AdjustedStation,
    DatumDefinition,
    Provenance,
    Solution,
    SolutionKind,
)
from geocomp.core.uncertainty import Covariance, UncertaintyMode
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.read_output import (
    AngularFormat,
    CoordinateRow,
    StationUncertainty,
    match_observations,
    printed_rows,
    read_adj,
    read_apu,
    read_cor,
)

__all__ = ["adjusted_stations", "datum_definition", "printed_rows", "read_solution"]


def datum_definition(rows: Iterable[CoordinateRow]) -> DatumDefinition:
    """What the constraint codes say about how the datum was fixed.

    DynAdjust writes one character per axis: ``C`` for constrained, ``F`` for
    free. Every axis free on every station is a solution with no datum at all;
    anything held makes it a constrained solution. The distinction matters
    beyond bookkeeping -- differencing a constrained solution against a
    minimum-constraint one across epochs measures the constraint rather than
    any motion (specs/14 section 2).

    Note what is *not* claimed: DynAdjust's ``C`` does not distinguish a
    genuinely fixed station from a tightly weighted one, so this never returns
    ``MINIMUM_CONSTRAINT`` or ``INNER_CONSTRAINT``. Those would be inferences.
    """
    codes = {code.strip().upper() for row in rows for code in row.constraint}
    if not codes:
        return DatumDefinition.NONE
    return DatumDefinition.CONSTRAINED if "C" in codes else DatumDefinition.NONE


def adjusted_stations(
    rows: Iterable[CoordinateRow],
    uncertainties: Iterable[StationUncertainty] = (),
) -> tuple[AdjustedStation, ...]:
    """Join the coordinate table to the positional-uncertainty file.

    Without an ``.apu`` the stations still come back, with their coordinates and
    corrections and no covariance -- which is the truth about a run that was not
    asked for one, rather than a diagonal invented from the standard deviations
    the ``.adj`` happens to print (specs/07 section 5 rule 2).

    With one, each station gains its 3x3 block and its error ellipse. The block
    is used only when its frame matches the position's: an ``.apu`` written with
    ``--output-apu-vcv-units 1`` holds a local e/n/up matrix, which does not
    describe cartesian X, Y and Z components and must not be attached to them.
    """
    by_id = {item.station_id: item for item in uncertainties}
    stations: list[AdjustedStation] = []
    for row in rows:
        item = by_id.pop(row.station_id, None)
        covariance: Covariance | None = None
        if item is not None:
            covariance = _matching_block(row, item)
        stations.append(
            AdjustedStation(
                station_id=row.station_id,
                position=row.position,
                covariance=covariance,
                ellipse=item.ellipse if item is not None else None,
                positional_uncertainty=item.horizontal_uncertainty if item is not None else None,
                correction=row.correction,
            )
        )
    if by_id:
        raise DataError(
            "dynadjust_uncertainty_for_an_unknown_station",
            stations=sorted(by_id)[:10],
            hint="the .apu names stations the .adj does not; the two are not from one run",
        )
    return tuple(stations)


def _matching_block(row: CoordinateRow, item: StationUncertainty) -> Covariance | None:
    """The station's covariance, if it is in the position's own frame."""
    axes = tuple(label.rsplit(".", 1)[-1] for label in item.covariance.labels)
    if axes == row.position.system.component_names:
        return item.covariance
    if axes == ("x", "y", "z") and row.position.system.component_names == ("x", "y", "z"):
        return item.covariance
    return None


def read_solution(
    adj_path: str | Path,
    *,
    network: Network,
    apu_path: str | Path | None = None,
    cor_path: str | Path | None = None,
    angular_format: AngularFormat | None = None,
    provenance: Provenance | None = None,
    solution_id: str | None = None,
) -> Solution:
    """One :class:`Solution` from the files of one ``dnaadjust`` run.

    *network* is what supplies the observation identifiers: DynAdjust's rows
    carry none, so they are matched back by the file order it preserves, and the
    match is verified row by row (see
    :func:`~geocomp.engines.dynadjust.read_output.match_observations`). It is
    also where the station names come from, which is what lets a name wider than
    its column be read at all.

    The ``.apu`` and ``.cor`` are optional because DynAdjust writes them only
    when asked. Their absence costs the covariances and nothing else.
    """
    known = set(network.stations)
    rows, measurements, statistics, preamble = read_adj(
        adj_path, known=known, angular_format=angular_format
    )

    uncertainties: list[StationUncertainty] = []
    if apu_path is not None:
        uncertainties, apu_preamble = read_apu(
            apu_path, known=known, angular_format=angular_format
        )
        if apu_preamble.version != preamble.version:
            raise DataError(
                "dynadjust_output_versions_disagree",
                adj=preamble.version,
                apu=apu_preamble.version,
                hint="the .adj and .apu are not from the same DynAdjust",
            )
    if cor_path is not None:
        # Read for its own sake: the ``.cor`` repeats the ``.adj``'s corrections
        # and adds the azimuth and distance of each shift. Reading it here means
        # a malformed one is a failure now rather than a surprise later.
        read_cor(cor_path, known=known)

    epoch = preamble.epoch
    if epoch is None:
        raise DataError(
            "dynadjust_output_without_an_epoch",
            path=str(adj_path),
            hint=(
                "FR-105: GeoComp will not assume an epoch, and a solution without "
                "one cannot enter a comparison"
            ),
        )

    return Solution(
        id=solution_id or f"{network.id}:dynadjust",
        network_id=network.id,
        kind=SolutionKind.ADJUSTMENT,
        crs=preamble.reference_frame or network.crs,
        epoch=epoch,
        datum_definition=datum_definition(rows),
        adjusted_stations=adjusted_stations(rows, uncertainties),
        parameter_covariance=_full_covariance(uncertainties),
        observation_results=tuple(match_observations(measurements, network)),
        statistics=statistics,
        # DynAdjust propagates the full variance matrix; nothing here is an
        # approximation GeoComp made (FR-203).
        uncertainty_mode=UncertaintyMode.RIGOROUS,
        provenance=provenance,
    )


def _full_covariance(uncertainties: list[StationUncertainty]) -> Covariance | None:
    """Assemble the whole parameter matrix, when the ``.apu`` carries it.

    Only under ``--output-all-covariances``: without it the file holds each
    station's own block and nothing between them, and a block-diagonal matrix
    assembled from those would assert that every pair of stations is
    uncorrelated -- which is false in every adjusted network, and is exactly the
    kind of plausible fabrication FR-322 forbids.
    """
    if not uncertainties or not any(item.cross for item in uncertainties):
        return None

    order = [item.station_id for item in uncertainties]
    index = {name: position * 3 for position, name in enumerate(order)}
    size = 3 * len(order)
    matrix = np.zeros((size, size), dtype=float)
    for item in uncertainties:
        start = index[item.station_id]
        matrix[start : start + 3, start : start + 3] = item.covariance.matrix
        for other, block in item.cross.items():
            if other not in index:
                raise DataError(
                    "dynadjust_covariance_for_an_unknown_station",
                    station=item.station_id,
                    other=other,
                )
            column = index[other]
            matrix[start : start + 3, column : column + 3] = block
            matrix[column : column + 3, start : start + 3] = block.T

    labels = tuple(label for item in uncertainties for label in item.covariance.labels)
    return Covariance(matrix=matrix, labels=labels, units=(Unit.METRE,) * size)
