# SPDX-License-Identifier: GPL-2.0-or-later
"""Six modules' reports, read in each language (specs/18 criterion 2).

The total-station tutorial from P13-34 stays covered. Levelling, gravimetry,
integration and monitoring use their committed tutorials; GNSS uses the real
comparison algorithm with a stand-in only for its external RTKLIB process.
Headings, paragraphs, note boxes and list items are compared, including inline
markup. See tests/test_report_language_guard.py for deliberate leak and data
false-positive checks and the precise limits of the prose guard.
"""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest

from tests.qgis.test_language import LANGUAGES, _catalogue, _Installed
from tests.qgis.test_tutorial import INNER, NETWORK, TUTORIAL_ALGORITHM, _network, _run
from tests.report_language import Report, retained_english

pytestmark = pytest.mark.qgis

# Deliberately English, one identical to a report label in the catalogue.
# These are configuration-file names supplied by the survey, not UI strings.
GNSS_DATA = ("Adjusted stations", "Check the observations before proceeding")


def _read(path: Path) -> Report:
    return Report(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def reports(geocomp_provider, tmp_path_factory) -> dict[str, Report]:
    """The tutorial's adjustment, reported once in each of the three languages."""
    directory = tmp_path_factory.mktemp("report-language")
    put = _run(TUTORIAL_ALGORITHM, {"DATASET": 0, "DESTINATION": str(directory)})
    installed = Path(put["OUTPUT_DIRECTORY"])
    imported = _run(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(installed / "raw_data.csv"),
            "MAPPING": str(installed / "mapping.json"),
            "PROFILES": str(installed / "profiles.json"),
            "OUTPUT_READINGS": str(installed / "readings.json"),
        },
    )
    reduced = _run(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": imported["OUTPUT_READINGS"],
            "PROFILES": str(installed / "profiles.json"),
            "OUTPUT_REDUCED": str(installed / "reduced.json"),
        },
    )
    made: dict[str, Report] = {}
    for locale in ("en", *LANGUAGES):
        path = installed / f"report-{locale}.html"
        parameters = _network(installed, reduced, f"solution-{locale}", datum=INNER, OUTPUT_HTML=str(path))
        if locale == "en":
            _run(NETWORK, parameters)
        else:
            with _Installed(locale):
                _run(NETWORK, parameters)
        made[locale] = _read(path)
    return made


@pytest.fixture(
    scope="module", params=("total_station", "levelling", "gnss", "gravimetry", "integration", "monitoring")
)
def module_reports(request, reports, geocomp_provider, tmp_path_factory):
    """A representative complete report per module, generated through Processing."""
    if request.param == "total_station":
        return reports, ()
    folder = tmp_path_factory.mktemp(f"report-{request.param}")
    return _additional_reports(request.param, folder)


def _additional_reports(module: str, folder: Path) -> tuple[dict[str, Report], tuple[str, ...]]:
    from geocomp.resources import available_datasets

    dataset = {
        "levelling": "rd04-loop",
        "gravimetry": "rd07-usgs",
        "integration": "combined-curitiba",
        "monitoring": "rd08-dam",
    }.get(module)
    if dataset:
        installed = _run(
            TUTORIAL_ALGORITHM,
            {
                "DATASET": available_datasets().index(dataset),
                "DESTINATION": str(folder),
            },
        )
        folder = Path(installed["OUTPUT_DIRECTORY"])
    # The same output paths in all languages: their names are survey data, not
    # translated text. Parse each file before the next run overwrites it.
    made = {}
    data = set(GNSS_DATA if module == "gnss" else ())
    for locale in ("en", *LANGUAGES):
        made[locale] = _read(_generate(module, folder, locale, data))
    return made, tuple(sorted(data))


def _generate(module: str, folder: Path, locale: str, data: set[str]) -> Path:
    def report(algorithm, parameters):
        with nullcontext() if locale == "en" else _Installed(locale):
            return _run(algorithm, parameters)

    path = folder / "report.html"
    if module == "levelling":
        imported = _run(
            "geocomp:levelling_import",
            {
                "BOOK": str(folder / "loop.csv"),
                "MAPPING": str(folder / "mapping.json"),
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_SETUPS": str(folder / "setups.json"),
            },
        )
        reduced = _run(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": imported["OUTPUT_SETUPS"],
                "PROFILES": str(folder / "profiles.json"),
                "OUTPUT_REDUCTIONS": str(folder / "reduced.json"),
            },
        )
        from tests.qgis.test_levelling_tutorial import _network as level_network

        report(
            "geocomp:levelling_network",
            level_network(
                folder,
                reduced,
                "BM1=100",
                "solution",
                OUTPUT_HTML=str(path),
            ),
        )
    elif module == "gravimetry":
        reduced = _run(
            "geocomp:gravimetry_preprocess",
            {
                "READINGS": str(folder / "Test2.txt"),
                "PROFILES": str(folder / "profiles.json"),
                "PRECISION_FLOOR": 0.0,
                "OUTPUT_READINGS": str(folder / "readings.json"),
            },
        )
        report(
            "geocomp:gravimetry_network",
            {
                "READINGS": reduced["OUTPUT_READINGS"],
                "KNOWN_GRAVITY": "sta1=0",
                "OUTPUT_SOLUTION": str(folder / "solution.json"),
                "OUTPUT_HTML": str(path),
            },
        )
    elif module == "integration":
        from tests.combined_network import HELD

        report(
            "geocomp:integration_gnss_total_station",
            {
                "GNSS": str(folder / "gnss.json"),
                "TOTAL_STATION": str(folder / "total-station.json"),
                "FRAME": 0,
                "FIXED_STATIONS": ",".join(HELD),
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_SOLUTION": str(folder / "solution.json"),
                "OUTPUT_HTML": str(path),
            },
        )
    elif module == "monitoring":
        from tests.qgis.test_monitoring_tutorial import _adjust, _compare

        first, second = _adjust(folder, 2025), _adjust(folder, 2026)
        # Sparse solutions also print these IDs in their station-block covariance
        # notice. They belong to the saved solutions, not the report's prose.
        data.update((first["solution"]["id"], second["solution"]["id"]))
        comparison = _run("geocomp:monitoring_compare_epochs", _compare(folder, first, second, "comparison"))
        report(
            "geocomp:monitoring_report",
            {
                "ANALYSIS": comparison["OUTPUT_ANALYSIS"],
                "OUTPUT_HTML": str(path),
            },
        )
    elif module == "gnss":
        from unittest.mock import patch

        from tests.qgis.test_configuration_comparison import _compare, _configuration
        from tests.qgis.test_engine_runs import _Rtklib

        # Only the external process is substituted; scanning, processing the
        # committed .pos result and the full report run normally, offline.
        run_folder = folder / f"run-{locale}"
        run_folder.mkdir()
        with patch("geocomp.services.engines.rtklib_engine", return_value=_Rtklib()):
            with nullcontext() if locale == "en" else _Installed(locale):
                configurations = [
                    _configuration(run_folder, name, f"pos1-elmask = {mask}\n")
                    for name, mask in zip(GNSS_DATA, (15, 25), strict=True)
                ]
                results, _, _ = _compare(run_folder, CONFIGURATIONS=configurations)
        path = Path(results["OUTPUT_HTML"])
    else:
        raise AssertionError(module)
    return path


def test_each_report_declares_its_language(module_reports):
    reports, _data = module_reports
    assert {locale: report.lang for locale, report in reports.items()} == {
        "en": "en",
        "pt_BR": "pt-BR",
        "es": "es",
    }


@pytest.mark.parametrize("locale", LANGUAGES)
def test_a_report_has_the_same_blocks_in_every_language(module_reports, locale):
    reports, _data = module_reports
    english = reports["en"]
    assert [kind for kind, _ in reports[locale].blocks] == [kind for kind, _ in english.blocks]
    assert sum(kind == "prose" for kind, _ in english.blocks) > 0


@pytest.mark.parametrize("locale", LANGUAGES)
def test_no_label_or_substantive_prose_is_left_in_english(module_reports, locale):
    reports, data = module_reports
    left = retained_english(reports["en"], reports[locale], _catalogue(locale), data=data)
    assert not left, f"still English in {locale}: {left}"


@pytest.mark.parametrize("locale", LANGUAGES)
@pytest.mark.parametrize("offset", (None, -3.0))
def test_gravity_notes_are_translated_when_displayed_without_changing_the_document(qgis_app, locale, offset):
    import copy
    from types import SimpleNamespace

    from geocomp.algorithms.gravimetry.common import report_notes
    from geocomp.core.techniques.gravimetry.network import _notes
    from geocomp.io.gravimeter_files import read_gravimeter_file
    from tests.qgis.test_gravimetry_algorithms import USGS

    loaded = read_gravimeter_file(USGS / "Test2.txt", utc_offset_hours=offset)
    # An arbitrary note from the document is survey data, even if English or
    # identical to a UI label. Only known generated acquisition notes translate.
    user_notes = ["Adjusted stations", "My notes: readings at West station were checked."]
    document = {"file_format": loaded.format.value, "notes": [*loaded.notes, *user_notes]}
    saved = copy.deepcopy(document)
    sensor = SimpleNamespace(to_mark=None, reading=SimpleNamespace(station="Adjusted stations"))
    network_notes = tuple(_notes([SimpleNamespace(tide_system="zero_tide")], [sensor]))
    english = report_notes(document, network_notes)
    assert english == [*document["notes"], *network_notes]
    with _Installed(locale):
        shown = report_notes(document, network_notes)
    assert document == saved
    assert shown[2:4] == user_notes
    assert "Adjusted stations" in shown[-1]
    assert "zero_tide" in shown[-2]
    assert ("UTC-3 h" if offset else "UTC") in shown[1]
    assert all(shown[index] != english[index] for index in (0, 1, 4, 5))


def test_the_report_language_guard_rejects_a_real_missing_paragraph_translation(qgis_app, monkeypatch):
    """Exercise Qt's actual fallback, rather than only editing already-rendered HTML."""
    import tests.qgis.test_language as languages
    from geocomp.algorithms.reporting import no_redundancy, render_document

    original = _catalogue("pt_BR")
    source = no_redundancy()
    damaged = {context: dict(messages) for context, messages in original.items()}
    del damaged["GeoCompReport"][source]
    monkeypatch.setattr(languages, "_catalogue", lambda _locale: damaged)
    english = Report(render_document("", [f"<p>{source}</p>"]))
    with _Installed("pt_BR"):
        shown = Report(render_document("", [f"<p>{no_redundancy()}</p>"]))
    # Judge against the undamaged catalogue: the defect cannot excuse itself.
    assert source in retained_english(english, shown, original)
