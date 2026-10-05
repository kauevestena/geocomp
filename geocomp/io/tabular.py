# SPDX-License-Identifier: GPL-2.0-or-later
"""Exporting networks and results to CSV and ``.xlsx`` (FR-162), and reading both (FR-160).

``specs/17-persistence-and-interoperability.md`` section 5.1.

Five sheets, one per thing a user asks for: stations, observations, adjusted
results, residuals and statistics. They are declared once, as
:data:`SHEETS`, and both writers consume the same declarations -- so a CSV
export and a spreadsheet export of the same solution have the same columns in
the same order, which is what makes one a substitute for the other.

**The ``.xlsx`` writer is built in, and that is a change from what was
planned.** ``specs/03-architecture.md`` section 3.7 listed ``openpyxl`` as an
optional dependency with the feature "degrading to CSV with a clear message"
where it is absent. Degrading is the wrong answer here for a reason that only
became clear on writing it: an ``.xlsx`` is a ZIP of XML, *writing* one needs no
formulas, no styling and no formats, and the whole writer is under a hundred
lines of standard library. Requiring a dependency a QGIS user cannot ``pip
install`` -- in order to produce a file GeoComp can perfectly well produce
itself -- buys nothing and costs the feature on exactly the machines least able
to fix it. So ``.xlsx`` export always works, everywhere.

**Reading one is built in too (P12c-13).** FR-160 asks for field books from
``.xlsx`` as well as CSV, and until P12c-13 only CSV was read. What an importer
needs from a workbook is the first sheet's cells as text, and that is the
shared-strings table, the sheet's XML and the relationship between them --
again standard library. Formulas are not evaluated: the value a spreadsheet
program saved with them is what is read. Dates are read as the serial numbers
they are stored as; no field book has a date column.

Numbers are written at full precision, never formatted. A spreadsheet is
somebody's next input, and a coordinate rounded on the way out is a coordinate
rounded for whatever they do next.
"""

from __future__ import annotations

import csv
import re
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.models import Network, Solution

__all__ = [
    "COMPARISON_FIELDS",
    "SHEETS",
    "Sheet",
    "read_coordinates",
    "read_rows",
    "read_workbook_rows",
    "sheet_rows",
    "write_csv",
    "write_workbook",
]


@dataclass(frozen=True)
class Sheet:
    """One table of an export: its name, its header and how to fill it."""

    name: str
    headers: tuple[str, ...]
    rows: Callable[[Network | None, Solution | None], list[list[Any]]]
    note: str = ""


def _station_rows(network: Network | None, solution: Solution | None) -> list[list[Any]]:
    del solution
    if network is None:
        return []
    rows = []
    for station in sorted(network.stations.values(), key=lambda s: s.id):
        position = station.approx_position
        values = position.values if position else ()
        rows.append(
            [
                station.id,
                station.name,
                station.station_type.name,
                station.constraint.mode.name,
                ";".join(sorted(station.constraint.components)),
                position.crs if position else "",
                position.height_type.name if position else "",
                *[quantity.value for quantity in values],
                *[quantity.std_dev for quantity in values],
            ]
        )
    return rows


def _observation_rows(network: Network | None, solution: Solution | None) -> list[list[Any]]:
    del solution
    if network is None:
        return []
    rows = []
    for observation in sorted(network.observations.values(), key=lambda o: o.id):
        for index, value in enumerate(observation.values):
            rows.append(
                [
                    observation.id,
                    observation.type.name,
                    observation.spec.components[index],
                    ";".join(observation.stations),
                    value.value,
                    value.std_dev,
                    value.unit.name,
                    value.mode.name,
                    ";".join(sorted(s.name for s in value.strategies)),
                    observation.status.name,
                    observation.cluster_id or "",
                ]
            )
    return rows


def _adjusted_rows(network: Network | None, solution: Solution | None) -> list[list[Any]]:
    del network
    if solution is None:
        return []
    rows = []
    for station in sorted(solution.adjusted_stations, key=lambda s: s.station_id):
        ellipse = station.ellipse
        rows.append(
            [
                station.station_id,
                *[quantity.value for quantity in station.position.values],
                *[quantity.std_dev for quantity in station.position.values],
                station.positional_uncertainty,
                ellipse.semi_major if ellipse else None,
                ellipse.semi_minor if ellipse else None,
                ellipse.orientation if ellipse else None,
                ellipse.confidence if ellipse else None,
                station.gravity.value if station.gravity is not None else None,
                station.gravity.std_dev if station.gravity is not None else None,
            ]
        )
    return rows


def _residual_rows(network: Network | None, solution: Solution | None) -> list[list[Any]]:
    del network
    if solution is None:
        return []
    rows = []
    for index, result in enumerate(solution.observation_results):
        test = result.w_test
        rows.append(
            [
                index,
                result.observation_id,
                result.residual,
                result.standardised_residual,
                result.redundancy,
                result.minimal_detectable_bias,
                result.external_reliability,
                result.adjusted_value,
                int(result.is_uncheckable),
                test.name if test else "",
                test.statistic if test and test.tested else None,
                int(test.passed) if test and test.tested else None,
            ]
        )
    return rows


def _statistics_rows(network: Network | None, solution: Solution | None) -> list[list[Any]]:
    del network
    if solution is None:
        return []
    statistics = solution.statistics
    test = statistics.global_test
    pairs: list[tuple[str, Any]] = [
        ("solution_id", solution.id),
        ("network_id", solution.network_id),
        ("kind", solution.kind.name),
        ("crs", solution.crs),
        ("epoch", solution.epoch.decimal_year),
        ("datum_definition", solution.datum_definition.name),
        ("uncertainty_mode", solution.uncertainty_mode.name),
        # FR-203: which approximations, not only that there were some.
        ("strategies", ";".join(sorted(s.name for s in solution.strategies))),
        ("n_observations", statistics.n_observations),
        ("n_parameters", statistics.n_parameters),
        ("n_constraints", statistics.n_constraints),
        ("degrees_of_freedom", statistics.degrees_of_freedom),
        ("variance_factor_apriori", statistics.variance_factor_apriori),
        ("variance_factor_aposteriori", statistics.variance_factor_aposteriori),
        ("iterations", statistics.iterations),
        ("converged", int(statistics.converged)),
        ("max_correction", statistics.max_correction),
        ("condition_number", statistics.condition_number),
        ("global_test", test.name if test else ""),
        # A test not made (no redundancy) has neither: blank, not NaN or a pass.
        ("global_test_statistic", test.statistic if test and test.tested else None),
        ("global_test_passed", int(test.passed) if test and test.tested else None),
    ]
    return [[name, value] for name, value in pairs]


#: The five exports, declared once and shared by both writers.
SHEETS: tuple[Sheet, ...] = (
    Sheet(
        "stations",
        (
            "id",
            "name",
            "type",
            "constraint",
            "constrained_components",
            "crs",
            "height_type",
            "value_1",
            "value_2",
            "value_3",
            "std_dev_1",
            "std_dev_2",
            "std_dev_3",
        ),
        _station_rows,
    ),
    Sheet(
        "observations",
        (
            "id",
            "type",
            "component",
            "stations",
            "value",
            "std_dev",
            "unit",
            "uncertainty_mode",
            "strategies",
            "status",
            "cluster",
        ),
        _observation_rows,
        note=(
            "One row per component: a GNSS baseline is three, and merging them "
            "would hide which carries what."
        ),
    ),
    Sheet(
        "adjusted",
        (
            "station",
            "value_1",
            "value_2",
            "value_3",
            "std_dev_1",
            "std_dev_2",
            "std_dev_3",
            "positional_uncertainty",
            "ellipse_semi_major",
            "ellipse_semi_minor",
            "ellipse_orientation",
            "ellipse_confidence",
            "gravity",
            "gravity_std_dev",
        ),
        _adjusted_rows,
        note=(
            "value_1..3 are the station's position in its own coordinate system. "
            "gravity and gravity_std_dev are in m/s^2, and empty for a station "
            "whose solution adjusted no gravity."
        ),
    ),
    Sheet(
        "residuals",
        (
            "row",
            "observation",
            "residual",
            "standardised_residual",
            "redundancy",
            "minimal_detectable_bias",
            "external_reliability",
            "adjusted_value",
            "is_uncheckable",
            "w_test",
            "w_statistic",
            "w_passed",
        ),
        _residual_rows,
    ),
    Sheet("statistics", ("quantity", "value"), _statistics_rows),
)

_BY_NAME = {sheet.name: sheet for sheet in SHEETS}

#: ``specs/20`` section 5, step 3: the fixed field list a comparison with
#: another package lines up, and where each lives in this export. The
#: comparison export *is* this one -- a second export of the same numbers would
#: be a second place for them to disagree. Statistics are rows of the
#: ``statistics`` sheet, keyed by their ``quantity``.
COMPARISON_FIELDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "adjusted coordinates": ("adjusted", ("value_1", "value_2", "value_3")),
    "variance factor": ("statistics", ("variance_factor_aposteriori",)),
    "degrees of freedom": ("statistics", ("degrees_of_freedom",)),
    "residuals": ("residuals", ("residual", "standardised_residual")),
    "error ellipses": (
        "adjusted",
        ("ellipse_semi_major", "ellipse_semi_minor", "ellipse_orientation", "ellipse_confidence"),
    ),
    "positional uncertainty": ("adjusted", ("positional_uncertainty",)),
    "test decisions": ("residuals", ("w_test", "w_statistic", "w_passed")),
    "global test decision": ("statistics", ("global_test_statistic", "global_test_passed")),
}


def sheet_rows(
    name: str, network: Network | None = None, solution: Solution | None = None
) -> tuple[tuple[str, ...], list[list[Any]]]:
    """The header and rows of one sheet."""
    try:
        sheet = _BY_NAME[name]
    except KeyError:
        raise ValidationError(
            "unknown_export_sheet",
            received=name,
            expected=sorted(_BY_NAME),
        ) from None
    return sheet.headers, sheet.rows(network, solution)


def _cell(value: Any) -> str:
    """One value as text, at full precision.

    ``repr`` for a float rather than a format: a coordinate written to six
    decimals is a coordinate the next computation cannot reproduce, and a
    spreadsheet is somebody's next input.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(
    directory: str | Path,
    *,
    network: Network | None = None,
    solution: Solution | None = None,
    sheets: Sequence[str] | None = None,
    prefix: str = "",
) -> list[Path]:
    """Write one CSV per sheet into *directory*, returning what was written.

    Only sheets with content are written: an empty ``residuals.csv`` beside a
    network that was never adjusted invites the reader to conclude the residuals
    were zero.
    """
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for sheet in _selected(sheets):
        headers, rows = sheet.headers, sheet.rows(network, solution)
        if not rows:
            continue
        path = target / f"{prefix}{sheet.name}.csv"
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([_cell(value) for value in row])
        written.append(path)
    return written


def _selected(sheets: Sequence[str] | None) -> list[Sheet]:
    if sheets is None:
        return list(SHEETS)
    chosen = []
    for name in sheets:
        try:
            chosen.append(_BY_NAME[name])
        except KeyError:
            raise ValidationError(
                "unknown_export_sheet", received=name, expected=sorted(_BY_NAME)
            ) from None
    return chosen


# -- the built-in .xlsx writer -------------------------------------------
#
# An .xlsx is a ZIP holding a handful of XML parts. Writing one needs the
# workbook, its relationships, the content types, and a sheet per table. No
# styles, no shared strings, no formats -- values are written inline, which is
# valid and is what a data export is.


def _column_name(index: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA."""
    name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def _sheet_xml(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]

    def render(number: int, values: Sequence[Any]) -> str:
        cells = []
        for index, value in enumerate(values, start=1):
            reference = f"{_column_name(index)}{number}"
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                cells.append(f'<c r="{reference}"><v>{int(value)}</v></c>')
            elif isinstance(value, (int, float)):
                cells.append(f'<c r="{reference}"><v>{value!r}</v></c>')
            else:
                text = escape(str(value))
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{text}</t></is></c>')
        return f'<row r="{number}">' + "".join(cells) + "</row>"

    lines.append(render(1, list(headers)))
    for number, row in enumerate(rows, start=2):
        lines.append(render(number, list(row)))

    lines.append("</sheetData></worksheet>")
    return "".join(lines)


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
    'relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.sheet.main+xml"/>'
    "{sheets}"
    "</Types>"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)


def write_workbook(
    path: str | Path,
    *,
    network: Network | None = None,
    solution: Solution | None = None,
    sheets: Sequence[str] | None = None,
) -> Path:
    """Write one ``.xlsx`` holding every non-empty sheet.

    Deterministic: the ZIP entries carry a fixed timestamp, so exporting the
    same solution twice gives byte-identical files (NFR-007). A file whose bytes
    change with the clock cannot be compared, checksummed or committed.
    """
    target = Path(path)
    chosen = [
        (sheet, sheet.rows(network, solution))
        for sheet in _selected(sheets)
    ]
    chosen = [(sheet, rows) for sheet, rows in chosen if rows]
    if not chosen:
        raise ValidationError(
            "nothing_to_export",
            expected=(
                "a network or a solution with content. Every sheet came out "
                "empty, and a workbook of empty sheets says the data was zero "
                "rather than absent"
            ),
        )

    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'worksheet+xml"/>'
        for index in range(1, len(chosen) + 1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(
            f'<sheet name="{escape(sheet.name)}" sheetId="{index}" r:id="rId{index}"/>'
            for index, (sheet, _rows) in enumerate(chosen, start=1)
        )
        + "</sheets></workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, len(chosen) + 1)
        )
        + "</Relationships>"
    )

    fixed = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:

        def add(name: str, text: str) -> None:
            info = zipfile.ZipInfo(name, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, text)

        add("[Content_Types].xml", _CONTENT_TYPES.format(sheets=overrides))
        add("_rels/.rels", _ROOT_RELS)
        add("xl/workbook.xml", workbook)
        add("xl/_rels/workbook.xml.rels", workbook_rels)
        for index, (sheet, rows) in enumerate(chosen, start=1):
            add(f"xl/worksheets/sheet{index}.xml", _sheet_xml(sheet.headers, rows))

    return target


# -- reading: CSV, or the first sheet of an .xlsx (FR-160) ---------------

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_RELATIONSHIP = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PACKAGE = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_REFERENCE = re.compile(r"^([A-Z]+)\d*$")


def read_rows(path: str | Path, *, encoding: str = "utf-8-sig") -> list[list[str]]:
    """The rows of a CSV file, or of an ``.xlsx`` workbook's first sheet, as text.

    One reader for every importer, so a field book is the same rows whichever
    of the two it arrives as. ``utf-8-sig`` for CSV because spreadsheet
    exporters routinely write a byte-order mark.
    """
    source = Path(path)
    if source.suffix.lower() == ".xlsx":
        return read_workbook_rows(source)
    with open(source, encoding=encoding, newline="") as handle:
        return list(csv.reader(handle))


def read_workbook_rows(path: str | Path, *, limit: int | None = None) -> list[list[str]]:
    """The first worksheet of an ``.xlsx``, every row as wide as the widest.

    A cell the sheet leaves out is ``""``, as an empty CSV field is. Numbers
    are their shortest exact decimal: a spreadsheet stores ``45.302`` as
    ``45.302000000000007``, and the field book said ``45.302``.

    With *limit*, only the sheet's first *limit* rows are read. The sheet is
    streamed and left as soon as they are, and the string table is read only
    as far as they reach into it, so a preview costs what it shows rather than
    what the workbook holds: the mapping dialog reads on the GUI thread
    (NFR-004), and until P12c-13 a 5,000-row workbook held it for 0.4 s.
    """
    source = Path(path)
    try:
        with zipfile.ZipFile(source) as archive:
            names = set(archive.namelist())
            with archive.open(_first_sheet(archive)) as part:
                rows = _sheet_cells(part, limit)
            needed = max(
                (
                    int(text)
                    for cells in rows.values()
                    for kind, text in cells.values()
                    if kind == "s" and text
                ),
                default=-1,
            )
            strings = (
                _shared_strings(archive, through=needed)
                if needed >= 0 and "xl/sharedStrings.xml" in names
                else []
            )
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, ValueError) as error:
        raise DataError("workbook_unreadable", path=str(source)) from error

    if not rows:
        return []
    width = max((max(cells) for cells in rows.values() if cells), default=0)
    return [
        [
            _decode(*rows[number][column], strings)
            if column in rows.get(number, {})
            else ""
            for column in range(1, width + 1)
        ]
        for number in range(1, max(rows) + 1)
    ]


def _sheet_cells(stream, limit: int | None) -> dict[int, dict[int, tuple[str, str]]]:
    """Each row's cells as (type, raw text), by row and column number, read
    one row at a time and no further than row *limit*."""
    rows: dict[int, dict[int, tuple[str, str]]] = {}
    for _event, element in ElementTree.iterparse(stream, events=("end",)):
        if element.tag != f"{_MAIN}row":
            continue
        number = int(element.get("r") or (max(rows, default=0) + 1))
        if limit is not None and number > limit:
            break
        cells: dict[int, tuple[str, str]] = {}
        column = 0
        for cell in element.findall(f"{_MAIN}c"):
            reference = cell.get("r")
            column = _column_index(reference) if reference else column + 1
            cells[column] = _cell_raw(cell)
        rows[number] = cells
        element.clear()
    return rows
def _first_sheet(archive: zipfile.ZipFile) -> str:
    """The part holding the workbook's first sheet, by its relationship."""
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    first = workbook.find(f"{_MAIN}sheets/{_MAIN}sheet")
    if first is None:
        raise ValueError("the workbook has no sheet")
    identifier = first.get(f"{_RELATIONSHIP}id")
    relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relationship in relationships.iter(f"{_PACKAGE}Relationship"):
        if relationship.get("Id") == identifier:
            target = relationship.get("Target", "")
            return target.lstrip("/") if target.startswith("/") else f"xl/{target}"
    raise ValueError("the first sheet has no part")


def _shared_strings(archive: zipfile.ZipFile, *, through: int) -> list[str]:
    """The workbook's string table, as far as entry *through*. Phonetic runs
    (``rPh``) are not the text."""
    table: list[str] = []
    with archive.open("xl/sharedStrings.xml") as part:
        for _event, item in ElementTree.iterparse(part, events=("end",)):
            if item.tag != f"{_MAIN}si":
                continue
            parts = [
                item.find(f"{_MAIN}t"),
                *(run.find(f"{_MAIN}t") for run in item.findall(f"{_MAIN}r")),
            ]
            table.append("".join(part.text or "" for part in parts if part is not None))
            item.clear()
            if len(table) > through:
                break
    return table


def _column_index(reference: str) -> int:
    """``A1`` -> 1, ``AA7`` -> 27."""
    match = _REFERENCE.match(reference)
    if match is None:
        raise ValueError(f"not a cell reference: {reference}")
    index = 0
    for letter in match.group(1):
        index = index * 26 + ord(letter) - ord("A") + 1
    return index


def _cell_raw(cell: ElementTree.Element) -> tuple[str, str]:
    """A cell's type and its text as stored: an index into the string table
    for a shared string, the text itself for an inline one."""
    kind = cell.get("t", "n")
    if kind == "inlineStr":
        return kind, "".join(node.text or "" for node in cell.iter(f"{_MAIN}t"))
    value = cell.find(f"{_MAIN}v")
    return kind, (value.text or "" if value is not None else "")


def _decode(kind: str, text: str, strings: list[str]) -> str:
    if kind == "s":
        return strings[int(text)] if text else ""
    if kind == "b":
        return "TRUE" if text == "1" else "FALSE"
    if kind == "n" and text and any(mark in text for mark in ".eE"):
        return repr(float(text))
    return text


def read_coordinates(path: str | Path) -> dict[str, tuple[float, float, float]]:
    """Stations and their coordinates from a CSV or ``.xlsx`` table (FR-160).

    One row per station: its name, then easting, northing and height in metres.
    A first row whose coordinates are not numbers is a header and is skipped;
    blank rows are skipped. A decimal comma is read as a decimal point, as in
    a field book (:func:`geocomp.io.mapping.parse_number`).
    """
    from geocomp.io.mapping import parse_number

    source = Path(path)
    coordinates: dict[str, tuple[float, float, float]] = {}
    first = True
    for number, row in enumerate(read_rows(source), start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        try:
            if len(cells) < 4 or not cells[0]:
                raise ValueError("not a station and three coordinates")
            values = tuple(parse_number(cell, "auto") for cell in cells[1:4])
        except ValueError as error:
            if first:
                first = False
                continue
            raise DataError(
                "coordinate_row_unreadable", path=str(source), row=number
            ) from error
        first = False
        coordinates[cells[0]] = (values[0], values[1], values[2])
    if not coordinates:
        raise DataError("coordinate_table_empty", path=str(source))
    return coordinates
