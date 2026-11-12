# SPDX-License-Identifier: GPL-2.0-or-later
"""The chain of algorithms a window runs, declared as data (FR-011).

ADR-0010: an interactive window computes nothing. It writes what was typed as
the inputs an algorithm reads and runs registered Processing algorithms, one
after another, each reading what the one before it wrote -- exactly the chain a
user assembles by hand in the toolbox or in the graphical modeller
(``specs/16`` section 9).

A chain is declared here, without QGIS, so that what a window is going to ask
of the algorithms can be read, fingerprinted and tested in a plain interpreter;
``geocomp.services.chain_runner`` is what runs one.

* a :class:`ChainStep` names an algorithm by its id and gives its parameters;
* a parameter may be an :class:`InputFile` -- text the step writes to a file
  first, a typed field book as the CSV the importer reads -- or a :class:`Ref`
  to a file an earlier step wrote;
* :func:`resolve` places every file in a folder and turns the declaration into
  parameters an algorithm can be run with.

Where each output goes is decided before anything runs, which is what lets a
later step refer to an earlier one's output without the chain being run to find
out where it went.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["Chain", "ChainStep", "InputFile", "Ref", "ResolvedStep", "fingerprint", "resolve"]


@dataclass(frozen=True)
class InputFile:
    """A file a step writes before it runs, and gives to its algorithm by path."""

    name: str
    text: str


@dataclass(frozen=True)
class Ref:
    """The file an earlier step wrote for one of its outputs."""

    step: str
    output: str


@dataclass(frozen=True)
class ChainStep:
    """One algorithm run.

    Attributes:
        key: Names the step within its chain, and its folder.
        algorithm: The algorithm's id, ``geocomp:<group>_<operation>``.
        parameters: By parameter name. A value of ``None`` is left out, so the
            algorithm takes it as not given.
        outputs: Each file destination the step asks for, with the file's name.
    """

    key: str
    algorithm: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedStep:
    """A step with every file placed: what an algorithm is run with."""

    key: str
    algorithm: str
    parameters: dict[str, Any]
    outputs: dict[str, Path]


@dataclass(frozen=True)
class Chain:
    """Steps run in order, each free to read what an earlier one wrote."""

    steps: tuple[ChainStep, ...]

    @property
    def algorithms(self) -> tuple[str, ...]:
        """The ids of the algorithms the chain runs, in order."""
        return tuple(step.algorithm for step in self.steps)

    def fingerprint(self) -> str:
        """What identifies the chain's inputs: equal for the same typed data and options.

        A result indexed with it is out of date the moment the field book or
        an option changes (:meth:`geocomp.jobs.document.Job.is_current`).
        """
        return fingerprint(
            [
                {
                    "key": step.key,
                    "algorithm": step.algorithm,
                    "parameters": {name: _plain(value) for name, value in step.parameters.items()},
                    "outputs": dict(step.outputs),
                }
                for step in self.steps
            ]
        )


def fingerprint(payload: Any) -> str:
    """The SHA-256 of *payload* written as canonical JSON."""
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, InputFile):
        return {"file": value.name, "sha256": hashlib.sha256(value.text.encode("utf-8")).hexdigest()}
    if isinstance(value, Ref):
        return {"ref": [value.step, value.output]}
    return value


def resolve(chain: Chain, folder: str | Path) -> tuple[ResolvedStep, ...]:
    """Place *chain*'s files under *folder* and return what each algorithm is run with.

    Each step has a subfolder of its own, named by its key. Its input files are
    written there now; its outputs are given paths there, and are written by
    the algorithm when it runs.

    Raises:
        KeyError: for a :class:`Ref` to a step that does not come earlier in the
            chain, or to an output that step does not declare. A chain that
            refers to nothing is a programming error, not a user's.
    """
    root = Path(folder)
    placed: dict[str, dict[str, Path]] = {}
    resolved: list[ResolvedStep] = []
    for step in chain.steps:
        directory = root / step.key
        directory.mkdir(parents=True, exist_ok=True)
        outputs = {name: directory / file_name for name, file_name in step.outputs.items()}
        parameters: dict[str, Any] = {}
        for name, value in step.parameters.items():
            if value is None:
                continue
            if isinstance(value, InputFile):
                target = directory / value.name
                target.write_text(value.text, encoding="utf-8")
                parameters[name] = str(target)
            elif isinstance(value, Ref):
                parameters[name] = str(placed[value.step][value.output])
            else:
                parameters[name] = value
        parameters.update({name: str(path) for name, path in outputs.items()})
        placed[step.key] = outputs
        resolved.append(
            ResolvedStep(key=step.key, algorithm=step.algorithm, parameters=parameters, outputs=outputs)
        )
    return tuple(resolved)
