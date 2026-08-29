# SPDX-License-Identifier: GPL-2.0-or-later
"""The fixed-width column machinery DynAdjust's text outputs are laid out on.

``specs/07-engine-dynadjust.md`` section 5. The Guide specifies each output file
column by column (Appendix C.7 to C.10), and those tables -- not one sample
file -- are what the parsers are written against. The widths below are the same
constants the writer uses, transcribed from
``dynadjust/include/config/dnaconsts-iostream.hpp`` at upstream commit
``5cdb897``, with the C++ names kept so the two can be compared by eye.

**No table here has a fixed layout.** Which columns appear depends on the run:
``--stn-coord-types`` chooses the coordinate columns and their widths,
``--stn-corrections`` adds three, ``--output-tstat-adj-msr`` and
``--output-database-ids`` add more, and ``--output-apu-vcv-units`` renames three.
A parser with hard-coded offsets reads the wrong column the first time a caller
changes a flag, and reads it as a *plausible number* rather than failing. So the
plan is built from the file's own column-header line every time, and a header
that does not match a known layout is refused rather than guessed at.

**A long station name has no delimiter after it.** The writer uses
``std::setw(STATION)``, which pads but never truncates, and station names may be
up to ``STN_NAME_WIDTH`` (31) characters. A 21-character name therefore runs
straight into the next field:

.. code-block:: text

    A STATION WITH SPACESCCC   -36.331031467  145.585707313 ...
    ^-------- name --------^^-^
                            constraint, with no space before it

and names may themselves contain spaces, so splitting on whitespace is no better
than slicing. That makes the name field genuinely ambiguous in the general case.
It is *not* ambiguous when the caller knows which names it wrote -- which GeoComp
always does, because it wrote the input files -- so :func:`take_name` resolves
against a known set when one is supplied, and reports the ambiguity rather than
inventing a split when one is not.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from geocomp.core.errors import DataError

__all__ = [
    "Column",
    "ColumnPlan",
    "NameResolution",
    "take_name",
]

# Widths, from dnaconsts-iostream.hpp. The C++ names are kept deliberately.
PAD2 = 2
PAD3 = 3
STATION = 20
MSR = 19
OUTLIER = 12
PACORR = 14
CORR = 12
PREC = 13
REL = 12
STAT = 11
CONSTRAINT = 5
LAT_EAST = 14
LON_NORTH = 15
HEIGHT = 11
ZONE = 8
XYZ = 15
STDDEV = 10

#: Widest a station name may be, from ``dnatypes-basic.hpp``
#: (``STN_NAME_WIDTH`` is 31 including the terminator, so 30 characters).
NAME_WIDTH = 30


@dataclass(frozen=True)
class Column:
    """One field of a fixed-width row.

    ``label`` is what the writer prints in the column-header line, which is how
    a plan is checked against a file. ``align`` is the writer's justification;
    it is carried because it decides where an over-wide value overflows to.
    """

    label: str
    width: int
    align: str = "r"

    def header(self) -> str:
        return self.label.ljust(self.width) if self.align == "l" else self.label.rjust(self.width)


@dataclass(frozen=True)
class ColumnPlan:
    """An ordered set of columns, with the offsets they occupy."""

    columns: tuple[Column, ...]

    @property
    def width(self) -> int:
        return sum(column.width for column in self.columns)

    def offsets(self) -> tuple[tuple[int, int], ...]:
        bounds: list[tuple[int, int]] = []
        start = 0
        for column in self.columns:
            bounds.append((start, start + column.width))
            start += column.width
        return tuple(bounds)

    def header(self) -> str:
        return "".join(column.header() for column in self.columns)

    def index(self, label: str) -> int:
        for position, column in enumerate(self.columns):
            if column.label == label:
                return position
        raise KeyError(label)

    def matches(self, line: str) -> bool:
        """Does *line* look like this plan's column-header line?

        Compared right-stripped: the writer's final column is followed by
        nothing, and trailing blanks in a file are not worth failing over.
        """
        return line.rstrip() == self.header().rstrip()

    def fields(self, line: str) -> tuple[str, ...]:
        """Slice *line* into stripped fields.

        A short line -- the writer omits trailing blanks -- yields empty strings
        for the columns past its end rather than raising, so an optional
        trailing column that was never written reads as absent.
        """
        return tuple(line[start:end].strip() for start, end in self.offsets())

    def value(self, line: str, label: str) -> str:
        start, end = self.offsets()[self.index(label)]
        return line[start:end].strip()


@dataclass(frozen=True)
class NameResolution:
    """Where a station name ended, and whether that was known or inferred."""

    name: str
    end: int
    #: ``True`` when the name was matched against a known set, ``False`` when it
    #: was taken from the column width. An inferred name is right whenever the
    #: name is shorter than its column, which is the ordinary case.
    resolved: bool


def take_name(line: str, *, width: int = STATION, known: Iterable[str] | None = None) -> NameResolution:
    """Read the station name that starts at the beginning of *line*.

    With *known* supplied, the longest member of it that the line starts with
    wins -- longest first, so ``BEEC`` never shadows ``BEECROFT``. Without it,
    the name is the first *width* characters, which is correct unless the name
    fills or overflows its column; in that case the field is genuinely
    ambiguous and this raises rather than returning a name it cannot justify.
    """
    if known is not None:
        for candidate in sorted(known, key=len, reverse=True):
            if candidate and line.startswith(candidate):
                return NameResolution(candidate, len(candidate), resolved=True)
        raise DataError(
            "dynadjust_unknown_station_in_output",
            line=line[:width].strip(),
            hint="the output names a station that was not in the input GeoComp wrote",
        )

    field = line[:width]
    if len(field) == width and not field.endswith(" "):
        raise DataError(
            "dynadjust_station_name_fills_its_column",
            line=line[: width + 8],
            width=width,
            hint=(
                "the name is at least as wide as its column, so it runs into the "
                "next field with no separator; pass the known station names to "
                "resolve it"
            ),
        )
    return NameResolution(field.strip(), width, resolved=False)


def require_header(lines: Sequence[str], plan: ColumnPlan, *, what: str) -> int:
    """Index of *plan*'s column-header line in *lines*, or a refusal.

    The refusal carries both headers because the useful question when a parser
    meets an unfamiliar file is *which column moved*, and that is answerable
    only by seeing the two side by side (specs/07 section 5 rule 1).
    """
    for index, line in enumerate(lines):
        if plan.matches(line):
            return index
    candidates = [line for line in lines if line.startswith(plan.columns[0].label)]
    raise DataError(
        "dynadjust_unrecognised_output_layout",
        table=what,
        expected=plan.header().rstrip(),
        found=candidates[0].rstrip() if candidates else None,
        hint="the file was written by a DynAdjust whose column layout this parser does not know",
    )
