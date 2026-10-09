# RD-04 circuito — un circuito de nivelación que no cierra, y por qué el ajuste no sabe decir dónde

**Conjunto de datos de referencia RD-04** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952), el
tutorial de nivelación. Versión en español del README.md; los números, los nombres y los valores que se
escriben son los mismos.

Tres líneas de nivelación geométrica entre tres puntos de referencia — BM1 a BM2, BM2 a BM4 y de vuelta a BM1
—, diez estacionamientos y veinte lecturas de mira, con las visuales equilibradas en cada estacionamiento. Una
lectura de frente en la línea BM2 a BM4 se anotó con 12 mm de error.

**Estos datos son construidos, y así se dice.** Las lecturas se generaron a partir de altitudes elegidas de
antemano — BM1 100,000 m, BM2 103,750 m, BM4 106,480 m — con 0,3 mm de ruido de una semilla fija, y después se
estropeó una lectura. Así se conoce la respuesta exactamente, y así se prueba la nivelación de GeoComp
(`tests/reference_levelling.py`). No es un levantamiento que alguien haya recorrido.

El tutorial muestra el circuito sin cerrar, un ajuste que esconde el error en lugar de encontrarlo, y las dos
altitudes conocidas que lo encuentran.

**Números.** En el texto, los números usan la coma decimal. Los valores entre comillas invertidas se escriben
tal como aparecen: el campo *Puntos de referencia* separa los puntos por comas, y en él la altitud se escribe
con punto.

---

## Los archivos

| Archivo | Qué es |
|---|---|
| `loop.csv` | La libreta de campo: una fila por lectura de mira — estacionamiento, punto, `BS` o `FS`, la lectura y la distancia de la visual en metros, y la línea |
| `mapping.json` | Qué columna alimenta qué campo (FR-160) |
| `profiles.json` | El nivel: 0,5 mm por lectura de mira, 0,7 mm por raíz de kilómetro. Sin él GeoComp se niega a importar, en lugar de inventar una precisión |

---

## Paso a paso

El documento que escribe cada paso es la entrada del siguiente.

### 1. Importar libreta de nivelación — `geocomp:levelling_import`

- **Libreta de campo**: `loop.csv`
- **Asignación de campos**: `mapping.json`
- **Perfiles de instrumento**: `profiles.json`

Diez estacionamientos en tres líneas, ninguna fila rechazada. El archivo tiene una fila por lectura, que es lo
que exporta un nivel digital; GeoComp lo deduce de las columnas que nombra la asignación.

### 2. Visuales iguales — `geocomp:levelling_equal_sights`

- **Estacionamientos**: el documento que escribió el paso 1
- **Perfiles de instrumento**: `profiles.json`

Cada línea se convierte en un desnivel con su incertidumbre. Las visuales están equilibradas en cada
estacionamiento, así que el desequilibrio acumulado es cero y un error de colimación se cancela; la peor línea,
BM2 a BM4, lleva 1,6 mm.

### 3. Cierres y tolerancias — `geocomp:levelling_closures`

- **Líneas reducidas**: el documento que escribió el paso 2
- **Modo**: *Circuito*
- **Coeficiente de tolerancia k (m por raíz de km)**: `0.008` — 8 mm √K, una tolerancia habitual para la
  nivelación ordinaria

Los tres desniveles deberían sumar cero alrededor del circuito. Suman **−15,7 mm**, frente a un permitido de
**7,0 mm** para los 0,76 km del circuito. **El circuito no cierra.**

Es todo lo que puede decir un circuito: algo en él está mal. No puede decir qué, porque cada línea contribuye a
la misma suma.

**Pruebe esto:** ejecútelo de nuevo con el coeficiente de tolerancia en `0`. El error de cierre es el mismo, y
no hay veredicto, ni aprobado ni reprobado: GeoComp no exige a un circuito una tolerancia que nadie declaró.

### 4. Ajuste de red de nivelación — `geocomp:levelling_network`

Mantenga solo BM1.

- **Líneas reducidas**: el documento que escribió el paso 2
- **Puntos de referencia**: `BM1=100.000`
- **Coeficiente de tolerancia k (m por raíz de km; 0 no evalúa nada)**: `0.008`
- **Incertidumbre por raíz de kilómetro (m)**: `0.0007`, el valor del propio nivel

El ajuste se ejecuta. Antes de ajustar, cierra cada línea que corre entre dos altitudes conocidas, y con solo
BM1 conocida no hay ninguna; juzgar un circuito le corresponde al algoritmo de cierres, y la comprobación del
propio ajuste es la prueba global (`specs/10` §3). Tres desniveles, dos altitudes desconocidas: **un grado de
libertad.** La prueba global falla, con un factor de varianza a posteriori de **662**: los datos discrepan de
su precisión declarada mucho más de lo que permite el azar.

**Ahora busque al culpable.** El data snooping prueba el residuo de cada línea, y todas marcan **1,00**, por
debajo del valor crítico de 1,96, así que **no se señala ningún error grosero.** No es que la prueba lo haya
pasado por alto. Con un grado de libertad hay la información de un solo residuo, y se reparte entre las tres
líneas en proporción a su longitud: 3,7 mm en BM1 a BM2, 10,3 mm en BM2 a BM4, 1,7 mm en BM4 de vuelta a BM1.
Cualquiera de ellas podría contener el error, y los residuos serían los mismos.

Las altitudes también están mal, y nada en ellas lo dice: BM2 sale a 103,7525 m, **2,5 mm** de donde está. El
ajuste ha escondido el error repartiéndolo.

### 5. Los puntos de referencia que lo encuentran

Ejecute de nuevo el ajuste de red, dando los **Puntos de referencia** como `BM1=100.000,BM2=103.750,BM4=106.480`
— las altitudes que un registro de puntos de referencia publicaría para ellos.

GeoComp se niega:

> 1 cierre(s) no cumplieron la tolerancia: BM2-BM4. GeoComp no ajusta una línea que no cumplió la tolerancia
> sin un reconocimiento explícito. Repita la línea, o active 'Ajustar líneas que no cumplieron la tolerancia'
> en esta ejecución o en la Configuración global (Nivelación).

Con cada línea corriendo ahora entre altitudes conocidas, cada línea cierra por sí sola, y solo **BM2 a BM4**
falla. Es la línea que hay que nivelar de nuevo. El circuito dijo que algo estaba mal; los puntos de referencia
dijeron dónde.

**Pruebe esto:** active *Ajustar líneas que no cumplieron la tolerancia* y ejecútelo una vez más. GeoComp se
niega otra vez, por otro motivo: con los tres puntos de referencia mantenidos no queda nada que estimar.

---

## Qué llevarse

- **El cierre de un circuito detecta; no localiza.** Tampoco un ajuste con un grado de libertad, por cuidadosas
  que sean sus estadísticas.
- **Un ajuste puede hacer que un error grosero parezca precisión.** Las altitudes del paso 4 vienen con
  incertidumbres de pocos milímetros y están mal en otro tanto, lo que solo avisó una prueba global reprobada.
- **Son las altitudes conocidas las que localizan un error**, al dar a cada línea algo propio contra lo que
  cerrar.
