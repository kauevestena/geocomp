# SPDX-License-Identifier: GPL-2.0-or-later
"""A Scintrex CG-5 export built from the format's header and column layout.

The real survey the reader is checked against in full cannot be redistributed
(``tests/data/rd07/PROVENANCE.md``), so tier 2 and tier 3 both use this: five
readings at three stations on one morning, numbers of the tests' own.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from geocomp.core.techniques.gravimetry import tidal_correction

MGAL = 1e-5
LAT, LON = -25.45, -49.23


def cg5_export(*, gmt_diff: float = 0.0, tide: str = "YES", utc_is_local_minus: float | None = None) -> str:
    """A CG-5 export of five readings at three stations on one morning.

    The TIDE column is Longman's at the instant ``local - utc_is_local_minus``
    hours, which is how the test decides which convention the file "uses"."""
    header = f"""/	CG-5 SURVEY
/	Survey name:   	test
/	Instrument S/N:	40123
/	Operator:      	geocomp
/	LONG:        	{abs(LON):.7f} W
/	LAT:         	{abs(LAT):.7f} S
/	GMT DIFF.:   	{gmt_diff}
/	CG-5 OPTIONS
/	Tide Correction:    {tide}
Line	   0.000S
"""
    lines = []
    base = datetime(2026, 3, 10, 9, 0, 0)
    for k, (station, grav) in enumerate(
        ((1, 3021.123), (2, 3021.456), (3, 3020.998), (2, 3021.459), (1, 3021.130))
    ):
        local = base + timedelta(minutes=20 * k)
        value = 0.0
        if utc_is_local_minus is not None:
            instant = (local - timedelta(hours=utc_is_local_minus)).replace(tzinfo=UTC)
            value = tidal_correction(instant, math.radians(LAT), math.radians(LON), 900.0).value / MGAL
        lines.append(
            f" 1.0000000   {station}.0000000  900.0000   {grav:.3f} 0.020    0.2    1.7 -2.33 "
            f"{value:.3f}  60   0 {local:%H:%M:%S}     41500.24753    0.0000  {local:%Y/%m/%d}"
        )
    return header + "\n".join(lines) + "\n"
