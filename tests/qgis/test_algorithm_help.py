# SPDX-License-Identifier: GPL-2.0-or-later
"""Every algorithm's help documents every parameter with its unit (specs/16 §8, criterion 6).

And specs/20 §2's structural check of the same, which P12c's audit found was
never implemented: the help of four algorithms was checked, of 46.

A number's unit is stated in its label -- ``(m)``, ``(rad)``, ``(hPa)`` -- and
the help lists the labels, so one rule holds both the dialog and the help.
A quantity without a unit is named in :data:`DIMENSIONLESS` with what it is.
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.qgis

#: Numeric parameters with no unit to state, and what each is instead.
DIMENSIONLESS = {
    "CONFIDENCE": "a probability",
    "ALPHA": "a probability",
    "BETA": "a probability",
    "VARIANCE_FACTOR": "a ratio of variances",
    "MAX_ITERATIONS": "a count",
    "SEGMENTATION_THRESHOLD": "a count of stations",
    "DRIFT_DEGREE": "a polynomial degree",
    "STADIA_FACTOR": "a ratio",
    "INFLATION": "a factor on a variance",
    "AMPLIFICATION": "the gravimetric factor, a ratio",
    "REFRACTION": "the refraction coefficient, a ratio of radii",
    "REFRACTION_SIGMA": "the uncertainty of that ratio",
}

#: A unit in a label: "(m)", "(m, 0 = ...)", "(°)", ", degrees", "decimal year".
UNIT = re.compile(r"\(|, degrees|decimal year")


def _algorithms():
    from qgis.core import QgsApplication

    from geocomp.registry import ALGORITHMS

    registry = QgsApplication.processingRegistry()
    return [registry.algorithmById(f"geocomp:{spec.name}") for spec in ALGORITHMS]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _ids():
    from geocomp.registry import ALGORITHMS

    return [spec.name for spec in ALGORITHMS]


@pytest.mark.parametrize("name", _ids())
def test_the_help_lists_every_parameter_and_output(name):
    from qgis.core import QgsApplication

    algorithm = QgsApplication.processingRegistry().algorithmById(f"geocomp:{name}")
    help_text = algorithm.shortHelpString()
    assert len(help_text) > 200, "a help that says almost nothing"
    for parameter in algorithm.parameterDefinitions():
        if not parameter.isDestination():
            assert parameter.description() in help_text, parameter.name()
    for output in algorithm.outputDefinitions():
        assert output.description() in help_text, output.name()


@pytest.mark.parametrize("name", _ids())
def test_every_number_states_its_unit(name):
    from qgis.core import QgsApplication, QgsProcessingParameterNumber

    algorithm = QgsApplication.processingRegistry().algorithmById(f"geocomp:{name}")
    missing = [
        f"{parameter.name()}: {parameter.description()!r}"
        for parameter in algorithm.parameterDefinitions()
        if isinstance(parameter, QgsProcessingParameterNumber)
        and parameter.name() not in DIMENSIONLESS
        and not UNIT.search(parameter.description())
    ]
    assert not missing, "numbers with no unit in their label: " + "; ".join(missing)


def test_the_base_class_words_are_translated():
    """The help's headings and the toolbox's group names are the base class's
    own; looked up under each algorithm's context, they had never been
    translated -- "Requirement" in no help, no group name in the toolbox."""
    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QCoreApplication, QTranslator

    class Marking(QTranslator):
        def translate(self, context, source, disambiguation=None, n=-1):
            return f"«{source}»" if context == "GeoCompAlgorithm" else None

    translator = Marking()
    QCoreApplication.installTranslator(translator)
    try:
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_network_adjust"
        )
        help_text = algorithm.shortHelpString()
        group = algorithm.group()
    finally:
        QCoreApplication.removeTranslator(translator)
    assert "«Requirement»" in help_text and "«Parameters»" in help_text
    assert group == "«Analysis»"
