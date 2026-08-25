# Archive — superseded planning documents

This folder holds planning material that is no longer authoritative but is kept for provenance.

| File | Origin | Status |
|---|---|---|
| [`2025-plugin-roadmap-v2.md`](./2025-plugin-roadmap-v2.md) | `plugin_roadmap.md` at repo root, written by an earlier agent | Superseded by [`../ROADMAP.md`](../ROADMAP.md) |

---

## Assessment of `2025-plugin-roadmap-v2.md`

The roadmap was reviewed line by line against the primary source
(`research_project/projeto_geocomp_abnt.tex`), the author's change notes
(`research_project/modificações.md`), the two design figures (`fig/menu_estrutura.png`,
`fig/workflow_geo_comp.png`), the prototype in `topo_test/`, and the upstream DynAdjust documentation.

It was **superseded rather than amended**, because its incorrect central premise propagates into its module
list, its file layout and its phase ordering — there is very little left once the premise is removed.

### Carried forward (the roadmap got these right)

- QGIS **Processing Provider** as an integration mechanism, with algorithms usable from the toolbox, the
  graphical modeller and batch mode → [`../16-processing-provider.md`](../16-processing-provider.md).
- The **pure-Python core / QGIS-free model layer** rule ("Ensure model layer is pure Python (no QGIS
  imports)") → kept and hardened into an enforced dependency rule in
  [`../03-architecture.md`](../03-architecture.md).
- **Subprocess wrapping of external engines** with captured stdout/stderr, return codes and timeouts →
  [`../07-engine-dynadjust.md`](../07-engine-dynadjust.md), [`../08-engine-rtklib.md`](../08-engine-rtklib.md).
- **Basic / Advanced usage profiles** → [`../18-i18n-and-profiles.md`](../18-i18n-and-profiles.md).
- **Trilingual UI** (PT-BR / EN / ES) via the QGIS translation system → same document.
- **GeoPackage for file mode, PostGIS optional** →
  [`../17-persistence-and-interoperability.md`](../17-persistence-and-interoperability.md).
- Styled result layers: error ellipses, residual vectors, thematic quality maps →
  [`../19-visualization.md`](../19-visualization.md).
- Testing with mocked subprocesses so CI can run without the engines installed →
  [`../20-testing-and-validation.md`](../20-testing-and-validation.md).

### Rejected or corrected

1. **The central premise is wrong.**
   > "The roadmap assumes all heavy geodetic math is delegated to **DynAdjust** and **RNX2RTKP**."
   > — `2025-plugin-roadmap-v2.md`, §Glossary

   DynAdjust adjusts networks and `rnx2rtkp` processes GNSS observations. Neither performs the
   *pre-processing* the project mandates: PD/PI reduction, atmospheric / instrument / EDM corrections,
   geometric reductions, traverse computation, resection, forward intersection, trigonometric levelling
   (including leap-frog), 3D radiation, the three geometric levelling methods, or gravimetric corrections.
   `topo_test/processing_prototype.ipynb` is the project author's own prototype of exactly this work, which
   settles the question: it is in-house computation. See
   [`../06-adjustment-core.md`](../06-adjustment-core.md) and the technique modules `09-`…`13-`.

2. **The GeoComp menu is missing entirely.** The proposal devotes a full subsection and a figure to a
   dedicated QGIS menu-bar entry with six groups (Estação Total, Nível, GNSS, Gravimetria, Integração,
   Configurações Globais), and `modificações.md` records that the author specifically asked for it. The
   roadmap describes only a Processing Provider. See
   [`../15-ui-menu-and-settings.md`](../15-ui-menu-and-settings.md).

3. **Covariance propagation is absent.** It is the proposal's stated central idea — every measurement and
   every derived quantity carries an uncertainty estimate, by rigorous *and* by approximate/heuristic means.
   The roadmap offers a single `sigma: float | dict` field on one dataclass. See
   [`../05-uncertainty-and-covariance.md`](../05-uncertainty-and-covariance.md).

4. **Multi-epoch comparison and structural monitoring are absent.** These are a specific objective (O6), a
   methodology section and an expected result in the proposal; the roadmap does not mention epochs at all.
   See [`../14-multi-epoch-monitoring.md`](../14-multi-epoch-monitoring.md).

5. **Statistical validation is absent.** No global chi-square test, no Baarda data snooping, no internal or
   external reliability, no error ellipses derived from theory. See
   [`../06-adjustment-core.md`](../06-adjustment-core.md).

6. **"Pre-analysis" is misdefined.** The roadmap describes `geocomp:network_preanalysis` as "connectivity,
   basic redundancy, simple consistency checks". In geodesy, network pre-analysis is *design and simulation*:
   deriving the covariance matrix of the parameters from the design matrix **A** and the weight matrix **P**
   alone, before any observation is made, to decide whether the planned network meets its precision and
   reliability specification. Both features are useful; they are now separate requirements.

7. **Gravimetry has no engine.** DynAdjust has no gravity measurement type, so gravimetric network adjustment
   must run on the in-house least-squares core that the roadmap's premise declares unnecessary. See
   [`../12-module-gravimetry.md`](../12-module-gravimetry.md).

8. **The DynAdjust interface is misdescribed.** The roadmap proposes
   `run_dynadjust(work_dir, executable="dynadjust")`. DynAdjust is a suite of programs — `dnaimport`,
   `dnareftran`, `dnageoid`, `dnasegment`, `dnaadjust`, `dnaplot` — driven as a pipeline, accepting DNA,
   DynaML and SINEX input. See [`../07-engine-dynadjust.md`](../07-engine-dynadjust.md).

9. **Engine acquisition is not addressed.** The proposal promises installation "com poucos cliques" — install
   QGIS, install the plugin, done. The roadmap never says how a user obtains the DynAdjust or RTKLIB binaries.
   See [`../adr/0003-engine-acquisition.md`](../adr/0003-engine-acquisition.md).

10. **The phase ordering is counterproductive.**
    - i18n is deferred to Phase 9. Retrofitting translation calls across a finished codebase is expensive;
      string discipline from the first commit is nearly free. i18n plumbing now lands in P0.
    - Nothing in the product works until an external binary is present (DynAdjust is Phase 4, and no
      in-house computation exists). This blocks CI and blocks the teaching use case. The revised roadmap
      delivers a complete, demoable vertical slice with no external engine by P3, and introduces DynAdjust
      at P6 as a second engine that cross-validates the first.

11. **The licensing conflict went unnoticed.** The proposal promises a permissive licence, but
    plugins.qgis.org requires GPLv2-or-later and PyQGIS/PyQt are GPL. See
    [`../adr/0001-licensing.md`](../adr/0001-licensing.md).

12. **"Create these files even if initially empty"** (§2) is rejected. Empty placeholder files drift from the
    specification and give a false impression of progress. Files are created when the phase that fills them
    begins.

### Repository layout difference

The roadmap proposed a top-level `geocomp-qgis-plugin/` directory containing a `geocomp/` package. The
adopted layout places the installable plugin package directly at `geocomp/` in this repository, with
specifications at `specs/`. See [`../03-architecture.md`](../03-architecture.md).
