# SPDX-License-Identifier: GPL-2.0-or-later
"""The spec's measurement-type table must cover the registry.

``specs/07-engine-dynadjust.md`` §4.2 calls its mapping table "the module's
contract", and says every row is confirmed. It was missing a row: nothing in it
mentioned ``HORIZONTAL_DISTANCE``, so the writer skipped it and a plane
trilateration network lost ten of its eleven observations without the spec ever
having considered the case.

A prose table and a Python registry drift because nothing makes them agree. This
makes them agree. It checks coverage, not correctness -- that a type is *listed*,
whether it maps or explicitly does not -- because the mapping itself is verified
against upstream in ``tests/test_dynaml_writer.py`` and a second copy of it here
would be one more thing to drift.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from geocomp.core.models.observation import OBSERVATION_TYPES, ObservationType

SPEC = Path(__file__).resolve().parents[2] / "specs" / "07-engine-dynadjust.md"

#: Rows of the §4.2 table look like ``| `TYPE` | X | **[V]** |``, and a row may
#: name more than one type: ``| `GRAVITY`, `GRAVITY_DIFFERENCE` | **none** | ...``
_ROW = re.compile(r"^\|((?:\s*`[A-Z_]+`(?:\s*\([^)]*\))?\s*,?)+)\|", re.MULTILINE)
_NAME = re.compile(r"`([A-Z_]+)`")


@pytest.fixture(scope="module")
def listed() -> set[str]:
    names: set[str] = set()
    for row in _ROW.findall(SPEC.read_text(encoding="utf-8")):
        names.update(_NAME.findall(row))
    return names


def test_the_table_was_found_at_all(listed: set[str]) -> None:
    """Guards the regex: an empty match would make every check below pass."""
    assert len(listed) > 10
    assert "GNSS_BASELINE" in listed


def test_every_observation_type_appears(listed: set[str]) -> None:
    """Including the ones that do not map. A type absent from the table is a
    case nobody decided about, which is how HORIZONTAL_DISTANCE came to be
    dropped silently."""
    missing = sorted(
        member.name for member in ObservationType if member.name not in listed
    )
    assert not missing, (
        f"specs/07 §4.2 does not mention: {missing}. Every GeoComp observation "
        "type needs a row, whether it maps to a DynAdjust type or explicitly "
        "does not."
    )


def test_the_table_names_no_type_that_does_not_exist(listed: set[str]) -> None:
    """The other direction: a row for a type that was renamed or removed."""
    known = {member.name for member in ObservationType}
    # The table also names DynAdjust's own types in prose; only rows whose first
    # cell is a GeoComp type are checked, and those must all exist.
    unknown = sorted(name for name in listed if name not in known)
    assert not unknown, f"specs/07 §4.2 names types that are not in the registry: {unknown}"


def test_the_types_with_no_code_are_the_ones_the_spec_explains() -> None:
    """Three types cannot reach DynAdjust, and each is discussed by name.

    Pinned as a set rather than a count: a fourth appearing silently is exactly
    the failure this module exists to catch, and it should fail here rather than
    in a user's adjustment.
    """
    unmapped = {
        member.name
        for member, spec in OBSERVATION_TYPES.items()
        if not spec.dynadjust_code
    }
    assert unmapped == {"GRAVITY", "GRAVITY_DIFFERENCE", "HORIZONTAL_DISTANCE"}

    text = SPEC.read_text(encoding="utf-8")
    for name in unmapped:
        assert f"`{name}`" in text, f"{name} has no DynAdjust type and the spec does not say why"
