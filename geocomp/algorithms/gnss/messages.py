# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for GNSS product resolution (``specs/08`` §5 and §9, phase P10c).

Each says what failed and what to do (NFR-006), and the three download failures
are kept apart because each has a different remedy (``specs/08`` §9): a product
the archive does not have yet, a login the archive refused, and a network that
did not answer. None of them carries a credential: services are named by id and
URLs are credential-free by construction (NFR-010).

RTKLIB's own failures follow (P12c-7). Until then none had a template, and
*GNSS processing* showed "could not complete the operation
(engine.rtklib_run_failed)": the engine's message, which ``specs/08`` section 9
and FR-305 require the user to see, was on the error and never reached them.
Each run failure's template now carries it.

Importing this module registers the templates; :mod:`geocomp.algorithms.gnss`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "data.product_not_found": MessageTemplate(
        "The product %1 is not available from %2. A recent day's final orbit is "
        "published about two weeks later; allow rapid orbits in Global Settings → GNSS, "
        "add another download service, or place the file in the product directory.",
        "product",
        "services",
    ),
    "data.product_authentication_failed": MessageTemplate(
        "The archive refused the login for %1 (HTTP %2). Check the QGIS authentication "
        "configuration named for this service in the download services file.",
        "url",
        "status",
    ),
    "data.product_network_failed": MessageTemplate(
        "Could not download %1: %2. The download was retried; check the network and "
        "the proxy configured in QGIS, then run again.",
        "url",
        "reason",
    ),
    "data.product_corrupt": MessageTemplate(
        "The product %1 could not be decompressed (%2). It was not used; run again to "
        "download it afresh.",
        "product",
        "reason",
    ),
    "data.product_compression_unsupported": MessageTemplate(
        "The product %1 is compressed with Unix compress (.Z), which GeoComp does not "
        "read. Point the service at the .gz or uncompressed file.",
        "product",
    ),
    "validation.product_service_credential_in_url": MessageTemplate(
        "The download service '%1' has a user name, password or token in a URL. "
        "Credentials are never written into a URL, a setting or a log: remove it, and "
        "name a QGIS authentication configuration in the service's 'authcfg' instead.",
        "service",
    ),
    "validation.product_service_scheme": MessageTemplate(
        "The download service '%1' uses the URL scheme '%2'; use https, http or file.",
        "service",
        "received",
    ),
    "validation.product_service_malformed": MessageTemplate(
        "A download service could not be read: %1. Each needs an 'id', a 'name' and "
        "'templates' keyed like 'orbit/final'.",
        "received",
    ),
    "validation.product_service_id": MessageTemplate(
        "The download service id '%1' is empty or is the id of a service GeoComp ships. "
        "Give the service an id of its own.",
        "received",
    ),
    "validation.product_service_template_key": MessageTemplate(
        "The download service '%1' has templates for products GeoComp does not know: %2. "
        "Keys are a product and a latency, such as 'orbit/final', 'orbit/rapid' or "
        "'gps_navigation/broadcast'.",
        "service",
        "received",
    ),
    # -- RTKLIB: the run (P12c-7) -----------------------------------------------
    "engine.rtklib_run_failed": MessageTemplate(
        "%1 stopped with exit code %2. Its own message: %3. Its working files are in %4.",
        "engine",
        "exit_code",
        "message",
        "work_dir",
    ),
    "engine.rtklib_wrote_no_output": MessageTemplate(
        "%1 finished without writing a solution file. Its own message: %2. Its working "
        "files are in %3.",
        "engine",
        "message",
        "work_dir",
    ),
    "engine.rtklib_produced_no_solution": MessageTemplate(
        "%1 ran on '%2' but solved no epoch; finishing without an error does not mean it "
        "solved anything. Its own message: %3. Check that the observations, the base "
        "station's and the products cover the same time. Its working files are in %4.",
        "engine",
        "rover",
        "message",
        "work_dir",
    ),
    "computation.rtklib_relative_mode_needs_a_base": MessageTemplate(
        "The %1 mode differences two receivers, and no base station was given for '%2'. "
        "Choose the base station's observations, or an absolute mode.",
        "mode",
        "rover",
    ),
    "computation.rtklib_absolute_mode_takes_no_base": MessageTemplate(
        "The %1 mode uses one receiver, and a base station ('%2') was given. RTKLIB would "
        "ignore it, silently turning a baseline into a single-receiver solution. Remove the "
        "base, or choose a relative mode.",
        "mode",
        "base",
    ),
    "computation.rtklib_sessions_do_not_overlap": MessageTemplate(
        "The rover '%1' and the base '%2' did not observe at the same time: their sessions "
        "share no epoch. Choose a base station whose observations overlap the rover's.",
        "rover",
        "base",
    ),
    "computation.rtklib_window_is_not_timezone_aware": MessageTemplate(
        "The processing window %1 has a time without a time zone. Give both ends in UTC.",
        "window",
    ),
    "computation.rtklib_window_ends_before_it_starts": MessageTemplate(
        "The processing window ends (%2) before it starts (%1). Give a window whose end is "
        "after its start.",
        "start",
        "end",
    ),
    "computation.rtklib_window_outside_the_session": MessageTemplate(
        "The processing window %1 does not overlap the session '%2', which observed %3. Give "
        "a window inside the observations; both are in GPS time.",
        "window",
        "session",
        "observed",
    ),
    "validation.rtklib_elevation_mask_out_of_range": MessageTemplate(
        "The elevation mask must be at least 0 and less than 90 degrees; %1 was given.",
        "received",
    ),
    "validation.rtklib_output_format_unknown": MessageTemplate(
        "'%1' is not an RTKLIB output format; it writes llh, xyz, enu or nmea.",
        "received",
    ),
    "validation.rtklib_base_position_type_unknown": MessageTemplate(
        "'%1' is not a way RTKLIB can be given the base position; expected %2.",
        "received",
        "expected",
    ),
    "validation.rtklib_base_position_needs_a_matching_type": MessageTemplate(
        "Base coordinates were given with the base position type '%1'. RTKLIB uses given "
        "coordinates only with llh or xyz, and would ignore them otherwise.",
        "received",
    ),
    "validation.rtklib_profile_unknown": MessageTemplate(
        "'%1' is not a processing profile; expected %2.",
        "received",
        "expected",
    ),
    # -- RTKLIB: reading the solution it wrote ------------------------------------
    "data.pos_column_header_missing": MessageTemplate(
        "'%1' has no column header, so its columns cannot be identified. RTKLIB writes one "
        "when its output header option is on; process the session again with it on.",
        "file",
    ),
    "data.pos_format_unrecognised": MessageTemplate(
        "'%1' is not a solution format GeoComp reads: its column header is '%2'. GeoComp "
        "reads latitude/longitude/height, ECEF X/Y/Z and ENU baseline solutions.",
        "file",
        "received",
    ),
    "data.pos_record_too_short": MessageTemplate(
        "A record of '%1' has %2, where %3 were expected. The file is truncated or damaged.",
        "file",
        "received",
        "expected",
    ),
    "data.pos_epoch_time_unreadable": MessageTemplate(
        "A record of '%1' has a time GeoComp cannot read: '%2'. RTKLIB writes either a GPS "
        "week and second, or a date and time.",
        "file",
        "received",
    ),
    "data.pos_solution_status_unknown": MessageTemplate(
        "A record of '%1' has the solution status '%2'; RTKLIB writes 1 to 6 (fix, float, "
        "SBAS, DGPS, single, PPP).",
        "file",
        "received",
    ),
    "data.pos_value_not_a_number": MessageTemplate(
        "A record of '%1' has '%2' where a number belongs.",
        "file",
        "received",
    ),
    "data.pos_file_has_no_solutions": MessageTemplate(
        "'%1' contains no solution epoch. Check that the observations, the base station's "
        "and the products cover the same time.",
        "file",
    ),
    "data.pos_not_geocentric": MessageTemplate(
        "'%1' holds %2 positions, and a GNSS baseline needs ECEF X, Y and Z. Process the "
        "session again with ECEF output.",
        "file",
        "received",
    ),
    "data.pos_without_reference_position": MessageTemplate(
        "'%1' does not record its base station's position (a '% ref pos' header), so its "
        "positions cannot be turned into vectors from the base. Process the session again "
        "with the output header on.",
        "file",
    ),
    "data.pos_quantities_are_geodetic": MessageTemplate(
        "This solution is in latitude, longitude and height (%1), whose components are not "
        "all metres, so they cannot be treated as one covariance. Use an ECEF or ENU "
        "solution.",
        "received",
    ),
    # -- the RINEX folder and files a run is given (P12c-7) ---------------------
    "data.gnss_scan_not_a_directory": MessageTemplate(
        "'%1' is not a folder. Choose the folder that holds the RINEX observation and "
        "navigation files.",
        "path",
    ),
    "data.rinex_file_empty": MessageTemplate(
        "'%1' is empty: a RINEX file starts with a header.",
        "file",
    ),
    "data.rinex_header_missing": MessageTemplate(
        "'%1' is not a RINEX file: its first record is '%2', where RINEX VERSION / TYPE was "
        "expected.",
        "file",
        "received",
    ),
    "data.rinex_header_unterminated": MessageTemplate(
        "The header of '%1' never ends: there is no END OF HEADER record. The file is "
        "truncated, or is not RINEX.",
        "file",
    ),
    "data.rinex_version_malformed": MessageTemplate(
        "'%1' gives its RINEX version as '%2', which is not a version number such as 2.11 or "
        "3.04.",
        "file",
        "received",
    ),
    "data.rinex_compression_unsupported": MessageTemplate(
        "'%1' is compressed as %2, which GeoComp does not read. Decompress it first; GeoComp "
        "reads uncompressed and gzip-compressed RINEX.",
        "file",
        "compression",
    ),
    # -- baselines, loops, comparisons and reference stations (P12c-7) ---------
    "data.baseline_between_one_station": MessageTemplate(
        "The baseline '%1' starts and ends at the same station, '%2'. A baseline joins two "
        "distinct stations.",
        "baseline",
        "station",
    ),
    "data.baseline_component_count": MessageTemplate(
        "The baseline '%1' has %2 components, where three were expected.",
        "baseline",
        "received",
    ),
    "data.baseline_component_unit": MessageTemplate(
        "The %2 component of the baseline '%1' is in %3; give it in metres.",
        "baseline",
        "component",
        "received",
    ),
    "data.baseline_covariance_size": MessageTemplate(
        "The baseline '%1' has a covariance of size %2, where a 3 by 3 over its components was "
        "expected.",
        "baseline",
        "received",
    ),
    "data.antenna_offset_unit": MessageTemplate(
        "The %1 antenna offset is in %2; give it in metres.",
        "component",
        "received",
    ),
    "validation.baseline_already_local": MessageTemplate(
        "The baseline '%1' has already been rotated into local east, north and up; it is "
        "rotated once, from ECEF.",
        "baseline",
    ),
    "validation.antenna_height_already_reduced": MessageTemplate(
        "The baseline '%1' already carries its antenna-height reduction; a second would "
        "double the offset.",
        "baseline",
    ),
    "validation.antenna_reduction_needs_ecef": MessageTemplate(
        "The antenna heights of the baseline '%1' are reduced while it is ECEF, before it is "
        "rotated; it is %2.",
        "baseline",
        "received",
    ),
    "validation.antenna_height_is_slant": MessageTemplate(
        "The antenna height at %2 of the baseline '%1' is a slant height. Converting one needs "
        "the antenna's dimensions, which GeoComp has no database of yet; give the vertical "
        "height from the mark to the antenna reference point.",
        "baseline",
        "end",
    ),
    "data.baseline_cluster_empty": MessageTemplate(
        "The GNSS cluster '%1' has no baselines.",
        "cluster",
    ),
    "data.baseline_cluster_mixed_frames": MessageTemplate(
        "The GNSS cluster '%1' mixes frames (%2); every baseline of a cluster is in one frame.",
        "cluster",
        "received",
    ),
    "validation.gnss_loop_too_short": MessageTemplate(
        "A GNSS loop needs at least three stations, and %1 were given: a two-station loop "
        "retraces one baseline and closes by construction.",
        "received",
    ),
    "validation.gnss_loop_repeats_a_station": MessageTemplate(
        "The GNSS loop %1 visits a station twice, which splits it into two loops. List each "
        "station once.",
        "loop",
    ),
    "validation.gnss_loop_leg_missing": MessageTemplate(
        "No baseline joins %1 and %2, so the loop cannot be closed. Process that pair, or "
        "choose a loop of baselines that exist.",
        "base",
        "rover",
    ),
    "data.gnss_loop_leg_not_ecef": MessageTemplate(
        "The leg '%1' of a GNSS loop is in %2. A loop sums its legs, and local east, north and "
        "up differ from station to station, so every leg must be ECEF.",
        "baseline",
        "frame",
    ),
    "data.gnss_loop_mixed_antenna_reduction": MessageTemplate(
        "The GNSS loop %1 mixes baselines reduced to the marks with baselines that are not, so "
        "its misclosure would measure the antenna heights. Reduce every leg, or none.",
        "loop",
    ),
    "data.comparison_needs_two_configurations": MessageTemplate(
        "A comparison needs at least two processing configurations, and %1 were given: a "
        "configuration compared with itself says nothing.",
        "received",
    ),
    "data.comparison_reference_not_found": MessageTemplate(
        "'%1' is not one of the configurations compared; expected %2.",
        "received",
        "expected",
    ),
    "data.comparison_mixed_station_pairs": MessageTemplate(
        "The configurations compared are of different station pairs (%1). Comparing "
        "configurations needs one station pair in all of them; two different baselines "
        "measure the network instead.",
        "received",
    ),
    "data.comparison_mixed_frames": MessageTemplate(
        "The configurations compared are in different frames (%1); compare them in one frame.",
        "received",
    ),
    "data.reference_station_database_missing": MessageTemplate(
        "The reference station database '%1' does not exist. Set its location in Global "
        "Settings, under GNSS.",
        "file",
    ),
    "data.reference_station_database_unreadable": MessageTemplate(
        "The reference station database '%1' could not be read: %2.",
        "file",
        "received",
    ),
    "data.reference_station_without_id": MessageTemplate(
        "A station in the reference station database has no id; every station needs one.",
    ),
    "data.duplicate_reference_station": MessageTemplate(
        "The station '%1' appears more than once in the reference station database.",
        "station",
    ),
    "data.reference_station_without_frame": MessageTemplate(
        "The reference station '%1' does not say which reference frame its coordinates are "
        "in; a coordinate without its frame is a number, not a position. Add the frame to the "
        "reference station database.",
        "station",
    ),
    "data.reference_station_position_count": MessageTemplate(
        "The reference station '%1' has %2 coordinates, where three geocentric components "
        "were expected.",
        "station",
        "received",
    ),
    "data.reference_station_position_unit": MessageTemplate(
        "The %2 coordinate of the reference station '%1' is in %3; give it in metres.",
        "station",
        "component",
        "received",
    ),
    "data.reference_station_not_found": MessageTemplate(
        "The station '%1' is not in the reference station database; expected %2.",
        "station",
        "expected",
    ),
    "validation.reference_station_without_velocity": MessageTemplate(
        "The reference station '%1' has no published velocity, and its coordinates must be "
        "moved to another epoch. A velocity taken as zero is a decimetre-scale assumption "
        "over a decade; give the velocity in the reference station database.",
        "station",
    ),
    "validation.reference_station_frame_mismatch": MessageTemplate(
        "The reference station '%1' is published in %2, a different frame from the one this "
        "processing works in. Transform its coordinates first; GeoComp records the "
        "transformation it applies.",
        "station",
        "received",
    ),
    "data.trajectory_point_frame": MessageTemplate(
        "A trajectory point's covariance is over %1, where local east, north and up "
        "components were expected.",
        "received",
    ),
    "data.trajectory_covariance_not_local": MessageTemplate(
        "A trajectory point's covariance is over %1, where local east, north and up "
        "components were expected.",
        "received",
    ),
    # -- GNSS sessions in the project (P12c-7) ----------------------------------
    "data.gnss_session_without_id": MessageTemplate(
        "A GNSS session has no id; baselines refer to a session by it. Give every session one.",
    ),
    "data.gnss_session_ends_before_it_starts": MessageTemplate(
        "The GNSS session '%1' ends at %3, before it starts at %2. Check the session's times.",
        "session",
        "start",
        "end",
    ),
    "data.antenna_height_unit": MessageTemplate(
        "The antenna height of the GNSS session '%1' is in %2; an antenna height is a length in "
        "metres.",
        "session",
        "received",
    ),
    "data.duplicate_gnss_session": MessageTemplate(
        "The project '%2' already has a GNSS session '%1'. Give each session its own id.",
        "session",
        "project",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
