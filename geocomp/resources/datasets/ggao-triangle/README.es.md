<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Triángulo GGAO — tres receptores GNSS, dos horas, y un circuito que dice en qué hora confiar

Versión en español del README.md; los números, los nombres y los valores que se escriben son los mismos. En el
texto, los números usan la coma decimal; lo que GeoComp escribe en el registro se cita tal como él lo escribe,
con punto.

Tres estaciones GNSS permanentes en el Goddard Geophysical and Astronomical Observatory de la NASA, en
Greenbelt, Maryland: **GODN**, **GODE** y **GODS**, a pocos pasos una de otra, observando juntas el 1 de enero
de 2025. Dos horas de ese día, cada una en su carpeta:

| Carpeta | Hora (tiempo GPS) | Qué contiene |
|---|---|---|
| `hour-00` | 00:00 a 00:59:30 | Una hora corriente |
| `hour-11` | 11:00 a 11:59:30 | La hora en que la propia validación de GeoComp encontró una falla (`specs/22-reference-data-sources.md` §5.1) |

Cada carpeta tiene las observaciones de las tres estaciones, `godn0010.25o`, `gode0010.25o` y `gods0010.25o`, y
el archivo de navegación transmitida del día, `brdc0010.25n.gz`.

**Los datos son de la NOAA.** Vienen de la red NOAA CORS, operada por el National Geodetic Survey; el Goddard de
la NASA suministró las observaciones. Cada archivo de observación es el archivo que la NOAA publicó para el día,
cortado a la hora y reducido al GPS y a los ocho observables que lee una solución GPS de doble frecuencia. No se
cambió ningún valor, y `scripts/make_ggao_triangle.py` rehace los archivos a partir de los de la NOAA. El
`NOTICE.md`, junto a este archivo, da la atribución y los términos.

El tutorial trata de una verificación, el **cierre del circuito**: tres líneas base alrededor de un triángulo
deberían sumar cero. No necesita ninguna coordenada publicada, y dice cuándo un conjunto de líneas base está en
desacuerdo consigo mismo.

---

## Paso a paso

### 1. Instalar conjunto de datos del tutorial — `geocomp:project_tutorial_dataset`

Si está leyendo esto en la carpeta en la que se instaló, este paso está hecho. Si no, está en el menú, en
*GeoComp ▸ Proyecto*.

- **Conjunto de datos**: *ggao-triangle*
- **Carpeta de destino**: una carpeta en la que pueda escribir

### 2. Relativo — Estático — `geocomp:gnss_relative_static`

Desde el menú, *GeoComp ▸ GNSS ▸ Relativo — Estático*. El primer lado del triángulo de medianoche.

- **Carpeta con observaciones RINEX**: `hour-00`
- **Estación base**: `GODN`
- **Estación móvil**: `GODE`
- **Solución**: `solutions-00/godn-gode.pos`, en una carpeta nueva junto a `hour-00`

Deje el resto como está. El registro dice cómo fue:

> 120 épocas, 96.7% con ambigüedades resueltas

Todas las épocas salvo las cuatro primeras, mientras la solución se asentaba, tienen las ambigüedades fijadas.
El registro también dice en qué se mantiene la base:

> La base GODN no está en la base de datos de estaciones de referencia, por lo que RTKLIB la mantiene en la
> posición aproximada de su cabecera RINEX, y los resultados no están en ningún marco de referencia declarado.

Aquí eso basta: un cierre necesita los vectores entre las estaciones, no dónde están las estaciones.

### 3. Relativo — Estático — `geocomp:gnss_relative_static`

El segundo lado.

- **Carpeta con observaciones RINEX**: `hour-00`
- **Estación base**: `GODN`
- **Estación móvil**: `GODS`
- **Solución**: `solutions-00/godn-gods.pos`

### 4. Relativo — Estático — `geocomp:gnss_relative_static`

El tercer lado, el que cierra el triángulo.

- **Carpeta con observaciones RINEX**: `hour-00`
- **Estación base**: `GODE`
- **Estación móvil**: `GODS`
- **Solución**: `solutions-00/gode-gods.pos`

Cada uno de los tres fija la misma parte de sus épocas, 96,7%.

### 5. Construir líneas base — `geocomp:gnss_build_baselines`

Desde el menú, *GeoComp ▸ GNSS ▸ Construir líneas base*.

- **Carpeta con soluciones .pos**: `solutions-00`
- **Líneas base**: algún lugar donde las encuentre

> 3 línea(s) base: 2 independientes, 1 dependientes

Dos de las tres líneas base bastan para situar las tres estaciones; la tercera es *dependiente*, y eso es lo que
la convierte en una verificación. Dando la vuelta al triángulo por las tres:

> El circuito GODN → GODE → GODS → GODN cierra con 0.37 mm en 282.2 m de líneas base (1.33 ppm).

**El triángulo cierra con 0,37 mm.** Tres vectores medidos de forma independiente, cada uno en su propia
ejecución, concuerdan entre sí en menos de medio milímetro.

---

## La hora de las once

Ahora las mismas tres ejecuciones en la otra carpeta.

### 6. Relativo — Estático — `geocomp:gnss_relative_static`

- **Carpeta con observaciones RINEX**: `hour-11`
- **Estación base**: `GODN`
- **Estación móvil**: `GODE`
- **Solución**: `solutions-11/godn-gode.pos`, en una carpeta nueva junto a `hour-11`

> 120 épocas, 48.3% con ambigüedades resueltas

La mitad de las épocas fijadas, no 96,7%. El registro dice lo que vio el motor:

> Saltos de ciclo detectados por el motor: 6, en G21.

### 7. Relativo — Estático — `geocomp:gnss_relative_static`

- **Carpeta con observaciones RINEX**: `hour-11`
- **Estación base**: `GODN`
- **Estación móvil**: `GODS`
- **Solución**: `solutions-11/godn-gods.pos`

> 120 épocas, 47.5% con ambigüedades resueltas

### 8. Relativo — Estático — `geocomp:gnss_relative_static`

- **Carpeta con observaciones RINEX**: `hour-11`
- **Estación base**: `GODE`
- **Estación móvil**: `GODS`
- **Solución**: `solutions-11/gode-gods.pos`

> 120 épocas, 97.5% con ambigüedades resueltas

El lado sin GODN fija tan bien como cualquier lado a medianoche.

### 9. Construir líneas base — `geocomp:gnss_build_baselines`

- **Carpeta con soluciones .pos**: `solutions-11`
- **Líneas base**: algún lugar donde las encuentre

Antes de cerrar el circuito, dice de qué están hechas dos de las líneas base:

> GODN-GODE se toma de una época cuyas ambigüedades no se fijaron (razón de ambigüedades 1.0). Una línea base
> flotante puede estar equivocada por mucho más de lo que dice su covarianza: procese la sesión de nuevo, en un
> intervalo más largo, o déjela fuera.

Y lo mismo de GODN-GODS. Después:

> El circuito GODN → GODE → GODS → GODN cierra con 7.62 mm en 282.3 m de líneas base (26.98 ppm).

**El triángulo falla por 7,62 mm**, veinte veces el circuito de medianoche sobre el mismo terreno. Las líneas
base de esa hora están en desacuerdo entre sí.

---

## Qué sacar de esto

- **El cierre de un circuito detecta; no localiza.** El circuito dice que uno de los tres lados está mal, no
  cuál. Aquí las propias ejecuciones señalan: los dos lados de GODN fijaron la mitad de sus épocas, y una
  línea base se toma de la última época, que en los dos no está fijada, como dice *Construir líneas base*.
  Procese esos dos de nuevo — un intervalo más largo, otra hora — antes de usarlos.
- **Un circuito que cierra no significa que las estaciones estén bien.** Un error común a los dos lados de una
  estación entra en el circuito dos veces, con signos opuestos, y se cancela. Con la configuración por defecto
  de GeoComp estas ejecuciones no aplican ninguna calibración de antena, y el circuito de medianoche todavía
  cierra con 0,37 mm, porque el error de cada antena está en dos lados. Cuando la validación de GeoComp comparó
  líneas base como estas con las coordenadas publicadas por el NGS, discreparon en milímetros mientras los
  circuitos cerraban en una fracción de uno (`specs/22-reference-data-sources.md` §5).
- **La parte fijada es parte de la respuesta.** La hora que no cerró es la hora que no fijó. Lea los indicadores
  de calidad antes de leer las coordenadas.
