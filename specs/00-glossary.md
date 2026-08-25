# 00 — Glossary

**Status:** Draft
**Purpose:** fix the meaning of every term used across these specifications, and fix its PT-BR and ES
rendering so that the trilingual UI stays terminologically consistent.

This document does double duty. For developers it disambiguates words that are overloaded (a "network" in
QGIS is not a "network" in geodesy). For translators it is normative: the PT-BR and ES columns are the
**required** translations — see [`18-i18n-and-profiles.md`](./18-i18n-and-profiles.md).

---

## 1. Project and data organisation

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| Project | Projeto | Proyecto | The top-level GeoComp container: one working area holding campaigns, networks, settings and results. Persisted as a GeoPackage or a PostGIS schema |
| Campaign | Campanha | Campaña | A field effort that produced observations, bounded in time and by crew/instrument. A campaign belongs to exactly one epoch |
| Epoch | Época | Época | (a) The reference date of a coordinate set, e.g. `2020.0`; (b) informally, one measurement occasion in a monitoring series. GeoComp always uses sense (a) in data; sense (b) is called a *monitoring epoch* |
| Network | Rede | Red | A set of stations connected by observations, adjusted as one unit |
| Station | Estação | Estación | A geodetic point with an identifier, approximate coordinates, and a constraint status. Also *mark*, *point* |
| Observation | Observação | Observación | One measurement relating one or more stations. See §3 for types |
| Cluster | Agrupamento | Agrupamiento | A set of observations sharing one full covariance matrix — e.g. a GNSS baseline vector, or a set of directions from one setup |
| Setup | Estacionamento | Estacionamiento | One occupation of one station by one instrument; the unit within which directions are internally consistent |
| Solution | Solução | Solución | The output of one adjustment or processing run: coordinates, covariance, residuals, statistics, provenance |
| Run | Execução | Ejecución | One invocation of an engine or algorithm, with its inputs, parameters, logs and exit status recorded |
| Provenance | Proveniência | Procedencia | The recorded chain of inputs, parameters, software versions and timestamps that produced a result |

## 2. Adjustment and statistics

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| Least squares | Mínimos quadrados | Mínimos cuadrados | Estimation by minimising **v**ᵀ**Pv** |
| Parametric model | Modelo paramétrico | Modelo paramétrico | Observation-equation form, **L**_b + **v** = **A x** + **L**₀ |
| Design matrix | Matriz design | Matriz de diseño | **A**, the Jacobian of the observation equations with respect to the parameters |
| Weight matrix | Matriz peso | Matriz de pesos | **P**, inversely proportional to the observation covariance matrix |
| Residual | Resíduo | Residuo | **v**, the correction applied to an observation by the adjustment |
| Variance factor | Fator de variância | Factor de varianza | σ₀², the variance of unit weight. *A priori* is assumed; *a posteriori* is estimated from the adjustment |
| Degrees of freedom | Graus de liberdade | Grados de libertad | Number of observations minus number of estimated parameters; equals total redundancy |
| Redundancy number | Número de redundância | Número de redundancia | rᵢ, the share of redundancy carried by observation *i*. Controls how visible a blunder in that observation is |
| Covariance matrix | Matriz variância-covariância | Matriz de varianza-covarianza | **Σ**, the full second-moment description of a quantity's uncertainty |
| Cofactor matrix | Matriz cofatora | Matriz cofactor | **Q** = **Σ** / σ₀² |
| Error ellipse | Elipse de erro | Elipse de error | The 2D confidence region of an adjusted position, from the eigen-decomposition of its 2×2 covariance block |
| Error ellipsoid | Elipsoide de erro | Elipsoide de error | The 3D equivalent |
| Positional uncertainty | Incerteza posicional | Incertidumbre posicional | A single scalar summary of positional quality at a stated confidence level (as reported in DynAdjust `.apu` files) |
| Global test | Teste global | Prueba global | The chi-square test comparing the a posteriori and a priori variance factors |
| Data snooping | Data snooping | Data snooping | Baarda's procedure of testing standardised residuals one at a time to locate an outlier. Term kept in English in all locales — it is used untranslated in the literature |
| Outlier / blunder | Erro grosseiro | Error grosero | An observation whose error is inconsistent with its assumed stochastic model |
| Internal reliability | Confiabilidade interna | Fiabilidad interna | The size of blunder the network can detect, per observation (the MDB) |
| External reliability | Confiabilidade externa | Fiabilidad externa | The effect on the coordinates of a blunder just too small to be detected |
| MDB (minimal detectable bias) | MDB (erro máximo não detectável) | MDB (sesgo mínimo detectable) | The smallest blunder in an observation detectable with stated α and β |
| Free network | Rede livre | Red libre | A network with no external coordinate constraints; the datum defect is removed by a minimum-constraint or inner-constraint solution |
| Constrained network | Rede amarrada / vinculada | Red ligada | A network in which one or more stations are held fixed or weighted to external coordinates |
| Datum defect | Deficiência de datum | Deficiencia de datum | The rank deficiency of a network with no datum definition |
| Pre-analysis | Pré-análise | Preanálisis | Computing the expected precision and reliability of a *planned* network from its geometry and assumed precisions, before any observation is made |
| Variance propagation | Propagação de variâncias | Propagación de varianzas | Deriving **Σ** of a derived quantity from **Σ** of its inputs, **Σ**_La = **A Σ**_Lb **A**ᵀ |

## 3. Observations and instruments

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| Total station | Estação total | Estación total | Combined electronic theodolite and EDM |
| Level | Nível | Nivel | Instrument for geometric (differential) levelling |
| Gravimeter | Gravímetro | Gravímetro | Instrument measuring gravity or gravity differences |
| Horizontal angle | Ângulo horizontal | Ángulo horizontal | The angle between two directions measured in the horizontal plane |
| Direction | Direção | Dirección | A single horizontal circle reading within a setup; a set of directions shares an unknown orientation parameter |
| Zenith angle | Ângulo zenital | Ángulo cenital | Angle from the local zenith to the line of sight |
| Vertical angle | Ângulo vertical | Ángulo vertical | Angle from the horizon to the line of sight; equals 90° − zenith angle |
| Slope distance | Distância inclinada | Distancia inclinada | The measured straight-line distance between instrument and target |
| Horizontal distance | Distância horizontal | Distancia horizontal | Slope distance reduced to the horizontal |
| Height difference | Desnível | Desnivel | The vertical separation of two points |
| Face left / Face right | PD (pontaria direta) / PI (pontaria inversa) | Círculo directo / Círculo inverso | The two telescope positions; combining them cancels several instrumental errors. The abbreviations **PD**/**PI** are used throughout the PT-BR UI and in the reference dataset RD-01 |
| Backsight / Foresight | Ré / Vante | Espalda / Frente | The direction observed to the previous / next point. Abbreviated **R**/**V** in RD-01 |
| Instrument height | Altura do instrumento | Altura del instrumento | Height of the instrument's trunnion axis above the mark (`hi`) |
| Target height | Altura do alvo / do sinal | Altura de la señal | Height of the target above the mark (`hs`) |
| EDM | MED (medidor eletrônico de distância) | MED | Electronic distance measurement unit |
| Prism constant | Constante do prisma | Constante del prisma | Additive correction specific to a reflector |
| Scale correction | Correção de escala | Corrección de escala | Multiplicative correction, e.g. ppm from atmospheric conditions |
| Collimation error | Erro de colimação | Error de colimación | Non-perpendicularity of line of sight and horizontal axis |
| Vertical index error | Erro de índice vertical | Error de índice vertical | Offset of the vertical circle zero from the true zenith |
| Traverse | Poligonação / poligonal | Poligonal | A chain of stations connected by successive angle and distance observations |
| Resection | Interseção à ré | Intersección inversa | Determining an occupied station's coordinates from sights to known points |
| Forward intersection | Interseção à vante | Intersección directa | Determining a sighted point's coordinates from known stations |
| Triangulation | Triangulação | Triangulación | A classical network determined mainly by angles |
| Trilateration | Trilateração | Trilateración | A classical network determined mainly by distances |
| Triangulateration | Triangulateração | Triangulateración | A classical network using both angles and distances |
| Trigonometric levelling | Nivelamento trigonométrico | Nivelación trigonométrica | Height differences from zenith angles and slope distances |
| Leap-frog | Leap-frog | Leap-frog | A trigonometric-levelling scheme with the instrument between two targets, cancelling refraction and height errors. Term kept in English in all locales |
| 3D radiation | Irradiação 3D | Radiación 3D | Three-dimensional coordinates of a point from one setup: horizontal angle, zenith angle, slope distance and heights |
| Geometric levelling | Nivelamento geométrico | Nivelación geométrica | Height differences from horizontal sights on graduated staves |
| Equal sights | Visadas iguais | Visuales iguales | Levelling with backsight and foresight distances equal — the preferred method |
| Equidistant sights | Visadas equidistantes | Visuales equidistantes | Levelling scheme used to cross obstacles such as rivers |
| Extreme sights | Visadas extremas | Visuales extremas | Levelling with multiple foresights from one setup |
| Instrument drift | Deriva | Deriva | Slow change of a gravimeter's reading with time; static and dynamic components are modelled separately |
| Tidal correction | Correção de maré | Corrección de marea | Removal of the solid-Earth and ocean-loading tidal signal from gravity readings |

## 4. GNSS

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| GNSS session | Sessão GNSS | Sesión GNSS | One continuous observation period by one receiver at one station |
| Baseline | Linha de base | Línea base | The 3D vector between two simultaneously observing stations, with its 3×3 covariance |
| Absolute positioning | Posicionamento absoluto | Posicionamiento absoluto | Position determined directly with respect to the geocentre |
| Relative positioning | Posicionamento relativo | Posicionamiento relativo | Position determined with respect to one or more known stations |
| Static | Estático | Estático | Receiver stationary throughout the session |
| Kinematic | Cinemático | Cinemático | Receiver in motion; a position per epoch |
| PPP | PPP (posicionamento por ponto preciso) | PPP | Precise Point Positioning: absolute positioning using precise orbit and clock products |
| Ambiguity resolution | Resolução de ambiguidades | Resolución de ambigüedades | Recovering the integer cycle count of the carrier phase |
| Fixed / float solution | Solução fixa / flutuante | Solución fija / flotante | Whether ambiguities were resolved to integers |
| Elevation mask | Máscara de elevação | Máscara de elevación | Minimum satellite elevation accepted |
| RINEX | RINEX | RINEX | Receiver-Independent Exchange format for GNSS observations and navigation messages |
| Precise ephemeris | Efemérides precisas | Efemérides precisas | Post-processed satellite orbits (SP3) |
| Clock product | Produto de relógio | Producto de reloj | Post-processed satellite clock corrections (CLK) |
| Antenna model | Modelo de antena | Modelo de antena | Phase-centre offsets and variations (ANTEX) |

## 5. Reference systems and heights

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| CRS | SRC (sistema de referência de coordenadas) | SRC | Coordinate reference system |
| Datum | Datum | Datum | The realisation that fixes origin, orientation and scale of a CRS |
| Reference epoch | Época de referência | Época de referencia | The date to which a datum's coordinates refer |
| Geodetic coordinates | Coordenadas geodésicas | Coordenadas geodésicas | Latitude, longitude, ellipsoidal height |
| Cartesian coordinates | Coordenadas cartesianas | Coordenadas cartesianas | Geocentric X, Y, Z |
| Projected coordinates | Coordenadas projetadas | Coordenadas proyectadas | Plane E, N in a map projection such as UTM |
| Ellipsoidal height | Altitude geométrica / elipsoidal | Altura elipsoidal | Height above the reference ellipsoid (h) |
| Orthometric height | Altitude ortométrica | Altura ortométrica | Height above the geoid (H) |
| Geoid undulation | Ondulação geoidal | Ondulación geoidal | N = h − H |
| Deflection of the vertical | Desvio da vertical | Desviación de la vertical | Angle between the plumb line and the ellipsoid normal |

## 6. Monitoring and deformation

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| Monitoring epoch | Época de monitoramento | Época de monitoreo | One complete survey of a monitoring network at one occasion |
| Displacement | Deslocamento | Desplazamiento | The coordinate difference of a station between two epochs |
| Deformation | Deformação | Deformación | The pattern of relative displacement across a body or network |
| Congruency test | Teste de congruência | Prueba de congruencia | A statistical test of whether two epochs' coordinate sets differ by more than their uncertainty |
| Reference (stable) block | Bloco de referência / pontos estáveis | Bloque de referencia | The subset of stations assumed not to move, used to relate epochs |
| Object points | Pontos objeto | Puntos objeto | The stations on the structure being monitored |
| Alert threshold | Limite de alerta | Umbral de alerta | A displacement magnitude above which the plugin flags a station |
| Time series | Série temporal | Serie temporal | The sequence of a station's coordinates across monitoring epochs |

## 7. Software and platform

| EN (source) | PT-BR | ES | Meaning |
|---|---|---|---|
| Engine | Motor (de processamento) | Motor | An external command-line program that performs a computation for GeoComp |
| DynAdjust | DynAdjust | DynAdjust | Geoscience Australia's least-squares network adjustment suite. See [`07-engine-dynadjust.md`](./07-engine-dynadjust.md) |
| RTKLIB / `rnx2rtkp` | RTKLIB / `rnx2rtkp` | RTKLIB / `rnx2rtkp` | GNSS post-processing package and its command-line post-processing tool. See [`08-engine-rtklib.md`](./08-engine-rtklib.md) |
| Processing Provider | Provedor de processamento | Proveedor de procesamiento | The QGIS mechanism that makes algorithms available in the toolbox, the modeller, batch mode and PyQGIS |
| Processing algorithm | Algoritmo de processamento | Algoritmo de procesamiento | A single `QgsProcessingAlgorithm` with declared inputs and outputs |
| Basic mode | Modo básico | Modo básico | Usage profile exposing a reduced parameter set with sensible defaults |
| Advanced mode | Modo avançado | Modo avanzado | Usage profile exposing the full parameter set |
| Global Settings | Configurações Globais | Configuraciones Globales | The GeoComp settings window, organised by equipment type |
| Reference dataset | Conjunto de dados de referência | Conjunto de datos de referencia | A dataset with an independently known correct answer, used to validate GeoComp |

---

## Terms deliberately *not* translated

`data snooping`, `leap-frog`, `RINEX`, `PPP`, `RTK`, `SINEX`, `DynaML`, `GeoPackage`, `PostGIS`, `RTKLIB`,
`DynAdjust`, and all file extensions and command names. These appear identically in all three locales.

## Ambiguities resolved

- **"Network"** always means a geodetic network. QGIS layer connections are called *layers* or *connections*.
- **"Epoch"** in data always means a coordinate reference epoch. A measurement occasion is a
  *monitoring epoch*. GNSS per-observation instants are called *sample instants*.
- **"Precision" vs "accuracy"** — precision describes dispersion (what a covariance matrix expresses);
  accuracy describes closeness to truth (which requires an independent reference). GeoComp's adjustment
  reports precision; validation against reference datasets reports accuracy.
- **"Gravimetry" vs "Gravimeter"** — the proposal names the menu group *Gravímetro* in the text and
  *Gravimetria* in `fig/menu_estrutura.png`. GeoComp uses **Gravimetry / Gravimetria / Gravimetría**,
  matching the figure and matching the technique-based naming of the other groups.
