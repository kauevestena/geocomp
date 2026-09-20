# Data attribution and reuse

NOAA Continuously Operating Reference Stations (CORS) Network (NCN), operated by
NOAA's National Geodetic Survey (NGS), accessed 17 September 2026 through the
official NOAA Open Data Dissemination (NODD) archive. Observations for GODN and
GODS were supplied by NASA Goddard Space Flight Center.

The [NODD NCN terms](https://registry.opendata.aws/noaa-ncn/) permit public use
and dissemination with attribution. The evidence bundle preserves the original compressed observation and navigation
files. This repository vendors coordinate and station-log bytes and pins download
hashes for the larger processing files. The original terms are included as `sources/ncn-license.html`.

The precise IGS final orbit and the NGS IGS20 composite antenna calibration
retain their upstream authorship and comments. The calibration is distributed
by [NGS ANTCAL](https://geodesy.noaa.gov/ANTCAL/index.xhtml); its only packaging
transformation here is lossless gzip compression. The IGS data/product terms URL and hash are retained in the manifest; see also
[NOAA/NOS's reuse policy](https://oceanservice.noaa.gov/about/faq.html). They do not imply
NOAA, NASA, NGS, IGS, or calibration contributors endorse GeoComp or this analysis.

The expected-results JSON is a transcription of the **ITRF2020 ARP** block in
the two official NGS coordinate sheets. Epoch propagation, decompressed RINEX,
engine outputs, error statistics, and this report are derived analysis, not
unaltered official NOAA products. No copyright is claimed over NOAA data.

Original validation scripts in this bundle are GPL-2.0-or-later, like GeoComp.
The separate RTKLIB checkout retains its own license; no engine binary is bundled.
