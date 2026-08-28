# SPDX-License-Identifier: GPL-2.0-or-later
"""Reading geoid models from the files they are published in (FR-165).

``specs/17-persistence-and-interoperability.md`` section 5.5, acceptance
criterion 8: *a geoid model imports, is applied, records its identity in the
solution, and contributes its uncertainty.*

**Two formats, both read here in pure Python.**

*GTX* is the vertical-shift grid PROJ uses, so it is the format a model that
QGIS already handles arrives in. It is a forty-byte header and a block of
big-endian ``float32``, which takes no library at all.

*ESRI ASCII grid* is the text form nearly every GIS exports, and it is what the
national agencies' models are most often redistributed as.

Reading them without GDAL is a deliberate choice, and the same one
:mod:`geocomp.io.store.geopackage` made: GDAL is present in a QGIS install and
absent from seven of the nine environments the test suite runs in. A reader that
needs it is a reader that is exercised in one job and assumed in the others.
Anything neither format covers is a refusal naming both, rather than a silent
failure to interpolate.

**The file does not say how good the model is, so the caller must.** No grid
format carries the model's accuracy, and
:class:`~geocomp.core.geoid.GeoidModel` will not be built without one (FR-204).
So ``sigma`` is a required argument here: a default would be this module
inventing the number that a combined height adjustment is most sensitive to.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.geoid import Coverage, GeoidModel

__all__ = ["read_esri_ascii", "read_geoid", "read_gtx"]

#: The GTX header: south, west, latitude step, longitude step, rows, columns.
#: Big-endian throughout, which is the format's definition and not the host's
#: byte order -- reading it natively works on x86 and produces nonsense on any
#: big-endian machine, so it is spelled out.
_GTX_HEADER = struct.Struct(">4d2i")


def read_geoid(
    path: str | Path,
    *,
    sigma: float,
    id: str = "",
    name: str = "",
    version: str = "",
    source: str = "",
) -> GeoidModel:
    """Read a geoid model, dispatching on the file's extension.

    Args:
        path: The grid file. ``.gtx`` is read as GTX; ``.asc``, ``.txt`` and
            ``.grd`` as ESRI ASCII.
        sigma: The model's stated accuracy in metres. **Required**: no grid
            format carries it, and a geoid whose uncertainty was invented here
            would silently set the precision of every combined height (FR-204).
        id: The model's identity. Defaults to the file's stem, which in practice
            *is* the identity -- ``MAPGEO2015.gtx`` -- and is at least traceable
            to something real, unlike a generated name.

    Raises:
        ValidationError: ``geoid_format_unsupported``, naming what is read.
    """
    path = Path(path)
    identity = {
        "id": id or path.stem,
        "name": name,
        "version": version,
        "source": source or str(path),
    }

    suffix = path.suffix.lower()
    if suffix == ".gtx":
        return read_gtx(path, sigma=sigma, **identity)
    if suffix in {".asc", ".txt", ".grd"}:
        return read_esri_ascii(path, sigma=sigma, **identity)
    raise ValidationError(
        "geoid_format_unsupported",
        received=suffix or path.name,
        expected=(
            "a GTX grid (.gtx) or an ESRI ASCII grid (.asc, .txt, .grd). Convert "
            "the model with QGIS or gdal_translate; GeoComp reads these two "
            "without GDAL so that a geoid works wherever the plugin does"
        ),
    )


def read_gtx(
    path: str | Path,
    *,
    sigma: float,
    id: str = "",
    name: str = "",
    version: str = "",
    source: str = "",
) -> GeoidModel:
    """Read a PROJ/NOAA GTX vertical grid.

    The header gives the **lower-left** node and the step, both in degrees, then
    ``rows * columns`` big-endian ``float32`` in row-major order starting at the
    south. That is the same south-up order
    :class:`~geocomp.core.geoid.GeoidModel` stores, so nothing is flipped -- and
    the ESRI reader below, whose format is north-up, is where a flip belongs.

    Longitudes are normalised to ``(-180, 180]``: GTX files from the American
    agencies are commonly written in ``0..360``, and a model covering Brazil
    then claims to cover China.
    """
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) < _GTX_HEADER.size:
        raise DataError(
            "geoid_file_truncated",
            path=str(path),
            received=len(raw),
            expected=f"at least {_GTX_HEADER.size} bytes of GTX header",
        )

    south, west, d_lat, d_lon, rows, columns = _GTX_HEADER.unpack_from(raw)
    if rows < 2 or columns < 2 or d_lat <= 0.0 or d_lon <= 0.0:
        raise DataError(
            "geoid_header_not_usable",
            path=str(path),
            received={
                "rows": rows,
                "columns": columns,
                "d_lat": d_lat,
                "d_lon": d_lon,
            },
            expected="at least 2x2 nodes and positive steps, in degrees",
        )

    body = raw[_GTX_HEADER.size :]
    wanted = rows * columns * 4
    if len(body) < wanted:
        raise DataError(
            "geoid_file_truncated",
            path=str(path),
            received=len(body),
            expected=f"{wanted} bytes for a {rows}x{columns} grid of float32",
        )

    values = np.frombuffer(body[:wanted], dtype=">f4").astype(float).reshape(rows, columns)
    west = _normalise_longitude(west)

    return GeoidModel(
        id=id or path.stem,
        values=values,
        coverage=Coverage(
            south=math.radians(south),
            north=math.radians(south + (rows - 1) * d_lat),
            west=math.radians(west),
            east=math.radians(west + (columns - 1) * d_lon),
        ),
        sigma=sigma,
        name=name,
        version=version,
        source=source or str(path),
        meta={"format": "gtx", "rows": rows, "columns": columns},
    )


def read_esri_ascii(
    path: str | Path,
    *,
    sigma: float,
    id: str = "",
    name: str = "",
    version: str = "",
    source: str = "",
) -> GeoidModel:
    """Read an ESRI ASCII grid.

    Six header lines -- ``ncols``, ``nrows``, ``xllcorner``/``xllcenter``,
    ``yllcorner``/``yllcenter``, ``cellsize``, optional ``NODATA_value`` -- then
    the values, whitespace-separated, **north row first**. The rows are
    therefore reversed on the way in: a model read the other way up is wrong by
    twice the north-south variation of the geoid, which across Brazil is metres,
    and it produces heights that look plausible everywhere.

    A ``NODATA_value`` inside the grid is a refusal rather than a NaN, because a
    sentinel that reaches :class:`~geocomp.core.geoid.GeoidModel` would be
    interpolated into a perfectly ordinary-looking undulation.

    ``xllcorner`` gives the corner of the lower-left *cell* rather than the node,
    so it is shifted by half a cell; ``xllcenter`` is the node and is used as it
    stands. Confusing the two puts the whole model half a cell out.
    """
    path = Path(path)
    header: dict[str, float] = {}
    numbers: list[float] = []

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if not fields:
                continue
            key = fields[0].lower()
            if key in _HEADER_KEYS and len(fields) >= 2 and not numbers:
                header[key] = float(fields[1])
                continue
            numbers.extend(float(field) for field in fields)

    missing = [key for key in ("ncols", "nrows", "cellsize") if key not in header]
    # Either spelling of the lower-left origin will do, but one of each pair
    # must be there: without it the grid has values and no idea where they are.
    for pair in (("xllcorner", "xllcenter"), ("yllcorner", "yllcenter")):
        if not set(pair) & header.keys():
            missing.append("|".join(pair))
    if missing:
        raise DataError(
            "geoid_header_incomplete",
            path=str(path),
            received=sorted(header),
            expected=f"an ESRI ASCII header; missing {sorted(set(missing))}",
        )

    rows, columns = int(header["nrows"]), int(header["ncols"])
    cell = header["cellsize"]
    if rows < 2 or columns < 2 or cell <= 0.0:
        raise DataError(
            "geoid_header_not_usable",
            path=str(path),
            received={"nrows": rows, "ncols": columns, "cellsize": cell},
            expected="at least 2x2 nodes and a positive cellsize, in degrees",
        )
    if len(numbers) != rows * columns:
        raise DataError(
            "geoid_cell_count",
            path=str(path),
            received=len(numbers),
            expected=f"{rows * columns} values for a {rows}x{columns} grid",
        )

    no_data = header.get("nodata_value")
    if no_data is not None and any(value == no_data for value in numbers):
        raise DataError(
            "geoid_grid_has_no_data",
            path=str(path),
            received=no_data,
            expected=(
                "a grid with no no-data cells over the area of interest. A "
                "sentinel interpolates into a plausible-looking undulation, so "
                "it is refused rather than carried"
            ),
        )

    # North row first in the file, south row first in the model.
    values = np.asarray(numbers, dtype=float).reshape(rows, columns)[::-1]

    west = header.get("xllcenter")
    south = header.get("yllcenter")
    if west is None:
        west = header["xllcorner"] + cell / 2.0
    if south is None:
        south = header["yllcorner"] + cell / 2.0

    return GeoidModel(
        id=id or path.stem,
        values=values,
        coverage=Coverage(
            south=math.radians(south),
            north=math.radians(south + (rows - 1) * cell),
            west=math.radians(_normalise_longitude(west)),
            east=math.radians(_normalise_longitude(west) + (columns - 1) * cell),
        ),
        sigma=sigma,
        name=name,
        version=version,
        source=source or str(path),
        meta={"format": "esri_ascii", "rows": rows, "columns": columns},
    )


_HEADER_KEYS = frozenset(
    {
        "ncols",
        "nrows",
        "xllcorner",
        "yllcorner",
        "xllcenter",
        "yllcenter",
        "cellsize",
        "nodata_value",
    }
)


def _normalise_longitude(degrees: float) -> float:
    """Bring a longitude into ``(-180, 180]``.

    GTX files from the American agencies are commonly written in ``0..360``; a
    model of Brazil whose west edge reads 309 then claims to cover China, and
    every point in the project falls outside its coverage.
    """
    return degrees - 360.0 if degrees > 180.0 else degrees
