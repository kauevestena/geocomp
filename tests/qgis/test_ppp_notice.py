# SPDX-License-Identifier: GPL-2.0-or-later
"""FR-604's notice, where the Absolute modes are chosen and run (specs/08 criterion 8, specs/11 criterion 8).

*GeoComp MUST state this in the UI rather than silently producing a degraded
result.* The notice was written in P7 and recorded as met; the P12c audit found
that nothing asserted it, so a refactor of the help could have dropped it with
every test still green.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis

ABSOLUTE = ("geocomp:gnss_absolute_static", "geocomp:gnss_absolute_kinematic")
RELATIVE = ("geocomp:gnss_relative_static", "geocomp:gnss_relative_kinematic")


def _algorithm(algorithm_id: str):
    from qgis.core import QgsApplication

    return QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.mark.parametrize("algorithm_id", ABSOLUTE)
def test_an_absolute_mode_states_the_limitation_in_its_help(algorithm_id):
    from geocomp.algorithms.gnss.common import ppp_limitation_notice

    algorithm = _algorithm(algorithm_id)
    assert algorithm.shortHelpString().startswith(ppp_limitation_notice())
    assert "PPP" in algorithm.shortDescription()


@pytest.mark.parametrize("algorithm_id", RELATIVE)
def test_a_relative_mode_does_not(algorithm_id):
    """A notice on every mode would be noise, and read as boilerplate."""
    from geocomp.algorithms.gnss.common import ppp_limitation_notice

    assert ppp_limitation_notice() not in _algorithm(algorithm_id).shortHelpString()


@pytest.mark.parametrize("algorithm_id", ABSOLUTE)
def test_a_run_warns_before_anything_else(algorithm_id, tmp_path):
    """At the top of the log, before a result exists to be mistaken for a good one.

    An empty folder stops the run at the scan, which is after the warning and
    before the engine, so this needs no ``rnx2rtkp``.
    """
    from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingFeedback

    class Listening(QgsProcessingFeedback):
        def __init__(self):
            super().__init__()
            self.warnings = []

        def pushWarning(self, text):  # noqa: N802 -- the Qt interface
            self.warnings.append(text)

    feedback = Listening()
    with pytest.raises(QgsProcessingException):
        _algorithm(algorithm_id).run(
            {"FOLDER": str(tmp_path)}, QgsProcessingContext(), feedback, catchExceptions=False
        )
    assert feedback.warnings, "the run stopped before warning"
    assert "PPP" in feedback.warnings[0] and "limited" in feedback.warnings[0]
