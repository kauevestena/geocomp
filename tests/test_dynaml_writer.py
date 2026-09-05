# SPDX-License-Identifier: GPL-2.0-or-later
"""Writing DynaML from a GeoComp network (FR-320, FR-104, FR-105).

``specs/07-engine-dynadjust.md`` section 4. Tier 1: no QGIS and no engine, so
the format conventions are checked wherever Python runs. That the files are
*accepted by dnaimport* is checked separately, in the engine tier, because only
that can prove it -- but the conventions below are where the errors actually
are, and they are checkable here.

The formats were confirmed against upstream at commit ``5cdb897``: Appendix B of
the User's Guide, which specifies the DNA fields column by column, plus its
statement that DynaML's elements follow the DNA definitions.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from geocomp.core.errors import ValidationError
from geocomp.core.geodesy import ELLIPSOIDS, transverse_mercator, utm_parameters
from geocomp.core.models import (
    Cluster,
    ClusterKind,
    ConstraintMode,
    ConstraintSpec,
    CoordinateSystem,
    HeightType,
    Network,
    Observation,
    ObservationType,
    Position,
    Station,
)
from geocomp.core.uncertainty import Covariance, Quantity
from geocomp.core.units import Unit
from geocomp.engines.dynadjust.dynaml import (
    MAX_STATION_NAME,
    station_names,
    write_measurement_file,
    write_station_file,
)
from geocomp.engines.dynadjust.formats import (
    hp_to_radians,
    parse_epoch,
    radians_to_hp,
    radians_to_seconds,
    seconds_to_radians,
)
from geocomp.engines.dynadjust.read_dynaml import read_station_file

METRE, RADIAN = Unit.METRE, Unit.RADIAN
FRAME, EPOCH = "GDA2020", "01.01.2020"


def cartesian(x: float, y: float, z: float, *, exact: bool = False) -> Position:
    make = (
        (lambda v: Quantity.exact(v, METRE))
        if exact
        else (lambda v: Quantity.from_std_dev(v, 0.5, METRE))
    )
    return Position(
        values=(make(x), make(y), make(z)),
        system=CoordinateSystem.CARTESIAN,
        crs="EPSG:7842",
        height_type=HeightType.ELLIPSOIDAL,
    )


def gnss_network(*, cluster_size: int = 1) -> Network:
    """A small cartesian GNSS network, one cluster of *cluster_size* baselines."""
    truth = {
        "BASE": (3760000.0, -4400000.0, -2700000.0),
        "PT01": (3760150.0, -4400090.0, -2700040.0),
        "PT02": (3760080.0, -4400200.0, -2700110.0),
    }
    network = Network(id="gnss", crs="EPSG:7842")
    network.add_station(
        Station(
            id="BASE",
            approx_position=cartesian(*truth["BASE"]),
            constraint=ConstraintSpec(
                mode=ConstraintMode.FIXED,
                components=frozenset({"x", "y", "z"}),
                position=cartesian(*truth["BASE"], exact=True),
            ),
        )
    )
    for name in ("PT01", "PT02"):
        network.add_station(Station(id=name, approx_position=cartesian(*truth[name])))

    pairs = [("BASE", "PT01"), ("BASE", "PT02")][:cluster_size]
    ids = []
    for index, (origin, target) in enumerate(pairs):
        delta = [truth[target][k] - truth[origin][k] for k in range(3)]
        observation = Observation(
            id=f"BL{index}",
            type=ObservationType.GNSS_BASELINE,
            stations=(origin, target),
            values=tuple(Quantity.from_std_dev(delta[k], 0.01, METRE) for k in range(3)),
            cluster_id="C0",
        )
        network.add_observation(observation)
        ids.append(observation.id)

    size = 3 * len(ids)
    matrix = np.eye(size) * 1.0e-4
    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = 1.0e-5
    labels = tuple(f"{o}.{c}" for o in ids for c in ("dx", "dy", "dz"))
    network.add_cluster(
        Cluster(
            id="C0",
            kind=ClusterKind.GNSS_BASELINE,
            observation_ids=tuple(ids),
            covariance=Covariance(matrix=matrix, labels=labels, units=(METRE,) * size),
        )
    )
    network.require_valid()
    return network


def parse(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


# -- HP notation, the convention most likely to be got wrong --------------


def test_hp_matches_upstreams_own_sample_value() -> None:
    """91.41495 is 91d 41' 49.5", not 91.41495 degrees.

    The value is lifted from `sampleData/urban-networkmsr.xml`, whose adjustment
    output reports it as `91 41 49.5010` -- so this is checked against the
    engine's own reading of its own file, not against our arithmetic.
    """
    radians = hp_to_radians("91.41495000")
    assert math.degrees(radians) == pytest.approx(91 + 41 / 60 + 49.5 / 3600)


def test_hp_round_trips_exactly() -> None:
    for text in ("91.41495000", "0.0000100", "359.5959999", "-0.2010331"):
        assert hp_to_radians(radians_to_hp(hp_to_radians(text))) == pytest.approx(
            hp_to_radians(text), abs=1e-12
        )


def test_a_negative_vertical_angle_keeps_its_sign_on_the_degrees() -> None:
    """The Guide's own example writes -0 20 10.331; negating each part loses it."""
    assert radians_to_hp(hp_to_radians("-0.2010331")).startswith("-0.")
    assert math.degrees(hp_to_radians("-0.2010331")) < 0


def test_hp_does_not_silently_accept_decimal_degrees() -> None:
    """91.75 as HP would be 91d 75' -- impossible, and it says so."""
    with pytest.raises(ValidationError) as excinfo:
        hp_to_radians("91.75")
    assert excinfo.value.code == "validation.hp_angle_minutes_out_of_range"


def test_seconds_carry_into_minutes_rather_than_becoming_sixty() -> None:
    """59.999999 seconds must not be written as '60.00000'."""
    almost = math.radians(10 + 59 / 60 + 59.9999999 / 3600)
    written = radians_to_hp(almost)
    assert "60" not in written.split(".")[1][2:4]
    assert hp_to_radians(written) == pytest.approx(almost, abs=1e-9)


def test_an_angular_standard_deviation_is_in_seconds_of_arc() -> None:
    """Guide Table B.4: the StdDev column is seconds, while Value is HP."""
    assert float(radians_to_seconds(math.radians(20.0 / 3600.0))) == pytest.approx(20.0)
    assert seconds_to_radians("20") == pytest.approx(math.radians(20.0 / 3600.0))


def test_an_epoch_is_read_as_day_month_year() -> None:
    """Read as ISO, 01.03.2010 is a different date and a datum shift."""
    assert parse_epoch("01.03.2010") == (1, 3, 2010)
    with pytest.raises(ValidationError):
        parse_epoch("2010-03-01")


# -- station names and constraints ----------------------------------------


def test_ordinary_names_are_left_alone(tmp_path: Path) -> None:
    network = gnss_network()
    document = write_station_file(
        network, tmp_path / "s.xml", frame=FRAME, epoch=EPOCH
    )
    assert document.renamed == {}


def test_a_name_too_long_is_mapped_not_truncated() -> None:
    """Two stations truncated to the same 20 characters become one station."""
    network = Network(id="n", crs="EPSG:7842")
    long_a = "STATION-" + "A" * 30
    long_b = "STATION-" + "A" * 29 + "B"
    for name in (long_a, long_b):
        network.add_station(Station(id=name, approx_position=cartesian(0, 0, 0)))

    names = station_names(network)
    assert names[long_a] != names[long_b]
    assert all(len(v) <= MAX_STATION_NAME for v in names.values())


def test_the_original_name_is_kept_in_the_description(tmp_path: Path) -> None:
    """So the user never sees a renamed station (specs/07 4.3 rule 3)."""
    network = Network(id="n", crs="EPSG:7842")
    long_name = "A-VERY-LONG-STATION-IDENTIFIER-INDEED"
    network.add_station(Station(id=long_name, approx_position=cartesian(1, 2, 3)))
    write_station_file(network, tmp_path / "s.xml", frame=FRAME, epoch=EPOCH)
    text = (tmp_path / "s.xml").read_text(encoding="utf-8")
    assert long_name in text


def test_constraints_use_the_positions_own_component_names(tmp_path: Path) -> None:
    """A cartesian position names them x, y, z; a fixed triple reports free."""
    network = gnss_network()
    write_station_file(network, tmp_path / "s.xml", frame=FRAME, epoch=EPOCH)
    root = parse(tmp_path / "s.xml")
    constraints = {
        station.findtext("Name"): station.findtext("Constraints")
        for station in root.findall("DnaStation")
    }
    assert constraints["BASE"] == "CCC"
    assert constraints["PT01"] == "FFF"


def test_a_weighted_constraint_is_refused_rather_than_approximated(tmp_path: Path) -> None:
    """DynAdjust holds a component exactly or not at all (specs/07 4.3 rule 4).

    Writing it as C would turn a stated uncertainty into an assertion of
    certainty -- holding exactly what the user asked to be held loosely.
    """
    network = gnss_network()
    station = network.stations["PT01"]
    network.stations["PT01"] = Station(
        id="PT01",
        approx_position=station.approx_position,
        constraint=ConstraintSpec(
            mode=ConstraintMode.WEIGHTED,
            components=frozenset({"x", "y", "z"}),
            position=cartesian(0, 0, 0),
            covariance=Covariance(np.eye(3) * 1e-4, ("x", "y", "z"), (METRE,) * 3),
        ),
    )
    with pytest.raises(ValidationError) as excinfo:
        write_station_file(network, tmp_path / "s.xml", frame=FRAME, epoch=EPOCH)
    assert excinfo.value.code == "validation.dynadjust_cannot_express_weighted_constraint"
    assert "in-house core" in str(excinfo.value)


# -- frame and epoch are never inferred (FR-105) --------------------------


def test_frame_and_epoch_are_written_on_the_root(tmp_path: Path) -> None:
    write_station_file(gnss_network(), tmp_path / "s.xml", frame=FRAME, epoch=EPOCH)
    root = parse(tmp_path / "s.xml")
    assert root.get("referenceframe") == FRAME
    assert root.get("epoch") == EPOCH


def test_a_missing_frame_is_refused(tmp_path: Path) -> None:
    """A run whose frame GeoComp inferred is a datum shift in the residuals."""
    with pytest.raises(ValidationError) as excinfo:
        write_station_file(gnss_network(), tmp_path / "s.xml", frame="", epoch=EPOCH)
    assert excinfo.value.code == "validation.dynadjust_frame_or_epoch_missing"


# -- FR-104: clusters stay clusters ---------------------------------------


def test_a_single_baseline_carries_its_full_covariance(tmp_path: Path) -> None:
    """The single most important correctness rule of the writer."""
    network = gnss_network(cluster_size=1)
    write_measurement_file(network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH)
    root = parse(tmp_path / "m.xml")

    measurements = root.findall("DnaMeasurement")
    assert len(measurements) == 1
    assert measurements[0].findtext("Type") == "G"

    baseline = measurements[0].find("GPSBaseline")
    for name in ("SigmaXX", "SigmaXY", "SigmaXZ", "SigmaYY", "SigmaYZ", "SigmaZZ"):
        assert baseline.findtext(name) is not None
    assert float(baseline.findtext("SigmaXX")) == pytest.approx(1.0e-4)
    # The off-diagonal is real and is written, not dropped.
    assert float(baseline.findtext("SigmaXY")) == pytest.approx(1.0e-5)


def test_a_baseline_cluster_carries_the_between_baseline_covariance(tmp_path: Path) -> None:
    """The correlation between baselines of one session is real and helps.

    Written as the repeated GPSCovariance blocks the schema allows. Dropping
    them would leave a block-diagonal matrix, which reports an uncertainty
    that is wrong in the direction nobody checks: too small.
    """
    network = gnss_network(cluster_size=2)
    write_measurement_file(network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH)
    root = parse(tmp_path / "m.xml")

    measurement = root.find("DnaMeasurement")
    assert measurement.findtext("Type") == "X"
    assert measurement.findtext("Total") == "2"

    baselines = measurement.findall("GPSBaseline")
    assert len(baselines) == 2
    # The first member carries its covariance with the second; the second has
    # none after it, which is what the upper-triangular convention means.
    assert len(baselines[0].findall("GPSCovariance")) == 1
    assert len(baselines[1].findall("GPSCovariance")) == 0

    block = baselines[0].find("GPSCovariance")
    assert float(block.findtext("m11")) == pytest.approx(1.0e-5)


def test_the_covariance_survives_to_full_double_precision(tmp_path: Path) -> None:
    """specs/07 acceptance criterion 2."""
    network = gnss_network(cluster_size=1)
    exact = 1.234567890123456e-07
    cluster = network.clusters["C0"]
    # Diagonal, so the matrix stays positive semi-definite -- an earlier draft
    # set one element of a correlated matrix and Covariance correctly refused
    # the indefinite result.
    matrix = np.eye(cluster.covariance.size) * exact
    network.clusters["C0"] = Cluster(
        id="C0",
        kind=cluster.kind,
        observation_ids=cluster.observation_ids,
        covariance=Covariance(matrix, cluster.covariance.labels, cluster.covariance.units),
    )
    write_measurement_file(network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH)
    root = parse(tmp_path / "m.xml")
    written = float(root.find("DnaMeasurement/GPSBaseline").findtext("SigmaXX"))
    assert written == exact


# -- types DynAdjust does not have are reported, never dropped ------------


def test_an_unmappable_observation_is_reported(tmp_path: Path) -> None:
    """A gravity observation vanishing is a change the user cannot see."""
    network = gnss_network()
    network.add_observation(
        Observation(
            id="G1",
            type=ObservationType.GRAVITY,
            stations=("BASE",),
            values=(Quantity.from_std_dev(9.78e-5, 1e-8, Unit.ACCELERATION),),
        )
    )
    document = write_measurement_file(
        network, tmp_path / "m.xml", frame=FRAME, epoch=EPOCH
    )
    assert [o for o, _ in document.skipped] == ["G1"]
    assert "no measurement type" in document.skipped[0][1]


def test_the_counts_report_what_was_written(tmp_path: Path) -> None:
    document = write_measurement_file(
        gnss_network(cluster_size=2), tmp_path / "m.xml", frame=FRAME, epoch=EPOCH
    )
    assert document.counts == {"X": 1}
    assert document.to_dict()["measurement_counts"] == {"X": 1}


# -- the model defect this writer uncovered -------------------------------


def test_a_gnss_baseline_cluster_can_be_constructed_at_all() -> None:
    """It could not be, until phase P6, and FR-104 is what it exists for.

    ``Cluster.__post_init__`` required one covariance row per *observation*
    while the adjustment's ``build_weight_matrix`` required one per
    *component*. For scalar members those agree; for a GNSS baseline, which has
    three components, they contradict -- so the constructor refused the 6x6 the
    adjustment needs and accepted the 2x2 the adjustment rejects. The headline
    case of FR-104 had no representable input, and no test had built a
    multi-component cluster to notice.
    """
    labels = tuple(f"{o}.{c}" for o in ("BL0", "BL1") for c in ("dx", "dy", "dz"))
    cluster = Cluster(
        id="C",
        kind=ClusterKind.GNSS_BASELINE,
        observation_ids=("BL0", "BL1"),
        covariance=Covariance(np.eye(6) * 1e-4, labels, (METRE,) * 6),
    )
    assert cluster.covariance.size == 6


def test_a_covariance_that_is_not_a_whole_multiple_is_still_refused() -> None:
    with pytest.raises(Exception) as excinfo:
        Cluster(
            id="C",
            kind=ClusterKind.GNSS_BASELINE,
            observation_ids=("a", "b", "c"),
            covariance=Covariance(np.eye(4), tuple("wxyz"), (METRE,) * 4),
        )
    assert "cluster_size_mismatch" in str(excinfo.value)


def test_the_network_checks_the_exact_component_count() -> None:
    """The divisibility check cannot see the members; the network can."""
    network = gnss_network(cluster_size=2)
    cluster = network.clusters["C0"]
    # A 3x3 is a whole multiple of two members only in the sense that it is not;
    # use 12, which divides by 2 but is not the 6 the members actually need.
    network.clusters["C0"] = Cluster(
        id="C0",
        kind=cluster.kind,
        observation_ids=cluster.observation_ids,
        covariance=Covariance(
            np.eye(12) * 1e-4, tuple(f"c{i}" for i in range(12)), (METRE,) * 12
        ),
    )
    problems = network.validate()
    assert any("12-component covariance" in p for p in problems)


class TestTheStationCoordinateType:
    """``<Type>`` is a declaration about the three numbers beside it.

    It was a single constant ``"XYZ"`` until a network that was not cartesian
    was put through the writer. The reasoning recorded for the constant -- that
    GeoComp's frames "are cartesian or projected already" -- was the defect: a
    projected easting is not a geocentric X, and a geodetic latitude in radians
    is not one either.
    """

    @staticmethod
    def _station(system: CoordinateSystem, values: tuple[float, float, float]) -> Network:
        units = (
            (Unit.RADIAN, Unit.RADIAN, Unit.METRE)
            if system is CoordinateSystem.GEODETIC
            else (Unit.METRE, Unit.METRE, Unit.METRE)
        )
        network = Network(id="n", crs="GDA2020")
        network.stations["A"] = Station(
            id="A",
            approx_position=Position(
                values=tuple(
                    Quantity.exact(value, unit)
                    for value, unit in zip(values, units, strict=True)
                ),  # type: ignore[arg-type]
                system=system,
                crs="GDA2020",
                height_type=HeightType.ELLIPSOIDAL,
            ),
        )
        return network

    def _write(self, network: Network, tmp_path: Path) -> str:
        path = tmp_path / "stn.xml"
        write_station_file(network, path, frame="GDA2020", epoch="01.01.2020")
        return path.read_text(encoding="utf-8")

    def test_a_cartesian_position_is_written_as_xyz(self, tmp_path: Path) -> None:
        network = self._station(
            CoordinateSystem.CARTESIAN, (-4251956.4559, 2869868.5766, -3777753.7504)
        )
        text = self._write(network, tmp_path)
        assert "<Type>XYZ</Type>" in text
        assert "<XAxis>-4251956.4559</XAxis>" in text

    def test_a_geodetic_position_is_written_as_llh_in_hp_notation(
        self, tmp_path: Path
    ) -> None:
        """Which is what upstream's own station files use, and what the reader
        reads back. Writing a latitude in radians into an ``XYZ`` slot puts the
        station 6371 km from where it belongs."""
        latitude = math.radians(-36 - 33 / 60 - 30.289906 / 3600)
        longitude = math.radians(146 + 43 / 60 + 22.017064 / 3600)
        network = self._station(CoordinateSystem.GEODETIC, (latitude, longitude, 208.3086))
        text = self._write(network, tmp_path)
        assert "<Type>LLH</Type>" in text
        assert "<XAxis>-36.3330289" in text
        assert "<YAxis>146.4322017" in text
        assert "<Height>208.3086</Height>" in text

    def test_a_geodetic_position_round_trips(self, tmp_path: Path) -> None:
        latitude, longitude = math.radians(-25.45), math.radians(-49.23)
        network = self._station(CoordinateSystem.GEODETIC, (latitude, longitude, 915.0))
        path = tmp_path / "stn.xml"
        write_station_file(network, path, frame="SIRGAS2000", epoch="01.01.2020")
        back = read_station_file(path).network.stations["A"].approx_position
        assert back.system is CoordinateSystem.GEODETIC
        assert back.values[0].value == pytest.approx(latitude, abs=1e-10)
        assert back.values[1].value == pytest.approx(longitude, abs=1e-10)
        assert back.values[2].value == pytest.approx(915.0)

    def test_a_projected_position_is_refused(self, tmp_path: Path) -> None:
        """DynaML's UTM type needs a zone and hemisphere GeoComp cannot derive,
        and every other type would put the easting somewhere it is not. A UTM
        22S station written as XYZ sits 845 km above the Earth's surface, and
        DynAdjust accepts it without complaint."""
        network = self._station(CoordinateSystem.PROJECTED, (671000.0, 7185000.0, 915.0))
        with pytest.raises(ValidationError) as excinfo:
            self._write(network, tmp_path)
        assert excinfo.value.code == "validation.dynadjust_cannot_write_projected_coordinates"
        assert excinfo.value.context["station"] == "A"
        assert excinfo.value.context["received"] == "projected"

    def test_a_station_with_no_position_still_writes(self, tmp_path: Path) -> None:
        """DynAdjust computes approximates for stations that lack them, so
        refusing here would reject networks it can adjust perfectly well."""
        network = Network(id="n", crs="GDA2020")
        network.stations["A"] = Station(id="A")
        text = self._write(network, tmp_path)
        assert "<Type>XYZ</Type>" in text
        assert "<XAxis>0.0000</XAxis>" in text


class TestAProjectedNetworkReachesDynAdjust:
    """``specs/07`` section 4.4, now that the inverse projection exists.

    A projected station used to be refused outright. It still is when nobody
    says *which* projection -- deriving a zone and a hemisphere from a CRS
    string needs a projection database, which is a different thing from
    mathematics -- but a caller that states the parameters gets an ``LLH``
    station DynAdjust accepts.

    This closes the coordinate half of the blocker behind P6's cross-validation
    criterion. The other half, that a horizontal distance has no DynAdjust
    equivalent at all (``specs/07`` section 4.2), is unaffected and still refuses.
    """

    #: SIRGAS 2000 / UTM 22S, which is what a Curitiba survey is actually in.
    PROJECTION = utm_parameters(22, southern_hemisphere=True, ellipsoid=ELLIPSOIDS["GRS80"])

    @staticmethod
    def _network(height_type: HeightType, up: float = 915.0) -> Network:
        network = Network(id="n", crs="EPSG:31982")
        network.stations["A"] = Station(
            id="A",
            approx_position=Position(
                values=(
                    Quantity.exact(670000.0, Unit.METRE),
                    Quantity.exact(7185000.0, Unit.METRE),
                    Quantity.exact(up, Unit.METRE),
                ),
                system=CoordinateSystem.PROJECTED,
                crs="EPSG:31982",
                height_type=height_type,
            ),
        )
        return network

    def _write(self, network: Network, tmp_path: Path, **kwargs) -> str:
        path = tmp_path / "stn.xml"
        write_station_file(network, path, frame="GDA2020", epoch="01.01.2020", **kwargs)
        return path.read_text(encoding="utf-8")

    def test_without_a_stated_projection_it_is_still_refused(self, tmp_path: Path) -> None:
        """The CRS string says EPSG:31982; reading a zone out of that is a
        database lookup, and guessing one puts the station in another country."""
        with pytest.raises(ValidationError) as excinfo:
            self._write(self._network(HeightType.ELLIPSOIDAL), tmp_path)
        assert excinfo.value.code == "validation.dynadjust_cannot_write_projected_coordinates"

    def test_with_one_it_is_written_as_llh(self, tmp_path: Path) -> None:
        text = self._write(
            self._network(HeightType.ELLIPSOIDAL), tmp_path, projection=self.PROJECTION
        )
        assert "<Type>LLH</Type>" in text
        # 670000 E, 7185000 N in UTM 22S is Curitiba: about 25.44 S, 49.31 W.
        latitude = hp_to_radians(text.split("<XAxis>")[1].split("</XAxis>")[0])
        longitude = hp_to_radians(text.split("<YAxis>")[1].split("</YAxis>")[0])
        assert math.degrees(latitude) == pytest.approx(-25.44, abs=0.02)
        assert math.degrees(longitude) == pytest.approx(-49.31, abs=0.02)

    def test_the_conversion_round_trips_through_the_reader(self, tmp_path: Path) -> None:
        """What the writer put in is what the reader gets out, to a micrometre."""
        network = self._network(HeightType.ELLIPSOIDAL)
        path = tmp_path / "stn.xml"
        write_station_file(
            network, path, frame="GDA2020", epoch="01.01.2020", projection=self.PROJECTION
        )
        back = read_station_file(path).network.stations["A"].approx_position
        assert back.system is CoordinateSystem.GEODETIC

        easting, northing = transverse_mercator(
            back.values[0].value, back.values[1].value, self.PROJECTION
        )
        assert easting == pytest.approx(670000.0, abs=1e-3)
        assert northing == pytest.approx(7185000.0, abs=1e-3)

    def test_an_orthometric_height_without_a_geoid_model_is_refused(
        self, tmp_path: Path
    ) -> None:
        """DynaML's LLH height is *h*. Writing *H* there is out by the undulation.

        Tens of metres in Brazil, and nothing downstream can detect it: the
        network adjusts, converges and reports a healthy variance factor with
        every station on the wrong surface.
        """
        with pytest.raises(ValidationError) as excinfo:
            self._write(
                self._network(HeightType.ORTHOMETRIC), tmp_path, projection=self.PROJECTION
            )
        assert excinfo.value.code == (
            "validation.dynadjust_orthometric_height_needs_a_geoid_model"
        )
        assert excinfo.value.context["station"] == "A"

    def test_an_orthometric_height_with_an_undulation_is_converted(
        self, tmp_path: Path
    ) -> None:
        text = self._write(
            self._network(HeightType.ORTHOMETRIC, up=915.0),
            tmp_path,
            projection=self.PROJECTION,
            undulations={"A": -4.0},
        )
        assert "<Height>911.0000</Height>" in text

    def test_a_two_dimensional_network_needs_no_geoid_model(self, tmp_path: Path) -> None:
        """``HeightType.NONE`` is a network with no height, not an unknown one.

        The conversion does not use the third component, so requiring a geoid
        undulation for it would refuse a plane network over a number that means
        nothing.
        """
        text = self._write(
            self._network(HeightType.NONE, up=0.0), tmp_path, projection=self.PROJECTION
        )
        assert "<Type>LLH</Type>" in text
        assert "<Height>0.0000</Height>" in text
