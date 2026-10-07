# SPDX-License-Identifier: GPL-2.0-or-later
"""Fetching GNSS products through the QGIS network stack (FR-352, FR-353, NFR-010).

``specs/08`` section 5: *downloads use the QGIS network stack, so the user's
proxy configuration is honoured*, and *credentials go through the QGIS
authentication system*. This is the :class:`~geocomp.core.techniques.gnss.products.Fetcher`
the plugin uses; the resolution logic lives in the core and is tested there.

**A login is applied by reference.** The service names a QGIS authentication
configuration by its id, and :meth:`QgsBlockingNetworkRequest.setAuthCfg` has
QGIS's authentication manager add the credential to the request. GeoComp never
holds the user name or password, so there is nothing for it to write into a
log, a provenance record or an export (NFR-010).

**Three outcomes, three different things to do** (``specs/08`` §9): a product
the archive does not have (*not found* -- try a lower latency, or wait), a login
refused (*authentication failed* -- check the authentication configuration),
and anything else (*network failed* -- retried with backoff by the core). A 403
from an anonymous service is read as *not found*: S3 answers a missing key that
way where listing is not public, and asking the user to check a login that does
not exist would send them the wrong way.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from qgis.core import QgsBlockingNetworkRequest, QgsFeedback
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

from geocomp.core.errors import DataError

__all__ = ["QgisFetcher"]

_TIMEOUT_MS = 120_000


class QgisFetcher:
    """Products over the QGIS network stack, with an optional login by reference."""

    def __init__(self, feedback: QgsFeedback | None = None) -> None:
        self.feedback = feedback

    def exists(self, url: str, authcfg: str) -> bool:
        """Whether the server has the file, asked with a HEAD request.

        Raises:     DataError: ``product_authentication_failed`` or ``product_network_failed``; a
        missing product is ``False``, not an error.
        """
        try:
            self._request("head", url, authcfg)
        except DataError as error:
            if error.code.endswith("product_not_found"):
                return False
            raise
        return True

    def get(self, url: str, authcfg: str) -> bytes:
        """The file's bytes, fetched through QGIS with the authentication configuration given.

        Raises:     DataError: ``product_not_found``, ``product_authentication_failed`` or
        ``product_network_failed``.
        """
        return bytes(self._request("get", url, authcfg).content())

    def _request(self, method: str, url: str, authcfg: str):
        request = QgsBlockingNetworkRequest()
        if authcfg:
            request.setAuthCfg(authcfg)
        network_request = QNetworkRequest(QUrl(url))
        network_request.setTransferTimeout(_TIMEOUT_MS)
        if method == "head":
            outcome = request.head(network_request, True, self.feedback)
        else:
            outcome = request.get(network_request, True, self.feedback)
        reply = request.reply()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        status = int(status) if status is not None else 0
        if outcome == QgsBlockingNetworkRequest.ErrorCode.NoError and 200 <= status < 300:
            return reply
        if status == 404 or (status == 403 and not authcfg):
            # The same context the core's not-found carries -- the product and
            # where it was looked for -- so one message serves both.
            raise DataError(
                "product_not_found",
                product=url.rsplit("/", 1)[-1],
                services=[urlsplit(url).hostname or url],
                url=url,
                status=status,
            )
        if status in (401, 403):
            raise DataError("product_authentication_failed", url=url, status=status)
        raise DataError(
            "product_network_failed",
            url=url,
            status=status,
            reason=request.errorMessage() or str(outcome),
        )
