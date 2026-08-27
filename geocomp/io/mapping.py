# SPDX-License-Identifier: GPL-2.0-or-later
"""Field mappings: a first-class, saveable object (FR-160).

``specs/17-persistence-and-interoperability.md`` section 5.1.

**The mapping is the point, not the parsing.** The same organisation imports the
same instrument export layout every week, and re-mapping columns by hand each
time is precisely the *"inconsistências decorrentes da manipulação manual"* the
research project set out to eliminate. So a mapping is a named, serialisable
document that can be saved, reused and distributed to colleagues -- not a
dictionary assembled inside an import routine.

A mapping carries: which source column feeds which GeoComp field, the unit of
each column, how angles are laid out, the decimal separator, constant values
applied to every row, and rows to skip.

**No column is silently discarded.** A source column the mapping does not
mention is reported, because a column nobody mapped is either a field the user
forgot or a field GeoComp does not yet understand, and both are worth saying.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from geocomp.core.errors import ValidationError
from geocomp.core.units import convert, dimension_of

__all__ = [
    "ANGLE_FIELDS",
    "FIELDS",
    "REQUIRED_FIELDS",
    "AngleFormat",
    "ColumnMapping",
    "FieldMapping",
    "infer_mapping",
]


class AngleFormat(Enum):
    """How an angle is laid out across the source columns.

    ``SEXAGESIMAL_TRIPLE`` is RD-01's layout and the common one in field-book
    exports: three columns of degrees, minutes and seconds. The others exist
    because instrument software disagrees, and guessing wrong is a silent error
    of up to a factor of sixty.
    """

    DECIMAL_DEGREES = "decimal_degrees"
    #: One column, ``"179 59 56"`` or ``"179-59-56"`` or ``179°59'56\""``.
    SEXAGESIMAL_TEXT = "sexagesimal_text"
    #: Three columns.
    SEXAGESIMAL_TRIPLE = "sexagesimal_triple"
    GON = "gon"
    RADIANS = "radians"


#: The logical fields a field book can supply. Ids are stable: a saved mapping
#: stores them, so renaming one breaks every mapping a user has kept.
FIELDS: tuple[str, ...] = (
    "station",
    "backsight",
    "foresight",
    "target",
    "face",
    "sighted",
    "horizontal",
    "horizontal_degrees",
    "horizontal_minutes",
    "horizontal_seconds",
    "zenith",
    "zenith_degrees",
    "zenith_minutes",
    "zenith_seconds",
    "distance",
    "instrument_height",
    "target_height",
    "temperature",
    "pressure",
    "humidity",
    "set_number",
    "instrument_id",
    "reflector_id",
)

#: Fields whose value is an angle, so the mapping's angle format applies.
ANGLE_FIELDS = frozenset({"horizontal", "zenith"})

#: Without these there is no observation at all.
REQUIRED_FIELDS = frozenset({"station", "horizontal", "zenith"})


@dataclass(frozen=True)
class ColumnMapping:
    """One logical field, and where its value comes from.

    Attributes:
        field: One of :data:`FIELDS`.
        column: Source column name, or ``None`` when :attr:`constant` supplies
            the value for every row.
        unit: The unit the *source* is in. Values are converted once, here at
            the boundary, and stored in SI thereafter.
        constant: A value applied to every row. Instrument height recorded once
            on the cover of a field book rather than on every line is the
            routine case.
    """

    field: str
    column: str | None = None
    unit: str = ""
    constant: str | None = None

    def __post_init__(self) -> None:
        if self.field not in FIELDS:
            raise ValidationError(
                "unknown_mapping_field",
                received=self.field,
                expected=f"one of: {', '.join(FIELDS)}",
            )
        if self.column is None and self.constant is None:
            raise ValidationError(
                "mapping_without_source",
                field=self.field,
                expected="either a source column or a constant value",
            )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"field": self.field}
        for key, value in (
            ("column", self.column),
            ("unit", self.unit),
            ("constant", self.constant),
        ):
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ColumnMapping:
        return cls(
            field=payload["field"],
            column=payload.get("column"),
            unit=payload.get("unit", ""),
            constant=payload.get("constant"),
        )


@dataclass(frozen=True)
class FieldMapping:
    """A named, reusable description of one source layout (FR-160).

    Attributes:
        decimal_separator: ``"."``, ``","`` or ``"auto"``. Auto decides per
            value, which is safe only because a field book never uses a comma
            as a thousands separator -- a distance of ``1,234`` is 1.234 m, not
            1234 m. Stated here because the assumption is load-bearing.
        skip_rows: Rows to discard before the header, for exports that begin
            with a title block.
        face_values: Which source token means which face. Defaults to RD-01's
            ``PD`` / ``PI``; a Leica export says ``F1`` / ``F2``.
        sighted_values: Which token means the backsight and which the foresight.
    """

    name: str
    columns: tuple[ColumnMapping, ...] = ()
    angle_format: AngleFormat = AngleFormat.SEXAGESIMAL_TRIPLE
    decimal_separator: str = "auto"
    skip_rows: int = 0
    face_values: dict[str, str] = field(
        default_factory=lambda: {"PD": "direct", "PI": "reverse"}
    )
    sighted_values: dict[str, str] = field(
        default_factory=lambda: {"R": "backsight", "V": "foresight"}
    )
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError(
                "mapping_without_name",
                expected="a name; a mapping exists to be saved and reused by it",
            )
        if self.decimal_separator not in (".", ",", "auto"):
            raise ValidationError(
                "unknown_decimal_separator",
                received=self.decimal_separator,
                expected="'.', ',' or 'auto'",
            )
        if self.skip_rows < 0:
            raise ValidationError(
                "negative_skip_rows", received=self.skip_rows, expected="zero or more"
            )
        seen = [mapping.field for mapping in self.columns]
        duplicates = sorted({name for name in seen if seen.count(name) > 1})
        if duplicates:
            raise ValidationError(
                "duplicate_mapped_field",
                received=duplicates,
                expected="each GeoComp field mapped at most once",
            )

    # -- lookup ----------------------------------------------------------

    def for_field(self, name: str) -> ColumnMapping | None:
        for mapping in self.columns:
            if mapping.field == name:
                return mapping
        return None

    @property
    def mapped_fields(self) -> frozenset[str]:
        return frozenset(mapping.field for mapping in self.columns)

    @property
    def source_columns(self) -> frozenset[str]:
        return frozenset(m.column for m in self.columns if m.column is not None)

    def missing_required(self) -> tuple[str, ...]:
        """Required fields the mapping does not supply, in a stable order.

        ``horizontal`` and ``zenith`` count as supplied when the sexagesimal
        triple that composes them is mapped instead.
        """
        mapped = set(self.mapped_fields)
        for name in ANGLE_FIELDS:
            triple = {f"{name}_degrees", f"{name}_minutes", f"{name}_seconds"}
            if triple <= mapped:
                mapped.add(name)
        return tuple(sorted(REQUIRED_FIELDS - mapped))

    def unrecognised(self, header: list[str]) -> tuple[str, ...]:
        """Source columns the mapping does not mention.

        Reported, never discarded silently: a column nobody mapped is either a
        field the user forgot or one GeoComp does not yet understand.
        """
        return tuple(
            column for column in header if column and column not in self.source_columns
        )

    # -- value conversion ------------------------------------------------

    def parse_number(self, text: str, *, unit: str = "") -> float:
        """Parse a number from the source, honouring the decimal separator.

        Converted from the source unit to SI here, at the boundary, and stored
        in SI thereafter -- which is what makes FR-095 hold: a file written
        under a comma-decimal locale reads back identically under a
        period-decimal one.
        """
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("empty value")

        if self.decimal_separator == ",":
            cleaned = cleaned.replace(",", ".")
        elif self.decimal_separator == "auto" and "," in cleaned and "." not in cleaned:
            cleaned = cleaned.replace(",", ".")

        value = float(cleaned)
        return convert(value, unit, _si_name(unit)) if unit else value

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "columns": [mapping.to_dict() for mapping in self.columns],
            "angle_format": self.angle_format.name,
            "decimal_separator": self.decimal_separator,
            "face_values": dict(self.face_values),
            "sighted_values": dict(self.sighted_values),
        }
        if self.skip_rows:
            payload["skip_rows"] = self.skip_rows
        if self.description:
            payload["description"] = self.description
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FieldMapping:
        return cls(
            name=payload["name"],
            columns=tuple(ColumnMapping.from_dict(c) for c in payload.get("columns", ())),
            angle_format=AngleFormat[payload.get("angle_format", "SEXAGESIMAL_TRIPLE")],
            decimal_separator=payload.get("decimal_separator", "auto"),
            skip_rows=int(payload.get("skip_rows", 0)),
            face_values=dict(payload.get("face_values", {"PD": "direct", "PI": "reverse"})),
            sighted_values=dict(
                payload.get("sighted_values", {"R": "backsight", "V": "foresight"})
            ),
            description=payload.get("description", ""),
        )


def _si_name(unit: str) -> str:
    """The SI unit of the same dimension, for :func:`~geocomp.core.units.convert`."""
    return dimension_of(unit).symbol


#: Header names phase P3 knows how to guess, per logical field.
#:
#: **Matched case-sensitively first, then case-insensitively.** That is not
#: fussiness: RD-01's own header contains both ``HS`` (the seconds of the
#: horizontal angle) and ``hs`` (the target height), which differ only by case
#: and mean entirely different things. A case-insensitive guess maps one of them
#: to the other's field and leaves a column unrecognised, and the import then
#: fails for a reason that looks nothing like the cause.
#:
#: Deliberately short: a guess that is usually right and always reviewable beats
#: a clever one nobody can predict.
_ALIASES: dict[str, tuple[str, ...]] = {
    "station": ("E", "e", "est", "estacao", "estação", "station", "setup", "occupied", "at"),
    "backsight": ("R", "r", "re", "ré", "backsight", "bs", "from"),
    "foresight": ("V", "v", "vante", "foresight", "fs", "to"),
    "target": ("target", "point", "ponto", "pt"),
    "face": ("pos", "face", "posicao", "posição"),
    "sighted": ("vis", "sighted", "visada"),
    "horizontal_degrees": ("HG", "hg", "hz_deg", "h_deg"),
    "horizontal_minutes": ("HM", "hm", "hz_min", "h_min"),
    "horizontal_seconds": ("HS", "hz_sec", "h_sec"),
    "horizontal": ("H", "hz", "horizontal", "angulo_horizontal"),
    "zenith_degrees": ("VG", "vg", "z_deg", "v_deg"),
    "zenith_minutes": ("VM", "vm", "z_min", "v_min"),
    "zenith_seconds": ("VS", "vs", "z_sec", "v_sec"),
    "zenith": ("Z", "z", "zenith", "zenital", "vertical"),
    "distance": ("D", "d", "dist", "distance", "sd", "slope_distance", "di"),
    "instrument_height": ("hi", "ih", "instrument_height", "alt_inst"),
    "target_height": ("hs", "th", "target_height", "alt_alvo", "prism_height"),
    "temperature": ("T", "t", "temp", "temperature"),
    "pressure": ("P", "p", "press", "pressure"),
    "humidity": ("rh", "humidity", "umidade"),
    "set_number": ("set", "serie", "série", "repetition"),
}


def infer_mapping(header: list[str], *, name: str = "inferred") -> FieldMapping:
    """Guess a mapping from a header row, for the import dialog to show.

    A **starting point the user reviews**, never an automatic import. The guess
    is right for RD-01's layout and for the common instrument exports, and where
    it is wrong the dialog is where that gets fixed -- which is why FR-160 makes
    the mapping user-controlled rather than inferred.

    Two passes: exact column names first, then case-insensitive for whatever is
    still unclaimed. See :data:`_ALIASES` for why the order matters.
    """
    available = [column for column in header if column and column.strip()]
    columns: list[ColumnMapping] = []
    claimed: set[str] = set()
    assigned: set[str] = set()

    def take(logical: str, column: str) -> None:
        columns.append(ColumnMapping(field=logical, column=column))
        claimed.add(column)
        assigned.add(logical)

    for exact in (True, False):
        for logical, aliases in _ALIASES.items():
            if logical in assigned:
                continue
            candidates = aliases if exact else tuple(a.lower() for a in aliases)
            for column in available:
                if column in claimed:
                    continue
                key = column.strip() if exact else column.strip().lower()
                if key in candidates:
                    take(logical, column)
                    break

    triple = {"horizontal_degrees", "horizontal_minutes", "horizontal_seconds"}
    angle_format = (
        AngleFormat.SEXAGESIMAL_TRIPLE if triple <= assigned else AngleFormat.DECIMAL_DEGREES
    )

    # A triple layout has no use for a decimal angle column, and keeping both
    # would leave the mapping claiming to supply one field two ways.
    if angle_format is AngleFormat.SEXAGESIMAL_TRIPLE:
        columns = [c for c in columns if c.field not in ANGLE_FIELDS]

    return FieldMapping(name=name, columns=tuple(columns), angle_format=angle_format)


def _si_name(unit: str) -> str:
    """The SI unit of the same dimension, for :func:`~geocomp.core.units.convert`."""
    return dimension_of(unit).symbol
