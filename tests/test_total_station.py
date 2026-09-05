# SPDX-License-Identifier: GPL-2.0-or-later
"""The total-station module (specs/09), other than RD-01.

RD-01's acceptance criteria live in ``test_reference_total_station.py``. This
file covers the properties that hold for *any* data: that the applied-once rule
is obeyed, that the stochastic precedence refuses rather than inventing, that
every analytic Jacobian matches complex-step differentiation, and that the
atmospheric physics reproduces the magnitudes the specification quotes.
"""

from __future__ import annotations

import math

import pytest

from geocomp.core.differentiation import complex_step_jacobian
from geocomp.core.errors import ValidationError
from geocomp.core.findings import Severity
from geocomp.core.instruments import (
    EdmSpecification,
    InstrumentProfile,
    ProfileLibrary,
    ReflectorProfile,
    SigmaSource,
    StochasticDefaults,
    resolve_sigma,
)
from geocomp.core.instruments.stochastic import (
    DIRECTION,
    HORIZONTAL_ANGLE,
    SLOPE_DISTANCE,
    ZENITH_ANGLE,
)
from geocomp.core.techniques.total_station import (
    Atmosphere,
    Face,
    FacePair,
    FaceReading,
    PreprocessingOptions,
    apply_atmospheric_correction,
    apply_edm_corrections,
    apply_instrument_corrections,
    curvature_and_refraction,
    preprocess_setup,
    reduce_basic,
    reduce_face_pair,
    reduce_single_face,
    reduce_to_ellipsoid,
    reduce_to_projection,
    refractive_index,
    saturation_vapour_pressure,
    setup_diagnostics,
    trigonometric_height,
)
from geocomp.core.techniques.total_station.atmosphere import group_refractivity
from geocomp.core.techniques.total_station.readings import Setup
from geocomp.core.techniques.total_station.reductions import DEFAULT_EARTH_RADIUS
from geocomp.core.uncertainty import Quantity, Strategy, UncertaintyMode
from geocomp.core.units import Unit, celsius_to_kelvin

METRE, RADIAN, KELVIN, PASCAL = Unit.METRE, Unit.RADIAN, Unit.KELVIN, Unit.PASCAL
NONE = Unit.DIMENSIONLESS


def metres(value: float, sigma: float = 0.002) -> Quantity:
    return Quantity.from_std_dev(value, sigma, METRE)


def radians(degrees: float, sigma: float = 5e-6) -> Quantity:
    return Quantity.from_std_dev(math.radians(degrees), sigma, RADIAN)


def atmosphere(t=20.0, p=1013.25, rh=60.0, st=0.0, sp=0.0, sh=0.0) -> Atmosphere:
    return Atmosphere.from_field_units(
        t, p, rh, temperature_sigma=st, pressure_sigma_hpa=sp, humidity_sigma_percent=sh
    )


class TestProfiles:
    def test_a_profile_needs_an_id_because_observations_reference_it(self):
        with pytest.raises(ValidationError) as caught:
            InstrumentProfile(id="")
        assert caught.value.code == "validation.instrument_profile_without_id"

    def test_constants_must_carry_the_right_dimension(self):
        with pytest.raises(ValidationError) as caught:
            InstrumentProfile(id="ts", collimation=Quantity.exact(0.0, METRE))
        assert caught.value.code == "validation.profile_wrong_unit"

    def test_a_cyclic_amplitude_without_a_wavelength_is_refused(self):
        """The correction is periodic in the distance; an amplitude alone has
        no meaning and would silently do nothing."""
        with pytest.raises(ValidationError) as caught:
            InstrumentProfile(id="ts", cyclic_error_amplitude=metres(0.001, 0.0))
        assert caught.value.code == "validation.cyclic_error_without_wavelength"

    def test_a_negative_precision_is_refused(self):
        with pytest.raises(ValidationError):
            EdmSpecification(constant=-0.001, proportional=2e-6)

    def test_the_edm_specification_is_the_manufacturer_two_part_form(self):
        spec = EdmSpecification(constant=0.002, proportional=2e-6)
        assert spec.sigma(0.0) == pytest.approx(0.002)
        assert spec.sigma(1000.0) == pytest.approx(0.004)
        assert spec.sigma(-1000.0) == pytest.approx(0.004), "sign of the distance is irrelevant"

    def test_the_user_scale_factor_multiplies_the_whole_specification(self):
        """Nominal specifications are usually optimistic; a surveyor who has run
        residual analysis on their own instrument has a better number."""
        nominal = EdmSpecification(constant=0.002, proportional=2e-6)
        doubled = EdmSpecification(constant=0.002, proportional=2e-6, scale=2.0)
        assert doubled.sigma(1000.0) == pytest.approx(2.0 * nominal.sigma(1000.0))

    def test_a_profile_round_trips_through_a_document(self):
        profile = InstrumentProfile(
            id="ts15",
            name="Leica TS15",
            collimation=Quantity.from_std_dev(1e-5, 2e-6, RADIAN),
            edm_additive=metres(-0.0345, 0.0003),
            cyclic_error_amplitude=metres(0.0002, 0.0001),
            cyclic_error_wavelength=10.0,
        )
        assert InstrumentProfile.from_dict(profile.to_dict()).to_dict() == profile.to_dict()

    def test_a_library_round_trips(self):
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="a"))
        library.add_reflector(ReflectorProfile(id="p", additive_constant=metres(-0.030, 0.0005)))
        assert ProfileLibrary.from_dict(library.to_dict()).to_dict() == library.to_dict()

    def test_the_first_profile_added_becomes_the_default(self):
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="a"))
        library.add_instrument(InstrumentProfile(id="b"))
        assert library.default_instrument == "a"
        assert library.instrument(None).id == "a"

    def test_a_duplicate_id_is_refused_rather_than_overwriting(self):
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="a"))
        with pytest.raises(ValidationError) as caught:
            library.add_instrument(InstrumentProfile(id="a"))
        assert caught.value.code == "validation.duplicate_instrument_profile"

    def test_an_unknown_instrument_names_what_is_available(self):
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="a"))
        with pytest.raises(ValidationError) as caught:
            library.instrument("nope")
        assert caught.value.code == "validation.unknown_instrument_profile"
        assert "a" in caught.value.context["expected"]

    def test_an_empty_library_refuses_rather_than_inventing_constants(self):
        with pytest.raises(ValidationError) as caught:
            ProfileLibrary().instrument(None)
        assert caught.value.code == "validation.no_instrument_profile"

    def test_no_reflector_is_a_legitimate_answer(self):
        """A reflectorless measurement has no prism and therefore no prism
        constant -- distinct from a prism whose constant happens to be zero."""
        assert ProfileLibrary().reflector(None) is None

    def test_renaming_carries_the_default_with_it(self):
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="old"))
        library.rename_instrument("old", "new")
        assert library.default_instrument == "new"
        assert library.instrument("new").id == "new"


class TestStochasticPrecedence:
    """specs/05 section 5: stated, then instrument, then type default, then refuse."""

    def test_a_stated_sigma_wins_and_is_rigorous(self):
        quantity, source = resolve_sigma(
            SLOPE_DISTANCE, 100.0, stated=0.003, instrument=InstrumentProfile(id="ts")
        )
        assert source is SigmaSource.STATED
        assert quantity.std_dev == pytest.approx(0.003)
        assert quantity.mode is UncertaintyMode.RIGOROUS

    def test_the_instrument_model_comes_next_and_is_approximate(self):
        """A manufacturer's brochure figure is not a measurement. specs/05
        section 2.3 lists NOMINAL_PRECISION among the approximate strategies and
        gives no partial credit."""
        instrument = InstrumentProfile(id="ts", edm=EdmSpecification(0.002, 2e-6))
        quantity, source = resolve_sigma(SLOPE_DISTANCE, 1000.0, instrument=instrument)
        assert source is SigmaSource.INSTRUMENT
        assert quantity.std_dev == pytest.approx(0.004)
        assert quantity.mode is UncertaintyMode.APPROXIMATE
        assert Strategy.NOMINAL_PRECISION in quantity.strategies

    def test_the_type_default_comes_last(self):
        defaults = StochasticDefaults().with_default(DIRECTION, 1e-5)
        quantity, source = resolve_sigma(DIRECTION, 0.5, defaults=defaults)
        assert source is SigmaSource.TYPE_DEFAULT
        assert Strategy.TYPE_DEFAULT in quantity.strategies

    def test_with_nothing_available_it_refuses(self):
        """The step that matters. A fabricated weight does not fail; it silently
        corrupts every statistic computed from it."""
        with pytest.raises(ValidationError) as caught:
            resolve_sigma(DIRECTION, 0.5, observation_id="d1")
        assert caught.value.code == "validation.missing_stochastic_model"
        assert caught.value.context["observation"] == "d1"
        assert "invent" in caught.value.context["expected"]

    def test_an_empty_default_set_still_refuses(self):
        """A fresh installation configures no defaults, and must refuse."""
        with pytest.raises(ValidationError):
            resolve_sigma(DIRECTION, 0.5, defaults=StochasticDefaults())

    def test_angular_precision_improves_as_the_root_of_the_set_count(self):
        instrument = InstrumentProfile(id="ts", sigma_direction=1e-5)
        one, _ = resolve_sigma(DIRECTION, 0.5, instrument=instrument, sets=1)
        four, _ = resolve_sigma(DIRECTION, 0.5, instrument=instrument, sets=4)
        assert four.std_dev == pytest.approx(one.std_dev / 2.0)

    def test_an_angle_is_root_two_times_a_direction(self):
        """An angle is the difference of two directions from one setup: the
        orientation cancels, the two pointing errors do not."""
        instrument = InstrumentProfile(id="ts", sigma_direction=1e-5)
        direction, _ = resolve_sigma(DIRECTION, 0.5, instrument=instrument)
        angle, _ = resolve_sigma(HORIZONTAL_ANGLE, 0.5, instrument=instrument)
        assert angle.std_dev == pytest.approx(direction.std_dev * math.sqrt(2.0))

    def test_the_zenith_refraction_term_grows_with_distance(self):
        instrument = InstrumentProfile(id="ts", sigma_zenith=5e-6, sigma_zenith_refraction=1e-9)
        near, _ = resolve_sigma(ZENITH_ANGLE, 10.0, instrument=instrument)
        far, _ = resolve_sigma(ZENITH_ANGLE, 5000.0, instrument=instrument)
        assert far.std_dev > near.std_dev
        assert far.std_dev == pytest.approx(5e-6 + 5000.0 * 1e-9)

    def test_a_negative_stated_sigma_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            resolve_sigma(SLOPE_DISTANCE, 10.0, stated=-0.001)
        assert caught.value.code == "validation.stated_sigma_negative"


class TestAtmosphere:
    """The magnitudes specs/09 section 2.3 quotes, reproduced rather than assumed."""

    def test_the_group_refractivity_matches_the_published_formula(self):
        """IUGG 1960: N_g = 287.6155 + 4.88660/l^2 + 0.06800/l^4."""
        assert group_refractivity(0.850) == pytest.approx(294.5092, abs=1e-4)
        assert group_refractivity(0.633) == pytest.approx(300.2345, abs=1e-3)

    def test_saturation_vapour_pressure_matches_the_wmo_form(self):
        e_s = saturation_vapour_pressure(Quantity.exact(celsius_to_kelvin(20.0), KELVIN))
        assert e_s.value == pytest.approx(2332.6, abs=1.0)
        assert e_s.unit is PASCAL

    def test_roughly_one_ppm_per_degree_celsius(self):
        def ppm(t: float) -> float:
            return (refractive_index(atmosphere(t=t)).value - 1.0) * 1e6

        assert ppm(21.0) - ppm(20.0) == pytest.approx(-1.0, abs=0.1)

    def test_roughly_one_ppm_per_three_and_a_half_hectopascals(self):
        def ppm(p: float) -> float:
            return (refractive_index(atmosphere(p=p)).value - 1.0) * 1e6

        assert ppm(1016.75) - ppm(1013.25) == pytest.approx(1.0, abs=0.1)

    def test_humidity_matters_much_less_than_the_other_two(self):
        """About 0.9 ppm across the entire range, which is why a missing
        hygrometer reading is far less serious than a missing thermometer."""
        def ppm(rh: float) -> float:
            return (refractive_index(atmosphere(rh=rh)).value - 1.0) * 1e6

        assert abs(ppm(100.0) - ppm(0.0)) == pytest.approx(0.9, abs=0.1)

    def test_a_two_degree_uncertainty_is_about_two_ppm(self):
        """The figure specs/09 section 2.3 quotes, and the reason the
        propagation exists rather than an assumption that it is negligible."""
        index = refractive_index(atmosphere(st=2.0))
        assert index.std_dev * 1e6 == pytest.approx(2.0, abs=0.2)

    def test_humid_air_is_more_temperature_sensitive_not_less(self):
        """T appears twice: in the dry term, and inside the saturation vapour
        pressure of the wet term. Both push the refractivity the same way as T
        rises, so humidity *amplifies* the temperature sensitivity rather than
        offsetting it -- which is why the two paths are propagated through one
        Jacobian rather than added as independent variances."""
        wet = refractive_index(atmosphere(rh=100.0, st=2.0)).std_dev
        dry = refractive_index(atmosphere(rh=0.0, st=2.0)).std_dev
        assert wet > dry

    def test_the_two_temperature_paths_are_one_jacobian_not_two_variances(self):
        """Treating them as independent contributions would give the quadrature
        sum, which is strictly smaller than the linear sum the single Jacobian
        produces. The two differ measurably, so this pins down which is used."""
        combined = refractive_index(atmosphere(rh=100.0, st=2.0)).std_dev
        dry_only = refractive_index(atmosphere(rh=0.0, st=2.0)).std_dev
        wet_contribution = combined - dry_only
        quadrature = math.hypot(dry_only, wet_contribution)
        assert combined > quadrature

    def test_the_correction_is_applied_to_the_distance(self):
        instrument = InstrumentProfile(id="ts")
        result = apply_atmospheric_correction(metres(1000.0), atmosphere(), instrument)
        assert result.applied
        assert result.distance.value != 1000.0
        assert abs(result.ppm.value) < 50.0

    def test_it_is_not_applied_twice(self):
        """The applied-once rule. An instrument configured to correct internally
        must not have GeoComp correct again."""
        instrument = InstrumentProfile(id="ts", applies_atmospheric=True)
        result = apply_atmospheric_correction(metres(1000.0), atmosphere(), instrument)
        assert not result.applied
        assert result.distance.value == pytest.approx(1000.0)
        assert result.ppm.value != 0.0, "the ppm is still reported, for the record"

    def test_a_celsius_temperature_is_refused_as_kelvin(self):
        with pytest.raises(ValidationError) as caught:
            Atmosphere(
                temperature=Quantity.exact(-20.0, KELVIN),
                pressure=Quantity.exact(101325.0, PASCAL),
                humidity=Quantity.exact(0.5, NONE),
            )
        assert caught.value.code == "validation.temperature_not_absolute"

    def test_humidity_outside_zero_to_one_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            Atmosphere(
                temperature=Quantity.exact(293.15, KELVIN),
                pressure=Quantity.exact(101325.0, PASCAL),
                humidity=Quantity.exact(60.0, NONE),
            )
        assert caught.value.code == "validation.humidity_out_of_range"

    def test_the_celsius_conversion_preserves_the_variance(self):
        """Adding 273.15 shifts a value and leaves its spread alone."""
        field = atmosphere(t=20.0, st=2.0)
        assert field.temperature.std_dev == pytest.approx(2.0)
        assert field.temperature.value == pytest.approx(293.15)


class TestEdmCorrections:
    def test_the_additive_constants_add(self):
        instrument = InstrumentProfile(id="ts", edm_additive=metres(-0.010, 0.0002))
        reflector = ReflectorProfile(id="p", additive_constant=metres(-0.020, 0.0003))
        result = apply_edm_corrections(metres(100.0), instrument, reflector)
        assert result.distance.value == pytest.approx(100.0 - 0.030)

    def test_a_constant_the_instrument_already_applied_is_not_applied_again(self):
        """The silent metre-level error this rule exists to prevent."""
        instrument = InstrumentProfile(
            id="ts", edm_additive=metres(-0.030, 0.0), applies_edm_constant=True
        )
        result = apply_edm_corrections(metres(100.0), instrument)
        assert result.distance.value == pytest.approx(100.0)
        assert result.additive_skipped
        assert any(f.code == "edm_constant_applied_by_instrument" for f in result.findings)

    def test_a_prism_constant_the_instrument_applied_is_not_applied_again(self):
        instrument = InstrumentProfile(id="ts")
        reflector = ReflectorProfile(
            id="p", additive_constant=metres(-0.030, 0.0), applies_internally=True
        )
        result = apply_edm_corrections(metres(100.0), instrument, reflector)
        assert result.distance.value == pytest.approx(100.0)
        assert result.additive_skipped

    def test_the_calibration_uncertainty_propagates(self):
        """A constant known to 0.3 mm and one known to 3 mm give the same
        distance and correctly different uncertainties."""
        precise = InstrumentProfile(id="a", edm_additive=metres(-0.030, 0.0003))
        vague = InstrumentProfile(id="b", edm_additive=metres(-0.030, 0.003))
        first = apply_edm_corrections(metres(100.0, 0.001), precise)
        second = apply_edm_corrections(metres(100.0, 0.001), vague)
        assert first.distance.value == pytest.approx(second.distance.value)
        assert second.distance.std_dev > first.distance.std_dev

    def test_the_scale_factor_multiplies(self):
        instrument = InstrumentProfile(
            id="ts", edm_scale=Quantity.from_std_dev(1.0 + 3e-6, 1e-6, NONE)
        )
        result = apply_edm_corrections(metres(1000.0), instrument)
        assert result.distance.value == pytest.approx(1000.0 * (1.0 + 3e-6))

    def test_the_cyclic_error_is_periodic_in_the_distance(self):
        instrument = InstrumentProfile(
            id="ts",
            cyclic_error_amplitude=metres(0.001, 0.0002),
            cyclic_error_wavelength=10.0,
        )
        quarter = apply_edm_corrections(metres(102.5), instrument).cyclic.value
        three_quarters = apply_edm_corrections(metres(107.5), instrument).cyclic.value
        assert quarter == pytest.approx(-0.001, abs=1e-9)
        assert three_quarters == pytest.approx(0.001, abs=1e-9)
        # A full wavelength later, the same value.
        assert apply_edm_corrections(metres(112.5), instrument).cyclic.value == pytest.approx(
            quarter, abs=1e-9
        )


class TestInstrumentCorrections:
    @staticmethod
    def _reduction(zenith_degrees: float):
        pair = FacePair(
            FaceReading("t", Face.DIRECT, radians(30.0), radians(zenith_degrees)),
            FaceReading("t", Face.REVERSE, radians(210.0), radians(360.0 - zenith_degrees)),
        )
        return reduce_face_pair(pair)

    def test_trunnion_tilt_vanishes_on_a_horizontal_sight(self):
        """cot(90 degrees) is zero: the horizontal axis being out of level does
        not displace a horizontal direction."""
        instrument = InstrumentProfile(
            id="ts", trunnion_tilt=Quantity.from_std_dev(1e-4, 1e-5, RADIAN)
        )
        reduction = self._reduction(90.0)
        corrected = apply_instrument_corrections(reduction, instrument)
        assert corrected.horizontal.value == pytest.approx(reduction.horizontal.value, abs=1e-15)

    def test_trunnion_tilt_grows_as_the_sight_steepens(self):
        instrument = InstrumentProfile(
            id="ts", trunnion_tilt=Quantity.from_std_dev(1e-4, 1e-5, RADIAN)
        )
        shallow = apply_instrument_corrections(self._reduction(80.0), instrument)
        steep = apply_instrument_corrections(self._reduction(60.0), instrument)
        shallow_shift = abs(shallow.horizontal.value - self._reduction(80.0).horizontal.value)
        steep_shift = abs(steep.horizontal.value - self._reduction(60.0).horizontal.value)
        assert steep_shift > shallow_shift

    def test_a_near_vertical_sight_is_reported_rather_than_amplified(self):
        """cot(z) is unbounded at the zenith, and a circle reading there carries
        almost no directional information anyway."""
        instrument = InstrumentProfile(
            id="ts", trunnion_tilt=Quantity.from_std_dev(1e-4, 1e-5, RADIAN)
        )
        corrected = apply_instrument_corrections(self._reduction(0.2), instrument)
        assert any(f.code == "near_vertical_sight" for f in corrected.findings)

    def test_a_single_face_pointing_has_the_constants_applied(self):
        """The pair cancels them; a lone reading cannot, so they come from the
        profile with their own uncertainties."""
        instrument = InstrumentProfile(
            id="ts",
            collimation=Quantity.from_std_dev(5e-5, 1e-6, RADIAN),
            vertical_index=Quantity.from_std_dev(3e-5, 1e-6, RADIAN),
        )
        reading = FaceReading("t", Face.DIRECT, radians(30.0), radians(85.0))
        reduction = reduce_single_face(reading, instrument)
        assert reduction.single_face
        assert reduction.horizontal.value == pytest.approx(
            math.radians(30.0) - 5e-5, abs=1e-15
        )
        assert reduction.zenith.value == pytest.approx(math.radians(85.0) - 3e-5, abs=1e-15)
        assert reduction.horizontal.std_dev > reading.horizontal.std_dev


class TestBasicReduction:
    def test_it_matches_the_closed_form_the_uncertainty_spec_works_through(self):
        """specs/05 section 4.1:

        sigma^2 = sin^2(z) sigma_d^2 + d^2 cos^2(z) sigma_z^2 + 2 d sin z cos z sigma_dz
        """
        d, z = metres(1000.0, 0.003), radians(88.0, 5e-6)
        for rho in (0.0, 0.5, -0.7):
            result = reduce_basic(d, z, metres(1.5, 0.001), metres(1.6, 0.001), correlation=rho)
            sin_z, cos_z = math.sin(z.value), math.cos(z.value)
            covariance = rho * d.std_dev * z.std_dev
            expected = math.sqrt(
                sin_z**2 * d.variance
                + d.value**2 * cos_z**2 * z.variance
                + 2.0 * d.value * sin_z * cos_z * covariance
            )
            assert result.horizontal_distance.std_dev == pytest.approx(expected, rel=1e-12)

    def test_the_correlation_term_is_not_negligible(self):
        """Which is the whole reason specs/05 requires it be kept."""
        d, z = metres(1000.0, 0.003), radians(88.0, 5e-6)
        independent = reduce_basic(d, z, metres(1.5), metres(1.6), correlation=0.0)
        correlated = reduce_basic(d, z, metres(1.5), metres(1.6), correlation=0.8)
        assert correlated.horizontal_distance.std_dev != pytest.approx(
            independent.horizontal_distance.std_dev, rel=1e-3
        )

    def test_an_unstated_correlation_is_recorded_as_an_assumption(self):
        """specs/05 section 4.1: dropping the term is INDEPENDENCE_ASSUMED and
        must be recorded as such, not silently treated as zero."""
        result = reduce_basic(metres(100.0), radians(89.0), metres(1.5), metres(1.6))
        assert Strategy.INDEPENDENCE_ASSUMED in result.horizontal_distance.strategies
        assert result.horizontal_distance.mode is UncertaintyMode.APPROXIMATE

    def test_an_explicit_zero_correlation_is_rigorous(self):
        """Knowing the correlation is zero is different from not knowing it."""
        result = reduce_basic(
            metres(100.0), radians(89.0), metres(1.5), metres(1.6), correlation=0.0
        )
        assert Strategy.INDEPENDENCE_ASSUMED not in result.horizontal_distance.strategies

    @staticmethod
    def _output_correlation(sigma_zenith: float, zenith_degrees: float = 60.0) -> float:
        result = reduce_basic(
            metres(1000.0, 0.003),
            radians(zenith_degrees, sigma_zenith),
            metres(1.5, 0.0),
            metres(1.6, 0.0),
            correlation=0.0,
        )
        correlation = result.covariance.to_correlation()
        return float(
            correlation[
                result.covariance.index("horizontal_distance"),
                result.covariance.index("height_difference"),
            ]
        )

    def test_the_outputs_are_correlated_through_the_shared_readings(self):
        """The horizontal distance and the height difference are computed from
        the same two readings, so they are never independent -- and in both
        limits they are almost perfectly correlated, with opposite signs.

        When the *distance* dominates the error budget both outputs scale with
        it together, giving +1. When the *zenith angle* dominates, an error that
        lengthens one shortens the other, giving -1. A 3D adjustment that
        assumed independence would be badly wrong at either end, which is why
        the joint covariance is the result rather than three separate sigmas.
        """
        angle_dominated = self._output_correlation(sigma_zenith=5e-5)
        distance_dominated = self._output_correlation(sigma_zenith=1e-9)

        assert angle_dominated == pytest.approx(-1.0, abs=0.05)
        assert distance_dominated == pytest.approx(1.0, abs=0.05)

    @pytest.mark.parametrize("zenith_degrees", [45.0, 60.0, 80.0])
    def test_the_correlation_vanishes_exactly_where_the_two_errors_balance(
        self, zenith_degrees
    ):
        """A closed-form property worth pinning down, because getting it right
        by accident is unlikely.

            cov(d_h, dH) = sin z cos z (sigma_d^2 - d^2 sigma_z^2)

        so the correlation is zero exactly when ``sigma_d = d sigma_z`` -- when
        the distance's own precision equals the lateral spread the angular
        precision implies at that distance -- and that condition does not depend
        on the zenith angle at all.
        """
        balanced = 0.003 / 1000.0
        assert self._output_correlation(
            sigma_zenith=balanced, zenith_degrees=zenith_degrees
        ) == pytest.approx(0.0, abs=1e-9)

        assert self._output_correlation(
            sigma_zenith=balanced * 10.0, zenith_degrees=zenith_degrees
        ) < 0.0
        assert self._output_correlation(
            sigma_zenith=balanced / 10.0, zenith_degrees=zenith_degrees
        ) > 0.0

    def test_the_correlation_is_never_silently_dropped(self):
        """Whatever its size, it is present in the covariance -- the caller
        decides whether to neglect it, and records the decision if so."""
        result = reduce_basic(
            metres(1000.0, 0.003), radians(88.0), metres(1.5), metres(1.6), correlation=0.0
        )
        i = result.covariance.index("horizontal_distance")
        j = result.covariance.index("height_difference")
        assert result.covariance.matrix[i, j] != 0.0

    def test_the_analytic_jacobian_matches_complex_step_differentiation(self):
        """specs/05 section 2.2: every analytic Jacobian has a test against a
        numerical one. A sign error here produces a plausible wrong uncertainty
        rather than an exception, which is the failure mode the whole
        uncertainty layer exists to prevent.

        The comparison is on the *propagated covariance*, not on the Jacobian in
        isolation, so it exercises the implementation rather than a
        reimplementation of it.
        """
        import cmath

        import numpy as np

        d, z = metres(1000.0, 0.003), radians(88.0, 5e-6)
        hi, hs = metres(1.500, 0.001), metres(1.600, 0.001)
        rho = 0.4
        result = reduce_basic(d, z, hi, hs, correlation=rho)

        def reduce(values):
            distance, zenith, instrument, target = values
            vertical = distance * cmath.cos(zenith)
            return [distance * cmath.sin(zenith), vertical, vertical + instrument - target]

        numeric = complex_step_jacobian(
            reduce, [d.value, z.value, hi.value, hs.value]
        )
        covariance = np.diag([d.variance, z.variance, hi.variance, hs.variance])
        covariance[0, 1] = covariance[1, 0] = rho * d.std_dev * z.std_dev
        expected = numeric @ covariance @ numeric.T

        assert np.allclose(result.covariance.matrix, expected, rtol=1e-9, atol=1e-18)

    def test_a_wrong_unit_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            reduce_basic(radians(45.0), radians(89.0), metres(1.5), metres(1.6))
        assert caught.value.code == "validation.reduction_wrong_unit"


class TestGeometricReductions:
    @pytest.mark.parametrize(
        ("distance", "expected_mm"), [(100.0, 0.683), (1000.0, 68.278), (5000.0, 1706.953)]
    )
    def test_curvature_and_refraction_reproduce_the_standard_magnitudes(
        self, distance, expected_mm
    ):
        correction = curvature_and_refraction(Quantity.exact(distance, METRE))
        assert correction.value * 1000.0 == pytest.approx(expected_mm, abs=0.01)

    def test_the_refraction_coefficient_dominates_on_long_sights(self):
        """k is poorly known and varies through the day, which is why its
        uncertainty is an input rather than an assumption."""
        short = curvature_and_refraction(Quantity.exact(100.0, METRE))
        long = curvature_and_refraction(Quantity.exact(5000.0, METRE))
        assert long.std_dev / long.value == pytest.approx(short.std_dev / short.value, rel=1e-6)
        assert long.std_dev > 0.09

    def test_a_stated_refraction_coefficient_is_used(self):
        stated = Quantity.from_std_dev(0.20, 0.01, NONE)
        correction = curvature_and_refraction(
            Quantity.exact(1000.0, METRE), refraction_coefficient=stated
        )
        assert correction.value == pytest.approx((1.0 - 0.20) * 1000.0**2 / (2 * DEFAULT_EARTH_RADIUS))

    def test_the_trigonometric_height_applies_it(self):
        reduction = reduce_basic(
            metres(1000.0), radians(88.0), metres(1.5), metres(1.6), correlation=0.0
        )
        corrected = trigonometric_height(reduction)
        assert corrected.value > reduction.height_difference.value
        assert corrected.value - reduction.height_difference.value == pytest.approx(
            0.0683, abs=0.001
        )

    def test_reduction_to_the_ellipsoid_shortens_a_distance_measured_above_it(self):
        result = reduce_to_ellipsoid(metres(1000.0), metres(1000.0, 0.5))
        assert result.distance.value < 1000.0
        assert result.correction.value == pytest.approx(-0.1569, abs=1e-3)

    def test_it_carries_the_height_uncertainty(self):
        """FR-205: a distance reduced to the ellipsoid is only as certain as the
        height it was reduced with."""
        precise = reduce_to_ellipsoid(metres(1000.0, 0.001), metres(1000.0, 0.01))
        vague = reduce_to_ellipsoid(metres(1000.0, 0.001), metres(1000.0, 50.0))
        assert vague.distance.std_dev > precise.distance.std_dev

    def test_the_geoid_undulation_is_applied_when_given(self):
        """Reducing with an orthometric height instead of an ellipsoidal one is
        a systematic scale error of about 1.6 ppm per 10 m."""
        without = reduce_to_ellipsoid(metres(1000.0), metres(100.0, 0.01))
        with_geoid = reduce_to_ellipsoid(
            metres(1000.0), metres(100.0, 0.01), geoid_undulation=metres(-10.0, 0.1)
        )
        assert with_geoid.distance.value > without.distance.value
        assert with_geoid.distance.value - without.distance.value == pytest.approx(
            1.57e-3, rel=0.05
        )

    def test_reduction_to_the_projection_scales(self):
        result = reduce_to_projection(
            metres(1000.0), Quantity.from_std_dev(0.9996, 1e-7, NONE)
        )
        assert result.distance.value == pytest.approx(999.6)
        assert result.correction.value == pytest.approx(-0.4)

    def test_a_scale_factor_with_a_dimension_is_refused(self):
        with pytest.raises(ValidationError) as caught:
            reduce_to_projection(metres(1000.0), metres(0.9996))
        assert caught.value.code == "validation.scale_factor_wrong_unit"


class TestSetupDiagnostics:
    @staticmethod
    def _setup(collimations_arcsec):
        setup = Setup(station="A", instrument_height=metres(1.5, 0.001), instrument_id="ts")
        for index, arcsec in enumerate(collimations_arcsec):
            c = arcsec / 3600.0
            setup.pairs.append(
                FacePair(
                    FaceReading(f"t{index}", Face.DIRECT, radians(30.0 + c), radians(90.0)),
                    FaceReading(f"t{index}", Face.REVERSE, radians(210.0 - c), radians(270.0)),
                )
            )
        return setup

    def test_a_constant_collimation_is_reported_but_not_flagged(self):
        """It is instrumental, and the face pairs cancelled it."""
        setup = self._setup([20.0, 20.0, 20.0])
        reductions = [reduce_face_pair(p, collimation_tolerance=1.0) for p in setup.pairs]
        diagnostics = setup_diagnostics(setup, reductions)
        assert math.degrees(diagnostics.collimation_mean) * 3600 == pytest.approx(20.0, abs=1e-6)
        assert diagnostics.collimation_spread == pytest.approx(0.0, abs=1e-12)
        assert not diagnostics.findings

    def test_a_drifting_collimation_is_flagged(self):
        """The instrument moved during the setup, and pairing does not fix it."""
        setup = self._setup([5.0, 40.0, 90.0])
        reductions = [reduce_face_pair(p, collimation_tolerance=1.0) for p in setup.pairs]
        diagnostics = setup_diagnostics(
            setup, reductions, collimation_drift_tolerance=math.radians(10.0 / 3600.0)
        )
        assert any(f.code == "collimation_drift" for f in diagnostics.findings)

    def test_one_pair_has_no_spread_to_report(self):
        setup = self._setup([20.0])
        reductions = [reduce_face_pair(p, collimation_tolerance=1.0) for p in setup.pairs]
        assert setup_diagnostics(setup, reductions).collimation_spread == 0.0


class TestPipeline:
    @staticmethod
    def _setup(**kwargs):
        setup = Setup(
            station="A", instrument_height=metres(1.500, 0.001), instrument_id="ts", **kwargs
        )
        setup.pairs.append(
            FacePair(
                FaceReading(
                    "B", Face.DIRECT, radians(0.0), radians(88.0), metres(150.0),
                    target_height=metres(1.600, 0.001),
                ),
                FaceReading(
                    "B", Face.REVERSE, radians(180.0), radians(272.0), metres(150.0),
                    target_height=metres(1.600, 0.001),
                ),
            )
        )
        return setup

    @staticmethod
    def _library():
        library = ProfileLibrary()
        library.add_instrument(InstrumentProfile(id="ts", edm_additive=metres(-0.030, 0.0003)))
        return library

    def test_the_chain_runs_and_applies_every_stage(self):
        result = preprocess_setup(self._setup(), self._library())
        pointing = result.pointings[0]
        assert pointing.basic is not None
        # The additive constant moved the distance; the reduction turned it into
        # a horizontal one; the height difference used both heights.
        assert pointing.reduction.distance.value < 150.0
        assert pointing.basic.horizontal_distance.value < pointing.reduction.distance.value

    def test_missing_meteorological_data_is_reported_not_defaulted(self):
        """Over a kilometre a 10 degree error is 10 mm; the user should know it
        was assumed rather than measured."""
        result = preprocess_setup(self._setup(), self._library())
        assert any(f.code == "no_atmospheric_data" for f in result.all_findings)
        assert result.pointings[0].atmospheric_ppm is None

    def test_recorded_conditions_are_used_when_present(self):
        setup = self._setup(
            temperature=Quantity.from_std_dev(celsius_to_kelvin(28.0), 1.0, KELVIN),
            pressure=Quantity.from_std_dev(94000.0, 200.0, PASCAL),
            humidity=Quantity.from_std_dev(0.7, 0.1, NONE),
        )
        result = preprocess_setup(setup, self._library())
        assert result.pointings[0].atmospheric_ppm is not None
        assert not any(f.code == "no_atmospheric_data" for f in result.all_findings)

    def test_the_atmospheric_stage_can_be_turned_off_explicitly(self):
        result = preprocess_setup(
            self._setup(),
            self._library(),
            options=PreprocessingOptions(apply_atmospheric=False),
        )
        assert not any(f.code == "no_atmospheric_data" for f in result.all_findings)

    def test_a_blocking_finding_makes_a_pointing_unusable_without_deleting_it(self):
        """specs/19 section 2: a rejected measurement that disappears from the
        output cannot be reconsidered."""
        setup = self._setup()
        setup.pairs[0] = FacePair(
            setup.pairs[0].direct,
            FaceReading(
                "B", Face.REVERSE, radians(180.0), radians(272.0), metres(149.0),
                target_height=metres(1.600, 0.001),
            ),
        )
        result = preprocess_setup(setup, self._library())
        assert len(result.pointings) == 1
        assert not result.pointings[0].is_usable
        assert result.severity is Severity.BLOCKING


class TestConstantsMatchTheSettings:
    """The core is callable without a settings service, so it carries its own
    defaults -- which means two copies of every number, and two copies drift.

    These assertions are the join. Changing a default in one place now fails
    until it is changed in the other.
    """

    @pytest.mark.parametrize(
        ("constant", "key"),
        [
            ("DEFAULT_COLLIMATION_TOLERANCE", "total_station.collimation_tolerance"),
            ("DEFAULT_DISTANCE_TOLERANCE", "total_station.face_distance_tolerance"),
        ],
    )
    def test_face_tolerances_agree(self, constant, key):
        from geocomp.core.settings_def import setting
        from geocomp.core.techniques.total_station import face

        assert getattr(face, constant) == pytest.approx(setting(key).default)

    def test_the_refraction_coefficient_agrees(self):
        from geocomp.core.settings_def import setting
        from geocomp.core.techniques.total_station.reductions import (
            DEFAULT_REFRACTION_COEFFICIENT,
        )

        assert DEFAULT_REFRACTION_COEFFICIENT == pytest.approx(
            setting("total_station.refraction_coefficient").default
        )

    def test_the_atmospheric_model_choices_match_the_enum(self):
        """The setting stores text and the core uses an enum; a value in one
        that the other cannot represent is a crash waiting for a user."""
        from geocomp.core.instruments.profiles import AtmosphericModel
        from geocomp.core.settings_def import setting

        choices = set(setting("total_station.atmospheric_model").choices)
        assert choices == {model.value for model in AtmosphericModel}
