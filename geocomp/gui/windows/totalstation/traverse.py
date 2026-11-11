# SPDX-License-Identifier: GPL-2.0-or-later
"""Total Station ▸ Traverse, on the typed field book (FR-011, FR-017).

``specs/15-ui-menu-and-settings.md`` section 7.2. Five steps:

1. **Route** -- the stations in the order they were occupied, chosen from those
   the field book names; the initial backsight; and the kind of traverse.
2. **Starting data** -- the coordinates of the first station and the azimuth to
   the backsight, typed or picked on the map; for a connected traverse, where
   it arrives.
3. **Options** -- how the misclosure is distributed, and the tolerances.
4. **Calculate** -- runs the import, the pre-processing and
   ``geocomp:totalstation_traverse``.
5. **Results** -- the misclosures and the coordinates, the algorithm's report,
   and the traverse drawn on the map.

Every option is a parameter of the algorithm, under the algorithm's own label,
and the route and the backsight are stored as the algorithm takes them. The
window adds two things a dialog cannot: the route is built by choosing among
the stations actually in the book, and a station is picked on the map.
"""

from __future__ import annotations

import json
import math
from typing import Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from geocomp.algorithms.display import display_format
from geocomp.core.errors import GeoCompError
from geocomp.core.number_format import localised
from geocomp.gui.windows.totalstation.common import TotalStationWindow
from geocomp.gui.workbench.layers import add_points_layer
from geocomp.gui.workbench.parameters import ParameterForm
from geocomp.gui.workbench.window import DONE, Step
from geocomp.jobs import total_station as ts
from geocomp.jobs.chains import Chain
from geocomp.jobs.tables import parse_number

__all__ = ["TraverseWindow"]

_TR_CONTEXT = "GeoCompTotalStationWindows"

#: The algorithm's ``KIND`` values, whose order is as permanent as its id.
_CLOSED, _CONNECTED, _OPEN = 0, 1, 2


def _tr(text: str) -> str:
    return QCoreApplication.translate(_TR_CONTEXT, text)


class TraverseWindow(TotalStationWindow):
    """Compute a traverse from the typed field book."""

    REPORT = ("traverse", "OUTPUT_HTML")
    TABLE = ("traverse", "OUTPUT_CSV")

    def build(self) -> None:
        """Route, starting data and options, then the run and its results."""
        self.add_step(Step("route", _tr("Route"), self._route_page(), problem=self._route_problem))
        self.add_step(
            Step(
                "start",
                _tr("Starting data"),
                self._start_page(),
                problem=self._start_problem,
            )
        )
        self.add_step(Step("options", _tr("Options"), self._options_page()))
        self.add_run_steps(_tr("Calculate"), _tr("Results"))
        self.results.add_action(
            _tr("Use as known stations"),
            self.use_as_known_stations,
            _tr(
                "Add the traverse's stations to the job's known points, for 3D radiation to "
                "start from. A traverse gives no heights: type them there."
            ),
        )
        self.results.add_action(
            _tr("Add stations to the map"),
            self.add_to_map,
            _tr("Add the stations to the project as a point layer."),
        )
        self._load_route()

    def chain(self) -> Chain:
        """The import, the pre-processing, and the traverse over the reductions."""
        return ts.traverse_chain(self.book)

    def _options(self) -> dict[str, Any]:
        return self.job.parameters(ts.WINDOW_TRAVERSE)

    # -- step 1: the route --------------------------------------------------------

    def _route_page(self) -> QWidget:
        page = QWidget(self)
        self.available = QListWidget(page)
        self.available.setObjectName("geocompRouteAvailable")
        self.route_list = QListWidget(page)
        self.route_list.setObjectName("geocompRoute")
        self.add_button = QPushButton(_tr("Add to route →"), page)
        self.remove_button = QPushButton(_tr("Remove"), page)
        self.up_button = QPushButton(_tr("Move up"), page)
        self.down_button = QPushButton(_tr("Move down"), page)
        self.clear_button = QPushButton(_tr("Clear route"), page)
        self.backsight_combo = QComboBox(page)
        self.backsight_combo.setObjectName("geocompBacksight")
        self.backsight_combo.setEditable(True)
        self.kind_form = ParameterForm(ts.TRAVERSE, ("KIND",), self._options, parent=page)

        self.add_button.clicked.connect(lambda _checked=False: self._add_selected())
        self.available.itemDoubleClicked.connect(lambda _item=None: self._add_selected())
        self.remove_button.clicked.connect(lambda _checked=False: self._edit_route("remove"))
        self.up_button.clicked.connect(lambda _checked=False: self._edit_route("up"))
        self.down_button.clicked.connect(lambda _checked=False: self._edit_route("down"))
        self.clear_button.clicked.connect(lambda _checked=False: self.set_route([]))
        self.backsight_combo.currentTextChanged.connect(self._backsight_changed)
        self.kind_form.changed.connect(lambda _name="": self._kind_changed())

        buttons = QVBoxLayout()
        for button in (
            self.add_button,
            self.remove_button,
            self.up_button,
            self.down_button,
            self.clear_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        left, right = QVBoxLayout(), QVBoxLayout()
        left.addWidget(QLabel(_tr("Points in the field book"), page))
        left.addWidget(self.available, 1)
        right.addWidget(QLabel(_tr("Route, in the order occupied"), page))
        right.addWidget(self.route_list, 1)
        lists = QHBoxLayout()
        lists.addLayout(left, 1)
        lists.addLayout(buttons)
        lists.addLayout(right, 1)
        form = QFormLayout()
        form.addRow(self.kind_form.label("BACKSIGHT"), self.backsight_combo)
        hint = QLabel(
            _tr(
                "A closed traverse ends on the station it started from: add that station "
                "again as the last of the route."
            ),
            page,
        )
        hint.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addLayout(lists, 1)
        layout.addLayout(form)
        layout.addWidget(self.kind_form)
        layout.addWidget(hint)
        return page

    def route(self) -> list[str]:
        """The route, as the algorithm's ``ROUTE`` parameter holds it."""
        return [name.strip() for name in str(self._options().get("ROUTE") or "").split(",") if name.strip()]

    def set_route(self, stations: list[str]) -> None:
        """Make *stations* the route, in that order."""
        options = self._options()
        if stations:
            options["ROUTE"] = ",".join(stations)
        else:
            options.pop("ROUTE", None)
        self._load_route()
        self.touch()

    def set_backsight(self, station: str) -> None:
        """Make *station* the initial backsight."""
        options = self._options()
        if station.strip():
            options["BACKSIGHT"] = station.strip()
        else:
            options.pop("BACKSIGHT", None)
        self._load_route()
        self.touch()

    def _load_route(self) -> None:
        """Set the Route step's widgets from the job and the field book."""
        self._loading = True
        try:
            names = self.book.point_names()
            self.available.clear()
            self.available.addItems(names)
            selected = self.route_list.currentRow()
            self.route_list.clear()
            self.route_list.addItems(self.route())
            if 0 <= selected < self.route_list.count():
                self.route_list.setCurrentRow(selected)
            self.backsight_combo.clear()
            self.backsight_combo.addItems(names)
            self.backsight_combo.setCurrentText(str(self._options().get("BACKSIGHT") or ""))
        finally:
            self._loading = False

    def _add_selected(self) -> None:
        item = self.available.currentItem()
        if item is not None:
            self.set_route([*self.route(), item.text()])
            self.route_list.setCurrentRow(self.route_list.count() - 1)

    def _edit_route(self, edit: str) -> None:
        route, row = self.route(), self.route_list.currentRow()
        if not 0 <= row < len(route):
            return
        if edit == "remove":
            del route[row]
        else:
            other = row - 1 if edit == "up" else row + 1
            if not 0 <= other < len(route):
                return
            route[row], route[other] = route[other], route[row]
            self.route_list.setCurrentRow(other)
        self.set_route(route)

    def _backsight_changed(self, text: str) -> None:
        if not getattr(self, "_loading", False) and text != str(self._options().get("BACKSIGHT") or ""):
            self.set_backsight(text)

    def _route_problem(self) -> str:
        if len(self.route()) < 2:
            return _tr("Add at least two stations to the route, in the order they were occupied.")
        if not str(self._options().get("BACKSIGHT") or "").strip():
            return _tr(
                "Choose the initial backsight: the point the first station sighted before "
                "turning the angle."
            )
        return ""

    # -- step 2: starting data -------------------------------------------------------

    def _start_page(self) -> QWidget:
        page = QWidget(self)
        self.start_form = ParameterForm(
            ts.TRAVERSE,
            ("START_EASTING", "START_NORTHING", "START_AZIMUTH"),
            self._options,
            parent=page,
        )
        # The closing data is advanced in the algorithm, where a closed loop is
        # the default and needs none. A connected traverse cannot be computed
        # without it, so here it is shown whenever the kind asks for it.
        closing = ("CLOSE_EASTING", "CLOSE_NORTHING", "CLOSE_AZIMUTH")
        self.close_form = ParameterForm(
            ts.TRAVERSE, closing, self._options, always=closing, parent=page
        )
        self.pick_start_button = QPushButton(_tr("Pick the start on the map"), page)
        self.pick_close_button = QPushButton(_tr("Pick the closing point on the map"), page)
        self.pick_start_button.clicked.connect(
            lambda _checked=False: self.pick_into(self.start_form, "START_EASTING", "START_NORTHING")
        )
        self.pick_close_button.clicked.connect(
            lambda _checked=False: self.pick_into(self.close_form, "CLOSE_EASTING", "CLOSE_NORTHING")
        )
        self.start_form.changed.connect(lambda _name="": self.touch())
        self.close_form.changed.connect(lambda _name="": self.touch())
        azimuth_note = QLabel(
            _tr(
                "The start azimuth is that of the line from the first station to the initial "
                "backsight, in decimal degrees, as the algorithm takes it."
            ),
            page,
        )
        azimuth_note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.start_form)
        layout.addWidget(self.pick_start_button)
        layout.addWidget(azimuth_note)
        layout.addWidget(self.close_form)
        layout.addWidget(self.pick_close_button)
        layout.addStretch(1)
        self._show_closing()
        return page

    def kind(self) -> int:
        """The traverse's kind, as the algorithm's ``KIND`` parameter numbers it."""
        return int(self.kind_form.value("KIND") or 0)

    def _kind_changed(self) -> None:
        self._show_closing()
        self.touch()

    def _show_closing(self) -> None:
        """Show the closing data the kind of traverse asks for, and no other."""
        kind = self.kind()
        for name in ("CLOSE_EASTING", "CLOSE_NORTHING"):
            self.close_form.set_shown(name, kind == _CONNECTED)
        self.close_form.set_shown("CLOSE_AZIMUTH", kind != _OPEN)
        self.pick_close_button.setVisible(kind == _CONNECTED)

    def pick_into(self, form: ParameterForm, easting: str, northing: str) -> None:
        """Take a point from the map into two of the algorithm's parameters."""

        def picked(x: float, y: float) -> None:
            form.set_value(easting, round(x, 4))
            form.set_value(northing, round(y, 4))

        self.pick_point(picked)

    def _start_problem(self) -> str:
        options = self._options()
        if self.kind() == _CONNECTED and (
            options.get("CLOSE_EASTING") is None or options.get("CLOSE_NORTHING") is None
        ):
            return _tr(
                "A connected traverse arrives at a known point. Give the closing easting and "
                "northing, or choose another kind in the Route step."
            )
        return ""

    # -- step 3: options ---------------------------------------------------------------

    def _options_page(self) -> QWidget:
        page = QWidget(self)
        self.options_form = ParameterForm(
            ts.TRAVERSE,
            ("METHOD", "ANGULAR_TOLERANCE", "RELATIVE_LIMIT"),
            self._options,
            parent=page,
        )
        self.options_form.changed.connect(lambda _name="": self.touch())
        note = QLabel(
            _tr(
                "A classical distribution is not least squares: the coordinates it gives are "
                "approximate. For the rigorous path, adjust the same field book with "
                "Classical network."
            ),
            page,
        )
        note.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.addWidget(self.options_form)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    # -- results -------------------------------------------------------------------------

    def figures(self, scalars: dict[str, Any]) -> list[tuple[str, str]]:
        """The algorithm's misclosures, in the display format its report uses."""
        shown = display_format()
        angular = _number(scalars.get("traverse.ANGULAR_MISCLOSURE"))
        linear = _number(scalars.get("traverse.LINEAR_MISCLOSURE"))
        relative = _number(scalars.get("traverse.RELATIVE_PRECISION"))
        within = scalars.get("traverse.WITHIN_TOLERANCE")
        return [
            (
                _tr("Angular misclosure"),
                _tr("not checked")
                if angular is None
                else shown.small_angle(math.radians(angular)) + " " + shown.small_angle_symbol,
            ),
            (
                _tr("Linear misclosure"),
                _tr("none: nothing to close on") if linear is None else localised(f"{linear:.4f}") + " m",
            ),
            (
                _tr("Relative precision"),
                _tr("none")
                if relative is None
                else _tr("exact closure")
                if math.isinf(relative)
                else "1:" + localised(f"{relative:.0f}"),
            ),
            (
                _tr("Within tolerance"),
                "" if within is None else _tr("Yes") if within else _tr("No: see the findings"),
            ),
        ]

    def coordinates(self) -> dict[str, tuple[float, float, float]]:
        """The stations the last run computed, as its coordinates document gives them."""
        path = self.output_path("traverse", "OUTPUT_COORDINATES")
        if path is None:
            return {}
        document = json.loads(path.read_text(encoding="utf-8"))
        return {
            str(name): (float(values[0]), float(values[1]), float(values[2]))
            for name, values in document.items()
        }

    def use_as_known_stations(self) -> int:
        """Write the computed stations into the job's known points. Returns how many.

        A station already there keeps the height typed for it; a new one takes
        the height the algorithm wrote, which for a traverse is zero.
        """
        book = self.book
        typed = {
            book.points.cell(row, "name"): book.points.cell(row, "height")
            for row in book.points.filled_rows()
        }
        coordinates = self.coordinates()
        for name, (easting, northing, up) in coordinates.items():
            kept = typed.get(name)
            height = parse_number(kept) if kept else up
            book.set_point(name, round(easting, 4), round(northing, 4), height, origin="traverse")
        if coordinates:
            self.touch()
        return len(coordinates)

    def add_to_map(self) -> None:
        """Add the computed stations to the project as a point layer."""
        add_points_layer(
            _tr("Traverse stations (%1)").replace("%1", self.job.name or _tr("untitled job")),
            self.job.crs,
            [
                {"name": name, "easting": easting, "northing": northing, "origin": "traverse"}
                for name, (easting, northing, _up) in self.coordinates().items()
            ],
        )

    def draw(self) -> None:
        """The known points, and the traverse the algorithm computed, along its route."""
        book = self.book
        for row in book.points.filled_rows():
            try:
                self.sketch.add_point(
                    parse_number(book.points.cell(row, "easting")),
                    parse_number(book.points.cell(row, "northing")),
                )
            except GeoCompError:
                continue
        if self.step("calculate").state != DONE:
            return
        coordinates = self.coordinates()
        for easting, northing, _up in coordinates.values():
            self.sketch.add_point(easting, northing, computed=True)
        legs = [coordinates[name][:2] for name in self.route() if name in coordinates]
        self.sketch.add_line(legs)

    def reload_pages(self) -> None:
        """Another job is the current one: show its route and options."""
        self._load_route()
        for form in (self.kind_form, self.start_form, self.close_form, self.options_form):
            form.reload()
        self._show_closing()

    def refresh(self) -> None:
        """Also offer the points the field book names now."""
        if hasattr(self, "available"):
            names = list(self.book.point_names())
            if [self.available.item(i).text() for i in range(self.available.count())] != names:
                self._load_route()
        super().refresh()


def _number(value: Any) -> float | None:
    """A scalar an algorithm returned, or ``None`` where it returned not-a-number."""
    if value is None:
        return None
    number = float(value)
    return None if math.isnan(number) else number
