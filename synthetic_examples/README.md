# GeoComp Synthetic Examples Catalogue

This directory contains **150 ready-to-use synthetic examples** (3 distinct scenarios for
each of the **49 Processing algorithms** plus the **Global Settings…** dialog across all
8 top-level menu entries of the GeoComp QGIS plugin).

## Quick Start

1. **In QGIS GUI:** Open any menu item under **GeoComp**, browse to the corresponding
   `synthetic_examples/<group>/<algorithm>/example_<N>_<slug>/inputs/` folder, and
   enter the parameter values listed in `example.json` (or in the tables below).
2. **Reference Outputs:** Every example folder also includes an `outputs/` subfolder
   containing the verified output files produced by GeoComp.
3. **Regenerate & Verify All 150 Examples Headlessly:**
   ```bash
   python3 scripts/generate_synthetic_examples.py --verify
   ```

## Directory Hierarchy by Menu Group

| Group Folder | Menu Group | Menu Items | Synthetic Examples |
|---|---|---:|---:|
| `01_total_station/` | **Total Station** | 8 | 24 |
| `02_level/` | **Level** | 6 | 18 |
| `03_gnss/` | **GNSS** | 9 | 27 |
| `04_gravimetry/` | **Gravimetry** | 2 | 6 |
| `05_integration/` | **Integration** | 4 | 12 |
| `06_analysis/` | **Analysis** | 9 | 27 |
| `07_project/` | **Project** | 11 | 33 |
| `08_global_settings/` | **Global Settings…** | 1 | 3 |

---
## Total Station (`01_total_station`)

### GeoComp ▸ Total Station ▸ Import field book (`geocomp:totalstation_import_fieldbook`)

#### Example 1: Two-face CSV field book (RD-01) with explicit direction/zenith/distance sigmas
- **Folder:** `01_total_station/totalstation_import_fieldbook/example_1_rd01_csv/`
- **Scenario:** Imports 12 readings across 3 station setups (A, B, C) with 1 arcsec angle and 2 mm distance precision.
- **Expected Result:** Imports 12 valid readings across 3 setups with 0 rejected records.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_1_rd01_csv/inputs/fieldbook.csv",
    "SIGMA_DIRECTION": 5e-06,
    "SIGMA_ZENITH": 5e-06,
    "SIGMA_DISTANCE": 0.002,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_1_rd01_csv/outputs/readings.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_1_rd01_csv/outputs/report.html",
    "OUTPUT_FINDINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_1_rd01_csv/outputs/findings.csv"
  }
  ```

#### Example 2: Excel spreadsheet (.xlsx) field book import with high-precision EDM sigmas
- **Folder:** `01_total_station/totalstation_import_fieldbook/example_2_xlsx_workbook/`
- **Scenario:** Imports the field book directly from an Excel .xlsx workbook without converting to CSV.
- **Expected Result:** Reads all 12 records from .xlsx matching CSV import identically.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_2_xlsx_workbook/inputs/fieldbook.xlsx",
    "SIGMA_DIRECTION": 2.5e-06,
    "SIGMA_ZENITH": 2.5e-06,
    "SIGMA_DISTANCE": 0.001,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_2_xlsx_workbook/outputs/readings.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_2_xlsx_workbook/outputs/report.html",
    "OUTPUT_FINDINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_2_xlsx_workbook/outputs/findings.csv"
  }
  ```

#### Example 3: Field book with a malformed row audited in findings.csv (FAIL_ON_REJECTED=False)
- **Folder:** `01_total_station/totalstation_import_fieldbook/example_3_rejected_row_audit/`
- **Scenario:** Appends a corrupted row to verify that valid rows import while the bad row is logged in findings.csv.
- **Expected Result:** Imports the 12 valid rows and logs REJECTED_COUNT=1 in findings.csv.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_3_rejected_row_audit/inputs/fieldbook_with_bad_row.csv",
    "SIGMA_DIRECTION": 5e-06,
    "SIGMA_ZENITH": 5e-06,
    "SIGMA_DISTANCE": 0.002,
    "FAIL_ON_REJECTED": false,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_3_rejected_row_audit/outputs/readings.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_3_rejected_row_audit/outputs/report.html",
    "OUTPUT_FINDINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_import_fieldbook/example_3_rejected_row_audit/outputs/findings.csv"
  }
  ```

### GeoComp ▸ Total Station ▸ Generalised pre-processing (`geocomp:totalstation_preprocess`)

#### Example 1: Two-face reduction catching RD-01's face-distance blunder (APPLY_ATMOSPHERIC=False)
- **Folder:** `01_total_station/totalstation_preprocess/example_1_no_atmospheric_blunder_caught/`
- **Scenario:** Pairs Face I and Face II readings across 6 pointings and flags the 1 pointing with a face-distance blunder.
- **Expected Result:** Reduces 6 pointings (USABLE_COUNT=5, BLOCKING_COUNT=1).
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_1_no_atmospheric_blunder_caught/inputs/readings.json",
    "APPLY_ATMOSPHERIC": false,
    "OUTPUT_REDUCED": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_1_no_atmospheric_blunder_caught/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_1_no_atmospheric_blunder_caught/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_1_no_atmospheric_blunder_caught/outputs/reductions.csv"
  }
  ```

#### Example 2: Atmospheric EDM scale reduction at 30 °C, 915 hPa, 50% RH
- **Folder:** `01_total_station/totalstation_preprocess/example_2_warm_atmosphere_correction/`
- **Scenario:** Applies first-velocity atmospheric correction and propagates temperature/pressure uncertainties.
- **Expected Result:** Applies atmospheric ppm correction and inflates distance variance by meteorological uncertainties.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_2_warm_atmosphere_correction/inputs/readings.json",
    "TEMPERATURE": 30.0,
    "PRESSURE": 915.0,
    "HUMIDITY": 50.0,
    "APPLY_ATMOSPHERIC": true,
    "OUTPUT_REDUCED": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_2_warm_atmosphere_correction/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_2_warm_atmosphere_correction/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_2_warm_atmosphere_correction/outputs/reductions.csv"
  }
  ```

#### Example 3: Custom face-distance tolerance (1.0 m) and explicit distance/zenith correlation (0.25)
- **Folder:** `01_total_station/totalstation_preprocess/example_3_relaxed_distance_tolerance/`
- **Scenario:** Relaxes face-pair distance tolerance to 1.0 m and sets distance/zenith correlation to 0.25.
- **Expected Result:** Accepts all 6 pointings under the 1.0 m tolerance and records 0.25 correlation.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_3_relaxed_distance_tolerance/inputs/readings.json",
    "APPLY_ATMOSPHERIC": false,
    "DISTANCE_TOLERANCE": 1.0,
    "CORRELATION": 0.25,
    "OUTPUT_REDUCED": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_3_relaxed_distance_tolerance/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_3_relaxed_distance_tolerance/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_preprocess/example_3_relaxed_distance_tolerance/outputs/reductions.csv"
  }
  ```

### GeoComp ▸ Total Station ▸ Traverse (`geocomp:totalstation_traverse`)

#### Example 1: Closed 4-station polygon traverse (A,B,C,D,A) with Compass (Bowditch) distribution
- **Folder:** `01_total_station/totalstation_traverse/example_1_closed_loop_bowditch/`
- **Scenario:** Runs a closed loop starting and ending at A (1000, 2000) with backsight D.
- **Expected Result:** Closes with zero angular and linear misclosure and recovers B, C, D.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_1_closed_loop_bowditch/inputs/reductions.json",
    "ROUTE": "A,B,C,D,A",
    "BACKSIGHT": "D",
    "START_EASTING": 1000.0,
    "START_NORTHING": 1000.0,
    "START_AZIMUTH": 333.434948822922,
    "CLOSE_AZIMUTH": 333.434948822922,
    "KIND": 0,
    "METHOD": 0,
    "OUTPUT_COORDINATES": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_1_closed_loop_bowditch/outputs/coordinates.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_1_closed_loop_bowditch/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_1_closed_loop_bowditch/outputs/stations.csv"
  }
  ```

#### Example 2: Connected traverse (A,B,C) closing onto known station C with Transit rule
- **Folder:** `01_total_station/totalstation_traverse/example_2_connected_transit_rule/`
- **Scenario:** Traverses from A through B to known station C (1140, 2110) using Transit distribution.
- **Expected Result:** Recovers B and C along the connected traverse using the Transit rule.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_2_connected_transit_rule/inputs/reductions.json",
    "ROUTE": "A,B,C",
    "BACKSIGHT": "D",
    "START_EASTING": 1000.0,
    "START_NORTHING": 1000.0,
    "START_AZIMUTH": 333.434948822922,
    "CLOSE_EASTING": 1230.0,
    "CLOSE_NORTHING": 940.0,
    "CLOSE_AZIMUTH": 150.25511870305778,
    "KIND": 1,
    "METHOD": 1,
    "OUTPUT_COORDINATES": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_2_connected_transit_rule/outputs/coordinates.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_2_connected_transit_rule/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_2_connected_transit_rule/outputs/stations.csv"
  }
  ```

#### Example 3: Open cantilever traverse (A,B,C) with no misclosure distribution
- **Folder:** `01_total_station/totalstation_traverse/example_3_open_traverse_undistributed/`
- **Scenario:** Propagates coordinates along open route A -> B -> C without closing control.
- **Expected Result:** Computes open traverse coordinates for B and C.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_3_open_traverse_undistributed/inputs/reductions.json",
    "ROUTE": "A,B,C",
    "BACKSIGHT": "D",
    "START_EASTING": 1000.0,
    "START_NORTHING": 1000.0,
    "START_AZIMUTH": 333.434948822922,
    "KIND": 2,
    "METHOD": 2,
    "OUTPUT_COORDINATES": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_3_open_traverse_undistributed/outputs/coordinates.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_3_open_traverse_undistributed/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_traverse/example_3_open_traverse_undistributed/outputs/stations.csv"
  }
  ```

### GeoComp ▸ Total Station ▸ Resection (`geocomp:totalstation_resection`)

#### Example 1: Redundant 4-target free-station resection at station R (targets A, B, C, D)
- **Folder:** `01_total_station/totalstation_resection/example_1_four_control_pillars/`
- **Scenario:** Solves occupied station R from observations to 4 surrounding control pillars.
- **Expected Result:** Recovers R = (1060.0, 2050.0) m and orientation constant.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_1_four_control_pillars/inputs/reductions.json",
    "STATION": "R",
    "KNOWN": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_1_four_control_pillars/inputs/known.json",
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_1_four_control_pillars/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_1_four_control_pillars/outputs/report.html"
  }
  ```

#### Example 2: Minimal 3-target resection at station R from control triangle (A, B, C)
- **Folder:** `01_total_station/totalstation_resection/example_2_three_point_minimal/`
- **Scenario:** Determines station R using only 3 control stations (A, B, C).
- **Expected Result:** Recovers exact coordinates of station R from 3 known points.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_2_three_point_minimal/inputs/reductions.json",
    "STATION": "R",
    "KNOWN": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_2_three_point_minimal/inputs/known_3pts.json",
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_2_three_point_minimal/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_2_three_point_minimal/outputs/report.html"
  }
  ```

#### Example 3: Resection starting from an explicit offset approximate position (1135, 980)
- **Folder:** `01_total_station/totalstation_resection/example_3_offset_approximate_start/`
- **Scenario:** Tests Gauss-Newton convergence when explicit approximate easting/northing are 18 m off.
- **Expected Result:** Converges from (1135, 980) to exact R = (1120.0, 990.0) m.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_3_offset_approximate_start/inputs/reductions.json",
    "STATION": "R",
    "KNOWN": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_3_offset_approximate_start/inputs/known.json",
    "APPROX_EASTING": 1135.0,
    "APPROX_NORTHING": 980.0,
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_3_offset_approximate_start/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_resection/example_3_offset_approximate_start/outputs/report.html"
  }
  ```

### GeoComp ▸ Total Station ▸ Forward intersection (`geocomp:totalstation_intersection`)

#### Example 1: Two-ray forward intersection to inaccessible target P1 from A and C
- **Folder:** `01_total_station/totalstation_intersection/example_1_two_ray_p1/`
- **Scenario:** Intersects azimuth rays from stations A and C onto target P1.
- **Expected Result:** Recovers P1 coordinates with strong intersection geometry.
- **Parameters (`example.json`):**
  ```json
  {
    "SIGHTINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_1_two_ray_p1/inputs/sightings_p1.json",
    "TARGET": "P1",
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_1_two_ray_p1/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_1_two_ray_p1/outputs/report.html"
  }
  ```

#### Example 2: Redundant 3-ray least-squares forward intersection to P1 from A, B, and C
- **Folder:** `01_total_station/totalstation_intersection/example_2_three_ray_redundant/`
- **Scenario:** Over-determined 3-ray intersection to P1 at 99% confidence.
- **Expected Result:** Computes least-squares position and 99% error ellipse for P1.
- **Parameters (`example.json`):**
  ```json
  {
    "SIGHTINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_2_three_ray_redundant/inputs/sightings_p1_3rays.json",
    "TARGET": "P1",
    "SIGMA_AZIMUTH": 0.001388888888888889,
    "CONFIDENCE": 0.99,
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_2_three_ray_redundant/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_2_three_ray_redundant/outputs/report.html"
  }
  ```

#### Example 3: Four-ray forward intersection to target P2 from all four control pillars (A, B, C, D)
- **Folder:** `01_total_station/totalstation_intersection/example_3_four_ray_target_p2/`
- **Scenario:** Intersects 4 azimuth rays onto target P2 with 2 degrees of freedom.
- **Expected Result:** Recovers exact P2 coordinates with 4-ray redundancy.
- **Parameters (`example.json`):**
  ```json
  {
    "SIGHTINGS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_3_four_ray_target_p2/inputs/sightings_p2_4rays.json",
    "TARGET": "P2",
    "SIGMA_AZIMUTH": 0.0008333333333333334,
    "CONFIDENCE": 0.95,
    "OUTPUT_POSITION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_3_four_ray_target_p2/outputs/position.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_intersection/example_3_four_ray_target_p2/outputs/report.html"
  }
  ```

### GeoComp ▸ Total Station ▸ Classical network (`geocomp:totalstation_network`)

#### Example 1: 2D planimetric classical network adjustment (RD-01) with inner constraint
- **Folder:** `01_total_station/totalstation_network/example_1_2d_inner_constraint/`
- **Scenario:** Adjusts the 3-station RD-01 triangle in 2D under minimum-trace inner constraint.
- **Expected Result:** Adjusts RD-01 in 2D with 4 degrees of freedom and writes network.json + solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/inputs/reduced.json",
    "APPROXIMATE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/inputs/approximate.json",
    "DIMENSION": 0,
    "DATUM": 1,
    "CRS": "EPSG:31982",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/outputs/network.json",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/outputs/report.html",
    "OUTPUT_STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_1_2d_inner_constraint/outputs/stations.csv"
  }
  ```

#### Example 2: 3D classical network adjustment preserving instrument and target heights (DIMENSION=1)
- **Folder:** `01_total_station/totalstation_network/example_2_3d_network_adjustment/`
- **Scenario:** Simultaneously adjusts horizontal directions, zenith angles, and slope distances in 3D.
- **Expected Result:** Produces 3D station coordinates and full 3D covariance matrices.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/inputs/reduced.json",
    "APPROXIMATE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/inputs/approximate.json",
    "DIMENSION": 1,
    "DATUM": 1,
    "CRS": "EPSG:31982",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/outputs/network.json",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/outputs/report.html",
    "OUTPUT_STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_2_3d_network_adjustment/outputs/stations.csv"
  }
  ```

#### Example 3: 1D height network adjustment (DIMENSION=2) reading approximate coordinates from CSV
- **Folder:** `01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/`
- **Scenario:** Adjusts trigonometric heights in 1D using a CSV table of approximate station coordinates.
- **Expected Result:** Adjusts 1D heights agreeing with the 3D vertical solution.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/inputs/reduced.json",
    "APPROXIMATE": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/inputs/approximate.csv",
    "DIMENSION": 2,
    "DATUM": 1,
    "CRS": "EPSG:31982",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/outputs/network.json",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/outputs/report.html",
    "OUTPUT_STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_network/example_3_1d_vertical_network_csv_approx/outputs/stations.csv"
  }
  ```

### GeoComp ▸ Total Station ▸ Trigonometric levelling (`geocomp:totalstation_trig_levelling`)

#### Example 1: Radial trigonometric levelling (MODE=0) with Earth curvature and refraction (k=0.13)
- **Folder:** `01_total_station/totalstation_trig_levelling/example_1_radial_curvature_refraction/`
- **Scenario:** Computes height differences from single-ended and reciprocal zenith angles across all setups.
- **Expected Result:** Computes radial height differences with curvature and refraction corrections.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_1_radial_curvature_refraction/inputs/reductions.json",
    "MODE": 0,
    "REFRACTION": 0.13,
    "REFRACTION_SIGMA": 0.05,
    "OUTPUT_HEIGHTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_1_radial_curvature_refraction/outputs/heights.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_1_radial_curvature_refraction/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_1_radial_curvature_refraction/outputs/differences.csv"
  }
  ```

#### Example 2: Balanced leap-frog trigonometric levelling from midpoint station L (A -> D)
- **Folder:** `01_total_station/totalstation_trig_levelling/example_2_balanced_leapfrog/`
- **Scenario:** Station L stands midway between A and D so curvature and refraction cancel out.
- **Expected Result:** Recovers exact height difference A -> D (+1.500 m) with 1 leap-frog pair.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_2_balanced_leapfrog/inputs/leapfrog_reductions.json",
    "MODE": 1,
    "OUTPUT_HEIGHTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_2_balanced_leapfrog/outputs/heights.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_2_balanced_leapfrog/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_2_balanced_leapfrog/outputs/differences.csv"
  }
  ```

#### Example 3: Radial trigonometric levelling with high refraction (k=0.18) and custom prism height
- **Folder:** `01_total_station/totalstation_trig_levelling/example_3_custom_refraction_and_heights/`
- **Scenario:** Evaluates vertical differences under strong thermal inversion refraction (k=0.18 ± 0.08).
- **Expected Result:** Writes height differences and propagates refraction uncertainty.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_3_custom_refraction_and_heights/inputs/reductions.json",
    "MODE": 0,
    "INSTRUMENT_HEIGHT": 1.6,
    "TARGET_HEIGHT": 1.6,
    "REFRACTION": 0.18,
    "REFRACTION_SIGMA": 0.08,
    "OUTPUT_HEIGHTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_3_custom_refraction_and_heights/outputs/heights.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_3_custom_refraction_and_heights/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_trig_levelling/example_3_custom_refraction_and_heights/outputs/differences.csv"
  }
  ```

### GeoComp ▸ Total Station ▸ 3D radiation (`geocomp:totalstation_radiation`)

#### Example 1: 3D radiation of detail points P1 and P2 orienting automatically from known stations
- **Folder:** `01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/`
- **Scenario:** Radiates non-control detail points (P1, P2) from setup A using backsights to known stations B and D.
- **Expected Result:** Recovers exact 3D coordinates of detail points P1 and P2 with full 3x3 covariance.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/inputs/reductions.json",
    "STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/inputs/known.json",
    "INSTRUMENT_HEIGHT": 1.5,
    "TARGET_HEIGHT": 1.5,
    "CORRELATION": 0.0,
    "OUTPUT_POINTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/outputs/points.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_1_detail_points_from_known_control/outputs/points.csv"
  }
  ```

#### Example 2: 3D radiation using pre-computed station orientation constants (orientations.json)
- **Folder:** `01_total_station/totalstation_radiation/example_2_with_explicit_orientations/`
- **Scenario:** Supplies explicit orientation angles for occupied stations via orientations.json.
- **Expected Result:** Radiates P1 and P2 using pre-computed orientations.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/inputs/reductions.json",
    "STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/inputs/known.json",
    "ORIENTATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/inputs/orientations.json",
    "INSTRUMENT_HEIGHT": 1.5,
    "TARGET_HEIGHT": 1.5,
    "OUTPUT_POINTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/outputs/points.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_2_with_explicit_orientations/outputs/points.csv"
  }
  ```

#### Example 3: 3D radiation detecting a 0.50 m displaced backsight control station (B)
- **Folder:** `01_total_station/totalstation_radiation/example_3_displaced_control_warning/`
- **Scenario:** Tests orientation spread warning when known station B is displaced by 0.50 m.
- **Expected Result:** Radiates detail points and warns that backsight control disagrees with recorded coordinates.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_3_displaced_control_warning/inputs/reductions.json",
    "STATIONS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_3_displaced_control_warning/inputs/displaced_known.json",
    "CORRELATION": 0.3,
    "OUTPUT_POINTS": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_3_displaced_control_warning/outputs/points.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_3_displaced_control_warning/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/01_total_station/totalstation_radiation/example_3_displaced_control_warning/outputs/points.csv"
  }
  ```

---
## Level (`02_level`)

### GeoComp ▸ Level ▸ Import levelling field book (`geocomp:levelling_import`)

#### Example 1: Balanced 3-setup differential levelling line (RD-04) with level profile
- **Folder:** `02_level/levelling_import/example_1_balanced_line/`
- **Scenario:** Imports 3 setups along a single levelling line using mapping.json and profiles.json.
- **Expected Result:** Imports 3 setups and 1 line with 0 rejected rows.
- **Parameters (`example.json`):**
  ```json
  {
    "BOOK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_1_balanced_line/inputs/book.csv",
    "MAPPING": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_1_balanced_line/inputs/mapping.json",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_1_balanced_line/inputs/profiles.json",
    "OUTPUT_SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_1_balanced_line/outputs/setups.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_1_balanced_line/outputs/report.html"
  }
  ```

#### Example 2: Multi-line closed levelling loop field book with line column mapping
- **Folder:** `02_level/levelling_import/example_2_four_line_loop/`
- **Scenario:** Imports 4 connected levelling lines forming a closed loop around benchmarks.
- **Expected Result:** Groups setups into 4 distinct levelling lines.
- **Parameters (`example.json`):**
  ```json
  {
    "BOOK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_2_four_line_loop/inputs/loop_book.csv",
    "MAPPING": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_2_four_line_loop/inputs/loop_mapping.json",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_2_four_line_loop/inputs/profiles.json",
    "OUTPUT_SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_2_four_line_loop/outputs/setups.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_2_four_line_loop/outputs/report.html"
  }
  ```

#### Example 3: Radial setup with intermediate foresights (IS) and explicit staff-reading sigma
- **Folder:** `02_level/levelling_import/example_3_extreme_sights_default_sigma/`
- **Scenario:** Imports a setup with backsight BS, foresight FS, and intermediate sights IS using SIGMA_READING=0.0005 m.
- **Expected Result:** Imports multi-foresight setup with 0.5 mm staff reading standard deviation.
- **Parameters (`example.json`):**
  ```json
  {
    "BOOK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_3_extreme_sights_default_sigma/inputs/extreme_book.csv",
    "MAPPING": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_3_extreme_sights_default_sigma/inputs/mapping.json",
    "SIGMA_READING": 0.0005,
    "STADIA_FACTOR": 100.0,
    "OUTPUT_SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_3_extreme_sights_default_sigma/outputs/setups.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_import/example_3_extreme_sights_default_sigma/outputs/report.html"
  }
  ```

### GeoComp ▸ Level ▸ Equal sights (`geocomp:levelling_equal_sights`)

#### Example 1: Balanced equal-sights reduction recovering exact height difference
- **Folder:** `02_level/levelling_equal_sights/example_1_balanced_line/`
- **Scenario:** Reduces balanced setups with zero sight-length imbalance.
- **Expected Result:** Produces reduced line with 0.0 m sight imbalance.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_1_balanced_line/inputs/setups.json",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_1_balanced_line/inputs/profiles.json",
    "OUTPUT_REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_1_balanced_line/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_1_balanced_line/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_1_balanced_line/outputs/lines.csv"
  }
  ```

#### Example 2: Equal-sights reduction of all 4 lines in a closed levelling loop
- **Folder:** `02_level/levelling_equal_sights/example_2_four_line_loop_reduction/`
- **Scenario:** Reduces all 4 lines of the RD-04 loop into a single reductions document.
- **Expected Result:** Reduces 4 lines (LINE_COUNT=4) ready for loop closure and network adjustment.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_2_four_line_loop_reduction/inputs/loop_setups.json",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_2_four_line_loop_reduction/inputs/profiles.json",
    "OUTPUT_REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_2_four_line_loop_reduction/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_2_four_line_loop_reduction/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_2_four_line_loop_reduction/outputs/lines.csv"
  }
  ```

#### Example 3: Imbalanced sights reduced with collimation correction and strict imbalance limits
- **Folder:** `02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/`
- **Scenario:** Applies collimation angle (5e-5 rad) across unbalanced sights and checks sight-imbalance limits.
- **Expected Result:** Applies collimation correction and flags sight imbalance in the HTML report.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/inputs/imbalanced_setups.json",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/inputs/profiles.json",
    "COLLIMATION": 5e-05,
    "COLLIMATION_SIGMA": 1e-05,
    "MAX_SIGHT_LENGTH": 50.0,
    "MAX_SIGHT_IMBALANCE": 2.0,
    "MAX_ACCUMULATED_IMBALANCE": 5.0,
    "OUTPUT_REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/outputs/reduced.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equal_sights/example_3_imbalanced_line_with_collimation/outputs/lines.csv"
  }
  ```

### GeoComp ▸ Level ▸ Equidistant sights (`geocomp:levelling_equidistant_sights`)

#### Example 1: Reciprocal river-crossing levelling cancelling refraction and collimation
- **Folder:** `02_level/levelling_equidistant_sights/example_1_reciprocal_crossing/`
- **Scenario:** Averages opposite-bank setups to cancel 12 mm refraction error.
- **Expected Result:** Cancels refraction error and recovers true crossing height difference.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_1_reciprocal_crossing/inputs/crossing_setups.json",
    "INFLATION": 2.0,
    "DISCREPANCY_TOLERANCE": 0.03,
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_1_reciprocal_crossing/outputs/crossing.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_1_reciprocal_crossing/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_1_reciprocal_crossing/outputs/crossings.csv"
  }
  ```

#### Example 2: Reciprocal crossing with 3.5x variance inflation factor
- **Folder:** `02_level/levelling_equidistant_sights/example_2_high_variance_inflation/`
- **Scenario:** Inflates crossing uncertainty by 3.5x to account for long-sight atmospheric turbulence.
- **Expected Result:** Outputs crossing height difference with 3.5x variance inflation.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_2_high_variance_inflation/inputs/crossing_setups.json",
    "INFLATION": 3.5,
    "DISCREPANCY_TOLERANCE": 0.03,
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_2_high_variance_inflation/outputs/crossing.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_2_high_variance_inflation/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_2_high_variance_inflation/outputs/crossings.csv"
  }
  ```

#### Example 3: Reciprocal crossing with tight 5 mm discrepancy tolerance flagging the 24 mm spread
- **Folder:** `02_level/levelling_equidistant_sights/example_3_discrepancy_exceeded/`
- **Scenario:** Checks diagnostic flagging when bank-to-bank spread (24 mm) exceeds DISCREPANCY_TOLERANCE (5 mm).
- **Expected Result:** Flags the 24 mm forward/reverse discrepancy against the 5 mm tolerance.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_3_discrepancy_exceeded/inputs/crossing_setups.json",
    "INFLATION": 2.0,
    "DISCREPANCY_TOLERANCE": 0.005,
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_3_discrepancy_exceeded/outputs/crossing.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_3_discrepancy_exceeded/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_equidistant_sights/example_3_discrepancy_exceeded/outputs/crossings.csv"
  }
  ```

### GeoComp ▸ Level ▸ Extreme sights (`geocomp:levelling_extreme_sights`)

#### Example 1: Correlated height differences from a multi-foresight setup (BM1 -> BM3, S1, S2)
- **Folder:** `02_level/levelling_extreme_sights/example_1_multiple_foresights/`
- **Scenario:** Computes correlated height differences sharing a common backsight reading at BM1.
- **Expected Result:** Produces 3 correlated height differences with full covariance matrix.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_1_multiple_foresights/inputs/extreme_setups.json",
    "ONLY_MULTIPLE": true,
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_1_multiple_foresights/inputs/profiles.json",
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_1_multiple_foresights/outputs/differences.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_1_multiple_foresights/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_1_multiple_foresights/outputs/differences.csv"
  }
  ```

#### Example 2: Extreme-sights reduction including single-foresight setups (ONLY_MULTIPLE=False)
- **Folder:** `02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/`
- **Scenario:** Runs extreme-sights reduction across standard single-foresight setups.
- **Expected Result:** Extracts per-setup height differences for all 3 setups.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/inputs/balanced_setups.json",
    "ONLY_MULTIPLE": false,
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/inputs/profiles.json",
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/outputs/differences.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_2_include_single_foresight_setups/outputs/differences.csv"
  }
  ```

#### Example 3: Multi-foresight setup checked against strict 20 m sight-length and 2 m imbalance limits
- **Folder:** `02_level/levelling_extreme_sights/example_3_strict_sight_limits/`
- **Scenario:** Enforces MAX_SIGHT_LENGTH=20 m and MAX_SIGHT_IMBALANCE=2 m on radial sights.
- **Expected Result:** Computes correlated differences and logs sight-length/imbalance warnings.
- **Parameters (`example.json`):**
  ```json
  {
    "SETUPS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_3_strict_sight_limits/inputs/extreme_setups.json",
    "ONLY_MULTIPLE": true,
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_3_strict_sight_limits/inputs/profiles.json",
    "MAX_SIGHT_LENGTH": 20.0,
    "MAX_SIGHT_IMBALANCE": 2.0,
    "OUTPUT_DIFFERENCES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_3_strict_sight_limits/outputs/differences.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_3_strict_sight_limits/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_extreme_sights/example_3_strict_sight_limits/outputs/differences.csv"
  }
  ```

### GeoComp ▸ Level ▸ Closures and tolerances (`geocomp:levelling_closures`)

#### Example 1: Closed 4-line loop closure check (k = 8 mm/sqrt(km)) distributed by line length
- **Folder:** `02_level/levelling_closures/example_1_loop_closure_by_length/`
- **Scenario:** Checks loop misclosure against 8 mm/sqrt(km) tolerance and distributes proportionally to length.
- **Expected Result:** Passes tolerance and distributes loop misclosure across the 4 lines.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_1_loop_closure_by_length/inputs/loop_reduced.json",
    "MODE": 0,
    "TOLERANCE_COEFFICIENT": 0.008,
    "WEIGHTING": 0,
    "LOOP_ID": "RD04_Loop",
    "OUTPUT_CLOSURES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_1_loop_closure_by_length/outputs/closures.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_1_loop_closure_by_length/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_1_loop_closure_by_length/outputs/distribution.csv"
  }
  ```

#### Example 2: Single levelling line checked against known benchmark difference distributing by setups
- **Folder:** `02_level/levelling_closures/example_2_line_against_known_difference/`
- **Scenario:** Compares reduced line against known height difference (+0.4 mm offset) with WEIGHTING=1.
- **Expected Result:** Evaluates +0.4 mm misclosure against known benchmark height difference.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_2_line_against_known_difference/inputs/line_reduced.json",
    "MODE": 1,
    "KNOWN_DIFFERENCE": 3.7496000000000005,
    "KNOWN_SIGMA": 0.0002,
    "TOLERANCE_COEFFICIENT": 0.008,
    "WEIGHTING": 1,
    "LOOP_ID": "Line_Check",
    "OUTPUT_CLOSURES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_2_line_against_known_difference/outputs/closures.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_2_line_against_known_difference/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_2_line_against_known_difference/outputs/distribution.csv"
  }
  ```

#### Example 3: Loop closure failing an ultra-tight 0.05 mm/sqrt(km) tolerance
- **Folder:** `02_level/levelling_closures/example_3_failing_tight_tolerance/`
- **Scenario:** Tests tolerance failure reporting when TOLERANCE_COEFFICIENT is set to 0.00005 m/sqrt(km).
- **Expected Result:** Flags the loop as exceeding permissible misclosure in closures.json.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_3_failing_tight_tolerance/inputs/loop_reduced.json",
    "MODE": 0,
    "TOLERANCE_COEFFICIENT": 5e-05,
    "WEIGHTING": 0,
    "LOOP_ID": "Special_Order_Loop",
    "OUTPUT_CLOSURES": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_3_failing_tight_tolerance/outputs/closures.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_3_failing_tight_tolerance/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_closures/example_3_failing_tight_tolerance/outputs/distribution.csv"
  }
  ```

### GeoComp ▸ Level ▸ Levelling network adjustment (`geocomp:levelling_network`)

#### Example 1: Constrained 1D levelling loop adjustment holding BM1 = 100.000 m
- **Folder:** `02_level/levelling_network/example_1_constrained_benchmark_loop/`
- **Scenario:** Least-squares adjustment of 4-line loop weighted by line length holding BM1 fixed.
- **Expected Result:** Adjusts benchmark heights around the loop with 1 degree of freedom.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_1_constrained_benchmark_loop/inputs/loop_reduced.json",
    "BENCHMARKS": "BM1=100.0",
    "WEIGHTING": 0,
    "SIGMA_PER_KM": 0.001,
    "FREE": false,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_1_constrained_benchmark_loop/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_1_constrained_benchmark_loop/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_1_constrained_benchmark_loop/outputs/heights.csv",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_1_constrained_benchmark_loop/outputs/network.json"
  }
  ```

#### Example 2: Free inner-constraint levelling network weighted by number of setups
- **Folder:** `02_level/levelling_network/example_2_free_network_by_setups/`
- **Scenario:** Solves a free 1D levelling network (FREE=True) weighted by setup count.
- **Expected Result:** Produces inner-constraint 1D vertical solution.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_2_free_network_by_setups/inputs/loop_reduced.json",
    "BENCHMARKS": "BM1=100.0",
    "WEIGHTING": 1,
    "SIGMA_PER_SETUP": 0.0005,
    "FREE": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_2_free_network_by_setups/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_2_free_network_by_setups/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_2_free_network_by_setups/outputs/heights.csv",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_2_free_network_by_setups/outputs/network.json"
  }
  ```

#### Example 3: Levelling network with tolerance gate (k=8 mm/sqrt(km)), ADJUST_FAILING=True, and 99% confidence
- **Folder:** `02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/`
- **Scenario:** Adjusts loop with pre-adjustment tolerance checking and Baarda data snooping.
- **Expected Result:** Evaluates line tolerances and completes 99% confidence 1D adjustment.
- **Parameters (`example.json`):**
  ```json
  {
    "REDUCTIONS": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/inputs/loop_reduced.json",
    "BENCHMARKS": "BM1=100.0",
    "WEIGHTING": 0,
    "SIGMA_PER_KM": 0.001,
    "CONFIDENCE": 0.99,
    "TOLERANCE_COEFFICIENT": 0.008,
    "ADJUST_FAILING": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/outputs/heights.csv",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/02_level/levelling_network/example_3_with_tolerance_gate_and_snooping/outputs/network.json"
  }
  ```

---
## GNSS (`03_gnss`)

### GeoComp ▸ GNSS ▸ Scan sessions (`geocomp:gnss_scan_sessions`)

#### Example 1: Two-station static/kinematic RINEX session (BASE + ROVE) with broadcast nav
- **Folder:** `03_gnss/gnss_scan_sessions/example_1_two_station_session/`
- **Scenario:** Scans folder containing base.05o, rover.05o, and brdc.05n on 2005-05-20.
- **Expected Result:** Detects 2 observation stations (BASE, ROVE), 1 navigation file, and temporal overlap.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_1_two_station_session/inputs/rinex",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_1_two_station_session/outputs/sessions.json"
  }
  ```

#### Example 2: Three-station simultaneous RINEX campaign (BASE, ROVE, AUX1)
- **Folder:** `03_gnss/gnss_scan_sessions/example_2_three_station_network_session/`
- **Scenario:** Scans multi-station campaign folder with 3 simultaneous receivers.
- **Expected Result:** Identifies all 3 stations (AUX1, BASE, ROVE) in the session summary.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_2_three_station_network_session/inputs/rinex",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_2_three_station_network_session/outputs/sessions.json"
  }
  ```

#### Example 3: Single-receiver standalone/PPP RINEX folder (ROVE only)
- **Folder:** `03_gnss/gnss_scan_sessions/example_3_single_receiver_ppp_session/`
- **Scenario:** Scans a folder with a single rover receiver and navigation file (no base station).
- **Expected Result:** Reports 1 observation file (ROVE) ready for absolute positioning.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_3_single_receiver_ppp_session/inputs/rinex_single",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_scan_sessions/example_3_single_receiver_ppp_session/outputs/sessions.json"
  }
  ```

### GeoComp ▸ GNSS ▸ Download products (`geocomp:gnss_download_products`)

#### Example 1: Download final SP3 orbit and GPS broadcast navigation for a RINEX folder's dates
- **Folder:** `03_gnss/gnss_download_products/example_1_from_rinex_folder_final/`
- **Scenario:** Infers GPS week 1323 / DOY 140 (2005-05-20) from RINEX headers and fetches SP3 + BRDC.
- **Expected Result:** Downloads igs13235.sp3 and brdc1400.05n into products/ and writes manifest.json.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_1_from_rinex_folder_final/inputs/rinex",
    "PRODUCTS": [
      0,
      1
    ],
    "LATENCY": 0,
    "CHECK_ONLY": false,
    "OUTPUT_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_1_from_rinex_folder_final/outputs/products",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_1_from_rinex_folder_final/outputs/manifest.json"
  }
  ```

#### Example 2: Explicit date range query for Rapid SP3 + GLONASS navigation
- **Folder:** `03_gnss/gnss_download_products/example_2_explicit_date_range_rapid/`
- **Scenario:** Requests Rapid orbits (igr) and GLONASS broadcast navigation for 2005-05-20.
- **Expected Result:** Fetches rapid orbit and GLONASS navigation files for 2005-05-20.
- **Parameters (`example.json`):**
  ```json
  {
    "FIRST_DAY": "2005-05-20",
    "LAST_DAY": "2005-05-20",
    "PRODUCTS": [
      0,
      2
    ],
    "LATENCY": 1,
    "CHECK_ONLY": false,
    "OUTPUT_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_2_explicit_date_range_rapid/outputs/products",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_2_explicit_date_range_rapid/outputs/manifest.json"
  }
  ```

#### Example 3: Dry-run availability check (CHECK_ONLY=True) without downloading payloads
- **Folder:** `03_gnss/gnss_download_products/example_3_check_availability_only/`
- **Scenario:** Probes product archive availability for SP3 + GPS nav without copying files.
- **Expected Result:** Verifies AVAILABLE=2, MISSING=0 and writes availability manifest.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_3_check_availability_only/inputs/rinex",
    "PRODUCTS": [
      0,
      1
    ],
    "LATENCY": 0,
    "CHECK_ONLY": true,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_download_products/example_3_check_availability_only/outputs/manifest.json"
  }
  ```

### GeoComp ▸ GNSS ▸ Absolute ▸ Absolute — Static (`geocomp:gnss_absolute_static`)

#### Example 1: Absolute static point positioning of ROVE with 15° elevation mask
- **Folder:** `03_gnss/gnss_absolute_static/example_1_default_rover_static/`
- **Scenario:** Runs static single-point/PPP positioning on station ROVE with 15° mask.
- **Expected Result:** Produces static .pos solution and quality summary JSON.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_1_default_rover_static/inputs/rinex",
    "ROVER_STATION": "ROVE",
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_1_default_rover_static/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_1_default_rover_static/outputs/quality.json"
  }
  ```

#### Example 2: Absolute static positioning of BASE with 25° multipath-rejection mask
- **Folder:** `03_gnss/gnss_absolute_static/example_2_high_elevation_mask_25deg/`
- **Scenario:** Processes station BASE in static mode with an elevated 25° cutoff angle.
- **Expected Result:** Produces static .pos solution and quality summary JSON.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_2_high_elevation_mask_25deg/inputs/rinex",
    "ROVER_STATION": "BASE",
    "ELEVATION_MASK": 25.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_2_high_elevation_mask_25deg/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_2_high_elevation_mask_25deg/outputs/quality.json"
  }
  ```

#### Example 3: Absolute static positioning with custom RTKLIB configuration file
- **Folder:** `03_gnss/gnss_absolute_static/example_3_custom_rtklib_conf/`
- **Scenario:** Uses an explicit RTKLIB .conf file overriding ionosphere/troposphere options.
- **Expected Result:** Produces static .pos solution and quality summary JSON.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_3_custom_rtklib_conf/inputs/rinex",
    "ROVER_STATION": "ROVE",
    "ELEVATION_MASK": 10.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_3_custom_rtklib_conf/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_3_custom_rtklib_conf/outputs/quality.json",
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_static/example_3_custom_rtklib_conf/inputs/custom_static.conf"
  }
  ```

### GeoComp ▸ GNSS ▸ Absolute ▸ Absolute — Kinematic (`geocomp:gnss_absolute_kinematic`)

#### Example 1: Absolute kinematic trajectory of ROVE with default settings
- **Folder:** `03_gnss/gnss_absolute_kinematic/example_1_rover_kinematic_trajectory/`
- **Scenario:** Computes epoch-by-epoch standalone kinematic trajectory for station ROVE.
- **Expected Result:** Produces epoch-by-epoch kinematic .pos file and quality metrics.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_1_rover_kinematic_trajectory/inputs/rinex",
    "ROVER_STATION": "ROVE",
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_1_rover_kinematic_trajectory/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_1_rover_kinematic_trajectory/outputs/quality.json"
  }
  ```

#### Example 2: Absolute kinematic trajectory with low 10° elevation mask
- **Folder:** `03_gnss/gnss_absolute_kinematic/example_2_low_mask_10deg/`
- **Scenario:** Includes low-elevation satellites down to 10° for urban/canopy kinematic tracking.
- **Expected Result:** Produces epoch-by-epoch kinematic .pos file and quality metrics.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_2_low_mask_10deg/inputs/rinex",
    "ROVER_STATION": "ROVE",
    "ELEVATION_MASK": 10.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_2_low_mask_10deg/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_2_low_mask_10deg/outputs/quality.json"
  }
  ```

#### Example 3: Absolute kinematic positioning with explicit RTKLIB configuration
- **Folder:** `03_gnss/gnss_absolute_kinematic/example_3_custom_kinematic_conf/`
- **Scenario:** Runs kinematic positioning driven by a custom RTKLIB configuration file.
- **Expected Result:** Produces epoch-by-epoch kinematic .pos file and quality metrics.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_3_custom_kinematic_conf/inputs/rinex",
    "ROVER_STATION": "ROVE",
    "ELEVATION_MASK": 20.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_3_custom_kinematic_conf/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_3_custom_kinematic_conf/outputs/quality.json",
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_absolute_kinematic/example_3_custom_kinematic_conf/inputs/custom_kinematic.conf"
  }
  ```

### GeoComp ▸ GNSS ▸ Relative ▸ Relative — Static (`geocomp:gnss_relative_static`)

#### Example 1: Relative static baseline BASE -> ROVE in SIRGAS2000 (15° mask)
- **Folder:** `03_gnss/gnss_relative_static/example_1_baseline_base_to_rove_sirgas/`
- **Scenario:** Carrier-phase static baseline processing between BASE and ROVE in SIRGAS2000.
- **Expected Result:** Solves carrier-phase static baseline BASE -> ROVE with fixed ambiguities (Q=1).
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_1_baseline_base_to_rove_sirgas/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 7,
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_1_baseline_base_to_rove_sirgas/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_1_baseline_base_to_rove_sirgas/outputs/quality.json"
  }
  ```

#### Example 2: Relative static baseline BASE -> ROVE in ITRF2020 with 20° mask
- **Folder:** `03_gnss/gnss_relative_static/example_2_baseline_itrf2020_20deg/`
- **Scenario:** Static baseline solution expressed in ITRF2020 with 20° elevation cutoff.
- **Expected Result:** Solves carrier-phase static baseline BASE -> ROVE with fixed ambiguities (Q=1).
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_2_baseline_itrf2020_20deg/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 2,
    "ELEVATION_MASK": 20.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_2_baseline_itrf2020_20deg/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_2_baseline_itrf2020_20deg/outputs/quality.json"
  }
  ```

#### Example 3: Relative static baseline with custom L1+L2 RTKLIB configuration file
- **Folder:** `03_gnss/gnss_relative_static/example_3_custom_static_carrier_conf/`
- **Scenario:** Uses an explicit RTKLIB static carrier-phase configuration file.
- **Expected Result:** Solves carrier-phase static baseline BASE -> ROVE with fixed ambiguities (Q=1).
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_3_custom_static_carrier_conf/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 1,
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_3_custom_static_carrier_conf/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_3_custom_static_carrier_conf/outputs/quality.json",
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_static/example_3_custom_static_carrier_conf/inputs/static_l1l2.conf"
  }
  ```

### GeoComp ▸ GNSS ▸ Relative ▸ Relative — Kinematic (`geocomp:gnss_relative_kinematic`)

#### Example 1: Post-processed kinematic (PPK) baseline BASE -> ROVE in SIRGAS2000
- **Folder:** `03_gnss/gnss_relative_kinematic/example_1_kinematic_ppk_sirgas2000/`
- **Scenario:** Relative kinematic carrier-phase trajectory of ROVE referenced to BASE.
- **Expected Result:** Produces relative kinematic .pos trajectory and quality summary.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_1_kinematic_ppk_sirgas2000/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 7,
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_1_kinematic_ppk_sirgas2000/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_1_kinematic_ppk_sirgas2000/outputs/quality.json"
  }
  ```

#### Example 2: Relative kinematic trajectory in ITRF2014 with 25° elevation mask
- **Folder:** `03_gnss/gnss_relative_kinematic/example_2_kinematic_itrf2014_25deg/`
- **Scenario:** PPK solution in ITRF2014 with high 25° elevation mask.
- **Expected Result:** Produces relative kinematic .pos trajectory and quality summary.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_2_kinematic_itrf2014_25deg/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 3,
    "ELEVATION_MASK": 25.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_2_kinematic_itrf2014_25deg/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_2_kinematic_itrf2014_25deg/outputs/quality.json"
  }
  ```

#### Example 3: Relative kinematic PPK with custom continuous-AR RTKLIB configuration
- **Folder:** `03_gnss/gnss_relative_kinematic/example_3_kinematic_custom_conf/`
- **Scenario:** Runs PPK with explicit RTKLIB configuration file.
- **Expected Result:** Produces relative kinematic .pos trajectory and quality summary.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_3_kinematic_custom_conf/inputs/rinex",
    "BASE_STATION": "BASE",
    "ROVER_STATION": "ROVE",
    "FRAME": 1,
    "ELEVATION_MASK": 15.0,
    "KEEP_WORK_DIR": true,
    "OUTPUT_POS": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_3_kinematic_custom_conf/outputs/solution.pos",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_3_kinematic_custom_conf/outputs/quality.json",
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_relative_kinematic/example_3_kinematic_custom_conf/inputs/kinematic_ppk.conf"
  }
  ```

### GeoComp ▸ GNSS ▸ Build baselines (`geocomp:gnss_build_baselines`)

#### Example 1: Build 3D baseline vector and Network JSON from .pos solution in SIRGAS2000
- **Folder:** `03_gnss/gnss_build_baselines/example_1_single_baseline_sirgas2000/`
- **Scenario:** Extracts ECEF baseline vector (dX, dY, dZ) and 3x3 covariance matrix from base_rove.pos.
- **Expected Result:** Builds baseline BASE -> ROVE with full 3x3 covariance in SIRGAS2000.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_1_single_baseline_sirgas2000/inputs/pos",
    "BASE_HEIGHT": 0.0,
    "ROVER_HEIGHT": 0.0,
    "INDEPENDENT_ONLY": true,
    "FRAME": 6,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_1_single_baseline_sirgas2000/outputs/baselines.json",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_1_single_baseline_sirgas2000/outputs/network.json"
  }
  ```

#### Example 2: Baseline extraction with unequal tripod antenna heights (Base 1.42 m, Rover 1.85 m)
- **Folder:** `03_gnss/gnss_build_baselines/example_2_antenna_height_reduction/`
- **Scenario:** Reduces baseline from antenna phase centre to monument marks with 3 mm height uncertainty.
- **Expected Result:** Applies vertical antenna height reduction along local ellipsoid normal and inflates vertical variance.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_2_antenna_height_reduction/inputs/pos",
    "BASE_HEIGHT": 1.42,
    "ROVER_HEIGHT": 1.85,
    "HEIGHT_SIGMA": 0.003,
    "INDEPENDENT_ONLY": true,
    "FRAME": 1,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_2_antenna_height_reduction/outputs/baselines.json",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_2_antenna_height_reduction/outputs/network.json"
  }
  ```

#### Example 3: Multi-baseline session (BASE->ROVE, BASE->AUX1) with per-station antenna matrix
- **Folder:** `03_gnss/gnss_build_baselines/example_3_multi_baseline_all_vectors/`
- **Scenario:** Extracts multiple baselines using per-station antenna height table (INDEPENDENT_ONLY=False).
- **Expected Result:** Builds 3-station GNSS network (BASE, ROVE, AUX1) with station-specific antenna offsets.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_3_multi_baseline_all_vectors/inputs/pos",
    "STATION_HEIGHTS": [
      "BASE",
      "1.500",
      "ROVE",
      "1.600",
      "AUX1",
      "1.550"
    ],
    "INDEPENDENT_ONLY": false,
    "FRAME": 2,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_3_multi_baseline_all_vectors/outputs/baselines.json",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_build_baselines/example_3_multi_baseline_all_vectors/outputs/network.json"
  }
  ```

### GeoComp ▸ GNSS ▸ Batch processing (`geocomp:gnss_batch`)

#### Example 1: Batch Relative — Static processing of all rovers (ROVE, AUX1) from BASE
- **Folder:** `03_gnss/gnss_batch/example_1_relative_static_batch/`
- **Scenario:** Automatically pairs BASE against every rover in the session folder in static mode.
- **Expected Result:** Processes both baselines (BASE->AUX1, BASE->ROVE) and writes batch_report.json.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_1_relative_static_batch/inputs/rinex",
    "BASE_STATION": "BASE",
    "FRAME": 7,
    "PROFILE": 0,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_1_relative_static_batch/outputs/batch_report.json"
  }
  ```

#### Example 2: Batch Relative — Kinematic processing in ITRF2020
- **Folder:** `03_gnss/gnss_batch/example_2_relative_kinematic_batch/`
- **Scenario:** Runs batch relative kinematic processing for all rovers referenced to BASE.
- **Expected Result:** Completes batch kinematic run and summarizes fix ratios in batch_report.json.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_2_relative_kinematic_batch/inputs/rinex",
    "BASE_STATION": "BASE",
    "FRAME": 2,
    "PROFILE": 1,
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_2_relative_kinematic_batch/outputs/batch_report.json"
  }
  ```

#### Example 3: Batch Absolute — Static positioning across all stations in folder
- **Folder:** `03_gnss/gnss_batch/example_3_absolute_static_batch/`
- **Scenario:** Processes every station (BASE and ROVE) independently in Absolute — Static mode.
- **Expected Result:** Runs standalone static positioning on every receiver in the folder.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_3_absolute_static_batch/inputs/rinex",
    "PROFILE": 2,
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_3_absolute_static_batch/inputs/batch_abs.conf",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_batch/example_3_absolute_static_batch/outputs/batch_report.json"
  }
  ```

### GeoComp ▸ GNSS ▸ Compare configurations (`geocomp:gnss_compare_configurations`)

#### Example 1: Elevation mask sensitivity sweep (10°, 15°, 20°, 25°)
- **Folder:** `03_gnss/gnss_compare_configurations/example_1_elevation_mask_sweep/`
- **Scenario:** Runs RTKLIB across 4 elevation masks and compares coordinate repeatability and fix ratio.
- **Expected Result:** Compares 4 elevation masks and outputs statistical significance test results.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_1_elevation_mask_sweep/inputs/rinex",
    "MASKS": "10,15,20,25",
    "CONFIDENCE": 0.95,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_1_elevation_mask_sweep/outputs/comparison.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_1_elevation_mask_sweep/outputs/comparison.csv",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_1_elevation_mask_sweep/outputs/comparison.json"
  }
  ```

#### Example 2: Extreme elevation mask comparison (15°, 30°, 40°) at 99% confidence
- **Folder:** `03_gnss/gnss_compare_configurations/example_2_high_cutoff_comparison/`
- **Scenario:** Evaluates dilution of precision and coordinate shift under severe sky obstruction (30° and 40°).
- **Expected Result:** Quantifies coordinate shift between 15°, 30°, and 40° masks at 99% confidence.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_2_high_cutoff_comparison/inputs/rinex",
    "MASKS": "15,30,40",
    "CONFIDENCE": 0.99,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_2_high_cutoff_comparison/outputs/comparison.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_2_high_cutoff_comparison/outputs/comparison.csv",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_2_high_cutoff_comparison/outputs/comparison.json"
  }
  ```

#### Example 3: Direct comparison of two custom RTKLIB .conf files (conf_mask12 vs conf_mask22)
- **Folder:** `03_gnss/gnss_compare_configurations/example_3_custom_config_files/`
- **Scenario:** Compares two user-supplied RTKLIB configuration files directly instead of a mask list.
- **Expected Result:** Compares the two named RTKLIB configurations side by side.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/inputs/rinex",
    "CONFIGURATIONS": [
      "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/inputs/conf_mask12.conf",
      "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/inputs/conf_mask22.conf"
    ],
    "CONFIDENCE": 0.95,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/outputs/comparison.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/outputs/comparison.csv",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/03_gnss/gnss_compare_configurations/example_3_custom_config_files/outputs/comparison.json"
  }
  ```

---
## Gravimetry (`04_gravimetry`)

### GeoComp ▸ Gravimetry ▸ Pre-processing (scale, tide, drift) (`geocomp:gravimetry_preprocess`)

#### Example 1: Scintrex CG-5 pre-processing keeping instrument tide and linear drift (degree 1)
- **Folder:** `04_gravimetry/gravimetry_preprocess/example_1_cg5_instrument_tide_linear/`
- **Scenario:** Reduces CG-5 readings (BASE, S1, S2) with linear drift fit.
- **Expected Result:** Fits linear instrumental drift from repeated BASE occupations.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_1_cg5_instrument_tide_linear/inputs/cg5_survey.txt",
    "PRECISION_FLOOR": 0.005,
    "REPLACE_TIDE": false,
    "TIDE_MODEL": 0,
    "AMPLIFICATION": 1.16,
    "DRIFT_DEGREE": 1,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_1_cg5_instrument_tide_linear/outputs/reduced_readings.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_1_cg5_instrument_tide_linear/outputs/corrections.csv",
    "OUTPUT_DRIFT": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_1_cg5_instrument_tide_linear/outputs/drift.json"
  }
  ```

#### Example 2: Replace CG-5 tide with Longman (1959) solid-Earth tide + 0.25 m sensor height
- **Folder:** `04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/`
- **Scenario:** Replaces instrument tide with Longman (1959) and applies free-air height reduction (0.25 m).
- **Expected Result:** Recomputes Longman luni-solar tide and applies free-air sensor-height correction.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/inputs/cg5_survey.txt",
    "PROFILES": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/inputs/gravimeter_profiles.json",
    "PRECISION_FLOOR": 0.005,
    "SENSOR_HEIGHT": 0.25,
    "SENSOR_HEIGHT_SIGMA": 0.002,
    "REPLACE_TIDE": true,
    "UTC_OFFSET": 0.0,
    "TIDE_MODEL": 0,
    "AMPLIFICATION": 1.16,
    "DRIFT_DEGREE": 1,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/outputs/reduced_readings.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/outputs/corrections.csv",
    "OUTPUT_DRIFT": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_2_longman_tide_replacement/outputs/drift.json"
  }
  ```

#### Example 3: Quadratic drift polynomial (degree 2) with no external tide model
- **Folder:** `04_gravimetry/gravimetry_preprocess/example_3_quadratic_drift_usgs_burris/`
- **Scenario:** Fits a 2nd-degree drift polynomial to capture nonlinear thermal drift.
- **Expected Result:** Estimates degree-2 drift coefficients and writes reduced_readings.json.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_3_quadratic_drift_usgs_burris/inputs/survey.txt",
    "PRECISION_FLOOR": 0.01,
    "REPLACE_TIDE": false,
    "TIDE_MODEL": 1,
    "DRIFT_DEGREE": 2,
    "OUTPUT_READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_3_quadratic_drift_usgs_burris/outputs/reduced_readings.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_3_quadratic_drift_usgs_burris/outputs/corrections.csv",
    "OUTPUT_DRIFT": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_preprocess/example_3_quadratic_drift_usgs_burris/outputs/drift.json"
  }
  ```

### GeoComp ▸ Gravimetry ▸ Gravimetric network adjustment (`geocomp:gravimetry_network`)

#### Example 1: Joint estimation of station gravity and linear drift holding station 1 = 978800.000 mGal
- **Folder:** `04_gravimetry/gravimetry_network/example_1_joint_drift_and_gravity/`
- **Scenario:** Simultaneously adjusts gravity at stations 1, 2, 3 and drift polynomial with full correlation.
- **Expected Result:** Adjusts station gravity values and drift parameters jointly.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_1_joint_drift_and_gravity/inputs/reduced_readings.json",
    "KNOWN_GRAVITY": "1=978800.000",
    "DRIFT_MODE": 0,
    "DRIFT_DEGREE": 1,
    "CORRELATED": true,
    "CONFIDENCE": 0.95,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_1_joint_drift_and_gravity/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_1_joint_drift_and_gravity/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_1_joint_drift_and_gravity/outputs/gravity.csv"
  }
  ```

#### Example 2: Drift fitted to base readings first (DRIFT_MODE=1) with uncorrelated differences
- **Folder:** `04_gravimetry/gravimetry_network/example_2_pre_fitted_base_drift/`
- **Scenario:** Removes base-fitted drift prior to network adjustment and treats differences as uncorrelated.
- **Expected Result:** Adjusts gravity values with weighted reference station 1 (±0.005 mGal).
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_2_pre_fitted_base_drift/inputs/reduced_readings.json",
    "KNOWN_GRAVITY": "1=978800.000±0.005",
    "DRIFT_MODE": 1,
    "DRIFT_DEGREE": 1,
    "CORRELATED": false,
    "CONFIDENCE": 0.99,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_2_pre_fitted_base_drift/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_2_pre_fitted_base_drift/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_2_pre_fitted_base_drift/outputs/gravity.csv"
  }
  ```

#### Example 3: Correlated gravimetric adjustment with alpha=0.005 Baarda snooping
- **Folder:** `04_gravimetry/gravimetry_network/example_3_high_confidence_snooping/`
- **Scenario:** Runs correlated difference adjustment with custom data-snooping significance alpha=0.005.
- **Expected Result:** Completes correlated gravimetric adjustment with Baarda data snooping.
- **Parameters (`example.json`):**
  ```json
  {
    "READINGS": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_3_high_confidence_snooping/inputs/reduced_readings.json",
    "KNOWN_GRAVITY": "1=978800.000",
    "DRIFT_MODE": 0,
    "DRIFT_DEGREE": 1,
    "CORRELATED": true,
    "ALPHA": 0.005,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_3_high_confidence_snooping/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_3_high_confidence_snooping/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/04_gravimetry/gravimetry_network/example_3_high_confidence_snooping/outputs/gravity.csv"
  }
  ```

---
## Integration (`05_integration`)

### GeoComp ▸ Integration ▸ GNSS and total station (`geocomp:integration_gnss_total_station`)

#### Example 1: Combine GNSS baselines and UTM 22S projected Total Station network in ITRF2020
- **Folder:** `05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/`
- **Scenario:** Projects UTM 22S total station starting coordinates into geocentric ITRF2020 and adjusts jointly with GNSS.
- **Expected Result:** Produces unified 3D solution in ITRF2020 recovering true station coordinates to < 3 cm.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/inputs/ts_grid.json",
    "FIXED_STATIONS": "CTB1,CTB2",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_1_utm_grid_and_gnss/outputs/combined.json"
  }
  ```

#### Example 2: GNSS + Total Station in ITRF2014 with Helmert variance component estimation
- **Folder:** `05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/`
- **Scenario:** Estimates per-technique variance components between GNSS and Total Station in ITRF2014.
- **Expected Result:** Estimates variance components for GNSS and Total Station groups.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/inputs/ts.json",
    "FRAME": 1,
    "FIXED_STATIONS": "CTB1,CTB2",
    "VARIANCE_COMPONENTS": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_2_variance_components_sirgas/outputs/combined.json"
  }
  ```

#### Example 3: GNSS + Total Station propagated to epoch 2025.0 using station velocities CSV
- **Folder:** `05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/`
- **Scenario:** Propagates coordinates to epoch 2025.0 via velocities.csv and adjusts in ITRF2014.
- **Expected Result:** Adjusts velocity-propagated combined network at epoch 2025.0.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/inputs/ts.json",
    "FRAME": 1,
    "EPOCH": "2025.0",
    "VELOCITIES": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/inputs/velocities.csv",
    "FIXED_STATIONS": "CTB1,CTB2",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_total_station/example_3_epoch_shift_with_velocities/outputs/combined.json"
  }
  ```

### GeoComp ▸ Integration ▸ Total station and level (`geocomp:integration_total_station_level`)

#### Example 1: Combine projected Total Station and Spirit Levelling in the Total Station's CRS
- **Folder:** `05_integration/integration_total_station_level/example_1_local_grid_combination/`
- **Scenario:** Combines terrestrial 3D total station and spirit levelling observations at epoch 2026.7.
- **Expected Result:** Combines Total Station and Levelling in EPSG:31982 recovering heights to < 5 mm.
- **Parameters (`example.json`):**
  ```json
  {
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_1_local_grid_combination/inputs/ts.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_1_local_grid_combination/inputs/levelling.json",
    "EPOCH": "2026.7",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_1_local_grid_combination/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_1_local_grid_combination/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_1_local_grid_combination/outputs/combined.json"
  }
  ```

#### Example 2: Total Station + Spirit Levelling with Helmert variance component estimation
- **Folder:** `05_integration/integration_total_station_level/example_2_with_variance_components/`
- **Scenario:** Estimates per-technique variance factors between terrestrial zeniths and spirit levelling.
- **Expected Result:** Balances terrestrial and levelling weights via VCE.
- **Parameters (`example.json`):**
  ```json
  {
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_2_with_variance_components/inputs/ts.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_2_with_variance_components/inputs/levelling.json",
    "EPOCH": "2026.7",
    "VARIANCE_COMPONENTS": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_2_with_variance_components/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_2_with_variance_components/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_2_with_variance_components/outputs/combined.json"
  }
  ```

#### Example 3: Total Station + Spirit Levelling at 99% confidence level
- **Folder:** `05_integration/integration_total_station_level/example_3_high_confidence_99pct/`
- **Scenario:** Runs combined terrestrial adjustment with 99% confidence intervals and ellipses.
- **Expected Result:** Outputs 99% confidence combined terrestrial solution.
- **Parameters (`example.json`):**
  ```json
  {
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_3_high_confidence_99pct/inputs/ts.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_3_high_confidence_99pct/inputs/levelling.json",
    "EPOCH": "2026.7",
    "CONFIDENCE": 0.99,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_3_high_confidence_99pct/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_3_high_confidence_99pct/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_total_station_level/example_3_high_confidence_99pct/outputs/combined.json"
  }
  ```

### GeoComp ▸ Integration ▸ GNSS and level (`geocomp:integration_gnss_level`)

#### Example 1: GNSS + Spirit Levelling coupled through ESRI ASCII geoid grid (h - H = N)
- **Folder:** `05_integration/integration_gnss_level/example_1_planar_geoid_coupling/`
- **Scenario:** Couples ellipsoidal GNSS heights and orthometric levelling differences through curitiba_planar.asc.
- **Expected Result:** Computes geoid residuals and adjusts GNSS + Levelling jointly.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/inputs/gnss.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/inputs/levelling.json",
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.03,
    "FIXED_STATIONS": "CTB1,CTB2",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_1_planar_geoid_coupling/outputs/combined.json"
  }
  ```

#### Example 2: GNSS + Spirit Levelling with Helmert variance component estimation
- **Folder:** `05_integration/integration_gnss_level/example_2_variance_components/`
- **Scenario:** Estimates variance components for GNSS baselines and spirit levelling lines.
- **Expected Result:** Converges variance components between GNSS and spirit levelling.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/inputs/gnss.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/inputs/levelling.json",
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.03,
    "FIXED_STATIONS": "CTB1,CTB2",
    "VARIANCE_COMPONENTS": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_2_variance_components/outputs/combined.json"
  }
  ```

#### Example 3: GNSS + Spirit Levelling combined in ITRF2008 (FRAME=2)
- **Folder:** `05_integration/integration_gnss_level/example_3_sirgas2000_frame/`
- **Scenario:** Transforms GNSS baselines to ITRF2008 and adjusts with spirit levelling.
- **Expected Result:** Produces combined GNSS + Levelling solution in ITRF2008.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/inputs/gnss.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/inputs/levelling.json",
    "FRAME": 2,
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.05,
    "FIXED_STATIONS": "CTB1,CTB2",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_gnss_level/example_3_sirgas2000_frame/outputs/combined.json"
  }
  ```

### GeoComp ▸ Integration ▸ Multiple techniques (`geocomp:integration_multiple`)

#### Example 1: Three-technique combination (GNSS + Total Station + Levelling) with VCE and geoid
- **Folder:** `05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/`
- **Scenario:** Simultaneously adjusts all 3 geometric techniques on the Curitiba network with variance components.
- **Expected Result:** Estimates variance components across gnss, total_station, and levelling.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/inputs/ts.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/inputs/levelling.json",
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.03,
    "FIXED_STATIONS": "CTB1,CTB2",
    "VARIANCE_COMPONENTS": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_1_gnss_ts_levelling_vce/outputs/combined.json"
  }
  ```

#### Example 2: Three-technique combination in ITRF2014 with projected UTM Total Station input
- **Folder:** `05_integration/integration_multiple/example_2_sirgas2000_no_vce/`
- **Scenario:** Combines GNSS, UTM 22S Total Station, and Spirit Levelling in ITRF2014.
- **Expected Result:** Combines all 3 techniques in ITRF2014.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/inputs/ts_grid.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/inputs/levelling.json",
    "FRAME": 1,
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.03,
    "FIXED_STATIONS": "CTB1,CTB2",
    "VARIANCE_COMPONENTS": false,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_2_sirgas2000_no_vce/outputs/combined.json"
  }
  ```

#### Example 3: Four-technique integration (GNSS + Total Station + Levelling + Gravimetry)
- **Folder:** `05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/`
- **Scenario:** Combines 3D geometric techniques alongside CG-5 gravimetry readings.
- **Expected Result:** Produces both geometric solution.json and gravimetric gravity_solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "GNSS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/inputs/gnss.json",
    "TOTAL_STATION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/inputs/ts.json",
    "LEVELLING": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/inputs/levelling.json",
    "READINGS": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/inputs/gravity_reduced.json",
    "KNOWN_GRAVITY": "1=978800.000",
    "GEOID": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/inputs/curitiba_planar.asc",
    "GEOID_SIGMA": 0.03,
    "FIXED_STATIONS": "CTB1,CTB2",
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/outputs/report.html",
    "OUTPUT_NETWORK": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/outputs/combined.json",
    "OUTPUT_GRAVITY": "/home/kaue/geocomp/synthetic_examples/05_integration/integration_multiple/example_3_all_four_techniques_with_gravity/outputs/gravity_solution.json"
  }
  ```

---
## Analysis (`06_analysis`)

### GeoComp ▸ Analysis ▸ Inspect network (`geocomp:analysis_network_inspect`)

#### Example 1: Topological and rank inspection of a sound 2D trilateration network
- **Folder:** `06_analysis/analysis_network_inspect/example_1_sound_2d_trilateration/`
- **Scenario:** Verifies connectivity, datum constraints, and degrees of freedom of RD-03 trilateration network.
- **Expected Result:** Reports CAN_ADJUST=True, BLOCKING_COUNT=0, COMPONENT_COUNT=1.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_1_sound_2d_trilateration/inputs/trilateration.json",
    "FRAME": 0,
    "FAIL_ON_BLOCKING": true,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_1_sound_2d_trilateration/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_1_sound_2d_trilateration/outputs/findings.csv"
  }
  ```

#### Example 2: Inspection of a 1D spirit-levelling network (FRAME=1)
- **Folder:** `06_analysis/analysis_network_inspect/example_2_1d_levelling_loop/`
- **Scenario:** Checks vertical benchmark sufficiency and graph connectivity in 1D height mode.
- **Expected Result:** Confirms 1D height network is connected and ready for adjustment.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_2_1d_levelling_loop/inputs/levelling_loop.json",
    "FRAME": 1,
    "FAIL_ON_BLOCKING": true,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_2_1d_levelling_loop/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_2_1d_levelling_loop/outputs/findings.csv"
  }
  ```

#### Example 3: Inspection of a 3D geodetic network (FRAME=2)
- **Folder:** `06_analysis/analysis_network_inspect/example_3_3d_geodetic_network/`
- **Scenario:** Audits 3D station connectivity and observation redundancy.
- **Expected Result:** Writes 3D topology inspection report and findings table.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_3_3d_geodetic_network/inputs/geodetic_3d.json",
    "FRAME": 2,
    "FAIL_ON_BLOCKING": false,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_3_3d_geodetic_network/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_inspect/example_3_3d_geodetic_network/outputs/findings.csv"
  }
  ```

### GeoComp ▸ Analysis ▸ Pre-analyse network design (`geocomp:analysis_network_preanalysis`)

#### Example 1: Pre-analysis of 2D trilateration design under constrained datum
- **Folder:** `06_analysis/analysis_network_preanalysis/example_1_constrained_2d_design/`
- **Scenario:** Computes expected station precisions, redundancy numbers, and MDBs before field observation.
- **Expected Result:** All planned stations meet the 50 mm positional uncertainty tolerance.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_1_constrained_2d_design/inputs/planned_network.json",
    "FRAME": 0,
    "DATUM": 0,
    "TOLERANCE": 0.05,
    "CONFIDENCE": 0.95,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_1_constrained_2d_design/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_1_constrained_2d_design/outputs/expected_precision.csv"
  }
  ```

#### Example 2: Free-network (inner constraint) pre-analysis at 99% confidence
- **Folder:** `06_analysis/analysis_network_preanalysis/example_2_inner_constraint_free/`
- **Scenario:** Evaluates internal geometry precision independent of control datum errors.
- **Expected Result:** Outputs 99% free-network error ellipses and minimal detectable biases.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_2_inner_constraint_free/inputs/planned_network.json",
    "FRAME": 0,
    "DATUM": 1,
    "CONFIDENCE": 0.99,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_2_inner_constraint_free/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_2_inner_constraint_free/outputs/expected_precision.csv"
  }
  ```

#### Example 3: Pre-analysis of a 1D spirit-levelling loop design (FRAME=1)
- **Folder:** `06_analysis/analysis_network_preanalysis/example_3_1d_levelling_design/`
- **Scenario:** Computes expected vertical standard deviations and observation redundancy numbers.
- **Expected Result:** Computes expected vertical precisions for all benchmarks in the loop.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_3_1d_levelling_design/inputs/planned_levelling.json",
    "FRAME": 1,
    "DATUM": 0,
    "TOLERANCE": 0.005,
    "CONFIDENCE": 0.95,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_3_1d_levelling_design/outputs/report.html",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_preanalysis/example_3_1d_levelling_design/outputs/expected_precision.csv"
  }
  ```

### GeoComp ▸ Analysis ▸ Adjust network (`geocomp:analysis_network_adjust`)

#### Example 1: 2D Gauss-Markov least-squares adjustment of trilateration network
- **Folder:** `06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/`
- **Scenario:** Adjusts 2D network with constrained datum and Baarda data snooping.
- **Expected Result:** Converges least-squares solution and writes solution.json, stations.csv, and residuals.csv.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/inputs/trilateration.json",
    "FRAME": 0,
    "DATUM": 0,
    "CONFIDENCE": 0.95,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/outputs/report.html",
    "OUTPUT_STATIONS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/outputs/stations.csv",
    "OUTPUT_RESIDUALS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_1_2d_constrained_trilateration/outputs/residuals.csv"
  }
  ```

#### Example 2: Free 2D network adjustment (inner constraint / trace minimum)
- **Folder:** `06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/`
- **Scenario:** Adjusts 2D distance network under inner constraints (DATUM=1).
- **Expected Result:** Computes minimum-trace free network solution.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/inputs/free_2d_network.json",
    "FRAME": 0,
    "DATUM": 1,
    "CONFIDENCE": 0.95,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/outputs/report.html",
    "OUTPUT_STATIONS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/outputs/stations.csv",
    "OUTPUT_RESIDUALS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_2_2d_inner_constraint/outputs/residuals.csv"
  }
  ```

#### Example 3: 1D height network adjustment (FRAME=1) at 99% confidence
- **Folder:** `06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/`
- **Scenario:** Adjusts 1D spirit-levelling network document through the general network adjustment engine.
- **Expected Result:** Adjusts 1D benchmark heights and writes residual diagnostics.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/inputs/levelling_loop.json",
    "FRAME": 1,
    "DATUM": 0,
    "CONFIDENCE": 0.99,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/outputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/outputs/report.html",
    "OUTPUT_STATIONS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/outputs/stations.csv",
    "OUTPUT_RESIDUALS_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_network_adjust/example_3_1d_levelling_adjustment/outputs/residuals.csv"
  }
  ```

### GeoComp ▸ Analysis ▸ Adjust network (DynAdjust) (`geocomp:analysis_dynadjust_adjust`)

#### Example 1: Full DynAdjust pipeline (import -> reftran -> adjust) from Network JSON
- **Folder:** `06_analysis/analysis_dynadjust_adjust/example_1_full_pipeline_from_network/`
- **Scenario:** Writes DynaML (.stn.xml / .msr.xml), runs DynAdjust pipeline, and parses adjusted coordinates + SINEX covariances.
- **Expected Result:** Runs DynAdjust pipeline and writes solution.json + working files.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_1_full_pipeline_from_network/inputs/network.json",
    "FRAME": "GDA2020",
    "EPOCH": 2020.0,
    "ENGINE_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "KEEP_WORKING_FILES": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_1_full_pipeline_from_network/outputs/solution.json",
    "OUTPUT_WORK_DIR": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_1_full_pipeline_from_network/outputs/work"
  }
  ```

#### Example 2: DynAdjust adjustment reading network directly from a GeoPackage store + NTv2 geoid + custom JSON options
- **Folder:** `06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/`
- **Scenario:** Reads network 'sample' from project_store.gpkg, includes dnageoid stage with synthetic_geoid.gsb, and passes custom CLI flags.
- **Expected Result:** Reads network from GeoPackage store, runs dnageoid stage, and writes solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "STORE": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/inputs/project_store.gpkg",
    "STORED_NETWORK": "sample",
    "FRAME": "GDA2020",
    "EPOCH": 2020.0,
    "GEOID_GRID": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/inputs/synthetic_geoid.gsb",
    "CONFIGURATION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/inputs/dynadjust_options.json",
    "ENGINE_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "KEEP_WORKING_FILES": true,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/outputs/solution.json",
    "OUTPUT_WORK_DIR": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_2_from_geopackage_store_with_geoid/outputs/work"
  }
  ```

#### Example 3: Prepare DynAdjust DynaML files and stop before running (STOP_BEFORE_RUNNING=True)
- **Folder:** `06_analysis/analysis_dynadjust_adjust/example_3_stop_before_running_prepare_only/`
- **Scenario:** Generates geocomp.stn.xml, geocomp.msr.xml, and geocomp-dynadjust.json for manual inspection without invoking binaries.
- **Expected Result:** Writes DynaML input files and manifest into prepared_job/ without running DynAdjust.
- **Parameters (`example.json`):**
  ```json
  {
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_3_stop_before_running_prepare_only/inputs/network.json",
    "FRAME": "GDA2020",
    "EPOCH": 2020.0,
    "STOP_BEFORE_RUNNING": true,
    "OUTPUT_WORK_DIR": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_adjust/example_3_stop_before_running_prepare_only/outputs/prepared_job"
  }
  ```

### GeoComp ▸ Analysis ▸ Run a prepared DynAdjust job (`geocomp:analysis_dynadjust_run_prepared`)

#### Example 1: Execute a prepared DynAdjust folder and import SINEX solution
- **Folder:** `06_analysis/analysis_dynadjust_run_prepared/example_1_nominal_prepared_job/`
- **Scenario:** Runs a prepared DynaML folder containing geocomp.stn.xml, geocomp.msr.xml, and geocomp-dynadjust.json.
- **Expected Result:** Executes prepared DynAdjust job and writes solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "PREPARED": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_1_nominal_prepared_job/inputs/prepared_job",
    "ENGINE_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "TIMEOUT": 600.0,
    "EXAGGERATION": 0.0,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_1_nominal_prepared_job/outputs/solution.json"
  }
  ```

#### Example 2: Execute a prepared job after hand-editing measurement weights in .msr.xml
- **Folder:** `06_analysis/analysis_dynadjust_run_prepared/example_2_edited_msr_prepared_job/`
- **Scenario:** Demonstrates the 2-step workflow: edit .msr.xml in a prepared folder, then run DynAdjust.
- **Expected Result:** Executes prepared DynAdjust job and writes solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "PREPARED": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_2_edited_msr_prepared_job/inputs/prepared_job",
    "ENGINE_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "TIMEOUT": 600.0,
    "EXAGGERATION": 100.0,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_2_edited_msr_prepared_job/outputs/solution.json"
  }
  ```

#### Example 3: Execute prepared DynAdjust job with custom stage timeout and 500x ellipse exaggeration
- **Folder:** `06_analysis/analysis_dynadjust_run_prepared/example_3_custom_timeout_and_exaggeration/`
- **Scenario:** Runs prepared job with 600 s stage timeout and 500x error ellipse scaling.
- **Expected Result:** Executes prepared DynAdjust job and writes solution.json.
- **Parameters (`example.json`):**
  ```json
  {
    "PREPARED": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_3_custom_timeout_and_exaggeration/inputs/prepared_job",
    "ENGINE_DIRECTORY": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "TIMEOUT": 600.0,
    "EXAGGERATION": 500.0,
    "OUTPUT_SOLUTION": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_run_prepared/example_3_custom_timeout_and_exaggeration/outputs/solution.json"
  }
  ```

### GeoComp ▸ Analysis ▸ Compare two solutions (`geocomp:analysis_dynadjust_compare`)

#### Example 1: Compare two identical adjustment solutions (0.1 mm coordinate tolerance)
- **Folder:** `06_analysis/analysis_dynadjust_compare/example_1_identical_solutions/`
- **Scenario:** Verifies zero coordinate and variance factor differences between two identical solutions.
- **Expected Result:** Confirms 0.0 mm max coordinate discrepancy and passes both tolerances.
- **Parameters (`example.json`):**
  ```json
  {
    "REFERENCE": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_1_identical_solutions/inputs/reference_solution.json",
    "OTHER": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_1_identical_solutions/inputs/other_solution.json",
    "COORDINATE_TOLERANCE": 0.0001,
    "VARIANCE_TOLERANCE": 0.01,
    "OUTPUT_REPORT": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_1_identical_solutions/outputs/comparison_report.html",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_1_identical_solutions/outputs/differences.json"
  }
  ```

#### Example 2: Compare two epoch solutions under a 20 mm coordinate tolerance
- **Folder:** `06_analysis/analysis_dynadjust_compare/example_2_relaxed_tolerance_agreement/`
- **Scenario:** Compares Epoch 1 and Epoch 2 (10 mm motion on O2) against a 20 mm tolerance.
- **Expected Result:** Reports ~10 mm max station difference within the 20 mm tolerance.
- **Parameters (`example.json`):**
  ```json
  {
    "REFERENCE": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_2_relaxed_tolerance_agreement/inputs/reference_solution.json",
    "OTHER": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_2_relaxed_tolerance_agreement/inputs/other_solution.json",
    "COORDINATE_TOLERANCE": 0.02,
    "VARIANCE_TOLERANCE": 0.5,
    "OUTPUT_REPORT": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_2_relaxed_tolerance_agreement/outputs/comparison_report.html",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_2_relaxed_tolerance_agreement/outputs/differences.json"
  }
  ```

#### Example 3: Compare two solutions with 20 mm station shift exceeding 0.1 mm tolerance
- **Folder:** `06_analysis/analysis_dynadjust_compare/example_3_divergent_solutions_flagged/`
- **Scenario:** Compares Epoch 1 against Epoch 3 (where O2 shifted by 20 mm) and flags tolerance exceedance.
- **Expected Result:** Flags station O2 as exceeding coordinate tolerance in differences.json.
- **Parameters (`example.json`):**
  ```json
  {
    "REFERENCE": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_3_divergent_solutions_flagged/inputs/epoch1_solution.json",
    "OTHER": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_3_divergent_solutions_flagged/inputs/epoch3_solution.json",
    "COORDINATE_TOLERANCE": 0.0001,
    "VARIANCE_TOLERANCE": 0.005,
    "OUTPUT_REPORT": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_3_divergent_solutions_flagged/outputs/comparison_report.html",
    "OUTPUT_JSON": "/home/kaue/geocomp/synthetic_examples/06_analysis/analysis_dynadjust_compare/example_3_divergent_solutions_flagged/outputs/differences.json"
  }
  ```

### GeoComp ▸ Analysis ▸ Compare two epochs (`geocomp:monitoring_compare_epochs`)

#### Example 1: Two-epoch dam deformation analysis (Epoch 1 vs Epoch 2) using network monitoring roles
- **Folder:** `06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/`
- **Scenario:** Tests congruence of reference pillars (R1..R4) and detects 10 mm displacement on crest O2.
- **Expected Result:** Confirms reference block stability and flags statistically significant motion at O2.
- **Parameters (`example.json`):**
  ```json
  {
    "FIRST": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/inputs/epoch_1.json",
    "SECOND": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/inputs/epoch_2.json",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/inputs/monitoring_network.json",
    "DATUM": 0,
    "CONFIDENCE": 0.95,
    "STRAIN": true,
    "OUTPUT_ANALYSIS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/outputs/analysis.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_1_dam_deformation_from_network_roles/outputs/monitoring_report.html"
  }
  ```

#### Example 2: Deformation analysis (Epoch 1 vs Epoch 3) with explicit station lists and alert thresholds CSV
- **Folder:** `06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/`
- **Scenario:** Evaluates 20 mm cumulative displacement at O2 against alert_thresholds.csv.
- **Expected Result:** Flags threshold exceedance on O2 and writes analysis.json + HTML report.
- **Parameters (`example.json`):**
  ```json
  {
    "FIRST": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/inputs/epoch_1.json",
    "SECOND": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/inputs/epoch_3.json",
    "REFERENCE": "R1,R2,R3,R4",
    "OBJECTS": "O1,O2,O3,O4,O5",
    "DATUM": 2,
    "CONFIDENCE": 0.99,
    "STRAIN": true,
    "THRESHOLDS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/inputs/alert_thresholds.csv",
    "OUTPUT_ANALYSIS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/outputs/analysis.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_2_explicit_roles_and_alert_thresholds/outputs/monitoring_report.html"
  }
  ```

#### Example 3: S-transformation with similarity datum (translation, rotation, scale) and STRAIN=False
- **Folder:** `06_analysis/monitoring_compare_epochs/example_3_similarity_datum_no_strain/`
- **Scenario:** Uses full 4-parameter 2D similarity datum over R1..R4 without rigid-body/strain decomposition.
- **Expected Result:** Computes displacement vectors under similarity S-transformation.
- **Parameters (`example.json`):**
  ```json
  {
    "FIRST": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_3_similarity_datum_no_strain/inputs/epoch_1.json",
    "SECOND": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_3_similarity_datum_no_strain/inputs/epoch_2.json",
    "REFERENCE": "R1,R2,R3,R4",
    "OBJECTS": "O1,O2,O3,O4,O5",
    "DATUM": 3,
    "CONFIDENCE": 0.95,
    "STRAIN": false,
    "OUTPUT_ANALYSIS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_3_similarity_datum_no_strain/outputs/analysis.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_compare_epochs/example_3_similarity_datum_no_strain/outputs/monitoring_report.html"
  }
  ```

### GeoComp ▸ Analysis ▸ Time series and velocities (`geocomp:monitoring_time_series`)

#### Example 1: Three-epoch time series recovering linear crest velocity on O2
- **Folder:** `06_analysis/monitoring_time_series/example_1_three_epoch_velocities/`
- **Scenario:** Fits weighted linear regression across 3 epochs to estimate station velocities.
- **Expected Result:** Recovers O2 velocity rate and near-zero reference velocities.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTIONS": [
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/inputs/epoch_1.json",
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/inputs/epoch_2.json",
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/inputs/epoch_3.json"
    ],
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/inputs/monitoring_network.json",
    "DATUM": 0,
    "CONFIDENCE": 0.95,
    "OUTPUT_SERIES": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/outputs/series.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/outputs/series.csv",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_1_three_epoch_velocities/outputs/monitoring_report.html"
  }
  ```

#### Example 2: Time series with explicit reference list (R1..R4), 99% confidence, and alert thresholds
- **Folder:** `06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/`
- **Scenario:** Computes time series using explicit reference list at 99% confidence and evaluates alert thresholds.
- **Expected Result:** Outputs multi-epoch offsets and flags threshold exceedances.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTIONS": [
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/inputs/epoch_1.json",
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/inputs/epoch_2.json",
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/inputs/epoch_3.json"
    ],
    "REFERENCE": "R1,R2,R3,R4",
    "DATUM": 0,
    "CONFIDENCE": 0.99,
    "THRESHOLDS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/inputs/velocity_thresholds.csv",
    "OUTPUT_SERIES": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/outputs/series.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/outputs/series.csv",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_2_explicit_reference_and_thresholds/outputs/monitoring_report.html"
  }
  ```

#### Example 3: Two-epoch minimal time series (Epoch 1 and Epoch 3) with similarity datum
- **Folder:** `06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/`
- **Scenario:** Computes velocity rates from two epochs under similarity datum.
- **Expected Result:** Computes 2-epoch rates and writes series.json + HTML report.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTIONS": [
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/inputs/epoch_1.json",
      "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/inputs/epoch_3.json"
    ],
    "REFERENCE": "R1,R2,R3,R4",
    "DATUM": 3,
    "CONFIDENCE": 0.95,
    "EXAGGERATION": 500.0,
    "OUTPUT_SERIES": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/outputs/series.json",
    "OUTPUT_CSV": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/outputs/series.csv",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_time_series/example_3_two_epoch_minimal_series/outputs/monitoring_report.html"
  }
  ```

### GeoComp ▸ Analysis ▸ Monitoring report (`geocomp:monitoring_report`)

#### Example 1: Standalone HTML monitoring report from two-epoch congruence analysis
- **Folder:** `06_analysis/monitoring_report/example_1_from_two_epoch_analysis/`
- **Scenario:** Renders two-epoch deformation tables, stability tests, and SVG vector map.
- **Expected Result:** Writes self-contained HTML report with SVG displacement vectors.
- **Parameters (`example.json`):**
  ```json
  {
    "ANALYSIS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_1_from_two_epoch_analysis/inputs/analysis.json",
    "EXAGGERATION": 0.0,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_1_from_two_epoch_analysis/outputs/monitoring_report.html"
  }
  ```

#### Example 2: Comprehensive monitoring report combining two-epoch analysis and multi-epoch time series
- **Folder:** `06_analysis/monitoring_report/example_2_combined_analysis_and_series/`
- **Scenario:** Includes both pairwise epoch comparison and multi-year velocity trend charts in one report.
- **Expected Result:** Renders combined pairwise + time-series monitoring report with 1000x map exaggeration.
- **Parameters (`example.json`):**
  ```json
  {
    "ANALYSIS": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_2_combined_analysis_and_series/inputs/analysis.json",
    "SERIES": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_2_combined_analysis_and_series/inputs/series.json",
    "EXAGGERATION": 1000.0,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_2_combined_analysis_and_series/outputs/monitoring_report.html"
  }
  ```

#### Example 3: Time-series monitoring report rendered from series.json alone
- **Folder:** `06_analysis/monitoring_report/example_3_from_series_only/`
- **Scenario:** Renders velocity tables and offset history from series.json with 500x exaggeration.
- **Expected Result:** Renders HTML monitoring report from series document.
- **Parameters (`example.json`):**
  ```json
  {
    "SERIES": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_3_from_series_only/inputs/series.json",
    "EXAGGERATION": 500.0,
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/06_analysis/monitoring_report/example_3_from_series_only/outputs/monitoring_report.html"
  }
  ```

---
## Project (`07_project`)

### GeoComp ▸ Project ▸ Export solution tables (`geocomp:project_export`)

#### Example 1: Export adjusted stations, residuals, and covariances as a folder of CSV files
- **Folder:** `07_project/project_export/example_1_csv_tables_with_network/`
- **Scenario:** Writes stations.csv, observations.csv, and covariance.csv from solution + network.
- **Expected Result:** Creates CSV tables in csv_tables/.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_1_csv_tables_with_network/inputs/solution.json",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_1_csv_tables_with_network/inputs/network.json",
    "FORMAT": 0,
    "OUTPUT_FOLDER": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_1_csv_tables_with_network/outputs/csv_tables"
  }
  ```

#### Example 2: Export solution tables into a multi-sheet Excel workbook (.xlsx)
- **Folder:** `07_project/project_export/example_2_xlsx_workbook/`
- **Scenario:** Packages Stations, Observations, and Covariance sheets into a single .xlsx spreadsheet.
- **Expected Result:** Writes multi-tab solution_tables.xlsx workbook.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_2_xlsx_workbook/inputs/solution.json",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_2_xlsx_workbook/inputs/network.json",
    "FORMAT": 1,
    "OUTPUT_WORKBOOK": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_2_xlsx_workbook/outputs/solution_tables.xlsx"
  }
  ```

#### Example 3: Export CSV tables from a standalone Solution JSON without a Network document
- **Folder:** `07_project/project_export/example_3_solution_only_csv/`
- **Scenario:** Exports adjusted coordinates and residuals directly from solution_epoch2.json.
- **Expected Result:** Exports solution tables without requiring the input network document.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_3_solution_only_csv/inputs/solution_epoch2.json",
    "FORMAT": 0,
    "OUTPUT_FOLDER": "/home/kaue/geocomp/synthetic_examples/07_project/project_export/example_3_solution_only_csv/outputs/csv_tables"
  }
  ```

### GeoComp ▸ Project ▸ Adjustment report (`geocomp:project_report`)

#### Example 1: Full HTML adjustment report with network summary, chi-square test, and SVG network plot
- **Folder:** `07_project/project_report/example_1_full_adjustment_report/`
- **Scenario:** Generates a complete adjustment report from solution.json + network.json.
- **Expected Result:** Writes self-contained HTML adjustment report with embedded SVG graphics.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_1_full_adjustment_report/inputs/solution.json",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_1_full_adjustment_report/inputs/network.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_1_full_adjustment_report/outputs/adjustment_report.html"
  }
  ```

#### Example 2: Adjustment report generated from Solution JSON alone
- **Folder:** `07_project/project_report/example_2_solution_only_report/`
- **Scenario:** Produces coordinate, precision, and residual tables when only solution.json is available.
- **Expected Result:** Renders HTML adjustment report from standalone solution document.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_2_solution_only_report/inputs/solution.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_2_solution_only_report/outputs/adjustment_report.html"
  }
  ```

#### Example 3: Adjustment report for RD-03 2D trilateration network
- **Folder:** `07_project/project_report/example_3_trilateration_solution_report/`
- **Scenario:** Renders adjustment report for the adjusted RD-03 trilateration network.
- **Expected Result:** Writes HTML adjustment report for RD-03 trilateration.
- **Parameters (`example.json`):**
  ```json
  {
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_3_trilateration_solution_report/inputs/trilat_solution.json",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_3_trilateration_solution_report/inputs/trilateration.json",
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_report/example_3_trilateration_solution_report/outputs/adjustment_report.html"
  }
  ```

### GeoComp ▸ Project ▸ Save to project store (`geocomp:project_store`)

#### Example 1: Create a new GeoPackage project store containing Network + Epoch 1 Solution
- **Folder:** `07_project/project_store/example_1_create_new_geopackage/`
- **Scenario:** Initializes project_store.gpkg and writes network and solution tables.
- **Expected Result:** Creates project_store.gpkg with full relational schema, network, and solution.
- **Parameters (`example.json`):**
  ```json
  {
    "STORE": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_1_create_new_geopackage/outputs/project_store.gpkg",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_1_create_new_geopackage/inputs/network.json",
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_1_create_new_geopackage/inputs/solution.json",
    "PROJECT_ID": "curitiba_dam_monitoring",
    "REPLACE": true
  }
  ```

#### Example 2: Append a second solution (sol_epoch_2) superseding sol_epoch_1
- **Folder:** `07_project/project_store/example_2_append_superseding_solution/`
- **Scenario:** Adds a new epoch solution to an existing GeoPackage and records lineage via SUPERSEDES.
- **Expected Result:** Appends sol_epoch_2 to project_store.gpkg with provenance link to sol_epoch_1.
- **Parameters (`example.json`):**
  ```json
  {
    "STORE": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_2_append_superseding_solution/outputs/project_store.gpkg",
    "SOLUTION": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_2_append_superseding_solution/inputs/solution_epoch2.json",
    "PROJECT_ID": "curitiba_dam_monitoring",
    "SUPERSEDES": "sol_epoch_1",
    "REPLACE": false
  }
  ```

#### Example 3: Replace contents of an existing GeoPackage store with a new network (REPLACE=True)
- **Folder:** `07_project/project_store/example_3_replace_existing_store/`
- **Scenario:** Overwrites an existing GeoPackage store cleanly with a fresh project and network.
- **Expected Result:** Replaces store contents with fresh_trilateration_project.
- **Parameters (`example.json`):**
  ```json
  {
    "STORE": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_3_replace_existing_store/outputs/replaced_store.gpkg",
    "NETWORK": "/home/kaue/geocomp/synthetic_examples/07_project/project_store/example_3_replace_existing_store/inputs/trilateration.json",
    "PROJECT_ID": "fresh_trilateration_project",
    "REPLACE": true
  }
  ```

### GeoComp ▸ Project ▸ Export project to PostGIS (`geocomp:project_export_postgis`)

#### Example 1: Export GeoComp GeoPackage project to PostGIS schema 'geocomp_curitiba'
- **Folder:** `07_project/project_export_postgis/example_1_export_to_default_schema/`
- **Scenario:** Copies all project, station, observation, and solution tables to PostGIS and verifies row-by-row equality.
- **Expected Result:** Copies all rows from project_store.gpkg to geocomp_local_pg / geocomp_curitiba and verifies 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/07_project/project_export_postgis/example_1_export_to_default_schema/inputs/project_store.gpkg",
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "geocomp_curitiba"
  }
  ```

#### Example 2: Export multi-epoch monitoring GeoPackage to PostGIS schema 'dam_monitoring_2024'
- **Folder:** `07_project/project_export_postgis/example_2_export_monitoring_archive/`
- **Scenario:** Transfers monitoring project store into a dedicated departmental PostGIS schema.
- **Expected Result:** Copies all rows from project_store.gpkg to geocomp_local_pg / dam_monitoring_2024 and verifies 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/07_project/project_export_postgis/example_2_export_monitoring_archive/inputs/project_store.gpkg",
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "dam_monitoring_2024"
  }
  ```

#### Example 3: Export classical survey GeoPackage to PostGIS schema 'ufpr_campus_control'
- **Folder:** `07_project/project_export_postgis/example_3_export_classical_campaign/`
- **Scenario:** Copies classical network store into PostGIS connection 'geocomp_local_pg'.
- **Expected Result:** Copies all rows from project_store.gpkg to geocomp_local_pg / ufpr_campus_control and verifies 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "SOURCE": "/home/kaue/geocomp/synthetic_examples/07_project/project_export_postgis/example_3_export_classical_campaign/inputs/project_store.gpkg",
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "ufpr_campus_control"
  }
  ```

### GeoComp ▸ Project ▸ Import project from PostGIS (`geocomp:project_import_postgis`)

#### Example 1: Import PostGIS project from schema 'geocomp_curitiba' into a portable GeoPackage
- **Folder:** `07_project/project_import_postgis/example_1_import_from_curitiba_schema/`
- **Scenario:** Copies every table from PostGIS schema 'geocomp_curitiba' into imported_curitiba.gpkg and verifies identity.
- **Expected Result:** Copies all rows from geocomp_local_pg / geocomp_curitiba into imported_geocomp_curitiba.gpkg with 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "geocomp_curitiba",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_import_postgis/example_1_import_from_curitiba_schema/outputs/imported_geocomp_curitiba.gpkg"
  }
  ```

#### Example 2: Import monitoring project from PostGIS schema 'dam_monitoring_2024' for offline field work
- **Folder:** `07_project/project_import_postgis/example_2_import_monitoring_snapshot/`
- **Scenario:** Creates an offline GeoPackage snapshot from 'dam_monitoring_2024'.
- **Expected Result:** Copies all rows from geocomp_local_pg / dam_monitoring_2024 into imported_dam_monitoring_2024.gpkg with 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "dam_monitoring_2024",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_import_postgis/example_2_import_monitoring_snapshot/outputs/imported_dam_monitoring_2024.gpkg"
  }
  ```

#### Example 3: Import classical network from PostGIS schema 'ufpr_campus_control'
- **Folder:** `07_project/project_import_postgis/example_3_import_campus_control/`
- **Scenario:** Round-trips 'ufpr_campus_control' back to a local GeoPackage file.
- **Expected Result:** Copies all rows from geocomp_local_pg / ufpr_campus_control into imported_ufpr_campus_control.gpkg with 0 differences.
- **Parameters (`example.json`):**
  ```json
  {
    "DATABASE": "geocomp_local_pg",
    "SCHEMA": "ufpr_campus_control",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_import_postgis/example_3_import_campus_control/outputs/imported_ufpr_campus_control.gpkg"
  }
  ```

### GeoComp ▸ Project ▸ Add base map (`geocomp:project_basemap`)

#### Example 1: Add default configured base map (OpenStreetMap Standard) reusing existing layer
- **Folder:** `07_project/project_basemap/example_1_default_osm_basemap/`
- **Scenario:** Adds the default XYZ tile base map to the bottom of the QGIS layer tree.
- **Expected Result:** Adds XYZ tile base map layer to the active QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "SERVICE": "",
    "REUSE": true
  }
  ```

#### Example 2: Add OpenTopoMap topographic base map (service='opentopomap')
- **Folder:** `07_project/project_basemap/example_2_opentopomap_topographic/`
- **Scenario:** Adds the OpenTopoMap contour/topographic backdrop ideal for field planning.
- **Expected Result:** Adds XYZ tile base map layer to the active QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "SERVICE": "opentopomap",
    "REUSE": true
  }
  ```

#### Example 3: Add OpenStreetMap layer forcing a second copy (REUSE=False)
- **Folder:** `07_project/project_basemap/example_3_force_new_basemap_layer/`
- **Scenario:** Inserts a fresh base map layer even when one is already present in the project.
- **Expected Result:** Adds XYZ tile base map layer to the active QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "SERVICE": "osm",
    "REUSE": false
  }
  ```

### GeoComp ▸ Project ▸ Create print layout (`geocomp:project_print_layout`)

#### Example 1: Deliverable 1: Network map with error ellipses, scale bar, north arrow, and legend
- **Folder:** `07_project/project_print_layout/example_1_network_map_with_ellipses/`
- **Scenario:** Creates a print layout framed around the project's adjusted stations and error ellipses.
- **Expected Result:** Creates print layout 'Curitiba_Network_Map' in the QGIS project layout manager.
- **Parameters (`example.json`):**
  ```json
  {
    "TEMPLATE": 0,
    "QUALITY": 0,
    "TITLE": "Curitiba Control Network — 95% Error Ellipses",
    "NAME": "Curitiba_Network_Map"
  }
  ```

#### Example 2: Deliverable 2: Monitoring displacement vector map
- **Folder:** `07_project/project_print_layout/example_2_displacement_monitoring_map/`
- **Scenario:** Builds a deformation map layout highlighting reference vs object stations and displacement arrows.
- **Expected Result:** Creates print layout 'Dam_Displacement_Map' in the project.
- **Parameters (`example.json`):**
  ```json
  {
    "TEMPLATE": 1,
    "QUALITY": 0,
    "TITLE": "Dam Deformation Vectors 2022–2024",
    "NAME": "Dam_Displacement_Map"
  }
  ```

#### Example 3: Deliverable 3: Internal reliability / Minimal Detectable Bias (MDB) quality map
- **Folder:** `07_project/project_print_layout/example_3_quality_redundancy_map/`
- **Scenario:** Styles network observations by Minimal Detectable Bias (QUALITY=2) and builds a thematic print layout.
- **Expected Result:** Creates thematic quality print layout 'MDB_Quality_Map'.
- **Parameters (`example.json`):**
  ```json
  {
    "TEMPLATE": 2,
    "QUALITY": 2,
    "TITLE": "Network Reliability — Minimal Detectable Bias",
    "NAME": "MDB_Quality_Map"
  }
  ```

### GeoComp ▸ Project ▸ GeoComp system report (`geocomp:project_system_report`)

#### Example 1: Standard GeoComp environment, QGIS, PROJ, and engine diagnostic report
- **Folder:** `07_project/project_system_report/example_1_standard_system_diagnostics/`
- **Scenario:** Generates an HTML diagnostic report detailing QGIS version, PROJ data paths, settings, and engine availability.
- **Expected Result:** Writes HTML system report with QGIS, Python, PROJ, and engine diagnostics.
- **Parameters (`example.json`):**
  ```json
  {
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_system_report/example_1_standard_system_diagnostics/outputs/system_report.html"
  }
  ```

#### Example 2: System report generated as a bug-report attachment
- **Folder:** `07_project/project_system_report/example_2_support_ticket_attachment/`
- **Scenario:** Produces a self-contained HTML environment snapshot suitable for attaching to an issue report.
- **Expected Result:** Writes HTML system report with QGIS, Python, PROJ, and engine diagnostics.
- **Parameters (`example.json`):**
  ```json
  {
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_system_report/example_2_support_ticket_attachment/outputs/system_report.html"
  }
  ```

#### Example 3: System report verifying custom RTKLIB and DynAdjust engine paths
- **Folder:** `07_project/project_system_report/example_3_post_engine_configuration_audit/`
- **Scenario:** Audits configured external engine binaries and effective Global Settings values.
- **Expected Result:** Writes HTML system report with QGIS, Python, PROJ, and engine diagnostics.
- **Parameters (`example.json`):**
  ```json
  {
    "OUTPUT_HTML": "/home/kaue/geocomp/synthetic_examples/07_project/project_system_report/example_3_post_engine_configuration_audit/outputs/system_report.html"
  }
  ```

### GeoComp ▸ Project ▸ Install tutorial dataset (`geocomp:project_tutorial_dataset`)

#### Example 1: Install tutorial dataset 'rd01' (Total Station Classical Network + worked .qgz project)
- **Folder:** `07_project/project_tutorial_dataset/example_1_install_rd01_total_station/`
- **Scenario:** Copies shipped tutorial dataset rd01 into destination folder and generates worked_example.qgz.
- **Expected Result:** Installs tutorial dataset 'rd01' and creates worked QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "DATASET": 0,
    "DESTINATION": "/home/kaue/geocomp/synthetic_examples/07_project/project_tutorial_dataset/example_1_install_rd01_total_station/outputs/tutorial_rd01",
    "OVERWRITE": true
  }
  ```

#### Example 2: Install tutorial dataset 'rd04-loop' (Spirit Levelling Loop)
- **Folder:** `07_project/project_tutorial_dataset/example_2_install_rd04_levelling_loop/`
- **Scenario:** Copies shipped levelling loop tutorial dataset rd04-loop with overwrite enabled.
- **Expected Result:** Installs tutorial dataset 'rd04-loop' and creates worked QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "DATASET": 2,
    "DESTINATION": "/home/kaue/geocomp/synthetic_examples/07_project/project_tutorial_dataset/example_2_install_rd04_levelling_loop/outputs/tutorial_rd04-loop",
    "OVERWRITE": true
  }
  ```

#### Example 3: Install tutorial dataset 'combined-curitiba' (Multi-technique GNSS + TS + Levelling)
- **Folder:** `07_project/project_tutorial_dataset/example_3_install_combined_curitiba/`
- **Scenario:** Installs the multi-technique Curitiba survey dataset and worked QGIS project.
- **Expected Result:** Installs tutorial dataset 'combined-curitiba' and creates worked QGIS project.
- **Parameters (`example.json`):**
  ```json
  {
    "DATASET": 5,
    "DESTINATION": "/home/kaue/geocomp/synthetic_examples/07_project/project_tutorial_dataset/example_3_install_combined_curitiba/outputs/tutorial_combined-curitiba",
    "OVERWRITE": true
  }
  ```

### GeoComp ▸ Project ▸ Install an engine (`geocomp:project_install_engine`)

#### Example 1: Download, verify SHA-256, and install DynAdjust with licence acknowledgement
- **Folder:** `07_project/project_install_engine/example_1_install_dynadjust_acknowledged/`
- **Scenario:** Installs DynAdjust binaries into the user's GeoComp engines directory after verifying SHA-256.
- **Expected Result:** Verifies archive checksum, extracts DynAdjust binaries, and records installed version.
- **Parameters (`example.json`):**
  ```json
  {
    "ENGINE": 0,
    "ACKNOWLEDGE_LICENCE": true
  }
  ```

#### Example 2: Download, verify SHA-256, and install RTKLIB (rnx2rtkp)
- **Folder:** `07_project/project_install_engine/example_2_install_rtklib/`
- **Scenario:** Installs RTKLIB's rnx2rtkp binary into the user's GeoComp engines directory.
- **Expected Result:** Verifies archive checksum, extracts rnx2rtkp, and reports installed version.
- **Parameters (`example.json`):**
  ```json
  {
    "ENGINE": 1,
    "ACKNOWLEDGE_LICENCE": false
  }
  ```

#### Example 3: Refuse DynAdjust installation when licence acknowledgement checkbox is unchecked
- **Folder:** `07_project/project_install_engine/example_3_dynadjust_without_licence_refused/`
- **Scenario:** Verifies that installing DynAdjust without ticking ACKNOWLEDGE_LICENCE raises a clear error.
- **Expected Result:** Refuses installation with a clear message asking to acknowledge DynAdjust's licence.
- **Parameters (`example.json`):**
  ```json
  {
    "ENGINE": 0,
    "ACKNOWLEDGE_LICENCE": false
  }
  ```

### GeoComp ▸ Project ▸ Package an engine problem (`geocomp:project_package_engine_problem`)

#### Example 1: Package a failed DynAdjust dnaimport working directory into a bug-report ZIP
- **Folder:** `07_project/project_package_engine_problem/example_1_dynadjust_failed_import/`
- **Scenario:** Bundles DynaML inputs, command log, stderr output, and README with upstream issue tracker URL.
- **Expected Result:** Creates dynadjust_problem_bundle.zip with ENGINE='DynAdjust' and README instructions.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_1_dynadjust_failed_import/inputs/dynadjust_work_dir",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_1_dynadjust_failed_import/outputs/dynadjust_problem_bundle.zip"
  }
  ```

#### Example 2: Package a failed RTKLIB rnx2rtkp working directory into a diagnostic ZIP
- **Folder:** `07_project/project_package_engine_problem/example_2_rtklib_failed_run/`
- **Scenario:** Bundles RINEX files, RTKLIB configuration, and invocation transcript into a reproducible archive.
- **Expected Result:** Creates rtklib_problem_bundle.zip with ENGINE='RTKLIB' and upstream reporting link.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_2_rtklib_failed_run/inputs/rtklib_work_dir",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_2_rtklib_failed_run/outputs/rtklib_problem_bundle.zip"
  }
  ```

#### Example 3: Package a multi-stage DynAdjust run where dnaimport succeeded but dnaadjust failed
- **Folder:** `07_project/project_package_engine_problem/example_3_dynadjust_singular_adjustment/`
- **Scenario:** Captures full multi-stage command history (dnaimport -> dnaadjust) in the diagnostic ZIP.
- **Expected Result:** Packages multi-stage logs into dynadjust_stage2_problem.zip.
- **Parameters (`example.json`):**
  ```json
  {
    "FOLDER": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_3_dynadjust_singular_adjustment/inputs/dynadjust_adjust_work_dir",
    "OUTPUT": "/home/kaue/geocomp/synthetic_examples/07_project/project_package_engine_problem/example_3_dynadjust_singular_adjustment/outputs/dynadjust_stage2_problem.zip"
  }
  ```

---
## Global Settings… (`08_global_settings`)

### GeoComp ▸ Global Settings… (`geocomp:global_settings_dialog`)

#### Example 1: Equipment profile libraries & meteorological defaults (Total Station, Level, Gravimeter)
- **Folder:** `08_global_settings/global_settings_dialog/example_1_equipment_profile_libraries/`
- **Scenario:** Configures custom JSON instrument library for Level and Curitiba plateau atmospheric defaults.
- **Expected Result:** Applies equipment profile paths and meteorological constants in Global Settings and verifies persistence.
- **Parameters (`example.json`):**
  ```json
  {
    "total_station.default_temperature_celsius": 22.5,
    "total_station.default_pressure_hpa": 915.0,
    "level.profile_library": "/home/kaue/geocomp/synthetic_examples/08_global_settings/global_settings_dialog/example_1_equipment_profile_libraries/inputs/level_profiles.json",
    "level.tolerance_coefficient": 0.004,
    "gravimeter.tide_amplification": 1.16
  }
  ```

#### Example 2: SIRGAS 2000 / UTM 22S (EPSG:31982) reference system, geoid model, and GNSS product mirror
- **Folder:** `08_global_settings/global_settings_dialog/example_2_gnss_and_reference_systems/`
- **Scenario:** Configures preferred CRS (EPSG:31982), epoch 2000.4, default geoid grid, and custom GNSS product download service JSON.
- **Expected Result:** Persists reference system, geoid model path, and GNSS service definitions in Global Settings.
- **Parameters (`example.json`):**
  ```json
  {
    "reference_systems.preferred_crs": "EPSG:31982",
    "reference_systems.default_epoch": 2000.4,
    "reference_systems.geoid_model": "/home/kaue/geocomp/synthetic_examples/08_global_settings/global_settings_dialog/example_2_gnss_and_reference_systems/inputs/curitiba_planar.asc",
    "reference_systems.geoid_sigma": 0.05,
    "gnss.elevation_mask": 15.0,
    "gnss.service_definitions": "/home/kaue/geocomp/synthetic_examples/08_global_settings/global_settings_dialog/example_2_gnss_and_reference_systems/inputs/custom_gnss_services.json",
    "gnss.product_fallback": true
  }
  ```

#### Example 3: 99% stochastic model, external engine paths (RTKLIB & DynAdjust), custom basemaps, and Advanced UI mode
- **Folder:** `08_global_settings/global_settings_dialog/example_3_stochastic_engines_and_interface/`
- **Scenario:** Configures Baarda snooping parameters, explicit engine paths, custom basemap catalogue, and Advanced DMS display.
- **Expected Result:** Updates stochastic, engine path, basemap, and UI settings and verifies GlobalSettingsDialog round-trip.
- **Parameters (`example.json`):**
  ```json
  {
    "stochastic.confidence_level": 0.99,
    "stochastic.outlier_alpha": 0.001,
    "stochastic.outlier_beta": 0.2,
    "paths.dynadjust_directory": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin",
    "paths.rtklib_program": "/home/kaue/geocomp/synthetic_examples/_shared_pipeline/bin/rnx2rtkp",
    "basemaps.catalogue": "/home/kaue/geocomp/synthetic_examples/08_global_settings/global_settings_dialog/example_3_stochastic_engines_and_interface/inputs/custom_basemaps.json",
    "interface.mode": "advanced",
    "interface.angle_format": "dms",
    "interface.coordinate_decimals": 4
  }
  ```
