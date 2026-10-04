# SPDX-License-Identifier: GPL-2.0-or-later
"""Which QGIS releases the tier-3 jobs run on (specs/21 criterion 5; ``scripts/qgis_versions.py``).

The matrix is decided when the workflow runs, from the QGIS images' own tags,
so that the LTR joins it the day it becomes a 4.x release. That decision is
only as good as these rules: a moving tag resolved by digest, never by a name
that merely looks like a release; a release below the plugin's minimum left
out and said so; and no matrix at all rather than an empty one.
"""

from __future__ import annotations

import pytest

from scripts.qgis_versions import UnresolvedError, minimum_version, resolve, same_release_line, select


def _tag(name: str, digest: str) -> dict:
    return {"name": name, "digest": f"sha256:{digest}"}


#: Docker Hub's listing as it stood on 3 October 2026, cut to what matters:
#: ``stable`` and ``ltr`` share digests with their releases and with the
#: distribution-suffixed and minor-only tags.
LISTING = [
    _tag("4.2.3-trixie", "56c6"),
    _tag("4.2.3", "8996"),
    _tag("4.2", "8996"),
    _tag("stable", "8996"),
    _tag("latest", "e243"),
    _tag("nightly", "e243"),
    _tag("3.44.15-noble", "497c"),
    _tag("3.44.15", "bacaf"),
    _tag("3.44", "bacaf"),
    _tag("ltr", "bacaf"),
    _tag("4.2.2", "6ffe"),
]


def test_a_channel_resolves_to_the_release_with_its_digest():
    assert resolve("stable", LISTING) == "4.2.3"
    assert resolve("ltr", LISTING) == "3.44.15"


def test_a_tag_that_only_looks_like_a_release_is_not_one():
    """``4.2`` shares stable's digest but names no release; ``4.2.3-trixie`` is another image."""
    listing = [_tag("stable", "8996"), _tag("4.2", "8996"), _tag("4.2.3-trixie", "8996")]
    with pytest.raises(UnresolvedError, match="no release tag"):
        resolve("stable", listing)


def test_a_channel_missing_from_the_listing_is_refused_rather_than_skipped():
    with pytest.raises(UnresolvedError, match="not in the listing"):
        resolve("ltr", [_tag("stable", "8996"), _tag("4.2.3", "8996")])


def test_releases_are_ordered_as_numbers_not_as_text():
    listing = [_tag("stable", "aa"), _tag("4.9.0", "aa"), _tag("4.10.0", "aa")]
    assert resolve("stable", listing) == "4.10.0"


def test_today_stable_alone_and_the_3x_ltr_reported():
    matrix, notes = select({"stable": "4.2.3", "ltr": "3.44.15"}, (4, 0, 0))
    assert matrix == {"include": [{"qgis": "4.2.3", "channel": "stable"}]}
    (note,) = notes
    assert "3.44.15" in note
    assert "ADR-0007" in note


def test_a_4x_ltr_joins_the_matrix_without_a_change():
    matrix, notes = select({"stable": "4.4.0", "ltr": "4.2.5"}, (4, 0, 0))
    assert matrix == {
        "include": [{"qgis": "4.4.0", "channel": "stable"}, {"qgis": "4.2.5", "channel": "ltr"}]
    }
    assert notes == []


def test_two_channels_on_one_release_run_once():
    matrix, notes = select({"stable": "4.2.5", "ltr": "4.2.5"}, (4, 0, 0))
    assert matrix == {"include": [{"qgis": "4.2.5", "channel": "stable, ltr"}]}
    assert len(notes) == 1


def test_a_stable_below_the_minimum_is_a_failure_not_an_empty_matrix():
    with pytest.raises(UnresolvedError, match=r"stable is 3\.44\.15"):
        select({"stable": "3.44.15", "ltr": "3.40.9"}, (4, 0, 0))


def test_the_floor_is_the_plugins_own_declaration():
    """The minimum QGIS enforces on install, not a number repeated in the workflow."""
    assert minimum_version() == (4, 0, 0)


def test_the_installed_qgis_is_the_release_its_job_names():
    assert same_release_line("4.2.3-Belém do Pará", "4.2.3") == (True, None)


def test_a_package_a_patch_behind_the_image_is_the_same_line_and_said_so():
    """Homebrew's cask was 4.2.2 the day the image was 4.2.3."""
    ok, note = same_release_line("4.2.2-Belém do Pará", "4.2.3")
    assert ok
    assert "4.2.2" in note and "4.2.3" in note


def test_another_release_line_is_not_the_channel_the_job_names():
    """A 3.44 LTR where a 4.2 LTR is expected would be tested and reported as 4.2."""
    assert same_release_line("3.44.14-Solothurn", "4.2.5")[0] is False
    assert same_release_line("4.0.3-Girona", "4.2.3")[0] is False


def test_on_linux_the_image_must_be_exactly_its_tag():
    assert same_release_line("4.2.2-Belém do Pará", "4.2.3", exact=True)[0] is False
