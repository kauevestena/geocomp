# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS products over the QGIS network stack, with a login by reference (phase P10c).

``specs/08`` §5 makes two requirements of the download that only a real QGIS can
show: *downloads use the QGIS network stack* and *credentials go through the
QGIS authentication system*. The archive here is a local HTTP server in its own
process (``product_archive.py``), one of whose folders needs a Basic login; the
login is stored in QGIS's authentication database and the service names it by
its id.

Criterion 7 is asserted end to end: after a download through that login, the
password appears in no log line, manifest, cache record, services file or
setting (NFR-010). The resolution logic itself is tier 1's
(``tests/test_gnss_products.py``); the real archive is the reference
workflow's (``scripts/check_products.py``).
"""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.qgis

DOWNLOAD = "geocomp:gnss_download_products"
USER = "surveyor"
#: Distinctive, so that finding it anywhere is unambiguous.
PASSWORD = "pw-7f3a9c1e-never-written"
ORBIT = "IGS0OPSFIN_20250010000_01D_15M_ORB.SP3"
NAVIGATION = "brdc0010.25n"


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
    """The local archive's base URL; public and private copies of one day."""
    root = tmp_path_factory.mktemp("archive")
    for folder in ("public", "private"):
        day = root / folder / "2025" / "001"
        day.mkdir(parents=True)
        (day / f"{ORBIT}.gz").write_bytes(gzip.compress(b"* orbit\n", mtime=0))
        (day / f"{NAVIGATION}.gz").write_bytes(gzip.compress(b"navigation\n", mtime=0))
    server = subprocess.Popen(
        [sys.executable, str(Path(__file__).with_name("product_archive.py")), str(root), USER, PASSWORD],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        port = int(server.stdout.readline())
        yield f"http://127.0.0.1:{port}"
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.fixture(scope="module")
def login(qgis_app):
    """A Basic login in QGIS's authentication database; its id, never its password."""
    from qgis.core import QgsApplication, QgsAuthMethodConfig

    manager = QgsApplication.authManager()
    if not manager.masterPasswordIsSet():
        assert manager.setMasterPassword("master-for-tests", True)
    config = QgsAuthMethodConfig()
    config.setName("product archive")
    config.setMethod("Basic")
    config.setConfig("username", USER)
    config.setConfig("password", PASSWORD)
    stored = manager.storeAuthenticationConfig(config)
    assert stored[0] if isinstance(stored, tuple) else stored
    assert config.id()
    return config.id()


_TEMPLATES = {
    "orbit/final": "IGS0OPSFIN_{yyyy}{doy}0000_01D_15M_ORB.SP3.gz",
    "gps_navigation/broadcast": "brdc{doy}0.{yy}n.gz",
}


def _services_file(
    tmp_path: Path, archive: str, *, folder: str, service: str, authcfg: str = "", keys=tuple(_TEMPLATES)
) -> Path:
    """A services file naming one service on the local archive."""
    path = tmp_path / "services.json"
    day = f"{archive}/{folder}/{{yyyy}}/{{doy}}/"
    entry = {
        "id": service,
        "name": f"Local archive, {folder}",
        "templates": {key: [day + _TEMPLATES[key]] for key in keys},
        **({"authcfg": authcfg} if authcfg else {}),
    }
    path.write_text(json.dumps({"services": [entry]}), encoding="utf-8")
    return path


class Recorder:
    """Everything a run says, in one string to search."""

    def __init__(self):
        from qgis.core import QgsProcessingFeedback

        lines: list[str] = []

        class _Feedback(QgsProcessingFeedback):
            def pushInfo(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def pushWarning(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def reportError(self, text, fatal=False):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def pushDebugInfo(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def pushCommandInfo(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def setProgressText(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

        self.lines = lines
        self.feedback = _Feedback()

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _download(parameters: dict, settings_values: dict) -> tuple[dict, Recorder]:
    from qgis.core import QgsApplication, QgsProcessingContext

    from geocomp.services.settings_service import settings

    recorder = Recorder()
    algorithm = QgsApplication.processingRegistry().algorithmById(DOWNLOAD)
    assert algorithm is not None, "the download algorithm is not registered"
    with settings.run_overrides(settings_values):
        results, ok = algorithm.create({}).run(
            parameters, QgsProcessingContext(), recorder.feedback, catchExceptions=False
        )
    assert ok
    return results, recorder


class TestTheFetcher:
    """Three outcomes, three things for the user to do (``specs/08`` §9)."""

    def test_an_anonymous_product_is_fetched(self, qgis_app, archive):
        from geocomp.services.downloads import QgisFetcher

        url = f"{archive}/public/2025/001/{ORBIT}.gz"
        fetcher = QgisFetcher()
        assert fetcher.exists(url, "")
        assert gzip.decompress(fetcher.get(url, "")) == b"* orbit\n"

    def test_a_missing_product_is_not_found(self, qgis_app, archive):
        from geocomp.core.errors import DataError
        from geocomp.services.downloads import QgisFetcher

        url = f"{archive}/public/2025/002/{ORBIT}.gz"
        assert not QgisFetcher().exists(url, "")
        with pytest.raises(DataError) as raised:
            QgisFetcher().get(url, "")
        assert raised.value.code == "data.product_not_found"
        assert raised.value.context["product"] == f"{ORBIT}.gz"

    def test_a_server_failure_is_a_network_failure(self, qgis_app, archive):
        from geocomp.core.errors import DataError
        from geocomp.services.downloads import QgisFetcher

        with pytest.raises(DataError) as raised:
            QgisFetcher().get(f"{archive}/fail/{ORBIT}.gz", "")
        assert raised.value.code == "data.product_network_failed"
        assert raised.value.context["status"] == 500

    def test_without_the_login_the_archive_refuses_and_it_says_so(self, qgis_app, archive):
        from geocomp.core.errors import DataError
        from geocomp.services.downloads import QgisFetcher

        with pytest.raises(DataError) as raised:
            QgisFetcher().get(f"{archive}/private/2025/001/{ORBIT}.gz", "")
        assert raised.value.code == "data.product_authentication_failed"

    def test_the_login_is_applied_by_reference(self, qgis_app, archive, login):
        from geocomp.services.downloads import QgisFetcher

        data = QgisFetcher().get(f"{archive}/private/2025/001/{ORBIT}.gz", login)
        assert gzip.decompress(data) == b"* orbit\n"


class TestCriterion7NoCredentialAnywhere:
    """``specs/08`` §10 criterion 7 and NFR-010, through the whole algorithm."""

    def test_a_download_through_a_login_leaves_no_trace_of_it(self, archive, login, tmp_path):
        from qgis.core import QgsSettings

        services = _services_file(
            tmp_path, archive, folder="private", service="local-private", authcfg=login
        )
        cache = tmp_path / "cache"
        manifest = tmp_path / "manifest.json"
        copies = tmp_path / "copies"
        results, recorder = _download(
            {
                "FIRST_DAY": "2025-01-01",
                "PRODUCTS": [0, 1],
                "OUTPUT_DIRECTORY": str(copies),
                "OUTPUT_JSON": str(manifest),
            },
            {
                "gnss.product_services": "local-private",
                "gnss.service_definitions": str(services),
                "gnss.product_cache": str(cache),
            },
        )
        assert results["AVAILABLE"] == 2 and results["MISSING"] == 0
        assert (copies / ORBIT).read_bytes() == b"* orbit\n"
        assert (copies / NAVIGATION).read_bytes() == b"navigation\n"

        written = {
            "the log": recorder.text,
            "the manifest": manifest.read_text(encoding="utf-8"),
            "the services file": services.read_text(encoding="utf-8"),
            **{
                f"the cache record {path.name}": path.read_text(encoding="utf-8")
                for path in cache.rglob("*.json")
            },
            "the settings": "\n".join(
                f"{key}={QgsSettings().value(key)}" for key in QgsSettings().allKeys()
            ),
        }
        assert len([k for k in written if k.startswith("the cache record")]) == 2
        leaks = [where for where, text in written.items() if PASSWORD in text or f"{USER}:" in text]
        assert not leaks, f"the password reached {leaks}"

        # What is kept instead: the service by id, a URL without a login.
        products = json.loads(manifest.read_text(encoding="utf-8"))["products"]
        assert {p["service"] for p in products} == {"local-private"}
        assert all(p["url"].startswith(archive + "/private/") for p in products)

    def test_a_url_with_a_password_in_it_is_refused_before_any_request(self, archive, tmp_path):
        from qgis.core import QgsProcessingException

        services = tmp_path / "services.json"
        services.write_text(
            json.dumps(
                {
                    "services": [
                        {
                            "id": "careless",
                            "templates": {
                                "orbit/final": [
                                    archive.replace("http://", f"http://{USER}:{PASSWORD}@") + "/x.gz"
                                ]
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(QgsProcessingException) as raised:
            _download(
                {"FIRST_DAY": "2025-01-01", "PRODUCTS": [0]},
                {
                    "gnss.product_services": "careless",
                    "gnss.service_definitions": str(services),
                    "gnss.product_cache": str(tmp_path / "cache"),
                },
            )
        assert PASSWORD not in str(raised.value)
        assert "careless" in str(raised.value)


class TestTheAlgorithm:
    def test_check_only_downloads_nothing(self, archive, tmp_path):
        services = _services_file(tmp_path, archive, folder="public", service="local", keys=["orbit/final"])
        cache = tmp_path / "cache"
        manifest = tmp_path / "manifest.json"
        results, _ = _download(
            {
                "FIRST_DAY": "2025-01-01",
                "LAST_DAY": "2025-01-02",
                "PRODUCTS": [0],
                "CHECK_ONLY": True,
                "OUTPUT_JSON": str(manifest),
            },
            {
                "gnss.product_services": "local",
                "gnss.service_definitions": str(services),
                "gnss.product_cache": str(cache),
            },
        )
        assert results["AVAILABLE"] == 1 and results["MISSING"] == 1
        report = json.loads(manifest.read_text(encoding="utf-8"))["availability"]
        assert [entry["available"] for entry in report] == [True, False]
        assert report[0]["source"] == "local"
        assert not cache.exists() or not any(cache.rglob("*.SP3"))

    def test_an_unknown_service_is_refused_by_name(self, tmp_path):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException) as raised:
            _download(
                {"FIRST_DAY": "2025-01-01", "PRODUCTS": [0]},
                {"gnss.product_services": "nooa-ncn", "gnss.product_cache": str(tmp_path / "cache")},
            )
        assert "nooa-ncn" in str(raised.value) and "noaa-ncn" in str(raised.value)

    def test_a_range_without_a_first_day_or_folder_is_refused(self, tmp_path):
        from qgis.core import QgsProcessingException

        with pytest.raises(QgsProcessingException):
            _download({"PRODUCTS": [0]}, {"gnss.product_cache": str(tmp_path / "cache")})


class Session:
    def __init__(self, start, end, nav_files=()):
        self.start, self.end, self.nav_files = start, end, tuple(nav_files)


class TestProcessingResolvesItsProducts:
    """The processing algorithms' helper: products for the sessions' own days."""

    MORNING = (datetime(2025, 1, 1, 8), datetime(2025, 1, 1, 12))

    def _settings(self, tmp_path: Path, archive: str) -> dict:
        services = _services_file(tmp_path, archive, folder="public", service="local")
        return {
            "gnss.product_services": "local",
            "gnss.service_definitions": str(services),
            "gnss.product_cache": str(tmp_path / "cache"),
        }

    def test_a_precise_run_gets_the_orbit_of_its_day_and_records_it(self, archive, tmp_path):
        from geocomp.algorithms.gnss.common import session_products
        from geocomp.services.settings_service import settings

        recorder = Recorder()
        with settings.run_overrides(self._settings(tmp_path, archive)):
            found = session_products(
                [Session(*self.MORNING, ["own.25n"])], "precise", 1, recorder.feedback
            )
        (path,) = found.paths
        assert Path(path).name == ORBIT
        (product,) = found.provenance()["products"]
        assert product["origin"] == "download" and product["service"] == "local" and product["sha256"]

    def test_a_folder_without_navigation_gets_the_broadcast_file(self, archive, tmp_path):
        from geocomp.algorithms.gnss.common import session_products
        from geocomp.services.settings_service import settings

        recorder = Recorder()
        with settings.run_overrides(self._settings(tmp_path, archive)):
            found = session_products([Session(*self.MORNING)], "broadcast", 1, recorder.feedback)
        assert [Path(p).name for p in found.paths] == [NAVIGATION]

    def test_a_missing_product_stops_the_run_before_the_engine(self, archive, tmp_path):
        from qgis.core import QgsProcessingException

        from geocomp.algorithms.gnss.common import session_products
        from geocomp.services.settings_service import settings

        later = (datetime(2025, 1, 2, 8), datetime(2025, 1, 2, 12))
        with settings.run_overrides(self._settings(tmp_path, archive)), pytest.raises(
            QgsProcessingException
        ) as raised:
            session_products([Session(*later, ["own.25n"])], "precise", 1, Recorder().feedback)
        assert "final orbit for 2025-01-02" in str(raised.value)

    def test_without_a_service_nothing_is_downloaded(self, tmp_path):
        from qgis.core import QgsProcessingException

        from geocomp.algorithms.gnss.common import session_products
        from geocomp.services.settings_service import settings

        overrides = {"gnss.product_services": "", "gnss.product_cache": str(tmp_path / "cache")}
        with settings.run_overrides(overrides), pytest.raises(QgsProcessingException) as raised:
            session_products([Session(*self.MORNING, ["own.25n"])], "precise", 1, Recorder().feedback)
        assert "no download service" in str(raised.value)
        assert date(2025, 1, 1).isoformat() in str(raised.value)
