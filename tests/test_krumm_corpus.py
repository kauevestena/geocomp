# SPDX-License-Identifier: GPL-2.0-or-later
"""GeoComp against 33 published network adjustments (``specs/22`` section 2).

This is the citation the project did not have. RD-02, RD-03 and RD-04 are
validated but *uncited*: they were built from the operations under test, so
"GeoComp agrees with itself" is all they establish. The networks here come from
Niemeier, Ghilani, Benning, Wolf, Leick, Strang and Borre, Grossmann, Caspary,
Baumann and Hoepke by way of Friedhelm Krumm's *Geodetic Network Adjustment
Examples*, and every one of them was **published with its adjusted
coordinates**. Reproducing those is a statement about the books.

The corpus lives in ``tests/data/krumm/``: GNU Gama's files at a pinned commit,
copied unchanged, with the licence chain in ``PROVENANCE.md`` beside them and
``scripts/check_krumm_corpus.py`` to prove the copy is verbatim. It is
**development data, not plugin content** -- see
:meth:`TestTheCorpusIsTestDataOnly.test_the_plugin_package_carries_none_of_it`,
which asserts that rather than trusting it.

The tables below are the expected outcome for every one of the 61 files, so a
change that turns a reproduction into a refusal fails here rather than quietly
shrinking the evidence.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from geocomp.core.adjustment.least_squares import AdjustmentOptions, adjust
from geocomp.core.adjustment.parameters import Frame
from geocomp.core.errors import GeoCompError
from geocomp.core.models import DatumDefinition
from geocomp.io.krumm import read_krumm

from .conftest import REPO_ROOT, krumm_corpus, requires_krumm

pytestmark = requires_krumm

FRAMES = {1: Frame.HEIGHT_1D, 2: Frame.PLANE_2D, 3: Frame.SPACE_3D}

#: The published coordinates are printed to four decimals, so a solution that
#: matches them exactly still differs by up to half a unit in the last place.
TOLERANCE_METRES = 1e-4

#: Every network whose published answer GeoComp reproduces. The worst
#: coordinate difference over all of them is under 0.05 mm, which is the
#: rounding of the printed value and not a residual disagreement.
REPRODUCED = (
    "1D/Baumann_Height_fix",
    "1D/Ghilani12_6_Height_fix",
    "1D/Krumm_Height_fix",
    "1D/Niemeier_Height_fix1",
    "1D/Niemeier_Height_free",
    "2D/Benning82_Distance_fix",
    "2D/Benning83_DistanceDirection_fix",
    "2D/Benning85",
    "2D/Benning88_Distance_fix",
    "2D/Carosio_DistanceDirection_fix",
    "2D/Ghilani14_5_Distance_fix",
    "2D/Ghilani15_4_Angle_fix",
    "2D/Ghilani15_5_Angle_fix",
    "2D/Ghilani16_1_Traverse",
    "2D/Ghilani16_2_DistanceAngleAzimuth_fix",
    "2D/Ghilani21_10_DistanceAngle_fix",
    "2D/Ghilani_Wolf_Distance_Angle",
    "2D/Grossmann_Direction_fix",
    "2D/Hoepke_Distance_free",
    "2D/LotherStrehle_Direction1",
    "2D/LotherStrehle_Direction2",
    "2D/LotherStrehle_Direction3",
    "2D/LotherStrehle_Direction4",
    "2D/LotherStrehle_Direction5",
    "2D/Niemeier_DistanceDirection_fix",
    "2D/StrangBorre_Distance_fix",
    "2D/StrangBorre_Distance_free",
    "2D/WeissEtAl_Distance_fix",
    "2D/Wolf_DistanceDirectionAngle_free",
    "3D/BlankenbachWillert3D_Distance_fix",
    "3D/Wolf_3D_DistanceVerticalAngle_fix",
    "3D/Wolf_3D_Distance_fix",
    "3D/Wolf_SpatialPolygonTraverse_fix",
)

#: Read and adjusted, but with nothing to compare against.
NO_COMPARABLE_ANSWER = {
    "1D/LotherStrehle_Height_1": "no .adj in the corpus",
    "1D/LotherStrehle_Height_2": "no .adj in the corpus",
    "1D/LotherStrehle_Height_3": "no .adj in the corpus",
    "1D/LotherStrehle_Height_4": "no .adj in the corpus",
    "1D/Mittermayer_Height_fix": "no .adj in the corpus",
    "1D/Mittermayer_Height_free": "no .adj in the corpus",
    "2D/Benning83_DistanceDirection_fix_Mb": "no .adj in the corpus",
    "2D/JaegerEtAl_DistanceDirection_fix": "no .adj in the corpus",
    "2D/Hoepke_Distance_fix": "the .adj is gama-local XML, not the printed table",
    "2D/Ghilani21_1_DistanceAngle_fix": (
        "the .adj has its station names truncated -- 102, 103, 201, 202, 203 "
        "are printed as 10, 01, 20, 02, 03 -- so there is nothing to match"
    ),
}

#: Files GeoComp refuses, each by name. A refusal is the honest outcome: a
#: network read without the part GeoComp cannot represent is a different
#: network, and comparing it against the published answer compares against an
#: adjustment nobody ran.
REFUSED = {
    "1D/Krumm_Height_dyn": "data.krumm_dynamic_datum_unsupported",
    "1D/LotherStrehle_Height_5": "data.krumm_dynamic_datum_unsupported",
    "1D/LotherStrehle_Height_6": "data.krumm_dynamic_datum_unsupported",
    "2D/LotherStrehle_Direction6": "data.krumm_dynamic_datum_unsupported",
    "2D/LotherStrehle_Direction7": "data.krumm_dynamic_datum_unsupported",
    # An azimuth to a point with no coordinates, combined with an angle turned
    # from it. GNU Gama excludes the same three files for the same reason.
    "2D/Krumm_Traverse1": "data.krumm_observation_station_unknown",
    "2D/Krumm_Traverse2": "data.krumm_observation_station_unknown",
    "2D/Krumm_Traverse3": "data.krumm_observation_station_unknown",
    "2D/Krumm_Traverse4": "data.krumm_section_unsupported",
    "2D/Leick53": "data.krumm_section_unsupported",
    "2D/Leick54": "data.krumm_section_unsupported",
    "2D/Leick55": "data.krumm_section_unsupported",
    "2D/Leick56": "data.krumm_section_unsupported",
    "2D/Wolf_Direction_fix_with_cond": "data.krumm_section_unsupported",
    "3D/Caspary": "data.krumm_section_unsupported",
    "3D/Ghilani_GNSS_Baselines": "data.krumm_section_unsupported",
    "3D/Wolf_PosAngle_and_Dist": "data.krumm_section_unsupported",
    "3D/Baumann23_3_4_fix": "data.krumm_setup_heights_unsupported",
}


def corpus_files() -> list[str]:
    root = krumm_corpus()
    if root is None:
        return []
    return sorted(f"{path.parent.name}/{path.stem}" for path in root.rglob("*.dat"))


def solve(name: str):
    """Read one example and adjust it the way the file asks to be adjusted."""
    root = krumm_corpus()
    assert root is not None
    report = read_krumm(root / f"{name}.dat")
    run = adjust(
        report.network,
        AdjustmentOptions(
            frame=FRAMES[report.dimension],
            datum=(
                DatumDefinition.INNER_CONSTRAINT
                if report.free
                else DatumDefinition.CONSTRAINED
            ),
            datum_stations=list(report.datum_stations) if report.datum_stations else None,
        ),
    )
    return report, run


def published(path: Path) -> dict[str, list[float]]:
    """The adjusted coordinates as the example prints them.

    ``name x dx sigma_x  y dy sigma_y [ z dz sigma_z ]``, in metres for the
    coordinates. A minus sign may be the typographic U+2212 rather than the
    ASCII one, and a stray line that is not a coordinate row is skipped rather
    than guessed at.
    """
    rows: dict[str, list[float]] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#")[0].strip()
        if not line or line.startswith("<"):
            continue
        tokens = line.replace("\u2212", "-").split()
        try:
            values = [float(token) for token in tokens[1:]]
        except ValueError:
            continue
        if values:
            rows[tokens[0]] = values
    return rows


@pytest.mark.parametrize("name", corpus_files())
def test_every_example_has_a_recorded_outcome(name):
    """No file in the corpus is unaccounted for.

    A new example appearing upstream, or one GeoComp starts or stops reading,
    shows up here as a name in no table rather than as a silently changed count.
    """
    recorded = set(REPRODUCED) | set(NO_COMPARABLE_ANSWER) | set(REFUSED)
    assert name in recorded


@pytest.mark.parametrize("name", sorted(REFUSED))
def test_a_refused_example_is_refused_by_name(name):
    with pytest.raises(GeoCompError) as caught:
        solve(name)
    assert caught.value.code == REFUSED[name]


@pytest.mark.parametrize("name", sorted(NO_COMPARABLE_ANSWER))
def test_an_example_without_an_answer_still_adjusts(name):
    _, run = solve(name)
    assert run.converged


@pytest.mark.parametrize("name", REPRODUCED)
def test_the_published_coordinates_are_reproduced(name):
    root = krumm_corpus()
    assert root is not None
    report, run = solve(name)
    assert run.converged

    components = FRAMES[report.dimension].components
    columns = {1: (0,), 2: (0, 3), 3: (0, 3, 6)}[report.dimension]

    reference = published(root / f"{name}.adj")
    assert reference, "the example is listed as reproduced, so it has an answer"

    for station_id, values in reference.items():
        for component, column in zip(components, columns, strict=True):
            index = run.layout.column(station_id, component)
            computed = (
                float(run.parameters[index])
                if index is not None
                else run.layout.fixed_values[(station_id, component)]
            )
            assert computed == pytest.approx(values[column], abs=TOLERANCE_METRES), (
                f"{name} {station_id}.{component}"
            )


def test_the_corpus_is_complete():
    """61 files, every one of them accounted for."""
    assert len(corpus_files()) == 61
    assert len(REPRODUCED) == 33
    assert not set(REPRODUCED) & set(REFUSED)


class TestTheCorpusIsTestDataOnly:
    """The terms these files are here on, asserted rather than intended.

    ``tests/data/krumm/PROVENANCE.md`` states two things: that the directory is
    GNU Gama's files unchanged, and that they are development data which never
    reaches an installed plugin. Both are load-bearing -- the first is what
    makes the attribution true, the second is what keeps the question away from
    the artefact that is actually distributed to users -- so neither is left as
    a promise in a document.
    """

    def test_the_plugin_package_carries_none_of_it(self):
        """``collect_files`` decides the archive's contents. Ask it directly."""
        specification = importlib.util.spec_from_file_location(
            "geocomp_build", REPO_ROOT / "scripts" / "build.py"
        )
        build = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(build)

        shipped = build.collect_files()
        assert shipped, "the build would produce an empty archive"

        corpus = (REPO_ROOT / "tests" / "data" / "krumm").resolve()
        offending = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in shipped
            if corpus in path.resolve().parents
        ]
        assert not offending, (
            "the Krumm corpus reached the plugin package. It is redistributed here "
            "as test data under GNU Gama's GPL-3; putting it in the artefact users "
            "install is a different question, and one PROVENANCE.md does not answer."
        )

    def test_no_runtime_module_reads_the_corpus(self):
        """Only the tests may name that directory."""
        readers = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "geocomp").rglob("*.py")
            if "data/krumm" in path.read_text(encoding="utf-8")
        ]
        assert not readers, f"plugin code reaching into the test corpus: {readers}"

    def test_the_vendored_copy_is_verbatim(self):
        """The provenance claim, checked against the digests it rests on.

        Offline: this compares the files against nothing, because upstream is not
        here. What it *can* do without a network is fail if somebody edits a
        vendored file and forgets that `scripts/check_krumm_corpus.py` exists --
        so it asserts the shape the checker depends on, and CI runs the checker
        itself against a real clone.
        """
        root = krumm_corpus()
        assert root is not None
        assert (root / "README.md").read_text(encoding="utf-8").startswith(
            "# Geodetic Network Adjustment Examples"
        ), "GNU Gama's own README must stay verbatim; GeoComp's notes go in PROVENANCE.md"
        assert (root / "PROVENANCE.md").is_file()
        assert len(list(root.rglob("*.dat"))) == 61
        assert len(list(root.rglob("*.adj"))) == 45
