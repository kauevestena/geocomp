# SPDX-License-Identifier: GPL-2.0-or-later
"""The landing page says the same thing in each of the three languages (P13-33, specs/18 §1.1).

``docs/`` publishes one page per language: English at the root, Portuguese
(Brazil) under ``pt-br/`` and Spanish under ``es/``. Three copies of one page
drift apart unless something holds them together, so these read each page's
markup and compare it with the English one: the same elements in the same
order, the same places linked to, the same assets and the same numbers. Each
page offers the other two, and says which one it is.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import pytest

from tests.conftest import REPO_ROOT

DOCS = REPO_ROOT / "docs"

#: Each language's page, by the ``lang`` it declares, and where it is published.
PAGES = {"en": "index.html", "pt-BR": "pt-br/index.html", "es": "es/index.html"}

#: Where the published site is resolved from: only paths within it matter here.
_SITE = "https://site.invalid/"


class _Page(HTMLParser):
    """One page's markup: its elements, its references and its text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.skeleton: list[tuple[str, str | None, str | None]] = []
        self.references: list[tuple[str, bool]] = []
        self.alternates: dict[str, str] = {}
        self.switcher: dict[str, tuple[str, bool]] = {}
        self.ids: set[str] = set()
        self.title = ""
        self.text: list[str] = []
        self._in = {"switcher": False, "title": False}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        self.skeleton.append((tag, a.get("id"), a.get("class")))
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "nav" and a.get("class") == "lang":
            self._in["switcher"] = True
        if tag == "title":
            self._in["title"] = True
        alternate = tag == "link" and a.get("rel") == "alternate"
        switch = tag == "a" and self._in["switcher"]
        if alternate:
            self.alternates[a["hreflang"]] = a["href"]
        if switch:
            self.switcher[a["hreflang"]] = (a["href"], a.get("aria-current") == "page")
        to_a_language = alternate or switch
        for name in ("href", "src", "srcset"):
            if a.get(name):
                self.references.append((a[name], to_a_language))

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav":
            self._in["switcher"] = False
        if tag == "title":
            self._in["title"] = False

    def handle_data(self, data: str) -> None:
        if self._in["title"]:
            self.title += data
        self.text.append(data)


def _read(lang: str) -> _Page:
    page = _Page()
    page.feed((DOCS / PAGES[lang]).read_text(encoding="utf-8"))
    return page


def _url(lang: str) -> str:
    """Where *lang*'s page is published, as its folder: what a link to it names."""
    return urljoin(_SITE, PAGES[lang].removesuffix("index.html"))


def _resolved(lang: str, reference: str) -> str:
    """*reference*, as written in *lang*'s page, as the address it reaches."""
    return urljoin(urljoin(_SITE, PAGES[lang]), reference)


def _numbers(page: _Page) -> list[str]:
    """Every number the page states, a decimal comma read as a point."""
    text = " ".join(page.text)
    return sorted(token.replace(",", ".") for token in re.findall(r"\d+(?:[.,]\d+)*", text))


@pytest.fixture(scope="module")
def pages() -> dict[str, _Page]:
    return {lang: _read(lang) for lang in PAGES}


@pytest.mark.parametrize("lang", PAGES)
def test_each_page_declares_its_language(pages, lang):
    assert pages[lang].lang == lang


@pytest.mark.parametrize("lang", PAGES)
def test_each_page_is_the_english_one_element_for_element(pages, lang):
    """The same elements, ids and classes in the same order: a section, card, step or
    table row in one language and not in another fails here."""
    assert pages[lang].skeleton == pages["en"].skeleton


@pytest.mark.parametrize("lang", PAGES)
def test_each_page_offers_every_language(pages, lang):
    page = pages[lang]
    resolved = {other: _resolved(lang, href) for other, href in page.alternates.items()}
    assert resolved == {**{other: _url(other) for other in PAGES}, "x-default": _url("en")}
    switcher = {other: (_resolved(lang, href), current) for other, (href, current) in page.switcher.items()}
    assert switcher == {other: (_url(other), other == lang) for other in PAGES}


@pytest.mark.parametrize("lang", PAGES)
def test_every_local_reference_is_there(pages, lang):
    for reference, _to_a_language in pages[lang].references:
        address = urlparse(_resolved(lang, reference))
        if not address.geturl().startswith(_SITE):
            continue
        path = DOCS / address.path.lstrip("/")
        if address.path.endswith("/"):
            path = path / "index.html"
        assert path.is_file(), f"{PAGES[lang]}: {reference} reaches {path.relative_to(REPO_ROOT)}"
        if address.fragment:
            assert address.fragment in pages[lang].ids, f"{PAGES[lang]}: no #{address.fragment}"


def _places(pages: dict[str, _Page], lang: str) -> list[str]:
    """Where *lang*'s page links, the language links aside (above): a section of the
    page itself by its id, anything else by the address it reaches."""
    return sorted(
        reference if reference.startswith("#") else _resolved(lang, reference)
        for reference, to_a_language in pages[lang].references
        if not to_a_language
    )


@pytest.mark.parametrize("lang", PAGES)
def test_each_page_links_to_the_same_places(pages, lang):
    """The same links out, the same sections and the same assets, wherever the page
    sits in the site."""
    assert _places(pages, lang) == _places(pages, "en")


@pytest.mark.parametrize("lang", PAGES)
def test_each_page_states_the_same_numbers(pages, lang):
    """A figure changed in one language and not the others fails here: 48 algorithms,
    a 1.000 m blunder, 120 epochs with 117 fixed, QGIS 4.0."""
    assert _numbers(pages[lang]) == _numbers(pages["en"])


def test_each_page_is_in_its_own_words(pages):
    """Three titles, not one copied: a page left in English fails here."""
    titles = [pages[lang].title for lang in PAGES]
    assert len(set(titles)) == len(titles)
