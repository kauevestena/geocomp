# SPDX-License-Identifier: GPL-2.0-or-later
"""What GNSS says about files and products, in words (P12c-41; FR-091, NFR-006).

Until P12c-41 the folder scan said what it skipped or doubted in its own English
-- "navigation files paired by fallback: ...", or a refusal's code and expected
value -- and the GNSS algorithms put that into a translated sentence: "Não foi
possível ler %1: data.rinex_header_missing". Each is now a finding, worded by its
template in the language, with what to do. So is a product: "orbit final
2025-01-02 (not found)" was the core's name for it and its reason, as they stood.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.qgis.test_language import LANGUAGES, _Installed

pytestmark = pytest.mark.qgis

DATA = Path(__file__).resolve().parents[1] / "data" / "rtklib"


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    return geocomp_provider


@pytest.fixture
def folder(tmp_path):
    """One file of each kind the scan reports: unreadable, misnamed, paired by fallback."""
    shutil.copy(DATA / "07590920.05o", tmp_path / "99990920.05o")  # names another station
    shutil.copy(DATA / "brdc_0759.05n.gz", tmp_path)  # states no day: paired by fallback
    (tmp_path / "30400920.05o").write_text("this is not RINEX\n", encoding="ascii")
    return tmp_path


def _warnings(folder: Path) -> list[str]:
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    class Listening(QgsProcessingFeedback):
        def __init__(self):
            super().__init__()
            self.warnings: list[str] = []

        def pushWarning(self, text):  # noqa: N802 -- the Qt interface
            self.warnings.append(text)

    feedback = Listening()
    algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:gnss_scan_sessions")
    algorithm.create({}).run(
        {"FOLDER": str(folder), "OUTPUT_JSON": str(folder / "sessions.json")},
        QgsProcessingContext(),
        feedback,
        catchExceptions=False,
    )
    return feedback.warnings


def test_each_is_said_in_words_with_what_to_do(folder):
    from tests.structural.test_message_templates import _REMEDY

    warnings = _warnings(folder)
    assert len(warnings) == 3, warnings
    for text in warnings:
        assert "data." not in text and "validation." not in text, text
        assert "paired by fallback" not in text and "(not set)" not in text, text
        assert _REMEDY.search(text), text
    assert any(text.startswith("Could not read ") and "30400920.05o" in text for text in warnings)
    assert any("station 9999" in text and "marker 0759" in text for text in warnings)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_each_is_said_in_the_language(folder, locale):
    english = _warnings(folder)
    with _Installed(locale) as catalogue:
        translated = _warnings(folder)
    frame = catalogue["GeoCompMessages"]["Could not read %1: %2"]
    assert any(text.startswith(frame.split("%1")[0]) for text in translated), translated
    assert not set(translated) & set(english), translated


@pytest.mark.parametrize("locale", (None, *LANGUAGES))
def test_a_product_is_named_in_the_language(locale):
    from contextlib import nullcontext
    from datetime import date

    from geocomp.algorithms.gnss.common import product_label
    from geocomp.core.techniques.gnss.products import Latency, ProductKind, ProductRequest

    request = ProductRequest(ProductKind.ORBIT, date(2025, 1, 2), Latency.FINAL)
    with _Installed(locale) if locale else nullcontext() as catalogue:
        label = product_label(request)
    if catalogue is None:
        assert label == "final orbit for 2025-01-02"
    else:
        expected = catalogue["GeoCompGnss"]["%1 for %2"]
        expected = expected.replace("%1", catalogue["GeoCompGnss"]["final orbit"])
        assert label == expected.replace("%2", "2025-01-02")
    assert request.describe() not in label


@pytest.mark.parametrize("reason", ("not found", "no download service"))
def test_a_product_that_cannot_be_had_says_why_and_what_to_do(reason):
    from datetime import date

    from geocomp.algorithms.gnss.common import unavailable_message
    from geocomp.core.techniques.gnss.products import Latency, ProductKind, ProductRequest
    from tests.structural.test_message_templates import _REMEDY

    request = ProductRequest(ProductKind.GPS_NAVIGATION, date(2025, 1, 2), Latency.BROADCAST)
    text = unavailable_message(request, reason)
    assert text.startswith("GPS broadcast navigation for 2025-01-02 is not in the cache"), text
    assert f"({reason})" not in text and _REMEDY.search(text), text
