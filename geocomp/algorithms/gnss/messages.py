# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing wording for GNSS product resolution (``specs/08`` §5 and §9, phase P10c).

Each says what failed and what to do (NFR-006), and the three download failures
are kept apart because each has a different remedy (``specs/08`` §9): a product
the archive does not have yet, a login the archive refused, and a network that
did not answer. None of them carries a credential: services are named by id and
URLs are credential-free by construction (NFR-010).

Importing this module registers the templates; :mod:`geocomp.algorithms.gnss`
imports it.
"""

from __future__ import annotations

from geocomp.services.messages import MessageTemplate, register_template

__all__ = ["TEMPLATES"]

TEMPLATES: dict[str, MessageTemplate] = {
    "data.product_not_found": MessageTemplate(
        "The product %1 is not available from %2. A recent day's final orbit is "
        "published about two weeks later; allow rapid orbits in Global Settings → GNSS, "
        "add another download service, or place the file in the product directory.",
        "product",
        "services",
    ),
    "data.product_authentication_failed": MessageTemplate(
        "The archive refused the login for %1 (HTTP %2). Check the QGIS authentication "
        "configuration named for this service in the download services file.",
        "url",
        "status",
    ),
    "data.product_network_failed": MessageTemplate(
        "Could not download %1: %2. The download was retried; check the network and "
        "the proxy configured in QGIS, then run again.",
        "url",
        "reason",
    ),
    "data.product_corrupt": MessageTemplate(
        "The product %1 could not be decompressed (%2). It was not used; run again to "
        "download it afresh.",
        "product",
        "reason",
    ),
    "data.product_compression_unsupported": MessageTemplate(
        "The product %1 is compressed with Unix compress (.Z), which GeoComp does not "
        "read. Point the service at the .gz or uncompressed file.",
        "product",
    ),
    "validation.product_service_credential_in_url": MessageTemplate(
        "The download service '%1' has a user name, password or token in a URL. "
        "Credentials are never written into a URL, a setting or a log: remove it, and "
        "name a QGIS authentication configuration in the service's 'authcfg' instead.",
        "service",
    ),
    "validation.product_service_scheme": MessageTemplate(
        "The download service '%1' uses the URL scheme '%2'; use https, http or file.",
        "service",
        "received",
    ),
    "validation.product_service_malformed": MessageTemplate(
        "A download service could not be read: %1. Each needs an 'id', a 'name' and "
        "'templates' keyed like 'orbit/final'.",
        "received",
    ),
    "validation.product_service_id": MessageTemplate(
        "The download service id '%1' is empty or is the id of a service GeoComp ships. "
        "Give the service an id of its own.",
        "received",
    ),
    "validation.product_service_template_key": MessageTemplate(
        "The download service '%1' has templates for products GeoComp does not know: %2. "
        "Keys are a product and a latency, such as 'orbit/final', 'orbit/rapid' or "
        "'gps_navigation/broadcast'.",
        "service",
        "received",
    ),
}

for _code, _template in TEMPLATES.items():
    register_template(_code, _template)
