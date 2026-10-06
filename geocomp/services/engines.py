# SPDX-License-Identifier: GPL-2.0-or-later
"""The engines as the plugin finds them, and installing one (FR-066, FR-300, FR-301; ADR-0003).

A program comes from one of four places, in the order ADR-0003 rule 4 sets and
ADR-0009 extends:

1. **A path the user configured**, in Global Settings under *Paths and
   engines* or, for one run, in an algorithm's own parameter. It always wins,
   and one that does not exist is refused rather than passed over.
2. **GeoComp's own installation** in the QGIS profile, put there by *Install an
   engine* and found again through its manifest
   (:func:`~geocomp.engines.manager.managed_directories`).
3. **The copy that ships inside the plugin**, where a build carries one: RTKLIB's
   ``rnx2rtkp`` (ADR-0009).
4. **The system path.**

Until P12c-6 the plugin had only the first, for DynAdjust alone and only as a
parameter, and the third. Nothing handed the managed directory to an engine, so
an installation the manager had downloaded and verified would never have run;
and nothing downloaded one, because nothing in the plugin called the manager.
RTKLIB had no configurable path at all.

Downloads go through the QGIS network stack, so the user's proxy configuration
is honoured (ADR-0003 rule 7). Verifying, extracting and recording are the
manager's, tested without QGIS.
"""

from __future__ import annotations

from pathlib import Path

from qgis.core import QgsApplication, QgsBlockingNetworkRequest
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

from geocomp.core.errors import DataError
from geocomp.engines.dynadjust.engine import DynAdjustEngine
from geocomp.engines.manager import (
    Installation,
    bundled_directories,
    current_platform,
    install_pinned,
    installation_root,
    installed,
    managed_directories,
)
from geocomp.engines.rtklib.engine import RtklibEngine
from geocomp.engines.status import EngineStatus

__all__ = [
    "DYNADJUST_DIRECTORY",
    "RTKLIB_PROGRAM",
    "QgisArchiveFetcher",
    "configured_path",
    "dynadjust_engine",
    "engine_root",
    "engine_status",
    "install_engine",
    "rtklib_engine",
]

#: The two settings this module reads, written out in full so the structural
#: check that every setting is read can find them.
DYNADJUST_DIRECTORY = "paths.dynadjust_directory"
RTKLIB_PROGRAM = "paths.rtklib_program"

#: An engine archive is tens of megabytes; ten minutes is generous for one over
#: a slow link, and a stalled transfer still ends.
_TIMEOUT_MS = 600_000


def _setting(key: str) -> str:
    from geocomp.services.settings_service import settings

    return str(settings.value(key) or "").strip()


def configured_path(engine: str) -> str:
    """The path set for *engine* in Global Settings, or empty."""
    return _setting({"dynadjust": DYNADJUST_DIRECTORY, "rtklib": RTKLIB_PROGRAM}[engine])


def engine_root() -> Path:
    """Where managed engines live: the QGIS profile's ``geocomp/engines`` (ADR-0003 rule 3)."""
    return installation_root(QgsApplication.qgisSettingsDirPath())


def dynadjust_engine(directory: str | None = None) -> DynAdjustEngine:
    """DynAdjust as the plugin finds it.

    Args:
        directory: A directory given for this run, which wins over the setting.
    """
    return DynAdjustEngine(
        configured_directory=(directory or "").strip() or configured_path("dynadjust") or None,
        extra_directories=managed_directories("dynadjust", engine_root()),
    )


def rtklib_engine() -> RtklibEngine:
    """RTKLIB's ``rnx2rtkp`` as the plugin finds it."""
    return RtklibEngine(
        configured=configured_path("rtklib") or None,
        extra_directories=managed_directories("rtklib", engine_root()),
        bundled_directories=bundled_directories("rtklib", Path(__file__).resolve().parent.parent),
    )


def engine_status() -> list[EngineStatus]:
    """What the About dialog and the system report show: each engine where the algorithms find it."""
    from geocomp.engines.status import engine_status as probe

    return probe(dynadjust=dynadjust_engine(), rtklib=rtklib_engine())


class QgisArchiveFetcher:
    """Downloads an engine archive over the QGIS network stack (ADR-0003 rule 7).

    A :data:`~geocomp.engines.manager.Fetcher`: it writes the archive to the
    path it is given and the manager verifies it before anything is extracted.
    No credentials: the releases are public, and none is ever stored (NFR-010).

    GitHub answers a release download with a redirect to its storage host,
    which :class:`QgsBlockingNetworkRequest` follows. It does not resolve a
    *relative* ``Location`` against the request -- GitHub's is absolute -- so a
    mirror that answers with a relative one fails here as a download error.
    """

    def __init__(self, feedback=None) -> None:
        self.feedback = feedback

    def __call__(self, url: str, destination: Path) -> None:
        request = QgsBlockingNetworkRequest()
        network_request = QNetworkRequest(QUrl(url))
        network_request.setTransferTimeout(_TIMEOUT_MS)
        outcome = request.get(network_request, True, self.feedback)
        reply = request.reply()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        status = int(status) if status is not None else 0
        if outcome == QgsBlockingNetworkRequest.ErrorCode.NoError and 200 <= status < 300:
            Path(destination).write_bytes(bytes(reply.content()))
            return
        raise DataError(
            "engine_download_failed",
            url=url,
            status=status,
            reason=request.errorMessage() or str(outcome),
        )


def install_engine(engine: str, *, feedback=None, root: str | Path | None = None) -> Installation:
    """Download, verify, install and record the pinned *engine* for this machine.

    Raises:
        ValidationError: ``engine_release_not_pinned`` for an engine or a platform
            GeoComp has no verified release of.
        DataError: a failed download, or an archive that does not verify -- which
            is deleted, and nothing is extracted from it.
    """
    root = Path(root) if root is not None else engine_root()
    install_pinned(engine, current_platform(), root=root, fetch=QgisArchiveFetcher(feedback))
    installation = installed(engine, root)
    if installation is None:  # pragma: no cover - install_pinned records it or raises
        raise DataError("engine_installation_not_recorded", engine=engine, root=str(root))
    return installation
