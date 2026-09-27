# SPDX-License-Identifier: GPL-2.0-or-later
"""Frame transformations (``specs/13`` section 5, criterion 4; FR-832).

The arithmetic is checked against PROJ: ``tests/data/frames/proj_reference.json``
holds pyproj's answers for 300 point, epoch and frame-pair combinations, made by
``scripts/check_frames.py`` and re-made in the ``reference`` workflow. What
PROJ cannot check -- moving a point between epochs, a velocity crossing a
transformation, the covariance, and SIRGAS 2000's refusal of any epoch but its
own -- is checked here against the definitions.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.geodesy.frames import (
    TRANSFORMATIONS,
    canonical_frame,
    transform_point,
    transform_vector,
    transformation_path,
)

REFERENCE = json.loads((Path(__file__).parent / "data" / "frames" / "proj_reference.json").read_text())
CURITIBA = np.array([3763788.2, -4367643.4, -2720372.5])
#: SIRGAS-typical: 1.5 cm/year north-north-east, as a plate interior moves.
VELOCITY = np.array([-0.0020, -0.0055, 0.0118])


class TestAgainstProj:
    @pytest.mark.parametrize(
        "case",
        REFERENCE["cases"],
        ids=[f"{c['source']}-{c['target']}-{c['point']}-{c['epoch']}" for c in REFERENCE["cases"]],
    )
    def test_every_case_agrees_to_a_micrometre(self, case):
        moved = transform_point(
            case["xyz"], source=case["source"], target=case["target"], epoch=case["epoch"]
        )
        assert math.dist(moved.xyz, case["proj"]) < 1e-6

    def test_proj_used_the_same_transformation(self):
        """Agreeing with a *different* operation would be a coincidence. SIRGAS
        2000 is the exception PROJ itself makes: it does not implement EPSG:9052
        and offers a no-op, which agrees only because 9052 is the identity."""
        for case in REFERENCE["cases"]:
            (helmert, _inverse), *rest = transformation_path(case["source"], case["target"])
            assert not rest
            if case["target"] == "SIRGAS2000":
                assert case["operation"].startswith("Ballpark")
            else:
                assert helmert.name in case["operation"], case

    def test_the_fixture_says_what_made_it(self):
        assert REFERENCE["epsg"] == "v11.004"
        assert len(REFERENCE["cases"]) == 303


class TestFrameNames:
    @pytest.mark.parametrize(
        ("name", "frame"),
        [
            ("ITRF2020", "ITRF2020"),
            ("EPSG:9988", "ITRF2020"),
            ("epsg:7912", "ITRF2014"),
            ("SIRGAS 2000", "SIRGAS2000"),
            ("EPSG:4674", "SIRGAS2000"),
            ("EPSG:4988", "SIRGAS2000"),
        ],
    )
    def test_every_crs_of_one_datum_is_that_frame(self, name, frame):
        assert canonical_frame(name) == frame

    @pytest.mark.parametrize("name", ["WGS84", "EPSG:4326", "GDA2020", ""])
    def test_anything_else_is_refused(self, name):
        """WGS 84 above all: its realisations are decimetres apart."""
        with pytest.raises(ValidationError) as caught:
            canonical_frame(name)
        assert caught.value.code == "validation.frame_unknown"


class TestTheParameters:
    def test_every_pair_of_itrfs_has_a_direct_transformation(self):
        frames = ("ITRF2000", "ITRF2005", "ITRF2008", "ITRF2014", "ITRF2020")
        for source in frames:
            for target in frames:
                if source != target:
                    assert len(transformation_path(source, target)) == 1

    def test_the_inverse_is_exact(self):
        for helmert in TRANSFORMATIONS:
            epoch = helmert.reference_epoch if helmert.time_specific else 2021.3
            there = helmert.forward(CURITIBA, epoch)
            assert np.abs(helmert.backward(there, epoch) - CURITIBA).max() < 1e-9

    def test_itrf2000_to_2020_is_centimetres_in_z_at_2024(self):
        """The largest of them, and a plausibility check on units: 34.2 mm in
        tz at 2015 growing 1.7 mm a year is 5 cm by 2024, and a scale of
        -2.25 ppb less 0.11 a year shrinks a 6400 km radius by 16 mm."""
        moved = transform_point(CURITIBA, source="ITRF2000", target="ITRF2020", epoch=2024.5)
        shift = moved.xyz - CURITIBA
        tz = 0.0342 + 0.0017 * 9.5
        scale = (-2.25 - 0.11 * 9.5) * 1e-9
        assert shift[2] == pytest.approx(tz + scale * CURITIBA[2], abs=1e-9)


class TestEpochs:
    def test_sirgas_2000_from_another_epoch_needs_a_velocity(self):
        with pytest.raises(ValidationError) as caught:
            transform_point(CURITIBA, source="ITRF2020", target="SIRGAS2000", epoch=2024.5)
        assert caught.value.code == "validation.epoch_change_without_velocity"

    def test_with_one_it_goes_through_itrf2000_and_back_to_2000_4(self):
        moved = transform_point(
            CURITIBA, source="ITRF2020", target="SIRGAS2000", epoch=2024.5, velocity=VELOCITY
        )
        kinds = [(step.kind, step.code) for step in moved.record.steps]
        assert kinds == [("helmert", "EPSG:9994"), ("epoch", ""), ("helmert", "EPSG:9052")]
        assert moved.record.target_epoch == pytest.approx(2000.4)
        # By hand: into ITRF2000 at 2024.5, then 24.1 years back along the
        # velocity as that frame sees it.
        (helmert, inverse), _ = transformation_path("ITRF2020", "SIRGAS2000")
        assert inverse
        in_2000 = helmert.backward(CURITIBA, 2024.5)
        assert np.abs(moved.xyz - (in_2000 + moved.velocity * (2000.4 - 2024.5))).max() < 1e-6
        # Twenty-four years at 1.1 cm/year -- the velocity as ITRF2000 sees it,
        # its z rate 2 mm/year lower -- is 28 cm: why a velocity is required.
        travelled = np.linalg.norm(moved.xyz - in_2000)
        # To a nanometre: the difference of two 4000 km coordinates rounds there.
        assert travelled == pytest.approx(np.linalg.norm(moved.velocity) * 24.1, abs=1e-8)
        assert 0.25 < travelled < 0.30

    def test_a_velocity_crosses_the_transformation_with_its_rates(self):
        """The transformed velocity is the derivative of the transformed
        position: move a year along the velocity on each side and compare."""
        now = transform_point(CURITIBA, source="ITRF2000", target="ITRF2020", epoch=2020.0, velocity=VELOCITY)
        later = transform_point(CURITIBA + VELOCITY, source="ITRF2000", target="ITRF2020", epoch=2021.0)
        assert np.abs((later.xyz - now.xyz) - now.velocity).max() < 1e-9
        # And the rates matter: 1.7 mm/year in tz and -0.11 ppb/year of scale
        # on a Z of -2720 km, 2.0 mm/year together, which a plain rotation of
        # the velocity would drop.
        expected = 0.0017 + (-0.11e-9) * CURITIBA[2]
        assert now.velocity[2] - VELOCITY[2] == pytest.approx(expected, abs=1e-8)

    def test_moving_within_a_frame_is_the_velocity_times_the_interval(self):
        moved = transform_point(
            CURITIBA,
            source="ITRF2020",
            target="ITRF2020",
            epoch=2020.0,
            target_epoch=2025.0,
            velocity=VELOCITY,
        )
        assert np.abs(moved.xyz - (CURITIBA + 5 * VELOCITY)).max() < 1e-12
        assert [step.kind for step in moved.record.steps] == ["epoch"]

    def test_nothing_to_do_is_recorded_as_nothing(self):
        moved = transform_point(CURITIBA, source="EPSG:9988", target="ITRF2020", epoch=2020.0)
        assert moved.record.is_identity
        assert np.array_equal(moved.xyz, CURITIBA)


class TestUncertainty:
    def test_the_covariance_goes_through_the_jacobian(self):
        covariance = np.diag([4e-6, 9e-6, 16e-6])
        moved = transform_point(
            CURITIBA, source="ITRF2014", target="ITRF2020", epoch=2024.0, covariance=covariance
        )
        ((helmert, _),) = transformation_path("ITRF2014", "ITRF2020")
        _t, m = helmert.at(2024.0)
        assert np.allclose(moved.covariance, m @ covariance @ m.T, rtol=0, atol=1e-18)
        # Parts per billion: the sigmas are the same to a nanometre.
        assert np.allclose(np.sqrt(np.diag(moved.covariance)), [2e-3, 3e-3, 4e-3], atol=1e-9)

    def test_a_velocitys_uncertainty_grows_with_the_interval(self):
        moved = transform_point(
            CURITIBA,
            source="ITRF2020",
            target="ITRF2020",
            epoch=2020.0,
            target_epoch=2030.0,
            covariance=np.eye(3) * 1e-6,
            velocity=VELOCITY,
            velocity_covariance=np.eye(3) * 1e-8,
        )
        assert moved.covariance[0, 0] == pytest.approx(1e-6 + 1e-8 * 100)

    def test_the_transformations_own_accuracy_is_recorded_not_added(self):
        """It is common to every point -- a shift of the network, not scatter
        between stations -- so adding it to each covariance would falsify
        every relative position. The record carries it."""
        moved = transform_point(
            CURITIBA, source="ITRF2005", target="ITRF2014", epoch=2020.0, covariance=np.eye(3) * 1e-6
        )
        assert moved.record.accuracy == pytest.approx(0.01)
        assert np.sqrt(moved.covariance[0, 0]) == pytest.approx(1e-3, rel=1e-6)
        payload = moved.record.to_dict()
        assert payload["steps"][0]["code"] == "EPSG:8079"
        assert payload["source"] == "ITRF2005" and payload["target"] == "ITRF2014"


class TestVectors:
    def test_the_translation_cancels_across_a_baseline(self):
        other = CURITIBA + np.array([2446.08, 687.45, 2188.67])
        a = transform_point(CURITIBA, source="ITRF2000", target="ITRF2020", epoch=2024.5).xyz
        b = transform_point(other, source="ITRF2000", target="ITRF2020", epoch=2024.5).xyz
        vector, _covariance, record = transform_vector(
            other - CURITIBA, source="ITRF2000", target="ITRF2020", epoch=2024.5
        )
        assert np.abs(vector - (b - a)).max() < 1e-9
        # Parts per billion of 3.4 km: a few micrometres.
        assert np.abs(vector - (other - CURITIBA)).max() < 1e-5
        assert record.steps[0].code == "EPSG:9994"

    def test_a_baseline_into_sirgas_2000_from_another_epoch_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            transform_vector([1.0, 2.0, 3.0], source="ITRF2000", target="SIRGAS2000", epoch=2024.5)
        assert caught.value.code == "validation.transformation_time_specific"
