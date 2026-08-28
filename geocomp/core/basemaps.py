# SPDX-License-Identifier: GPL-2.0-or-later
"""Base map services, as configurable records (FR-167, NFR-010).

``specs/17-persistence-and-interoperability.md`` section 5.6: *"the plugin
offers to add configured base map services, and honours the user's existing QGIS
layers and connections. No bundled imagery, no hard-coded service -- a
configurable list with sensible defaults."*

**A service is a record, not a setting.** It has a URL, an attribution, a zoom
range and possibly a reference to a credential -- the same shape as an
instrument profile, and for the same reason (``specs/15`` section 2.2): an
organisation owns several, distributes them to its staff as a file, and a single
"the" base map would be wrong for all but one job. So the catalogue lives here
and travels as a document; ``basemaps.catalogue`` in the settings names the file
that replaces the defaults.

**Credentials are never here** (NFR-010). A service needing authentication
stores ``auth_config_id``, which is a key into the QGIS authentication database
and is meaningless outside it. A username or a token in a catalogue file would
be copied into every export, every provenance record and every log the moment
someone shared their configuration -- which is exactly the accident the
requirement exists to prevent. :meth:`BaseMapService.to_dict` is what the file
and the provenance record are written from, and it cannot emit a secret because
none is stored.

**The defaults are defaults, not a bundled dependency.** Two services, both
openly licensed and both requiring attribution that this module carries with
them. Any of them can be removed and all of them replaced, which is what
"configurable list with sensible defaults" means. Nothing here downloads
anything; adding a layer is the QGIS layer's business
(:mod:`geocomp.visualization`, phase P5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from geocomp.core.errors import DataError, ValidationError

__all__ = [
    "DEFAULT_SERVICES",
    "BaseMapCatalogue",
    "BaseMapService",
    "ServiceKind",
    "load_catalogue",
]


class ServiceKind(Enum):
    """How QGIS should be asked to load the service."""

    #: Slippy-map tiles, ``{z}/{x}/{y}``. The common case.
    XYZ = "xyz"
    #: OGC Web Map Service.
    WMS = "wms"
    #: OGC Web Map Tile Service.
    WMTS = "wmts"


@dataclass(frozen=True)
class BaseMapService:
    """One configured base map.

    Attributes:
        id: Stable identifier, referenced by ``basemaps.default_service``.
        name: What the user sees. English here; the *services* are data, not
            interface text, so they are not translated -- an organisation's
            "Ortofoto 2023" should read the same in every language.
        url: The tile or service URL. For :attr:`ServiceKind.XYZ` this carries
            ``{z}``, ``{x}`` and ``{y}`` placeholders.
        attribution: **Required.** Every openly licensed tile service requires
            it, and a base map added without it puts the user in breach of the
            licence without telling them. A service that genuinely needs none
            says so with the string ``"none"`` rather than by leaving it empty,
            so the difference between "no attribution required" and "nobody
            filled this in" stays visible.
        auth_config_id: A QGIS authentication configuration id, never a
            credential (NFR-010). Empty for an open service.
        maximum_zoom: Above this the server returns nothing useful; QGIS
            over-zooms the last level instead of showing blank tiles.
    """

    id: str
    name: str
    url: str
    attribution: str
    kind: ServiceKind = ServiceKind.XYZ
    minimum_zoom: int = 0
    maximum_zoom: int = 19
    auth_config_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError(
                "basemap_without_id",
                expected="an id; `basemaps.default_service` refers to a service by it",
            )
        if not self.url.strip():
            raise ValidationError("basemap_without_url", service=self.id)
        if not self.attribution.strip():
            raise ValidationError(
                "basemap_without_attribution",
                service=self.id,
                expected=(
                    'the attribution the service requires, or the string "none" if it '
                    "genuinely requires none. Adding a base map without its attribution "
                    "puts the user in breach of the licence without telling them"
                ),
            )
        if self.kind is ServiceKind.XYZ and not all(
            token in self.url for token in ("{z}", "{x}", "{y}")
        ):
            raise ValidationError(
                "basemap_url_without_tile_tokens",
                service=self.id,
                received=self.url,
                expected="{z}, {x} and {y} in an XYZ tile URL",
            )
        if self.minimum_zoom < 0 or self.maximum_zoom < self.minimum_zoom:
            raise ValidationError(
                "basemap_zoom_range",
                service=self.id,
                received=[self.minimum_zoom, self.maximum_zoom],
                expected="0 <= minimum_zoom <= maximum_zoom",
            )
        if _looks_like_a_credential(self.url):
            raise ValidationError(
                "basemap_url_carries_a_credential",
                service=self.id,
                expected=(
                    "a URL with no embedded credential. Use auth_config_id, which names "
                    "an entry in the QGIS authentication database; a key in the URL is "
                    "copied into every export and every log (NFR-010)"
                ),
            )

    @property
    def needs_authentication(self) -> bool:
        return bool(self.auth_config_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialise for a catalogue file or a provenance record.

        Emits ``auth_config_id`` -- a reference, safe to record and useless to
        anyone without the user's authentication database -- and never anything
        that could be a credential, because none is stored (NFR-010).
        """
        payload: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "attribution": self.attribution,
            "kind": self.kind.value,
            "minimum_zoom": self.minimum_zoom,
            "maximum_zoom": self.maximum_zoom,
        }
        if self.auth_config_id:
            payload["auth_config_id"] = self.auth_config_id
        if self.meta:
            payload["meta"] = dict(self.meta)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BaseMapService:
        return cls(
            id=str(payload["id"]),
            name=str(payload.get("name", payload["id"])),
            url=str(payload["url"]),
            attribution=str(payload.get("attribution", "")),
            kind=ServiceKind(payload.get("kind", "xyz")),
            minimum_zoom=int(payload.get("minimum_zoom", 0)),
            maximum_zoom=int(payload.get("maximum_zoom", 19)),
            auth_config_id=str(payload.get("auth_config_id", "")),
            meta=dict(payload.get("meta", {})),
        )

    def uri(self) -> str:
        """The QGIS data-source URI for this service.

        Built here rather than in the GUI layer so it can be tested without
        QGIS: the escaping of ``&`` in a tile URL, which QGIS's XYZ provider
        requires, is the kind of detail that is wrong once and then wrong
        everywhere.
        """
        parts = [
            f"type={self.kind.value}",
            f"url={self.url.replace('&', '%26')}",
            f"zmin={self.minimum_zoom}",
            f"zmax={self.maximum_zoom}",
        ]
        if self.auth_config_id:
            parts.append(f"authcfg={self.auth_config_id}")
        return "&".join(parts)


def _looks_like_a_credential(url: str) -> bool:
    """Whether *url* embeds something that should be in the auth database.

    Deliberately shallow: it catches the two shapes that actually occur -- a
    ``user:password@host`` authority, and an API key as a query parameter -- and
    does not try to be a secret scanner. A check that tried to be exhaustive
    would produce false positives on legitimate service URLs, and a base map
    that refuses to load is a worse failure than the one it prevents.
    """
    authority = url.split("//", 1)[-1].split("/", 1)[0]
    if "@" in authority and ":" in authority.split("@", 1)[0]:
        return True
    lowered = url.lower()
    return any(
        f"{token}=" in lowered
        for token in ("apikey", "api_key", "access_token", "accesstoken", "subscriptionkey")
    )


#: Sensible defaults, per ``specs/17`` section 5.6. Both are openly licensed and
#: carry the attribution their licence requires. They are a starting list, not a
#: dependency: ``basemaps.catalogue`` replaces them wholesale.
DEFAULT_SERVICES: tuple[BaseMapService, ...] = (
    BaseMapService(
        id="osm",
        name="OpenStreetMap",
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution="© OpenStreetMap contributors",
        maximum_zoom=19,
    ),
    BaseMapService(
        id="opentopomap",
        name="OpenTopoMap",
        url="https://tile.opentopomap.org/{z}/{x}/{y}.png",
        attribution="© OpenStreetMap contributors, SRTM | © OpenTopoMap (CC-BY-SA)",
        maximum_zoom=17,
    ),
)


@dataclass(frozen=True)
class BaseMapCatalogue:
    """The configured services, in the order they are offered."""

    services: tuple[BaseMapService, ...] = DEFAULT_SERVICES

    def __post_init__(self) -> None:
        ids = [service.id for service in self.services]
        duplicated = sorted({name for name in ids if ids.count(name) > 1})
        if duplicated:
            raise ValidationError(
                "basemap_duplicate_id",
                received=duplicated,
                expected="one service per id; `basemaps.default_service` names one",
            )

    def service(self, service_id: str) -> BaseMapService:
        for service in self.services:
            if service.id == service_id:
                return service
        raise ValidationError(
            "basemap_not_configured",
            received=service_id,
            expected=[service.id for service in self.services],
        )

    def default(self, configured: str) -> BaseMapService | None:
        """The service ``basemaps.default_service`` names, or ``None``.

        ``None`` rather than the first service when the setting is empty: an
        unset default means *do not add one*, and quietly adding the first
        entry would put a layer on the user's canvas they never asked for.
        A configured id that is not in the catalogue is an error, not a
        fallback -- the user named something, and silently substituting is how
        a mandated aerial photo becomes a street map nobody noticed.
        """
        if not configured:
            return None
        return self.service(configured)

    def to_dict(self) -> dict[str, Any]:
        return {"services": [service.to_dict() for service in self.services]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BaseMapCatalogue:
        return cls(
            services=tuple(
                BaseMapService.from_dict(entry) for entry in payload.get("services", ())
            )
        )


def load_catalogue(path: str | Path | None) -> BaseMapCatalogue:
    """Read a catalogue file, or return the defaults when none is configured.

    Raises:
        DataError: ``basemap_catalogue_unreadable`` when the file is named but
            cannot be parsed. Falling back to the defaults would be worse than
            failing: the user configured a list, and quietly using a different
            one is how a project ends up with the wrong imagery.
    """
    if not path:
        return BaseMapCatalogue()

    file = Path(path)
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DataError(
            "basemap_catalogue_unreadable",
            path=str(file),
            reason=str(error),
            expected="a readable JSON catalogue, or no catalogue configured at all",
        ) from error

    return BaseMapCatalogue.from_dict(payload)
