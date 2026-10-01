#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Download GNSS products from the real archive and check them against pinned bytes.

The product download (FR-352, phase P10c) is tested against a stub and a local
server in the test suite; this is the check against the archive itself. It
resolves RD-06's two days -- IGS final orbits and GPS broadcast navigation --
through ``core/techniques/gnss/products.py`` from NOAA's CORS open-data bucket,
exactly as the plugin does, and requires that what arrives is byte for byte
what ``tests/data/rd06/source_manifest.json`` pinned on 17 September 2026. Then
it resolves them again and requires that the second resolution made no network
call (``specs/08`` §10 criterion 6).

The fetcher here is the standard library's, which honours ``HTTPS_PROXY``; the
plugin's is the QGIS network stack's (``geocomp/services/downloads.py``). Both
sit behind the same three outcomes -- not found, refused login, network
failure -- so the resolution logic checked here is the one the plugin runs.

Exit 0 when every product matches, 1 when one differs, 2 when the archive could
not be reached.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from geocomp.core.errors import DataError  # noqa: E402
from geocomp.core.techniques.gnss.products import (  # noqa: E402
    NOAA,
    Latency,
    ProductKind,
    requests_for,
    resolve,
)

MANIFEST = ROOT / "tests" / "data" / "rd06" / "source_manifest.json"
DAYS = (date(2025, 1, 1), date(2025, 1, 2))


class UrllibFetcher:
    """The standard library's fetcher, mapped onto the three outcomes."""

    def __init__(self) -> None:
        self.calls = 0

    def _open(self, url: str, method: str):
        self.calls += 1
        request = urllib.request.Request(url, method=method)
        try:
            return urllib.request.urlopen(request, timeout=60)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise DataError("product_not_found", url=url) from error
            if error.code in (401, 403):
                raise DataError("product_authentication_failed", url=url, status=error.code) from error
            raise DataError("product_network_failed", url=url, status=error.code) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise DataError("product_network_failed", url=url, reason=str(error)) from error

    def exists(self, url: str, authcfg: str) -> bool:
        try:
            with self._open(url, "HEAD"):
                return True
        except DataError as error:
            if error.code.endswith("product_not_found"):
                return False
            raise

    def get(self, url: str, authcfg: str) -> bytes:
        with self._open(url, "GET") as response:
            return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cache", type=Path, help="Cache directory (default: a temporary one)")
    args = parser.parse_args()

    pinned = {e["file"]: e for e in json.loads(MANIFEST.read_text(encoding="utf-8"))}
    requests = requests_for(DAYS, [ProductKind.ORBIT, ProductKind.GPS_NAVIGATION], latency=Latency.FINAL)
    with tempfile.TemporaryDirectory(prefix="geocomp-products-") as scratch:
        cache = args.cache or Path(scratch)
        fetcher = UrllibFetcher()
        try:
            first = resolve(requests, cache=cache, directory=None, services=[NOAA], fetcher=fetcher)
        except DataError as error:
            print(f"The archive could not be reached: {error}", file=sys.stderr)
            return 2
        failures = [f"{r.describe()}: {reason}" for r, reason in first.missing]
        for product in first.resolved:
            name = product.record.url.rsplit("/", 1)[-1]
            entry = pinned.get(name)
            received = product.record.downloaded_sha256
            if entry is None:
                print(f"  {name}: downloaded, not pinned by RD-06 (sha256 {received})")
                continue
            if received != entry["sha256"]:
                failures.append(f"{name}: sha256 {received} != pinned {entry['sha256']}")
            else:
                print(f"  {name}: matches RD-06's pinned bytes")
        before = fetcher.calls
        again = resolve(requests, cache=cache, directory=None, services=[NOAA], fetcher=fetcher)
        if fetcher.calls != before or len(again.resolved) != len(first.resolved):
            failures.append(f"the second resolution made {fetcher.calls - before} network call(s)")
        else:
            print(f"Second resolution: {len(again.resolved)} products from the cache, no network call.")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
