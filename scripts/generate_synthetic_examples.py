# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate and verify synthetic examples for every GeoComp menu option.

Builds ``synthetic_examples/`` at the repository root with 3 distinct synthetic
scenarios for all 49 Processing algorithms plus the *Global Settings...* dialog
(50 menu items x 3 examples = 150 synthetic examples total).

Usage::

    python3 scripts/generate_synthetic_examples.py [--verify] [--output DIR]
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import gzip
import hashlib
import io
import json
import math
import shutil
import stat
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclasses.dataclass
class ExampleSpec:
    """One synthetic test scenario for a GeoComp menu option."""

    menu_group_id: str
    menu_group_title: str
    menu_path: str
    algorithm_id: str
    algorithm_title: str
    example_index: int
    slug: str
    title: str
    scenario: str
    parameters: dict[str, Any]
    expected_summary: str
    expect_exception: str | None = None


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_rows_csv(path: Path, rows: list[list[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)
    return path


def _make_executable(path: Path, content: str) -> Path:
    _write_text(path, content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _copy_into(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return dst


def _run_alg(algorithm_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Run a registered GeoComp Processing algorithm synchronously."""
    from qgis.core import QgsApplication, QgsProcessingContext, QgsProcessingFeedback

    alg = QgsApplication.processingRegistry().algorithmById(algorithm_id).create({})
    results, ok = alg.run(
        parameters, QgsProcessingContext(), QgsProcessingFeedback(), catchExceptions=False
    )
    assert ok, f"Setup algorithm failed: {algorithm_id}"
    return results


def _create_standin_rtklib(bin_dir: Path) -> Path:
    """Create a deterministic stand-in ``rnx2rtkp`` executable for offline runs."""
    script = """#!/usr/bin/env python3
import pathlib
import sys

args = sys.argv[1:]
if "--version" in args or "-h" in args:
    print("rnx2rtkp RTKLIB EX 2.5.1")
    sys.exit(0)

out = pathlib.Path(args[args.index("-o") + 1])
conf_text = ""
if "-k" in args:
    conf_path = pathlib.Path(args[args.index("-k") + 1])
    if conf_path.is_file():
        conf_text = conf_path.read_text(encoding="utf-8", errors="ignore")

elmask = 15.0
for line in conf_text.splitlines():
    if line.strip().startswith("pos1-elmask"):
        try:
            elmask = float(line.split("=")[1].strip().split()[0])
        except ValueError:
            pass

offset = (elmask - 15.0) * 0.0002
x0 = 4075539.8850 + offset
y0 = 931735.2910 - offset
z0 = 4801629.3730 + offset * 0.5

out.write_text(
    "% program   : RTKLIB ver.2.4.3 b34\\n"
    "% inp file  : rover.05o\\n"
    "% inp file  : base.05o\\n"
    "% inp file  : brdc.05n\\n"
    "% obs start : 2005/05/20 00:00:00.0 GPST (week1323 432000.0s)\\n"
    "% obs end   : 2005/05/20 00:30:00.0 GPST (week1323 433800.0s)\\n"
    "% ref pos   : 4075578.3850   931852.8900  4801570.1540\\n"
    "%\\n"
    "% (x/y/z-ecef=WGS84,Q=1:fix,2:float,ns=# of satellites)\\n"
    "%  GPST                  x-ecef(m)      y-ecef(m)      z-ecef(m)   Q  ns"
    "   sdx(m)   sdy(m)   sdz(m)  sdxy(m)  sdyz(m)  sdzx(m) age(s)  ratio\\n"
    f"2005/05/20 00:00:00.000 {x0:14.4f} {y0:14.4f} {z0:14.4f}   1   8"
    "   0.0021   0.0018   0.0029  -0.0005   0.0004  -0.0008   0.00   28.4\\n"
    f"2005/05/20 00:15:00.000 {x0+0.0004:14.4f} {y0-0.0002:14.4f} {z0+0.0003:14.4f}   1   8"
    "   0.0020   0.0017   0.0028  -0.0005   0.0004  -0.0008   0.00   31.2\\n"
    f"2005/05/20 00:30:00.000 {x0-0.0002:14.4f} {y0+0.0003:14.4f} {z0-0.0001:14.4f}   1   9"
    "   0.0019   0.0016   0.0027  -0.0004   0.0003  -0.0007   0.00   35.0\\n",
    encoding="utf-8",
)
"""
    return _make_executable(bin_dir / "rnx2rtkp", script)


def _create_standin_dynadjust(bin_dir: Path) -> Path:
    """Create deterministic stand-in DynAdjust executables in *bin_dir*."""
    sample_dir = REPO_ROOT / "tests" / "data" / "dynadjust" / "output"
    adj_text = (sample_dir / "sample.adj").read_text(encoding="utf-8")
    apu_text = (sample_dir / "sample.apu").read_text(encoding="utf-8")
    cor_text = (sample_dir / "sample.cor").read_text(encoding="utf-8")

    body = f"""#!/usr/bin/env python3
import pathlib
import sys

args = sys.argv[1:]
if "--version" in args:
    print("+ Version:      1.4.0, Release with OpenBLAS")
    sys.exit(0)

program = pathlib.Path(sys.argv[0]).name
network = "run"
for i, token in enumerate(args):
    if token in ("-n", "--network-name") and i + 1 < len(args):
        network = args[i + 1]

if program == "dnaadjust":
    for mode in ("simult", "phased"):
        pathlib.Path(f"{{network}}.{{mode}}.adj").write_text({adj_text!r}, encoding="utf-8")
        pathlib.Path(f"{{network}}.{{mode}}.apu").write_text({apu_text!r}, encoding="utf-8")
        pathlib.Path(f"{{network}}.{{mode}}.cor").write_text({cor_text!r}, encoding="utf-8")
"""
    for prog in ("dnaimport", "dnareftran", "dnageoid", "dnasegment", "dnaadjust"):
        _make_executable(bin_dir / prog, body)
    return bin_dir


def _levelling_line_rows(book: Any) -> list[list[str]]:
    rows = [["setup", "point", "kind", "reading", "distance"]]
    for setup in book.line.setups:
        rows.append(
            [
                setup.id,
                setup.backsight.station,
                "BS",
                f"{setup.backsight.reading.value:.5f}",
                f"{setup.backsight.distance_value:.2f}",
            ]
        )
        for index, sight in enumerate(setup.foresights):
            rows.append(
                [
                    setup.id,
                    sight.station,
                    "FS" if index == 0 else "IS",
                    f"{sight.reading.value:.5f}",
                    f"{sight.distance_value:.2f}",
                ]
            )
    return rows


def _levelling_mapping_doc(path: Path, with_line: bool = False) -> Path:
    cols = [
        {"field": "setup", "column": "setup"},
        {"field": "station", "column": "point"},
        {"field": "sight", "column": "kind"},
        {"field": "reading", "column": "reading"},
        {"field": "distance", "column": "distance"},
    ]
    if with_line:
        cols.append({"field": "line", "column": "line"})
    return _write_json(path, {"name": "synthetic_levelling", "columns": cols, "decimal_separator": "."})


def _write_planar_geoid(path: Path) -> Path:
    from tests.test_integration import GEOID

    step = math.degrees(GEOID.coverage.north - GEOID.coverage.south) / 2.0
    lines = [
        "ncols 3",
        "nrows 3",
        f"xllcenter {math.degrees(GEOID.coverage.west)!r}",
        f"yllcenter {math.degrees(GEOID.coverage.south)!r}",
        f"cellsize {step!r}",
    ]
    lines.extend(" ".join(repr(float(v)) for v in row) for row in np.asarray(GEOID.values)[::-1])
    return _write_text(path, "\n".join(lines) + "\n")


def _prepare_shared_assets(base_dir: Path) -> dict[str, Any]:
    """Generate shared foundational synthetic files used across examples."""
    from geocomp.core.instruments import ProfileLibrary
    from geocomp.core.models import (
        MonitoringRole,
        Project,
    )
    from geocomp.core.settings_def import SETTINGS
    from geocomp.engines.dynadjust.read_dynaml import read_dynaml
    from geocomp.io.store import open_store
    from geocomp.services.settings_service import settings as gc_settings
    from tests import combined_network as comb_field
    from tests import networks as nets
    from tests import reference_levelling as rd
    from tests import reference_rd01 as rd01
    from tests import synthetic as syn
    from tests.gravimeter_samples import cg5_export
    from tests.monitoring_network import (
        OBJECTS as MON_OBJECTS,
    )
    from tests.monitoring_network import (
        REFERENCE as MON_REFERENCE,
    )
    from tests.monitoring_network import (
        epoch as mon_epoch,
    )
    from tests.monitoring_network import (
        epoch_network as mon_epoch_network,
    )
    from tests.test_integration import (
        gnss_input_held_at_truth,
        levelling_input,
        total_station_input,
    )
    from tests.test_integration_modes import (
        grid_total_station_input,
        levelling_with_benchmark,
        local_levelling,
        local_total_station,
    )

    for defn in SETTINGS:
        gc_settings.reset_global(defn.key)

    shared = base_dir / "_shared_pipeline"
    shared.mkdir(parents=True, exist_ok=True)

    # 1. Stand-in binaries (RTKLIB + DynAdjust)
    bin_dir = shared / "bin"
    rtklib_bin = _create_standin_rtklib(bin_dir)
    dynadjust_dir = _create_standin_dynadjust(bin_dir)
    gc_settings.set_global("paths.rtklib_program", str(rtklib_bin))
    gc_settings.set_global("paths.dynadjust_directory", str(dynadjust_dir))

    # 2. Total station synthetic & RD01 files
    rd01_readings_json = shared / "rd01_readings.json"
    _run_alg(
        "geocomp:totalstation_import_fieldbook",
        {
            "SOURCE": str(rd01.RAW),
            "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
            "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
            "SIGMA_DISTANCE": 0.002,
            "OUTPUT_READINGS": str(rd01_readings_json),
            "OUTPUT_HTML": str(shared / "rd01_import.html"),
            "OUTPUT_FINDINGS": str(shared / "rd01_findings.csv"),
        },
    )
    rd01_reduced_json = shared / "rd01_reduced.json"
    _run_alg(
        "geocomp:totalstation_preprocess",
        {
            "READINGS": str(rd01_readings_json),
            "APPLY_ATMOSPHERIC": False,
            "OUTPUT_REDUCED": str(rd01_reduced_json),
            "OUTPUT_HTML": str(shared / "rd01_pre.html"),
            "OUTPUT_CSV": str(shared / "rd01_pre.csv"),
        },
    )
    rd01_approx_json = _write_json(shared / "rd01_approx.json", rd01.approximate_coordinates())

    syn_reductions_json = _write_json(shared / "syn_reductions.json", syn.reductions_document())
    syn_leapfrog_json = _write_json(
        shared / "syn_leapfrog.json", syn.reductions_document({"L": syn.SETUPS["L"]})
    )
    syn_known_json = _write_json(shared / "syn_known.json", syn.known_points())
    syn_all_approx_json = _write_json(shared / "syn_all_approx.json", dict(syn.COORDINATES))

    # 3. Levelling synthetic files
    lib = ProfileLibrary()
    lib.add_level(rd.profile())
    lev_profiles_json = _write_json(shared / "lev_profiles.json", lib.to_dict())
    lev_map_json = _levelling_mapping_doc(shared / "lev_mapping.json", with_line=False)
    lev_loop_map_json = _levelling_mapping_doc(shared / "lev_loop_mapping.json", with_line=True)

    lev_bal_csv = _write_rows_csv(shared / "lev_balanced.csv", _levelling_line_rows(rd.balanced_line()))
    lev_imb_csv = _write_rows_csv(shared / "lev_imbalanced.csv", _levelling_line_rows(rd.imbalanced_line()))

    ext_setup, _ = rd.extreme_sights_setup()
    ext_rows = [["setup", "point", "kind", "reading", "distance"]]
    ext_rows.append(
        [
            ext_setup.id,
            ext_setup.backsight.station,
            "BS",
            f"{ext_setup.backsight.reading.value:.5f}",
            f"{ext_setup.backsight.distance_value:.2f}",
        ]
    )
    for idx, sight in enumerate(ext_setup.foresights):
        ext_rows.append(
            [
                ext_setup.id,
                sight.station,
                "FS" if idx == 0 else "IS",
                f"{sight.reading.value:.5f}",
                f"{sight.distance_value:.2f}",
            ]
        )
    lev_ext_csv = _write_rows_csv(shared / "lev_extreme.csv", ext_rows)

    near, far, _ = rd.reciprocal_crossing(refraction=0.012)
    recip_rows = [["setup", "point", "kind", "reading", "distance"]]
    for pair in (near, far):
        for kind, sight in (("BS", pair.near), ("FS", pair.far)):
            recip_rows.append(
                [
                    pair.setup_id,
                    sight.station,
                    kind,
                    f"{sight.reading.value:.5f}",
                    f"{sight.distance_value:.2f}",
                ]
            )
    lev_recip_csv = _write_rows_csv(shared / "lev_reciprocal.csv", recip_rows)

    loop_books, _ = rd.loop(noise=0.0003)
    loop_rows = [["setup", "point", "kind", "reading", "distance", "line"]]
    for b in loop_books:
        for s in b.line.setups:
            loop_rows.append(
                [
                    s.id,
                    s.backsight.station,
                    "BS",
                    f"{s.backsight.reading.value:.5f}",
                    f"{s.backsight.distance_value:.2f}",
                    b.line.id,
                ]
            )
            loop_rows.append(
                [
                    s.id,
                    s.foresights[0].station,
                    "FS",
                    f"{s.foresights[0].reading.value:.5f}",
                    f"{s.foresights[0].distance_value:.2f}",
                    b.line.id,
                ]
            )
    lev_loop_csv = _write_rows_csv(shared / "lev_loop.csv", loop_rows)

    lev_bal_setups = shared / "lev_bal_setups.json"
    lev_imb_setups = shared / "lev_imb_setups.json"
    lev_ext_setups = shared / "lev_ext_setups.json"
    lev_recip_setups = shared / "lev_recip_setups.json"
    lev_loop_setups = shared / "lev_loop_setups.json"

    for csv_p, map_p, out_p in [
        (lev_bal_csv, lev_map_json, lev_bal_setups),
        (lev_imb_csv, lev_map_json, lev_imb_setups),
        (lev_ext_csv, lev_map_json, lev_ext_setups),
        (lev_recip_csv, lev_map_json, lev_recip_setups),
        (lev_loop_csv, lev_loop_map_json, lev_loop_setups),
    ]:
        _run_alg(
            "geocomp:levelling_import",
            {
                "BOOK": str(csv_p),
                "MAPPING": str(map_p),
                "PROFILES": str(lev_profiles_json),
                "OUTPUT_SETUPS": str(out_p),
                "OUTPUT_HTML": str(out_p.with_suffix(".html")),
            },
        )

    lev_bal_red = shared / "lev_bal_reduced.json"
    lev_loop_red = shared / "lev_loop_reduced.json"
    for st_p, out_p in [(lev_bal_setups, lev_bal_red), (lev_loop_setups, lev_loop_red)]:
        _run_alg(
            "geocomp:levelling_equal_sights",
            {
                "SETUPS": str(st_p),
                "PROFILES": str(lev_profiles_json),
                "OUTPUT_REDUCTIONS": str(out_p),
                "OUTPUT_HTML": str(out_p.with_suffix(".html")),
                "OUTPUT_CSV": str(out_p.with_suffix(".csv")),
            },
        )

    # 4. Gravimetry synthetic files
    cg5_txt = _write_text(shared / "cg5_survey.txt", cg5_export(gmt_diff=0.0, tide="YES"))
    grav_reduced_json = shared / "grav_reduced.json"
    _run_alg(
        "geocomp:gravimetry_preprocess",
        {
            "READINGS": str(cg5_txt),
            "PRECISION_FLOOR": 0.005,
            "OUTPUT_READINGS": str(grav_reduced_json),
            "OUTPUT_CSV": str(shared / "grav_corr.csv"),
            "OUTPUT_DRIFT": str(shared / "grav_drift.json"),
        },
    )

    # 5. Integration synthetic files
    comb_gnss_json = _write_json(
        shared / "comb_gnss.json", gnss_input_held_at_truth().to_dict()
    )
    comb_ts_ecef_json = _write_json(shared / "comb_ts_ecef.json", total_station_input().to_dict())
    comb_ts_grid_json = _write_json(
        shared / "comb_ts_grid.json", grid_total_station_input().to_dict()
    )
    comb_lev_json = _write_json(shared / "comb_lev.json", levelling_input().to_dict())
    comb_lev_bm_json = _write_json(
        shared / "comb_lev_bm.json", levelling_with_benchmark().to_dict()
    )
    local_ts_json = _write_json(shared / "local_ts.json", local_total_station().to_dict())
    local_lev_json = _write_json(shared / "local_lev.json", local_levelling().to_dict())
    geoid_asc = _write_planar_geoid(shared / "curitiba_planar.asc")
    ntv2_gsb = _write_text(
        shared / "synthetic_geoid.gsb",
        "NUM_OREC 11\nNUM_SREC 11\nNUM_FILE  1\nGS_TYPE SECONDS\n",
    )

    vel_rows = [["station", "vx", "vy", "vz"]]
    for sid in sorted(comb_field.TRUTH):
        vel_rows.append([sid, "-0.0040", "0.0110", "0.0130"])
    vel_csv = _write_rows_csv(shared / "station_velocities.csv", vel_rows)

    # 6. Analysis & Monitoring networks and solutions
    trilat_net_json = _write_json(shared / "trilateration.json", nets.trilateration().network.to_dict())
    lev_net_1d_json = _write_json(shared / "levelling_loop_net.json", nets.levelling_loop().network.to_dict())

    roles_net = mon_epoch_network(1, seed=1)
    for name, stn in list(roles_net.stations.items()):
        roles_net.stations[name] = dataclasses.replace(
            stn,
            monitoring_role=(
                MonitoringRole.REFERENCE if name in MON_REFERENCE else MonitoringRole.OBJECT
            ),
        )
    mon_roles_json = _write_json(shared / "monitoring_roles_network.json", roles_net.to_dict())
    mon_sol1 = mon_epoch(1, seed=1)
    mon_sol2 = dataclasses.replace(
        mon_epoch(2, moves={"O2": (0.008, -0.006)}, seed=2), network_id=roles_net.id
    )
    mon_sol3 = dataclasses.replace(
        mon_epoch(3, moves={"O2": (0.016, -0.012)}, seed=3), network_id=roles_net.id
    )
    mon_sol1_json = _write_json(shared / "mon_epoch1.json", mon_sol1.to_dict())
    mon_sol2_json = _write_json(shared / "mon_epoch2.json", mon_sol2.to_dict())
    mon_sol3_json = _write_json(shared / "mon_epoch3.json", mon_sol3.to_dict())

    mon_analysis_json = shared / "monitoring_analysis.json"
    _run_alg(
        "geocomp:monitoring_compare_epochs",
        {
            "FIRST": str(mon_sol1_json),
            "SECOND": str(mon_sol2_json),
            "NETWORK": str(mon_roles_json),
            "OUTPUT_ANALYSIS": str(mon_analysis_json),
            "OUTPUT_HTML": str(shared / "mon_cmp.html"),
        },
    )
    mon_series_json = shared / "monitoring_series.json"
    _run_alg(
        "geocomp:monitoring_time_series",
        {
            "SOLUTIONS": [str(mon_sol1_json), str(mon_sol2_json), str(mon_sol3_json)],
            "NETWORK": str(mon_roles_json),
            "OUTPUT_SERIES": str(mon_series_json),
            "OUTPUT_CSV": str(shared / "mon_series.csv"),
            "OUTPUT_HTML": str(shared / "mon_series.html"),
        },
    )

    # 7. DynAdjust sample network & prepared folder
    dna_data = REPO_ROOT / "tests" / "data" / "dynadjust"
    dna_net = read_dynaml(dna_data / "sample-stn.xml", dna_data / "sample-msr.xml").network
    dna_net.id = "sample"
    dna_net_json = _write_json(shared / "dynadjust_network.json", dna_net.to_dict())

    prepared_dir = shared / "dynadjust_prepared_job"
    if prepared_dir.exists():
        shutil.rmtree(prepared_dir)
    _run_alg(
        "geocomp:analysis_dynadjust_adjust",
        {
            "NETWORK": str(dna_net_json),
            "FRAME": "GDA2020",
            "EPOCH": 2020.0,
            "STOP_BEFORE_RUNNING": True,
            "OUTPUT_WORK_DIR": str(prepared_dir),
        },
    )

    # 8. Project store (.gpkg)
    proj = Project(id="curitiba_survey")
    proj.add_network(dna_net)
    proj.add_network(roles_net)
    store_gpkg = shared / "project_store.gpkg"
    if store_gpkg.exists():
        store_gpkg.unlink()
    with open_store(store_gpkg, create=True) as st:
        st.write(proj)
        st.write_solution(mon_sol1)

    # 9. GNSS sample RINEX folder + .pos folder
    rinex_src = REPO_ROOT / "tests" / "data" / "rtklib"
    rinex_dir = shared / "gnss_rinex"
    rinex_dir.mkdir(parents=True, exist_ok=True)
    base_obs = (rinex_src / "30400920.05o").read_text(encoding="utf-8")
    _write_text(rinex_dir / "base.05o", base_obs.replace("3040  ", "BASE  ", 1))
    rover_obs = (rinex_src / "07590920.05o").read_text(encoding="utf-8")
    _write_text(rinex_dir / "rover.05o", rover_obs.replace("0759  ", "ROVE  ", 1))
    with gzip.open(rinex_src / "brdc_0759.05n.gz", "rt", encoding="utf-8") as gz_in:
        _write_text(rinex_dir / "brdc.05n", gz_in.read())

    pos_dir = shared / "gnss_pos"
    pos_dir.mkdir(parents=True, exist_ok=True)
    xyz_pos_text = (rinex_src / "pos" / "xyz.pos").read_text(encoding="utf-8")
    _write_text(
        pos_dir / "base_rove.pos",
        xyz_pos_text.replace("07590920.05o", "rover.05o").replace("30400920.05o", "base.05o"),
    )

    return {
        "shared": shared,
        "rtklib_bin": rtklib_bin,
        "dynadjust_dir": dynadjust_dir,
        "rd01_raw_csv": rd01.RAW,
        "rd01_readings_json": rd01_readings_json,
        "rd01_reduced_json": rd01_reduced_json,
        "rd01_approx_json": rd01_approx_json,
        "syn_reductions_json": syn_reductions_json,
        "syn_leapfrog_json": syn_leapfrog_json,
        "syn_known_json": syn_known_json,
        "syn_all_approx_json": syn_all_approx_json,
        "lev_profiles_json": lev_profiles_json,
        "lev_map_json": lev_map_json,
        "lev_loop_map_json": lev_loop_map_json,
        "lev_bal_csv": lev_bal_csv,
        "lev_imb_csv": lev_imb_csv,
        "lev_ext_csv": lev_ext_csv,
        "lev_recip_csv": lev_recip_csv,
        "lev_loop_csv": lev_loop_csv,
        "lev_bal_setups": lev_bal_setups,
        "lev_imb_setups": lev_imb_setups,
        "lev_ext_setups": lev_ext_setups,
        "lev_recip_setups": lev_recip_setups,
        "lev_loop_setups": lev_loop_setups,
        "lev_bal_red": lev_bal_red,
        "lev_loop_red": lev_loop_red,
        "cg5_txt": cg5_txt,
        "grav_reduced_json": grav_reduced_json,
        "comb_gnss_json": comb_gnss_json,
        "comb_ts_ecef_json": comb_ts_ecef_json,
        "comb_ts_grid_json": comb_ts_grid_json,
        "comb_lev_json": comb_lev_json,
        "comb_lev_bm_json": comb_lev_bm_json,
        "local_ts_json": local_ts_json,
        "local_lev_json": local_lev_json,
        "geoid_asc": geoid_asc,
        "ntv2_gsb": ntv2_gsb,
        "vel_csv": vel_csv,
        "comb_held": ",".join(comb_field.HELD),
        "trilat_net_json": trilat_net_json,
        "lev_net_1d_json": lev_net_1d_json,
        "mon_roles_json": mon_roles_json,
        "mon_sol1_json": mon_sol1_json,
        "mon_sol2_json": mon_sol2_json,
        "mon_sol3_json": mon_sol3_json,
        "mon_analysis_json": mon_analysis_json,
        "mon_series_json": mon_series_json,
        "mon_ref": ",".join(MON_REFERENCE),
        "mon_obj": ",".join(MON_OBJECTS),
        "dna_net_json": dna_net_json,
        "prepared_dir": prepared_dir,
        "store_gpkg": store_gpkg,
        "rinex_dir": rinex_dir,
        "pos_dir": pos_dir,
    }


def _build_total_station_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    from tests import reference_rd01 as rd01
    from tests import synthetic as syn

    group_id = "01_total_station"
    group_title = "Total Station"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    # 1. geocomp:totalstation_import_fieldbook
    alg = "geocomp:totalstation_import_fieldbook"
    alg_title = "Import field book"
    menu_path = "GeoComp ▸ Total Station ▸ Import field book"
    d1 = group_dir / "totalstation_import_fieldbook" / "example_1_rd01_csv"
    fb1 = _copy_into(rd01.RAW, d1 / "inputs" / "fieldbook.csv")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_rd01_csv",
            "Two-face CSV field book (RD-01) with explicit direction/zenith/distance sigmas",
            "Imports 12 readings across 3 station setups (A, B, C) with 1 arcsec angle and 2 mm distance "
            "precision.",
            {
                "SOURCE": str(fb1),
                "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
                "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
                "SIGMA_DISTANCE": 0.002,
                "OUTPUT_READINGS": str(d1 / "outputs" / "readings.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_FINDINGS": str(d1 / "outputs" / "findings.csv"),
            },
            "Imports 12 valid readings across 3 setups with 0 rejected records.",
        )
    )

    d2 = group_dir / "totalstation_import_fieldbook" / "example_2_xlsx_workbook"
    from tests.test_spreadsheet_import import _csv_rows, workbook

    (d2 / "inputs").mkdir(parents=True, exist_ok=True)
    fb2 = workbook(d2 / "inputs" / "fieldbook.xlsx", _csv_rows(rd01.RAW))
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_xlsx_workbook",
            "Excel spreadsheet (.xlsx) field book import with high-precision EDM sigmas",
            "Imports the field book directly from an Excel .xlsx workbook without converting to CSV.",
            {
                "SOURCE": str(fb2),
                "SIGMA_DIRECTION": 2.5e-6,
                "SIGMA_ZENITH": 2.5e-6,
                "SIGMA_DISTANCE": 0.001,
                "OUTPUT_READINGS": str(d2 / "outputs" / "readings.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_FINDINGS": str(d2 / "outputs" / "findings.csv"),
            },
            "Reads all 12 records from .xlsx matching CSV import identically.",
        )
    )

    d3 = group_dir / "totalstation_import_fieldbook" / "example_3_rejected_row_audit"
    raw_lines = rd01.RAW.read_text(encoding="utf-8").splitlines()
    raw_lines.append("A,B,I,not_a_number,90.0,100.0,1.5,1.5")
    fb3 = _write_text(d3 / "inputs" / "fieldbook_with_bad_row.csv", "\n".join(raw_lines) + "\n")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_rejected_row_audit",
            "Field book with a malformed row audited in findings.csv (FAIL_ON_REJECTED=False)",
            "Appends a corrupted row to verify that valid rows import while the bad row is logged in "
            "findings.csv.",
            {
                "SOURCE": str(fb3),
                "SIGMA_DIRECTION": rd01.SIGMA_ANGLE,
                "SIGMA_ZENITH": rd01.SIGMA_ANGLE,
                "SIGMA_DISTANCE": 0.002,
                "FAIL_ON_REJECTED": False,
                "OUTPUT_READINGS": str(d3 / "outputs" / "readings.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_FINDINGS": str(d3 / "outputs" / "findings.csv"),
            },
            "Imports the 12 valid rows and logs REJECTED_COUNT=1 in findings.csv.",
        )
    )

    # 2. geocomp:totalstation_preprocess
    alg = "geocomp:totalstation_preprocess"
    alg_title = "Generalised pre-processing"
    menu_path = "GeoComp ▸ Total Station ▸ Generalised pre-processing"
    d1 = group_dir / "totalstation_preprocess" / "example_1_no_atmospheric_blunder_caught"
    rd1 = _copy_into(assets["rd01_readings_json"], d1 / "inputs" / "readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_no_atmospheric_blunder_caught",
            "Two-face reduction catching RD-01's face-distance blunder (APPLY_ATMOSPHERIC=False)",
            "Pairs Face I and Face II readings across 6 pointings and flags the 1 pointing with a "
            "face-distance blunder.",
            {
                "READINGS": str(rd1),
                "APPLY_ATMOSPHERIC": False,
                "OUTPUT_REDUCED": str(d1 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "reductions.csv"),
            },
            "Reduces 6 pointings (USABLE_COUNT=5, BLOCKING_COUNT=1).",
        )
    )

    d2 = group_dir / "totalstation_preprocess" / "example_2_warm_atmosphere_correction"
    rd2 = _copy_into(assets["rd01_readings_json"], d2 / "inputs" / "readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_warm_atmosphere_correction",
            "Atmospheric EDM scale reduction at 30 °C, 915 hPa, 50% RH",
            "Applies first-velocity atmospheric correction and propagates temperature/pressure "
            "uncertainties.",
            {
                "READINGS": str(rd2),
                "TEMPERATURE": 30.0,
                "PRESSURE": 915.0,
                "HUMIDITY": 50.0,
                "APPLY_ATMOSPHERIC": True,
                "OUTPUT_REDUCED": str(d2 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "reductions.csv"),
            },
            "Applies atmospheric ppm correction and inflates distance variance by meteorological "
            "uncertainties.",
        )
    )

    d3 = group_dir / "totalstation_preprocess" / "example_3_relaxed_distance_tolerance"
    rd3 = _copy_into(assets["rd01_readings_json"], d3 / "inputs" / "readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_relaxed_distance_tolerance",
            "Custom face-distance tolerance (1.0 m) and explicit distance/zenith correlation (0.25)",
            "Relaxes face-pair distance tolerance to 1.0 m and sets distance/zenith correlation to 0.25.",
            {
                "READINGS": str(rd3),
                "APPLY_ATMOSPHERIC": False,
                "DISTANCE_TOLERANCE": 1.0,
                "CORRELATION": 0.25,
                "OUTPUT_REDUCED": str(d3 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "reductions.csv"),
            },
            "Accepts all 6 pointings under the 1.0 m tolerance and records 0.25 correlation.",
        )
    )

    # 3. geocomp:totalstation_traverse
    alg = "geocomp:totalstation_traverse"
    alg_title = "Traverse"
    menu_path = "GeoComp ▸ Total Station ▸ Traverse"
    d1 = group_dir / "totalstation_traverse" / "example_1_closed_loop_bowditch"
    red1 = _copy_into(assets["syn_reductions_json"], d1 / "inputs" / "reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_closed_loop_bowditch",
            "Closed 4-station polygon traverse (A,B,C,D,A) with Compass (Bowditch) distribution",
            "Runs a closed loop starting and ending at A (1000, 2000) with backsight D.",
            {
                "REDUCTIONS": str(red1),
                "ROUTE": ",".join(syn.ROUTE),
                "BACKSIGHT": syn.BACKSIGHT,
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "CLOSE_AZIMUTH": math.degrees(syn.azimuth("D", "A")),
                "KIND": 0,
                "METHOD": 0,
                "OUTPUT_COORDINATES": str(d1 / "outputs" / "coordinates.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "stations.csv"),
            },
            "Closes with zero angular and linear misclosure and recovers B, C, D.",
        )
    )

    d2 = group_dir / "totalstation_traverse" / "example_2_connected_transit_rule"
    red2 = _copy_into(assets["syn_reductions_json"], d2 / "inputs" / "reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_connected_transit_rule",
            "Connected traverse (A,B,C) closing onto known station C with Transit rule",
            "Traverses from A through B to known station C (1140, 2110) using Transit distribution.",
            {
                "REDUCTIONS": str(red2),
                "ROUTE": "A,B,C",
                "BACKSIGHT": "D",
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "CLOSE_EASTING": syn.COORDINATES["C"][0],
                "CLOSE_NORTHING": syn.COORDINATES["C"][1],
                "CLOSE_AZIMUTH": math.degrees(syn.azimuth("B", "C")),
                "KIND": 1,
                "METHOD": 1,
                "OUTPUT_COORDINATES": str(d2 / "outputs" / "coordinates.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "stations.csv"),
            },
            "Recovers B and C along the connected traverse using the Transit rule.",
        )
    )

    d3 = group_dir / "totalstation_traverse" / "example_3_open_traverse_undistributed"
    red3 = _copy_into(assets["syn_reductions_json"], d3 / "inputs" / "reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_open_traverse_undistributed",
            "Open cantilever traverse (A,B,C) with no misclosure distribution",
            "Propagates coordinates along open route A -> B -> C without closing control.",
            {
                "REDUCTIONS": str(red3),
                "ROUTE": "A,B,C",
                "BACKSIGHT": "D",
                "START_EASTING": syn.COORDINATES["A"][0],
                "START_NORTHING": syn.COORDINATES["A"][1],
                "START_AZIMUTH": math.degrees(syn.start_azimuth()),
                "KIND": 2,
                "METHOD": 2,
                "OUTPUT_COORDINATES": str(d3 / "outputs" / "coordinates.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "stations.csv"),
            },
            "Computes open traverse coordinates for B and C.",
        )
    )

    # 4. geocomp:totalstation_resection
    alg = "geocomp:totalstation_resection"
    alg_title = "Resection"
    menu_path = "GeoComp ▸ Total Station ▸ Resection"
    d1 = group_dir / "totalstation_resection" / "example_1_four_control_pillars"
    red1 = _copy_into(assets["syn_reductions_json"], d1 / "inputs" / "reductions.json")
    kn1 = _copy_into(assets["syn_known_json"], d1 / "inputs" / "known.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_four_control_pillars",
            "Redundant 4-target free-station resection at station R (targets A, B, C, D)",
            "Solves occupied station R from observations to 4 surrounding control pillars.",
            {
                "REDUCTIONS": str(red1),
                "STATION": "R",
                "KNOWN": str(kn1),
                "OUTPUT_POSITION": str(d1 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
            },
            "Recovers R = (1060.0, 2050.0) m and orientation constant.",
        )
    )

    d2 = group_dir / "totalstation_resection" / "example_2_three_point_minimal"
    red2 = _copy_into(assets["syn_reductions_json"], d2 / "inputs" / "reductions.json")
    kn2 = _write_json(d2 / "inputs" / "known_3pts.json", syn.known_points(("A", "B", "C")))
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_three_point_minimal",
            "Minimal 3-target resection at station R from control triangle (A, B, C)",
            "Determines station R using only 3 control stations (A, B, C).",
            {
                "REDUCTIONS": str(red2),
                "STATION": "R",
                "KNOWN": str(kn2),
                "OUTPUT_POSITION": str(d2 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
            },
            "Recovers exact coordinates of station R from 3 known points.",
        )
    )

    d3 = group_dir / "totalstation_resection" / "example_3_offset_approximate_start"
    red3 = _copy_into(assets["syn_reductions_json"], d3 / "inputs" / "reductions.json")
    kn3 = _copy_into(assets["syn_known_json"], d3 / "inputs" / "known.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_offset_approximate_start",
            "Resection starting from an explicit offset approximate position (1135, 980)",
            "Tests Gauss-Newton convergence when explicit approximate easting/northing are 18 m off.",
            {
                "REDUCTIONS": str(red3),
                "STATION": "R",
                "KNOWN": str(kn3),
                "APPROX_EASTING": 1135.0,
                "APPROX_NORTHING": 980.0,
                "OUTPUT_POSITION": str(d3 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
            },
            "Converges from (1135, 980) to exact R = (1120.0, 990.0) m.",
        )
    )

    # 5. geocomp:totalstation_intersection
    alg = "geocomp:totalstation_intersection"
    alg_title = "Forward intersection"
    menu_path = "GeoComp ▸ Total Station ▸ Forward intersection"
    d1 = group_dir / "totalstation_intersection" / "example_1_two_ray_p1"
    s1 = _write_json(d1 / "inputs" / "sightings_p1.json", syn.sightings_document("P1", ("A", "C")))
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_two_ray_p1",
            "Two-ray forward intersection to inaccessible target P1 from A and C",
            "Intersects azimuth rays from stations A and C onto target P1.",
            {
                "SIGHTINGS": str(s1),
                "TARGET": "P1",
                "OUTPUT_POSITION": str(d1 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
            },
            "Recovers P1 coordinates with strong intersection geometry.",
        )
    )

    d2 = group_dir / "totalstation_intersection" / "example_2_three_ray_redundant"
    s2 = _write_json(
        d2 / "inputs" / "sightings_p1_3rays.json", syn.sightings_document("P1", ("A", "B", "C"))
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_three_ray_redundant",
            "Redundant 3-ray least-squares forward intersection to P1 from A, B, and C",
            "Over-determined 3-ray intersection to P1 at 99% confidence.",
            {
                "SIGHTINGS": str(s2),
                "TARGET": "P1",
                "SIGMA_AZIMUTH": 5.0 / 3600.0,
                "CONFIDENCE": 0.99,
                "OUTPUT_POSITION": str(d2 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
            },
            "Computes least-squares position and 99% error ellipse for P1.",
        )
    )

    d3 = group_dir / "totalstation_intersection" / "example_3_four_ray_target_p2"
    s3 = _write_json(
        d3 / "inputs" / "sightings_p2_4rays.json",
        syn.sightings_document("P2", ("A", "B", "C", "D")),
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_four_ray_target_p2",
            "Four-ray forward intersection to target P2 from all four control pillars (A, B, C, D)",
            "Intersects 4 azimuth rays onto target P2 with 2 degrees of freedom.",
            {
                "SIGHTINGS": str(s3),
                "TARGET": "P2",
                "SIGMA_AZIMUTH": 3.0 / 3600.0,
                "CONFIDENCE": 0.95,
                "OUTPUT_POSITION": str(d3 / "outputs" / "position.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
            },
            "Recovers exact P2 coordinates with 4-ray redundancy.",
        )
    )

    # 6. geocomp:totalstation_network
    alg = "geocomp:totalstation_network"
    alg_title = "Classical network"
    menu_path = "GeoComp ▸ Total Station ▸ Classical network"
    d1 = group_dir / "totalstation_network" / "example_1_2d_inner_constraint"
    red1 = _copy_into(assets["rd01_reduced_json"], d1 / "inputs" / "reduced.json")
    ap1 = _copy_into(assets["rd01_approx_json"], d1 / "inputs" / "approximate.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_2d_inner_constraint",
            "2D planimetric classical network adjustment (RD-01) with inner constraint",
            "Adjusts the 3-station RD-01 triangle in 2D under minimum-trace inner constraint.",
            {
                "REDUCTIONS": str(red1),
                "APPROXIMATE": str(ap1),
                "DIMENSION": 0,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(d1 / "outputs" / "network.json"),
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_STATIONS": str(d1 / "outputs" / "stations.csv"),
            },
            "Adjusts RD-01 in 2D with 4 degrees of freedom and writes network.json + solution.json.",
        )
    )

    d2 = group_dir / "totalstation_network" / "example_2_3d_network_adjustment"
    red2 = _copy_into(assets["rd01_reduced_json"], d2 / "inputs" / "reduced.json")
    ap2 = _copy_into(assets["rd01_approx_json"], d2 / "inputs" / "approximate.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_3d_network_adjustment",
            "3D classical network adjustment preserving instrument and target heights (DIMENSION=1)",
            "Simultaneously adjusts horizontal directions, zenith angles, and slope distances in 3D.",
            {
                "REDUCTIONS": str(red2),
                "APPROXIMATE": str(ap2),
                "DIMENSION": 1,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(d2 / "outputs" / "network.json"),
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_STATIONS": str(d2 / "outputs" / "stations.csv"),
            },
            "Produces 3D station coordinates and full 3D covariance matrices.",
        )
    )

    d3 = group_dir / "totalstation_network" / "example_3_1d_vertical_network_csv_approx"
    red3 = _copy_into(assets["rd01_reduced_json"], d3 / "inputs" / "reduced.json")
    ap3_csv = _write_text(
        d3 / "inputs" / "approximate.csv",
        "station,easting,northing,height\n"
        + "".join(
            f"{name},{e!r},{n!r},{u!r}\n"
            for name, (e, n, u) in rd01.approximate_coordinates().items()
        ),
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_1d_vertical_network_csv_approx",
            "1D height network adjustment (DIMENSION=2) reading approximate coordinates from CSV",
            "Adjusts trigonometric heights in 1D using a CSV table of approximate station coordinates.",
            {
                "REDUCTIONS": str(red3),
                "APPROXIMATE": str(ap3_csv),
                "DIMENSION": 2,
                "DATUM": 1,
                "CRS": "EPSG:31982",
                "OUTPUT_NETWORK": str(d3 / "outputs" / "network.json"),
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_STATIONS": str(d3 / "outputs" / "stations.csv"),
            },
            "Adjusts 1D heights agreeing with the 3D vertical solution.",
        )
    )

    # 7. geocomp:totalstation_trig_levelling
    alg = "geocomp:totalstation_trig_levelling"
    alg_title = "Trigonometric levelling"
    menu_path = "GeoComp ▸ Total Station ▸ Trigonometric levelling"
    d1 = group_dir / "totalstation_trig_levelling" / "example_1_radial_curvature_refraction"
    red1 = _copy_into(assets["syn_reductions_json"], d1 / "inputs" / "reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_radial_curvature_refraction",
            "Radial trigonometric levelling (MODE=0) with Earth curvature and refraction (k=0.13)",
            "Computes height differences from single-ended and reciprocal zenith angles across all setups.",
            {
                "REDUCTIONS": str(red1),
                "MODE": 0,
                "REFRACTION": 0.13,
                "REFRACTION_SIGMA": 0.05,
                "OUTPUT_HEIGHTS": str(d1 / "outputs" / "heights.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "differences.csv"),
            },
            "Computes radial height differences with curvature and refraction corrections.",
        )
    )

    d2 = group_dir / "totalstation_trig_levelling" / "example_2_balanced_leapfrog"
    red2 = _copy_into(assets["syn_leapfrog_json"], d2 / "inputs" / "leapfrog_reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_balanced_leapfrog",
            "Balanced leap-frog trigonometric levelling from midpoint station L (A -> D)",
            "Station L stands midway between A and D so curvature and refraction cancel out.",
            {
                "REDUCTIONS": str(red2),
                "MODE": 1,
                "OUTPUT_HEIGHTS": str(d2 / "outputs" / "heights.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "differences.csv"),
            },
            "Recovers exact height difference A -> D (+1.500 m) with 1 leap-frog pair.",
        )
    )

    d3 = group_dir / "totalstation_trig_levelling" / "example_3_custom_refraction_and_heights"
    red3 = _copy_into(assets["syn_reductions_json"], d3 / "inputs" / "reductions.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_custom_refraction_and_heights",
            "Radial trigonometric levelling with high refraction (k=0.18) and custom prism height",
            "Evaluates vertical differences under strong thermal inversion refraction (k=0.18 ± 0.08).",
            {
                "REDUCTIONS": str(red3),
                "MODE": 0,
                "INSTRUMENT_HEIGHT": 1.60,
                "TARGET_HEIGHT": 1.60,
                "REFRACTION": 0.18,
                "REFRACTION_SIGMA": 0.08,
                "OUTPUT_HEIGHTS": str(d3 / "outputs" / "heights.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "differences.csv"),
            },
            "Writes height differences and propagates refraction uncertainty.",
        )
    )

    # 8. geocomp:totalstation_radiation
    alg = "geocomp:totalstation_radiation"
    alg_title = "3D radiation"
    menu_path = "GeoComp ▸ Total Station ▸ 3D radiation"
    d1 = group_dir / "totalstation_radiation" / "example_1_detail_points_from_known_control"
    red1 = _copy_into(assets["syn_reductions_json"], d1 / "inputs" / "reductions.json")
    kn1 = _copy_into(assets["syn_known_json"], d1 / "inputs" / "known.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_detail_points_from_known_control",
            "3D radiation of detail points P1 and P2 orienting automatically from known stations",
            "Radiates non-control detail points (P1, P2) from setup A using backsights to known stations B "
            "and D.",
            {
                "REDUCTIONS": str(red1),
                "STATIONS": str(kn1),
                "INSTRUMENT_HEIGHT": syn.INSTRUMENT_HEIGHT,
                "TARGET_HEIGHT": syn.TARGET_HEIGHT,
                "CORRELATION": 0.0,
                "OUTPUT_POINTS": str(d1 / "outputs" / "points.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "points.csv"),
            },
            "Recovers exact 3D coordinates of detail points P1 and P2 with full 3x3 covariance.",
        )
    )

    d2 = group_dir / "totalstation_radiation" / "example_2_with_explicit_orientations"
    red2 = _copy_into(assets["syn_reductions_json"], d2 / "inputs" / "reductions.json")
    kn2 = _copy_into(assets["syn_known_json"], d2 / "inputs" / "known.json")
    or2 = _write_json(
        d2 / "inputs" / "orientations.json",
        {name: math.degrees(val) for name, val in syn.ORIENTATIONS.items()},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_with_explicit_orientations",
            "3D radiation using pre-computed station orientation constants (orientations.json)",
            "Supplies explicit orientation angles for occupied stations via orientations.json.",
            {
                "REDUCTIONS": str(red2),
                "STATIONS": str(kn2),
                "ORIENTATIONS": str(or2),
                "INSTRUMENT_HEIGHT": 1.50,
                "TARGET_HEIGHT": 1.50,
                "OUTPUT_POINTS": str(d2 / "outputs" / "points.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "points.csv"),
            },
            "Radiates P1 and P2 using pre-computed orientations.",
        )
    )

    d3 = group_dir / "totalstation_radiation" / "example_3_displaced_control_warning"
    red3 = _copy_into(assets["syn_reductions_json"], d3 / "inputs" / "reductions.json")
    moved = dict(syn.known_points())
    moved["B"] = [moved["B"][0] + 0.500, moved["B"][1], moved["B"][2]]
    kn3 = _write_json(d3 / "inputs" / "displaced_known.json", moved)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_displaced_control_warning",
            "3D radiation detecting a 0.50 m displaced backsight control station (B)",
            "Tests orientation spread warning when known station B is displaced by 0.50 m.",
            {
                "REDUCTIONS": str(red3),
                "STATIONS": str(kn3),
                "CORRELATION": 0.3,
                "OUTPUT_POINTS": str(d3 / "outputs" / "points.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "points.csv"),
            },
            "Radiates detail points and warns that backsight control disagrees with recorded coordinates.",
        )
    )

    return specs


def _build_levelling_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    group_id = "02_level"
    group_title = "Level"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    # 1. geocomp:levelling_import
    alg = "geocomp:levelling_import"
    alg_title = "Import levelling field book"
    menu_path = "GeoComp ▸ Level ▸ Import levelling field book"
    d1 = group_dir / "levelling_import" / "example_1_balanced_line"
    bk1 = _copy_into(assets["lev_bal_csv"], d1 / "inputs" / "book.csv")
    mp1 = _copy_into(assets["lev_map_json"], d1 / "inputs" / "mapping.json")
    pr1 = _copy_into(assets["lev_profiles_json"], d1 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_balanced_line",
            "Balanced 3-setup differential levelling line (RD-04) with level profile",
            "Imports 3 setups along a single levelling line using mapping.json and profiles.json.",
            {
                "BOOK": str(bk1),
                "MAPPING": str(mp1),
                "PROFILES": str(pr1),
                "OUTPUT_SETUPS": str(d1 / "outputs" / "setups.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
            },
            "Imports 3 setups and 1 line with 0 rejected rows.",
        )
    )

    d2 = group_dir / "levelling_import" / "example_2_four_line_loop"
    bk2 = _copy_into(assets["lev_loop_csv"], d2 / "inputs" / "loop_book.csv")
    mp2 = _copy_into(assets["lev_loop_map_json"], d2 / "inputs" / "loop_mapping.json")
    pr2 = _copy_into(assets["lev_profiles_json"], d2 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_four_line_loop",
            "Multi-line closed levelling loop field book with line column mapping",
            "Imports 4 connected levelling lines forming a closed loop around benchmarks.",
            {
                "BOOK": str(bk2),
                "MAPPING": str(mp2),
                "PROFILES": str(pr2),
                "OUTPUT_SETUPS": str(d2 / "outputs" / "setups.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
            },
            "Groups setups into 4 distinct levelling lines.",
        )
    )

    d3 = group_dir / "levelling_import" / "example_3_extreme_sights_default_sigma"
    bk3 = _copy_into(assets["lev_ext_csv"], d3 / "inputs" / "extreme_book.csv")
    mp3 = _copy_into(assets["lev_map_json"], d3 / "inputs" / "mapping.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_extreme_sights_default_sigma",
            "Radial setup with intermediate foresights (IS) and explicit staff-reading sigma",
            "Imports a setup with backsight BS, foresight FS, and intermediate sights IS using "
            "SIGMA_READING=0.0005 m.",
            {
                "BOOK": str(bk3),
                "MAPPING": str(mp3),
                "SIGMA_READING": 0.0005,
                "STADIA_FACTOR": 100.0,
                "OUTPUT_SETUPS": str(d3 / "outputs" / "setups.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
            },
            "Imports multi-foresight setup with 0.5 mm staff reading standard deviation.",
        )
    )

    # 2. geocomp:levelling_equal_sights
    alg = "geocomp:levelling_equal_sights"
    alg_title = "Equal sights"
    menu_path = "GeoComp ▸ Level ▸ Equal sights"
    d1 = group_dir / "levelling_equal_sights" / "example_1_balanced_line"
    st1 = _copy_into(assets["lev_bal_setups"], d1 / "inputs" / "setups.json")
    pr1 = _copy_into(assets["lev_profiles_json"], d1 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_balanced_line",
            "Balanced equal-sights reduction recovering exact height difference",
            "Reduces balanced setups with zero sight-length imbalance.",
            {
                "SETUPS": str(st1),
                "PROFILES": str(pr1),
                "OUTPUT_REDUCTIONS": str(d1 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "lines.csv"),
            },
            "Produces reduced line with 0.0 m sight imbalance.",
        )
    )

    d2 = group_dir / "levelling_equal_sights" / "example_2_four_line_loop_reduction"
    st2 = _copy_into(assets["lev_loop_setups"], d2 / "inputs" / "loop_setups.json")
    pr2 = _copy_into(assets["lev_profiles_json"], d2 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_four_line_loop_reduction",
            "Equal-sights reduction of all 4 lines in a closed levelling loop",
            "Reduces all 4 lines of the RD-04 loop into a single reductions document.",
            {
                "SETUPS": str(st2),
                "PROFILES": str(pr2),
                "OUTPUT_REDUCTIONS": str(d2 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "lines.csv"),
            },
            "Reduces 4 lines (LINE_COUNT=4) ready for loop closure and network adjustment.",
        )
    )

    d3 = group_dir / "levelling_equal_sights" / "example_3_imbalanced_line_with_collimation"
    st3 = _copy_into(assets["lev_imb_setups"], d3 / "inputs" / "imbalanced_setups.json")
    pr3 = _copy_into(assets["lev_profiles_json"], d3 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_imbalanced_line_with_collimation",
            "Imbalanced sights reduced with collimation correction and strict imbalance limits",
            "Applies collimation angle (5e-5 rad) across unbalanced sights and checks sight-imbalance "
            "limits.",
            {
                "SETUPS": str(st3),
                "PROFILES": str(pr3),
                "COLLIMATION": 5e-5,
                "COLLIMATION_SIGMA": 1e-5,
                "MAX_SIGHT_LENGTH": 50.0,
                "MAX_SIGHT_IMBALANCE": 2.0,
                "MAX_ACCUMULATED_IMBALANCE": 5.0,
                "OUTPUT_REDUCTIONS": str(d3 / "outputs" / "reduced.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "lines.csv"),
            },
            "Applies collimation correction and flags sight imbalance in the HTML report.",
        )
    )

    # 3. geocomp:levelling_equidistant_sights
    alg = "geocomp:levelling_equidistant_sights"
    alg_title = "Equidistant sights"
    menu_path = "GeoComp ▸ Level ▸ Equidistant sights"
    d1 = group_dir / "levelling_equidistant_sights" / "example_1_reciprocal_crossing"
    st1 = _copy_into(assets["lev_recip_setups"], d1 / "inputs" / "crossing_setups.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_reciprocal_crossing",
            "Reciprocal river-crossing levelling cancelling refraction and collimation",
            "Averages opposite-bank setups to cancel 12 mm refraction error.",
            {
                "SETUPS": str(st1),
                "INFLATION": 2.0,
                "DISCREPANCY_TOLERANCE": 0.030,
                "OUTPUT_DIFFERENCES": str(d1 / "outputs" / "crossing.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "crossings.csv"),
            },
            "Cancels refraction error and recovers true crossing height difference.",
        )
    )

    d2 = group_dir / "levelling_equidistant_sights" / "example_2_high_variance_inflation"
    st2 = _copy_into(assets["lev_recip_setups"], d2 / "inputs" / "crossing_setups.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_high_variance_inflation",
            "Reciprocal crossing with 3.5x variance inflation factor",
            "Inflates crossing uncertainty by 3.5x to account for long-sight atmospheric turbulence.",
            {
                "SETUPS": str(st2),
                "INFLATION": 3.5,
                "DISCREPANCY_TOLERANCE": 0.030,
                "OUTPUT_DIFFERENCES": str(d2 / "outputs" / "crossing.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "crossings.csv"),
            },
            "Outputs crossing height difference with 3.5x variance inflation.",
        )
    )

    d3 = group_dir / "levelling_equidistant_sights" / "example_3_discrepancy_exceeded"
    st3 = _copy_into(assets["lev_recip_setups"], d3 / "inputs" / "crossing_setups.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_discrepancy_exceeded",
            "Reciprocal crossing with tight 5 mm discrepancy tolerance flagging the 24 mm spread",
            "Checks diagnostic flagging when bank-to-bank spread (24 mm) exceeds DISCREPANCY_TOLERANCE (5 "
            "mm).",
            {
                "SETUPS": str(st3),
                "INFLATION": 2.0,
                "DISCREPANCY_TOLERANCE": 0.005,
                "OUTPUT_DIFFERENCES": str(d3 / "outputs" / "crossing.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "crossings.csv"),
            },
            "Flags the 24 mm forward/reverse discrepancy against the 5 mm tolerance.",
        )
    )

    # 4. geocomp:levelling_extreme_sights
    alg = "geocomp:levelling_extreme_sights"
    alg_title = "Extreme sights"
    menu_path = "GeoComp ▸ Level ▸ Extreme sights"
    d1 = group_dir / "levelling_extreme_sights" / "example_1_multiple_foresights"
    st1 = _copy_into(assets["lev_ext_setups"], d1 / "inputs" / "extreme_setups.json")
    pr1 = _copy_into(assets["lev_profiles_json"], d1 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_multiple_foresights",
            "Correlated height differences from a multi-foresight setup (BM1 -> BM3, S1, S2)",
            "Computes correlated height differences sharing a common backsight reading at BM1.",
            {
                "SETUPS": str(st1),
                "ONLY_MULTIPLE": True,
                "PROFILES": str(pr1),
                "OUTPUT_DIFFERENCES": str(d1 / "outputs" / "differences.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "differences.csv"),
            },
            "Produces 3 correlated height differences with full covariance matrix.",
        )
    )

    d2 = group_dir / "levelling_extreme_sights" / "example_2_include_single_foresight_setups"
    st2 = _copy_into(assets["lev_bal_setups"], d2 / "inputs" / "balanced_setups.json")
    pr2 = _copy_into(assets["lev_profiles_json"], d2 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_include_single_foresight_setups",
            "Extreme-sights reduction including single-foresight setups (ONLY_MULTIPLE=False)",
            "Runs extreme-sights reduction across standard single-foresight setups.",
            {
                "SETUPS": str(st2),
                "ONLY_MULTIPLE": False,
                "PROFILES": str(pr2),
                "OUTPUT_DIFFERENCES": str(d2 / "outputs" / "differences.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "differences.csv"),
            },
            "Extracts per-setup height differences for all 3 setups.",
        )
    )

    d3 = group_dir / "levelling_extreme_sights" / "example_3_strict_sight_limits"
    st3 = _copy_into(assets["lev_ext_setups"], d3 / "inputs" / "extreme_setups.json")
    pr3 = _copy_into(assets["lev_profiles_json"], d3 / "inputs" / "profiles.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_strict_sight_limits",
            "Multi-foresight setup checked against strict 20 m sight-length and 2 m imbalance limits",
            "Enforces MAX_SIGHT_LENGTH=20 m and MAX_SIGHT_IMBALANCE=2 m on radial sights.",
            {
                "SETUPS": str(st3),
                "ONLY_MULTIPLE": True,
                "PROFILES": str(pr3),
                "MAX_SIGHT_LENGTH": 20.0,
                "MAX_SIGHT_IMBALANCE": 2.0,
                "OUTPUT_DIFFERENCES": str(d3 / "outputs" / "differences.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "differences.csv"),
            },
            "Computes correlated differences and logs sight-length/imbalance warnings.",
        )
    )

    # 5. geocomp:levelling_closures
    alg = "geocomp:levelling_closures"
    alg_title = "Closures and tolerances"
    menu_path = "GeoComp ▸ Level ▸ Closures and tolerances"
    d1 = group_dir / "levelling_closures" / "example_1_loop_closure_by_length"
    red1 = _copy_into(assets["lev_loop_red"], d1 / "inputs" / "loop_reduced.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_loop_closure_by_length",
            "Closed 4-line loop closure check (k = 8 mm/sqrt(km)) distributed by line length",
            "Checks loop misclosure against 8 mm/sqrt(km) tolerance and distributes proportionally to "
            "length.",
            {
                "REDUCTIONS": str(red1),
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": 0.008,
                "WEIGHTING": 0,
                "LOOP_ID": "RD04_Loop",
                "OUTPUT_CLOSURES": str(d1 / "outputs" / "closures.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "distribution.csv"),
            },
            "Passes tolerance and distributes loop misclosure across the 4 lines.",
        )
    )

    d2 = group_dir / "levelling_closures" / "example_2_line_against_known_difference"
    red2 = _copy_into(assets["lev_bal_red"], d2 / "inputs" / "line_reduced.json")
    bal_payload = json.loads(assets["lev_bal_red"].read_text(encoding="utf-8"))
    true_dh = float(bal_payload["lines"][0]["height_difference"]["value"])
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_line_against_known_difference",
            "Single levelling line checked against known benchmark difference distributing by setups",
            "Compares reduced line against known height difference (+0.4 mm offset) with WEIGHTING=1.",
            {
                "REDUCTIONS": str(red2),
                "MODE": 1,
                "KNOWN_DIFFERENCE": true_dh - 0.0004,
                "KNOWN_SIGMA": 0.0002,
                "TOLERANCE_COEFFICIENT": 0.008,
                "WEIGHTING": 1,
                "LOOP_ID": "Line_Check",
                "OUTPUT_CLOSURES": str(d2 / "outputs" / "closures.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "distribution.csv"),
            },
            "Evaluates +0.4 mm misclosure against known benchmark height difference.",
        )
    )

    d3 = group_dir / "levelling_closures" / "example_3_failing_tight_tolerance"
    red3 = _copy_into(assets["lev_loop_red"], d3 / "inputs" / "loop_reduced.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_failing_tight_tolerance",
            "Loop closure failing an ultra-tight 0.05 mm/sqrt(km) tolerance",
            "Tests tolerance failure reporting when TOLERANCE_COEFFICIENT is set to 0.00005 m/sqrt(km).",
            {
                "REDUCTIONS": str(red3),
                "MODE": 0,
                "TOLERANCE_COEFFICIENT": 0.00005,
                "WEIGHTING": 0,
                "LOOP_ID": "Special_Order_Loop",
                "OUTPUT_CLOSURES": str(d3 / "outputs" / "closures.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "distribution.csv"),
            },
            "Flags the loop as exceeding permissible misclosure in closures.json.",
        )
    )

    # 6. geocomp:levelling_network
    alg = "geocomp:levelling_network"
    alg_title = "Levelling network adjustment"
    menu_path = "GeoComp ▸ Level ▸ Levelling network adjustment"
    d1 = group_dir / "levelling_network" / "example_1_constrained_benchmark_loop"
    red1 = _copy_into(assets["lev_loop_red"], d1 / "inputs" / "loop_reduced.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_constrained_benchmark_loop",
            "Constrained 1D levelling loop adjustment holding BM1 = 100.000 m",
            "Least-squares adjustment of 4-line loop weighted by line length holding BM1 fixed.",
            {
                "REDUCTIONS": str(red1),
                "BENCHMARKS": "BM1=100.0",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.001,
                "FREE": False,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "heights.csv"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "network.json"),
            },
            "Adjusts benchmark heights around the loop with 1 degree of freedom.",
        )
    )

    d2 = group_dir / "levelling_network" / "example_2_free_network_by_setups"
    red2 = _copy_into(assets["lev_loop_red"], d2 / "inputs" / "loop_reduced.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_free_network_by_setups",
            "Free inner-constraint levelling network weighted by number of setups",
            "Solves a free 1D levelling network (FREE=True) weighted by setup count.",
            {
                "REDUCTIONS": str(red2),
                "BENCHMARKS": "BM1=100.0",
                "WEIGHTING": 1,
                "SIGMA_PER_SETUP": 0.0005,
                "FREE": True,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "heights.csv"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "network.json"),
            },
            "Produces inner-constraint 1D vertical solution.",
        )
    )

    d3 = group_dir / "levelling_network" / "example_3_with_tolerance_gate_and_snooping"
    red3 = _copy_into(assets["lev_loop_red"], d3 / "inputs" / "loop_reduced.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_with_tolerance_gate_and_snooping",
            "Levelling network with tolerance gate (k=8 mm/sqrt(km)), ADJUST_FAILING=True, and 99% "
            "confidence",
            "Adjusts loop with pre-adjustment tolerance checking and Baarda data snooping.",
            {
                "REDUCTIONS": str(red3),
                "BENCHMARKS": "BM1=100.0",
                "WEIGHTING": 0,
                "SIGMA_PER_KM": 0.001,
                "CONFIDENCE": 0.99,
                "TOLERANCE_COEFFICIENT": 0.008,
                "ADJUST_FAILING": True,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "heights.csv"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "network.json"),
            },
            "Evaluates line tolerances and completes 99% confidence 1D adjustment.",
        )
    )

    return specs


def _build_gnss_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    group_id = "03_gnss"
    group_title = "GNSS"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    def _populate_rinex(target_dir: Path, extra_station: bool = False) -> Path:
        _copy_into(assets["rinex_dir"], target_dir)
        if extra_station:
            rover_text = (target_dir / "rover.05o").read_text(encoding="utf-8")
            aux_text = rover_text.replace("ROVE", "AUX1")
            (target_dir / "aux1.05o").write_text(aux_text, encoding="utf-8")
        return target_dir

    def _write_rtklib_conf(path: Path, mode: str = "kinematic", elmask: int = 15) -> Path:
        return _write_text(
            path,
            f"# Custom RTKLIB options ({mode})\n"
            f"pos1-elmask        ={elmask}\n"
            "pos1-frequency     =l1+l2\n"
            "pos1-soltype       =combined\n"
            "pos2-armode        =continuous\n",
        )

    # 1. geocomp:gnss_scan_sessions
    alg = "geocomp:gnss_scan_sessions"
    alg_title = "Scan sessions"
    menu_path = "GeoComp ▸ GNSS ▸ Scan sessions"
    d1 = group_dir / "gnss_scan_sessions" / "example_1_two_station_session"
    r1 = _populate_rinex(d1 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_two_station_session",
            "Two-station static/kinematic RINEX session (BASE + ROVE) with broadcast nav",
            "Scans folder containing base.05o, rover.05o, and brdc.05n on 2005-05-20.",
            {
                "FOLDER": str(r1),
                "OUTPUT_JSON": str(d1 / "outputs" / "sessions.json"),
            },
            "Detects 2 observation stations (BASE, ROVE), 1 navigation file, and temporal overlap.",
        )
    )

    d2 = group_dir / "gnss_scan_sessions" / "example_2_three_station_network_session"
    r2 = _populate_rinex(d2 / "inputs" / "rinex", extra_station=True)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_three_station_network_session",
            "Three-station simultaneous RINEX campaign (BASE, ROVE, AUX1)",
            "Scans multi-station campaign folder with 3 simultaneous receivers.",
            {
                "FOLDER": str(r2),
                "OUTPUT_JSON": str(d2 / "outputs" / "sessions.json"),
            },
            "Identifies all 3 stations (AUX1, BASE, ROVE) in the session summary.",
        )
    )

    d3 = group_dir / "gnss_scan_sessions" / "example_3_single_receiver_ppp_session"
    r3 = d3 / "inputs" / "rinex_single"
    r3.mkdir(parents=True, exist_ok=True)
    shutil.copy2(assets["rinex_dir"] / "rover.05o", r3 / "rover.05o")
    shutil.copy2(assets["rinex_dir"] / "brdc.05n", r3 / "brdc.05n")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_single_receiver_ppp_session",
            "Single-receiver standalone/PPP RINEX folder (ROVE only)",
            "Scans a folder with a single rover receiver and navigation file (no base station).",
            {
                "FOLDER": str(r3),
                "OUTPUT_JSON": str(d3 / "outputs" / "sessions.json"),
            },
            "Reports 1 observation file (ROVE) ready for absolute positioning.",
        )
    )

    # 2. geocomp:gnss_download_products
    alg = "geocomp:gnss_download_products"
    alg_title = "Download products"
    menu_path = "GeoComp ▸ GNSS ▸ Download products"
    d1 = group_dir / "gnss_download_products" / "example_1_from_rinex_folder_final"
    r1 = _populate_rinex(d1 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_from_rinex_folder_final",
            "Download final SP3 orbit and GPS broadcast navigation for a RINEX folder's dates",
            "Infers GPS week 1323 / DOY 140 (2005-05-20) from RINEX headers and fetches SP3 + BRDC.",
            {
                "FOLDER": str(r1),
                "PRODUCTS": [0, 1],
                "LATENCY": 0,
                "CHECK_ONLY": False,
                "OUTPUT_DIRECTORY": str(d1 / "outputs" / "products"),
                "OUTPUT_JSON": str(d1 / "outputs" / "manifest.json"),
            },
            "Downloads igs13235.sp3 and brdc1400.05n into products/ and writes manifest.json.",
        )
    )

    d2 = group_dir / "gnss_download_products" / "example_2_explicit_date_range_rapid"
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_explicit_date_range_rapid",
            "Explicit date range query for Rapid SP3 + GLONASS navigation",
            "Requests Rapid orbits (igr) and GLONASS broadcast navigation for 2005-05-20.",
            {
                "FIRST_DAY": "2005-05-20",
                "LAST_DAY": "2005-05-20",
                "PRODUCTS": [0, 2],
                "LATENCY": 1,
                "CHECK_ONLY": False,
                "OUTPUT_DIRECTORY": str(d2 / "outputs" / "products"),
                "OUTPUT_JSON": str(d2 / "outputs" / "manifest.json"),
            },
            "Fetches rapid orbit and GLONASS navigation files for 2005-05-20.",
        )
    )

    d3 = group_dir / "gnss_download_products" / "example_3_check_availability_only"
    r3 = _populate_rinex(d3 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_check_availability_only",
            "Dry-run availability check (CHECK_ONLY=True) without downloading payloads",
            "Probes product archive availability for SP3 + GPS nav without copying files.",
            {
                "FOLDER": str(r3),
                "PRODUCTS": [0, 1],
                "LATENCY": 0,
                "CHECK_ONLY": True,
                "OUTPUT_JSON": str(d3 / "outputs" / "manifest.json"),
            },
            "Verifies AVAILABLE=2, MISSING=0 and writes availability manifest.",
        )
    )

    # 3. geocomp:gnss_absolute_static
    alg = "geocomp:gnss_absolute_static"
    alg_title = "Absolute — Static"
    menu_path = "GeoComp ▸ GNSS ▸ Absolute ▸ Absolute — Static"
    for idx, (slug, title, desc, mask, use_conf) in enumerate(
        [
            (
                "example_1_default_rover_static",
                "Absolute static point positioning of ROVE with 15° elevation mask",
                "Runs static single-point/PPP positioning on station ROVE with 15° mask.",
                15.0,
                False,
            ),
            (
                "example_2_high_elevation_mask_25deg",
                "Absolute static positioning of BASE with 25° multipath-rejection mask",
                "Processes station BASE in static mode with an elevated 25° cutoff angle.",
                25.0,
                False,
            ),
            (
                "example_3_custom_rtklib_conf",
                "Absolute static positioning with custom RTKLIB configuration file",
                "Uses an explicit RTKLIB .conf file overriding ionosphere/troposphere options.",
                10.0,
                True,
            ),
        ],
        start=1,
    ):
        d = group_dir / "gnss_absolute_static" / slug
        rdir = _populate_rinex(d / "inputs" / "rinex")
        params: dict[str, Any] = {
            "FOLDER": str(rdir),
            "ROVER_STATION": "BASE" if idx == 2 else "ROVE",
            "ELEVATION_MASK": mask,
            "KEEP_WORK_DIR": True,
            "OUTPUT_POS": str(d / "outputs" / "solution.pos"),
            "OUTPUT_JSON": str(d / "outputs" / "quality.json"),
        }
        if use_conf:
            conf = _write_rtklib_conf(d / "inputs" / "custom_static.conf", mode="single", elmask=10)
            params["CONFIGURATION"] = str(conf)
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                params,
                "Produces static .pos solution and quality summary JSON.",
            )
        )

    # 4. geocomp:gnss_absolute_kinematic
    alg = "geocomp:gnss_absolute_kinematic"
    alg_title = "Absolute — Kinematic"
    menu_path = "GeoComp ▸ GNSS ▸ Absolute ▸ Absolute — Kinematic"
    for idx, (slug, title, desc, mask, use_conf) in enumerate(
        [
            (
                "example_1_rover_kinematic_trajectory",
                "Absolute kinematic trajectory of ROVE with default settings",
                "Computes epoch-by-epoch standalone kinematic trajectory for station ROVE.",
                15.0,
                False,
            ),
            (
                "example_2_low_mask_10deg",
                "Absolute kinematic trajectory with low 10° elevation mask",
                "Includes low-elevation satellites down to 10° for urban/canopy kinematic tracking.",
                10.0,
                False,
            ),
            (
                "example_3_custom_kinematic_conf",
                "Absolute kinematic positioning with explicit RTKLIB configuration",
                "Runs kinematic positioning driven by a custom RTKLIB configuration file.",
                20.0,
                True,
            ),
        ],
        start=1,
    ):
        d = group_dir / "gnss_absolute_kinematic" / slug
        rdir = _populate_rinex(d / "inputs" / "rinex")
        params = {
            "FOLDER": str(rdir),
            "ROVER_STATION": "ROVE",
            "ELEVATION_MASK": mask,
            "KEEP_WORK_DIR": True,
            "OUTPUT_POS": str(d / "outputs" / "solution.pos"),
            "OUTPUT_JSON": str(d / "outputs" / "quality.json"),
        }
        if use_conf:
            conf = _write_rtklib_conf(d / "inputs" / "custom_kinematic.conf", mode="single", elmask=20)
            params["CONFIGURATION"] = str(conf)
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                params,
                "Produces epoch-by-epoch kinematic .pos file and quality metrics.",
            )
        )

    # 5. geocomp:gnss_relative_static
    alg = "geocomp:gnss_relative_static"
    alg_title = "Relative — Static"
    menu_path = "GeoComp ▸ GNSS ▸ Relative ▸ Relative — Static"
    for idx, (slug, title, desc, frame_idx, mask, use_conf) in enumerate(
        [
            (
                "example_1_baseline_base_to_rove_sirgas",
                "Relative static baseline BASE -> ROVE in SIRGAS2000 (15° mask)",
                "Carrier-phase static baseline processing between BASE and ROVE in SIRGAS2000.",
                7,
                15.0,
                False,
            ),
            (
                "example_2_baseline_itrf2020_20deg",
                "Relative static baseline BASE -> ROVE in ITRF2020 with 20° mask",
                "Static baseline solution expressed in ITRF2020 with 20° elevation cutoff.",
                2,
                20.0,
                False,
            ),
            (
                "example_3_custom_static_carrier_conf",
                "Relative static baseline with custom L1+L2 RTKLIB configuration file",
                "Uses an explicit RTKLIB static carrier-phase configuration file.",
                1,
                15.0,
                True,
            ),
        ],
        start=1,
    ):
        d = group_dir / "gnss_relative_static" / slug
        rdir = _populate_rinex(d / "inputs" / "rinex")
        params = {
            "FOLDER": str(rdir),
            "BASE_STATION": "BASE",
            "ROVER_STATION": "ROVE",
            "FRAME": frame_idx,
            "ELEVATION_MASK": mask,
            "KEEP_WORK_DIR": True,
            "OUTPUT_POS": str(d / "outputs" / "solution.pos"),
            "OUTPUT_JSON": str(d / "outputs" / "quality.json"),
        }
        if use_conf:
            conf = _write_rtklib_conf(d / "inputs" / "static_l1l2.conf", mode="static", elmask=15)
            params["CONFIGURATION"] = str(conf)
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                params,
                "Solves carrier-phase static baseline BASE -> ROVE with fixed ambiguities (Q=1).",
            )
        )

    # 6. geocomp:gnss_relative_kinematic
    alg = "geocomp:gnss_relative_kinematic"
    alg_title = "Relative — Kinematic"
    menu_path = "GeoComp ▸ GNSS ▸ Relative ▸ Relative — Kinematic"
    for idx, (slug, title, desc, frame_idx, mask, use_conf) in enumerate(
        [
            (
                "example_1_kinematic_ppk_sirgas2000",
                "Post-processed kinematic (PPK) baseline BASE -> ROVE in SIRGAS2000",
                "Relative kinematic carrier-phase trajectory of ROVE referenced to BASE.",
                7,
                15.0,
                False,
            ),
            (
                "example_2_kinematic_itrf2014_25deg",
                "Relative kinematic trajectory in ITRF2014 with 25° elevation mask",
                "PPK solution in ITRF2014 with high 25° elevation mask.",
                3,
                25.0,
                False,
            ),
            (
                "example_3_kinematic_custom_conf",
                "Relative kinematic PPK with custom continuous-AR RTKLIB configuration",
                "Runs PPK with explicit RTKLIB configuration file.",
                1,
                15.0,
                True,
            ),
        ],
        start=1,
    ):
        d = group_dir / "gnss_relative_kinematic" / slug
        rdir = _populate_rinex(d / "inputs" / "rinex")
        params = {
            "FOLDER": str(rdir),
            "BASE_STATION": "BASE",
            "ROVER_STATION": "ROVE",
            "FRAME": frame_idx,
            "ELEVATION_MASK": mask,
            "KEEP_WORK_DIR": True,
            "OUTPUT_POS": str(d / "outputs" / "solution.pos"),
            "OUTPUT_JSON": str(d / "outputs" / "quality.json"),
        }
        if use_conf:
            conf = _write_rtklib_conf(d / "inputs" / "kinematic_ppk.conf", mode="kinematic", elmask=15)
            params["CONFIGURATION"] = str(conf)
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                params,
                "Produces relative kinematic .pos trajectory and quality summary.",
            )
        )

    # 7. geocomp:gnss_build_baselines
    alg = "geocomp:gnss_build_baselines"
    alg_title = "Build baselines"
    menu_path = "GeoComp ▸ GNSS ▸ Build baselines"
    d1 = group_dir / "gnss_build_baselines" / "example_1_single_baseline_sirgas2000"
    pdir1 = _copy_into(assets["pos_dir"], d1 / "inputs" / "pos")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_single_baseline_sirgas2000",
            "Build 3D baseline vector and Network JSON from .pos solution in SIRGAS2000",
            "Extracts ECEF baseline vector (dX, dY, dZ) and 3x3 covariance matrix from base_rove.pos.",
            {
                "FOLDER": str(pdir1),
                "BASE_HEIGHT": 0.0,
                "ROVER_HEIGHT": 0.0,
                "INDEPENDENT_ONLY": True,
                "FRAME": 6,
                "OUTPUT_JSON": str(d1 / "outputs" / "baselines.json"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "network.json"),
            },
            "Builds baseline BASE -> ROVE with full 3x3 covariance in SIRGAS2000.",
        )
    )

    d2 = group_dir / "gnss_build_baselines" / "example_2_antenna_height_reduction"
    pdir2 = _copy_into(assets["pos_dir"], d2 / "inputs" / "pos")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_antenna_height_reduction",
            "Baseline extraction with unequal tripod antenna heights (Base 1.42 m, Rover 1.85 m)",
            "Reduces baseline from antenna phase centre to monument marks with 3 mm height uncertainty.",
            {
                "FOLDER": str(pdir2),
                "BASE_HEIGHT": 1.42,
                "ROVER_HEIGHT": 1.85,
                "HEIGHT_SIGMA": 0.003,
                "INDEPENDENT_ONLY": True,
                "FRAME": 1,
                "OUTPUT_JSON": str(d2 / "outputs" / "baselines.json"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "network.json"),
            },
            "Applies vertical antenna height reduction along local ellipsoid normal and inflates vertical "
            "variance.",
        )
    )

    d3 = group_dir / "gnss_build_baselines" / "example_3_multi_baseline_all_vectors"
    pdir3 = _copy_into(assets["pos_dir"], d3 / "inputs" / "pos")
    pos_text = (pdir3 / "base_rove.pos").read_text(encoding="utf-8")
    (pdir3 / "base_aux1.pos").write_text(
        pos_text.replace("rover.05o", "aux1.05o").replace("-3976219.", "-3976250."),
        encoding="utf-8",
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_multi_baseline_all_vectors",
            "Multi-baseline session (BASE->ROVE, BASE->AUX1) with per-station antenna matrix",
            "Extracts multiple baselines using per-station antenna height table (INDEPENDENT_ONLY=False).",
            {
                "FOLDER": str(pdir3),
                "STATION_HEIGHTS": ["BASE", "1.500", "ROVE", "1.600", "AUX1", "1.550"],
                "INDEPENDENT_ONLY": False,
                "FRAME": 2,
                "OUTPUT_JSON": str(d3 / "outputs" / "baselines.json"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "network.json"),
            },
            "Builds 3-station GNSS network (BASE, ROVE, AUX1) with station-specific antenna offsets.",
        )
    )

    # 8. geocomp:gnss_batch
    alg = "geocomp:gnss_batch"
    alg_title = "Batch processing"
    menu_path = "GeoComp ▸ GNSS ▸ Batch processing"
    d1 = group_dir / "gnss_batch" / "example_1_relative_static_batch"
    r1 = _populate_rinex(d1 / "inputs" / "rinex", extra_station=True)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_relative_static_batch",
            "Batch Relative — Static processing of all rovers (ROVE, AUX1) from BASE",
            "Automatically pairs BASE against every rover in the session folder in static mode.",
            {
                "FOLDER": str(r1),
                "BASE_STATION": "BASE",
                "FRAME": 7,
                "PROFILE": 0,
                "OUTPUT_JSON": str(d1 / "outputs" / "batch_report.json"),
            },
            "Processes both baselines (BASE->AUX1, BASE->ROVE) and writes batch_report.json.",
        )
    )

    d2 = group_dir / "gnss_batch" / "example_2_relative_kinematic_batch"
    r2 = _populate_rinex(d2 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_relative_kinematic_batch",
            "Batch Relative — Kinematic processing in ITRF2020",
            "Runs batch relative kinematic processing for all rovers referenced to BASE.",
            {
                "FOLDER": str(r2),
                "BASE_STATION": "BASE",
                "FRAME": 2,
                "PROFILE": 1,
                "OUTPUT_JSON": str(d2 / "outputs" / "batch_report.json"),
            },
            "Completes batch kinematic run and summarizes fix ratios in batch_report.json.",
        )
    )

    d3 = group_dir / "gnss_batch" / "example_3_absolute_static_batch"
    r3 = _populate_rinex(d3 / "inputs" / "rinex")
    conf3 = _write_rtklib_conf(d3 / "inputs" / "batch_abs.conf", mode="single", elmask=15)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_absolute_static_batch",
            "Batch Absolute — Static positioning across all stations in folder",
            "Processes every station (BASE and ROVE) independently in Absolute — Static mode.",
            {
                "FOLDER": str(r3),
                "PROFILE": 2,
                "CONFIGURATION": str(conf3),
                "OUTPUT_JSON": str(d3 / "outputs" / "batch_report.json"),
            },
            "Runs standalone static positioning on every receiver in the folder.",
        )
    )

    # 9. geocomp:gnss_compare_configurations
    alg = "geocomp:gnss_compare_configurations"
    alg_title = "Compare configurations"
    menu_path = "GeoComp ▸ GNSS ▸ Compare configurations"
    d1 = group_dir / "gnss_compare_configurations" / "example_1_elevation_mask_sweep"
    r1 = _populate_rinex(d1 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_elevation_mask_sweep",
            "Elevation mask sensitivity sweep (10°, 15°, 20°, 25°)",
            "Runs RTKLIB across 4 elevation masks and compares coordinate repeatability and fix ratio.",
            {
                "FOLDER": str(r1),
                "MASKS": "10,15,20,25",
                "CONFIDENCE": 0.95,
                "OUTPUT_HTML": str(d1 / "outputs" / "comparison.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "comparison.csv"),
                "OUTPUT_JSON": str(d1 / "outputs" / "comparison.json"),
            },
            "Compares 4 elevation masks and outputs statistical significance test results.",
        )
    )

    d2 = group_dir / "gnss_compare_configurations" / "example_2_high_cutoff_comparison"
    r2 = _populate_rinex(d2 / "inputs" / "rinex")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_high_cutoff_comparison",
            "Extreme elevation mask comparison (15°, 30°, 40°) at 99% confidence",
            "Evaluates dilution of precision and coordinate shift under severe sky obstruction (30° and "
            "40°).",
            {
                "FOLDER": str(r2),
                "MASKS": "15,30,40",
                "CONFIDENCE": 0.99,
                "OUTPUT_HTML": str(d2 / "outputs" / "comparison.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "comparison.csv"),
                "OUTPUT_JSON": str(d2 / "outputs" / "comparison.json"),
            },
            "Quantifies coordinate shift between 15°, 30°, and 40° masks at 99% confidence.",
        )
    )

    d3 = group_dir / "gnss_compare_configurations" / "example_3_custom_config_files"
    r3 = _populate_rinex(d3 / "inputs" / "rinex")
    c_a = _write_rtklib_conf(d3 / "inputs" / "conf_mask12.conf", mode="kinematic", elmask=12)
    c_b = _write_rtklib_conf(d3 / "inputs" / "conf_mask22.conf", mode="kinematic", elmask=22)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_custom_config_files",
            "Direct comparison of two custom RTKLIB .conf files (conf_mask12 vs conf_mask22)",
            "Compares two user-supplied RTKLIB configuration files directly instead of a mask list.",
            {
                "FOLDER": str(r3),
                "CONFIGURATIONS": [str(c_a), str(c_b)],
                "CONFIDENCE": 0.95,
                "OUTPUT_HTML": str(d3 / "outputs" / "comparison.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "comparison.csv"),
                "OUTPUT_JSON": str(d3 / "outputs" / "comparison.json"),
            },
            "Compares the two named RTKLIB configurations side by side.",
        )
    )

    return specs


def _build_gravimetry_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    from geocomp.core.instruments import ProfileLibrary
    from geocomp.core.instruments.gravimeter import GravimeterProfile

    group_id = "04_gravimetry"
    group_title = "Gravimetry"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    lib = ProfileLibrary()
    lib.add_gravimeter(
        GravimeterProfile(
            id="CG-5 40123",
            sigma_reading=5.0e-8,
            applies_tide=True,
            source="Synthetic Scintrex CG-5 #40123",
        )
    )

    # 1. geocomp:gravimetry_preprocess
    alg = "geocomp:gravimetry_preprocess"
    alg_title = "Pre-processing (scale, tide, drift)"
    menu_path = "GeoComp ▸ Gravimetry ▸ Pre-processing (scale, tide, drift)"
    d1 = group_dir / "gravimetry_preprocess" / "example_1_cg5_instrument_tide_linear"
    cg1 = _copy_into(assets["cg5_txt"], d1 / "inputs" / "cg5_survey.txt")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_cg5_instrument_tide_linear",
            "Scintrex CG-5 pre-processing keeping instrument tide and linear drift (degree 1)",
            "Reduces CG-5 readings (BASE, S1, S2) with linear drift fit.",
            {
                "READINGS": str(cg1),
                "PRECISION_FLOOR": 0.005,
                "REPLACE_TIDE": False,
                "TIDE_MODEL": 0,
                "AMPLIFICATION": 1.16,
                "DRIFT_DEGREE": 1,
                "OUTPUT_READINGS": str(d1 / "outputs" / "reduced_readings.json"),
                "OUTPUT_CSV": str(d1 / "outputs" / "corrections.csv"),
                "OUTPUT_DRIFT": str(d1 / "outputs" / "drift.json"),
            },
            "Fits linear instrumental drift from repeated BASE occupations.",
        )
    )

    d2 = group_dir / "gravimetry_preprocess" / "example_2_longman_tide_replacement"
    cg2 = _copy_into(assets["cg5_txt"], d2 / "inputs" / "cg5_survey.txt")
    gp2 = _write_json(d2 / "inputs" / "gravimeter_profiles.json", lib.to_dict())
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_longman_tide_replacement",
            "Replace CG-5 tide with Longman (1959) solid-Earth tide + 0.25 m sensor height",
            "Replaces instrument tide with Longman (1959) and applies free-air height reduction (0.25 m).",
            {
                "READINGS": str(cg2),
                "PROFILES": str(gp2),
                "PRECISION_FLOOR": 0.005,
                "SENSOR_HEIGHT": 0.25,
                "SENSOR_HEIGHT_SIGMA": 0.002,
                "REPLACE_TIDE": True,
                "UTC_OFFSET": 0.0,
                "TIDE_MODEL": 0,
                "AMPLIFICATION": 1.16,
                "DRIFT_DEGREE": 1,
                "OUTPUT_READINGS": str(d2 / "outputs" / "reduced_readings.json"),
                "OUTPUT_CSV": str(d2 / "outputs" / "corrections.csv"),
                "OUTPUT_DRIFT": str(d2 / "outputs" / "drift.json"),
            },
            "Recomputes Longman luni-solar tide and applies free-air sensor-height correction.",
        )
    )

    d3 = group_dir / "gravimetry_preprocess" / "example_3_quadratic_drift_usgs_burris"
    cg3 = _copy_into(assets["cg5_txt"], d3 / "inputs" / "survey.txt")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_quadratic_drift_usgs_burris",
            "Quadratic drift polynomial (degree 2) with no external tide model",
            "Fits a 2nd-degree drift polynomial to capture nonlinear thermal drift.",
            {
                "READINGS": str(cg3),
                "PRECISION_FLOOR": 0.010,
                "REPLACE_TIDE": False,
                "TIDE_MODEL": 1,
                "DRIFT_DEGREE": 2,
                "OUTPUT_READINGS": str(d3 / "outputs" / "reduced_readings.json"),
                "OUTPUT_CSV": str(d3 / "outputs" / "corrections.csv"),
                "OUTPUT_DRIFT": str(d3 / "outputs" / "drift.json"),
            },
            "Estimates degree-2 drift coefficients and writes reduced_readings.json.",
        )
    )

    # 2. geocomp:gravimetry_network
    alg = "geocomp:gravimetry_network"
    alg_title = "Gravimetric network adjustment"
    menu_path = "GeoComp ▸ Gravimetry ▸ Gravimetric network adjustment"
    d1 = group_dir / "gravimetry_network" / "example_1_joint_drift_and_gravity"
    gr1 = _copy_into(assets["grav_reduced_json"], d1 / "inputs" / "reduced_readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_joint_drift_and_gravity",
            "Joint estimation of station gravity and linear drift holding station 1 = 978800.000 mGal",
            "Simultaneously adjusts gravity at stations 1, 2, 3 and drift polynomial with full correlation.",
            {
                "READINGS": str(gr1),
                "KNOWN_GRAVITY": "1=978800.000",
                "DRIFT_MODE": 0,
                "DRIFT_DEGREE": 1,
                "CORRELATED": True,
                "CONFIDENCE": 0.95,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "gravity.csv"),
            },
            "Adjusts station gravity values and drift parameters jointly.",
        )
    )

    d2 = group_dir / "gravimetry_network" / "example_2_pre_fitted_base_drift"
    gr2 = _copy_into(assets["grav_reduced_json"], d2 / "inputs" / "reduced_readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_pre_fitted_base_drift",
            "Drift fitted to base readings first (DRIFT_MODE=1) with uncorrelated differences",
            "Removes base-fitted drift prior to network adjustment and treats differences as uncorrelated.",
            {
                "READINGS": str(gr2),
                "KNOWN_GRAVITY": "1=978800.000±0.005",
                "DRIFT_MODE": 1,
                "DRIFT_DEGREE": 1,
                "CORRELATED": False,
                "CONFIDENCE": 0.99,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "gravity.csv"),
            },
            "Adjusts gravity values with weighted reference station 1 (±0.005 mGal).",
        )
    )

    d3 = group_dir / "gravimetry_network" / "example_3_high_confidence_snooping"
    gr3 = _copy_into(assets["grav_reduced_json"], d3 / "inputs" / "reduced_readings.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_high_confidence_snooping",
            "Correlated gravimetric adjustment with alpha=0.005 Baarda snooping",
            "Runs correlated difference adjustment with custom data-snooping significance alpha=0.005.",
            {
                "READINGS": str(gr3),
                "KNOWN_GRAVITY": "1=978800.000",
                "DRIFT_MODE": 0,
                "DRIFT_DEGREE": 1,
                "CORRELATED": True,
                "ALPHA": 0.005,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "gravity.csv"),
            },
            "Completes correlated gravimetric adjustment with Baarda data snooping.",
        )
    )

    return specs


def _build_integration_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    group_id = "05_integration"
    group_title = "Integration"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []
    held = assets["comb_held"]

    # 1. geocomp:integration_gnss_total_station
    alg = "geocomp:integration_gnss_total_station"
    alg_title = "GNSS and total station"
    menu_path = "GeoComp ▸ Integration ▸ GNSS and total station"
    d1 = group_dir / "integration_gnss_total_station" / "example_1_utm_grid_and_gnss"
    g1 = _copy_into(assets["comb_gnss_json"], d1 / "inputs" / "gnss.json")
    t1 = _copy_into(assets["comb_ts_grid_json"], d1 / "inputs" / "ts_grid.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_utm_grid_and_gnss",
            "Combine GNSS baselines and UTM 22S projected Total Station network in ITRF2020",
            "Projects UTM 22S total station starting coordinates into geocentric ITRF2020 and adjusts "
            "jointly with GNSS.",
            {
                "GNSS": str(g1),
                "TOTAL_STATION": str(t1),
                "FIXED_STATIONS": held,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "combined.json"),
            },
            "Produces unified 3D solution in ITRF2020 recovering true station coordinates to < 3 cm.",
        )
    )

    d2 = group_dir / "integration_gnss_total_station" / "example_2_variance_components_sirgas"
    g2 = _copy_into(assets["comb_gnss_json"], d2 / "inputs" / "gnss.json")
    t2 = _copy_into(assets["comb_ts_ecef_json"], d2 / "inputs" / "ts.json")
    _copy_into(assets["vel_csv"], d2 / "inputs" / "velocities.csv")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_variance_components_sirgas",
            "GNSS + Total Station in ITRF2014 with Helmert variance component estimation",
            "Estimates per-technique variance components between GNSS and Total Station in ITRF2014.",
            {
                "GNSS": str(g2),
                "TOTAL_STATION": str(t2),
                "FRAME": 1,
                "FIXED_STATIONS": held,
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "combined.json"),
            },
            "Estimates variance components for GNSS and Total Station groups.",
        )
    )

    d3 = group_dir / "integration_gnss_total_station" / "example_3_epoch_shift_with_velocities"
    g3 = _copy_into(assets["comb_gnss_json"], d3 / "inputs" / "gnss.json")
    t3 = _copy_into(assets["comb_ts_ecef_json"], d3 / "inputs" / "ts.json")
    v3 = _copy_into(assets["vel_csv"], d3 / "inputs" / "velocities.csv")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_epoch_shift_with_velocities",
            "GNSS + Total Station propagated to epoch 2025.0 using station velocities CSV",
            "Propagates coordinates to epoch 2025.0 via velocities.csv and adjusts in ITRF2014.",
            {
                "GNSS": str(g3),
                "TOTAL_STATION": str(t3),
                "FRAME": 1,
                "EPOCH": "2025.0",
                "VELOCITIES": str(v3),
                "FIXED_STATIONS": held,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "combined.json"),
            },
            "Adjusts velocity-propagated combined network at epoch 2025.0.",
        )
    )

    # 2. geocomp:integration_total_station_level
    alg = "geocomp:integration_total_station_level"
    alg_title = "Total station and level"
    menu_path = "GeoComp ▸ Integration ▸ Total station and level"
    d1 = group_dir / "integration_total_station_level" / "example_1_local_grid_combination"
    t1 = _copy_into(assets["local_ts_json"], d1 / "inputs" / "ts.json")
    l1 = _copy_into(assets["local_lev_json"], d1 / "inputs" / "levelling.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_local_grid_combination",
            "Combine projected Total Station and Spirit Levelling in the Total Station's CRS",
            "Combines terrestrial 3D total station and spirit levelling observations at epoch 2026.7.",
            {
                "TOTAL_STATION": str(t1),
                "LEVELLING": str(l1),
                "EPOCH": "2026.7",
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "combined.json"),
            },
            "Combines Total Station and Levelling in EPSG:31982 recovering heights to < 5 mm.",
        )
    )

    d2 = group_dir / "integration_total_station_level" / "example_2_with_variance_components"
    t2 = _copy_into(assets["local_ts_json"], d2 / "inputs" / "ts.json")
    l2 = _copy_into(assets["local_lev_json"], d2 / "inputs" / "levelling.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_with_variance_components",
            "Total Station + Spirit Levelling with Helmert variance component estimation",
            "Estimates per-technique variance factors between terrestrial zeniths and spirit levelling.",
            {
                "TOTAL_STATION": str(t2),
                "LEVELLING": str(l2),
                "EPOCH": "2026.7",
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "combined.json"),
            },
            "Balances terrestrial and levelling weights via VCE.",
        )
    )

    d3 = group_dir / "integration_total_station_level" / "example_3_high_confidence_99pct"
    t3 = _copy_into(assets["local_ts_json"], d3 / "inputs" / "ts.json")
    l3 = _copy_into(assets["local_lev_json"], d3 / "inputs" / "levelling.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_high_confidence_99pct",
            "Total Station + Spirit Levelling at 99% confidence level",
            "Runs combined terrestrial adjustment with 99% confidence intervals and ellipses.",
            {
                "TOTAL_STATION": str(t3),
                "LEVELLING": str(l3),
                "EPOCH": "2026.7",
                "CONFIDENCE": 0.99,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "combined.json"),
            },
            "Outputs 99% confidence combined terrestrial solution.",
        )
    )

    # 3. geocomp:integration_gnss_level
    alg = "geocomp:integration_gnss_level"
    alg_title = "GNSS and level"
    menu_path = "GeoComp ▸ Integration ▸ GNSS and level"
    d1 = group_dir / "integration_gnss_level" / "example_1_planar_geoid_coupling"
    g1 = _copy_into(assets["comb_gnss_json"], d1 / "inputs" / "gnss.json")
    l1 = _copy_into(assets["comb_lev_bm_json"], d1 / "inputs" / "levelling.json")
    geo1 = _copy_into(assets["geoid_asc"], d1 / "inputs" / "curitiba_planar.asc")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_planar_geoid_coupling",
            "GNSS + Spirit Levelling coupled through ESRI ASCII geoid grid (h - H = N)",
            "Couples ellipsoidal GNSS heights and orthometric levelling differences through "
            "curitiba_planar.asc.",
            {
                "GNSS": str(g1),
                "LEVELLING": str(l1),
                "GEOID": str(geo1),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": held,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "combined.json"),
            },
            "Computes geoid residuals and adjusts GNSS + Levelling jointly.",
        )
    )

    d2 = group_dir / "integration_gnss_level" / "example_2_variance_components"
    g2 = _copy_into(assets["comb_gnss_json"], d2 / "inputs" / "gnss.json")
    l2 = _copy_into(assets["comb_lev_json"], d2 / "inputs" / "levelling.json")
    geo2 = _copy_into(assets["geoid_asc"], d2 / "inputs" / "curitiba_planar.asc")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_variance_components",
            "GNSS + Spirit Levelling with Helmert variance component estimation",
            "Estimates variance components for GNSS baselines and spirit levelling lines.",
            {
                "GNSS": str(g2),
                "LEVELLING": str(l2),
                "GEOID": str(geo2),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": held,
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "combined.json"),
            },
            "Converges variance components between GNSS and spirit levelling.",
        )
    )

    d3 = group_dir / "integration_gnss_level" / "example_3_sirgas2000_frame"
    g3 = _copy_into(assets["comb_gnss_json"], d3 / "inputs" / "gnss.json")
    l3 = _copy_into(assets["comb_lev_json"], d3 / "inputs" / "levelling.json")
    geo3 = _copy_into(assets["geoid_asc"], d3 / "inputs" / "curitiba_planar.asc")
    _copy_into(assets["vel_csv"], d3 / "inputs" / "velocities.csv")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_sirgas2000_frame",
            "GNSS + Spirit Levelling combined in ITRF2008 (FRAME=2)",
            "Transforms GNSS baselines to ITRF2008 and adjusts with spirit levelling.",
            {
                "GNSS": str(g3),
                "LEVELLING": str(l3),
                "FRAME": 2,
                "GEOID": str(geo3),
                "GEOID_SIGMA": 0.05,
                "FIXED_STATIONS": held,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "combined.json"),
            },
            "Produces combined GNSS + Levelling solution in ITRF2008.",
        )
    )

    # 4. geocomp:integration_multiple
    alg = "geocomp:integration_multiple"
    alg_title = "Multiple techniques"
    menu_path = "GeoComp ▸ Integration ▸ Multiple techniques"
    d1 = group_dir / "integration_multiple" / "example_1_gnss_ts_levelling_vce"
    g1 = _copy_into(assets["comb_gnss_json"], d1 / "inputs" / "gnss.json")
    t1 = _copy_into(assets["comb_ts_ecef_json"], d1 / "inputs" / "ts.json")
    l1 = _copy_into(assets["comb_lev_json"], d1 / "inputs" / "levelling.json")
    geo1 = _copy_into(assets["geoid_asc"], d1 / "inputs" / "curitiba_planar.asc")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_gnss_ts_levelling_vce",
            "Three-technique combination (GNSS + Total Station + Levelling) with VCE and geoid",
            "Simultaneously adjusts all 3 geometric techniques on the Curitiba network with variance "
            "components.",
            {
                "GNSS": str(g1),
                "TOTAL_STATION": str(t1),
                "LEVELLING": str(l1),
                "GEOID": str(geo1),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": held,
                "VARIANCE_COMPONENTS": True,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d1 / "outputs" / "combined.json"),
            },
            "Estimates variance components across gnss, total_station, and levelling.",
        )
    )

    d2 = group_dir / "integration_multiple" / "example_2_sirgas2000_no_vce"
    g2 = _copy_into(assets["comb_gnss_json"], d2 / "inputs" / "gnss.json")
    t2 = _copy_into(assets["comb_ts_grid_json"], d2 / "inputs" / "ts_grid.json")
    l2 = _copy_into(assets["comb_lev_json"], d2 / "inputs" / "levelling.json")
    geo2 = _copy_into(assets["geoid_asc"], d2 / "inputs" / "curitiba_planar.asc")
    _copy_into(assets["vel_csv"], d2 / "inputs" / "velocities.csv")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_sirgas2000_no_vce",
            "Three-technique combination in ITRF2014 with projected UTM Total Station input",
            "Combines GNSS, UTM 22S Total Station, and Spirit Levelling in ITRF2014.",
            {
                "GNSS": str(g2),
                "TOTAL_STATION": str(t2),
                "LEVELLING": str(l2),
                "FRAME": 1,
                "GEOID": str(geo2),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": held,
                "VARIANCE_COMPONENTS": False,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d2 / "outputs" / "combined.json"),
            },
            "Combines all 3 techniques in ITRF2014.",
        )
    )

    d3 = group_dir / "integration_multiple" / "example_3_all_four_techniques_with_gravity"
    g3 = _copy_into(assets["comb_gnss_json"], d3 / "inputs" / "gnss.json")
    t3 = _copy_into(assets["comb_ts_ecef_json"], d3 / "inputs" / "ts.json")
    l3 = _copy_into(assets["comb_lev_json"], d3 / "inputs" / "levelling.json")
    gr3 = _copy_into(assets["grav_reduced_json"], d3 / "inputs" / "gravity_reduced.json")
    geo3 = _copy_into(assets["geoid_asc"], d3 / "inputs" / "curitiba_planar.asc")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_all_four_techniques_with_gravity",
            "Four-technique integration (GNSS + Total Station + Levelling + Gravimetry)",
            "Combines 3D geometric techniques alongside CG-5 gravimetry readings.",
            {
                "GNSS": str(g3),
                "TOTAL_STATION": str(t3),
                "LEVELLING": str(l3),
                "READINGS": str(gr3),
                "KNOWN_GRAVITY": "1=978800.000",
                "GEOID": str(geo3),
                "GEOID_SIGMA": 0.03,
                "FIXED_STATIONS": held,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_NETWORK": str(d3 / "outputs" / "combined.json"),
                "OUTPUT_GRAVITY": str(d3 / "outputs" / "gravity_solution.json"),
            },
            "Produces both geometric solution.json and gravimetric gravity_solution.json.",
        )
    )

    return specs


def _build_analysis_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    group_id = "06_analysis"
    group_title = "Analysis"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    # 1. geocomp:analysis_network_inspect
    alg = "geocomp:analysis_network_inspect"
    alg_title = "Inspect network"
    menu_path = "GeoComp ▸ Analysis ▸ Inspect network"
    d1 = group_dir / "analysis_network_inspect" / "example_1_sound_2d_trilateration"
    n1 = _copy_into(assets["trilat_net_json"], d1 / "inputs" / "trilateration.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_sound_2d_trilateration",
            "Topological and rank inspection of a sound 2D trilateration network",
            "Verifies connectivity, datum constraints, and degrees of freedom of RD-03 trilateration "
            "network.",
            {
                "NETWORK": str(n1),
                "FRAME": 0,
                "FAIL_ON_BLOCKING": True,
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "findings.csv"),
            },
            "Reports CAN_ADJUST=True, BLOCKING_COUNT=0, COMPONENT_COUNT=1.",
        )
    )

    d2 = group_dir / "analysis_network_inspect" / "example_2_1d_levelling_loop"
    n2 = _copy_into(assets["lev_net_1d_json"], d2 / "inputs" / "levelling_loop.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_1d_levelling_loop",
            "Inspection of a 1D spirit-levelling network (FRAME=1)",
            "Checks vertical benchmark sufficiency and graph connectivity in 1D height mode.",
            {
                "NETWORK": str(n2),
                "FRAME": 1,
                "FAIL_ON_BLOCKING": True,
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "findings.csv"),
            },
            "Confirms 1D height network is connected and ready for adjustment.",
        )
    )

    d3 = group_dir / "analysis_network_inspect" / "example_3_3d_geodetic_network"
    n3 = _copy_into(assets["dna_net_json"], d3 / "inputs" / "geodetic_3d.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_3d_geodetic_network",
            "Inspection of a 3D geodetic network (FRAME=2)",
            "Audits 3D station connectivity and observation redundancy.",
            {
                "NETWORK": str(n3),
                "FRAME": 2,
                "FAIL_ON_BLOCKING": False,
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "findings.csv"),
            },
            "Writes 3D topology inspection report and findings table.",
        )
    )

    # 2. geocomp:analysis_network_preanalysis
    alg = "geocomp:analysis_network_preanalysis"
    alg_title = "Pre-analyse network design"
    menu_path = "GeoComp ▸ Analysis ▸ Pre-analyse network design"
    d1 = group_dir / "analysis_network_preanalysis" / "example_1_constrained_2d_design"
    n1 = _copy_into(assets["trilat_net_json"], d1 / "inputs" / "planned_network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_constrained_2d_design",
            "Pre-analysis of 2D trilateration design under constrained datum",
            "Computes expected station precisions, redundancy numbers, and MDBs before field observation.",
            {
                "NETWORK": str(n1),
                "FRAME": 0,
                "DATUM": 0,
                "TOLERANCE": 0.050,
                "CONFIDENCE": 0.95,
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d1 / "outputs" / "expected_precision.csv"),
            },
            "All planned stations meet the 50 mm positional uncertainty tolerance.",
        )
    )

    d2 = group_dir / "analysis_network_preanalysis" / "example_2_inner_constraint_free"
    n2 = _copy_into(assets["trilat_net_json"], d2 / "inputs" / "planned_network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_inner_constraint_free",
            "Free-network (inner constraint) pre-analysis at 99% confidence",
            "Evaluates internal geometry precision independent of control datum errors.",
            {
                "NETWORK": str(n2),
                "FRAME": 0,
                "DATUM": 1,
                "CONFIDENCE": 0.99,
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d2 / "outputs" / "expected_precision.csv"),
            },
            "Outputs 99% free-network error ellipses and minimal detectable biases.",
        )
    )

    d3 = group_dir / "analysis_network_preanalysis" / "example_3_1d_levelling_design"
    n3 = _copy_into(assets["lev_net_1d_json"], d3 / "inputs" / "planned_levelling.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_1d_levelling_design",
            "Pre-analysis of a 1D spirit-levelling loop design (FRAME=1)",
            "Computes expected vertical standard deviations and observation redundancy numbers.",
            {
                "NETWORK": str(n3),
                "FRAME": 1,
                "DATUM": 0,
                "TOLERANCE": 0.005,
                "CONFIDENCE": 0.95,
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_CSV": str(d3 / "outputs" / "expected_precision.csv"),
            },
            "Computes expected vertical precisions for all benchmarks in the loop.",
        )
    )

    # 3. geocomp:analysis_network_adjust
    alg = "geocomp:analysis_network_adjust"
    alg_title = "Adjust network"
    menu_path = "GeoComp ▸ Analysis ▸ Adjust network"
    d1 = group_dir / "analysis_network_adjust" / "example_1_2d_constrained_trilateration"
    n1 = _copy_into(assets["trilat_net_json"], d1 / "inputs" / "trilateration.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_2d_constrained_trilateration",
            "2D Gauss-Markov least-squares adjustment of trilateration network",
            "Adjusts 2D network with constrained datum and Baarda data snooping.",
            {
                "NETWORK": str(n1),
                "FRAME": 0,
                "DATUM": 0,
                "CONFIDENCE": 0.95,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "report.html"),
                "OUTPUT_STATIONS_CSV": str(d1 / "outputs" / "stations.csv"),
                "OUTPUT_RESIDUALS_CSV": str(d1 / "outputs" / "residuals.csv"),
            },
            "Converges least-squares solution and writes solution.json, stations.csv, and residuals.csv.",
        )
    )

    d2 = group_dir / "analysis_network_adjust" / "example_2_2d_inner_constraint"
    n2 = _copy_into(assets["mon_roles_json"], d2 / "inputs" / "free_2d_network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_2d_inner_constraint",
            "Free 2D network adjustment (inner constraint / trace minimum)",
            "Adjusts 2D distance network under inner constraints (DATUM=1).",
            {
                "NETWORK": str(n2),
                "FRAME": 0,
                "DATUM": 1,
                "CONFIDENCE": 0.95,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "report.html"),
                "OUTPUT_STATIONS_CSV": str(d2 / "outputs" / "stations.csv"),
                "OUTPUT_RESIDUALS_CSV": str(d2 / "outputs" / "residuals.csv"),
            },
            "Computes minimum-trace free network solution.",
        )
    )

    d3 = group_dir / "analysis_network_adjust" / "example_3_1d_levelling_adjustment"
    n3 = _copy_into(assets["lev_net_1d_json"], d3 / "inputs" / "levelling_loop.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_1d_levelling_adjustment",
            "1D height network adjustment (FRAME=1) at 99% confidence",
            "Adjusts 1D spirit-levelling network document through the general network adjustment engine.",
            {
                "NETWORK": str(n3),
                "FRAME": 1,
                "DATUM": 0,
                "CONFIDENCE": 0.99,
                "OUTPUT_SOLUTION": str(d3 / "outputs" / "solution.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "report.html"),
                "OUTPUT_STATIONS_CSV": str(d3 / "outputs" / "stations.csv"),
                "OUTPUT_RESIDUALS_CSV": str(d3 / "outputs" / "residuals.csv"),
            },
            "Adjusts 1D benchmark heights and writes residual diagnostics.",
        )
    )

    # 4. geocomp:analysis_dynadjust_adjust
    alg = "geocomp:analysis_dynadjust_adjust"
    alg_title = "Adjust network (DynAdjust)"
    menu_path = "GeoComp ▸ Analysis ▸ Adjust network (DynAdjust)"
    d1 = group_dir / "analysis_dynadjust_adjust" / "example_1_full_pipeline_from_network"
    n1 = _copy_into(assets["dna_net_json"], d1 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_full_pipeline_from_network",
            "Full DynAdjust pipeline (import -> reftran -> adjust) from Network JSON",
            "Writes DynaML (.stn.xml / .msr.xml), runs DynAdjust pipeline, and parses adjusted coordinates + "
            "SINEX covariances.",
            {
                "NETWORK": str(n1),
                "FRAME": "GDA2020",
                "EPOCH": 2020.0,
                "ENGINE_DIRECTORY": str(assets["dynadjust_dir"]),
                "KEEP_WORKING_FILES": True,
                "OUTPUT_SOLUTION": str(d1 / "outputs" / "solution.json"),
                "OUTPUT_WORK_DIR": str(d1 / "outputs" / "work"),
            },
            "Runs DynAdjust pipeline and writes solution.json + working files.",
        )
    )

    d2 = group_dir / "analysis_dynadjust_adjust" / "example_2_from_geopackage_store_with_geoid"
    st2 = _copy_into(assets["store_gpkg"], d2 / "inputs" / "project_store.gpkg")
    gsb2 = _copy_into(assets["ntv2_gsb"], d2 / "inputs" / "synthetic_geoid.gsb")
    cfg2 = _write_json(
        d2 / "inputs" / "dynadjust_options.json",
        {"dnaadjust": ["--free-stn-sd", "10"]},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_from_geopackage_store_with_geoid",
            "DynAdjust adjustment reading network directly from a GeoPackage store + NTv2 geoid + custom "
            "JSON options",
            "Reads network 'sample' from project_store.gpkg, includes dnageoid stage with "
            "synthetic_geoid.gsb, and passes custom CLI flags.",
            {
                "STORE": str(st2),
                "STORED_NETWORK": "sample",
                "FRAME": "GDA2020",
                "EPOCH": 2020.0,
                "GEOID_GRID": str(gsb2),
                "CONFIGURATION": str(cfg2),
                "ENGINE_DIRECTORY": str(assets["dynadjust_dir"]),
                "KEEP_WORKING_FILES": True,
                "OUTPUT_SOLUTION": str(d2 / "outputs" / "solution.json"),
                "OUTPUT_WORK_DIR": str(d2 / "outputs" / "work"),
            },
            "Reads network from GeoPackage store, runs dnageoid stage, and writes solution.json.",
        )
    )

    d3 = group_dir / "analysis_dynadjust_adjust" / "example_3_stop_before_running_prepare_only"
    n3 = _copy_into(assets["dna_net_json"], d3 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_stop_before_running_prepare_only",
            "Prepare DynAdjust DynaML files and stop before running (STOP_BEFORE_RUNNING=True)",
            "Generates geocomp.stn.xml, geocomp.msr.xml, and geocomp-dynadjust.json for manual inspection "
            "without invoking binaries.",
            {
                "NETWORK": str(n3),
                "FRAME": "GDA2020",
                "EPOCH": 2020.0,
                "STOP_BEFORE_RUNNING": True,
                "OUTPUT_WORK_DIR": str(d3 / "outputs" / "prepared_job"),
            },
            "Writes DynaML input files and manifest into prepared_job/ without running DynAdjust.",
        )
    )

    # 5. geocomp:analysis_dynadjust_run_prepared
    alg = "geocomp:analysis_dynadjust_run_prepared"
    alg_title = "Run a prepared DynAdjust job"
    menu_path = "GeoComp ▸ Analysis ▸ Run a prepared DynAdjust job"
    for idx, (slug, title, desc, exag) in enumerate(
        [
            (
                "example_1_nominal_prepared_job",
                "Execute a prepared DynAdjust folder and import SINEX solution",
                "Runs a prepared DynaML folder containing geocomp.stn.xml, geocomp.msr.xml, and "
                "geocomp-dynadjust.json.",
                0.0,
            ),
            (
                "example_2_edited_msr_prepared_job",
                "Execute a prepared job after hand-editing measurement weights in .msr.xml",
                "Demonstrates the 2-step workflow: edit .msr.xml in a prepared folder, then run DynAdjust.",
                100.0,
            ),
            (
                "example_3_custom_timeout_and_exaggeration",
                "Execute prepared DynAdjust job with custom stage timeout and 500x ellipse exaggeration",
                "Runs prepared job with 600 s stage timeout and 500x error ellipse scaling.",
                500.0,
            ),
        ],
        start=1,
    ):
        d = group_dir / "analysis_dynadjust_run_prepared" / slug
        pdir = _copy_into(assets["prepared_dir"], d / "inputs" / "prepared_job")
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {
                    "PREPARED": str(pdir),
                    "ENGINE_DIRECTORY": str(assets["dynadjust_dir"]),
                    "TIMEOUT": 600.0,
                    "EXAGGERATION": exag,
                    "OUTPUT_SOLUTION": str(d / "outputs" / "solution.json"),
                },
                "Executes prepared DynAdjust job and writes solution.json.",
            )
        )

    # 6. geocomp:analysis_dynadjust_compare
    alg = "geocomp:analysis_dynadjust_compare"
    alg_title = "Compare two solutions"
    menu_path = "GeoComp ▸ Analysis ▸ Compare two solutions"
    d1 = group_dir / "analysis_dynadjust_compare" / "example_1_identical_solutions"
    s1_a = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "reference_solution.json")
    s1_b = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "other_solution.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_identical_solutions",
            "Compare two identical adjustment solutions (0.1 mm coordinate tolerance)",
            "Verifies zero coordinate and variance factor differences between two identical solutions.",
            {
                "REFERENCE": str(s1_a),
                "OTHER": str(s1_b),
                "COORDINATE_TOLERANCE": 0.0001,
                "VARIANCE_TOLERANCE": 0.01,
                "OUTPUT_REPORT": str(d1 / "outputs" / "comparison_report.html"),
                "OUTPUT_JSON": str(d1 / "outputs" / "differences.json"),
            },
            "Confirms 0.0 mm max coordinate discrepancy and passes both tolerances.",
        )
    )

    d2 = group_dir / "analysis_dynadjust_compare" / "example_2_relaxed_tolerance_agreement"
    s2_a = _copy_into(assets["mon_sol1_json"], d2 / "inputs" / "reference_solution.json")
    s2_b = _copy_into(assets["mon_sol2_json"], d2 / "inputs" / "other_solution.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_relaxed_tolerance_agreement",
            "Compare two epoch solutions under a 20 mm coordinate tolerance",
            "Compares Epoch 1 and Epoch 2 (10 mm motion on O2) against a 20 mm tolerance.",
            {
                "REFERENCE": str(s2_a),
                "OTHER": str(s2_b),
                "COORDINATE_TOLERANCE": 0.020,
                "VARIANCE_TOLERANCE": 0.50,
                "OUTPUT_REPORT": str(d2 / "outputs" / "comparison_report.html"),
                "OUTPUT_JSON": str(d2 / "outputs" / "differences.json"),
            },
            "Reports ~10 mm max station difference within the 20 mm tolerance.",
        )
    )

    d3 = group_dir / "analysis_dynadjust_compare" / "example_3_divergent_solutions_flagged"
    s3_a = _copy_into(assets["mon_sol1_json"], d3 / "inputs" / "epoch1_solution.json")
    s3_b = _copy_into(assets["mon_sol3_json"], d3 / "inputs" / "epoch3_solution.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_divergent_solutions_flagged",
            "Compare two solutions with 20 mm station shift exceeding 0.1 mm tolerance",
            "Compares Epoch 1 against Epoch 3 (where O2 shifted by 20 mm) and flags tolerance exceedance.",
            {
                "REFERENCE": str(s3_a),
                "OTHER": str(s3_b),
                "COORDINATE_TOLERANCE": 0.0001,
                "VARIANCE_TOLERANCE": 0.005,
                "OUTPUT_REPORT": str(d3 / "outputs" / "comparison_report.html"),
                "OUTPUT_JSON": str(d3 / "outputs" / "differences.json"),
            },
            "Flags station O2 as exceeding coordinate tolerance in differences.json.",
        )
    )

    # 7. geocomp:monitoring_compare_epochs
    alg = "geocomp:monitoring_compare_epochs"
    alg_title = "Compare two epochs"
    menu_path = "GeoComp ▸ Analysis ▸ Compare two epochs"
    d1 = group_dir / "monitoring_compare_epochs" / "example_1_dam_deformation_from_network_roles"
    e1 = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "epoch_1.json")
    e2 = _copy_into(assets["mon_sol2_json"], d1 / "inputs" / "epoch_2.json")
    mn1 = _copy_into(assets["mon_roles_json"], d1 / "inputs" / "monitoring_network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_dam_deformation_from_network_roles",
            "Two-epoch dam deformation analysis (Epoch 1 vs Epoch 2) using network monitoring roles",
            "Tests congruence of reference pillars (R1..R4) and detects 10 mm displacement on crest O2.",
            {
                "FIRST": str(e1),
                "SECOND": str(e2),
                "NETWORK": str(mn1),
                "DATUM": 0,
                "CONFIDENCE": 0.95,
                "STRAIN": True,
                "OUTPUT_ANALYSIS": str(d1 / "outputs" / "analysis.json"),
                "OUTPUT_HTML": str(d1 / "outputs" / "monitoring_report.html"),
            },
            "Confirms reference block stability and flags statistically significant motion at O2.",
        )
    )

    d2 = group_dir / "monitoring_compare_epochs" / "example_2_explicit_roles_and_alert_thresholds"
    e1_2 = _copy_into(assets["mon_sol1_json"], d2 / "inputs" / "epoch_1.json")
    e3_2 = _copy_into(assets["mon_sol3_json"], d2 / "inputs" / "epoch_3.json")
    from tests.monitoring_network import tutorial_thresholds

    th2 = _write_text(d2 / "inputs" / "alert_thresholds.csv", tutorial_thresholds())
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_explicit_roles_and_alert_thresholds",
            "Deformation analysis (Epoch 1 vs Epoch 3) with explicit station lists and alert thresholds CSV",
            "Evaluates 20 mm cumulative displacement at O2 against alert_thresholds.csv.",
            {
                "FIRST": str(e1_2),
                "SECOND": str(e3_2),
                "REFERENCE": assets["mon_ref"],
                "OBJECTS": assets["mon_obj"],
                "DATUM": 2,
                "CONFIDENCE": 0.99,
                "STRAIN": True,
                "THRESHOLDS": str(th2),
                "OUTPUT_ANALYSIS": str(d2 / "outputs" / "analysis.json"),
                "OUTPUT_HTML": str(d2 / "outputs" / "monitoring_report.html"),
            },
            "Flags threshold exceedance on O2 and writes analysis.json + HTML report.",
        )
    )

    d3 = group_dir / "monitoring_compare_epochs" / "example_3_similarity_datum_no_strain"
    e1_3 = _copy_into(assets["mon_sol1_json"], d3 / "inputs" / "epoch_1.json")
    e2_3 = _copy_into(assets["mon_sol2_json"], d3 / "inputs" / "epoch_2.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_similarity_datum_no_strain",
            "S-transformation with similarity datum (translation, rotation, scale) and STRAIN=False",
            "Uses full 4-parameter 2D similarity datum over R1..R4 without rigid-body/strain decomposition.",
            {
                "FIRST": str(e1_3),
                "SECOND": str(e2_3),
                "REFERENCE": assets["mon_ref"],
                "OBJECTS": assets["mon_obj"],
                "DATUM": 3,
                "CONFIDENCE": 0.95,
                "STRAIN": False,
                "OUTPUT_ANALYSIS": str(d3 / "outputs" / "analysis.json"),
                "OUTPUT_HTML": str(d3 / "outputs" / "monitoring_report.html"),
            },
            "Computes displacement vectors under similarity S-transformation.",
        )
    )

    # 8. geocomp:monitoring_time_series
    alg = "geocomp:monitoring_time_series"
    alg_title = "Time series and velocities"
    menu_path = "GeoComp ▸ Analysis ▸ Time series and velocities"
    d1 = group_dir / "monitoring_time_series" / "example_1_three_epoch_velocities"
    s_1 = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "epoch_1.json")
    s_2 = _copy_into(assets["mon_sol2_json"], d1 / "inputs" / "epoch_2.json")
    s_3 = _copy_into(assets["mon_sol3_json"], d1 / "inputs" / "epoch_3.json")
    mn1 = _copy_into(assets["mon_roles_json"], d1 / "inputs" / "monitoring_network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_three_epoch_velocities",
            "Three-epoch time series recovering linear crest velocity on O2",
            "Fits weighted linear regression across 3 epochs to estimate station velocities.",
            {
                "SOLUTIONS": [str(s_1), str(s_2), str(s_3)],
                "NETWORK": str(mn1),
                "DATUM": 0,
                "CONFIDENCE": 0.95,
                "OUTPUT_SERIES": str(d1 / "outputs" / "series.json"),
                "OUTPUT_CSV": str(d1 / "outputs" / "series.csv"),
                "OUTPUT_HTML": str(d1 / "outputs" / "monitoring_report.html"),
            },
            "Recovers O2 velocity rate and near-zero reference velocities.",
        )
    )

    d2 = group_dir / "monitoring_time_series" / "example_2_explicit_reference_and_thresholds"
    s2_1 = _copy_into(assets["mon_sol1_json"], d2 / "inputs" / "epoch_1.json")
    s2_2 = _copy_into(assets["mon_sol2_json"], d2 / "inputs" / "epoch_2.json")
    s2_3 = _copy_into(assets["mon_sol3_json"], d2 / "inputs" / "epoch_3.json")
    th2 = _write_text(d2 / "inputs" / "velocity_thresholds.csv", tutorial_thresholds())
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_explicit_reference_and_thresholds",
            "Time series with explicit reference list (R1..R4), 99% confidence, and alert thresholds",
            "Computes time series using explicit reference list at 99% confidence and evaluates alert "
            "thresholds.",
            {
                "SOLUTIONS": [str(s2_1), str(s2_2), str(s2_3)],
                "REFERENCE": assets["mon_ref"],
                "DATUM": 0,
                "CONFIDENCE": 0.99,
                "THRESHOLDS": str(th2),
                "OUTPUT_SERIES": str(d2 / "outputs" / "series.json"),
                "OUTPUT_CSV": str(d2 / "outputs" / "series.csv"),
                "OUTPUT_HTML": str(d2 / "outputs" / "monitoring_report.html"),
            },
            "Outputs multi-epoch offsets and flags threshold exceedances.",
        )
    )

    d3 = group_dir / "monitoring_time_series" / "example_3_two_epoch_minimal_series"
    s3_1 = _copy_into(assets["mon_sol1_json"], d3 / "inputs" / "epoch_1.json")
    s3_2 = _copy_into(assets["mon_sol3_json"], d3 / "inputs" / "epoch_3.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_two_epoch_minimal_series",
            "Two-epoch minimal time series (Epoch 1 and Epoch 3) with similarity datum",
            "Computes velocity rates from two epochs under similarity datum.",
            {
                "SOLUTIONS": [str(s3_1), str(s3_2)],
                "REFERENCE": assets["mon_ref"],
                "DATUM": 3,
                "CONFIDENCE": 0.95,
                "EXAGGERATION": 500.0,
                "OUTPUT_SERIES": str(d3 / "outputs" / "series.json"),
                "OUTPUT_CSV": str(d3 / "outputs" / "series.csv"),
                "OUTPUT_HTML": str(d3 / "outputs" / "monitoring_report.html"),
            },
            "Computes 2-epoch rates and writes series.json + HTML report.",
        )
    )

    # 9. geocomp:monitoring_report
    alg = "geocomp:monitoring_report"
    alg_title = "Monitoring report"
    menu_path = "GeoComp ▸ Analysis ▸ Monitoring report"
    d1 = group_dir / "monitoring_report" / "example_1_from_two_epoch_analysis"
    an1 = _copy_into(assets["mon_analysis_json"], d1 / "inputs" / "analysis.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_from_two_epoch_analysis",
            "Standalone HTML monitoring report from two-epoch congruence analysis",
            "Renders two-epoch deformation tables, stability tests, and SVG vector map.",
            {
                "ANALYSIS": str(an1),
                "EXAGGERATION": 0.0,
                "OUTPUT_HTML": str(d1 / "outputs" / "monitoring_report.html"),
            },
            "Writes self-contained HTML report with SVG displacement vectors.",
        )
    )

    d2 = group_dir / "monitoring_report" / "example_2_combined_analysis_and_series"
    an2 = _copy_into(assets["mon_analysis_json"], d2 / "inputs" / "analysis.json")
    sr2 = _copy_into(assets["mon_series_json"], d2 / "inputs" / "series.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_combined_analysis_and_series",
            "Comprehensive monitoring report combining two-epoch analysis and multi-epoch time series",
            "Includes both pairwise epoch comparison and multi-year velocity trend charts in one report.",
            {
                "ANALYSIS": str(an2),
                "SERIES": str(sr2),
                "EXAGGERATION": 1000.0,
                "OUTPUT_HTML": str(d2 / "outputs" / "monitoring_report.html"),
            },
            "Renders combined pairwise + time-series monitoring report with 1000x map exaggeration.",
        )
    )

    d3 = group_dir / "monitoring_report" / "example_3_from_series_only"
    sr3 = _copy_into(assets["mon_series_json"], d3 / "inputs" / "series.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_from_series_only",
            "Time-series monitoring report rendered from series.json alone",
            "Renders velocity tables and offset history from series.json with 500x exaggeration.",
            {
                "SERIES": str(sr3),
                "EXAGGERATION": 500.0,
                "OUTPUT_HTML": str(d3 / "outputs" / "monitoring_report.html"),
            },
            "Renders HTML monitoring report from series document.",
        )
    )

    return specs


def _build_project_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    from geocomp.core.models import Network, Project, Solution
    from geocomp.engines.base import run_process
    from geocomp.io.store import open_store

    group_id = "07_project"
    group_title = "Project"
    group_dir = base_dir / group_id
    specs: list[ExampleSpec] = []

    # 1. geocomp:project_export
    alg = "geocomp:project_export"
    alg_title = "Export solution tables"
    menu_path = "GeoComp ▸ Project ▸ Export solution tables"
    d1 = group_dir / "project_export" / "example_1_csv_tables_with_network"
    s1 = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "solution.json")
    n1 = _copy_into(assets["mon_roles_json"], d1 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_csv_tables_with_network",
            "Export adjusted stations, residuals, and covariances as a folder of CSV files",
            "Writes stations.csv, observations.csv, and covariance.csv from solution + network.",
            {
                "SOLUTION": str(s1),
                "NETWORK": str(n1),
                "FORMAT": 0,
                "OUTPUT_FOLDER": str(d1 / "outputs" / "csv_tables"),
            },
            "Creates CSV tables in csv_tables/.",
        )
    )

    d2 = group_dir / "project_export" / "example_2_xlsx_workbook"
    s2 = _copy_into(assets["mon_sol1_json"], d2 / "inputs" / "solution.json")
    n2 = _copy_into(assets["mon_roles_json"], d2 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_xlsx_workbook",
            "Export solution tables into a multi-sheet Excel workbook (.xlsx)",
            "Packages Stations, Observations, and Covariance sheets into a single .xlsx spreadsheet.",
            {
                "SOLUTION": str(s2),
                "NETWORK": str(n2),
                "FORMAT": 1,
                "OUTPUT_WORKBOOK": str(d2 / "outputs" / "solution_tables.xlsx"),
            },
            "Writes multi-tab solution_tables.xlsx workbook.",
        )
    )

    d3 = group_dir / "project_export" / "example_3_solution_only_csv"
    s3 = _copy_into(assets["mon_sol2_json"], d3 / "inputs" / "solution_epoch2.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_solution_only_csv",
            "Export CSV tables from a standalone Solution JSON without a Network document",
            "Exports adjusted coordinates and residuals directly from solution_epoch2.json.",
            {
                "SOLUTION": str(s3),
                "FORMAT": 0,
                "OUTPUT_FOLDER": str(d3 / "outputs" / "csv_tables"),
            },
            "Exports solution tables without requiring the input network document.",
        )
    )

    # 2. geocomp:project_report
    alg = "geocomp:project_report"
    alg_title = "Adjustment report"
    menu_path = "GeoComp ▸ Project ▸ Adjustment report"
    d1 = group_dir / "project_report" / "example_1_full_adjustment_report"
    s1 = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "solution.json")
    n1 = _copy_into(assets["mon_roles_json"], d1 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_full_adjustment_report",
            "Full HTML adjustment report with network summary, chi-square test, and SVG network plot",
            "Generates a complete adjustment report from solution.json + network.json.",
            {
                "SOLUTION": str(s1),
                "NETWORK": str(n1),
                "OUTPUT_HTML": str(d1 / "outputs" / "adjustment_report.html"),
            },
            "Writes self-contained HTML adjustment report with embedded SVG graphics.",
        )
    )

    d2 = group_dir / "project_report" / "example_2_solution_only_report"
    s2 = _copy_into(assets["mon_sol2_json"], d2 / "inputs" / "solution.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_solution_only_report",
            "Adjustment report generated from Solution JSON alone",
            "Produces coordinate, precision, and residual tables when only solution.json is available.",
            {
                "SOLUTION": str(s2),
                "OUTPUT_HTML": str(d2 / "outputs" / "adjustment_report.html"),
            },
            "Renders HTML adjustment report from standalone solution document.",
        )
    )

    d3 = group_dir / "project_report" / "example_3_trilateration_solution_report"
    trilat_sol = d3 / "inputs" / "trilat_solution.json"
    trilat_net = _copy_into(assets["trilat_net_json"], d3 / "inputs" / "trilateration.json")
    _run_alg(
        "geocomp:analysis_network_adjust",
        {
            "NETWORK": str(trilat_net),
            "FRAME": 0,
            "DATUM": 0,
            "OUTPUT_SOLUTION": str(trilat_sol),
            "OUTPUT_HTML": str(d3 / "inputs" / "adj.html"),
        },
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_trilateration_solution_report",
            "Adjustment report for RD-03 2D trilateration network",
            "Renders adjustment report for the adjusted RD-03 trilateration network.",
            {
                "SOLUTION": str(trilat_sol),
                "NETWORK": str(trilat_net),
                "OUTPUT_HTML": str(d3 / "outputs" / "adjustment_report.html"),
            },
            "Writes HTML adjustment report for RD-03 trilateration.",
        )
    )

    # 3. geocomp:project_store
    alg = "geocomp:project_store"
    alg_title = "Save to project store"
    menu_path = "GeoComp ▸ Project ▸ Save to project store"
    d1 = group_dir / "project_store" / "example_1_create_new_geopackage"
    s1 = _copy_into(assets["mon_sol1_json"], d1 / "inputs" / "solution.json")
    n1 = _copy_into(assets["mon_roles_json"], d1 / "inputs" / "network.json")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_create_new_geopackage",
            "Create a new GeoPackage project store containing Network + Epoch 1 Solution",
            "Initializes project_store.gpkg and writes network and solution tables.",
            {
                "STORE": str(d1 / "outputs" / "project_store.gpkg"),
                "NETWORK": str(n1),
                "SOLUTION": str(s1),
                "PROJECT_ID": "curitiba_dam_monitoring",
                "REPLACE": True,
            },
            "Creates project_store.gpkg with full relational schema, network, and solution.",
        )
    )

    d2 = group_dir / "project_store" / "example_2_append_superseding_solution"
    s2_old = json.loads(assets["mon_sol1_json"].read_text(encoding="utf-8"))
    s2_old["id"] = "sol_epoch_1"
    s2_new = json.loads(assets["mon_sol2_json"].read_text(encoding="utf-8"))
    s2_new["id"] = "sol_epoch_2"
    sol_new_path = _write_json(d2 / "inputs" / "solution_epoch2.json", s2_new)
    seed_store = d2 / "outputs" / "project_store.gpkg"
    seed_store.parent.mkdir(parents=True, exist_ok=True)
    if seed_store.exists():
        seed_store.unlink()
    with open_store(seed_store, create=True) as st:
        p = Project(id="curitiba_dam_monitoring")
        p.add_network(Network.from_dict(json.loads(assets["mon_roles_json"].read_text(encoding="utf-8"))))
        st.write(p)
        st.write_solution(Solution.from_dict(s2_old))
    _copy_into(seed_store, d2 / "inputs" / "existing_store.gpkg")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_append_superseding_solution",
            "Append a second solution (sol_epoch_2) superseding sol_epoch_1",
            "Adds a new epoch solution to an existing GeoPackage and records lineage via SUPERSEDES.",
            {
                "STORE": str(seed_store),
                "SOLUTION": str(sol_new_path),
                "PROJECT_ID": "curitiba_dam_monitoring",
                "SUPERSEDES": "sol_epoch_1",
                "REPLACE": False,
            },
            "Appends sol_epoch_2 to project_store.gpkg with provenance link to sol_epoch_1.",
        )
    )

    d3 = group_dir / "project_store" / "example_3_replace_existing_store"
    n3 = _copy_into(assets["trilat_net_json"], d3 / "inputs" / "trilateration.json")
    st3_out = _copy_into(assets["store_gpkg"], d3 / "outputs" / "replaced_store.gpkg")
    _copy_into(assets["store_gpkg"], d3 / "inputs" / "prior_store.gpkg")
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_replace_existing_store",
            "Replace contents of an existing GeoPackage store with a new network (REPLACE=True)",
            "Overwrites an existing GeoPackage store cleanly with a fresh project and network.",
            {
                "STORE": str(st3_out),
                "NETWORK": str(n3),
                "PROJECT_ID": "fresh_trilateration_project",
                "REPLACE": True,
            },
            "Replaces store contents with fresh_trilateration_project.",
        )
    )

    # 4. geocomp:project_export_postgis
    alg = "geocomp:project_export_postgis"
    alg_title = "Export project to PostGIS"
    menu_path = "GeoComp ▸ Project ▸ Export project to PostGIS"
    for idx, (slug, title, desc, schema_name) in enumerate(
        [
            (
                "example_1_export_to_default_schema",
                "Export GeoComp GeoPackage project to PostGIS schema 'geocomp_curitiba'",
                "Copies all project, station, observation, and solution tables to PostGIS and verifies "
                "row-by-row equality.",
                "geocomp_curitiba",
            ),
            (
                "example_2_export_monitoring_archive",
                "Export multi-epoch monitoring GeoPackage to PostGIS schema 'dam_monitoring_2024'",
                "Transfers monitoring project store into a dedicated departmental PostGIS schema.",
                "dam_monitoring_2024",
            ),
            (
                "example_3_export_classical_campaign",
                "Export classical survey GeoPackage to PostGIS schema 'ufpr_campus_control'",
                "Copies classical network store into PostGIS connection 'geocomp_local_pg'.",
                "ufpr_campus_control",
            ),
        ],
        start=1,
    ):
        d = group_dir / "project_export_postgis" / slug
        gpkg = _copy_into(assets["store_gpkg"], d / "inputs" / "project_store.gpkg")
        _write_text(
            d / "inputs" / "postgis_connection_setup.sql",
            f"-- Run in PostgreSQL before manual GUI test if not created automatically:\n"
            f"CREATE EXTENSION IF NOT EXISTS postgis;\n"
            f"-- GeoComp will create schema '{schema_name}' on connection 'geocomp_local_pg'.\n",
        )
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {
                    "SOURCE": str(gpkg),
                    "DATABASE": "geocomp_local_pg",
                    "SCHEMA": schema_name,
                },
                f"Copies all rows from project_store.gpkg to geocomp_local_pg / {schema_name} and verifies 0 "
                "differences.",
            )
        )

    # 5. geocomp:project_import_postgis
    alg = "geocomp:project_import_postgis"
    alg_title = "Import project from PostGIS"
    menu_path = "GeoComp ▸ Project ▸ Import project from PostGIS"
    for idx, (slug, title, desc, schema_name) in enumerate(
        [
            (
                "example_1_import_from_curitiba_schema",
                "Import PostGIS project from schema 'geocomp_curitiba' into a portable GeoPackage",
                "Copies every table from PostGIS schema 'geocomp_curitiba' into imported_curitiba.gpkg and "
                "verifies identity.",
                "geocomp_curitiba",
            ),
            (
                "example_2_import_monitoring_snapshot",
                "Import monitoring project from PostGIS schema 'dam_monitoring_2024' for offline field work",
                "Creates an offline GeoPackage snapshot from 'dam_monitoring_2024'.",
                "dam_monitoring_2024",
            ),
            (
                "example_3_import_campus_control",
                "Import classical network from PostGIS schema 'ufpr_campus_control'",
                "Round-trips 'ufpr_campus_control' back to a local GeoPackage file.",
                "ufpr_campus_control",
            ),
        ],
        start=1,
    ):
        d = group_dir / "project_import_postgis" / slug
        _write_json(
            d / "inputs" / "connection_info.json",
            {"connection_name": "geocomp_local_pg", "schema": schema_name},
        )
        out_gpkg = d / "outputs" / f"imported_{schema_name}.gpkg"
        if out_gpkg.exists():
            out_gpkg.unlink()
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {
                    "DATABASE": "geocomp_local_pg",
                    "SCHEMA": schema_name,
                    "OUTPUT": str(out_gpkg),
                },
                f"Copies all rows from geocomp_local_pg / {schema_name} into {out_gpkg.name} with 0 "
                "differences.",
            )
        )

    # 6. geocomp:project_basemap
    alg = "geocomp:project_basemap"
    alg_title = "Add base map"
    menu_path = "GeoComp ▸ Project ▸ Add base map"
    for idx, (slug, title, desc, service_id, reuse) in enumerate(
        [
            (
                "example_1_default_osm_basemap",
                "Add default configured base map (OpenStreetMap Standard) reusing existing layer",
                "Adds the default XYZ tile base map to the bottom of the QGIS layer tree.",
                "",
                True,
            ),
            (
                "example_2_opentopomap_topographic",
                "Add OpenTopoMap topographic base map (service='opentopomap')",
                "Adds the OpenTopoMap contour/topographic backdrop ideal for field planning.",
                "opentopomap",
                True,
            ),
            (
                "example_3_force_new_basemap_layer",
                "Add OpenStreetMap layer forcing a second copy (REUSE=False)",
                "Inserts a fresh base map layer even when one is already present in the project.",
                "osm",
                False,
            ),
        ],
        start=1,
    ):
        d = group_dir / "project_basemap" / slug
        _write_json(
            d / "inputs" / "basemap_request.json",
            {"service": service_id or "default (osm)", "reuse": reuse},
        )
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {"SERVICE": service_id, "REUSE": reuse},
                "Adds XYZ tile base map layer to the active QGIS project.",
            )
        )

    # 7. geocomp:project_print_layout
    alg = "geocomp:project_print_layout"
    alg_title = "Create print layout"
    menu_path = "GeoComp ▸ Project ▸ Create print layout"
    d1 = group_dir / "project_print_layout" / "example_1_network_map_with_ellipses"
    _write_json(
        d1 / "inputs" / "layout_config.json",
        {"template": "Network map with error ellipses", "title": "Curitiba Control Network"},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_network_map_with_ellipses",
            "Deliverable 1: Network map with error ellipses, scale bar, north arrow, and legend",
            "Creates a print layout framed around the project's adjusted stations and error ellipses.",
            {
                "TEMPLATE": 0,
                "QUALITY": 0,
                "TITLE": "Curitiba Control Network — 95% Error Ellipses",
                "NAME": "Curitiba_Network_Map",
            },
            "Creates print layout 'Curitiba_Network_Map' in the QGIS project layout manager.",
        )
    )

    d2 = group_dir / "project_print_layout" / "example_2_displacement_monitoring_map"
    _write_json(
        d2 / "inputs" / "layout_config.json",
        {"template": "Displacement map", "title": "Dam Deformation Vectors 2022–2024"},  # noqa: RUF001 -- a range of years
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_displacement_monitoring_map",
            "Deliverable 2: Monitoring displacement vector map",
            "Builds a deformation map layout highlighting reference vs object stations and displacement "
            "arrows.",
            {
                "TEMPLATE": 1,
                "QUALITY": 0,
                "TITLE": "Dam Deformation Vectors 2022–2024",  # noqa: RUF001 -- a range of years
                "NAME": "Dam_Displacement_Map",
            },
            "Creates print layout 'Dam_Displacement_Map' in the project.",
        )
    )

    d3 = group_dir / "project_print_layout" / "example_3_quality_redundancy_map"
    _write_json(
        d3 / "inputs" / "layout_config.json",
        {"template": "Quality map", "quality_metric": "Minimal detectable bias"},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_quality_redundancy_map",
            "Deliverable 3: Internal reliability / Minimal Detectable Bias (MDB) quality map",
            "Styles network observations by Minimal Detectable Bias (QUALITY=2) and builds a thematic print "
            "layout.",
            {
                "TEMPLATE": 2,
                "QUALITY": 2,
                "TITLE": "Network Reliability — Minimal Detectable Bias",
                "NAME": "MDB_Quality_Map",
            },
            "Creates thematic quality print layout 'MDB_Quality_Map'.",
        )
    )

    # 8. geocomp:project_system_report
    alg = "geocomp:project_system_report"
    alg_title = "GeoComp system report"
    menu_path = "GeoComp ▸ Project ▸ GeoComp system report"
    for idx, (slug, title, desc) in enumerate(
        [
            (
                "example_1_standard_system_diagnostics",
                "Standard GeoComp environment, QGIS, PROJ, and engine diagnostic report",
                "Generates an HTML diagnostic report detailing QGIS version, PROJ data paths, settings, and "
                "engine availability.",
            ),
            (
                "example_2_support_ticket_attachment",
                "System report generated as a bug-report attachment",
                "Produces a self-contained HTML environment snapshot suitable for attaching to an issue "
                "report.",
            ),
            (
                "example_3_post_engine_configuration_audit",
                "System report verifying custom RTKLIB and DynAdjust engine paths",
                "Audits configured external engine binaries and effective Global Settings values.",
            ),
        ],
        start=1,
    ):
        d = group_dir / "project_system_report" / slug
        _write_json(d / "inputs" / "diagnostic_context.json", {"scenario": slug})
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {"OUTPUT_HTML": str(d / "outputs" / "system_report.html")},
                "Writes HTML system report with QGIS, Python, PROJ, and engine diagnostics.",
            )
        )

    # 9. geocomp:project_tutorial_dataset
    alg = "geocomp:project_tutorial_dataset"
    alg_title = "Install tutorial dataset"
    menu_path = "GeoComp ▸ Project ▸ Install tutorial dataset"
    for idx, (slug, title, desc, ds_idx, ds_name) in enumerate(
        [
            (
                "example_1_install_rd01_total_station",
                "Install tutorial dataset 'rd01' (Total Station Classical Network + worked .qgz project)",
                "Copies shipped tutorial dataset rd01 into destination folder and generates "
                "worked_example.qgz.",
                0,
                "rd01",
            ),
            (
                "example_2_install_rd04_levelling_loop",
                "Install tutorial dataset 'rd04-loop' (Spirit Levelling Loop)",
                "Copies shipped levelling loop tutorial dataset rd04-loop with overwrite enabled.",
                2,
                "rd04-loop",
            ),
            (
                "example_3_install_combined_curitiba",
                "Install tutorial dataset 'combined-curitiba' (Multi-technique GNSS + TS + Levelling)",
                "Installs the multi-technique Curitiba survey dataset and worked QGIS project.",
                5,
                "combined-curitiba",
            ),
        ],
        start=1,
    ):
        d = group_dir / "project_tutorial_dataset" / slug
        _write_json(d / "inputs" / "dataset_selection.json", {"dataset_index": ds_idx, "dataset_id": ds_name})
        dest = d / "outputs" / f"tutorial_{ds_name}"
        dest.mkdir(parents=True, exist_ok=True)
        specs.append(
            ExampleSpec(
                group_id,
                group_title,
                menu_path,
                alg,
                alg_title,
                idx,
                slug,
                title,
                desc,
                {
                    "DATASET": ds_idx,
                    "DESTINATION": str(dest),
                    "OVERWRITE": True,
                },
                f"Installs tutorial dataset '{ds_name}' and creates worked QGIS project.",
            )
        )

    # 10. geocomp:project_install_engine
    alg = "geocomp:project_install_engine"
    alg_title = "Install an engine"
    menu_path = "GeoComp ▸ Project ▸ Install an engine"
    d1 = group_dir / "project_install_engine" / "example_1_install_dynadjust_acknowledged"
    _write_json(
        d1 / "inputs" / "install_request.json",
        {"engine": "DynAdjust", "acknowledge_licence": True},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_install_dynadjust_acknowledged",
            "Download, verify SHA-256, and install DynAdjust with licence acknowledgement",
            "Installs DynAdjust binaries into the user's GeoComp engines directory after verifying SHA-256.",
            {"ENGINE": 0, "ACKNOWLEDGE_LICENCE": True},
            "Verifies archive checksum, extracts DynAdjust binaries, and records installed version.",
        )
    )

    d2 = group_dir / "project_install_engine" / "example_2_install_rtklib"
    _write_json(
        d2 / "inputs" / "install_request.json",
        {"engine": "RTKLIB", "acknowledge_licence": False},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_install_rtklib",
            "Download, verify SHA-256, and install RTKLIB (rnx2rtkp)",
            "Installs RTKLIB's rnx2rtkp binary into the user's GeoComp engines directory.",
            {"ENGINE": 1, "ACKNOWLEDGE_LICENCE": False},
            "Verifies archive checksum, extracts rnx2rtkp, and reports installed version.",
        )
    )

    d3 = group_dir / "project_install_engine" / "example_3_dynadjust_without_licence_refused"
    _write_json(
        d3 / "inputs" / "install_request.json",
        {"engine": "DynAdjust", "acknowledge_licence": False, "note": "Tests licence guard"},
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_dynadjust_without_licence_refused",
            "Refuse DynAdjust installation when licence acknowledgement checkbox is unchecked",
            "Verifies that installing DynAdjust without ticking ACKNOWLEDGE_LICENCE raises a clear error.",
            {"ENGINE": 0, "ACKNOWLEDGE_LICENCE": False},
            "Refuses installation with a clear message asking to acknowledge DynAdjust's licence.",
            expect_exception="DynAdjust",
        )
    )

    # 11. geocomp:project_package_engine_problem
    alg = "geocomp:project_package_engine_problem"
    alg_title = "Package an engine problem"
    menu_path = "GeoComp ▸ Project ▸ Package an engine problem"

    d1 = group_dir / "project_package_engine_problem" / "example_1_dynadjust_failed_import"
    w1 = d1 / "inputs" / "dynadjust_work_dir"
    if w1.exists():
        shutil.rmtree(w1)
    _copy_into(assets["prepared_dir"], w1)
    run_process(
        [
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('Error: malformed station record\\n'); sys.exit(2)",
        ],
        work_dir=w1,
        program="dnaimport",
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_dynadjust_failed_import",
            "Package a failed DynAdjust dnaimport working directory into a bug-report ZIP",
            "Bundles DynaML inputs, command log, stderr output, and README with upstream issue tracker URL.",
            {
                "FOLDER": str(w1),
                "OUTPUT": str(d1 / "outputs" / "dynadjust_problem_bundle.zip"),
            },
            "Creates dynadjust_problem_bundle.zip with ENGINE='DynAdjust' and README instructions.",
        )
    )

    d2 = group_dir / "project_package_engine_problem" / "example_2_rtklib_failed_run"
    w2 = d2 / "inputs" / "rtklib_work_dir"
    if w2.exists():
        shutil.rmtree(w2)
    _copy_into(assets["rinex_dir"], w2)
    run_process(
        [sys.executable, "-c", "import sys; sys.stderr.write('Error: no navigation data\\n'); sys.exit(1)"],
        work_dir=w2,
        program="rnx2rtkp",
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_rtklib_failed_run",
            "Package a failed RTKLIB rnx2rtkp working directory into a diagnostic ZIP",
            "Bundles RINEX files, RTKLIB configuration, and invocation transcript into a reproducible "
            "archive.",
            {
                "FOLDER": str(w2),
                "OUTPUT": str(d2 / "outputs" / "rtklib_problem_bundle.zip"),
            },
            "Creates rtklib_problem_bundle.zip with ENGINE='RTKLIB' and upstream reporting link.",
        )
    )

    d3 = group_dir / "project_package_engine_problem" / "example_3_dynadjust_singular_adjustment"
    w3 = d3 / "inputs" / "dynadjust_adjust_work_dir"
    if w3.exists():
        shutil.rmtree(w3)
    _copy_into(assets["prepared_dir"], w3)
    run_process([sys.executable, "-c", "print('dnaimport ok')"], work_dir=w3, program="dnaimport")
    run_process(
        [sys.executable, "-c", "import sys; sys.stderr.write('Singular normal matrix\\n'); sys.exit(3)"],
        work_dir=w3,
        program="dnaadjust",
    )
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_dynadjust_singular_adjustment",
            "Package a multi-stage DynAdjust run where dnaimport succeeded but dnaadjust failed",
            "Captures full multi-stage command history (dnaimport -> dnaadjust) in the diagnostic ZIP.",
            {
                "FOLDER": str(w3),
                "OUTPUT": str(d3 / "outputs" / "dynadjust_stage2_problem.zip"),
            },
            "Packages multi-stage logs into dynadjust_stage2_problem.zip.",
        )
    )

    return specs


def _build_global_settings_examples(base_dir: Path, assets: dict[str, Any]) -> list[ExampleSpec]:
    group_id = "08_global_settings"
    group_title = "Global Settings…"
    group_dir = base_dir / group_id
    alg = "geocomp:global_settings_dialog"
    alg_title = "Global Settings…"
    menu_path = "GeoComp ▸ Global Settings…"
    specs: list[ExampleSpec] = []

    d1 = group_dir / "global_settings_dialog" / "example_1_equipment_profile_libraries"
    lev_lib = _copy_into(assets["lev_profiles_json"], d1 / "inputs" / "level_profiles.json")
    settings_1 = {
        "total_station.default_temperature_celsius": 22.5,
        "total_station.default_pressure_hpa": 915.0,
        "level.profile_library": str(lev_lib),
        "level.tolerance_coefficient": 0.004,
        "gravimeter.tide_amplification": 1.16,
    }
    _write_json(d1 / "inputs" / "settings_profile_bundle.json", settings_1)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            1,
            "example_1_equipment_profile_libraries",
            "Equipment profile libraries & meteorological defaults (Total Station, Level, Gravimeter)",
            "Configures custom JSON instrument library for Level and Curitiba plateau atmospheric defaults.",
            settings_1,
            "Applies equipment profile paths and meteorological constants in Global Settings and verifies "
            "persistence.",
        )
    )

    d2 = group_dir / "global_settings_dialog" / "example_2_gnss_and_reference_systems"
    geoid_file = _copy_into(assets["geoid_asc"], d2 / "inputs" / "curitiba_planar.asc")
    services_file = _write_json(
        d2 / "inputs" / "custom_gnss_services.json",
        [
            {
                "id": "ufpr_mirror",
                "name": "UFPR Local GNSS Mirror",
                "sp3_final": "https://gnss.ufpr.br/igs/W{wwww}/igs{wwww}{d}.sp3.Z",
                "nav_gps": "https://gnss.ufpr.br/brdc/{yyyy}/brdc{ddd}0.{yy}n.Z",
            }
        ],
    )
    settings_2 = {
        "reference_systems.preferred_crs": "EPSG:31982",
        "reference_systems.default_epoch": 2000.4,
        "reference_systems.geoid_model": str(geoid_file),
        "reference_systems.geoid_sigma": 0.05,
        "gnss.elevation_mask": 15.0,
        "gnss.service_definitions": str(services_file),
        "gnss.product_fallback": True,
    }
    _write_json(d2 / "inputs" / "settings_gnss_reference_bundle.json", settings_2)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            2,
            "example_2_gnss_and_reference_systems",
            "SIRGAS 2000 / UTM 22S (EPSG:31982) reference system, geoid model, and GNSS product mirror",
            "Configures preferred CRS (EPSG:31982), epoch 2000.4, default geoid grid, and custom GNSS "
            "product download service JSON.",
            settings_2,
            "Persists reference system, geoid model path, and GNSS service definitions in Global Settings.",
        )
    )

    d3 = group_dir / "global_settings_dialog" / "example_3_stochastic_engines_and_interface"
    basemap_cat = _write_json(
        d3 / "inputs" / "custom_basemaps.json",
        {
            "services": [
                {
                    "id": "ibge_topo",
                    "name": "IBGE Topographic Base",
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "attribution": "© IBGE / OpenStreetMap contributors",
                    "zmin": 0,
                    "zmax": 18,
                }
            ]
        },
    )
    settings_3 = {
        "stochastic.confidence_level": 0.99,
        "stochastic.outlier_alpha": 0.001,
        "stochastic.outlier_beta": 0.20,
        "paths.dynadjust_directory": str(assets["dynadjust_dir"]),
        "paths.rtklib_program": str(assets["rtklib_bin"]),
        "basemaps.catalogue": str(basemap_cat),
        "interface.mode": "advanced",
        "interface.angle_format": "dms",
        "interface.coordinate_decimals": 4,
    }
    _write_json(d3 / "inputs" / "settings_advanced_bundle.json", settings_3)
    specs.append(
        ExampleSpec(
            group_id,
            group_title,
            menu_path,
            alg,
            alg_title,
            3,
            "example_3_stochastic_engines_and_interface",
            "99% stochastic model, external engine paths (RTKLIB & DynAdjust), custom basemaps, and Advanced "
            "UI mode",
            "Configures Baarda snooping parameters, explicit engine paths, custom basemap catalogue, and "
            "Advanced DMS display.",
            settings_3,
            "Updates stochastic, engine path, basemap, and UI settings and verifies GlobalSettingsDialog "
            "round-trip.",
        )
    )

    return specs


@contextmanager
def _verification_environment(base_dir: Path, assets: dict[str, Any]):
    """Provide deterministic offline stand-ins for external servers during --verify."""
    import zipfile

    from qgis.core import (
        QgsCoordinateReferenceSystem,
        QgsFeature,
        QgsField,
        QgsGeometry,
        QgsPointXY,
        QgsProject,
        QgsVectorLayer,
    )
    from qgis.PyQt.QtCore import QMetaType

    from geocomp.engines import manager as engine_manager_mod
    from geocomp.engines.manager import EngineRelease, current_platform
    from geocomp.io.store import open_store
    from geocomp.services import downloads as downloads_svc_mod
    from geocomp.services import engines as engines_svc_mod
    from geocomp.services import postgis as postgis_svc_mod
    from geocomp.services.settings_service import settings as gc_settings
    from tests import synthetic as syn

    gc_settings.set_global("paths.rtklib_program", str(assets["rtklib_bin"]))
    gc_settings.set_global("paths.dynadjust_directory", str(assets["dynadjust_dir"]))

    project = QgsProject.instance()
    project.clear()
    project.setCrs(QgsCoordinateReferenceSystem("EPSG:31982"))

    st_layer = QgsVectorLayer("Point?crs=EPSG:31982", "Adjusted stations", "memory")
    st_dp = st_layer.dataProvider()
    st_dp.addAttributes(
        [
            QgsField("station", QMetaType.Type.QString),
            QgsField("role", QMetaType.Type.QString),
            QgsField("sigma_2d", QMetaType.Type.Double),
            QgsField("positional_uncertainty", QMetaType.Type.Double),
        ]
    )
    st_layer.updateFields()
    for sid, (e, n, _h) in syn.COORDINATES.items():
        feat = QgsFeature(st_layer.fields())
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(e, n)))
        feat.setAttributes([sid, "reference" if sid in ("A", "B") else "object", 0.002, 0.004])
        st_dp.addFeature(feat)
    st_layer.setCustomProperty("geocomp/result_layer", "stations")
    project.addMapLayer(st_layer)

    obs_layer = QgsVectorLayer("LineString?crs=EPSG:31982", "Observations", "memory")
    obs_dp = obs_layer.dataProvider()
    obs_dp.addAttributes(
        [
            QgsField("from_station", QMetaType.Type.QString),
            QgsField("to_station", QMetaType.Type.QString),
            QgsField("redundancy", QMetaType.Type.Double),
            QgsField("standardised_residual", QMetaType.Type.Double),
            QgsField("mdb", QMetaType.Type.Double),
            QgsField("external_reliability", QMetaType.Type.Double),
        ]
    )
    obs_layer.updateFields()
    for u, v in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C"), ("B", "D")]:
        feat = QgsFeature(obs_layer.fields())
        eu, nu, _ = syn.COORDINATES[u]
        ev, nv, _ = syn.COORDINATES[v]
        feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(eu, nu), QgsPointXY(ev, nv)]))
        feat.setAttributes([u, v, 0.65, 0.42, 0.0035, 0.0018])
        obs_dp.addFeature(feat)
    obs_layer.setCustomProperty("geocomp/result_layer", "residuals")
    project.addMapLayer(obs_layer)

    ell_layer = QgsVectorLayer("Polygon?crs=EPSG:31982", "Error ellipses", "memory")
    ell_dp = ell_layer.dataProvider()
    ell_dp.addAttributes([QgsField("station", QMetaType.Type.QString)])
    ell_layer.updateFields()
    for sid, (e, n, _h) in syn.COORDINATES.items():
        feat = QgsFeature(ell_layer.fields())
        ring = [
            QgsPointXY(e - 2.0, n - 1.0),
            QgsPointXY(e + 2.0, n - 1.0),
            QgsPointXY(e + 2.0, n + 1.0),
            QgsPointXY(e - 2.0, n + 1.0),
            QgsPointXY(e - 2.0, n - 1.0),
        ]
        feat.setGeometry(QgsGeometry.fromPolygonXY([ring]))
        feat.setAttributes([sid])
        ell_dp.addFeature(feat)
    ell_layer.setCustomProperty("geocomp/result_layer", "ellipses")
    project.addMapLayer(ell_layer)

    disp_layer = QgsVectorLayer("LineString?crs=EPSG:31982", "Displacements", "memory")
    disp_dp = disp_layer.dataProvider()
    disp_dp.addAttributes(
        [QgsField("station", QMetaType.Type.QString), QgsField("significant", QMetaType.Type.Int)]
    )
    disp_layer.updateFields()
    for sid in ("C", "D"):
        e, n, _ = syn.COORDINATES[sid]
        feat = QgsFeature(disp_layer.fields())
        feat.setGeometry(
            QgsGeometry.fromPolylineXY([QgsPointXY(e, n), QgsPointXY(e + 5.0, n - 3.0)])
        )
        feat.setAttributes([sid, 1])
        disp_dp.addFeature(feat)
    disp_layer.setCustomProperty("geocomp/result_layer", "displacements")
    project.addMapLayer(disp_layer)

    pg_backing_dir = base_dir / "_shared_pipeline" / "mock_postgis_schemas"
    if pg_backing_dir.exists():
        shutil.rmtree(pg_backing_dir)
    pg_backing_dir.mkdir(parents=True, exist_ok=True)

    orig_open_db = postgis_svc_mod.open_database_store
    orig_conn_names = postgis_svc_mod.connection_names

    class _StandInDatabaseStore:
        def __init__(self, conn: str, schema: str, create: bool = False):
            self._path = pg_backing_dir / f"{conn}__{schema}.gpkg"
            self.location = f"{conn} / {schema}"
            self._store = open_store(self._path, create=create)

        def __enter__(self):
            self._store.__enter__()
            return self

        def __exit__(self, *exc):
            return self._store.__exit__(*exc)

        def __getattr__(self, name: str):
            return getattr(self._store, name)

        def remove_what_was_created(self) -> None:
            self._store.close()
            if self._path.exists():
                self._path.unlink()

    def _mock_open_database_store(
        connection_name: str, schema: str, *, create: bool = False, migrate_older: bool = False
    ):
        return _StandInDatabaseStore(connection_name, schema, create=create)

    def _build_engine_zip(programs: tuple[str, ...], version_line: str) -> tuple[bytes, str]:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for prog in programs:
                script = (
                    f"#!/usr/bin/env python3\nimport sys\n"
                    f"if '--version' in sys.argv or '-h' in sys.argv:\n"
                    f"    print({version_line!r})\n"
                ).encode()
                info = zipfile.ZipInfo(f"bin/{prog}")
                info.external_attr = 0o755 << 16
                zf.writestr(info, script)
        payload = buf.getvalue()
        return payload, hashlib.sha256(payload).hexdigest()

    dna_members = (
        "dnaadjust",
        "dnadiff",
        "dnageoid",
        "dnaimport",
        "dnaplot",
        "dnareftran",
        "dnasegment",
        "dynadjust",
    )
    dna_bytes, dna_sha = _build_engine_zip(
        dna_members, "+ Version:      1.4.0, Release with OpenBLAS"
    )
    rtk_bytes, rtk_sha = _build_engine_zip(("rnx2rtkp",), "rnx2rtkp RTKLIB EX 2.5.1")

    plat = current_platform()
    orig_pinned = engine_manager_mod.PINNED
    engine_manager_mod.PINNED = (
        EngineRelease(
            engine="dynadjust",
            version="1.4.0",
            platform=plat,
            url="https://local.geocomp.test/dynadjust.zip",
            sha256=dna_sha,
            members=dna_members,
        ),
        EngineRelease(
            engine="rtklib",
            version="2.5.1",
            platform=plat,
            url="https://local.geocomp.test/rtklib.zip",
            sha256=rtk_sha,
            members=("rnx2rtkp",),
        ),
    )

    managed_root = base_dir / "_shared_pipeline" / "managed_engines"
    managed_root.mkdir(parents=True, exist_ok=True)
    orig_engine_root = engines_svc_mod.engine_root
    engines_svc_mod.engine_root = lambda: managed_root

    orig_archive_call = engines_svc_mod.QgisArchiveFetcher.__call__

    def _mock_archive_fetch(self, url: str, destination: Path) -> None:
        Path(destination).write_bytes(dna_bytes if "dynadjust" in url else rtk_bytes)

    engines_svc_mod.QgisArchiveFetcher.__call__ = _mock_archive_fetch

    orig_qgis_exists = downloads_svc_mod.QgisFetcher.exists
    orig_qgis_get = downloads_svc_mod.QgisFetcher.get

    def _mock_product_exists(self, url: str, authcfg: str) -> bool:
        return True

    def _mock_product_get(self, url: str, authcfg: str) -> bytes:
        content = b"#cP2005  4  2  0  0  0.00000000      96 ORBIT IGS00 HLM  IGS\nEOF\n"
        if url.endswith(".gz"):
            return gzip.compress(content)
        return content

    downloads_svc_mod.QgisFetcher.exists = _mock_product_exists
    downloads_svc_mod.QgisFetcher.get = _mock_product_get

    gc_settings.set_global("gnss.product_services", "noaa-ncn")
    gc_settings.set_global("gnss.service_definitions", "")
    gc_settings.set_global("gnss.product_cache", str(base_dir / "_shared_pipeline" / "product_cache"))

    postgis_svc_mod.open_database_store = _mock_open_database_store
    postgis_svc_mod.connection_names = lambda: ["geocomp_local_pg"]
    try:
        yield
    finally:
        postgis_svc_mod.open_database_store = orig_open_db
        postgis_svc_mod.connection_names = orig_conn_names
        engine_manager_mod.PINNED = orig_pinned
        engines_svc_mod.engine_root = orig_engine_root
        engines_svc_mod.QgisArchiveFetcher.__call__ = orig_archive_call
        downloads_svc_mod.QgisFetcher.exists = orig_qgis_exists
        downloads_svc_mod.QgisFetcher.get = orig_qgis_get


def _verify_all_examples(base_dir: Path, assets: dict[str, Any], specs: list[ExampleSpec]) -> None:
    """Execute all 150 examples in headless QGIS Processing and verify outputs."""
    from qgis.core import (
        QgsApplication,
        QgsProcessingContext,
        QgsProcessingException,
        QgsProcessingFeedback,
        QgsProject,
    )

    from geocomp.gui.settings_dialog import GlobalSettingsDialog
    from geocomp.services.settings_service import settings as gc_settings

    class _SilentFeedback(QgsProcessingFeedback):
        def __init__(self):
            super().__init__()
            self.infos: list[str] = []
            self.warnings: list[str] = []
            self.errors: list[str] = []

        def pushInfo(self, text: str) -> None:  # noqa: N802
            self.infos.append(text)

        def pushWarning(self, text: str) -> None:  # noqa: N802
            self.warnings.append(text)

        def reportError(self, text: str, fatalError: bool = False) -> None:  # noqa: N802, N803
            self.errors.append(text)

    passed = 0
    with _verification_environment(base_dir, assets):
        for spec in specs:
            alg_folder = spec.algorithm_id.split(":", 1)[-1]
            ex_dir = base_dir / spec.menu_group_id / alg_folder / spec.slug
            (ex_dir / "outputs").mkdir(parents=True, exist_ok=True)

            if spec.algorithm_id == "geocomp:global_settings_dialog":
                for key, val in spec.parameters.items():
                    gc_settings.set_global(key, val)
                    assert gc_settings.value(key) == val, f"Setting {key} mismatch"
                dlg = GlobalSettingsDialog()
                dlg.close()
                for key in spec.parameters:
                    gc_settings.reset_global(key)
                gc_settings.set_global("paths.rtklib_program", str(assets["rtklib_bin"]))
                gc_settings.set_global("paths.dynadjust_directory", str(assets["dynadjust_dir"]))
                result_summary: dict[str, Any] = {
                    "status": "verified",
                    "applied_settings": spec.parameters,
                }
                _write_json(ex_dir / "outputs" / "verified_settings.json", result_summary)
                _write_json(
                    ex_dir / "example.json",
                    {**dataclasses.asdict(spec), "verification": result_summary},
                )
                passed += 1
                continue

            proto = QgsApplication.processingRegistry().algorithmById(spec.algorithm_id)
            assert proto is not None, f"Algorithm not registered: {spec.algorithm_id}"
            alg = proto.create({})
            feedback = _SilentFeedback()
            context = QgsProcessingContext()
            context.setProject(QgsProject.instance())

            if spec.expect_exception:
                try:
                    alg.run(spec.parameters, context, feedback, catchExceptions=False)
                except QgsProcessingException as exc:
                    assert spec.expect_exception in str(exc), (
                        f"Expected {spec.expect_exception!r} in {exc!r}"
                    )
                    result_summary = {
                        "status": "verified_expected_exception",
                        "exception": str(exc),
                    }
                    _write_json(ex_dir / "outputs" / "expected_error.json", result_summary)
                else:
                    raise AssertionError(
                        f"Expected QgsProcessingException for {spec.algorithm_id}/{spec.slug}"
                    )
            else:
                try:
                    results, ok = alg.run(
                        spec.parameters, context, feedback, catchExceptions=False
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed {spec.algorithm_id} / {spec.slug}: {exc}\n"
                        f"Errors: {feedback.errors}\nWarnings: {feedback.warnings}"
                    ) from exc
                assert ok, f"Algorithm returned ok=False: {spec.algorithm_id} / {spec.slug}"
                result_summary = {
                    "status": "verified",
                    "results": {k: str(v) for k, v in results.items()},
                    "info_lines": len(feedback.infos),
                    "warning_lines": len(feedback.warnings),
                }
                _write_json(ex_dir / "outputs" / "run_results.json", result_summary)

            _write_json(
                ex_dir / "example.json",
                {**dataclasses.asdict(spec), "verification": result_summary},
            )
            passed += 1

    print(f"Verified {passed}/{len(specs)} synthetic examples successfully.")


def _write_catalog_files(base_dir: Path, specs: list[ExampleSpec]) -> None:
    """Write ``MANIFEST.json`` and a comprehensive ``README.md`` in *base_dir*."""
    manifest = {
        "plugin": "GeoComp",
        "total_menu_options": len({s.algorithm_id for s in specs}),
        "total_examples": len(specs),
        "examples": [
            {
                "menu_group_id": s.menu_group_id,
                "menu_group_title": s.menu_group_title,
                "menu_path": s.menu_path,
                "algorithm_id": s.algorithm_id,
                "algorithm_title": s.algorithm_title,
                "example_index": s.example_index,
                "slug": s.slug,
                "folder": f"{s.menu_group_id}/{s.algorithm_id.split(':', 1)[-1]}/{s.slug}",
                "title": s.title,
                "scenario": s.scenario,
                "parameters": s.parameters,
                "expected_summary": s.expected_summary,
            }
            for s in specs
        ],
    }
    _write_json(base_dir / "MANIFEST.json", manifest)

    lines: list[str] = [
        "# GeoComp Synthetic Examples Catalogue",
        "",
        "This directory contains **150 ready-to-use synthetic examples** (3 distinct scenarios for",
        "each of the **49 Processing algorithms** plus the **Global Settings…** dialog across all",
        "8 top-level menu entries of the GeoComp QGIS plugin).",
        "",
        "## Quick Start",
        "",
        "1. **In QGIS GUI:** Open any menu item under **GeoComp**, browse to the corresponding",
        "   `synthetic_examples/<group>/<algorithm>/example_<N>_<slug>/inputs/` folder, and",
        "   enter the parameter values listed in `example.json` (or in the tables below).",
        "2. **Reference Outputs:** Every example folder also includes an `outputs/` subfolder",
        "   containing the verified output files produced by GeoComp.",
        "3. **Regenerate & Verify All 150 Examples Headlessly:**",
        "   ```bash",
        "   python3 scripts/generate_synthetic_examples.py --verify",
        "   ```",
        "",
        "## Directory Hierarchy by Menu Group",
        "",
        "| Group Folder | Menu Group | Menu Items | Synthetic Examples |",
        "|---|---|---:|---:|",
    ]

    groups: dict[str, list[ExampleSpec]] = {}
    for s in specs:
        groups.setdefault(s.menu_group_id, []).append(s)

    for gid, gspecs in groups.items():
        gtitle = gspecs[0].menu_group_title
        n_items = len({x.algorithm_id for x in gspecs})
        lines.append(f"| `{gid}/` | **{gtitle}** | {n_items} | {len(gspecs)} |")

    lines.append("")

    for gid, gspecs in groups.items():
        gtitle = gspecs[0].menu_group_title
        lines.append("---")
        lines.append(f"## {gtitle} (`{gid}`)")
        lines.append("")

        by_alg: dict[str, list[ExampleSpec]] = {}
        for s in gspecs:
            by_alg.setdefault(s.algorithm_id, []).append(s)

        for alg_id, aspecs in by_alg.items():
            first = aspecs[0]
            alg_short = alg_id.split(":", 1)[-1]
            lines.append(f"### {first.menu_path} (`{alg_id}`)")
            lines.append("")
            for ex in aspecs:
                rel_folder = f"{gid}/{alg_short}/{ex.slug}"
                lines.append(f"#### Example {ex.example_index}: {ex.title}")
                lines.append(f"- **Folder:** `{rel_folder}/`")
                lines.append(f"- **Scenario:** {ex.scenario}")
                lines.append(f"- **Expected Result:** {ex.expected_summary}")
                lines.append("- **Parameters (`example.json`):**")
                lines.append("  ```json")
                lines.extend(
                    f"  {line}"
                    for line in json.dumps(ex.parameters, indent=2, ensure_ascii=False).splitlines()
                )
                lines.append("  ```")
                lines.append("")

    _write_text(base_dir / "README.md", "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "synthetic_examples",
        help="Target directory for generated synthetic examples (default: synthetic_examples/)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Execute all 150 examples through headless QGIS Processing and verify outputs",
    )
    args = parser.parse_args(argv)

    from qgis.core import QgsApplication

    from geocomp.provider import GeoCompProvider

    qgs = QgsApplication([], False)
    qgs.initQgis()
    provider = GeoCompProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    out_dir: Path = args.output.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    assets = _prepare_shared_assets(out_dir)
    specs: list[ExampleSpec] = []
    specs.extend(_build_total_station_examples(out_dir, assets))
    specs.extend(_build_levelling_examples(out_dir, assets))
    specs.extend(_build_gnss_examples(out_dir, assets))
    specs.extend(_build_gravimetry_examples(out_dir, assets))
    specs.extend(_build_integration_examples(out_dir, assets))
    specs.extend(_build_analysis_examples(out_dir, assets))
    specs.extend(_build_project_examples(out_dir, assets))
    specs.extend(_build_global_settings_examples(out_dir, assets))

    for spec in specs:
        alg_folder = spec.algorithm_id.split(":", 1)[-1]
        ex_dir = out_dir / spec.menu_group_id / alg_folder / spec.slug
        _write_json(ex_dir / "example.json", dataclasses.asdict(spec))

    if args.verify:
        _verify_all_examples(out_dir, assets, specs)

    _write_catalog_files(out_dir, specs)
    print(
        f"Generated {len(specs)} synthetic examples across "
        f"{len({s.algorithm_id for s in specs})} menu options in {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
