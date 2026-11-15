# SPDX-License-Identifier: GPL-2.0-or-later
"""The job file and the chains a window runs (FR-011, FR-013; ``specs/17`` section 6).

The job file is the record and the results are not: a job reopens exactly as it
was typed, a result is indexed with a fingerprint of the inputs that produced
it, and a save that fails leaves the previous file.
"""

from __future__ import annotations

import json

import pytest

from geocomp.core.errors import StorageError, ValidationError
from geocomp.jobs import (
    JOB_KIND,
    JOB_SUFFIX,
    JOB_VERSION,
    CellKind,
    Chain,
    ChainStep,
    Column,
    InputFile,
    Job,
    Ref,
    TypedTable,
    fingerprint,
    resolve,
)

COLUMNS = {
    "book": (Column("station", CellKind.NAME), Column("angle", CellKind.ANGLE)),
    "points": (Column("name", CellKind.NAME), Column("easting", CellKind.NUMBER)),
}


def job() -> Job:
    made = Job(
        "total_station",
        {name: TypedTable(columns) for name, columns in COLUMNS.items()},
        name="Praça",
        crs="EPSG:31982",
        entry={"angle_typing": "dms"},
    )
    made.tables["book"].paste(0, "station", "E1\t87 31 15,50\nE2\t0 00 00")
    made.parameters("traverse")["KIND"] = 1
    made.state("traverse")["route"] = ["E1", "E2"]
    return made


class TestRoundTrip:
    def test_a_job_reopens_as_it_was_typed(self, tmp_path):
        original = job()
        path = original.save(tmp_path / "praca.gcjob")
        reopened = Job.load(path, COLUMNS)
        assert reopened.to_dict() == original.to_dict()
        assert reopened.tables["book"].cell(0, "angle") == "87 31 15,50"
        assert reopened.name == "Praça"
        assert reopened.path == path

    def test_the_suffix_is_added_when_it_is_missing(self, tmp_path):
        path = job().save(tmp_path / "praca")
        assert path.name == "praca" + JOB_SUFFIX
        assert path.is_file()

    def test_the_file_states_its_kind_and_version(self, tmp_path):
        payload = json.loads(job().save(tmp_path / "a.gcjob").read_text(encoding="utf-8"))
        assert payload["kind"] == JOB_KIND
        assert payload["version"] == JOB_VERSION

    def test_non_ascii_names_are_stored_as_themselves(self, tmp_path):
        assert "Praça" in job().save(tmp_path / "a.gcjob").read_text(encoding="utf-8")

    def test_a_table_is_filled_by_column_key(self):
        """A job saved before a column was added, or with its columns in
        another order, still opens."""
        payload = job().to_dict()
        payload["tables"]["book"] = {
            "columns": ["angle", "retired", "station"],
            "rows": [["1 02 03", "x", "E9"]],
        }
        reopened = Job.from_dict(payload, COLUMNS)
        assert reopened.tables["book"].row(0) == ("E9", "1 02 03")

    def test_a_table_the_file_lacks_opens_empty(self):
        payload = job().to_dict()
        del payload["tables"]["points"]
        assert Job.from_dict(payload, COLUMNS).tables["points"].row_count == 0


class TestRefusals:
    def test_a_document_of_another_kind(self, tmp_path):
        other = tmp_path / "readings.json"
        other.write_text('{"kind": "geocomp.readings", "version": 1}', encoding="utf-8")
        with pytest.raises(ValidationError) as refusal:
            Job.load(other, COLUMNS)
        assert refusal.value.code == "validation.job_file_not_a_job"
        assert refusal.value.context["path"] == str(other)

    def test_a_job_a_later_geocomp_saved(self):
        payload = job().to_dict()
        payload["version"] = JOB_VERSION + 1
        with pytest.raises(ValidationError) as refusal:
            Job.from_dict(payload, COLUMNS, source="later.gcjob")
        assert refusal.value.code == "validation.job_file_newer"

    def test_a_file_that_is_not_json(self, tmp_path):
        broken = tmp_path / "broken.gcjob"
        broken.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValidationError) as refusal:
            Job.load(broken, COLUMNS)
        assert refusal.value.code == "validation.job_file_unreadable"

    def test_a_file_that_is_not_there(self, tmp_path):
        with pytest.raises(ValidationError) as refusal:
            Job.load(tmp_path / "absent.gcjob", COLUMNS)
        assert refusal.value.code == "validation.job_file_unreadable"

    def test_a_job_never_saved_has_nowhere_to_be_saved_again(self):
        with pytest.raises(StorageError) as refusal:
            job().save()
        assert refusal.value.code == "storage.job_not_saved"


class TestSaving:
    def test_a_failed_save_leaves_the_previous_job(self, tmp_path, monkeypatch):
        original = job()
        path = original.save(tmp_path / "a.gcjob")
        before = path.read_text(encoding="utf-8")
        original.tables["book"].set_cell(0, "station", "changed")

        def refuse(*_args, **_kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("os.replace", refuse)
        with pytest.raises(StorageError):
            original.save()
        assert path.read_text(encoding="utf-8") == before
        assert [entry.name for entry in tmp_path.iterdir()] == ["a.gcjob"]

    def test_the_results_lie_beside_the_file(self, tmp_path):
        made = job()
        assert made.results_directory is None
        made.save(tmp_path / "praca.gcjob")
        assert made.results_directory == tmp_path / "praca_results"


class TestResults:
    def test_a_result_is_current_only_for_the_inputs_that_produced_it(self):
        made = job()
        assert made.result("traverse") is None
        assert not made.is_current("traverse", "abc")
        made.record_result(
            "traverse", fingerprint="abc", outputs={"traverse.OUTPUT_HTML": "traverse/report.html"},
            scalars={"LINEAR_MISCLOSURE": 0.004}, log=["Closes to 1:9000."],
        )
        assert made.is_current("traverse", "abc")
        assert not made.is_current("traverse", "abd")
        assert made.result("traverse")["scalars"] == {"LINEAR_MISCLOSURE": 0.004}

    def test_the_index_is_saved_with_the_job(self, tmp_path):
        made = job()
        made.record_result("traverse", fingerprint="abc", outputs={}, scalars={"N": 1})
        reopened = Job.load(made.save(tmp_path / "a.gcjob"), COLUMNS)
        assert reopened.is_current("traverse", "abc")
        assert reopened.parameters("traverse") == {"KIND": 1}
        assert reopened.state("traverse") == {"route": ["E1", "E2"]}


def chain(angle: str = "87 31 15") -> Chain:
    return Chain(
        (
            ChainStep(
                key="import",
                algorithm="geocomp:totalstation_import_fieldbook",
                parameters={
                    "SOURCE": InputFile("book.csv", f"station,angle\nE1,{angle}\n"),
                    "PROFILES": None,
                },
                outputs={"OUTPUT_READINGS": "readings.json"},
            ),
            ChainStep(
                key="preprocess",
                algorithm="geocomp:totalstation_preprocess",
                parameters={"READINGS": Ref("import", "OUTPUT_READINGS"), "TEMPERATURE": 20.0},
                outputs={"OUTPUT_REDUCED": "reduced.json"},
            ),
        )
    )


class TestChains:
    def test_every_file_is_placed_before_anything_runs(self, tmp_path):
        first, second = resolve(chain(), tmp_path)
        assert first.parameters["SOURCE"] == str(tmp_path / "import" / "book.csv")
        assert (tmp_path / "import" / "book.csv").read_text(encoding="utf-8").startswith("station,angle")
        assert first.outputs == {"OUTPUT_READINGS": tmp_path / "import" / "readings.json"}
        assert first.parameters["OUTPUT_READINGS"] == str(tmp_path / "import" / "readings.json")
        assert second.parameters["READINGS"] == first.parameters["OUTPUT_READINGS"]
        assert second.parameters["TEMPERATURE"] == 20.0

    def test_a_parameter_not_given_is_left_to_the_algorithm(self, tmp_path):
        first, _second = resolve(chain(), tmp_path)
        assert "PROFILES" not in first.parameters

    def test_the_algorithms_are_named_in_order(self):
        assert chain().algorithms == (
            "geocomp:totalstation_import_fieldbook",
            "geocomp:totalstation_preprocess",
        )

    def test_the_fingerprint_is_of_the_typed_data_and_the_options(self):
        assert chain().fingerprint() == chain().fingerprint()
        assert chain("87 31 16").fingerprint() != chain().fingerprint()

    def test_a_reference_to_nothing_is_a_programming_error(self, tmp_path):
        broken = Chain((ChainStep(key="a", algorithm="x", parameters={"IN": Ref("absent", "OUT")}),))
        with pytest.raises(KeyError):
            resolve(broken, tmp_path)

    def test_a_fingerprint_does_not_depend_on_the_order_of_keys(self):
        assert fingerprint({"a": 1, "b": [1, 2]}) == fingerprint({"b": [1, 2], "a": 1})
