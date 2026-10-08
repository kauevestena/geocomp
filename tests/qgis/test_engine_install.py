# SPDX-License-Identifier: GPL-2.0-or-later
"""Installing an engine from the plugin, and the plugin finding it (FR-066, FR-300, FR-301; P12c-6).

``specs/21`` section 4 puts an engine manager in Global Settings. Until P12c-6
the manager's library existed and nothing in the plugin called it; nothing
looked in the folder it installed into; *Paths and engines* held no setting at
all; and RTKLIB could be found only on the system path.

Here, through the plugin's own code and the QGIS network stack:

* *Install an engine* downloads from a local server that redirects, as
  GitHub's release downloads do, verifies, installs, records and runs the
  result, and the algorithms then find it;
* an archive that does not match its pinned digest is refused, and nothing is
  installed; a failed download says so;
* the paths in Global Settings win over the installation, and one that does
  not exist is refused in words, not as a code;
* the settings window shows what is installed and opens the installer.

The engine served is a stand-in -- shell scripts that answer ``--version`` as
DynAdjust 1.4.0 does -- so these run on Linux and macOS. The real archives,
on all three systems, are ``tests/test_engine_manager_live.py``'s.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from tests.conftest import requires_qgis

pytestmark = [
    pytest.mark.qgis,
    requires_qgis,
    pytest.mark.skipif(sys.platform == "win32", reason="the stand-in engine is a set of shell scripts"),
]

INSTALL = "geocomp:project_install_engine"
PROGRAMS = (
    "dnaadjust",
    "dnadiff",
    "dnageoid",
    "dnaimport",
    "dnaplot",
    "dnareftran",
    "dnasegment",
    "dynadjust",
)
BANNER = "#!/bin/sh\necho '+ Version: 1.4.0, Release with OpenBLAS'\n"


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


def _archive(path: Path, *, banner: str = BANNER) -> bytes:
    with zipfile.ZipFile(path, "w") as handle:
        for name in PROGRAMS:
            handle.writestr(f"dynadjust-stand-in/{name}", banner)
    return path.read_bytes()


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    """A local release page: ``/redirect/<name>`` answers 302 to ``/<name>``."""
    root = tmp_path_factory.mktemp("releases")
    good = _archive(root / "dynadjust.zip")
    _archive(root / "tampered.zip", banner=BANNER + "# changed after it was vetted\n")
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).with_name("product_archive.py")), str(root), "u", "p"],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        port = int(process.stdout.readline())
        yield f"http://127.0.0.1:{port}", hashlib.sha256(good).hexdigest()
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture
def pinned(monkeypatch, server, tmp_path):
    """This machine's pin pointed at the local server, and a profile of its own."""
    from geocomp.engines import manager

    base, digest = server
    root = tmp_path / "profile" / "geocomp" / "engines"
    monkeypatch.setattr("geocomp.services.engines.engine_root", lambda: root)

    def pin(path: str, sha256: str = digest) -> None:
        release = manager.EngineRelease(
            engine="dynadjust",
            version="1.4.0",
            platform=manager.current_platform(),
            url=f"{base}{path}",
            sha256=sha256,
            members=PROGRAMS,
        )
        monkeypatch.setattr("geocomp.engines.manager.PINNED", (release,))

    pin("/redirect/dynadjust.zip")
    return root, pin


@pytest.fixture
def no_engine_on_the_path(monkeypatch, tmp_path):
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))


@pytest.fixture
def global_setting():
    from geocomp.services.settings_service import settings

    touched = []

    def put(key: str, value: str) -> None:
        touched.append(key)
        settings.set_global(key, value)

    yield put
    for key in touched:
        settings.reset_global(key)


def _install(recorder=None, *, acknowledged=True):
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    algorithm = QgsApplication.processingRegistry().algorithmById(INSTALL)
    assert algorithm is not None, "Install an engine is not registered"
    feedback = recorder.feedback if recorder is not None else QgsProcessingFeedback()
    results, ok = algorithm.create({}).run(
        {"ENGINE": 0, "ACKNOWLEDGE_LICENCE": acknowledged},
        QgsProcessingContext(),
        feedback,
        catchExceptions=False,
    )
    assert ok
    return results


class Recorder:
    def __init__(self):
        from qgis.core import QgsProcessingFeedback

        lines: list[str] = []

        class _Feedback(QgsProcessingFeedback):
            def pushInfo(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def pushWarning(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

        self.lines = lines
        self.feedback = _Feedback()

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class TestInstalling:
    def test_it_downloads_through_qgis_verifies_installs_records_and_runs_it(
        self, pinned, no_engine_on_the_path
    ):
        from geocomp.engines.manager import MANIFEST

        root, _pin = pinned
        recorder = Recorder()
        results = _install(recorder)

        assert results["OUTPUT_VERSION"] == "1.4.0"
        directory = Path(results["OUTPUT_DIRECTORY"])
        assert directory.is_relative_to(root.resolve())
        assert (directory / "dnaadjust").is_file()
        record = json.loads((root / "dynadjust" / MANIFEST).read_text(encoding="utf-8"))
        assert record["version"] == "1.4.0"
        assert "Verified against the SHA-256" in recorder.text
        assert "DynAdjust 1.4.0 runs" in recorder.text

    def test_the_algorithms_then_find_it(self, pinned, no_engine_on_the_path):
        from geocomp.services.engines import dynadjust_engine, engine_status

        results = _install()
        found = dynadjust_engine().detect()
        assert found is not None
        assert found.path.parent == Path(results["OUTPUT_DIRECTORY"])
        (dynadjust,) = [e for e in engine_status() if e.name == "DynAdjust"]
        assert dynadjust.version is not None and dynadjust.version.path == found.path

    def test_an_archive_that_does_not_match_is_refused_and_nothing_installed(self, pinned):
        from qgis.core import QgsProcessingException

        from geocomp.engines.manager import installed

        root, pin = pinned
        pin("/redirect/tampered.zip")
        with pytest.raises(QgsProcessingException) as caught:
            _install()
        assert "is not the one GeoComp was tested with" in str(caught.value)
        assert installed("dynadjust", root) is None
        assert not [path for path in root.rglob("*") if path.is_file()]

    def test_a_failed_download_says_so(self, pinned):
        from qgis.core import QgsProcessingException

        _root, pin = pinned
        pin("/no-such-release.zip")
        with pytest.raises(QgsProcessingException) as caught:
            _install()
        assert "could not be downloaded" in str(caught.value)
        assert "404" in str(caught.value)

    def test_a_platform_with_no_pin_is_told_what_to_do(self, pinned, monkeypatch):
        from qgis.core import QgsProcessingException

        monkeypatch.setattr("geocomp.engines.manager.PINNED", ())
        with pytest.raises(QgsProcessingException) as caught:
            _install()
        assert "no verified release" in str(caught.value)
        assert "Global Settings" in str(caught.value)


class TestTheLicenceAcknowledgement:
    """DynAdjust is another party's program under its own licence; a person who
    installs it says they know."""

    def test_it_is_a_tick_box_that_starts_unticked(self):
        from qgis.core import QgsApplication, QgsProcessingParameterBoolean

        algorithm = QgsApplication.processingRegistry().algorithmById(INSTALL)
        definition = algorithm.parameterDefinition("ACKNOWLEDGE_LICENCE")
        assert isinstance(definition, QgsProcessingParameterBoolean)
        assert definition.defaultValue() is False
        assert "separate program under its own licence" in definition.description()

    def test_without_it_nothing_is_downloaded_or_installed(self, pinned, no_engine_on_the_path):
        from qgis.core import QgsProcessingException

        from geocomp.engines.manager import installed

        root, _pin = pinned
        recorder = Recorder()
        with pytest.raises(QgsProcessingException) as caught:
            _install(recorder, acknowledged=False)
        assert not [path for path in root.rglob("*") if path.is_file()]
        assert installed("dynadjust", root) is None
        assert "Downloading" not in recorder.text

        text = str(caught.value)
        # The refusal names the box as the dialog labels it, says whose
        # program and which licence, and says nothing was fetched.
        assert "I understand that DynAdjust is a separate program under its own licence" in text
        assert "Geoscience Australia" in text and "Apache-2.0" in text
        assert "Nothing was downloaded" in text

    def test_with_it_the_install_goes_ahead_and_says_what_was_confirmed(
        self, pinned, no_engine_on_the_path
    ):
        recorder = Recorder()
        results = _install(recorder)
        assert results["OUTPUT_VERSION"] == "1.4.0"
        assert "You confirmed that you understand DynAdjust is a separate program" in recorder.text
        assert recorder.text.index("You confirmed") < recorder.text.index("Downloading")

    def test_the_help_says_the_same_thing_the_refusal_does(self):
        from qgis.core import QgsApplication

        algorithm = QgsApplication.processingRegistry().algorithmById(INSTALL)
        help_text = algorithm.shortHelpString()
        assert "Apache-2.0" in help_text and "does not distribute it" in help_text
        assert "https://github.com/GeoscienceAustralia/DynAdjust" in help_text


class TestTheSettings:
    def test_paths_and_engines_holds_both_paths_global_only(self):
        from geocomp.core.settings_def import Scope, settings_in_section

        declared = {d.key: d for d in settings_in_section("paths")}
        assert set(declared) == {
            "paths.dynadjust_directory",
            "paths.rtklib_program",
            "paths.working_directory",
            "paths.report_templates",
        }
        assert all(d.scopes == frozenset({Scope.GLOBAL}) for d in declared.values())

    def test_a_configured_dynadjust_directory_wins_over_the_installation(
        self, pinned, global_setting, tmp_path, no_engine_on_the_path
    ):
        import shutil

        from geocomp.services.engines import dynadjust_engine

        results = _install()
        own = tmp_path / "own-build"
        shutil.copytree(results["OUTPUT_DIRECTORY"], own)
        global_setting("paths.dynadjust_directory", str(own))
        assert dynadjust_engine().detect().path.parent == own
        # And the installer says that its installation is not the one used.
        recorder = Recorder()
        _install(recorder)
        assert "will keep using it" in recorder.text

    def test_a_configured_rtklib_program_is_the_one_found(self, global_setting, tmp_path):
        from geocomp.services.engines import rtklib_engine

        program = tmp_path / "rnx2rtkp"
        program.write_text("#!/bin/sh\n", encoding="utf-8")
        program.chmod(0o755)
        global_setting("paths.rtklib_program", str(program))
        assert rtklib_engine().locate() == (program, "configured")

    def test_a_configured_directory_that_does_not_exist_is_refused_in_words(
        self, global_setting, tmp_path
    ):
        from qgis.core import (
            QgsApplication,
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        from tests.networks import trilateration

        network = tmp_path / "network.json"
        network.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
        missing = tmp_path / "not-there"
        global_setting("paths.dynadjust_directory", str(missing))
        algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:analysis_dynadjust_adjust")
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.create({}).run(
                {"NETWORK": str(network), "OUTPUT_SOLUTION": str(tmp_path / "s.json")},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        text = str(caught.value)
        assert str(missing) in text and "does not exist" in text
        assert "engine_path_not_found" not in text

    def test_without_dynadjust_the_refusal_offers_the_install(
        self, pinned, tmp_path, no_engine_on_the_path
    ):
        from qgis.core import (
            QgsApplication,
            QgsProcessingContext,
            QgsProcessingException,
            QgsProcessingFeedback,
        )

        from tests.networks import trilateration

        network = tmp_path / "network.json"
        network.write_text(json.dumps(trilateration().network.to_dict()), encoding="utf-8")
        algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:analysis_dynadjust_adjust")
        with pytest.raises(QgsProcessingException) as caught:
            algorithm.create({}).run(
                {"NETWORK": str(network), "OUTPUT_SOLUTION": str(tmp_path / "s.json")},
                QgsProcessingContext(),
                QgsProcessingFeedback(),
                catchExceptions=False,
            )
        assert "Install an engine" in str(caught.value)


class TestAnAbsentEngine:
    def test_is_explained_in_words_rather_than_as_a_code(self, qgis_app):
        """FR-306. RTKLIB's absence reached the GNSS algorithms' users as
        "could not complete the operation (computation.engine_not_available)"
        until P12c-6."""
        from geocomp.engines.base import EngineAbsentError, require
        from geocomp.services.messages import message_for

        with pytest.raises(EngineAbsentError) as caught:
            require(None, engine="rnx2rtkp", operation="GNSS processing")
        text = message_for(caught.value)
        assert text.startswith("rnx2rtkp is needed for GNSS processing and was not found.")
        assert "Global Settings" in text
        assert "engine_not_available" not in text


class TestTheWindow:
    def test_paths_and_engines_shows_what_is_installed_and_opens_the_installer(self, qgis_app, monkeypatch):
        from qgis.PyQt.QtWidgets import QLabel, QPushButton

        from geocomp.gui import settings_dialog

        opened = []
        monkeypatch.setattr(
            settings_dialog, "open_algorithm_dialog", lambda algorithm, parameters: opened.append(algorithm)
        )
        dialog = settings_dialog.GlobalSettingsDialog()
        try:
            assert {"paths.dynadjust_directory", "paths.rtklib_program"} <= set(dialog._editors)
            states = dialog.findChild(QLabel, "geocompEngineStates")
            assert "DynAdjust" in states.text() and "rnx2rtkp" in states.text()
            button = dialog.findChild(QPushButton, "geocompInstallDynAdjust")
            button.click()
            assert opened == [INSTALL]
        finally:
            dialog.deleteLater()
