# SPDX-License-Identifier: GPL-2.0-or-later
"""The ``rnx2rtkp`` adapter: the configuration, the job, and the run.

Most of this is tier 1 -- the configuration writer and the job's preconditions
need no engine. The tier-4 class at the end is what only a real ``rnx2rtkp``
can show, and it is where the two defects recorded in ``specs/08`` §2.1 came
from: a configuration file silently relocating the base station, and relative
input paths resolving against the wrong directory.
"""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import ComputationError, ValidationError
from geocomp.engines.base import EngineAbsentError
from geocomp.engines.rtklib import (
    PROFILES,
    RtklibConfig,
    RtklibEngine,
    RtklibJob,
    command_line,
    parse_config,
    parse_version,
    profile,
    program_filenames,
    write_config,
)
from geocomp.io.gnss_discovery import overlapping_groups, scan_folder
from tests.conftest import requires_rtklib

DATA = Path(__file__).parent / "data" / "rtklib"


@pytest.fixture
def sessions():
    scan = scan_folder(DATA)
    pair = next(group for group in overlapping_groups(scan.sessions) if len(group) == 2)
    base, rover = sorted(pair, key=lambda session: session.station_id)
    return base, rover


class TestVersion:
    def test_the_fork_is_named_because_the_two_can_differ(self):
        """FR-302 asks which distribution produced a result, and the forks'
        behaviour can differ at the same nominal version."""
        version = parse_version("rnx2rtkp RTKLIB EX 2.5.1", path=Path("/x"))
        assert version.name == "RTKLIB-EX"
        assert version.version == "2.5.1"
        assert version.tested

    def test_takasus_original_prints_no_distribution_word(self):
        version = parse_version("rnx2rtkp RTKLIB 2.4.3 b34", path=Path("/x"))
        assert version.name == "RTKLIB"
        assert version.version == "2.4.3"

    def test_an_untested_version_is_a_warning_not_a_refusal(self):
        """FR-302: a user with a newer engine should be told the parsers may not
        match it, not prevented from working."""
        version = parse_version("rnx2rtkp RTKLIB EX 9.9.9", path=Path("/x"))
        assert version is not None
        assert not version.tested

    def test_output_that_is_not_a_version_banner_is_no_version(self):
        assert parse_version("error : no input file", path=Path("/x")) is None

    def test_the_raw_banner_is_kept(self):
        """Not normalised: a parser keyed on it must match what the engine said."""
        assert parse_version("rnx2rtkp RTKLIB EX 2.5.1", path=Path("/x")).raw == (
            "rnx2rtkp RTKLIB EX 2.5.1"
        )

    def test_windows_appends_an_extension(self):
        assert program_filenames() == ("rnx2rtkp", "rnx2rtkp.exe")


class TestGracefulAbsence:
    def test_an_absent_engine_is_reported_not_crashed_into(self, tmp_path, monkeypatch):
        """FR-306: GNSS processing is disabled with an explanation rather than
        failing part-way through a run."""
        monkeypatch.setenv("PATH", str(tmp_path))
        engine = RtklibEngine()
        assert not engine.available
        assert engine.version() is None

    def test_running_without_an_engine_names_what_is_missing(
        self, tmp_path, monkeypatch, sessions
    ):
        monkeypatch.setenv("PATH", str(tmp_path))
        base, rover = sessions
        with pytest.raises(EngineAbsentError):
            RtklibEngine().run(RtklibJob(rover=rover, base=base), work_dir=tmp_path)


class TestConfiguration:
    def test_every_menu_mode_has_a_profile(self):
        assert set(PROFILES) == {
            "relative-static", "relative-kinematic", "absolute-static", "absolute-kinematic",
        }

    def test_a_profile_names_itself_so_a_run_can_be_traced_to_it(self):
        assert profile("relative-static").name == "relative-static"

    def test_an_unknown_profile_lists_the_ones_there_are(self):
        with pytest.raises(ValidationError) as caught:
            profile("nonsense")
        assert "relative-static" in caught.value.context["expected"]

    def test_the_absolute_profiles_are_the_ppp_ones(self):
        """``specs/08`` §3: the FR-604 notice attaches to these, and the UI
        needs to know which they are."""
        assert profile("absolute-static").mode.is_ppp
        assert profile("absolute-kinematic").mode.is_ppp
        assert not profile("relative-static").mode.is_ppp

    def test_the_relative_modes_are_the_ones_needing_a_base(self):
        assert profile("relative-static").mode.is_relative
        assert not profile("absolute-static").mode.is_relative

    def test_writing_is_deterministic(self, tmp_path):
        """NFR-007: a run reproduced from its recorded configuration must be the
        same run, which needs the same bytes."""
        first = write_config(profile("relative-static"), tmp_path / "a.conf")
        second = write_config(profile("relative-static"), tmp_path / "b.conf")
        assert first.read_bytes() == second.read_bytes()

    def test_the_file_round_trips(self, tmp_path):
        """``specs/08`` §10 criterion 2, and what lets a user edit it in
        Advanced mode (FR-325) without GeoComp losing track of it."""
        config = profile("relative-static")
        path = write_config(config, tmp_path / "c.conf")
        assert parse_config(path.read_text()) == config.settings()

    def test_the_enumerations_are_written_as_comments(self, tmp_path):
        """A user editing the file needs them; a file written without them is
        one nobody can safely change."""
        text = write_config(profile("relative-static"), tmp_path / "c.conf").read_text()
        assert "(0:single,1:dgps,2:kinematic,3:static" in text
        assert "# profile: relative-static" in text

    def test_an_empty_value_survives_the_round_trip(self):
        """In this format an empty value is how a field separator or an
        exclusion list is set to nothing -- dropping it changes the run."""
        assert parse_config("out-fieldsep       =\n") == {"out-fieldsep": ""}

    def test_comments_and_blank_lines_are_not_settings(self):
        assert parse_config("# a comment\n\n  \npos1-elmask =15 # (deg)\n") == {
            "pos1-elmask": "15"
        }

    @pytest.mark.parametrize("mask", [-1.0, 90.0, 120.0])
    def test_an_impossible_elevation_mask_is_refused(self, mask):
        with pytest.raises(ValidationError) as caught:
            RtklibConfig(elevation_mask=mask)
        assert caught.value.code == "validation.rtklib_elevation_mask_out_of_range"

    def test_an_unknown_output_format_is_refused(self):
        with pytest.raises(ValidationError):
            RtklibConfig(output_format="kml")

    def test_unmodelled_options_pass_through(self, tmp_path):
        """FR-325: a user in Advanced mode is not limited to the options this
        dataclass happens to know about."""
        config = profile("relative-static").with_options(extra={"pos2-arlockcnt": "7"})
        assert parse_config(write_config(config, tmp_path / "c.conf").read_text())[
            "pos2-arlockcnt"
        ] == "7"


class TestTheBaseStationPosition:
    """The defect this class exists for, found by running the engine.

    Loading a configuration file resets the base-station position to the option
    table's default -- latitude 0, longitude 0, height 0 -- while the
    command-line path takes it from the base's RINEX header. So
    ``rnx2rtkp -k <config>`` and ``rnx2rtkp -p 3`` are **not** equivalent, and a
    generated configuration that omits ``ant2-postype`` puts the base station in
    the Gulf of Guinea. Measured on the sample pair: with it, 120 solutions;
    without it, none.

    ``specs/08`` §2 makes ``-k`` the primary mechanism *because it is
    reproducible*. Omitting this would have made it reproducibly wrong -- and a
    base only slightly wrong would have succeeded rather than failed.
    """

    def test_the_base_position_comes_from_the_rinex_header_by_default(self):
        assert profile("relative-static").settings()["ant2-postype"] == "rinexhead"

    def test_every_profile_states_it(self):
        for name in PROFILES:
            assert "ant2-postype" in profile(name).settings(), name

    def test_explicit_base_coordinates_are_written(self):
        config = profile("relative-static").with_options(
            base_position=(35.1320636, 139.6243004, 75.3847), base_position_type="llh"
        )
        settings = config.settings()
        assert settings["ant2-postype"] == "llh"
        assert float(settings["ant2-pos1"]) == pytest.approx(35.1320636)
        assert float(settings["ant2-pos3"]) == pytest.approx(75.3847)

    def test_coordinates_without_a_matching_type_are_refused(self):
        """``rnx2rtkp`` ignores the coordinates when the type is not llh or
        xyz, so the run would quietly use the header position instead."""
        with pytest.raises(ValidationError) as caught:
            RtklibConfig(base_position=(1.0, 2.0, 3.0), base_position_type="rinexhead")
        assert caught.value.code == "validation.rtklib_base_position_needs_a_matching_type"

    def test_an_unknown_position_type_is_refused(self):
        with pytest.raises(ValidationError):
            RtklibConfig(base_position_type="somewhere")


class TestJobPreconditions:
    def test_a_relative_mode_needs_a_base(self, sessions):
        _, rover = sessions
        with pytest.raises(ComputationError) as caught:
            RtklibJob(rover=rover, base=None, config=profile("relative-static"))
        assert caught.value.code == "computation.rtklib_relative_mode_needs_a_base"

    def test_an_absolute_mode_refuses_one(self, sessions):
        """``rnx2rtkp`` ignores a base in PPP rather than refusing it, so a user
        who thought they were processing a baseline would get a PPP solution
        labelled as one."""
        base, rover = sessions
        with pytest.raises(ComputationError) as caught:
            RtklibJob(rover=rover, base=base, config=profile("absolute-static"))
        assert caught.value.code == "computation.rtklib_absolute_mode_takes_no_base"

    def test_sessions_that_never_observed_together_are_refused(self, sessions):
        base, rover = sessions
        elsewhere = replace(
            base,
            id="elsewhere",
            start=base.end,
            end=base.end.replace(hour=23),
        )
        with pytest.raises(ComputationError) as caught:
            RtklibJob(rover=rover, base=elsewhere)
        assert caught.value.code == "computation.rtklib_sessions_do_not_overlap"

    def test_the_rover_is_named_first(self, sessions):
        """The order is the interface, not a convention: reversing it computes
        the baseline backwards while reporting success."""
        base, rover = sessions
        files = RtklibJob(rover=rover, base=base).input_files()
        assert Path(files[0]).name == Path(rover.obs_file).name
        assert Path(files[1]).name == Path(base.obs_file).name

    def test_navigation_files_follow_and_are_not_repeated(self, sessions):
        base, rover = sessions
        files = RtklibJob(rover=rover, base=base).input_files()
        assert len(files) == len(set(files))
        assert any(name.endswith(".gz") for name in files)

    def test_supplied_products_are_passed_to_the_engine(self, sessions):
        """GeoComp does not download them in this phase; a caller that has them
        on disk can still use them."""
        base, rover = sessions
        job = RtklibJob(rover=rover, base=base, products=("igs15904.sp3",))
        assert job.input_files()[-1] == "igs15904.sp3"


class TestCommandLine:
    def test_the_configuration_is_the_mechanism(self, sessions, tmp_path):
        """``specs/08`` §2: only the inputs, the output and the config file are
        flags. Everything else is in the file the user can read."""
        base, rover = sessions
        command = command_line(
            Path("/usr/bin/rnx2rtkp"),
            RtklibJob(rover=rover, base=base),
            config_file=tmp_path / "c.conf",
            output_file=tmp_path / "out.pos",
        )
        assert command[1] == "-k"
        assert command[3] == "-o"
        assert [part for part in command if part.startswith("-")] == ["-k", "-o"]

    def test_every_path_is_absolute(self, sessions, tmp_path):
        """The process runs in the working directory, not the caller's, so a
        relative path that was right at discovery resolves to nothing by the
        time the engine opens it -- and ``rnx2rtkp`` calls that
        ``error : no obs data``, which sounds like a problem with the
        observations rather than with where they were looked for."""
        base, rover = sessions
        command = command_line(
            Path("/usr/bin/rnx2rtkp"),
            RtklibJob(rover=rover, base=base),
            config_file=tmp_path / "c.conf",
            output_file=tmp_path / "out.pos",
        )
        for part in command[1:]:
            if not part.startswith("-"):
                assert Path(part).is_absolute(), part


@requires_rtklib
class TestAgainstTheRealEngine:
    """Tier 4: the chain from a folder of RINEX to a fixed solution.

    The data is RTKLIB's own 2005 GSI pair, so this shows the pipeline runs and
    resolves ambiguities. It does **not** show the coordinates are right: these
    stations have no published official coordinates reachable from this project.
    That is RD-06, and ``specs/22`` §5 records why it is not here.
    """

    def test_the_engine_reports_itself(self):
        version = RtklibEngine().version()
        assert version is not None
        assert version.name.startswith("RTKLIB")
        assert version.source

    def test_a_folder_of_rinex_becomes_a_fixed_baseline(self, sessions):
        base, rover = sessions
        with tempfile.TemporaryDirectory() as work:
            result = RtklibEngine().run(
                RtklibJob(rover=rover, base=base, config=profile("relative-static")),
                work_dir=work,
            )
            assert result.ok
            assert result.run.exit_code == 0
            solution = result.solution
            assert len(solution.epochs) == 120
            assert solution.fixed_fraction > 0.9
            assert solution.last().is_ambiguity_fixed

    def test_the_covariance_survives_the_whole_chain(self, sessions):
        """FR-206 end to end: the cross-component terms reach a ``Covariance``
        from a live run, not only from a committed fixture."""
        base, rover = sessions
        with tempfile.TemporaryDirectory() as work:
            result = RtklibEngine().run(RtklibJob(rover=rover, base=base), work_dir=work)
            covariance = result.solution.last().covariance
            assert covariance.labels == ("n", "e", "u")
            off_diagonal = covariance.matrix - np.diag(np.diag(covariance.matrix))
            assert np.count_nonzero(off_diagonal) == 6
            assert max(np.sqrt(np.diag(covariance.matrix))) < 0.05

    def test_the_configuration_used_is_kept_beside_the_run(self, sessions):
        """FR-036, FR-955: the working directory is retained so a user can
        reproduce the invocation or attach it to a bug report."""
        base, rover = sessions
        with tempfile.TemporaryDirectory() as work:
            result = RtklibEngine().run(RtklibJob(rover=rover, base=base), work_dir=work)
            assert result.config_file.is_file()
            assert "pos1-posmode" in result.config_file.read_text()
            assert result.run.work_dir == Path(work)

    def test_the_written_configuration_is_what_the_engine_read(self, sessions):
        """The round trip that matters: the file GeoComp wrote, fed back through
        ``-k``, is the run that happened."""
        base, rover = sessions
        with tempfile.TemporaryDirectory() as work:
            result = RtklibEngine().run(RtklibJob(rover=rover, base=base), work_dir=work)
            written = parse_config(result.config_file.read_text())
            assert written["pos1-posmode"] == "static"
            assert written["ant2-postype"] == "rinexhead"

    def test_a_run_that_solves_nothing_is_not_a_success(self, sessions, tmp_path):
        """A run can exit zero having solved nothing. Judging success on the
        exit code would report an empty solution as a good one -- the same
        lesson ``specs/07`` §4.3 records for ``dnaimport``.

        Forced by putting the base station where it is not: the default position
        a configuration file would have used.
        """
        from geocomp.core.errors import EngineError

        base, rover = sessions
        job = RtklibJob(
            rover=rover,
            base=base,
            config=profile("relative-static").with_options(
                base_position=(0.0, 0.0, 0.0), base_position_type="llh"
            ),
        )
        with pytest.raises(EngineError) as caught:
            RtklibEngine().run(job, work_dir=tmp_path)
        assert caught.value.code in {
            "engine.rtklib_produced_no_solution",
            "engine.rtklib_wrote_no_output",
        }
        assert caught.value.context["message"]
