# SPDX-License-Identifier: GPL-2.0-or-later
"""Base class for every GeoComp Processing algorithm.

Fixes the conventions of ``specs/16-processing-provider.md`` in one place so
that twenty algorithms behave like one plugin: identity derived from the
registry, translation, Basic/Advanced parameter gating, and the rule that
``processAlgorithm`` orchestrates but contains no geodetic mathematics.

**FR-071 is the invariant that matters here.** A parameter hidden in Basic mode
takes exactly the value it would take as the Advanced default: gating changes
what is *shown*, never what is *computed*. Without that, a Basic-mode result
would be a cheaper approximation a professional could not defend, which would
defeat the "modo comercial" framing the research project gives it.
"""

from __future__ import annotations

import functools
import html
from typing import Any

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingParameterDefinition,
)
from qgis.PyQt.QtCore import QCoreApplication

from geocomp.core.number_format import numbers_for
from geocomp.core.settings_def import MODE_ADVANCED
from geocomp.registry import ALGORITHMS, AlgorithmSpec

#: The context of the base class's own words: the help's headings, the group names.
_CONTEXT = "GeoCompAlgorithm"

__all__ = ["GeoCompAlgorithm", "worked_examples_of"]

_BY_CLASS: dict[str, AlgorithmSpec] = {spec.class_name: spec for spec in ALGORITHMS}


def worked_examples_of(algorithm_id: str) -> list[str]:
    """The shipped datasets whose walkthrough runs *algorithm_id*, in the order they install.

    Read from the walkthroughs' declared chains
    (:mod:`geocomp.algorithms.project.worked_examples`), which the tier-3 tests
    hold to each README's steps. Imported here, not at the top: that module
    imports algorithm modules, which import this one.
    """
    from geocomp.algorithms.project.worked_examples import WORKED

    return [name for name, chain in WORKED.items() if any(s.algorithm == algorithm_id for s in chain())]

class GeoCompAlgorithm(QgsProcessingAlgorithm):
    """Common behaviour for GeoComp algorithms.

    Subclasses implement :meth:`initAlgorithm` and :meth:`processAlgorithm`, and
    are declared in :mod:`geocomp.registry`; identity, group and menu placement
    come from that declaration rather than being restated here, so the two can
    never disagree.
    """

    #: Translation context. One per algorithm keeps Linguist navigable.
    TR_CONTEXT = "GeoCompAlgorithm"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Every ``processAlgorithm`` checks its inputs first, names the one it
        refuses, and writes all its outputs or none (specs/16 §7).

        Wrapped here, when the class is defined, so that no algorithm can leave
        a rule out: :mod:`geocomp.algorithms.inputs` and
        :mod:`geocomp.algorithms.transaction` say what each does.
        """
        super().__init_subclass__(**kwargs)
        own = cls.__dict__.get("processAlgorithm")
        if own is not None:
            from geocomp.algorithms.inputs import validated
            from geocomp.algorithms.transaction import transactional

            cls.processAlgorithm = validated(transactional(_in_the_display_locale(own)))

    def checkParameterValues(
        self, parameters: dict[str, Any], context: QgsProcessingContext
    ) -> tuple[bool, str]:
        """GeoComp's check, then QGIS's, each naming the input by its label (specs/16 §7).

        The dialog and ``processing.run`` call this before a run starts, so a
        missing file is refused with its parameter named before anything runs.
        QGIS's own refusal names the parameter by its internal name ("Incorrect
        parameter value for VELOCITIES"), which the dialog never shows; it is
        said against the label instead.
        """
        from geocomp.algorithms.inputs import input_problem

        problem = input_problem(self, parameters, context)
        if problem is not None:
            return False, problem
        ok, message = super().checkParameterValues(parameters, context)
        if ok:
            return ok, message
        for definition in self.parameterDefinitions():
            if message.rstrip(". ").endswith(definition.name()):
                return False, _tr("%1: this value cannot be used.").replace("%1", definition.description())
        return ok, message

    def about_input(self, name: str, message: str) -> str:
        """*message*, said against input *name* by the label the dialog shows (specs/16 §7).

        For a refusal that knows which input it is about but carries no path the
        run's wrapper could recognise it by.
        """
        label = self.parameterDefinition(name).description()
        if label in message:
            return message
        return _tr("%1: %2").replace("%1", label).replace("%2", message)

    @classmethod
    def spec(cls) -> AlgorithmSpec:
        """The registry entry for this class."""
        try:
            return _BY_CLASS[cls.__name__]
        except KeyError:  # pragma: no cover - caught by the parity test first
            raise RuntimeError(
                f"{cls.__name__} is not declared in geocomp.registry.ALGORITHMS"
            ) from None

    # -- identity (specs/16 section 3) -----------------------------------

    def name(self) -> str:
        """Stable, never translated. Saved models and scripts store this."""
        return self.spec().name

    def group(self) -> str:
        """The translated label of the algorithm's group in the toolbox."""
        return _group_label(self.spec().group)

    def groupId(self) -> str:
        """The id of the algorithm's group, from its registry entry."""
        return self.spec().group

    def createInstance(self) -> GeoCompAlgorithm:
        """A fresh instance of the same algorithm, as Processing asks for one per run."""
        return type(self)()

    def tr(self, text: str) -> str:
        """Translate a string in the algorithm's own translation context."""
        return QCoreApplication.translate(self.TR_CONTEXT, text)

    # -- Basic / Advanced gating (FR-070, FR-071) ------------------------

    def is_advanced_mode(self) -> bool:
        """Whether the user is in Advanced mode.

        Read through the settings service so the run, project and global scopes
        all apply (FR-068).
        """
        from geocomp.services.settings_service import settings

        return settings.value("interface.mode") == MODE_ADVANCED

    def addAdvancedParameter(self, parameter: QgsProcessingParameterDefinition) -> None:
        """Add *parameter* flagged as advanced, and hidden in Basic mode.

        Hidden, not removed: the parameter exists in both modes with the same
        default, so a run in Basic mode uses exactly the value a run in Advanced
        mode left untouched. That is what makes FR-071 hold structurally rather
        than by discipline -- there is one default, not a Basic one and an
        Advanced one -- and why a script or a model may still set it.

        Until P12c-13 it was flagged advanced in both modes, so the mode changed
        nothing a user could see: QGIS shows advanced parameters, collapsed,
        whatever GeoComp's mode says.
        """
        flags = parameter.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced
        if not self.is_advanced_mode():
            flags |= QgsProcessingParameterDefinition.Flag.FlagHidden
        parameter.setFlags(flags)
        self.addParameter(parameter)

    # -- help (specs/16 section 8) ---------------------------------------

    def shortHelpString(self) -> str:
        """Every algorithm documents what it does and every parameter with units.

        Subclasses override :meth:`help_body`, which says what the algorithm
        does. This adds what ``specs/16`` section 8 asks of every help and no
        body did until P12c: each parameter with its unit, and each output.
        They are the parameters' own labels, which state their units -- a test
        holds every number to it -- so the list cannot drift from the dialog.
        Then, since P13-13, the tutorials whose walkthrough runs it, so a reader
        can see it used on real data; and the requirement, so a reader can find
        the specification.
        """
        body = self.help_body().strip()
        spec = self.spec()
        inputs = [p for p in self.parameterDefinitions() if not p.isDestination()]
        outputs = {o.name(): o.description() for o in self.outputDefinitions()}
        parts = [body]
        if inputs:
            parts.append(
                f"<p><b>{_tr('Parameters')}</b></p><ul>"
                + "".join(f"<li>{html.escape(p.description(), quote=False)}</li>" for p in inputs)
                + "</ul>"
            )
        if outputs:
            parts.append(
                f"<p><b>{_tr('Outputs')}</b></p><ul>"
                + "".join(f"<li>{html.escape(text, quote=False)}</li>" for text in outputs.values())
                + "</ul>"
            )
        worked = worked_examples_of(spec.id)
        if worked:
            # Two sentences, not one with a plural made up: since P13-17 the GNSS
            # tutorial and the GNSS sample both run Relative — Static.
            sentence = (
                _tr(
                    "the %1 tutorial runs it. Install it with Install tutorial dataset: its README "
                    "walks through each step, and the project it installs holds the walkthrough as "
                    "a model to run."
                )
                if len(worked) == 1
                else _tr(
                    "the %1 tutorials run it. Install one with Install tutorial dataset: its README "
                    "walks through each step, and the project it installs holds the walkthrough as "
                    "a model to run."
                )
            ).replace("%1", ", ".join(worked))
            parts.append(
                f"<p><b>{_tr('Worked example')}</b> &mdash; {html.escape(sentence, quote=False)}</p>"
            )
        parts.append(f"<p><i>{_tr('Requirement')}: {spec.requirement}</i></p>")
        return "\n\n".join(parts)

    def help_body(self) -> str:
        """The algorithm's help text. Subclasses must override."""
        raise NotImplementedError

    def displayName(self) -> str:  # pragma: no cover - trivial, overridden
        """The algorithm's translated name; every subclass overrides it."""
        raise NotImplementedError

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:  # pragma: no cover
        """Declare the parameters and outputs; every subclass overrides it."""
        raise NotImplementedError


def _in_the_display_locale(process):
    """A run writes its numbers for one language from start to end (FR-094).

    Read once, at the start, and held for the run in a context variable, so a
    run on a worker thread is not changed under it by anything the main thread
    does meanwhile.
    """

    @functools.wraps(process)
    def run(self, parameters, context, feedback):
        with numbers_for():
            return process(self, parameters, context, feedback)

    return run


def _tr(text: str) -> str:
    # The base class's own words are catalogued under its own context. Through
    # ``self.tr`` they were looked up under each subclass's, where they are not,
    # so "Requirement" had never been translated in any algorithm's help, nor a
    # Processing group's name in the toolbox (found by P12c's audit).
    return QCoreApplication.translate(_CONTEXT, text)


def _group_label(group_id: str) -> str:
    """The Processing group names, translated.

    Written out in full so the translation extractor sees each one; the mapping
    is keyed by the stable group ids declared in :mod:`geocomp.registry`.
    """
    return {
        "totalstation": _tr("Total Station"),
        "levelling": _tr("Level"),
        "gnss": _tr("GNSS"),
        "gravimetry": _tr("Gravimetry"),
        "integration": _tr("Integration"),
        "analysis": _tr("Analysis"),
        "monitoring": _tr("Monitoring"),
        "project": _tr("Project and data"),
        "visualization": _tr("Visualisation and reporting"),
    }.get(group_id, group_id)
