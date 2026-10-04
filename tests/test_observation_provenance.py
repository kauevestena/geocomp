# SPDX-License-Identifier: GPL-2.0-or-later
"""Every observation says where it came from (FR-102; specs/04 section 2.5).

An adjusted network is only as explicable as its observations: a residual that
stands out has to lead back to the line of the file it came from. Here, the
record itself, its JSON and network-document forms, and the readers that take
observations straight from a file. Each reader's provenance is checked against
the file: the line it names holds the observation's first station.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from geocomp.core.errors import DataError
from geocomp.core.models import (
    Network,
    Observation,
    ObservationSource,
    ObservationType,
    Station,
)
from geocomp.core.uncertainty import Quantity
from geocomp.core.units import Unit

DATA = Path(__file__).parent / "data"
KRUMM = DATA / "krumm" / "2D" / "Benning83_DistanceDirection_fix.dat"
DNA_STATIONS = DATA / "dynadjust" / "sample.stn"
DNA_MEASUREMENTS = DATA / "dynadjust" / "sample.msr"
DYNAML_STATIONS = DATA / "dynadjust" / "sample-stn.xml"
DYNAML_MEASUREMENTS = DATA / "dynadjust" / "sample-msr.xml"


def _distance(identifier: str = "d1", **extra) -> Observation:
    return Observation(
        id=identifier,
        type=ObservationType.HORIZONTAL_DISTANCE,
        stations=("A", "B"),
        values=(Quantity.from_std_dev(100.0, 0.002, Unit.METRE),),
        **extra,
    )


class TestTheRecord:
    def test_it_must_say_what_made_the_observation(self):
        with pytest.raises(DataError) as refused:
            ObservationSource("")
        assert refused.value.code == "data.observation_source_without_reader"

    def test_it_round_trips_through_json(self):
        source = ObservationSource("total_station", "book.csv", ("row 12", "row 13"))
        assert ObservationSource.from_dict(source.to_dict()) == source
        assert ObservationSource.from_dict({"reader": "design"}) == ObservationSource("design")

    def test_an_observation_carries_it_through_a_network_document(self):
        source = ObservationSource("dna", "survey.msr", ("line 40",))
        network = Network(id="n", crs="LOCAL")
        for name in ("A", "B"):
            network.add_station(Station(id=name, approx_position=None))
        network.add_observation(_distance(provenance=source))
        back = Network.from_dict(network.to_dict())
        assert back.observations["d1"].provenance == source

    def test_one_written_before_it_existed_reads_back_without_one(self):
        """Absent, not invented: a document older than P12c-19 has no key."""
        payload = _distance().to_dict()
        assert "provenance" not in payload
        assert Observation.from_dict(payload).provenance is None


def _lines_named(records: tuple[str, ...]) -> list[int]:
    (record,) = records
    found = re.fullmatch(r"lines? (\d+)(?:-(\d+))?", record)
    assert found, record
    first, last = int(found.group(1)), int(found.group(2) or found.group(1))
    return list(range(first, last + 1))


class TestTheReadersSayWhichLine:
    def test_krumm(self):
        from geocomp.io.krumm import read_krumm

        network = read_krumm(KRUMM).network
        text = KRUMM.read_text(encoding="utf-8", errors="replace").splitlines()
        assert network.observations
        for observation in network.observations.values():
            source = observation.provenance
            assert source.reader == "krumm" and source.file == KRUMM.name
            (line,) = _lines_named(source.records)
            assert observation.stations[0] in text[line - 1].split()

    def test_adjust(self, tmp_path):
        from geocomp.io.adjust import read_adjust
        from tests.test_adjust import SMALL, write

        path = write(tmp_path, SMALL)
        network = read_adjust(path).network
        text = path.read_text(encoding="utf-8").splitlines()
        assert network.observations
        for observation in network.observations.values():
            source = observation.provenance
            assert source.reader == "adjust" and source.file == path.name
            (line,) = _lines_named(source.records)
            # The row names the backsight first; the observation the occupied station.
            assert set(observation.stations) <= set(text[line - 1].split())

    def test_dna(self):
        from geocomp.engines.dynadjust.read_dna import read_dna

        network = read_dna(DNA_STATIONS, DNA_MEASUREMENTS).network
        text = DNA_MEASUREMENTS.read_text(encoding="utf-8", errors="replace").splitlines()
        assert network.observations
        for observation in network.observations.values():
            source = observation.provenance
            assert source.reader == "dna" and source.file == DNA_MEASUREMENTS.name
            lines = _lines_named(source.records)
            assert any(observation.stations[0] in text[line - 1] for line in lines)

    def test_dynaml(self):
        from geocomp.engines.dynadjust.read_dynaml import read_dynaml

        network = read_dynaml(DYNAML_STATIONS, DYNAML_MEASUREMENTS).network
        elements = ET.parse(DYNAML_MEASUREMENTS).getroot().findall("DnaMeasurement")
        assert network.observations
        for observation in network.observations.values():
            source = observation.provenance
            assert source.reader == "dynaml" and source.file == DYNAML_MEASUREMENTS.name
            (record,) = source.records
            ordinal = int(record.removeprefix("DnaMeasurement "))
            element = elements[ordinal - 1]
            named = {
                e.text.strip()
                for e in element.iter()
                if e.tag in ("First", "Second", "Third") and e.text
            }
            assert observation.stations[0] in named


class TestTheTotalStationChain:
    def test_each_observation_names_the_rows_it_was_reduced_from(self):
        """Both faces of the pair: two rows of the field book, holding its stations."""
        import csv

        from geocomp.core.techniques.total_station import preprocess_setup
        from geocomp.core.techniques.total_station.pipeline import to_observations
        from geocomp.io import infer_mapping, read_field_book_csv
        from tests import reference_rd01 as rd01
        from tests.test_fieldbook_import import library, rd01_header

        imported = read_field_book_csv(rd01.RAW, infer_mapping(rd01_header()), library=library())
        with rd01.RAW.open(encoding="utf-8-sig", newline="") as handle:
            table = list(csv.reader(handle))  # row n of the book is table[n - 1]
        seen = 0
        for setup in imported.setups:
            observations, _clusters = to_observations(
                preprocess_setup(setup, library()), dimension=3, source_file=rd01.RAW.name
            )
            for observation in observations:
                source = observation.provenance
                assert source.reader == "total_station" and source.file == rd01.RAW.name
                assert len(source.records) == 2
                for record in source.records:
                    row = dict(zip(table[0], table[int(record.removeprefix("row ")) - 1], strict=True))
                    # Each row names the backsight (R) and the foresight (V);
                    # "vis" says which of the two this pointing sighted.
                    sighted = row["R"] if row["vis"] == "R" else row["V"]
                    assert (row["E"], sighted) == observation.stations
                seen += 1
        assert seen


class TestTheLevellingChain:
    def test_a_line_names_the_rows_of_the_book_it_was_reduced_from(self, tmp_path):
        """Every reading of the line is in one of the runs it names, and nothing else is."""
        import csv

        import tests.reference_levelling as rd
        from geocomp.core.techniques.levelling import build_network
        from geocomp.core.techniques.levelling.line import reduce_line
        from geocomp.io.levelbook import ColumnMapping, LevelMapping, read_level_book_csv

        book = rd.balanced_line()
        rows = [["setup", "point", "kind", "reading", "distance"]]
        for setup in book.line.setups:
            for kind, sight in (("BS", setup.backsight), ("FS", setup.foresights[0])):
                reading, distance = f"{sight.reading.value:.5f}", f"{sight.distance_value:.2f}"
                rows.append([setup.id, sight.station, kind, reading, distance])
        path = tmp_path / "book.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows(rows)
        mapping = LevelMapping(
            name="m",
            columns=tuple(
                ColumnMapping(field, column=column)
                for field, column in (
                    ("setup", "setup"),
                    ("station", "point"),
                    ("sight", "kind"),
                    ("reading", "reading"),
                    ("distance", "distance"),
                )
            ),
            decimal_separator=".",
        )
        read = read_level_book_csv(path, mapping, level=rd.profile())
        (line,) = read.lines
        reduction = reduce_line(line, rd.profile())
        assert reduction.records == (f"rows 2-{len(rows)}",)

        network = build_network([reduction], [], source_file=path.name).network
        (observation,) = network.observations.values()
        assert observation.provenance == ObservationSource("levelling", "book.csv", reduction.records)

    def test_rows_are_gathered_into_runs(self):
        from geocomp.core.techniques.levelling.line import row_runs

        assert row_runs(["row 3", "row 4", "row 5", "row 9", "row 11", "row 12"]) == (
            "rows 3-5",
            "row 9",
            "rows 11-12",
        )
        assert row_runs([]) == ()


class TestTheGravimetryChain:
    def test_a_difference_names_the_lines_its_readings_were_on(self):
        """Each line named holds a reading at one of the difference's two stations."""
        from geocomp.core.instruments import ProfileLibrary
        from geocomp.core.instruments.gravimeter import GravimeterProfile
        from geocomp.core.techniques.gravimetry import (
            DriftOptions,
            ReductionOptions,
            build_gravity_network,
            reduce_readings,
        )
        from geocomp.core.uncertainty import Quantity
        from geocomp.core.units import Unit
        from geocomp.io.gravimeter_files import read_gravimeter_file

        source = DATA / "rd07" / "gsadjust" / "Test2.txt"
        loaded = read_gravimeter_file(source, source=source.name, additive_sigma=5.0e-8)
        library = ProfileLibrary()
        for instrument in loaded.instruments:
            library.add_gravimeter(
                GravimeterProfile(id=instrument, calibration_factor=Quantity.exact(1.0, Unit.DIMENSIONLESS))
            )
        network = build_gravity_network(
            reduce_readings(loaded.readings, library, ReductionOptions()),
            library,
            drift=DriftOptions(),
        ).network
        text = source.read_text(encoding="utf-8", errors="replace").splitlines()
        differences = [o for o in network.observations.values() if len(o.stations) == 2]
        assert differences
        for observation in differences:
            source_record = observation.provenance
            assert source_record.reader == "gravimetry" and source_record.file == source.name
            for record in source_record.records:
                line = text[int(record.removeprefix("line ")) - 1]
                assert any(station in line.split() for station in observation.stations), record
