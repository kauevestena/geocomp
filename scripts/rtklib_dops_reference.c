/* SPDX-License-Identifier: GPL-2.0-or-later
 *
 * Reference dilutions of precision from RTKLIB's own dops(), for
 * tests/data/rtklib/dops/ (P12c-35).
 *
 * GeoComp computes DOP from the satellite geometry rnx2rtkp writes to its
 * solution-status file (-y 2, the $SAT lines). This program computes it with
 * RTKLIB's function, from the same lines, so the test compares GeoComp with
 * RTKLIB rather than with a second copy of GeoComp's own arithmetic.
 *
 * Build against the pinned RTKLIB-EX source and run on a .stat file:
 *
 *   cc -O2 -I$RTKLIB/src -DENAGLO -DENAQZS -DENAGAL -DENACMP -DENAIRN -DNFREQ=4 -DNEXOBS=3 \
 *      scripts/rtklib_dops_reference.c $RTKLIB/src/rtkcmn.c $RTKLIB/src/trace.c -lm -o dops-reference
 *   ./dops-reference solution.pos.stat > dops.csv
 *
 * One row per epoch: the GPS week and time of week, the satellites counted,
 * and GDOP, PDOP, HDOP, VDOP. A satellite counts when its first-frequency line
 * is marked valid (vsat 1), as the solution used it; the cutoff passed to
 * dops() is zero, because the engine's own elevation mask already decided
 * which satellites have lines at all.
 */
#include <stdio.h>
#include <string.h>
#include "rtklib.h"

static void flush(int week, double tow, int n, const double *azel)
{
    double dop[4];
    if (n == 0) return;
    dops(n, azel, 0.0, dop);
    printf("%d,%.3f,%d,%.6f,%.6f,%.6f,%.6f\n", week, tow, n, dop[0], dop[1], dop[2], dop[3]);
}

int main(int argc, char **argv)
{
    FILE *fp;
    char line[1024], id[16];
    double azel[2 * MAXSAT], tow, cur_tow = -1.0, az, el, resp, resc;
    int week, cur_week = -1, frq, vsat, n = 0;

    if (argc < 2 || !(fp = fopen(argv[1], "r"))) {
        fprintf(stderr, "usage: dops-reference solution.pos.stat\n");
        return 1;
    }
    printf("week,tow,satellites,gdop,pdop,hdop,vdop\n");
    while (fgets(line, sizeof line, fp)) {
        if (strncmp(line, "$SAT,", 5)) continue;
        for (char *p = line; *p; p++) if (*p == ',') *p = ' ';
        if (sscanf(line + 4, "%d %lf %15s %d %lf %lf %lf %lf %d", &week, &tow, id, &frq, &az,
                   &el, &resp, &resc, &vsat) < 9) continue;
        if (week != cur_week || tow != cur_tow) {
            flush(cur_week, cur_tow, n, azel);
            cur_week = week; cur_tow = tow; n = 0;
        }
        if (frq != 1 || vsat != 1 || n >= MAXSAT) continue;
        azel[2 * n] = az * D2R;
        azel[2 * n + 1] = el * D2R;
        n++;
    }
    flush(cur_week, cur_tow, n, azel);
    fclose(fp);
    return 0;
}
