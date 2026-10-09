# SPDX-License-Identifier: GPL-2.0-or-later
"""USGS's synthetic gravity surveys for GSadjust: their published truth, and the gravimetry tutorial.

The surveys are vendored verbatim in ``tests/data/rd07/gsadjust/`` (CC0;
``PROVENANCE.md`` there), and two of them ship as the gravimetry tutorial
(P13-4). What is known about them is what USGS published beside them in
``GSadjust_TestData.xlsx``: five stations at 50, 48, 45, 48.5 and 46 mGal, a
drift, a calibration per meter and a 3 microgal noise.
``tests/test_gravimetry_network.py`` checks this transcription against the
workbook.
"""

from __future__ import annotations

from pathlib import Path

from geocomp.core.instruments import GravimeterProfile, ProfileLibrary
from geocomp.core.uncertainty import Quantity

DATA = Path(__file__).parent / "data" / "rd07" / "gsadjust"

#: GSadjust_TestData.xlsx, the "True" data table of every sheet, mGal.
TRUTH = {"sta1": 50.0, "sta2": 48.0, "sta3": 45.0, "sta4": 48.5, "sta5": 46.0}
#: Each sheet's stated drift (mGal/h) and calibration per meter. The readings
#: are the calibration times the truth, so the factor that recovers the truth
#: is its reciprocal. Test 5's drift is a piecewise function, not a rate.
CASES = {
    "Test1": {"drift_mgal_h": 0.0, "calibration": {"B44": 1.0}},
    "Test2": {"drift_mgal_h": 0.01, "calibration": {"B44": 1.0}},
    "Test3": {"drift_mgal_h": 0.01, "calibration": {"B44": 1.03}},
    "Test4": {"drift_mgal_h": 0.01, "calibration": {"B44": 1.1, "B108": 1.05}},
    "Test5": {"drift_mgal_h": None, "calibration": {"B44": 1.003}},
}
#: "Station standard deviation, mGal" on every sheet.
SIGMA_MGAL = 0.003

#: The surveys the tutorial ships: a clean one, and one whose meter reads 3 % high.
TUTORIAL_SURVEYS = ("Test2", "Test3")


def tutorial_profiles(*, calibrated: bool) -> ProfileLibrary:
    """Meter B44 as the tutorial describes it: 3 microgal a reading, tide already removed.

    *calibrated* gives it the factor that undoes Test 3's stated calibration,
    1/1.03; otherwise it has none, as a meter does before anyone has measured
    its scale.
    """
    factor = 1.0 / CASES["Test3"]["calibration"]["B44"] if calibrated else 1.0
    library = ProfileLibrary()
    library.add_gravimeter(
        GravimeterProfile(
            id="B44",
            name="USGS synthetic meter B44",
            calibration_factor=Quantity.exact(factor),
            sigma_reading=SIGMA_MGAL / 1e5,
            applies_tide=True,
            source=(
                "USGS GSadjust synthetic surveys; calibration from Test 3's stated 1.03"
                if calibrated
                else "USGS GSadjust synthetic surveys; scale not calibrated"
            ),
        )
    )
    return library
