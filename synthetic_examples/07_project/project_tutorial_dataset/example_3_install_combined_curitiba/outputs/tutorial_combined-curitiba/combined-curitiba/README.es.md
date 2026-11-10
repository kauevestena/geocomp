# Levantamiento combinado, Curitiba — GNSS y una estación total ajustados juntos, y la que exageró su precisión

El tutorial de integración (`specs/13-module-integration.md`, FR-952). Versión en español del README.md; los
números, los nombres y los valores que se escriben son los mismos.

Seis estaciones en unos 3 km cerca de Curitiba. Líneas base GNSS unen dos marcas de control, CTB1 y CTB2, con las
otras cuatro, procesadas en ITRF2014 en 2020,0. Una estación total ocupa cuatro de las estaciones y mide
direcciones, ángulos cenitales y distancias inclinadas a todas las estaciones que puede ver, con un ángulo y un
acimut más: 44 observaciones, en ningún marco, como una estación total no tiene ninguno.

La estación total declara su precisión como 2 mm en una distancia, 1,5″ en una dirección y 3″ en un ángulo
cenital. **Midió tres veces peor que eso.**

**Estos datos son construidos, y así se dice.** Cada medida se calculó a partir de posiciones elegidas de
antemano y se perturbó con una semilla fija; las de la estación total, con tres veces las desviaciones estándar
que declara. Es el levantamiento con el que la integración de GeoComp se valida frente a DynAdjust
(`tests/combined_network.py`, `specs/07` §6.3), con ese único cambio. Nadie lo recorrió.

**Números.** En el texto, los números usan la coma decimal. Lo que GeoComp escribe en el registro se cita tal
como él lo escribe, con punto.

---

## Los archivos

| Archivo | Qué es |
|---|---|
| `gnss.json` | Las líneas base GNSS y una altura elipsoidal, en ITRF2014 en 2020,0, con CTB1 y CTB2 en sus posiciones conocidas (un documento de red de GeoComp) |
| `total-station.json` | Las observaciones de la estación total, sin marco (un documento de red) |

---

## Paso a paso

### 1. GNSS y estación total — `geocomp:integration_gnss_total_station`

- **Red GNSS (de Construir líneas base)**: `gnss.json`
- **Red de estación total (de Red clásica)**: `total-station.json`
- **Marco de la combinación**: *ITRF2020*
- **Estaciones fijas (separadas por comas)**: `CTB1,CTB2`
- **Estimar un componente de varianza por técnica**: desmarcado

Las dos entradas se combinan en ITRF2020: las líneas base GNSS llevadas desde ITRF2014, las observaciones de la
estación total dadas según la vertical de cada estación. El registro lo dice: *2 entradas combinadas (gnss,
total_station) en ITRF2020; 7 transformación(es) aplicada(s).*

**41 grados de libertad, y la prueba global falla**, con un factor de varianza de **5,80**. Algo en el
levantamiento combinado discrepa de su precisión declarada. La prueba global no puede decir qué. El registro, sin
embargo, lo desglosa por técnica:

> GNSS: 5 observación(es), 20.6% de la redundancia, vᵀPv/r 1.375. Estación total: 44 observación(es), 79.4% de
> la redundancia, vᵀPv/r 6.950.

Los cuadrados ponderados de los residuos de cada técnica sobre su parte de la redundancia: **6,950 para la
estación total**, frente a 1,375 para el GNSS. Es una lectura rápida de cómo se ajustan los pesos de una técnica,
y el informe lo dice; todavía no es un componente de varianza, que el paso siguiente estima.

### 2. GNSS y estación total — `geocomp:integration_gnss_total_station`

Lo mismo, dejando que los datos pesen cada técnica.

- **Red GNSS (de Construir líneas base)**: `gnss.json`
- **Red de estación total (de Red clásica)**: `total-station.json`
- **Marco de la combinación**: *ITRF2020*
- **Estaciones fijas (separadas por comas)**: `CTB1,CTB2`
- **Estimar un componente de varianza por técnica**: marcado

La sección *Técnicas* del informe, bajo *Componentes de varianza*, da a la estación total un componente de
**7,19 ± 1,76** y al GNSS **0,56 ± 0,46**. Un componente es el factor por el que se multiplican las varianzas
declaradas de una técnica: las desviaciones estándar de la estación total se subestimaron unas **2,7** veces,
donde el levantamiento se hizo con 3, y las del GNSS son casi correctas, pues el 1 está dentro de la
incertidumbre de su componente.

La prueba global ahora pasa, y eso no dice nada: los componentes se estimaron para que pasara. Lo que es
información son los propios componentes, y que el peso de la estación total en la solución es ahora el que se
ganó. Su parte de la redundancia pasa del 79,4 % al **88,5 %**.

---

## Qué llevarse

- **La prueba global de un ajuste combinado dice que algo discrepa, no qué técnica.** El desglose por técnica
  dice cuál.
- **Los componentes de varianza pesan cada técnica por lo que midió, no por lo que declaró.** Son una
  estimación con su propia incertidumbre, y necesitan redundancia dentro de cada técnica para poder estimarse.
- **Después de los componentes de varianza, una prueba global aprobada no es evidencia.** Los componentes sí.
