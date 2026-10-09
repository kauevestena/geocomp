# SPDX-License-Identifier: GPL-2.0-or-later
"""The GNSS tutorial, followed as its README says (P13-17).

``rnx2rtkp`` is tier 4, so each run here answers with the solution RTKLIB-EX
``2.5.1`` gave for that hour's pair, committed in ``tests/data/ggao``: the
algorithms, their logs and the closure are GeoComp's own, and the engine's
output is the real one. ``tests/test_ggao_triangle.py`` runs the engine itself
on the shipped files and holds it to the same solutions.

Writing the tutorial found three defects on the way, each fixed before it:
*Build baselines* did not close a loop (P13-14), it could not read what
*Relative — Static* wrote (P13-15), and a folder of one station's two hours was
processed as whichever hour came last (P13-16).
"""

from __future__ import annotations

import gzip
import json
import re
import shutil
from pathlib import Path

import pytest

from geocomp.resources import DATASETS_DIR, available_datasets
from tests.conftest import REPO_ROOT, requires_qgis
from tests.qgis.walkthrough import algorithm, check_names, quoted, quotes, run, steps

pytestmark = [pytest.mark.qgis, requires_qgis]

NAME = "ggao-triangle"
README = DATASETS_DIR / NAME / "README.md"
INSTALL = "geocomp:project_tutorial_dataset"
STATIC = "geocomp:gnss_relative_static"
BUILD = "geocomp:gnss_build_baselines"
RECORDED = REPO_ROOT / "tests" / "data" / "ggao"
HOURS = ("hour-00", "hour-11")
LEGS = (("GODN", "GODE"), ("GODN", "GODS"), ("GODE", "GODS"))
TOP = ("NOTICE.md", "README.es.md", "README.md", "README.pt_BR.md")
IN_EACH_HOUR = ("brdc0010.25n.gz", "gode0010.25o", "godn0010.25o", "gods0010.25o")
SUMMARY = re.compile(r"(\d+) epochs, ([\d.]+)% with resolved ambiguities")
CLOSURE = re.compile(r"closes to ([\d.]+) mm over ([\d.]+) m of baselines \(([\d.]+) ppm\)")


class _Recorded:
    """Stands in for ``RtklibEngine``: each hour's pair answered with the real engine's solution."""

    def __init__(self) -> None:
        from geocomp.engines.base import EngineVersion

        self.jobs: list = []
        self._version = EngineVersion(
            name="RTKLIB-EX", version="2.5.1", path=Path("/opt/rtklib/rnx2rtkp"), tested=True
        )

    def version(self):
        return self._version

    def run(self, job, *, work_dir, on_progress=None):
        from geocomp.engines.base import EngineRun
        from geocomp.engines.rtklib import RtklibResult
        from geocomp.engines.rtklib.read_pos import read_pos
        from geocomp.engines.rtklib.read_stat import read_status

        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        self.jobs.append(job)
        hour = Path(job.rover.obs_file).parent.name
        pair = f"{job.base.station_id}-{job.rover.station_id}".lower()
        output = work_dir / f"{job.rover.id}.pos"
        shutil.copyfile(RECORDED / hour / f"{pair}.pos", output)
        # The residual file the adapter reads the slips and the geometry from.
        status = (RECORDED / hour / f"{pair}.pos.stat.gz").read_bytes()
        config = work_dir / "rnx2rtkp.conf"
        config.write_text("", encoding="utf-8")
        run = EngineRun(
            program="rnx2rtkp",
            command=("rnx2rtkp",),
            exit_code=0,
            stdout="",
            stderr="",
            seconds=1.0,
            work_dir=work_dir,
            version=self._version,
        )
        solution = read_pos(output)
        status_file = output.with_name(f"{output.name}.stat")
        status_file.write_bytes(gzip.decompress(status))
        epochs = read_status(status_file)
        solution.geometry = {time: epoch.sightings for time, epoch in epochs.items()}
        solution.slips = {time: epoch.slips for time, epoch in epochs.items()}
        solution.rejections = {time: epoch.rejections for time, epoch in epochs.items()}
        return RtklibResult(run=run, solution=solution, config_file=config, output_file=output)


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


def _menu(algorithm_id: str) -> str:
    from geocomp.gui.menu import menu_label
    from geocomp.registry import ALGORITHMS

    spec = next(spec for spec in ALGORITHMS if spec.id == algorithm_id)
    return f"GeoComp ▸ {menu_label(spec.menu)}"


@pytest.fixture(scope="module")
def folder(tmp_path_factory) -> Path:
    results = run(
        INSTALL,
        {
            "DATASET": available_datasets().index(NAME),
            "DESTINATION": str(tmp_path_factory.mktemp("ggao")),
        },
    )
    assert results["FILE_COUNT"] == len(TOP) + len(HOURS) * len(IN_EACH_HOUR)
    return Path(results["OUTPUT_DIRECTORY"])


def _follow(folder: Path, language: str | None = None) -> dict[str, str]:
    """Steps 2 to 9, in *language* when one is given: each hour's log, every line of it."""
    from qgis.core import QgsProcessingContext

    from geocomp.services import engines
    from tests.qgis.test_engine_runs import _feedback

    root = folder.parent / f"followed-{language or 'en'}"
    logs = {}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(engines, "rtklib_engine", _Recorded)
        context = _Installed(language) if language else _Nothing()
        with context:
            for hour in HOURS:
                solutions = root / f"solutions-{hour[-2:]}"
                feedback = _feedback()
                for base, rover in LEGS:
                    # The solutions' folder is not made first: the README calls it new.
                    _run(
                        STATIC,
                        {
                            "FOLDER": str(folder / hour),
                            "BASE_STATION": base,
                            "ROVER_STATION": rover,
                            "OUTPUT_POS": str(solutions / f"{base}-{rover}.pos".lower()),
                        },
                        feedback,
                        QgsProcessingContext(),
                    )
                _run(
                    BUILD,
                    {"FOLDER": str(solutions), "OUTPUT_JSON": str(root / f"baselines-{hour}.json")},
                    feedback,
                    QgsProcessingContext(),
                )
                logs[hour] = "\n".join([*feedback.infos, *feedback.warnings])
                logs[f"{hour}.json"] = (root / f"baselines-{hour}.json").read_text(encoding="utf-8")
    return logs


def _run(algorithm_id: str, parameters: dict, feedback, context) -> None:
    ok = algorithm(algorithm_id).create({}).run(parameters, context, feedback, catchExceptions=False)[1]
    assert ok, algorithm_id


class _Nothing:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _Installed(language: str):  # noqa: N802 -- the class it hands back
    from tests.qgis.test_language import _Installed as installed

    return installed(language)


@pytest.fixture(scope="module")
def followed(folder) -> dict[str, str]:
    return _follow(folder)


def _flat(text: str) -> str:
    return " ".join(text.split())


class TestItNamesWhatTheDialogsShow:
    def test_it_has_the_nine_steps(self, readme):
        assert [step.algorithm_id for step in steps(readme)] == [
            INSTALL,
            *(STATIC,) * 3,
            BUILD,
            *(STATIC,) * 3,
            BUILD,
        ]

    def test_every_title_input_and_choice_is_the_dialogs(self, readme):
        check_names(readme)

    def test_it_says_where_each_is_in_the_menu(self, readme):
        quoted(readme, f"*{_menu(INSTALL)}*")
        for algorithm_id in (STATIC, BUILD):
            quoted(readme, f"*{_menu(algorithm_id)} ▸ {algorithm(algorithm_id).displayName()}*")

    def test_the_runs_it_names_are_the_ones_followed_here(self, readme):
        """Each processing step's folder, base and rover, in this module's order."""
        runs = [dict(step.filled) for step in steps(readme) if step.algorithm_id == STATIC]
        instance = algorithm(STATIC)
        label = {
            name: instance.parameterDefinition(name).description()
            for name in ("FOLDER", "BASE_STATION", "ROVER_STATION")
        }
        assert [
            (run[label["FOLDER"]], run[label["BASE_STATION"]], run[label["ROVER_STATION"]]) for run in runs
        ] == [(f"`{hour}`", f"`{base}`", f"`{rover}`") for hour in HOURS for base, rover in LEGS]


class TestFollowingIt:
    def test_it_installs_both_hours(self, folder):
        assert sorted(path.name for path in folder.iterdir() if path.is_file()) == sorted(
            (*TOP, f"{NAME}.qgz")
        )
        for hour in HOURS:
            assert sorted(path.name for path in (folder / hour).iterdir()) == list(IN_EACH_HOUR)

    def test_the_log_says_everything_it_quotes(self, readme, followed):
        log = _flat(followed["hour-00"] + "\n" + followed["hour-11"])
        said = quotes(readme)
        assert len(said) == 10
        for quote in said:
            assert _flat(quote) in log, quote

    def test_midnight_fixes_all_but_the_first_four_epochs_on_every_side(self, readme, followed):
        from geocomp.engines.rtklib.read_pos import read_pos

        assert SUMMARY.findall(followed["hour-00"]) == [("120", "96.7")] * 3
        for base, rover in LEGS:
            solution = read_pos(RECORDED / "hour-00" / f"{base}-{rover}.pos".lower())
            flags = [epoch.is_ambiguity_fixed for epoch in solution.epochs]
            assert flags == [False] * 4 + [True] * 116
        quoted(readme, "All but the first four epochs")
        quoted(readme, "Each of the three fixes the same share of its epochs, 96.7%")

    def test_eleven_o_clock_fixes_half_on_godns_sides_and_their_last_epoch_is_not_fixed(
        self, readme, followed
    ):
        from geocomp.engines.rtklib.read_pos import read_pos

        assert SUMMARY.findall(followed["hour-11"]) == [("120", "48.3"), ("120", "47.5"), ("120", "97.5")]
        last = {
            (base, rover): read_pos(RECORDED / "hour-11" / f"{base}-{rover}.pos".lower()).last()
            for base, rover in LEGS
        }
        assert not last["GODN", "GODE"].is_ambiguity_fixed
        assert not last["GODN", "GODS"].is_ambiguity_fixed
        assert last["GODE", "GODS"].is_ambiguity_fixed
        quoted(readme, "GODN's two sides fixed half their epochs")

    def test_the_closures_are_the_ones_it_states(self, readme, followed):
        midnight, eleven = (json.loads(followed[f"{hour}.json"])["closures"] for hour in HOURS)
        ((midnight,), (eleven,)) = (midnight, eleven)
        assert midnight["loop"] == eleven["loop"] == ["GODN", "GODE", "GODS"]
        quoted(readme, f"**The triangle closes to {midnight['magnitude_mm']:.2f} mm.**")
        quoted(readme, f"still closes to {midnight['magnitude_mm']:.2f} mm")
        quoted(readme, f"**The triangle misses by {eleven['magnitude_mm']:.2f} mm**")
        assert int(eleven["magnitude_mm"] / midnight["magnitude_mm"]) == 20
        quoted(readme, "twenty times the midnight loop")

    def test_the_float_sides_are_named_and_only_they(self, followed):
        """P13-18: a baseline is its last epoch, and *Build baselines* says when
        that epoch's ambiguities were not fixed. At midnight none; at eleven,
        GODN's two sides."""
        midnight, eleven = (json.loads(followed[f"{hour}.json"])["float"] for hour in HOURS)
        assert midnight == [] and sorted(eleven) == ["GODN-GODE", "GODN-GODS"]
        assert followed["hour-11"].count("is taken from an epoch whose ambiguities were not fixed") == 2
        assert "is taken from an epoch" not in followed["hour-00"]

    def test_the_build_counts_one_dependent_baseline(self, followed):
        assert "3 baseline(s): 2 independent, 1 dependent" in followed["hour-00"]
        assert len(CLOSURE.findall(followed["hour-00"])) == 1


@pytest.mark.parametrize("language", ("pt_BR", "es"))
class TestInEachLanguage:
    """The translations, held to GeoComp speaking their language, as the other tutorials' are."""

    def test_every_name_it_uses_is_the_dialogs(self, language):
        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        with _Installed(language):
            check_names(translated)
            quoted(translated, f"*{_menu(INSTALL)}*")
            for algorithm_id in (STATIC, BUILD):
                quoted(translated, f"*{_menu(algorithm_id)} ▸ {algorithm(algorithm_id).displayName()}*")

    def test_it_quotes_the_log_in_that_language(self, language, folder):
        translated = README.with_name(f"README.{language}.md").read_text(encoding="utf-8")
        logs = _follow(folder, language)
        log = _flat(logs["hour-00"] + "\n" + logs["hour-11"])
        said = quotes(translated)
        assert len(said) == 10
        for quote in said:
            assert _flat(quote) in log, quote
