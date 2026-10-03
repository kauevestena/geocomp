# SPDX-License-Identifier: GPL-2.0-or-later
"""A base in another frame is transformed for the run, with its record (specs/11 criterion 7).

Until P12c a relative run held its base where the RINEX header put it. That
position is approximate and in no stated frame, and the reference-station
database (FR-063) was read by nothing. The core refused any frame mismatch and
left the transformation to a caller, and no caller applied it. These hold the
algorithms' side of what is now done instead: the base is fetched from the
database, brought into the run's frame at the session's epoch, given to RTKLIB
as explicit coordinates, and recorded. A run that cannot do this is refused
before the engine starts.

``rnx2rtkp`` is not needed: what is under test is everything up to the engine's
configuration, and RTKLIB's reading of an explicit base is the engine tier's.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from tests.conftest import requires_qgis

pytestmark = [pytest.mark.qgis, requires_qgis]

# NGS coordinate sheet for GODN, ITRF2020 at 2020.0, as tests/test_gnss_stations.py.
GODN_XYZ = (1130760.752, -4831298.683, 3994155.197)
VELOCITY = (-0.0152, 0.0002, 0.0022)
OBSERVED = datetime(2025, 7, 2, 12, 0, tzinfo=UTC)


@pytest.fixture
def database(qgis_app, tmp_path):
    """A reference-station database holding GODN, configured for the length of a test."""
    from geocomp.services.settings_service import settings

    def write(*, velocity=VELOCITY):
        from geocomp.core.models.epoch import Epoch
        from geocomp.core.techniques.gnss.stations import ReferenceStation, StationDatabase
        from geocomp.core.uncertainty import Quantity
        from geocomp.core.units import Unit

        stations = StationDatabase()
        stations.add(
            ReferenceStation(
                id="GODN",
                position=tuple(Quantity.from_std_dev(v, 0.002, Unit.METRE) for v in GODN_XYZ),
                frame="ITRF2020",
                epoch=Epoch(decimal_year=2020.0),
                velocity_per_year=velocity,
                source="NGS coordinate sheet",
            )
        )
        path = tmp_path / "stations.json"
        stations.write(path)
        settings.set_global("gnss.reference_station_database", str(path))
        return path

    write()
    yield write
    settings.reset_global("gnss.reference_station_database")


def _session(station_id: str = "GODN", start=OBSERVED):
    return SimpleNamespace(station_id=station_id, start=start)


def _feedback():
    from qgis.core import QgsProcessingFeedback

    return QgsProcessingFeedback()


def test_a_base_in_another_frame_is_held_where_the_transformation_puts_it(database):
    from geocomp.algorithms.gnss.common import base_coordinates
    from geocomp.core.models.epoch import Epoch
    from geocomp.core.techniques.gnss.stations import StationDatabase, to_frame

    held, record = base_coordinates(_session(), "SIRGAS2000", _feedback())

    published = StationDatabase.read(database()).get("GODN")
    expected = to_frame(published, "SIRGAS2000", Epoch.from_datetime(OBSERVED))
    assert held == {"base_position": expected.xyz, "base_position_type": "xyz"}
    assert record["frame"] == "SIRGAS2000"
    assert record["published"] == {"frame": "ITRF2020", "epoch": 2020.0, "xyz": list(GODN_XYZ)}
    assert record["transformation"]["source"] == "ITRF2020"
    assert record["transformation"]["steps"]
    assert record["epoch"] == pytest.approx(Epoch.from_datetime(OBSERVED).decimal_year)


def test_in_its_own_frame_it_is_only_moved_to_the_sessions_epoch(database):
    from geocomp.algorithms.gnss.common import base_coordinates

    held, record = base_coordinates(_session(), None, _feedback())
    assert record["frame"] == "ITRF2020"
    assert "transformation" not in record
    assert record["propagated_years"] == pytest.approx(5.5, abs=0.01)
    assert held["base_position"][0] == pytest.approx(GODN_XYZ[0] + VELOCITY[0] * 5.5, abs=2e-3)


def test_the_configuration_gives_rtklib_the_coordinates(database):
    from geocomp.algorithms.gnss.common import base_coordinates, configured_profile

    held, _record = base_coordinates(_session(), "SIRGAS2000", _feedback())
    configuration = configured_profile("relative-static", **held)
    assert configuration.base_position == held["base_position"]
    assert configuration.base_position_type == "xyz"


def test_a_base_not_in_the_database_keeps_its_header_and_says_so(database):
    from geocomp.algorithms.gnss.common import base_coordinates

    held, record = base_coordinates(_session("nowhere"), "SIRGAS2000", _feedback())
    assert held == {}
    assert record == {"station": "nowhere", "source": "RINEX header", "frame": None}


def test_without_a_velocity_the_epoch_cannot_change_and_the_run_is_refused(database):
    from qgis.core import QgsProcessingException

    from geocomp.algorithms.gnss.common import base_coordinates

    database(velocity=None)
    with pytest.raises(QgsProcessingException):
        base_coordinates(_session(), "SIRGAS2000", _feedback())


def test_a_session_with_no_start_cannot_be_given_an_epoch(database):
    from qgis.core import QgsProcessingException

    from geocomp.algorithms.gnss.common import base_coordinates

    with pytest.raises(QgsProcessingException, match="start time"):
        base_coordinates(_session(start=None), "SIRGAS2000", _feedback())


class TestTheRunsFrame:
    def test_the_projects_is_the_preferred_crss_datum(self, qgis_app):
        from geocomp.algorithms.gnss.common import run_frame
        from geocomp.services.settings_service import settings

        try:
            settings.set_global("reference_systems.preferred_crs", "EPSG:31982")
            assert run_frame(0) == "SIRGAS2000"
            settings.set_global("reference_systems.preferred_crs", "EPSG:4326")
            assert run_frame(0) is None, "WGS 84 names no realisation"
        finally:
            settings.reset_global("reference_systems.preferred_crs")
        assert run_frame(0) is None

    def test_the_others_are_as_published_or_named(self):
        from geocomp.algorithms.gnss.common import run_frame
        from geocomp.core.geodesy.frames import FRAME_NAMES

        assert run_frame(1) is None
        assert [run_frame(index) for index in range(2, 2 + len(FRAME_NAMES))] == list(FRAME_NAMES)

    @pytest.mark.parametrize(
        "algorithm_id",
        ["geocomp:gnss_relative_static", "geocomp:gnss_relative_kinematic", "geocomp:gnss_batch"],
    )
    def test_every_algorithm_with_a_base_offers_it(self, geocomp_provider, algorithm_id):
        from qgis.core import QgsApplication

        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        assert algorithm.parameterDefinition("FRAME") is not None

    @pytest.mark.parametrize("algorithm_id", ["geocomp:gnss_absolute_static"])
    def test_an_absolute_run_has_no_base_and_no_choice(self, geocomp_provider, algorithm_id):
        from qgis.core import QgsApplication

        algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
        assert algorithm.parameterDefinition("FRAME") is None
