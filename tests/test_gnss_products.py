# SPDX-License-Identifier: GPL-2.0-or-later
"""GNSS products: names, sources, the cache and its record (``specs/08`` §5, phase P10c).

The network is a stub here, which is what lets the criteria be asserted exactly:
a second run makes **no** network call (``specs/08`` §10 criterion 6), every
product used is named in a record, no credential reaches a URL GeoComp keeps
(criterion 7, NFR-010), and a refused login is told apart from a lost
connection (§9). The real network is ``tests/qgis/test_product_download.py``'s,
and the real archive is engine CI's.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import date, datetime
from pathlib import Path

import pytest

from geocomp.core.errors import DataError, ValidationError
from geocomp.core.techniques.gnss.products import (
    NOAA,
    Latency,
    ProductKind,
    ProductRequest,
    ProductService,
    check_availability,
    days_of,
    fetch_with_retry,
    gps_week,
    read_services,
    requests_for,
    resolve,
    safe_url,
)

MANIFEST = Path(__file__).parent / "data" / "rd06" / "source_manifest.json"
NEW_YEAR_2025 = date(2025, 1, 1)


class FakeArchive:
    """A fetcher over a dict of URL -> bytes, counting every call."""

    def __init__(self, files: dict[str, bytes], *, failures: dict[str, list[str]] | None = None):
        self.files = files
        self.failures = failures or {}
        self.calls: list[tuple[str, str, str]] = []

    def _fail(self, url: str) -> None:
        queue = self.failures.get(url)
        if queue:
            raise DataError(queue.pop(0), url=url)

    def exists(self, url: str, authcfg: str) -> bool:
        self.calls.append(("exists", url, authcfg))
        self._fail(url)
        return url in self.files

    def get(self, url: str, authcfg: str) -> bytes:
        self.calls.append(("get", url, authcfg))
        self._fail(url)
        if url not in self.files:
            raise DataError("product_not_found", url=url)
        return self.files[url]


def _gz(text: str) -> bytes:
    return gzip.compress(text.encode(), mtime=0)


def _final(day: date) -> ProductRequest:
    return ProductRequest(ProductKind.ORBIT, day, Latency.FINAL)


class TestNames:
    def test_gps_week_and_day(self):
        # NOAA's own legacy file for 1 January 2025 is igs23473.sp3.gz.
        assert gps_week(NEW_YEAR_2025) == (2347, 3)
        assert gps_week(date(2020, 1, 15)) == (2088, 3)

    def test_the_noaa_urls_are_the_ones_rd06_pins(self):
        """RD-06's manifest records these two URLs with their SHA-256: the
        templates produce them character for character."""
        pinned = {e["file"]: e["url"] for e in json.loads(MANIFEST.read_text())}
        orbit, *_legacy = NOAA.urls(_final(NEW_YEAR_2025))
        assert orbit == pinned["IGS0OPSFIN_20250010000_01D_15M_ORB.SP3.gz"]
        (navigation,) = NOAA.urls(
            ProductRequest(ProductKind.GPS_NAVIGATION, NEW_YEAR_2025, Latency.BROADCAST)
        )
        assert navigation == pinned["brdc0010.25n.gz"]
        second = ProductRequest(ProductKind.GPS_NAVIGATION, date(2025, 1, 2), Latency.BROADCAST)
        assert NOAA.urls(second) == (pinned["brdc0020.25n.gz"],)

    def test_the_legacy_name_follows_the_long_one(self):
        long_name, legacy = NOAA.urls(ProductRequest(ProductKind.ORBIT, date(2020, 1, 15), Latency.RAPID))
        assert long_name.endswith("/rinex/2020/015/IGS0OPSRAP_20200150000_01D_15M_ORB.SP3.gz")
        assert legacy.endswith("/rinex/2020/015/igr20883.sp3.gz")

    def test_the_days_a_session_touches(self):
        spans = [
            (datetime(2025, 1, 1, 22), datetime(2025, 1, 2, 3)),
            (datetime(2025, 1, 1, 8), None),
            (None, None),
        ]
        assert days_of(spans) == [date(2025, 1, 1), date(2025, 1, 2)]

    def test_navigation_is_broadcast_whatever_the_orbit_latency(self):
        requests = requests_for(
            [NEW_YEAR_2025], [ProductKind.ORBIT, ProductKind.GPS_NAVIGATION], latency=Latency.RAPID
        )
        assert [r.latency for r in requests] == [Latency.RAPID, Latency.BROADCAST]


class TestResolution:
    @pytest.fixture
    def archive(self):
        (url, _legacy) = NOAA.urls(_final(NEW_YEAR_2025))
        return FakeArchive({url: _gz("* final orbit\n")})

    def test_a_download_lands_in_the_cache_with_its_record(self, archive, tmp_path):
        result = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        (product,) = result.resolved
        assert product.path.read_text() == "* final orbit\n"
        assert product.path.parent == tmp_path / "orbit" / "final" / "IGS" / "2025" / "001"
        record = product.record
        assert record.origin == "download" and record.service == "noaa-ncn"
        assert record.sha256 == hashlib.sha256(b"* final orbit\n").hexdigest()
        assert record.downloaded_sha256 == hashlib.sha256(_gz("* final orbit\n")).hexdigest()
        assert (
            json.loads((product.path.parent / (product.path.name + ".json")).read_text())["url"] == record.url
        )

    def test_criterion_6_a_second_run_makes_no_network_call(self, archive, tmp_path):
        resolve([_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive)
        archive.calls.clear()
        again = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        assert archive.calls == []
        (product,) = again.resolved
        assert product.record.origin == "cache" and product.record.url  # still names its source

    def test_the_product_directory_comes_before_any_download(self, archive, tmp_path):
        directory = tmp_path / "products"
        directory.mkdir()
        (directory / "IGS0OPSFIN_20250010000_01D_15M_ORB.SP3").write_text("* on disk\n")
        result = resolve(
            [_final(NEW_YEAR_2025)],
            cache=tmp_path / "cache",
            directory=directory,
            services=[NOAA],
            fetcher=archive,
        )
        assert archive.calls == []
        assert result.resolved[0].record.origin == "directory"

    def test_a_damaged_cache_entry_is_fetched_again(self, archive, tmp_path):
        first = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        first.resolved[0].path.write_text("truncated")
        again = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        assert again.resolved[0].record.origin == "download"

    def test_without_a_fetcher_a_missing_product_is_reported_not_fetched(self, tmp_path):
        result = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=None
        )
        assert result.resolved == () and result.missing[0][1] == "no download service"

    def test_the_legacy_name_is_tried_when_the_long_one_is_absent(self, tmp_path):
        _long, legacy = NOAA.urls(_final(date(2020, 1, 15)))
        archive = FakeArchive({legacy: _gz("* legacy\n")})
        result = resolve(
            [_final(date(2020, 1, 15))], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        assert result.resolved[0].path.name == "igs20883.sp3"

    def test_a_lower_latency_is_used_only_when_allowed_and_then_recorded(self, tmp_path):
        rapid, _legacy = NOAA.urls(_final(NEW_YEAR_2025).with_latency(Latency.RAPID))
        archive = FakeArchive({rapid: _gz("* rapid\n")})
        strict = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=archive
        )
        assert strict.resolved == () and strict.missing
        lenient = resolve(
            [_final(NEW_YEAR_2025)],
            cache=tmp_path,
            directory=None,
            services=[NOAA],
            fetcher=archive,
            fallback=True,
        )
        assert lenient.resolved[0].record.latency == "rapid"
        assert lenient.substituted == ((_final(NEW_YEAR_2025), Latency.RAPID),)

    def test_services_are_tried_in_priority_order(self, tmp_path):
        mirror = ProductService(
            "mirror", "A mirror", {"orbit/final": ("https://mirror.example/{yyyy}/{doy}/orbit.sp3.gz",)}
        )
        archive = FakeArchive({"https://mirror.example/2025/001/orbit.sp3.gz": _gz("* mirror\n")})
        result = resolve(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[mirror, NOAA], fetcher=archive
        )
        assert result.resolved[0].record.service == "mirror"
        assert [call[0] for call in archive.calls] == ["get"]


class TestAvailability:
    def test_reported_before_anything_is_fetched(self, tmp_path):
        final, _legacy = NOAA.urls(_final(NEW_YEAR_2025))
        rapid, _legacy = NOAA.urls(_final(date(2025, 1, 2)).with_latency(Latency.RAPID))
        archive = FakeArchive({final: b"x", rapid: b"y"})
        report = check_availability(
            [_final(NEW_YEAR_2025), _final(date(2025, 1, 2))],
            cache=tmp_path,
            directory=None,
            services=[NOAA],
            fetcher=archive,
            fallback=True,
        )
        assert [c[0] for c in archive.calls if c[0] == "get"] == []
        assert report[0].available and report[0].fallback is None
        assert report[1].available and report[1].fallback is Latency.RAPID

    def test_unavailable_says_so(self, tmp_path):
        report = check_availability(
            [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[NOAA], fetcher=FakeArchive({})
        )
        assert not report[0].available and report[0].reason == "not found"


class TestFailures:
    def test_a_network_failure_is_retried_with_backoff(self):
        url = "https://example.org/x.gz"
        archive = FakeArchive(
            {url: b"ok"}, failures={url: ["product_network_failed", "product_network_failed"]}
        )
        waits: list[float] = []
        assert fetch_with_retry(archive, url, "", sleep=waits.append) == b"ok"
        assert waits == [2.0, 4.0]

    def test_a_refused_login_is_not_retried_and_says_so(self, tmp_path):
        service = ProductService(
            "private",
            "An archive with a login",
            {"orbit/final": ("https://private.example/{doy}.sp3.gz",)},
            authcfg="abc1234",
        )
        archive = FakeArchive(
            {"https://private.example/001.sp3.gz": b""},
            failures={"https://private.example/001.sp3.gz": ["product_authentication_failed"]},
        )
        with pytest.raises(DataError) as caught:
            resolve(
                [_final(NEW_YEAR_2025)], cache=tmp_path, directory=None, services=[service], fetcher=archive
            )
        assert caught.value.code.endswith("product_authentication_failed")
        assert archive.calls == [("get", "https://private.example/001.sp3.gz", "abc1234")]

    def test_a_corrupt_download_is_refused(self, tmp_path):
        url, _legacy = NOAA.urls(_final(NEW_YEAR_2025))
        with pytest.raises(DataError) as caught:
            resolve(
                [_final(NEW_YEAR_2025)],
                cache=tmp_path,
                directory=None,
                services=[NOAA],
                fetcher=FakeArchive({url: b"<html>an error page</html>"}),
            )
        assert caught.value.code.endswith("product_corrupt")


class TestCredentials:
    """Criterion 7 and NFR-010: no credential in anything GeoComp keeps."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://user:secret@archive.example/{doy}.sp3.gz",
            "https://archive.example/{doy}.sp3.gz?token=abc",
            "https://archive.example/{doy}.sp3.gz?X-Amz-Signature=abc",
            "https://archive.example/{doy}.sp3.gz?api_key=abc",
        ],
    )
    def test_a_template_carrying_one_is_refused(self, url):
        with pytest.raises(ValidationError) as caught:
            ProductService("bad", "bad", {"orbit/final": (url,)})
        assert caught.value.code.endswith("product_service_credential_in_url")
        assert "secret" not in str(caught.value.context) and "abc" not in str(caught.value.context)

    def test_a_service_names_its_login_by_reference(self, tmp_path):
        services = read_services(
            {
                "services": [
                    {
                        "id": "cddis",
                        "name": "CDDIS",
                        "authcfg": "ab12cd3",
                        "templates": {
                            "orbit/final": "https://cddis.example/{week}/IGS0OPSFIN_{yyyy}{doy}.SP3.gz"
                        },
                    }
                ]
            }
        )
        assert services["cddis"].authcfg == "ab12cd3"
        url = services["cddis"].urls(_final(NEW_YEAR_2025))[0]
        archive = FakeArchive({url: _gz("* cddis\n")})
        result = resolve(
            [_final(NEW_YEAR_2025)],
            cache=tmp_path,
            directory=None,
            services=list(services.values()),
            fetcher=archive,
        )
        record = json.dumps(result.records[0].to_dict())
        assert "ab12cd3" not in record  # not even the reference reaches the record
        assert archive.calls[0][2] == "ab12cd3"

    def test_safe_url_passes_an_ordinary_url(self):
        assert safe_url("https://noaa-cors-pds.s3.amazonaws.com/rinex/2025/001/x.gz").startswith("https://")

    @pytest.mark.parametrize(
        ("payload", "code"),
        [
            ({"services": [{"id": "noaa-ncn", "templates": {}}]}, "product_service_id"),
            (
                {"services": [{"id": "x", "templates": {"orbit/hourly": "https://a/b"}}]},
                "product_service_template_key",
            ),
            ({"services": [{"name": "no id"}]}, "product_service_malformed"),
            (
                {"services": [{"id": "x", "templates": {"orbit/final": "ftp://a/b"}}]},
                "product_service_scheme",
            ),
        ],
    )
    def test_a_malformed_services_file_is_named(self, payload, code):
        with pytest.raises(ValidationError) as caught:
            read_services(payload)
        assert caught.value.code.endswith(code)
