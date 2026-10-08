# SPDX-License-Identifier: GPL-2.0-or-later
"""Inputs held in the project's own layers read as their files do (FR-160, FR-320; P12c-44).

A field book: the layer is made from the very rows the file holds, named as the
file is, and the two imports must write the same document. Twice: once with
every field text, as a CSV opened in QGIS is, and once with the numeric columns
typed as numbers, as a layer of the user's own design would be -- the case
where a reading of ``1.4520`` comes back from QGIS as the double ``1.452``.

Stations: Classical network adjusts RD-01 to the same answer from a point layer
as from the coordinates file, the layer in the network's CRS with Z, and in
another CRS with the heights in a field.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import tests.reference_levelling as rd
import tests.reference_rd01 as rd01
from tests.conftest import requires_qgis
from tests.qgis.test_levelling_algorithms import (
    _line_rows,
    _reading_layout_mapping,
    _write_book,
)

pytestmark = [pytest.mark.qgis, requires_qgis]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


def _numeric(column: list[str]) -> bool:
    try:
        [float(value) for value in column if value != ""]
    except ValueError:
        return False
    return any(value != "" for value in column)


def _layer(rows: list[list[str]], name: str, *, typed: bool):
    """A memory layer without geometry holding *rows*, the first being the header."""
    from qgis.core import QgsFeature, QgsVectorLayer

    header, body = rows[0], rows[1:]
    kinds = [
        "double" if typed and _numeric([row[index] for row in body]) else "string"
        for index in range(len(header))
    ]
    assert not typed or "double" in kinds, "a typed layer with no numeric column tests nothing"
    uri = "None?" + "&".join(f"field={field}:{kind}" for field, kind in zip(header, kinds, strict=True))
    layer = QgsVectorLayer(uri, name, "memory")
    assert layer.isValid()
    features = []
    for row in body:
        feature = QgsFeature(layer.fields())
        feature.setAttributes(
            [
                (float(value) if value != "" else None) if kind == "double" else value
                for value, kind in zip(row, kinds, strict=True)
            ]
        )
        features.append(feature)
    assert layer.dataProvider().addFeatures(features)
    return layer


def _run(algorithm_id: str, parameters: dict):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok
    return results


def _csv_rows(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


TOTAL_STATION = {
    "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
    "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
    "SIGMA_DISTANCE": 0.002,
}


class TestATotalStationBook:
    def _import(self, tmp_path: Path, **source) -> dict:
        results = _run(
            "geocomp:totalstation_import_fieldbook",
            {**source, **TOTAL_STATION, "OUTPUT_READINGS": str(tmp_path / "readings.json")},
        )
        return json.loads(Path(results["OUTPUT_READINGS"]).read_text(encoding="utf-8"))

    @pytest.mark.parametrize("typed", [False, True], ids=["text", "typed"])
    def test_its_layer_reads_as_its_file(self, tmp_path, typed):
        for directory in ("file", "layer"):
            (tmp_path / directory).mkdir()
        from_file = self._import(tmp_path / "file", SOURCE=str(rd01.RAW))
        layer = _layer(_csv_rows(rd01.RAW), rd01.RAW.name, typed=typed)
        from_layer = self._import(tmp_path / "layer", SOURCE_LAYER=layer)
        assert from_layer == from_file
        assert len(from_layer["setups"]) == 3

    def test_both_are_refused(self, tmp_path):
        from qgis.core import QgsProcessingException

        layer = _layer(_csv_rows(rd01.RAW), rd01.RAW.name, typed=False)
        with pytest.raises(QgsProcessingException, match="two ways of giving the same input"):
            self._import(tmp_path, SOURCE=str(rd01.RAW), SOURCE_LAYER=layer)

    def test_neither_is_refused(self, tmp_path):
        from qgis.core import QgsProcessingException

        with pytest.raises(
            QgsProcessingException,
            match="Neither 'Field book' nor 'Field book, as a layer of the project' was given",
        ):
            self._import(tmp_path)


class TestALevellingBook:
    @pytest.mark.parametrize("typed", [False, True], ids=["text", "typed"])
    def test_its_layer_reads_as_its_file(self, tmp_path, typed):
        rows = _line_rows(rd.balanced_line())
        book = _write_book(tmp_path / "book.csv", rows)
        mapping = _reading_layout_mapping(tmp_path / "mapping.json")
        documents = []
        layer = _layer(rows, book.name, typed=typed)
        for name, source in (("file", {"BOOK": str(book)}), ("layer", {"BOOK_LAYER": layer})):
            results = _run(
                "geocomp:levelling_import",
                {**source, "MAPPING": str(mapping), "OUTPUT_SETUPS": str(tmp_path / f"{name}.json")},
            )
            documents.append(json.loads(Path(results["OUTPUT_SETUPS"]).read_text(encoding="utf-8")))
        assert documents[0] == documents[1]
        assert documents[0]["lines"]


# -- stations ---------------------------------------------------------------

#: Where RD-01's local frame is moved to: inside the area EPSG:31982 is defined
#: for, so the network is reduced to the grid and the heights the layer gives
#: are used, not only carried.
_FALSE_ORIGIN = (500_000.0, 7_000_000.0)


def _stations() -> dict[str, tuple[float, float, float]]:
    """RD-01's approximate stations at :data:`_FALSE_ORIGIN`, each with a height of its own."""
    east, north = _FALSE_ORIGIN
    return {
        name: (e + east, n + north, 100.25 + index)
        for index, (name, (e, n, _up)) in enumerate(rd01.approximate_coordinates().items())
    }


def _point_layer(stations, crs: str, *, with_z: bool, height_field: bool = False, carry_to: str = ""):
    """*stations* as a point layer in *crs*, named by an integer field, as a user's own would be.

    With *carry_to*, the points are moved from *crs* into that CRS first, and the
    layer is in it. A height field holds text with a decimal comma.
    """
    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsFeature,
        QgsGeometry,
        QgsPoint,
        QgsPointXY,
        QgsProject,
        QgsVectorLayer,
    )

    transform = None
    if carry_to:
        transform = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(crs), QgsCoordinateReferenceSystem(carry_to), QgsProject.instance()
        )
    uri = ("PointZ" if with_z else "Point") + f"?crs={carry_to or crs}&field=station:integer"
    if height_field:
        uri += "&field=height:string"
    layer = QgsVectorLayer(uri, "stations", "memory")
    assert layer.isValid()
    features = []
    for name, (easting, northing, up) in stations.items():
        if transform is not None:
            moved = transform.transform(QgsPointXY(easting, northing))
            easting, northing = moved.x(), moved.y()
        feature = QgsFeature(layer.fields())
        feature.setAttributes([int(name)] + ([f"{up}".replace(".", ",")] if height_field else []))
        point = QgsPoint(easting, northing, up) if with_z else QgsPoint(easting, northing)
        feature.setGeometry(QgsGeometry(point))
        features.append(feature)
    assert layer.dataProvider().addFeatures(features)
    return layer


@pytest.fixture(scope="module")
def reduced(tmp_path_factory) -> str:
    """RD-01 imported and reduced: the observations every station source is adjusted with."""
    directory = tmp_path_factory.mktemp("rd01")
    readings = _run(
        "geocomp:totalstation_import_fieldbook",
        {"SOURCE": str(rd01.RAW), **TOTAL_STATION, "OUTPUT_READINGS": str(directory / "readings.json")},
    )
    return _run(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": readings["OUTPUT_READINGS"],
            "APPLY_ATMOSPHERIC": False,
            "OUTPUT_REDUCED": str(directory / "reduced.json"),
        },
    )["OUTPUT_REDUCED"]


def _adjust(reduced: str, directory: Path, feedback=None, **source) -> tuple[dict, dict, dict]:
    """Classical network over RD-01: its results, its network document, and its stations by name."""
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    directory.mkdir()
    parameters = {
        "REDUCTIONS": reduced,
        **source,
        "DIMENSION": 0,
        "DATUM": 1,
        "CRS": "EPSG:31982",
        "OUTPUT_NETWORK": str(directory / "network.json"),
        "OUTPUT_STATIONS": str(directory / "stations.csv"),
    }
    algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:totalstation_network").create({})
    results, ok = algorithm.run(
        parameters, QgsProcessingContext(), feedback or QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok
    network = json.loads((directory / "network.json").read_text(encoding="utf-8"))
    with open(directory / "stations.csv", encoding="utf-8", newline="") as handle:
        stations = {row["station"]: (float(row["x"]), float(row["y"])) for row in csv.DictReader(handle)}
    return results, network, stations


def _heights(network: dict) -> list[float]:
    return [station["approx_position"]["values"][2]["value"] for station in network["stations"]]


class TestStationsFromAPointLayer:
    @pytest.fixture(scope="class")
    def from_file(self, reduced, tmp_path_factory):
        directory = tmp_path_factory.mktemp("from_file")
        approximate = directory / "approximate.json"
        approximate.write_text(json.dumps(_stations()), encoding="utf-8")
        return _adjust(reduced, directory / "run", APPROXIMATE=str(approximate))

    def _same(self, adjusted, from_file, *, tolerance: float) -> None:
        results, network, stations = adjusted
        expected_results, expected_network, expected_stations = from_file
        assert results["DEGREES_OF_FREEDOM"] == expected_results["DEGREES_OF_FREEDOM"]
        # Linearised about points a few nanometres apart: the same to a part in a million.
        assert results["VARIANCE_FACTOR"] == pytest.approx(expected_results["VARIANCE_FACTOR"], rel=1e-6)
        assert stations.keys() == expected_stations.keys() == {"1", "2", "3"}
        for name, (x, y) in stations.items():
            assert x == pytest.approx(expected_stations[name][0], abs=tolerance)
            assert y == pytest.approx(expected_stations[name][1], abs=tolerance)
        # The heights the reduction to the grid used, as the layer gave them.
        assert _heights(network) == _heights(expected_network) == [100.25, 101.25, 102.25]

    def test_in_the_networks_crs_with_z_it_reads_as_its_file(self, reduced, from_file, tmp_path):
        layer = _point_layer(_stations(), "EPSG:31982", with_z=True)
        adjusted = _adjust(reduced, tmp_path / "run", APPROXIMATE_LAYER=layer, STATION_FIELD="station")
        self._same(adjusted, from_file, tolerance=0.0)

    def test_in_another_crs_it_is_carried_into_the_networks(self, reduced, from_file, tmp_path):
        from tests.qgis.test_engine_runs import _feedback

        layer = _point_layer(_stations(), "EPSG:31982", with_z=False, height_field=True, carry_to="EPSG:4326")
        feedback = _feedback()
        adjusted = _adjust(
            reduced,
            tmp_path / "run",
            feedback,
            APPROXIMATE_LAYER=layer,
            STATION_FIELD="station",
            HEIGHT_FIELD="height",
        )
        # There and back through PROJ: a few nanometres, not the millimetres of a wrong CRS.
        self._same(adjusted, from_file, tolerance=1e-6)
        assert any("carried from EPSG:4326 to EPSG:31982" in info for info in feedback.infos), feedback.infos


class TestAPointLayerRefused:
    def _refused(self, reduced, tmp_path, match: str, **source) -> None:
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException, match=match):
            _adjust(reduced, tmp_path / "run", **source)

    def test_without_the_field_naming_the_stations(self, reduced, tmp_path):
        layer = _point_layer(_stations(), "EPSG:31982", with_z=True)
        self._refused(reduced, tmp_path, "Field naming each station: Name the field", APPROXIMATE_LAYER=layer)

    def test_without_heights(self, reduced, tmp_path):
        layer = _point_layer(_stations(), "EPSG:31982", with_z=False)
        self._refused(
            reduced, tmp_path, "have no Z. Name the field", APPROXIMATE_LAYER=layer, STATION_FIELD="station"
        )

    def test_with_a_station_twice(self, reduced, tmp_path):
        stations = _stations()
        layer = _point_layer({**stations, "4": stations["1"]}, "EPSG:31982", with_z=True)
        layer.startEditing()
        last = max(feature.id() for feature in layer.getFeatures())
        layer.changeAttributeValue(last, 0, 1)
        assert layer.commitChanges()
        self._refused(
            reduced, tmp_path, "Station '1' appears twice", APPROXIMATE_LAYER=layer, STATION_FIELD="station"
        )

    def test_with_the_file_as_well(self, reduced, tmp_path):
        approximate = tmp_path / "approximate.json"
        approximate.write_text(json.dumps(_stations()), encoding="utf-8")
        layer = _point_layer(_stations(), "EPSG:31982", with_z=True)
        self._refused(
            reduced,
            tmp_path,
            "'Approximate coordinates' and 'Approximate coordinates, as a point layer of the project'",
            APPROXIMATE=str(approximate),
            APPROXIMATE_LAYER=layer,
            STATION_FIELD="station",
        )


    @pytest.mark.parametrize(
        ("change", "match"),
        [
            ("name", "Feature 1 of 'stations' has no station name"),
            ("geometry", "Station '1' in 'stations' has no position"),
            ("points", "Station '1' in 'stations' is 2 points"),
            ("height", "The height of station '1' in 'stations' is not a number: 'about 100'"),
        ],
    )
    def test_a_station_it_cannot_place(self, reduced, tmp_path, change, match):
        """Each refused by the station it is about, before anything is adjusted."""
        from qgis.core import QgsFeature, QgsGeometry, QgsPoint, QgsVectorLayer

        layer = QgsVectorLayer(
            "MultiPointZ?crs=EPSG:31982&field=station:string&field=height:string", "stations", "memory"
        )
        features = []
        for name, (easting, northing, up) in _stations().items():
            feature = QgsFeature(layer.fields())
            feature.setAttributes([name, str(up)])
            feature.setGeometry(QgsGeometry(QgsPoint(easting, northing, up)))
            features.append(feature)
        first = features[0]
        if change == "name":
            first.setAttributes(["", first.attributes()[1]])
        elif change == "geometry":
            first.setGeometry(QgsGeometry())
        elif change == "points":
            first.setGeometry(QgsGeometry.fromWkt("MultiPointZ ((500000 7000000 100), (500001 7000000 100))"))
        else:
            first.setAttributes([first.attributes()[0], "about 100"])
        assert layer.dataProvider().addFeatures(features)
        self._refused(
            reduced, tmp_path, match, APPROXIMATE_LAYER=layer, STATION_FIELD="station", HEIGHT_FIELD="height"
        )


class TestDynAdjustInputFromLayers:
    """FR-320 end to end: observations and stations held in the project's layers, written for DynAdjust.

    RD-01 twice through *Import field book*, *Generalised pre-processing*,
    *Classical network* and DynAdjust stopped before running: once from its
    files, once from a table layer and a point layer. DynAdjust's input must not
    tell them apart. In three dimensions, because DynAdjust has no measurement
    type for a horizontal distance; with the geoid undulation, because the
    heights are orthometric on projected coordinates.
    """

    @staticmethod
    def _job(
        directory: Path, monkeypatch, *, book: dict, stations: dict, dimension: int = 1, **extra
    ) -> tuple[Path, list[str]]:
        """The job's folder, and what the run said."""
        from qgis.core import QgsApplication, QgsProcessingContext

        from geocomp.algorithms.engines import dynadjust_adjust
        from tests.qgis.test_engine_runs import _feedback, _NeverDetected

        directory.mkdir()
        readings = _run(
            "geocomp:totalstation_import_fieldbook",
            {**book, **TOTAL_STATION, "OUTPUT_READINGS": str(directory / "readings.json")},
        )["OUTPUT_READINGS"]
        reduced = _run(
            "geocomp:totalstation_preprocess",
            {
                "READINGS": readings,
                "APPLY_ATMOSPHERIC": False,
                "OUTPUT_REDUCED": str(directory / "reduced.json"),
            },
        )["OUTPUT_REDUCED"]
        network = _run(
            "geocomp:totalstation_network",
            {
                "REDUCTIONS": reduced,
                **stations,
                "DIMENSION": dimension,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(directory / "network.json"),
            },
        )["OUTPUT_NETWORK"]
        monkeypatch.setattr(dynadjust_adjust, "dynadjust_engine", lambda directory=None: _NeverDetected())
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geocomp:analysis_dynadjust_adjust"
        ).create({})
        results, ok = algorithm.run(
            {
                "NETWORK": network,
                **({"GEOID_UNDULATION": -4.0} | extra),
                "FRAME": "SIRGAS2000",
                "EPOCH": 2000.4,
                "STOP_BEFORE_RUNNING": True,
                "OUTPUT_WORK_DIR": str(directory / "job"),
            },
            QgsProcessingContext(),
            feedback := _feedback(),
            catchExceptions=False,
        )
        assert ok
        return Path(results["OUTPUT_WORK_DIR"]), feedback.infos

    def test_dynadjust_is_given_the_same_input(self, tmp_path, monkeypatch):
        from geocomp.engines.dynadjust.engine import MANIFEST

        approximate = tmp_path / "approximate.json"
        approximate.write_text(json.dumps(_stations()), encoding="utf-8")
        from_files, _infos = self._job(
            tmp_path / "files",
            monkeypatch,
            book={"SOURCE": str(rd01.RAW)},
            stations={"APPROXIMATE": str(approximate)},
        )
        from_layers, infos = self._job(
            tmp_path / "layers",
            monkeypatch,
            book={"SOURCE_LAYER": _layer(_csv_rows(rd01.RAW), rd01.RAW.name, typed=True)},
            stations={
                "APPROXIMATE_LAYER": _point_layer(_stations(), "EPSG:31982", with_z=True),
                "STATION_FIELD": "station",
            },
        )
        jobs = (from_files, from_layers)
        manifests = [json.loads((job / MANIFEST).read_text(encoding="utf-8")) for job in jobs]
        assert manifests[0]["network"]["observations"]
        assert manifests[0]["network"]["observations"] == manifests[1]["network"]["observations"]
        assert manifests[0]["network"]["stations"] == manifests[1]["network"]["stations"]
        for name in ("station_file", "measurement_file"):
            files = [
                (job / manifest[name]).read_text(encoding="utf-8")
                for job, manifest in zip(jobs, manifests, strict=True)
            ]
            assert files[0] == files[1], name
        stations = (from_layers / manifests[1]["station_file"]).read_text(encoding="utf-8")
        # Latitude and longitude, not an easting in XAxis; h = H + N, with N = -4 m.
        assert stations.count("<Type>LLH</Type>") == 3 and "<Type>XYZ</Type>" not in stations
        assert "<Height>96.2500</Height>" in stations
        # Station 3's direction set of one is reported, and leaving it out changes nothing.
        assert [skip[0] for skip in manifests[1]["skipped"]] == ["3-dir-1"]
        assert "The heights of 3 station(s) are made ellipsoidal with N = -4.000 m." in infos

    @staticmethod
    def _files(tmp_path: Path) -> dict:
        approximate = tmp_path / "approximate.json"
        approximate.write_text(json.dumps(_stations()), encoding="utf-8")
        return {"book": {"SOURCE": str(rd01.RAW)}, "stations": {"APPROXIMATE": str(approximate)}}

    def test_a_plane_network_is_refused_for_its_horizontal_distances(self, tmp_path, monkeypatch):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException, match="have no DynAdjust equivalent"):
            self._job(tmp_path / "run", monkeypatch, dimension=0, **self._files(tmp_path))

    def test_its_orthometric_heights_need_the_undulation(self, tmp_path, monkeypatch):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException, match="in a projected CRS, the geoid undulation N"):
            self._job(tmp_path / "run", monkeypatch, GEOID_UNDULATION=None, **self._files(tmp_path))

    def test_a_grid_and_an_undulation_are_refused(self, tmp_path, monkeypatch):
        from qgis.core import QgsProcessingException

        grid = tmp_path / "geoid.gsb"
        grid.write_bytes(b"NUM_OREC")
        with pytest.raises(QgsProcessingException, match="geoid grid and a geoid undulation were both given"):
            self._job(tmp_path / "run", monkeypatch, GEOID_GRID=str(grid), **self._files(tmp_path))

    @pytest.mark.parametrize(
        ("crs", "central_meridian", "false_northing"),
        [
            ("EPSG:31982", -51.0, 10_000_000.0),
            ("EPSG:31983", -45.0, 10_000_000.0),
            ("EPSG:31976", -51.0, 0.0),
        ],
    )
    def test_the_projection_is_read_from_the_crs(self, crs, central_meridian, false_northing):
        """SIRGAS 2000 / UTM 22S, 23S and 22N, as QGIS's projection database names them."""
        import math

        from geocomp.algorithms.projection import projection_of_crs

        projection = projection_of_crs(crs)
        assert math.degrees(projection.central_meridian) == pytest.approx(central_meridian)
        assert projection.false_northing == false_northing
        assert projection.scale_factor == 0.9996
        assert projection.ellipsoid.name == "GRS80"

    @pytest.mark.parametrize("crs", ["EPSG:4326", "EPSG:3857", "EPSG:32722", "not a CRS"])
    def test_a_crs_it_cannot_invert_is_none(self, crs):
        """Geographic, not Transverse Mercator, not on GRS80 (WGS 84 / UTM 22S), and unknown."""
        from geocomp.algorithms.projection import projection_of_crs

        assert projection_of_crs(crs) is None
