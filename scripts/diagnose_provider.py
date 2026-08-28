#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Load every registered algorithm one at a time, printing as it goes.

A crash inside ``QgsProcessingProvider.addAlgorithm`` takes the whole process
down with it, and the traceback names ``loadAlgorithms`` rather than the
algorithm being added -- so a hundred and thirty tests fail at once and none of
them says which one is at fault. This walks the registry with a flush after
every line, so the **last line printed before the abort names the culprit**.

Run it wherever a QGIS is available::

    QT_QPA_PLATFORM=offscreen python3 scripts/diagnose_provider.py

It is deliberately not a test: a test that aborts the interpreter cannot report
anything, which is the whole problem.
"""

from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    from qgis.core import Qgis, QgsApplication, QgsProcessingProvider

    print(f"QGIS {Qgis.QGIS_VERSION}", flush=True)
    app = QgsApplication([], False)
    app.initQgis()

    from geocomp.registry import ALGORITHMS

    class Probe(QgsProcessingProvider):
        def id(self) -> str:
            return "geocomp_probe"

        def name(self) -> str:
            return "GeoComp probe"

        def loadAlgorithms(self) -> None:  # noqa: N802 - Qt
            pass

    provider = Probe()
    failed: list[str] = []

    for spec in ALGORITHMS:
        print(f"import   {spec.id}", flush=True)
        try:
            module = importlib.import_module(spec.module)
        except Exception:  # noqa: BLE001 - a diagnostic reports every failure
            traceback.print_exc()
            failed.append(f"{spec.id}: import")
            continue

        print(f"construct {spec.id}", flush=True)
        try:
            algorithm = getattr(module, spec.class_name)()
        except Exception:  # noqa: BLE001 - a diagnostic reports every failure
            traceback.print_exc()
            failed.append(f"{spec.id}: construct")
            continue

        # The dangerous one: addAlgorithm calls initAlgorithm across the C++
        # boundary, where an exception in a Python override is fatal under
        # PyQt6 rather than merely printed as it was under PyQt5.
        print(f"add       {spec.id}", flush=True)
        if not provider.addAlgorithm(algorithm):
            failed.append(f"{spec.id}: addAlgorithm returned False")
            print(f"REFUSED  {spec.id}", flush=True)
            continue

        print(f"ok        {spec.id}", flush=True)

    print(f"\n{len(ALGORITHMS) - len(failed)}/{len(ALGORITHMS)} loaded", flush=True)
    for entry in failed:
        print(f"FAILED {entry}", flush=True)

    app.exitQgis()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
