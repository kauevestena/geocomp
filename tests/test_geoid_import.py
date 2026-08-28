# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading geoid models from GTX and ESRI ASCII files (FR-165).

``specs/17-persistence-and-interoperability.md`` section 5.5 and its acceptance
criterion 8: *a geoid model imports, is applied, records its identity in the
solution, and contributes its uncertainty.* The first and last clauses are here;
the middle two are in :mod:`tests.test_levelling` and
:mod:`tests.test_geoid_in_a_solution`.

Both readers are written against the formats' published layouts, so the tests
build the files byte by byte from those layouts rather than from the reader --
a test that generates its fixture with the code under test proves only that the
code is self-consistent.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.io.geoid import read_esri_ascii, read_geoid, read_gtx

#: Rows south to north, columns west to east. Distinct values throughout, so a
#: transposed or flipped read cannot pass by symmetry.
GRID = [
    [-5.0, -5.5, -6.0, -6.5],
    [-4.0, -4.5, -5.0, -5.5],
    [-3.0, -3.5, -4.0, -4.5],
]
SOUTH, WEST, STEP = -26.0, -51.0, 0.5


def write_gtx(path: Path, grid: list[list[float]], *, west: float = WEST) -> Path:
    """A GTX file assembled from the format's definition: header then float32.

    Header: south, west, latitude step, longitude step (all float64 degrees),
    then rows and columns (int32). Big-endian throughout. Values follow in
    row-major order from the southern row.
    """
    rows, columns = len(grid), len(grid[0])
    payload = struct.pack(">4d2i", SOUTH, west, STEP, STEP, rows, columns)
    for row in grid:
        payload += struct.pack(f">{columns}f", *row)
    path.write_bytes(payload)
    return path


def write_esri(path: Path, grid: list[list[float]], *, no_data: float | None = None) -> Path:
    """An ESRI ASCII grid: six header lines, then the **north row first**."""
    rows, columns = len(grid), len(grid[0])
    lines = [
        f"ncols {columns}",
        f"nrows {rows}",
        f"xllcenter {WEST}",
        f"yllcenter {SOUTH}",
        f"cellsize {STEP}",
    ]
    if no_data is not None:
        lines.append(f"NODATA_value {no_data}")
    lines.extend(" ".join(f"{value}" for value in row) for row in reversed(grid))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# -- GTX ------------------------------------------------------------------


def test_gtx_reads_the_grid_the_right_way_up(tmp_path: Path) -> None:
    """Row 0 of a GTX file is the southern row, and stays row 0."""
    model = read_gtx(write_gtx(tmp_path / "MAPGEO.gtx", GRID), sigma=0.05)
    np.testing.assert_allclose(model.values, np.array(GRID))
    assert model.undulation(math.radians(SOUTH), math.radians(WEST)).value == pytest.approx(-5.0)
    assert model.undulation(
        math.radians(SOUTH + 2 * STEP), math.radians(WEST)
    ).value == pytest.approx(-3.0)


def test_gtx_coverage_comes_from_the_header(tmp_path: Path) -> None:
    model = read_gtx(write_gtx(tmp_path / "g.gtx", GRID), sigma=0.05)
    assert model.coverage.south == pytest.approx(math.radians(SOUTH))
    assert model.coverage.north == pytest.approx(math.radians(SOUTH + 2 * STEP))
    assert model.coverage.west == pytest.approx(math.radians(WEST))
    assert model.coverage.east == pytest.approx(math.radians(WEST + 3 * STEP))


def test_gtx_longitudes_past_180_are_brought_back(tmp_path: Path) -> None:
    """A 0..360 file of Brazil would otherwise claim to cover China."""
    model = read_gtx(write_gtx(tmp_path / "g.gtx", GRID, west=360.0 + WEST), sigma=0.05)
    assert model.coverage.west == pytest.approx(math.radians(WEST))
    assert model.coverage.contains(math.radians(SOUTH), math.radians(WEST))


def test_gtx_takes_its_identity_from_the_file_name(tmp_path: Path) -> None:
    """FR-804: the id is what a solution records, so it must be traceable."""
    model = read_gtx(write_gtx(tmp_path / "MAPGEO2015.gtx", GRID), sigma=0.05)
    assert model.id == "MAPGEO2015"
    assert model.source.endswith("MAPGEO2015.gtx")


def test_a_truncated_gtx_is_reported_not_padded(tmp_path: Path) -> None:
    path = write_gtx(tmp_path / "g.gtx", GRID)
    path.write_bytes(path.read_bytes()[:-8])
    with pytest.raises(DataError) as excinfo:
        read_gtx(path, sigma=0.05)
    assert excinfo.value.code == "data.geoid_file_truncated"


def test_a_gtx_header_that_cannot_be_used_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "g.gtx"
    path.write_bytes(struct.pack(">4d2i", SOUTH, WEST, 0.0, STEP, 3, 4) + b"\x00" * 48)
    with pytest.raises(DataError) as excinfo:
        read_gtx(path, sigma=0.05)
    assert excinfo.value.code == "data.geoid_header_not_usable"


# -- ESRI ASCII -----------------------------------------------------------


def test_esri_rows_are_flipped_on_the_way_in(tmp_path: Path) -> None:
    """The file's first row is the north one; the model's is the south one.

    Reading it the other way up is wrong by twice the north-south variation of
    the geoid -- metres, across Brazil -- and looks entirely plausible.
    """
    model = read_esri_ascii(write_esri(tmp_path / "g.asc", GRID), sigma=0.05)
    np.testing.assert_allclose(model.values, np.array(GRID))
    assert model.undulation(math.radians(SOUTH), math.radians(WEST)).value == pytest.approx(-5.0)


def test_the_two_formats_read_the_same_grid_identically(tmp_path: Path) -> None:
    """The strongest check available: two independent parsers, one answer."""
    gtx = read_gtx(write_gtx(tmp_path / "g.gtx", GRID), sigma=0.05)
    esri = read_esri_ascii(write_esri(tmp_path / "g.asc", GRID), sigma=0.05)
    np.testing.assert_allclose(gtx.values, esri.values)
    for edge, value in gtx.coverage.to_dict().items():
        assert value == pytest.approx(esri.coverage.to_dict()[edge]), edge


def test_a_corner_origin_is_shifted_by_half_a_cell(tmp_path: Path) -> None:
    """``xllcorner`` is the cell's corner; ``xllcenter`` is the node itself."""
    path = tmp_path / "corner.asc"
    path.write_text(
        f"ncols 4\nnrows 3\nxllcorner {WEST}\nyllcorner {SOUTH}\ncellsize {STEP}\n"
        + "\n".join(" ".join(str(v) for v in row) for row in reversed(GRID))
        + "\n",
        encoding="utf-8",
    )
    model = read_esri_ascii(path, sigma=0.05)
    assert model.coverage.south == pytest.approx(math.radians(SOUTH + STEP / 2.0))
    assert model.coverage.west == pytest.approx(math.radians(WEST + STEP / 2.0))


def test_a_no_data_cell_is_refused_not_interpolated(tmp_path: Path) -> None:
    """A sentinel becomes a perfectly ordinary-looking undulation otherwise."""
    holed = [list(row) for row in GRID]
    holed[1][2] = -9999.0
    path = write_esri(tmp_path / "holed.asc", holed, no_data=-9999.0)
    with pytest.raises(DataError) as excinfo:
        read_esri_ascii(path, sigma=0.05)
    assert excinfo.value.code == "data.geoid_grid_has_no_data"


def test_a_declared_no_data_value_that_is_absent_is_fine(tmp_path: Path) -> None:
    """Nearly every file declares one; only a file that *uses* one is refused."""
    model = read_esri_ascii(write_esri(tmp_path / "g.asc", GRID, no_data=-9999.0), sigma=0.05)
    np.testing.assert_allclose(model.values, np.array(GRID))


def test_a_wrong_cell_count_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "short.asc"
    path.write_text(
        f"ncols 4\nnrows 3\nxllcenter {WEST}\nyllcenter {SOUTH}\ncellsize {STEP}\n"
        "1 2 3 4\n5 6 7 8\n",
        encoding="utf-8",
    )
    with pytest.raises(DataError) as excinfo:
        read_esri_ascii(path, sigma=0.05)
    assert excinfo.value.code == "data.geoid_cell_count"
    assert excinfo.value.context["received"] == 8


def test_a_missing_header_field_names_what_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "bare.asc"
    path.write_text("ncols 4\nnrows 3\ncellsize 0.5\n1 2 3 4\n", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        read_esri_ascii(path, sigma=0.05)
    assert excinfo.value.code == "data.geoid_header_incomplete"
    assert "xllcorner|xllcenter" in str(excinfo.value)


# -- dispatch and the required accuracy -----------------------------------


def test_read_geoid_dispatches_on_the_extension(tmp_path: Path) -> None:
    assert read_geoid(write_gtx(tmp_path / "a.gtx", GRID), sigma=0.05).meta["format"] == "gtx"
    assert (
        read_geoid(write_esri(tmp_path / "b.asc", GRID), sigma=0.05).meta["format"]
        == "esri_ascii"
    )


def test_an_unsupported_format_names_the_two_that_work(tmp_path: Path) -> None:
    path = tmp_path / "model.tif"
    path.write_bytes(b"II*\x00")
    with pytest.raises(ValidationError) as excinfo:
        read_geoid(path, sigma=0.05)
    assert excinfo.value.code == "validation.geoid_format_unsupported"
    assert ".gtx" in str(excinfo.value)


def test_the_accuracy_cannot_be_defaulted(tmp_path: Path) -> None:
    """FR-204: no grid format carries it, so the caller states it or nothing works.

    A default here would be this module quietly setting the precision that a
    combined height adjustment is most sensitive to.
    """
    with pytest.raises(TypeError):
        read_geoid(write_gtx(tmp_path / "g.gtx", GRID))  # type: ignore[call-arg]


def test_a_zero_accuracy_is_refused_by_the_model(tmp_path: Path) -> None:
    with pytest.raises(ValidationError) as excinfo:
        read_gtx(write_gtx(tmp_path / "g.gtx", GRID), sigma=0.0)
    assert excinfo.value.code == "validation.geoid_without_sigma"


def test_identity_and_version_are_carried_through(tmp_path: Path) -> None:
    model = read_geoid(
        write_gtx(tmp_path / "g.gtx", GRID),
        sigma=0.05,
        id="MAPGEO2015",
        name="Modelo de Ondulacao Geoidal",
        version="2015",
        source="IBGE",
    )
    assert (model.id, model.version, model.source) == ("MAPGEO2015", "2015", "IBGE")
    assert model.label == "Modelo de Ondulacao Geoidal 2015"
