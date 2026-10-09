# RD-01 — un triángulo de estación total, con dos errores reales

**Conjunto de datos de referencia RD-01** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952). Versión en
español del README.md; los números, los nombres y los valores que se escriben son los mismos.

Tres estaciones, seis visuales, cada una observada en los dos círculos del instrumento. Es el levantamiento
completo de estación total más pequeño que existe, y ejercita toda la primera rebanada vertical de GeoComp:
importación de la libreta de campo, reducción de los círculos, las reducciones básicas, montaje de la red,
pruebas estadísticas y ajuste.

Son también **datos reales con dos errores reales**, y por eso es el tutorial. Un tutorial en el que nada está
mal enseña qué botones apretar. Este enseña para qué sirve el programa.

**Números.** En el texto, los números usan la coma decimal. Los valores entre comillas invertidas se escriben
tal como aparecen, y lo que GeoComp escribe en el registro se cita tal como él lo escribe, con punto.

---

## Los archivos

| Archivo | Qué es |
|---|---|
| `raw_data.csv` | La libreta de campo tal como se registró: estación, espalda, frente, círculo, ángulos sexagesimales, distancia inclinada, alturas del instrumento y de la señal |
| `mapping.json` | Qué columna alimenta qué campo (FR-160). Se define una vez y sirve para toda exportación del mismo instrumento |
| `profiles.json` | Las precisiones nominales del instrumento. Sin ellas GeoComp se niega a importar, en lugar de inventar una sigma |
| `approximate.json` | Coordenadas iniciales del ajuste, en un marco local con la estación 1 en el origen |

Las coordenadas son locales, no proyectadas. RD-01 no tiene ningún punto conocido ni ningún acimut medido, así
que nada lo ata a un datum — vea *La red es libre* más abajo.

---

## Paso a paso

El documento que escribe cada paso es la entrada del siguiente, así que el tutorial entero también se arma como
un modelo en el modelador gráfico.

### 1. Importar libreta de campo — `geocomp:totalstation_import_fieldbook`

- **Libreta de campo**: `raw_data.csv`
- **Asignación de campos**: `mapping.json`
- **Perfiles de instrumento**: `profiles.json`

Doce registros, tres estacionamientos, ninguno rechazado. Cada lectura sale con una incertidumbre, tomada del
perfil del instrumento: las incertidumbres se asignan en la frontera, porque un valor que entra en el sistema
sin una nunca puede adquirirla honestamente después.

**Pruebe esto:** ejecútelo de nuevo sin los perfiles. Se niega, y dice qué necesita. GeoComp no inventa una
desviación estándar, porque una sigma inventada se propaga por todos los números siguientes y convierte una
calidad desconocida en una calidad declarada.

### 2. Preprocesamiento generalizado — `geocomp:totalstation_preprocess`

- **Lecturas**: el documento que escribió el paso 1
- **Perfiles de instrumento**: `profiles.json` otra vez

Los perfiles se necesitan una segunda vez, y no es un descuido: las lecturas registran *qué* instrumento las
tomó, y reducir un par de círculos necesita la colimación, el índice vertical y las constantes del distanciómetro
de ese instrumento. GeoComp no pone las de otro en su lugar — se niega y nombra el que buscaba, porque una
sustitución silenciosa dejaría mal todo número siguiente de una manera que nada podría detectar.

Seis visuales reducidas a partir de doce lecturas. **Cinco son utilizables y una está bloqueada**, y la bloqueada
es el primer error real: la visual de la estación 3 a la estación 2, cuyos dos círculos discrepan en la distancia
en 1,000 m. El registro dice, de la estación 3:

> Los dos círculos hacia 2 discrepan en la distancia en +1.0000 m, frente a una tolerancia de 0.0087 m. La
> media de los dos no es la medida de nada; compruebe la libreta de campo antes de usar este par.

Un par de círculos mide la misma línea dos veces. Los ángulos concuerdan en segundos; las distancias difieren en
un metro redondo. Eso no es ruido, es un error de transcripción — una cifra anotada mal en la libreta. Promediar
las dos escondería un error de medio metro en la media y daría una distancia verosímil y equivocada. GeoComp
bloquea la visual y dice por qué, y las otras cinco siguen adelante.

**Mire el informe.** Los errores de colimación y de índice vertical se estiman a partir de los propios pares de
círculos y se informan por estacionamiento, que es para lo que sirve el segundo círculo: observar en los dos los
cancela, y su tamaño dice si el instrumento necesita ajuste.

### 3. Red clásica — `geocomp:totalstation_network`

- **Observaciones reducidas**: el documento que escribió el paso 2
- **Coordenadas aproximadas**: `approximate.json`
- **Dimensión**: *2D — planimétrico*
- **Definición del datum**: *Constricción interna — red libre, traza mínima*
- **Código de SRC, por ejemplo EPSG:31982**: `EPSG:31982` (UTM 22S), o el SRC proyectado de su propia zona

Las coordenadas de RD-01 son locales, pero un SRC sigue siendo obligatorio y GeoComp no inventa uno: unas
coordenadas ajustadas no significan nada sin saber *en qué* son coordenadas, y una suposición quedaría registrada
en la solución como si alguien la hubiera elegido.

El ajuste converge con **4 grados de libertad**, y **la prueba global falla**, con un factor de varianza de
**140,67**. Esa es la respuesta correcta, y lo segundo que enseña este conjunto de datos.

Las distancias entre las estaciones discrepan en unos 15 mm según el extremo desde el que se midieron, frente a
la precisión de 2 mm que declara el perfil del instrumento. La prueba global compara los residuos con el modelo
estocástico, y el modelo dice que los datos deberían ser mejores de lo que son. Algo está mal: o el instrumento
es menos preciso de lo declarado, o el centrado fue peor de lo supuesto, o todavía queda dentro un error grosero
menor. Una prueba que pasara aquí no estaría probando nada.

**Mire la capa de residuos.** Las observaciones se colorean según lo que la prueba w decidió sobre cada una, y no
se eliminó ninguna observación — GeoComp señala candidatas y le deja a usted la decisión (FR-255). Rechazar una
medida es un juicio sobre el levantamiento, no un paso aritmético.

### 4. El mapa

Pida al paso 3 las capas de resultado, las salidas cuyos nombres terminan en *(capa)*. Llegan con estilo:
estaciones dimensionadas por su incertidumbre posicional, elipses de error, residuos por significancia, la red por
tipo de observación, y los vectores de corrección.

**El nombre de la capa de elipses declara su factor de exageración.** Un semieje de 2 mm es invisible a cualquier
escala de mapa, así que las elipses dibujadas siempre se amplían, y una exageración que no se declara convierte
una visualización de calidad en una representación engañosa. Cambie el factor y vea cómo cambia el nombre con él.

---

## La red es libre

RD-01 no contiene ningún punto conocido, ningún acimut medido ni ninguna altura fija. Su deficiencia de datum es,
por tanto, **tres**: dos traslaciones y una rotación. Las distancias fijan la escala; nada fija dónde está el
triángulo ni hacia dónde mira.

Una red libre solo puede ajustarse con constricciones internas o mínimas. No es una limitación del programa, es
una propiedad de los datos: el levantamiento de verdad no sabe dónde está.

**Pruebe esto:** ejecute el paso 3 de nuevo con **Definición del datum** en *Constricción mínima — sobre las
estaciones elegidas* y **Estaciones del datum (separadas por comas; vacío = todas)** en `1,2`, para que dos de las
tres estaciones definan el datum en lugar de todas, y compare. Los residuos, los 4 grados de libertad y el factor
de varianza de 140,67 son los mismos, y solo se mueven las coordenadas. Esa es la lección: la constricción elige
un marco, no añade información.

Mantener además la estación 1, nombrándola en **Estaciones fijas (separadas por comas)**, se rechaza. Una estación
mantenida ya elimina parte de la deficiencia de datum, y las constricciones la eliminarían una segunda vez,
deformando la red para cumplir con ambas. Tampoco puede la estación 1 sola ser el datum, mantenida en *Ligada —
mantiene las estaciones que la red fija*: fija las dos traslaciones y deja la rotación, y GeoComp lo dice.

---

## El tercer error, que no está en los datos

El `processed_data.csv` de la carpeta `topo_test/` del repositorio es la salida del cuaderno prototipo del que
salió este conjunto de datos, y **una de sus seis direcciones reducidas está desviada 180°**. El prototipo
promediaba los dos círculos aritméticamente. Las direcciones son circulares: los dos círculos de una visual
difieren en unos 180°, así que su media aritmética cae a mitad de camino entre ellos en lugar de sobre uno de
ellos, y para una visual de aquí eso cae justo a media vuelta de la verdad.

Se demuestra de dos maneras, no se afirma. El valor publicado da un triángulo cuyos ángulos interiores suman
38,24° en lugar de 180°, e implica una distancia 2–3 de 4,43 m frente a los 24,35 m que se midieron. Las dos
comprobaciones están en `tests/test_reference_total_station.py`.

GeoComp reduce los círculos de forma circular y obtiene 199,110°, donde el prototipo publicó 19,110°. Si está
comparando los números de GeoComp con ese archivo, esta es la única línea que no coincidirá, y GeoComp tiene
razón.
