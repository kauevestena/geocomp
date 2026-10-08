# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for what the engine manager, engine discovery and DynAdjust refuse.

Each says what happened and what to do about it (NFR-006). Until P12c-6 none of
the manager's codes had a template: nothing in the plugin installed an engine,
and a DynAdjust directory that did not exist reached the user as
"could not complete the operation (validation.engine_path_not_found)". Until
P12c-7 none of DynAdjust's did either: what GeoComp could not write for it,
a stage that failed, and an output file that did not read all reached the user
as a code -- *Adjust network (DynAdjust)* showing it with its context, the
integration algorithms without even that.

A failed stage's template carries DynAdjust's own message (FR-305), which names
the station or measurement it could not use better than GeoComp could.

Importing this module registers the templates; :mod:`geocomp.algorithms.engines`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    # -- an engine that is not there (FR-306) -----------------------------
    # RTKLIB's absence reached the GNSS algorithms' users as "could not complete
    # the operation (computation.engine_not_available)" until P12c-6.
    "computation.engine_not_available": MessageTemplate(
        "%1 is needed for %2 and was not found. Give its path in Global Settings, under Paths "
        "and engines, or put it on the system path. Everything in GeoComp that does not need "
        "it works without it.",
        "engine",
        "operation",
    ),
    "validation.engine_path_not_found": MessageTemplate(
        "The path given for %1 does not exist: '%2'. GeoComp does not fall back to another "
        "copy of the program when one is named. Correct the path in Global Settings, under "
        "Paths and engines, or clear it to use GeoComp's installation or the system path.",
        "program",
        "received",
    ),
    "validation.engine_release_not_pinned": MessageTemplate(
        "GeoComp has no verified release of %1 for this computer (%2); it has one for: %3. "
        "Install the engine yourself and give its path in Global Settings, under Paths and "
        "engines.",
        "engine",
        "platform",
        "available",
    ),
    "data.engine_download_failed": MessageTemplate(
        "The engine could not be downloaded from %1 (HTTP status %2: %3). Check the network "
        "and QGIS's proxy settings, then run the installation again.",
        "url",
        "status",
        "reason",
    ),
    "data.engine_download_produced_nothing": MessageTemplate(
        "The download of %1 from %2 produced no file. Run the installation again.",
        "engine",
        "url",
    ),
    "data.engine_archive_digest_mismatch": MessageTemplate(
        "The downloaded archive is not the one GeoComp was tested with: its SHA-256 is %1, "
        "and GeoComp expects %2. It was deleted and nothing was installed. Run the "
        "installation again; if it happens again, report it rather than working around it.",
        "received",
        "expected",
    ),
    "data.engine_archive_member_escapes": MessageTemplate(
        "The downloaded archive contains '%1', which would be written outside the "
        "installation folder. Nothing was extracted. Report this: the archive is not the "
        "one GeoComp expects.",
        "member",
    ),
    "data.engine_archive_contains_symlink": MessageTemplate(
        "The downloaded archive contains a link, '%1', where only programs were expected. "
        "Nothing was extracted. Report this: the archive is not the one GeoComp expects.",
        "member",
    ),
    "data.engine_archive_missing_programs": MessageTemplate(
        "The downloaded archive does not contain %1. The engine's release has probably "
        "changed shape, and GeoComp needs updating; meanwhile install it yourself and give "
        "its path in Global Settings.",
        "expected",
    ),
    "data.engine_archive_programs_scattered": MessageTemplate(
        "The downloaded archive puts the engine's programs in several folders (%1); GeoComp "
        "runs them from one. Install the engine yourself and give its path in Global "
        "Settings.",
        "received",
    ),
    "data.engine_installation_not_recorded": MessageTemplate(
        "%1 was installed in %2 but its record could not be written. Run the installation "
        "again.",
        "engine",
        "root",
    ),
    "validation.engine_release_digest_malformed": MessageTemplate(
        "GeoComp's record of the %1 release has a malformed SHA-256 digest ('%2'), so no "
        "download of it could be verified. This is a defect in GeoComp: please report it, "
        "and install the engine yourself meanwhile.",
        "engine",
        "received",
    ),
    # -- DynAdjust: the network GeoComp writes for it (P12c-7) -----------------
    "validation.dynadjust_job_without_stations": MessageTemplate(
        "The network '%1' has no stations, so DynAdjust has nothing to adjust. Choose a "
        "network document with its stations and observations.",
        "network",
    ),
    "validation.dynadjust_confidence_out_of_range": MessageTemplate(
        "The confidence level must be a probability strictly between 0 and 1; %1 was given. "
        "Give one such as 0.95.",
        "received",
    ),
    "validation.dynadjust_job_frame_or_epoch_missing": MessageTemplate(
        "DynAdjust needs an explicit reference frame and epoch, and this run is missing one "
        "or both. GeoComp will not guess either: a guessed frame is a datum shift hidden in "
        "the residuals. Set the reference frame and epoch in the dialog, or record them on "
        "the network.",
    ),
    "validation.dynadjust_frame_or_epoch_missing": MessageTemplate(
        "The files for DynAdjust cannot be written without an explicit reference frame and "
        "epoch, and one or both are missing. GeoComp will not guess either. Set them on the "
        "run or record them on the network.",
    ),
    "validation.dynadjust_configuration_unknown_program": MessageTemplate(
        "The DynAdjust configuration names '%1', which is not a program GeoComp runs. It may "
        "give options to: %2. Name one of those.",
        "program",
        "expected",
    ),
    "validation.dynadjust_option_reserved": MessageTemplate(
        "The DynAdjust configuration gives '%1' to %2, an option GeoComp sets itself. "
        "Change it through the algorithm's own parameter instead: GeoComp reads the output "
        "back by what that option says, and would misread it.",
        "option",
        "program",
    ),
    "data.dynadjust_configuration_unreadable": MessageTemplate(
        "The DynAdjust configuration '%1' could not be read as JSON: %2. Correct the JSON.",
        "path",
        "reason",
    ),
    "validation.dynadjust_configuration_invalid": MessageTemplate(
        "The DynAdjust configuration '%1' is not a list of options per program. Write it "
        'as {"dnaadjust": ["--option", "value"]}.',
        "path",
    ),
    "data.dynadjust_prepared_manifest_missing": MessageTemplate(
        "'%1' holds no job GeoComp prepared. Run Adjust network (DynAdjust) with "
        "'Stop after writing the input' first, and give the folder it wrote.",
        "work_dir",
    ),
    "data.dynadjust_prepared_manifest_unreadable": MessageTemplate(
        "The prepared job in '%1' could not be read: %2. It is the file GeoComp wrote "
        "beside the input; prepare the job again rather than editing it.",
        "path",
        "reason",
    ),
    "data.dynadjust_prepared_measurements_changed": MessageTemplate(
        "The prepared measurement file '%1' now holds %2 measurements where GeoComp wrote %3. "
        "The result is matched to the network measurement by measurement, so measurements "
        "cannot be added or removed: set a measurement's Ignore to * to leave it out.",
        "path",
        "found",
        "written",
    ),
    "data.dynadjust_prepared_directions_changed": MessageTemplate(
        "A direction set in the prepared measurement file '%1' now holds %2 directions after "
        "its reference where GeoComp wrote %3 (the set whose reference is observation %4). "
        "Directions cannot be added or removed: set a direction's Ignore to * to leave it "
        "out.",
        "path",
        "found",
        "written",
        "observation",
    ),
    "data.dynadjust_prepared_file_missing": MessageTemplate(
        "The prepared input file '%1' is no longer in '%2'. Edit the input files in place; "
        "do not rename or remove them.",
        "path",
        "work_dir",
    ),
    "validation.dynadjust_geoid_grid_required": MessageTemplate(
        "The network '%1' has orthometric heights, and DynAdjust cannot relate them to "
        "ellipsoidal heights without a geoid model. Give a geoid grid (NTv2), or, for a network "
        "in a projected CRS, the geoid undulation N.",
        "network",
    ),
    "validation.dynadjust_network_would_be_partial": MessageTemplate(
        "%1 of the %2 observations in '%3' have no DynAdjust equivalent (%4). Adjusting the "
        "rest would answer a different question, with a variance factor that looks healthy. "
        "Adjust this network with GeoComp's own adjustment, or remove those observations.",
        "skipped",
        "of",
        "network",
        "reasons",
    ),
    "validation.dynadjust_cannot_express_weighted_constraint": MessageTemplate(
        "Station '%1' has a weighted constraint, which DynAdjust cannot express: it holds a "
        "coordinate fixed or leaves it free, nothing between. Adjust this network with "
        "GeoComp's own adjustment, or make the constraint fixed or free.",
        "station",
    ),
    "validation.dynadjust_cannot_write_projected_coordinates": MessageTemplate(
        "Station '%1' is in %2, a projected CRS GeoComp cannot carry to the latitude and "
        "longitude DynAdjust needs: it inverts UTM and Transverse Mercator on GRS80, with all of "
        "a network's stations in one CRS. Give the stations geodetic or geocentric coordinates, "
        "or put the network in such a CRS.",
        "station",
        "crs",
    ),
    "validation.dynadjust_orthometric_height_needs_a_geoid_model": MessageTemplate(
        "Station '%1' has an orthometric height, and DynAdjust needs a height above the "
        "ellipsoid. Give a geoid grid (NTv2) in the dialog, or a geoid undulation for this "
        "station.",
        "station",
    ),
    "validation.dynadjust_cluster_covariance_shape": MessageTemplate(
        "The GNSS cluster '%1' has a covariance matrix of shape %2, where %3 by %3 was expected "
        "for its %4 three-component members, so it cannot be written for DynAdjust. Check the "
        "file the cluster was imported from.",
        "cluster",
        "received",
        "size",
        "members",
    ),
    "validation.gnss_baseline_not_geocentric": MessageTemplate(
        "The GNSS baseline '%1' is recorded as %2, and DynAdjust's baselines are geocentric "
        "(ECEF) vectors: written as it is, it would be read back as something else. Import "
        "the baselines as ECEF X, Y and Z components.",
        "observation",
        "received",
    ),
    "validation.combination_not_for_dynadjust": MessageTemplate(
        "This combined network cannot be sent to DynAdjust (%1). Adjust it with GeoComp's "
        "own adjustment.",
        "reason",
    ),
    "validation.angle_not_finite": MessageTemplate(
        "An angle in the network is %1, which is not a number DynAdjust can be given. Check "
        "the observation it belongs to.",
        "received",
    ),
    # -- An engine's problem, for its developers (FR-955; P12c-48) ----------------
    "validation.engine_run_record_missing": MessageTemplate(
        "'%1' holds no record of an engine run. Choose the working folder a DynAdjust or "
        "RTKLIB run kept: the one its refusal names, or one the run was asked to keep. A "
        "folder kept before this version of GeoComp has no record; run it again.",
        "folder",
    ),
    # -- DynAdjust: the run ------------------------------------------------------
    "computation.dynadjust_program_not_found": MessageTemplate(
        "The DynAdjust program %1 was not found. Install DynAdjust from Project > Install an "
        "engine, or give its directory in Global Settings, under Paths and engines.",
        "program",
    ),
    "computation.dynadjust_stage_failed": MessageTemplate(
        "DynAdjust's %1 stopped with exit code %2. The command was %5, run in %4, where its "
        "working files and the input GeoComp wrote are kept; look there for the cause, or "
        "package them for DynAdjust's developers with Package an engine problem. "
        "DynAdjust's own message: %3",
        "program",
        "exit_code",
        "diagnostic",
        "work_dir",
        "command",
    ),
    "computation.dynadjust_stage_timed_out": MessageTemplate(
        "DynAdjust's %1 was stopped at its time limit of %3 s, after running for %2 s, "
        "before it finished. Raise the timeout per stage among the algorithm's advanced "
        "parameters. Its working files are kept in %4.",
        "program",
        "elapsed",
        "limit",
        "work_dir",
    ),
    "computation.dynadjust_import_incomplete": MessageTemplate(
        "dnaimport reported success but did not take in everything GeoComp wrote: it counted "
        "%1, where GeoComp wrote %2. Adjusting the rest would give a plausible answer for a "
        "different network, so the run was stopped. Check the records dnaimport's own message "
        "names: %3",
        "received",
        "expected",
        "diagnostic",
    ),
    "computation.dynadjust_output_missing": MessageTemplate(
        "dnaadjust reported success but wrote no adjustment file (%1). Run the adjustment "
        "again with the generated input and raw output kept, and look at its messages there.",
        "expected",
    ),
    # -- DynAdjust: reading what it wrote ----------------------------------------
    "data.dynadjust_unsupported_output_version": MessageTemplate(
        "'%1' was written by DynAdjust %2, whose output layout GeoComp does not read; it "
        "reads the layouts of %3. Run one of those versions.",
        "path",
        "received",
        "expected",
    ),
    "data.dynadjust_unrecognised_output_layout": MessageTemplate(
        "The %1 table in DynAdjust's output has columns GeoComp does not recognise, so it was "
        "probably written by a DynAdjust version GeoComp has not been checked against. "
        "Expected the header '%2'; found '%3'. Use the DynAdjust release GeoComp was checked "
        "against, which the Install an engine algorithm installs.",
        "table",
        "expected",
        "found",
    ),
    "data.dynadjust_unknown_station_in_output": MessageTemplate(
        "DynAdjust's output names a station that is not in the network GeoComp wrote ('%1'), "
        "so the output and the network are not from the same run. Give the output of the run "
        "prepared from this network.",
        "line",
    ),
    "data.dynadjust_station_name_fills_its_column": MessageTemplate(
        "A station name fills its whole %1-character column in DynAdjust's output, so it "
        "cannot be told apart from the next field ('%2'). Shorten the station names, or read "
        "the output together with the network it came from.",
        "width",
        "line",
    ),
    "data.dynadjust_output_column_overflowed": MessageTemplate(
        "A value for station '%1' was wider than the column DynAdjust reserved for it (%2), "
        "so the fields after it cannot be read: '%3'. A latitude and longitude precision "
        "above 6 decimals does this; run DynAdjust with the default precision.",
        "station",
        "column",
        "line",
    ),
    "data.dynadjust_output_not_a_number": MessageTemplate(
        "DynAdjust's output has '%1' where the %2 should be a number, in the line '%3'. Run "
        "the adjustment again to write the output afresh.",
        "received",
        "field",
        "line",
    ),
    "data.dynadjust_output_has_no_usable_coordinates": MessageTemplate(
        "DynAdjust's coordinate table has no position GeoComp can read: it printed %1, and "
        "none of X/Y/Z, latitude/longitude or easting/northing. Write the adjustment with "
        "one of those coordinate outputs.",
        "coordinate_types",
    ),
    "data.dynadjust_angular_format_unknown": MessageTemplate(
        "GeoComp cannot tell whether the angles in this DynAdjust output are in DDD.MMSSsss "
        "notation or decimal degrees: the file does not record the command that wrote it. "
        "Use the output of a run that records it, as GeoComp's own runs do.",
    ),
    "data.dynadjust_angular_measurement_format_unsupported": MessageTemplate(
        "This DynAdjust output writes angles in degrees, minutes and seconds with symbols "
        "(%1), which GeoComp does not read. Run DynAdjust with its default angular format.",
        "received",
    ),
    "data.dynadjust_unknown_measurement_component": MessageTemplate(
        "DynAdjust's output has a component '%1' for measurement %2 that GeoComp does not "
        "know to be angular or linear, in the line '%3'. Check that the output is from the "
        "DynAdjust release GeoComp was tested with.",
        "component",
        "measurement",
        "line",
    ),
    "data.dynadjust_output_has_no_solution": MessageTemplate(
        "'%1' records no solution: the adjustment did not reach one. DynAdjust's messages in "
        "the same folder say why. Read them, correct the input, and run it again.",
        "path",
    ),
    "data.dynadjust_cor_angle_unreadable": MessageTemplate(
        "An angle in DynAdjust's corrections file (.cor) could not be read: '%1', in the line "
        "'%2'. Run the adjustment again to write the file afresh.",
        "received",
        "line",
    ),
    "data.dynadjust_observation_has_no_code": MessageTemplate(
        "Observation '%1' is a %2, which DynAdjust has no measurement type for, so its "
        "adjusted value cannot be found in the output. Adjust the network with GeoComp's own "
        "adjustment, or leave that observation out.",
        "observation",
        "type",
    ),
    "data.dynadjust_measurement_count_mismatch": MessageTemplate(
        "DynAdjust's adjusted-measurement table has %1 rows where the network has %2 "
        "measurements, so the rows cannot be matched to the observations. The output and the "
        "network are not from the same run. Give the output of the run prepared from this "
        "network.",
        "received",
        "expected",
    ),
    "data.dynadjust_measurement_type_mismatch": MessageTemplate(
        "The adjusted measurement for observation '%1' is a %2 in DynAdjust's output, where a "
        "%3 was written: the rows are not in the order of the network. The output and the "
        "network are not from the same run. Give the output of the run prepared from this "
        "network.",
        "observation",
        "received",
        "expected",
    ),
    "data.dynadjust_measurement_station_mismatch": MessageTemplate(
        "The adjusted measurement for observation '%1' joins %2 in DynAdjust's output, where "
        "it joins %3 in the network. The output and the network are not from the same run. "
        "Give the output of the run prepared from this network.",
        "observation",
        "received",
        "expected",
    ),
    "data.dynadjust_apu_row_without_a_station": MessageTemplate(
        "A row of DynAdjust's uncertainty file (.apu) does not name a station: '%1'. The file "
        "is damaged or in a layout GeoComp does not read. Run the adjustment again to write "
        "it afresh.",
        "line",
    ),
    "data.dynadjust_apu_covariance_before_any_station": MessageTemplate(
        "DynAdjust's uncertainty file (.apu) has a covariance row before any station row: "
        "'%1'. The file is damaged or in a layout GeoComp does not read. Run the adjustment "
        "again to write it afresh.",
        "line",
    ),
    "data.dynadjust_uncertainty_for_an_unknown_station": MessageTemplate(
        "DynAdjust's uncertainty file (.apu) names stations its adjustment file (.adj) does "
        "not: %1. The two files are not from the same run. Give the .adj and .apu files of "
        "one run.",
        "stations",
    ),
    "data.dynadjust_covariance_for_an_unknown_station": MessageTemplate(
        "DynAdjust's uncertainty file (.apu) gives a covariance between '%1' and '%2', and "
        "the adjustment does not have both. The two files are not from the same run. Give the "
        ".adj and .apu files of one run.",
        "station",
        "other",
    ),
    "data.dynadjust_output_without_an_epoch": MessageTemplate(
        "'%1' records no epoch, and GeoComp will not assume one: a solution without an epoch "
        "cannot be compared or transformed. Run the adjustment with an explicit epoch.",
        "path",
    ),
    "data.dynadjust_output_versions_disagree": MessageTemplate(
        "The adjustment file was written by DynAdjust %1 and the uncertainty file by "
        "DynAdjust %2, so they are not from the same run. Give the files one run wrote.",
        "adj",
        "apu",
    ),
    "validation.hp_angle_empty": MessageTemplate(
        "An angle in DynAdjust's output is empty where a value in DDD.MMSSsss notation was "
        "expected. Run the adjustment again to write the output afresh.",
    ),
    "validation.hp_angle_malformed": MessageTemplate(
        "'%1' is not an angle in DynAdjust's DDD.MMSSsss notation. Give it as DDD.MMSSsss, "
        "for example 123.4530 for 123 degrees, 45 minutes and 30 seconds.",
        "received",
    ),
    "validation.hp_angle_minutes_out_of_range": MessageTemplate(
        "The angle '%1' has 60 or more minutes, which DDD.MMSSsss notation does not allow. "
        "Correct the minutes.",
        "received",
    ),
    "validation.hp_angle_seconds_out_of_range": MessageTemplate(
        "The angle '%1' has 60 or more seconds, which DDD.MMSSsss notation does not allow. "
        "Correct the seconds.",
        "received",
    ),
    "validation.epoch_malformed": MessageTemplate(
        "'%1' is not a date in DynAdjust's dd.mm.yyyy form. Give it as, for example, "
        "01.01.2020.",
        "received",
    ),
    "validation.epoch_out_of_range": MessageTemplate(
        "'%1' is not a real date (dd.mm.yyyy). Correct the day or the month.",
        "received",
    ),
    # -- DynaML and DNA files read back ------------------------------------------
    "data.dynaml_unreadable": MessageTemplate(
        "'%1' could not be read as a DynaML (DynAdjust XML) file: %2. Check that the file is "
        "complete.",
        "path",
        "reason",
    ),
    "data.dynaml_wrong_root": MessageTemplate(
        "'%1' is not a DynaML file: its root element is '%2', where DnaXmlFormat was "
        "expected. Choose a DynaML file.",
        "path",
        "received",
    ),
    "data.dynaml_wrong_file_type": MessageTemplate(
        "'%1' is a DynaML file of type '%2', where a %3 or a Combined File was expected. "
        "Choose a file of that type.",
        "path",
        "received",
        "wanted",
    ),
    "data.dynaml_station_without_coordinates": MessageTemplate(
        "A station in the DynaML file has no coordinates (no StationCoord element); every "
        "station needs them. Add the station's StationCoord element, or export the file "
        "again.",
    ),
    "data.dynaml_unknown_coordinate_type": MessageTemplate(
        "Station '%1' in the DynaML file has the coordinate type '%2', which GeoComp does not "
        "read; it reads %3. Export the stations in one of those types.",
        "station",
        "received",
        "expected",
    ),
    "data.dynaml_directional_variance_scale_unsupported": MessageTemplate(
        "Measurement %1 scales its variances (%2), which GeoComp cannot represent: only a "
        "scale of 1 can be read. Remove the scaling, or scale the standard deviations "
        "themselves.",
        "measurement",
        "received",
    ),
    "data.dynaml_setup_height_on_an_unaffected_type": MessageTemplate(
        "Measurement %1 is a %2 with a %3 of %4, but a height offset does not change this "
        "kind of measurement. Remove the offset, or check the measurement type.",
        "measurement",
        "type",
        "field",
        "received",
    ),
    "data.dna_unreadable": MessageTemplate(
        "'%1' could not be read as a DynAdjust DNA file: %2. Check that the file is complete.",
        "path",
        "reason",
    ),
    "data.dna_header_missing": MessageTemplate(
        "'%1' is not a DynAdjust DNA file: its first line does not begin with !#=DNA. Choose "
        "the DNA file DynAdjust or GeoComp wrote.",
        "path",
    ),
    "data.dna_directional_variance_scale_unsupported": MessageTemplate(
        "Measurement %1 scales its variances (%2), which GeoComp cannot represent: only a "
        "scale of 1 can be read. Remove the scaling, or scale the standard deviations "
        "themselves.",
        "measurement",
        "received",
    ),
    "data.dna_setup_height_on_an_unaffected_type": MessageTemplate(
        "Measurement %1 is a %2 with a %3 of %4, but a height offset does not change this "
        "kind of measurement. Remove the offset, or check the measurement type.",
        "measurement",
        "type",
        "field",
        "received",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
