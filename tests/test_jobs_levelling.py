# SPDX-License-Identifier: GPL-2.0-or-later
"""The typed levelling field book (ROADMAP P14c; FR-012, FR-013).

**Typed equals imported.** RD-04's books typed into the grid are read by the
importer's own reader exactly as the same books written as CSV, the layout the
toolbox tests write them in. And the number typed reaches the reader as typed:
a sight distance's precision is taken from its digits when nothing else gives
one, so ``32.4`` re-printed as ``32.400000000000006`` would be a different book.
"""

from __future__ import annotations

import json

import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.instruments.stochastic import STAFF_READING, StochasticDefaults
from geocomp.io.levelbook import LevelMapping, read_level_book
from geocomp.io.mapping import ColumnMapping
from geocomp.jobs import levelling as lv
from geocomp.jobs.chains import InputFile, Ref, resolve
from tests import reference_levelling as rd


def csv_rows(books, *, with_line: bool = True) -> list[list[str]]:
    """RD-04 books as the toolbox tests write them: one row per reading."""
    rows = [["setup", "point", "kind", "reading", "distance", *(["line"] if with_line else [])]]
    for book in books:
        for setup in book.line.setups:
            sights = [("BS", setup.backsight)] + [
                ("FS" if index == 0 else "IS", sight) for index, sight in enumerate(setup.foresights)
            ]
            for kind, sight in sights:
                rows.append(
                    [
                        setup.id,
                        sight.station,
                        kind,
                        f"{sight.reading.value:.5f}",
                        f"{sight.distance_value:.2f}",
                        *([book.line.id] if with_line else []),
                    ]
                )
    return rows


CSV_MAPPING = LevelMapping(
    name="tier1",
    columns=(
        ColumnMapping(field="setup", column="setup"),
        ColumnMapping(field="station", column="point"),
        ColumnMapping(field="sight", column="kind"),
        ColumnMapping(field="reading", column="reading"),
        ColumnMapping(field="distance", column="distance"),
        ColumnMapping(field="line", column="line"),
    ),
    decimal_separator=".",
)


def typed(books) -> lv.LevellingBook:
    """The same books typed into the grid: line, setup, station, sight, reading, distance."""
    book = lv.LevellingBook(lv.new_job())
    block = "\n".join(
        "\t".join([line, setup, station, kind, reading, "", "", distance])
        for setup, station, kind, reading, distance, line in csv_rows(books)[1:]
    )
    book.table.paste(0, "line", block)
    return book


class TestTypedEqualsImported:
    def test_the_balanced_line_reads_as_its_csv(self):
        books = [rd.balanced_line()]
        level = rd.profile()
        expected = read_level_book(csv_rows(books), CSV_MAPPING, level=level)
        result = typed(books).read(level=level)
        assert result.setups == expected.setups
        assert [line.id for line in result.lines] == [line.id for line in expected.lines]
        assert result.findings == expected.findings

    def test_the_loop_reads_as_its_csv_line_by_line(self):
        books, _truth = rd.loop(noise=0.0003)
        level = rd.profile()
        expected = read_level_book(csv_rows(books), CSV_MAPPING, level=level)
        result = typed(books).read(level=level)
        assert [line.id for line in result.lines] == [line.id for line in expected.lines]
        assert result.setups == expected.setups

    def test_a_number_reaches_the_reader_as_typed(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(0, "line", "L\t\tBM1\tBS\t1,23450\t\t\t32,4\nL\t\tT1\tFS\t0.98760\t\t\t32")
        rows = book.emit().rows
        assert rows[1][4:6] == ("1.23450", "32.4")
        assert rows[2][4:6] == ("0.98760", "32")
        defaults = StochasticDefaults().with_default(STAFF_READING, 0.0005)
        (setup,) = book.read(defaults=defaults).setups
        # 32.4 is known to 0.05 m, 32 to half a metre: the digits are the precision.
        assert setup.backsight.distance.std_dev == pytest.approx(0.05 / 3**0.5)
        assert setup.foresights[0].distance.std_dev == pytest.approx(0.5 / 3**0.5)


class TestHowTheBookIsRead:
    def test_a_backsight_opens_a_setup_and_the_sights_below_belong_to_it(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(
            0,
            "line",
            "\n".join(
                [
                    "L1\t\tBM1\tR\t1.5\t\t\t30",
                    "\t\tT1\tV\t1.2\t\t\t30",
                    "\tE7\tT1\tré\t1.4\t\t\t30",
                    "\t\tT2\tI\t1.3\t\t\t20",
                    "\t\tBM2\tvante\t1.1\t\t\t30",
                ]
            ),
        )
        rows = book.emit().rows
        assert [row[:4] for row in rows[1:]] == [
            ("L1", "1", "BM1", "BS"),
            ("L1", "1", "T1", "FS"),
            ("L1", "E7", "T1", "BS"),
            ("L1", "E7", "T2", "IS"),
            ("L1", "E7", "BM2", "FS"),
        ]
        assert book.setups() == {
            "1": [("BS", "BM1"), ("FS", "T1")],
            "E7": [("BS", "T1"), ("IS", "T2"), ("FS", "BM2")],
        }

    def test_one_wire_typed_makes_a_book_of_three(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(0, "line", "L\tS1\tBM1\tBS\t1.500\t1.650\t1.350\nL\tS1\tT1\tFS\t1.200")
        assert book.three_wire
        emission = book.emit()
        assert emission.rows[0][4:7] == ("upper", "middle", "lower")
        assert emission.rows[1][4:7] == ("1.650", "1.500", "1.350")
        defaults = StochasticDefaults().with_default(STAFF_READING, 0.0005)
        result = book.read(defaults=defaults)
        (refused,) = [finding for finding in result.findings if finding.code == "level_missing_value"]
        typed_finding, row = lv.as_typed(refused)
        assert (typed_finding.context["row"], row) == ("2", 1), "named as the grid numbers it"
        # ... and the setup it left without a foresight is named by its first row.
        (malformed,) = [finding for finding in result.findings if finding.code == "level_setup_malformed"]
        assert lv.as_typed(malformed)[1] == 0

    def test_a_row_without_a_reading_is_not_one(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(0, "line", "L\nL\tS1\tBM1\tBS\t1.5\n\t\t\t\t\t\t\t\tjust a note")
        assert book.reading_rows() == (1,)
        rows = book.emit().rows
        assert rows[1] == ("",) * len(rows[0]) and rows[3] == ("",) * len(rows[0])

    def test_an_empty_book_and_an_unreadable_cell_are_refused(self):
        book = lv.LevellingBook(lv.new_job())
        with pytest.raises(ValidationError) as refusal:
            book.emit()
        assert refusal.value.code == "validation.level_book_empty"
        book.table.paste(0, "line", "L\tS1\tBM1\tBX\t1.5")
        with pytest.raises(ValidationError) as refusal:
            book.emit()
        assert refusal.value.code == "validation.level_book_cells_unreadable"
        check = book.check()
        assert [problem.column for problem in check.problems] == ["sight"]

    def test_a_malformed_setup_is_named_by_the_row_it_starts_on(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(0, "line", "L\tS1\tBM1\tBS\t1.5\t\t\t30\nL\tS2\tT1\tFS\t1.2\t\t\t30")
        defaults = StochasticDefaults().with_default(STAFF_READING, 0.0005)
        check = book.check(defaults=defaults)
        malformed = [f for f in check.findings if f.code == "level_setup_malformed"]
        assert len(malformed) == 2
        assert {lv.as_typed(finding)[1] for finding in malformed} == {0, 1}

    def test_the_mapping_document_leaves_the_stadia_factor_to_the_import(self):
        book = lv.LevellingBook(lv.new_job())
        book.table.paste(0, "line", "L\tS1\tBM1\tBS\t1.5")
        payload = json.loads(book.emit().mapping_text())
        assert "stadia_factor" not in payload
        assert payload["decimal_separator"] == "."
        assert payload["sight_values"] == {"BS": "backsight", "FS": "foresight", "IS": "intermediate"}


class TestBenchmarks:
    def test_they_are_written_as_the_networks_list_each_height_as_typed(self):
        book = lv.LevellingBook(lv.new_job())
        book.benchmarks.paste(0, "name", "BM1\t100.000\nBM2\t103,750\t0,002\nBM3\t101.2\t0")
        assert book.benchmarks_text() == "BM1=100.000, BM2=103.750±0.002, BM3=101.2"

    @pytest.mark.parametrize(
        ("cells", "code"),
        [
            ("BM1", "validation.benchmark_incomplete"),
            ("BM1\t100\nBM1\t101", "validation.benchmark_repeated"),
            ("BM,1\t100", "validation.benchmark_name_unusable"),
            ("BM1\thundred", "validation.benchmarks_unreadable"),
        ],
    )
    def test_what_is_wrong_with_them_is_refused(self, cells, code):
        book = lv.LevellingBook(lv.new_job())
        book.benchmarks.paste(0, "name", cells)
        with pytest.raises(ValidationError) as refusal:
            book.known_benchmarks()
        assert refusal.value.code == code


class TestChains:
    def book(self) -> lv.LevellingBook:
        book = typed([rd.balanced_line()])
        book.benchmarks.paste(0, "name", "BM1\t100.000")
        return book

    def test_each_window_runs_the_algorithms_before_it_and_its_own(self):
        book = self.book()
        assert lv.import_chain(book).algorithms == (lv.IMPORT,)
        assert lv.equal_chain(book).algorithms == (lv.IMPORT, lv.EQUAL)
        assert lv.equidistant_chain(book).algorithms == (lv.IMPORT, lv.EQUIDISTANT)
        assert lv.extreme_chain(book).algorithms == (lv.IMPORT, lv.EXTREME)
        assert lv.closures_chain(book).algorithms == (lv.IMPORT, lv.EQUAL, lv.CLOSURES)
        assert lv.network_chain(book).algorithms == (lv.IMPORT, lv.EQUAL, lv.NETWORK)

    def test_each_step_reads_what_the_one_before_it_wrote(self, tmp_path):
        steps = {step.key: step for step in resolve(lv.network_chain(self.book()), tmp_path)}
        assert steps["equal"].parameters["SETUPS"] == str(steps["import"].outputs["OUTPUT_SETUPS"])
        assert steps["network"].parameters["REDUCTIONS"] == str(
            steps["equal"].outputs["OUTPUT_REDUCTIONS"]
        )
        assert steps["network"].parameters["BENCHMARKS"] == "BM1=100.000"
        assert (tmp_path / "import" / "book.csv").read_text(encoding="utf-8").startswith(
            "line,setup,station,sight,reading,distance,note\n"
        )

    def test_the_level_is_the_field_books_for_every_algorithm_that_takes_one(self):
        book = self.book()
        book.job.parameters(lv.WINDOW_FIELD_BOOK).update(
            {"PROFILES": "/tmp/levels.json", "LEVEL_ID": "rd04-level", "SIGMA_READING": 0.0005}
        )
        book.job.parameters(lv.WINDOW_EQUAL).update({"COLLIMATION": 1e-4, "BOOK": "/etc/passwd"})
        imported, equal = lv.equal_chain(book).steps
        assert isinstance(imported.parameters["BOOK"], InputFile), "a job cannot redirect the book"
        assert imported.parameters["SIGMA_READING"] == 0.0005
        assert equal.parameters == {
            "PROFILES": "/tmp/levels.json",
            "LEVEL_ID": "rd04-level",
            "COLLIMATION": 1e-4,
            "SETUPS": Ref("import", "OUTPUT_SETUPS"),
        }
        extreme = lv.extreme_chain(book).steps[-1]
        assert extreme.parameters["LEVEL_ID"] == "rd04-level"

    def test_a_free_network_is_given_no_benchmarks(self):
        book = self.book()
        book.job.parameters(lv.WINDOW_NETWORK)["FREE"] = True
        assert "BENCHMARKS" not in lv.network_chain(book).steps[-1].parameters
        book.benchmarks.paste(0, "name", "BM,1\t1")
        lv.network_chain(book)  # benchmarks are not read for a free network

    def test_the_fingerprint_follows_the_book_and_the_benchmarks(self):
        book = self.book()
        first = lv.network_chain(book).fingerprint()
        book.benchmarks.set_cell(0, "height", "100.001")
        second = lv.network_chain(book).fingerprint()
        book.table.set_cell(0, "distance", "30.5")
        third = lv.network_chain(book).fingerprint()
        assert len({first, second, third}) == 3


class TestJobs:
    def test_a_job_reopens_with_its_book_and_benchmarks(self, tmp_path):
        book = typed([rd.balanced_line()])
        book.benchmarks.paste(0, "name", "BM1\t100.000")
        path = book.job.save(tmp_path / "rd04")
        reopened = lv.LevellingBook(lv.load_job(path))
        assert reopened.table.to_list() == book.table.to_list()
        assert reopened.benchmarks_text() == "BM1=100.000"

    def test_the_job_of_another_technique_is_refused(self, tmp_path):
        from geocomp.jobs import total_station as ts

        path = ts.new_job().save(tmp_path / "ts")
        with pytest.raises(ValidationError) as refusal:
            lv.load_job(path)
        assert refusal.value.code == "validation.job_other_technique"
