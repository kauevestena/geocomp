# RD-07 USGS — una red gravimétrica cuya respuesta publicó otro, y un gravímetro que lee un 3 % de más

**Conjunto de datos de referencia RD-07, su mitad del USGS** (`specs/20-testing-and-validation.md` §3,
`specs/22-reference-data-sources.md` §5.6, FR-950, FR-952), el tutorial de gravimetría. Versión en español del
README.md; los números, los nombres y los valores que se escriben son los mismos.

Dos levantamientos de gravimetría relativa de cinco estaciones, sta1 a sta5, cada estación visitada dos o tres
veces en una tarde con el gravímetro B44, once lecturas por levantamiento. Son **los levantamientos sintéticos
de prueba del USGS para GSadjust**, copiados sin cambios del repositorio de GSadjust en el commit `17bb3ca`. El
USGS los generó a partir de una verdad que publicó junto a ellos, así que la respuesta se conoce y no es la del
propio GeoComp:

| | sta1 | sta2 | sta3 | sta4 | sta5 | Deriva | Escala del gravímetro |
|---|---|---|---|---|---|---|---|
| **Verdad**, mGal | 50,000 | 48,000 | 45,000 | 48,500 | 46,000 | | |
| `Test2.txt` | | | | | | 0,01 mGal por hora | correcta |
| `Test3.txt` | | | | | | 0,01 mGal por hora | **lee un 3 % de más** |

Cada lectura lleva 3 µGal de ruido. Los archivos son de dominio público en los Estados Unidos y se dedican al
mundo entero bajo CC0; el `GSadjust-LICENSE.md` que los acompaña lo dice.

**Números.** En el texto, los números usan la coma decimal. Los valores entre comillas invertidas se escriben
tal como aparecen: el campo *Gravedad conocida (mGal)* separa las estaciones por comas, y en él la gravedad se
escribe con punto.

---

## Los archivos

| Archivo | Qué es |
|---|---|
| `Test2.txt`, `Test3.txt` | Los dos levantamientos, en el formato de exportación Burris que lee GeoComp |
| `profiles.json` | El gravímetro B44: 3 µGal por lectura, marea ya eliminada, **sin calibración** — como está un gravímetro antes de que alguien mida su escala |
| `profiles-calibrated.json` | El mismo gravímetro con la calibración con que se generó la Prueba 3: un factor de 1/1,03 |
| `GSadjust-LICENSE.md` | La licencia del USGS para los levantamientos |

---

## Paso a paso

### 1. Preprocesamiento (escala, marea, deriva) — `geocomp:gravimetry_preprocess`

- **Archivo del gravímetro**: `Test2.txt`
- **Perfiles de gravímetro**: `profiles.json`
- **Piso de precisión (mGal)**: `0`
- **Lecturas reducidas**: `test2.json`

Once lecturas, once ocupaciones, una sesión. Una exportación Burris no declara ni la precisión ni la zona
horaria, y el registro dice qué se supuso para cada una: los 3 µGal del perfil, y UTC. También ajusta la deriva a
las tres lecturas de sta1 sola, la base: **0,01008 ± 0,00142 mGal por hora**.

### 2. Ajuste de red gravimétrica — `geocomp:gravimetry_network`

- **Lecturas reducidas**: `test2.json`
- **Gravedad conocida (mGal)**: `sta1=50.000`
- **Tratamiento de la deriva**: *Estimada junto con los valores de las estaciones*

El ajuste tiene **5 grados de libertad**, y la prueba global pasa con un factor de varianza de **1,17**. La
deriva se estima junto con las estaciones, a partir de todas las lecturas en lugar de las tres de la base:
**0,00915 ± 0,00109 mGal por hora**, frente a los 0,01 que puso el USGS.

Y las estaciones vuelven como las publicó el USGS. sta2 está a **1,3 µGal** de su verdad, sta3 a **2,6**, sta4 a
**0,9** y sta5 a **2,0**, cada una dentro de su propia desviación estándar de unos 3 µGal.

### 3. Preprocesamiento (escala, marea, deriva) — `geocomp:gravimetry_preprocess`

El segundo levantamiento, con el mismo perfil.

- **Archivo del gravímetro**: `Test3.txt`
- **Perfiles de gravímetro**: `profiles.json`
- **Piso de precisión (mGal)**: `0`
- **Lecturas reducidas**: `test3.json`

### 4. Ajuste de red gravimétrica — `geocomp:gravimetry_network`

Esta vez la gravedad de sta3 también se conoce, como la daría un gravímetro absoluto.

- **Lecturas reducidas**: `test3.json`
- **Gravedad conocida (mGal)**: `sta1=50.000,sta3=45.000`
- **Tratamiento de la deriva**: *Estimada junto con los valores de las estaciones*

**La prueba global falla**, con un factor de varianza de **525**. Las diferencias del gravímetro no caben entre
dos valores que se conocen ambos.

**Pruebe esto:** mantenga solo sta1, `sta1=50.000`. La prueba global pasa, con un factor de varianza de
**1,51**, y sta3 sale a **44,846 mGal**, a **154 µGal** de su verdad. Nada en el ajuste lo dice. Un gravímetro
que lee cada diferencia un 3 % de más es coherente consigo mismo: cada diferencia está mal en la misma
proporción, la red cierra, y los residuos son los de un levantamiento correcto. Ejecútelo de nuevo con
`profiles-calibrated.json` y el factor de varianza es el mismo, 1,51, en todas las cifras mostradas.

### 5. Preprocesamiento (escala, marea, deriva) — `geocomp:gravimetry_preprocess`

El segundo levantamiento otra vez, con la calibración del gravímetro.

- **Archivo del gravímetro**: `Test3.txt`
- **Perfiles de gravímetro**: `profiles-calibrated.json`
- **Piso de precisión (mGal)**: `0`
- **Lecturas reducidas**: `test3-calibrated.json`

### 6. Ajuste de red gravimétrica — `geocomp:gravimetry_network`

- **Lecturas reducidas**: `test3-calibrated.json`
- **Gravedad conocida (mGal)**: `sta1=50.000,sta3=45.000`
- **Tratamiento de la deriva**: *Estimada junto con los valores de las estaciones*

La prueba global pasa, con un factor de varianza de **1,56**, y las tres estaciones desconocidas quedan a menos
de **2,5 µGal** de su verdad.

---

## Qué llevarse

- **Una red comprueba la coherencia del gravímetro, no su escala.** Un error de calibración deja cada estadística
  como estaba; solo algo que conozca el tamaño de una diferencia puede encontrarlo, como un segundo valor
  absoluto o una línea de calibración.
- **Una estación conocida da un datum y nada con que comprobarlo.** Dos ponen a prueba la escala.
- **La deriva se estima con más precisión a partir de todas las lecturas que solo con las de la base**
  (±0,00109 frente a ±0,00142 mGal por hora aquí), y GeoComp la estima junto con las estaciones salvo que se le
  indique otra cosa.
