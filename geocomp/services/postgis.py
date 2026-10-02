# SPDX-License-Identifier: GPL-2.0-or-later
"""PostGIS project stores through the QGIS connection registry (FR-131, NFR-010).

``specs/17-persistence-and-interoperability.md`` section 4: *reading a PostGIS
store uses the QGIS connection registry, so GeoComp inherits the user's existing
connections and credentials handling rather than asking again*.

A connection is named, as it is in the QGIS browser. Its URI may carry a user
name and password, or -- better -- the id of a QGIS authentication
configuration; either way :meth:`QgsDataSourceUri.connectionInfo` with
``expandAuthConfig`` turns it into the libpq string the driver needs, **in
memory and only for the call that opens the connection**. GeoComp never stores
it, logs it, or names a store by it: the store's label is the connection's name
and the schema, which say where the project is and nothing a reader should not
see.
"""

from __future__ import annotations

from typing import Any

from qgis.core import QgsDataSourceUri, QgsProviderRegistry

from geocomp.core.errors import DataError

__all__ = ["connection_names", "open_database_store", "store_label"]

PROVIDER = "postgres"


def connection_names() -> list[str]:
    """The PostgreSQL connections saved in QGIS, by name."""
    metadata = QgsProviderRegistry.instance().providerMetadata(PROVIDER)
    if metadata is None:
        return []
    return sorted(metadata.connections())


def store_label(connection_name: str, schema: str) -> str:
    """How a PostGIS store is named to the user: never by its connection string."""
    return f"{connection_name} / {schema}"


def _conninfo(connection_name: str) -> str:
    metadata = QgsProviderRegistry.instance().providerMetadata(PROVIDER)
    connections = metadata.connections() if metadata is not None else {}
    if connection_name not in connections:
        raise DataError(
            "postgis_connection_unknown",
            received=connection_name,
            expected=(
                "the name of a PostgreSQL connection saved in QGIS (Browser > "
                f"PostgreSQL); saved: {', '.join(sorted(connections)) or 'none'}"
            ),
        )
    uri = QgsDataSourceUri(connections[connection_name].uri())
    return uri.connectionInfo(True)


def open_database_store(
    connection_name: str,
    schema: str,
    *,
    create: bool = False,
    migrate_older: bool = False,
) -> Any:
    """Open the project in *schema* of a QGIS-saved PostgreSQL connection."""
    from geocomp.io.store.postgis import open_postgis_store

    return open_postgis_store(
        _conninfo(connection_name),
        schema,
        create=create,
        migrate_older=migrate_older,
        label=store_label(connection_name, schema),
    )
