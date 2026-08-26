# SPDX-License-Identifier: GPL-2.0-or-later
"""The first-velocity (atmospheric) correction (FR-401).

``specs/09-module-total-station.md`` section 2.3.

An EDM measures a time of flight and converts it to a distance using an assumed
refractive index. The air it actually measured through had a different one, so
the distance it reported is wrong by the ratio:

    d_true = d_measured * n_reference / n_actual

expressed conventionally in parts per million. It is roughly 1 ppm per 1 degree
Celsius and per 3.5 hPa -- so on a 20 m sight it is microns, and over a
kilometre with a 10 degree error it is 10 mm.

**That range is exactly why the uncertainty propagates rather than being
assumed negligible** (FR-204). GeoComp does not decide for the user whether the
correction matters; it computes it, attaches the uncertainty of the
meteorological readings that produced it, and lets the resulting sigma say so.
Where no meteorological data exist, the configured defaults are used and the
result is marked ``APPROXIMATE`` with :attr:`Strategy.TYPE_DEFAULT` (FR-202).

## On the model choice

:func:`refractive_index` implements **Barrell and Sears** via the IUGG 1960
group-refractivity formula, which is the physics that every manufacturer's
simplified formula approximates, and which is documented in the standard
literature rather than in one vendor's manual.

The ``LEICA`` and ``TRIMBLE`` options of
:class:`~geocomp.core.instruments.profiles.AtmosphericModel` select the same
physics evaluated at that manufacturer's **reference conditions**, which is the
part of the difference that actually moves a result. Their published simplified
closed forms differ from Barrell-Sears by well under 0.1 ppm -- 0.1 mm per
kilometre -- and transcribing them from the manuals is recorded as outstanding
in ``specs/09``. Shipping constants recalled rather than read would be worse
than shipping the physics they approximate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.profiles import AtmosphericModel, InstrumentProfile
from geocomp.core.uncertainty import Covariance, Quantity, UncertaintyMode
from geocomp.core.units import Unit, celsius_to_kelvin

__all__ = [
    "Atmosphere",
    "AtmosphericCorrection",
    "apply_atmospheric_correction",
    "group_refractivity",
    "refractive_index",
    "saturation_vapour_pressure",
]

#: Standard conditions the group refractivity is defined at: 0 degrees Celsius,
#: 1013.25 hPa, dry air with 0.0375 percent CO2.
STANDARD_TEMPERATURE_K = 273.15
STANDARD_PRESSURE_PA = 101325.0

#: Coefficient of the water-vapour term, in kelvin per pascal, converted from
#: the conventional 11.27 K/hPa of the Barrell-Sears formulation.
WATER_VAPOUR_COEFFICIENT = 11.27 / 100.0

#: Typical carrier wavelength of an infrared EDM, in micrometres. Instruments
#: vary between roughly 0.6 and 0.9 um; the resulting refractivity differs by
#: about 1.5 ppm across that range, which is why it is a parameter.
DEFAULT_WAVELENGTH_UM = 0.850

#: Reference conditions each manufacturer's zero-ppm setting corresponds to:
#: (temperature in Celsius, pressure in hPa, relative humidity as a fraction).
#: Used only when the instrument profile does not state its own reference index.
_REFERENCE_CONDITIONS = {
    AtmosphericModel.BARRELL_SEARS: (15.0, 1013.25, 0.0),
    AtmosphericModel.LEICA: (12.0, 1013.25, 0.60),
    AtmosphericModel.TRIMBLE: (20.0, 1013.25, 0.50),
}


@dataclass(frozen=True)
class Atmosphere:
    """The air a distance was measured through.

    Attributes:
        temperature: Kelvin. Stored in SI even though field books record
            Celsius, because the Celsius scale is affine and mixing the two is
            a 273 K error waiting to happen -- see
            :func:`~geocomp.core.units.celsius_to_kelvin`.
        pressure: Pascals.
        humidity: Relative humidity as a fraction in ``[0, 1]``.
        wavelength_um: The EDM's carrier wavelength, micrometres.
    """

    temperature: Quantity
    pressure: Quantity
    humidity: Quantity
    wavelength_um: float = DEFAULT_WAVELENGTH_UM

    def __post_init__(self) -> None:
        for name, quantity, unit in (
            ("temperature", self.temperature, Unit.KELVIN),
            ("pressure", self.pressure, Unit.PASCAL),
            ("humidity", self.humidity, Unit.DIMENSIONLESS),
        ):
            if quantity.unit is not unit:
                raise ValidationError(
                    "atmosphere_wrong_unit",
                    parameter=name,
                    received=quantity.unit.name,
                    expected=unit.name,
                )
        if self.temperature.value <= 0.0:
            raise ValidationError(
                "temperature_not_absolute",
                received=self.temperature.value,
                expected="a temperature in kelvin; use celsius_to_kelvin() to convert",
            )
        if not 0.0 <= self.humidity.value <= 1.0:
            raise ValidationError(
                "humidity_out_of_range",
                received=self.humidity.value,
                expected="a relative humidity between 0 and 1",
            )
        if self.wavelength_um <= 0.0:
            raise ValidationError(
                "non_positive_wavelength",
                received=self.wavelength_um,
                expected="a positive carrier wavelength in micrometres",
            )

    @classmethod
    def from_field_units(
        cls,
        temperature_celsius: Quantity,
        pressure_hpa: Quantity,
        humidity_percent: Quantity,
        *,
        wavelength_um: float = DEFAULT_WAVELENGTH_UM,
    ) -> Atmosphere:
        """Build from the units a field book actually records.

        The variances carry across the temperature conversion unchanged: adding
        273.15 shifts a value and leaves its spread alone.
        """
        return cls(
            temperature=Quantity(
                value=celsius_to_kelvin(temperature_celsius.value),
                variance=temperature_celsius.variance,
                unit=Unit.KELVIN,
                mode=temperature_celsius.mode,
                strategies=temperature_celsius.strategies,
            ),
            pressure=Quantity(
                value=pressure_hpa.value * 100.0,
                variance=pressure_hpa.variance * 100.0**2,
                unit=Unit.PASCAL,
                mode=pressure_hpa.mode,
                strategies=pressure_hpa.strategies,
            ),
            humidity=Quantity(
                value=humidity_percent.value / 100.0,
                variance=humidity_percent.variance / 100.0**2,
                unit=Unit.DIMENSIONLESS,
                mode=humidity_percent.mode,
                strategies=humidity_percent.strategies,
            ),
            wavelength_um=wavelength_um,
        )


@dataclass(frozen=True)
class AtmosphericCorrection:
    """A distance with the first-velocity correction applied.

    Attributes:
        distance: The corrected slope distance.
        ppm: The correction applied, in parts per million. Reported because it
            is the number a surveyor recognises and can sanity-check against
            the instrument's own display.
        refractive_index: The actual index computed from the conditions.
        reference_index: The index the instrument assumed.
        applied: False when the instrument had already applied it, in which
            case ``distance`` is the input unchanged. See the applied-once rule
            in :mod:`geocomp.core.instruments.profiles`.
    """

    distance: Quantity
    ppm: Quantity
    refractive_index: Quantity
    reference_index: float
    applied: bool = True


def saturation_vapour_pressure(temperature: Quantity) -> Quantity:
    """Saturation water-vapour pressure over liquid water, in pascals.

    The Magnus-Tetens form recommended by the WMO:

        e_s = 611.2 * exp(17.62 * t / (243.12 + t))

    with *t* in degrees Celsius. Good to about 0.1 percent between -40 and
    +50 degrees, which is far better than the humidity readings it will be
    multiplied by.
    """
    if temperature.unit is not Unit.KELVIN:
        raise ValidationError(
            "temperature_wrong_unit",
            received=temperature.unit.name,
            expected=Unit.KELVIN.name,
        )
    value, derivative = _saturation(temperature.value)
    return Quantity(
        value=value,
        variance=derivative**2 * temperature.variance,
        unit=Unit.PASCAL,
        mode=temperature.mode,
        strategies=temperature.strategies,
    )


def _saturation(temperature_k: float) -> tuple[float, float]:
    """Saturation vapour pressure and its derivative with respect to *T*.

    Returned together because :func:`refractive_index` needs the derivative for
    its Jacobian, and recovering it from the propagated variance would divide by
    zero for an exactly-known temperature.
    """
    celsius = temperature_k - STANDARD_TEMPERATURE_K
    denominator = 243.12 + celsius
    value = 611.2 * math.exp(17.62 * celsius / denominator)
    # d(e_s)/dt = e_s * 17.62 * 243.12 / (243.12 + t)^2, and dt/dT = 1.
    return value, value * 17.62 * 243.12 / denominator**2


def group_refractivity(wavelength_um: float) -> float:
    """(n_g - 1) * 1e6 for standard air, by the IUGG 1960 formula.

        N_g = 287.6155 + 4.88660 / lambda^2 + 0.06800 / lambda^4

    Dimensionless and exact for its inputs, so a plain float: it is a property
    of the formula and the carrier wavelength, not a measurement.
    """
    if wavelength_um <= 0.0:
        raise ValidationError(
            "non_positive_wavelength",
            received=wavelength_um,
            expected="a positive carrier wavelength in micrometres",
        )
    squared = wavelength_um**2
    return 287.6155 + 4.88660 / squared + 0.06800 / squared**2


def refractive_index(atmosphere: Atmosphere) -> Quantity:
    """The refractive index of the measured air, with propagated uncertainty.

        N = N_g * (273.15 / 101325) * (p / T) - 11.27 * e / T

    with *N* = (n - 1) * 1e6, *p* and *e* in pascals and *T* in kelvin.

    The three inputs are independent -- a thermometer, a barometer and a
    hygrometer -- but *e* depends on *T* through the saturation pressure, so
    the temperature enters twice and its two paths are correlated. That is
    handled by building the covariance over (T, p, RH) and propagating with the
    full Jacobian rather than by adding variances, which would double-count.
    """
    temperature = atmosphere.temperature
    pressure = atmosphere.pressure
    humidity = atmosphere.humidity

    n_g = group_refractivity(atmosphere.wavelength_um)
    dry_coefficient = n_g * STANDARD_TEMPERATURE_K / STANDARD_PRESSURE_PA

    t = temperature.value
    p = pressure.value
    rh = humidity.value

    e_s, de_s_dt = _saturation(t)
    e = rh * e_s

    value = dry_coefficient * p / t - WATER_VAPOUR_COEFFICIENT * e / t

    # dN/dT: the dry term falls as 1/T, and the wet term both falls as 1/T and
    # grows through e_s(T). Both are kept.
    d_dt = -dry_coefficient * p / t**2 + WATER_VAPOUR_COEFFICIENT * e / t**2 - (
        WATER_VAPOUR_COEFFICIENT * rh * de_s_dt / t
    )
    d_dp = dry_coefficient / t
    d_drh = -WATER_VAPOUR_COEFFICIENT * e_s / t

    covariance = Covariance.diagonal(
        {
            "temperature": temperature.variance,
            "pressure": pressure.variance,
            "humidity": humidity.variance,
        },
        {"temperature": Unit.KELVIN, "pressure": Unit.PASCAL, "humidity": Unit.DIMENSIONLESS},
        mode=_worst_mode(temperature, pressure, humidity),
        strategies=temperature.strategies | pressure.strategies | humidity.strategies,
    )
    propagated = covariance.transform(
        np.array([[d_dt, d_dp, d_drh]]), ["refractivity"], [Unit.DIMENSIONLESS]
    )

    return Quantity(
        value=1.0 + value * 1e-6,
        variance=propagated.matrix[0, 0] * 1e-12,
        unit=Unit.DIMENSIONLESS,
        mode=propagated.mode,
        strategies=propagated.strategies,
    )


def apply_atmospheric_correction(
    distance: Quantity,
    atmosphere: Atmosphere,
    instrument: InstrumentProfile,
) -> AtmosphericCorrection:
    """Correct a slope distance for the air it was measured through.

    Honours the applied-once rule: when the instrument applied the correction
    itself, this returns the distance unchanged with ``applied=False`` rather
    than applying it a second time.
    """
    actual = refractive_index(atmosphere)
    reference = _reference_index(instrument, atmosphere.wavelength_um)

    ratio = reference / actual.value
    ppm_value = (ratio - 1.0) * 1e6
    # d(ppm)/d(n_actual) = -1e6 * n_ref / n_actual^2
    d_ppm = -1e6 * reference / actual.value**2
    ppm = Quantity(
        value=ppm_value,
        variance=d_ppm**2 * actual.variance,
        unit=Unit.DIMENSIONLESS,
        mode=actual.mode,
        strategies=actual.strategies,
    )

    if instrument.applies_atmospheric:
        return AtmosphericCorrection(
            distance=distance,
            ppm=ppm,
            refractive_index=actual,
            reference_index=reference,
            applied=False,
        )

    scale = Quantity(
        value=ratio,
        variance=(reference / actual.value**2) ** 2 * actual.variance,
        unit=Unit.DIMENSIONLESS,
        mode=actual.mode,
        strategies=actual.strategies,
    )
    return AtmosphericCorrection(
        distance=distance * scale,
        ppm=ppm,
        refractive_index=actual,
        reference_index=reference,
        applied=True,
    )


def _reference_index(instrument: InstrumentProfile, wavelength_um: float) -> float:
    """The refractive index the instrument's zero-ppm setting corresponds to.

    Taken from the profile when it states one, because that is the value the
    manufacturer published for that instrument. Otherwise computed from the
    model's reference conditions, so that the two paths are the same physics.
    """
    if instrument.reference_refractive_index:
        return instrument.reference_refractive_index

    celsius, pressure_hpa, relative = _REFERENCE_CONDITIONS[instrument.atmospheric_model]
    reference = Atmosphere(
        temperature=Quantity.exact(celsius_to_kelvin(celsius), Unit.KELVIN),
        pressure=Quantity.exact(pressure_hpa * 100.0, Unit.PASCAL),
        humidity=Quantity.exact(relative, Unit.DIMENSIONLESS),
        wavelength_um=wavelength_um,
    )
    return refractive_index(reference).value


def _worst_mode(*quantities: Quantity) -> UncertaintyMode:
    """APPROXIMATE if any input is: specs/05 section 2.3 gives no partial credit."""
    if any(q.mode is UncertaintyMode.APPROXIMATE for q in quantities):
        return UncertaintyMode.APPROXIMATE
    return UncertaintyMode.RIGOROUS
