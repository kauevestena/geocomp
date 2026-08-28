# SPDX-License-Identifier: GPL-2.0-or-later
"""Base map services (FR-167) and the credential rule they must not break (NFR-010).

``specs/17-persistence-and-interoperability.md`` section 5.6. The services are
records rather than settings, so they get the treatment records get: validation
that refuses the states that would produce a wrong or unlicensed layer, and a
serialisation that cannot leak a secret because none is stored.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geocomp.core.basemaps import (
    DEFAULT_SERVICES,
    BaseMapCatalogue,
    BaseMapService,
    ServiceKind,
    load_catalogue,
)
from geocomp.core.errors import DataError, ValidationError


def service(**kwargs: object) -> BaseMapService:
    defaults: dict[str, object] = {
        "id": "aerial",
        "name": "Aerial 2023",
        "url": "https://tiles.example.org/{z}/{x}/{y}.png",
        "attribution": "© Example",
    }
    defaults.update(kwargs)
    return BaseMapService(**defaults)  # type: ignore[arg-type]


# -- validation -----------------------------------------------------------


def test_a_service_without_attribution_is_refused() -> None:
    """Adding a base map without it puts the user in breach of the licence."""
    with pytest.raises(ValidationError) as excinfo:
        service(attribution="  ")
    assert excinfo.value.code == "validation.basemap_without_attribution"


def test_no_attribution_required_is_said_rather_than_left_blank() -> None:
    """So "none required" stays distinguishable from "nobody filled this in"."""
    assert service(attribution="none").attribution == "none"


def test_an_xyz_url_without_tile_tokens_is_refused() -> None:
    with pytest.raises(ValidationError) as excinfo:
        service(url="https://tiles.example.org/map.png")
    assert excinfo.value.code == "validation.basemap_url_without_tile_tokens"


def test_a_wms_url_needs_no_tile_tokens() -> None:
    wms = service(kind=ServiceKind.WMS, url="https://example.org/wms?service=WMS")
    assert wms.kind is ServiceKind.WMS


def test_an_impossible_zoom_range_is_refused() -> None:
    with pytest.raises(ValidationError) as excinfo:
        service(minimum_zoom=12, maximum_zoom=4)
    assert excinfo.value.code == "validation.basemap_zoom_range"


# -- NFR-010: credentials never live here ---------------------------------


def test_an_api_key_in_the_url_is_refused() -> None:
    """It would be copied into every export, provenance record and log."""
    with pytest.raises(ValidationError) as excinfo:
        service(url="https://tiles.example.org/{z}/{x}/{y}.png?apikey=s3cret")
    assert excinfo.value.code == "validation.basemap_url_carries_a_credential"


def test_a_password_in_the_authority_is_refused() -> None:
    with pytest.raises(ValidationError) as excinfo:
        service(url="https://user:hunter2@tiles.example.org/{z}/{x}/{y}.png")
    assert excinfo.value.code == "validation.basemap_url_carries_a_credential"


@pytest.mark.parametrize(
    "url",
    [
        "https://tiles.example.org/{z}/{x}/{y}.png",
        "https://tiles.example.org/{z}/{x}/{y}.png?style=grey&lang=pt",
        "https://tiles.example.org:8443/{z}/{x}/{y}.png",
    ],
)
def test_ordinary_urls_are_not_flagged(url: str) -> None:
    """A base map that refuses to load is worse than the accident it prevents."""
    assert service(url=url).url == url


def test_authentication_goes_through_an_auth_config_reference() -> None:
    authenticated = service(auth_config_id="qgis_auth_7f2a1c")
    assert authenticated.needs_authentication
    assert "authcfg=qgis_auth_7f2a1c" in authenticated.uri()


def test_the_serialisation_carries_a_reference_and_no_secret() -> None:
    payload = service(auth_config_id="qgis_auth_7f2a1c").to_dict()
    assert payload["auth_config_id"] == "qgis_auth_7f2a1c"
    text = json.dumps(payload)
    assert "hunter2" not in text and "apikey" not in text.lower()


def test_an_open_service_serialises_without_the_auth_key_at_all() -> None:
    assert "auth_config_id" not in service().to_dict()


# -- the QGIS URI, built here so it can be tested here --------------------


def test_the_uri_escapes_the_ampersands_qgis_would_otherwise_split_on() -> None:
    built = service(url="https://tiles.example.org/{z}/{x}/{y}.png?a=1&b=2").uri()
    assert "a=1%26b=2" in built
    # The URI's own separators survive: three besides the url.
    assert built.startswith("type=xyz&url=")
    assert "zmin=0" in built and "zmax=19" in built


def test_the_uri_round_trips_through_a_dictionary() -> None:
    original = service(auth_config_id="cfg", minimum_zoom=3, maximum_zoom=17)
    assert BaseMapService.from_dict(original.to_dict()).uri() == original.uri()


# -- the catalogue --------------------------------------------------------


def test_the_defaults_are_valid_and_attributed() -> None:
    """They are constructed at import, so a broken one breaks the plugin."""
    assert len(DEFAULT_SERVICES) >= 2
    for entry in DEFAULT_SERVICES:
        assert entry.attribution.strip()
        assert not entry.needs_authentication


def test_duplicate_ids_are_refused() -> None:
    with pytest.raises(ValidationError) as excinfo:
        BaseMapCatalogue(services=(service(id="a"), service(id="a", name="Other")))
    assert excinfo.value.code == "validation.basemap_duplicate_id"


def test_an_unset_default_adds_nothing() -> None:
    """Not "the first one": an unset default means do not add a layer at all."""
    assert BaseMapCatalogue().default("") is None


def test_a_configured_default_that_is_missing_is_an_error_not_a_fallback() -> None:
    """Substituting is how a mandated aerial photo becomes a street map."""
    with pytest.raises(ValidationError) as excinfo:
        BaseMapCatalogue().default("ortofoto-2023")
    assert excinfo.value.code == "validation.basemap_not_configured"
    assert "osm" in str(excinfo.value)


def test_a_catalogue_file_replaces_the_defaults(tmp_path: Path) -> None:
    path = tmp_path / "basemaps.json"
    path.write_text(
        json.dumps({"services": [service(id="ortofoto").to_dict()]}), encoding="utf-8"
    )
    catalogue = load_catalogue(path)
    assert [entry.id for entry in catalogue.services] == ["ortofoto"]


def test_no_configured_catalogue_gives_the_defaults() -> None:
    assert load_catalogue(None).services == DEFAULT_SERVICES
    assert load_catalogue("").services == DEFAULT_SERVICES


def test_an_unreadable_catalogue_is_reported_not_replaced(tmp_path: Path) -> None:
    """The user configured a list; quietly using a different one is worse."""
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(DataError) as excinfo:
        load_catalogue(path)
    assert excinfo.value.code == "data.basemap_catalogue_unreadable"


def test_a_missing_catalogue_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(DataError) as excinfo:
        load_catalogue(tmp_path / "absent.json")
    assert excinfo.value.code == "data.basemap_catalogue_unreadable"
