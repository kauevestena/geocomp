# SPDX-License-Identifier: GPL-2.0-or-later
"""Offering a base map when results arrive on the map (FR-167; phase P12a).

``specs/17-persistence-and-interoperability.md`` section 5.6: *the plugin offers
to add configured base map services*. ``basemaps.offer_on_result_layers`` is
that offer's switch. Until P12a it was declared, shown, stored -- and read by
nothing, so turning it off changed nothing because there was nothing to turn
off.

**An offer, not an addition.** When a GeoComp result layer is added to a
project that has no configured base map, the message bar asks, with one button
per service the user may want: the configured default alone when there is one,
the catalogue's services otherwise. Nothing is added unless a button is
pressed. Adding a layer the user did not ask for is what
:meth:`geocomp.core.basemaps.BaseMapCatalogue.default` refuses to do, and the
offer keeps that promise: it asks.

**Once per project.** A user who ignores the question for one result is not
asked again for the next five; one who wants it never asked again has a button
that turns the setting off, which is also how they find out it exists.
"""

from __future__ import annotations

from typing import Any

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QPushButton

from geocomp.core.errors import GeoCompError

__all__ = ["BaseMapOffer", "services_to_offer"]

_CONTEXT = "GeoCompBaseMapOffer"

#: The most services offered as buttons; a longer catalogue is reached through
#: the *Add base map* algorithm, which can name any of them.
MAX_BUTTONS = 4


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


def services_to_offer(project: QgsProject) -> list[Any]:
    """The base map services to offer for *project*: none, the default, or the catalogue.

    None when the offer is switched off, or when a configured service is already
    in the project -- the results have their context and a second base map
    would be clutter.

    Raises:
        GeoCompError: when ``basemaps.catalogue`` names a file that cannot be
            read. The caller says so rather than offering the built-in list:
            the user configured a catalogue, and offering another is how a
            project ends up with imagery nobody chose (``specs/17`` section 5.6).
    """
    from geocomp.core.basemaps import load_catalogue
    from geocomp.layers.basemaps import existing_base_map
    from geocomp.services.settings_service import settings

    if not settings.value("basemaps.offer_on_result_layers"):
        return []
    catalogue = load_catalogue(settings.value("basemaps.catalogue"))
    if any(existing_base_map(service, project) is not None for service in catalogue.services):
        return []
    default = catalogue.default(settings.value("basemaps.default_service"))
    if default is not None:
        return [default]
    return list(catalogue.services[:MAX_BUTTONS])


class BaseMapOffer:
    """Watches a project for GeoComp result layers and offers a base map beneath them."""

    def __init__(self, message_bar: Any, project: QgsProject | None = None) -> None:
        self._bar = message_bar
        self._project = project or QgsProject.instance()
        self._asked: set[str] = set()
        self._project.layersAdded.connect(self.layers_added)
        # A new or reopened project is a new question: every unsaved project
        # shares one empty file name, and would otherwise be asked only once.
        self._project.cleared.connect(self._asked.clear)

    def unload(self) -> None:
        """Disconnect from the project's signals, tolerating ones already gone."""
        for signal, slot in (
            (self._project.layersAdded, self.layers_added),
            (self._project.cleared, self._asked.clear),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

    def layers_added(self, layers: list[Any]) -> None:
        """Offer a base map when result layers are added, once per project.

        Layers that are not GeoComp results are ignored. A failure to list the services is reported
        in the message bar instead.
        """
        from geocomp.algorithms.layer_outputs import RESULT_LAYER_PROPERTY

        if not any(layer.customProperty(RESULT_LAYER_PROPERTY) for layer in layers):
            return
        key = self._project.fileName() or "unsaved project"
        if key in self._asked:
            return
        try:
            services = services_to_offer(self._project)
        except GeoCompError as error:
            from geocomp.services.messages import message_for

            self._asked.add(key)
            self._bar.pushMessage(
                _tr("Base map"), message_for(error), Qgis.MessageLevel.Warning, 0
            )
            return
        if not services:
            return
        self._asked.add(key)
        self._push(services)

    def _push(self, services: list[Any]) -> None:
        item = self._bar.createMessage(
            _tr("Base map"), _tr("Add a base map beneath the results, for context?")
        )
        for service in services:
            button = QPushButton(service.name, item)
            button.setObjectName(f"geocompBaseMapOffer_{service.id}")
            button.clicked.connect(lambda _=False, chosen=service: self._add(chosen, item))
            item.layout().addWidget(button)
        never = QPushButton(_tr("Don't offer again"), item)
        never.setObjectName("geocompBaseMapOfferNever")
        never.clicked.connect(lambda _=False: self._never(item))
        item.layout().addWidget(never)
        self._bar.pushWidget(item, Qgis.MessageLevel.Info, 0)

    def _add(self, service: Any, item: Any) -> None:
        from geocomp.layers.basemaps import add_base_map
        from geocomp.services.settings_service import settings

        self._bar.popWidget(item)
        _layer, outcome = add_base_map(
            service,
            self._project,
            reuse_existing=bool(settings.value("basemaps.reuse_existing_layer")),
        )
        if outcome == "invalid":
            self._bar.pushMessage(
                _tr("Base map"),
                _tr("The base map service could not be loaded; check its address: ") + service.url,
                Qgis.MessageLevel.Warning,
                0,
            )
            return
        # A base map used without its attribution is a licence breach; the
        # message bar is where the user is looking when it appears.
        self._bar.pushMessage(
            service.name, _tr("Attribution: ") + service.attribution, Qgis.MessageLevel.Info, 10
        )

    def _never(self, item: Any) -> None:
        from geocomp.services.settings_service import settings

        self._bar.popWidget(item)
        settings.set_global("basemaps.offer_on_result_layers", False)
