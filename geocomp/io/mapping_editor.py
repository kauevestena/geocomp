# SPDX-License-Identifier: GPL-2.0-or-later
"""The state behind the field-mapping dialog (FR-160).

``specs/15-ui-menu-and-settings.md`` section 3 lists field mapping among the few
operations that need a custom dialog, because mapping columns is impossible
without seeing the data they contain.

This module is the dialog's *state*, with no Qt in it. The widget in
:mod:`geocomp.gui.mapping_dialog` renders it and calls into it; every decision
the dialog makes -- which fields are still missing, which column got assigned
twice, whether the mapping can be used -- is made here, where it can be tested
without QGIS.

That split is not ceremony. A mapping dialog is exactly where a wrong answer is
expensive and invisible: assigning ``hs`` to the horizontal seconds instead of
the target height produces a file that imports cleanly and means something else
entirely, and RD-01's own header contains both ``HS`` and ``hs``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace

from geocomp.core.findings import Finding, Severity
from geocomp.io.mapping import (
    FIELDS,
    AngleFormat,
    ColumnMapping,
    FieldMapping,
    infer_mapping,
)

__all__ = ["MappingEditor", "PreviewTable", "field_is_required"]

#: How many source rows the dialog shows. Enough to see the shape of the data
#: and to catch a column whose first row happens to look like another's.
PREVIEW_ROWS = 12


def field_is_required(field: str) -> bool:
    """Whether leaving *field* unmapped blocks the import.

    ``horizontal`` and ``zenith`` are required, but a sexagesimal triple
    supplies them, so the individual triple members are not themselves required
    and the dialog must not mark them as such.
    """
    from geocomp.io.mapping import REQUIRED_FIELDS

    return field in REQUIRED_FIELDS


@dataclass(frozen=True)
class PreviewTable:
    """The head of the source file: the header, and a few rows under it."""

    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def column(self, name: str) -> tuple[str, ...]:
        """The preview values of one source column, empty if there is no such
        column -- a mapping may name a column the file has since lost."""
        if name not in self.header:
            return ()
        index = self.header.index(name)
        return tuple(row[index] if index < len(row) else "" for row in self.rows)


class MappingEditor:
    """A field mapping under construction, with its problems.

    Starts from :func:`~geocomp.io.mapping.infer_mapping`, because a dialog
    that opened empty would make the common case -- a header GeoComp already
    understands -- the most laborious one.
    """

    def __init__(self, preview: PreviewTable, mapping: FieldMapping | None = None) -> None:
        self.preview = preview
        self._assignments: dict[str, ColumnMapping] = {}
        self.angle_format = AngleFormat.DECIMAL_DEGREES
        self.decimal_separator = "auto"
        self.name = ""
        self.load(mapping or infer_mapping(list(preview.header)))

    # -- state -----------------------------------------------------------

    def load(self, mapping: FieldMapping) -> None:
        """Replace the whole assignment, e.g. from a saved mapping file."""
        self._assignments = {
            column.field: column for column in mapping.columns if column.field in FIELDS
        }
        self.angle_format = mapping.angle_format
        self.decimal_separator = mapping.decimal_separator
        self.name = mapping.name

    def column_for(self, field: str) -> str:
        """The source column assigned to *field*, or the empty string."""
        assignment = self._assignments.get(field)
        return assignment.column or "" if assignment else ""

    def constant_for(self, field: str) -> float | None:
        assignment = self._assignments.get(field)
        return assignment.constant if assignment else None

    def unit_for(self, field: str) -> str:
        assignment = self._assignments.get(field)
        return assignment.unit if assignment else ""

    def assign(self, field: str, column: str) -> None:
        """Point *field* at a source column, or at nothing when empty.

        Assigning a column does not un-assign it elsewhere. A duplicate is
        reported instead, because which of the two the user meant is not
        something this can know, and silently clearing the other one would undo
        a choice they made deliberately.
        """
        if field not in FIELDS:
            raise KeyError(field)
        if not column:
            self._clear(field, keep_constant=True)
            return
        existing = self._assignments.get(field)
        self._assignments[field] = (
            replace(existing, column=column, constant=None)
            if existing
            else ColumnMapping(field=field, column=column)
        )

    def set_constant(self, field: str, constant: float | None) -> None:
        """Give *field* one value for every row -- an instrument height held
        all day, a temperature recorded once. A constant replaces a column,
        since a field cannot have both."""
        if field not in FIELDS:
            raise KeyError(field)
        if constant is None:
            self._clear(field, keep_constant=False)
            return
        self._assignments[field] = ColumnMapping(
            field=field, column=None, unit=self.unit_for(field), constant=constant
        )

    def set_unit(self, field: str, unit: str) -> None:
        existing = self._assignments.get(field)
        if existing is None:
            return
        self._assignments[field] = replace(existing, unit=unit)

    def _clear(self, field: str, *, keep_constant: bool) -> None:
        existing = self._assignments.get(field)
        if existing is None:
            return
        if keep_constant and existing.constant is not None:
            self._assignments[field] = replace(existing, column=None)
            return
        del self._assignments[field]

    # -- results ---------------------------------------------------------

    def mapping(self) -> FieldMapping:
        """The mapping as it stands, in the declared field order.

        Ordered by :data:`~geocomp.io.mapping.FIELDS` rather than by the order
        the user happened to touch them, so two people who make the same
        choices produce the same file.
        """
        return FieldMapping(
            name=self.name or "custom",
            columns=tuple(
                self._assignments[field] for field in FIELDS if field in self._assignments
            ),
            angle_format=self.angle_format,
            decimal_separator=self.decimal_separator,
        )

    def findings(self) -> tuple[Finding, ...]:
        """Everything wrong with the mapping, worst first.

        Every problem at once, not the first one: a user fixing a mapping wants
        to see the whole list, and a dialog that revealed them one at a time
        would turn one pass into five.
        """
        mapping = self.mapping()
        found: list[Finding] = []

        for field in mapping.missing_required():
            found.append(
                Finding(
                    code="required_field_unmapped",
                    severity=Severity.BLOCKING,
                    message=(
                        f"nothing supplies '{field}', and without it there is no "
                        "observation to import"
                    ),
                    observations=(field,),
                )
            )

        used = Counter(
            assignment.column for assignment in self._assignments.values() if assignment.column
        )
        for column, count in sorted(used.items()):
            if count > 1:
                fields = sorted(
                    field
                    for field, assignment in self._assignments.items()
                    if assignment.column == column
                )
                found.append(
                    Finding(
                        code="column_assigned_twice",
                        severity=Severity.BLOCKING,
                        message=(
                            f"column '{column}' is assigned to {' and '.join(fields)}. "
                            "One column cannot be two fields, and importing it as both "
                            "would double-count the measurement"
                        ),
                        observations=tuple(fields),
                    )
                )

        for column in mapping.unrecognised(list(self.preview.header)):
            found.append(
                Finding(
                    code="column_unmapped",
                    severity=Severity.INFO,
                    message=(
                        f"column '{column}' is not mapped to anything and will be ignored"
                    ),
                    observations=(column,),
                )
            )

        missing_columns = sorted(
            assignment.column
            for assignment in self._assignments.values()
            if assignment.column and assignment.column not in self.preview.header
        )
        for column in missing_columns:
            found.append(
                Finding(
                    code="mapped_column_absent",
                    severity=Severity.BLOCKING,
                    message=(
                        f"the mapping expects a column '{column}', which this file does "
                        "not have. A mapping saved for one export layout does not fit "
                        "another"
                    ),
                    observations=(column,),
                )
            )

        return tuple(sorted(found, key=lambda finding: -finding.severity.rank))

    @property
    def is_usable(self) -> bool:
        """Whether the mapping can be used. Informational findings do not
        block: an unmapped column is worth saying and not worth stopping for."""
        return not any(finding.is_blocking for finding in self.findings())
