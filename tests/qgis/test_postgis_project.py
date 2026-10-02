# SPDX-License-Identifier: GPL-2.0-or-later
"""PostGIS projects through QGIS: connections, the store algorithm, the mode switches (P11).

``specs/17`` section 4: a PostGIS store is reached through the QGIS connection
registry, *so GeoComp inherits the user's existing connections and credentials
handling rather than asking again*. Here the connection is saved in QGIS the way
a user saves one, with its login in a QGIS authentication configuration rather
than in the connection itself, and every assertion goes through it.

Needs a PostgreSQL server with PostGIS, named by ``GEOCOMP_TEST_POSTGRES`` as a
libpq connection string, and ``psycopg2`` in the Python QGIS runs; skips with
that reason otherwise. The ``test`` workflow's QGIS job provides both.
"""

from __future__ import annotations

import json
import os
import uuid

import pytest

from tests.test_project_store import reference  # noqa: F401 -- the fixture

pytestmark = pytest.mark.qgis

DSN = os.environ.get("GEOCOMP_TEST_POSTGRES", "")
CONNECTION = "geocomp-test-p11"
EXPORT = "geocomp:project_export_postgis"
IMPORT = "geocomp:project_import_postgis"
STORE = "geocomp:project_store"

try:
    import psycopg2
    from psycopg2.extensions import parse_dsn
except ImportError:  # pragma: no cover - depends on the environment
    psycopg2 = None


@pytest.fixture(autouse=True, scope="module")
def _registered(geocomp_provider):
    if not DSN or psycopg2 is None:
        pytest.skip(
            "needs a PostgreSQL server with PostGIS: set GEOCOMP_TEST_POSTGRES and "
            "install psycopg2 into QGIS's Python"
        )
    return geocomp_provider


@pytest.fixture(scope="module")
def password():
    return parse_dsn(DSN).get("password", "")


@pytest.fixture(scope="module")
def saved_connection(qgis_app, _registered):
    """A PostgreSQL connection saved in QGIS, its login in an authentication configuration."""
    from qgis.core import (
        QgsApplication,
        QgsAuthMethodConfig,
        QgsDataSourceUri,
        QgsProviderRegistry,
    )

    parts = parse_dsn(DSN)
    manager = QgsApplication.authManager()
    if not manager.masterPasswordIsSet():
        assert manager.setMasterPassword("master-for-tests", True)
    config = QgsAuthMethodConfig()
    config.setName("geocomp test database")
    config.setMethod("Basic")
    config.setConfig("username", parts.get("user", ""))
    config.setConfig("password", parts.get("password", ""))
    stored = manager.storeAuthenticationConfig(config)
    assert stored[0] if isinstance(stored, tuple) else stored

    uri = QgsDataSourceUri()
    uri.setConnection(
        parts.get("host", "localhost"),
        parts.get("port", "5432"),
        parts.get("dbname", "postgres"),
        "",
        "",
        QgsDataSourceUri.SslMode.SslDisable,
        config.id(),
    )
    metadata = QgsProviderRegistry.instance().providerMetadata("postgres")
    metadata.saveConnection(metadata.createConnection(uri.uri(False), {}), CONNECTION)
    yield CONNECTION
    metadata.deleteConnection(CONNECTION)


@pytest.fixture
def schema():
    name = "gc_qgis_" + uuid.uuid4().hex[:12]
    yield name
    connection = psycopg2.connect(DSN)
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE %s",
            (name + "%",),
        )
        for (found,) in cursor.fetchall():
            cursor.execute(f'DROP SCHEMA "{found}" CASCADE')
    connection.close()


@pytest.fixture
def project_file(tmp_path, reference):  # noqa: F811 -- the imported fixture
    """A GeoPackage holding RD-03's levelling loop and its solution."""
    from geocomp.io.store import open_store

    project, solution, network = reference

    path = tmp_path / "project.gpkg"
    with open_store(path, create=True) as store:
        store.write(project)
        store.write_solution(solution)
    return path, project, solution, network


class Recorder:
    def __init__(self):
        from qgis.core import QgsProcessingFeedback

        lines: list[str] = []

        class _Feedback(QgsProcessingFeedback):
            def pushInfo(self, text):  # noqa: N802 -- the Qt interface
                lines.append(text)

            def pushWarning(self, text):  # noqa: N802
                lines.append(text)

            def reportError(self, text, fatal=False):  # noqa: N802
                lines.append(text)

        self.lines = lines
        self.feedback = _Feedback()


def _run(algorithm_id: str, parameters: dict) -> tuple[dict, Recorder]:
    from qgis.core import QgsApplication, QgsProcessingContext

    recorder = Recorder()
    algorithm = QgsApplication.processingRegistry().algorithmById(algorithm_id)
    assert algorithm is not None, f"{algorithm_id} is not registered"
    results, ok = algorithm.create({}).run(
        parameters, QgsProcessingContext(), recorder.feedback, catchExceptions=False
    )
    assert ok
    return results, recorder


class TestTheConnectionRegistry:
    def test_the_saved_connection_is_offered(self, saved_connection):
        from geocomp.services.postgis import connection_names

        assert saved_connection in connection_names()

    def test_a_store_opens_with_qgiss_login_and_is_named_without_it(
        self, saved_connection, schema, password
    ):
        from geocomp.services.postgis import open_database_store

        with open_database_store(saved_connection, schema, create=True) as store:
            assert store.location == f"{saved_connection} / {schema}"
            assert password not in store.location

    def test_an_unknown_connection_is_refused_by_name(self, saved_connection, schema):
        from geocomp.core.errors import DataError
        from geocomp.services.postgis import open_database_store

        with pytest.raises(DataError) as caught:
            open_database_store("no-such-connection", schema)
        assert caught.value.code == "data.postgis_connection_unknown"
        assert saved_connection in str(caught.value)


class TestModeSwitching:
    def test_export_then_import_loses_nothing(self, saved_connection, schema, project_file, tmp_path):
        from geocomp.io.store import differences, open_store

        path, *_ = project_file
        exported, log_out = _run(
            EXPORT, {"SOURCE": str(path), "DATABASE": saved_connection, "SCHEMA": schema}
        )
        back = tmp_path / "back.gpkg"
        imported, log_in = _run(
            IMPORT, {"DATABASE": saved_connection, "SCHEMA": schema, "OUTPUT": str(back)}
        )
        assert exported["ROWS"] == imported["ROWS"] > 0
        assert any("identical" in line for line in log_out.lines + log_in.lines)
        with open_store(path) as a, open_store(back) as b:
            assert differences(a, b) == []

    def test_no_password_reaches_the_log_or_the_copy(
        self, saved_connection, schema, project_file, tmp_path, password
    ):
        """NFR-010, end to end: the login stays in QGIS's authentication store."""
        from qgis.core import QgsSettings

        assert password and password not in saved_connection, (
            "the test database needs a password, distinct from the connection's name, "
            "for this to mean anything"
        )
        path, *_ = project_file
        _, log_out = _run(
            EXPORT, {"SOURCE": str(path), "DATABASE": saved_connection, "SCHEMA": schema}
        )
        back = tmp_path / "back.gpkg"
        results, log_in = _run(
            IMPORT, {"DATABASE": saved_connection, "SCHEMA": schema, "OUTPUT": str(back)}
        )
        written = {
            "the log": "\n".join(log_out.lines + log_in.lines),
            "the results": json.dumps(results, default=str),
            "the imported GeoPackage": back.read_bytes().decode("latin-1"),
            "the QGIS settings": "\n".join(
                f"{key}={QgsSettings().value(key)}" for key in QgsSettings().allKeys()
            ),
        }
        leaks = [where for where, text in written.items() if password in text]
        assert not leaks, f"the password reached {leaks}"

    def test_exporting_over_a_project_is_refused(self, saved_connection, schema, project_file):
        from qgis.core import QgsProcessingException

        path, *_ = project_file
        _run(EXPORT, {"SOURCE": str(path), "DATABASE": saved_connection, "SCHEMA": schema})
        with pytest.raises(QgsProcessingException) as caught:
            _run(EXPORT, {"SOURCE": str(path), "DATABASE": saved_connection, "SCHEMA": schema})
        assert schema in str(caught.value)


class TestSavingToTheDatabase:
    def test_the_store_algorithm_writes_a_postgis_project(
        self, saved_connection, schema, project_file, tmp_path
    ):
        from geocomp.services.postgis import open_database_store

        _, _, solution, network = project_file
        network_path = tmp_path / "network.json"
        network_path.write_text(json.dumps(network.to_dict()), encoding="utf-8")
        solution_path = tmp_path / "solution.json"
        solution_path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
        results, _ = _run(
            STORE,
            {
                "DATABASE": saved_connection,
                "SCHEMA": schema,
                "NETWORK": str(network_path),
                "SOLUTION": str(solution_path),
            },
        )
        assert results["DATABASE"] == f"{saved_connection} / {schema}"
        with open_database_store(saved_connection, schema) as store:
            assert [s.id for s in store.read_solutions()] == [solution.id]
            assert network.id in store.read().networks

    def test_a_file_and_a_database_together_are_refused(
        self, saved_connection, schema, project_file, tmp_path
    ):
        from qgis.core import QgsProcessingException

        _, _, solution, _ = project_file
        solution_path = tmp_path / "solution.json"
        solution_path.write_text(json.dumps(solution.to_dict()), encoding="utf-8")
        with pytest.raises(QgsProcessingException):
            _run(
                STORE,
                {
                    "STORE": str(tmp_path / "also.gpkg"),
                    "DATABASE": saved_connection,
                    "SCHEMA": schema,
                    "SOLUTION": str(solution_path),
                },
            )
