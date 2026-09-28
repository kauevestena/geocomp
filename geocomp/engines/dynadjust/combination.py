# SPDX-License-Identifier: GPL-2.0-or-later
"""A combination adjusted by DynAdjust (``specs/13`` section 6, phase P9b).

The core decides *whether* DynAdjust may adjust a combination
(:func:`~geocomp.core.techniques.integration.combine.route`): not with gravity,
nor a type it has no letter for, nor in a local system, nor with orthometric
heights whose geoid the in-house core estimates with its uncertainty. This is
the engine side of the answer "yes": the combined network, already in one frame
at one epoch, written, run and read back as one solution whose provenance says
what was combined, how, and why DynAdjust.

Nothing is dropped to make the network fit: the job does not allow a partial
network, so an observation the DynaML writer would skip refuses the run
(``dynadjust_network_would_be_partial``) rather than DynAdjust adjusting a
different network from the one combined.

**What this path does not give** is the per-technique breakdown: its
redundancy numbers come from the in-house design, which DynAdjust's output does
not carry. The residuals are on the solution per observation; the report says
the breakdown is absent and why, rather than inventing one.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from geocomp.core.errors import ValidationError
from geocomp.core.techniques.integration.adjustment import CombinedAdjustment
from geocomp.core.techniques.integration.combine import Combination, route
from geocomp.engines.base import DEFAULT_TIMEOUT, ProgressCallback
from geocomp.engines.dynadjust.engine import DynAdjustEngine, DynAdjustJob

__all__ = ["adjust_with_dynadjust"]


def adjust_with_dynadjust(
    combination: Combination,
    work_dir: str | Path,
    *,
    confidence: float = 0.95,
    solution_id: str = "combined",
    engine: DynAdjustEngine | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    on_progress: ProgressCallback | None = None,
) -> CombinedAdjustment:
    """Run DynAdjust on *combination*, which routing must allow.

    Raises:
        ValidationError: ``combination_not_for_dynadjust`` with routing's reason
            when it keeps the combination in-house; the engine's own
            ``dynadjust_network_would_be_partial`` for an observation it cannot write.
    """
    routing = route(combination.network, "dynadjust")
    if routing.engine != "dynadjust":
        raise ValidationError(
            "combination_not_for_dynadjust",
            reason=routing.reason,
            expected="the in-house path (adjust_combination), which routing chose",
        )
    engine = engine or DynAdjustEngine()
    job = DynAdjustJob(
        network=combination.network,
        name="combined",
        target_frame=combination.frame,
        target_epoch=combination.epoch,
        confidence=confidence,
    )
    prepared = engine.prepare(job, work_dir)
    runs = engine.run(prepared, timeout=timeout, on_progress=on_progress)
    solution = engine.parse(runs, prepared)
    provenance = solution.provenance
    parameters = {
        **(provenance.parameters if provenance is not None else {}),
        **combination.provenance_parameters(),
        "routing": {"engine": routing.engine, "reason": routing.reason},
    }
    solution = replace(
        solution,
        id=solution_id,
        provenance=None
        if provenance is None
        else replace(
            provenance,
            algorithm_id="combined_adjustment",
            parameters=parameters,
            input_ids=combination.inputs,
        ),
    )
    return CombinedAdjustment(
        combination=combination,
        solution=solution,
        run=None,
        routing=routing,
        breakdown=(),
        geoid=(),
    )
