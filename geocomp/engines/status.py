# SPDX-License-Identifier: GPL-2.0-or-later
"""Which engines are installed, at what version, under what licence (specs/21 criterion 8).

One answer for the two places a user asks: the About dialog and the system
report a support request attaches. Until P12c's audit neither asked the
engines. The dialog named their licences, said nothing of their versions and
announced that engine integration "arrives in later development phases"; the
report said both were "not integrated yet". Both had been false since P6 and
P7.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from geocomp.core.errors import GeoCompError
from geocomp.engines.base import EngineVersion

__all__ = ["EngineStatus", "engine_status"]


@dataclass(frozen=True)
class EngineStatus:
    """One engine: what it is, whose it is, and what this machine has of it.

    Attributes:
        name: As a user knows it.
        licence: Its own licence; it is not part of GeoComp (``THIRD_PARTY.md``).
        attribution: Who wrote it.
        url: Where it comes from.
        version: What was found, or ``None`` when it is not installed.
    """

    name: str
    licence: str
    attribution: str
    url: str
    version: EngineVersion | None


def _detected(probe: Callable[[], EngineVersion | None]) -> EngineVersion | None:
    # An engine that is present but will not say its version -- a broken
    # install, a configured path that is wrong -- is reported as not found, not
    # allowed to stop the dialog or the report that would help diagnose it.
    try:
        return probe()
    except (GeoCompError, OSError):
        return None


def engine_status(*, dynadjust=None, rtklib=None) -> list[EngineStatus]:
    """Every engine GeoComp runs, probed where the algorithms would find it.

    Args:
        dynadjust / rtklib: The engines as the plugin builds them
            (:mod:`geocomp.services.engines`), with the configured path and the
            managed installation; without them, the system path alone.
    """
    from geocomp.engines.dynadjust.engine import DynAdjustEngine
    from geocomp.engines.rtklib.engine import RtklibEngine

    dynadjust = dynadjust or DynAdjustEngine()
    rtklib = rtklib or RtklibEngine()
    return [
        EngineStatus(
            name="DynAdjust",
            licence="Apache License 2.0",
            attribution="Geoscience Australia",
            url="https://github.com/GeoscienceAustralia/DynAdjust",
            version=_detected(dynadjust.detect),
        ),
        EngineStatus(
            name="RTKLIB (rnx2rtkp)",
            licence="BSD-2-Clause",
            attribution="T. Takasu, and the RTKLIB-EX contributors",
            url="https://www.rtklib.com/",
            version=_detected(rtklib.version),
        ),
    ]
