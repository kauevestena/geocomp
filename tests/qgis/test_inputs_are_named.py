# SPDX-License-Identifier: GPL-2.0-or-later
"""Every algorithm checks its inputs before computing, and names the one it refuses (specs/16 criterion 7).

Over every algorithm the provider registers and every input it declares, three
ways an input can be wrong:

* a file or folder that does not exist -- refused by the dialog's check and by
  a run from PyQGIS alike, before anything is written;
* a mandatory input left out;
* a file of the wrong kind -- not JSON, not a gravimeter export, a field book
  whose header maps nothing.

Each refusal must carry the label the dialog shows for the input at fault.
P12c-6 found none of 38 missing files named that way: the path alone at best,
and a traceback, an internal code or "could not complete the operation" at
worst (``geocomp/algorithms/inputs.py``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

#: Algorithms that accept the placeholder of the wrong-kind test as a valid
#: input, each with why: there is nothing to refuse.
#: A refusal that reached the user as GeoComp's internal code -- with its
#: context (``data.x (path=...)``) or inside "could not complete the operation
#: (data.x)" -- rather than as a sentence. On Linux such a refusal still
#: carried the input's path verbatim and was named after the input; on Windows
#: the path is escaped in it, and that is how *Save to a project store* was
#: found showing its code.
CODE = re.compile(r"\b(?:geocomp|validation|data|computation|engine|storage)\.[a-z0-9_]+(?: \(|\))")

ACCEPTS_ANY_CONTENT = {
    "geocomp:gnss_scan_sessions": "an empty folder is a folder with no sessions, which it reports",
    "geocomp:project_tutorial_dataset": "its only input is the folder it writes into",
}


def _algorithms(provider):
    return sorted(provider.algorithms(), key=lambda algorithm: algorithm.id())


def _placeholder(definition, tmp_path: Path, tag: str):
    """A value that passes for *definition* without saying anything about the run."""
    from qgis.core import (
        QgsProcessingParameterBoolean,
        QgsProcessingParameterCrs,
        QgsProcessingParameterEnum,
        QgsProcessingParameterFile,
        QgsProcessingParameterMultipleLayers,
        QgsProcessingParameterNumber,
        QgsProcessingParameterString,
    )

    if isinstance(definition, QgsProcessingParameterMultipleLayers):
        paths = [tmp_path / f"{tag}-{definition.name()}-{n}.json" for n in (1, 2)]
        for path in paths:
            path.write_text("this is not what it should be\n", encoding="utf-8")
        return [str(path) for path in paths]
    if isinstance(definition, QgsProcessingParameterFile):
        if definition.behavior() == QgsProcessingParameterFile.Folder:
            folder = tmp_path / f"{tag}-{definition.name()}"
            folder.mkdir(exist_ok=True)
            return str(folder)
        path = tmp_path / f"{tag}-{definition.name()}.{definition.extension() or 'json'}"
        path.write_text("this is not what it should be\n", encoding="utf-8")
        return str(path)
    if definition.defaultValue() is not None:
        return definition.defaultValue()
    if isinstance(definition, QgsProcessingParameterString):
        return "X"
    if isinstance(definition, QgsProcessingParameterNumber):
        return 1.0
    if isinstance(definition, QgsProcessingParameterEnum):
        return 0
    if isinstance(definition, QgsProcessingParameterBoolean):
        return False
    if isinstance(definition, QgsProcessingParameterCrs):
        return "EPSG:4326"
    return None


def _parameters(algorithm, tmp_path: Path, tag: str) -> dict:
    """Every input given a placeholder, every output a path in *tmp_path*."""
    parameters = {}
    for definition in algorithm.parameterDefinitions():
        if definition.isDestination():
            parameters[definition.name()] = str(tmp_path / f"{tag}-{definition.name()}.out")
            continue
        value = _placeholder(definition, tmp_path, tag)
        if value is not None:
            parameters[definition.name()] = value
    return parameters


def _run(algorithm, parameters):
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    return algorithm.create({}).run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )


def _inputs(algorithm, kind):
    return [d for d in algorithm.parameterDefinitions() if isinstance(d, kind) and not d.isDestination()]


def test_a_missing_file_or_folder_is_refused_before_the_run_and_named(geocomp_provider, tmp_path):
    from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingParameterFile

    unnamed = []
    checked = 0
    for algorithm in _algorithms(geocomp_provider):
        for definition in _inputs(algorithm, QgsProcessingParameterFile):
            tag = f"{algorithm.name()}-{definition.name()}"
            parameters = _parameters(algorithm, tmp_path, tag)
            # With the input's own extension, so what is refused is that it is
            # missing and not QGIS's filter.
            nowhere = str(tmp_path / "nowhere" / f"{tag}.{definition.extension() or 'json'}")
            parameters[definition.name()] = nowhere
            checked += 1

            ok, message = algorithm.create({}).checkParameterValues(parameters, QgsProcessingContext())
            if ok or definition.description() not in message:
                unnamed.append(f"{algorithm.id()} {definition.name()}, dialog: {message!r}")
            try:
                _run(algorithm, parameters)
                unnamed.append(f"{algorithm.id()} {definition.name()}: ran with a missing input")
                continue
            except QgsProcessingException as error:
                text = str(error)
            if definition.description() not in text or nowhere not in text:
                unnamed.append(f"{algorithm.id()} {definition.name()}, run: {text!r}")
            written = [
                name
                for name, value in parameters.items()
                if algorithm.parameterDefinition(name).isDestination() and Path(value).exists()
            ]
            if written:
                unnamed.append(f"{algorithm.id()} {definition.name()}: wrote {written} before refusing")
    assert checked > 70, "the walk found too few file inputs to mean anything"
    assert not unnamed, "\n".join(unnamed)


def test_a_mandatory_input_left_out_is_named(geocomp_provider, tmp_path):
    from qgis.core import QgsProcessingException, QgsProcessingParameterDefinition

    unnamed = []
    checked = 0
    for algorithm in _algorithms(geocomp_provider):
        for definition in algorithm.parameterDefinitions():
            mandatory = not (definition.flags() & QgsProcessingParameterDefinition.FlagOptional)
            if definition.isDestination() or not mandatory or definition.defaultValue() is not None:
                continue
            tag = f"{algorithm.name()}-{definition.name()}"
            parameters = _parameters(algorithm, tmp_path, tag)
            parameters.pop(definition.name(), None)
            checked += 1
            try:
                _run(algorithm, parameters)
                unnamed.append(f"{algorithm.id()} {definition.name()}: ran without it")
            except QgsProcessingException as error:
                if definition.description() not in str(error):
                    unnamed.append(f"{algorithm.id()} {definition.name()}: {str(error)!r}")
    assert checked > 40
    assert not unnamed, "\n".join(unnamed)


def test_an_input_of_the_wrong_kind_is_refused_and_named(geocomp_provider, tmp_path):
    """Every file input given text that is no GeoComp document and no export.

    Which input an algorithm reads first decides which one it refuses, so the
    assertion is that the refusal names *an* input, by its label -- and that it
    is a refusal at all, not a traceback.
    """
    from qgis.core import QgsProcessingException, QgsProcessingParameterFile

    unnamed = []
    for algorithm in _algorithms(geocomp_provider):
        files = _inputs(algorithm, QgsProcessingParameterFile)
        if not files or algorithm.id() in ACCEPTS_ANY_CONTENT:
            continue
        parameters = _parameters(algorithm, tmp_path, algorithm.name())
        labels = [d.description() for d in algorithm.parameterDefinitions() if not d.isDestination()]
        try:
            _run(algorithm, parameters)
        except QgsProcessingException as error:
            if not any(label in str(error) for label in labels):
                unnamed.append(f"{algorithm.id()}: {str(error)!r}")
            elif CODE.search(str(error)):
                unnamed.append(f"{algorithm.id()}: a code, not a sentence: {str(error)!r}")
            continue
        except Exception as error:  # noqa: BLE001 -- what is asserted is that this does not happen
            unnamed.append(f"{algorithm.id()}: {type(error).__name__} escaped: {error}")
            continue
        if any(d.name() in parameters for d in files):
            unnamed.append(f"{algorithm.id()}: accepted inputs of the wrong kind")
    assert not unnamed, "\n".join(unnamed)


def test_a_refusal_carrying_an_inputs_path_is_said_against_that_input(geocomp_provider, tmp_path):
    """The rule itself, on one algorithm with two documents: a network given
    where a solution is expected is refused against the input it was given as."""
    import json

    from qgis.core import QgsProcessingException

    from tests.networks import trilateration

    network = tmp_path / "network.json"
    network.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
    algorithm = next(a for a in geocomp_provider.algorithms() if a.id() == "geocomp:project_report")
    with pytest.raises(QgsProcessingException) as caught:
        _run(algorithm, {"SOLUTION": str(network), "OUTPUT_HTML": str(tmp_path / "report.html")})
    label = algorithm.parameterDefinition("SOLUTION").description()
    assert str(caught.value).startswith(label)
    assert "network document, not a solution" in str(caught.value)


def test_a_path_is_recognised_as_a_code_without_a_template_shows_it():
    """``repr()`` doubles a Windows path's backslashes; the input is still named."""
    from geocomp.algorithms.inputs import _carries

    path = r"C:\Users\surveyor\network.json"
    assert _carries(f"data.some_code (path={path!r})", path)
    assert _carries(f"'{path}' could not be read as a JSON document", path)
    assert not _carries(r"data.some_code (path='C:\\Users\\surveyor\\other.json')", path)
