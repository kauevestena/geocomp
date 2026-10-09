# RD-08 presa — dos épocas de una estructura monitoreada, y el único punto que se movió

**Conjunto de datos de referencia RD-08, su mitad sintética** (`specs/20-testing-and-validation.md` §3,
FR-950, FR-952), el tutorial de monitoreo. Versión en español del README.md; los números, los nombres y los
valores que se escriben son los mismos.

Cuatro pilares de referencia en terreno estable alrededor de una estructura, R1 a R4, en un terreno de 1200 m
por 900 m, y cinco objetivos en la propia estructura, O1 a O5. Cada par de los nueve se mide por distancia, 36
distancias en cada época, cada una a 1 mm. La red se midió en 2025 y de nuevo en 2026. Entretanto, **O2 se movió
8 mm hacia el este y 6 mm hacia el sur.**

**Estos datos son construidos, y así se dice.** Las distancias se generaron a partir de posiciones elegidas de
antemano, con 1 mm de ruido de una semilla fija en cada época, y el movimiento se puso en las posiciones de la
segunda época. Así se conoce la respuesta exactamente, y así se prueba el monitoreo de GeoComp
(`tests/monitoring_network.py`). No es una estructura que alguien haya levantado.

El tutorial ajusta cada época, compara las dos, encuentra O2, y después muestra qué pasa cuando las estaciones
que se toman por estables no lo son.

**Números.** En el texto, los números usan la coma decimal. Los valores entre comillas invertidas se escriben
tal como aparecen. El mensaje que da GeoComp en el último paso se cita tal como él lo escribe.

---

## Los archivos

| Archivo | Qué es |
|---|---|
| `epoch-2025.json` | La primera época, tal como se midió: la posición aproximada de cada estación y las 36 distancias (un documento de red de GeoComp) |
| `epoch-2026.json` | La segunda época, de la misma manera |
| `thresholds.csv` | Un umbral de alerta: 5 mm de movimiento en cualquiera de los cinco objetivos |

---

## Paso a paso

### 1. Ajustar red — `geocomp:analysis_network_adjust`

La primera época, apoyada en los cuatro pilares.

- **Documento de la red**: `epoch-2025.json`
- **Marco de coordenadas**: *2D — planimétrico (E, N)*
- **Definición del datum**: *Constricción mínima — sobre las estaciones elegidas*
- **Estaciones del datum (separadas por comas; vacío = todas)**: `R1,R2,R3,R4`
- **Solución**: `solution-2025.json`

Treinta y seis distancias y nueve estaciones: **21 grados de libertad.** La prueba global pasa, con un factor de
varianza a posteriori de **1,14**: las distancias concuerdan entre sí tan bien como su 1 mm dice que deberían.

El data snooping enumera **3** observaciones cuya prueba w supera el valor crítico de 1,94, la mayor con
**2,37**. Son ruido. Con un 95 % de confianza, una observación buena de cada veinte supera el valor crítico por
azar, y 36 de ellas dan unas dos. GeoComp no rechaza ninguna, y en el monitoreo eso importa: una observación
eliminada porque discrepa de las demás puede ser el movimiento que se vino a medir.

### 2. Ajustar red — `geocomp:analysis_network_adjust`

La segunda época, de la misma manera.

- **Documento de la red**: `epoch-2026.json`
- **Marco de coordenadas**: *2D — planimétrico (E, N)*
- **Definición del datum**: *Constricción mínima — sobre las estaciones elegidas*
- **Estaciones del datum (separadas por comas; vacío = todas)**: `R1,R2,R3,R4`
- **Solución**: `solution-2026.json`

La prueba global pasa de nuevo, con un factor de varianza de **1,18**. Nada en ninguno de los dos ajustes dice
que algo se haya movido. Una sola época no puede decirlo: el movimiento está entre ellas.

### 3. Comparar dos épocas — `geocomp:monitoring_compare_epochs`

- **Primera época (solución)**: `solution-2025.json`
- **Segunda época (solución)**: `solution-2026.json`
- **Estaciones de referencia (separadas por comas)**: `R1,R2,R3,R4`
- **Umbrales de alerta (CSV)**: `thresholds.csv`
- **Documento del análisis**: `comparison.json`
- **Informe de monitoreo**: algún lugar donde pueda abrirlo

Desde el menú, *GeoComp ▸ Análisis ▸ Comparar dos épocas* muestra primero si las dos soluciones se pueden
comparar: el mismo marco, épocas declaradas, las mismas estaciones. Estas se pueden.

**El bloque de referencia se prueba primero**, porque todo desplazamiento se mide respecto de él. Su prueba de
congruencia da **0,59** frente a un valor crítico de **2,44**: los pilares no se han movido unos respecto de
otros. La de la red entera da **16,07** frente a **1,91**: otra cosa sí se ha movido.

**Movimiento significativo en una estación: O2**, de **10,8 mm**, 8,7 mm hacia el este y 6,5 mm hacia el sur. Su
prueba da **77,1** frente a **3,22**. Se movió 10,0 mm; los otros 0,8 mm son el ruido de la medición de dos
épocas, bien dentro de su elipse del 95 % de **3,0 por 2,1 mm**. De los demás objetivos, el mayor desplazamiento
es el de O3, de **2,0 mm**, y ninguno es significativo.

El umbral de alerta se supera solo en O2. Es una cuestión distinta de la significancia. Un movimiento
significativo menor que el umbral es real pero tolerable; un movimiento mayor que el umbral que no es
significativo no se distingue del ruido, y el informe dice cuál es cuál.

**Pruebe esto:** ajuste las dos épocas de nuevo con *Definición del datum* en *Constricción interna — red libre,
traza mínima*, que no fija ninguna estación en particular, y compárelas. Los desplazamientos salen iguales, hasta
la décima de micrómetro. La comparación transforma las dos épocas al bloque de referencia antes de medir nada,
así que el datum en que se ajustó cada época no importa. **Importa qué estaciones son la referencia.**

### 4. Un bloque de referencia que se ha movido

Compare de nuevo, dando las **Estaciones de referencia (separadas por comas)** como `R1,R2,R3,R4,O2`: como si O2
fuera un pilar. GeoComp se niega:

> El bloque de referencia se ha movido: su prueba de congruencia da 28.8678 frente a un valor crítico de 2.2371,
> y la localización implica a O2. El análisis no continúa sobre un bloque que se ha movido, porque ese
> movimiento se repartiría entre todas las demás estaciones. Las estaciones que permanecen estables son R1, R2,
> R3, R4. Revise los pilares implicados y analice de nuevo con ellos entre los puntos objeto.

y dice dónde escribió la localización. Tomado como estable, los 10,8 mm de O2 se habrían repartido entre los
otros cuatro pilares y aparecido, menores y en la dirección equivocada, en todos los objetivos de la estructura.

---

## Qué llevarse

- **El movimiento está entre las épocas.** Cada ajuste por sí solo pasa, y no tiene nada que decir sobre él.
- **El bloque de referencia se prueba antes de medir nada respecto de él.** Un pilar que se movió y se toma por
  estable mueve todo lo demás.
- **El datum de cada época no importa; la elección de las estaciones de referencia sí.**
- **Significativo y alarmante son preguntas distintas.** La significancia se mide frente a la incertidumbre del
  propio desplazamiento; un umbral es un límite de ingeniería.
- **El data snooping al 95 % señala observaciones buenas por azar.** GeoComp las enumera y no rechaza ninguna.
