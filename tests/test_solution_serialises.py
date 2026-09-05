# SPDX-License-Identifier: GPL-2.0-or-later
"""Everything an adjustment produces must survive being written out.

A ``Solution`` is the durable artefact: it is what the algorithms write, what
storage keeps, and what multi-epoch analysis reads back. So it has to be JSON,
and every number in it has to be a number ``json`` recognises.

That is less automatic than it sounds. The adjustment is NumPy throughout, and
``np.float64`` subclasses ``float`` -- so it serialises silently and nobody
notices -- while ``np.bool_`` does **not** subclass ``bool`` and the encoder
refuses it. One leaked: the w-test's ``passed`` was a comparison of two NumPy
scalars, and every adjustment that wrote a solution failed at the last step with
a ``TypeError`` naming neither the field nor the test it came from.

Nothing here needs QGIS. The bug reached the algorithms only because no tier-1
test had ever asked a real adjustment's solution to serialise -- it checked the
numbers and stopped. This module asks.
"""

from __future__ import annotations

import json

import pytest

from geocomp.core.adjustment.least_squares import (
    AdjustmentOptions,
    adjust,
    to_observation_results,
    to_solution,
)
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.models import DatumDefinition, Epoch, Solution
from geocomp.core.statistics.tests import data_snooping, global_test
from tests.networks import levelling_loop, triangulateration, trilateration

CASES = {
    "levelling": (levelling_loop, Frame.HEIGHT_1D),
    "trilateration": (trilateration, Frame.PLANE_2D),
    "triangulateration": (triangulateration, Frame.PLANE_2D),
}


def _solution(builder, frame: Frame) -> Solution:
    reference = builder()
    options = AdjustmentOptions(frame=frame, datum=DatumDefinition.FIXED)
    run = adjust(reference.network, options)
    test = global_test(run.variance_factor_aposteriori, run.degrees_of_freedom)
    snooping = data_snooping(
        run.residuals,
        run.cofactor_residuals,
        run.system.weight,
        run.system.row_labels,
        variance_factor=run.variance_factor_aposteriori,
    )
    return to_solution(
        run,
        reference.network,
        solution_id=f"serialise-{frame.value}",
        crs=reference.network.crs or "EPSG:31982",
        epoch=Epoch.from_decimal_year(2026.0),
        datum=DatumDefinition.FIXED,
        observation_results=to_observation_results(run, snooping=snooping),
        global_test=test,
    )


@pytest.mark.parametrize("name", sorted(CASES))
class TestASolutionIsWritable:
    def test_it_serialises(self, name):
        """The check that was missing. Not "the numbers are right" -- that is
        tested elsewhere -- but "the document can be written at all"."""
        builder, frame = CASES[name]
        json.dumps(_solution(builder, frame).to_dict())

    def test_it_reads_back_equal(self, name):
        builder, frame = CASES[name]
        payload = _solution(builder, frame).to_dict()
        assert Solution.from_dict(json.loads(json.dumps(payload))).to_dict() == payload

    def test_no_numpy_scalar_survives_into_the_document(self, name):
        """``np.float64`` serialises silently because it subclasses ``float``,
        so a leak is invisible until one that does not -- ``np.bool_`` -- comes
        through the same path. Every leaf is required to be an exact built-in."""
        import numpy as np

        builder, frame = CASES[name]
        offenders: list[str] = []

        def walk(node, path: str) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")
            elif isinstance(node, np.generic) or type(node) not in (
                bool,
                int,
                float,
                str,
                type(None),
            ):
                offenders.append(f"{path}: {type(node).__name__}")

        walk(_solution(builder, frame).to_dict(), name)
        assert not offenders, "\n".join(offenders)


def test_a_numpy_bool_cannot_reach_a_test_result():
    """The specific leak, coerced at the boundary so no producer can repeat it.

    ``np.bool_`` is not a ``bool``: it does not subclass it, and the JSON
    encoder refuses it. Coercing in ``TestResult`` means every producer is
    covered, including ones not written yet."""
    import numpy as np

    from geocomp.core.models import TestResult

    result = TestResult(name="global", statistic=1.0, passed=np.bool_(True))
    assert type(result.passed) is bool
    assert json.dumps(result.to_dict())
