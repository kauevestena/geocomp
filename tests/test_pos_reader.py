# SPDX-License-Identifier: GPL-2.0-or-later
"""``engines/rtklib/read_pos.py`` -- the solution file, with its covariance whole.

Every fixture here was written by a real ``rnx2rtkp`` (``ver.EX 2.5.1``) from
the committed RINEX pair, one per output format. That matters more than usual:
``specs/08`` §7's **[C]** claim was about which columns these files carry, and
the answer turned out to include two traps that no amount of reading the manual
would have surfaced.

The strongest check in this file is :meth:`TestTheFormatsAgree` -- the LLH and
ENU runs are the *same solution* written in two orderings, so their covariances
must be one matrix under permutation. Getting a cross-column pairing wrong in
either format breaks that identity, and nothing else would.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError
from geocomp.engines.rtklib import PosFormat, SolutionStatus, read_pos

POS = Path(__file__).parent / "data" / "rtklib" / "pos"


@pytest.fixture(params=["llh", "llh-dms", "xyz", "enu"])
def solution(request):
    return read_pos(POS / f"{request.param}.pos")


class TestEveryFormatReads:
    def test_the_format_is_identified_from_the_column_header(self):
        assert read_pos(POS / "llh.pos").format is PosFormat.LLH
        assert read_pos(POS / "llh-dms.pos").format is PosFormat.LLH_DMS
        assert read_pos(POS / "xyz.pos").format is PosFormat.XYZ
        assert read_pos(POS / "enu.pos").format is PosFormat.ENU

    def test_the_same_run_gives_the_same_epochs_whatever_the_format(self, solution):
        assert len(solution.epochs) == 120
        assert len(solution.fixed_epochs()) == 117
        assert solution.fixed_fraction == pytest.approx(117 / 120)

    def test_the_engine_identifies_itself(self, solution):
        """FR-302: which distribution produced a result is part of the record."""
        assert solution.program == "rnx2rtkp ver.EX 2.5.1"

    def test_the_inputs_are_recorded(self, solution):
        assert len(solution.inputs) == 3
        assert any("07590920.05o" in name for name in solution.inputs)

    def test_the_observation_span_is_read(self, solution):
        assert solution.obs_start == datetime(2005, 4, 2, 0, 0, tzinfo=UTC)
        assert solution.obs_end == datetime(2005, 4, 2, 0, 59, 30, tzinfo=UTC)

    def test_the_last_epoch_is_the_static_answer(self, solution):
        """A static run writes the filter's state at every epoch; the last one
        is the converged answer. Taking the first, or averaging them, mixes a
        converging filter's early guesses into the result."""
        last = solution.last()
        assert last.time == datetime(2005, 4, 2, 0, 59, 30, tzinfo=UTC)
        assert last.status is SolutionStatus.FIXED
        assert last.is_ambiguity_fixed

    def test_the_quality_indicators_survive(self, solution):
        """``specs/08`` §7: a float solution presented without its Q is a
        misrepresentation, so Q travels with the result."""
        first = solution.epochs[0]
        assert first.status is SolutionStatus.FLOAT
        assert not first.is_ambiguity_fixed
        assert first.satellites == 7
        assert solution.last().ratio > 0.0


class TestCovariance:
    """FR-206: the cross-component terms are preserved, not reduced to three
    standard deviations."""

    def test_the_matrix_is_symmetric_and_positive_semi_definite(self, solution):
        matrix = solution.last().covariance.matrix
        np.testing.assert_allclose(matrix, matrix.T, rtol=0, atol=0)
        assert min(np.linalg.eigvalsh(matrix)) >= -1e-15

    def test_the_off_diagonals_are_not_zero(self, solution):
        """Discarding them and keeping three standard deviations is a loss that
        silently misstates every downstream statistic, and is forbidden."""
        matrix = solution.last().covariance.matrix
        assert np.count_nonzero(matrix - np.diag(np.diag(matrix))) == 6

    def test_a_negative_cross_term_stays_negative(self):
        """The defect this parser exists to avoid.

        ``sqvar()`` writes ``sign(c) * sqrt(|c|)``, so the covariance is
        ``sign(v) * v**2``. Squaring alone turns every negative correlation
        positive -- and in a levelled GNSS solution the north-up and east-up
        terms are routinely negative, so an ellipse would lean the wrong way.
        """
        covariance = read_pos(POS / "llh.pos").last().covariance
        index = {name: position for position, name in enumerate(covariance.labels)}
        assert covariance.matrix[index["e"], index["u"]] < 0.0
        assert covariance.matrix[index["n"], index["e"]] < 0.0
        assert covariance.matrix[index["n"], index["u"]] > 0.0

    def test_a_cross_term_is_the_square_of_the_printed_value(self):
        """Not the printed value itself, which would be wrong by a square."""
        solution = read_pos(POS / "llh.pos")
        last_line = [
            line for line in (POS / "llh.pos").read_text().splitlines()
            if not line.startswith("%")
        ][-1]
        printed = float(last_line.split()[11])  # sdeu, the second cross column
        covariance = solution.last().covariance
        index = {name: position for position, name in enumerate(covariance.labels)}
        assert covariance.matrix[index["e"], index["u"]] == pytest.approx(
            math.copysign(printed * printed, printed)
        )

    def test_the_labels_name_the_components_in_matrix_order(self, solution):
        """``Covariance`` requires labels precisely because a matrix silently
        reordered relative to its components is a nearly invisible defect."""
        assert solution.last().covariance.labels == solution.components
        assert set(solution.components) in ({"n", "e", "u"}, {"x", "y", "z"})

    def test_the_deviations_match_the_diagonal(self, solution):
        """Only where a component and its deviation are the same quantity.

        A geodetic epoch pairs degrees with metres and refuses; see
        ``TestQuantitiesRefuseAGeodeticEpoch``.
        """
        epoch = solution.last()
        if epoch.is_geodetic:
            pytest.skip("a geodetic epoch has no metre components to pair")
        diagonal = np.sqrt(np.diag(epoch.covariance.matrix))
        for quantity, sigma in zip(epoch.quantities(), diagonal, strict=True):
            assert quantity.std_dev == pytest.approx(float(sigma))


class TestQuantitiesRefuseAGeodeticEpoch:
    """``quantities()`` pairs each component with its own standard deviation.

    For the two geodetic formats the components are degrees of latitude and
    longitude while the deviations are metres on the ground, so the pairing
    would produce a ``Quantity`` whose value and uncertainty are different
    quantities under one unit: 35.16 degrees plus or minus 1.5 metres. Nothing
    downstream could notice. It refuses instead (phase P7c).
    """

    @pytest.mark.parametrize("name", ("llh", "llh-dms"))
    def test_a_geodetic_epoch_refuses(self, name):
        from geocomp.core.errors import DataError

        with pytest.raises(DataError) as raised:
            read_pos(POS / f"{name}.pos").last().quantities()
        assert raised.value.code == "data.pos_quantities_are_geodetic"

    @pytest.mark.parametrize("name", ("xyz", "enu"))
    def test_a_metric_epoch_does_not(self, name):
        """Guards the guard: were `is_geodetic` true for everything, the test
        above would pass while the method had simply stopped working."""
        quantities = read_pos(POS / f"{name}.pos").last().quantities()
        assert len(quantities) == 3

    def test_the_sexagesimal_position_becomes_three_numbers(self):
        """``-g`` writes seven columns, whose *last three* are the longitude's
        minutes, its seconds and the height -- a triple that looks like a
        position. ``decimal_position`` is what a caller that wants a coordinate
        uses, and it agrees with the plain format's."""
        plain = read_pos(POS / "llh.pos").last().decimal_position
        sexagesimal = read_pos(POS / "llh-dms.pos").last().decimal_position
        assert len(sexagesimal) == 3
        assert sexagesimal == pytest.approx(plain, abs=1e-6)
        assert sexagesimal != pytest.approx(
            read_pos(POS / "llh-dms.pos").last().position[-3:], abs=1e-6
        )

    def test_a_three_column_position_passes_through(self):
        epoch = read_pos(POS / "xyz.pos").last()
        assert epoch.decimal_position == epoch.position


class TestTheFormatsAgree:
    """The check that makes the per-format column mapping evidence.

    The LLH and ENU runs are one solution written in two different orderings,
    so their covariances must be one matrix under permutation. A cross-column
    paired wrongly in either format breaks the identity, and nothing else in
    this file would notice.
    """

    def test_llh_and_enu_are_the_same_matrix_permuted(self):
        llh = read_pos(POS / "llh.pos").last().covariance
        enu = read_pos(POS / "enu.pos").last().covariance
        assert llh.labels == ("n", "e", "u")
        assert enu.labels == ("e", "n", "u")

        order = [enu.labels.index(name) for name in llh.labels]
        reordered = enu.matrix[np.ix_(order, order)]
        np.testing.assert_allclose(llh.matrix, reordered, rtol=1e-12, atol=1e-18)

    def test_the_mislabelled_header_changes_nothing(self):
        """``-g`` labels the third cross column ``sdue`` while writing the same
        N-U covariance the default format calls ``sdun``. Using the format's
        meaning rather than the label is what makes these two identical."""
        plain = read_pos(POS / "llh.pos").last().covariance
        sexagesimal = read_pos(POS / "llh-dms.pos").last().covariance
        assert plain.labels == sexagesimal.labels
        np.testing.assert_allclose(plain.matrix, sexagesimal.matrix, rtol=0, atol=0)

    def test_the_column_header_really_does_disagree_between_them(self):
        """Guards the test above: if upstream fixed the label, that test would
        pass for a new reason and this one says so."""
        plain = (POS / "llh.pos").read_text()
        sexagesimal = (POS / "llh-dms.pos").read_text()
        assert "sdun(m)" in plain and "sdue(m)" not in plain
        assert "sdue(m)" in sexagesimal and "sdun(m)" not in sexagesimal

    def test_the_reference_position_agrees_across_representations(self):
        """``% ref pos`` is written in the solution's own representation, so
        with ``-g`` the line carries seven numbers rather than three. Taking the
        first three yields a latitude's degrees, minutes and seconds
        masquerading as a position."""
        plain = read_pos(POS / "llh.pos").reference_position
        sexagesimal = read_pos(POS / "llh-dms.pos").reference_position
        assert sexagesimal == pytest.approx(plain, abs=1e-6)
        assert plain[0] == pytest.approx(35.132063637)


class TestPositions:
    def test_a_geodetic_position_is_degrees_and_metres(self):
        latitude, longitude, height = read_pos(POS / "llh.pos").last().position
        assert 35.0 < latitude < 35.5
        assert 139.0 < longitude < 140.0
        assert 0.0 < height < 200.0

    def test_the_sexagesimal_format_keeps_all_seven_fields(self):
        position = read_pos(POS / "llh-dms.pos").last().position
        assert len(position) == 7
        assert position[0] == pytest.approx(35.0)

    def test_an_enu_solution_is_a_baseline_not_a_position(self):
        """Which is what makes ``-a`` the interesting format for FR-602."""
        east, north, up = read_pos(POS / "enu.pos").last().position
        assert abs(east) > 100.0 and abs(north) > 100.0
        assert abs(up) < 100.0

    def test_the_ecef_position_is_metres_from_the_geocentre(self):
        assert all(abs(value) > 1e6 for value in read_pos(POS / "xyz.pos").last().position)


class TestRefusals:
    def test_a_file_with_no_column_header_is_refused(self, tmp_path):
        """Without it there is nothing to identify the format, and guessing
        would assign columns to the wrong components."""
        path = tmp_path / "headless.pos"
        path.write_text("1316 518400.000  1.0 2.0 3.0 1 7 0.1 0.1 0.1 0 0 0 0 0\n")
        with pytest.raises(DataError) as caught:
            read_pos(path)
        assert caught.value.code == "data.pos_column_header_missing"

    def test_a_short_record_is_refused_rather_than_padded(self, tmp_path):
        path = tmp_path / "short.pos"
        header = [
            line for line in (POS / "llh.pos").read_text().splitlines()
            if line.startswith("%")
        ]
        path.write_text("\n".join([*header, "1316 518400.000  35.1 139.6 70.0  1  7"]) + "\n")
        with pytest.raises(DataError) as caught:
            read_pos(path)
        assert caught.value.code == "data.pos_record_too_short"

    def test_an_unknown_quality_flag_is_refused(self, tmp_path):
        path = tmp_path / "q.pos"
        lines = (POS / "llh.pos").read_text().splitlines()
        body = next(line for line in lines if not line.startswith("%")).split()
        body[5] = "9"
        path.write_text(
            "\n".join([*[x for x in lines if x.startswith("%")], " ".join(body)]) + "\n"
        )
        with pytest.raises(DataError) as caught:
            read_pos(path)
        assert caught.value.code == "data.pos_solution_status_unknown"

    def test_an_empty_solution_says_so_when_asked_for_its_answer(self, tmp_path):
        path = tmp_path / "empty.pos"
        path.write_text(
            "\n".join(
                line for line in (POS / "llh.pos").read_text().splitlines()
                if line.startswith("%")
            ) + "\n"
        )
        solution = read_pos(path)
        assert solution.epochs == ()
        assert solution.fixed_fraction == 0.0
        with pytest.raises(DataError) as caught:
            solution.last()
        assert caught.value.code == "data.pos_file_has_no_solutions"


class TestHeaderAnomalies:
    def test_the_known_files_report_none(self, solution):
        assert solution.header_anomalies == []

    def test_a_header_labelling_columns_differently_is_reported_not_obeyed(self, tmp_path):
        """The labels are checked against what the format means. A disagreement
        is a fact the user should see, not an instruction to follow."""
        path = tmp_path / "odd.pos"
        text = (POS / "llh.pos").read_text().replace("sdne(m)", "sdxx(m)")
        path.write_text(text)
        solution = read_pos(path)
        assert len(solution.header_anomalies) == 1
        assert "sdxx" in solution.header_anomalies[0]
        # And the covariance is unchanged: the format decided, not the label.
        np.testing.assert_allclose(
            solution.last().covariance.matrix,
            read_pos(POS / "llh.pos").last().covariance.matrix,
            rtol=0, atol=0,
        )


class TestTimeRepresentations:
    """``-t`` writes a calendar date and time where the default writes a GPS
    week and a second of week. Both are two whitespace-separated fields, which
    is what lets one parser take either."""

    def test_a_calendar_time_is_read(self):
        solution = read_pos(POS / "llh-calendar.pos")
        assert solution.format is PosFormat.LLH
        assert solution.epochs[0].time == datetime(2005, 4, 2, 0, 0, tzinfo=UTC)
        assert solution.last().time == datetime(2005, 4, 2, 0, 59, 30, tzinfo=UTC)

    def test_the_two_representations_give_the_same_instants(self):
        """Which also shows the week/second conversion is right: GPS time is
        converted on the GPS scale, with no leap-second offset applied, and the
        calendar form the engine wrote is already GPS time."""
        weeks = read_pos(POS / "llh.pos")
        calendar = read_pos(POS / "llh-calendar.pos")
        assert [epoch.time for epoch in weeks.epochs] == [
            epoch.time for epoch in calendar.epochs
        ]

    def test_the_same_solution_comes_out_either_way(self):
        np.testing.assert_allclose(
            read_pos(POS / "llh.pos").last().covariance.matrix,
            read_pos(POS / "llh-calendar.pos").last().covariance.matrix,
            rtol=0, atol=0,
        )

    def test_an_unreadable_time_is_refused(self, tmp_path):
        path = tmp_path / "bad-time.pos"
        lines = (POS / "llh-calendar.pos").read_text().splitlines()
        body = next(line for line in lines if not line.startswith("%")).split()
        body[0] = "2005/13/45"
        path.write_text(
            "\n".join([*[x for x in lines if x.startswith("%")], " ".join(body)]) + "\n"
        )
        with pytest.raises(DataError) as caught:
            read_pos(path)
        assert caught.value.code == "data.pos_epoch_time_unreadable"

    def test_a_value_that_is_not_a_number_is_refused(self, tmp_path):
        path = tmp_path / "nan.pos"
        lines = (POS / "llh.pos").read_text().splitlines()
        body = next(line for line in lines if not line.startswith("%")).split()
        body[8] = "----"
        path.write_text(
            "\n".join([*[x for x in lines if x.startswith("%")], " ".join(body)]) + "\n"
        )
        with pytest.raises(DataError) as caught:
            read_pos(path)
        assert caught.value.code == "data.pos_value_not_a_number"


class TestSerialisation:
    def test_the_summary_records_what_matters_for_provenance(self):
        payload = read_pos(POS / "llh.pos").to_dict()
        assert payload["format"] == "llh"
        assert payload["program"] == "rnx2rtkp ver.EX 2.5.1"
        assert payload["epochs"] == 120
        assert payload["fixed_epochs"] == 117
        assert payload["header_anomalies"] == []


class TestTheResolvedAntennas:
    """``specs/08`` §7.5. The engine writes back the ANTEX entry it *matched*,
    not the one it was told to use, and on a miss it writes nothing at all and
    processes on uncalibrated. That makes this header line the only evidence
    that a calibrated run was calibrated."""

    def _with_header(self, tmp_path, *lines):
        source = (POS / "xyz.pos").read_text().splitlines()
        body = [line for line in source if not line.startswith("%")]
        comments = [line for line in source if line.startswith("%")]
        path = tmp_path / "antennas.pos"
        path.write_text("\n".join([comments[0], *lines, *comments[1:], *body]) + "\n")
        return read_pos(path)

    def test_a_matched_entry_is_reported_per_position(self, tmp_path):
        solution = self._with_header(
            tmp_path,
            "% antenna1  : AOAD/M_T        JPLA  ( 0.0000  0.0000  0.0000)",
            "% antenna2  : TPSCR.G3        SCIS  ( 0.0000  0.0000  0.0000)",
        )
        assert solution.antennas == {1: "AOAD/M_T        JPLA", 2: "TPSCR.G3        SCIS"}

    def test_a_radome_is_kept_because_it_is_the_whole_distinction(self, tmp_path):
        """``searchpcv`` falls back to the antenna *without* its radome, which is
        a different calibration. Splitting the name on whitespace would turn
        ``AOAD/M_T JPLA`` into ``AOAD/M_T`` and hide exactly that."""
        solution = self._with_header(
            tmp_path, "% antenna1  : AOAD/M_T        NONE  ( 0.0000  0.0000  0.0000)"
        )
        assert solution.antennas[1] == "AOAD/M_T        NONE"

    def test_an_empty_name_means_no_calibration_was_applied(self, tmp_path):
        """The engine clears the name on an ANTEX miss and carries on. Nothing
        else in the output says so: the run succeeds and the solution is wrong
        by that antenna's phase-centre offset."""
        solution = self._with_header(
            tmp_path, "% antenna1  :                       ( 0.0000  0.0000  0.0000)"
        )
        assert solution.antennas == {1: ""}

    def test_a_run_without_antenna_lines_reports_nothing_rather_than_guessing(self):
        assert read_pos(POS / "xyz.pos").antennas == {}

    def test_it_reaches_the_provenance_record(self, tmp_path):
        solution = self._with_header(
            tmp_path, "% antenna1  : TPSCR.G3        SCIS  ( 0.0000  0.0000  0.0000)"
        )
        assert solution.to_dict()["antennas"] == {"1": "TPSCR.G3        SCIS"}
