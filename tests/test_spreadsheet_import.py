# SPDX-License-Identifier: GPL-2.0-or-later
"""Field books from ``.xlsx`` as well as CSV (FR-160, specs/17 section 5.1).

Until P12c-13 only CSV was read, though FR-160 names both. The reader is the
standard library's, like the writer beside it: an importer needs the first
sheet's cells as text, and that is the string table, the sheet and the
relationship between them.

The workbooks here are written by hand, part by part, the way a spreadsheet
program writes them -- numbers at seventeen significant digits, text in the
shared-string table, cells left out where they are empty -- so the reader is
checked against what it will meet rather than against GeoComp's own writer.
"""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import pytest

from geocomp.core.errors import DataError
from geocomp.io import infer_mapping, read_field_book_csv
from geocomp.io.tabular import read_coordinates, read_rows
from tests import reference_rd01 as rd01
from tests.test_fieldbook_import import library

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELATIONSHIPS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE = "http://schemas.openxmlformats.org/package/2006/relationships"


def _column(index: int) -> str:
    name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def _is_number(text: str) -> bool:
    """Whether a spreadsheet would hold *text* as a number and give it back unchanged."""
    try:
        value = float(text)
    except ValueError:
        return False
    return text == repr(value) or (text.isdigit() and not text.startswith("0")) or text == "0"


def workbook(
    path: Path,
    rows: list[list[str]],
    *,
    sheets: tuple[str, ...] = ("sheet1.xml",),
    absolute: bool = False,
    extra_strings: str = "",
    sheet_data: str | None = None,
) -> Path:
    """Write *rows* as the first of *sheets*, as a spreadsheet program would."""
    strings: list[str] = []
    xml_rows = []
    for number, row in enumerate(rows, start=1):
        cells = []
        for index, text in enumerate(row, start=1):
            reference = f"{_column(index)}{number}"
            if text == "":
                continue
            if _is_number(text):
                cells.append(f'<c r="{reference}"><v>{float(text):.17g}</v></c>')
            else:
                strings.append(text)
                cells.append(f'<c r="{reference}" t="s"><v>{len(strings) - 1}</v></c>')
        xml_rows.append(f'<row r="{number}">' + "".join(cells) + "</row>")
    data = "".join(xml_rows) if sheet_data is None else sheet_data
    sheet = f'<worksheet xmlns="{MAIN}"><sheetData>{data}</sheetData></worksheet>'
    table = (
        f'<sst xmlns="{MAIN}">'
        + "".join(f"<si><t>{escape(text)}</t></si>" for text in strings)
        + extra_strings
        + "</sst>"
    )
    target = "/xl/worksheets/" if absolute else "worksheets/"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{MAIN}" xmlns:r="{RELATIONSHIPS}"><sheets>'
            + "".join(
                f'<sheet name="S{index}" sheetId="{index}" r:id="rId{index}"/>'
                for index in range(1, len(sheets) + 1)
            )
            + "</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            f'<Relationships xmlns="{PACKAGE}">'
            + "".join(
                f'<Relationship Id="rId{index}" Target="{target}{name}"/>'
                for index, name in enumerate(sheets, start=1)
            )
            + "</Relationships>",
        )
        archive.writestr("xl/sharedStrings.xml", table)
        for index, name in enumerate(sheets):
            archive.writestr(
                f"xl/worksheets/{name}",
                sheet if index == 0 else f'<worksheet xmlns="{MAIN}"><sheetData/></worksheet>',
            )
    return path


def _csv_rows(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


class TestRd01FromASpreadsheet:
    """RD-01's field book saved as a workbook reads as the CSV does."""

    @pytest.fixture
    def saved(self, tmp_path) -> Path:
        return workbook(tmp_path / "rd01.xlsx", _csv_rows(rd01.RAW))

    def test_the_rows_are_the_csvs(self, saved):
        assert read_rows(saved) == _csv_rows(rd01.RAW)

    def test_the_import_is_the_csvs(self, saved):
        mapping = infer_mapping(_csv_rows(rd01.RAW)[0])
        from_csv = read_field_book_csv(rd01.RAW, mapping, library=library())
        from_workbook = read_field_book_csv(saved, mapping, library=library())
        assert from_workbook.is_clean
        assert from_workbook.row_count == from_csv.row_count == 12
        assert [setup.station for setup in from_workbook.setups] == [
            setup.station for setup in from_csv.setups
        ]
        assert from_workbook.records == from_csv.records


class TestTheCells:
    def test_a_number_is_its_shortest_exact_decimal(self, tmp_path):
        """A spreadsheet stores 45.302 as 45.302000000000007."""
        path = workbook(tmp_path / "n.xlsx", [["45.302", "0.1", "12"]])
        assert read_rows(path) == [["45.302", "0.1", "12"]]

    def test_a_cell_left_out_is_empty_and_a_row_left_out_is_blank(self, tmp_path):
        path = workbook(tmp_path / "g.xlsx", [["a", "", "c"], [], ["x"]])
        assert read_rows(path) == [["a", "", "c"], ["", "", ""], ["x", "", ""]]

    def test_rich_text_is_its_runs_and_a_reading_aid_is_not_text(self, tmp_path):
        rich = (
            "<si><r><t>Est</t></r><r><t>ação</t></r>"
            "<rPh sb=\"0\" eb=\"1\"><t>reading aid</t></rPh></si>"
        )
        path = workbook(
            tmp_path / "r.xlsx",
            [["first"]],
            extra_strings=rich,
            sheet_data=(
                '<row r="1">'
                '<c r="A1" t="s"><v>1</v></c>'
                '<c r="B1" t="inlineStr"><is><t>inline</t></is></c>'
                '<c r="C1" t="b"><v>1</v></c>'
                "</row>"
            ),
        )
        assert read_rows(path) == [["Estação", "inline", "TRUE"]]

    def test_the_first_sheet_is_the_workbooks_first_not_the_first_file(self, tmp_path):
        path = workbook(
            tmp_path / "o.xlsx", [["mine"]], sheets=("sheet2.xml", "sheet1.xml"), absolute=True
        )
        assert read_rows(path) == [["mine"]]


class TestARefusal:
    @pytest.mark.parametrize(
        "content", [b"Station,HZ\nA,1\n", b"PK\x03\x04 not really a zip"], ids=["csv", "broken"]
    )
    def test_a_file_that_is_not_a_workbook_is_said_to_be_so(self, tmp_path, content):
        path = tmp_path / "book.xlsx"
        path.write_bytes(content)
        with pytest.raises(DataError) as refused:
            read_rows(path)
        assert refused.value.code == "data.workbook_unreadable"
        assert refused.value.context["path"] == str(path)

    def test_a_workbook_with_no_sheet_is_refused(self, tmp_path):
        path = tmp_path / "empty.xlsx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/workbook.xml", f'<workbook xmlns="{MAIN}"><sheets/></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="{PACKAGE}"/>')
        with pytest.raises(DataError):
            read_rows(path)


class TestStationCoordinates:
    """FR-160 names stations as well as observations: a table of approximate or
    control coordinates, one station a row."""

    def test_a_table_with_a_header_reads_as_its_rows(self, tmp_path):
        path = tmp_path / "control.csv"
        path.write_text(
            "station,easting,northing,height\nA,1000.0,2000.0,10.5\n\nB,1100.25,2050.5,11\n",
            encoding="utf-8",
        )
        assert read_coordinates(path) == {
            "A": (1000.0, 2000.0, 10.5),
            "B": (1100.25, 2050.5, 11.0),
        }

    def test_a_workbook_reads_as_the_csv_does(self, tmp_path):
        rows = [["station", "E", "N", "h"], ["A", "1000.0", "2000.0", "10.5"]]
        path = workbook(tmp_path / "control.xlsx", rows)
        assert read_coordinates(path) == {"A": (1000.0, 2000.0, 10.5)}

    def test_a_decimal_comma_is_a_decimal_point(self, tmp_path):
        path = tmp_path / "control.csv"
        path.write_text('A,"1000,5","2000,25","10,0"\n', encoding="utf-8")
        assert read_coordinates(path) == {"A": (1000.5, 2000.25, 10.0)}

    def test_a_row_that_is_not_coordinates_is_named(self, tmp_path):
        path = tmp_path / "control.csv"
        path.write_text("station,E,N,h\nA,1,2,3\nB,1,two,3\n", encoding="utf-8")
        with pytest.raises(DataError) as refused:
            read_coordinates(path)
        assert refused.value.code == "data.coordinate_row_unreadable"
        assert refused.value.context["row"] == 3

    def test_a_table_with_no_station_is_refused(self, tmp_path):
        path = tmp_path / "control.csv"
        path.write_text("station,E,N,h\n", encoding="utf-8")
        with pytest.raises(DataError) as refused:
            read_coordinates(path)
        assert refused.value.code == "data.coordinate_table_empty"
