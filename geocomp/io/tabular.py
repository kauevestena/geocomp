# SPDX-License-Identifier: GPL-2.0-or-later
"""Exporting networks and results to CSV and ``.xlsx`` (FR-162).

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
to fix it. So ``.xlsx`` export always works, everywhere, and ``openpyxl``
remains optional for the day GeoComp needs to *read* one, which is a genuinely
harder problem.

Numbers are written at full precision, never formatted. A spreadsheet is
somebody's next input, and a coordinate rounded on the way out is a coordinate
rounded for whatever they do next.
"""

from __future__ import annotations

import csv
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from geocomp.core.errors import ValidationError
from geocomp.core.models import Network, Solution

__all__ = [
    "SHEETS",
    "Sheet",
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
                test.statistic if test else None,
                int(test.passed) if test else None,
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
        ("global_test_statistic", test.statistic if test else None),
        ("global_test_passed", int(test.passed) if test else None),
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
        ),
        _adjusted_rows,
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
