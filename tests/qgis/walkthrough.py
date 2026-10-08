# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading a tutorial's README the way its tests hold it to the toolbox (P13-2, P13-3).

A walkthrough names a step's algorithm in its heading, ``### 3. Compare two
epochs — `geocomp:monitoring_compare_epochs```, and the inputs to fill as a
list under it, ``- **Reference stations (comma-separated)**: `R1,R2```. A
choice from a list is written in italics, ``- **Mode**: *Loop*``. The tests
compare all three with the dialog: the title with the algorithm's name, every
label with one of its inputs, every italic choice with that input's options.
A reader looks for exactly those words on the screen.

The numbers the prose quotes are checked by the tests themselves, against what
the algorithms returned; :func:`quoted` is how.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple

import pytest

STEP = re.compile(r"^### \d+\. (?P<title>.+?) — `(?P<id>geocomp:\w+)`$")
FILLED = re.compile(r"^- \*\*(?P<label>.+?)\*\*: (?P<value>.*)$")
CHOICE = re.compile(r"^\*(?P<choice>[^*]+)\*")


class Step(NamedTuple):
    title: str
    algorithm_id: str
    filled: list[tuple[str, str]]


def flat(text: str) -> str:
    """*text* as one line, its block-quote markers gone: what a reader reads, not how it wraps."""
    return " ".join(line.removeprefix(">").strip() for line in text.splitlines() if line.strip())


def steps(readme: str) -> list[Step]:
    """Each step that names an algorithm, with the inputs it fills and what it fills them with."""
    found: list[Step] = []
    current: Step | None = None
    for line in readme.splitlines():
        heading = STEP.match(line)
        if heading:
            current = Step(heading["title"], heading["id"], [])
            found.append(current)
        elif line.startswith("#"):
            current = None
        elif current is not None and (filled := FILLED.match(line)):
            current.filled.append((filled["label"], filled["value"]))
    return found


def quote(readme: str) -> str:
    """The README's block quote, as one line: the words GeoComp is quoted as saying."""
    return flat("\n".join(line for line in readme.splitlines() if line.startswith(">")))


def quoted(readme: str, text: str) -> None:
    """Assert the README says *text*, however its lines wrap."""
    assert text in flat(readme), f"the README does not say {text!r}"


def mm(metres: float, places: int = 1) -> str:
    """Millimetres as the README writes them, with a typographic minus."""
    return f"{metres * 1000:.{places}f}".replace("-", "\N{MINUS SIGN}")


def algorithm(algorithm_id: str) -> Any:
    from qgis.core import QgsApplication

    registered = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert registered is not None, f"{algorithm_id} is not registered"
    return registered.create({})


def label(algorithm_id: str, name: str) -> str:
    """The label the dialog shows input *name* by."""
    instance = algorithm(algorithm_id)  # held: the definition is the algorithm's, and goes with it
    return instance.parameterDefinition(name).description()


def run(algorithm_id: str, parameters: dict) -> dict:
    from qgis.core import QgsProcessingContext, QgsProcessingFeedback

    results, ok = algorithm(algorithm_id).run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"{algorithm_id} reported failure"
    return results


def refusal(algorithm_id: str, parameters: dict) -> str:
    """What *algorithm_id* says when it refuses *parameters*, as one line."""
    from qgis.core import QgsProcessingContext, QgsProcessingException, QgsProcessingFeedback

    with pytest.raises(QgsProcessingException) as caught:
        algorithm(algorithm_id).run(
            parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
        )
    return flat(str(caught.value))


def option(algorithm_id: str, name: str, choice: str) -> int:
    """The index of *choice* among input *name*'s options, as a run is given it."""
    instance = algorithm(algorithm_id)
    options = list(instance.parameterDefinition(name).options())
    assert choice in options, (algorithm_id, name, choice, options)
    return options.index(choice)


def check_names(readme: str) -> None:
    """Every step's title, input and choice is the dialog's own."""
    for step in steps(readme):
        instance = algorithm(step.algorithm_id)
        assert step.title == instance.displayName(), step.algorithm_id
        assert step.filled, f"step {step.title!r} fills nothing"
        definitions = {definition.description(): definition for definition in instance.parameterDefinitions()}
        for name, value in step.filled:
            assert name in definitions, (step.algorithm_id, name, sorted(definitions))
            choice = CHOICE.match(value)
            if choice and hasattr(definitions[name], "options"):
                assert choice["choice"] in definitions[name].options(), (step.algorithm_id, name, value)
