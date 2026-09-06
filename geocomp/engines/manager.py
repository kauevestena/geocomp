# SPDX-License-Identifier: GPL-2.0-or-later
"""Acquiring, verifying and installing engine binaries (FR-300…FR-302, ADR-0003).

The proposal promises adoption in "poucos cliques". DynAdjust and RTKLIB are
compiled C++ programs distributed separately per platform, so keeping that
promise means GeoComp fetches them. ADR-0003 sets seven rules; this module is
those rules, and the two that shape the code most are:

**Verify before extracting.** A downloaded executable that has not been verified
is a security problem, not a convenience. The digest is **pinned in this
repository**, not read from beside the download. That distinction matters: a
checksum published next to a file by whoever published the file proves only that
the transfer was not corrupted. A digest committed here, reviewed when it
changes, proves the bytes are the ones somebody vetted -- which is what a
supply-chain check is for.

**Extraction is not trusted either.** A zip entry may name ``../../bin/sh``;
Python's ``extractall`` will happily write it. Every member is checked to land
inside the target directory before anything is written.

**The fetcher is injected.** Downloading has to honour the user's QGIS proxy
configuration (ADR-0003 rule 7), which needs Qt -- but verification, extraction
and installation are where the security lives, and they must be testable in the
eight CI jobs that have no QGIS. So :func:`install` takes a ``fetch`` callable.
The QGIS-backed one lives in :mod:`geocomp.services.engine_downloads`; the tests
pass a local file. What is tested is what runs, minus the socket.
"""

from __future__ import annotations

import hashlib
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError, ValidationError
from geocomp.engines.base import EngineVersion, discover

__all__ = [
    "PINNED",
    "EngineRelease",
    "Fetcher",
    "install",
    "installation_root",
    "program_directory",
    "verify",
]

#: Downloads *to* a destination path. Injected so the security-critical half of
#: this module is testable without a network or Qt.
Fetcher = Callable[[str, Path], None]

#: Read in 1 MiB blocks: a static engine archive is tens of megabytes, and
#: hashing it in one read would hold all of it in memory inside QGIS.
_BLOCK = 1024 * 1024


@dataclass(frozen=True)
class EngineRelease:
    """One pinned, verifiable engine build for one platform.

    Attributes:
        sha256: **Required.** There is deliberately no way to construct a
            release without one: an unverifiable download is not an option this
            module offers, so it cannot be reached by forgetting a field.
        members: The executables the archive is expected to contain. Checked
            after extraction, so an archive that changed shape upstream fails
            here with a clear message rather than later as "engine not found"
            on a machine where it was just installed.
    """

    engine: str
    version: str
    platform: str
    url: str
    sha256: str
    members: tuple[str, ...] = ()
    static: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or not all(c in "0123456789abcdef" for c in self.sha256.lower()):
            raise ValidationError(
                "engine_release_digest_malformed",
                engine=self.engine,
                received=self.sha256,
                expected="a 64-character hex SHA-256 digest",
            )


#: The releases this GeoComp release was built and tested against.
#:
#: Every digest here was computed from an archive actually downloaded and
#: hashed by ``scripts/pin_engine_release.py`` -- never copied from a checksum
#: published beside the download, which proves only that a transfer was not
#: corrupted, and never invented.
#:
#: **Two builds per platform where upstream offers them**, and the order
#: matters: :func:`releases_for` returns them as listed, so the self-contained
#: build comes first (ADR-0003 rule 1). The MKL builds link Intel's runtime and
#: are offered second for users who want it; ``static`` says which is which
#: rather than leaving it to be inferred from a filename.
PINNED: tuple[EngineRelease, ...] = (
    EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="linux-x86_64",
        url=(
            "https://github.com/GeoscienceAustralia/DynAdjust/releases/download/"
            "v1.4.0/dynadjust-linux-openblas-static.zip"
        ),
        sha256="5cc371bfe030815fc8b7af7d6ec00640bdd64bbeac5d0bc559296cd5b9d4f239",
        members=(
            "dnaadjust", "dnadiff", "dnageoid", "dnaimport",
            "dnaplot", "dnareftran", "dnasegment", "dynadjust",
        ),
        static=True,
        notes="OpenBLAS, statically linked. 34.9 MB.",
    ),
    EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="linux-x86_64",
        url=(
            "https://github.com/GeoscienceAustralia/DynAdjust/releases/download/"
            "v1.4.0/dynadjust-linux-mkl.zip"
        ),
        sha256="965002d8edb720732e101193fe5ad65034ed8ff9908cbc13026d06e8507b3b26",
        members=(
            "dnaadjust", "dnadiff", "dnageoid", "dnaimport",
            "dnaplot", "dnareftran", "dnasegment", "dynadjust",
        ),
        static=False,
        notes="Intel MKL. Needs the MKL runtime present.",
    ),
    EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="macos-arm64",
        url=(
            "https://github.com/GeoscienceAustralia/DynAdjust/releases/download/"
            "v1.4.0/dynadjust-macos-static.zip"
        ),
        sha256="849c665ff186aba7231bccccdf0c08dd5777d73aa4574787e5e531039db9699e",
        members=(
            "dnaadjust", "dnadiff", "dnageoid", "dnaimport",
            "dnaplot", "dnareftran", "dnasegment", "dynadjust",
        ),
        static=True,
        notes="Apple Silicon, statically linked.",
    ),
    # The Windows programs are named differently -- `adjust.exe`, not
    # `dnaadjust.exe` -- which is why `members` here does not mirror the Unix
    # rows and why the adapter carries
    # `engines.dynadjust.engine.WINDOWS_PROGRAM_NAMES`.
    EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="windows-x86_64",
        url=(
            "https://github.com/GeoscienceAustralia/DynAdjust/releases/download/"
            "v1.4.0/dynadjust-windows-openblas.zip"
        ),
        sha256="ccbae5ce395848f4525b0f52d766ad2860c98b2bed177050cb1f9c246e827a69",
        members=(
            "adjust.exe", "dnadiff.exe", "dynadjust.exe", "geoid.exe",
            "import.exe", "plot.exe", "reftran.exe", "segment.exe",
        ),
        static=False,
        notes="OpenBLAS. Ships its own DLLs beside the programs.",
    ),
    EngineRelease(
        engine="dynadjust",
        version="1.4.0",
        platform="windows-x86_64",
        url=(
            "https://github.com/GeoscienceAustralia/DynAdjust/releases/download/"
            "v1.4.0/dynadjust-windows-mkl.zip"
        ),
        sha256="f1f085a684163eb8c65fb2d7f80f24c3035b781f68e02403e0b002c7712140f4",
        members=(
            "adjust.exe", "dnadiff.exe", "dynadjust.exe", "geoid.exe",
            "import.exe", "plot.exe", "reftran.exe", "segment.exe",
        ),
        static=False,
        notes="Intel MKL. Needs the MKL runtime present.",
    ),
)


def installation_root(profile_directory: str | Path) -> Path:
    """Where managed engines live: inside the QGIS profile (ADR-0003 rule 3).

    Not a system location, so installing needs no elevated privileges and
    removing GeoComp's profile removes the engines with it.
    """
    return Path(profile_directory) / "geocomp" / "engines"


def releases_for(engine: str, platform: str) -> tuple[EngineRelease, ...]:
    return tuple(r for r in PINNED if r.engine == engine and r.platform == platform)


def digest(path: str | Path) -> str:
    """The SHA-256 of a file, hex, lower case."""
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while block := handle.read(_BLOCK):
            hasher.update(block)
    return hasher.hexdigest()


def verify(path: str | Path, expected: str) -> str:
    """Check a downloaded archive against its pinned digest (ADR-0003 rule 2).

    Raises:
        DataError: ``engine_archive_digest_mismatch``, carrying both digests.
            The downloaded file is **deleted** first: leaving an archive that
            failed verification on disk is leaving something for a later,
            less careful code path to find and extract.
    """
    path = Path(path)
    found = digest(path)
    if found != expected.lower():
        path.unlink(missing_ok=True)
        raise DataError(
            "engine_archive_digest_mismatch",
            path=str(path),
            received=found,
            expected=expected.lower(),
            note=(
                "The download does not match the digest pinned in GeoComp. It was "
                "deleted rather than kept. This is either a corrupted transfer or a "
                "file that is not the one GeoComp was tested against; retry, and if it "
                "persists, report it rather than working around it"
            ),
        )
    return found


def safe_members(archive: zipfile.ZipFile, target: Path) -> list[zipfile.ZipInfo]:
    """The archive's members, having checked every one lands inside *target*.

    ``ZipFile.extractall`` writes wherever a member name points, and a member
    named ``../../../.bashrc`` is a valid zip entry. Absolute paths and symlinks
    are refused for the same reason. This is checked for *every* member before
    *any* is written, so a malicious archive cannot get a partial write in
    before the refusal.
    """
    target = target.resolve()
    members = []
    for member in archive.infolist():
        name = member.filename
        if name.endswith("/"):
            continue
        destination = (target / name).resolve()
        if not destination.is_relative_to(target):
            raise DataError(
                "engine_archive_member_escapes",
                member=name,
                expected=(
                    "every member to extract inside the installation directory. "
                    "This archive contains a path that would write outside it, so "
                    "nothing was extracted"
                ),
            )
        # Mode's high bits carry the Unix file type; 0xA000 is a symlink, which
        # can point outside the target after extraction even when its own name
        # does not.
        if (member.external_attr >> 16) & 0xF000 == 0xA000:
            raise DataError(
                "engine_archive_contains_symlink",
                member=name,
                expected="a plain archive of executables and libraries",
            )
        members.append(member)
    return members


def extract(archive_path: str | Path, target: Path, *, expect: Iterable[str] = ()) -> list[Path]:
    """Extract a verified archive into *target*, then check what arrived.

    Executables are made executable: a zip written on Windows carries no Unix
    permission bits, so the binaries arrive unrunnable and the failure appears
    much later as a permission error nobody connects to the install. On Windows
    the call is a no-op beyond the read-only flag, which is right: executability
    there comes from the extension, not from the mode.
    """
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        members = safe_members(archive, target)
        for member in members:
            archive.extract(member, target)

    written = [target / member.filename for member in members]
    for path in written:
        if path.suffix.lower() not in {".txt", ".md", ".xsd", ".json"}:
            path.chmod(path.stat().st_mode | 0o755)

    missing = [name for name in expect if not any(p.name == name for p in written)]
    if missing:
        raise DataError(
            "engine_archive_missing_programs",
            received=sorted({p.name for p in written})[:20],
            expected=sorted(missing),
            note=(
                "The archive extracted but does not contain the programs GeoComp "
                "expects. Upstream's archive layout has probably changed, which "
                "means the pinned release needs updating rather than working around"
            ),
        )
    return written


def install(
    release: EngineRelease,
    *,
    root: str | Path,
    fetch: Fetcher,
    keep_archive: bool = False,
) -> Path:
    """Download, verify, extract and check one pinned release.

    The order is the whole point: **verify before extract**, always.

    Returns **the directory the programs are actually in**, which is not always
    the one they were extracted into: upstream's archives nest everything under
    a single folder, so ``dynadjust-linux-openblas-static.zip`` puts its
    programs in ``<version>/dynadjust-linux-static/``. Returning the version
    directory would hand :func:`~geocomp.engines.base.discover` a path whose
    direct children are one folder, and the engine would be reported absent on
    a machine where it had just installed and verified perfectly.
    """
    root = Path(root)
    destination = root / release.engine / release.version
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination.parent / f"{release.engine}-{release.version}.zip"

    fetch(release.url, archive_path)
    if not archive_path.exists():
        raise DataError(
            "engine_download_produced_nothing",
            engine=release.engine,
            url=release.url,
            expected="the fetcher to write the archive to the given path",
        )

    verify(archive_path, release.sha256)
    written = extract(archive_path, destination, expect=release.members)

    if not keep_archive:
        archive_path.unlink(missing_ok=True)
    return program_directory(written, release.members, fallback=destination)


def program_directory(
    written: Sequence[Path], members: Sequence[str], *, fallback: Path
) -> Path:
    """The one directory holding the programs, from where they actually landed.

    Derived from the extracted paths rather than assumed, because upstream's
    layout is upstream's to change: v1.4.0 nests under
    ``dynadjust-linux-static/``, and a later release that stops doing so should
    keep working without an edit here.

    Raises:
        DataError: when the programs are spread across more than one directory.
            GeoComp drives them from a single directory, so this is a layout it
            cannot use -- and saying so at install time is far more use than
            letting :func:`~geocomp.engines.base.discover` report half of them
            missing later, on a machine where the install just succeeded.
    """
    wanted = set(members)
    homes = {path.parent for path in written if path.name in wanted}
    if not homes:
        return fallback
    if len(homes) > 1:
        raise DataError(
            "engine_archive_programs_scattered",
            received=sorted(str(home) for home in homes),
            expected="every program in one directory, which is how GeoComp runs them",
        )
    return homes.pop()


def install_pinned(engine: str, platform: str, *, root: str | Path, fetch: Fetcher) -> Path:
    """Install the pinned release for *engine* on *platform*.

    Raises:
        ValidationError: ``engine_release_not_pinned`` when the table has no row.
            Naming the script that adds one, because the fix is a two-minute
            job on a machine with network access and an unexplained refusal
            would send someone looking for a bug instead.
    """
    candidates = releases_for(engine, platform)
    if not candidates:
        raise ValidationError(
            "engine_release_not_pinned",
            engine=engine,
            platform=platform,
            available=sorted({(r.engine, r.platform) for r in PINNED}),
            expected=(
                "a pinned release for this engine and platform. Run "
                "scripts/pin_engine_release.py on a machine that can reach the "
                "upstream releases page: it downloads the archive, computes its "
                "digest and prints the row to add to PINNED. Meanwhile, set the "
                "engine's path in Global Settings to an existing installation"
            ),
        )
    return install(candidates[0], root=root, fetch=fetch)


@dataclass
class EngineStatus:
    """What the UI needs to decide whether to enable an operation (FR-306)."""

    engine: str
    version: EngineVersion | None = None
    programs: dict[str, Path] = field(default_factory=dict)
    missing: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.version is not None and not self.missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "available": self.available,
            "version": self.version.to_dict() if self.version else None,
            "missing": list(self.missing),
        }


def locate(
    engine: str,
    programs: Iterable[str],
    *,
    configured: str | Path | None = None,
    extra_directories: Iterable[Path] = (),
) -> EngineStatus:
    """Find every program an engine needs, reporting which are missing.

    Per-program rather than per-engine because DynAdjust is a **suite**
    (``specs/07`` section 1): a half-installed one, with ``dnaimport`` present
    and ``dnaadjust`` not, is a real state that produces a baffling failure
    halfway through a pipeline. Naming the missing program turns that into a
    sentence the user can act on.
    """
    directories = tuple(Path(d) for d in extra_directories)
    found: dict[str, Path] = {}
    missing: list[str] = []
    for program in programs:
        path, _source = discover(program, configured=configured, extra_directories=directories)
        if path is None:
            missing.append(program)
        else:
            found[program] = path
    return EngineStatus(engine=engine, programs=found, missing=tuple(missing))
