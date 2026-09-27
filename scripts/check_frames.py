#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check GeoComp's frame transformations against PROJ (``specs/13`` criterion 4).

``geocomp/core/geodesy/frames.py`` computes the IERS transformations in-house,
from the EPSG parameters it copies. This is the independent check: pyproj
transforms the same points between the same frames at the same epochs, and the
two must agree to a micrometre.

The PROJ results are committed as ``tests/data/frames/proj_reference.json``, so
the tier-1 test compares against them wherever Python runs; this script, run in
the ``reference`` workflow, recomputes them with a real PROJ and fails if either
GeoComp or the fixture has drifted. It also checks that PROJ used the
**same** EPSG operation GeoComp did -- agreeing with a different transformation
would be a coincidence, not a check.

Usage::

    python scripts/check_frames.py            # check
    python scripts/check_frames.py --write    # regenerate the fixture
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from geocomp.core.geodesy.frames import transform_point, transformation_path  # noqa: E402

FIXTURE = ROOT / "tests" / "data" / "frames" / "proj_reference.json"

#: Geocentric CRS of each frame, which is what PROJ transforms between.
GEOCENTRIC = {
    "ITRF2000": "EPSG:4919",
    "ITRF2005": "EPSG:4896",
    "ITRF2008": "EPSG:5332",
    "ITRF2014": "EPSG:7789",
    "ITRF2020": "EPSG:9988",
    "SIRGAS2000": "EPSG:4988",
}
ITRF = ("ITRF2000", "ITRF2005", "ITRF2008", "ITRF2014", "ITRF2020")

#: Curitiba, Manaus, and a point near the North Pole where the scale and
#: rotation terms are largest relative to the translation.
POINTS = {
    "curitiba": (3763788.2, -4367643.4, -2720372.5),
    "manaus": (3179008.1, -5043535.7, -337451.2),
    "north": (1100000.0, 700000.0, 6260000.0),
}
EPOCHS = (2000.0, 2000.4, 2010.0, 2015.0, 2024.5)

#: A micrometre. The arithmetic is exact to far better; anything larger is a
#: parameter copied wrongly, a unit, a sign or a convention.
TOLERANCE = 1e-6


def cases() -> list[dict]:
    found = []
    for source in ITRF:
        for target in ITRF:
            if source == target:
                continue
            for name, xyz in POINTS.items():
                for epoch in EPOCHS:
                    found.append(
                        {"source": source, "target": target, "point": name, "xyz": xyz, "epoch": epoch}
                    )
    # SIRGAS 2000 is ITRF2000 at 2000.4 and only there. PROJ 9.4 lists that
    # operation (EPSG:9052, method 1065) as *unavailable* and offers a no-op
    # "ballpark" instead, which agrees only because 9052 is the identity. These
    # cases therefore check consistency, not the operation; what the frame
    # module does for SIRGAS 2000 that matters -- refusing another epoch
    # without a velocity -- is tested in tier 1.
    for name, xyz in POINTS.items():
        found.append(
            {"source": "ITRF2000", "target": "SIRGAS2000", "point": name, "xyz": xyz, "epoch": 2000.4}
        )
    return found


def ours(case: dict) -> list[float]:
    moved = transform_point(case["xyz"], source=case["source"], target=case["target"], epoch=case["epoch"])
    return [float(v) for v in moved.xyz]


def with_proj() -> dict:
    import pyproj

    transformers: dict[tuple[str, str], object] = {}
    results = []
    for case in cases():
        key = (case["source"], case["target"])
        if key not in transformers:
            transformers[key] = pyproj.Transformer.from_crs(GEOCENTRIC[key[0]], GEOCENTRIC[key[1]])
        transformer = transformers[key]
        x, y, z, _t = transformer.transform(*case["xyz"], case["epoch"])
        results.append(
            {**case, "xyz": list(case["xyz"]), "proj": [x, y, z], "operation": transformer.description}
        )
    return {
        "pyproj": pyproj.__version__,
        "proj": pyproj.proj_version_str,
        "epsg": pyproj.database.get_database_metadata("EPSG.VERSION"),
        "cases": results,
    }


def compare(reference: dict) -> list[str]:
    failures = []
    for case in reference["cases"]:
        path = transformation_path(case["source"], case["target"])
        expected_names = {helmert.name for helmert, _inverse in path}
        identity = all(h.time_specific and not any(h.translation) for h, _ in path)
        if identity and case["operation"].startswith("Ballpark"):
            pass  # see cases(): PROJ does not implement EPSG:9052
        elif not any(name in case["operation"] for name in expected_names):
            failures.append(
                f"{case['source']}->{case['target']}: PROJ used {case['operation']!r}, "
                f"GeoComp {sorted(expected_names)}"
            )
            continue
        difference = math.dist(ours(case), case["proj"])
        if difference > TOLERANCE:
            failures.append(
                f"{case['source']}->{case['target']} {case['point']} @ {case['epoch']}: "
                f"{difference * 1e6:.3f} micrometres"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the committed fixture")
    arguments = parser.parse_args()

    fresh = with_proj()
    print(
        f"pyproj {fresh['pyproj']}, PROJ {fresh['proj']}, EPSG {fresh['epsg']}: {len(fresh['cases'])} cases"
    )
    failures = compare(fresh)
    for failure in failures:
        print("  DIFFERS", failure)
    if arguments.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fresh, indent=1) + "\n")
        print(f"  wrote {FIXTURE.relative_to(ROOT)}")
    elif FIXTURE.is_file():
        committed = json.loads(FIXTURE.read_text())
        by_key = {(c["source"], c["target"], c["point"], c["epoch"]): c["proj"] for c in committed["cases"]}
        for case in fresh["cases"]:
            stored = by_key.get((case["source"], case["target"], case["point"], case["epoch"]))
            if stored is None or math.dist(stored, case["proj"]) > TOLERANCE:
                failures.append(f"fixture stale for {case['source']}->{case['target']} {case['point']}")
                print("  STALE  ", failures[-1])
    worst = max(math.dist(ours(c), c["proj"]) for c in fresh["cases"])
    print(f"  largest difference from PROJ: {worst * 1e9:.1f} nanometres")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
