# SPDX-License-Identifier: GPL-2.0-or-later
"""Download the products a campaign needs (FR-352, FR-353, NFR-010).

``specs/11-module-gnss.md`` section 2 lists *download products* among the GNSS
supporting operations, and ``specs/08`` section 5 says how: each product from
the cache, then the product directory, then a configured download service, and
every product recorded by name, origin and checksum.

Processing resolves its own products, so this algorithm is for the two things
processing cannot do: **fetch ahead** -- a campaign's orbits downloaded while
there is a network, processed later where there is none -- and **check
ahead**, which reports what can be had and from where without downloading
anything, so a recent session's missing final orbit is known before a long
batch is planned around it.

**No credential passes through here.** A service that needs a login names a
QGIS authentication configuration in the services file; the QGIS network stack
applies it. The manifest and the log carry service ids and credential-free URLs
only (NFR-010).
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from qgis.core import (
    Qgis,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDateTime,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
)

from geocomp.algorithms.base import GeoCompAlgorithm
from geocomp.algorithms.gnss.common import (
    PRODUCT_FALLBACK,
    gnss_setting,
    product_cache,
    product_directory,
    product_services,
    translate_error,
)
from geocomp.core.errors import GeoCompError
from geocomp.core.techniques.gnss.products import (
    Latency,
    ProductKind,
    Resolution,
    check_availability,
    days_of,
    requests_for,
    resolve,
)

FOLDER = "FOLDER"
FIRST_DAY = "FIRST_DAY"
LAST_DAY = "LAST_DAY"
PRODUCTS = "PRODUCTS"
LATENCY = "LATENCY"
CHECK_ONLY = "CHECK_ONLY"
OUTPUT_DIRECTORY = "OUTPUT_DIRECTORY"
OUTPUT_JSON = "OUTPUT_JSON"
AVAILABLE = "AVAILABLE"
MISSING = "MISSING"

_KINDS = (ProductKind.ORBIT, ProductKind.GPS_NAVIGATION, ProductKind.GLONASS_NAVIGATION)
_LATENCIES = (Latency.FINAL, Latency.RAPID)

#: QGIS 4 spells the date-only type ``Qgis.ProcessingDateTimeParameterDataType.Date``
#: and QGIS 3 before 3.36 ``QgsProcessingParameterDateTime.Type.Date``; the older
#: spelling is kept only so the test suite runs against a distribution's QGIS 3,
#: as ``layer_outputs`` does for source types.
if hasattr(Qgis, "ProcessingDateTimeParameterDataType"):
    _DATE = Qgis.ProcessingDateTimeParameterDataType.Date
else:  # pragma: no cover -- QGIS < 3.36
    _DATE = QgsProcessingParameterDateTime.Type.Date

#: A year of days. A typo in a year -- 2015 for 2025 -- would otherwise start
#: ten years of downloads; a campaign longer than this is fetched in parts.
MAX_DAYS = 366


class DownloadProductsAlgorithm(GeoCompAlgorithm):
    """Fetch, or check, the orbits and navigation for a set of days."""

    TR_CONTEXT = "DownloadProductsAlgorithm"

    def displayName(self) -> str:
        return self.tr("Download products")

    def shortDescription(self) -> str:
        return self.tr("Fetch or check the orbits and navigation a campaign needs.")

    def help_body(self) -> str:
        return self.tr(
            "<p>Resolves IGS orbits and broadcast navigation for the days of a "
            "folder's sessions, or for a range of days: each from the product "
            "cache, then the product directory, then the download services "
            "configured in Global Settings → GNSS, in their order.</p>"
            "<p><b>Check only</b> downloads nothing: it reports, for each product, "
            "whether it can be had and from where. Use it before a long batch on "
            "recent data, whose final orbits may not be published yet.</p>"
            "<p>Processing resolves its own products; this is for fetching a "
            "campaign's products while there is a network, to process later "
            "without one. Ultra-rapid orbits are not offered.</p>"
            "<p>A service that needs a login names a QGIS authentication "
            "configuration; GeoComp never sees the credential, and the manifest "
            "records service ids and URLs without one.</p>"
        )

    def initAlgorithm(self, config: dict[str, Any] | None = None) -> None:
        self.addParameter(
            QgsProcessingParameterFile(
                FOLDER,
                self.tr("Folder of RINEX observations (days from its sessions)"),
                behavior=QgsProcessingParameterFile.Behavior.Folder,
                optional=True,
            )
        )
        for name, label in (
            (FIRST_DAY, self.tr("First day (instead of, or as well as, a folder)")),
            (LAST_DAY, self.tr("Last day")),
        ):
            self.addParameter(
                QgsProcessingParameterDateTime(
                    name, label, type=_DATE, optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                PRODUCTS,
                self.tr("Products"),
                options=[
                    self.tr("Precise orbit (SP3)"),
                    self.tr("GPS broadcast navigation"),
                    self.tr("GLONASS broadcast navigation"),
                ],
                allowMultiple=True,
                defaultValue=[0, 1],
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                LATENCY,
                self.tr("Orbit latency"),
                options=[self.tr("Final"), self.tr("Rapid")],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                CHECK_ONLY, self.tr("Check availability only; download nothing"), defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                OUTPUT_DIRECTORY,
                self.tr("Copy the products to"),
                optional=True,
                createByDefault=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                OUTPUT_JSON,
                self.tr("Product manifest"),
                self.tr("JSON files (*.json)"),
                optional=True,
                createByDefault=True,
            )
        )
        self.addOutput(QgsProcessingOutputNumber(AVAILABLE, self.tr("Products available")))
        self.addOutput(QgsProcessingOutputNumber(MISSING, self.tr("Products missing")))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        days = self._days(parameters, context, feedback)
        kinds = [_KINDS[i] for i in self.parameterAsEnums(parameters, PRODUCTS, context)]
        if not kinds:
            raise QgsProcessingException(self.tr("Choose at least one product."))
        latency = _LATENCIES[self.parameterAsEnum(parameters, LATENCY, context)]
        check_only = self.parameterAsBoolean(parameters, CHECK_ONLY, context)
        requests = requests_for(days, kinds, latency=latency)

        services = product_services()
        fallback = bool(gnss_setting(PRODUCT_FALLBACK))
        fetcher = None
        if services:
            from geocomp.services.downloads import QgisFetcher

            fetcher = QgisFetcher(feedback)
            feedback.pushInfo(
                self.tr("Download services, in order: %1").replace(
                    "%1", ", ".join(service.id for service in services)
                )
            )
        else:
            feedback.pushWarning(
                self.tr(
                    "No download service is configured; only the cache and the "
                    "product directory are looked in."
                )
            )
        cache = product_cache()
        directory = product_directory()

        if check_only:
            manifest, available, missing = self._check(
                requests, cache, directory, services, fetcher, fallback, feedback
            )
        else:
            manifest, available, missing, resolved = self._fetch(
                requests, cache, directory, services, fetcher, fallback, feedback
            )
        manifest = {
            "days": [day.isoformat() for day in days],
            "services": [service.id for service in services],
            "check_only": check_only,
            **manifest,
        }
        feedback.pushInfo(
            self.tr("%1 product(s) available, %2 missing")
            .replace("%1", str(available))
            .replace("%2", str(missing))
        )

        outputs: dict[str, Any] = {AVAILABLE: available, MISSING: missing}
        target = self.parameterAsString(parameters, OUTPUT_DIRECTORY, context)
        if target and not check_only:
            folder = Path(target)
            folder.mkdir(parents=True, exist_ok=True)
            for product in resolved.resolved:
                shutil.copy2(product.path, folder / product.path.name)
            outputs[OUTPUT_DIRECTORY] = str(folder)
        destination = self.parameterAsFileOutput(parameters, OUTPUT_JSON, context)
        if destination:
            Path(destination).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            outputs[OUTPUT_JSON] = destination
        feedback.setProgress(100)
        return outputs

    def _days(
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> list[date]:
        """The days asked for: a folder's sessions, a range, or both."""
        spans = []
        folder = self.parameterAsFile(parameters, FOLDER, context)
        if folder:
            from geocomp.io.gnss_discovery import scan_folder

            try:
                scan = scan_folder(Path(folder))
            except GeoCompError as exc:
                raise QgsProcessingException(translate_error(exc)) from exc
            for path, reason in scan.skipped:
                feedback.pushWarning(
                    self.tr("Could not read %1: %2").replace("%1", str(path)).replace("%2", reason)
                )
            spans += [(session.start, session.end) for session in scan.sessions]
        first = self.parameterAsDateTime(parameters, FIRST_DAY, context)
        last = self.parameterAsDateTime(parameters, LAST_DAY, context)
        if first.isValid():
            start = first.date().toPyDate()
            end = last.date().toPyDate() if last.isValid() else start
            if end < start:
                raise QgsProcessingException(
                    self.tr("The last day, %1, is before the first, %2.")
                    .replace("%1", end.isoformat())
                    .replace("%2", start.isoformat())
                )
            spans.append((datetime.combine(start, time()), datetime.combine(end, time())))
        days = days_of(spans)
        if not days:
            raise QgsProcessingException(
                self.tr("Give a folder of observations with dated sessions, or a first day.")
            )
        if len(days) > MAX_DAYS:
            raise QgsProcessingException(
                self.tr("%1 days were asked for; fetch at most %2 at a time.")
                .replace("%1", str(len(days)))
                .replace("%2", str(MAX_DAYS))
            )
        return days

    def _not_available(self, feedback: QgsProcessingFeedback, request, reason: str) -> None:
        feedback.pushWarning(
            self.tr("%1: not available (%2)").replace("%1", request.describe()).replace("%2", reason)
        )

    def _check(self, requests, cache, directory, services, fetcher, fallback, feedback):
        report = []
        for index, request in enumerate(requests):
            if feedback.isCanceled():
                break
            try:
                (found,) = check_availability(
                    [request],
                    cache=cache,
                    directory=directory,
                    services=services,
                    fetcher=fetcher,
                    fallback=fallback,
                )
            except GeoCompError as exc:
                feedback.pushWarning(
                    self.tr("%1: %2").replace("%1", request.describe()).replace("%2", translate_error(exc))
                )
                report.append({"product": request.describe(), "available": False, "reason": exc.code})
                continue
            entry = {
                "product": request.describe(),
                "available": found.available,
                "source": found.source,
                "url": found.url,
                **({"fallback": found.fallback.value} if found.fallback else {}),
                **({"reason": found.reason} if found.reason else {}),
            }
            report.append(entry)
            if found.available:
                feedback.pushInfo(
                    self.tr("%1: available from %2%3")
                    .replace("%1", request.describe())
                    .replace("%2", found.source)
                    .replace(
                        "%3",
                        self.tr(" (as %1)").replace("%1", found.fallback.value) if found.fallback else "",
                    )
                )
            else:
                self._not_available(feedback, request, found.reason)
            feedback.setProgress(int(100 * (index + 1) / len(requests)))
        available = sum(1 for entry in report if entry["available"])
        return {"availability": report}, available, len(requests) - available

    def _fetch(self, requests, cache, directory, services, fetcher, fallback, feedback):
        resolved, missing, substituted = [], [], []
        for index, request in enumerate(requests):
            if feedback.isCanceled():
                break
            try:
                one = resolve(
                    [request],
                    cache=cache,
                    directory=directory,
                    services=services,
                    fetcher=fetcher,
                    fallback=fallback,
                )
            except GeoCompError as exc:
                # A failed download is reported against its product and the rest
                # are still fetched (specs/08 section 9).
                feedback.pushWarning(
                    self.tr("%1: %2").replace("%1", request.describe()).replace("%2", translate_error(exc))
                )
                missing.append((request, exc.code.split(".")[-1]))
                continue
            resolved += one.resolved
            missing += one.missing
            substituted += one.substituted
            for product in one.resolved:
                feedback.pushInfo(
                    self.tr("%1: %2 (%3)")
                    .replace("%1", request.describe())
                    .replace("%2", product.record.name)
                    .replace("%3", product.record.origin)
                )
            for _request, reason in one.missing:
                self._not_available(feedback, request, reason)
            for _request, used in one.substituted:
                feedback.pushWarning(
                    self.tr("%1: used the %2 orbit, as Global Settings allow.")
                    .replace("%1", request.describe())
                    .replace("%2", used.value)
                )
            feedback.setProgress(int(100 * (index + 1) / len(requests)))
        resolution = Resolution(tuple(resolved), tuple(missing), tuple(substituted))
        return resolution.to_dict(), len(resolved), len(requests) - len(resolved), resolution
