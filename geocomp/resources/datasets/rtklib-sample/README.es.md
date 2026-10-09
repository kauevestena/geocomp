<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Línea base de ejemplo de RTKLIB — una sesión GNSS que se ejecuta en dos minutos

Versión en español del README.md; los números, los nombres y los valores que se escriben son los mismos. En el
texto, los números usan la coma decimal; lo que GeoComp escribe en el registro se cita tal como él lo escribe,
con punto.

Dos receptores que observaron al mismo tiempo el 2 de abril de 2005, a 3,3 km uno del otro, y las efemérides
transmitidas del día. Son **los propios datos de ejemplo de RTKLIB**, copiados sin cambios del repositorio de
RTKLIB-EX en el commit `06e8644`; RTKLIB tiene licencia BSD de 2 cláusulas, y su aviso está en
`RTKLIB-license.txt` junto a este archivo.

| Archivo | Qué es |
|---|---|
| `30400920.05o` | Estación `3040`, `RINEX 2.10`, GPS, 30 s. **La base.** |
| `07590920.05o` | Estación `0759`, el mismo día, el mismo modelo de receptor y de antena. **La móvil.** |
| `brdc_0759.05n.gz` | El archivo de navegación transmitida de ese día. GeoComp lo lee comprimido. |

---

## Paso a paso

### 1. Instalar conjunto de datos del tutorial — `geocomp:project_tutorial_dataset`

Si está leyendo esto en la carpeta en la que se instaló, este paso está hecho. Si no, está en el menú, en
*GeoComp ▸ Proyecto*.

- **Conjunto de datos**: *rtklib-sample*
- **Carpeta de destino**: una carpeta en la que pueda escribir

### 2. Relativo — Estático — `geocomp:gnss_relative_static`

Desde el menú, *GeoComp ▸ GNSS ▸ Relativo — Estático*.

- **Carpeta con observaciones RINEX**: la carpeta que instaló el paso 1
- **Estación base**: `3040`
- **Estación móvil**: `0759`
- **Solución**: algún lugar donde la encuentre
- **Resumen de calidad**: algún lugar donde lo encuentre
- **Épocas de la solución (capa)**: déjela cargar

Deje el resto como está. `rnx2rtkp` se ejecuta. **No necesita instalarlo:** GeoComp trae el suyo, y el registro
dice *Usando RTKLIB-EX* `2.5.1` y dónde está.

## Qué debería ver

**120 épocas** en la primera hora (00:00 a 00:59:30), **117 de ellas con las ambigüedades fijadas** y tres
flotantes. El registro lo dice así:

> 120 épocas, 97.5% con ambigüedades resueltas

El registro dice, de las observaciones de cada estación, que el nombre del archivo de navegación no dice de qué
día es:

> el nombre de ningún archivo de navegación indica el día de esta sesión, por lo que se le ofrecen todos los
> archivos de navegación de la carpeta (1). Nombre los archivos de navegación por su día, o deje en la carpeta
> solo los de esta sesión.

Es lo esperado aquí, e inofensivo: hay un solo archivo de navegación, y es el correcto.

Y dice en qué se mantiene la base:

> La base 3040 no está en la base de datos de estaciones de referencia, por lo que RTKLIB la mantiene en la
> posición aproximada de su cabecera RINEX, y los resultados no están en ningún marco de referencia declarado.

## Qué no muestra esto

**La cadena, no la exactitud.** Estas dos estaciones no tienen coordenadas oficiales publicadas que este proyecto
pueda obtener, así que la línea base se mantiene en la posición aproximada de la cabecera, y nada aquí dice que
las coordenadas sean correctas. Lo que muestra es la cadena entera funcionando — el descubrimiento de las
sesiones, el motor, la lectura de la solución, los indicadores de calidad, la capa del mapa — y las ambigüedades
resolviéndose. El conjunto de datos que validaría la exactitud es RD-06 (`specs/22-reference-data-sources.md` §5).
