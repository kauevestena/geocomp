# SPDX-License-Identifier: GPL-2.0-or-later
"""Instrument profiles edited as named profiles (FR-061, FR-069; specs/15 §2.2).

Everything the profile window does that is not drawing a window lives in
``geocomp/core/instruments/editing.py``, and is held here without QGIS: every
kind's fields shown in the unit a surveyor reads them in and stored in the unit
the profile keeps, and the library operations the window offers.
"""

from __future__ import annotations

import json
import math

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.editing import (
    FIELDS,
    KINDS,
    add_profile,
    duplicate_profile,
    edited,
    export_profiles,
    import_profiles,
    remove_profile,
    set_default,
    shown,
)
from geocomp.core.instruments.profiles import InstrumentProfile, ProfileLibrary

ARCSECONDS = 180.0 * 3600.0 / math.pi


def _library() -> ProfileLibrary:
    library = ProfileLibrary()
    for kind in KINDS:
        add_profile(library, kind.key, f"{kind.key}-1")
    return library


class TestEveryKind:
    @pytest.mark.parametrize("kind", [kind.key for kind in KINDS])
    def test_every_field_round_trips_through_the_window(self, kind):
        """What is shown, written back unchanged, is the profile it came from."""
        library = _library()
        profile = getattr(library, kind)[f"{kind}-1"]
        payload = profile.to_dict()
        values = {
            field.key: shown(payload, field, small_angle=ARCSECONDS) for field in FIELDS[kind]
        }
        assert edited(kind, payload, values, small_angle=ARCSECONDS) == profile

    @pytest.mark.parametrize("kind", [kind.key for kind in KINDS])
    def test_every_field_is_one_the_profile_stores(self, kind):
        """A field naming nothing would be shown empty and written nowhere."""
        payload = getattr(_library(), kind)[f"{kind}-1"].to_dict()
        stored = set(payload) | {"name", "manufacturer", "model", "serial_number", "serial",
                                 "calibration_date", "calibration_reference", "source"}
        for field in FIELDS[kind]:
            assert field.path[0] in stored, field.key


class TestTheUnits:
    def test_an_index_error_is_shown_in_seconds_and_stored_in_radians(self):
        library = _library()
        profile = library.instruments["instruments-1"]
        changed = edited(
            "instruments",
            profile.to_dict(),
            {"vertical_index": (12.0, 1.5), "sigma_direction": 1.0},
            small_angle=ARCSECONDS,
        )
        assert changed.vertical_index.value == pytest.approx(12.0 / ARCSECONDS)
        assert changed.vertical_index.std_dev == pytest.approx(1.5 / ARCSECONDS)
        assert changed.sigma_direction == pytest.approx(1.0 / ARCSECONDS)

    def test_the_same_angle_in_cc_under_gon(self):
        cc = 200.0 / math.pi * 1.0e4
        payload = InstrumentProfile(id="t").to_dict()
        changed = edited("instruments", payload, {"collimation": (30.0, 0.0)}, small_angle=cc)
        assert changed.collimation.value == pytest.approx(30.0 / cc)

    def test_millimetres_and_ppm(self):
        payload = InstrumentProfile(id="t").to_dict()
        changed = edited(
            "instruments",
            payload,
            {
                "edm_additive": (-17.4, 0.3),
                "edm_scale": (3.0, 0.5),
                "edm.constant": 1.0,
                "edm.proportional": 1.5,
            },
            small_angle=ARCSECONDS,
        )
        assert changed.edm_additive.value == pytest.approx(-0.0174)
        assert changed.edm_additive.std_dev == pytest.approx(0.0003)
        assert changed.edm_scale.value == pytest.approx(1.000003)
        assert changed.edm_scale.std_dev == pytest.approx(0.5e-6)
        assert changed.edm.constant == pytest.approx(0.001)
        assert changed.edm.proportional == pytest.approx(1.5e-6)
        shown_scale = shown(changed.to_dict(), _field("instruments", "edm_scale"), small_angle=ARCSECONDS)
        assert shown_scale == pytest.approx((3.0, 0.5))

    def test_a_decimal_comma_is_a_number(self):
        payload = InstrumentProfile(id="t").to_dict()
        changed = edited("instruments", payload, {"sigma_target_height": "1,5"}, small_angle=ARCSECONDS)
        assert changed.sigma_target_height == pytest.approx(0.0015)

    def test_a_levelling_class_in_millimetres_per_root_kilometre(self):
        library = _library()
        payload = library.levelling_classes["levelling_classes-1"].to_dict()
        changed = edited(
            "levelling_classes", payload, {"tolerance_coefficient": 4.0}, small_angle=ARCSECONDS
        )
        assert changed.tolerance_coefficient == pytest.approx(0.004)

    def test_a_gravimeter_reading_in_microgal(self):
        library = _library()
        payload = library.gravimeters["gravimeters-1"].to_dict()
        changed = edited("gravimeters", payload, {"sigma_reading": 5.0}, small_angle=ARCSECONDS)
        assert changed.sigma_reading == pytest.approx(5.0e-8)


def _field(kind, key):
    return next(field for field in FIELDS[kind] if field.key == key)


class TestWhatIsRefused:
    def test_what_the_profile_refuses_is_refused_in_its_words(self):
        payload = InstrumentProfile(id="t").to_dict()
        with pytest.raises(ValidationError) as refused:
            edited("instruments", payload, {"sigma_direction": -1.0}, small_angle=ARCSECONDS)
        assert refused.value.code == "validation.instrument_sigma_negative"

    def test_a_counter_gravimeter_needs_its_table(self):
        payload = _library().gravimeters["gravimeters-1"].to_dict()
        with pytest.raises(ValidationError) as refused:
            edited("gravimeters", payload, {"reading_unit": "counter"}, small_angle=ARCSECONDS)
        assert refused.value.code == "validation.counter_gravimeter_without_table"

    def test_text_that_is_not_a_number(self):
        payload = InstrumentProfile(id="t").to_dict()
        with pytest.raises(ValidationError) as refused:
            edited("instruments", payload, {"sigma_zenith": "one"}, small_angle=ARCSECONDS)
        assert refused.value.code == "validation.profile_value_not_a_number"
        assert refused.value.context["parameter"] == "sigma_zenith"


class TestTheLibrary:
    def test_add_refuses_an_id_in_use(self):
        library = _library()
        with pytest.raises(ValidationError) as refused:
            add_profile(library, "instruments", "instruments-1")
        assert refused.value.code == "validation.duplicate_profile"

    def test_duplicate_copies_everything_but_the_id(self):
        library = _library()
        original = edited(
            "instruments",
            library.instruments["instruments-1"].to_dict(),
            {"serial_number": "S-1", "vertical_index": (5.0, 1.0)},
            small_angle=ARCSECONDS,
        )
        library.instruments["instruments-1"] = original
        copy = duplicate_profile(library, "instruments", "instruments-1", "instruments-2")
        assert copy.id == "instruments-2"
        assert copy.vertical_index == original.vertical_index
        assert copy.serial_number == "S-1"

    def test_delete_clears_a_default_that_named_it(self):
        library = _library()
        set_default(library, "levels", "levels-1")
        remove_profile(library, "levels", "levels-1")
        assert library.levels == {}
        assert library.default_level == ""

    def test_a_default_must_be_in_the_library(self):
        with pytest.raises(ValidationError) as refused:
            set_default(_library(), "levels", "nowhere")
        assert refused.value.code == "validation.unknown_profile"

    def test_import_adds_the_new_and_keeps_what_is_already_there(self):
        library = _library()
        mine = library.instruments["instruments-1"]
        other = ProfileLibrary()
        add_profile(other, "instruments", "instruments-1")  # same id, other values
        other.instruments["instruments-1"] = edited(
            "instruments", other.instruments["instruments-1"].to_dict(),
            {"serial_number": "THEIRS"}, small_angle=ARCSECONDS,
        )
        add_profile(other, "reflectors", "prism-2")
        added, kept = import_profiles(library, other)
        assert added == ["reflectors/prism-2"]
        assert kept == ["instruments/instruments-1"]
        assert library.instruments["instruments-1"] is mine

    def test_export_takes_only_what_was_chosen_with_its_default(self):
        library = _library()
        add_profile(library, "instruments", "spare")
        set_default(library, "instruments", "spare")
        exported = export_profiles(library, {"instruments": ["spare"]})
        assert list(exported.instruments) == ["spare"]
        assert exported.default_instrument == "spare"
        assert exported.levels == {}
        # And it is a library a run reads.
        again = ProfileLibrary.from_dict(json.loads(json.dumps(exported.to_dict())))
        assert again.instruments["spare"] == library.instruments["spare"]
