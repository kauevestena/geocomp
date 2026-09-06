# SPDX-License-Identifier: GPL-2.0-or-later
"""Convert the *Adjust*-format reference corpus into GeoComp's own serialisation.

``specs/22-reference-data-sources.md`` section 4. The five networks of RD-12 are
published as ``.Adat`` files, and this repository vendors them as
``Network.to_dict()`` JSON instead: the *data* is CC BY 4.0 and free to
redistribute, and GeoComp's own serialisation is a documented format this
project already round-trips, so nothing is lost by carrying them in it.

The ``.Adat`` reader and writer still exist -- interoperability with the format
*is* FR-161 -- and ``tests/test_adjust.py`` exercises them by round trip. This
script is what produced the vendored files, kept so that the conversion is
reproducible rather than a one-off somebody ran once.

Usage::

    python3 scripts/convert_adjust_corpus.py --source /path/to/adat/files

The source files are not in the repository. Point ``--source`` at a directory
holding the ten files from the Mendeley record named in
``tests/data/adjust/PROVENANCE.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geocomp.core.models import ObservationType  # noqa: E402
from geocomp.core.uncertainty import Quantity  # noqa: E402
from geocomp.core.units import Unit  # noqa: E402
from geocomp.io.adjust import read_adjust  # noqa: E402

TARGET = ROOT / "tests" / "data" / "adjust"

#: ``<source stem>`` -> ``<vendored name>``. Only the halves that carry values;
#: the plan halves are read by the corpus test from the same source directory
#: when it is available, and are not vendored -- they hold no measurement.
NETWORKS = {
    "Poligonal AC dados": "traverse-ac",
    "Poligonal AD dados": "traverse-ad",
    "Poligonal BC Dados": "traverse-bc",
    "triangulateracao DADOS": "triangulateration",
    "MMEL dados": "free-stations",
}

#: ``MMEL dados.Adat`` declares 51 angles and holds 52. Its plan half declares
#: 52 of each and holds them, and the two differ by exactly one distance
#: (``EL10 16``): a row was removed and both counts were decremented, so the
#: angle count is wrong by one. The rows are the data; the header is a summary.
ACCEPT_COUNT_MISMATCH = {"MMEL dados"}

#: The six angles of the round at station 9 in the triangulateration carry the
#: values of the *next* row in the round -- a one-step cyclic displacement that
#: leaves the round's sum at 360 degrees, so a closure check cannot see it.
#: ``specs/22`` section 4.2 has the measurement. The corrected copy rotates the
#: values back; the faithful copy keeps them, because the blunder is the most
#: useful thing in the file (RD-12b).
ROTATED_ROUND = ("triangulateracao DADOS", "9")


def rotate_round_back(network, station: str):
    """Give each angle at *station* the value of the previous row in file order.

    Returns the number of observations changed. Observation ids are assigned in
    file order by the reader, so sorting by id recovers that order.
    """
    at_station = [
        observation
        for observation in sorted(
            network.observations.values(), key=lambda o: (o.id[0], int(o.id[1:]))
        )
        if observation.type is ObservationType.HORIZONTAL_ANGLE
        and observation.stations[0] == station
    ]
    values = [observation.value for observation in at_station]
    for index, observation in enumerate(at_station):
        previous = values[index - 1]
        network.observations[observation.id] = type(observation)(
            id=observation.id,
            type=observation.type,
            stations=observation.stations,
            values=(Quantity(previous.value, previous.variance, Unit.RADIAN),),
        )
    return len(at_station)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    arguments = parser.parse_args()

    TARGET.mkdir(parents=True, exist_ok=True)
    for stem, name in sorted(NETWORKS.items()):
        source = arguments.source / f"{stem}.Adat"
        if not source.is_file():
            print(f"  MISSING {source}", file=sys.stderr)
            return 1
        report = read_adjust(source, accept_count_mismatch=stem in ACCEPT_COUNT_MISMATCH)
        payload = {
            "title": report.title,
            "source_file": source.name,
            "declared": list(report.declared),
            "found": list(report.found),
            "control": list(report.control),
            "network": report.network.to_dict(),
        }
        path = TARGET / f"{name}.json"
        path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}  ({len(report.network.observations)} observations)")

        if stem == ROTATED_ROUND[0]:
            corrected = read_adjust(source).network
            changed = rotate_round_back(corrected, ROTATED_ROUND[1])
            payload = {
                "title": report.title + " (station 9 round de-rotated)",
                "source_file": source.name,
                "declared": list(report.declared),
                "found": list(report.found),
                "control": list(report.control),
                "correction": (
                    f"the {changed} angles at station {ROTATED_ROUND[1]} each carry the "
                    "value of the previous row in the file, undoing a one-step cyclic "
                    "displacement; see tests/data/adjust/PROVENANCE.md"
                ),
                "network": corrected.to_dict(),
            }
            path = TARGET / f"{name}-corrected.json"
            path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            print(f"  wrote {path.relative_to(ROOT)}  ({changed} angles rotated back)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
