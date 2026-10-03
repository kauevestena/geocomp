#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Which QGIS releases the tier-3 jobs run on (specs/21 criterion 5, ADR-0007).

Criterion 5 asks for the QGIS tier on the current LTR and the current stable.
ADR-0007 reads NFR-001 as the 4.x series: the current 4.x LTR once one exists,
the current stable until then. The QGIS project's container images name both
-- ``qgis/qgis:stable`` and ``qgis/qgis:ltr`` -- and when this was written
``ltr`` was 3.44, a Qt 5 QGIS that the plugin's ``qgisMinimumVersion`` refuses.

So the set is decided each time the workflow runs, not written into it:

* each moving tag is resolved, through Docker Hub's tag listing, to the
  release tag with the same digest (``stable`` -> ``4.2.3``);
* a release below the plugin's ``qgisMinimumVersion`` is reported and left out;
* two channels on the same release are run once.

The jobs then use the release tag, so each job's name says which QGIS it
tested, and a tag that moves while the workflow runs cannot change that. When
4.2 becomes the LTR, the matrix gains it with no change here.

Writes ``matrix=<json>`` to ``$GITHUB_OUTPUT`` (and prints it), in the form
``{"include": [{"qgis": "4.2.3", "channel": "stable"}]}``. Exit 1 when a
channel cannot be resolved or stable is below the minimum (there would be
nothing to test, and an empty matrix is a green tick for nothing); exit 2 when
Docker Hub cannot be reached.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY = "qgis/qgis"
CHANNELS = ("stable", "ltr")
LISTING = f"https://hub.docker.com/v2/repositories/{REPOSITORY}/tags?page_size=100&ordering=last_updated"
#: Pages of the listing to read before giving up: the release tag is pushed
#: with its channel tag, so it is on the first page in practice.
PAGES = 5

RELEASE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
METADATA = Path(__file__).resolve().parent.parent / "geocomp" / "metadata.txt"


class UnresolvedError(Exception):
    """A channel tag that no release tag shares a digest with."""


def minimum_version(metadata: Path = METADATA) -> tuple[int, ...]:
    """The plugin's own ``qgisMinimumVersion``: the floor is the one QGIS enforces."""
    for line in metadata.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "qgisMinimumVersion":
            return version_tuple(value.strip())
    raise ValueError(f"{metadata} declares no qgisMinimumVersion")


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def resolve(channel: str, listing: list[dict]) -> str:
    """The release (``X.Y.Z``) whose image is the one *channel* names.

    Matched by digest, which is what makes two tags the same image; a tag that
    only looks like a release (``4.2``, ``4.2.3-trixie``) is not one.
    """
    digests = {entry.get("name"): entry.get("digest") for entry in listing}
    digest = digests.get(channel)
    if not digest:
        raise UnresolvedError(f"{REPOSITORY}:{channel} is not in the listing")
    releases = sorted(
        (version_tuple(name), name)
        for name, other in digests.items()
        if name and other == digest and RELEASE.match(name)
    )
    if not releases:
        raise UnresolvedError(f"no release tag of {REPOSITORY} has the digest of {channel} ({digest})")
    return releases[-1][1]


def select(releases: dict[str, str], minimum: tuple[int, ...]) -> tuple[dict, list[str]]:
    """The matrix for *releases* (channel -> release), and what to report about it."""
    notes: list[str] = []
    include: list[dict] = []
    for channel in CHANNELS:
        release = releases[channel]
        if version_tuple(release) < minimum:
            floor = ".".join(str(part) for part in minimum)
            if channel == "stable":
                raise UnresolvedError(f"QGIS stable is {release}, below the plugin's minimum {floor}")
            notes.append(
                f"QGIS {channel} is {release}, below the plugin's minimum {floor} "
                "(ADR-0007): the QGIS tier runs on stable alone until a 4.x LTR exists"
            )
            continue
        same = next((row for row in include if row["qgis"] == release), None)
        if same is not None:
            notes.append(f"QGIS {channel} is {release}, the same release as {same['channel']}: run once")
            same["channel"] += f", {channel}"
            continue
        include.append({"qgis": release, "channel": channel})
    return {"include": include}, notes


def fetch_listing(*, pages: int = PAGES) -> list[dict]:
    listing: list[dict] = []
    url: str | None = LISTING
    for _ in range(pages):
        if url is None:
            break
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.load(response)
        listing.extend(page.get("results", []))
        url = page.get("next")
    return listing


def main() -> int:
    try:
        listing = fetch_listing()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"::error::Docker Hub's tag listing for {REPOSITORY} could not be read: {error}")
        return 2
    try:
        releases = {channel: resolve(channel, listing) for channel in CHANNELS}
        matrix, notes = select(releases, minimum_version())
    except UnresolvedError as error:
        print(f"::error::{error}")
        return 1
    for channel, release in releases.items():
        print(f"{REPOSITORY}:{channel} is {release}")
    for note in notes:
        print(f"::notice::{note}")
    line = "matrix=" + json.dumps(matrix, separators=(",", ":"))
    print(line)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
