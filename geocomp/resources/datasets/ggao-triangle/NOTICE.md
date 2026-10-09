<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Where this data comes from, and on what terms

**Source.** NOAA Continuously Operating Reference Stations (CORS) Network (NCN), operated by NOAA's National
Geodetic Survey (NGS). The observations of GODN, GODE and GODS were supplied by NASA Goddard Space Flight Center.
The files are NOAA's for 1 January 2025 (day 001), from the NOAA Open Data Dissemination archive:
`godn0010.25d.gz`, `gode0010.25d.gz`, `gods0010.25d.gz` and `brdc0010.25n.gz`. Their SHA-256 digests are pinned
in `tests/data/rd06/source_manifest.json` in GeoComp's repository.

**Terms.** The [NODD NCN terms](https://registry.opendata.aws/noaa-ncn/) permit public use and dissemination
with attribution. Neither NOAA, NGS nor NASA endorses GeoComp or this tutorial.

**What was changed.** The navigation file is NOAA's, unchanged. Each observation file is NOAA's daily file,
decompressed from Hatanaka form and changed in two ways:

- **cut to one hour of GPS time**, 00:00 to 01:00 in `hour-00` and 11:00 to 12:00 in `hour-11`: every epoch
  record inside the hour is copied unmodified, and the header's first and last observation times are set to
  the epochs kept;
- **reduced to GPS and the observables C1, P1, L1, S1, C2, P2, L2 and S2**: every kept value is copied
  unchanged, and the header lists the kept observables.

Each file's header says both in its comments. `scripts/make_ggao_triangle.py` makes the files from NOAA's,
and GeoComp's tests hold these to what it makes, byte for byte.
