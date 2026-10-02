# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-071 for every algorithm: Basic and Advanced compute the same thing (phase P12a).

*Switching between Basic and Advanced MUST NOT change results for parameters
left at their defaults.* ``specs/16`` section 5 and ``specs/ROADMAP.md`` P12's
exit criterion: *every algorithm passes the Basic/Advanced identity check*.

GeoComp holds it by construction: an advanced parameter is **flagged**, never
removed (:meth:`geocomp.algorithms.base.GeoCompAlgorithm.addAdvancedParameter`),
and its default is the Global Setting it corresponds to
(:mod:`geocomp.algorithms.defaults`). So a run in Basic mode, which cannot see
the parameter, uses exactly the value a run in Advanced mode left untouched
uses. This file checks the construction across all registered algorithms, so
that an algorithm which one day builds a different parameter set per mode, or
hides a parameter that has no value to fall back on, fails here by name.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _ids() -> list[str]:
    from geocomp.registry import ALGORITHMS

    return [spec.id for spec in ALGORITHMS]


def _advanced_flag():
    from qgis.core import QgsProcessingParameterDefinition

    return QgsProcessingParameterDefinition.Flag.FlagAdvanced


def _signature(algorithm_id: str) -> list[tuple]:
    """Every parameter as a run sees it: name, type, default, optionality, advanced or not."""
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    instance = algorithm.create({})
    advanced = _advanced_flag()
    return [
        (
            definition.name(),
            definition.type(),
            repr(definition.defaultValue()),
            bool(definition.flags() & definition.Flag.FlagOptional),
            bool(definition.flags() & advanced),
        )
        for definition in instance.parameterDefinitions()
    ]


@pytest.mark.parametrize("algorithm_id", _ids())
def test_switching_the_mode_changes_no_parameter(algorithm_id):
    from geocomp.core.settings_def import MODE_ADVANCED, MODE_BASIC
    from geocomp.services.settings_service import settings

    with settings.run_overrides({"interface.mode": MODE_BASIC}):
        basic = _signature(algorithm_id)
    with settings.run_overrides({"interface.mode": MODE_ADVANCED}):
        advanced = _signature(algorithm_id)
    assert basic == advanced


@pytest.mark.parametrize("algorithm_id", _ids())
def test_a_hidden_parameter_always_has_a_value_to_run_with(algorithm_id):
    """Basic mode cannot set an advanced parameter, so one that is required and
    has no default would make the algorithm unrunnable there -- or, worse, run
    on whatever Processing substitutes."""
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    instance = algorithm.create({})
    advanced = _advanced_flag()
    stranded = [
        definition.name()
        for definition in instance.parameterDefinitions()
        if definition.flags() & advanced
        and not definition.flags() & definition.Flag.FlagOptional
        and not definition.isDestination()
        and definition.defaultValue() is None
    ]
    assert not stranded, f"advanced, required and with no default: {stranded}"


def test_every_algorithm_is_checked():
    """Guards the parametrisation: an empty registry would pass both tests above."""
    assert len(_ids()) >= 45


def test_no_algorithm_reads_the_mode_while_it_runs():
    """The other half of identical *results*: identical parameters are not enough
    if a run itself asks which mode it is in. Nothing under ``algorithms/`` may,
    except the base class's declaration of the question."""
    from tests.conftest import PLUGIN_DIR

    readers = sorted(
        path.relative_to(PLUGIN_DIR).as_posix()
        for path in (PLUGIN_DIR / "algorithms").rglob("*.py")
        if path.name != "base.py"
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in ("is_advanced_mode", '"interface.mode"', "MODE_ADVANCED", "MODE_BASIC")
        )
    )
    assert not readers, f"these algorithms ask which mode they run in: {readers}"
