<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Live demo run-sheet (Ubuntu 22.04 / 24.04, QGIS)

What was checked, what was not, and what to do if something misbehaves on stage.

## Before the day — do all of this once, on the presentation machine

1. **QGIS 4.0 or later must be installed and start.** The plugin's declared minimum is 4.0 and it will not
   load on 3.x. This is the one thing this sheet cannot check for you: confirm `Help ▸ About` says 4.x.
2. **Install the plugin**: `Plugins ▸ Manage and Install Plugins ▸ Install from ZIP`, choose `geocomp.zip`
   (the `geocomp-plugin` artifact of the latest green `build` run). Tick *Show also experimental plugins* if it
   is not listed. A **GeoComp** menu should appear.
3. **Check the engine**: `GeoComp ▸ Project ▸ System report` (or the About dialog). It should say
   `RTKLIB-EX 2.5.1`, source **bundled**. DynAdjust is *not* needed for either example below.
4. **Install both datasets** into a folder you can write to: `GeoComp ▸ Project ▸ Install tutorial dataset`,
   once for `rd01`, once for `rtklib-sample`. Do it before the audience arrives.
5. **Run both examples once at home**, with the projector off. A first run is the only time you meet a surprise.

## Example 1 — an adjustment (about 5 minutes)

Dataset `rd01`: the author's total-station triangle. Its own `README.md` is the script — follow it step by
step. The point to make: **it contains two real errors, and the software finds both** — a 1.000 m
transcription blunder blocked at pre-processing, and a global test that correctly fails.

## Example 2 — a GNSS baseline (about 4 minutes)

Dataset `rtklib-sample`. `GeoComp ▸ GNSS ▸ Relative — Static`:

| Field | Value |
|---|---|
| Folder of RINEX observations | the `rtklib-sample` folder you installed |
| Base station | `3040` |
| Rover station | `0759` |

Leave everything else. Expect, in the log: *Using RTKLIB-EX 2.5.1* from inside the plugin; **120 epochs, 97.5 %
with resolved ambiguities** (117 fixed, 3 float); a note that the navigation file was *paired by fallback*
(harmless); and a note that base `3040` is not in the reference-station database, so the results are **in no
stated frame**.

**Say this out loud:** the example shows the whole chain running — session discovery, the engine, the
solution reader, the quality figures, the map layer. It does **not** show that the coordinates are accurate:
the two stations have no published coordinates here to compare with.

## What was and was not verified (as of this sheet)

| | |
|---|---|
| The bundled `rnx2rtkp` builds on Ubuntu 22.04, links only libc and libm, and reproduces the committed fixtures | **checked in CI** |
| The plugin, unpacked the way QGIS does it, finds and runs the bundled program with nothing on `PATH` | **checked in CI** (in the QGIS stable container) |
| The GNSS run through the bundled program: engine, solution file, quality summary | **checked here**, headless: 120 epochs, 117 fixed |
| The **result layer on the map**, and the **dialogs** | **not checked here** — the QGIS available while building this is older than 4.0. Covered by the QGIS tier of CI, but not looked at by eye. **Look at it at home.** |
| Windows and macOS | **not built** |

## If something goes wrong on stage

- **No GeoComp menu**: the plugin is installed but not enabled — `Plugins ▸ Manage and Install Plugins ▸ Installed`.
- **"rnx2rtkp not found"**: the bundled copy was not unpacked or is not executable. Set a path to your own in
  `GeoComp ▸ Global Settings ▸ Paths and engines`; a configured path always wins.
- **A result looks wrong**: say so and show the provenance — every result records the program, its version and
  its exact command line. That is a feature, and it is the honest answer.
- Have the `.pos` solution and the `summary.json` from your home run open in another window as a fallback.
