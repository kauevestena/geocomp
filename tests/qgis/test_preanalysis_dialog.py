# SPDX-License-Identifier: GPL-2.0-or-later
"""The interactive pre-analysis dialog, on a real canvas (FR-272).

Everything an edit *means* is decided by ``DesignSession`` and tested without
QGIS in ``tests/test_design_session.py``. What only a Qt runtime can answer is
whether a click on the canvas reaches the session, whether the panel repaints,
whether the rubber bands are created and removed, and -- the one that would go
unnoticed in a screenshot -- whether the dialog gives the canvas back when it
closes.

That last one matters more than it looks. A dialog that left its map tool
installed leaves the user clicking stations into a design that is no longer on
screen, with nothing to explain why the canvas has stopped behaving.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis


def _click(tool, easting: float, northing: float, button=None):
    """Drive the map tool the way the canvas does, in map coordinates."""
    from qgis.PyQt.QtCore import QPointF, Qt
    from qgis.PyQt.QtGui import QMouseEvent

    if button is None:
        button = Qt.MouseButton.LeftButton
    point = tool.canvas.getCoordinateTransform().transform(easting, northing)
    # QPointF, not QPoint: Qt6 dropped the integer-point overload, and passing
    # one raises rather than rounding.
    position = QPointF(float(int(point.x())), float(int(point.y())))
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        position,
        button,
        button,
        Qt.KeyboardModifier.NoModifier,
    )
    tool.canvasReleaseEvent(event)


@pytest.fixture
def canvas(qgis_app):
    from qgis.core import QgsCoordinateReferenceSystem, QgsRectangle
    from qgis.gui import QgsMapCanvas

    widget = QgsMapCanvas()
    widget.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:31982"))
    widget.setExtent(QgsRectangle(0.0, 0.0, 1000.0, 1000.0))
    widget.resize(600, 600)
    widget.refresh()
    yield widget
    widget.deleteLater()


@pytest.fixture
def dialog(canvas):
    from geocomp.gui.preanalysis_dialog import PreAnalysisDialog

    widget = PreAnalysisDialog(canvas)
    yield widget
    widget.done(0)
    widget.deleteLater()


class TestItTakesOverTheCanvasAndGivesItBack:
    def test_it_installs_its_map_tool(self, canvas, dialog):
        assert canvas.mapTool() is dialog.tool

    def test_closing_restores_the_previous_tool(self, canvas):
        from geocomp.gui.preanalysis_dialog import PreAnalysisDialog

        before = canvas.mapTool()
        widget = PreAnalysisDialog(canvas)
        assert canvas.mapTool() is widget.tool
        widget.done(0)
        assert canvas.mapTool() is before

    def test_closing_removes_everything_it_drew(self, canvas):
        """Rubber bands are canvas items, not dialog children: they outlive the
        dialog unless it removes them."""
        from geocomp.gui.preanalysis_dialog import PreAnalysisDialog

        widget = PreAnalysisDialog(canvas)
        widget.session.add_station("A", 100.0, 100.0)
        widget.session.add_station("B", 500.0, 300.0)
        widget._refresh()
        assert widget._markers
        widget.done(0)
        assert not widget._markers
        assert not widget._bands


class TestClicksReachTheDesign:
    def test_clicking_empty_ground_adds_a_station(self, dialog):
        _click(dialog.tool, 200.0, 200.0)
        assert len(dialog.session.network.stations) == 1

    def test_each_added_station_gets_its_own_name(self, dialog):
        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 400.0, 600.0)
        assert len(dialog.session.network.stations) == 2

    def test_a_station_lands_where_it_was_clicked(self, dialog):
        _click(dialog.tool, 250.0, 750.0)
        station = next(iter(dialog.session.network.stations.values()))
        east, north, _up = station.approx_position.values
        assert east.value == pytest.approx(250.0, abs=5.0)
        assert north.value == pytest.approx(750.0, abs=5.0)

    def test_connect_mode_joins_two_stations(self, dialog):
        from geocomp.gui.preanalysis_dialog import CONNECT

        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 700.0, 300.0)
        dialog._modes.button(CONNECT).click()
        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 700.0, 300.0)
        assert len(dialog.session.network.observations) == 1

    def test_connecting_a_station_to_itself_does_nothing(self, dialog):
        """An observation from a station to itself is not a measurement, and
        the click that made it was a slip."""
        from geocomp.gui.preanalysis_dialog import CONNECT

        _click(dialog.tool, 200.0, 200.0)
        dialog._modes.button(CONNECT).click()
        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 200.0, 200.0)
        assert not dialog.session.network.observations

    def test_remove_mode_takes_a_station_and_its_observations(self, dialog):
        from geocomp.gui.preanalysis_dialog import CONNECT, REMOVE

        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 700.0, 300.0)
        dialog._modes.button(CONNECT).click()
        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 700.0, 300.0)

        dialog._modes.button(REMOVE).click()
        _click(dialog.tool, 200.0, 200.0)
        assert len(dialog.session.network.stations) == 1
        assert not dialog.session.network.observations

    def test_move_mode_relocates_a_station(self, dialog):
        from geocomp.gui.preanalysis_dialog import MOVE

        _click(dialog.tool, 200.0, 200.0)
        dialog._modes.button(MOVE).click()
        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 800.0, 800.0)
        station = next(iter(dialog.session.network.stations.values()))
        assert station.approx_position.values[0].value == pytest.approx(800.0, abs=5.0)

    def test_a_right_click_abandons_a_half_finished_connection(self, dialog):
        from qgis.PyQt.QtCore import Qt

        from geocomp.gui.preanalysis_dialog import CONNECT

        _click(dialog.tool, 200.0, 200.0)
        _click(dialog.tool, 700.0, 300.0)
        dialog._modes.button(CONNECT).click()
        _click(dialog.tool, 200.0, 200.0)
        assert dialog._pending is not None
        _click(dialog.tool, 500.0, 500.0, Qt.MouseButton.RightButton)
        assert dialog._pending is None
        assert not dialog.session.network.observations


class TestThePanelKeepsUp:
    def test_an_empty_design_says_so_and_cannot_be_accepted(self, dialog):
        from qgis.PyQt.QtWidgets import QDialogButtonBox

        assert "Nothing to evaluate" in dialog._summary.text()
        assert not dialog._buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    def test_a_complete_design_fills_the_table_and_enables_ok(self, dialog):
        from qgis.PyQt.QtWidgets import QDialogButtonBox

        _build_quadrilateral(dialog)
        assert dialog._table.rowCount() == 4
        assert dialog._buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()

    def test_the_table_reports_millimetres_per_station(self, dialog):
        _build_quadrilateral(dialog)
        values = [float(dialog._table.item(row, 1).text()) for row in range(4)]
        assert all(value > 0.0 for value in values)

    def test_the_group_box_states_the_exaggeration_the_ellipses_used(self, dialog):
        """FR-901, in the view a user judges a design by."""
        _build_quadrilateral(dialog)
        title = dialog._summary.parent().title()
        assert f"{dialog.exaggeration:g}" in title

    def test_undo_is_offered_only_once_there_is_something_to_undo(self, dialog):
        assert not dialog._undo.isEnabled()
        _click(dialog.tool, 200.0, 200.0)
        assert dialog._undo.isEnabled()
        dialog._undo.click()
        assert not dialog.session.network.stations


class TestWhatItHandsOn:
    def test_the_design_becomes_a_network_the_algorithm_accepts(self, dialog, tmp_path):
        """The dialog builds the design; the numbers still come from the
        algorithm, so an interactive design and a loaded one are evaluated by
        the same code (ADR-0005)."""
        import json

        from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

        _build_quadrilateral(dialog)
        document = tmp_path / "design.json"
        document.write_text(json.dumps(dialog.network().to_dict()), encoding="utf-8")

        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_network_preanalysis"
        )
        results, ok = algorithm.create({}).run(
            {
                "NETWORK": str(document),
                "FRAME": 0,
                "OUTPUT_HTML": str(tmp_path / "design.html"),
            },
            QgsProcessingContext(),
            QgsProcessingFeedback(),
            catchExceptions=False,
        )
        assert ok
        assert results["WORST_UNCERTAINTY"] > 0.0

    def test_the_dispatcher_knows_it_needs_a_canvas(self, qgis_app):
        """Without one there is nothing to place a design on, so the item falls
        back to the plain Processing dialog rather than opening a design tool
        with no map under it."""
        from geocomp.gui.prompts import collect_parameters, has_custom_dialog

        assert has_custom_dialog("geocomp:analysis_network_preanalysis")
        assert collect_parameters("geocomp:analysis_network_preanalysis", None, None) == {}


def _build_quadrilateral(dialog) -> None:
    from geocomp.gui.preanalysis_dialog import CONNECT

    corners = ((150.0, 150.0), (800.0, 200.0), (850.0, 800.0), (200.0, 850.0))
    for east, north in corners:
        _click(dialog.tool, east, north)
    dialog._modes.button(CONNECT).click()
    for first in range(len(corners)):
        for second in range(first + 1, len(corners)):
            _click(dialog.tool, *corners[first])
            _click(dialog.tool, *corners[second])
