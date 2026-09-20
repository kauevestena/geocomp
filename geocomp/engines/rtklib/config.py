# SPDX-License-Identifier: GPL-2.0-or-later
"""The ``rnx2rtkp`` configuration file (FR-354).

``specs/08-engine-rtklib.md`` section 2: **GeoComp invokes with ``-k <config>``
as the primary mechanism**, because a configuration file is reproducible,
storable in provenance, attachable to a bug report, and editable by the user in
Advanced mode. Command-line flags are used only where they have no
configuration-file equivalent -- the input files, the output path, and the time
window.

The format is RTKLIB's own: ``key = value`` with an optional ``#`` comment,
grouped by prefix (``pos1-`` the functional model, ``pos2-`` ambiguity
resolution, ``out-`` the output representation, ``stats-`` the stochastic
model). GeoComp writes only the options it has a reason to set and leaves the
rest to the engine's defaults, because a configuration file that restates every
default is one where a deliberate choice cannot be told from an accident.

**The comments are part of the contract.** Every value RTKLIB writes carries the
enumeration it came from, and a user editing the file in Advanced mode needs
them; a file written without them is one nobody can safely change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any

from geocomp.core.errors import ValidationError

__all__ = [
    "PROFILES",
    "PositioningMode",
    "RtklibConfig",
    "parse_config",
    "profile",
    "write_config",
]


class PositioningMode(Enum):
    """``pos1-posmode``, and the menu item each serves (``specs/11`` section 1)."""

    SINGLE = "single"
    DGPS = "dgps"
    KINEMATIC = "kinematic"
    STATIC = "static"
    MOVINGBASE = "movingbase"
    FIXED = "fixed"
    PPP_KINE = "ppp-kine"
    PPP_STATIC = "ppp-static"

    @property
    def is_ppp(self) -> bool:
        """Whether the FR-604 limitation notice applies.

        ``specs/08`` section 3: RTKLIB's PPP is substantially weaker than its
        relative positioning, and a silently degraded PPP solution used for a
        monitoring baseline is a real harm. The notice is the UI's to show; this
        is how it knows to.
        """
        return self in {PositioningMode.PPP_KINE, PositioningMode.PPP_STATIC}

    @property
    def is_relative(self) -> bool:
        """Whether a base station is needed at all."""
        return self in {
            PositioningMode.DGPS,
            PositioningMode.KINEMATIC,
            PositioningMode.STATIC,
            PositioningMode.MOVINGBASE,
        }


@dataclass(frozen=True)
class RtklibConfig:
    """The options GeoComp sets, as values rather than as text.

    Attributes:
        name: The profile this came from, carried into provenance so a result
            can be traced to the configuration that produced it rather than to
            a file that may since have been edited.
        extra: Anything not modelled here, written verbatim. The escape hatch
            that keeps a user in Advanced mode from being limited to the
            options this dataclass happens to know about (FR-325).
    """

    mode: PositioningMode = PositioningMode.STATIC
    name: str = ""
    frequencies: str = "l1+l2"
    solution_type: str = "forward"
    elevation_mask: float = 15.0
    ionosphere: str = "brdc"
    troposphere: str = "saas"
    ephemeris: str = "brdc"
    navigation_systems: int = 1
    ambiguity_mode: str = "continuous"
    ambiguity_threshold: float = 3.0
    output_format: str = "llh"
    output_header: bool = True
    output_options: bool = True
    time_format: str = "tow"
    degrees_format: str = "deg"
    height: str = "ellipsoidal"
    static_output: str = "all"
    base_position: tuple[float, float, float] | None = None
    base_position_type: str = "rinexhead"
    rover_position_type: str = "single"
    extra: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.elevation_mask < 0.0 or self.elevation_mask >= 90.0:
            raise ValidationError(
                "rtklib_elevation_mask_out_of_range",
                received=self.elevation_mask,
                expected="an elevation mask in [0, 90) degrees",
            )
        if self.output_format not in {"llh", "xyz", "enu", "nmea"}:
            raise ValidationError(
                "rtklib_output_format_unknown",
                received=self.output_format,
                expected="llh, xyz, enu or nmea",
            )
        if self.base_position_type not in _POSITION_TYPES:
            raise ValidationError(
                "rtklib_base_position_type_unknown",
                received=self.base_position_type,
                expected=f"one of {sorted(_POSITION_TYPES)}",
            )
        if self.base_position is not None and self.base_position_type not in {"llh", "xyz"}:
            raise ValidationError(
                "rtklib_base_position_needs_a_matching_type",
                received=self.base_position_type,
                expected=(
                    "llh or xyz when explicit base coordinates are given; "
                    "rnx2rtkp ignores the coordinates otherwise"
                ),
            )

    def settings(self) -> dict[str, str]:
        """The configuration as ordered ``key -> value`` pairs."""
        values: dict[str, str] = {
            "pos1-posmode": self.mode.value,
            "pos1-frequency": self.frequencies,
            "pos1-soltype": self.solution_type,
            "pos1-elmask": _number(self.elevation_mask),
            "pos1-ionoopt": self.ionosphere,
            "pos1-tropopt": self.troposphere,
            "pos1-sateph": self.ephemeris,
            "pos1-navsys": str(self.navigation_systems),
            "pos2-armode": self.ambiguity_mode,
            "pos2-arthres": _number(self.ambiguity_threshold),
            "out-solformat": self.output_format,
            "out-outhead": "on" if self.output_header else "off",
            "out-outopt": "on" if self.output_options else "off",
            "out-timeform": self.time_format,
            "out-degform": self.degrees_format,
            "out-height": self.height,
            "out-solstatic": self.static_output,
            # **Not optional, and the reason is worth stating.** Loading a
            # configuration file resets the base-station position to the option
            # table's default -- latitude 0, longitude 0, height 0 -- while the
            # command-line path takes it from the base's RINEX header. So
            # `rnx2rtkp -k <config>` and `rnx2rtkp -p 3` are *not* equivalent,
            # and a generated configuration that omits this puts the base in
            # the Gulf of Guinea. Measured: with it, 120 solutions from the
            # sample pair; without it, none. `specs/08` section 2 makes `-k` the
            # primary mechanism because it is reproducible -- omitting this
            # would have made it reproducibly wrong, and a base only slightly
            # wrong would succeed rather than fail.
            "ant1-postype": self.rover_position_type,
            "ant2-postype": self.base_position_type,
        }
        if self.base_position is not None:
            for index, value in enumerate(self.base_position, start=1):
                values[f"ant2-pos{index}"] = repr(float(value))
        values.update(self.extra)
        return values

    def with_options(self, **changes: Any) -> RtklibConfig:
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "mode": self.mode.value, "settings": self.settings()}


#: The comment RTKLIB writes beside each value, so a file GeoComp wrote can be
#: edited as safely as one RTKLIB wrote. Absent keys get no comment rather than
#: an invented one.
#: ``POSOPT`` in RTKLIB's ``options.c``.
_POSITION_TYPES = frozenset({"llh", "xyz", "single", "posfile", "rinexhead", "rtcm"})

_COMMENTS = {
    "pos1-posmode": "(0:single,1:dgps,2:kinematic,3:static,4:movingbase,5:fixed,6:ppp-kine,7:ppp-static)",
    "pos1-frequency": "(1:l1,2:l1+l2,3:l1+l2+l5)",
    "pos1-soltype": "(0:forward,1:backward,2:combined)",
    "pos1-elmask": "(deg)",
    "pos1-ionoopt": "(0:off,1:brdc,2:sbas,3:dual-freq,4:est-stec)",
    "pos1-tropopt": "(0:off,1:saas,2:sbas,3:est-ztd,4:est-ztdgrad)",
    "pos1-sateph": "(0:brdc,1:precise,2:brdc+sbas,3:brdc+ssrapc,4:brdc+ssrcom)",
    "pos1-navsys": "(1:gps+2:sbas+4:glo+8:gal+16:qzs+32:comp)",
    "pos2-armode": "(0:off,1:continuous,2:instantaneous,3:fix-and-hold)",
    "out-solformat": "(0:llh,1:xyz,2:enu,3:nmea)",
    "out-outhead": "(0:off,1:on)",
    "out-outopt": "(0:off,1:on)",
    "out-timeform": "(0:tow,1:hms)",
    "out-degform": "(0:deg,1:dms)",
    "out-height": "(0:ellipsoidal,1:geodetic)",
    "out-solstatic": "(0:all,1:single)",
    "ant1-postype": "(0:llh,1:xyz,2:single,3:posfile,4:rinexhead,5:rtcm)",
    "ant2-postype": "(0:llh,1:xyz,2:single,3:posfile,4:rinexhead,5:rtcm)",
}

#: Named profiles for the four menu modes (``specs/11`` section 1). Named so a
#: run records *which* configuration produced it and a comparison (FR-359) has
#: something to compare.
PROFILES: dict[str, RtklibConfig] = {
    "relative-static": RtklibConfig(
        name="relative-static", mode=PositioningMode.STATIC, static_output="all"
    ),
    "relative-kinematic": RtklibConfig(
        name="relative-kinematic", mode=PositioningMode.KINEMATIC
    ),
    "absolute-static": RtklibConfig(
        name="absolute-static",
        mode=PositioningMode.PPP_STATIC,
        ephemeris="precise",
        ionosphere="dual-freq",
        ambiguity_mode="off",
    ),
    "absolute-kinematic": RtklibConfig(
        name="absolute-kinematic",
        mode=PositioningMode.PPP_KINE,
        ephemeris="precise",
        ionosphere="dual-freq",
        ambiguity_mode="off",
    ),
}


def profile(name: str) -> RtklibConfig:
    """A named profile.

    Raises:
        ValidationError: naming every profile there is, because a caller that
            mistyped one needs the list more than it needs a traceback.
    """
    try:
        return PROFILES[name]
    except KeyError as error:
        raise ValidationError(
            "rtklib_profile_unknown",
            received=name,
            expected=f"one of {sorted(PROFILES)}",
        ) from error


def write_config(config: RtklibConfig, path: str | Path) -> Path:
    """Write *config* to *path* in RTKLIB's own format.

    Deterministic: the same configuration writes the same bytes, which is what
    lets NFR-007 hold for a run that is reproduced from its recorded
    configuration.
    """
    path = Path(path)
    lines = [
        "# rnx2rtkp options, written by GeoComp",
        f"# profile: {config.name or 'unnamed'}",
        "",
    ]
    for key, value in config.settings().items():
        comment = _COMMENTS.get(key, "")
        entry = f"{key:<19}={value:<11}"
        lines.append(f"{entry} # {comment}".rstrip() if comment else entry.rstrip())
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


_SETTING = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=\s*([^#]*?)\s*(?:#.*)?$")


def parse_config(text: str) -> dict[str, str]:
    """Read an RTKLIB options file back into ``key -> value``.

    For the round trip ``specs/08`` section 10 criterion 2 requires, and for
    reading a file the user edited in Advanced mode (FR-325). Comments and blank
    lines are dropped; a key with an empty value is **kept**, because in this
    format that is how a field separator or an exclusion list is set to nothing.
    """
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = _SETTING.match(line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _number(value: float) -> str:
    """Trim a float that is really an integer, as RTKLIB's own files do."""
    return str(int(value)) if float(value).is_integer() else repr(float(value))
