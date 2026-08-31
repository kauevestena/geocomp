# SPDX-License-Identifier: GPL-2.0-or-later
"""The engine abstraction, and the acquisition rules ADR-0003 sets.

``specs/03-architecture.md`` section 3.3, ``specs/07-engine-dynadjust.md``
sections 2 and 7, FR-300 to FR-306.

Tier 1: nothing here needs QGIS or an engine. That is deliberate rather than
convenient. The security-critical half of the manager -- verify the digest,
refuse an archive that would write outside its directory, refuse one carrying a
symlink -- must be exercised in every CI job, not only the one job that has
QGIS. The single part that genuinely needs Qt, downloading through the user's
proxy, is an injected callable, so what these tests run is what ships minus the
socket.
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys
import zipfile
from pathlib import Path

import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.engines.base import (
    EngineAbsentError,
    EngineRun,
    EngineVersion,
    discover,
    require,
    run_process,
)
from geocomp.engines.manager import (
    PINNED,
    EngineRelease,
    digest,
    extract,
    install,
    install_pinned,
    installation_root,
    locate,
    verify,
)


def make_zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    return path


def sha_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# -- discovery: an explicit path wins, and never falls back ---------------


def test_a_configured_path_wins(tmp_path: Path) -> None:
    """ADR-0003 rule 4: a user who set a path had a reason."""
    program = tmp_path / "dnaimport"
    program.write_text("#!/bin/sh\n", encoding="utf-8")
    found, source = discover("dnaimport", configured=program)
    assert (found, source) == (program, "configured")


def test_a_configured_directory_is_searched_for_the_program(tmp_path: Path) -> None:
    (tmp_path / "dnaadjust").write_text("#!/bin/sh\n", encoding="utf-8")
    found, source = discover("dnaadjust", configured=tmp_path)
    assert found == tmp_path / "dnaadjust" and source == "configured"


def test_a_configured_path_that_is_missing_is_an_error_not_a_fallback(tmp_path: Path) -> None:
    """Falling back would run a different program than the one named."""
    with pytest.raises(ValidationError) as excinfo:
        discover("dnaimport", configured=tmp_path / "nowhere")
    assert excinfo.value.code == "validation.engine_path_not_found"


def test_a_managed_installation_is_found_before_the_path(tmp_path: Path) -> None:
    managed = tmp_path / "managed"
    managed.mkdir()
    (managed / "dnaimport").write_text("#!/bin/sh\n", encoding="utf-8")
    found, source = discover("dnaimport", extra_directories=[managed])
    assert found == managed / "dnaimport" and source == "managed"


def test_absence_is_reported_not_raised() -> None:
    """FR-306: the UI asks 'is this available?' and must get an answer."""
    found, source = discover("geocomp-no-such-program-exists")
    assert (found, source) == (None, "absent")


# -- graceful absence (FR-306) -------------------------------------------


def test_require_names_what_to_do_about_it() -> None:
    with pytest.raises(EngineAbsentError) as excinfo:
        require(None, engine="DynAdjust", operation="network adjustment")
    message = str(excinfo.value)
    assert "Global Settings" in message
    assert "continues to work without it" in message


def test_require_passes_a_present_engine_through(tmp_path: Path) -> None:
    version = EngineVersion(name="dnaadjust", version="1.4.0", path=tmp_path)
    assert require(version, engine="DynAdjust", operation="x") is version


def test_a_half_installed_suite_names_the_missing_program(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DynAdjust is a suite; a partial install fails halfway through a pipeline.

    ``PATH`` is emptied for the duration. Without that the test asserts
    something about the machine it runs on rather than about ``locate``: on one
    with DynAdjust installed the "missing" program is found on ``PATH`` and the
    suite is complete, which is correct behaviour and a failing test.
    """
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    (tmp_path / "dnaimport").write_text("#!/bin/sh\n", encoding="utf-8")
    status = locate("dynadjust", ["dnaimport", "dnaadjust"], extra_directories=[tmp_path])
    assert not status.available
    assert status.missing == ("dnaadjust",)
    assert "dnaimport" in status.programs


def test_a_complete_suite_is_available(tmp_path: Path) -> None:
    for program in ("dnaimport", "dnaadjust"):
        (tmp_path / program).write_text("#!/bin/sh\n", encoding="utf-8")
    status = locate("dynadjust", ["dnaimport", "dnaadjust"], extra_directories=[tmp_path])
    assert status.missing == ()
    # `available` also needs a version, which locate does not detect.
    assert status.version is None


# -- the pinned table -----------------------------------------------------


def test_a_release_cannot_be_declared_without_a_real_digest() -> None:
    """An unverifiable download is not an option this module offers."""
    with pytest.raises(ValidationError) as excinfo:
        EngineRelease(
            engine="dynadjust",
            version="1.4.0",
            platform="linux-x86_64",
            url="https://example.org/x.zip",
            sha256="not-a-digest",
        )
    assert excinfo.value.code == "validation.engine_release_digest_malformed"


def test_every_pinned_release_has_a_well_formed_digest() -> None:
    """Guards the table itself, however it is filled in later."""
    for release in PINNED:
        assert len(release.sha256) == 64
        assert release.url.startswith("https://")


def test_an_unpinned_engine_refuses_and_names_the_script(tmp_path: Path) -> None:
    """The refusal has to be actionable: the fix is a two-minute job."""
    with pytest.raises(ValidationError) as excinfo:
        install_pinned("dynadjust", "linux-x86_64", root=tmp_path, fetch=lambda url, path: None)
    assert excinfo.value.code == "validation.engine_release_not_pinned"
    assert "pin_engine_release.py" in str(excinfo.value)


# -- verification (ADR-0003 rule 2) --------------------------------------


def test_a_matching_digest_passes(tmp_path: Path) -> None:
    payload = b"engine bytes"
    path = tmp_path / "engine.zip"
    path.write_bytes(payload)
    assert verify(path, sha_of(payload)) == sha_of(payload)
    assert path.exists()


def test_a_mismatched_digest_deletes_the_file_and_says_both(tmp_path: Path) -> None:
    """Leaving it on disk leaves something for a less careful path to extract."""
    path = tmp_path / "engine.zip"
    path.write_bytes(b"not what was expected")
    with pytest.raises(DataError) as excinfo:
        verify(path, sha_of(b"the real thing"))
    assert excinfo.value.code == "data.engine_archive_digest_mismatch"
    assert not path.exists()
    assert excinfo.value.context["received"] != excinfo.value.context["expected"]


def test_the_digest_is_computed_in_blocks_not_all_at_once(tmp_path: Path) -> None:
    """A static engine archive is tens of megabytes inside a running QGIS."""
    path = tmp_path / "big.bin"
    payload = os.urandom(3 * 1024 * 1024 + 17)
    path.write_bytes(payload)
    assert digest(path) == sha_of(payload)


# -- extraction is not trusted either -------------------------------------


def test_a_member_escaping_the_target_is_refused(tmp_path: Path) -> None:
    """`extractall` writes wherever a member name points."""
    archive = make_zip(tmp_path / "evil.zip", {"../../escaped": b"x", "dnaimport": b"y"})
    with pytest.raises(DataError) as excinfo:
        extract(archive, tmp_path / "install")
    assert excinfo.value.code == "data.engine_archive_member_escapes"
    assert not (tmp_path.parent / "escaped").exists()


def test_an_absolute_member_is_refused(tmp_path: Path) -> None:
    archive = tmp_path / "abs.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("/etc/geocomp-owned", b"x")
    with pytest.raises(DataError) as excinfo:
        extract(archive, tmp_path / "install")
    assert excinfo.value.code == "data.engine_archive_member_escapes"


def test_nothing_is_written_before_every_member_is_checked(tmp_path: Path) -> None:
    """A malicious archive must not get a partial write in before the refusal."""
    target = tmp_path / "install"
    archive = make_zip(
        tmp_path / "mixed.zip", {"innocent": b"a", "also-fine": b"b", "../escaped": b"c"}
    )
    with pytest.raises(DataError):
        extract(archive, target)
    assert not target.exists() or list(target.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="zip symlink attributes are a Unix concern")
def test_a_symlink_member_is_refused(tmp_path: Path) -> None:
    """Its own name may be innocent while it points outside after extraction."""
    archive = tmp_path / "link.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        info = zipfile.ZipInfo("dnaimport")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        handle.writestr(info, "/etc/passwd")
    with pytest.raises(DataError) as excinfo:
        extract(archive, tmp_path / "install")
    assert excinfo.value.code == "data.engine_archive_contains_symlink"


@pytest.mark.skipif(sys.platform == "win32", reason="the mode bits are a Unix concern")
def test_extracted_programs_are_executable(tmp_path: Path) -> None:
    """A zip written on Windows carries no Unix permission bits."""
    archive = make_zip(tmp_path / "engine.zip", {"dnaimport": b"#!/bin/sh\n"})
    written = extract(archive, tmp_path / "install")
    assert written[0].stat().st_mode & stat.S_IXUSR


def test_an_archive_missing_the_programs_says_so(tmp_path: Path) -> None:
    """Better here than as 'engine not found' on a machine that just installed it."""
    archive = make_zip(tmp_path / "engine.zip", {"README.md": b"hello"})
    with pytest.raises(DataError) as excinfo:
        extract(archive, tmp_path / "install", expect=["dnaimport"])
    assert excinfo.value.code == "data.engine_archive_missing_programs"


# -- install: the order is the point --------------------------------------


def test_install_verifies_before_extracting(tmp_path: Path) -> None:
    """A tampered archive must never reach the extractor."""
    payload_path = tmp_path / "source.zip"
    make_zip(payload_path, {"dnaimport": b"#!/bin/sh\n"})
    tampered = payload_path.read_bytes()

    release = EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="linux-x86_64",
        url="https://example.org/dynadjust-linux-static.zip",
        sha256=sha_of(b"a completely different archive"),
        members=("dnaimport",),
    )

    def fetch(url: str, destination: Path) -> None:
        destination.write_bytes(tampered)

    root = tmp_path / "root"
    with pytest.raises(DataError) as excinfo:
        install(release, root=root, fetch=fetch)
    assert excinfo.value.code == "data.engine_archive_digest_mismatch"
    installed = root / "dynadjust" / "1.4.0"
    assert not installed.exists() or list(installed.iterdir()) == []


def test_install_places_the_programs_and_removes_the_archive(tmp_path: Path) -> None:
    source = make_zip(tmp_path / "source.zip", {"dnaimport": b"#!/bin/sh\n", "dnaadjust": b"x"})
    payload = source.read_bytes()
    release = EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="linux-x86_64",
        url="https://example.org/dynadjust-linux-static.zip",
        sha256=sha_of(payload),
        members=("dnaimport", "dnaadjust"),
    )
    root = tmp_path / "root"
    where = install(release, root=root, fetch=lambda u, p: p.write_bytes(payload))

    assert (where / "dnaimport").exists() and (where / "dnaadjust").exists()
    assert not list(root.glob("dynadjust/*.zip"))
    # And the installed programs are discoverable by the same call the plugin uses.
    status = locate("dynadjust", ["dnaimport", "dnaadjust"], extra_directories=[where])
    assert status.missing == ()


def test_a_fetcher_that_writes_nothing_is_reported(tmp_path: Path) -> None:
    release = EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="linux-x86_64",
        url="https://example.org/x.zip",
        sha256=sha_of(b""),
    )
    with pytest.raises(DataError) as excinfo:
        install(release, root=tmp_path, fetch=lambda u, p: None)
    assert excinfo.value.code == "data.engine_download_produced_nothing"


def test_engines_install_inside_the_qgis_profile(tmp_path: Path) -> None:
    """ADR-0003 rule 3: no elevated privileges, and removal is clean."""
    root = installation_root(tmp_path)
    assert root.is_relative_to(tmp_path)
    assert "engines" in root.parts


# -- running a process (FR-036, FR-304) -----------------------------------


def test_a_run_records_everything_needed_to_reproduce_it(tmp_path: Path) -> None:
    run = run_process(
        [sys.executable, "-c", "print('hello from the engine')"],
        work_dir=tmp_path,
        program="fake-engine",
    )
    assert run.ok
    assert "hello from the engine" in run.stdout
    assert run.exit_code == 0
    assert run.seconds >= 0.0
    assert run.work_dir == tmp_path
    assert run.command[0] == sys.executable


def test_a_failing_run_keeps_the_engines_own_message(tmp_path: Path) -> None:
    """FR-305: an exit code is not a diagnostic."""
    run = run_process(
        [sys.executable, "-c", "import sys; sys.stderr.write('bad station name at line 12\\n'); sys.exit(3)"],
        work_dir=tmp_path,
    )
    assert not run.ok
    assert run.exit_code == 3
    assert "bad station name at line 12" in run.diagnostic


def test_a_diagnostic_falls_back_to_stdout(tmp_path: Path) -> None:
    """Engines that report errors on stdout are common; an empty box is worse."""
    run = run_process(
        [sys.executable, "-c", "print('- Error: cannot read file'); raise SystemExit(1)"],
        work_dir=tmp_path,
    )
    assert "cannot read file" in run.diagnostic


def test_progress_is_reported_line_by_line_while_it_runs(tmp_path: Path) -> None:
    """A bar that jumps from zero to done is not a progress bar."""
    seen: list[str] = []
    run_process(
        [sys.executable, "-c", "import sys\nfor i in range(5): print(f'step {i}'); sys.stdout.flush()"],
        work_dir=tmp_path,
        on_progress=seen.append,
    )
    assert seen == [f"step {i}" for i in range(5)]


def test_a_timeout_is_distinguished_from_a_failure(tmp_path: Path) -> None:
    """They mean different things and send the user to different places."""
    run = run_process(
        [sys.executable, "-c", "import time\nprint('working', flush=True)\ntime.sleep(30)"],
        work_dir=tmp_path,
        timeout=1.0,
    )
    assert run.timed_out
    assert not run.ok
    assert run.seconds < 25.0


def test_the_work_directory_is_kept_for_reproduction(tmp_path: Path) -> None:
    """FR-955: a user must be able to attach the inputs to a bug report."""
    work = tmp_path / "run-1"
    run_process([sys.executable, "-c", "open('generated.txt','w').write('x')"], work_dir=work)
    assert (work / "generated.txt").read_text(encoding="utf-8") == "x"


def test_provenance_truncates_a_huge_log_but_keeps_both_ends(tmp_path: Path) -> None:
    """The version banner is at the top and the error is at the bottom."""
    run = EngineRun(
        program="dnaadjust",
        command=("dnaadjust", "network"),
        exit_code=1,
        stdout="\n".join(f"line {i}" for i in range(500)),
        stderr="",
        seconds=1.0,
        work_dir=tmp_path,
    )
    recorded = run.to_dict()["stdout"]
    assert "line 0" in recorded
    assert "line 499" in recorded
    assert "lines omitted" in recorded
    assert len(recorded) < len(run.stdout)


def test_a_short_log_is_not_truncated(tmp_path: Path) -> None:
    run = EngineRun(
        program="dnaimport",
        command=("dnaimport",),
        exit_code=0,
        stdout="three\nshort\nlines",
        stderr="",
        seconds=0.1,
        work_dir=tmp_path,
    )
    assert run.to_dict()["stdout"] == "three\nshort\nlines"


def test_the_version_travels_with_the_run(tmp_path: Path) -> None:
    """FR-302: a silently updated engine is a silently changed result."""
    version = EngineVersion(
        name="dnaadjust", version="1.4.0", path=tmp_path / "dnaadjust", tested=False
    )
    run = run_process([sys.executable, "-c", "pass"], work_dir=tmp_path, version=version)
    assert run.to_dict()["version"]["version"] == "1.4.0"
    assert run.to_dict()["version"]["tested"] is False
