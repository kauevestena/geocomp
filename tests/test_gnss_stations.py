# SPDX-License-Identifier: GPL-2.0-or-later
"""The reference station database, and the two rules it exists to enforce.

``specs/11-module-gnss.md`` section 7. A base station is a position *in a frame,
at an epoch*, and the failures this file pins are the ones that leave no trace:
a station used at the wrong epoch, or coordinates from one frame processed as
though they were another.

RD-06's GODN and GODS are the fixtures, with their real published ITRF2020 ARP
coordinates and velocities, because they make one property checkable that
synthetic numbers would not: **the two share a velocity exactly, so the baseline
between them is epoch-invariant while neither position is.**
"""

from __future__ import annotations

import json

import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models.epoch import Epoch
from geocomp.core.techniques.gnss.stations import (
    ReferenceStation,
    StationDatabase,
    propagate_to_epoch,
    require_same_frame,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

ITRF2020 = Epoch(decimal_year=2020.0, label="2020.0")

# NGS coordinate sheets, ITRF2020 at epoch 2020.0, antenna reference point.
GODN_XYZ = (1130760.752, -4831298.683, 3994155.197)
GODS_XYZ = (1130752.184, -4831349.109, 3994098.960)
VELOCITY = (-0.0152, 0.0002, 0.0022)


def station(identifier, xyz, *, epoch=ITRF2020, velocity=VELOCITY, frame="ITRF2020"):
    return ReferenceStation(
        id=identifier,
        position=tuple(Quantity.from_std_dev(v, 0.002, Unit.METRE) for v in xyz),
        frame=frame,
        epoch=epoch,
        velocity_per_year=velocity,
        source="https://geodesy.noaa.gov/corsdata/coord/coord_20/",
    )


class TestAStationIsAPositionInAFrameAtAnEpoch:
    def test_a_station_without_a_frame_is_refused(self):
        with pytest.raises(DataError, match="reference_station_without_frame"):
            ReferenceStation(
                id="GODN",
                position=tuple(Quantity.exact(v, Unit.METRE) for v in GODN_XYZ),
                frame="",
            )

    def test_a_position_in_the_wrong_unit_is_refused(self):
        with pytest.raises(DataError, match="reference_station_position_unit"):
            ReferenceStation(
                id="GODN",
                position=(
                    Quantity.exact(1.0, Unit.RADIAN),
                    Quantity.exact(2.0, Unit.METRE),
                    Quantity.exact(3.0, Unit.METRE),
                ),
                frame="ITRF2020",
            )

    def test_an_absent_epoch_is_refused_where_one_is_required(self):
        """FR-105, through the same require_epoch every other module uses."""
        undated = station("GODN", GODN_XYZ, epoch=None)
        with pytest.raises(ValidationError, match="epoch_required"):
            undated.epoch_for("build a baseline")


class TestPropagatingToAnotherEpoch:
    def test_the_position_moves_by_velocity_times_interval(self):
        moved = propagate_to_epoch(station("GODN", GODN_XYZ), Epoch(decimal_year=2025.0))
        for found, origin, rate in zip(moved.xyz, GODN_XYZ, VELOCITY, strict=True):
            assert found == pytest.approx(origin + rate * 5.0, abs=1e-12)

    def test_the_new_epoch_and_the_old_one_are_both_recorded(self):
        moved = propagate_to_epoch(station("GODN", GODN_XYZ), Epoch(decimal_year=2025.0))
        assert moved.epoch.decimal_year == 2025.0
        assert moved.meta["propagated_from_epoch"] == 2020.0
        assert moved.meta["propagated_years"] == pytest.approx(5.0)

    def test_a_shared_velocity_leaves_the_baseline_unchanged(self):
        """The property RD-06 rests on, checked rather than assumed.

        GODN and GODS carry identical published velocities, so propagating both
        to any epoch moves them together: the *positions* change by 76 mm over
        five years, the *baseline* by nothing. `reference.json` states this as
        its reason for calling the expected vector epoch-invariant.
        """
        target = Epoch(decimal_year=2025.0)
        before = [b - a for a, b in zip(GODN_XYZ, GODS_XYZ, strict=True)]
        after = [
            b - a
            for a, b in zip(
                propagate_to_epoch(station("GODN", GODN_XYZ), target).xyz,
                propagate_to_epoch(station("GODS", GODS_XYZ), target).xyz,
                strict=True,
            )
        ]
        assert after == pytest.approx(before, abs=1e-12)
        # ... while the positions themselves genuinely moved.
        moved = propagate_to_epoch(station("GODN", GODN_XYZ), target)
        assert abs(moved.xyz[0] - GODN_XYZ[0]) == pytest.approx(0.076, abs=1e-9)

    def test_an_unstated_velocity_is_refused_rather_than_assumed_zero(self):
        """15 mm/year is typical, so a decade of "probably zero" is 15 cm."""
        with pytest.raises(ValidationError, match="reference_station_without_velocity"):
            propagate_to_epoch(
                station("GODN", GODN_XYZ, velocity=None), Epoch(decimal_year=2025.0)
            )

    def test_propagating_without_a_source_epoch_is_refused(self):
        with pytest.raises(ValidationError, match="epoch_required"):
            propagate_to_epoch(
                station("GODN", GODN_XYZ, epoch=None), Epoch(decimal_year=2025.0)
            )


class TestFrameMismatchIsRefusedNotTransformed:
    def test_a_matching_frame_passes(self):
        require_same_frame(station("GODN", GODN_XYZ), "ITRF2020", operation="processing")

    def test_a_different_frame_raises_and_names_the_phase_that_owns_it(self):
        """FR-832 is P10's. Until then a mismatch is an error, not a guess:
        ITRF2020 read as SIRGAS2000 is wrong by decimetres and internally
        consistent."""
        with pytest.raises(ValidationError, match="reference_station_frame_mismatch") as caught:
            require_same_frame(
                station("GODN", GODN_XYZ, frame="SIRGAS2000"),
                "ITRF2020",
                operation="processing",
            )
        assert "FR-832" in caught.value.context["expected"]


class TestTheDatabase:
    def test_a_station_round_trips_through_json(self, tmp_path):
        database = StationDatabase()
        database.add(station("GODN", GODN_XYZ))
        database.add(station("GODS", GODS_XYZ))
        path = tmp_path / "stations.json"
        database.write(path)

        returned = StationDatabase.read(path)
        assert sorted(returned.stations) == ["GODN", "GODS"]
        assert returned.get("GODN").xyz == pytest.approx(GODN_XYZ)
        assert returned.get("GODN").epoch.decimal_year == 2020.0
        assert returned.get("GODN").velocity_per_year == pytest.approx(VELOCITY)
        # The uncertainty survives too -- it is what specs/22 §5's residual
        # comes down to, so losing it in a round trip would matter.
        assert returned.get("GODN").position[0].std_dev == pytest.approx(0.002)

    def test_a_duplicate_is_refused(self):
        database = StationDatabase()
        database.add(station("GODN", GODN_XYZ))
        with pytest.raises(DataError, match="duplicate_reference_station"):
            database.add(station("GODN", GODN_XYZ))

    def test_an_unknown_station_names_what_is_there(self):
        database = StationDatabase()
        database.add(station("GODN", GODN_XYZ))
        with pytest.raises(DataError, match="reference_station_not_found") as caught:
            database.get("GODS")
        assert "GODN" in caught.value.context["expected"]

    def test_a_missing_file_is_refused_by_name(self, tmp_path):
        with pytest.raises(DataError, match="reference_station_database_missing"):
            StationDatabase.read(tmp_path / "absent.json")

    def test_unreadable_json_is_refused_by_name(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(DataError, match="reference_station_database_unreadable"):
            StationDatabase.read(path)

    def test_resolve_applies_the_frame_check_and_the_epoch_together(self):
        """The one call an algorithm makes, so neither rule can be forgotten."""
        database = StationDatabase()
        database.add(station("GODN", GODN_XYZ))

        same = database.resolve("GODN", frame="ITRF2020", epoch=ITRF2020)
        assert same.xyz == pytest.approx(GODN_XYZ)

        moved = database.resolve("GODN", frame="ITRF2020", epoch=Epoch(decimal_year=2025.0))
        assert moved.xyz[0] == pytest.approx(GODN_XYZ[0] - 0.076, abs=1e-9)

        with pytest.raises(ValidationError, match="reference_station_frame_mismatch"):
            database.resolve("GODN", frame="SIRGAS2000", epoch=ITRF2020)

    def test_resolve_without_an_epoch_leaves_the_station_where_it_was(self):
        database = StationDatabase()
        database.add(station("GODN", GODN_XYZ))
        assert database.resolve("GODN", frame="ITRF2020").xyz == pytest.approx(GODN_XYZ)

    def test_an_empty_database_serialises(self, tmp_path):
        path = tmp_path / "empty.json"
        StationDatabase().write(path)
        assert json.loads(path.read_text()) == {"stations": []}
        assert StationDatabase.read(path).stations == {}
