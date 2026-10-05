<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="es">
    <context>
        <name>AbsoluteKinematicAlgorithm</name>
        <message>
            <source>Absolute — Kinematic</source>
            <translation>Absoluto — Cinemático</translation>
        </message>
        <message>
            <source>Kinematic PPP. RTKLIB's PPP is limited — see the notice in the help.</source>
            <translation>PPP cinemático. El PPP de RTKLIB es limitado — vea el aviso en la ayuda.</translation>
        </message>
    </context>
    <context>
        <name>AbsoluteStaticAlgorithm</name>
        <message>
            <source>Absolute — Static</source>
            <translation>Absoluto — Estático</translation>
        </message>
        <message>
            <source>Static PPP. RTKLIB's PPP is limited — see the notice in the help.</source>
            <translation>PPP estático. El PPP de RTKLIB es limitado — vea el aviso en la ayuda.</translation>
        </message>
    </context>
    <context>
        <name>BatchProcessAlgorithm</name>
        <message>
            <source>%1 failed: %2</source>
            <translation>%1 falló: %2</translation>
        </message>
        <message>
            <source>%1 succeeded, %2 failed, %3 rejected</source>
            <translation>%1 con éxito, %2 con fallo, %3 rechazadas</translation>
        </message>
        <message>
            <source>%1: %2 epochs</source>
            <translation>%1: %2 épocas</translation>
        </message>
        <message>
            <source>&lt;p&gt;Processes every rover session in a folder against one base station, with the same configuration.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A session that fails does not stop the batch.&lt;/b&gt; Each is attempted, each failure is reported with the reason, and the summary lists what succeeded, what failed and what ran but produced no usable solution. A campaign of fifty sessions with one truncated file finishes and tells you which one it was.&lt;/p&gt;&lt;p&gt;Cancelling stops the batch promptly: the remaining sessions are not attempted, and what has already run is kept.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Products are checked before the batch starts.&lt;/b&gt; The orbits and navigation every session needs are resolved first -- from the cache, the product directory or a download service -- and a batch that lacks any is refused, naming each session and product, before a long run begins. A download that fails is reported against its session, and the batch continues.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Procesa todas las sesiones móviles de una carpeta respecto a una estación base, con la misma configuración.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Una sesión que falla no detiene el lote.&lt;/b&gt; Cada una se intenta, cada fallo se informa con su motivo, y el resumen enumera lo que tuvo éxito, lo que falló y lo que se ejecutó pero no produjo una solución utilizable. Una campaña de cincuenta sesiones con un archivo truncado termina e indica cuál fue.&lt;/p&gt;&lt;p&gt;Cancelar detiene el lote de inmediato: las sesiones restantes no se intentan, y lo ya ejecutado se conserva.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Los productos se comprueban antes de que empiece el lote.&lt;/b&gt; Las órbitas y la navegación que necesita cada sesión se resuelven primero -- desde la caché, el directorio de productos o un servicio de descarga -- y un lote al que le falte alguno se rechaza, nombrando cada sesión y producto, antes de que comience una ejecución larga. Una descarga que falla se informa en su sesión, y el lote continúa.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Absolute (PPP) processing in RTKLIB is limited and typically decimetre-level. Prefer Relative processing where a base station is available.</source>
            <translation>El procesamiento Absoluto (PPP) en RTKLIB es limitado y típicamente decimétrico. Prefiera el procesamiento Relativo cuando haya una estación base disponible.</translation>
        </message>
        <message>
            <source>Absolute — Kinematic</source>
            <translation>Absoluto — Cinemático</translation>
        </message>
        <message>
            <source>Absolute — Static</source>
            <translation>Absoluto — Estático</translation>
        </message>
        <message>
            <source>Base station</source>
            <translation>Estación base</translation>
        </message>
        <message>
            <source>Base: %1</source>
            <translation>Base: %1</translation>
        </message>
        <message>
            <source>Batch processing</source>
            <translation>Procesamiento por lotes</translation>
        </message>
        <message>
            <source>Batch report</source>
            <translation>Informe del lote</translation>
        </message>
        <message>
            <source>Could not read %1: %2</source>
            <translation>No se pudo leer %1: %2</translation>
        </message>
        <message>
            <source>Folder of RINEX observations</source>
            <translation>Carpeta con observaciones RINEX</translation>
        </message>
        <message>
            <source>Frame of the results (relative modes)</source>
            <translation>Marco de referencia de los resultados (modos relativos)</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>Name the base station explicitly; the folder holds: %1</source>
            <translation>Indique la estación base explícitamente; la carpeta contiene: %1</translation>
        </message>
        <message>
            <source>No RINEX observation sessions were found in %1</source>
            <translation>No se encontraron sesiones de observación RINEX en %1</translation>
        </message>
        <message>
            <source>No session for base station %1</source>
            <translation>Ninguna sesión para la estación base %1</translation>
        </message>
        <message>
            <source>Process every session in a folder; one failure does not stop the rest.</source>
            <translation>Procesa todas las sesiones de una carpeta; un fallo no detiene las demás.</translation>
        </message>
        <message>
            <source>Processing mode</source>
            <translation>Modo de procesamiento</translation>
        </message>
        <message>
            <source>Relative — Kinematic</source>
            <translation>Relativo — Cinemático</translation>
        </message>
        <message>
            <source>Relative — Static</source>
            <translation>Relativo — Estático</translation>
        </message>
    </context>
    <context>
        <name>BuildBaselinesAlgorithm</name>
        <message>
            <source>%1 baseline(s): %2 independent, %3 dependent</source>
            <translation>%1 línea(s) base: %2 independientes, %3 dependientes</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads every ECEF &lt;code&gt;.pos&lt;/code&gt; solution in a folder and builds the baseline each determined: the vector between the two marks, with its full 3x3 covariance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Antenna heights are reduced once.&lt;/b&gt; The vector the engine determined is between antenna reference points; the adjustment wants the vector between the marks. Applying the reduction twice is detected and refused.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Only the independent subset is kept by default.&lt;/b&gt; Processing every pair of n simultaneously observing stations yields n(n-1)/2 baselines of which only n-1 are independent; using them all inflates the apparent redundancy of the adjustment. The dependent ones are marked in the output rather than discarded.&lt;/p&gt;&lt;p&gt;The result is a cluster: the observations share one covariance matrix and reach DynAdjust as a G or X measurement with it intact.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The optional layer draws every baseline that was built&lt;/b&gt;, including the dependent ones when they were not kept, because seeing which pairs carried no new information is the point of drawing them at all. The &lt;code&gt;independent&lt;/code&gt; column and the dashed symbol say which is which; the JSON output carries only what was kept.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The network document&lt;/b&gt; is what the Integration menu combines with other techniques: the baselines at their sessions' mid-epochs and each mark's starting position. It needs &lt;i&gt;Frame of the base coordinates&lt;/i&gt;, which a &lt;code&gt;.pos&lt;/code&gt; file does not state and GeoComp will not assume.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee cada solución &lt;code&gt;.pos&lt;/code&gt; ECEF de una carpeta y construye la línea base que cada una determinó: el vector entre las dos marcas, con su covarianza 3x3 completa.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las alturas de antena se reducen una sola vez.&lt;/b&gt; El vector que determinó el motor es entre puntos de referencia de antena; el ajuste quiere el vector entre las marcas. Aplicar la reducción dos veces se detecta y se rechaza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;De forma predeterminada solo se conserva el subconjunto independiente.&lt;/b&gt; Procesar todos los pares de n estaciones observando simultáneamente produce n(n-1)/2 líneas base, de las cuales solo n-1 son independientes; usarlas todas infla la redundancia aparente del ajuste. Las dependientes se marcan en la salida en lugar de descartarse.&lt;/p&gt;&lt;p&gt;El resultado es un agrupamiento: las observaciones comparten una matriz de varianza-covarianza y llegan a DynAdjust como una medición G o X con ella intacta.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La capa opcional dibuja todas las líneas base construidas&lt;/b&gt;, incluidas las dependientes cuando no se conservaron, porque ver qué pares no aportaron información nueva es precisamente el motivo de dibujarlas. La columna &lt;code&gt;independent&lt;/code&gt; y el símbolo discontinuo dicen cuál es cuál; la salida JSON lleva solo lo que se conservó.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El documento de red&lt;/b&gt; es lo que el menú Integración combina con otras técnicas: las líneas base en las épocas medias de sus sesiones y la posición inicial de cada marca. Necesita &lt;i&gt;Marco de las coordenadas de la base&lt;/i&gt;, que un archivo &lt;code&gt;.pos&lt;/code&gt; no indica y GeoComp no supone.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Base antenna height above the mark (m)</source>
            <translation>Altura de la antena de la base sobre la marca (m)</translation>
        </message>
        <message>
            <source>Baselines</source>
            <translation>Líneas base</translation>
        </message>
        <message>
            <source>Baselines (layer)</source>
            <translation>Líneas base (capa)</translation>
        </message>
        <message>
            <source>Build baselines</source>
            <translation>Construir líneas base</translation>
        </message>
        <message>
            <source>Folder of .pos solutions</source>
            <translation>Carpeta con soluciones .pos</translation>
        </message>
        <message>
            <source>Frame of the base coordinates</source>
            <translation>Marco de las coordenadas de la base</translation>
        </message>
        <message>
            <source>GNSS baselines</source>
            <translation>Líneas base GNSS</translation>
        </message>
        <message>
            <source>GeoComp network (*.json)</source>
            <translation>Red GeoComp (*.json)</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>Keep only the independent subset</source>
            <translation>Conservar solo el subconjunto independiente</translation>
        </message>
        <message>
            <source>Keeping %1 dependent baseline(s). They carry no new information, and an adjustment that treats them as independent will report an uncertainty smaller than the data supports.</source>
            <translation>Conservando %1 línea(s) base dependiente(s). No aportan información nueva, y un ajuste que las trate como independientes informará una incertidumbre menor de la que los datos sustentan.</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>No .pos solutions were found in %1</source>
            <translation>No se encontró ninguna solución .pos en %1</translation>
        </message>
        <message>
            <source>No baseline could be built from the solutions in %1</source>
            <translation>No se pudo construir ninguna línea base a partir de las soluciones en %1</translation>
        </message>
        <message>
            <source>Not stated</source>
            <translation>No indicado</translation>
        </message>
        <message>
            <source>Rover antenna height above the mark (m)</source>
            <translation>Altura de la antena del móvil sobre la marca (m)</translation>
        </message>
        <message>
            <source>Skipped %1: %2</source>
            <translation>Omitido %1: %2</translation>
        </message>
        <message>
            <source>The network document needs the frame the base coordinates were given in. A .pos file does not state it and GeoComp does not assume one: a vector with no frame cannot be brought into another's.</source>
            <translation>El documento de red necesita el marco en que se dieron las coordenadas de la base. Un archivo .pos no lo indica y GeoComp no supone uno: un vector sin marco no puede llevarse a otro.</translation>
        </message>
        <message>
            <source>Turn processed sessions into baseline observations with covariance.</source>
            <translation>Convierte sesiones procesadas en observaciones de línea base con covarianza.</translation>
        </message>
        <message>
            <source>Uncertainty of each antenna height (m)</source>
            <translation>Incertidumbre de cada altura de antena (m)</translation>
        </message>
    </context>
    <context>
        <name>ClassicalNetworkAlgorithm</name>
        <message>
            <source>%1 distance(s), from %2 to %3 ppm.</source>
            <translation>%1 distancia(s), de %2 a %3 ppm.</translation>
        </message>
        <message>
            <source>%1 is not a conformal projection: its scale differs between the meridian and the parallel, so a distance's reduction would depend on its direction. Adjust in a conformal projection, such as UTM, or turn the reduction off.</source>
            <translation>%1 no es una proyección conforme: su escala difiere entre el meridiano y el paralelo, de modo que la reducción de una distancia dependería de su dirección. Ajuste en una proyección conforme, como la UTM, o desactive la reducción.</translation>
        </message>
        <message>
            <source>%1 observation(s) exceed the w-test critical value; none was rejected.</source>
            <translation>%1 observación(es) supera(n) el valor crítico de la prueba w; ninguna fue rechazada.</translation>
        </message>
        <message>
            <source>1D — heights</source>
            <translation>1D — altitudes</translation>
        </message>
        <message>
            <source>2D — planimetric</source>
            <translation>2D — planimétrico</translation>
        </message>
        <message>
            <source>3D</source>
            <translation>3D</translation>
        </message>
        <message>
            <source>&lt;p&gt;Assembles the reduced pointings into a geodetic network and adjusts it by least squares, with the global test, data snooping and reliability analysis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulation, trilateration and triangulateration are not three different computations.&lt;/b&gt; They are one adjustment over three different observation sets, and which one a survey is depends on what was measured. This algorithm adjusts whatever the pointings contain.&lt;/p&gt;&lt;p&gt;Free and constrained solutions are both available, which is the comparison between &lt;i&gt;redes livres&lt;/i&gt; and &lt;i&gt;redes amarradas&lt;/i&gt; the research project names as a teaching goal. A free network is adjusted with inner constraints and is the honest choice when nothing external orients or positions the survey.&lt;/p&gt;&lt;p&gt;The network document is written out as well as the solution, so the chain &lt;i&gt;pre-process &amp;rarr; build &amp;rarr; inspect &amp;rarr; adjust&lt;/i&gt; can be assembled in the graphical modeller using the Analysis algorithms.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Approximate coordinates&lt;/b&gt; &amp;mdash; a JSON object mapping each station to &lt;code&gt;[easting, northing, up]&lt;/code&gt;, or a CSV or .xlsx table with a station, its easting, its northing and its height on each row. Required, not derived: the linearised model needs a point to linearise about, and a traverse or a resection is how a surveyor obtains one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimension&lt;/b&gt; &amp;mdash; which of 2D, 3D and 1D to adjust in. It decides which reduced quantities become observations: a 2D adjustment takes directions and horizontal distances, a 3D one takes directions, zenith angles and slope distances. Emitting all of them would use the same measurement twice.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;b&gt;Fixed stations&lt;/b&gt; &amp;mdash; comma-separated; their approximate coordinates are held exactly.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt;, &lt;b&gt;reference epoch&lt;/b&gt; and &lt;b&gt;CRS&lt;/b&gt; &amp;mdash; recorded on the solution.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reduce measured distances to the grid&lt;/b&gt; &amp;mdash; a total station measures a distance on the ground, and a plane adjustment computes one from grid coordinates. On a projected CRS the two differ by the reduction to the ellipsoid, about 157 ppm for each kilometre of height, and by the projection's scale factor, on UTM from &amp;minus;400 ppm at the central meridian to about +1000 ppm at a zone's edge. In a 2D adjustment each horizontal distance is reduced by both, at the mean height of its ends and the scale factor of its line, and the report states the range applied. Coordinates that lie outside the area the CRS is defined for are read as a local plane and are not reduced; neither is a network in a CRS that is not projected.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Geoid undulation N&lt;/b&gt; (m) &amp;mdash; the approximate heights are orthometric, and the reduction to the ellipsoid needs ellipsoidal ones, &lt;i&gt;h = H + N&lt;/i&gt;. Each 10 m of N left out is 1.6 ppm.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; and &lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON documents; the first feeds the Analysis algorithms, the second holds the adjusted coordinates with their full covariance and provenance. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; and &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Result layers&lt;/b&gt; &amp;mdash; five optional map layers, arriving styled and ready to read (FR-905): adjusted stations sized by their positional uncertainty, error ellipses, observations coloured by what the w-test decided about them, the measured network by observation type, and the coordinate correction vectors. None is created unless asked for, so an adjustment run to feed another algorithm writes nothing extra.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ellipse exaggeration&lt;/b&gt; &amp;mdash; real ellipses are invisible at map scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to the network's own extent. Whatever factor is used is stated in the layer's name, which is what reaches the legend: an unstated exaggeration turns a quality visualisation into a misrepresentation.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reúne las visuales reducidas en una red geodésica y la ajusta por mínimos cuadrados, con la prueba global, el data snooping y el análisis de fiabilidad.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulación, trilateración y triangulateración no son tres cálculos distintos.&lt;/b&gt; Son un único ajuste sobre tres conjuntos de observaciones distintos, y cuál de ellos es un levantamiento depende de lo que se midió. Este algoritmo ajusta lo que contengan las visuales.&lt;/p&gt;&lt;p&gt;Las soluciones libres y ligadas están ambas disponibles, que es la comparación entre &lt;i&gt;redes libres&lt;/i&gt; y &lt;i&gt;redes ligadas&lt;/i&gt; que el proyecto de investigación nombra como objetivo pedagógico. Una red libre se ajusta con constricciones internas y es la elección honesta cuando nada externo orienta o posiciona el levantamiento.&lt;/p&gt;&lt;p&gt;El documento de la red se escribe además de la solución, de modo que la cadena &lt;i&gt;preprocesar &amp;rarr; construir &amp;rarr; inspeccionar &amp;rarr; ajustar&lt;/i&gt; pueda montarse en el modelador gráfico usando los algoritmos de Análisis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordenadas aproximadas&lt;/b&gt; &amp;mdash; un objeto JSON que asocia cada estación a &lt;code&gt;[E, N, altitud]&lt;/code&gt;, o una tabla CSV o .xlsx con una estación, su E, su N y su altitud en cada fila. Exigidas, no derivadas: el modelo linealizado necesita un punto en torno al cual linealizar, y una poligonal o una intersección inversa es como un topógrafo lo obtiene.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimensión&lt;/b&gt; &amp;mdash; en cuál de 2D, 3D y 1D ajustar. Ello decide qué magnitudes reducidas se convierten en observaciones: un ajuste 2D toma direcciones y distancias horizontales, uno 3D toma direcciones, ángulos cenitales y distancias inclinadas. Emitirlas todas usaría la misma medida dos veces.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina la deficiencia de datum. &lt;b&gt;Estaciones fijas&lt;/b&gt; &amp;mdash; separadas por comas; sus coordenadas aproximadas se mantienen exactamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt;, &lt;b&gt;época de referencia&lt;/b&gt; y &lt;b&gt;SRC&lt;/b&gt; &amp;mdash; registrados en la solución.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reducir las distancias medidas a la cuadrícula&lt;/b&gt; &amp;mdash; una estación total mide una distancia sobre el terreno, y un ajuste plano la calcula a partir de coordenadas de la cuadrícula. En un SRC proyectado ambas difieren por la reducción al elipsoide, unos 157 ppm por kilómetro de altura, y por el factor de escala de la proyección, en UTM de &amp;minus;400 ppm en el meridiano central a unos +1000 ppm en el borde de una zona. En un ajuste 2D cada distancia horizontal se reduce por ambos, a la altura media de sus extremos y con el factor de escala de su línea, y el informe indica el intervalo aplicado. Las coordenadas fuera del área para la que el SRC está definido se leen como un plano local y no se reducen; tampoco una red en un SRC que no es proyectado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ondulación geoidal N&lt;/b&gt; (m) &amp;mdash; las alturas aproximadas son ortométricas, y la reducción al elipsoide necesita alturas elipsoidales, &lt;i&gt;h = H + N&lt;/i&gt;. Cada 10 m de N omitidos son 1,6 ppm.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; y &lt;b&gt;Solución&lt;/b&gt; &amp;mdash; documentos JSON; el primero alimenta los algoritmos de Análisis, el segundo contiene las coordenadas ajustadas con su matriz de covarianzas completa y la procedencia. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; y &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Capas de resultado&lt;/b&gt; &amp;mdash; cinco capas opcionales, que llegan con estilo y listas para leer (FR-905): estaciones ajustadas dimensionadas por su incertidumbre posicional, elipses de error, observaciones coloreadas según lo que decidió la prueba w, la red medida por tipo de observación y los vectores de corrección de coordenadas. Ninguna se crea sin solicitarla, de modo que un ajuste ejecutado para alimentar otro algoritmo no escribe nada de más.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración de las elipses&lt;/b&gt; &amp;mdash; las elipses reales son invisibles a escala de mapa, por lo que se dibujan ampliadas. Déjelo en 0 y se ajusta un factor a la propia extensión de la red. Sea cual sea el factor utilizado, se declara en el nombre de la capa, que es lo que llega a la leyenda: una exageración no declarada convierte una visualización de calidad en una tergiversación.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A CRS authority code is required, for example 'EPSG:31982'. GeoComp does not infer one: the adjusted coordinates are meaningless without knowing what they are coordinates in, and a guess would be recorded on the solution as though it had been chosen. For a local survey with no datum, use the projected CRS of the area it sits in.</source>
            <translation>Es obligatorio indicar un código de SRC, por ejemplo 'EPSG:31982'. GeoComp no lo deduce: las coordenadas ajustadas carecen de sentido sin saber en qué sistema están, y una suposición quedaría registrada en la solución como si alguien la hubiera elegido. Para un levantamiento local sin datum, use el SRC proyectado de la zona en la que se encuentra.</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estaciones ajustadas</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
        </message>
        <message>
            <source>Approximate coordinates</source>
            <translation>Coordenadas aproximadas</translation>
        </message>
        <message>
            <source>Approximate coordinates for station '%1' are not three numbers.</source>
            <translation>Las coordenadas aproximadas de la estación '%1' no son tres números.</translation>
        </message>
        <message>
            <source>Build a triangulation, trilateration or triangulateration network from reduced pointings and adjust it.</source>
            <translation>Construye una red de triangulación, trilateración o triangulateración a partir de las visuales reducidas y la ajusta.</translation>
        </message>
        <message>
            <source>CRS authority code, e.g. EPSG:31982</source>
            <translation>Código de SRC, por ejemplo EPSG:31982</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Classical network</source>
            <translation>Red clásica</translation>
        </message>
        <message>
            <source>Classical network report</source>
            <translation>Informe de la red clásica</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Converged in %1 iteration(s); %2 degree(s) of freedom.</source>
            <translation>Convergió en %1 iteración(es); %2 grado(s) de libertad.</translation>
        </message>
        <message>
            <source>Coordinates (*.json *.csv *.xlsx);;All files (*)</source>
            <translation>Coordenadas (*.json *.csv *.xlsx);;Todos los archivos (*)</translation>
        </message>
        <message>
            <source>Critical value</source>
            <translation>Valor crítico</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Deficiencia de datum</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Dimension</source>
            <translation>Dimensión</translation>
        </message>
        <message>
            <source>Distances reduced to the grid</source>
            <translation>Distancias reducidas a la cuadrícula</translation>
        </message>
        <message>
            <source>Fixed stations (comma-separated)</source>
            <translation>Estaciones fijas (separadas por comas)</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_network</source>
            <translation>Generado por GeoComp — geocomp:totalstation_network</translation>
        </message>
        <message>
            <source>GeoComp network (*.json)</source>
            <translation>Red GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Geoid undulation N (m)</source>
            <translation>Ondulación geoidal N (m)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Inspection</source>
            <translation>Inspección</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iteraciones</translation>
        </message>
        <message>
            <source>Lower critical value</source>
            <translation>Valor crítico inferior</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>No: %1 is not a projected CRS, so there is no grid to reduce to.</source>
            <translation>No: %1 no es un SRC proyectado, así que no hay cuadrícula a la que reducir.</translation>
        </message>
        <message>
            <source>No: distances are reduced to the grid in a 2D adjustment only, and this one is not 2D.</source>
            <translation>No: las distancias se reducen a la cuadrícula solo en un ajuste 2D, y este no es 2D.</translation>
        </message>
        <message>
            <source>No: the network has no distance to reduce.</source>
            <translation>No: la red no tiene distancia que reducir.</translation>
        </message>
        <message>
            <source>No: the reduction was turned off.</source>
            <translation>No: la reducción se desactivó.</translation>
        </message>
        <message>
            <source>No: these stations lie outside the area %1 is defined for, so the coordinates are read as a local plane: %2.</source>
            <translation>No: estas estaciones están fuera del área para la que %1 está definido, así que las coordenadas se leen como un plano local: %2.</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Observations exceeding the critical value are candidates, not rejections. Nothing has been removed.</source>
            <translation>Las observaciones que superan el valor crítico son candidatas, no rechazos. No se ha eliminado nada.</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedad</translation>
        </message>
        <message>
            <source>QGIS gives no scale factor for %1 at %2, %3.</source>
            <translation>QGIS no da factor de escala para %1 en %2, %3.</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reduce measured distances to the grid</source>
            <translation>Reducir las distancias medidas a la cuadrícula</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Reduced to the grid: %1</source>
            <translation>Reducidas a la cuadrícula: %1</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Reference epoch, decimal year (0 = the network's own)</source>
            <translation>Época de referencia, año decimal (0 = la de la propia red)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieje mayor (mm)</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Standardised residual</source>
            <translation>Residuo estandarizado</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estadístico</translation>
        </message>
        <message>
            <source>Std dev X (mm)</source>
            <translation>Desviación típica X (mm)</translation>
        </message>
        <message>
            <source>Std dev Y (mm)</source>
            <translation>Desviación típica Y (mm)</translation>
        </message>
        <message>
            <source>The approximate coordinates document is empty.</source>
            <translation>El documento de coordenadas aproximadas está vacío.</translation>
        </message>
        <message>
            <source>The global test fails.</source>
            <translation>La prueba global falla.</translation>
        </message>
        <message>
            <source>The global test fails: %1</source>
            <translation>La prueba global falla: %1</translation>
        </message>
        <message>
            <source>The global test passes.</source>
            <translation>La prueba global pasa.</translation>
        </message>
        <message>
            <source>The network cannot be adjusted: %1</source>
            <translation>La red no puede ajustarse: %1</translation>
        </message>
        <message>
            <source>These fixed stations have no approximate coordinates: %1</source>
            <translation>Estas estaciones fijas no tienen coordenadas aproximadas: %1</translation>
        </message>
        <message>
            <source>Upper critical value</source>
            <translation>Valor crítico superior</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Variance factor</source>
            <translation>Factor de varianza</translation>
        </message>
        <message>
            <source>Variance factor %1.</source>
            <translation>Factor de varianza %1.</translation>
        </message>
        <message>
            <source>X (m)</source>
            <translation>X (m)</translation>
        </message>
        <message>
            <source>Y (m)</source>
            <translation>Y (m)</translation>
        </message>
        <message>
            <source>Z (m)</source>
            <translation>Z (m)</translation>
        </message>
    </context>
    <context>
        <name>CombinedAdjustmentAlgorithm</name>
        <message>
            <source>%1: %2 observation(s), %3 of the redundancy, vᵀPv/r %4.</source>
            <translation>%1: %2 observación(es), %3 de la redundancia, vᵀPv/r %4.</translation>
        </message>
        <message>
            <source>'%1' is not an epoch. Write it as a decimal year, for example 2024.5.</source>
            <translation>'%1' no es una época. Escríbala como año decimal, por ejemplo 2024.5.</translation>
        </message>
        <message>
            <source>&lt;p&gt;&lt;b&gt;Inputs&lt;/b&gt; are the network documents the technique algorithms write. Each is combined as its producer built it; stations with the same name in two inputs are the same mark, which is what ties the techniques together.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fixed stations&lt;/b&gt; are held where the first input that places them says they are &amp;mdash; for GNSS, the base coordinates from the processing.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Engine&lt;/b&gt;: DynAdjust is used only when it can adjust everything. Gravity, an observation type it lacks, a local system or orthometric heights keep the combination in the in-house core, and the report says which and why.&lt;/p&gt;&lt;p&gt;The report has a &lt;i&gt;Techniques&lt;/i&gt; section: each technique's share of the redundancy and of the weighted squares, the variance components when asked for, the geoid residuals, and every frame transformation applied.&lt;/p&gt;</source>
            <translation>&lt;p&gt;&lt;b&gt;Las entradas&lt;/b&gt; son los documentos de red que escriben los algoritmos de cada técnica. Cada una se combina tal como la construyó su productor; las estaciones con el mismo nombre en dos entradas son la misma marca, y eso es lo que une las técnicas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las estaciones fijas&lt;/b&gt; se mantienen donde la primera entrada que las ubica dice que están &amp;mdash; en GNSS, las coordenadas de la base usadas en el procesamiento.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Motor&lt;/b&gt;: DynAdjust se usa solo cuando puede ajustarlo todo. La gravedad, un tipo de observación que no tiene, un sistema local o las alturas ortométricas mantienen la combinación en el núcleo propio, y el informe dice cuál y por qué.&lt;/p&gt;&lt;p&gt;El informe tiene una sección &lt;i&gt;Técnicas&lt;/i&gt;: la parte de cada técnica en la redundancia y en los cuadrados ponderados, los componentes de varianza cuando se piden, los residuos del geoide y toda transformación de marco aplicada.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>&lt;p&gt;Combines a GNSS network and a total-station network in one geocentric frame at one epoch, each observation at its own station's vertical.&lt;/p&gt;&lt;p&gt;The total-station network may be in a UTM or Transverse Mercator projection of SIRGAS 2000 or an ITRF: its starting coordinates are read through it. Its measurements belong to no frame and are not transformed. Hold control through the GNSS input: a point held in grid coordinates is refused, because its height is not the ellipsoidal one.&lt;/p&gt;&lt;p&gt;A geoid model is needed only if orthometric heights take part.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Combina una red GNSS y una red de estación total en un marco geocéntrico, en una época, cada observación en la vertical de su propia estación.&lt;/p&gt;&lt;p&gt;La red de estación total puede estar en una proyección UTM o Transversa de Mercator de SIRGAS 2000 o de un ITRF: sus coordenadas iniciales se leen a través de ella. Sus mediciones no pertenecen a ningún marco y no se transforman. Fije el control mediante la entrada GNSS: un punto fijado en coordenadas de cuadrícula se rechaza, porque su altura no es la elipsoidal.&lt;/p&gt;&lt;p&gt;Un modelo geoidal solo se necesita si participan alturas ortométricas.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>&lt;p&gt;Combines a total-station network and a levelling network in the total station's own coordinate reference system. Nothing is transformed: neither technique measures a position in a frame.&lt;/p&gt;&lt;p&gt;When the total-station network holds only height differences, the combination is adjusted in heights alone; otherwise in three dimensions, where a mark reached only by levelling is refused by name, because nothing places it horizontally.&lt;/p&gt;&lt;p&gt;A benchmark held by the levelling network and a control point held by the total station are the same hold if they agree in height.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Combina una red de estación total y una red de nivelación en el propio sistema de referencia de coordenadas de la estación total. Nada se transforma: ninguna de las técnicas mide una posición en un marco.&lt;/p&gt;&lt;p&gt;Cuando la red de estación total contiene solo desniveles, la combinación se ajusta solo en alturas; de lo contrario, en tres dimensiones, y una marca alcanzada solo por la nivelación se rechaza por su nombre, porque nada la ubica horizontalmente.&lt;/p&gt;&lt;p&gt;Un banco de nivel fijado por la red de nivelación y un punto de control fijado por la estación total son la misma fijación si concuerdan en altura.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>&lt;p&gt;GNSS gives ellipsoidal heights and levelling orthometric ones; they are related by the geoid, h = H + N. The geoid model is &lt;b&gt;required&lt;/b&gt;, is named in the solution and the report, and its uncertainty takes part: each station's undulation is estimated with the model as its prior.&lt;/p&gt;&lt;p&gt;The &lt;b&gt;geoid residuals&lt;/b&gt; in the report are the survey's test of the model over the project area.&lt;/p&gt;&lt;p&gt;A levelling benchmark enters as an orthometric height observation with its uncertainty; one held exactly is refused, because it would make the geoid exact there. Every levelled mark must also be occupied by GNSS, or nothing places it horizontally.&lt;/p&gt;</source>
            <translation>&lt;p&gt;GNSS da alturas elipsoidales y la nivelación, ortométricas; se relacionan por el geoide, h = H + N. El modelo geoidal es &lt;b&gt;obligatorio&lt;/b&gt;, se nombra en la solución y en el informe, y su incertidumbre participa: la ondulación de cada estación se estima con el modelo como información a priori.&lt;/p&gt;&lt;p&gt;Los &lt;b&gt;residuos del geoide&lt;/b&gt; en el informe son la prueba del modelo que hace el levantamiento en el área del proyecto.&lt;/p&gt;&lt;p&gt;Un banco de nivel entra como observación de altura ortométrica con su incertidumbre; uno fijado exactamente se rechaza, porque haría exacto el geoide allí. Toda marca nivelada debe también ser ocupada por GNSS, o nada la ubica horizontalmente.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>&lt;p&gt;Three or more of GNSS, total station, levelling and gravimetry. With GNSS the combination is geocentric; without it, in the inputs' own system.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Gravity is adjusted beside the geometry&lt;/b&gt;, by the in-house core with its drift model: nothing in the combination relates gravity to position, so adjusting it inside would give the same answer. It is never dropped, and asking for DynAdjust with gravity present keeps the whole combination in-house, with the reason in the report.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Tres o más entre GNSS, estación total, nivelación y gravimetría. Con GNSS la combinación es geocéntrica; sin él, en el propio sistema de las entradas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La gravedad se ajusta junto a la geometría&lt;/b&gt;, por el núcleo propio con su modelo de deriva: nada en la combinación relaciona gravedad y posición, así que ajustarla dentro daría la misma respuesta. Nunca se descarta, y pedir DynAdjust con gravedad presente mantiene toda la combinación en el núcleo propio, con el motivo en el informe.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjust GNSS baselines and levelled height differences together, through a geoid.</source>
            <translation>Ajusta líneas base GNSS y desniveles nivelados en conjunto, mediante un geoide.</translation>
        </message>
        <message>
            <source>Adjust GNSS baselines and total-station observations together.</source>
            <translation>Ajusta líneas base GNSS y observaciones de estación total en conjunto.</translation>
        </message>
        <message>
            <source>Adjust three or more techniques together, gravity included.</source>
            <translation>Ajusta tres o más técnicas en conjunto, incluida la gravedad.</translation>
        </message>
        <message>
            <source>Adjust total-station and levelling observations together.</source>
            <translation>Ajusta observaciones de estación total y de nivelación en conjunto.</translation>
        </message>
        <message>
            <source>Combined %1 inputs (%2) in %3; %4 transformation(s) applied.</source>
            <translation>%1 entradas combinadas (%2) en %3; %4 transformación(es) aplicada(s).</translation>
        </message>
        <message>
            <source>Combined network</source>
            <translation>Red combinada</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>DynAdjust, when it can adjust everything</source>
            <translation>DynAdjust, cuando pueda ajustarlo todo</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Engine: %1 (%2).</source>
            <translation>Motor: %1 (%2).</translation>
        </message>
        <message>
            <source>Epoch (decimal year; empty takes the inputs')</source>
            <translation>Época (año decimal; vacío toma la de las entradas)</translation>
        </message>
        <message>
            <source>Estimate a variance component per technique</source>
            <translation>Estimar un componente de varianza por técnica</translation>
        </message>
        <message>
            <source>Fixed stations (comma-separated)</source>
            <translation>Estaciones fijas (separadas por comas)</translation>
        </message>
        <message>
            <source>Frame to combine in</source>
            <translation>Marco de la combinación</translation>
        </message>
        <message>
            <source>GNSS and level</source>
            <translation>GNSS y nivel</translation>
        </message>
        <message>
            <source>GNSS and total station</source>
            <translation>GNSS y estación total</translation>
        </message>
        <message>
            <source>GNSS network (from Build baselines)</source>
            <translation>Red GNSS (de Construir líneas base)</translation>
        </message>
        <message>
            <source>GeoComp in-house core</source>
            <translation>Núcleo propio de GeoComp</translation>
        </message>
        <message>
            <source>GeoComp network (*.json)</source>
            <translation>Red GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Geoid model (GTX or ESRI ASCII grid)</source>
            <translation>Modelo geoidal (cuadrícula GTX o ESRI ASCII)</translation>
        </message>
        <message>
            <source>Geoid model uncertainty (m)</source>
            <translation>Incertidumbre del modelo geoidal (m)</translation>
        </message>
        <message>
            <source>Gravity readings (from Gravimetry pre-processing)</source>
            <translation>Lecturas gravimétricas (del preprocesamiento de gravimetría)</translation>
        </message>
        <message>
            <source>Gravity solution</source>
            <translation>Solución gravimétrica</translation>
        </message>
        <message>
            <source>Gravity was adjusted beside the geometry, by the in-house core; its solution is written separately.</source>
            <translation>La gravedad se ajustó junto a la geometría, por el núcleo propio; su solución se escribe aparte.</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Known gravity (station=mGal[±sigma], ...)</source>
            <translation>Gravedad conocida (estación=mGal[±sigma], ...)</translation>
        </message>
        <message>
            <source>Levelling network (from Network adjustment)</source>
            <translation>Red de nivelación (de Ajuste de red)</translation>
        </message>
        <message>
            <source>Line %1 of the velocities file does not hold numbers.</source>
            <translation>La línea %1 del archivo de velocidades no contiene números.</translation>
        </message>
        <message>
            <source>Line %1 of the velocities file has %2 numbers. Write station, vx, vy, vz in metres a year, and optionally their three standard deviations.</source>
            <translation>La línea %1 del archivo de velocidades tiene %2 números. Escriba estación, vx, vy, vz en metros por año y, opcionalmente, sus tres desviaciones estándar.</translation>
        </message>
        <message>
            <source>Multiple techniques</source>
            <translation>Múltiples técnicas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>State the epoch of the combination (a decimal year). None of the inputs states one, and GeoComp does not assume one.</source>
            <translation>Indique la época de la combinación (un año decimal). Ninguna de las entradas indica una, y GeoComp no supone una.</translation>
        </message>
        <message>
            <source>Station velocities (CSV: station, vx, vy, vz in m/yr)</source>
            <translation>Velocidades de las estaciones (CSV: estación, vx, vy, vz en m/año)</translation>
        </message>
        <message>
            <source>These fixed stations have no position any input could hold them at: %1. In a combination with GNSS, a station is held at its GNSS position.</source>
            <translation>Estas estaciones fijas no tienen posición en la que alguna entrada pueda fijarlas: %1. En una combinación con GNSS, la estación se fija en su posición GNSS.</translation>
        </message>
        <message>
            <source>This combination needs at least %1 techniques and was given %2. Use the two-technique combination that matches your inputs.</source>
            <translation>Esta combinación necesita al menos %1 técnicas y recibió %2. Use la combinación de dos técnicas que corresponde a sus entradas.</translation>
        </message>
        <message>
            <source>Total station and level</source>
            <translation>Estación total y nivel</translation>
        </message>
        <message>
            <source>Total station network (from Classical network)</source>
            <translation>Red de estación total (de Red clásica)</translation>
        </message>
        <message>
            <source>the inputs' own system</source>
            <translation>el propio sistema de las entradas</translation>
        </message>
        <message>
            <source>this run</source>
            <translation>esta ejecución</translation>
        </message>
    </context>
    <context>
        <name>CompareConfigurationsAlgorithm</name>
        <message>
            <source>%1 failed: %2</source>
            <translation>%1 falló: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Processes one pair of simultaneously observing sessions at several elevation masks, and compares the baselines they determine.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The comparison is by significance, not by size.&lt;/b&gt; A 3 mm difference is large when both solutions are good to 0.5 mm and nothing at all when they are good to 5 mm, so each difference is tested against the combined covariance of the two solutions.&lt;/p&gt;&lt;p&gt;The two runs share their observations, so treating them as independent overstates the difference's uncertainty and under-reports significance. That is the conservative direction for a test whose job is to stop a parameter being called important when it is not, and the assumption is recorded on the result.&lt;/p&gt;&lt;p&gt;A difference reported as &lt;i&gt;not significant&lt;/i&gt; is the informative answer: it says the parameter changed nothing this data can resolve.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Procesa un par de sesiones observando simultáneamente bajo varias máscaras de elevación, y compara las líneas base que determinan.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La comparación es por significación, no por tamaño.&lt;/b&gt; Una diferencia de 3 mm es grande cuando ambas soluciones tienen precisión de 0,5 mm y es irrelevante cuando tienen 5 mm, así que cada diferencia se contrasta con la covarianza combinada de las dos soluciones.&lt;/p&gt;&lt;p&gt;Las dos ejecuciones comparten sus observaciones, así que tratarlas como independientes sobrestima la incertidumbre de la diferencia y subestima la significación. Esa es la dirección conservadora para una prueba cuya función es impedir que un parámetro se considere importante cuando no lo es, y la suposición queda registrada en el resultado.&lt;/p&gt;&lt;p&gt;Una diferencia informada como &lt;i&gt;no significativa&lt;/i&gt; es la respuesta informativa: dice que el parámetro no cambió nada que estos datos puedan resolver.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Base %1 → rover %2</source>
            <translation>Base %1 → móvil %2</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Compare configurations</source>
            <translation>Comparar configuraciones</translation>
        </message>
        <message>
            <source>Comparison</source>
            <translation>Comparación</translation>
        </message>
        <message>
            <source>Comparison needs exactly one pair of simultaneously observing sessions in the folder.</source>
            <translation>La comparación necesita exactamente un par de sesiones observando simultáneamente en la carpeta.</translation>
        </message>
        <message>
            <source>Comparison table</source>
            <translation>Tabla de comparación</translation>
        </message>
        <message>
            <source>Confidence for the significance test</source>
            <translation>Confianza para la prueba de significación</translation>
        </message>
        <message>
            <source>Could not read the elevation masks from %1</source>
            <translation>No se pudieron leer las máscaras de elevación de %1</translation>
        </message>
        <message>
            <source>Elevation masks to compare (degrees)</source>
            <translation>Máscaras de elevación a comparar (grados)</translation>
        </message>
        <message>
            <source>Fewer than two configurations produced a baseline to compare.</source>
            <translation>Menos de dos configuraciones produjeron una línea base para comparar.</translation>
        </message>
        <message>
            <source>Folder of RINEX observations</source>
            <translation>Carpeta con observaciones RINEX</translation>
        </message>
        <message>
            <source>Give at least two elevation masks to compare.</source>
            <translation>Indique al menos dos máscaras de elevación para comparar.</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>No difference is significant at this confidence: over this data, the elevation mask changed nothing that can be resolved.</source>
            <translation>Ninguna diferencia es significativa con esta confianza: sobre estos datos, la máscara de elevación no cambió nada que pueda resolverse.</translation>
        </message>
        <message>
            <source>Process the same data several ways and compare, with significance.</source>
            <translation>Procesa los mismos datos de varias formas y compara, con significación.</translation>
        </message>
        <message>
            <source>mask %1°</source>
            <translation>máscara %1°</translation>
        </message>
    </context>
    <context>
        <name>DownloadProductsAlgorithm</name>
        <message>
            <source> (as %1)</source>
            <translation> (como %1)</translation>
        </message>
        <message>
            <source>%1 days were asked for; fetch at most %2 at a time.</source>
            <translation>Se pidieron %1 días; descargue como máximo %2 a la vez.</translation>
        </message>
        <message>
            <source>%1 product(s) available, %2 missing</source>
            <translation>%1 producto(s) disponible(s), %2 faltantes</translation>
        </message>
        <message>
            <source>%1: %2</source>
            <translation>%1: %2</translation>
        </message>
        <message>
            <source>%1: %2 (%3)</source>
            <translation>%1: %2 (%3)</translation>
        </message>
        <message>
            <source>%1: available from %2%3</source>
            <translation>%1: disponible en %2%3</translation>
        </message>
        <message>
            <source>%1: not available (%2)</source>
            <translation>%1: no disponible (%2)</translation>
        </message>
        <message>
            <source>%1: used the %2 orbit, as Global Settings allow.</source>
            <translation>%1: se usó la órbita %2, como permite la Configuración Global.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Resolves IGS orbits and broadcast navigation for the days of a folder's sessions, or for a range of days: each from the product cache, then the product directory, then the download services configured in Global Settings → GNSS, in their order.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Check only&lt;/b&gt; downloads nothing: it reports, for each product, whether it can be had and from where. Use it before a long batch on recent data, whose final orbits may not be published yet.&lt;/p&gt;&lt;p&gt;Processing resolves its own products; this is for fetching a campaign's products while there is a network, to process later without one. Ultra-rapid orbits are not offered.&lt;/p&gt;&lt;p&gt;A service that needs a login names a QGIS authentication configuration; GeoComp never sees the credential, and the manifest records service ids and URLs without one.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Resuelve órbitas IGS y navegación transmitida para los días de las sesiones de una carpeta, o para un rango de días: cada una desde la caché de productos, luego el directorio de productos, luego los servicios de descarga configurados en Configuración Global → GNSS, en su orden.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Solo comprobar&lt;/b&gt; no descarga nada: informa, para cada producto, si puede obtenerse y de dónde. Úselo antes de un lote largo con datos recientes, cuyas órbitas finales quizá aún no se hayan publicado.&lt;/p&gt;&lt;p&gt;El procesamiento resuelve sus propios productos; esto sirve para descargar los productos de una campaña mientras hay red, para procesar después sin ella. No se ofrecen órbitas ultrarrápidas.&lt;/p&gt;&lt;p&gt;Un servicio que requiere inicio de sesión nombra una configuración de autenticación de QGIS; GeoComp nunca ve la credencial, y el manifiesto registra ids de servicio y URLs sin ella.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Check availability only; download nothing</source>
            <translation>Solo comprobar la disponibilidad; no descargar nada</translation>
        </message>
        <message>
            <source>Choose at least one product.</source>
            <translation>Elija al menos un producto.</translation>
        </message>
        <message>
            <source>Copy the products to</source>
            <translation>Copiar los productos a</translation>
        </message>
        <message>
            <source>Could not read %1: %2</source>
            <translation>No se pudo leer %1: %2</translation>
        </message>
        <message>
            <source>Download products</source>
            <translation>Descargar productos</translation>
        </message>
        <message>
            <source>Download services, in order: %1</source>
            <translation>Servicios de descarga, en orden: %1</translation>
        </message>
        <message>
            <source>Fetch or check the orbits and navigation a campaign needs.</source>
            <translation>Descarga o comprueba las órbitas y la navegación que necesita una campaña.</translation>
        </message>
        <message>
            <source>Final</source>
            <translation>Final</translation>
        </message>
        <message>
            <source>First day (instead of, or as well as, a folder)</source>
            <translation>Primer día (en lugar de una carpeta, o además de ella)</translation>
        </message>
        <message>
            <source>Folder of RINEX observations (days from its sessions)</source>
            <translation>Carpeta de observaciones RINEX (días de sus sesiones)</translation>
        </message>
        <message>
            <source>GLONASS broadcast navigation</source>
            <translation>Navegación transmitida GLONASS</translation>
        </message>
        <message>
            <source>GPS broadcast navigation</source>
            <translation>Navegación transmitida GPS</translation>
        </message>
        <message>
            <source>Give a folder of observations with dated sessions, or a first day.</source>
            <translation>Indique una carpeta de observaciones con sesiones fechadas, o un primer día.</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>Last day</source>
            <translation>Último día</translation>
        </message>
        <message>
            <source>No download service is configured; only the cache and the product directory are looked in.</source>
            <translation>No hay ningún servicio de descarga configurado; solo se consultan la caché y el directorio de productos.</translation>
        </message>
        <message>
            <source>Orbit latency</source>
            <translation>Latencia de la órbita</translation>
        </message>
        <message>
            <source>Precise orbit (SP3)</source>
            <translation>Órbita precisa (SP3)</translation>
        </message>
        <message>
            <source>Product manifest</source>
            <translation>Manifiesto de productos</translation>
        </message>
        <message>
            <source>Products</source>
            <translation>Productos</translation>
        </message>
        <message>
            <source>Products available</source>
            <translation>Productos disponibles</translation>
        </message>
        <message>
            <source>Products missing</source>
            <translation>Productos faltantes</translation>
        </message>
        <message>
            <source>Rapid</source>
            <translation>Rápida</translation>
        </message>
        <message>
            <source>The last day, %1, is before the first, %2.</source>
            <translation>El último día, %1, es anterior al primero, %2.</translation>
        </message>
    </context>
    <context>
        <name>DynAdjustAdjustAlgorithm</name>
        <message>
            <source>%1 observation(s) have no DynAdjust equivalent and were not written: %2</source>
            <translation>%1 observación(es) no tienen equivalente en DynAdjust y no se escribieron: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts a geodetic network using &lt;b&gt;DynAdjust&lt;/b&gt;, Geoscience Australia's least-squares suite, and reads its output back into the same solution structure GeoComp's own adjustment produces. Everything downstream &amp;mdash; reports, map layers, storage, multi-epoch comparison &amp;mdash; works the same way whichever engine produced the result.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust must be installed separately.&lt;/b&gt; It is not bundled: it is a large native program under a different licence, and shipping a copy inside a QGIS plugin would make GeoComp responsible for its build. If it is not found, this algorithm says so and names what is missing.&lt;/p&gt;&lt;p&gt;DynAdjust is a suite, not one program. This runs, in order, &lt;code&gt;dnaimport&lt;/code&gt;, then &lt;code&gt;dnareftran&lt;/code&gt; if the target frame or epoch differs from the network's, then &lt;code&gt;dnageoid&lt;/code&gt; if orthometric heights take part, then &lt;code&gt;dnasegment&lt;/code&gt; for a network too large to adjust in one piece, then &lt;code&gt;dnaadjust&lt;/code&gt;. Which stages ran, and why each other one did not, is recorded in the solution's provenance.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference frame&lt;/b&gt; and &lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the frame and epoch to adjust in. Leave them empty to use the network's own. Neither is ever guessed: a frame GeoComp inferred rather than knew is a datum shift absorbed into the residuals.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Geoid grid&lt;/b&gt; &amp;mdash; an NTv2 file, required when the network has orthometric heights, because the height systems cannot be related without one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the chi-square test and the positional uncertainties. &lt;b&gt;Convergence threshold&lt;/b&gt; and &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; passed to DynAdjust unchanged.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Segmentation threshold&lt;/b&gt; &amp;mdash; above this many stations the network is segmented and adjusted in phases, which is rigorous: the block solutions and their variances equal the simultaneous ones.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust directory&lt;/b&gt; &amp;mdash; where the programs are, for this run. Empty, GeoComp uses the directory set in Global Settings under Paths and engines, then its own installation (Project &amp;rsaquo; Install an engine), then the system path. &lt;b&gt;Timeout&lt;/b&gt; &amp;mdash; seconds before a stage is abandoned and its process group killed.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Keep the working files&lt;/b&gt; &amp;mdash; writes the generated input and the raw DynAdjust output to a folder instead of a temporary directory. An adjustment that surprises you is answerable only from the files that produced it.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust configuration&lt;/b&gt; &amp;mdash; a JSON file of options of your own for each program, added after GeoComp's: &lt;code&gt;{"dnaadjust": ["--free-stn-sd", "10"]}&lt;/code&gt;. The options GeoComp sets itself, such as the confidence or the output files, are refused: each has a parameter here, and GeoComp reads the output back by them. The options are recorded in the solution's provenance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Stop after writing the input&lt;/b&gt; &amp;mdash; writes the input files and the plan to the working-files folder and stops, without running DynAdjust, which need not even be installed. Inspect or edit the files there, then run them with &lt;b&gt;Run a prepared DynAdjust job&lt;/b&gt;. Which files were edited is recorded in the result.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON: adjusted coordinates, the full variance matrix, per-observation residuals, the statistics, and the provenance recording every command line that ran.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;ENGINE_VERSION&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;CONVERGED&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; and &lt;code&gt;ADJUSTMENT_MODE&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta una red geodésica usando &lt;b&gt;DynAdjust&lt;/b&gt;, el conjunto de programas de mínimos cuadrados de Geoscience Australia, y lee su salida de vuelta en la misma estructura de solución que produce el ajuste propio de GeoComp. Todo lo que viene después &amp;mdash; informes, capas de mapa, almacenamiento, comparación multiépoca &amp;mdash; funciona igual, sea cual sea el motor que produjo el resultado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust debe instalarse por separado.&lt;/b&gt; No se distribuye junto: es un programa nativo grande, bajo otra licencia, y llevar una copia dentro de un complemento de QGIS haría a GeoComp responsable de su compilación. Si no se encuentra, este algoritmo lo indica y nombra lo que falta.&lt;/p&gt;&lt;p&gt;DynAdjust es un conjunto de programas, no uno solo. Este algoritmo ejecuta, en este orden, &lt;code&gt;dnaimport&lt;/code&gt;, luego &lt;code&gt;dnareftran&lt;/code&gt; si el marco o la época de destino difieren de los de la red, luego &lt;code&gt;dnageoid&lt;/code&gt; si participan alturas ortométricas, luego &lt;code&gt;dnasegment&lt;/code&gt; para una red demasiado grande para ajustarse de una vez, y por último &lt;code&gt;dnaadjust&lt;/code&gt;. Qué etapas se ejecutaron, y por qué cada una de las otras no, queda registrado en la procedencia de la solución.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de referencia&lt;/b&gt; y &lt;b&gt;Época de referencia&lt;/b&gt; &amp;mdash; el marco y la época en que ajustar. Déjelos vacíos para usar los de la propia red. Ninguno se adivina nunca: un marco que GeoComp infirió en lugar de conocer es un desplazamiento de datum absorbido por los residuos.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Malla del geoide&lt;/b&gt; &amp;mdash; un archivo NTv2, obligatorio cuando la red tiene alturas ortométricas, porque los sistemas de alturas no pueden relacionarse sin él.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la prueba ji-cuadrado y las incertidumbres posicionales. &lt;b&gt;Umbral de convergencia&lt;/b&gt; y &lt;b&gt;Número máximo de iteraciones&lt;/b&gt; &amp;mdash; se pasan a DynAdjust sin cambios.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbral de segmentación&lt;/b&gt; &amp;mdash; por encima de este número de estaciones la red se segmenta y se ajusta por fases, lo cual es riguroso: las soluciones de los bloques y sus varianzas son iguales a las simultáneas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Directorio de DynAdjust&lt;/b&gt; &amp;mdash; dónde están los programas, para esta ejecución. Vacío, GeoComp usa el directorio definido en Configuraciones Globales, en Rutas y motores, luego su propia instalación (Proyecto &amp;rsaquo; Instalar un motor), luego la ruta del sistema. &lt;b&gt;Tiempo límite&lt;/b&gt; &amp;mdash; segundos antes de abandonar una etapa y terminar su grupo de procesos.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Conservar los archivos de trabajo&lt;/b&gt; &amp;mdash; escribe la entrada generada y la salida sin procesar de DynAdjust en una carpeta en vez de un directorio temporal. Un ajuste que sorprende sólo puede responderse a partir de los archivos que lo produjeron.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Configuración de DynAdjust&lt;/b&gt; &amp;mdash; un archivo JSON con opciones propias para cada programa, añadidas después de las de GeoComp: &lt;code&gt;{"dnaadjust": ["--free-stn-sd", "10"]}&lt;/code&gt;. Las opciones que GeoComp define por sí mismo, como la confianza o los archivos de salida, se rechazan: cada una tiene aquí un parámetro, y GeoComp lee la salida de vuelta por ellas. Las opciones quedan registradas en la procedencia de la solución.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Detenerse tras escribir la entrada&lt;/b&gt; &amp;mdash; escribe los archivos de entrada y el plan en la carpeta de archivos de trabajo y se detiene, sin ejecutar DynAdjust, que ni siquiera necesita estar instalado. Inspeccione o edite los archivos allí y luego ejecútelos con &lt;b&gt;Ejecutar un trabajo preparado de DynAdjust&lt;/b&gt;. Los archivos editados quedan registrados en el resultado.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON: coordenadas ajustadas, la matriz de varianzas completa, residuos por observación, las estadísticas y la procedencia con cada línea de comandos que se ejecutó.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;ENGINE_VERSION&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;CONVERGED&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; y &lt;code&gt;ADJUSTMENT_MODE&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A DynAdjust program the pipeline needs is missing: %1. DynAdjust is a suite, and a partial installation fails part way through.</source>
            <translation>Falta un programa de DynAdjust que el flujo necesita: %1. DynAdjust es un conjunto de programas, y una instalación parcial falla a mitad de camino.</translation>
        </message>
        <message>
            <source>Adjust a network with Geoscience Australia's DynAdjust and read the result back.</source>
            <translation>Ajustar una red con DynAdjust de Geoscience Australia y leer el resultado de vuelta.</translation>
        </message>
        <message>
            <source>Adjust network (DynAdjust)</source>
            <translation>Ajustar red (DynAdjust)</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Convergence threshold (m)</source>
            <translation>Umbral de convergencia (m)</translation>
        </message>
        <message>
            <source>DynAdjust %1 has not been checked against this GeoComp release. It will be used, but if its output format has changed the result may be refused when it is read back.</source>
            <translation>DynAdjust %1 no se ha verificado con esta versión de GeoComp. Se usará, pero si su formato de salida ha cambiado el resultado puede rechazarse al leerlo.</translation>
        </message>
        <message>
            <source>DynAdjust configuration (JSON: options per program)</source>
            <translation>Configuración de DynAdjust (JSON: opciones por programa)</translation>
        </message>
        <message>
            <source>DynAdjust directory (empty: Global Settings, then GeoComp's installation, then the system path)</source>
            <translation>Directorio de DynAdjust (vacío: Configuraciones Globales, luego la instalación de GeoComp, luego la ruta del sistema)</translation>
        </message>
        <message>
            <source>DynAdjust was not found. Install it with Project &gt; Install an engine, or give the directory holding its programs in Global Settings under Paths and engines, or in the 'DynAdjust directory' parameter. GeoComp does not bundle it: it is a separate program under its own licence.</source>
            <translation>No se encontró DynAdjust. Instálelo con Proyecto &gt; Instalar un motor, o indique el directorio que contiene sus programas en Configuraciones Globales, en Rutas y motores, o en el parámetro 'Directorio de DynAdjust'. GeoComp no lo distribuye: es un programa aparte, con su propia licencia.</translation>
        </message>
        <message>
            <source>Geoid grid (NTv2), for orthometric heights</source>
            <translation>Malla del geoide (NTv2), para alturas ortométricas</translation>
        </message>
        <message>
            <source>Keep the generated input and raw output</source>
            <translation>Conservar la entrada generada y la salida sin procesar</translation>
        </message>
        <message>
            <source>Maximum iterations</source>
            <translation>Número máximo de iteraciones</translation>
        </message>
        <message>
            <source>Network document</source>
            <translation>Documento de red</translation>
        </message>
        <message>
            <source>Pipeline: %1</source>
            <translation>Flujo: %1</translation>
        </message>
        <message>
            <source>Reference epoch, decimal year (0 = the network's own)</source>
            <translation>Época de referencia, año decimal (0 = la de la propia red)</translation>
        </message>
        <message>
            <source>Reference frame (empty = the network's own)</source>
            <translation>Marco de referencia (vacío = el de la propia red)</translation>
        </message>
        <message>
            <source>Segment above this many stations</source>
            <translation>Segmentar por encima de este número de estaciones</translation>
        </message>
        <message>
            <source>Skipping %1: %2</source>
            <translation>Omitiendo %1: %2</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Stop after writing the input, to inspect or edit it</source>
            <translation>Detenerse tras escribir la entrada, para inspeccionarla o editarla</translation>
        </message>
        <message>
            <source>Stopped before running DynAdjust. The input is in %1: %2 and %3. Inspect or edit them there, then run Run a prepared DynAdjust job on that folder.</source>
            <translation>Detenido antes de ejecutar DynAdjust. La entrada está en %1: %2 y %3. Inspecciónelos o edítelos allí y luego ejecute Ejecutar un trabajo preparado de DynAdjust sobre esa carpeta.</translation>
        </message>
        <message>
            <source>Timeout per stage (s)</source>
            <translation>Tiempo límite por etapa (s)</translation>
        </message>
        <message>
            <source>Using DynAdjust %1 from %2.</source>
            <translation>Usando DynAdjust %1 de %2.</translation>
        </message>
        <message>
            <source>Working files</source>
            <translation>Archivos de trabajo</translation>
        </message>
    </context>
    <context>
        <name>DynAdjustCompareAlgorithm</name>
        <message>
            <source>%1 quantity/quantities disagree.</source>
            <translation>%1 magnitud(es) discrepan.</translation>
        </message>
        <message>
            <source>'%1' could not be read as JSON: %2</source>
            <translation>'%1' no se pudo leer como JSON: %2</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp solution document: %2</source>
            <translation>'%1' no es un documento de solución de GeoComp: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Compares two solution documents of the same network and reports, quantity by quantity, where they agree and where they do not.&lt;/p&gt;&lt;p&gt;Its first purpose is cross-validating GeoComp's own least-squares core against &lt;b&gt;DynAdjust&lt;/b&gt;: two independent implementations of the same problem, so agreement is evidence about both and a disagreement is a real finding about one of them. It is not limited to that. Any two solutions compare on the same terms &amp;mdash; the same network adjusted with a different stochastic model, or before and after an observation was rejected &amp;mdash; because every engine fills the same structure.&lt;/p&gt;&lt;h3&gt;What is compared&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Degrees of freedom, observation count and parameter count&lt;/b&gt; must match &lt;i&gt;exactly&lt;/i&gt;. They are properties of the model rather than of the arithmetic, so a difference means the two solved different problems &amp;mdash; and comparing residuals after that would be meaningless.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The variance factor&lt;/b&gt; is compared relatively, because an absolute tolerance is wrong at both ends: it is a large error on a variance factor of 0.001 and negligible on one of 100.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinates&lt;/b&gt;, per station, as the largest difference over the three components &amp;mdash; but only when both solutions are in the same frame. Differencing a geocentric X against a projected easting produces a number, and the number means nothing, so a frame mismatch is reported as &lt;i&gt;not compared&lt;/i&gt; with both frames named.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Residuals&lt;/b&gt;, per observation. These move before the coordinates do: a sign error in a Jacobian or a dropped correlation between the components of a GNSS baseline shows here first.&lt;/p&gt;&lt;p&gt;A quantity that could not be compared does &lt;b&gt;not&lt;/b&gt; count as a disagreement. Absence of evidence is not evidence, and treating it as such would make an unconvertible frame look like a defect in an engine.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reference solution&lt;/b&gt; and &lt;b&gt;Other solution&lt;/b&gt; &amp;mdash; JSON documents. The comparison is symmetric; the names decide only which column is which.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate tolerance&lt;/b&gt; &amp;mdash; metres. The default of 0.1 mm is far below any observation's precision and far above the last-digit differences two orderings of the same arithmetic produce.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Variance factor tolerance&lt;/b&gt; &amp;mdash; relative. The default of 1% accommodates DynAdjust printing sigma-nought to three decimals.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; plain text, one line per quantity. &lt;b&gt;Differences&lt;/b&gt; &amp;mdash; JSON, per station and per observation, for a plot or a spreadsheet.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;AGREES&lt;/code&gt;, &lt;code&gt;LARGEST_COORDINATE_DIFFERENCE&lt;/code&gt;, &lt;code&gt;LARGEST_RESIDUAL_DIFFERENCE&lt;/code&gt; and &lt;code&gt;DISAGREEMENT_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Compara dos documentos de solución de la misma red e informa, magnitud por magnitud, dónde concuerdan y dónde no.&lt;/p&gt;&lt;p&gt;Su primer propósito es validar de forma cruzada el núcleo de mínimos cuadrados de GeoComp contra &lt;b&gt;DynAdjust&lt;/b&gt;: dos implementaciones independientes del mismo problema, de modo que la concordancia es evidencia sobre ambas y una discrepancia es un hallazgo real sobre una de ellas. No se limita a eso. Dos soluciones cualesquiera se comparan en los mismos términos &amp;mdash; la misma red ajustada con un modelo estocástico distinto, o antes y después de rechazar una observación &amp;mdash; porque todo motor rellena la misma estructura.&lt;/p&gt;&lt;h3&gt;Qué se compara&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Grados de libertad, número de observaciones y número de parámetros&lt;/b&gt; deben coincidir &lt;i&gt;exactamente&lt;/i&gt;. Son propiedades del modelo y no de la aritmética, de modo que una diferencia significa que ambos resolvieron problemas distintos &amp;mdash; y comparar residuos después de eso no tendría sentido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El factor de varianza&lt;/b&gt; se compara relativamente, porque una tolerancia absoluta se equivoca en los dos extremos: es un error grande en un factor de varianza de 0,001 y despreciable en uno de 100.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordenadas&lt;/b&gt;, por estación, como la mayor diferencia entre las tres componentes &amp;mdash; pero sólo cuando ambas soluciones están en el mismo marco. Restar una X geocéntrica de una E proyectada produce un número, y el número no significa nada, de modo que una discrepancia de marco se informa como &lt;i&gt;no comparado&lt;/i&gt;, nombrando ambos marcos.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Residuos&lt;/b&gt;, por observación. Se mueven antes que las coordenadas: un error de signo en una jacobiana o una correlación perdida entre las componentes de una línea base GNSS aparece aquí primero.&lt;/p&gt;&lt;p&gt;Una magnitud que no pudo compararse &lt;b&gt;no&lt;/b&gt; cuenta como discrepancia. La ausencia de evidencia no es evidencia, y tratarla como tal haría que un marco inconvertible pareciera un defecto de un motor.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución de referencia&lt;/b&gt; y &lt;b&gt;Otra solución&lt;/b&gt; &amp;mdash; documentos JSON. La comparación es simétrica; los nombres sólo deciden qué columna es cuál.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerancia de coordenadas&lt;/b&gt; &amp;mdash; metros. El valor por omisión de 0,1 mm está muy por debajo de la precisión de cualquier observación y muy por encima de las diferencias de último dígito que producen dos ordenaciones de la misma aritmética.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerancia del factor de varianza&lt;/b&gt; &amp;mdash; relativa. El valor por omisión del 1% acomoda que DynAdjust imprima el sigma-cero con tres decimales.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; texto plano, una línea por magnitud. &lt;b&gt;Diferencias&lt;/b&gt; &amp;mdash; JSON, por estación y por observación, para una gráfica o una hoja de cálculo.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;AGREES&lt;/code&gt;, &lt;code&gt;LARGEST_COORDINATE_DIFFERENCE&lt;/code&gt;, &lt;code&gt;LARGEST_RESIDUAL_DIFFERENCE&lt;/code&gt; y &lt;code&gt;DISAGREEMENT_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Compare two solutions</source>
            <translation>Comparar dos soluciones</translation>
        </message>
        <message>
            <source>Comparison report</source>
            <translation>Informe de comparación</translation>
        </message>
        <message>
            <source>Coordinate tolerance (m)</source>
            <translation>Tolerancia de coordenadas (m)</translation>
        </message>
        <message>
            <source>Cross-validate two adjustments of the same network, whichever engines produced them.</source>
            <translation>Validar de forma cruzada dos ajustes de la misma red, sean cuales sean los motores que los produjeron.</translation>
        </message>
        <message>
            <source>Differences</source>
            <translation>Diferencias</translation>
        </message>
        <message>
            <source>No solution document was given for parameter '%1'.</source>
            <translation>No se indicó ningún documento de solución para el parámetro '%1'.</translation>
        </message>
        <message>
            <source>Other solution</source>
            <translation>Otra solución</translation>
        </message>
        <message>
            <source>Reference solution</source>
            <translation>Solución de referencia</translation>
        </message>
        <message>
            <source>The solution document '%1' does not exist.</source>
            <translation>El documento de solución '%1' no existe.</translation>
        </message>
        <message>
            <source>The two solutions name different networks (%1 and %2). Comparing them is only meaningful if they are in fact the same network under two names.</source>
            <translation>Las dos soluciones nombran redes distintas (%1 y %2). Compararlas sólo tiene sentido si son de hecho la misma red con dos nombres.</translation>
        </message>
        <message>
            <source>Variance factor tolerance (relative)</source>
            <translation>Tolerancia del factor de varianza (relativa)</translation>
        </message>
    </context>
    <context>
        <name>DynAdjustRunPreparedAlgorithm</name>
        <message>
            <source>&lt;p&gt;Runs a DynAdjust job that &lt;b&gt;Adjust network (DynAdjust)&lt;/b&gt; prepared with &lt;b&gt;Stop after writing the input&lt;/b&gt;, and reads the result back into the same solution GeoComp's own adjustment produces.&lt;/p&gt;&lt;p&gt;Between the two you may inspect the input files in the folder, and edit them: a measurement's variance to scale, a station to constrain, an option DynAdjust offers that GeoComp does not. They are run as they are now. GeoComp compares each with what it wrote, and the solution's provenance names the files that were edited, because a result from edited input is not the network's alone.&lt;/p&gt;&lt;p&gt;To leave a measurement out, set its &lt;code&gt;Ignore&lt;/code&gt; to &lt;code&gt;*&lt;/code&gt;: on the measurement, or on one direction of a direction set. It is set aside in the solution, as though you had set it aside in GeoComp. Do not add or remove measurements: the result is matched to the network measurement by measurement, in the order GeoComp wrote them, and a file with a different set is refused.&lt;/p&gt;&lt;p&gt;Do not rename or remove the files, and do not edit the job file GeoComp wrote beside them: it is how the result is read back.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Prepared folder&lt;/b&gt; &amp;mdash; the working-files folder the stopped run returned. &lt;b&gt;DynAdjust directory&lt;/b&gt; and &lt;b&gt;Timeout&lt;/b&gt; &amp;mdash; as for Adjust network (DynAdjust).&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON, as Adjust network (DynAdjust) writes it. The scalar outputs are the same, with &lt;code&gt;EDITED_INPUTS&lt;/code&gt;: the input files that were edited, or nothing.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ejecuta un trabajo de DynAdjust que &lt;b&gt;Ajustar red (DynAdjust)&lt;/b&gt; preparó con &lt;b&gt;Detenerse tras escribir la entrada&lt;/b&gt;, y lee el resultado de vuelta en la misma solución que produce el ajuste propio de GeoComp.&lt;/p&gt;&lt;p&gt;Entre uno y otro puede inspeccionar los archivos de entrada en la carpeta y editarlos: la varianza de una medición a escalar, una estación a restringir, una opción que DynAdjust ofrece y GeoComp no. Se ejecutan tal como están ahora. GeoComp compara cada uno con lo que escribió, y la procedencia de la solución nombra los archivos editados, porque un resultado de una entrada editada no es solo de la red.&lt;/p&gt;&lt;p&gt;Para dejar fuera una medición, marque su &lt;code&gt;Ignore&lt;/code&gt; con &lt;code&gt;*&lt;/code&gt;: en la medición, o en una dirección de un conjunto de direcciones. Se aparta en la solución, como si la hubiera apartado en GeoComp. No añada ni elimine mediciones: el resultado se asocia a la red medición por medición, en el orden en que GeoComp las escribió, y un archivo con un conjunto distinto se rechaza.&lt;/p&gt;&lt;p&gt;No renombre ni elimine los archivos, y no edite el archivo de trabajo que GeoComp escribió junto a ellos: es por él que el resultado se lee de vuelta.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Carpeta preparada&lt;/b&gt; &amp;mdash; la carpeta de archivos de trabajo que devolvió la ejecución detenida. &lt;b&gt;Directorio de DynAdjust&lt;/b&gt; y &lt;b&gt;Tiempo límite&lt;/b&gt; &amp;mdash; como en Ajustar red (DynAdjust).&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON, como lo escribe Ajustar red (DynAdjust). Las salidas escalares son las mismas, con &lt;code&gt;EDITED_INPUTS&lt;/code&gt;: los archivos de entrada que se editaron, o nada.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>DynAdjust directory (empty: Global Settings, then GeoComp's installation, then the system path)</source>
            <translation>Directorio de DynAdjust (vacío: Configuraciones Globales, luego la instalación de GeoComp, luego la ruta del sistema)</translation>
        </message>
        <message>
            <source>Flagged Ignore in the input, and set aside in the solution: %1.</source>
            <translation>Marcadas con Ignore en la entrada, y apartadas en la solución: %1.</translation>
        </message>
        <message>
            <source>Prepared folder</source>
            <translation>Carpeta preparada</translation>
        </message>
        <message>
            <source>Run a prepared DynAdjust job</source>
            <translation>Ejecutar un trabajo preparado de DynAdjust</translation>
        </message>
        <message>
            <source>Run the DynAdjust input prepared earlier, as written or as edited, and read the result back.</source>
            <translation>Ejecutar la entrada de DynAdjust preparada antes, tal como se escribió o como se editó, y leer el resultado de vuelta.</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>These input files were edited after GeoComp wrote them: %1. They are run as they are, and the solution records that they were edited.</source>
            <translation>Estos archivos de entrada se editaron después de que GeoComp los escribiera: %1. Se ejecutan tal como están, y la solución registra que se editaron.</translation>
        </message>
        <message>
            <source>Timeout per stage (s)</source>
            <translation>Tiempo límite por etapa (s)</translation>
        </message>
    </context>
    <context>
        <name>EqualSightsAlgorithm</name>
        <message>
            <source>%1 line(s) are exactly balanced. On those the collimation error does not enter the result at all, whatever its value.</source>
            <translation>%1 línea(s) están exactamente equilibradas. En ellas, el error de colimación no entra en absoluto en el resultado, sea cual sea su valor.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reduces each levelling line to one height difference between its two end marks, propagating the uncertainty of every staff reading.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Equal sights is the preferred method&lt;/b&gt; because equal backsight and foresight lengths cancel, to first order, the instrument's collimation error and the effects of curvature and refraction. GeoComp checks the balance and reports the &lt;b&gt;accumulated&lt;/b&gt; imbalance, which is the figure that actually matters: imbalances of opposite sign at successive setups cancel each other, and it is their sum that multiplies the collimation.&lt;/p&gt;&lt;p&gt;The line is reduced as a whole, with the collimation carried once rather than per setup. So on a balanced line the collimation contributes neither a correction nor an uncertainty &amp;mdash; whatever its value, and whatever its own uncertainty. On an imbalanced line it contributes both, and the report shows the raw and corrected differences side by side.&lt;/p&gt;&lt;p&gt;A setup carrying more than one foresight has its extra points reported as side shots. They are correlated with each other through the shared backsight; use &lt;b&gt;Extreme sights&lt;/b&gt; when that correlation matters.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; the document the importer produced.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt;, &lt;b&gt;level id&lt;/b&gt;, &lt;b&gt;collimation&lt;/b&gt; (rad) and its &lt;b&gt;uncertainty&lt;/b&gt; &amp;mdash; where the two-peg test result comes from. A collimation given here overrides the profile's, because a test done this morning beats a profile written last year. With no collimation at all, no correction is applied and the imbalance is reported instead.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Longest sight&lt;/b&gt;, &lt;b&gt;largest imbalance per setup&lt;/b&gt; and &lt;b&gt;largest imbalance per line&lt;/b&gt; (m) &amp;mdash; limits from the specification the work is under. Zero disables a check.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced lines&lt;/b&gt; &amp;mdash; JSON, the input to Closures and to Network adjustment. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Lines&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;LINE_COUNT&lt;/code&gt;, &lt;code&gt;WORST_IMBALANCE&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reduce cada línea de nivelación a un único desnivel entre sus dos referencias extremas, propagando la incertidumbre de cada lectura de mira.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las visuales iguales son el método preferente&lt;/b&gt; porque longitudes iguales de espalda y de frente cancelan, en primer orden, el error de colimación del instrumento y los efectos de la curvatura y la refracción. GeoComp verifica el equilibrio y reporta el desequilibrio &lt;b&gt;acumulado&lt;/b&gt;, que es el valor que realmente importa: desequilibrios de signo contrario en estacionamientos sucesivos se cancelan, y es su suma la que multiplica la colimación.&lt;/p&gt;&lt;p&gt;La línea se reduce como un todo, con la colimación propagada una sola vez en lugar de por estacionamiento. Así, en una línea equilibrada la colimación no aporta ni corrección ni incertidumbre &amp;mdash; sea cual sea su valor y su propia incertidumbre. En una línea desequilibrada aporta ambas, y el informe muestra lado a lado los desniveles bruto y corregido.&lt;/p&gt;&lt;p&gt;Un estacionamiento con más de una visual de frente reporta sus puntos adicionales como puntos radiados. Estos están correlacionados entre sí a través de la visual de espalda compartida; use las &lt;b&gt;visuales extremas&lt;/b&gt; cuando esa correlación importe.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estacionamientos&lt;/b&gt; &amp;mdash; el documento producido por el importador.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt;, &lt;b&gt;identificador del nivel&lt;/b&gt;, &lt;b&gt;colimación&lt;/b&gt; (rad) y su &lt;b&gt;incertidumbre&lt;/b&gt; &amp;mdash; de dónde procede el resultado del ensayo de las dos estacas. Una colimación indicada aquí prevalece sobre la del perfil, porque un ensayo hecho esta mañana vale más que un perfil escrito el año pasado. Sin colimación alguna, no se aplica corrección y en su lugar se reporta el desequilibrio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Visual más larga&lt;/b&gt;, &lt;b&gt;mayor desequilibrio por estacionamiento&lt;/b&gt; y &lt;b&gt;mayor desequilibrio por línea&lt;/b&gt; (m) &amp;mdash; límites de la especificación bajo la que se trabaja. Cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; JSON, la entrada de los cierres y del ajuste de la red. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Líneas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;LINE_COUNT&lt;/code&gt;, &lt;code&gt;WORST_IMBALANCE&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Accumulated imbalance (m)</source>
            <translation>Desequilibrio acumulado (m)</translation>
        </message>
        <message>
            <source>Balance</source>
            <translation>Equilibrio</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Collimation (mm)</source>
            <translation>Colimación (mm)</translation>
        </message>
        <message>
            <source>Collimation (rad)</source>
            <translation>Colimación (rad)</translation>
        </message>
        <message>
            <source>Collimation uncertainty (rad)</source>
            <translation>Incertidumbre de la colimación (rad)</translation>
        </message>
        <message>
            <source>Equal sights</source>
            <translation>Visuales iguales</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GeoComp levelling reductions (*.json)</source>
            <translation>Reducciones de nivelación de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Instrument</source>
            <translation>Instrumento</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfiles de instrumento</translation>
        </message>
        <message>
            <source>Largest imbalance per line (m)</source>
            <translation>Mayor desequilibrio por línea (m)</translation>
        </message>
        <message>
            <source>Largest imbalance per setup (m)</source>
            <translation>Mayor desequilibrio por estacionamiento (m)</translation>
        </message>
        <message>
            <source>Length (km)</source>
            <translation>Longitud (km)</translation>
        </message>
        <message>
            <source>Level id</source>
            <translation>Identificador del nivel</translation>
        </message>
        <message>
            <source>Levelling: equal sights</source>
            <translation>Nivelación: visuales iguales</translation>
        </message>
        <message>
            <source>Line</source>
            <translation>Línea</translation>
        </message>
        <message>
            <source>Lines</source>
            <translation>Líneas</translation>
        </message>
        <message>
            <source>Longest sight (m)</source>
            <translation>Visual más larga (m)</translation>
        </message>
        <message>
            <source>Raw dH (m)</source>
            <translation>dH bruto (m)</translation>
        </message>
        <message>
            <source>Reduce levelling lines to height differences, with the balance check.</source>
            <translation>Reduce líneas de nivelación a desniveles, con la verificación del equilibrio de las visuales.</translation>
        </message>
        <message>
            <source>Reduced lines</source>
            <translation>Líneas reducidas</translation>
        </message>
        <message>
            <source>Reduced with level profile '%1'. The collimation is carried once over each whole line, so a balanced line takes neither a correction nor an uncertainty from it.</source>
            <translation>Reducido con el perfil de nivel '%1'. La colimación se propaga una sola vez por línea completa, por lo que una línea equilibrada no recibe de ella ni corrección ni incertidumbre.</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Setup</source>
            <translation>Estacionamiento</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Side shots</source>
            <translation>Puntos radiados</translation>
        </message>
        <message>
            <source>Side shots are levelled from a line's setup without the line passing through them. A point observed once has no redundancy, so it is not adjusted; use Extreme sights when the correlation between several such points matters.</source>
            <translation>Los puntos radiados se nivelan desde un estacionamiento de la línea sin que la línea pase por ellos. Un punto observado una sola vez no tiene redundancia, por lo que no se ajusta; use las visuales extremas cuando importe la correlación entre varios de esos puntos.</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Uncertainty (mm)</source>
            <translation>Incertidumbre (mm)</translation>
        </message>
        <message>
            <source>dH (m)</source>
            <translation>dH (m)</translation>
        </message>
    </context>
    <context>
        <name>EquidistantSightsAlgorithm</name>
        <message>
            <source>&lt;p&gt;Combines reciprocal observations across an obstacle &amp;mdash; a river is the case the proposal names &amp;mdash; where an equal-sight setup is impossible.&lt;/p&gt;&lt;p&gt;Each bank's instrument reads the staff on its own side over a short sight and the staff across the water over a long one. The long sight carries almost all of the error, and it enters the two determinations with &lt;b&gt;opposite sign&lt;/b&gt;, so it cancels in their mean. That cancellation is the method.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The uncertainty is deliberately more conservative than for equal sights.&lt;/b&gt; Refraction over water varies rapidly and asymmetrically, and the two observations were not simultaneous, so the symmetry the method relies on holds only approximately. The propagated variance is multiplied by the inflation factor and the result is marked as an empirical scaling, which follows it into every report. Setting the factor to one is allowed and is reported as a warning, because it claims the two observations saw identical air.&lt;/p&gt;&lt;p&gt;The two determinations' &lt;b&gt;discrepancy&lt;/b&gt; is reported. Its expected value is zero; a large one says the refraction changed between them, which is precisely the assumption the method makes, so it is shown rather than averaged away.&lt;/p&gt;&lt;h3&gt;Input layout&lt;/h3&gt;&lt;p&gt;Each crossing is &lt;b&gt;two setups&lt;/b&gt; in the imported book, each with one backsight (the near staff) and one foresight (the far staff), and the second setup observes the same two stations the other way round. Setups are paired in the order they appear.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; the document the importer produced. &lt;b&gt;Variance inflation&lt;/b&gt; &amp;mdash; at least one. &lt;b&gt;Discrepancy tolerance&lt;/b&gt; (m) &amp;mdash; above which the two banks' disagreement is reported; zero disables it.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Height differences&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Crossings&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;CROSSING_COUNT&lt;/code&gt; and &lt;code&gt;WORST_DISCREPANCY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Combina observaciones recíprocas a través de un obstáculo &amp;mdash; un río es el caso que la propuesta menciona &amp;mdash; donde un estacionamiento de visuales iguales es imposible.&lt;/p&gt;&lt;p&gt;El instrumento de cada orilla lee la mira de su propio lado en una visual corta y la mira del otro lado del agua en una visual larga. La visual larga carga casi todo el error, y este entra en las dos determinaciones con &lt;b&gt;signo contrario&lt;/b&gt;, por lo que se cancela en su media. Esa cancelación es el método.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La incertidumbre es deliberadamente más conservadora que la de las visuales iguales.&lt;/b&gt; La refracción sobre el agua varía rápida y asimétricamente, y las dos observaciones no fueron simultáneas, por lo que la simetría en la que se apoya el método solo se cumple aproximadamente. La varianza propagada se multiplica por el factor de inflación y el resultado se marca como escalado empírico, que lo acompaña en todos los informes. Fijar el factor en uno está permitido y se reporta como advertencia, porque afirma que las dos observaciones vieron exactamente el mismo aire.&lt;/p&gt;&lt;p&gt;Se reporta la &lt;b&gt;discrepancia&lt;/b&gt; entre las dos determinaciones. Su valor esperado es cero; una discrepancia grande indica que la refracción cambió entre ellas, que es precisamente el supuesto del método, por lo que se muestra en lugar de diluirse en la media.&lt;/p&gt;&lt;h3&gt;Disposición de los datos&lt;/h3&gt;&lt;p&gt;Cada travesía son &lt;b&gt;dos estacionamientos&lt;/b&gt; en la libreta importada, cada una con una visual de espalda (la mira cercana) y una de frente (la mira lejana), observando el segundo estacionamiento las mismas dos estaciones en sentido inverso. Los estacionamientos se emparejan en el orden en que aparecen.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estacionamientos&lt;/b&gt; &amp;mdash; el documento producido por el importador. &lt;b&gt;Inflación de la varianza&lt;/b&gt; &amp;mdash; al menos uno. &lt;b&gt;Tolerancia de la discrepancia&lt;/b&gt; (m) &amp;mdash; por encima de la cual se reporta la divergencia entre las orillas; cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Travesías&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;CROSSING_COUNT&lt;/code&gt; y &lt;code&gt;WORST_DISCREPANCY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A reciprocal crossing is two setups, one from each bank, so the book must hold an even number of at least two. It holds %1.</source>
            <translation>Una travesía recíproca son dos estacionamientos, uno desde cada orilla, por lo que la libreta debe contener un número par de al menos dos. Contiene %1.</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Crossings</source>
            <translation>Travesías</translation>
        </message>
        <message>
            <source>Discrepancy</source>
            <translation>Discrepancia</translation>
        </message>
        <message>
            <source>Discrepancy (mm)</source>
            <translation>Discrepancia (mm)</translation>
        </message>
        <message>
            <source>Discrepancy tolerance (m)</source>
            <translation>Tolerancia de la discrepancia (m)</translation>
        </message>
        <message>
            <source>Equidistant sights</source>
            <translation>Visuales equidistantes</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>From the far bank (m)</source>
            <translation>Desde la orilla opuesta (m)</translation>
        </message>
        <message>
            <source>From the near bank (m)</source>
            <translation>Desde la orilla cercana (m)</translation>
        </message>
        <message>
            <source>GeoComp height differences (*.json)</source>
            <translation>Desniveles GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height differences</source>
            <translation>Desniveles</translation>
        </message>
        <message>
            <source>Levelling: equidistant sights</source>
            <translation>Nivelación: visuales equidistantes</translation>
        </message>
        <message>
            <source>Mean dH (m)</source>
            <translation>dH medio (m)</translation>
        </message>
        <message>
            <source>Reciprocal levelling across an obstacle, from both banks.</source>
            <translation>Nivelación recíproca a través de un obstáculo, desde ambas orillas.</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Setup '%1' carries several foresights. A reciprocal crossing has one near staff and one far staff per bank.</source>
            <translation>El estacionamiento '%1' tiene varias visuales de frente. Una travesía recíproca tiene una mira cercana y una mira lejana por orilla.</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>The discrepancy is the two banks' disagreement. Its expected value is zero; a large one says the refraction changed between the two observations, which is the assumption the method rests on.</source>
            <translation>La discrepancia es la divergencia entre las dos orillas. Su valor esperado es cero; una discrepancia grande indica que la refracción cambió entre las dos observaciones, que es justamente el supuesto en el que se apoya el método.</translation>
        </message>
        <message>
            <source>The variance was multiplied by %1 and the result marked as an empirical scaling. Refraction over water varies rapidly and asymmetrically, and the two reciprocal observations were not simultaneous.</source>
            <translation>La varianza se multiplicó por %1 y el resultado se marcó como escalado empírico. La refracción sobre el agua varía rápida y asimétricamente, y las dos observaciones recíprocas no fueron simultáneas.</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Uncertainty (mm)</source>
            <translation>Incertidumbre (mm)</translation>
        </message>
        <message>
            <source>Uncertainty model</source>
            <translation>Modelo de incertidumbre</translation>
        </message>
        <message>
            <source>Variance inflation</source>
            <translation>Factor de inflación de la varianza</translation>
        </message>
    </context>
    <context>
        <name>ExportToPostgisAlgorithm</name>
        <message>
            <source>&lt;p&gt;Copies every table of a GeoComp GeoPackage into a schema of a PostGIS database, for a project that several people work on or that grows large. Nothing is converted through text: coordinates, covariances and their provenance arrive exactly as they were.&lt;/p&gt;&lt;p&gt;Both stores are then compared, every row of every table, and the log says so. The schema must be new or empty; an existing project is never overwritten. The database is reached through a connection saved in QGIS, with its login, and must have the PostGIS extension.&lt;/p&gt;&lt;p&gt;An older GeoPackage is migrated first, after a backup.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Copia todas las tablas de un GeoPackage de GeoComp a un esquema de una base de datos PostGIS, para un proyecto en el que trabajan varias personas o que crece mucho. Nada se convierte a texto: las coordenadas, las covarianzas y su procedencia llegan exactamente como eran.&lt;/p&gt;&lt;p&gt;Después se comparan los dos repositorios, cada fila de cada tabla, y el registro lo indica. El esquema debe ser nuevo o estar vacío; nunca se sobrescribe un proyecto existente. Se accede a la base de datos mediante una conexión guardada en QGIS, con su inicio de sesión, y debe tener la extensión PostGIS.&lt;/p&gt;&lt;p&gt;Un GeoPackage más antiguo se migra antes, tras una copia de seguridad.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Copy a GeoPackage project into a PostGIS schema, and check the copy.</source>
            <translation>Copia un proyecto GeoPackage a un esquema PostGIS y comprueba la copia.</translation>
        </message>
        <message>
            <source>Export project to PostGIS</source>
            <translation>Exportar proyecto a PostGIS</translation>
        </message>
        <message>
            <source>GeoComp GeoPackage</source>
            <translation>GeoPackage de GeoComp</translation>
        </message>
        <message>
            <source>Project store</source>
            <translation>Repositorio del proyecto</translation>
        </message>
        <message>
            <source>Rows copied</source>
            <translation>Filas copiadas</translation>
        </message>
    </context>
    <context>
        <name>ExtremeSightsAlgorithm</name>
        <message>
            <source>&lt;p&gt;Reduces each instrument setup to one height difference per foresight, keeping the &lt;b&gt;full covariance&lt;/b&gt; between them.&lt;/p&gt;&lt;p&gt;All the foresights of a setup subtract the same backsight reading, so they share its error. Between two of them the backsight &lt;b&gt;cancels exactly&lt;/b&gt;: their height difference is one foresight minus the other, and the backsight does not appear. Treating the two as independent adds twice the backsight variance that is not there and reports an uncertainty too &lt;b&gt;large&lt;/b&gt; &amp;mdash; which is the opposite of the usual failure, and can have a network declared inadequate that is in fact fine.&lt;/p&gt;&lt;p&gt;The report gives both: the difference from the backsighted station to each foresight, and the difference between each pair of foresights computed through the covariance, next to what treating them independently would have claimed.&lt;/p&gt;&lt;p&gt;The correlation is carried into the output document as a covariance, so a network adjustment built from these setups keeps it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; the document the importer produced. &lt;b&gt;Only setups with several foresights&lt;/b&gt; &amp;mdash; skip the ordinary one-foresight setups, which have no correlation to show.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt; and &lt;b&gt;level id&lt;/b&gt; &amp;mdash; where the reading precision comes from. &lt;b&gt;Longest sight&lt;/b&gt; and &lt;b&gt;largest imbalance per setup&lt;/b&gt; (m) &amp;mdash; limits; zero disables a check.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Height differences&lt;/b&gt; &amp;mdash; JSON with the covariances. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Differences&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;DIFFERENCE_COUNT&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reduce cada estacionamiento del instrumento a un desnivel por cada visual de frente, conservando la &lt;b&gt;covarianza completa&lt;/b&gt; entre ellos.&lt;/p&gt;&lt;p&gt;Todas las visuales de frente de un estacionamiento restan la misma lectura de espalda, por lo que comparten su error. Entre dos de ellas la visual de espalda &lt;b&gt;se cancela exactamente&lt;/b&gt;: su desnivel es una visual de frente menos la otra, y la de espalda no aparece. Tratarlas como independientes añade dos veces la varianza de la espalda que no está ahí y reporta una incertidumbre demasiado &lt;b&gt;grande&lt;/b&gt; &amp;mdash; lo contrario del fallo habitual, y puede llevar a declarar inadecuada una red que en realidad está bien.&lt;/p&gt;&lt;p&gt;El informe presenta ambos: el desnivel de la estación visada de espalda a cada visual de frente, y el desnivel entre cada par de visuales de frente calculado a través de la covarianza, junto a lo que un tratamiento independiente habría afirmado.&lt;/p&gt;&lt;p&gt;La correlación se lleva al documento de salida como una covarianza, por lo que un ajuste de red construido a partir de estos estacionamientos la conserva.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estacionamientos&lt;/b&gt; &amp;mdash; el documento producido por el importador. &lt;b&gt;Solo estacionamientos con varias visuales de frente&lt;/b&gt; &amp;mdash; omite los estacionamientos ordinarios de una sola visual, que no tienen correlación que mostrar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt; e &lt;b&gt;identificador del nivel&lt;/b&gt; &amp;mdash; de dónde procede la precisión de las lecturas. &lt;b&gt;Visual más larga&lt;/b&gt; y &lt;b&gt;mayor desequilibrio por estacionamiento&lt;/b&gt; (m) &amp;mdash; límites; cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON con las covarianzas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;DIFFERENCE_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Differences</source>
            <translation>Desniveles</translation>
        </message>
        <message>
            <source>Differences between foresighted points</source>
            <translation>Desniveles entre los puntos visados</translation>
        </message>
        <message>
            <source>Extreme sights</source>
            <translation>Visuales extremas</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GeoComp height differences (*.json)</source>
            <translation>Desniveles GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height differences</source>
            <translation>Desniveles</translation>
        </message>
        <message>
            <source>Height differences from each setup</source>
            <translation>Desniveles desde cada estacionamiento</translation>
        </message>
        <message>
            <source>If treated as independent (mm)</source>
            <translation>Si se tratan como independientes (mm)</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfiles de instrumento</translation>
        </message>
        <message>
            <source>Largest imbalance per setup (m)</source>
            <translation>Mayor desequilibrio por estacionamiento (m)</translation>
        </message>
        <message>
            <source>Level id</source>
            <translation>Identificador del nivel</translation>
        </message>
        <message>
            <source>Levelling: extreme sights</source>
            <translation>Nivelación: visuales extremas</translation>
        </message>
        <message>
            <source>Longest sight (m)</source>
            <translation>Visual más larga (m)</translation>
        </message>
        <message>
            <source>No setup carries several foresights. Extreme sights is for a setup that levelled a group of points at once; clear 'Only setups with several foresights' to reduce the ordinary ones too.</source>
            <translation>Ningún estacionamiento tiene varias visuales de frente. Las visuales extremas son para un estacionamiento que niveló un conjunto de puntos a la vez; desmarque 'Solo estacionamientos con varias visuales de frente' para reducir también los estacionamientos ordinarios.</translation>
        </message>
        <message>
            <source>Only setups with several foresights</source>
            <translation>Solo estacionamientos con varias visuales de frente</translation>
        </message>
        <message>
            <source>Overstated by (%)</source>
            <translation>Sobrestimada en (%)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Setup</source>
            <translation>Estacionamiento</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Several foresights from one setup, kept correlated through the backsight.</source>
            <translation>Varias visuales de frente desde un estacionamiento, mantenidas correlacionadas por la visual de espalda.</translation>
        </message>
        <message>
            <source>The backsight cancels between two foresights of one setup, so these differences are better determined than independent treatment would suggest. The last column is how much an independent treatment would have overstated the uncertainty by.</source>
            <translation>La visual de espalda se cancela entre dos visuales de frente del mismo estacionamiento, por lo que estos desniveles quedan mejor determinados de lo que un tratamiento independiente sugeriría. La última columna indica en cuánto un tratamiento independiente habría sobrestimado la incertidumbre.</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Uncertainty (mm)</source>
            <translation>Incertidumbre (mm)</translation>
        </message>
        <message>
            <source>Why the correlation helps</source>
            <translation>Por qué la correlación ayuda</translation>
        </message>
        <message>
            <source>dH (m)</source>
            <translation>dH (m)</translation>
        </message>
    </context>
    <context>
        <name>GeoComp</name>
        <message>
            <source>GeoComp</source>
            <translation>GeoComp</translation>
        </message>
    </context>
    <context>
        <name>GeoCompAbout</name>
        <message>
            <source>A framework for pre-analysis, GNSS processing and adjustment of geodetic networks inside QGIS.</source>
            <translation>Un framework para preanálisis, procesamiento GNSS y ajuste de redes geodésicas dentro de QGIS.</translation>
        </message>
        <message>
            <source>About GeoComp</source>
            <translation>Acerca de GeoComp</translation>
        </message>
        <message>
            <source>Developed at the Departamento de Geomática, Setor de Ciências da Terra, Universidade Federal do Paraná.</source>
            <translation>Desarrollado en el Departamento de Geomática, Setor de Ciências da Terra, Universidade Federal do Paraná.</translation>
        </message>
        <message>
            <source>GeoComp is free software under the GNU General Public License, version 2 or later. You may use it, including commercially, study it, modify it and redistribute it.</source>
            <translation>GeoComp es software libre bajo la GNU General Public License, versión 2 o posterior. Puede utilizarlo, incluso comercialmente, estudiarlo, modificarlo y redistribuirlo.</translation>
        </message>
        <message>
            <source>GeoComp runs external engines as separate programs. They are not part of GeoComp and carry their own licences:</source>
            <translation>GeoComp ejecuta motores externos como programas separados. No forman parte de GeoComp y tienen sus propias licencias:</translation>
        </message>
        <message>
            <source>Licence</source>
            <translation>Licencia</translation>
        </message>
        <message>
            <source>Processing engines</source>
            <translation>Motores de procesamiento</translation>
        </message>
        <message>
            <source>Source code</source>
            <translation>Código fuente</translation>
        </message>
        <message>
            <source>not installed</source>
            <translation>no instalado</translation>
        </message>
        <message>
            <source>version %1, at %2</source>
            <translation>versión %1, en %2</translation>
        </message>
    </context>
    <context>
        <name>GeoCompAdjustmentReport</name>
        <message>
            <source>(assumed: none was stated)</source>
            <translation>(supuesta: no se declaró ninguna)</translation>
        </message>
        <message>
            <source>(not recorded)</source>
            <translation>(no registrado)</translation>
        </message>
        <message>
            <source>Active observations</source>
            <translation>Observaciones activas</translation>
        </message>
        <message>
            <source>Adjusted N (m)</source>
            <translation>N ajustado (m)</translation>
        </message>
        <message>
            <source>Adjusted coordinates</source>
            <translation>Coordenadas ajustadas</translation>
        </message>
        <message>
            <source>Adjusted gravity</source>
            <translation>Gravedad ajustada</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estaciones ajustadas</translation>
        </message>
        <message>
            <source>Adjustment report</source>
            <translation>Informe de ajuste</translation>
        </message>
        <message>
            <source>Algorithm</source>
            <translation>Algoritmo</translation>
        </message>
        <message>
            <source>An observation with a redundancy number near zero is uncheckable: no blunder in it is detectable at all. A network full of them can pass every statistical test while being wrong, so they are listed here whether or not anything else in this report looks amiss.</source>
            <translation>Una observación con número de redundancia próximo a cero no es verificable: ningún error grosero en ella es siquiera detectable. Una red llena de ellas puede superar todas las pruebas estadísticas estando equivocada, por lo que se listan aquí con independencia de que todo lo demás en este informe parezca correcto.</translation>
        </message>
        <message>
            <source>Applied to</source>
            <translation>Aplicada a</translation>
        </message>
        <message>
            <source>Astro-geodetic</source>
            <translation>Astrogeodesia</translation>
        </message>
        <message>
            <source>CANDIDATE</source>
            <translation>CANDIDATA</translation>
        </message>
        <message>
            <source>Candidates, not rejections. GeoComp never removes an observation on its own: in a monitoring network the displacement being measured is exactly what an automatic outlier remover would delete.</source>
            <translation>Candidatos, no rechazos. GeoComp nunca elimina una observación por su cuenta: en una red de monitorización, el desplazamiento que se está midiendo es exactamente lo que un eliminador automático de errores groseros borraría.</translation>
        </message>
        <message>
            <source>Command line</source>
            <translation>Línea de comandos</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Components</source>
            <translation>Componentes</translation>
        </message>
        <message>
            <source>Condition number</source>
            <translation>Número de condición</translation>
        </message>
        <message>
            <source>Confidence</source>
            <translation>Confianza</translation>
        </message>
        <message>
            <source>Constrained stations</source>
            <translation>Estaciones constreñidas</translation>
        </message>
        <message>
            <source>Constraint</source>
            <translation>Constricción</translation>
        </message>
        <message>
            <source>Constraints</source>
            <translation>Constricciones</translation>
        </message>
        <message>
            <source>Converged</source>
            <translation>Convergió</translation>
        </message>
        <message>
            <source>Coordinate reference system</source>
            <translation>Sistema de referencia de coordenadas</translation>
        </message>
        <message>
            <source>Correlated clusters</source>
            <translation>Agrupamientos correlacionados</translation>
        </message>
        <message>
            <source>Count</source>
            <translation>Cantidad</translation>
        </message>
        <message>
            <source>Created</source>
            <translation>Creado en</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>Decision</source>
            <translation>Decisión</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Digest</source>
            <translation>Resumen criptográfico</translation>
        </message>
        <message>
            <source>DynAdjust</source>
            <translation>DynAdjust</translation>
        </message>
        <message>
            <source>Effective value</source>
            <translation>Valor efectivo</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Engine version</source>
            <translation>Versión del motor</translation>
        </message>
        <message>
            <source>Epoch</source>
            <translation>Época</translation>
        </message>
        <message>
            <source>Error ellipses</source>
            <translation>Elipses de error</translation>
        </message>
        <message>
            <source>Estimated by least-squares variance component estimation, one factor per technique. Each technique's weights were rescaled by its factor, and the solution above is the rescaled network's.</source>
            <translation>Estimados por estimación de componentes de varianza por mínimos cuadrados, un factor por técnica. Los pesos de cada técnica se reescalaron por su factor, y la solución anterior es la de la red reescalada.</translation>
        </message>
        <message>
            <source>Every observation in this adjustment is checkable.</source>
            <translation>Todas las observaciones de este ajuste son verificables.</translation>
        </message>
        <message>
            <source>Every transformation the combination applied, with the input and the position it was applied to. A datum shift not listed here was not applied.</source>
            <translation>Toda transformación que aplicó la combinación, con la entrada y la posición a la que se aplicó. Un cambio de datum que no figure aquí no se aplicó.</translation>
        </message>
        <message>
            <source>Every uncertainty in this report was propagated rigorously: no approximate strategy was used at any step.</source>
            <translation>Todas las incertidumbres de este informe se propagaron rigurosamente: no se usó ninguna estrategia aproximada en ningún paso.</translation>
        </message>
        <message>
            <source>Excluded by hand</source>
            <translation>Excluida manualmente</translation>
        </message>
        <message>
            <source>Exit code</source>
            <translation>Código de salida</translation>
        </message>
        <message>
            <source>External effect</source>
            <translation>Efecto externo</translation>
        </message>
        <message>
            <source>External effect (%1)</source>
            <translation>Efecto externo (%1)</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>Field</source>
            <translation>Campo</translation>
        </message>
        <message>
            <source>Frame</source>
            <translation>Marco</translation>
        </message>
        <message>
            <source>Frames and epochs</source>
            <translation>Marcos y épocas</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>GeoComp</source>
            <translation>GeoComp</translation>
        </message>
        <message>
            <source>GeoComp in-house core</source>
            <translation>Núcleo propio de GeoComp</translation>
        </message>
        <message>
            <source>Geoid model</source>
            <translation>Modelo geoidal</translation>
        </message>
        <message>
            <source>Geoid priors</source>
            <translation>Información a priori del geoide</translation>
        </message>
        <message>
            <source>Geoid residuals</source>
            <translation>Residuos del geoide</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>Global test: %1</source>
            <translation>Prueba global: %1</translation>
        </message>
        <message>
            <source>Gravimetry</source>
            <translation>Gravimetría</translation>
        </message>
        <message>
            <source>Gravity (%1)</source>
            <translation>Gravedad (%1)</translation>
        </message>
        <message>
            <source>Identification</source>
            <translation>Identificación</translation>
        </message>
        <message>
            <source>Input</source>
            <translation>Entrada</translation>
        </message>
        <message>
            <source>Inputs</source>
            <translation>Entradas</translation>
        </message>
        <message>
            <source>Inputs are recorded by id and by content digest. The digest is what turns &amp;quot;reproduce this&amp;quot; into something checkable: the same id with different content is a different run.</source>
            <translation>Las entradas se registran por identificador y por resumen criptográfico del contenido. El resumen es lo que convierte &amp;quot;reproducir esto&amp;quot; en algo verificable: el mismo identificador con contenido distinto es otra ejecución.</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iteraciones</translation>
        </message>
        <message>
            <source>Kind</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Largest correction</source>
            <translation>Mayor corrección</translation>
        </message>
        <message>
            <source>Largest |w|</source>
            <translation>Mayor |w|</translation>
        </message>
        <message>
            <source>Levelling</source>
            <translation>Nivelación</translation>
        </message>
        <message>
            <source>Lower critical</source>
            <translation>Crítico inferior</translation>
        </message>
        <message>
            <source>MDB</source>
            <translation>MDB</translation>
        </message>
        <message>
            <source>MDB (%1)</source>
            <translation>MDB (%1)</translation>
        </message>
        <message>
            <source>Model N (m)</source>
            <translation>N del modelo (m)</translation>
        </message>
        <message>
            <source>Model std. dev. (m)</source>
            <translation>Desv. estándar del modelo (m)</translation>
        </message>
        <message>
            <source>NO</source>
            <translation>NO</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>No effective parameters were recorded for this run.</source>
            <translation>No se registraron parámetros efectivos para esta ejecución.</translation>
        </message>
        <message>
            <source>No error ellipse was computed. A one-dimensional adjustment has none: a height has an uncertainty, not an ellipse.</source>
            <translation>No se calculó ninguna elipse de error. Un ajuste unidimensional no tiene ninguna: una altitud tiene una incertidumbre, no una elipse.</translation>
        </message>
        <message>
            <source>No global test was run for this solution.</source>
            <translation>No se ejecutó ninguna prueba global para esta solución.</translation>
        </message>
        <message>
            <source>No per-technique breakdown: its redundancy numbers come from the in-house adjustment's design, and DynAdjust's output does not carry them. The residuals are listed per observation below.</source>
            <translation>Sin desglose por técnica: sus números de redundancia provienen del diseño del ajuste propio, y la salida de DynAdjust no los contiene. Los residuos se listan por observación más abajo.</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observation results</source>
            <translation>Resultados por observación</translation>
        </message>
        <message>
            <source>Observation type</source>
            <translation>Tipo de observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Observations by type</source>
            <translation>Observaciones por tipo</translation>
        </message>
        <message>
            <source>Observations set aside</source>
            <translation>Observaciones dejadas fuera</translation>
        </message>
        <message>
            <source>Orientation</source>
            <translation>Orientación</translation>
        </message>
        <message>
            <source>Outlier candidates</source>
            <translation>Candidatos a error grosero</translation>
        </message>
        <message>
            <source>Parameter</source>
            <translation>Parámetro</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Per-technique breakdown</source>
            <translation>Desglose por técnica</translation>
        </message>
        <message>
            <source>Positional uncertainty (mm)</source>
            <translation>Incertidumbre posicional (mm)</translation>
        </message>
        <message>
            <source>Provenance</source>
            <translation>Procedencia</translation>
        </message>
        <message>
            <source>QGIS</source>
            <translation>QGIS</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reason</source>
            <translation>Motivo</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Rejected by a test</source>
            <translation>Rechazada por una prueba</translation>
        </message>
        <message>
            <source>Reliability</source>
            <translation>Fiabilidad</translation>
        </message>
        <message>
            <source>Report template</source>
            <translation>Plantilla de informe</translation>
        </message>
        <message>
            <source>Residual</source>
            <translation>Residuo</translation>
        </message>
        <message>
            <source>Residual (%1)</source>
            <translation>Residuo (%1)</translation>
        </message>
        <message>
            <source>Residual (m)</source>
            <translation>Residuo (m)</translation>
        </message>
        <message>
            <source>Results</source>
            <translation>Resultados</translation>
        </message>
        <message>
            <source>Row</source>
            <translation>Fila</translation>
        </message>
        <message>
            <source>Rows</source>
            <translation>Filas</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieje mayor (mm)</translation>
        </message>
        <message>
            <source>Semi-minor (mm)</source>
            <translation>Semieje menor (mm)</translation>
        </message>
        <message>
            <source>Setting</source>
            <translation>Configuración</translation>
        </message>
        <message>
            <source>Share</source>
            <translation>Proporción</translation>
        </message>
        <message>
            <source>Shown in %1, as the Gravimeter settings ask; the solution stores m/s². A station held fixed has no uncertainty of its own and is not listed.</source>
            <translation>Mostrado en %1, como piden las configuraciones del Gravímetro; la solución almacena m/s². Una estación mantenida fija no tiene incertidumbre propia y no se lista.</translation>
        </message>
        <message>
            <source>Software</source>
            <translation>Software</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Some uncertainties in this report are APPROXIMATE. The strategies used were: %1. An approximate figure presented as a rigorously propagated one misrepresents the quality of the survey, which is why this notice cannot be removed by a template.</source>
            <translation>Algunas incertidumbres de este informe son APROXIMADAS. Las estrategias usadas fueron: %1. Un valor aproximado presentado como rigurosamente propagado tergiversa la calidad del levantamiento, y por eso este aviso no puede eliminarse mediante una plantilla.</translation>
        </message>
        <message>
            <source>Source</source>
            <translation>Origen</translation>
        </message>
        <message>
            <source>Standard deviation</source>
            <translation>Desviación estándar</translation>
        </message>
        <message>
            <source>Standardised</source>
            <translation>Estandarizado</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estadístico</translation>
        </message>
        <message>
            <source>Statistics</source>
            <translation>Estadísticas</translation>
        </message>
        <message>
            <source>Status</source>
            <translation>Estado</translation>
        </message>
        <message>
            <source>Steps</source>
            <translation>Pasos</translation>
        </message>
        <message>
            <source>Superseded by</source>
            <translation>Sustituida por</translation>
        </message>
        <message>
            <source>Technique</source>
            <translation>Técnica</translation>
        </message>
        <message>
            <source>Techniques</source>
            <translation>Técnicas</translation>
        </message>
        <message>
            <source>Test</source>
            <translation>Prueba</translation>
        </message>
        <message>
            <source>The geoid model %1 tested by the survey: at each station where an orthometric height met an ellipsoidal one, the undulation the adjustment found against the one the model gave.</source>
            <translation>El modelo geoidal %1 puesto a prueba por el levantamiento: en cada estación donde una altura ortométrica se encontró con una elipsoidal, la ondulación que obtuvo el ajuste frente a la que dio el modelo.</translation>
        </message>
        <message>
            <source>The global test failed. Either the observations disagree with each other more than their weights allow, or the weights are wrong — the test cannot distinguish the two, and reporting it as &amp;quot;the adjustment failed&amp;quot; would.</source>
            <translation>La prueba global falló. O las observaciones difieren entre sí más de lo que sus pesos permiten, o los pesos son incorrectos — la prueba no distingue ambos casos, y comunicarlo como &amp;quot;el ajuste falló&amp;quot; sí lo haría.</translation>
        </message>
        <message>
            <source>The network was not supplied to the report, so the input summary is limited to what the solution records.</source>
            <translation>La red no se suministró al informe, por lo que el resumen de entradas se limita a lo que registra la solución.</translation>
        </message>
        <message>
            <source>The redundancy each technique carries, and its own part of the weighted squares. The parts add up to the whole. A technique's vᵀPv / r is a quick reading of how its weights fit, not its variance component: that is estimated below when it was asked for.</source>
            <translation>La redundancia que aporta cada técnica y su propia parte de los cuadrados ponderados. Las partes suman el todo. El vᵀPv / r de una técnica es una lectura rápida de cómo encajan sus pesos, no su componente de varianza: este se estima más abajo cuando se pidió.</translation>
        </message>
        <message>
            <source>The scope column is what makes a run reproducible: the same value reached from a project override and from the built-in default are different statements to somebody repeating the work.</source>
            <translation>La columna del ámbito es lo que hace reproducible una ejecución: el mismo valor obtenido de una anulación del proyecto y del valor por defecto son afirmaciones distintas para quien repite el trabajo.</translation>
        </message>
        <message>
            <source>These observations are not in this adjustment. Each is kept with the reason it was set aside, and returns to the adjustment when its status is set back to active and the network is adjusted again.</source>
            <translation>Estas observaciones no están en este ajuste. Cada una se conserva con el motivo por el que se dejó fuera, y vuelve al ajuste cuando su estado se restablece a activa y la red se ajusta de nuevo.</translation>
        </message>
        <message>
            <source>This solution adjusted no station.</source>
            <translation>Esta solución no ajustó ninguna estación.</translation>
        </message>
        <message>
            <source>This solution carries no provenance record, so what produced it cannot be reproduced from this report.</source>
            <translation>Esta solución no lleva registro de procedencia, por lo que lo que la produjo no puede reproducirse a partir de este informe.</translation>
        </message>
        <message>
            <source>This solution recorded no per-observation results.</source>
            <translation>Esta solución no registró resultados por observación.</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hacia</translation>
        </message>
        <message>
            <source>Total station</source>
            <translation>Estación total</translation>
        </message>
        <message>
            <source>Type</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Uncertainty</source>
            <translation>Incertidumbre</translation>
        </message>
        <message>
            <source>Uncertainty mode</source>
            <translation>Modo de incertidumbre</translation>
        </message>
        <message>
            <source>Uncheckable</source>
            <translation>No verificables</translation>
        </message>
        <message>
            <source>Uncheckable observations</source>
            <translation>Observaciones no verificables</translation>
        </message>
        <message>
            <source>Units</source>
            <translation>Unidades</translation>
        </message>
        <message>
            <source>Upper critical</source>
            <translation>Crítico superior</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Variance components</source>
            <translation>Componentes de varianza</translation>
        </message>
        <message>
            <source>Variance factor</source>
            <translation>Factor de varianza</translation>
        </message>
        <message>
            <source>Variance factor a posteriori</source>
            <translation>Factor de varianza a posteriori</translation>
        </message>
        <message>
            <source>Variance factor a priori</source>
            <translation>Factor de varianza a priori</translation>
        </message>
        <message>
            <source>Version</source>
            <translation>Versión</translation>
        </message>
        <message>
            <source>Weighted constraints</source>
            <translation>Restricciones ponderadas</translation>
        </message>
        <message>
            <source>What a failed global test means</source>
            <translation>Qué significa una prueba global fallida</translation>
        </message>
        <message>
            <source>Where each value came from</source>
            <translation>De dónde vino cada valor</translation>
        </message>
        <message>
            <source>Why this engine</source>
            <translation>Por qué este motor</translation>
        </message>
        <message>
            <source>accepted</source>
            <translation>aceptada</translation>
        </message>
        <message>
            <source>not testable</source>
            <translation>no comprobable</translation>
        </message>
        <message>
            <source>passed</source>
            <translation>aprobó</translation>
        </message>
        <message>
            <source>shipped with GeoComp</source>
            <translation>incluido con GeoComp</translation>
        </message>
        <message>
            <source>sigma %1 (mm)</source>
            <translation>sigma %1 (mm)</translation>
        </message>
        <message>
            <source>sigma (%1)</source>
            <translation>sigma (%1)</translation>
        </message>
        <message>
            <source>vᵀPv</source>
            <translation>vᵀPv</translation>
        </message>
        <message>
            <source>vᵀPv / r</source>
            <translation>vᵀPv / r</translation>
        </message>
        <message>
            <source>w</source>
            <translation>w</translation>
        </message>
        <message>
            <source>w-test</source>
            <translation>prueba w</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sí</translation>
        </message>
    </context>
    <context>
        <name>GeoCompAlgorithm</name>
        <message>
            <source>%1 is required, and none was given.</source>
            <translation>%1 es obligatorio, y no se indicó ninguno.</translation>
        </message>
        <message>
            <source>%1: %2</source>
            <translation>%1: %2</translation>
        </message>
        <message>
            <source>%1: the file '%2' does not exist.</source>
            <translation>%1: el archivo '%2' no existe.</translation>
        </message>
        <message>
            <source>%1: the folder '%2' does not exist.</source>
            <translation>%1: la carpeta '%2' no existe.</translation>
        </message>
        <message>
            <source>%1: this value cannot be used.</source>
            <translation>%1: este valor no se puede usar.</translation>
        </message>
        <message>
            <source>Analysis</source>
            <translation>Análisis</translation>
        </message>
        <message>
            <source>Cancelled. Nothing was written: every output is as it was before the run.</source>
            <translation>Cancelado. No se escribió nada: todas las salidas están como estaban antes de la ejecución.</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>Gravimetry</source>
            <translation>Gravimetría</translation>
        </message>
        <message>
            <source>Integration</source>
            <translation>Integración</translation>
        </message>
        <message>
            <source>Level</source>
            <translation>Nivel</translation>
        </message>
        <message>
            <source>Monitoring</source>
            <translation>Monitoreo</translation>
        </message>
        <message>
            <source>Outputs</source>
            <translation>Salidas</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Project and data</source>
            <translation>Proyecto y datos</translation>
        </message>
        <message>
            <source>Requirement</source>
            <translation>Requisito</translation>
        </message>
        <message>
            <source>Total Station</source>
            <translation>Estación Total</translation>
        </message>
        <message>
            <source>Visualisation and reporting</source>
            <translation>Visualización e informes</translation>
        </message>
    </context>
    <context>
        <name>GeoCompAnalysis</name>
        <message>
            <source>'%1' could not be read as a GeoComp network. %2</source>
            <translation>No se pudo leer '%1' como una red de GeoComp. %2</translation>
        </message>
        <message>
            <source>'%1' could not be read: %2</source>
            <translation>No se pudo leer '%1': %2</translation>
        </message>
        <message>
            <source>'%1' is not valid JSON: %2</source>
            <translation>'%1' no es un JSON válido: %2</translation>
        </message>
        <message>
            <source>1D — gravity values</source>
            <translation>1D — valores de gravedad</translation>
        </message>
        <message>
            <source>1D — heights only</source>
            <translation>1D — solo altitudes</translation>
        </message>
        <message>
            <source>2D — planimetric (easting, northing)</source>
            <translation>2D — planimétrico (E, N)</translation>
        </message>
        <message>
            <source>3D — easting, northing, up</source>
            <translation>3D — E, N, altitud</translation>
        </message>
        <message>
            <source>Constrained — hold the stations the network fixes</source>
            <translation>Ligada — mantiene las estaciones que la red fija</translation>
        </message>
        <message>
            <source>Fixed — hold the constrained stations exactly</source>
            <translation>Fija — mantiene exactamente las estaciones constreñidas</translation>
        </message>
        <message>
            <source>Inner constraint — free network, trace minimum</source>
            <translation>Constricción interna — red libre, traza mínima</translation>
        </message>
        <message>
            <source>Minimum constraint — over chosen stations</source>
            <translation>Constricción mínima — sobre las estaciones elegidas</translation>
        </message>
        <message>
            <source>No network document was given for parameter '%1'.</source>
            <translation>No se indicó ningún documento de red para el parámetro '%1'.</translation>
        </message>
        <message>
            <source>The network document '%1' does not exist.</source>
            <translation>El documento de red '%1' no existe.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompBaseMapOffer</name>
        <message>
            <source>Add a base map beneath the results, for context?</source>
            <translation>¿Añadir un mapa base bajo los resultados, como contexto?</translation>
        </message>
        <message>
            <source>Attribution: </source>
            <translation>Atribución: </translation>
        </message>
        <message>
            <source>Base map</source>
            <translation>Mapa base</translation>
        </message>
        <message>
            <source>Don't offer again</source>
            <translation>No volver a ofrecer</translation>
        </message>
        <message>
            <source>The base map service could not be loaded: </source>
            <translation>No se pudo cargar el servicio de mapa base: </translation>
        </message>
    </context>
    <context>
        <name>GeoCompCompareDialog</name>
        <message>
            <source>%1 stations in both epochs.</source>
            <translation>%1 estaciones en ambas épocas.</translation>
        </message>
        <message>
            <source>%1 — epoch %2, %3, datum %4</source>
            <translation>%1 — época %2, %3, datum %4</translation>
        </message>
        <message>
            <source>Choose both epochs' solutions.</source>
            <translation>Elija las soluciones de ambas épocas.</translation>
        </message>
        <message>
            <source>Compare two epochs</source>
            <translation>Comparar dos épocas</translation>
        </message>
        <message>
            <source>First epoch</source>
            <translation>Primera época</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Not comparable: %1</source>
            <translation>No comparables: %1</translation>
        </message>
        <message>
            <source>Second epoch</source>
            <translation>Segunda época</translation>
        </message>
        <message>
            <source>The epochs will be taken as independent: the displacements' uncertainty is overstated if they share reference stations or products.</source>
            <translation>Las épocas se tomarán como independientes: la incertidumbre de los desplazamientos se sobreestima si comparten estaciones de referencia o productos.</translation>
        </message>
        <message>
            <source>Transformed from %1 to %2, accuracy %3 mm, common to every station.</source>
            <translation>Transformado de %1 a %2, exactitud %3 mm, común a todas las estaciones.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompDefaults</name>
        <message>
            <source>No reference epoch was stated, by the run or its network, so the solution carries %1, assumed. It cannot enter a comparison of epochs (FR-105).</source>
            <translation>No se declaró ninguna época de referencia, ni por la ejecución ni por su red, por lo que la solución lleva %1, supuesta. No puede entrar en una comparación de épocas (FR-105).</translation>
        </message>
    </context>
    <context>
        <name>GeoCompGnss</name>
        <message>
            <source>%1 %2 has not been checked against this GeoComp release. It will be used, but if its output format has changed the solution may be refused when it is read back.</source>
            <translation>%1 %2 no se ha comprobado con esta versión de GeoComp. Se usará, pero si su formato de salida ha cambiado la solución puede rechazarse al leerla.</translation>
        </message>
        <message>
            <source>%1: %2</source>
            <translation>%1: %2</translation>
        </message>
        <message>
            <source>%1: used the %2 orbit, as Global Settings allow; recorded in provenance.</source>
            <translation>%1: se usó la órbita %2, como permite la Configuración Global; registrado en la procedencia.</translation>
        </message>
        <message>
            <source>&lt;p&gt;&lt;b&gt;Absolute (PPP) processing in RTKLIB is limited.&lt;/b&gt; Its precise point positioning is not equivalent to a dedicated PPP service: convergence is slower, the ambiguity handling is simpler, and the result is typically decimetre-level rather than centimetre-level. Prefer Relative processing where a base station is available, and treat an Absolute solution as indicative unless you have checked it against an independent determination.&lt;/p&gt;</source>
            <translation>&lt;p&gt;&lt;b&gt;El procesamiento Absoluto (PPP) en RTKLIB es limitado.&lt;/b&gt; Su posicionamiento puntual preciso no equivale a un servicio PPP dedicado: la convergencia es más lenta, el tratamiento de ambigüedades es más simple y el resultado es típicamente decimétrico en lugar de centimétrico. Prefiera el procesamiento Relativo cuando haya una estación base disponible, y trate una solución Absoluta como indicativa a menos que la haya contrastado con una determinación independiente.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>&lt;p&gt;&lt;b&gt;RTKLIB configuration file&lt;/b&gt; (Advanced) &amp;mdash; options of your own for &lt;code&gt;rnx2rtkp&lt;/code&gt;, as &lt;code&gt;key = value&lt;/code&gt; lines in RTKLIB's own format: any option it reads, including those GeoComp offers no parameter for. They come over Global Settings, and the parameters here come over them. Three things stay GeoComp's, and a file that sets one is refused: the positioning mode, which is the menu item; the base station's position (&lt;code&gt;ant2-postype&lt;/code&gt; and &lt;code&gt;ant2-pos1&lt;/code&gt; to &lt;code&gt;ant2-pos3&lt;/code&gt;), which GeoComp holds; and every &lt;code&gt;out-&lt;/code&gt; option, because the solution is read back by them. The summary records the file and the options taken from it.&lt;/p&gt;</source>
            <translation>&lt;p&gt;&lt;b&gt;Archivo de configuración de RTKLIB&lt;/b&gt; (Avanzado) &amp;mdash; opciones propias para &lt;code&gt;rnx2rtkp&lt;/code&gt;, como líneas &lt;code&gt;clave = valor&lt;/code&gt; en el formato propio de RTKLIB: cualquier opción que lea, incluidas aquellas para las que GeoComp no ofrece parámetro. Prevalecen sobre la Configuración Global, y los parámetros de aquí prevalecen sobre ellas. Tres cosas siguen siendo de GeoComp, y un archivo que defina alguna se rechaza: el modo de posicionamiento, que es el elemento de menú; la posición de la estación base (&lt;code&gt;ant2-postype&lt;/code&gt; y &lt;code&gt;ant2-pos1&lt;/code&gt; a &lt;code&gt;ant2-pos3&lt;/code&gt;), que GeoComp fija; y toda opción &lt;code&gt;out-&lt;/code&gt;, porque la solución se lee de vuelta por ellas. El resumen registra el archivo y las opciones tomadas de él.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>As the base station publishes it</source>
            <translation>Como lo publica la estación base</translation>
        </message>
        <message>
            <source>Base %1 is not in the reference-station database, so RTKLIB holds it at the approximate position in its RINEX header, and the results are in no stated frame.</source>
            <translation>La base %1 no está en la base de datos de estaciones de referencia, por lo que RTKLIB la mantiene en la posición aproximada de su cabecera RINEX, y los resultados no están en ningún marco de referencia declarado.</translation>
        </message>
        <message>
            <source>Base %1: published in %2 at %3, transformed to %4 at %5 for this run.</source>
            <translation>Base %1: publicada en %2 en la época %3, transformada a %4 en la época %5 para esta ejecución.</translation>
        </message>
        <message>
            <source>Could not read the download services file %1: %2</source>
            <translation>No se pudo leer el archivo de servicios de descarga %1: %2</translation>
        </message>
        <message>
            <source>Product %1 (%2)</source>
            <translation>Producto %1 (%2)</translation>
        </message>
        <message>
            <source>Products this run needs are not available: %1. Place them in the product directory, add a download service in Global Settings → GNSS, or -- for a recent session whose final orbit is not yet published -- allow rapid orbits there.</source>
            <translation>Productos que esta ejecución necesita no están disponibles: %1. Colóquelos en el directorio de productos, añada un servicio de descarga en Configuración Global → GNSS, o -- para una sesión reciente cuya órbita final aún no se ha publicado -- permita allí órbitas rápidas.</translation>
        </message>
        <message>
            <source>RTKLIB configuration file</source>
            <translation>Archivo de configuración de RTKLIB</translation>
        </message>
        <message>
            <source>RTKLIB options (*.conf);;All files (*)</source>
            <translation>Opciones de RTKLIB (*.conf);;Todos los archivos (*)</translation>
        </message>
        <message>
            <source>The configured antenna file does not exist: %1</source>
            <translation>El archivo de antena configurado no existe: %1</translation>
        </message>
        <message>
            <source>The configured product directory does not exist: %1</source>
            <translation>El directorio de productos configurado no existe: %1</translation>
        </message>
        <message>
            <source>The project's: the preferred CRS's frame</source>
            <translation>El del proyecto: el marco de referencia del SRC preferido</translation>
        </message>
        <message>
            <source>The session of base %1 states no start time, so its published coordinates cannot be brought to the epoch it was observed at.</source>
            <translation>La sesión de la base %1 no declara hora de inicio, por lo que sus coordenadas publicadas no pueden llevarse a la época en que se observó.</translation>
        </message>
        <message>
            <source>Timeout per run (s)</source>
            <translation>Tiempo límite por ejecución (s)</translation>
        </message>
        <message>
            <source>Unknown download service: %1. Known services: %2</source>
            <translation>Servicio de descarga desconocido: %1. Servicios conocidos: %2</translation>
        </message>
        <message>
            <source>Unknown processing profile: %1</source>
            <translation>Perfil de procesamiento desconocido: %1</translation>
        </message>
        <message>
            <source>Using %1 %2 from %3.</source>
            <translation>Usando %1 %2 de %3.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompGnssProcess</name>
        <message>
            <source>%1 epochs, %2% with resolved ambiguities</source>
            <translation>%1 épocas, %2% con ambigüedades resueltas</translation>
        </message>
        <message>
            <source>%1: %2</source>
            <translation>%1: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Processes a folder of RINEX observations with &lt;code&gt;rnx2rtkp&lt;/code&gt;. Sessions are discovered from the file headers, not their names, and only sessions that actually overlap in time are processed together.&lt;/p&gt;&lt;p&gt;Processing options come from Global Settings → GNSS unless a parameter here overrides them: elevation mask, ephemeris source, atmospheric models and the ambiguity ratio threshold.&lt;/p&gt;&lt;p&gt;Outputs the engine's &lt;code&gt;.pos&lt;/code&gt; solution and a JSON summary of the run's quality indicators: solution status per epoch, the fraction of epochs with resolved ambiguities, satellite counts and the ambiguity ratio.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Procesa una carpeta de observaciones RINEX con &lt;code&gt;rnx2rtkp&lt;/code&gt;. Las sesiones se descubren a partir de las cabeceras de los archivos, no de sus nombres, y solo se procesan juntas las sesiones que realmente se solapan en el tiempo.&lt;/p&gt;&lt;p&gt;Las opciones de procesamiento provienen de Configuración Global → GNSS, salvo que un parámetro aquí las sustituya: máscara de elevación, fuente de las efemérides, modelos atmosféricos y el umbral de la razón de ambigüedades.&lt;/p&gt;&lt;p&gt;Produce la solución &lt;code&gt;.pos&lt;/code&gt; del motor y un resumen JSON de los indicadores de calidad de la ejecución: estado de la solución por época, la fracción de épocas con ambigüedades resueltas, recuento de satélites y la razón de ambigüedades.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Absolute (PPP) processing in RTKLIB is limited and typically decimetre-level. Prefer Relative processing where a base station is available.</source>
            <translation>El procesamiento Absoluto (PPP) en RTKLIB es limitado y típicamente decimétrico. Prefiera el procesamiento Relativo cuando haya una estación base disponible.</translation>
        </message>
        <message>
            <source>Base %1 → rover %2</source>
            <translation>Base %1 → móvil %2</translation>
        </message>
        <message>
            <source>Base station</source>
            <translation>Estación base</translation>
        </message>
        <message>
            <source>Elevation mask, degrees (-1 uses Global Settings)</source>
            <translation>Máscara de elevación, grados (-1 usa la Configuración Global)</translation>
        </message>
        <message>
            <source>Folder of RINEX observations</source>
            <translation>Carpeta con observaciones RINEX</translation>
        </message>
        <message>
            <source>Frame of the results</source>
            <translation>Marco de referencia de los resultados</translation>
        </message>
        <message>
            <source>GNSS trajectory</source>
            <translation>Trayectoria GNSS</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>Keep the engine's working directory</source>
            <translation>Conservar el directorio de trabajo del motor</translation>
        </message>
        <message>
            <source>Name the %1 station explicitly; the folder holds: %2</source>
            <translation>Indique la estación %1 explícitamente; la carpeta contiene: %2</translation>
        </message>
        <message>
            <source>No %1 session for station %2; found: %3</source>
            <translation>Ninguna sesión %1 para la estación %2; encontradas: %3</translation>
        </message>
        <message>
            <source>No RINEX observation sessions were found in %1</source>
            <translation>No se encontraron sesiones de observación RINEX en %1</translation>
        </message>
        <message>
            <source>Options from %1: %2</source>
            <translation>Opciones de %1: %2</translation>
        </message>
        <message>
            <source>Quality summary</source>
            <translation>Resumen de calidad</translation>
        </message>
        <message>
            <source>RTKLIB solution (*.pos)</source>
            <translation>Solución RTKLIB (*.pos)</translation>
        </message>
        <message>
            <source>Relative processing needs two sessions that observed at the same time; the folder's sessions do not overlap.</source>
            <translation>El procesamiento relativo necesita dos sesiones observadas al mismo tiempo; las sesiones de la carpeta no se solapan.</translation>
        </message>
        <message>
            <source>Rover station</source>
            <translation>Estación móvil</translation>
        </message>
        <message>
            <source>Skipped %1: %2</source>
            <translation>Omitido %1: %2</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Solution epochs (layer)</source>
            <translation>Épocas de la solución (capa)</translation>
        </message>
        <message>
            <source>The engine's working files are in %1.</source>
            <translation>Los archivos de trabajo del motor están en %1.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompGravimetry</name>
        <message>
            <source>'%1' could not be read as a gravimeter profile library: %2 is missing or invalid.</source>
            <translation>No se pudo leer '%1' como una biblioteca de perfiles de gravímetro: %2 falta o no es válido.</translation>
        </message>
        <message>
            <source>'%1' could not be read as reduced gravity readings: %2</source>
            <translation>No se pudo leer '%1' como lecturas gravimétricas reducidas: %2</translation>
        </message>
        <message>
            <source>'%1' holds no readings.</source>
            <translation>'%1' no contiene lecturas.</translation>
        </message>
        <message>
            <source>'%1' is not a reduced gravity readings document. Run 'Pre-processing (scale, tide, drift)' on the gravimeter file first.</source>
            <translation>'%1' no es un documento de lecturas gravimétricas reducidas. Ejecute primero 'Preprocesamiento (escala, marea, deriva)' sobre el archivo del gravímetro.</translation>
        </message>
        <message>
            <source>'%1' was written by a newer GeoComp (document version %2). Update GeoComp to read it.</source>
            <translation>'%1' fue escrito por un GeoComp más reciente (versión de documento %2). Actualice GeoComp para leerlo.</translation>
        </message>
        <message>
            <source>No gravimeter profile was given, so each instrument's own scale was used with a calibration factor of one whose uncertainty is unknown and not propagated. The result is labelled approximate for it. Give a profile library with each instrument's calibration to remove the assumption.</source>
            <translation>No se proporcionó ningún perfil de gravímetro, así que se usó la escala propia de cada instrumento, con un factor de calibración igual a uno cuya incertidumbre es desconocida y no se propaga. Por ello el resultado se marca como aproximado. Proporcione una biblioteca de perfiles con la calibración de cada instrumento para eliminar esa suposición.</translation>
        </message>
        <message>
            <source>assumed: no gravimeter profile was given</source>
            <translation>supuesto: no se proporcionó ningún perfil de gravímetro</translation>
        </message>
    </context>
    <context>
        <name>GeoCompLayers</name>
        <message>
            <source>%1% confidence, exaggerated %2x</source>
            <translation>%1% de confianza, exageración de %2x</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estaciones ajustadas</translation>
        </message>
        <message>
            <source>Adjusted stations (layer)</source>
            <translation>Estaciones ajustadas (capa)</translation>
        </message>
        <message>
            <source>Constraint</source>
            <translation>Constricción</translation>
        </message>
        <message>
            <source>Coordinate corrections (%1)</source>
            <translation>Correcciones de coordenadas (%1)</translation>
        </message>
        <message>
            <source>Coordinate corrections (layer)</source>
            <translation>Correcciones de coordenadas (capa)</translation>
        </message>
        <message>
            <source>Displacement ellipses (%1)</source>
            <translation>Elipses de los desplazamientos (%1)</translation>
        </message>
        <message>
            <source>Displacements %1 to %2 (%3)</source>
            <translation>Desplazamientos de %1 a %2 (%3)</translation>
        </message>
        <message>
            <source>Ellipse exaggeration (0 = from the network's extent)</source>
            <translation>Exageración de las elipses (0 = a partir de la extensión de la red)</translation>
        </message>
        <message>
            <source>Ellipses and correction vectors are drawn exaggerated %1x.</source>
            <translation>Las elipses y los vectores de corrección se dibujan con una exageración de %1x.</translation>
        </message>
        <message>
            <source>Epoch</source>
            <translation>Época</translation>
        </message>
        <message>
            <source>Error ellipses (%1)</source>
            <translation>Elipses de error (%1)</translation>
        </message>
        <message>
            <source>Error ellipses (layer)</source>
            <translation>Elipses de error (capa)</translation>
        </message>
        <message>
            <source>External reliability</source>
            <translation>Fiabilidad externa</translation>
        </message>
        <message>
            <source>GNSS baselines</source>
            <translation>Líneas base GNSS</translation>
        </message>
        <message>
            <source>GNSS solution status</source>
            <translation>Estado de la solución GNSS</translation>
        </message>
        <message>
            <source>GNSS trajectory</source>
            <translation>Trayectoria GNSS</translation>
        </message>
        <message>
            <source>Gravity differences</source>
            <translation>Diferencias de gravedad</translation>
        </message>
        <message>
            <source>Gravity stations</source>
            <translation>Estaciones gravimétricas</translation>
        </message>
        <message>
            <source>Independence</source>
            <translation>Independencia</translation>
        </message>
        <message>
            <source>Minimal detectable bias</source>
            <translation>Sesgo mínimo detectable (MDB)</translation>
        </message>
        <message>
            <source>No relative ellipses were drawn: no observation joins two stations this solution estimates.</source>
            <translation>No se dibujó ninguna elipse relativa: ninguna observación une dos estaciones que esta solución estima.</translation>
        </message>
        <message>
            <source>No relative ellipses were drawn: they need the covariance between stations, which this solution does not carry.</source>
            <translation>No se dibujó ninguna elipse relativa: necesitan la covarianza entre estaciones, que esta solución no lleva.</translation>
        </message>
        <message>
            <source>Observation type</source>
            <translation>Tipo de observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Observations (layer)</source>
            <translation>Observaciones (capa)</translation>
        </message>
        <message>
            <source>Positional uncertainty</source>
            <translation>Incertidumbre posicional</translation>
        </message>
        <message>
            <source>Redundancy number</source>
            <translation>Número de redundancia</translation>
        </message>
        <message>
            <source>Relative ellipses (%1)</source>
            <translation>Elipses relativas (%1)</translation>
        </message>
        <message>
            <source>Relative ellipses between observed stations (layer)</source>
            <translation>Elipses relativas entre estaciones observadas (capa)</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Residuos</translation>
        </message>
        <message>
            <source>Residuals (layer)</source>
            <translation>Residuos (capa)</translation>
        </message>
        <message>
            <source>Standardised residual</source>
            <translation>Residuo estandarizado</translation>
        </message>
        <message>
            <source>The geocentric solution is drawn in %1: easting, northing and ellipsoidal height.</source>
            <translation>La solución geocéntrica se dibuja en %1: coordenada este, coordenada norte y altura elipsoidal.</translation>
        </message>
        <message>
            <source>The style file '%1' could not be applied: %2</source>
            <translation>No se pudo aplicar el archivo de estilo '%1': %2</translation>
        </message>
        <message>
            <source>The style file '%1' is missing, so the layer is unstyled.</source>
            <translation>No se encontró el archivo de estilo '%1', por lo que la capa quedó sin estilo.</translation>
        </message>
        <message>
            <source>Velocities, one year's motion (%1)</source>
            <translation>Velocidades, movimiento de un año (%1)</translation>
        </message>
        <message>
            <source>W-test decision</source>
            <translation>Decisión de la prueba w</translation>
        </message>
        <message>
            <source>exaggerated %1x</source>
            <translation>exageración de %1x</translation>
        </message>
    </context>
    <context>
        <name>GeoCompLevelling</name>
        <message>
            <source>'%1' could not be read as an instrument profile library. %2</source>
            <translation>No se pudo leer '%1' como una biblioteca de perfiles de instrumento. %2</translation>
        </message>
        <message>
            <source>'%1' could not be read as levelling lines: %2</source>
            <translation>'%1' no pudo leerse como líneas de nivelación: %2</translation>
        </message>
        <message>
            <source>'%1' does not contain a GeoComp document: its top level is not an object.</source>
            <translation>'%1' no contiene un documento de GeoComp: su nivel superior no es un objeto.</translation>
        </message>
        <message>
            <source>'%1' holds no levelling lines. Run 'Import levelling field book' first.</source>
            <translation>'%1' no contiene líneas de nivelación. Ejecute primero 'Importar libreta de nivelación'.</translation>
        </message>
        <message>
            <source>'%1' holds no reduced levelling lines. Run 'Equal sights' first.</source>
            <translation>'%1' no contiene líneas de nivelación reducidas. Ejecute primero 'Visuales iguales'.</translation>
        </message>
        <message>
            <source>'%1' is not a levelling reduction document.</source>
            <translation>'%1' no es un documento de reducción de nivelación.</translation>
        </message>
        <message>
            <source>'%1' is not valid JSON: %2</source>
            <translation>'%1' no es un JSON válido: %2</translation>
        </message>
        <message>
            <source>Blocking</source>
            <translation>Bloqueante</translation>
        </message>
        <message>
            <source>Code</source>
            <translation>Código</translation>
        </message>
        <message>
            <source>Configured for this run</source>
            <translation>Configurada para esta ejecución</translation>
        </message>
        <message>
            <source>Finding</source>
            <translation>Hallazgo</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Información</translation>
        </message>
        <message>
            <source>Involves</source>
            <translation>Implica</translation>
        </message>
        <message>
            <source>No file was given for parameter '%1'.</source>
            <translation>No se indicó ningún archivo para el parámetro '%1'.</translation>
        </message>
        <message>
            <source>Nothing to report.</source>
            <translation>Nada que informar.</translation>
        </message>
        <message>
            <source>Severity</source>
            <translation>Severidad</translation>
        </message>
        <message>
            <source>The file '%1' does not exist.</source>
            <translation>El archivo '%1' no existe.</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Advertencia</translation>
        </message>
        <message>
            <source>entered on the algorithm's parameters</source>
            <translation>introducida en los parámetros del algoritmo</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMapping</name>
        <message>
            <source>%1 (required)</source>
            <translation>%1 (obligatorio)</translation>
        </message>
        <message>
            <source>'%1' could not be read as a field mapping: %2</source>
            <translation>'%1' no pudo leerse como una asignación de campos: %2</translation>
        </message>
        <message>
            <source>'%1' could not be written: %2</source>
            <translation>'%1' no pudo escribirse: %2</translation>
        </message>
        <message>
            <source>(none)</source>
            <translation>(ninguno)</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato de los ángulos</translation>
        </message>
        <message>
            <source>Backsight station</source>
            <translation>Estación de espalda</translation>
        </message>
        <message>
            <source>Comma</source>
            <translation>Coma</translation>
        </message>
        <message>
            <source>Decimal degrees</source>
            <translation>Grados decimales</translation>
        </message>
        <message>
            <source>Decimal separator</source>
            <translation>Separador decimal</translation>
        </message>
        <message>
            <source>Degrees, minutes and seconds in one column</source>
            <translation>Grados, minutos y segundos en una columna</translation>
        </message>
        <message>
            <source>Degrees, minutes and seconds in three columns</source>
            <translation>Grados, minutos y segundos en tres columnas</translation>
        </message>
        <message>
            <source>Detect automatically</source>
            <translation>Detectar automáticamente</translation>
        </message>
        <message>
            <source>Face</source>
            <translation>Posición del anteojo</translation>
        </message>
        <message>
            <source>Fields</source>
            <translation>Campos</translation>
        </message>
        <message>
            <source>Foresight station</source>
            <translation>Estación de frente</translation>
        </message>
        <message>
            <source>Format</source>
            <translation>Formato</translation>
        </message>
        <message>
            <source>GeoComp field mapping (*.json)</source>
            <translation>Asignación de campos de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp — Field mapping</source>
            <translation>GeoComp — Asignación de campos</translation>
        </message>
        <message>
            <source>Gon</source>
            <translation>Gon</translation>
        </message>
        <message>
            <source>Horizontal degrees</source>
            <translation>Grados del ángulo horizontal</translation>
        </message>
        <message>
            <source>Horizontal direction</source>
            <translation>Dirección horizontal</translation>
        </message>
        <message>
            <source>Horizontal minutes</source>
            <translation>Minutos del ángulo horizontal</translation>
        </message>
        <message>
            <source>Horizontal seconds</source>
            <translation>Segundos del ángulo horizontal</translation>
        </message>
        <message>
            <source>Instrument</source>
            <translation>Instrumento</translation>
        </message>
        <message>
            <source>Instrument height</source>
            <translation>Altura del instrumento</translation>
        </message>
        <message>
            <source>Load mapping</source>
            <translation>Cargar asignación</translation>
        </message>
        <message>
            <source>Load mapping…</source>
            <translation>Cargar asignación…</translation>
        </message>
        <message>
            <source>Mapping not loaded</source>
            <translation>Asignación no cargada</translation>
        </message>
        <message>
            <source>Mapping not saved</source>
            <translation>Asignación no guardada</translation>
        </message>
        <message>
            <source>Nothing to fix.</source>
            <translation>Nada que corregir.</translation>
        </message>
        <message>
            <source>Occupied station</source>
            <translation>Estación ocupada</translation>
        </message>
        <message>
            <source>One value for every row, for a quantity that was recorded once.</source>
            <translation>Un solo valor para todas las filas, para una magnitud registrada una sola vez.</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Punto</translation>
        </message>
        <message>
            <source>Pressure</source>
            <translation>Presión</translation>
        </message>
        <message>
            <source>Problems</source>
            <translation>Problemas</translation>
        </message>
        <message>
            <source>Radians</source>
            <translation>Radianes</translation>
        </message>
        <message>
            <source>Reflector</source>
            <translation>Reflector</translation>
        </message>
        <message>
            <source>Relative humidity</source>
            <translation>Humedad relativa</translation>
        </message>
        <message>
            <source>Save mapping</source>
            <translation>Guardar asignación</translation>
        </message>
        <message>
            <source>Save mapping…</source>
            <translation>Guardar asignación…</translation>
        </message>
        <message>
            <source>Set number</source>
            <translation>Número de serie</translation>
        </message>
        <message>
            <source>Sighted (backsight or foresight)</source>
            <translation>Visual (espalda o frente)</translation>
        </message>
        <message>
            <source>Slope distance</source>
            <translation>Distancia inclinada</translation>
        </message>
        <message>
            <source>Source: %1</source>
            <translation>Origen: %1</translation>
        </message>
        <message>
            <source>Target</source>
            <translation>Objetivo</translation>
        </message>
        <message>
            <source>Target height</source>
            <translation>Altura de la señal</translation>
        </message>
        <message>
            <source>Temperature</source>
            <translation>Temperatura</translation>
        </message>
        <message>
            <source>Zenith angle</source>
            <translation>Ángulo cenital</translation>
        </message>
        <message>
            <source>Zenith degrees</source>
            <translation>Grados del ángulo cenital</translation>
        </message>
        <message>
            <source>Zenith minutes</source>
            <translation>Minutos del ángulo cenital</translation>
        </message>
        <message>
            <source>Zenith seconds</source>
            <translation>Segundos del ángulo cenital</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMenu</name>
        <message>
            <source>&amp;GeoComp</source>
            <translation>&amp;GeoComp</translation>
        </message>
        <message>
            <source>Absolute</source>
            <translation>Absoluto</translation>
        </message>
        <message>
            <source>Analysis</source>
            <translation>Análisis</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>Global Settings…</source>
            <translation>Configuraciones Globales…</translation>
        </message>
        <message>
            <source>Gravimetry</source>
            <translation>Gravimetría</translation>
        </message>
        <message>
            <source>Integration</source>
            <translation>Integración</translation>
        </message>
        <message>
            <source>Level</source>
            <translation>Nivel</translation>
        </message>
        <message>
            <source>No operations available yet in this version.</source>
            <translation>Aún no hay operaciones disponibles en esta versión.</translation>
        </message>
        <message>
            <source>Project</source>
            <translation>Proyecto</translation>
        </message>
        <message>
            <source>Relative</source>
            <translation>Relativo</translation>
        </message>
        <message>
            <source>Total Station</source>
            <translation>Estación Total</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMessages</name>
        <message>
            <source>%1 already holds a project, and copying into it would mix two. Copy into a new GeoPackage or a new schema.</source>
            <translation>%1 ya contiene un proyecto, y copiar en él mezclaría dos. Copie a un GeoPackage nuevo o a un esquema nuevo.</translation>
        </message>
        <message>
            <source>%1 cannot be applied to values in %2: the units do not fit the operation.</source>
            <translation>%1 no puede aplicarse a valores en %2: las unidades no sirven a la operación.</translation>
        </message>
        <message>
            <source>%1 finished without writing a solution file. Its own message: %2. Its working files are in %3.</source>
            <translation>%1 terminó sin escribir un archivo de solución. El mensaje del propio motor: %2. Los archivos de trabajo están en %3.</translation>
        </message>
        <message>
            <source>%1 holds JSON, but not a profile library: a library is an object with lists of instruments, reflectors, levels and gravimeters.</source>
            <translation>%1 contiene JSON, pero no una biblioteca de perfiles: una biblioteca es un objeto con listas de instrumentos, reflectores, niveles y gravímetros.</translation>
        </message>
        <message>
            <source>%1 is needed for %2 and was not found. Give its path in Global Settings, under Paths and engines, or put it on the system path. Everything in GeoComp that does not need it works without it.</source>
            <translation>%1 es necesario para %2 y no se encontró. Indique su ruta en Configuraciones Globales, en Rutas y motores, o póngalo en la ruta del sistema. Todo lo de GeoComp que no lo necesita funciona sin él.</translation>
        </message>
        <message>
            <source>%1 is not a GeoComp project store: it holds other tables (%2). GeoComp does not write into a store it did not create; choose a new file or schema.</source>
            <translation>%1 no es un repositorio de proyecto de GeoComp: contiene otras tablas (%2). GeoComp no escribe en un repositorio que no creó; elija un archivo o esquema nuevo.</translation>
        </message>
        <message>
            <source>%1 is not an absolute temperature: in kelvin it must be above zero. Check the temperature readings.</source>
            <translation>%1 no es una temperatura absoluta: en kelvin debe ser mayor que cero. Compruebe las lecturas de temperatura.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm over %3 km, beyond the %4 mm permitted by class %5. GeoComp will not adjust a line that failed its tolerance without an explicit acknowledgement.</source>
            <translation>%1 tiene un error de cierre de %2 mm en %3 km, más allá de los %4 mm que permite la clase %5. GeoComp no ajusta una línea que falló su tolerancia sin una confirmación explícita.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm, %3 times its own propagated standard deviation. That is consistent with accumulated random error, which is the case proportional distribution is correct for.</source>
            <translation>%1 tiene un error de cierre de %2 mm, %3 veces su propia desviación estándar propagada. Eso es compatible con error aleatorio acumulado, que es el caso para el que la distribución proporcional es correcta.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm, which has not been judged against a tolerance because no levelling class was given. The misclosure is reported; whether it is acceptable is not.</source>
            <translation>%1 tiene un error de cierre de %2 mm, que no se ha juzgado frente a una tolerancia porque no se indicó ninguna clase de nivelación. Se informa el error de cierre; si es aceptable, no.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm, which has not been judged against a tolerance because no sight distances were recorded, so its length is unknown. The misclosure is reported; whether it is acceptable is not.</source>
            <translation>%1 tiene un error de cierre de %2 mm, que no se ha juzgado frente a una tolerancia porque no se registró ninguna distancia de visual, así que su longitud es desconocida. Se informa el error de cierre; si es aceptable, no.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm, which has not been judged against a tolerance because the class states no tolerance coefficient. The misclosure is reported; whether it is acceptable is not.</source>
            <translation>%1 tiene un error de cierre de %2 mm, que no se ha juzgado frente a una tolerancia porque la clase no declara coeficiente de tolerancia. Se informa el error de cierre; si es aceptable, no.</translation>
        </message>
        <message>
            <source>%1 misclosed by %2 mm, which is %3 times its own propagated standard deviation. That is not accumulated random error, so distributing it proportionally would spread one mistake evenly along the line and make it harder to find. Adjust the network and let data snooping locate it instead.</source>
            <translation>%1 tiene un error de cierre de %2 mm, que es %3 veces su propia desviación estándar propagada. Eso no es error aleatorio acumulado, así que distribuirlo proporcionalmente repartiría una sola equivocación a lo largo de la línea y la haría más difícil de encontrar. Ajuste la red y deje que el data snooping la localice.</translation>
        </message>
        <message>
            <source>%1 needs at least 1 degree of freedom, and has %2: a network with no redundancy has no test to apply. Add observations.</source>
            <translation>%1 necesita al menos 1 grado de libertad, y tiene %2: una red sin redundancia no tiene prueba que aplicar. Añada observaciones.</translation>
        </message>
        <message>
            <source>%1 observations of type %2 between %3: %4. Repeated measurements are expected; a duplicated import is not.</source>
            <translation>%1 observaciones del tipo %2 entre %3: %4. Las mediciones repetidas son esperables; una importación duplicada no lo es.</translation>
        </message>
        <message>
            <source>%1 of the %2 observations in '%3' have no DynAdjust equivalent (%4). Adjusting the rest would answer a different question, with a variance factor that looks healthy. Adjust this network with GeoComp's own adjustment, or remove those observations.</source>
            <translation>%1 de las %2 observaciones en '%3' no tienen equivalente en DynAdjust (%4). Ajustar el resto respondería a otra pregunta, con un factor de varianza de apariencia saludable. Ajuste esta red con el ajuste propio de GeoComp, o elimine esas observaciones.</translation>
        </message>
        <message>
            <source>%1 ran on '%2' but solved no epoch; finishing without an error does not mean it solved anything. Its own message: %3. The sessions observed %5; check that they and the products cover the same time. Its working files are in %4.</source>
            <translation>%1 se ejecutó sobre '%2', pero no resolvió ninguna época; terminar sin error no significa que haya resuelto algo. Su propio mensaje: %3. Las sesiones observaron %5; compruebe que ellas y los productos cubren el mismo periodo. Sus archivos de trabajo están en %4.</translation>
        </message>
        <message>
            <source>%1 setup(s) carried several foresights and entered the network as correlated clusters. They share their backsight, so it cancels in every difference the adjustment forms between two points of one setup, which makes those differences better determined, not worse.</source>
            <translation>%1 estacionamiento(s) tuvieron varias visuales de frente y entraron en la red como agrupamientos correlacionados. Comparten la visual de espalda, que se cancela en toda diferencia que el ajuste forma entre dos puntos de un mismo estacionamiento, lo que hace esas diferencias mejor determinadas, no peor.</translation>
        </message>
        <message>
            <source>%1 side shot(s) were levelled from these lines and are not in the network: %2. A spur observed once has no redundancy, so adjusting it would change nothing; their heights follow from the adjusted line. Adjust the network from its setups to include every point.</source>
            <translation>%1 punto(s) radiado(s) se nivelaron desde estas líneas y no están en la red: %2. Un ramal observado una vez no tiene redundancia, así que ajustarlo no cambiaría nada; sus alturas se siguen de la línea ajustada. Ajuste la red a partir de los estacionamientos para incluir todos los puntos.</translation>
        </message>
        <message>
            <source>%1 station(s) are reached only through heights, so nothing determines where they are horizontally: %2. Tie them in with a GNSS vector or a total-station observation, hold them horizontally, or adjust the levelling on its own.</source>
            <translation>%1 estación(es) se alcanzan solo mediante alturas, así que nada determina dónde están horizontalmente: %2. Vincúlelas con un vector GNSS o una observación de estación total, fíjelas horizontalmente o ajuste la nivelación por separado.</translation>
        </message>
        <message>
            <source>%1 station(s) have no approximate position: %2. The linearised model needs a point to linearise about; supply them, or generate them from the observations.</source>
            <translation>%1 estación(es) no tienen posición aproximada: %2. El modelo linealizado necesita un punto alrededor del cual linealizar; indíquelas, o genérelas a partir de las observaciones.</translation>
        </message>
        <message>
            <source>%1 station(s) take part in no active observation and cannot be determined: %2.</source>
            <translation>%1 estación(es) no participan en ninguna observación activa y no pueden determinarse: %2.</translation>
        </message>
        <message>
            <source>%1 stopped with exit code %2. Its own message: %3. Its working files are in %4.</source>
            <translation>%1 se detuvo con el código de salida %2. El mensaje del propio motor: %3. Los archivos de trabajo están en %4.</translation>
        </message>
        <message>
            <source>%1 trigonometric height difference(s) joined the network, each weighted by its own propagated uncertainty.</source>
            <translation>%1 desnivel(es) trigonométrico(s) entraron en la red, cada uno ponderado por su propia incertidumbre propagada.</translation>
        </message>
        <message>
            <source>%1 trigonometric height difference(s) joined the network, each weighted by its own propagated uncertainty; they reach %2 point(s) no line did.</source>
            <translation>%1 desnivel(es) trigonométrico(s) entraron en la red, cada uno ponderado por su propia incertidumbre propagada; alcanzan %2 punto(s) que ninguna línea alcanzó.</translation>
        </message>
        <message>
            <source>%1 value(s) were given for a covariance matrix over %2 components; give one per component.</source>
            <translation>Se dieron %1 valor(es) para una matriz de varianza-covarianza de %2 componentes; dé uno por componente.</translation>
        </message>
        <message>
            <source>%1 was installed in %2 but its record could not be written. Run the installation again.</source>
            <translation>%1 se instaló en %2, pero su registro no pudo escribirse. Vuelva a ejecutar la instalación.</translation>
        </message>
        <message>
            <source>%1 was stopped at its time limit of %3 s, after running for %2 s, before it finished. Raise the timeout among the algorithm's advanced parameters. Its last message: %4. Its working files are in %5.</source>
            <translation>%1 se detuvo en su tiempo límite de %3 s, tras ejecutarse durante %2 s, antes de terminar. Aumente el tiempo límite en los parámetros avanzados del algoritmo. Su último mensaje: %4. Los archivos de trabajo están en %5.</translation>
        </message>
        <message>
            <source>%1: the ellipsoidal height %2 m was converted to the orthometric height %3 m through %4 (N = %5 m). The model's uncertainty is in the result, which is now +/- %6 mm rather than %7 mm.</source>
            <translation>%1: la altura elipsoidal %2 m se convirtió en la altura ortométrica %3 m mediante %4 (N = %5 m). La incertidumbre del modelo está en el resultado, que ahora es +/- %6 mm en lugar de %7 mm.</translation>
        </message>
        <message>
            <source>'%1' contains no solution epoch. Check that the observations, the base station's and the products cover the same time.</source>
            <translation>'%1' no contiene ninguna época de solución. Compruebe que las observaciones, las de la estación base y los productos cubran el mismo período.</translation>
        </message>
        <message>
            <source>'%1' could not be read as a DynAdjust DNA file: %2.</source>
            <translation>'%1' no se pudo leer como archivo DNA de DynAdjust: %2.</translation>
        </message>
        <message>
            <source>'%1' could not be read as a DynaML (DynAdjust XML) file: %2.</source>
            <translation>'%1' no se pudo leer como archivo DynaML (XML de DynAdjust): %2.</translation>
        </message>
        <message>
            <source>'%1' could not be read as a JSON document (%2).</source>
            <translation>'%1' no se pudo leer como documento JSON (%2).</translation>
        </message>
        <message>
            <source>'%1' could not be read as an .xlsx workbook: it is damaged, or it has no worksheet. Save it again from the spreadsheet program, or export it as CSV.</source>
            <translation>'%1' no se pudo leer como libro .xlsx: está dañado o no tiene hoja de cálculo. Guárdelo de nuevo desde el programa de hojas de cálculo, o expórtelo como CSV.</translation>
        </message>
        <message>
            <source>'%1' declares %2 azimuth observation(s), which GeoComp does not read: no example of an azimuth row exists to check its layout against, and a guessed layout reads a plausible wrong number.</source>
            <translation>'%1' declara %2 observación(es) de acimut, que GeoComp no lee: no existe ningún ejemplo de una fila de acimut con el que comprobar su disposición, y una disposición adivinada lee un número erróneo verosímil.</translation>
        </message>
        <message>
            <source>'%1' does not record its base station's position (a '% ref pos' header), so its positions cannot be turned into vectors from the base. Process the session again with the output header on.</source>
            <translation>'%1' no registra la posición de la estación base (un encabezado '% ref pos'), por lo que sus posiciones no pueden convertirse en vectores desde la base. Procese la sesión de nuevo con el encabezado de salida activado.</translation>
        </message>
        <message>
            <source>'%1' gives its RINEX version as '%2', which is not a version number such as 2.11 or 3.04.</source>
            <translation>'%1' indica su versión RINEX como '%2', que no es un número de versión como 2.11 o 3.04.</translation>
        </message>
        <message>
            <source>'%1' gives values for %2 of its observation rows and not for the others. A file is either a plan, with no values, or a set of measurements, with all of them.</source>
            <translation>'%1' da valores para %2 de sus filas de observación y no para las demás. Un archivo es o una planificación, sin valores, o un conjunto de mediciones, con todos ellos.</translation>
        </message>
        <message>
            <source>'%1' has %2 line(s) after its header, fewer than the %3 stations it declares.</source>
            <translation>'%1' tiene %2 línea(s) tras su encabezado, menos que las %3 estaciones que declara.</translation>
        </message>
        <message>
            <source>'%1' has %2 line(s); an Adjust file starts with a title line and a counts line.</source>
            <translation>'%1' tiene %2 línea(s); un archivo Adjust empieza con una línea de título y una línea de recuentos.</translation>
        </message>
        <message>
            <source>'%1' has a dynamic datum, which weights the held coordinates by a covariance matrix. GeoComp does not read it: reading it as fixed would claim a certainty the example does not.</source>
            <translation>'%1' tiene un datum dinámico, que pondera las coordenadas mantenidas por una matriz de varianza-covarianza. GeoComp no lo lee: leerlo como fijo afirmaría una certeza que el ejemplo no afirma.</translation>
        </message>
        <message>
            <source>'%1' has no column header, so its columns cannot be identified. RTKLIB writes one when its output header option is on; process the session again with it on.</source>
            <translation>'%1' no tiene encabezado de columnas, por lo que sus columnas no pueden identificarse. RTKLIB escribe uno cuando la opción de encabezado de salida está activada; procese la sesión de nuevo con ella activada.</translation>
        </message>
        <message>
            <source>'%1' holds %2 positions, and a GNSS baseline needs ECEF X, Y and Z. Process the session again with ECEF output.</source>
            <translation>'%1' contiene posiciones %2, y una línea base GNSS necesita X, Y y Z ECEF. Procese la sesión de nuevo con salida ECEF.</translation>
        </message>
        <message>
            <source>'%1' holds no %2 readings.</source>
            <translation>'%1' no contiene lecturas %2.</translation>
        </message>
        <message>
            <source>'%1' holds no job GeoComp prepared. Run Adjust network (DynAdjust) with 'Stop after writing the input' first, and give the folder it wrote.</source>
            <translation>'%1' no contiene ningún trabajo que GeoComp haya preparado. Ejecute antes Ajustar red (DynAdjust) con 'Detenerse tras escribir la entrada' e indique la carpeta que escribió.</translation>
        </message>
        <message>
            <source>'%1' holds no station coordinates. Each row gives a station, then its easting, northing and height, in metres.</source>
            <translation>'%1' no contiene coordenadas de estaciones. Cada fila da una estación, luego su E, su N y su altitud, en metros.</translation>
        </message>
        <message>
            <source>'%1' in the datum section is neither a station nor an axis letter and a station, such as xA.</source>
            <translation>'%1' en la sección de datum no es ni una estación ni una letra de eje seguida de una estación, como xA.</translation>
        </message>
        <message>
            <source>'%1' is a DynaML file of type '%2', where a %3 or a Combined File was expected.</source>
            <translation>'%1' es un archivo DynaML del tipo '%2', donde se esperaba un %3 o un Combined File.</translation>
        </message>
        <message>
            <source>'%1' is a network document, not a solution: it has stations but no adjusted stations. Choose the solution an adjustment wrote.</source>
            <translation>'%1' es un documento de red, no una solución: tiene estaciones, pero ninguna estación ajustada. Elija la solución que escribió un ajuste.</translation>
        </message>
        <message>
            <source>'%1' is compressed as %2, which GeoComp does not read. Decompress it first; GeoComp reads uncompressed and gzip-compressed RINEX.</source>
            <translation>'%1' está comprimido como %2, que GeoComp no lee. Descomprímalo primero; GeoComp lee RINEX sin comprimir y comprimido con gzip.</translation>
        </message>
        <message>
            <source>'%1' is empty.</source>
            <translation>'%1' está vacío.</translation>
        </message>
        <message>
            <source>'%1' is empty: a RINEX file starts with a header.</source>
            <translation>'%1' está vacío: un archivo RINEX empieza con un encabezado.</translation>
        </message>
        <message>
            <source>'%1' is not a DynAdjust DNA file: its first line does not begin with !#=DNA.</source>
            <translation>'%1' no es un archivo DNA de DynAdjust: su primera línea no empieza por !#=DNA.</translation>
        </message>
        <message>
            <source>'%1' is not a DynaML file: its root element is '%2', where DnaXmlFormat was expected.</source>
            <translation>'%1' no es un archivo DynaML: su elemento raíz es '%2', donde se esperaba DnaXmlFormat.</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp document: its top level is not a JSON object.</source>
            <translation>'%1' no es un documento de GeoComp: su nivel superior no es un objeto JSON.</translation>
        </message>
        <message>
            <source>'%1' is not a RINEX file: its first record is '%2', where RINEX VERSION / TYPE was expected.</source>
            <translation>'%1' no es un archivo RINEX: su primer registro es '%2', donde se esperaba RINEX VERSION / TYPE.</translation>
        </message>
        <message>
            <source>'%1' is not a bare template file name; give a name such as 'adjustment.html', with no path.</source>
            <translation>'%1' no es un nombre simple de archivo de plantilla; indique un nombre como 'adjustment.html', sin ruta.</translation>
        </message>
        <message>
            <source>'%1' is not a date in DynAdjust's dd.mm.yyyy form.</source>
            <translation>'%1' no es una fecha en la forma dd.mm.aaaa de DynAdjust.</translation>
        </message>
        <message>
            <source>'%1' is not a datum GeoComp can refer displacements to. Choose one of: %2.</source>
            <translation>'%1' no es un datum al que GeoComp pueda referir desplazamientos. Elija uno de: %2.</translation>
        </message>
        <message>
            <source>'%1' is not a datum GeoComp reads; expected %2.</source>
            <translation>'%1' no es un datum que GeoComp lea; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a datum-defect component GeoComp knows.</source>
            <translation>'%1' no es una componente de deficiencia de datum que GeoComp conozca.</translation>
        </message>
        <message>
            <source>'%1' is not a decimal separator; use '.', ',' or 'auto'.</source>
            <translation>'%1' no es un separador decimal; use '.', ',' o 'auto'.</translation>
        </message>
        <message>
            <source>'%1' is not a distance unit GeoComp writes; expected %2. Correct it in Global Settings, under Interface.</source>
            <translation>'%1' no es una unidad de distancia que GeoComp escriba; se esperaba %2. Corríjala en Configuraciones Globales, en Interfaz.</translation>
        </message>
        <message>
            <source>'%1' is not a folder. Choose the folder that holds the RINEX observation and navigation files.</source>
            <translation>'%1' no es una carpeta. Elija la carpeta que contiene los archivos RINEX de observación y de navegación.</translation>
        </message>
        <message>
            <source>'%1' is not a geoid grid format GeoComp reads. Give a GTX grid (.gtx) or an ESRI ASCII grid (.asc, .txt, .grd); QGIS or gdal_translate can convert one.</source>
            <translation>'%1' no está en un formato de malla del geoide que GeoComp lea. Indique una malla GTX (.gtx) o una malla ESRI ASCII (.asc, .txt, .grd); QGIS o gdal_translate pueden convertir una.</translation>
        </message>
        <message>
            <source>'%1' is not a kind of observation GeoComp weights; expected %2.</source>
            <translation>'%1' no es un tipo de observación que GeoComp pondere; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a kind of sight the mapping knows (%2).</source>
            <translation>'%1' no es un tipo de visual que la asignación conozca (%2).</translation>
        </message>
        <message>
            <source>'%1' is not a network document as GeoComp writes it (%2).</source>
            <translation>'%1' no es un documento de red como lo escribe GeoComp (%2).</translation>
        </message>
        <message>
            <source>'%1' is not a number, on the line: %2</source>
            <translation>'%1' no es un número, en la línea: %2</translation>
        </message>
        <message>
            <source>'%1' is not a positive line length in metres; the length weights the levelled line.</source>
            <translation>'%1' no es una longitud de línea positiva en metros; la longitud pondera la línea nivelada.</translation>
        </message>
        <message>
            <source>'%1' is not a processing profile; expected %2.</source>
            <translation>'%1' no es un perfil de procesamiento; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a real date (dd.mm.yyyy).</source>
            <translation>'%1' no es una fecha real (dd.mm.aaaa).</translation>
        </message>
        <message>
            <source>'%1' is not a reference frame GeoComp holds transformations for; it holds %2. WGS 84 is not one: its realisations differ by decimetres, and the name does not say which.</source>
            <translation>'%1' no es un marco de referencia para el que GeoComp tenga transformaciones; tiene %2. WGS 84 no es uno de ellos: sus realizaciones difieren en decímetros, y el nombre no dice cuál.</translation>
        </message>
        <message>
            <source>'%1' is not a sheet GeoComp exports; the sheets are %2.</source>
            <translation>'%1' no es una hoja que GeoComp exporte; las hojas son %2.</translation>
        </message>
        <message>
            <source>'%1' is not a solution document as GeoComp writes it (%2).</source>
            <translation>'%1' no es un documento de solución como lo escribe GeoComp (%2).</translation>
        </message>
        <message>
            <source>'%1' is not a solution format GeoComp reads: its column header is '%2'. GeoComp reads latitude/longitude/height, ECEF X/Y/Z and ENU baseline solutions.</source>
            <translation>'%1' no está en un formato de solución que GeoComp lea: su encabezado de columnas es '%2'. GeoComp lee soluciones en latitud/longitud/altura, X/Y/Z ECEF y líneas base ENU.</translation>
        </message>
        <message>
            <source>'%1' is not a solver; expected %2.</source>
            <translation>'%1' no es un método de solución; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a variance-component group of this adjustment; the groups are %2.</source>
            <translation>'%1' no es un grupo de componentes de varianza de este ajuste; los grupos son %2.</translation>
        </message>
        <message>
            <source>'%1' is not a way RTKLIB can be given the base position; expected %2.</source>
            <translation>'%1' no es una forma de dar la posición de la base a RTKLIB; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a weighting mode; use length or setups.</source>
            <translation>'%1' no es un modo de ponderación; use length o setups (longitud o estacionamientos).</translation>
        </message>
        <message>
            <source>'%1' is not an RTKLIB output format; it writes llh, xyz, enu or nmea.</source>
            <translation>'%1' no es un formato de salida de RTKLIB; escribe llh, xyz, enu o nmea.</translation>
        </message>
        <message>
            <source>'%1' is not an adjustment engine; expected %2.</source>
            <translation>'%1' no es un motor de ajuste; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not an angle format GeoComp writes; expected %2. Correct it in Global Settings, under Interface.</source>
            <translation>'%1' no es un formato de ángulo que GeoComp escriba; se esperaba %2. Corríjalo en Configuraciones Globales, en Interfaz.</translation>
        </message>
        <message>
            <source>'%1' is not an angle in DynAdjust's DDD.MMSSsss notation.</source>
            <translation>'%1' no es un ángulo en la notación DDD.MMSSsss de DynAdjust.</translation>
        </message>
        <message>
            <source>'%1' is not an angle in degrees, minutes and seconds, such as 12°34'56", on the line: %2</source>
            <translation>'%1' no es un ángulo en grados, minutos y segundos, como 12°34'56", en la línea: %2</translation>
        </message>
        <message>
            <source>'%1' is not an ellipsoid GeoComp knows; it knows %2.</source>
            <translation>'%1' no es un elipsoide que GeoComp conozca; conoce %2.</translation>
        </message>
        <message>
            <source>'%1' is not one of the configurations compared; expected %2.</source>
            <translation>'%1' no es una de las configuraciones comparadas; se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not one of the face values the mapping knows (%2).</source>
            <translation>'%1' no es uno de los valores de círculo que la asignación conoce (%2).</translation>
        </message>
        <message>
            <source>'%1' is not one of the sighted values the mapping knows (%2).</source>
            <translation>'%1' no es uno de los valores de punto visado que la asignación conoce (%2).</translation>
        </message>
        <message>
            <source>'%1' observes stations that have no approximate coordinates (%2). An angle or azimuth to such a point defines a direction, not a position; reduce it before the network is adjusted.</source>
            <translation>'%1' observa estaciones sin coordenadas aproximadas (%2). Un ángulo o acimut hacia tal punto define una dirección, no una posición; redúzcalo antes de ajustar la red.</translation>
        </message>
        <message>
            <source>'%1' reads %2, but minutes and seconds must be below 60. The columns are probably in the wrong order, or the angle is already decimal.</source>
            <translation>'%1' dice %2, pero los minutos y segundos deben quedar por debajo de 60. Probablemente las columnas están en el orden equivocado, o el ángulo ya es decimal.</translation>
        </message>
        <message>
            <source>'%1' records no epoch, and GeoComp will not assume one: a solution without an epoch cannot be compared or transformed. Run the adjustment with an explicit epoch.</source>
            <translation>'%1' no registra ninguna época, y GeoComp no supone una: una solución sin época no puede compararse ni transformarse. Ejecute el ajuste con una época explícita.</translation>
        </message>
        <message>
            <source>'%1' records no solution: the adjustment did not reach one. DynAdjust's messages in the same folder say why.</source>
            <translation>'%1' no registra ninguna solución: el ajuste no llegó a una. Los mensajes de DynAdjust en la misma carpeta dicen por qué.</translation>
        </message>
        <message>
            <source>'%1' was written by DynAdjust %2, whose output layout GeoComp does not read; it reads the layouts of %3. Run one of those versions.</source>
            <translation>'%1' fue escrito por DynAdjust %2, cuyo formato de salida GeoComp no lee; lee los formatos de %3. Use una de esas versiones.</translation>
        </message>
        <message>
            <source>'%2' has a section %1 that GeoComp does not know.</source>
            <translation>'%2' tiene una sección %1 que GeoComp no conoce.</translation>
        </message>
        <message>
            <source>'%2' has no reference epoch, which is needed to %1. GeoComp will not assume one, because an assumed epoch produces a confidently wrong displacement; give the epoch.</source>
            <translation>'%2' no tiene época de referencia, que es necesaria para %1. GeoComp no asume una, porque una época asumida produce un desplazamiento erróneo con toda confianza; indique la época.</translation>
        </message>
        <message>
            <source>'%2', given for '%1', is not a number.</source>
            <translation>'%2', dado para '%1', no es un número.</translation>
        </message>
        <message>
            <source>'%2', given for '%1', is not an angle.</source>
            <translation>'%2', dado para '%1', no es un ángulo.</translation>
        </message>
        <message>
            <source>(not set)</source>
            <translation>(no definido)</translation>
        </message>
        <message>
            <source>A %1 of %2 cannot weight an observation; the extent must not be negative.</source>
            <translation>Un(a) %1 de %2 no puede ponderar una observación; la extensión no puede ser negativa.</translation>
        </message>
        <message>
            <source>A %1 was given where a number or a value with its uncertainty was expected.</source>
            <translation>Se dio un %1 donde se esperaba un número o un valor con su incertidumbre.</translation>
        </message>
        <message>
            <source>A %1-dimensional adjustment is not supported; GeoComp adjusts in 1, 2 or 3 dimensions.</source>
            <translation>Un ajuste %1-dimensional no está soportado; GeoComp ajusta en 1, 2 o 3 dimensiones.</translation>
        </message>
        <message>
            <source>A GNSS loop needs at least three stations, and %1 were given: a two-station loop retraces one baseline and closes by construction.</source>
            <translation>Un circuito GNSS necesita al menos tres estaciones, y se dieron %1: un circuito de dos estaciones recorre de vuelta una línea base y cierra por construcción.</translation>
        </message>
        <message>
            <source>A GNSS session has no id; baselines refer to a session by it. Give every session one.</source>
            <translation>Una sesión GNSS no tiene id; las líneas base se refieren a una sesión por él. Dé uno a cada sesión.</translation>
        </message>
        <message>
            <source>A Jacobian of shape %1 cannot propagate a covariance matrix of size %2: it needs one column per component. This is an internal error; please report it.</source>
            <translation>Una matriz jacobiana de forma %1 no puede propagar una matriz de varianza-covarianza de tamaño %2: necesita una columna por componente. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>A Jacobian of shape %1 was given to propagate an uncertainty; it must be a matrix. This is an internal error; please report it.</source>
            <translation>Se dio una matriz jacobiana de forma %1 para propagar una incertidumbre; debe ser una matriz. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>A base map service in the catalogue has no id; the default service is named by it. Give every service one.</source>
            <translation>Un servicio de mapa base del catálogo no tiene id; el servicio predeterminado se nombra por él. Dé uno a cada servicio.</translation>
        </message>
        <message>
            <source>A baseline states antenna heights (%2). Reducing it to the marks needs each mark's vertical, which this file does not give: %1</source>
            <translation>Una línea base indica alturas de antena (%2). Reducirla a las marcas requiere la vertical de cada marca, que este archivo no da: %1</translation>
        </message>
        <message>
            <source>A column of the mapping names no field. Choose the field it fills, or remove it.</source>
            <translation>Una columna de la asignación no nombra ningún campo. Elija el campo que rellena, o elimínela.</translation>
        </message>
        <message>
            <source>A comparison needs at least two processing configurations, and %1 were given: a configuration compared with itself says nothing.</source>
            <translation>Una comparación necesita al menos dos configuraciones de procesamiento, y se dieron %1: una configuración comparada consigo misma no dice nada.</translation>
        </message>
        <message>
            <source>A connected traverse needs the known point it arrives at, and none was given.</source>
            <translation>Una poligonal encuadrada necesita el punto conocido al que llega, y no se dio ninguno.</translation>
        </message>
        <message>
            <source>A constraint gives a gravity value but does not hold gravity, so the value would be silently ignored. Add gravity to its components, or remove the value.</source>
            <translation>Una restricción indica un valor de gravedad, pero no mantiene la gravedad, por lo que el valor se ignoraría en silencio. Añada la gravedad a sus componentes, o elimine el valor.</translation>
        </message>
        <message>
            <source>A constraint names components its position does not have (%1); expected among %2.</source>
            <translation>Una restricción nombra componentes que su posición no tiene (%1); se esperaba entre %2.</translation>
        </message>
        <message>
            <source>A coordinate row is too short: %1</source>
            <translation>Una fila de coordenadas es demasiado corta: %1</translation>
        </message>
        <message>
            <source>A correlation coefficient must lie between -1 and 1.</source>
            <translation>Un coeficiente de correlación debe estar entre -1 y 1.</translation>
        </message>
        <message>
            <source>A counter reading is in %1; counter units are dimensionless.</source>
            <translation>Una lectura de contador está en %1; las unidades de contador son adimensionales.</translation>
        </message>
        <message>
            <source>A counter reading of %1 is outside the gravimeter's calibration table, which runs from %2 to %3. The table cannot be extrapolated, because the next interval's factor is not in it.</source>
            <translation>Una lectura de contador de %1 está fuera de la tabla de calibración del gravímetro, que va de %2 a %3. La tabla no puede extrapolarse, porque el factor del intervalo siguiente no está en ella.</translation>
        </message>
        <message>
            <source>A covariance matrix has no component '%1'.</source>
            <translation>Una matriz de varianza-covarianza no tiene la componente '%1'.</translation>
        </message>
        <message>
            <source>A covariance matrix has the shape %1; a covariance matrix is square. Check the matrix the observations or the solution carry.</source>
            <translation>Una matriz de varianza-covarianza tiene la forma %1; una matriz de varianza-covarianza es cuadrada. Compruebe la matriz que llevan las observaciones o la solución.</translation>
        </message>
        <message>
            <source>A covariance matrix is not positive semi-definite: its smallest eigenvalue is %1. No set of uncertainties produces such a matrix, so it was mistyped, truncated, or assembled from parts that do not belong together.</source>
            <translation>Una matriz de varianza-covarianza no es semidefinida positiva: su menor valor propio es %1. Ningún conjunto de incertidumbres produce tal matriz, así que se tecleó mal, se truncó, o se montó a partir de partes que no van juntas.</translation>
        </message>
        <message>
            <source>A covariance matrix is not symmetric: the entries for %2 differ by %1 from their mirror images. A covariance matrix is symmetric, so the matrix was written or read wrongly.</source>
            <translation>Una matriz de varianza-covarianza no es simétrica: los elementos de %2 difieren en %1 de sus simétricos. Una matriz de varianza-covarianza es simétrica, así que la matriz se escribió o se leyó mal.</translation>
        </message>
        <message>
            <source>A covariance matrix names the same component twice, so its rows cannot be told apart. Give each component its own name.</source>
            <translation>Una matriz de varianza-covarianza nombra la misma componente dos veces, así que sus filas no pueden distinguirse. Dé a cada componente su propio nombre.</translation>
        </message>
        <message>
            <source>A covariance matrix of size %2 gives %1 unit(s); it must give one per row.</source>
            <translation>Una matriz de varianza-covarianza de tamaño %2 da %1 unidad(es); debe dar una por fila.</translation>
        </message>
        <message>
            <source>A covariance matrix of size %2 names %1 component(s); it must name one per row.</source>
            <translation>Una matriz de varianza-covarianza de tamaño %2 nombra %1 componente(s); debe nombrar una por fila.</translation>
        </message>
        <message>
            <source>A difference network is one of heights or of gravity values; %1 is neither.</source>
            <translation>Una red de diferencias es de alturas o de valores de gravedad; %1 no es ninguna de las dos.</translation>
        </message>
        <message>
            <source>A direction set in the prepared measurement file '%1' now holds %2 directions after its reference where GeoComp wrote %3 (the set whose reference is observation %4). Directions cannot be added or removed; to leave one out, set its Ignore to *.</source>
            <translation>Un conjunto de direcciones en el archivo de mediciones preparado '%1' contiene ahora %2 direcciones tras la de referencia, donde GeoComp escribió %3 (el conjunto cuya referencia es la observación %4). No se pueden añadir ni eliminar direcciones; para dejar una fuera, marque su Ignore con *.</translation>
        </message>
        <message>
            <source>A direction was asked of two coincident points, where it is undefined. Check for two stations with the same coordinates.</source>
            <translation>Se pidió una dirección entre dos puntos coincidentes, donde no está definida. Compruebe si hay dos estaciones con las mismas coordenadas.</translation>
        </message>
        <message>
            <source>A download service could not be read: %1. Each needs an 'id', a 'name' and 'templates' keyed like 'orbit/final'.</source>
            <translation>No se pudo leer un servicio de descarga: %1. Cada uno necesita 'id', 'name' y 'templates' con claves como 'orbit/final'.</translation>
        </message>
        <message>
            <source>A free station carries a position, components or a gravity value to be held at. Remove them, or constrain the station as fixed or weighted.</source>
            <translation>Una estación libre lleva una posición, componentes o un valor de gravedad a mantener. Elimínelos, o aplique a la estación una restricción fija o ponderada.</translation>
        </message>
        <message>
            <source>A geoid model has no id; a solution records which model produced its heights by it. Give the model one.</source>
            <translation>Un modelo geoidal no tiene id; una solución registra por él qué modelo produjo sus alturas. Dé uno al modelo.</translation>
        </message>
        <message>
            <source>A geoid model was given, but this combination is in a local system (%1) where every height is what its input says it is. Leave the geoid out.</source>
            <translation>Se indicó un modelo geoidal, pero esta combinación está en un sistema local (%1), donde cada altura es lo que dice su entrada. No indique el geoide.</translation>
        </message>
        <message>
            <source>A geometry in the project store could not be read (it begins %1). The store may be damaged; the numeric coordinates beside it are the record.</source>
            <translation>No se pudo leer una geometría del repositorio del proyecto (empieza por %1). El repositorio puede estar dañado; las coordenadas numéricas a su lado son el registro.</translation>
        </message>
        <message>
            <source>A gravimeter profile has no id; readings refer to the instrument by it. Give every profile one.</source>
            <translation>Un perfil de gravímetro no tiene id; las lecturas se refieren al instrumento por él. Dé uno a cada perfil.</translation>
        </message>
        <message>
            <source>A gravity constraint is in %1, where %2 was expected.</source>
            <translation>Una restricción de gravedad está en %1, donde se esperaba %2.</translation>
        </message>
        <message>
            <source>A height difference for the orthometric correction is in %1; give it in metres.</source>
            <translation>Un desnivel para la corrección ortométrica está en %1; indíquelo en metros.</translation>
        </message>
        <message>
            <source>A height difference is in %1; give it in metres.</source>
            <translation>Un desnivel está en %1; indíquelo en metros.</translation>
        </message>
        <message>
            <source>A height of %1 m is below the centre of the Earth, so the reduction is impossible. Check the station's height.</source>
            <translation>Una altura de %1 m queda por debajo del centro de la Tierra, por lo que la reducción es imposible. Compruebe la altura de la estación.</translation>
        </message>
        <message>
            <source>A known height difference is in %1; give it in metres.</source>
            <translation>Un desnivel conocido está en %1; indíquelo en metros.</translation>
        </message>
        <message>
            <source>A known value is given for '%1', which is not a station of the network. Check its name.</source>
            <translation>Se dio un valor conocido para '%1', que no es una estación de la red. Compruebe su nombre.</translation>
        </message>
        <message>
            <source>A level profile has no id; observations refer to a profile by it. Give every profile one.</source>
            <translation>Un perfil de nivel no tiene id; las observaciones se refieren a un perfil por él. Dé uno a cada perfil.</translation>
        </message>
        <message>
            <source>A levelling class has no id; lines and reports refer to a class by it. Give every class one.</source>
            <translation>Una clase de nivelación no tiene id; líneas e informes se refieren a una clase por él. Dé uno a cada clase.</translation>
        </message>
        <message>
            <source>A levelling line has no id. Closures and findings refer to a line by its id; give every line one.</source>
            <translation>Una línea de nivelación no tiene id. Los cierres y los hallazgos se refieren a una línea por su id; dé uno a cada línea.</translation>
        </message>
        <message>
            <source>A levelling line length cannot be negative; %1 km was given.</source>
            <translation>La longitud de una línea de nivelación no puede ser negativa; se dio %1 km.</translation>
        </message>
        <message>
            <source>A pair of readings has the faces %1, where face left and then face right were expected.</source>
            <translation>Un par de lecturas tiene las posiciones %1, donde se esperaba círculo directo y después círculo inverso.</translation>
        </message>
        <message>
            <source>A planned observation names no stations; it connects two.</source>
            <translation>Una observación planificada no nombra estaciones; une dos.</translation>
        </message>
        <message>
            <source>A planned station has no name; give it one.</source>
            <translation>Una estación planificada no tiene nombre; póngale uno.</translation>
        </message>
        <message>
            <source>A position has %1 component(s), where three were expected.</source>
            <translation>Una posición tiene %1 componente(s), donde se esperaban tres.</translation>
        </message>
        <message>
            <source>A position has no component '%1'; expected %2.</source>
            <translation>Una posición no tiene la componente '%1'; se esperaba %2.</translation>
        </message>
        <message>
            <source>A position has no coordinate reference system, and GeoComp does not infer one. Give it, such as EPSG:4674.</source>
            <translation>Una posición no tiene sistema de referencia de coordenadas, y GeoComp no infiere uno. Indíquelo, por ejemplo EPSG:4674.</translation>
        </message>
        <message>
            <source>A position must move from epoch %1 and no velocity was given for it. Supply one in the velocities file.</source>
            <translation>Una posición debe llevarse desde la época %1 y no se dio velocidad para ella. Indique una en el archivo de velocidades.</translation>
        </message>
        <message>
            <source>A probability for %1 must lie between 0 and 1; %2 was given.</source>
            <translation>Una probabilidad para %1 debe estar entre 0 y 1; se dio %2.</translation>
        </message>
        <message>
            <source>A profile with the id '%1' is already in the library. Choose another id.</source>
            <translation>Un perfil con el id '%1' ya está en la biblioteca. Elija otro id.</translation>
        </message>
        <message>
            <source>A project store at schema %1 cannot be brought forward by this version of GeoComp: a migration step is missing. Report this; do not edit the store by hand.</source>
            <translation>Esta versión de GeoComp no puede actualizar un repositorio de proyecto en el esquema %1: falta un paso de migración. Informe del problema; no edite el repositorio a mano.</translation>
        </message>
        <message>
            <source>A propagation gives %1 unit(s) for %2 named value(s). This is an internal error; please report it.</source>
            <translation>Una propagación da %1 unidad(es) para %2 valor(es) nombrado(s). Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>A propagation produces %1 value(s) but names %2. This is an internal error; please report it.</source>
            <translation>Una propagación produce %1 valor(es), pero nombra %2. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>A reading names no target. Every reading needs the station or point it sighted.</source>
            <translation>Una lectura no nombra objetivo. Toda lectura necesita la estación o el punto visado.</translation>
        </message>
        <message>
            <source>A reading of the gravimeter '%1' is in %2, where %3 was expected.</source>
            <translation>Una lectura del gravímetro '%1' está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>A reciprocal pair at setup '%1' reads the same station, '%2', on both banks. A reciprocal crossing needs one station on each bank.</source>
            <translation>Un par recíproco en el estacionamiento '%1' lee la misma estación, '%2', en ambas orillas. Una travesía recíproca necesita una estación en cada orilla.</translation>
        </message>
        <message>
            <source>A record of '%1' has %2 columns, where at least %3 were expected for the %4 format. The file is truncated or damaged.</source>
            <translation>Un registro de '%1' tiene %2 columnas, donde se esperaban al menos %3 para el formato %4. El archivo está truncado o dañado.</translation>
        </message>
        <message>
            <source>A record of '%1' has '%2' where a number belongs.</source>
            <translation>Un registro de '%1' tiene '%2' donde debería haber un número.</translation>
        </message>
        <message>
            <source>A record of '%1' has a time GeoComp cannot read: '%2'. RTKLIB writes either a GPS week and second, or a date and time.</source>
            <translation>Un registro de '%1' tiene una hora que GeoComp no puede leer: '%2'. RTKLIB escribe una semana y un segundo GPS, o una fecha y una hora.</translation>
        </message>
        <message>
            <source>A record of '%1' has the solution status '%2'; RTKLIB writes 1 to 6 (fix, float, SBAS, DGPS, single, PPP).</source>
            <translation>Un registro de '%1' tiene el estado de solución '%2'; RTKLIB escribe de 1 a 6 (fija, flotante, SBAS, DGPS, simple, PPP).</translation>
        </message>
        <message>
            <source>A relative ellipse needs the same number of components for both stations, and was given %1 and %2.</source>
            <translation>Una elipse relativa necesita el mismo número de componentes para ambas estaciones, y recibió %1 y %2.</translation>
        </message>
        <message>
            <source>A relative uncertainty was asked of a value of zero, where it is undefined.</source>
            <translation>Se pidió la incertidumbre relativa de un valor cero, donde no está definida.</translation>
        </message>
        <message>
            <source>A resection needs at least three known points, and %1 were sighted: fewer cannot fix both a position and an orientation.</source>
            <translation>Una intersección inversa necesita al menos tres puntos conocidos, y se visaron %1: menos no fijan a la vez una posición y una orientación.</translation>
        </message>
        <message>
            <source>A row of DynAdjust's uncertainty file (.apu) does not name a station: '%1'. The file is damaged or in a layout GeoComp does not read.</source>
            <translation>Una fila del archivo de incertidumbres de DynAdjust (.apu) no nombra una estación: '%1'. El archivo está dañado o en un formato que GeoComp no lee.</translation>
        </message>
        <message>
            <source>A row of the %1 section gives one setup height without the other (%3); give instrument and target heights together, or neither: %2</source>
            <translation>Una fila de la sección %1 da una altura de estacionamiento sin la otra (%3); dé las alturas del instrumento y de la señal juntas, o ninguna: %2</translation>
        </message>
        <message>
            <source>A row of the %1 section has %3 value(s), where %2 are needed: %4</source>
            <translation>Una fila de la sección %1 tiene %3 valor(es), donde se necesitan %2: %4</translation>
        </message>
        <message>
            <source>A series needs two epochs at least; %1 was given.</source>
            <translation>Una serie necesita al menos dos épocas; se dio %1.</translation>
        </message>
        <message>
            <source>A setup has no id. Readings and findings refer to a setup by its id; give every setup one.</source>
            <translation>Un estacionamiento no tiene id. Las lecturas y los hallazgos se refieren a un estacionamiento por su id; dé uno a cada estacionamiento.</translation>
        </message>
        <message>
            <source>A setup names no station. Every setup needs the station the instrument occupied.</source>
            <translation>Un estacionamiento no nombra estación. Todo estacionamiento necesita la estación ocupada por el instrumento.</translation>
        </message>
        <message>
            <source>A staff reading names no station. Every reading needs the point the staff stood on.</source>
            <translation>Una lectura de mira no nombra estación. Toda lectura necesita el punto sobre el que estaba la mira.</translation>
        </message>
        <message>
            <source>A station constrained as %1 does not say which components the constraint holds. Name them, such as height, or make the station free.</source>
            <translation>Una estación con restricción %1 no dice qué componentes mantiene la restricción. Nómbrelas, como la altura, o deje la estación libre.</translation>
        </message>
        <message>
            <source>A station constrained as %1 has no coordinates to be held at. Give them, or make the station free.</source>
            <translation>Una estación con restricción %1 no tiene coordenadas a mantener. Indíquelas, o deje la estación libre.</translation>
        </message>
        <message>
            <source>A station has no id; observations and solutions refer to a station by it. Give every station one.</source>
            <translation>Una estación no tiene id; las observaciones y las soluciones se refieren a una estación por él. Dé uno a cada estación.</translation>
        </message>
        <message>
            <source>A station in the DynaML file has no coordinates (no StationCoord element); every station needs them.</source>
            <translation>Una estación del archivo DynaML no tiene coordenadas (ningún elemento StationCoord); toda estación las necesita.</translation>
        </message>
        <message>
            <source>A station in the reference station database has no id; every station needs one.</source>
            <translation>Una estación de la base de datos de estaciones de referencia no tiene id; toda estación necesita uno.</translation>
        </message>
        <message>
            <source>A station name fills its whole %1-character column in DynAdjust's output, so it cannot be told apart from the next field ('%2'). Shorten the station names, or read the output together with the network it came from.</source>
            <translation>Un nombre de estación ocupa toda su columna de %1 caracteres en la salida de DynAdjust, por lo que no puede distinguirse del campo siguiente ('%2'). Acorte los nombres de las estaciones, o lea la salida junto con la red de la que procede.</translation>
        </message>
        <message>
            <source>A station row of '%1' is too short; it gives a name and two coordinates: %2</source>
            <translation>Una fila de estación de '%1' es demasiado corta; da un nombre y dos coordenadas: %2</translation>
        </message>
        <message>
            <source>A station's gravity is constrained as %1, but no known gravity is given. Give it in m/s², or remove gravity from the constrained components.</source>
            <translation>La gravedad de una estación tiene restricción %1, pero no se indica ninguna gravedad conocida. Indíquela en m/s², o elimine la gravedad de las componentes restringidas.</translation>
        </message>
        <message>
            <source>A time was given without its time zone. GeoComp stores times in UTC and will not guess the zone; give the time with its offset, such as +00:00.</source>
            <translation>Se indicó una hora sin su zona horaria. GeoComp almacena las horas en UTC y no adivina la zona; indique la hora con su desfase, por ejemplo +00:00.</translation>
        </message>
        <message>
            <source>A trajectory point's covariance is over %1, where local east, north and up components were expected.</source>
            <translation>La covarianza de un punto de la trayectoria es sobre %1, donde se esperaban componentes locales este, norte y arriba.</translation>
        </message>
        <message>
            <source>A value (%1) was divided by zero. Check the input for a zero where a divisor is expected, such as a zero distance.</source>
            <translation>Un valor (%1) se dividió por cero. Compruebe si la entrada tiene un cero donde se espera un divisor, como una distancia nula.</translation>
        </message>
        <message>
            <source>A value for station '%1' was wider than the column DynAdjust reserved for it (%2), so the fields after it cannot be read: '%3'. A latitude and longitude precision above 6 decimals does this; run DynAdjust with the default precision.</source>
            <translation>Un valor de la estación '%1' era más ancho que la columna que DynAdjust le reservó (%2), por lo que los campos siguientes no pueden leerse: '%3'. Una precisión de latitud y longitud de más de 6 decimales lo causa; ejecute DynAdjust con la precisión predeterminada.</translation>
        </message>
        <message>
            <source>A value in %1 cannot be raised to the power %2: the result would need a compound unit, which GeoComp does not track.</source>
            <translation>Un valor en %1 no puede elevarse a la potencia %2: el resultado necesitaría una unidad compuesta, que GeoComp no sigue.</translation>
        </message>
        <message>
            <source>A value is marked rigorous but names approximations (%1). A value that used an approximation is approximate; this is an internal error, please report it.</source>
            <translation>Un valor está marcado como riguroso, pero nombra aproximaciones (%1). Un valor que usó una aproximación es aproximado; este es un error interno, por favor, infórmelo.</translation>
        </message>
        <message>
            <source>A weighted constraint has no covariance. Without an uncertainty it is a fixed constraint under another name: give its covariance, or make it fixed.</source>
            <translation>Una restricción ponderada no tiene matriz de varianza-covarianza. Sin incertidumbre es una restricción fija con otro nombre: indique su matriz de varianza-covarianza, o hágala fija.</translation>
        </message>
        <message>
            <source>A weighted gravity constraint has no variance. Without an uncertainty it is a fixed constraint under another name: give its variance, or make it fixed.</source>
            <translation>Una restricción de gravedad ponderada no tiene varianza. Sin incertidumbre es una restricción fija con otro nombre: indique su varianza, o hágala fija.</translation>
        </message>
        <message>
            <source>An angle in '%1' has minutes or seconds of 60 or more (%3): %2</source>
            <translation>Un ángulo en '%1' tiene minutos o segundos de 60 o más (%3): %2</translation>
        </message>
        <message>
            <source>An angle in DynAdjust's corrections file (.cor) could not be read: '%1', in the line '%2'.</source>
            <translation>Un ángulo del archivo de correcciones de DynAdjust (.cor) no se pudo leer: '%1', en la línea '%2'.</translation>
        </message>
        <message>
            <source>An angle in DynAdjust's output is empty where a value in DDD.MMSSsss notation was expected.</source>
            <translation>Un ángulo en la salida de DynAdjust está vacío donde se esperaba un valor en la notación DDD.MMSSsss.</translation>
        </message>
        <message>
            <source>An angle in the network is %1, which is not a number DynAdjust can be given. Check the observation it belongs to.</source>
            <translation>Un ángulo de la red vale %1, que no es un número que pueda darse a DynAdjust. Compruebe la observación a la que pertenece.</translation>
        </message>
        <message>
            <source>An ellipse needs at least 8 vertices to be drawn as an ellipse; %1 was given.</source>
            <translation>Una elipse necesita al menos 8 vértices para dibujarse como elipse; se dio %1.</translation>
        </message>
        <message>
            <source>An error ellipse needs a 2 by 2 or 3 by 3 covariance block, and was given one of shape %1.</source>
            <translation>Una elipse de error necesita un bloque de covarianza de 2 por 2 o 3 por 3, y recibió uno de forma %1.</translation>
        </message>
        <message>
            <source>An intersection needs at least two stations sighting the target, and %1 did.</source>
            <translation>Una intersección directa necesita al menos dos estaciones que visen el objetivo, y %1 lo visó.</translation>
        </message>
        <message>
            <source>An observation in %1 cannot be weighted by a model for %2.</source>
            <translation>Una observación en %1 no puede ponderarse con un modelo para %2.</translation>
        </message>
        <message>
            <source>An observation row of '%1' has %3 value(s), which is neither a distance (2 or 4) nor an angle (3 or 7): %2</source>
            <translation>Una fila de observación de '%1' tiene %3 valor(es), lo que no es ni una distancia (2 o 4) ni un ángulo (3 o 7): %2</translation>
        </message>
        <message>
            <source>An observation row of '%1' names stations that are not in the coordinate block (%3): %2</source>
            <translation>Una fila de observación de '%1' nombra estaciones que no están en el bloque de coordenadas (%3): %2</translation>
        </message>
        <message>
            <source>An observation with a %1 of %2 gets no uncertainty and so an infinite weight, which would dominate the network. Check its extent.</source>
            <translation>Una observación con %1 de %2 queda sin incertidumbre y, por tanto, con peso infinito, lo que dominaría la red. Compruebe su extensión.</translation>
        </message>
        <message>
            <source>An observation's provenance names no reader. It must say what made the observation: a file format or a reduction.</source>
            <translation>La procedencia de una observación no indica ningún lector. Debe decir qué produjo la observación: un formato de archivo o una reducción.</translation>
        </message>
        <message>
            <source>Another planned station is already named '%1'; give this one a different name.</source>
            <translation>Otra estación planificada ya se llama '%1'; dé a esta un nombre distinto.</translation>
        </message>
        <message>
            <source>Base coordinates were given with the base position type '%1'. RTKLIB uses given coordinates only with llh or xyz, and would ignore them otherwise.</source>
            <translation>Se dieron coordenadas de la base con el tipo de posición de la base '%1'. RTKLIB usa coordenadas dadas solo con llh o xyz, y las ignoraría en los demás casos.</translation>
        </message>
        <message>
            <source>Correlated cluster '%1' supplies %2 observation rows but a %3 covariance matrix. The two must agree, in the same order.</source>
            <translation>El agrupamiento correlacionado '%1' aporta %2 filas de observación pero una matriz de varianza-covarianza %3. Ambos deben coincidir, en el mismo orden.</translation>
        </message>
        <message>
            <source>Could not connect to the PostgreSQL server: %1. Check the connection in the QGIS browser; its login is the one GeoComp uses.</source>
            <translation>No se pudo conectar al servidor PostgreSQL: %1. Compruebe la conexión en el navegador de QGIS; su inicio de sesión es el que usa GeoComp.</translation>
        </message>
        <message>
            <source>Could not download %1: %2. The download was retried; check the network and the proxy configured in QGIS, then run again.</source>
            <translation>No se pudo descargar %1: %2. La descarga se reintentó; compruebe la red y el proxy configurado en QGIS, y ejecute de nuevo.</translation>
        </message>
        <message>
            <source>DynAdjust needs an explicit reference frame and epoch, and this run is missing one or both. GeoComp will not guess either: a guessed frame is a datum shift hidden in the residuals. Set the reference frame and epoch in the dialog, or record them on the network.</source>
            <translation>DynAdjust necesita un marco de referencia y una época explícitos, y a esta ejecución le falta uno de ellos o ambos. GeoComp no adivina ninguno: un marco adivinado es un desplazamiento de datum escondido en los residuos. Defina el marco de referencia y la época en el diálogo, o regístrelos en la red.</translation>
        </message>
        <message>
            <source>DynAdjust's %1 stopped with exit code %2. The command was %5, run in %4, where its working files and the input GeoComp wrote are kept. DynAdjust's own message: %3</source>
            <translation>El %1 de DynAdjust se detuvo con el código de salida %2. El comando fue %5, ejecutado en %4, donde se conservan los archivos de trabajo y la entrada que escribió GeoComp. El mensaje del propio DynAdjust: %3</translation>
        </message>
        <message>
            <source>DynAdjust's %1 was stopped at its time limit of %3 s, after running for %2 s, before it finished. Raise the timeout per stage among the algorithm's advanced parameters. Its working files are kept in %4.</source>
            <translation>El %1 de DynAdjust se detuvo en su tiempo límite de %3 s, tras ejecutarse durante %2 s, antes de terminar. Aumente el tiempo límite por etapa en los parámetros avanzados del algoritmo. Los archivos de trabajo se conservan en %4.</translation>
        </message>
        <message>
            <source>DynAdjust's adjusted-measurement table has %1 rows where the network has %2 measurements, so the rows cannot be matched to the observations. The output and the network are not from the same run.</source>
            <translation>La tabla de mediciones ajustadas de DynAdjust tiene %1 filas donde la red tiene %2 mediciones, por lo que las filas no pueden asociarse a las observaciones. La salida y la red no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>DynAdjust's coordinate table has no position GeoComp can read: it printed %1, and none of X/Y/Z, latitude/longitude or easting/northing. Write the adjustment with one of those coordinate outputs.</source>
            <translation>La tabla de coordenadas de DynAdjust no tiene ninguna posición que GeoComp pueda leer: imprimió %1, y ninguno de X/Y/Z, latitud/longitud o este/norte. Escriba el ajuste con una de esas salidas de coordenadas.</translation>
        </message>
        <message>
            <source>DynAdjust's output has '%1' where the %2 should be a number, in the line '%3'.</source>
            <translation>La salida de DynAdjust tiene '%1' donde %2 debería ser un número, en la línea '%3'.</translation>
        </message>
        <message>
            <source>DynAdjust's output has a component '%1' for measurement %2 that GeoComp does not know to be angular or linear, in the line '%3'.</source>
            <translation>La salida de DynAdjust tiene un componente '%1' en la medición %2 que GeoComp no sabe si es angular o lineal, en la línea '%3'.</translation>
        </message>
        <message>
            <source>DynAdjust's output names a station that is not in the network GeoComp wrote ('%1'), so the output and the network are not from the same run.</source>
            <translation>La salida de DynAdjust nombra una estación que no está en la red escrita por GeoComp ('%1'), por lo que la salida y la red no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>DynAdjust's uncertainty file (.apu) gives a covariance between '%1' and '%2', and the adjustment does not have both. The two files are not from the same run.</source>
            <translation>El archivo de incertidumbres de DynAdjust (.apu) da una covarianza entre '%1' y '%2', y el ajuste no tiene ambas. Los dos archivos no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>DynAdjust's uncertainty file (.apu) has a covariance row before any station row: '%1'. The file is damaged or in a layout GeoComp does not read.</source>
            <translation>El archivo de incertidumbres de DynAdjust (.apu) tiene una fila de covarianza antes de cualquier fila de estación: '%1'. El archivo está dañado o en un formato que GeoComp no lee.</translation>
        </message>
        <message>
            <source>DynAdjust's uncertainty file (.apu) names stations its adjustment file (.adj) does not: %1. The two files are not from the same run.</source>
            <translation>El archivo de incertidumbres de DynAdjust (.apu) nombra estaciones que su archivo de ajuste (.adj) no nombra: %1. Los dos archivos no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>Each field can be mapped once, and %1 is mapped more than once. Map each to a single column.</source>
            <translation>Cada campo puede asignarse una vez, y %1 está asignado más de una vez. Asigne cada uno a una sola columna.</translation>
        </message>
        <message>
            <source>Every station in this network is held fixed, so there is nothing to estimate. Free at least one station, or one of its components.</source>
            <translation>Toda estación de esta red está fija, así que no hay nada que estimar. Libere al menos una estación, o una de sus componentes.</translation>
        </message>
        <message>
            <source>GeoComp cannot tell whether the angles in this DynAdjust output are in DDD.MMSSsss notation or decimal degrees: the file does not record the command that wrote it. Use the output of a run that records it, as GeoComp's own runs do.</source>
            <translation>GeoComp no puede saber si los ángulos de esta salida de DynAdjust están en la notación DDD.MMSSsss o en grados decimales: el archivo no registra el comando que lo escribió. Use la salida de una ejecución que lo registre, como las del propio GeoComp.</translation>
        </message>
        <message>
            <source>GeoComp cannot tell which way this file's GMT difference runs, and computing the tide needs UTC. Give the offset of the file's times from UTC explicitly, or keep the instrument's own tide correction.</source>
            <translation>GeoComp no puede determinar el sentido de la diferencia GMT de este archivo, y el cálculo de la marea necesita UTC. Indique explícitamente el desfase de las horas del archivo respecto a UTC, o mantenga la corrección de marea del propio instrumento.</translation>
        </message>
        <message>
            <source>GeoComp could not complete the operation (%1). See the GeoComp tab of the Log Messages panel for details.</source>
            <translation>GeoComp no pudo completar la operación (%1). Consulte la pestaña GeoComp del panel Mensajes de Registro para más detalles.</translation>
        </message>
        <message>
            <source>GeoComp has no assumed precision for a planned %1, and will not invent one. State its precision.</source>
            <translation>GeoComp no tiene precisión supuesta para un(a) %1 planificado(a), y no inventará una. Indique su precisión.</translation>
        </message>
        <message>
            <source>GeoComp has no verified release of %1 for this computer (%2); it has one for: %3. Install the engine yourself and give its path in Global Settings, under Paths and engines.</source>
            <translation>GeoComp no tiene una versión verificada de %1 para este equipo (%2); la tiene para: %3. Instale el motor usted mismo e indique su ruta en Configuraciones Globales, en Rutas y motores.</translation>
        </message>
        <message>
            <source>GeoComp holds no transformation between the frames %1.</source>
            <translation>GeoComp no tiene transformación entre los marcos de referencia %1.</translation>
        </message>
        <message>
            <source>GeoComp's record of the %1 release has a malformed SHA-256 digest ('%2'), so no download of it could be verified. This is a defect in GeoComp: please report it, and install the engine yourself meanwhile.</source>
            <translation>El registro de GeoComp de la versión de %1 tiene un resumen SHA-256 mal formado ('%2'), por lo que ninguna descarga de ella podría verificarse. Es un defecto de GeoComp: por favor, infórmelo, y mientras tanto instale el motor usted mismo.</translation>
        </message>
        <message>
            <source>Gravity observations (%1) were merged into the geometric network, where they would be adjusted as if free of drift. Give the gravity as its own network, built with its drift model.</source>
            <translation>Se incorporaron observaciones de gravedad (%1) a la red geométrica, donde se ajustarían como si estuvieran libres de deriva. Indique la gravedad como su propia red, construida con su modelo de deriva.</translation>
        </message>
        <message>
            <source>Heights cannot be converted between %1. A geoid relates ellipsoidal and orthometric heights only; normal heights need a quasi-geoid, which is a different model.</source>
            <translation>Las alturas no pueden convertirse entre %1. Un geoide relaciona solo alturas elipsoidales y ortométricas; las alturas normales necesitan un cuasigeoide, que es un modelo distinto.</translation>
        </message>
        <message>
            <source>Heights of different types (%1) cannot be combined without a geoid model: the result would be wrong by the geoid undulation and still look reasonable. Give a geoid model, or heights of one type.</source>
            <translation>Alturas de tipos diferentes (%1) no pueden combinarse sin un modelo geoidal: el resultado sería erróneo en la ondulación geoidal y aun así parecería razonable. Indique un modelo geoidal, o alturas de un solo tipo.</translation>
        </message>
        <message>
            <source>In '%1', the %2 '%3' is not a number, on the line: %4</source>
            <translation>En '%1', el/la %2 '%3' no es un número, en la línea: %4</translation>
        </message>
        <message>
            <source>In the input '%1', %2 must be moved to the combination's epoch, and no velocity was given for it. Supply one in the velocities file; zero is not assumed -- it is a decimetre a decade in most of Brazil.</source>
            <translation>En la entrada '%1', %2 debe llevarse a la época de la combinación, y no se dio velocidad para él. Indique una en el archivo de velocidades; no se supone cero -- es un decímetro por década en la mayor parte de Brasil.</translation>
        </message>
        <message>
            <source>Line %1 of '%2' could not be read as a %3 line; compare it with the export's layout, then correct or remove it and run again.</source>
            <translation>La línea %1 de '%2' no se pudo leer como una línea %3; compárela con el formato de la exportación, luego corríjala o elimínela y ejecute de nuevo.</translation>
        </message>
        <message>
            <source>Line %1 of '%2' gives the time '%3' without its offset from UTC. The tide depends on the time to the minute, so a time without a zone is a guess; write it as, for example, 2013-09-15T05:57:01Z or 2013-09-15T02:57:01-03:00.</source>
            <translation>La línea %1 de '%2' indica la hora '%3' sin su desfase respecto a UTC. La marea depende de la hora al minuto, así que una hora sin zona es una conjetura; escríbala, por ejemplo, como 2013-09-15T05:57:01Z o 2013-09-15T02:57:01-03:00.</translation>
        </message>
        <message>
            <source>Line %1: %2</source>
            <translation>Línea de nivelación %1: %2</translation>
        </message>
        <message>
            <source>Measurement %1 is a %2 with a %3 of %4, but a height offset does not change this kind of measurement. Remove the offset, or check the measurement type.</source>
            <translation>La medición %1 es un(a) %2 con %3 de %4, pero un desplazamiento de altura no cambia este tipo de medición. Elimine el desplazamiento, o compruebe el tipo de medición.</translation>
        </message>
        <message>
            <source>Measurement %1 scales its variances (%2), which GeoComp cannot represent: only a scale of 1 can be read. Remove the scaling, or scale the standard deviations themselves.</source>
            <translation>La medición %1 escala sus varianzas (%2), lo que GeoComp no puede representar: solo puede leerse una escala de 1. Elimine la escala, o escale las propias desviaciones estándar.</translation>
        </message>
        <message>
            <source>No baseline joins %1 and %2, so the loop cannot be closed. Process that pair, or choose a loop of baselines that exist.</source>
            <translation>Ninguna línea base une %1 y %2, por lo que el circuito no puede cerrarse. Procese ese par, o elija un circuito de líneas base existentes.</translation>
        </message>
        <message>
            <source>No benchmark was supplied, so the network is free: it has one datum defect, and determines every height difference but no height. Adjust it with an inner or minimum constraint.</source>
            <translation>No se indicó ningún punto de referencia, así que la red es libre: tiene una deficiencia de datum y determina todos los desniveles, pero ninguna altura. Ajústela con una restricción interna o mínima.</translation>
        </message>
        <message>
            <source>No gravimeter profile was named and the profile library sets no default. Add one to the library, or run without a library to use the file's own instrument names.</source>
            <translation>No se indicó ningún perfil de gravímetro y la biblioteca de perfiles no define uno predeterminado. Añada uno a la biblioteca, o ejecute sin biblioteca para usar los nombres de instrumento del propio archivo.</translation>
        </message>
        <message>
            <source>No instrument profile applies: none is named on the observation, and the library has no default. GeoComp does not invent instrument constants; give an Instrument profiles file, or name a profile.</source>
            <translation>Ningún perfil de instrumento se aplica: ninguno se nombra en la observación, y la biblioteca no tiene uno por defecto. GeoComp no inventa constantes de instrumento; indique un archivo de Perfiles de instrumento, o nombre un perfil.</translation>
        </message>
        <message>
            <source>No level profile applies: none is named on the line, and the library has no default. GeoComp does not invent instrument precisions; give an Instrument profiles file, or name a profile.</source>
            <translation>Ningún perfil de nivel se aplica: ninguno se nombra en la línea, y la biblioteca no tiene uno por defecto. GeoComp no inventa precisiones de instrumento; indique un archivo de Perfiles de instrumento, o nombre un perfil.</translation>
        </message>
        <message>
            <source>No levelling line of '%1' reaches the benchmarks %2. A constraint on a station no line reaches does nothing, and would hide that the network is unconstrained; check their names, or remove them.</source>
            <translation>Ninguna línea de nivelación de '%1' alcanza los puntos de referencia %2. Una restricción en una estación que ninguna línea alcanza no hace nada, y ocultaría que la red no está ligada; compruebe los nombres, o elimínelos.</translation>
        </message>
        <message>
            <source>No observations were supplied; the adjustment needs at least one active observation.</source>
            <translation>No se proporcionó ninguna observación; el ajuste necesita al menos una observación activa.</translation>
        </message>
        <message>
            <source>No one dimension of adjustment, 1D, 2D or 3D, takes every observation of the network '%1'.</source>
            <translation>Ninguna dimensión de ajuste, 1D, 2D o 3D, acepta todas las observaciones de la red '%1'.</translation>
        </message>
        <message>
            <source>No reading or absolute value refers to %1, so its gravity cannot be held or adjusted. Check the station names against the readings.</source>
            <translation>Ninguna lectura ni valor absoluto se refiere a %1, así que su gravedad no puede fijarse ni ajustarse. Compruebe los nombres de las estaciones con las lecturas.</translation>
        </message>
        <message>
            <source>No reference stations were named. A displacement is measured against stations assumed stable; name them in Reference stations, or mark them REFERENCE in the network document.</source>
            <translation>No se nombraron estaciones de referencia. Un desplazamiento se mide contra estaciones supuestas estables; nómbrelas en Estaciones de referencia, o márquelas REFERENCE en el documento de la red.</translation>
        </message>
        <message>
            <source>No stations were given to define the datum on; give at least one estimated station.</source>
            <translation>No se indicó ninguna estación sobre la que definir el datum; indique al menos una estación estimada.</translation>
        </message>
        <message>
            <source>Nothing supplies '%1', and without it there is no observation to import.</source>
            <translation>Nada proporciona '%1', y sin ello no hay observación que importar.</translation>
        </message>
        <message>
            <source>Observation '%1' between %2 has no horizontal separation at the approximate coordinates, so the zenith angle cannot be linearised there. Correct the approximate coordinates.</source>
            <translation>La observación '%1' entre %2 no tiene separación horizontal en las coordenadas aproximadas, por lo que el ángulo cenital no puede linealizarse allí. Corrija las coordenadas aproximadas.</translation>
        </message>
        <message>
            <source>Observation '%1' carries no uncertainty, so it cannot be weighted. GeoComp does not invent a weight, because a fabricated one silently corrupts every statistic; give the observation its standard deviation.</source>
            <translation>La observación '%1' no lleva incertidumbre, así que no puede ponderarse. GeoComp no inventa un peso, porque un peso fabricado corrompe silenciosamente toda estadística; indique la desviación estándar de la observación.</translation>
        </message>
        <message>
            <source>Observation '%1' connects stations that are at the same approximate position (%2), so its direction is undefined. Correct the approximate coordinates.</source>
            <translation>La observación '%1' une estaciones que están en la misma posición aproximada (%2), por lo que su dirección es indefinida. Corrija las coordenadas aproximadas.</translation>
        </message>
        <message>
            <source>Observation '%1' is a %2, which DynAdjust has no measurement type for, so its adjusted value cannot be found in the output.</source>
            <translation>La observación '%1' es un(a) %2, para el que DynAdjust no tiene tipo de medición, por lo que su valor ajustado no puede encontrarse en la salida.</translation>
        </message>
        <message>
            <source>Observation '%1' is of type %2, which is not a gravity observation, so it cannot take part in a gravity adjustment.</source>
            <translation>La observación '%1' es de tipo %2, que no es una observación gravimétrica, por lo que no puede participar en un ajuste de gravedad.</translation>
        </message>
        <message>
            <source>Observation '%1' is of type %2, which the in-house adjustment does not implement. %3</source>
            <translation>La observación '%1' es de tipo %2, que el ajuste propio de GeoComp aún no implementa. %3</translation>
        </message>
        <message>
            <source>Observation '%1' of type %2 cannot contribute to a %3 adjustment. Choose a coordinate frame the observation can constrain, or exclude it.</source>
            <translation>La observación '%1', de tipo %2, no puede contribuir a un ajuste %3. Elija un marco de coordenadas que la observación pueda constreñir, o exclúyala.</translation>
        </message>
        <message>
            <source>Orthometric heights (from levelling) meet the ellipsoidal heights the geocentric frame computes, and no geoid model relates them. Choose a geoid model: without one they differ by the undulation, tens of metres in much of Brazil.</source>
            <translation>Alturas ortométricas (de la nivelación) se encuentran con las alturas elipsoidales que calcula el marco geocéntrico, y ningún modelo geoidal las relaciona. Elija un modelo geoidal: sin él difieren en la ondulación, decenas de metros en buena parte de Brasil.</translation>
        </message>
        <message>
            <source>PostGIS projects need the psycopg2 Python module, which this QGIS does not have. Install it into the Python QGIS uses (on Linux, the python3-psycopg2 package), then restart QGIS.</source>
            <translation>Los proyectos PostGIS necesitan el módulo de Python psycopg2, que este QGIS no tiene. Instálelo en el Python que usa QGIS (en Linux, el paquete python3-psycopg2) y reinicie QGIS.</translation>
        </message>
        <message>
            <source>Reading '%1' has had no tide removed, and the tide model is set to none. Leaving the tide in costs a few hundred microgal that change by the hour; choose Longman's model, or confirm that the instrument applied its own.</source>
            <translation>A la lectura '%1' no se le quitó la marea, y el modelo de marea está configurado como ninguno. Dejar la marea cuesta algunos cientos de microgal que cambian cada hora; elija el modelo de Longman, o confirme que el instrumento aplicó el suyo.</translation>
        </message>
        <message>
            <source>Reading '%1' needs a tide correction and has no latitude and longitude to compute it for. Add the location to the file, or keep an instrument-applied tide.</source>
            <translation>La lectura '%1' necesita una corrección de marea y no tiene latitud y longitud para calcularla. Añada la ubicación al archivo, o mantenga la marea aplicada por el instrumento.</translation>
        </message>
        <message>
            <source>Reducing distances to the ellipsoid needs a height for every station a distance ends at, and the positions of these do not say what their height is measured from: %1. Give the heights, or turn the reduction off.</source>
            <translation>Reducir distancias al elipsoide exige una altura para cada estación en la que termina una distancia, y las posiciones de estas no dicen desde qué superficie se mide su altura: %1. Indique las alturas, o desactive la reducción.</translation>
        </message>
        <message>
            <source>Reducing distances to the grid needs an approximate position for every station a distance ends at, and these have none: %1. Give them approximate coordinates, or turn the reduction off.</source>
            <translation>Reducir distancias a la cuadrícula exige una posición aproximada para cada estación en la que termina una distancia, y estas no tienen ninguna: %1. Deles coordenadas aproximadas, o desactive la reducción.</translation>
        </message>
        <message>
            <source>Row %1 of the alert thresholds file cannot be read: '%2'. Expected a positive limit in metres, or in metres a year for a velocity. Each row is kind, limit, stations, group.</source>
            <translation>La fila %1 del archivo de umbrales de alerta no se puede leer: '%2'. Se esperaba un límite positivo en metros, o en metros por año para una velocidad. Cada fila es tipo, límite, estaciones, grupo.</translation>
        </message>
        <message>
            <source>Row %1 of the gravimeter's calibration table does not increase; the counter readings must increase strictly down the table.</source>
            <translation>La fila %1 de la tabla de calibración del gravímetro no aumenta; las lecturas de contador deben aumentar estrictamente a lo largo de la tabla.</translation>
        </message>
        <message>
            <source>Row %1 of the gravimeter's calibration table gives %2, where the previous row and its factor imply %3. The rows disagree by more than printing explains, so one of them was mistyped.</source>
            <translation>La fila %1 de la tabla de calibración del gravímetro da %2, donde la fila anterior y su factor implican %3. Las filas discrepan más de lo que la impresión explica, por lo que una de ellas se escribió mal.</translation>
        </message>
        <message>
            <source>Row %1 of the gravimeter's calibration table has the interval factor %2; it must be positive.</source>
            <translation>La fila %1 de la tabla de calibración del gravímetro tiene el factor de intervalo %2; debe ser positivo.</translation>
        </message>
        <message>
            <source>Row %1: %2</source>
            <translation>Fila %1 de la libreta: %2</translation>
        </message>
        <message>
            <source>Row %1: a second pointing to %2 on the same face, in set %3. The first was kept; give the repetition its own set number to use both.</source>
            <translation>Fila %1 de la libreta: una segunda puntería hacia %2 en el mismo círculo, en la serie %3. Se conservó la primera; dé a la repetición su propio número de serie para usar ambas.</translation>
        </message>
        <message>
            <source>Row %2 of '%1' is not a station followed by its easting, northing and height, in metres. Correct the row, or remove it.</source>
            <translation>La fila %2 de '%1' no es una estación seguida de su E, su N y su altitud, en metros. Corrija la fila, o elimínela.</translation>
        </message>
        <message>
            <source>Session '%1' cannot be pre-corrected: its base station %2 was read %3 time(s), and a degree-%4 drift needs one more reading than its degree. Estimate the drift with the station values instead, or lower the degree.</source>
            <translation>La sesión '%1' no puede precorregirse: su estación base %2 se leyó %3 vez/veces, y una deriva de grado %4 necesita una lectura más que su grado. Estime la deriva junto con los valores de las estaciones, o reduzca el grado.</translation>
        </message>
        <message>
            <source>Session '%1' holds readings from several instruments (%2). Drift belongs to an instrument, so each needs its own session.</source>
            <translation>La sesión '%1' contiene lecturas de varios instrumentos (%2). La deriva pertenece a un instrumento, así que cada uno necesita su propia sesión.</translation>
        </message>
        <message>
            <source>Setup %1 has %2 backsight(s) and %3 foresight(s); it needs exactly one backsight and at least one foresight.</source>
            <translation>El estacionamiento %1 tiene %2 visual(es) de espalda y %3 visual(es) de frente; necesita exactamente una visual de espalda y al menos una de frente.</translation>
        </message>
        <message>
            <source>Setup %1 is out of balance by %2 m and no level profile was supplied, so no collimation correction was applied. Supply the two-peg test result to correct it, or balance the sights so it does not matter.</source>
            <translation>El estacionamiento %1 está desequilibrado en %2 m y no se indicó ningún perfil de nivel, así que no se aplicó ninguna corrección de colimación. Indique el resultado del ensayo de las dos estacas para corregirlo, o equilibre las visuales para que no importe.</translation>
        </message>
        <message>
            <source>Setup %1 is out of balance by %2 m on the sight to %3, beyond the %4 m its class permits.</source>
            <translation>El estacionamiento %1 está desequilibrado en %2 m en la visual hacia %3, más allá de los %4 m que permite su clase.</translation>
        </message>
        <message>
            <source>Setup %1 recorded no sight distances, so its balance cannot be checked and no collimation correction can be applied. Record the distances, or read three wires and let them be derived.</source>
            <translation>El estacionamiento %1 no registró distancias de visual, así que su equilibrio no puede comprobarse y no puede aplicarse ninguna corrección de colimación. Registre las distancias, o lea los tres hilos y deje que se deriven.</translation>
        </message>
        <message>
            <source>Setup %1: %2</source>
            <translation>Estacionamiento %1: %2</translation>
        </message>
        <message>
            <source>Someone else saved %1 since you opened it (revision %2 now; you read %3). Nothing was written. Open the project again and redo your change, so their save is not overwritten.</source>
            <translation>Otra persona guardó %1 desde que usted lo abrió (revisión %2 ahora; usted leyó la %3). No se escribió nada. Abra el proyecto de nuevo y rehaga su cambio, para no sobrescribir lo que guardó.</translation>
        </message>
        <message>
            <source>State the epoch of the combination (a decimal year). None of the inputs states one GeoComp could take, and it does not assume one.</source>
            <translation>Indique la época de la combinación (un año decimal). Ninguna de las entradas indica una que GeoComp pueda tomar, y no supone una.</translation>
        </message>
        <message>
            <source>Station %1 appears in only %2 observation component(s), but a %3D position needs at least %4.</source>
            <translation>La estación %1 aparece en solo %2 componente(s) de observación, pero una posición %3D necesita al menos %4.</translation>
        </message>
        <message>
            <source>Station %1 is expected to reach %2 mm, against a required %3 mm.</source>
            <translation>Se espera que la estación %1 alcance %2 mm, frente a los %3 mm exigidos.</translation>
        </message>
        <message>
            <source>Station %1 records %2 different instrument heights. The first was used; check the field book.</source>
            <translation>La estación %1 registra %2 alturas del instrumento distintas. Se usó la primera; compruebe la libreta de campo.</translation>
        </message>
        <message>
            <source>Station %1 records no instrument height. Zero was assumed, which is right only for a leap-frog setup.</source>
            <translation>La estación %1 no registra altura del instrumento. Se asumió cero, lo que solo es correcto para un estacionamiento leap-frog.</translation>
        </message>
        <message>
            <source>Station %1 records no temperature or pressure, so the first-velocity correction was not applied. On short sights this is immaterial; over a kilometre a 10 degree error is 10 mm.</source>
            <translation>La estación %1 no registra temperatura ni presión, así que no se aplicó la corrección de primera velocidad. En visuales cortas es irrelevante; en un kilómetro, un error de 10 grados da 10 mm.</translation>
        </message>
        <message>
            <source>Station '%1' has a weighted constraint, which DynAdjust cannot express: it holds a coordinate fixed or leaves it free, nothing between. Adjust this network with GeoComp's own adjustment, or make the constraint fixed or free.</source>
            <translation>La estación '%1' tiene una restricción ponderada, que DynAdjust no puede expresar: mantiene una coordenada fija o la deja libre, nada intermedio. Ajuste esta red con el ajuste propio de GeoComp, o haga la restricción fija o libre.</translation>
        </message>
        <message>
            <source>Station '%1' has an orthometric height, and DynAdjust needs a height above the ellipsoid. Give a geoid grid (NTv2) in the dialog, or a geoid undulation for this station.</source>
            <translation>La estación '%1' tiene una altura ortométrica, y DynAdjust necesita una altura sobre el elipsoide. Indique una malla del geoide (NTv2) en el diálogo, o una ondulación geoidal para esta estación.</translation>
        </message>
        <message>
            <source>Station '%1' has no approximate %2, and the linearised adjustment needs a point to linearise about. Supply approximate coordinates, or generate them from the observations.</source>
            <translation>La estación '%1' no tiene %2 aproximada, y el ajuste linealizado necesita un punto en torno al cual linealizar. Proporcione coordenadas aproximadas, o genérelas a partir de las observaciones.</translation>
        </message>
        <message>
            <source>Station '%1' has no location, so its adjusted gravity has nowhere to be reported. Give its readings a latitude and longitude.</source>
            <translation>La estación '%1' no tiene ubicación, así que su gravedad ajustada no tiene dónde informarse. Dé a sus lecturas una latitud y una longitud.</translation>
        </message>
        <message>
            <source>Station '%1' has projected coordinates (%2, %3), and GeoComp cannot tell which projection that coordinate system is, so it cannot give DynAdjust the latitude and longitude it needs. Give the stations geodetic or geocentric coordinates.</source>
            <translation>La estación '%1' tiene coordenadas proyectadas (%2, %3), y GeoComp no puede saber qué proyección es ese sistema de coordenadas, por lo que no puede dar a DynAdjust la latitud y la longitud que necesita. Dé a las estaciones coordenadas geodésicas o geocéntricas.</translation>
        </message>
        <message>
            <source>Station '%1' in the DynaML file has the coordinate type '%2', which GeoComp does not read; it reads %3.</source>
            <translation>La estación '%1' del archivo DynaML tiene el tipo de coordenada '%2', que GeoComp no lee; lee %3.</translation>
        </message>
        <message>
            <source>Station '%1' is held fixed but carries no position, so there is no value to hold it at. Give it coordinates, or release the constraint.</source>
            <translation>La estación '%1' está fija pero no tiene posición, por lo que no hay valor en el que mantenerla. Asígnele coordenadas, o libere la constricción.</translation>
        </message>
        <message>
            <source>Station '%1' is not foresighted from setup '%2', which foresights %3.</source>
            <translation>La estación '%1' no se visa de frente desde el estacionamiento '%2', que visa de frente %3.</translation>
        </message>
        <message>
            <source>Strain cannot be computed here. It needs east and north components, and three object points at least, spread over an area rather than along a line.</source>
            <translation>La deformación no puede calcularse aquí. Necesita las componentes este y norte, y al menos tres puntos objeto, repartidos por un área y no a lo largo de una línea.</translation>
        </message>
        <message>
            <source>The %1 antenna offset is in %2; give it in metres.</source>
            <translation>El desplazamiento de antena %1 está en %2; indíquelo en metros.</translation>
        </message>
        <message>
            <source>The %1 is in %2, where %3 was expected.</source>
            <translation>El/la %1 está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 is in %2; give it in metres.</source>
            <translation>El/la %1 está en %2; indíquelo en metros.</translation>
        </message>
        <message>
            <source>The %1 is in %2; give it in radians.</source>
            <translation>El/la %1 está en %2; indíquelo en radianes.</translation>
        </message>
        <message>
            <source>The %1 latitude %2 (radians) lies outside -90 to 90 degrees. Check the stations' positions.</source>
            <translation>La latitud %1 %2 (radianes) queda fuera de -90 a 90 grados. Compruebe las posiciones de las estaciones.</translation>
        </message>
        <message>
            <source>The %1 mode differences two receivers, and no base station was given for '%2'. Choose the base station's observations, or an absolute mode.</source>
            <translation>El modo %1 diferencia dos receptores, y no se dio ninguna estación base para '%2'. Elija las observaciones de la estación base, o un modo absoluto.</translation>
        </message>
        <message>
            <source>The %1 mode uses one receiver, and a base station ('%2') was given. RTKLIB would ignore it, silently turning a baseline into a single-receiver solution. Remove the base, or choose a relative mode.</source>
            <translation>El modo %1 usa un receptor, y se dio una estación base ('%2'). RTKLIB la ignoraría, convirtiendo silenciosamente una línea base en una solución de un solo receptor. Quite la base, o elija un modo relativo.</translation>
        </message>
        <message>
            <source>The %1 of a position carries no uncertainty (it is a %2). Every coordinate in GeoComp carries its standard deviation; give one.</source>
            <translation>El/la %1 de una posición no lleva incertidumbre (es un %2). Toda coordenada en GeoComp lleva su desviación estándar; indique una.</translation>
        </message>
        <message>
            <source>The %1 of a position is in %2, where %3 was expected.</source>
            <translation>El/la %1 de una posición está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 of a reading is in %2, where %3 was expected.</source>
            <translation>El/la %1 de una lectura está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 of a reduction is in %2, where %3 was expected.</source>
            <translation>El/la %1 de una reducción está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 of an instrument profile is in %2, where %3 was expected.</source>
            <translation>El/la %1 de un perfil de instrumento está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 of the atmosphere is in %2, where %3 was expected.</source>
            <translation>El/la %1 de la atmósfera está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The %1 of the reading on '%2' is in %3; give it in metres.</source>
            <translation>El/la %1 de la lectura en '%2' está en %3; indíquelo en metros.</translation>
        </message>
        <message>
            <source>The %1 of the sight to '%2' is in %3, where %4 was expected.</source>
            <translation>El/la %1 de la visual a '%2' está en %3, donde se esperaba %4.</translation>
        </message>
        <message>
            <source>The %1 table in DynAdjust's output has columns GeoComp does not recognise, so it was probably written by a DynAdjust version GeoComp has not been checked against. Expected the header '%2'; found '%3'.</source>
            <translation>La tabla %1 en la salida de DynAdjust tiene columnas que GeoComp no reconoce, por lo que probablemente fue escrita por una versión de DynAdjust con la que GeoComp no se ha verificado. Se esperaba el encabezado '%2'; se encontró '%3'.</translation>
        </message>
        <message>
            <source>The %1 threshold's limit is %2; it must be positive.</source>
            <translation>El límite del umbral %1 es %2; debe ser positivo.</translation>
        </message>
        <message>
            <source>The %1 wire reading carries no uncertainty; every reading needs one.</source>
            <translation>La lectura del hilo %1 no tiene incertidumbre; toda lectura necesita una.</translation>
        </message>
        <message>
            <source>The %1 wire reading is in %2; give it in metres.</source>
            <translation>La lectura del hilo %1 está en %2; indíquela en metros.</translation>
        </message>
        <message>
            <source>The %2 '%1' has no standard deviation: none was imported, no instrument profile gives one, and no default is set. GeoComp does not invent one, because a fabricated weight corrupts every statistic computed from it. Set the default in Global Settings, under Stochastic model, or give an instrument profile.</source>
            <translation>El/la %2 '%1' no tiene desviación estándar: no se importó ninguna, ningún perfil de instrumento la da, y no hay ningún valor por defecto. GeoComp no inventa una, porque un peso fabricado corrompe toda estadística calculada a partir de él. Defina el valor por defecto en las Configuraciones Globales, en Modelo estocástico, o indique un perfil de instrumento.</translation>
        </message>
        <message>
            <source>The %2 component of the baseline '%1' is in %3; give it in metres.</source>
            <translation>La componente %2 de la línea base '%1' está en %3; indíquela en metros.</translation>
        </message>
        <message>
            <source>The %2 coordinate of the reference station '%1' is in %3; give it in metres.</source>
            <translation>La coordenada %2 de la estación de referencia '%1' está en %3; indíquela en metros.</translation>
        </message>
        <message>
            <source>The %2 of the instrument '%1' is %3; a standard deviation cannot be negative.</source>
            <translation>El/la %2 del instrumento '%1' es %3; una desviación estándar no puede ser negativa.</translation>
        </message>
        <message>
            <source>The %2 of the level '%1' is %3; a standard deviation cannot be negative.</source>
            <translation>El/la %2 del nivel '%1' es %3; una desviación estándar no puede ser negativa.</translation>
        </message>
        <message>
            <source>The %2 of the levelling class '%1' is %3; a limit cannot be negative, and zero means unconstrained.</source>
            <translation>El/la %2 de la clase de nivelación '%1' es %3; un límite no puede ser negativo, y cero significa sin restricción.</translation>
        </message>
        <message>
            <source>The %2 of the observation '%1' carries no uncertainty. Every observation in GeoComp carries its standard deviation; give one.</source>
            <translation>El/la %2 de la observación '%1' no lleva incertidumbre. Toda observación en GeoComp lleva su desviación estándar; indique una.</translation>
        </message>
        <message>
            <source>The %2 of the observation '%1' is %3, where a length in metres was expected.</source>
            <translation>El/la %2 de la observación '%1' es %3, donde se esperaba una longitud en metros.</translation>
        </message>
        <message>
            <source>The %2 of the observation '%1' is in %3, where %4 was expected.</source>
            <translation>El/la %2 de la observación '%1' está en %3, donde se esperaba %4.</translation>
        </message>
        <message>
            <source>The '%1' engine is required for this operation but is not installed. Install it from Global Settings, under Paths and engines.</source>
            <translation>El motor '%1' es necesario para esta operación, pero no está instalado. Instálelo desde Configuraciones Globales, en Rutas y motores.</translation>
        </message>
        <message>
            <source>The CG-5 header field %1 of '%2' reads '%3', which is not a latitude or longitude with its hemisphere. The tide needs the survey's location.</source>
            <translation>El campo de cabecera CG-5 %1 de '%2' contiene '%3', que no es una latitud o longitud con su hemisferio. La marea necesita la ubicación del levantamiento.</translation>
        </message>
        <message>
            <source>The CSV '%1' lacks required columns: it has %2, and needs %3.</source>
            <translation>El CSV '%1' no tiene las columnas obligatorias: tiene %2 y necesita %3.</translation>
        </message>
        <message>
            <source>The DynAdjust configuration '%1' could not be read as JSON: %2.</source>
            <translation>No se pudo leer la configuración de DynAdjust '%1' como JSON: %2.</translation>
        </message>
        <message>
            <source>The DynAdjust configuration '%1' is not a list of options per program. Write it as {"dnaadjust": ["--option", "value"]}.</source>
            <translation>La configuración de DynAdjust '%1' no es una lista de opciones por programa. Escríbala como {"dnaadjust": ["--option", "value"]}.</translation>
        </message>
        <message>
            <source>The DynAdjust configuration gives '%1' to %2, an option GeoComp sets itself. Change it through the algorithm's own parameter instead: GeoComp reads the output back by what that option says, and would misread it.</source>
            <translation>La configuración de DynAdjust pasa '%1' a %2, una opción que GeoComp define por sí mismo. Cámbiela mediante el parámetro propio del algoritmo: GeoComp lee la salida de vuelta por lo que esa opción dice, y la leería mal.</translation>
        </message>
        <message>
            <source>The DynAdjust configuration names '%1', which is not a program GeoComp runs. It may give options to: %2.</source>
            <translation>La configuración de DynAdjust nombra '%1', que no es un programa que GeoComp ejecute. Puede dar opciones a: %2.</translation>
        </message>
        <message>
            <source>The DynAdjust program %1 was not found. Install DynAdjust from Project &gt; Install an engine, or give its directory in Global Settings, under Paths and engines.</source>
            <translation>No se encontró el programa %1 de DynAdjust. Instale DynAdjust desde Proyecto &gt; Instalar un motor, o indique su directorio en las Configuraciones Globales, en Rutas y motores.</translation>
        </message>
        <message>
            <source>The EDM %1 is %2; a precision cannot be negative.</source>
            <translation>El/la %1 del MED es %2; una precisión no puede ser negativa.</translation>
        </message>
        <message>
            <source>The EDM carrier wavelength must be positive, in micrometres; %1 was given. Check the instrument profile.</source>
            <translation>La longitud de onda de la portadora del MED debe ser positiva, en micrómetros; se dio %1. Compruebe el perfil del instrumento.</translation>
        </message>
        <message>
            <source>The GNSS baseline '%1' is in %2, not in the network's own frame. Differenced against coordinates in another frame it would be wrong by a rotation, with nothing to say so; rotate it into the network's frame first.</source>
            <translation>La línea base GNSS '%1' está en %2, no en el marco propio de la red. Diferenciada contra coordenadas en otro marco, estaría equivocada por una rotación, sin que nada lo dijera; rótela primero al marco de la red.</translation>
        </message>
        <message>
            <source>The GNSS baseline '%1' is recorded as %2, and DynAdjust's baselines are geocentric (ECEF) vectors: written as it is, it would be read back as something else. Import the baselines as ECEF X, Y and Z components.</source>
            <translation>La línea base GNSS '%1' está registrada como %2, y las líneas base de DynAdjust son vectores geocéntricos (ECEF): escrita tal cual, se leería de vuelta como otra cosa. Importe las líneas base como componentes X, Y y Z ECEF.</translation>
        </message>
        <message>
            <source>The GNSS cluster '%1' has a covariance matrix of shape %2, where %3 by %3 was expected for its %4 three-component members, so it cannot be written for DynAdjust. Check the file the cluster was imported from.</source>
            <translation>El agrupamiento GNSS '%1' tiene una matriz de varianza-covarianza de forma %2, donde se esperaba %3 por %3 para sus %4 miembros de tres componentes, así que no puede escribirse para DynAdjust. Compruebe el archivo del que se importó el agrupamiento.</translation>
        </message>
        <message>
            <source>The GNSS cluster '%1' has no baselines.</source>
            <translation>El agrupamiento GNSS '%1' no tiene líneas base.</translation>
        </message>
        <message>
            <source>The GNSS cluster '%1' mixes frames (%2); every baseline of a cluster is in one frame.</source>
            <translation>El agrupamiento GNSS '%1' mezcla marcos de referencia (%2); toda línea base de un agrupamiento está en un solo marco.</translation>
        </message>
        <message>
            <source>The GNSS loop %1 mixes baselines reduced to the marks with baselines that are not, so its misclosure would measure the antenna heights. Reduce every leg, or none.</source>
            <translation>El circuito GNSS %1 mezcla líneas base reducidas a las marcas con otras que no lo están, por lo que su error de cierre mediría las alturas de antena. Reduzca todos los lados, o ninguno.</translation>
        </message>
        <message>
            <source>The GNSS loop %1 visits a station twice, which splits it into two loops. List each station once.</source>
            <translation>El circuito GNSS %1 pasa dos veces por una estación, lo que lo divide en dos circuitos. Liste cada estación una vez.</translation>
        </message>
        <message>
            <source>The GNSS session '%1' ends at %3, before it starts at %2. Check the session's times.</source>
            <translation>La sesión GNSS '%1' termina en %3, antes de empezar en %2. Compruebe las horas de la sesión.</translation>
        </message>
        <message>
            <source>The RTKLIB configuration file '%1' could not be read: %2.</source>
            <translation>No se pudo leer el archivo de configuración de RTKLIB '%1': %2.</translation>
        </message>
        <message>
            <source>The RTKLIB configuration file '%1' sets no options. It should hold key = value lines, as rnx2rtkp -k reads; check that it is the file you meant.</source>
            <translation>El archivo de configuración de RTKLIB '%1' no define ninguna opción. Debe contener líneas clave = valor, como las lee rnx2rtkp -k; compruebe que es el archivo que quería.</translation>
        </message>
        <message>
            <source>The RTKLIB configuration file gives '%1', where %2 was expected.</source>
            <translation>El archivo de configuración de RTKLIB da '%1', donde se esperaba %2.</translation>
        </message>
        <message>
            <source>The RTKLIB configuration file sets %1, which GeoComp sets itself: the positioning mode is the algorithm's, the base station's position is held by GeoComp, and the solution is read back by the out- options. Remove them from the file.</source>
            <translation>El archivo de configuración de RTKLIB define %1, que GeoComp define por sí mismo: el modo de posicionamiento es del algoritmo, la posición de la estación base la fija GeoComp, y la solución se lee de vuelta por las opciones out-. Elimínelas del archivo.</translation>
        </message>
        <message>
            <source>The URL of the base map service '%1' carries a key or password, which would be copied into every export and every log. Remove it, and name a QGIS authentication configuration in the service's auth_config_id instead.</source>
            <translation>La URL del servicio de mapa base '%1' lleva una clave o contraseña, que se copiaría en cada exportación y cada registro. Elimínela, y nombre en su lugar una configuración de autenticación de QGIS en el auth_config_id del servicio.</translation>
        </message>
        <message>
            <source>The URL of the base map service '%1' is an XYZ tile URL without {z}, {x} and {y}, so no tile could be requested. Add them where the service expects them.</source>
            <translation>La URL del servicio de mapa base '%1' es una URL de teselas XYZ sin {z}, {x} e {y}, así que no podría solicitarse ninguna tesela. Añádalos donde el servicio los espera.</translation>
        </message>
        <message>
            <source>The absolute gravity value '%1' has no usable value or uncertainty. Without an uncertainty it would be a fixed constraint under another name; give it in m/s^2 with its uncertainty.</source>
            <translation>El valor de gravedad absoluta '%1' no tiene valor o incertidumbre utilizable. Sin incertidumbre sería una restricción fija con otro nombre; indíquelo en m/s^2 con su incertidumbre.</translation>
        </message>
        <message>
            <source>The adjusted gravity of the station '%1' is in %2, where %3 was expected.</source>
            <translation>La gravedad ajustada de la estación '%1' está en %2, donde se esperaba %3.</translation>
        </message>
        <message>
            <source>The adjusted measurement for observation '%1' is a %2 in DynAdjust's output, where a %3 was written: the rows are not in the order of the network. The output and the network are not from the same run.</source>
            <translation>La medición ajustada de la observación '%1' es un(a) %2 en la salida de DynAdjust, donde se escribió un(a) %3: las filas no están en el orden de la red. La salida y la red no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>The adjusted measurement for observation '%1' joins %2 in DynAdjust's output, where it joins %3 in the network. The output and the network are not from the same run.</source>
            <translation>La medición ajustada de la observación '%1' une %2 en la salida de DynAdjust, mientras que en la red une %3. La salida y la red no son de la misma ejecución.</translation>
        </message>
        <message>
            <source>The adjustment file was written by DynAdjust %1 and the uncertainty file by DynAdjust %2, so they are not from the same run. Give the files one run wrote.</source>
            <translation>El archivo de ajuste fue escrito por DynAdjust %1 y el archivo de incertidumbres por DynAdjust %2, por lo que no son de la misma ejecución. Indique los archivos escritos por una misma ejecución.</translation>
        </message>
        <message>
            <source>The adjustment of '%1' did not converge: after %2 iteration(s) the largest correction was still %3, against a threshold of %4. Approximate coordinates that are far from the truth are the usual cause; a blunder large enough to drag the solution is the other. No coordinates are returned, because iterate %2 of a diverging sequence is not a result.</source>
            <translation>El ajuste de '%1' no convergió: tras %2 iteración(es) la mayor corrección seguía siendo %3, frente a un umbral de %4. Unas coordenadas aproximadas lejanas de la verdad son la causa habitual; un error grosero suficientemente grande como para arrastrar la solución es la otra. No se devuelve ninguna coordenada, porque la iteración %2 de una sucesión divergente no es un resultado.</translation>
        </message>
        <message>
            <source>The adjustment of '%1' produced no iterations at all. This is an internal error; please report it with the network that caused it.</source>
            <translation>El ajuste de '%1' no produjo iteración alguna. Se trata de un error interno; comuníquelo junto con la red que lo provocó.</translation>
        </message>
        <message>
            <source>The angle '%1' has 60 or more minutes, which DDD.MMSSsss notation does not allow.</source>
            <translation>El ángulo '%1' tiene 60 minutos o más, lo que la notación DDD.MMSSsss no permite.</translation>
        </message>
        <message>
            <source>The angle '%1' has 60 or more seconds, which DDD.MMSSsss notation does not allow.</source>
            <translation>El ángulo '%1' tiene 60 segundos o más, lo que la notación DDD.MMSSsss no permite.</translation>
        </message>
        <message>
            <source>The angle of the leg %1 is in %2; give it in radians.</source>
            <translation>El ángulo del lado %1 está en %2; indíquelo en radianes.</translation>
        </message>
        <message>
            <source>The angular misclosure is %1 arcsec over %2 station(s), against a tolerance of %3 arcsec.</source>
            <translation>El error de cierre angular es de %1 segundos de arco en %2 estación(es), frente a una tolerancia de %3 segundos de arco.</translation>
        </message>
        <message>
            <source>The antenna height at %2 of the baseline '%1' is a slant height. Converting one needs the antenna's dimensions, which GeoComp has no database of yet; give the vertical height from the mark to the antenna reference point.</source>
            <translation>La altura de antena en %2 de la línea base '%1' es una altura inclinada. Convertirla exige las dimensiones de la antena, de las que GeoComp aún no tiene base de datos; indique la altura vertical de la marca al punto de referencia de la antena.</translation>
        </message>
        <message>
            <source>The antenna height of the GNSS session '%1' is in %2; an antenna height is a length in metres.</source>
            <translation>La altura de la antena de la sesión GNSS '%1' está en %2; una altura de antena es una longitud en metros.</translation>
        </message>
        <message>
            <source>The antenna heights of the baseline '%1' are reduced while it is ECEF, before it is rotated; it is %2.</source>
            <translation>Las alturas de antena de la línea base '%1' se reducen mientras es ECEF, antes de rotarla; es %2.</translation>
        </message>
        <message>
            <source>The approximate heights of these stations are orthometric: %1. Reducing a distance to the ellipsoid needs the ellipsoidal height, so give the geoid undulation, or turn the reduction off.</source>
            <translation>Las alturas aproximadas de estas estaciones son ortométricas: %1. Reducir una distancia al elipsoide exige la altura elipsoidal, así que indique la ondulación geoidal, o desactive la reducción.</translation>
        </message>
        <message>
            <source>The archive refused the login for %1 (HTTP %2). Check the QGIS authentication configuration named for this service in the download services file.</source>
            <translation>El archivo rechazó el inicio de sesión para %1 (HTTP %2). Compruebe la configuración de autenticación de QGIS indicada para este servicio en el archivo de servicios de descarga.</translation>
        </message>
        <message>
            <source>The base map catalogue '%1' could not be read (%2). Correct the file, or clear the catalogue in Global Settings, under Base maps, to use the built-in services.</source>
            <translation>El catálogo de mapas base '%1' no se pudo leer (%2). Corrija el archivo, o vacíe el catálogo en Configuraciones Globales, en Mapas base, para usar los servicios incorporados.</translation>
        </message>
        <message>
            <source>The base map catalogue has more than one service with the id %1. Give each service its own id.</source>
            <translation>El catálogo de mapas base tiene más de un servicio con el id %1. Dé a cada servicio su propio id.</translation>
        </message>
        <message>
            <source>The base map service '%1' has no URL. Give it the address of its tiles.</source>
            <translation>El servicio de mapa base '%1' no tiene URL. Dele la dirección de sus teselas.</translation>
        </message>
        <message>
            <source>The base map service '%1' has no attribution. Adding a base map without the attribution its licence requires breaches that licence; give it, or write none if the service genuinely requires none.</source>
            <translation>El servicio de mapa base '%1' no tiene atribución. Añadir un mapa base sin la atribución que su licencia exige incumple esa licencia; indíquela, o escriba none si el servicio realmente no exige ninguna.</translation>
        </message>
        <message>
            <source>The base station '%2' was not read in the session '%1', which read %3.</source>
            <translation>La estación base '%2' no se leyó en la sesión '%1', que leyó %3.</translation>
        </message>
        <message>
            <source>The baseline '%1' already carries its antenna-height reduction; a second would double the offset.</source>
            <translation>La línea base '%1' ya lleva su reducción de altura de antena; una segunda duplicaría el desplazamiento.</translation>
        </message>
        <message>
            <source>The baseline '%1' has %2 components, where three were expected.</source>
            <translation>La línea base '%1' tiene %2 componentes, donde se esperaban tres.</translation>
        </message>
        <message>
            <source>The baseline '%1' has a covariance of size %2, where a 3 by 3 over its components was expected.</source>
            <translation>La línea base '%1' tiene una covarianza de tamaño %2, donde se esperaba una de 3 por 3 sobre sus componentes.</translation>
        </message>
        <message>
            <source>The baseline '%1' has already been rotated into local east, north and up; it is rotated once, from ECEF.</source>
            <translation>La línea base '%1' ya se rotó a este, norte y arriba locales; se rota una vez, a partir de ECEF.</translation>
        </message>
        <message>
            <source>The baseline '%1' records its frame as '%2', which GeoComp does not know; expected %3.</source>
            <translation>La línea base '%1' registra su marco como '%2', que GeoComp no conoce; se esperaba %3.</translation>
        </message>
        <message>
            <source>The baseline '%1' starts and ends at the same station, '%2'. A baseline joins two distinct stations.</source>
            <translation>La línea base '%1' empieza y termina en la misma estación, '%2'. Una línea base une dos estaciones distintas.</translation>
        </message>
        <message>
            <source>The benchmark '%1' does not say which kind of height it has (orthometric, normal or ellipsoidal), so it cannot be checked against the others.</source>
            <translation>El punto de referencia '%1' no dice qué tipo de altura tiene (ortométrica, normal o elipsoidal), por lo que no puede comprobarse frente a los demás.</translation>
        </message>
        <message>
            <source>The benchmark '%1' has a %2 height to convert with the geoid '%3', and no position: a geoid undulation depends on where the station is. Give the benchmark its latitude and longitude.</source>
            <translation>El punto de referencia '%1' tiene una altura %2 que convertir con el geoide '%3', y ninguna posición: una ondulación geoidal depende de dónde está la estación. Dé al punto de referencia su latitud y longitud.</translation>
        </message>
        <message>
            <source>The benchmark '%1' is a weighted constraint with no uncertainty, which is a fixed constraint under another name. Give its height an uncertainty, or hold it fixed.</source>
            <translation>El punto de referencia '%1' es una restricción ponderada sin incertidumbre, lo que es una restricción fija con otro nombre. Dé una incertidumbre a su altura, o manténgalo fijo.</translation>
        </message>
        <message>
            <source>The calibration factor of the gravimeter '%1' is %2; it must be a positive number close to 1.</source>
            <translation>El factor de calibración del gravímetro '%1' es %2; debe ser un número positivo cercano a 1.</translation>
        </message>
        <message>
            <source>The cluster %1 carries a covariance of size %2 for members with %3 components in all; it needs one row per component.</source>
            <translation>El agrupamiento %1 lleva una matriz de varianza-covarianza de tamaño %2 para miembros con %3 componentes en total; necesita una fila por componente.</translation>
        </message>
        <message>
            <source>The cluster %1 lists the observation %2, which the network does not have.</source>
            <translation>El agrupamiento %1 lista la observación %2, que la red no tiene.</translation>
        </message>
        <message>
            <source>The cluster '%1' has %2 observation(s) and a covariance of size %3, which does not cover every component of every member. A GNSS baseline contributes three rows, so the size is a whole multiple of the number of members.</source>
            <translation>El agrupamiento '%1' tiene %2 observación(es) y una matriz de varianza-covarianza de tamaño %3, que no cubre todas las componentes de todos los miembros. Una línea base aporta tres filas, así que el tamaño es un múltiplo entero del número de miembros.</translation>
        </message>
        <message>
            <source>The cluster '%1' has no member observations. Give it its observations, or remove it.</source>
            <translation>El agrupamiento '%1' no tiene observaciones miembro. Dele sus observaciones, o elimínelo.</translation>
        </message>
        <message>
            <source>The cluster '%1' lists an observation twice. Each member appears once, in the order of the covariance.</source>
            <translation>El agrupamiento '%1' lista una observación dos veces. Cada miembro aparece una vez, en el orden de la matriz de varianza-covarianza.</translation>
        </message>
        <message>
            <source>The collimation implied by the %1 face pairs at station %2 varies by %3 arcsec. A collimation that is constant across a setup is instrumental and harmless; one that drifts means the instrument was disturbed, and face pairing does not fix that.</source>
            <translation>La colimación que implican los %1 pares de círculo directo e inverso en la estación %2 varía %3 segundos de arco. Una colimación constante a lo largo de un estacionamiento es instrumental e inofensiva; una que varía significa que el instrumento fue perturbado, y emparejar los círculos no lo corrige.</translation>
        </message>
        <message>
            <source>The column '%1' is assigned to %2. One column cannot be two fields, and importing it as both would count the measurement twice.</source>
            <translation>La columna '%1' está asignada a %2. Una columna no puede ser dos campos, e importarla como ambos contaría la medición dos veces.</translation>
        </message>
        <message>
            <source>The column '%1' is not mapped to anything and will be ignored.</source>
            <translation>La columna '%1' no está asignada a nada y se ignorará.</translation>
        </message>
        <message>
            <source>The confidence level must be a probability strictly between 0 and 1; %1 was given.</source>
            <translation>El nivel de confianza debe ser una probabilidad estrictamente entre 0 y 1; se dio %1.</translation>
        </message>
        <message>
            <source>The confidence level must lie strictly between 0 and 1; %1 was given.</source>
            <translation>El nivel de confianza debe estar estrictamente entre 0 y 1; se dio %1.</translation>
        </message>
        <message>
            <source>The configurations compared are in different frames (%1); compare them in one frame.</source>
            <translation>Las configuraciones comparadas están en marcos de referencia distintos (%1); compárelas en un solo marco.</translation>
        </message>
        <message>
            <source>The configurations compared are of different station pairs (%1). Comparing configurations needs one station pair in all of them; two different baselines measure the network instead.</source>
            <translation>Las configuraciones comparadas son de pares de estaciones distintos (%1). Comparar configuraciones exige el mismo par de estaciones en todas ellas; dos líneas base distintas miden, en cambio, la red.</translation>
        </message>
        <message>
            <source>The constant of the reflector %1 is applied by the instrument, so GeoComp did not apply it again.</source>
            <translation>La constante del reflector %1 la aplica el instrumento, así que GeoComp no la aplicó de nuevo.</translation>
        </message>
        <message>
            <source>The control station '%2' in '%1' gives no standard deviations. A control station in this format is weighted, not held, so two standard deviations follow its coordinates: %3</source>
            <translation>La estación de control '%2' en '%1' no da desviaciones estándar. Una estación de control en este formato es ponderada, no mantenida, así que dos desviaciones estándar siguen a sus coordenadas: %3</translation>
        </message>
        <message>
            <source>The correlated cluster '%1' has members in different variance-component groups (%2), and a covariance cannot be rescaled by two factors at once. Put the whole cluster in one group.</source>
            <translation>El agrupamiento correlacionado '%1' tiene miembros en grupos de componentes de varianza distintos (%2), y una covarianza no puede reescalarse con dos factores a la vez. Ponga todo el agrupamiento en un solo grupo.</translation>
        </message>
        <message>
            <source>The counts line of '%1' declares %2, but the file holds %3. The counts are the format's own check, so GeoComp cannot tell which was intended.</source>
            <translation>La línea de recuentos de '%1' declara %2, pero el archivo contiene %3. Los recuentos son la comprobación del propio formato, así que GeoComp no puede saber cuál era la intención.</translation>
        </message>
        <message>
            <source>The counts line of '%1' reads '%2', which is not five whole numbers.</source>
            <translation>La línea de recuentos de '%1' dice '%2', que no son cinco números enteros.</translation>
        </message>
        <message>
            <source>The counts line of '%1' reads '%2'; an Adjust file gives five counts: distances, angles, azimuths, control stations and total stations.</source>
            <translation>La línea de recuentos de '%1' dice '%2'; un archivo Adjust da cinco recuentos: distancias, ángulos, acimuts, estaciones de control y total de estaciones.</translation>
        </message>
        <message>
            <source>The coverage of a geoid model is not in order: its south bound must lie below its north bound, and its west bound west of its east. Check the bounds the grid declares.</source>
            <translation>La cobertura de un modelo geoidal no está en orden: su límite sur debe estar por debajo del límite norte, y su límite oeste al oeste del este. Compruebe los límites que declara la malla.</translation>
        </message>
        <message>
            <source>The cross-covariance given has shape %1; it must be %2.</source>
            <translation>La covarianza cruzada indicada tiene forma %1; debe ser %2.</translation>
        </message>
        <message>
            <source>The database behind %1 does not have the PostGIS extension. A database administrator enables it once, with: CREATE EXTENSION postgis</source>
            <translation>La base de datos detrás de %1 no tiene la extensión PostGIS. Un administrador la habilita una vez, con: CREATE EXTENSION postgis</translation>
        </message>
        <message>
            <source>The datum '%1' needs a plan (east and north) and these solutions have none. Use the translation datum for heights.</source>
            <translation>El datum '%1' necesita planimetría (este y norte) y estas soluciones no la tienen. Use el datum de traslación para alturas.</translation>
        </message>
        <message>
            <source>The datum constraints do not remove the network's remaining freedom (%1 constraint(s) applied). Check that the stations defining the datum are enough to fix it.</source>
            <translation>Las constricciones de datum no eliminan la libertad restante de la red (%1 constricción(es) aplicada(s)). Compruebe que las estaciones que definen el datum bastan para fijarlo.</translation>
        </message>
        <message>
            <source>The default standard deviation for %1 is %2; it cannot be negative. Correct it in Global Settings, under Stochastic model.</source>
            <translation>La desviación estándar por defecto para %1 es %2; no puede ser negativa. Corríjala en las Configuraciones Globales, en Modelo estocástico.</translation>
        </message>
        <message>
            <source>The degree of the drift polynomial must be 1 or more; %1 was given.</source>
            <translation>El grado del polinomio de deriva debe ser 1 o más; se dio %1.</translation>
        </message>
        <message>
            <source>The design cannot be evaluated: %1</source>
            <translation>El diseño no puede evaluarse: %1</translation>
        </message>
        <message>
            <source>The design has no observation '%1'.</source>
            <translation>El diseño no tiene la observación '%1'.</translation>
        </message>
        <message>
            <source>The design has no redundancy, so nothing in it can be checked. A blunder anywhere would be invisible and would pass into the coordinates unaltered.</source>
            <translation>El diseño no tiene redundancia, así que nada en él puede comprobarse. Un error grosero en cualquier lugar sería invisible y pasaría inalterado a las coordenadas.</translation>
        </message>
        <message>
            <source>The design has no station '%1'.</source>
            <translation>El diseño no tiene la estación '%1'.</translation>
        </message>
        <message>
            <source>The design has no stations yet; add one to begin.</source>
            <translation>El diseño aún no tiene estaciones; añada una para empezar.</translation>
        </message>
        <message>
            <source>The design has stations but no planned observations, so there is nothing to evaluate. Connect two stations to begin.</source>
            <translation>El diseño tiene estaciones pero ninguna observación planificada, así que no hay nada que evaluar. Una dos estaciones para empezar.</translation>
        </message>
        <message>
            <source>The direction '%1' belongs to no setup or direction set, so it has no orientation unknown and would be adjusted as an absolute azimuth. Give it its setup.</source>
            <translation>La dirección '%1' no pertenece a ningún estacionamiento ni serie de direcciones, por lo que no tiene incógnita de orientación y se ajustaría como un acimut absoluto. Dele su estacionamiento.</translation>
        </message>
        <message>
            <source>The distance of the leg %1 is in %2; give it in metres.</source>
            <translation>La distancia del lado %1 está en %2; indíquela en metros.</translation>
        </message>
        <message>
            <source>The download of %1 from %2 produced no file. Run the installation again.</source>
            <translation>La descarga de %1 desde %2 no produjo ningún archivo. Vuelva a ejecutar la instalación.</translation>
        </message>
        <message>
            <source>The download service '%1' has a user name, password or token in a URL. Credentials are never written into a URL, a setting or a log: remove it, and name a QGIS authentication configuration in the service's 'authcfg' instead.</source>
            <translation>El servicio de descarga '%1' tiene un nombre de usuario, contraseña o token en una URL. Las credenciales nunca se escriben en una URL, una configuración o un registro: elimínelo y, en su lugar, indique una configuración de autenticación de QGIS en el 'authcfg' del servicio.</translation>
        </message>
        <message>
            <source>The download service '%1' has templates for products GeoComp does not know: %2. Keys are a product and a latency, such as 'orbit/final', 'orbit/rapid' or 'gps_navigation/broadcast'.</source>
            <translation>El servicio de descarga '%1' tiene plantillas para productos que GeoComp no conoce: %2. Las claves son un producto y una latencia, como 'orbit/final', 'orbit/rapid' o 'gps_navigation/broadcast'.</translation>
        </message>
        <message>
            <source>The download service '%1' uses the URL scheme '%2'; use https, http or file.</source>
            <translation>El servicio de descarga '%1' usa el esquema de URL '%2'; use https, http o file.</translation>
        </message>
        <message>
            <source>The download service id '%1' is empty or is the id of a service GeoComp ships. Give the service an id of its own.</source>
            <translation>El id de servicio de descarga '%1' está vacío o es el id de un servicio incluido en GeoComp. Dé al servicio un id propio.</translation>
        </message>
        <message>
            <source>The downloaded archive contains '%1', which would be written outside the installation folder. Nothing was extracted. Report this: the archive is not the one GeoComp expects.</source>
            <translation>El archivo comprimido descargado contiene '%1', que se escribiría fuera de la carpeta de instalación. No se extrajo nada. Infórmelo: el archivo comprimido no es el que GeoComp espera.</translation>
        </message>
        <message>
            <source>The downloaded archive contains a link, '%1', where only programs were expected. Nothing was extracted. Report this: the archive is not the one GeoComp expects.</source>
            <translation>El archivo comprimido descargado contiene un enlace, '%1', donde solo se esperaban programas. No se extrajo nada. Infórmelo: el archivo comprimido no es el que GeoComp espera.</translation>
        </message>
        <message>
            <source>The downloaded archive does not contain %1. The engine's release has probably changed shape, and GeoComp needs updating; meanwhile install it yourself and give its path in Global Settings.</source>
            <translation>El archivo comprimido descargado no contiene %1. La publicación del motor probablemente cambió de forma y GeoComp necesita actualizarse; mientras tanto, instálelo usted mismo e indique su ruta en Configuraciones Globales.</translation>
        </message>
        <message>
            <source>The downloaded archive is not the one GeoComp was tested with: its SHA-256 is %1, and GeoComp expects %2. It was deleted and nothing was installed. Run the installation again; if it happens again, report it rather than working around it.</source>
            <translation>El archivo comprimido descargado no es aquel con el que se probó GeoComp: su SHA-256 es %1 y GeoComp espera %2. Se eliminó y no se instaló nada. Vuelva a ejecutar la instalación; si vuelve a ocurrir, infórmelo en lugar de sortearlo.</translation>
        </message>
        <message>
            <source>The downloaded archive puts the engine's programs in several folders (%1); GeoComp runs them from one. Install the engine yourself and give its path in Global Settings.</source>
            <translation>El archivo comprimido descargado coloca los programas del motor en varias carpetas (%1); GeoComp los ejecuta desde una sola. Instale el motor usted mismo e indique su ruta en Configuraciones Globales.</translation>
        </message>
        <message>
            <source>The drift model has occupations and elapsed times in different numbers (%1); each occupation needs one elapsed time.</source>
            <translation>El modelo de deriva tiene ocupaciones y tiempos transcurridos en números distintos (%1); cada ocupación necesita un tiempo transcurrido.</translation>
        </message>
        <message>
            <source>The drift of session '%1' cannot be estimated with the station values: no station was read again at enough different times for a degree-%2 drift. Re-occupy a station in that session, lower the degree, or split the session.</source>
            <translation>La deriva de la sesión '%1' no puede estimarse junto con los valores de las estaciones: ninguna estación se volvió a leer en suficientes instantes distintos para una deriva de grado %2. Reocupe una estación en esa sesión, reduzca el grado o divida la sesión.</translation>
        </message>
        <message>
            <source>The drift time scale must be a positive number of seconds; %1 was given.</source>
            <translation>La escala de tiempo de la deriva debe ser un número positivo de segundos; se dio %1.</translation>
        </message>
        <message>
            <source>The drift time scale of the gravity observation '%1' must be a positive number of seconds; %2 was given.</source>
            <translation>La escala de tiempo de la deriva de la observación gravimétrica '%1' debe ser un número positivo de segundos; se dio %2.</translation>
        </message>
        <message>
            <source>The elevation mask must be at least 0 and less than 90 degrees; %1 was given.</source>
            <translation>La máscara de elevación debe ser de al menos 0 y menos de 90 grados; se dio %1.</translation>
        </message>
        <message>
            <source>The ellipse exaggeration must be a positive, finite factor; %1 was given. Every drawn result states the factor it was drawn with.</source>
            <translation>La exageración de las elipses debe ser un factor positivo y finito; se dio %1. Todo resultado dibujado indica el factor con que se dibujó.</translation>
        </message>
        <message>
            <source>The ellipse size, as a fraction of the map extent, must be above 0 and at most 1; %1 was given.</source>
            <translation>El tamaño de la elipse, como fracción de la extensión del mapa, debe ser mayor que 0 y como máximo 1; se dio %1.</translation>
        </message>
        <message>
            <source>The ellipsoid '%1' has a semi-major axis of %2; it must be positive.</source>
            <translation>El elipsoide '%1' tiene un semieje mayor de %2; debe ser positivo.</translation>
        </message>
        <message>
            <source>The ellipsoid '%1' has an inverse flattening of %2; it must be greater than 1, and a sphere's is infinite.</source>
            <translation>El elipsoide '%1' tiene un achatamiento inverso de %2; debe ser mayor que 1, y el de una esfera es infinito.</translation>
        </message>
        <message>
            <source>The engine could not be downloaded from %1 (HTTP status %2: %3). Check the network and QGIS's proxy settings, then run the installation again.</source>
            <translation>No se pudo descargar el motor desde %1 (estado HTTP %2: %3). Compruebe la red y la configuración de proxy de QGIS y vuelva a ejecutar la instalación.</translation>
        </message>
        <message>
            <source>The epoch %1 is not a finite decimal year; give one such as 2024.5.</source>
            <translation>La época %1 no es un año decimal finito; indique una como 2024.5.</translation>
        </message>
        <message>
            <source>The exaggeration factor %1 is not finite; an infinite factor gives the ellipses no size.</source>
            <translation>El factor de exageración %1 no es finito; un factor infinito no da tamaño a las elipses.</translation>
        </message>
        <message>
            <source>The face pair to %1 implies a horizontal collimation of %2 arcsec, beyond the %3 arcsec tolerance. The pair still cancels it; a value this large means the instrument needs adjustment, or the pointings were not to the same target.</source>
            <translation>El par de círculo directo e inverso hacia %1 implica una colimación horizontal de %2 segundos de arco, más allá de la tolerancia de %3 segundos de arco. El par todavía la cancela; un valor tan grande significa que el instrumento necesita ajuste, o que las punterías no fueron al mismo objetivo.</translation>
        </message>
        <message>
            <source>The face pair to %1 implies a vertical index error of %2 arcsec, beyond the %3 arcsec tolerance.</source>
            <translation>El par de círculo directo e inverso hacia %1 implica un error de índice vertical de %2 segundos de arco, más allá de la tolerancia de %3 segundos de arco.</translation>
        </message>
        <message>
            <source>The field '%1' has neither a source column nor a constant value. Choose a column, or give a value for every row.</source>
            <translation>El campo '%1' no tiene columna de origen ni valor constante. Elija una columna, o indique un valor para todas las filas.</translation>
        </message>
        <message>
            <source>The field book '%1' could not be read. Choose an existing, readable CSV or .xlsx file.</source>
            <translation>La libreta de campo '%1' no se pudo leer. Elija un archivo CSV o .xlsx existente y legible.</translation>
        </message>
        <message>
            <source>The field mapping has no name. Give it one: a mapping is saved and reused by its name.</source>
            <translation>La asignación de campos no tiene nombre. Póngale uno: una asignación se guarda y se reutiliza por su nombre.</translation>
        </message>
        <message>
            <source>The field mapping supplies no column for %1, which every import needs: at least the station and the two angles. Give a mapping that names them, or a field book whose header does.</source>
            <translation>La asignación de campos no proporciona columna para %1, que toda importación necesita: al menos la estación y los dos ángulos. Proporcione una asignación que los nombre, o una libreta de campo cuyo encabezado los nombre.</translation>
        </message>
        <message>
            <source>The files for DynAdjust cannot be written without an explicit reference frame and epoch, and one or both are missing. GeoComp will not guess either. Set them on the run or record them on the network.</source>
            <translation>Los archivos para DynAdjust no pueden escribirse sin un marco de referencia y una época explícitos, y falta uno de ellos o ambos. GeoComp no adivina ninguno. Defínalos en la ejecución o regístrelos en la red.</translation>
        </message>
        <message>
            <source>The frames %1 are related only at epoch %2, and the second solution is at another. Carrying a position between epochs along a velocity is exactly the motion being measured, so GeoComp will not do it here. Give both epochs in frames related at every epoch (the ITRFs), or in the same frame.</source>
            <translation>Los marcos %1 se relacionan solo en la época %2, y la segunda solución está en otra. Llevar una posición entre épocas a lo largo de una velocidad es exactamente el movimiento que se mide, por eso GeoComp no lo hace aquí. Indique ambas épocas en marcos relacionados en cualquier época (los ITRF), o en el mismo marco.</translation>
        </message>
        <message>
            <source>The free datum of '%1' names different components for different stations (%2); an inner constraint names the same components for every station.</source>
            <translation>El datum libre de '%1' nombra componentes distintas para estaciones distintas (%2); una restricción interna nombra las mismas componentes para todas las estaciones.</translation>
        </message>
        <message>
            <source>The geoid grid '%1' has %2 values where its header promises %3, for a grid of %4 by %5. The file is truncated or damaged.</source>
            <translation>La malla geoidal '%1' tiene %2 valores donde su encabezado promete %3, para una malla de %4 por %5. El archivo está truncado o dañado.</translation>
        </message>
        <message>
            <source>The geoid grid '%1' has cells without data (value %2). Such a cell would be interpolated into a plausible-looking undulation, so the grid is refused. Use a grid that covers the network completely.</source>
            <translation>La malla del geoide '%1' tiene celdas sin datos (valor %2). Una celda así se interpolaría como una ondulación geoidal de apariencia plausible, por eso la malla se rechaza. Use una malla que cubra la red por completo.</translation>
        </message>
        <message>
            <source>The geoid grid '%1' is truncated: it has %2 bytes, and the format needs %3.</source>
            <translation>La malla del geoide '%1' está truncada: tiene %2 bytes, y el formato necesita %3.</translation>
        </message>
        <message>
            <source>The geoid model '%1' has a grid of shape %2; interpolation needs a two-dimensional grid of at least 2 by 2 nodes.</source>
            <translation>El modelo geoidal '%1' tiene una malla de forma %2; la interpolación necesita una malla bidimensional de al menos 2 por 2 nodos.</translation>
        </message>
        <message>
            <source>The geoid model '%1' has nodes without a value. A no-data value in the grid would be interpolated into a plausible-looking height; fill the grid, or use one that covers the area completely.</source>
            <translation>El modelo geoidal '%1' tiene nodos sin valor. Un valor sin dato en la malla se interpolaría en una altura de apariencia verosímil; complete la malla, o use una que cubra el área por completo.</translation>
        </message>
        <message>
            <source>The geoid model '%1' is named but its grid was not given, and the benchmarks mix height types (%2). A name records which model was used but cannot compute an undulation: give the geoid grid, or convert the heights first.</source>
            <translation>El modelo de geoide '%1' se nombra, pero no se dio su malla, y los puntos de referencia mezclan tipos de altura (%2). Un nombre registra qué modelo se usó, pero no calcula una ondulación: indique la malla del geoide, o convierta las alturas antes.</translation>
        </message>
        <message>
            <source>The geoid model '%1' states an accuracy of %2. A geoid model is not exact, and its uncertainty often limits a combined height solution; give its stated accuracy in metres, as a positive number.</source>
            <translation>El modelo geoidal '%1' declara una exactitud de %2. Un modelo geoidal no es exacto, y su incertidumbre a menudo limita una solución combinada de alturas; indique su exactitud declarada en metros, como un número positivo.</translation>
        </message>
        <message>
            <source>The gravimeter '%1' reads counter units and has no calibration table, without which a counter reading means nothing. Add the manufacturer's table to its profile.</source>
            <translation>El gravímetro '%1' lee unidades de contador y no tiene tabla de calibración, sin la cual una lectura de contador no significa nada. Añada la tabla del fabricante a su perfil.</translation>
        </message>
        <message>
            <source>The gravimeter '%1' reads gravity directly and has a calibration table too; converting twice would be a silent error. Remove the table, or mark the instrument as reading counter units.</source>
            <translation>El gravímetro '%1' lee gravedad directamente y tiene también una tabla de calibración; convertir dos veces sería un error silencioso. Elimine la tabla, o marque el instrumento como lector de unidades de contador.</translation>
        </message>
        <message>
            <source>The gravimeter's calibration table has %1 row(s); it needs at least two, since one row has no interval to interpolate over.</source>
            <translation>La tabla de calibración del gravímetro tiene %1 fila(s); necesita al menos dos, pues una fila no tiene intervalo sobre el que interpolar.</translation>
        </message>
        <message>
            <source>The gravimetric factor must be positive, typically 1.16; %1 was given.</source>
            <translation>El factor gravimétrico debe ser positivo, típicamente 1,16; se dio %1.</translation>
        </message>
        <message>
            <source>The gravity network has no readings, so there is nothing to adjust.</source>
            <translation>La red gravimétrica no tiene lecturas, por lo que no hay nada que ajustar.</translation>
        </message>
        <message>
            <source>The gravity observation '%1' has a drift term (%2) but not the times it depends on, so the drift cannot be evaluated. Build the gravity network from its readings, which records them.</source>
            <translation>La observación gravimétrica '%1' tiene un término de deriva (%2), pero no los tiempos de los que depende, por lo que la deriva no puede evaluarse. Construya la red gravimétrica a partir de sus lecturas, que los registran.</translation>
        </message>
        <message>
            <source>The gravity reading '%1' lacks an id, a station or a session; every reading needs all three.</source>
            <translation>La lectura gravimétrica '%1' no tiene id, estación o sesión; toda lectura necesita los tres.</translation>
        </message>
        <message>
            <source>The grid coordinate %1 could not be converted back to latitude and longitude; it lies outside the projection's domain.</source>
            <translation>La coordenada de cuadrícula %1 no pudo convertirse de vuelta a latitud y longitud; queda fuera del dominio de la proyección.</translation>
        </message>
        <message>
            <source>The header of '%1' never ends: there is no END OF HEADER record. The file is truncated, or is not RINEX.</source>
            <translation>El encabezado de '%1' nunca termina: no hay registro END OF HEADER. El archivo está truncado, o no es RINEX.</translation>
        </message>
        <message>
            <source>The header of the geoid grid '%1' does not describe a usable grid (%2): it needs at least 2 by 2 nodes and a positive spacing, in degrees.</source>
            <translation>El encabezado de la malla del geoide '%1' no describe una malla utilizable (%2): necesita al menos 2 por 2 nodos y un espaciado positivo, en grados.</translation>
        </message>
        <message>
            <source>The header of the geoid grid '%1' is not a complete ESRI ASCII header: it lacks %2.</source>
            <translation>El encabezado de la malla geoidal '%1' no es un encabezado ESRI ASCII completo: le falta %2.</translation>
        </message>
        <message>
            <source>The height difference '%1' does not say whether it is orthometric or ellipsoidal. Rebuild its network with the current GeoComp, which records it.</source>
            <translation>El desnivel '%1' no dice si es ortométrico o elipsoidal. Reconstruya su red con el GeoComp actual, que lo registra.</translation>
        </message>
        <message>
            <source>The height observation '%1' is %2; the geocentric adjustment takes ellipsoidal or orthometric heights.</source>
            <translation>La observación de altura '%1' es %2; el ajuste geocéntrico usa alturas elipsoidales u ortométricas.</translation>
        </message>
        <message>
            <source>The height of the benchmark '%1' is in %2; give it in metres.</source>
            <translation>La altura del punto de referencia '%1' está en %2; indíquela en metros.</translation>
        </message>
        <message>
            <source>The incomplete beta function is undefined for a = %1, b = %2, x = %3.</source>
            <translation>La función beta incompleta no está definida para a = %1, b = %2, x = %3.</translation>
        </message>
        <message>
            <source>The incomplete gamma function is undefined for a = %1, x = %2.</source>
            <translation>La función gamma incompleta no está definida para a = %1, x = %2.</translation>
        </message>
        <message>
            <source>The input '%1' holds GNSS observations (%2), which need a geocentric frame. Use a combination that includes the GNSS network.</source>
            <translation>La entrada '%1' contiene observaciones GNSS (%2), que necesitan un marco geocéntrico. Use una combinación que incluya la red GNSS.</translation>
        </message>
        <message>
            <source>The input '%1' holds a position (%2) but does not say what frame it is in. State the frame when the network is built -- for GNSS baselines, the frame of the base coordinates.</source>
            <translation>La entrada '%1' contiene una posición (%2) pero no dice en qué marco está. Indique el marco al construir la red -- para líneas base GNSS, el marco de las coordenadas de la base.</translation>
        </message>
        <message>
            <source>The input '%1' holds a position (%2) but not its epoch. GeoComp does not assume one: the frame moves, and the same coordinates at two epochs are two different places.</source>
            <translation>La entrada '%1' contiene una posición (%2) pero no su época. GeoComp no supone una: el marco se mueve, y las mismas coordenadas en dos épocas son dos lugares distintos.</translation>
        </message>
        <message>
            <source>The input '%1' holds the benchmark '%2' exactly. In a geocentric combination a benchmark's height holds h - N, and holding it exactly would make the geoid exact there. Give the benchmark its uncertainty (height±sigma) when adjusting the levelling network.</source>
            <translation>La entrada '%1' fija el banco de nivel '%2' exactamente. En una combinación geocéntrica, la altura de un banco de nivel fija h - N, y fijarla exactamente haría exacto el geoide allí. Dé al banco su incertidumbre (altura±sigma) al ajustar la red de nivelación.</translation>
        </message>
        <message>
            <source>The input '%1' holds the station '%2' in grid coordinates. In a geocentric combination a grid height is not the ellipsoidal height the frame holds. Hold the station through the GNSS input instead (Fixed stations), or leave it free in this one.</source>
            <translation>La entrada '%1' fija la estación '%2' en coordenadas de cuadrícula. En una combinación geocéntrica, una altura de cuadrícula no es la altura elipsoidal que fija el marco. Fije la estación mediante la entrada GNSS (Estaciones fijas) o déjela libre en esta.</translation>
        </message>
        <message>
            <source>The input '%1' is in %2, which GeoComp cannot transform from. Give it in ITRF2000 to ITRF2020 or SIRGAS 2000, or in a UTM or Transverse Mercator projection of one of them. Combining it untransformed would absorb a datum shift into the residuals.</source>
            <translation>La entrada '%1' está en %2, desde el cual GeoComp no puede transformar. Désela en ITRF2000 a ITRF2020 o SIRGAS 2000, o en una proyección UTM o Transversa de Mercator de uno de ellos. Combinarla sin transformar absorbería un cambio de datum en los residuos.</translation>
        </message>
        <message>
            <source>The inputs are in different coordinate reference systems (%1). A combination without GNSS is adjusted in the inputs' own system, so they must share one.</source>
            <translation>Las entradas están en sistemas de referencia de coordenadas distintos (%1). Una combinación sin GNSS se ajusta en el propio sistema de las entradas, así que deben compartir uno.</translation>
        </message>
        <message>
            <source>The inputs fall into %1 pieces that share no station, so they cannot be adjusted as one network. A combination is tied together by the stations the techniques have in common.</source>
            <translation>Las entradas se dividen en %1 partes que no comparten estación, así que no pueden ajustarse como una red. Una combinación se une por las estaciones que las técnicas tienen en común.</translation>
        </message>
        <message>
            <source>The instrument %1 applies its additive constant internally, so GeoComp did not apply it again.</source>
            <translation>El instrumento %1 aplica internamente su constante aditiva, así que GeoComp no la aplicó de nuevo.</translation>
        </message>
        <message>
            <source>The instrument profile '%1' gives a cyclic-error amplitude without its wavelength; the correction is periodic in the distance and means nothing without one.</source>
            <translation>El perfil de instrumento '%1' da una amplitud de error cíclico sin su longitud de onda; la corrección es periódica en la distancia y no significa nada sin ella.</translation>
        </message>
        <message>
            <source>The intersected target falls on the station '%1' that sights it. The target must be distinct from every station sighting it.</source>
            <translation>El objetivo de la intersección directa cae sobre la estación '%1' que lo visa. El objetivo debe ser distinto de toda estación que lo vise.</translation>
        </message>
        <message>
            <source>The intersection cannot determine the point: the sightings are nearly parallel, and rays that do not cross determine nothing however many there are. Sight it from a station at a wider angle.</source>
            <translation>La intersección directa no puede determinar el punto: las visuales son casi paralelas, y rayos que no se cruzan no determinan nada, por muchos que sean. Víselo desde una estación con un ángulo más abierto.</translation>
        </message>
        <message>
            <source>The intersection did not converge in %1 iterations. Check the azimuths for a blunder.</source>
            <translation>La intersección directa no convergió en %1 iteraciones. Compruebe los acimuts en busca de un error grosero.</translation>
        </message>
        <message>
            <source>The known points %1 are collinear, so they define no circle and cannot fix a resection between them.</source>
            <translation>Los puntos conocidos %1 son colineales, así que no definen ningún círculo y no pueden fijar una intersección inversa entre ellos.</translation>
        </message>
        <message>
            <source>The latitude %1 (radians) lies outside -90 to 90 degrees, so the tide cannot be computed. Check the station's position.</source>
            <translation>La latitud %1 (radianes) queda fuera de -90 a 90 grados, por lo que la marea no puede calcularse. Compruebe la posición de la estación.</translation>
        </message>
        <message>
            <source>The leg '%1' of a GNSS loop is in %2. A loop sums its legs, and local east, north and up differ from station to station, so every leg must be ECEF.</source>
            <translation>El lado '%1' de un circuito GNSS está en %2. Un circuito suma sus lados, y este, norte y arriba locales difieren de estación a estación, por eso todo lado debe ser ECEF.</translation>
        </message>
        <message>
            <source>The length of the levelling line '%1' is unknown, because it has no sight distances, and weighting by length needs it. Weight by setup count instead, or record the distances.</source>
            <translation>La longitud de la línea de nivelación '%1' es desconocida, porque no tiene distancias de visual, y la ponderación por longitud la necesita. Pondere por número de estacionamientos, o registre las distancias.</translation>
        </message>
        <message>
            <source>The level profile '%1' has no reading standard deviation, and GeoComp does not invent one: a fabricated weight corrupts every statistic computed from it. Give the profile its sigma_reading.</source>
            <translation>El perfil de nivel '%1' no tiene desviación estándar de lectura, y GeoComp no inventa una: un peso fabricado corrompe toda estadística calculada a partir de él. Indique el sigma_reading del perfil.</translation>
        </message>
        <message>
            <source>The levelling book has no data: it needs a header row and at least one row of readings.</source>
            <translation>La libreta de nivelación no tiene datos: necesita una fila de encabezado y al menos una fila de lecturas.</translation>
        </message>
        <message>
            <source>The levelling line '%1' breaks at setup '%2': its backsight is on %3, where %4 was expected, the first foresight of setup %5. A line advances through each setup's first foresight; the others are side shots.</source>
            <translation>La línea de nivelación '%1' se interrumpe en el estacionamiento '%2': su visual de espalda está en %3, donde se esperaba %4, la primera visual de frente del estacionamiento %5. Una línea avanza por la primera visual de frente de cada estacionamiento; las demás son puntos radiados.</translation>
        </message>
        <message>
            <source>The levelling line '%1' has a %2 of %3, which cannot weight it: a zero would give it no uncertainty and an infinite weight. Check its sight distances or setups.</source>
            <translation>La línea de nivelación '%1' tiene %2 de %3, lo que no puede ponderarla: un cero le daría incertidumbre nula y peso infinito. Compruebe sus distancias de visual o sus estacionamientos.</translation>
        </message>
        <message>
            <source>The levelling line '%1' has no setups. Check the book's line and setup columns.</source>
            <translation>La línea de nivelación '%1' no tiene estacionamientos. Compruebe las columnas de línea y de estacionamiento de la libreta.</translation>
        </message>
        <message>
            <source>The levelling network '%1' has no reduced lines, so there is nothing to adjust.</source>
            <translation>La red de nivelación '%1' no tiene líneas reducidas, por lo que no hay nada que ajustar.</translation>
        </message>
        <message>
            <source>The levelling network '%1' has no reduced setups, so there is nothing to adjust.</source>
            <translation>La red de nivelación '%1' no tiene estacionamientos reducidos, por lo que no hay nada que ajustar.</translation>
        </message>
        <message>
            <source>The library has no profile with the id '%1'.</source>
            <translation>La biblioteca no tiene ningún perfil con el id '%1'.</translation>
        </message>
        <message>
            <source>The line %1 accumulated %2 m of sight imbalance, beyond the %3 m its class permits. It is the accumulated figure, not the per-setup one, that multiplies the collimation error over a line.</source>
            <translation>La línea %1 acumuló %2 m de desequilibrio de visuales, más allá de los %3 m que permite su clase. Es el valor acumulado, no el de cada estacionamiento, el que multiplica el error de colimación a lo largo de una línea.</translation>
        </message>
        <message>
            <source>The line %1 is %2 m long, so a length-weighted standard deviation for it is almost zero, and its weight almost infinite.</source>
            <translation>La línea %1 tiene %2 m de longitud, así que una desviación estándar ponderada por la longitud es casi cero para ella, y su peso casi infinito.</translation>
        </message>
        <message>
            <source>The line %1 is exactly balanced, so the collimation error contributes neither a correction nor an uncertainty, whatever its value. This is what makes equal sights the preferred method.</source>
            <translation>La línea %1 está exactamente equilibrada, así que el error de colimación no aporta ni corrección ni incertidumbre, sea cual sea su valor. Eso es lo que hace de las visuales iguales el método preferente.</translation>
        </message>
        <message>
            <source>The line %1 recorded no sight distances, so its length is unknown. Length weighting and the k*sqrt(L) tolerance both need it, and will refuse rather than assume a length of zero.</source>
            <translation>La línea %1 no registró distancias de visual, así que su longitud es desconocida. La ponderación por longitud y la tolerancia k*sqrt(L) la necesitan, y rechazarán en lugar de asumir una longitud cero.</translation>
        </message>
        <message>
            <source>The logarithm of %1 is undefined; it needs a positive value.</source>
            <translation>El logaritmo de %1 no está definido; necesita un valor positivo.</translation>
        </message>
        <message>
            <source>The loop '%1' ends at %2 and does not return to %3, where it began. A loop must return to the station it began at.</source>
            <translation>El circuito '%1' termina en %2 y no vuelve a %3, donde empezó. Un circuito debe volver a la estación en la que empezó.</translation>
        </message>
        <message>
            <source>The loop '%1' has no lines. A loop is a sequence of levelling lines that returns to where it began.</source>
            <translation>El circuito '%1' no tiene líneas. Un circuito es una secuencia de líneas de nivelación que vuelve al punto en que empezó.</translation>
        </message>
        <message>
            <source>The loop '%1' is broken at line '%2', which joins %3 and does not continue from the line before it: expected a line starting or ending at %4.</source>
            <translation>El circuito '%1' está interrumpido en la línea '%2', que une %3 y no continúa desde la línea anterior: se esperaba una línea que empiece o termine en %4.</translation>
        </message>
        <message>
            <source>The map extent %1 has no area; it needs a positive width and height.</source>
            <translation>La extensión del mapa %1 no tiene área; necesita un ancho y un alto positivos.</translation>
        </message>
        <message>
            <source>The mapping '%1' does not show which book layout it is: it maps %2. Map station and sight for a book with one row per reading, or backsight_station and foresight_station for one row per setup.</source>
            <translation>La asignación '%1' no muestra cuál es el formato de la libreta: asigna %2. Asigne station y sight (estación y visual) para una libreta con una fila por lectura, o backsight_station y foresight_station para una fila por estacionamiento.</translation>
        </message>
        <message>
            <source>The mapping '%1' maps %2, and also needs %3.</source>
            <translation>La asignación '%1' asigna %2, y también necesita %3.</translation>
        </message>
        <message>
            <source>The mapping '%1' mixes the columns of two book layouts (%2). Map station and sight for a book with one row per reading, or backsight_station and foresight_station for one row per setup, not both.</source>
            <translation>La asignación '%1' mezcla columnas de dos formatos de libreta (%2). Asigne station y sight (estación y visual) para una libreta con una fila por lectura, o backsight_station y foresight_station para una fila por estacionamiento, no ambos.</translation>
        </message>
        <message>
            <source>The mapping expects a column '%1', which this file does not have. A mapping saved for one export layout does not fit another.</source>
            <translation>La asignación espera una columna '%1', que este archivo no tiene. Una asignación guardada para un formato de exportación no sirve para otro.</translation>
        </message>
        <message>
            <source>The mapping names %1, which GeoComp does not know as a field-book field. Expected %2.</source>
            <translation>La asignación nombra %1, que GeoComp no conoce como campo de libreta de campo. Se esperaba %2.</translation>
        </message>
        <message>
            <source>The mapping names %1, which GeoComp does not know as a levelling-book field. Expected %2.</source>
            <translation>La asignación nombra %1, que GeoComp no conoce como campo de libreta de nivelación. Se esperaba %2.</translation>
        </message>
        <message>
            <source>The network '%1' has no active observations, so there is nothing to adjust. Observations marked as rejected do not take part; re-activate the ones you want to use.</source>
            <translation>La red '%1' no tiene observaciones activas, por lo que no hay nada que ajustar. Las observaciones marcadas como rechazadas no participan; reactive las que desee utilizar.</translation>
        </message>
        <message>
            <source>The network '%1' has no stations, so DynAdjust has nothing to adjust. Choose a network document with its stations and observations.</source>
            <translation>La red '%1' no tiene estaciones, por lo que DynAdjust no tiene nada que ajustar. Elija un documento de red con sus estaciones y observaciones.</translation>
        </message>
        <message>
            <source>The network '%1' has orthometric heights, and DynAdjust cannot relate them to ellipsoidal heights without a geoid model. Give a geoid grid (NTv2) in the dialog, or a geoid undulation for each station.</source>
            <translation>La red '%1' tiene alturas ortométricas, y DynAdjust no puede relacionarlas con alturas elipsoidales sin un modelo de geoide. Indique una malla del geoide (NTv2) en el diálogo, o una ondulación geoidal para cada estación.</translation>
        </message>
        <message>
            <source>The network '%1' is not internally consistent: %2 observation(s) or cluster(s) name something it does not have, or a cluster's covariance does not fit its members. Run Inspect network to see each problem.</source>
            <translation>La red '%1' no es internamente consistente: %2 observación(es) o agrupamiento(s) nombran algo que no tiene, o la matriz de varianza-covarianza de un agrupamiento no corresponde a sus miembros. Ejecute Inspeccionar red para ver cada problema.</translation>
        </message>
        <message>
            <source>The network '%2' has two clusters with the id '%1'. Give each cluster its own id.</source>
            <translation>La red '%2' tiene dos agrupamientos con el id '%1'. Dé a cada agrupamiento su propio id.</translation>
        </message>
        <message>
            <source>The network '%2' has two observations with the id '%1'. Give each observation its own id.</source>
            <translation>La red '%2' tiene dos observaciones con el id '%1'. Dé a cada observación su propio id.</translation>
        </message>
        <message>
            <source>The network '%2' has two stations with the id '%1'. Give each station its own id, or merge the two.</source>
            <translation>La red '%2' tiene dos estaciones con el id '%1'. Dé a cada estación su propio id, o fusione las dos.</translation>
        </message>
        <message>
            <source>The network cannot be written as the Adjust file '%1': it has observations of type %2, and the format holds only horizontal distances and horizontal angles. Written without them, the file would be a different network.</source>
            <translation>La red no puede escribirse como el archivo Adjust '%1': tiene observaciones del tipo %2, y el formato solo contiene distancias horizontales y ángulos horizontales. Escrito sin ellas, el archivo sería una red distinta.</translation>
        </message>
        <message>
            <source>The network does not determine %1 combination(s) of unknowns: %2. Add observations that fix them, or define the datum with inner or minimum constraints so the remaining freedom is removed deliberately.</source>
            <translation>La red no determina %1 combinación(es) de incógnitas: %2. Añada observaciones que las fijen, o defina el datum con constricciones internas o mínimas, de modo que la libertad restante se elimine deliberadamente.</translation>
        </message>
        <message>
            <source>The network falls into %1 disconnected parts. Each has its own datum, and they cannot be adjusted together.</source>
            <translation>La red se divide en %1 partes desconectadas. Cada una tiene su propio datum, y no pueden ajustarse juntas.</translation>
        </message>
        <message>
            <source>The network has no active observations, so there is nothing to adjust.</source>
            <translation>La red no tiene observaciones activas, así que no hay nada que ajustar.</translation>
        </message>
        <message>
            <source>The network was weighted by %1, replacing each line's propagated reading uncertainty.</source>
            <translation>La red se ponderó por %1, sustituyendo la incertidumbre de lectura propagada de cada línea.</translation>
        </message>
        <message>
            <source>The network was weighted by each line's propagated reading uncertainty, since no k*sqrt(L) or k*sqrt(n) model was configured. That figure knows nothing of refraction, staff calibration or a tripod settling, so expect a variance factor above one.</source>
            <translation>La red se ponderó por la incertidumbre de lectura propagada de cada línea, ya que no se configuró ningún modelo k*sqrt(L) o k*sqrt(n). Ese valor no sabe nada de refracción, calibración de miras ni del asentamiento de un trípode, así que espere un factor de varianza mayor que uno.</translation>
        </message>
        <message>
            <source>The normal orthometric correction for this section is %1 mm, at mean latitude %2 degrees and mean height %3 m. This is the normal correction, from the ellipsoid's gravity field; the rigorous one needs observed gravity along the line.</source>
            <translation>La corrección ortométrica normal de esta sección es %1 mm, en la latitud media de %2 grados y la altura media de %3 m. Esta es la corrección normal, a partir del campo de gravedad del elipsoide; la rigurosa necesita la gravedad observada a lo largo de la línea.</translation>
        </message>
        <message>
            <source>The normal orthometric correction for this section is %1 mm, below the %2 mm at which it could matter to any levelling. Applying it changes nothing.</source>
            <translation>La corrección ortométrica normal de esta sección es %1 mm, por debajo de los %2 mm a partir de los cuales podría importar a alguna nivelación. Aplicarla no cambia nada.</translation>
        </message>
        <message>
            <source>The number of rows to skip cannot be negative (%1).</source>
            <translation>El número de filas a omitir no puede ser negativo (%1).</translation>
        </message>
        <message>
            <source>The number of sets must be at least 1; %1 was given.</source>
            <translation>El número de series debe ser al menos 1; se dio %1.</translation>
        </message>
        <message>
            <source>The number of setups for the level '%1' cannot be negative; %2 was given.</source>
            <translation>El número de estacionamientos del nivel '%1' no puede ser negativo; se dio %2.</translation>
        </message>
        <message>
            <source>The observation %1 cannot be deleted: the stored solutions %2 were computed from it (FR-135). Supersede those solutions first, or keep the observation.</source>
            <translation>La observación %1 no se puede eliminar: las soluciones almacenadas %2 se calcularon a partir de ella (FR-135). Reemplace antes esas soluciones, o conserve la observación.</translation>
        </message>
        <message>
            <source>The observation %1 is a %2, which GeoComp's own adjustment does not yet implement.</source>
            <translation>La observación %1 es un(a) %2, que el ajuste propio de GeoComp aún no implementa.</translation>
        </message>
        <message>
            <source>The observation %1 names the cluster %2, which the network does not have.</source>
            <translation>La observación %1 nombra el agrupamiento %2, que la red no tiene.</translation>
        </message>
        <message>
            <source>The observation %1 names the station %2, which the network does not have.</source>
            <translation>La observación %1 nombra la estación %2, que la red no tiene.</translation>
        </message>
        <message>
            <source>The observation %1, a %2, cannot contribute to a %3D adjustment.</source>
            <translation>La observación %1, un(a) %2, no puede contribuir a un ajuste %3D.</translation>
        </message>
        <message>
            <source>The observation '%1' between %2 is a sight of zero length or exactly vertical, which determines no direction. Check the two stations' coordinates.</source>
            <translation>La observación '%1' entre %2 es una visual de longitud cero o exactamente vertical, que no determina ninguna dirección. Compruebe las coordenadas de las dos estaciones.</translation>
        </message>
        <message>
            <source>The observation '%1' has %2 components, where one was expected.</source>
            <translation>La observación '%1' tiene %2 componentes, donde se esperaba una.</translation>
        </message>
        <message>
            <source>The observation '%1' is a %2 and gives %3, which that type does not use. GeoComp would ignore it, and an ignored instrument height is a metre-scale error that looks like nothing. Remove it, or use %4.</source>
            <translation>La observación '%1' es un(a) %2 e indica %3, que ese tipo no usa. GeoComp lo ignoraría, y una altura del instrumento ignorada es un error del orden del metro que no parece nada. Elimínelo, o use %4.</translation>
        </message>
        <message>
            <source>The observation '%1' is a %2 and joins %3 station(s), where that type joins %4.</source>
            <translation>La observación '%1' es un(a) %2 y une %3 estación(es), donde ese tipo une %4.</translation>
        </message>
        <message>
            <source>The observation '%1' is a %2 with %3 value(s), where that type has %4.</source>
            <translation>La observación '%1' es un(a) %2 con %3 valor(es), donde ese tipo tiene %4.</translation>
        </message>
        <message>
            <source>The observation '%1' is a %2, which the geocentric adjustment cannot use; it takes %3.</source>
            <translation>La observación '%1' es un(a) %2, que el ajuste geocéntrico no puede usar; usa %3.</translation>
        </message>
        <message>
            <source>The observation '%1' is a %2, whose components are correlated, but it belongs to no cluster. Treating them as independent falsifies the adjustment; give it the cluster that carries its covariance.</source>
            <translation>La observación '%1' es un(a) %2, cuyas componentes están correlacionadas, pero no pertenece a ningún agrupamiento. Tratarlas como independientes falsea el ajuste; dele el agrupamiento que lleva su matriz de varianza-covarianza.</translation>
        </message>
        <message>
            <source>The observation '%1' is active but carries a rejection record. Mark it rejected, or remove the record.</source>
            <translation>La observación '%1' está activa, pero lleva un registro de rechazo. Márquela como rechazada, o elimine el registro.</translation>
        </message>
        <message>
            <source>The observation '%1' states a standard deviation of %2; it cannot be negative.</source>
            <translation>La observación '%1' declara una desviación estándar de %2; no puede ser negativa.</translation>
        </message>
        <message>
            <source>The occupied station lies on the danger circle through %1: every point on that circle sees the three in the same directions, so they do not determine a position. Add a fourth point off the circle, or a distance.</source>
            <translation>La estación ocupada está sobre el círculo peligroso que pasa por %1: todo punto de ese círculo ve los tres en las mismas direcciones, así que no determinan una posición. Añada un cuarto punto fuera del círculo, o una distancia.</translation>
        </message>
        <message>
            <source>The orthometric correction needs an approximate height for every station, and these have none: %1. Connect them to a benchmark, or turn the correction off.</source>
            <translation>La corrección ortométrica necesita una altura aproximada para cada estación, y estas no tienen ninguna: %1. Conéctelas a un punto de referencia, o desactive la corrección.</translation>
        </message>
        <message>
            <source>The orthometric correction needs the latitude of every station a line ends at, and these have no position in the station positions layer: %1. Add them, check the station id field, or turn the correction off.</source>
            <translation>La corrección ortométrica necesita la latitud de cada estación donde termina una línea, y estas no tienen posición en la capa de posiciones de las estaciones: %1. Añádalas, revise el campo del identificador de la estación, o desactive la corrección.</translation>
        </message>
        <message>
            <source>The path given for %1 does not exist: '%2'. GeoComp does not fall back to another copy of the program when one is named. Correct the path in Global Settings, under Paths and engines, or clear it to use GeoComp's installation or the system path.</source>
            <translation>La ruta indicada para %1 no existe: '%2'. Cuando se indica una, GeoComp no recurre a otra copia del programa. Corrija la ruta en Configuraciones Globales, en Rutas y motores, o bórrela para usar la instalación de GeoComp o la ruta del sistema.</translation>
        </message>
        <message>
            <source>The planned network '%1' contains no observations, so there is no design to evaluate. Add the observations you intend to make, with their assumed precisions.</source>
            <translation>La red planificada '%1' no contiene observaciones, por lo que no hay diseño que evaluar. Añada las observaciones que pretende realizar, con sus precisiones supuestas.</translation>
        </message>
        <message>
            <source>The planned observation %1 would be uncheckable: no blunder in it could be detected at all.</source>
            <translation>La observación planificada %1 sería incomprobable: ningún error grosero en ella podría detectarse.</translation>
        </message>
        <message>
            <source>The point %1 lies too near the centre of the Earth to have geodetic coordinates. Check its cartesian coordinates.</source>
            <translation>El punto %1 queda demasiado cerca del centro de la Tierra para tener coordenadas geodésicas. Compruebe sus coordenadas cartesianas.</translation>
        </message>
        <message>
            <source>The point at latitude, longitude %2 lies outside the coverage of the geoid model '%1', which spans latitudes %3 to %4 and longitudes %5 to %6. A geoid model quoted beyond its coverage gives a confidently wrong height; use a model that covers the point.</source>
            <translation>El punto en latitud, longitud %2 queda fuera de la cobertura del modelo geoidal '%1', que abarca las latitudes de %3 a %4 y las longitudes de %5 a %6. Un modelo geoidal usado fuera de su cobertura da una altura errónea con toda confianza; use un modelo que cubra el punto.</translation>
        </message>
        <message>
            <source>The point is %1 degrees from the central meridian of %2, beyond where the projection is accurate; GeoComp refuses rather than give a coordinate with an error nobody can see. Use a projection centred nearer the point.</source>
            <translation>El punto está a %1 grados del meridiano central de %2, más allá de donde la proyección es exacta; GeoComp lo rechaza en lugar de dar una coordenada con un error que nadie ve. Use una proyección centrada más cerca del punto.</translation>
        </message>
        <message>
            <source>The point scale factor is in %1; it is a dimensionless number.</source>
            <translation>El factor de escala puntual está en %1; es un número adimensional.</translation>
        </message>
        <message>
            <source>The point scale factor is undefined at latitude %1 degrees, where a parallel has no length.</source>
            <translation>El factor de escala puntual no está definido en la latitud %1 grados, donde un paralelo no tiene longitud.</translation>
        </message>
        <message>
            <source>The pointing to %1 was rejected during pre-processing and is not used here.</source>
            <translation>La puntería hacia %1 se rechazó en el preprocesamiento y no se usa aquí.</translation>
        </message>
        <message>
            <source>The pointing to %1 was taken on one face only, so the instrumental errors were corrected from the profile rather than cancelled. Their uncertainties are included in the result.</source>
            <translation>La puntería hacia %1 se hizo en un solo círculo, así que los errores instrumentales se corrigieron con el perfil en lugar de cancelarse. Sus incertidumbres están incluidas en el resultado.</translation>
        </message>
        <message>
            <source>The prepared input file '%1' is no longer in '%2'. Edit the input files in place; do not rename or remove them.</source>
            <translation>El archivo de entrada preparado '%1' ya no está en '%2'. Edite los archivos de entrada en su sitio; no los renombre ni los elimine.</translation>
        </message>
        <message>
            <source>The prepared job in '%1' could not be read: %2. It is the file GeoComp wrote beside the input; prepare the job again rather than editing it.</source>
            <translation>No se pudo leer el trabajo preparado en '%1': %2. Es el archivo que GeoComp escribió junto a la entrada; prepare el trabajo de nuevo en vez de editarlo.</translation>
        </message>
        <message>
            <source>The prepared measurement file '%1' now holds %2 measurements where GeoComp wrote %3. The result is matched to the network measurement by measurement, so measurements cannot be added or removed; to leave one out, set its Ignore to *.</source>
            <translation>El archivo de mediciones preparado '%1' contiene ahora %2 mediciones, donde GeoComp escribió %3. El resultado se asocia a la red medición por medición, así que no se pueden añadir ni eliminar mediciones; para dejar una fuera, marque su Ignore con *.</translation>
        </message>
        <message>
            <source>The processing window %1 does not overlap the session '%2', which observed %3. Give a window inside the observations; both are in GPS time.</source>
            <translation>La ventana de procesamiento %1 no se superpone a la sesión '%2', que observó %3. Dé una ventana dentro de las observaciones; ambas están en tiempo GPS.</translation>
        </message>
        <message>
            <source>The processing window %1 has a time without a time zone. Give both ends in UTC.</source>
            <translation>La ventana de procesamiento %1 tiene una hora sin zona horaria. Dé ambos extremos en UTC.</translation>
        </message>
        <message>
            <source>The processing window ends (%2) before it starts (%1). Give a window whose end is after its start.</source>
            <translation>La ventana de procesamiento termina (%2) antes de empezar (%1). Dé una ventana cuyo fin sea posterior al inicio.</translation>
        </message>
        <message>
            <source>The product %1 could not be decompressed (%2). It was not used; run again to download it afresh.</source>
            <translation>El producto %1 no pudo descomprimirse (%2). No se usó; ejecute de nuevo para descargarlo otra vez.</translation>
        </message>
        <message>
            <source>The product %1 is compressed with Unix compress (.Z), which GeoComp does not read. Point the service at the .gz or uncompressed file.</source>
            <translation>El producto %1 está comprimido con Unix compress (.Z), que GeoComp no lee. Apunte el servicio al archivo .gz o sin comprimir.</translation>
        </message>
        <message>
            <source>The product %1 is not available from %2. A recent day's final orbit is published about two weeks later; allow rapid orbits in Global Settings → GNSS, add another download service, or place the file in the product directory.</source>
            <translation>El producto %1 no está disponible en %2. La órbita final de un día reciente se publica unas dos semanas después; permita órbitas rápidas en Configuración Global → GNSS, añada otro servicio de descarga, o coloque el archivo en el directorio de productos.</translation>
        </message>
        <message>
            <source>The project '%1' was written with storage schema %2, and this version of GeoComp reads up to schema %3. Reading a schema it does not understand would corrupt the project; update GeoComp to open it.</source>
            <translation>El proyecto '%1' se escribió con el esquema de almacenamiento %2, y esta versión de GeoComp lee hasta el esquema %3. Leer un esquema que no entiende corrompería el proyecto; actualice GeoComp para abrirlo.</translation>
        </message>
        <message>
            <source>The project '%2' already has a GNSS session '%1'. Give each session its own id.</source>
            <translation>El proyecto '%2' ya tiene una sesión GNSS '%1'. Dé a cada sesión su propio id.</translation>
        </message>
        <message>
            <source>The project '%2' already has a campaign '%1'. Give the new campaign another id, or replace the existing one.</source>
            <translation>El proyecto '%2' ya tiene una campaña '%1'. Dé otro id a la nueva campaña, o sustituya la existente.</translation>
        </message>
        <message>
            <source>The project '%2' already has a network '%1'. Give the new network another id, or replace the existing one.</source>
            <translation>El proyecto '%2' ya tiene una red '%1'. Dé otro id a la nueva red, o sustituya la existente.</translation>
        </message>
        <message>
            <source>The project store %1 holds no project yet. Save a network or a solution to it first.</source>
            <translation>El repositorio de proyecto %1 aún no contiene ningún proyecto. Guarde en él una red o una solución primero.</translation>
        </message>
        <message>
            <source>The project store %1 records schema version %2, which no GeoComp wrote. It may be damaged; restore it from a backup.</source>
            <translation>El repositorio de proyecto %1 registra la versión de esquema %2, que ningún GeoComp escribió. Puede estar dañado; restáurelo desde una copia de seguridad.</translation>
        </message>
        <message>
            <source>The project store %1 uses schema %2, older than this version's %3. It can be migrated, after a backup is taken.</source>
            <translation>El repositorio de proyecto %1 usa el esquema %2, más antiguo que el %3 de esta versión. Se puede migrar, tras una copia de seguridad.</translation>
        </message>
        <message>
            <source>The project store %1 was written by a newer GeoComp (schema %2; this version reads up to %3). Update the plugin to open it: GeoComp does not read a schema it does not understand, because what it cannot see would be lost on the next save.</source>
            <translation>El repositorio de proyecto %1 lo escribió un GeoComp más reciente (esquema %2; esta versión lee hasta el %3). Actualice el complemento para abrirlo: GeoComp no lee un esquema que no entiende, porque lo que no puede ver se perdería al guardar.</translation>
        </message>
        <message>
            <source>The rays to %1 are close to parallel: the error ellipse is %2 times longer than it is wide, so the point is poorly determined along one direction however precise the individual sightings are.</source>
            <translation>Los rayos hacia %1 son casi paralelos: la elipse de error es %2 veces más larga que ancha, así que el punto está mal determinado a lo largo de una dirección, por precisas que sean las visuales individuales.</translation>
        </message>
        <message>
            <source>The reading '%1' appears twice. Remove the duplicate line and run again.</source>
            <translation>La lectura '%1' aparece dos veces. Elimine la línea duplicada y ejecute de nuevo.</translation>
        </message>
        <message>
            <source>The reading on '%1' carries no uncertainty; every reading needs one.</source>
            <translation>La lectura en '%1' no tiene incertidumbre; toda lectura necesita una.</translation>
        </message>
        <message>
            <source>The reading standard deviation of the gravimeter '%1' is %2; it cannot be negative.</source>
            <translation>La desviación estándar de lectura del gravímetro '%1' es %2; no puede ser negativa.</translation>
        </message>
        <message>
            <source>The readings name the gravimeter '%1', which the profile library does not hold: expected %2. Add a profile with that id, carrying the instrument's calibration.</source>
            <translation>Las lecturas indican el gravímetro '%1', que la biblioteca de perfiles no contiene: se esperaba %2. Añada un perfil con ese identificador, con la calibración del instrumento.</translation>
        </message>
        <message>
            <source>The readings of '%1' state no precision and its profile gives none. GeoComp does not invent a weight: set a reading precision floor, or a nominal precision in the gravimeter profile.</source>
            <translation>Las lecturas de '%1' no indican precisión y su perfil no proporciona ninguna. GeoComp no inventa un peso: defina un piso de precisión de las lecturas, o una precisión nominal en el perfil del gravímetro.</translation>
        </message>
        <message>
            <source>The reference block (%1) is too small to define the datum '%2'. Add reference stations, or choose a datum with fewer parameters.</source>
            <translation>El bloque de referencia (%1) es demasiado pequeño para definir el datum '%2'. Añada estaciones de referencia, o elija un datum con menos parámetros.</translation>
        </message>
        <message>
            <source>The reference block has moved: its congruency test gives %1 against a critical value of %2, and the localisation implicates %3. The analysis does not proceed on a block that has itself moved, because that motion would be spread over every other station. The stations that remain stable are %4. Check the implicated pillars, then analyse again with them among the object points.</source>
            <translation>El bloque de referencia se ha movido: su prueba de congruencia da %1 frente a un valor crítico de %2, y la localización implica a %3. El análisis no continúa sobre un bloque que se ha movido, porque ese movimiento se repartiría entre todas las demás estaciones. Las estaciones que permanecen estables son %4. Revise los pilares implicados y analice de nuevo con ellos entre los puntos objeto.</translation>
        </message>
        <message>
            <source>The reference station '%1' does not say which reference frame its coordinates are in; a coordinate without its frame is a number, not a position. Add the frame to the reference station database.</source>
            <translation>La estación de referencia '%1' no dice en qué marco de referencia están sus coordenadas; una coordenada sin su marco es un número, no una posición. Añada el marco a la base de datos de estaciones de referencia.</translation>
        </message>
        <message>
            <source>The reference station '%1' has %2 coordinates, where three geocentric components were expected.</source>
            <translation>La estación de referencia '%1' tiene %2 coordenadas, donde se esperaban tres componentes geocéntricas.</translation>
        </message>
        <message>
            <source>The reference station '%1' has no published velocity, and its coordinates must be moved to another epoch. A velocity taken as zero is a decimetre-scale assumption over a decade; give the velocity in the reference station database.</source>
            <translation>La estación de referencia '%1' no tiene velocidad publicada, y sus coordenadas deben llevarse a otra época. Una velocidad tomada como cero es una suposición del orden del decímetro a lo largo de una década; indique la velocidad en la base de datos de estaciones de referencia.</translation>
        </message>
        <message>
            <source>The reference station '%1' is published in %2, a different frame from the one this processing works in. Transform its coordinates first; GeoComp records the transformation it applies.</source>
            <translation>La estación de referencia '%1' se publica en %2, un marco de referencia distinto de aquel en que trabaja este procesamiento. Transforme primero sus coordenadas; GeoComp registra la transformación que aplica.</translation>
        </message>
        <message>
            <source>The reference station database '%1' could not be read: %2.</source>
            <translation>La base de datos de estaciones de referencia '%1' no se pudo leer: %2.</translation>
        </message>
        <message>
            <source>The reference station database '%1' does not exist. Set its location in Global Settings, under GNSS.</source>
            <translation>La base de datos de estaciones de referencia '%1' no existe. Defina su ubicación en las Configuraciones Globales, en GNSS.</translation>
        </message>
        <message>
            <source>The relative humidity must lie between 0 and 1; %1 was given.</source>
            <translation>La humedad relativa debe estar entre 0 y 1; se dio %1.</translation>
        </message>
        <message>
            <source>The report template %1 uses tokens GeoComp does not fill (%2); expected %3.</source>
            <translation>La plantilla de informe %1 usa marcadores que GeoComp no rellena (%2); se esperaba %3.</translation>
        </message>
        <message>
            <source>The resection cannot determine the station: its equations are singular, and the known points are not on a common circle with it. Check the directions for a blunder.</source>
            <translation>La intersección inversa no puede determinar la estación: sus ecuaciones son singulares, y los puntos conocidos no están en un círculo común con ella. Compruebe las direcciones en busca de un error grosero.</translation>
        </message>
        <message>
            <source>The resection did not converge in %1 iterations. Check the approximate coordinates, and the directions for a blunder.</source>
            <translation>La intersección inversa no convergió en %1 iteraciones. Compruebe las coordenadas aproximadas, y las direcciones en busca de un error grosero.</translation>
        </message>
        <message>
            <source>The resection sights %1, which have no known position. Every point sighted in a resection needs one.</source>
            <translation>La intersección inversa visa %1, que no tienen posición conocida. Todo punto visado en una intersección inversa necesita una.</translation>
        </message>
        <message>
            <source>The resection's station falls on the known point '%1' it sights. The occupied station must be distinct from every point sighted.</source>
            <translation>La estación de la intersección inversa cae sobre el punto conocido '%1' que visa. La estación ocupada debe ser distinta de todo punto visado.</translation>
        </message>
        <message>
            <source>The residuals cannot tell the variance-component groups %1 apart. Merge them, or fix the weights of one.</source>
            <translation>Los residuos no pueden distinguir los grupos de componentes de varianza %1. Únalos, o fije los pesos de uno de ellos.</translation>
        </message>
        <message>
            <source>The rounding of a printed covariance matrix was given as %1; it is half the place value of the last digit printed, which is positive. This is an internal error; please report it.</source>
            <translation>El redondeo de una matriz de varianza-covarianza impresa se dio como %1; es la mitad del valor posicional del último dígito impreso, que es positivo. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>The rover '%1' and the base '%2' did not observe at the same time: their sessions share no epoch. Choose a base station whose observations overlap the rover's.</source>
            <translation>El móvil '%1' y la base '%2' no observaron al mismo tiempo: sus sesiones no tienen ninguna época en común. Elija una estación base cuyas observaciones se superpongan a las del móvil.</translation>
        </message>
        <message>
            <source>The scale reference must be a positive radius, in the map's units; %1 was given.</source>
            <translation>La referencia de escala debe ser un radio positivo, en las unidades del mapa; se dio %1.</translation>
        </message>
        <message>
            <source>The second pair of a reciprocal crossing is reversed: its near reading is on %1, where %2 was expected. The second pair is observed from the far bank, so its near reading is onto the station the difference runs to.</source>
            <translation>El segundo par de una travesía recíproca está invertido: su lectura cercana está en %1, donde se esperaba %2. El segundo par se observa desde la orilla opuesta, así que su lectura cercana es hacia la estación a la que va el desnivel.</translation>
        </message>
        <message>
            <source>The section %1 is listed as read but has no reader. This is an internal error; please report it.</source>
            <translation>La sección %1 figura como leída, pero no tiene lector. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>The section %1 of '%2' holds %3. GeoComp reads none of the file rather than read it without that section: without one of its observations it would be a different example.</source>
            <translation>La sección %1 de '%2' contiene %3. GeoComp no lee nada del archivo en lugar de leerlo sin esa sección: sin una de sus observaciones, sería un ejemplo distinto.</translation>
        </message>
        <message>
            <source>The sensor height of the gravity reading '%1' is in %2; give it in metres.</source>
            <translation>La altura del sensor de la lectura gravimétrica '%1' está en %2; indíquela en metros.</translation>
        </message>
        <message>
            <source>The set number must be at least 1; %1 was given.</source>
            <translation>El número de serie debe ser al menos 1; se dio %1.</translation>
        </message>
        <message>
            <source>The setting %1 is %2, which is out of range; expected a whole number from 0 to %3. Correct it in Global Settings, under Interface.</source>
            <translation>La configuración %1 es %2, lo que está fuera de rango; se esperaba un número entero de 0 a %3. Corríjala en Configuraciones Globales, en Interfaz.</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be greater than %2 (received %3).</source>
            <translation>La configuración '%1' no puede ser mayor que %2 (se recibió %3).</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be less than %2 (received %3).</source>
            <translation>La configuración '%1' no puede ser menor que %2 (se recibió %3).</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be set at %2 scope; it can be set at %3.</source>
            <translation>La configuración '%1' no puede definirse en el ámbito %2; puede definirse en %3.</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be set to '%2'. Permitted values are: %3.</source>
            <translation>La configuración '%1' no puede establecerse en '%2'. Los valores permitidos son: %3.</translation>
        </message>
        <message>
            <source>The setting '%1' expects a value of type %2, but received %3. Correct it in Global Settings, or restore the default.</source>
            <translation>La configuración '%1' espera un valor de tipo %2, pero recibió %3. Corríjala en Configuraciones Globales o restaure el valor predeterminado.</translation>
        </message>
        <message>
            <source>The setting '%1' is a project setting, and no project is open. Open or create a GeoComp project first.</source>
            <translation>La configuración '%1' es una configuración de proyecto, y no hay ningún proyecto abierto. Abra o cree primero un proyecto de GeoComp.</translation>
        </message>
        <message>
            <source>The setup '%1' has no foresight: a backsight alone gives no height difference.</source>
            <translation>El estacionamiento '%1' no tiene visual de frente: una espalda sola no da ningún desnivel.</translation>
        </message>
        <message>
            <source>The setup '%1' sights the same station more than once (%2). A second sight onto the same point from one setup adds nothing; check the station names.</source>
            <translation>El estacionamiento '%1' visa la misma estación más de una vez (%2). Una segunda visual al mismo punto desde el mismo estacionamiento no añade nada; compruebe los nombres de las estaciones.</translation>
        </message>
        <message>
            <source>The sight distance to '%1' is negative (%2). Check the book's distance column.</source>
            <translation>La distancia de la visual a '%1' es negativa (%2). Compruebe la columna de distancias de la libreta.</translation>
        </message>
        <message>
            <source>The sight to %1 from setup %2 is %3 m, beyond the %4 m its class permits. Long sights magnify both refraction and the residual collimation error.</source>
            <translation>La visual hacia %1 desde el estacionamiento %2 tiene %3 m, más allá de los %4 m que permite su clase. Las visuales largas amplían tanto la refracción como el error de colimación residual.</translation>
        </message>
        <message>
            <source>The sight to %1 is within one degree of vertical, where the horizontal circle reading carries almost no directional information and the trunnion-tilt correction is unbounded. It was not applied.</source>
            <translation>La visual hacia %1 está a menos de un grado de la vertical, donde la lectura del círculo horizontal casi no aporta información de dirección y la corrección por inclinación del eje secundario no está acotada. No se aplicó.</translation>
        </message>
        <message>
            <source>The solution %1 cannot supersede itself; name the earlier solution it replaces.</source>
            <translation>La solución %1 no puede reemplazarse a sí misma; indique la solución anterior a la que reemplaza.</translation>
        </message>
        <message>
            <source>The solution '%1' carries the epoch %2 only because nothing stated one: the adjustment used its own default. An assumed epoch is not when the network was measured, so it cannot enter a comparison (FR-105). Adjust the epoch's network again with its observation date as the reference epoch.</source>
            <translation>La solución '%1' lleva la época %2 solo porque nada declaró una: el ajuste usó su propio valor por defecto. Una época supuesta no es cuando se midió la red, por lo que no puede entrar en una comparación (FR-105). Ajuste de nuevo la red de esa época con su fecha de observación como época de referencia.</translation>
        </message>
        <message>
            <source>The solution '%1' has no coordinate reference system, and GeoComp does not infer one. Give the solution its CRS.</source>
            <translation>La solución '%1' no tiene sistema de referencia de coordenadas, y GeoComp no infiere uno. Dé a la solución su SRC.</translation>
        </message>
        <message>
            <source>The solution '%1' has no position components to compare (%2).</source>
            <translation>La solución '%1' no tiene componentes de posición que comparar (%2).</translation>
        </message>
        <message>
            <source>The solution '%1' has no station '%2'. Check the station's id, and that this is the solution that adjusted it.</source>
            <translation>La solución '%1' no tiene la estación '%2'. Compruebe el id de la estación, y que esta sea la solución que la ajustó.</translation>
        </message>
        <message>
            <source>The solution '%1' mixes coordinate systems (%2) among its stations. Compare solutions whose stations are all in one system.</source>
            <translation>La solución '%1' mezcla sistemas de coordenadas (%2) entre sus estaciones. Compare soluciones cuyas estaciones estén todas en un solo sistema.</translation>
        </message>
        <message>
            <source>The solution '%1' states no epoch, and GeoComp does not assume one (FR-105). Adjust its network again with its observation date.</source>
            <translation>La solución '%1' no indica época, y GeoComp no supone ninguna (FR-105). Ajuste su red de nuevo con la fecha de observación.</translation>
        </message>
        <message>
            <source>The solution '%1' states no epoch, so it cannot enter a comparison (FR-105). The difference of two unknown instants is not a displacement; GeoComp does not assume one. Adjust the epoch's network again with its observation date.</source>
            <translation>La solución '%1' no indica época, así que no puede entrar en una comparación (FR-105). La diferencia entre dos instantes desconocidos no es un desplazamiento; GeoComp no supone una época. Ajuste la red de esa época de nuevo con la fecha de observación.</translation>
        </message>
        <message>
            <source>The solutions '%1' and '%2' have no station in common, so there is nothing to compare. The same mark must carry the same name at every epoch.</source>
            <translation>Las soluciones '%1' y '%2' no tienen estaciones en común, así que no hay nada que comparar. La misma marca debe llevar el mismo nombre en todas las épocas.</translation>
        </message>
        <message>
            <source>The sparse solver was asked for, but SciPy is not installed in QGIS's Python. Install SciPy, or let GeoComp choose the solver.</source>
            <translation>Se pidió el resolvedor disperso, pero SciPy no está instalado en el Python de QGIS. Instale SciPy o deje que GeoComp elija el resolvedor.</translation>
        </message>
        <message>
            <source>The square root of %1 is undefined; it needs a value that is not negative.</source>
            <translation>La raíz cuadrada de %1 no está definida; necesita un valor que no sea negativo.</translation>
        </message>
        <message>
            <source>The stadia constant must be positive, usually 100; %1 was given.</source>
            <translation>La constante estadimétrica debe ser positiva, normalmente 100; se dio %1.</translation>
        </message>
        <message>
            <source>The stadia constant of the level '%1' must be positive, usually 100; %2 was given.</source>
            <translation>La constante estadimétrica del nivel '%1' debe ser positiva, normalmente 100; se dio %2.</translation>
        </message>
        <message>
            <source>The station '%1' appears more than once in the reference station database.</source>
            <translation>La estación '%1' aparece más de una vez en la base de datos de estaciones de referencia.</translation>
        </message>
        <message>
            <source>The station '%1' has a %2 position, which the geocentric adjustment cannot hold. Give it cartesian or geodetic coordinates.</source>
            <translation>La estación '%1' tiene una posición %2, que el ajuste geocéntrico no puede mantener. Dele coordenadas cartesianas o geodésicas.</translation>
        </message>
        <message>
            <source>The station '%1' holds an orthometric height on its position, and the geocentric adjustment holds ellipsoidal heights. Enter the orthometric height as an orthometric-height observation, which the geoid relates to the frame.</source>
            <translation>La estación '%1' mantiene una altura ortométrica en su posición, y el ajuste geocéntrico mantiene alturas elipsoidales. Indique la altura ortométrica como una observación de altura ortométrica, que el geoide relaciona con el marco.</translation>
        </message>
        <message>
            <source>The station '%1' holds only %2 of its geodetic coordinates. Hold latitude, longitude and height together, or use a cartesian constraint; a height alone is entered as a height observation.</source>
            <translation>La estación '%1' mantiene solo %2 de sus coordenadas geodésicas. Mantenga latitud, longitud y altura juntas, o use una restricción cartesiana; una altura sola se indica como observación de altura.</translation>
        </message>
        <message>
            <source>The station '%1' is constrained but has no coordinates to be held at. Give them, or make the station free.</source>
            <translation>La estación '%1' tiene una restricción, pero no tiene coordenadas a mantener. Indíquelas, o deje la estación libre.</translation>
        </message>
        <message>
            <source>The station '%1' is held by two inputs (%2) at positions %3 m apart. Hold it in one input only, or correct the one that is wrong: two holds a distance apart force that distance into the residuals.</source>
            <translation>La estación '%1' está fijada por dos entradas (%2) en posiciones a %3 m entre sí. Fíjela en una sola entrada o corrija la equivocada: dos fijaciones separadas por una distancia fuerzan esa distancia en los residuos.</translation>
        </message>
        <message>
            <source>The station '%1' is held fixed in gravity but has no gravity value to hold. Give its gravity value.</source>
            <translation>La estación '%1' se mantiene fija en gravedad, pero no tiene valor de gravedad que mantener. Indique su valor de gravedad.</translation>
        </message>
        <message>
            <source>The station '%1' is not a station of the adjusted gravity network; a held station has no estimated value.</source>
            <translation>La estación '%1' no es una estación de la red gravimétrica ajustada; una estación mantenida fija no tiene valor estimado.</translation>
        </message>
        <message>
            <source>The station '%1' is not in the reference station database; expected %2.</source>
            <translation>La estación '%1' no está en la base de datos de estaciones de referencia; se esperaba %2.</translation>
        </message>
        <message>
            <source>The station '%1' needs a geoid undulation and has no approximate position to look it up at. Give it one.</source>
            <translation>La estación '%1' necesita una ondulación geoidal y no tiene posición aproximada en la que buscarla. Dele una.</translation>
        </message>
        <message>
            <source>The station '%2' cannot be written to '%1' as control: the format gives a control station two standard deviations and has no way to say it is held exactly. Give it a weighted constraint with its covariance.</source>
            <translation>La estación '%2' no puede escribirse en '%1' como control: el formato da a una estación de control dos desviaciones estándar y no tiene forma de decir que se mantiene exactamente. Dele una restricción ponderada con su matriz de varianza-covarianza.</translation>
        </message>
        <message>
            <source>The station '%2' of '%1' has no approximate position, which the combination needs to know which way is up there. Give it an approximate position.</source>
            <translation>La estación '%2' de '%1' no tiene posición aproximada, que la combinación necesita para saber hacia dónde es arriba allí. Dele una posición aproximada.</translation>
        </message>
        <message>
            <source>The stations %1 are held twice: given with their own constraint, and held here as well. Hold each one way only.</source>
            <translation>Las estaciones %1 se mantienen fijas dos veces: dadas con su propia restricción, y mantenidas fijas aquí también. Mantenga cada una de un solo modo.</translation>
        </message>
        <message>
            <source>The temperature is in %1; the atmospheric correction takes kelvin.</source>
            <translation>La temperatura está en %1; la corrección atmosférica usa kelvin.</translation>
        </message>
        <message>
            <source>The three wires read at %1 from setup %2 give (upper + lower) / 2 - middle = %3 m, which should be zero. One of the three was misread, or they were entered in the wrong columns.</source>
            <translation>Los tres hilos leídos en %1 desde el estacionamiento %2 dan (superior + inferior) / 2 - medio = %3 m, que debería ser cero. Uno de los tres se leyó mal, o se anotaron en las columnas equivocadas.</translation>
        </message>
        <message>
            <source>The three wires read at %1 give (upper + lower) / 2 - middle = %2 m, which should be zero. One of the three was misread, or they were entered in the wrong columns.</source>
            <translation>Los tres hilos leídos en %1 dan (superior + inferior) / 2 - medio = %2 m, que debería ser cero. Uno de los tres se leyó mal, o se anotaron en las columnas equivocadas.</translation>
        </message>
        <message>
            <source>The three-wire readings %1 are not in the order lower, middle, upper. A staff is read upwards, so the values were probably entered in the wrong columns.</source>
            <translation>Las lecturas de los tres hilos %1 no están en el orden inferior, medio, superior. Una mira se lee de abajo arriba, por lo que los valores probablemente se introdujeron en las columnas equivocadas.</translation>
        </message>
        <message>
            <source>The tide at %1 cannot be computed: the time has no time zone, and the tide depends on the time to the minute.</source>
            <translation>La marea en %1 no puede calcularse: la hora no tiene zona horaria, y la marea depende de la hora al minuto.</translation>
        </message>
        <message>
            <source>The time of the gravity reading '%1' has no time zone. A time zone guessed an hour wrong is tens of microgal of tide; give the time zone of the readings.</source>
            <translation>La hora de la lectura gravimétrica '%1' no tiene zona horaria. Una zona horaria errada en una hora son decenas de microgal de marea; indique la zona horaria de las lecturas.</translation>
        </message>
        <message>
            <source>The transformation %1 holds only at its own epoch, and the coordinates are at %2. Move them to that epoch with a velocity first.</source>
            <translation>La transformación %1 vale solo en su propia época, y las coordenadas están en %2. Llévelas primero a esa época con una velocidad.</translation>
        </message>
        <message>
            <source>The traverse closes to 1:%1 over %2 m, against a required 1:%3.</source>
            <translation>La poligonal cierra con 1:%1 en %2 m, frente a los 1:%3 exigidos.</translation>
        </message>
        <message>
            <source>The traverse has no legs. A traverse needs at least one leg between two stations.</source>
            <translation>La poligonal no tiene lados. Una poligonal necesita al menos un lado entre dos estaciones.</translation>
        </message>
        <message>
            <source>The two banks give height differences that differ by %1 m. The method assumes the refraction was the same for both, and a discrepancy this size says it was not.</source>
            <translation>Las dos orillas dan desniveles que difieren en %1 m. El método supone que la refracción fue la misma para ambas, y una discrepancia de este tamaño dice que no lo fue.</translation>
        </message>
        <message>
            <source>The two faces of a pair point at different targets (%1); both faces of a pair sight the same target.</source>
            <translation>Las dos posiciones de un par visan objetivos distintos (%1); las dos posiciones de un par visan el mismo objetivo.</translation>
        </message>
        <message>
            <source>The two faces to %1 disagree on the distance by %2 m, against a tolerance of %3 m. The mean of the two is not a measurement of anything; check the field book before using this pair.</source>
            <translation>Los dos círculos hacia %1 discrepan en la distancia en %2 m, frente a una tolerancia de %3 m. La media de las dos no es la medida de nada; compruebe la libreta de campo antes de usar este par.</translation>
        </message>
        <message>
            <source>The two pairs of a reciprocal crossing join different stations: the second joins %1, where %2 was expected.</source>
            <translation>Los dos pares de una travesía recíproca unen estaciones distintas: el segundo une %1, donde se esperaba %2.</translation>
        </message>
        <message>
            <source>The two runs of a double-run section join different stations (%1). Both runs of a section go between the same two stations, in either direction.</source>
            <translation>Los dos recorridos de una sección de ida y vuelta unen estaciones distintas (%1). Los dos recorridos de una sección van entre las mismas dos estaciones, en cualquier sentido.</translation>
        </message>
        <message>
            <source>The two sights differ by %1 m over %2 m. Leap-frog cancels refraction in proportion to how equal the sights are, so an imbalanced pair gets much less of the method's benefit.</source>
            <translation>Las dos visuales difieren en %1 m en %2 m. El leap-frog cancela la refracción en la medida en que las visuales son iguales, así que un par desequilibrado recibe mucho menos del beneficio del método.</translation>
        </message>
        <message>
            <source>The two solutions (%1) define their datum differently: %2. A free solution compares with a free one, and a held solution with one held the same way; a held one carries its constraint in its coordinates, and no transformation takes it out. Adjust both epochs with the same datum definition.</source>
            <translation>Las dos soluciones (%1) definen el datum de forma distinta: %2. Una solución libre se compara con una libre, y una fijada con una fijada del mismo modo; una fijada lleva su restricción en sus coordenadas, y ninguna transformación la quita. Ajuste ambas épocas con la misma definición del datum.</translation>
        </message>
        <message>
            <source>The two solutions (%1) hold heights of different types: %2. Their difference would be the difference of the height systems, not motion. Adjust both epochs with heights of one type.</source>
            <translation>Las dos soluciones (%1) tienen alturas de tipos distintos: %2. Su diferencia sería la diferencia entre los sistemas de altura, no movimiento. Ajuste ambas épocas con alturas de un solo tipo.</translation>
        </message>
        <message>
            <source>The two solutions (%1) relate heights to the ellipsoid through different geoid models: %2. Heights from two models differ by the difference of the models, which is not motion. Use the same geoid model at every epoch.</source>
            <translation>Las dos soluciones (%1) relacionan las alturas con el elipsoide mediante modelos geoidales distintos: %2. Las alturas de dos modelos difieren por la diferencia de los modelos, que no es movimiento. Use el mismo modelo geoidal en todas las épocas.</translation>
        </message>
        <message>
            <source>The two solutions are in different coordinate systems (%1). Two projections differ by the projection, not by motion. Adjust both epochs in one coordinate reference system, or give both in a geocentric frame, which GeoComp transforms.</source>
            <translation>Las dos soluciones están en sistemas de coordenadas distintos (%1). Dos proyecciones difieren por la proyección, no por movimiento. Ajuste ambas épocas en un solo sistema de referencia de coordenadas, o indique ambas en un marco geocéntrico, que GeoComp transforma.</translation>
        </message>
        <message>
            <source>The two solutions are in frames GeoComp cannot relate (%1). Give both in ITRF2000 to ITRF2020 or SIRGAS 2000, which GeoComp transforms between with the transformation's own uncertainty.</source>
            <translation>Las dos soluciones están en marcos que GeoComp no puede relacionar (%1). Indique ambas en ITRF2000 a ITRF2020 o SIRGAS 2000, entre los que GeoComp transforma con la incertidumbre propia de la transformación.</translation>
        </message>
        <message>
            <source>The two solutions estimate different components (%1). Compare epochs adjusted in the same dimension: plan with plan, heights with heights, 3D with 3D.</source>
            <translation>Las dos soluciones estiman componentes distintas (%1). Compare épocas ajustadas en la misma dimensión: planimetría con planimetría, alturas con alturas, 3D con 3D.</translation>
        </message>
        <message>
            <source>The uncertainty of a length cannot be propagated between two coincident points. Check for two stations with the same coordinates.</source>
            <translation>La incertidumbre de una longitud no puede propagarse entre dos puntos coincidentes. Compruebe si hay dos estaciones con las mismas coordenadas.</translation>
        </message>
        <message>
            <source>The uncertainty of a square root cannot be propagated at zero, where its derivative is infinite.</source>
            <translation>La incertidumbre de una raíz cuadrada no puede propagarse en cero, donde su derivada es infinita.</translation>
        </message>
        <message>
            <source>The value %1 has a variance of %2; a variance cannot be negative.</source>
            <translation>El valor %1 tiene una varianza de %2; una varianza no puede ser negativa.</translation>
        </message>
        <message>
            <source>The value %1 is marked approximate without saying how its uncertainty was estimated. This is an internal error; please report it.</source>
            <translation>El valor %1 está marcado como aproximado sin decir cómo se estimó su incertidumbre. Este es un error interno; por favor, infórmelo.</translation>
        </message>
        <message>
            <source>The value given for %1 is not a number: '%2'. Enter a number, with a point or a comma for the decimals.</source>
            <translation>El valor indicado para %1 no es un número: '%2'. Introduzca un número, con punto o coma para los decimales.</translation>
        </message>
        <message>
            <source>The variance component of the group '%1' cannot be estimated: its redundancy is only %2, so its residuals barely depend on its own weights. Fix its weights, or merge it with another group.</source>
            <translation>La componente de varianza del grupo '%1' no puede estimarse: su redundancia es de solo %2, por lo que sus residuos apenas dependen de sus propios pesos. Fije sus pesos, o únalo a otro grupo.</translation>
        </message>
        <message>
            <source>The variance components did not settle in %1 iterations (last factors: %2). A group with little redundancy can oscillate; merge it with another, or fix its weights.</source>
            <translation>Las componentes de varianza no se estabilizaron en %1 iteraciones (últimos factores: %2). Un grupo con poca redundancia puede oscilar; únalo a otro, o fije sus pesos.</translation>
        </message>
        <message>
            <source>The variance factor of the group '%1' came out negative (%2): its residuals are smaller than its model allows. The group has too little redundancy, or its stochastic model is wrong in shape rather than in scale.</source>
            <translation>El factor de varianza del grupo '%1' salió negativo (%2): sus residuos son menores de lo que su modelo admite. El grupo tiene poca redundancia, o su modelo estocástico está equivocado en la forma, no en la escala.</translation>
        </message>
        <message>
            <source>The variance inflation of a reciprocal crossing must be at least 1; %1 was given. A smaller factor would claim the method is better than its readings.</source>
            <translation>La inflación de varianza de una travesía recíproca debe ser al menos 1; se dio %1. Un factor menor afirmaría que el método es mejor que sus lecturas.</translation>
        </message>
        <message>
            <source>The variance of this crossing was multiplied by %1. Refraction over water varies rapidly and asymmetrically, and the two reciprocal observations were not simultaneous, so the symmetry the method relies on holds only approximately.</source>
            <translation>La varianza de esta travesía se multiplicó por %1. La refracción sobre el agua varía rápida y asimétricamente, y las dos observaciones recíprocas no fueron simultáneas, así que la simetría en la que se apoya el método solo se cumple aproximadamente.</translation>
        </message>
        <message>
            <source>The vertical gradient %2 at the station '%1' cannot be used: it must be a finite number in s^-2, with a non-negative uncertainty.</source>
            <translation>El gradiente vertical %2 en la estación '%1' no puede usarse: debe ser un número finito en s^-2, con una incertidumbre no negativa.</translation>
        </message>
        <message>
            <source>The vertical index error at station %1 varies by %2 arcsec across its face pairs.</source>
            <translation>El error de índice vertical en la estación %1 varía %2 segundos de arco entre sus pares de círculo directo e inverso.</translation>
        </message>
        <message>
            <source>The weighted constraint on '%1' (%2) has a singular covariance: a direction in it is infinitely precise, which is a fixed constraint written as a weighted one. Fix those components instead, or correct the covariance.</source>
            <translation>La restricción ponderada en '%1' (%2) tiene una covarianza singular: una dirección en ella es infinitamente precisa, lo que es una restricción fija escrita como ponderada. Fije esas componentes, o corrija la covarianza.</translation>
        </message>
        <message>
            <source>The weighted constraint on '%1' has a covariance over %2, which does not cover the constrained components %3.</source>
            <translation>La restricción ponderada en '%1' tiene una covarianza sobre %2, que no cubre las componentes restringidas %3.</translation>
        </message>
        <message>
            <source>The weighting coefficient must be positive; %1 was given. A zero would claim every difference is exact and give it an infinite weight.</source>
            <translation>El coeficiente de ponderación debe ser positivo; se dio %1. Un cero afirmaría que toda diferencia es exacta y le daría peso infinito.</translation>
        </message>
        <message>
            <source>The zoom range of the base map service '%1' runs from %2; the minimum zoom must be 0 or more, and no greater than the maximum.</source>
            <translation>El rango de zoom del servicio de mapa base '%1' va de %2; el zoom mínimo debe ser 0 o más, y no mayor que el máximo.</translation>
        </message>
        <message>
            <source>There is no GeoComp project at %1. Check the name, or choose to create it.</source>
            <translation>No hay ningún proyecto de GeoComp en %1. Compruebe el nombre, o elija crearlo.</translation>
        </message>
        <message>
            <source>There is no PostgreSQL connection named '%1' in QGIS. Add it in the Browser panel under PostgreSQL, or choose one that exists.</source>
            <translation>No hay ninguna conexión PostgreSQL llamada '%1' en QGIS. Añádala en el panel Navegador bajo PostgreSQL, o elija una que exista.</translation>
        </message>
        <message>
            <source>There is no base map service '%1' in the catalogue; expected %2. Choose one of them, or add the service to the catalogue in Global Settings, under Base maps.</source>
            <translation>No hay ningún servicio de mapa base '%1' en el catálogo; se esperaba %2. Elija uno de ellos, o añada el servicio al catálogo en Configuraciones Globales, en Mapas base.</translation>
        </message>
        <message>
            <source>There is no instrument profile '%1'; expected %2.</source>
            <translation>No hay ningún perfil de instrumento '%1'; se esperaba %2.</translation>
        </message>
        <message>
            <source>There is no level profile '%1'; expected %2.</source>
            <translation>No hay ningún perfil de nivel '%1'; se esperaba %2.</translation>
        </message>
        <message>
            <source>There is no levelling class '%1'; expected %2.</source>
            <translation>No hay ninguna clase de nivelación '%1'; se esperaba %2.</translation>
        </message>
        <message>
            <source>There is no reflector profile '%1'; expected %2.</source>
            <translation>No hay ningún perfil de reflector '%1'; se esperaba %2.</translation>
        </message>
        <message>
            <source>There is no report template '%1' in the configured directory or among the shipped ones: %2.</source>
            <translation>No hay ninguna plantilla de informe '%1' en el directorio configurado ni entre las incluidas: %2.</translation>
        </message>
        <message>
            <source>There is no solution %1 in this project store.</source>
            <translation>No hay ninguna solución %1 en este repositorio de proyecto.</translation>
        </message>
        <message>
            <source>There is nothing to export: every sheet came out empty. Choose a network or a solution with content; a workbook of empty sheets would say the data was zero rather than absent.</source>
            <translation>No hay nada que exportar: todas las hojas quedaron vacías. Elija una red o una solución con contenido; un libro de hojas vacías diría que los datos eran cero en lugar de ausentes.</translation>
        </message>
        <message>
            <source>These distances are part of a correlated cluster, whose covariance describes them as measured, and reducing them would leave it describing other values: %1. Reduce them before they are clustered, or turn the reduction off.</source>
            <translation>Estas distancias forman parte de un agrupamiento correlacionado, cuya covarianza las describe como medidas, y reducirlas la dejaría describiendo otros valores: %1. Redúzcalas antes de agruparlas, o desactive la reducción.</translation>
        </message>
        <message>
            <source>These stations are not in both solutions: %1. Stations both epochs estimate: %2.</source>
            <translation>Estas estaciones no están en ambas soluciones: %1. Estaciones que ambas épocas estiman: %2.</translation>
        </message>
        <message>
            <source>These stations were not compared: %1. The compared stations are: %2.</source>
            <translation>Estas estaciones no se compararon: %1. Las estaciones comparadas son: %2.</translation>
        </message>
        <message>
            <source>This DynAdjust output writes angles in degrees, minutes and seconds with symbols (%1), which GeoComp does not read. Run DynAdjust with its default angular format.</source>
            <translation>Esta salida de DynAdjust escribe ángulos en grados, minutos y segundos con símbolos (%1), lo que GeoComp no lee. Ejecute DynAdjust con su formato angular predeterminado.</translation>
        </message>
        <message>
            <source>This JSON file is not a GeoComp network document: it has no network identifier. Expected a network document, with its identifier and its list of stations.</source>
            <translation>Este archivo JSON no es un documento de red de GeoComp: no tiene identificador de red. Se esperaba un documento de red, con su identificador y su lista de estaciones.</translation>
        </message>
        <message>
            <source>This combination was routed to DynAdjust (%1) and cannot be adjusted here. Choose GeoComp's own engine, or the DynAdjust path.</source>
            <translation>Esta combinación se encaminó a DynAdjust (%1) y no puede ajustarse aquí. Elija el motor propio de GeoComp, o la ruta de DynAdjust.</translation>
        </message>
        <message>
            <source>This combined network cannot be sent to DynAdjust (%1). Adjust it with GeoComp's own adjustment.</source>
            <translation>Esta red combinada no puede enviarse a DynAdjust (%1). Ajústela con el ajuste propio de GeoComp.</translation>
        </message>
        <message>
            <source>This computation needs the whole network held densely, about %3 MiB for %1 observation rows and %2 unknowns, and this machine allows %4 MiB. Variance component estimation is such a computation: run the adjustment without it, or estimate the components on a part of the network.</source>
            <translation>Este cálculo necesita toda la red en matrices densas, unos %3 MiB para %1 filas de observación y %2 incógnitas, y esta máquina permite %4 MiB. La estimación de componentes de varianza es un cálculo así: ejecute el ajuste sin ella o estime los componentes en una parte de la red.</translation>
        </message>
        <message>
            <source>This crossing was reduced with no variance inflation, so its uncertainty assumes the two reciprocal observations saw identical refraction. They were not simultaneous, so they did not.</source>
            <translation>Esta travesía se redujo sin inflación de varianza, así que su incertidumbre supone que las dos observaciones recíprocas vieron una refracción idéntica. No fueron simultáneas, así que no la vieron.</translation>
        </message>
        <message>
            <source>This file does not hold a GeoComp network: its top level is %1, and a network document is a JSON object. Check that you chose the right file.</source>
            <translation>Este archivo no contiene una red de GeoComp: su nivel superior es %1, y un documento de red es un objeto JSON. Compruebe que ha elegido el archivo correcto.</translation>
        </message>
        <message>
            <source>This file is a '%1', not a '%2'. Give the document the monitoring algorithm wrote for this input.</source>
            <translation>Este archivo es un '%1', no un '%2'. Indique el documento que el algoritmo de monitoreo escribió para esta entrada.</translation>
        </message>
        <message>
            <source>This file is not a gravimeter export GeoComp can read. Expected a Scintrex CG-5 export (a header of '/' lines), a ZLS Burris export (16 space-separated columns, the date as YYYY/MM/DD), or a CSV whose header names %1.</source>
            <translation>Este archivo no es una exportación de gravímetro que GeoComp pueda leer. Se esperaba una exportación del Scintrex CG-5 (un encabezado de líneas '/'), una exportación del ZLS Burris (16 columnas separadas por espacios, la fecha como AAAA/MM/DD), o un CSV cuyo encabezado nombre %1.</translation>
        </message>
        <message>
            <source>This monitoring document is version %1; this GeoComp reads version %2. Run the analysis again to write it anew.</source>
            <translation>Este documento de monitoreo es de la versión %1; este GeoComp lee la versión %2. Ejecute el análisis de nuevo para reescribirlo.</translation>
        </message>
        <message>
            <source>This monitoring document lacks %1, so it cannot be read. Run the analysis again to write it anew.</source>
            <translation>A este documento de monitoreo le falta %1, así que no se puede leer. Ejecute el análisis de nuevo para reescribirlo.</translation>
        </message>
        <message>
            <source>This network document could not be read: %1. It may have been written by a different version of GeoComp, or edited by hand.</source>
            <translation>No se pudo leer este documento de red: %1. Puede haber sido escrito por otra versión de GeoComp, o editado a mano.</translation>
        </message>
        <message>
            <source>This network is too large to adjust without SciPy: %1 observation rows and %2 unknowns would need about %3 MiB held densely, and this machine allows %4 MiB. Install SciPy into QGIS's Python and run it again; the sparse solver it provides adjusts 10,000 stations in a few hundred MiB. Beyond about 10,000 stations, adjust the network with DynAdjust's segmentation.</source>
            <translation>Esta red es demasiado grande para ajustarse sin SciPy: %1 filas de observación y %2 incógnitas necesitarían unos %3 MiB en matrices densas, y esta máquina permite %4 MiB. Instale SciPy en el Python de QGIS y vuelva a ejecutarlo; el resolvedor disperso que proporciona ajusta 10.000 estaciones en unos cientos de MiB. Por encima de unas 10.000 estaciones, ajuste la red con la segmentación de DynAdjust.</translation>
        </message>
        <message>
            <source>This project file holds %1 networks, so GeoComp cannot tell which one you mean. Export the network you want to analyse and choose that file instead.</source>
            <translation>Este archivo de proyecto contiene %1 redes, por lo que GeoComp no puede saber a cuál se refiere. Exporte la red que desea analizar y elija ese archivo.</translation>
        </message>
        <message>
            <source>This solution is in latitude, longitude and height (%1), whose components are not all metres, so they cannot be treated as one covariance. Use an ECEF or ENU solution.</source>
            <translation>Esta solución está en latitud, longitud y altura (%1), cuyos componentes no son todos metros, por lo que no pueden tratarse como una sola covarianza. Use una solución ECEF o ENU.</translation>
        </message>
        <message>
            <source>This traverse does not close on a known point, so no misclosure exists and nothing about it can be checked. A blunder anywhere in it would be invisible.</source>
            <translation>Esta poligonal no cierra en un punto conocido, así que no existe error de cierre y nada en ella puede comprobarse. Un error grosero en cualquier lugar sería invisible.</translation>
        </message>
        <message>
            <source>Two correlated values were combined (%1) as if they were independent, which would misstate the uncertainty of the result. This is an internal error; please report it with the data that caused it.</source>
            <translation>Dos valores correlacionados se combinaron (%1) como si fueran independientes, lo que declararía mal la incertidumbre del resultado. Este es un error interno; por favor, infórmelo con los datos que lo causaron.</translation>
        </message>
        <message>
            <source>Two gravimeter profiles share the id '%1'. Rename or replace one of them.</source>
            <translation>Dos perfiles de gravímetro comparten el id '%1'. Cambie el nombre o sustituya uno de ellos.</translation>
        </message>
        <message>
            <source>Two instrument profiles share the id '%1'. Rename or replace one of them.</source>
            <translation>Dos perfiles de instrumento comparten el id '%1'. Cambie el nombre o sustituya uno de ellos.</translation>
        </message>
        <message>
            <source>Two level profiles share the id '%1'. Rename or replace one of them.</source>
            <translation>Dos perfiles de nivel comparten el id '%1'. Cambie el nombre o sustituya uno de ellos.</translation>
        </message>
        <message>
            <source>Two levelling classes share the id '%1'. Rename or replace one of them.</source>
            <translation>Dos clases de nivelación comparten el id '%1'. Cambie el nombre o sustituya una de ellas.</translation>
        </message>
        <message>
            <source>Two reflector profiles share the id '%1'. Rename or replace one of them.</source>
            <translation>Dos perfiles de reflector comparten el id '%1'. Cambie el nombre o sustituya uno de ellos.</translation>
        </message>
        <message>
            <source>UTM zone %1 does not exist; the zones run from 1 to 60.</source>
            <translation>La zona UTM %1 no existe; las zonas van de 1 a 60.</translation>
        </message>
        <message>
            <source>Values in %2 cannot be combined (%1): the result would need a compound unit, which GeoComp does not track.</source>
            <translation>Valores en %2 no pueden combinarse (%1): el resultado necesitaría una unidad compuesta, que GeoComp no sigue.</translation>
        </message>
        <message>
            <source>Variance components cannot be estimated with the sparse solver: the estimator reads the whole residual cofactor matrix, which that solver never forms. Let GeoComp choose the solver.</source>
            <translation>Los componentes de varianza no pueden estimarse con el resolvedor disperso: el estimador lee la matriz cofactor de los residuos completa, que ese resolvedor nunca forma. Deje que GeoComp elija el resolvedor.</translation>
        </message>
        <message>
            <source>Weighting by extent is defined for height and gravity differences, not for %1.</source>
            <translation>La ponderación por extensión está definida para diferencias de altura y de gravedad, no para %1.</translation>
        </message>
        <message>
            <source>dnaadjust reported success but wrote no adjustment file (%1). Run the adjustment again with the generated input and raw output kept, and look at its messages there.</source>
            <translation>dnaadjust informó éxito pero no escribió ningún archivo de ajuste (%1). Ejecute el ajuste de nuevo conservando la entrada generada y la salida sin procesar, y consulte sus mensajes allí.</translation>
        </message>
        <message>
            <source>dnaimport reported success but did not take in everything GeoComp wrote: it counted %1, where GeoComp wrote %2. Adjusting the rest would give a plausible answer for a different network, so the run was stopped. dnaimport's own message: %3</source>
            <translation>dnaimport informó éxito pero no incorporó todo lo que GeoComp escribió: contó %1, donde GeoComp escribió %2. Ajustar el resto daría una respuesta plausible para otra red, por eso se detuvo la ejecución. El mensaje del propio dnaimport: %3</translation>
        </message>
        <message>
            <source>no occupied station is given.</source>
            <translation>no se indica ninguna estación ocupada.</translation>
        </message>
        <message>
            <source>no station is given for '%1', so the pointing has no target.</source>
            <translation>no se indica ninguna estación para '%1', así que la puntería no tiene objetivo.</translation>
        </message>
        <message>
            <source>the angle '%1' is empty.</source>
            <translation>el ángulo '%1' está vacío.</translation>
        </message>
        <message>
            <source>the set number '%1' is not a whole number.</source>
            <translation>el número de serie '%1' no es un número entero.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMonitoring</name>
        <message>
            <source>From the network: translation and rotation for a plan, translation for heights</source>
            <translation>Según la red: traslación y rotación para planimetría, traslación para alturas</translation>
        </message>
        <message>
            <source>Name the reference stations -- the pillars assumed stable, against which movement is measured -- or mark them REFERENCE in the network document. GeoComp does not choose them: a block picked by the software is picked to make the answer stable.</source>
            <translation>Nombre las estaciones de referencia -- los pilares supuestos estables, contra los que se mide el movimiento -- o márquelas REFERENCE en el documento de la red. GeoComp no las elige: un bloque elegido por el software se elige para que la respuesta salga estable.</translation>
        </message>
        <message>
            <source>Similarity: translation, rotation and scale</source>
            <translation>Semejanza: traslación, rotación y escala</translation>
        </message>
        <message>
            <source>The alert thresholds file '%1' could not be read: %2</source>
            <translation>No se pudo leer el archivo de umbrales de alerta '%1': %2</translation>
        </message>
        <message>
            <source>Translation</source>
            <translation>Traslación</translation>
        </message>
        <message>
            <source>Translation and rotation</source>
            <translation>Traslación y rotación</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMonitoringReport</name>
        <message>
            <source>%1 (mm)</source>
            <translation>%1 (mm)</translation>
        </message>
        <message>
            <source>%1 carries each station's own covariance and not the covariance between stations, so the stations of that epoch were taken as uncorrelated with one another. The test of a difference between stations, and of the reference block, leaves that correlation out.</source>
            <translation>%1 lleva la covarianza propia de cada estación y no la covarianza entre estaciones; por eso las estaciones de esa época se tomaron como no correlacionadas entre sí. La prueba de una diferencia entre estaciones, y la del bloque de referencia, dejan fuera esa correlación.</translation>
        </message>
        <message>
            <source>(not recorded)</source>
            <translation>(no registrado)</translation>
        </message>
        <message>
            <source>A station over its limit is flagged whether or not its motion is significant: the owner's criterion is not silenced by the survey's precision.</source>
            <translation>Una estación por encima de su límite se señala sea o no significativo su movimiento: el criterio del propietario no queda silenciado por la precisión del levantamiento.</translation>
        </message>
        <message>
            <source>Accuracy (mm)</source>
            <translation>Exactitud (mm)</translation>
        </message>
        <message>
            <source>Alerts</source>
            <translation>Alertas</translation>
        </message>
        <message>
            <source>All compared stations</source>
            <translation>Todas las estaciones comparadas</translation>
        </message>
        <message>
            <source>Analysis refused</source>
            <translation>Análisis rechazado</translation>
        </message>
        <message>
            <source>Approximate: %1.</source>
            <translation>Aproximado: %1.</translation>
        </message>
        <message>
            <source>At epoch</source>
            <translation>En la época</translation>
        </message>
        <message>
            <source>Azimuth of the first principal strain (°)</source>
            <translation>Acimut de la primera deformación principal (°)</translation>
        </message>
        <message>
            <source>Both epochs agree in frame, datum definition, height type, geoid model and engine; nothing was found that would put a systematic difference into the displacements.</source>
            <translation>Ambas épocas coinciden en marco, definición del datum, tipo de altura, modelo geoidal y motor; no se encontró nada que introdujera una diferencia sistemática en los desplazamientos.</translation>
        </message>
        <message>
            <source>Compatibility and transformations</source>
            <translation>Compatibilidad y transformaciones</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Coordinate reference system</source>
            <translation>Sistema de referencia de coordenadas</translation>
        </message>
        <message>
            <source>Criterion</source>
            <translation>Criterio</translation>
        </message>
        <message>
            <source>Critical value</source>
            <translation>Valor crítico</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>Datum of the displacements</source>
            <translation>Datum de los desplazamientos</translation>
        </message>
        <message>
            <source>Decision</source>
            <translation>Decisión</translation>
        </message>
        <message>
            <source>Deformation</source>
            <translation>Deformación</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Dilatation (ppm)</source>
            <translation>Dilatación (ppm)</translation>
        </message>
        <message>
            <source>Displacement map</source>
            <translation>Mapa de los desplazamientos</translation>
        </message>
        <message>
            <source>Displacements</source>
            <translation>Desplazamientos</translation>
        </message>
        <message>
            <source>Each displacement is tested against its own covariance at the confidence level above. Not significant is not zero: the value is kept, with its uncertainty, because we could not detect motion is a different statement from there is no motion.</source>
            <translation>Cada desplazamiento se prueba contra su propia covarianza al nivel de confianza indicado. No significativo no es cero: el valor se conserva, con su incertidumbre, porque no pudimos detectar movimiento es una afirmación distinta de no hay movimiento.</translation>
        </message>
        <message>
            <source>Each epoch of the series was compared with the first under the same checks: frames, epochs, datum definitions, height types and geoid models.</source>
            <translation>Cada época de la serie se comparó con la primera con las mismas verificaciones: marcos, épocas, definiciones del datum, tipos de altura y modelos geoidales.</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Epoch</source>
            <translation>Época</translation>
        </message>
        <message>
            <source>Epochs</source>
            <translation>Épocas</translation>
        </message>
        <message>
            <source>Every epoch of the series is referred to the reference block by an S-transformation.</source>
            <translation>Cada época de la serie se refiere al bloque de referencia mediante una transformación S.</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GeoComp</source>
            <translation>GeoComp</translation>
        </message>
        <message>
            <source>Geoid model</source>
            <translation>Modelo geoidal</translation>
        </message>
        <message>
            <source>Global congruency</source>
            <translation>Congruencia global</translation>
        </message>
        <message>
            <source>Group</source>
            <translation>Grupo</translation>
        </message>
        <message>
            <source>Heights</source>
            <translation>Altitudes</translation>
        </message>
        <message>
            <source>Horizontal</source>
            <translation>Horizontal</translation>
        </message>
        <message>
            <source>Largest contributions</source>
            <translation>Mayores contribuciones</translation>
        </message>
        <message>
            <source>Limit</source>
            <translation>Límite</translation>
        </message>
        <message>
            <source>Maximum shear (ppm)</source>
            <translation>Cizalla máxima (ppm)</translation>
        </message>
        <message>
            <source>Monitoring report</source>
            <translation>Informe de monitoreo</translation>
        </message>
        <message>
            <source>No alert thresholds were set for this analysis.</source>
            <translation>No se definieron umbrales de alerta para este análisis.</translation>
        </message>
        <message>
            <source>No station crossed a threshold. %1 station checks were made.</source>
            <translation>Ninguna estación superó un umbral. Se hicieron %1 verificaciones de estación.</translation>
        </message>
        <message>
            <source>No transformation was applied: both epochs are in one frame.</source>
            <translation>No se aplicó ninguna transformación: ambas épocas están en un mismo marco.</translation>
        </message>
        <message>
            <source>Object stations</source>
            <translation>Estaciones objeto</translation>
        </message>
        <message>
            <source>Offsets from the first epoch, referred to the reference block, with a band of %1 standard deviations (%2% confidence) and the fitted velocity line.</source>
            <translation>Desplazamientos respecto a la primera época, referidos al bloque de referencia, con una banda de %1 desviaciones estándar (%2% de confianza) y la recta de velocidad ajustada.</translation>
        </message>
        <message>
            <source>Parameter</source>
            <translation>Parámetro</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Pooled variance factor</source>
            <translation>Factor de varianza combinado</translation>
        </message>
        <message>
            <source>Principal strains (ppm)</source>
            <translation>Deformaciones principales (ppm)</translation>
        </message>
        <message>
            <source>QGIS</source>
            <translation>QGIS</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reference block</source>
            <translation>Bloque de referencia</translation>
        </message>
        <message>
            <source>Reference block congruency</source>
            <translation>Congruencia del bloque de referencia</translation>
        </message>
        <message>
            <source>Reference stations</source>
            <translation>Estaciones de referencia</translation>
        </message>
        <message>
            <source>Removed</source>
            <translation>Eliminada</translation>
        </message>
        <message>
            <source>Report template</source>
            <translation>Plantilla de informe</translation>
        </message>
        <message>
            <source>Rigid rotation (µrad)</source>
            <translation>Rotación rígida (µrad)</translation>
        </message>
        <message>
            <source>Rigid translation east, north (mm)</source>
            <translation>Traslación rígida este, norte (mm)</translation>
        </message>
        <message>
            <source>Role</source>
            <translation>Rol</translation>
        </message>
        <message>
            <source>Significant</source>
            <translation>Significativo</translation>
        </message>
        <message>
            <source>Software</source>
            <translation>Software</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Speed (mm/a)</source>
            <translation>Rapidez (mm/a)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Stations in one epoch only, not compared: %1.</source>
            <translation>Estaciones en una sola época, no comparadas: %1.</translation>
        </message>
        <message>
            <source>Stations tested</source>
            <translation>Estaciones probadas</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estadístico</translation>
        </message>
        <message>
            <source>Std. dev. %1 (mm)</source>
            <translation>Desv. estándar %1 (mm)</translation>
        </message>
        <message>
            <source>Std. dev. %1 (mm/a)</source>
            <translation>Desv. estándar %1 (mm/a)</translation>
        </message>
        <message>
            <source>Step</source>
            <translation>Paso</translation>
        </message>
        <message>
            <source>Steps</source>
            <translation>Pasos</translation>
        </message>
        <message>
            <source>Strain test</source>
            <translation>Prueba de la deformación</translation>
        </message>
        <message>
            <source>Strain was not computed: it needs three object points at least, spread over an area.</source>
            <translation>La deformación no se calculó: se necesitan al menos tres puntos objeto, distribuidos en un área.</translation>
        </message>
        <message>
            <source>Strain was not requested.</source>
            <translation>No se solicitó la deformación.</translation>
        </message>
        <message>
            <source>The datum definitions differ (%1 and %2); both are free, and they are related by the S-transformation onto the reference block.</source>
            <translation>Las definiciones del datum difieren (%1 y %2); ambas son libres, y se relacionan mediante la transformación S sobre el bloque de referencia.</translation>
        </message>
        <message>
            <source>The displacements' uncertainties were propagated rigorously, with the correlation between the epochs.</source>
            <translation>Las incertidumbres de los desplazamientos se propagaron rigurosamente, con la correlación entre las épocas.</translation>
        </message>
        <message>
            <source>The epochs were processed by different engines or versions: %1 and %2.</source>
            <translation>Las épocas se procesaron con motores o versiones distintos: %1 y %2.</translation>
        </message>
        <message>
            <source>The epochs were taken as independent. If they share reference stations, a datum definition or GNSS products, they are positively correlated: each displacement's true uncertainty is smaller than the one stated here, so the significance of real motion is understated, not overstated.</source>
            <translation>Las épocas se tomaron como independientes. Si comparten estaciones de referencia, una definición del datum o productos GNSS, están correlacionadas positivamente: la incertidumbre verdadera de cada desplazamiento es menor que la aquí indicada, y la significancia de un movimiento real se subestima, no se sobreestima.</translation>
        </message>
        <message>
            <source>The reference block moved. The localisation implicates %1; the stations that remain stable together are %2. This subset is proposed, not adopted: the analysis did not proceed, because a moved block spreads its motion over every other station. Check the implicated pillars, then analyse again with them among the object points.</source>
            <translation>El bloque de referencia se movió. La localización implica a %1; las estaciones que permanecen estables en conjunto son %2. Este subconjunto se propone, no se adopta: el análisis no continuó, porque un bloque que se ha movido reparte su movimiento entre todas las demás estaciones. Revise los pilares implicados y analice de nuevo con ellos entre los puntos objeto.</translation>
        </message>
        <message>
            <source>The reference stations have not moved relative to one another at this confidence: the block is a sound datum for the displacements.</source>
            <translation>Las estaciones de referencia no se han movido unas respecto de otras con esta confianza: el bloque es un datum sólido para los desplazamientos.</translation>
        </message>
        <message>
            <source>The stations have no plan position to draw them at; see the table above.</source>
            <translation>Las estaciones no tienen posición planimétrica donde dibujarlas; vea la tabla anterior.</translation>
        </message>
        <message>
            <source>The transformation's accuracy enters every station alike, as a common translation: it cancels in displacements measured against the reference block and remains in an absolute one.</source>
            <translation>La exactitud de la transformación entra igual en todas las estaciones, como una traslación común: se cancela en los desplazamientos medidos contra el bloque de referencia y permanece en uno absoluto.</translation>
        </message>
        <message>
            <source>Time series</source>
            <translation>Series temporales</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>To epoch</source>
            <translation>A la época</translation>
        </message>
        <message>
            <source>Uncertainty</source>
            <translation>Incertidumbre</translation>
        </message>
        <message>
            <source>Uncertainty mode</source>
            <translation>Modo de incertidumbre</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Velocities</source>
            <translation>Velocidades</translation>
        </message>
        <message>
            <source>Version</source>
            <translation>Versión</translation>
        </message>
        <message>
            <source>Vertical</source>
            <translation>Vertical</translation>
        </message>
        <message>
            <source>alert</source>
            <translation>alerta</translation>
        </message>
        <message>
            <source>alert limit</source>
            <translation>límite de alerta</translation>
        </message>
        <message>
            <source>all</source>
            <translation>todas</translation>
        </message>
        <message>
            <source>arrows and ellipses exaggerated %1x; ellipses at %2% confidence</source>
            <translation>flechas y elipses exageradas %1x; elipses al %2% de confianza</translation>
        </message>
        <message>
            <source>band</source>
            <translation>banda</translation>
        </message>
        <message>
            <source>deforming</source>
            <translation>deformándose</translation>
        </message>
        <message>
            <source>displacement magnitude</source>
            <translation>magnitud del desplazamiento</translation>
        </message>
        <message>
            <source>east</source>
            <translation>este</translation>
        </message>
        <message>
            <source>epoch (decimal year)</source>
            <translation>época (año decimal)</translation>
        </message>
        <message>
            <source>fitted line</source>
            <translation>recta ajustada</translation>
        </message>
        <message>
            <source>height</source>
            <translation>altura</translation>
        </message>
        <message>
            <source>horizontal displacement</source>
            <translation>desplazamiento horizontal</translation>
        </message>
        <message>
            <source>moving as a rigid block</source>
            <translation>moviéndose como bloque rígido</translation>
        </message>
        <message>
            <source>no</source>
            <translation>no</translation>
        </message>
        <message>
            <source>north</source>
            <translation>norte</translation>
        </message>
        <message>
            <source>not significant</source>
            <translation>no significativo</translation>
        </message>
        <message>
            <source>object</source>
            <translation>objeto</translation>
        </message>
        <message>
            <source>offset (mm)</source>
            <translation>desplazamiento (mm)</translation>
        </message>
        <message>
            <source>passed</source>
            <translation>aprobó</translation>
        </message>
        <message>
            <source>reference</source>
            <translation>referencia</translation>
        </message>
        <message>
            <source>shipped with GeoComp</source>
            <translation>incluido con GeoComp</translation>
        </message>
        <message>
            <source>significant</source>
            <translation>significativo</translation>
        </message>
        <message>
            <source>significant motion</source>
            <translation>movimiento significativo</translation>
        </message>
        <message>
            <source>speed</source>
            <translation>rapidez</translation>
        </message>
        <message>
            <source>translation</source>
            <translation>traslación</translation>
        </message>
        <message>
            <source>translation and rotation</source>
            <translation>traslación y rotación</translation>
        </message>
        <message>
            <source>translation, rotation and scale</source>
            <translation>traslación, rotación y escala</translation>
        </message>
        <message>
            <source>up</source>
            <translation>altura</translation>
        </message>
        <message>
            <source>v %1 (mm/a)</source>
            <translation>v %1 (mm/a)</translation>
        </message>
        <message>
            <source>vertical displacement</source>
            <translation>desplazamiento vertical</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sí</translation>
        </message>
    </context>
    <context>
        <name>GeoCompPlugin</name>
        <message>
            <source>About GeoComp…</source>
            <translation>Acerca de GeoComp…</translation>
        </message>
        <message>
            <source>GeoComp</source>
            <translation>GeoComp</translation>
        </message>
        <message>
            <source>GeoComp Global Settings</source>
            <translation>Configuraciones Globales de GeoComp</translation>
        </message>
        <message>
            <source>Results panel</source>
            <translation>Panel de resultados</translation>
        </message>
        <message>
            <source>Run again: %1</source>
            <translation>Ejecutar de nuevo: %1</translation>
        </message>
        <message>
            <source>Run the last GeoComp algorithm again</source>
            <translation>Ejecutar de nuevo el último algoritmo de GeoComp</translation>
        </message>
        <message>
            <source>Time series panel</source>
            <translation>Panel de series temporales</translation>
        </message>
    </context>
    <context>
        <name>GeoCompPostgis</name>
        <message>
            <source>%1 rows copied; every table compared identical.</source>
            <translation>%1 filas copiadas; todas las tablas comparadas idénticas.</translation>
        </message>
        <message>
            <source>Copying %1 to %2</source>
            <translation>Copiando %1 a %2</translation>
        </message>
        <message>
            <source>Give a PostgreSQL connection and a schema.</source>
            <translation>Indique una conexión PostgreSQL y un esquema.</translation>
        </message>
        <message>
            <source>PostgreSQL connection</source>
            <translation>Conexión PostgreSQL</translation>
        </message>
        <message>
            <source>Schema</source>
            <translation>Esquema</translation>
        </message>
        <message>
            <source>The copy in %1 differs from the original in %2 place(s), listed above. Do not use it; delete it and report this.</source>
            <translation>La copia en %1 difiere del original en %2 punto(s), enumerados arriba. No la use; elimínela e informe del problema.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompPreAnalysis</name>
        <message>
            <source> mm</source>
            <translation> mm</translation>
        </message>
        <message>
            <source>%1 station(s), %2 observation(s), %3 degree(s) of freedom. Worst: %4 mm at %5.</source>
            <translation>%1 estación(es), %2 observación(es), %3 grado(s) de libertad. Peor: %4 mm en %5.</translation>
        </message>
        <message>
            <source>(none)</source>
            <translation>(ninguna)</translation>
        </message>
        <message>
            <source>Add station</source>
            <translation>Añadir estación</translation>
        </message>
        <message>
            <source>Azimuth</source>
            <translation>Acimut</translation>
        </message>
        <message>
            <source>Click on the map to…</source>
            <translation>Haga clic en el mapa para…</translation>
        </message>
        <message>
            <source>Connect</source>
            <translation>Conectar</translation>
        </message>
        <message>
            <source>Connect draws</source>
            <translation>Conectar dibuja</translation>
        </message>
        <message>
            <source>Design</source>
            <translation>Diseño</translation>
        </message>
        <message>
            <source>Direction</source>
            <translation>Dirección</translation>
        </message>
        <message>
            <source>Expected precision</source>
            <translation>Precisión esperada</translation>
        </message>
        <message>
            <source>Expected precision (ellipses exaggerated %1x)</source>
            <translation>Precisión esperada (elipses con exageración de %1x)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>GeoComp — Interactive pre-analysis</source>
            <translation>GeoComp — Preanálisis interactivo</translation>
        </message>
        <message>
            <source>Height difference</source>
            <translation>Desnivel</translation>
        </message>
        <message>
            <source>Horizontal distance</source>
            <translation>Distancia horizontal</translation>
        </message>
        <message>
            <source>Move</source>
            <translation>Mover</translation>
        </message>
        <message>
            <source>Nothing to evaluate yet.</source>
            <translation>Todavía no hay nada que evaluar.</translation>
        </message>
        <message>
            <source>Nothing to report.</source>
            <translation>Nada que informar.</translation>
        </message>
        <message>
            <source>Positional uncertainty (mm)</source>
            <translation>Incertidumbre posicional (mm)</translation>
        </message>
        <message>
            <source>Redo</source>
            <translation>Rehacer</translation>
        </message>
        <message>
            <source>Remove</source>
            <translation>Eliminar</translation>
        </message>
        <message>
            <source>Required precision</source>
            <translation>Precisión requerida</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieje mayor (mm)</translation>
        </message>
        <message>
            <source>Semi-minor (mm)</source>
            <translation>Semieje menor (mm)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Undo</source>
            <translation>Deshacer</translation>
        </message>
    </context>
    <context>
        <name>GeoCompProfiles</name>
        <message>
            <source>%1 (default)</source>
            <translation>%1 (predeterminado)</translation>
        </message>
        <message>
            <source>%1 added.</source>
            <translation>%1 añadido.</translation>
        </message>
        <message>
            <source>%1 copied to %2.</source>
            <translation>%1 copiado a %2.</translation>
        </message>
        <message>
            <source>%1 could not be read as instrument profiles: %2</source>
            <translation>%1 no se pudo leer como perfiles de instrumento: %2</translation>
        </message>
        <message>
            <source>%1 deleted.</source>
            <translation>%1 eliminado.</translation>
        </message>
        <message>
            <source>%1 does not exist yet. It is written there when saved.</source>
            <translation>%1 todavía no existe. La biblioteca se escribe en esa ubicación al guardar.</translation>
        </message>
        <message>
            <source>%1 is the default.</source>
            <translation>%1 es el predeterminado.</translation>
        </message>
        <message>
            <source>%1 profile(s) exported to %2.</source>
            <translation>%1 perfil(es) exportado(s) a %2.</translation>
        </message>
        <message>
            <source>%1 profile(s) imported.</source>
            <translation>%1 perfil(es) importado(s).</translation>
        </message>
        <message>
            <source>%1 profile(s) imported. Already in the library, and not replaced: %2.</source>
            <translation>%1 perfil(es) importado(s). Ya estaban en la biblioteca y no se reemplazaron: %2.</translation>
        </message>
        <message>
            <source>%1 updated.</source>
            <translation>%1 actualizado.</translation>
        </message>
        <message>
            <source>%1 — %2</source>
            <translation>%1 — %2</translation>
        </message>
        <message>
            <source>(not saved)</source>
            <translation>(no guardado)</translation>
        </message>
        <message>
            <source>Add…</source>
            <translation>Añadir…</translation>
        </message>
        <message>
            <source>Apply</source>
            <translation>Aplicar</translation>
        </message>
        <message>
            <source>Atmospheric model</source>
            <translation>Modelo atmosférico</translation>
        </message>
        <message>
            <source>Calibration certificate</source>
            <translation>Certificado de calibración</translation>
        </message>
        <message>
            <source>Calibration date</source>
            <translation>Fecha de calibración</translation>
        </message>
        <message>
            <source>Calibration factor</source>
            <translation>Factor de calibración</translation>
        </message>
        <message>
            <source>Collimation error (%1)</source>
            <translation>Error de colimación (%1)</translation>
        </message>
        <message>
            <source>Delete</source>
            <translation>Eliminar</translation>
        </message>
        <message>
            <source>Direction, one set (%1)</source>
            <translation>Dirección, una serie (%1)</translation>
        </message>
        <message>
            <source>Duplicate profile</source>
            <translation>Duplicar perfil</translation>
        </message>
        <message>
            <source>Duplicate…</source>
            <translation>Duplicar…</translation>
        </message>
        <message>
            <source>EDM additive constant (mm)</source>
            <translation>Constante aditiva del MED (mm)</translation>
        </message>
        <message>
            <source>EDM cyclic error amplitude (mm)</source>
            <translation>Amplitud del error cíclico del MED (mm)</translation>
        </message>
        <message>
            <source>EDM cyclic error wavelength (m)</source>
            <translation>Longitud de onda del error cíclico del MED (m)</translation>
        </message>
        <message>
            <source>EDM precision, constant part (mm)</source>
            <translation>Precisión del MED, parte constante (mm)</translation>
        </message>
        <message>
            <source>EDM precision, factor on the specification</source>
            <translation>Precisión del MED, factor sobre la especificación</translation>
        </message>
        <message>
            <source>EDM precision, proportional part (ppm)</source>
            <translation>Precisión del MED, parte proporcional (ppm)</translation>
        </message>
        <message>
            <source>EDM scale error (ppm)</source>
            <translation>Error de escala del MED (ppm)</translation>
        </message>
        <message>
            <source>Export profiles</source>
            <translation>Exportar perfiles</translation>
        </message>
        <message>
            <source>Export selected…</source>
            <translation>Exportar seleccionados…</translation>
        </message>
        <message>
            <source>GeoComp instrument profiles</source>
            <translation>Perfiles de instrumento de GeoComp</translation>
        </message>
        <message>
            <source>GeoComp instrument profiles (*.json)</source>
            <translation>Perfiles de instrumento de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Gravimeters</source>
            <translation>Gravímetros</translation>
        </message>
        <message>
            <source>Height difference, per root kilometre (mm)</source>
            <translation>Desnivel, por raíz de kilómetro (mm)</translation>
        </message>
        <message>
            <source>Height difference, per setup (mm)</source>
            <translation>Desnivel, por estacionamiento (mm)</translation>
        </message>
        <message>
            <source>Import profiles</source>
            <translation>Importar perfiles</translation>
        </message>
        <message>
            <source>Import…</source>
            <translation>Importar…</translation>
        </message>
        <message>
            <source>Instrument height (mm)</source>
            <translation>Altura del instrumento (mm)</translation>
        </message>
        <message>
            <source>Its standard deviation, in the same unit</source>
            <translation>Su desviación estándar, en la misma unidad</translation>
        </message>
        <message>
            <source>Largest imbalance along a line (m)</source>
            <translation>Mayor desbalance a lo largo de una línea (m)</translation>
        </message>
        <message>
            <source>Largest imbalance per setup (m)</source>
            <translation>Mayor desbalance por estacionamiento (m)</translation>
        </message>
        <message>
            <source>Levelling classes</source>
            <translation>Clases de nivelación</translation>
        </message>
        <message>
            <source>Levels</source>
            <translation>Niveles</translation>
        </message>
        <message>
            <source>Line-of-sight tilt (%1)</source>
            <translation>Inclinación de la línea de visual (%1)</translation>
        </message>
        <message>
            <source>Longest sight (m)</source>
            <translation>Visual más larga (m)</translation>
        </message>
        <message>
            <source>Manufacturer</source>
            <translation>Fabricante</translation>
        </message>
        <message>
            <source>Misclosure tolerance k, in k√L (mm)</source>
            <translation>Tolerancia de error de cierre k, en k√L (mm)</translation>
        </message>
        <message>
            <source>Model</source>
            <translation>Modelo</translation>
        </message>
        <message>
            <source>Name</source>
            <translation>Nombre</translation>
        </message>
        <message>
            <source>New</source>
            <translation>Nuevo</translation>
        </message>
        <message>
            <source>New profile</source>
            <translation>Nuevo perfil</translation>
        </message>
        <message>
            <source>One outer-wire reading (mm)</source>
            <translation>Una lectura de hilo extremo (mm)</translation>
        </message>
        <message>
            <source>One reading (µGal)</source>
            <translation>Una lectura (µGal)</translation>
        </message>
        <message>
            <source>One staff reading (mm)</source>
            <translation>Una lectura de mira (mm)</translation>
        </message>
        <message>
            <source>Open instrument profiles</source>
            <translation>Abrir perfiles de instrumento</translation>
        </message>
        <message>
            <source>Open…</source>
            <translation>Abrir…</translation>
        </message>
        <message>
            <source>Prism constant (mm)</source>
            <translation>Constante del prisma (mm)</translation>
        </message>
        <message>
            <source>Profile id</source>
            <translation>Id del perfil</translation>
        </message>
        <message>
            <source>Readings are</source>
            <translation>Las lecturas son</translation>
        </message>
        <message>
            <source>Reference refractive index</source>
            <translation>Índice de refracción de referencia</translation>
        </message>
        <message>
            <source>Reflectors</source>
            <translation>Reflectores</translation>
        </message>
        <message>
            <source>Save</source>
            <translation>Guardar</translation>
        </message>
        <message>
            <source>Save as…</source>
            <translation>Guardar como…</translation>
        </message>
        <message>
            <source>Save instrument profiles</source>
            <translation>Guardar perfiles de instrumento</translation>
        </message>
        <message>
            <source>Saved to %1.</source>
            <translation>Guardado en %1.</translation>
        </message>
        <message>
            <source>Serial number</source>
            <translation>Número de serie</translation>
        </message>
        <message>
            <source>Source document</source>
            <translation>Documento de origen</translation>
        </message>
        <message>
            <source>Stadia factor</source>
            <translation>Constante estadimétrica</translation>
        </message>
        <message>
            <source>Target height (mm)</source>
            <translation>Altura de la señal (mm)</translation>
        </message>
        <message>
            <source>The instrument applies its EDM constant</source>
            <translation>El instrumento aplica su constante del MED</translation>
        </message>
        <message>
            <source>The instrument applies the atmospheric correction</source>
            <translation>El instrumento aplica la corrección atmosférica</translation>
        </message>
        <message>
            <source>The instrument applies this constant</source>
            <translation>El instrumento aplica esta constante</translation>
        </message>
        <message>
            <source>The level removes its own tilt</source>
            <translation>El nivel elimina su propia inclinación</translation>
        </message>
        <message>
            <source>The profiles have changes that are not saved. Discard them?</source>
            <translation>Los perfiles tienen cambios sin guardar. ¿Descartarlos?</translation>
        </message>
        <message>
            <source>The readings have the tide removed</source>
            <translation>Las lecturas ya tienen la marea eliminada</translation>
        </message>
        <message>
            <source>Total stations</source>
            <translation>Estaciones totales</translation>
        </message>
        <message>
            <source>Trunnion axis tilt (%1)</source>
            <translation>Inclinación del eje secundario (%1)</translation>
        </message>
        <message>
            <source>Unsaved changes</source>
            <translation>Cambios sin guardar</translation>
        </message>
        <message>
            <source>Use as default</source>
            <translation>Usar como predeterminado</translation>
        </message>
        <message>
            <source>Vertical index error (%1)</source>
            <translation>Error de índice vertical (%1)</translation>
        </message>
        <message>
            <source>Zenith angle, one set (%1)</source>
            <translation>Ángulo cenital, una serie (%1)</translation>
        </message>
        <message>
            <source>Zenith angle, refraction term (%1 per km)</source>
            <translation>Ángulo cenital, término de refracción (%1 por km)</translation>
        </message>
        <message>
            <source>counter units, through a calibration table</source>
            <translation>unidades del contador, mediante una tabla de calibración</translation>
        </message>
        <message>
            <source>gravity</source>
            <translation>gravedad</translation>
        </message>
        <message>
            <source>± </source>
            <translation>± </translation>
        </message>
    </context>
    <context>
        <name>GeoCompPrompts</name>
        <message>
            <source>Choose a field book</source>
            <translation>Elija una libreta de campo</translation>
        </message>
        <message>
            <source>Field books (*.csv *.xlsx *.txt);;All files (*)</source>
            <translation>Libretas de campo (*.csv *.xlsx *.txt);;Todos los archivos (*)</translation>
        </message>
    </context>
    <context>
        <name>GeoCompReport</name>
        <message>
            <source>No redundancy: there are as many observations as unknowns, so the observations fit exactly by construction. Nothing in this result has been checked, neither the observations nor their precisions; the uncertainties are the stated precisions of the observations, propagated.</source>
            <translation>Sin redundancia: hay tantas observaciones como incógnitas, así que las observaciones se ajustan exactamente por construcción. Nada en este resultado se ha comprobado, ni las observaciones ni sus precisiones; las incertidumbres son las precisiones declaradas de las observaciones, propagadas.</translation>
        </message>
        <message>
            <source>not defined</source>
            <translation>no definido</translation>
        </message>
        <message>
            <source>not tested</source>
            <translation>no probado</translation>
        </message>
    </context>
    <context>
        <name>GeoCompResultsPanel</name>
        <message>
            <source>%1 solution(s) from %2.</source>
            <translation>%1 solución(es) de %2.</translation>
        </message>
        <message>
            <source>(superseded)</source>
            <translation>(sustituida)</translation>
        </message>
        <message>
            <source>Algorithm</source>
            <translation>Algoritmo</translation>
        </message>
        <message>
            <source>All observations</source>
            <translation>Todas las observaciones</translation>
        </message>
        <message>
            <source>Blunder candidate</source>
            <translation>Candidato a error grosero</translation>
        </message>
        <message>
            <source>Blunder candidates</source>
            <translation>Candidatos a error grosero</translation>
        </message>
        <message>
            <source>Condition number</source>
            <translation>Número de condición</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Constraints</source>
            <translation>Constricciones</translation>
        </message>
        <message>
            <source>Converged</source>
            <translation>Convergió</translation>
        </message>
        <message>
            <source>Coordinates</source>
            <translation>Coordenadas</translation>
        </message>
        <message>
            <source>Created</source>
            <translation>Creado en</translation>
        </message>
        <message>
            <source>Decision</source>
            <translation>Decisión</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>External reliability</source>
            <translation>Fiabilidad externa</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>Filter by observation id</source>
            <translation>Filtrar por el identificador de la observación</translation>
        </message>
        <message>
            <source>GeoComp project (*.gpkg)</source>
            <translation>Proyecto GeoComp (*.gpkg)</translation>
        </message>
        <message>
            <source>GeoComp results</source>
            <translation>Resultados de GeoComp</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iteraciones</translation>
        </message>
        <message>
            <source>Largest last correction</source>
            <translation>Mayor corrección en la última iteración</translation>
        </message>
        <message>
            <source>Lower critical value</source>
            <translation>Valor crítico inferior</translation>
        </message>
        <message>
            <source>MDB</source>
            <translation>MDB</translation>
        </message>
        <message>
            <source>Not tested</source>
            <translation>No probada</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Open project store</source>
            <translation>Abrir repositorio del proyecto</translation>
        </message>
        <message>
            <source>Open project store…</source>
            <translation>Abrir repositorio del proyecto…</translation>
        </message>
        <message>
            <source>Open solution</source>
            <translation>Abrir solución</translation>
        </message>
        <message>
            <source>Open solution…</source>
            <translation>Abrir solución…</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Passes the w-test</source>
            <translation>Pasa la prueba w</translation>
        </message>
        <message>
            <source>Positional uncertainty (m)</source>
            <translation>Incertidumbre posicional (m)</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reading the project store %1</source>
            <translation>Leyendo el repositorio del proyecto %1</translation>
        </message>
        <message>
            <source>Reading the solution %1</source>
            <translation>Leyendo la solución %1</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Residual</source>
            <translation>Residuo</translation>
        </message>
        <message>
            <source>Semi-major (m)</source>
            <translation>Semieje mayor (m)</translation>
        </message>
        <message>
            <source>Semi-minor (m)</source>
            <translation>Semieje menor (m)</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Standard deviations (m)</source>
            <translation>Desviaciones estándar (m)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Statistics</source>
            <translation>Estadísticas</translation>
        </message>
        <message>
            <source>Test statistic</source>
            <translation>Estadístico de prueba</translation>
        </message>
        <message>
            <source>The solution %1 could not be read: %2</source>
            <translation>No se pudo leer la solución %1: %2</translation>
        </message>
        <message>
            <source>This solution's uncertainties are approximate; its report names the strategies used.</source>
            <translation>Las incertidumbres de esta solución son aproximadas; su informe indica las estrategias usadas.</translation>
        </message>
        <message>
            <source>Uncertainty mode</source>
            <translation>Modo de incertidumbre</translation>
        </message>
        <message>
            <source>Uncheckable</source>
            <translation>No verificable</translation>
        </message>
        <message>
            <source>Uncheckable observations</source>
            <translation>Observaciones no verificables</translation>
        </message>
        <message>
            <source>Upper critical value</source>
            <translation>Valor crítico superior</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Variance factor</source>
            <translation>Factor de varianza</translation>
        </message>
        <message>
            <source>Variance factor, a posteriori</source>
            <translation>Factor de varianza, a posteriori</translation>
        </message>
        <message>
            <source>Variance factor, a priori</source>
            <translation>Factor de varianza, a priori</translation>
        </message>
        <message>
            <source>no</source>
            <translation>no</translation>
        </message>
        <message>
            <source>passed</source>
            <translation>aprobó</translation>
        </message>
        <message>
            <source>w</source>
            <translation>w</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sí</translation>
        </message>
    </context>
    <context>
        <name>GeoCompSettings</name>
        <message>
            <source>(not editable in this version)</source>
            <translation>(no editable en esta versión)</translation>
        </message>
        <message>
            <source>Additional download services (JSON)</source>
            <translation>Servicios de descarga adicionales (JSON)</translation>
        </message>
        <message>
            <source>Adjust lines that failed their tolerance</source>
            <translation>Ajustar líneas que no cumplieron la tolerancia</translation>
        </message>
        <message>
            <source>Advanced</source>
            <translation>Avanzado</translation>
        </message>
        <message>
            <source>Ambiguity ratio threshold</source>
            <translation>Umbral de la razón de ambigüedades</translation>
        </message>
        <message>
            <source>Angle decimal places</source>
            <translation>Decimales de los ángulos</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato de los ángulos</translation>
        </message>
        <message>
            <source>Angular tolerance per station (rad)</source>
            <translation>Tolerancia angular por estación (rad)</translation>
        </message>
        <message>
            <source>Antenna calibration file (ANTEX)</source>
            <translation>Archivo de calibración de antena (ANTEX)</translation>
        </message>
        <message>
            <source>Apply orthometric corrections</source>
            <translation>Aplicar correcciones ortométricas</translation>
        </message>
        <message>
            <source>Atmospheric model</source>
            <translation>Modelo atmosférico</translation>
        </message>
        <message>
            <source>Barrell and Sears</source>
            <translation>Barrell y Sears</translation>
        </message>
        <message>
            <source>Base map catalogue file</source>
            <translation>Archivo de catálogo de mapas base</translation>
        </message>
        <message>
            <source>Base map to offer</source>
            <translation>Mapa base a ofrecer</translation>
        </message>
        <message>
            <source>Base maps</source>
            <translation>Mapas base</translation>
        </message>
        <message>
            <source>Basic</source>
            <translation>Básico</translation>
        </message>
        <message>
            <source>Broadcast</source>
            <translation>Transmitidas</translation>
        </message>
        <message>
            <source>Broadcast model</source>
            <translation>Modelo de las efemérides transmitidas</translation>
        </message>
        <message>
            <source>Coefficient of refraction (k)</source>
            <translation>Coeficiente de refracción (k)</translation>
        </message>
        <message>
            <source>Collimation tolerance (rad)</source>
            <translation>Tolerancia de la colimación (rad)</translation>
        </message>
        <message>
            <source>Compass (Bowditch) rule</source>
            <translation>Regla de la brújula (Bowditch)</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Coordinate decimal places</source>
            <translation>Decimales de las coordenadas</translation>
        </message>
        <message>
            <source>Critical</source>
            <translation>Crítico</translation>
        </message>
        <message>
            <source>Debug</source>
            <translation>Depuración</translation>
        </message>
        <message>
            <source>Decimal degrees</source>
            <translation>Grados decimales</translation>
        </message>
        <message>
            <source>Default direction standard deviation (rad)</source>
            <translation>Desviación típica de las direcciones (rad)</translation>
        </message>
        <message>
            <source>Default geoid model file</source>
            <translation>Archivo del modelo geoidal predeterminado</translation>
        </message>
        <message>
            <source>Default pressure (hPa)</source>
            <translation>Presión por defecto (hPa)</translation>
        </message>
        <message>
            <source>Default reference epoch</source>
            <translation>Época de referencia predeterminada</translation>
        </message>
        <message>
            <source>Default relative humidity (%)</source>
            <translation>Humedad relativa por defecto (%)</translation>
        </message>
        <message>
            <source>Default slope-distance standard deviation (m)</source>
            <translation>Desviación típica de las distancias inclinadas (m)</translation>
        </message>
        <message>
            <source>Default temperature (degrees Celsius)</source>
            <translation>Temperatura por defecto (grados Celsius)</translation>
        </message>
        <message>
            <source>Default zenith-angle standard deviation (rad)</source>
            <translation>Desviación típica de los ángulos cenitales (rad)</translation>
        </message>
        <message>
            <source>Degrees, minutes, seconds</source>
            <translation>Grados, minutos, segundos</translation>
        </message>
        <message>
            <source>Distance unit</source>
            <translation>Unidad de distancia</translation>
        </message>
        <message>
            <source>Download services, in priority order (empty: never download)</source>
            <translation>Servicios de descarga, en orden de prioridad (vacío: no descargar nunca)</translation>
        </message>
        <message>
            <source>Downloads the DynAdjust release GeoComp was tested with, checks it against the digest recorded in GeoComp, and installs it in the QGIS profile.</source>
            <translation>Descarga la versión de DynAdjust con la que se probó GeoComp, la comprueba contra el resumen criptográfico registrado en GeoComp y la instala en el perfil de QGIS.</translation>
        </message>
        <message>
            <source>Drift polynomial degree</source>
            <translation>Grado del polinomio de deriva</translation>
        </message>
        <message>
            <source>Drift treatment</source>
            <translation>Tratamiento de la deriva</translation>
        </message>
        <message>
            <source>Dual-frequency (ionosphere-free)</source>
            <translation>Doble frecuencia (libre de ionosfera)</translation>
        </message>
        <message>
            <source>DynAdjust directory (empty: GeoComp's installation, then the system path)</source>
            <translation>Directorio de DynAdjust (vacío: la instalación de GeoComp, luego la ruta del sistema)</translation>
        </message>
        <message>
            <source>Elevation mask (degrees)</source>
            <translation>Máscara de elevación (grados)</translation>
        </message>
        <message>
            <source>English</source>
            <translation>Inglés</translation>
        </message>
        <message>
            <source>Ephemeris source</source>
            <translation>Fuente de las efemérides</translation>
        </message>
        <message>
            <source>Español</source>
            <translation>Español</translation>
        </message>
        <message>
            <source>Estimated (STEC)</source>
            <translation>Estimado (STEC)</translation>
        </message>
        <message>
            <source>Estimated with the station values</source>
            <translation>Estimada junto con los valores de las estaciones</translation>
        </message>
        <message>
            <source>Estimated zenith delay</source>
            <translation>Retardo cenital estimado</translation>
        </message>
        <message>
            <source>Estimated zenith delay with gradients</source>
            <translation>Retardo cenital estimado con gradientes</translation>
        </message>
        <message>
            <source>Face-pair distance tolerance (m; 0 = from the instrument's EDM)</source>
            <translation>Tolerancia de distancia entre caras (m; 0 = del MED del instrumento)</translation>
        </message>
        <message>
            <source>Fitted to base readings first</source>
            <translation>Ajustada antes a las lecturas de la base</translation>
        </message>
        <message>
            <source>Follow QGIS</source>
            <translation>Seguir a QGIS</translation>
        </message>
        <message>
            <source>Foot</source>
            <translation>Pie</translation>
        </message>
        <message>
            <source>From %1 to %2.</source>
            <translation>De %1 a %2.</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>GeoComp — Global Settings</source>
            <translation>GeoComp — Configuraciones Globales</translation>
        </message>
        <message>
            <source>Gon</source>
            <translation>Gon</translation>
        </message>
        <message>
            <source>Gravimeter</source>
            <translation>Gravímetro</translation>
        </message>
        <message>
            <source>Gravimeter profile library</source>
            <translation>Biblioteca de perfiles de gravímetro</translation>
        </message>
        <message>
            <source>Gravimetric factor (tide amplification)</source>
            <translation>Factor gravimétrico (amplificación de la marea)</translation>
        </message>
        <message>
            <source>Gravity display unit</source>
            <translation>Unidad de visualización de la gravedad</translation>
        </message>
        <message>
            <source>Height-difference weighting</source>
            <translation>Ponderación de los desniveles</translation>
        </message>
        <message>
            <source>IONEX map</source>
            <translation>Mapa IONEX</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Información</translation>
        </message>
        <message>
            <source>Install DynAdjust…</source>
            <translation>Instalar DynAdjust…</translation>
        </message>
        <message>
            <source>Instrument profile library</source>
            <translation>Biblioteca de perfiles de instrumento</translation>
        </message>
        <message>
            <source>Instrument profiles…</source>
            <translation>Perfiles de instrumento…</translation>
        </message>
        <message>
            <source>Interface</source>
            <translation>Interfaz</translation>
        </message>
        <message>
            <source>Ionospheric correction</source>
            <translation>Corrección ionosférica</translation>
        </message>
        <message>
            <source>Language</source>
            <translation>Idioma</translation>
        </message>
        <message>
            <source>Largest permitted imbalance per line (m)</source>
            <translation>Mayor desequilibrio permitido por línea (m)</translation>
        </message>
        <message>
            <source>Largest permitted imbalance per setup (m)</source>
            <translation>Mayor desequilibrio permitido por estacionamiento (m)</translation>
        </message>
        <message>
            <source>Leica</source>
            <translation>Leica</translation>
        </message>
        <message>
            <source>Level</source>
            <translation>Nivel</translation>
        </message>
        <message>
            <source>Level profile library</source>
            <translation>Biblioteca de perfiles de nivel</translation>
        </message>
        <message>
            <source>Log verbosity</source>
            <translation>Detalle del registro</translation>
        </message>
        <message>
            <source>Longest permitted sight (m)</source>
            <translation>Visual más larga permitida (m)</translation>
        </message>
        <message>
            <source>Longman (1959)</source>
            <translation>Longman (1959)</translation>
        </message>
        <message>
            <source>Metre</source>
            <translation>Metro</translation>
        </message>
        <message>
            <source>No settings in this section yet. They are added by the development phase that implements this equipment type.</source>
            <translation>Todavía no hay configuraciones en esta sección. Se añaden en la fase de desarrollo que implementa este tipo de equipo.</translation>
        </message>
        <message>
            <source>None</source>
            <translation>Ninguna</translation>
        </message>
        <message>
            <source>None (every instrument applies its own)</source>
            <translation>Ninguno (cada instrumento aplica el suyo)</translation>
        </message>
        <message>
            <source>None: report the misclosure only (least squares is Network adjustment)</source>
            <translation>Ninguna: solo informar del error de cierre (mínimos cuadrados es el Ajuste de red)</translation>
        </message>
        <message>
            <source>Not saved: these values are not numbers within their range: %1.</source>
            <translation>No guardado: estos valores no son números dentro de su intervalo: %1.</translation>
        </message>
        <message>
            <source>Not set — each run states its CRS</source>
            <translation>No definido — cada ejecución indica su SRC</translation>
        </message>
        <message>
            <source>Offer a base map when adding result layers</source>
            <translation>Ofrecer un mapa base al añadir capas de resultado</translation>
        </message>
        <message>
            <source>Outlier test significance level</source>
            <translation>Nivel de significancia de la prueba de errores groseros</translation>
        </message>
        <message>
            <source>Outlier test type II error rate</source>
            <translation>Tasa de error tipo II de la prueba de errores groseros</translation>
        </message>
        <message>
            <source>Override for this project: the value is saved in the project, travels with it, and applies to it alone.</source>
            <translation>Sobrescribir en este proyecto: el valor se guarda en el proyecto, viaja con él y solo se aplica a él.</translation>
        </message>
        <message>
            <source>Paths and engines</source>
            <translation>Rutas y motores</translation>
        </message>
        <message>
            <source>Permissible misclosure k, in m per root kilometre</source>
            <translation>Error de cierre admisible k, en m por raíz de kilómetro</translation>
        </message>
        <message>
            <source>Português (Brasil)</source>
            <translation>Portugués (Brasil)</translation>
        </message>
        <message>
            <source>Precise (IGS products)</source>
            <translation>Precisas (productos IGS)</translation>
        </message>
        <message>
            <source>Precise product directory</source>
            <translation>Directorio de productos precisos</translation>
        </message>
        <message>
            <source>Preferred coordinate reference system</source>
            <translation>Sistema de referencia de coordenadas preferido</translation>
        </message>
        <message>
            <source>Product cache (empty: the QGIS profile's folder)</source>
            <translation>Caché de productos (vacío: la carpeta del perfil de QGIS)</translation>
        </message>
        <message>
            <source>Proportional to line length</source>
            <translation>Proporcional a la longitud de la línea</translation>
        </message>
        <message>
            <source>Proportional to the number of setups</source>
            <translation>Proporcional al número de estacionamientos</translation>
        </message>
        <message>
            <source>RTKLIB rnx2rtkp program (empty: the system path)</source>
            <translation>Programa rnx2rtkp de RTKLIB (vacío: la ruta del sistema)</translation>
        </message>
        <message>
            <source>Radian</source>
            <translation>Radián</translation>
        </message>
        <message>
            <source>Reading precision floor, added in quadrature (m/s²)</source>
            <translation>Piso de precisión de las lecturas, sumado en cuadratura (m/s²)</translation>
        </message>
        <message>
            <source>Reference station database</source>
            <translation>Base de datos de estaciones de referencia</translation>
        </message>
        <message>
            <source>Reference systems</source>
            <translation>Sistemas de referencia</translation>
        </message>
        <message>
            <source>Required relative precision (1:N)</source>
            <translation>Precisión relativa exigida (1:N)</translation>
        </message>
        <message>
            <source>SBAS</source>
            <translation>SBAS</translation>
        </message>
        <message>
            <source>Saastamoinen</source>
            <translation>Saastamoinen</translation>
        </message>
        <message>
            <source>Settings resolve in the order: this run, this project, global, default.</source>
            <translation>Las configuraciones se resuelven en el orden: esta ejecución, este proyecto, global, predeterminado.</translation>
        </message>
        <message>
            <source>Show the GeoComp toolbar</source>
            <translation>Mostrar la barra de herramientas de GeoComp</translation>
        </message>
        <message>
            <source>Solid-Earth tide model</source>
            <translation>Modelo de marea terrestre</translation>
        </message>
        <message>
            <source>Stated accuracy of the geoid model (m)</source>
            <translation>Exactitud declarada del modelo geoidal (m)</translation>
        </message>
        <message>
            <source>Stochastic model</source>
            <translation>Modelo estocástico</translation>
        </message>
        <message>
            <source>Total Station</source>
            <translation>Estación Total</translation>
        </message>
        <message>
            <source>Total stations, reflectors, levels, levelling classes and gravimeters, as named profiles: add, edit, duplicate, delete, import and export them.</source>
            <translation>Estaciones totales, reflectores, niveles, clases de nivelación y gravímetros, como perfiles con nombre: añádalos, edítelos, duplíquelos, elimínelos, impórtelos y expórtelos.</translation>
        </message>
        <message>
            <source>Transit rule</source>
            <translation>Regla del tránsito</translation>
        </message>
        <message>
            <source>Traverse adjustment method</source>
            <translation>Método de ajuste de la poligonal</translation>
        </message>
        <message>
            <source>Trimble</source>
            <translation>Trimble</translation>
        </message>
        <message>
            <source>Tropospheric correction</source>
            <translation>Corrección troposférica</translation>
        </message>
        <message>
            <source>US survey foot</source>
            <translation>Pie topográfico estadounidense</translation>
        </message>
        <message>
            <source>Uncertainty of k</source>
            <translation>Incertidumbre de k</translation>
        </message>
        <message>
            <source>Uncertainty of the default pressure (hPa)</source>
            <translation>Incertidumbre de la presión por defecto (hPa)</translation>
        </message>
        <message>
            <source>Uncertainty of the default temperature (degrees Celsius)</source>
            <translation>Incertidumbre de la temperatura por defecto (grados Celsius)</translation>
        </message>
        <message>
            <source>Usage mode</source>
            <translation>Modo de uso</translation>
        </message>
        <message>
            <source>Use a base map already in the project, if there is one</source>
            <translation>Usar un mapa base ya presente en el proyecto, si lo hay</translation>
        </message>
        <message>
            <source>Use only the independent baseline subset</source>
            <translation>Usar solo el subconjunto independiente de líneas base</translation>
        </message>
        <message>
            <source>Use rapid orbits where final ones are not yet published</source>
            <translation>Usar órbitas rápidas donde las finales aún no se han publicado</translation>
        </message>
        <message>
            <source>Variance inflation for reciprocal sights</source>
            <translation>Inflación de la varianza para visuales recíprocas</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Advertencia</translation>
        </message>
        <message>
            <source>default</source>
            <translation>predeterminado</translation>
        </message>
        <message>
            <source>from %1</source>
            <translation>de %1</translation>
        </message>
        <message>
            <source>global</source>
            <translation>global</translation>
        </message>
        <message>
            <source>mGal</source>
            <translation>mGal</translation>
        </message>
        <message>
            <source>not found</source>
            <translation>no encontrado</translation>
        </message>
        <message>
            <source>this project</source>
            <translation>este proyecto</translation>
        </message>
        <message>
            <source>this run</source>
            <translation>esta ejecución</translation>
        </message>
        <message>
            <source>version %1, at %2</source>
            <translation>versión %1, en %2</translation>
        </message>
        <message>
            <source>µGal</source>
            <translation>µGal</translation>
        </message>
    </context>
    <context>
        <name>GeoCompStyles</name>
        <message>
            <source>Absolute value</source>
            <translation>Valor absoluto</translation>
        </message>
        <message>
            <source>Alert: a threshold crossed</source>
            <translation>Alerta: un umbral superado</translation>
        </message>
        <message>
            <source>Alert: a velocity threshold crossed</source>
            <translation>Alerta: un umbral de velocidad superado</translation>
        </message>
        <message>
            <source>Azimuth</source>
            <translation>Acimut</translation>
        </message>
        <message>
            <source>Blunder candidate</source>
            <translation>Candidato a error grosero</translation>
        </message>
        <message>
            <source>DGPS</source>
            <translation>DGPS</translation>
        </message>
        <message>
            <source>Dependent (no new information)</source>
            <translation>Dependiente (sin información nueva)</translation>
        </message>
        <message>
            <source>Direction</source>
            <translation>Dirección</translation>
        </message>
        <message>
            <source>Estimated</source>
            <translation>Estimada</translation>
        </message>
        <message>
            <source>Fixed</source>
            <translation>Fija</translation>
        </message>
        <message>
            <source>Fixed (ambiguities resolved)</source>
            <translation>Fija (ambigüedades resueltas)</translation>
        </message>
        <message>
            <source>Float</source>
            <translation>Flotante</translation>
        </message>
        <message>
            <source>Height difference</source>
            <translation>Desnivel</translation>
        </message>
        <message>
            <source>Held (datum)</source>
            <translation>Mantenida (datum)</translation>
        </message>
        <message>
            <source>Horizontal angle</source>
            <translation>Ángulo horizontal</translation>
        </message>
        <message>
            <source>Horizontal distance</source>
            <translation>Distancia horizontal</translation>
        </message>
        <message>
            <source>Independent</source>
            <translation>Independiente</translation>
        </message>
        <message>
            <source>MDB not a length (see the table)</source>
            <translation>MDB no es una longitud (ver la tabla)</translation>
        </message>
        <message>
            <source>No epoch stated</source>
            <translation>Sin época declarada</translation>
        </message>
        <message>
            <source>Not assessed</source>
            <translation>No evaluada</translation>
        </message>
        <message>
            <source>Not computed</source>
            <translation>No calculado</translation>
        </message>
        <message>
            <source>Not recorded</source>
            <translation>No registrado</translation>
        </message>
        <message>
            <source>Not significant</source>
            <translation>No significativo</translation>
        </message>
        <message>
            <source>Not testable</source>
            <translation>No comprobable</translation>
        </message>
        <message>
            <source>Not tested</source>
            <translation>No probada</translation>
        </message>
        <message>
            <source>Other</source>
            <translation>Otra</translation>
        </message>
        <message>
            <source>PPP</source>
            <translation>PPP</translation>
        </message>
        <message>
            <source>Passes the w-test</source>
            <translation>Pasa la prueba w</translation>
        </message>
        <message>
            <source>Relative only</source>
            <translation>Solo relativa</translation>
        </message>
        <message>
            <source>SBAS</source>
            <translation>SBAS</translation>
        </message>
        <message>
            <source>Significant motion</source>
            <translation>Movimiento significativo</translation>
        </message>
        <message>
            <source>Significant velocity</source>
            <translation>Velocidad significativa</translation>
        </message>
        <message>
            <source>Single (no differential)</source>
            <translation>Simple (sin diferencial)</translation>
        </message>
        <message>
            <source>Slope distance</source>
            <translation>Distancia inclinada</translation>
        </message>
        <message>
            <source>Uncheckable (r below 0.01)</source>
            <translation>No verificable (r por debajo de 0.01)</translation>
        </message>
        <message>
            <source>Uncheckable: no finite MDB</source>
            <translation>No verificable: sin MDB finito</translation>
        </message>
        <message>
            <source>Uncheckable: no finite effect</source>
            <translation>No verificable: sin efecto finito</translation>
        </message>
        <message>
            <source>Weighted</source>
            <translation>Ponderada</translation>
        </message>
        <message>
            <source>Zenith angle</source>
            <translation>Ángulo cenital</translation>
        </message>
        <message>
            <source>r 0.01 to 0.1</source>
            <translation>r de 0.01 a 0.1</translation>
        </message>
        <message>
            <source>r 0.1 to 0.3</source>
            <translation>r de 0.1 a 0.3</translation>
        </message>
        <message>
            <source>r 0.3 to 0.5</source>
            <translation>r de 0.3 a 0.5</translation>
        </message>
        <message>
            <source>r 0.5 to 1</source>
            <translation>r de 0.5 a 1</translation>
        </message>
        <message>
            <source>|w| 1 to 2</source>
            <translation>|w| de 1 a 2</translation>
        </message>
        <message>
            <source>|w| 2 to 3</source>
            <translation>|w| de 2 a 3</translation>
        </message>
        <message>
            <source>|w| 3 or more</source>
            <translation>|w| 3 o más</translation>
        </message>
        <message>
            <source>|w| below 1</source>
            <translation>|w| por debajo de 1</translation>
        </message>
    </context>
    <context>
        <name>GeoCompTimeSeries</name>
        <message>
            <source>%1 rows written.</source>
            <translation>%1 filas escritas.</translation>
        </message>
        <message>
            <source>%1 stations over %2 epochs; band %3% confidence.</source>
            <translation>%1 estaciones en %2 épocas; banda con %3% de confianza.</translation>
        </message>
        <message>
            <source>%1, epoch %2 (%3): %4 ± %5 mm</source>
            <translation>%1, época %2 (%3): %4 ± %5 mm</translation>
        </message>
        <message>
            <source>East</source>
            <translation>Este</translation>
        </message>
        <message>
            <source>Export CSV…</source>
            <translation>Exportar CSV…</translation>
        </message>
        <message>
            <source>Export image…</source>
            <translation>Exportar imagen…</translation>
        </message>
        <message>
            <source>Export the plot</source>
            <translation>Exportar el gráfico</translation>
        </message>
        <message>
            <source>Export the series</source>
            <translation>Exportar la serie</translation>
        </message>
        <message>
            <source>GeoComp monitoring document (*.json)</source>
            <translation>Documento de monitoreo GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp time series</source>
            <translation>Series temporales GeoComp</translation>
        </message>
        <message>
            <source>Height</source>
            <translation>Altura</translation>
        </message>
        <message>
            <source>North</source>
            <translation>Norte</translation>
        </message>
        <message>
            <source>Open a series document</source>
            <translation>Abrir un documento de serie</translation>
        </message>
        <message>
            <source>Open series…</source>
            <translation>Abrir serie…</translation>
        </message>
        <message>
            <source>Plot written.</source>
            <translation>Gráfico escrito.</translation>
        </message>
        <message>
            <source>Reading the series %1</source>
            <translation>Leyendo la serie %1</translation>
        </message>
        <message>
            <source>Select stations on a velocity layer, or open a series document.</source>
            <translation>Seleccione estaciones en una capa de velocidades, o abra un documento de serie.</translation>
        </message>
        <message>
            <source>The series document could not be read: %1</source>
            <translation>No se pudo leer el documento de la serie: %1</translation>
        </message>
        <message>
            <source>Up</source>
            <translation>Altura</translation>
        </message>
    </context>
    <context>
        <name>GeoCompTotalStation</name>
        <message>
            <source>'%1' contains no setups, so there is nothing to process.</source>
            <translation>'%1' no contiene estacionamientos, por lo que no hay nada que procesar.</translation>
        </message>
        <message>
            <source>'%1' could not be read as a field mapping: %2</source>
            <translation>No se pudo leer '%1' como una asignación de campos: %2</translation>
        </message>
        <message>
            <source>'%1' could not be read as an instrument profile library. %2</source>
            <translation>No se pudo leer '%1' como una biblioteca de perfiles de instrumento. %2</translation>
        </message>
        <message>
            <source>'%1' could not be read as readings: %2</source>
            <translation>No se pudo leer '%1' como lecturas: %2</translation>
        </message>
        <message>
            <source>'%1' does not contain a GeoComp document: its top level is not an object.</source>
            <translation>'%1' no contiene un documento de GeoComp: su nivel superior no es un objeto.</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp readings document. Run Import field book first, or choose the file it produced.</source>
            <translation>'%1' no es un documento de lecturas de GeoComp. Ejecute primero Importar libreta de campo, o elija el archivo que produjo.</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp reductions document. Run Generalised pre-processing first, or choose the file it produced.</source>
            <translation>'%1' no es un documento de reducciones de GeoComp. Ejecute primero el Preprocesamiento generalizado, o elija el archivo que produjo.</translation>
        </message>
        <message>
            <source>'%1' is not valid JSON: %2</source>
            <translation>'%1' no es un JSON válido: %2</translation>
        </message>
        <message>
            <source>'%1' was written by an earlier Generalised pre-processing, which did not record the instrument and target heights. A 3D network needs them: without them every zenith angle and slope distance would be adjusted as though it ran from mark to mark. Run Generalised pre-processing again on the readings.</source>
            <translation>'%1' fue escrito por una versión anterior del Preprocesamiento generalizado, que no registraba las alturas del instrumento y de la señal. Una red 3D las necesita: sin ellas, cada ángulo cenital y cada distancia inclinada se ajustaría como si se hubiera medido de marca a marca. Ejecute de nuevo el Preprocesamiento generalizado sobre las lecturas.</translation>
        </message>
        <message>
            <source>Blocking</source>
            <translation>Bloqueante</translation>
        </message>
        <message>
            <source>Code</source>
            <translation>Código</translation>
        </message>
        <message>
            <source>Finding</source>
            <translation>Hallazgo</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Información</translation>
        </message>
        <message>
            <source>Involves</source>
            <translation>Implica</translation>
        </message>
        <message>
            <source>No file was given for parameter '%1'.</source>
            <translation>No se indicó ningún archivo para el parámetro '%1'.</translation>
        </message>
        <message>
            <source>Nothing to report.</source>
            <translation>Nada que informar.</translation>
        </message>
        <message>
            <source>Severity</source>
            <translation>Severidad</translation>
        </message>
        <message>
            <source>The file '%1' does not exist.</source>
            <translation>El archivo '%1' no existe.</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Advertencia</translation>
        </message>
    </context>
    <context>
        <name>GravimetryNetworkAlgorithm</name>
        <message>
            <source>'%1' does not hold a number.</source>
            <translation>'%1' no contiene un número.</translation>
        </message>
        <message>
            <source>'%1' is not a known gravity. Write it as station=value in mGal, for example RG26=979197.5759, and add ±sigma to weight it as an absolute determination rather than hold it.</source>
            <translation>'%1' no es una gravedad conocida. Escríbala como estación=valor en mGal, por ejemplo RG26=979197.5759, y añada ±sigma para ponderarla como una determinación absoluta en lugar de fijarla.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts the readings &lt;i&gt;Pre-processing (scale, tide, drift)&lt;/i&gt; reduced: each session's occupations become gravity differences, absolute values enter weighted, and the result goes through the same global test, data snooping and reliability analysis as any other GeoComp adjustment.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Drift.&lt;/b&gt; Estimated with the station values by default, one polynomial per session: every re-occupation informs it, not only a base station's. &lt;i&gt;Fitted to base readings first&lt;/i&gt; is the classical field method, kept for comparison and for sessions that re-occupy nothing but their base. The differences carry their exact covariance either way: successive differences share an occupation and are correlated, and the calibration factor's uncertainty is common to every reading of an instrument.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Known gravity&lt;/b&gt; is entered as &lt;code&gt;station=value&lt;/code&gt; pairs in mGal, separated by commas or semicolons. With &lt;code&gt;±sigma&lt;/code&gt; the value is an absolute determination and is weighted by its uncertainty, for example &lt;code&gt;RG26=979197.5759±0.0106&lt;/code&gt;; without it the station is held exactly, which makes it the datum and every uncertainty relative to it. With none, the network is adjusted with an inner constraint and every value is relative to their mean; the report says which.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A value must refer to the mark.&lt;/b&gt; Give the pre-processing a sensor height, or readings taken 20 cm above the mark will differ from an absolute value quoted at it by about 60 µGal.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Uncheckable observations are listed by name.&lt;/b&gt; A gravity network is small and weakly redundant, and a difference with a redundancy near zero can hide a blunder no test will find. A lone absolute value is always one. The report lists them and the layers draw them in a colour of their own.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced readings&lt;/b&gt; &amp;mdash; the document pre-processing wrote. &lt;b&gt;Known gravity&lt;/b&gt; &amp;mdash; as above. &lt;b&gt;Drift treatment&lt;/b&gt; and &lt;b&gt;drift degree&lt;/b&gt; default to the Gravimeter settings.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Carry the correlation between differences&lt;/b&gt; (advanced) &amp;mdash; on by default. Off reproduces MCGravi and pyGrav, which treat the differences as independent, and the result records the assumption. &lt;b&gt;Confidence&lt;/b&gt;, &lt;b&gt;alpha&lt;/b&gt; and &lt;b&gt;beta&lt;/b&gt; &amp;mdash; for the tests.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON, in m/s². &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Gravity&lt;/b&gt; &amp;mdash; CSV. &lt;b&gt;Gravity stations&lt;/b&gt; and &lt;b&gt;Gravity differences&lt;/b&gt; &amp;mdash; layers, located where the readings were taken; values in the display unit of the Gravimeter settings, which a column names. Scalars: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; and &lt;code&gt;DATUM_DEFECT&lt;/code&gt; (of the relative observations alone).&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta las lecturas que el &lt;i&gt;Preprocesamiento (escala, marea, deriva)&lt;/i&gt; redujo: las ocupaciones de cada sesión se convierten en diferencias de gravedad, los valores absolutos entran ponderados, y el resultado pasa por la misma prueba global, data snooping y análisis de fiabilidad que cualquier otro ajuste de GeoComp.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Deriva.&lt;/b&gt; Estimada junto con los valores de las estaciones por defecto, un polinomio por sesión: toda reocupación contribuye, no solo las de una estación base. &lt;i&gt;Ajustada antes a las lecturas de la base&lt;/i&gt; es el método clásico de campo, conservado para comparar y para sesiones que no reocupan nada más que su base. Las diferencias llevan su covarianza exacta en ambos casos: las diferencias sucesivas comparten una ocupación y están correlacionadas, y la incertidumbre del factor de calibración es común a todas las lecturas de un instrumento.&lt;/p&gt;&lt;p&gt;La &lt;b&gt;gravedad conocida&lt;/b&gt; se introduce como pares &lt;code&gt;estación=valor&lt;/code&gt; en mGal, separados por comas o puntos y comas. Con &lt;code&gt;±sigma&lt;/code&gt; el valor es una determinación absoluta y se pondera por su incertidumbre, por ejemplo &lt;code&gt;RG26=979197.5759±0.0106&lt;/code&gt;; sin él la estación se mantiene fija exactamente, lo que la convierte en el datum y toda incertidumbre relativa a ella. Sin ninguna, la red se ajusta con una constricción interna y todo valor es relativo a su media; el informe dice cuál fue el caso.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Un valor debe referirse a la marca.&lt;/b&gt; Indique al preprocesamiento una altura del sensor, o las lecturas tomadas 20 cm por encima de la marca diferirán de un valor absoluto indicado en ella en unos 60 µGal.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las observaciones no verificables se enumeran por nombre.&lt;/b&gt; Una red gravimétrica es pequeña y poco redundante, y una diferencia con redundancia cercana a cero puede ocultar un error grosero que ninguna prueba encontrará. Un valor absoluto aislado siempre es una de ellas. El informe las enumera y las capas las dibujan con un color propio.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Lecturas reducidas&lt;/b&gt; &amp;mdash; el documento que escribió el preprocesamiento. &lt;b&gt;Gravedad conocida&lt;/b&gt; &amp;mdash; como arriba. &lt;b&gt;Tratamiento de la deriva&lt;/b&gt; y &lt;b&gt;grado de la deriva&lt;/b&gt; toman por defecto las configuraciones del Gravímetro.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Considerar la correlación entre diferencias&lt;/b&gt; (avanzado) &amp;mdash; activado por defecto. Desactivado reproduce MCGravi y pyGrav, que tratan las diferencias como independientes, y el resultado registra esa suposición. &lt;b&gt;Confianza&lt;/b&gt;, &lt;b&gt;alfa&lt;/b&gt; y &lt;b&gt;beta&lt;/b&gt; &amp;mdash; para las pruebas.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON, en m/s². &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Gravedad&lt;/b&gt; &amp;mdash; CSV. &lt;b&gt;Estaciones gravimétricas&lt;/b&gt; y &lt;b&gt;Diferencias de gravedad&lt;/b&gt; &amp;mdash; capas, ubicadas donde se tomaron las lecturas; valores en la unidad de visualización de las configuraciones del Gravímetro, que una columna indica. Escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; y &lt;code&gt;DATUM_DEFECT&lt;/code&gt; (solo de las observaciones relativas).&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjust relative and absolute gravity as a network, with each session's drift.</source>
            <translation>Ajusta gravedad relativa y absoluta como una red, con la deriva de cada sesión.</translation>
        </message>
        <message>
            <source>Adjusted gravity</source>
            <translation>Gravedad ajustada</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
        </message>
        <message>
            <source>Base residuals</source>
            <translation>Residuos de la base</translation>
        </message>
        <message>
            <source>CANDIDATE</source>
            <translation>CANDIDATA</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Candidates, not rejections. GeoComp never removes an observation on its own: in a monitoring network the change being measured is exactly what an automatic outlier remover would delete.</source>
            <translation>Candidatas, no rechazos. GeoComp nunca elimina una observación por su cuenta: en una red de monitoreo, el cambio que se está midiendo es exactamente lo que un eliminador automático de errores groseros borraría.</translation>
        </message>
        <message>
            <source>Carry the correlation between differences</source>
            <translation>Considerar la correlación entre diferencias</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Data snooping significance (alpha)</source>
            <translation>Significancia del data snooping (alfa)</translation>
        </message>
        <message>
            <source>Data snooping type II error rate (beta)</source>
            <translation>Tasa de error tipo II del data snooping (beta)</translation>
        </message>
        <message>
            <source>Datum</source>
            <translation>Datum</translation>
        </message>
        <message>
            <source>Datum defect of the differences</source>
            <translation>Deficiencia de datum de las diferencias</translation>
        </message>
        <message>
            <source>Datum: %1.</source>
            <translation>Datum: %1.</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Degrees of freedom %1; variance factor %2.</source>
            <translation>Grados de libertad %1; factor de varianza %2.</translation>
        </message>
        <message>
            <source>Determined by</source>
            <translation>Determinada por</translation>
        </message>
        <message>
            <source>Drift</source>
            <translation>Deriva</translation>
        </message>
        <message>
            <source>Drift of %1: %2 ± %3 %4 per hour.</source>
            <translation>Deriva de %1: %2 ± %3 %4 por hora.</translation>
        </message>
        <message>
            <source>Drift per hour, then per hour², … (%1)</source>
            <translation>Deriva por hora, luego por hora², … (%1)</translation>
        </message>
        <message>
            <source>Drift polynomial degree</source>
            <translation>Grado del polinomio de deriva</translation>
        </message>
        <message>
            <source>Drift treatment</source>
            <translation>Tratamiento de la deriva</translation>
        </message>
        <message>
            <source>Estimated with the station values</source>
            <translation>Estimada junto con los valores de las estaciones</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>Fitted to base readings first</source>
            <translation>Ajustada antes a las lecturas de la base</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>Gravimetric network adjustment</source>
            <translation>Ajuste de red gravimétrica</translation>
        </message>
        <message>
            <source>Gravity</source>
            <translation>Gravedad</translation>
        </message>
        <message>
            <source>Gravity differences</source>
            <translation>Diferencias de gravedad</translation>
        </message>
        <message>
            <source>Gravity differences (%1)</source>
            <translation>Diferencias de gravedad (%1)</translation>
        </message>
        <message>
            <source>Gravity stations</source>
            <translation>Estaciones gravimétricas</translation>
        </message>
        <message>
            <source>Gravity stations (%1)</source>
            <translation>Estaciones gravimétricas (%1)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Instrument</source>
            <translation>Instrumento</translation>
        </message>
        <message>
            <source>Known gravity (mGal)</source>
            <translation>Gravedad conocida (mGal)</translation>
        </message>
        <message>
            <source>MDB</source>
            <translation>MDB</translation>
        </message>
        <message>
            <source>No blunder in these could be detected, whatever the tests below say: %1. A lone absolute value and a station reached by one difference are the usual cases. Re-observe or add a connection to make them checkable.</source>
            <translation>Ningún error grosero en estas podría detectarse, digan lo que digan las pruebas de abajo: %1. Un valor absoluto aislado y una estación alcanzada por una sola diferencia son los casos habituales. Vuelva a observar o añada una conexión para hacerlas verificables.</translation>
        </message>
        <message>
            <source>Not testable</source>
            <translation>No comprobable</translation>
        </message>
        <message>
            <source>Notes</source>
            <translation>Notas</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Occupations</source>
            <translation>Ocupaciones</translation>
        </message>
        <message>
            <source>Outlier candidate: %1 (w = %2).</source>
            <translation>Candidato a error grosero: %1 (w = %2).</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Readings</source>
            <translation>Lecturas</translation>
        </message>
        <message>
            <source>Reduced readings</source>
            <translation>Lecturas reducidas</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Residual</source>
            <translation>Residuo</translation>
        </message>
        <message>
            <source>Row</source>
            <translation>Fila</translation>
        </message>
        <message>
            <source>Session</source>
            <translation>Sesión</translation>
        </message>
        <message>
            <source>Sessions</source>
            <translation>Sesiones</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Summary</source>
            <translation>Resumen</translation>
        </message>
        <message>
            <source>The global test failed. Either the observations disagree more than their weights allow, or the weights are wrong — the test cannot distinguish the two. A reading's own standard error knows nothing of tilt, temperature or transport; a precision floor in pre-processing is the usual remedy, and the report of the run that used one says so.</source>
            <translation>La prueba global falló. O las observaciones discrepan más de lo que sus pesos permiten, o los pesos son incorrectos — la prueba no puede distinguir ambos casos. El error estándar de una lectura no sabe nada de inclinación, temperatura ni transporte; un piso de precisión en el preprocesamiento es el remedio habitual, y el informe de la ejecución que lo usó lo dice.</translation>
        </message>
        <message>
            <source>The global test failed. Either the observations disagree with each other more than their weights allow, or the weights are wrong — the test cannot tell you which.</source>
            <translation>La prueba global falló. O las observaciones difieren entre sí más de lo que sus pesos permiten, o los pesos son incorrectos — la prueba no distingue ambos casos.</translation>
        </message>
        <message>
            <source>The station '%1' is given a known gravity twice.</source>
            <translation>A la estación '%1' se le dio una gravedad conocida dos veces.</translation>
        </message>
        <message>
            <source>Tide system</source>
            <translation>Sistema de marea</translation>
        </message>
        <message>
            <source>Treatment</source>
            <translation>Tratamiento</translation>
        </message>
        <message>
            <source>Uncertainty</source>
            <translation>Incertidumbre</translation>
        </message>
        <message>
            <source>Uncheckable observations</source>
            <translation>Observaciones no verificables</translation>
        </message>
        <message>
            <source>Uncheckable: %1. No blunder in it could be detected.</source>
            <translation>No verificable: %1. Ningún error grosero en ella podría detectarse.</translation>
        </message>
        <message>
            <source>Units</source>
            <translation>Unidades</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Values are shown in %1, as the Gravimeter settings ask. The solution stores m/s².</source>
            <translation>Los valores se muestran en %1, como piden las configuraciones del Gravímetro. La solución almacena m/s².</translation>
        </message>
        <message>
            <source>Variance factor</source>
            <translation>Factor de varianza</translation>
        </message>
        <message>
            <source>absolute value and differences</source>
            <translation>valor absoluto y diferencias</translation>
        </message>
        <message>
            <source>accepted</source>
            <translation>aceptada</translation>
        </message>
        <message>
            <source>approximate: %1</source>
            <translation>aproximada: %1</translation>
        </message>
        <message>
            <source>differences</source>
            <translation>diferencias</translation>
        </message>
        <message>
            <source>estimated with the station values</source>
            <translation>estimada junto con los valores de las estaciones</translation>
        </message>
        <message>
            <source>fitted to base %1 first</source>
            <translation>ajustada antes a la base %1</translation>
        </message>
        <message>
            <source>held</source>
            <translation>fijada</translation>
        </message>
        <message>
            <source>not computed</source>
            <translation>no calculado</translation>
        </message>
        <message>
            <source>not testable</source>
            <translation>no comprobable</translation>
        </message>
        <message>
            <source>passed</source>
            <translation>aprobó</translation>
        </message>
        <message>
            <source>rigorous</source>
            <translation>rigurosa</translation>
        </message>
        <message>
            <source>sigma</source>
            <translation>sigma</translation>
        </message>
        <message>
            <source>w</source>
            <translation>w</translation>
        </message>
        <message>
            <source>w-test</source>
            <translation>prueba w</translation>
        </message>
    </context>
    <context>
        <name>GravimetryPreprocessAlgorithm</name>
        <message>
            <source>&lt;p&gt;Reads a relative gravimeter file and reduces every reading: through the instrument's &lt;b&gt;calibration&lt;/b&gt;, with the &lt;b&gt;solid-Earth tide&lt;/b&gt; removed, and to the &lt;b&gt;mark&lt;/b&gt;. The result is a document the network adjustment reads.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Formats.&lt;/b&gt; A Scintrex CG-5 text export, whose header gives the location, the clock's GMT difference and whether the instrument removed the tide itself; a ZLS Burris export; or a CSV with the columns &lt;code&gt;station&lt;/code&gt;, &lt;code&gt;time&lt;/code&gt; (ISO 8601 with its UTC offset) and &lt;code&gt;reading_mgal&lt;/code&gt;, and optionally &lt;code&gt;sd_mgal&lt;/code&gt;, &lt;code&gt;instrument&lt;/code&gt;, &lt;code&gt;session&lt;/code&gt;, &lt;code&gt;latitude_deg&lt;/code&gt;, &lt;code&gt;longitude_deg&lt;/code&gt;, &lt;code&gt;height_m&lt;/code&gt;, &lt;code&gt;sensor_height_m&lt;/code&gt; and &lt;code&gt;tide_applied&lt;/code&gt;. The format is recognised from the content.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The tide is removed once.&lt;/b&gt; An instrument that applied its own correction keeps it. Ask for GeoComp's instead and the instrument's is added back first; that needs the file's times in UTC, and GeoComp settles which way a CG-5's GMT difference runs by comparing the instrument's tide with its own under both readings. Longman's model agrees with ETERNA to about 1.5 µGal, and that figure is carried as the tide's uncertainty.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Drift is shown here and estimated in the network.&lt;/b&gt; For each session the log and the drift table give the drift its base readings show, and whether the session's re-occupations let the network estimate it jointly with the station values. Nothing is subtracted from the readings.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Gravimeter file&lt;/b&gt;. &lt;b&gt;Gravimeter profiles&lt;/b&gt; &amp;mdash; a profile library whose gravimeters carry each instrument's calibration table and factor, keyed by the instrument name the file uses (for a CG-5, &lt;code&gt;CG-5&lt;/code&gt; and its serial number, e.g. &lt;code&gt;CG-5 40236&lt;/code&gt;). Without one, each instrument's own scale is used, and the result is labelled approximate for it.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Precision floor&lt;/b&gt; (mGal) &amp;mdash; added in quadrature to each reading's own precision, for what that figure knows nothing of: tilt, temperature, transport. A CG-5's precision is &lt;code&gt;SD / &amp;radic;DUR&lt;/code&gt;; a Burris states none and takes the floor alone. Zero adds nothing.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sensor height&lt;/b&gt; (m) &amp;mdash; above the mark, for readings that do not carry their own. Left empty, readings are taken to refer to the mark, and the notes say so: an absolute value quoted at the mark and readings taken 20 cm above it differ by about 60 µGal.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Replace the instrument's tide&lt;/b&gt; &amp;mdash; as above. &lt;b&gt;UTC offset&lt;/b&gt; (hours, advanced) &amp;mdash; the file's local time minus UTC, when it should not be inferred.&lt;/p&gt;&lt;p&gt;The tide model, the gravimetric factor and the drift degree default to the Gravimeter settings.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced readings&lt;/b&gt; &amp;mdash; JSON, in SI, with the profiles the readings were reduced with. &lt;b&gt;Corrections&lt;/b&gt; &amp;mdash; CSV, one row per reading, in the display unit. &lt;b&gt;Drift&lt;/b&gt; &amp;mdash; CSV, one row per session; the coefficients are per hour to the power of the degree. Scalars: &lt;code&gt;READING_COUNT&lt;/code&gt;, &lt;code&gt;OCCUPATION_COUNT&lt;/code&gt;, &lt;code&gt;SESSION_COUNT&lt;/code&gt;, &lt;code&gt;UNESTIMABLE_SESSIONS&lt;/code&gt; (sessions whose drift the network cannot estimate jointly) and &lt;code&gt;LARGEST_TIDE&lt;/code&gt; in m/s².&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee un archivo de gravímetro relativo y reduce cada lectura: por la &lt;b&gt;calibración&lt;/b&gt; del instrumento, con la &lt;b&gt;marea terrestre&lt;/b&gt; eliminada, y a la &lt;b&gt;marca&lt;/b&gt;. El resultado es un documento que lee el ajuste de la red.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Formatos.&lt;/b&gt; Una exportación de texto del Scintrex CG-5, cuya cabecera indica la ubicación, la diferencia GMT del reloj y si el instrumento eliminó la marea por su cuenta; una exportación del ZLS Burris; o un CSV con las columnas &lt;code&gt;station&lt;/code&gt;, &lt;code&gt;time&lt;/code&gt; (ISO 8601 con su desfase respecto a UTC) y &lt;code&gt;reading_mgal&lt;/code&gt;, y opcionalmente &lt;code&gt;sd_mgal&lt;/code&gt;, &lt;code&gt;instrument&lt;/code&gt;, &lt;code&gt;session&lt;/code&gt;, &lt;code&gt;latitude_deg&lt;/code&gt;, &lt;code&gt;longitude_deg&lt;/code&gt;, &lt;code&gt;height_m&lt;/code&gt;, &lt;code&gt;sensor_height_m&lt;/code&gt; y &lt;code&gt;tide_applied&lt;/code&gt;. El formato se reconoce por el contenido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La marea se elimina una vez.&lt;/b&gt; Un instrumento que aplicó su propia corrección la conserva. Pida la de GeoComp en su lugar y la del instrumento se vuelve a sumar primero; eso exige las horas del archivo en UTC, y GeoComp determina el sentido de la diferencia GMT de un CG-5 comparando la marea del instrumento con la suya bajo ambas interpretaciones. El modelo de Longman concuerda con ETERNA en unos 1,5 µGal, y esa cifra se lleva como la incertidumbre de la marea.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La deriva se muestra aquí y se estima en la red.&lt;/b&gt; Para cada sesión, el registro y la tabla de deriva dan la deriva que muestran las lecturas de la base, y si las reocupaciones de la sesión permiten que la red la estime junto con los valores de las estaciones. No se resta nada de las lecturas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Archivo del gravímetro&lt;/b&gt;. &lt;b&gt;Perfiles de gravímetro&lt;/b&gt; &amp;mdash; una biblioteca de perfiles cuyos gravímetros llevan la tabla y el factor de calibración de cada instrumento, identificados por el nombre de instrumento que usa el archivo (para un CG-5, &lt;code&gt;CG-5&lt;/code&gt; y su número de serie, p. ej. &lt;code&gt;CG-5 40236&lt;/code&gt;). Sin ella, se usa la escala propia de cada instrumento, y el resultado se marca como aproximado por ello.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Piso de precisión&lt;/b&gt; (mGal) &amp;mdash; sumado en cuadratura a la precisión propia de cada lectura, por lo que esa cifra ignora: inclinación, temperatura, transporte. La precisión de un CG-5 es &lt;code&gt;SD / &amp;radic;DUR&lt;/code&gt;; un Burris no indica ninguna y usa solo el piso. Cero no suma nada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura del sensor&lt;/b&gt; (m) &amp;mdash; sobre la marca, para lecturas que no traen la suya. Si se deja vacía, se considera que las lecturas se refieren a la marca, y las notas lo dicen: un valor absoluto indicado en la marca y lecturas tomadas 20 cm por encima difieren en unos 60 µGal.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sustituir la marea del instrumento&lt;/b&gt; &amp;mdash; como arriba. &lt;b&gt;Desfase UTC&lt;/b&gt; (horas, avanzado) &amp;mdash; la hora local del archivo menos UTC, cuando no debe inferirse.&lt;/p&gt;&lt;p&gt;El modelo de marea, el factor gravimétrico y el grado de la deriva toman por defecto las configuraciones del Gravímetro.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Lecturas reducidas&lt;/b&gt; &amp;mdash; JSON, en SI, con los perfiles con que se redujeron las lecturas. &lt;b&gt;Correcciones&lt;/b&gt; &amp;mdash; CSV, una fila por lectura, en la unidad de visualización. &lt;b&gt;Deriva&lt;/b&gt; &amp;mdash; CSV, una fila por sesión; los coeficientes son por hora elevada al grado. Escalares: &lt;code&gt;READING_COUNT&lt;/code&gt;, &lt;code&gt;OCCUPATION_COUNT&lt;/code&gt;, &lt;code&gt;SESSION_COUNT&lt;/code&gt;, &lt;code&gt;UNESTIMABLE_SESSIONS&lt;/code&gt; (sesiones cuya deriva la red no puede estimar conjuntamente) y &lt;code&gt;LARGEST_TIDE&lt;/code&gt; en m/s².&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Corrections</source>
            <translation>Correcciones</translation>
        </message>
        <message>
            <source>Drift</source>
            <translation>Deriva</translation>
        </message>
        <message>
            <source>Drift polynomial degree</source>
            <translation>Grado del polinomio de deriva</translation>
        </message>
        <message>
            <source>GeoComp gravity readings (*.json)</source>
            <translation>Lecturas gravimétricas de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Gravimeter file</source>
            <translation>Archivo del gravímetro</translation>
        </message>
        <message>
            <source>Gravimeter profiles</source>
            <translation>Perfiles de gravímetro</translation>
        </message>
        <message>
            <source>Gravimetric factor (tide amplification)</source>
            <translation>Factor gravimétrico (amplificación de la marea)</translation>
        </message>
        <message>
            <source>Local time minus UTC (hours)</source>
            <translation>Hora local menos UTC (horas)</translation>
        </message>
        <message>
            <source>Longman (1959)</source>
            <translation>Longman (1959)</translation>
        </message>
        <message>
            <source>None (every instrument applies its own)</source>
            <translation>Ninguno (cada instrumento aplica el suyo)</translation>
        </message>
        <message>
            <source>Pre-processing (scale, tide, drift)</source>
            <translation>Preprocesamiento (escala, marea, deriva)</translation>
        </message>
        <message>
            <source>Precision floor (mGal)</source>
            <translation>Piso de precisión (mGal)</translation>
        </message>
        <message>
            <source>Read a gravimeter file, apply its calibration, remove the tide, and show each session's drift.</source>
            <translation>Lee un archivo de gravímetro, aplica su calibración, elimina la marea y muestra la deriva de cada sesión.</translation>
        </message>
        <message>
            <source>Reduced readings</source>
            <translation>Lecturas reducidas</translation>
        </message>
        <message>
            <source>Replace the instrument's tide correction with GeoComp's</source>
            <translation>Sustituir la corrección de marea del instrumento por la de GeoComp</translation>
        </message>
        <message>
            <source>Sensor height above the mark (m)</source>
            <translation>Altura del sensor sobre la marca (m)</translation>
        </message>
        <message>
            <source>Sensor height standard deviation (m)</source>
            <translation>Desviación estándar de la altura del sensor (m)</translation>
        </message>
        <message>
            <source>Session %1 re-occupies no station at enough different times: the network cannot estimate its drift with the station values. Pre-correct it from a base, or re-occupy a station.</source>
            <translation>La sesión %1 no reocupa ninguna estación en suficientes instantes distintos: la red no puede estimar su deriva junto con los valores de las estaciones. Precorríjala a partir de una base, o reocupe una estación.</translation>
        </message>
        <message>
            <source>Session %1: %2 ± %3 %4 per hour from %5 readings of %6.</source>
            <translation>Sesión %1: %2 ± %3 %4 por hora a partir de %5 lecturas de %6.</translation>
        </message>
        <message>
            <source>Tide model</source>
            <translation>Modelo de marea</translation>
        </message>
    </context>
    <context>
        <name>ImportFieldBookAlgorithm</name>
        <message>
            <source>%1 record(s) read into %2 setup(s); %3 rejected.</source>
            <translation>%1 registro(s) leído(s) en %2 estacionamiento(s); %3 rechazado(s).</translation>
        </message>
        <message>
            <source>%1 record(s) were rejected; see the findings.</source>
            <translation>%1 registro(s) fueron rechazados; consulte los hallazgos.</translation>
        </message>
        <message>
            <source>(constant %1)</source>
            <translation>(constante %1)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads a total-station field book from a CSV file and writes a GeoComp readings document the other Total Station algorithms take as input.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The field mapping is a saved, reusable object.&lt;/b&gt; The same organisation imports the same instrument export layout every week, and re-mapping columns by hand each time is exactly the manual handling this plugin exists to remove. Leave the mapping empty and GeoComp infers one from the header, which is right for the layouts it recognises; the report then states every column it mapped, so an inferred mapping is never silently trusted.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Every bad record is reported and none stops the import.&lt;/b&gt; A field book with six problems needs one run and produces six findings, each naming its source row.&lt;/p&gt;&lt;p&gt;An uncertainty is attached to every reading here, at the boundary, from the instrument profile or from the per-type defaults below. Where neither supplies one the import refuses: GeoComp does not invent a standard deviation, because a fabricated weight silently corrupts every statistic computed from it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Field book&lt;/b&gt; &amp;mdash; the CSV file. &lt;b&gt;Field mapping&lt;/b&gt; &amp;mdash; a saved mapping document (JSON); empty infers one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt; &amp;mdash; a profile library (JSON). Empty uses a generic total station of 2 mm + 2 ppm and 5 arcseconds, and everything computed from it is marked approximate.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Default direction, zenith and distance precision&lt;/b&gt; &amp;mdash; used where the instrument profile supplies none. In radians and metres; 0 means not configured.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fail if any record was rejected&lt;/b&gt; &amp;mdash; when set, a rejected record stops the algorithm, so a model does not carry on with a partial import.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Readings&lt;/b&gt; &amp;mdash; the JSON document. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Findings&lt;/b&gt; &amp;mdash; CSV, one row per problem. Scalars: &lt;code&gt;RECORD_COUNT&lt;/code&gt;, &lt;code&gt;SETUP_COUNT&lt;/code&gt; and &lt;code&gt;REJECTED_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee una libreta de campo de estación total desde un archivo CSV y escribe un documento de lecturas de GeoComp que los demás algoritmos de Estación Total toman como entrada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La asignación de campos es un objeto guardado y reutilizable.&lt;/b&gt; La misma organización importa el mismo formato de exportación del instrumento cada semana, y reasignar columnas a mano cada vez es exactamente la manipulación manual que este complemento existe para eliminar. Deje la asignación vacía y GeoComp infiere una a partir del encabezado, lo cual es correcto para los formatos que reconoce; el informe declara entonces cada columna que asignó, de modo que una asignación inferida nunca se confía en silencio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Todo registro defectuoso se comunica y ninguno detiene la importación.&lt;/b&gt; Una libreta con seis problemas requiere una ejecución y produce seis hallazgos, cada uno nombrando su fila de origen.&lt;/p&gt;&lt;p&gt;Se adjunta una incertidumbre a cada lectura aquí, en la frontera, a partir del perfil del instrumento o de los valores por omisión por tipo de abajo. Donde ninguno de los dos la aporta, la importación se niega: GeoComp no inventa una desviación típica, porque un peso fabricado corrompe en silencio toda estadística calculada a partir de él.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Libreta de campo&lt;/b&gt; &amp;mdash; el archivo CSV. &lt;b&gt;Asignación de campos&lt;/b&gt; &amp;mdash; un documento de asignación guardado (JSON); vacío infiere uno.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt; &amp;mdash; una biblioteca de perfiles (JSON). Vacío utiliza una estación total genérica de 2 mm + 2 ppm y 5 segundos de arco, y todo lo calculado a partir de ella se marca como aproximado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Precisión por omisión de dirección, cenital y de distancia&lt;/b&gt; &amp;mdash; se usan donde el perfil del instrumento no aporta ninguna. En radianes y metros; 0 significa no configurado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fallar si se rechaza algún registro&lt;/b&gt; &amp;mdash; cuando se marca, un registro rechazado detiene el algoritmo, de modo que un modelo no prosiga con una importación parcial.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Lecturas&lt;/b&gt; &amp;mdash; el documento JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Hallazgos&lt;/b&gt; &amp;mdash; CSV, una fila por problema. Escalares: &lt;code&gt;RECORD_COUNT&lt;/code&gt;, &lt;code&gt;SETUP_COUNT&lt;/code&gt; y &lt;code&gt;REJECTED_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato del ángulo</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Column not mapped</source>
            <translation>Columna no asignada</translation>
        </message>
        <message>
            <source>Columns not mapped, and therefore not imported: %1</source>
            <translation>Columnas no asignadas, y por tanto no importadas: %1</translation>
        </message>
        <message>
            <source>Default direction precision (rad)</source>
            <translation>Precisión por omisión de las direcciones (rad)</translation>
        </message>
        <message>
            <source>Default distance precision (m)</source>
            <translation>Precisión por omisión de las distancias (m)</translation>
        </message>
        <message>
            <source>Default zenith angle precision (rad)</source>
            <translation>Precisión por omisión de los ángulos cenitales (rad)</translation>
        </message>
        <message>
            <source>Fail if any record was rejected</source>
            <translation>Fallar si se rechaza algún registro</translation>
        </message>
        <message>
            <source>Field book</source>
            <translation>Libreta de campo</translation>
        </message>
        <message>
            <source>Field book import report</source>
            <translation>Informe de importación de la libreta de campo</translation>
        </message>
        <message>
            <source>Field books (*.csv *.xlsx);;All files (*)</source>
            <translation>Libretas de campo (*.csv *.xlsx);;Todos los archivos (*)</translation>
        </message>
        <message>
            <source>Field mapping</source>
            <translation>Asignación de campos</translation>
        </message>
        <message>
            <source>Field mapping used</source>
            <translation>Asignación de campos utilizada</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_import_fieldbook</source>
            <translation>Generado por GeoComp — geocomp:totalstation_import_fieldbook</translation>
        </message>
        <message>
            <source>GeoComp field</source>
            <translation>Campo de GeoComp</translation>
        </message>
        <message>
            <source>GeoComp readings (*.json)</source>
            <translation>Lecturas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Import</source>
            <translation>Importación</translation>
        </message>
        <message>
            <source>Import field book</source>
            <translation>Importar libreta de campo</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfiles de instrumento</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedad</translation>
        </message>
        <message>
            <source>Read a CSV field book through a saved, reusable field mapping.</source>
            <translation>Lee una libreta de campo en CSV mediante una asignación de campos guardada y reutilizable.</translation>
        </message>
        <message>
            <source>Reading '%1' with mapping '%2'…</source>
            <translation>Leyendo '%1' con la asignación '%2'…</translation>
        </message>
        <message>
            <source>Readings</source>
            <translation>Lecturas</translation>
        </message>
        <message>
            <source>Records</source>
            <translation>Registros</translation>
        </message>
        <message>
            <source>Rejected records</source>
            <translation>Registros rechazados</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Rows read</source>
            <translation>Filas leídas</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Source column</source>
            <translation>Columna de origen</translation>
        </message>
        <message>
            <source>The field book '%1' does not exist.</source>
            <translation>La libreta de campo '%1' no existe.</translation>
        </message>
        <message>
            <source>The field book '%1' is empty.</source>
            <translation>La libreta de campo '%1' está vacía.</translation>
        </message>
        <message>
            <source>Unit</source>
            <translation>Unidad</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
    </context>
    <context>
        <name>ImportFromPostgisAlgorithm</name>
        <message>
            <source>&lt;p&gt;Copies every table of a GeoComp project in a PostGIS schema into a GeoPackage: for work away from the database, for a copy to send, or to keep a monitoring project's state at a date.&lt;/p&gt;&lt;p&gt;Both stores are then compared, every row of every table, and the log says so. The GeoPackage must be new; an existing project is never overwritten.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Copia todas las tablas de un proyecto de GeoComp en un esquema PostGIS a un GeoPackage: para trabajar lejos de la base de datos, para enviar una copia, o para guardar el estado de un proyecto de monitoreo en una fecha.&lt;/p&gt;&lt;p&gt;Después se comparan los dos repositorios, cada fila de cada tabla, y el registro lo indica. El GeoPackage debe ser nuevo; nunca se sobrescribe un proyecto existente.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Copy a PostGIS project into a new GeoPackage, and check the copy.</source>
            <translation>Copia un proyecto PostGIS a un GeoPackage nuevo y comprueba la copia.</translation>
        </message>
        <message>
            <source>GeoPackage</source>
            <translation>GeoPackage</translation>
        </message>
        <message>
            <source>GeoPackage (*.gpkg)</source>
            <translation>GeoPackage (*.gpkg)</translation>
        </message>
        <message>
            <source>Import project from PostGIS</source>
            <translation>Importar proyecto desde PostGIS</translation>
        </message>
        <message>
            <source>Rows copied</source>
            <translation>Filas copiadas</translation>
        </message>
    </context>
    <context>
        <name>ImportLevelBookAlgorithm</name>
        <message>
            <source>%1 setup(s) in %2 line(s).</source>
            <translation>%1 estacionamiento(s) en %2 línea(s).</translation>
        </message>
        <message>
            <source>'%1' could not be read as a levelling field mapping: %2</source>
            <translation>'%1' no pudo leerse como un mapeo de campos de nivelación: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads a levelling field book and assembles it into instrument setups and lines, attaching an uncertainty to every reading.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Two layouts are recognised&lt;/b&gt;, and which one a file is in is worked out from the columns the mapping names rather than asked for. One row per setup, backsight and foresight side by side, is what a spreadsheet naturally produces. One row per reading, each carrying a setup identifier, is what an instrument exports &amp;mdash; and the only layout that can express a setup with several foresights at all.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Three-wire readings&lt;/b&gt; may replace a single reading in either layout. They buy the sight distance for free by stadia, which is what makes the sight-balance check possible on a book that never recorded a distance, and a half-sum check that catches a misread wire.&lt;/p&gt;&lt;p&gt;Numbers are read locale-independently: a comma decimal separator is handled here, at the boundary, and never again.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Field book&lt;/b&gt; &amp;mdash; the CSV. &lt;b&gt;Field mapping&lt;/b&gt; &amp;mdash; a saved mapping document describing the layout.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt; and &lt;b&gt;level id&lt;/b&gt; &amp;mdash; where the reading precision comes from. With neither, a generic level is assumed and the report says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Default staff-reading uncertainty&lt;/b&gt; (m) &amp;mdash; the last resort before refusing. Zero means not configured; GeoComp does not invent a sigma, because a fabricated weight corrupts every statistic computed from it.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Stadia factor&lt;/b&gt; &amp;mdash; used only when three wires are read and no level profile is available.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; JSON, the input to the reduction algorithms. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;LINE_COUNT&lt;/code&gt; and &lt;code&gt;REJECTED_ROWS&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee una libreta de nivelación y la organiza en estacionamientos del instrumento y líneas, asignando una incertidumbre a cada lectura.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Se reconocen dos disposiciones&lt;/b&gt;, y cuál usa el archivo se deduce de las columnas que indica el mapeo, en lugar de preguntarse. Una fila por estacionamiento, con espalda y frente lado a lado, es lo que una hoja de cálculo produce de forma natural. Una fila por lectura, cada una con el identificador del estacionamiento, es lo que exporta un instrumento &amp;mdash; y la única disposición capaz de expresar un estacionamiento con varias visuales de frente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las lecturas de los tres hilos&lt;/b&gt; pueden sustituir a una lectura única en cualquiera de las disposiciones. Dan gratis la distancia de la visual por estadimetría, que es lo que hace posible la verificación del equilibrio en una libreta que nunca registró distancias, y una verificación de la semisuma que detecta un hilo mal leído.&lt;/p&gt;&lt;p&gt;Los números se leen con independencia de la configuración regional: una coma decimal se trata aquí, en la frontera, y nunca más.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Libreta&lt;/b&gt; &amp;mdash; el CSV. &lt;b&gt;Mapeo de campos&lt;/b&gt; &amp;mdash; un documento de mapeo guardado que describe la disposición.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt; e &lt;b&gt;identificador del nivel&lt;/b&gt; &amp;mdash; de dónde procede la precisión de las lecturas. Sin ninguno de ellos se asume un nivel genérico y el informe lo dice.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Incertidumbre por defecto de la lectura de mira&lt;/b&gt; (m) &amp;mdash; el último recurso antes de rechazar. Cero significa no configurado; GeoComp no inventa un sigma, porque un peso fabricado corrompe todas las estadísticas calculadas a partir de él.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Constante estadimétrica&lt;/b&gt; &amp;mdash; se usa solo cuando se leen tres hilos y no hay perfil de nivel disponible.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estacionamientos&lt;/b&gt; &amp;mdash; JSON, la entrada de los algoritmos de reducción. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;LINE_COUNT&lt;/code&gt; y &lt;code&gt;REJECTED_ROWS&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Default staff-reading uncertainty (m)</source>
            <translation>Incertidumbre por defecto de la lectura de mira (m)</translation>
        </message>
        <message>
            <source>Distances recorded</source>
            <translation>Distancias registradas</translation>
        </message>
        <message>
            <source>Field book</source>
            <translation>Libreta de campo</translation>
        </message>
        <message>
            <source>Field books (*.csv *.xlsx);;All files (*)</source>
            <translation>Libretas de campo (*.csv *.xlsx);;Todos los archivos (*)</translation>
        </message>
        <message>
            <source>Field mapping</source>
            <translation>Asignación de campos</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GeoComp setups (*.json)</source>
            <translation>Estacionamientos de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Import levelling field book</source>
            <translation>Importar libreta de nivelación</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfiles de instrumento</translation>
        </message>
        <message>
            <source>Layout</source>
            <translation>Disposición</translation>
        </message>
        <message>
            <source>Level id</source>
            <translation>Identificador del nivel</translation>
        </message>
        <message>
            <source>Level profile</source>
            <translation>Perfil del nivel</translation>
        </message>
        <message>
            <source>Levelling field book import</source>
            <translation>Importación de libreta de nivelación</translation>
        </message>
        <message>
            <source>Line</source>
            <translation>Línea</translation>
        </message>
        <message>
            <source>Lines</source>
            <translation>Líneas</translation>
        </message>
        <message>
            <source>Lines assembled</source>
            <translation>Líneas montadas</translation>
        </message>
        <message>
            <source>No usable setup was read. Every row was rejected; the report lists why, row by row.</source>
            <translation>No se leyó ningún estacionamiento utilizable. Todas las filas fueron rechazadas; el informe indica por qué, fila a fila.</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Read a CSV levelling book into setups and lines, with findings.</source>
            <translation>Lee una libreta de nivelación en CSV, produciendo estacionamientos, líneas y hallazgos.</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Rows read</source>
            <translation>Filas leídas</translation>
        </message>
        <message>
            <source>Rows rejected</source>
            <translation>Filas rechazadas</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Setups assembled</source>
            <translation>Estacionamientos montados</translation>
        </message>
        <message>
            <source>Stadia factor</source>
            <translation>Constante estadimétrica</translation>
        </message>
        <message>
            <source>Summary</source>
            <translation>Resumen</translation>
        </message>
        <message>
            <source>These source columns were not mapped and were ignored: %1</source>
            <translation>Estas columnas del origen no se mapearon y fueron ignoradas: %1</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Unmapped columns</source>
            <translation>Columnas no mapeadas</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>no</source>
            <translation>no</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sí</translation>
        </message>
    </context>
    <context>
        <name>InstallEngineAlgorithm</name>
        <message>
            <source>&lt;p&gt;Downloads the DynAdjust release GeoComp was tested with, for this computer's operating system, from Geoscience Australia's release page. Before anything is extracted the download is checked against the SHA-256 digest recorded in GeoComp; a download that does not match is deleted and nothing is installed.&lt;/p&gt;&lt;p&gt;The programs go into GeoComp's folder in the QGIS profile, so no administrator rights are needed and removing the profile removes them. The version is recorded, and the installed program is run once to show that it works on this computer.&lt;/p&gt;&lt;p&gt;The download uses QGIS's network settings, including its proxy.&lt;/p&gt;&lt;p&gt;A DynAdjust directory set in Global Settings, under Paths and engines, is still used in preference to this installation; clear it to use this one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RTKLIB&lt;/b&gt; is not offered: its authors publish executables for Windows only. Install it yourself and give the path to &lt;code&gt;rnx2rtkp&lt;/code&gt; in Global Settings.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Descarga la versión de DynAdjust con la que se probó GeoComp, para el sistema operativo de este equipo, desde la página de versiones de Geoscience Australia. Antes de extraer nada, la descarga se comprueba contra el resumen criptográfico SHA-256 registrado en GeoComp; una descarga que no coincide se elimina y no se instala nada.&lt;/p&gt;&lt;p&gt;Los programas van a la carpeta de GeoComp en el perfil de QGIS, por lo que no se necesitan permisos de administrador, y eliminar el perfil los elimina. La versión queda registrada, y el programa instalado se ejecuta una vez para mostrar que funciona en este equipo.&lt;/p&gt;&lt;p&gt;La descarga usa la configuración de red de QGIS, incluido su proxy.&lt;/p&gt;&lt;p&gt;Un directorio de DynAdjust definido en Configuraciones Globales, en Rutas y motores, sigue teniendo preferencia sobre esta instalación; bórrelo para usar esta.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RTKLIB&lt;/b&gt; no se ofrece: sus autores publican ejecutables solo para Windows. Instálelo usted mismo e indique la ruta de &lt;code&gt;rnx2rtkp&lt;/code&gt; en Configuraciones Globales.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A DynAdjust directory is set in Global Settings (%1), and the algorithms will keep using it. Clear it to use this installation.</source>
            <translation>Hay un directorio de DynAdjust definido en Configuraciones Globales (%1), y los algoritmos seguirán usándolo. Bórrelo para usar esta instalación.</translation>
        </message>
        <message>
            <source>Download, verify and install DynAdjust for this computer.</source>
            <translation>Descargar, verificar e instalar DynAdjust en este equipo.</translation>
        </message>
        <message>
            <source>Downloading DynAdjust %1 for %2 from %3</source>
            <translation>Descargando DynAdjust %1 para %2 desde %3</translation>
        </message>
        <message>
            <source>DynAdjust</source>
            <translation>DynAdjust</translation>
        </message>
        <message>
            <source>DynAdjust %1 runs: %2.</source>
            <translation>DynAdjust %1 funciona: %2.</translation>
        </message>
        <message>
            <source>DynAdjust %1 was downloaded, verified and installed in %2, but it does not run on this computer. Install DynAdjust another way and give its directory in Global Settings, under Paths and engines.</source>
            <translation>DynAdjust %1 se descargó, verificó e instaló en %2, pero no funciona en este equipo. Instale DynAdjust de otra forma e indique su directorio en Configuraciones Globales, en Rutas y motores.</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Install an engine</source>
            <translation>Instalar un motor</translation>
        </message>
        <message>
            <source>Installed in</source>
            <translation>Instalado en</translation>
        </message>
        <message>
            <source>The program reports version %1 although release %2 was installed.</source>
            <translation>El programa informa la versión %1, aunque se instaló la versión %2.</translation>
        </message>
        <message>
            <source>Verified against the SHA-256 recorded in GeoComp (%1) and installed in %2.</source>
            <translation>Verificado contra el SHA-256 registrado en GeoComp (%1) e instalado en %2.</translation>
        </message>
        <message>
            <source>Version installed</source>
            <translation>Versión instalada</translation>
        </message>
    </context>
    <context>
        <name>IntersectionAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes the coordinates of a point sighted from two or more known stations whose orientation is known, by least squares. Two stations give a unique solution; more give residuals and a covariance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Weak geometry is reported rather than left to be discovered.&lt;/b&gt; Near-parallel rays do not determine a point however precise each sighting is, and the error ellipse is where that shows: when it comes out more than ten times longer than it is wide, the run says so. Rays that are exactly parallel are refused, because there is no intersection to return.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Sightings&lt;/b&gt; &amp;mdash; a JSON object mapping each observing station to its position and the azimuth it observed:&lt;/p&gt;&lt;pre&gt;{"A": {"position": [0, 0], "azimuth": 57.99},
 "B": {"position": [1000, 0], "azimuth": 300.02}}&lt;/pre&gt;&lt;p&gt;Positions in metres, azimuths in degrees from north, clockwise. Azimuths rather than circle readings: an intersection is computed from &lt;i&gt;oriented&lt;/i&gt; stations, and where the orientation is unknown the station has to be resected first.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Target&lt;/b&gt; &amp;mdash; the name to give the computed point. &lt;b&gt;Azimuth precision&lt;/b&gt; (degrees) &amp;mdash; applied to every sighting that does not state its own, and what the resulting ellipse is scaled by.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the reported ellipse.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Position&lt;/b&gt; &amp;mdash; a JSON document in the shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SEMI_MAJOR&lt;/code&gt;, &lt;code&gt;SEMI_MINOR&lt;/code&gt; in metres and &lt;code&gt;WEAK_GEOMETRY&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula las coordenadas de un punto visado desde dos o más estaciones conocidas cuya orientación se conoce, por mínimos cuadrados. Dos estaciones dan una solución única; más dan residuos y una covarianza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La geometría débil se comunica en lugar de dejarse para ser descubierta.&lt;/b&gt; Los rayos casi paralelos no determinan un punto por precisa que sea cada visual, y la elipse de errores es donde eso aparece: cuando sale más de diez veces más larga que ancha, la ejecución lo advierte. Los rayos exactamente paralelos se rechazan, porque no hay intersección que devolver.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Visuales&lt;/b&gt; &amp;mdash; un objeto JSON que asocia cada estación observadora a su posición y al acimut que observó:&lt;/p&gt;&lt;pre&gt;{"A": {"position": [0, 0], "azimuth": 57.99},
 "B": {"position": [1000, 0], "azimuth": 300.02}}&lt;/pre&gt;&lt;p&gt;Posiciones en metros, acimutes en grados desde el norte, en sentido horario. Acimutes y no lecturas de círculo: una intersección directa se calcula a partir de estaciones &lt;i&gt;orientadas&lt;/i&gt;, y donde la orientación se desconoce la estación debe determinarse antes por intersección inversa.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Objetivo&lt;/b&gt; &amp;mdash; el nombre que dar al punto calculado. &lt;b&gt;Precisión del acimut&lt;/b&gt; (grados) &amp;mdash; aplicada a toda visual que no declare la suya, y es por ella por la que se escala la elipse resultante.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la elipse comunicada.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Posición&lt;/b&gt; &amp;mdash; un documento JSON con el formato que la Red clásica toma como coordenadas aproximadas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SEMI_MAJOR&lt;/code&gt;, &lt;code&gt;SEMI_MINOR&lt;/code&gt; en metros y &lt;code&gt;WEAK_GEOMETRY&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>At least two sightings are needed; the document holds %1.</source>
            <translation>Se necesitan al menos dos visuales; el documento contiene %1.</translation>
        </message>
        <message>
            <source>Azimuth precision (°)</source>
            <translation>Precisión del acimut (°)</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>E %1, N %2; ellipse %3 by %4 mm.</source>
            <translation>E %1, N %2; elipse %3 por %4 mm.</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>Ellipse azimuth</source>
            <translation>Acimut de la elipse</translation>
        </message>
        <message>
            <source>Fix a sighted point from two or more oriented known stations.</source>
            <translation>Determina un punto visado desde dos o más estaciones conocidas y orientadas.</translation>
        </message>
        <message>
            <source>Forward intersection</source>
            <translation>Intersección directa</translation>
        </message>
        <message>
            <source>Forward intersection report</source>
            <translation>Informe de la intersección directa</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_intersection</source>
            <translation>Generado por GeoComp — geocomp:totalstation_intersection</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Geometry</source>
            <translation>Geometría</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Intersecting '%1' from %2 station(s).</source>
            <translation>Intersecando '%1' desde %2 estación(es).</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Punto</translation>
        </message>
        <message>
            <source>Position</source>
            <translation>Posición</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Residual (%1)</source>
            <translation>Residuo (%1)</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Residuos</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieje mayor (mm)</translation>
        </message>
        <message>
            <source>Semi-minor (mm)</source>
            <translation>Semieje menor (mm)</translation>
        </message>
        <message>
            <source>Sighting '%1' does not hold numbers.</source>
            <translation>La visual '%1' no contiene números.</translation>
        </message>
        <message>
            <source>Sighting '%1' must be an object with a 'position' pair and an 'azimuth'.</source>
            <translation>La visual '%1' debe ser un objeto con un par 'position' y un 'azimuth'.</translation>
        </message>
        <message>
            <source>Sightings</source>
            <translation>Visuales</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Target name</source>
            <translation>Nombre del objetivo</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
    </context>
    <context>
        <name>LevellingClosureAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes the misclosure of a levelling loop or line and compares it with the permissible misclosure &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt;, with &lt;i&gt;L&lt;/i&gt; in kilometres.&lt;/p&gt;&lt;p&gt;&lt;b&gt;With no k configured there is no verdict.&lt;/b&gt; The misclosure is still reported &amp;mdash; it is the number that matters &amp;mdash; but whether it is acceptable is not, because inventing a tolerance to have something to compare against would be worse than saying nothing. GeoComp ships no national tolerance table: &lt;i&gt;k&lt;/i&gt; differs by country, by class within a country and by edition of the standard, and a wrong value does not fail loudly, it quietly accepts a line that should have been re-run.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The distribution across setups comes with a caveat that is part of the answer.&lt;/b&gt; Distributing a misclosure proportionally is the classical correction and many specifications require it, so it is computed. But proportional distribution &lt;b&gt;localises nothing&lt;/b&gt;: every setup gets its share whether or not it is where the error entered, so a blunder is smeared evenly along the line and made harder to find.&lt;/p&gt;&lt;p&gt;So the misclosure is also compared with &lt;b&gt;its own propagated standard deviation&lt;/b&gt;. A small ratio means the line closed as well as its own readings say it should, and distributing that misclosure is exactly right. A large one means something happened that the reading precisions do not explain, and spreading it evenly is the one response guaranteed to hide it &amp;mdash; adjust the network and let data snooping find it instead. The report says which case you are in.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced lines&lt;/b&gt; &amp;mdash; the document a reduction produced. &lt;b&gt;Mode&lt;/b&gt; &amp;mdash; loop (the lines must chain and return to where they began; a line entered in the opposite direction is handled from the station ids) or line (the first line only, against a known height difference).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Known height difference&lt;/b&gt; and its &lt;b&gt;uncertainty&lt;/b&gt; (m) &amp;mdash; from the two benchmarks' published heights. The uncertainty enters the misclosure's: a line closed against two third-order marks has not been tested as sharply as one closed against two first-order marks.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerance coefficient k&lt;/b&gt; (m per root kilometre) &amp;mdash; zero for no verdict. &lt;b&gt;Distribute by&lt;/b&gt; &amp;mdash; line length or setup count.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Closure&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Distribution&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;MISCLOSURE&lt;/code&gt; and &lt;code&gt;PERMISSIBLE&lt;/code&gt; in metres, and &lt;code&gt;PASSED&lt;/code&gt; (1, 0, or -1 for not judged).&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula el error de cierre de un circuito o de una línea de nivelación y lo compara con el error admisible &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt;, con &lt;i&gt;L&lt;/i&gt; en kilómetros.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sin una k configurada no hay veredicto.&lt;/b&gt; El error de cierre se sigue reportando &amp;mdash; es el número que importa &amp;mdash; pero si es aceptable no, porque inventar una tolerancia solo para tener con qué comparar sería peor que no decir nada. GeoComp no incluye ninguna tabla nacional de tolerancias: &lt;i&gt;k&lt;/i&gt; difiere de país a país, de clase a clase dentro de un país y de edición a edición de la norma, y un valor equivocado no falla de forma ruidosa, acepta silenciosamente una línea que debería haberse repetido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La distribución entre estacionamientos viene con una salvedad que forma parte de la respuesta.&lt;/b&gt; Distribuir proporcionalmente un error de cierre es la corrección clásica y muchas especificaciones la exigen, por lo que se calcula. Pero la distribución proporcional &lt;b&gt;no localiza nada&lt;/b&gt;: cada estacionamiento recibe su parte, esté o no donde entró el error, por lo que un error grosero se reparte uniformemente por la línea y resulta más difícil de encontrar.&lt;/p&gt;&lt;p&gt;Por eso el error de cierre se compara también con &lt;b&gt;su propia desviación típica propagada&lt;/b&gt;. Una razón pequeña significa que la línea cerró tan bien como indican sus propias lecturas, y distribuir ese error es exactamente lo correcto. Una razón grande significa que ocurrió algo que las precisiones de las lecturas no explican, y repartirlo uniformemente es la única respuesta que garantiza ocultarlo &amp;mdash; ajuste la red y deje que el data snooping lo encuentre. El informe indica en qué caso está.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; el documento producido por una reducción. &lt;b&gt;Modo&lt;/b&gt; &amp;mdash; circuito (las líneas deben encadenarse y volver al punto de partida; una línea introducida en sentido inverso se trata a partir de los identificadores de las estaciones) o línea (solo la primera, contra un desnivel conocido).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Desnivel conocido&lt;/b&gt; y su &lt;b&gt;incertidumbre&lt;/b&gt; (m) &amp;mdash; de las altitudes publicadas de las dos referencias. La incertidumbre entra en la del error de cierre: una línea cerrada contra dos referencias de tercer orden no se ha comprobado tan severamente como una cerrada contra dos de primer orden.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coeficiente de tolerancia k&lt;/b&gt; (m por raíz de kilómetro) &amp;mdash; cero para ningún veredicto. &lt;b&gt;Distribuir por&lt;/b&gt; &amp;mdash; longitud de la línea o número de estacionamientos.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Cierre&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Distribución&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;MISCLOSURE&lt;/code&gt; y &lt;code&gt;PERMISSIBLE&lt;/code&gt; en metros, y &lt;code&gt;PASSED&lt;/code&gt; (1, 0, o -1 para no evaluado).&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Closure</source>
            <translation>Cierre</translation>
        </message>
        <message>
            <source>Closures and tolerances</source>
            <translation>Cierres y tolerancias</translation>
        </message>
        <message>
            <source>Correction (mm)</source>
            <translation>Corrección (mm)</translation>
        </message>
        <message>
            <source>Correction over the setup's own uncertainty</source>
            <translation>Corrección sobre la incertidumbre del propio estacionamiento</translation>
        </message>
        <message>
            <source>Distribute by</source>
            <translation>Distribuir por</translation>
        </message>
        <message>
            <source>Distribution</source>
            <translation>Distribución</translation>
        </message>
        <message>
            <source>Distribution across setups</source>
            <translation>Distribución entre estacionamientos</translation>
        </message>
        <message>
            <source>Do not distribute this</source>
            <translation>No distribuya este error</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>GeoComp closure (*.json)</source>
            <translation>Cierre de GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Kind</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Known height difference (m)</source>
            <translation>Desnivel conocido (m)</translation>
        </message>
        <message>
            <source>Length (km)</source>
            <translation>Longitud (km)</translation>
        </message>
        <message>
            <source>Levelling: closures</source>
            <translation>Nivelación: cierres</translation>
        </message>
        <message>
            <source>Line against a known difference</source>
            <translation>Línea contra un desnivel conocido</translation>
        </message>
        <message>
            <source>Line and loop misclosure, against a configurable tolerance.</source>
            <translation>Error de cierre de línea y de circuito, frente a una tolerancia configurable.</translation>
        </message>
        <message>
            <source>Line length</source>
            <translation>Longitud de la línea</translation>
        </message>
        <message>
            <source>Loop</source>
            <translation>Circuito</translation>
        </message>
        <message>
            <source>Loop name</source>
            <translation>Nombre del circuito</translation>
        </message>
        <message>
            <source>Misclosure %1 mm over %2 km.</source>
            <translation>Error de cierre de %1 mm en %2 km.</translation>
        </message>
        <message>
            <source>Misclosure (mm)</source>
            <translation>Error de cierre (mm)</translation>
        </message>
        <message>
            <source>Misclosure over its own uncertainty</source>
            <translation>Error de cierre sobre su propia incertidumbre</translation>
        </message>
        <message>
            <source>Mode</source>
            <translation>Modo</translation>
        </message>
        <message>
            <source>Number of setups</source>
            <translation>Número de estacionamientos</translation>
        </message>
        <message>
            <source>OUT OF TOLERANCE</source>
            <translation>FUERA DE TOLERANCIA</translation>
        </message>
        <message>
            <source>Permissible (mm)</source>
            <translation>Tolerancia (mm)</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reduced lines</source>
            <translation>Líneas reducidas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Setup</source>
            <translation>Estacionamiento</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Share</source>
            <translation>Parte</translation>
        </message>
        <message>
            <source>The misclosure is consistent with the readings' own precision, which is the case proportional distribution is correct for.</source>
            <translation>El error de cierre es compatible con la precisión de las propias lecturas, que es el caso en el que la distribución proporcional es correcta.</translation>
        </message>
        <message>
            <source>The misclosure is far larger than the readings' own precision explains. That is not accumulated random error, so distributing it proportionally would spread one mistake evenly along the line and make it harder to find. Adjust the network and let data snooping locate it.</source>
            <translation>El error de cierre es mucho mayor de lo que explica la precisión de las propias lecturas. No es error aleatorio acumulado, por lo que distribuirlo proporcionalmente repartiría un único fallo por toda la línea y haría más difícil encontrarlo. Ajuste la red y deje que el data snooping lo localice.</translation>
        </message>
        <message>
            <source>Tolerance coefficient k (m per root km)</source>
            <translation>Coeficiente de tolerancia k (m por raíz de km)</translation>
        </message>
        <message>
            <source>Uncertainty of the known difference (m)</source>
            <translation>Incertidumbre del desnivel conocido (m)</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Verdict</source>
            <translation>Veredicto</translation>
        </message>
        <message>
            <source>not judged — no tolerance was configured</source>
            <translation>no evaluado — no se configuró ninguna tolerancia</translation>
        </message>
        <message>
            <source>within tolerance</source>
            <translation>dentro de la tolerancia</translation>
        </message>
    </context>
    <context>
        <name>LevellingNetworkAlgorithm</name>
        <message>
            <source>%1 %2: misclosure %3 mm; %4.</source>
            <translation>%1 %2: error de cierre %3 mm; %4.</translation>
        </message>
        <message>
            <source>%1 closure(s) failed their tolerance: %2. GeoComp does not adjust a line that failed its tolerance without an explicit acknowledgement. Re-run the line, or turn on 'Adjust lines that failed their tolerance' for this run or in Global Settings (Levelling).</source>
            <translation>%1 cierre(s) no cumplieron la tolerancia: %2. GeoComp no ajusta una línea que no cumplió la tolerancia sin un reconocimiento explícito. Repita la línea, o active 'Ajustar líneas que no cumplieron la tolerancia' en esta ejecución o en la Configuración global (Nivelación).</translation>
        </message>
        <message>
            <source>%1 is not the height-difference document Trigonometric levelling writes.</source>
            <translation>%1 no es el documento de desniveles que escribe la Nivelación trigonométrica.</translation>
        </message>
        <message>
            <source>'%1' does not hold a number.</source>
            <translation>'%1' no contiene un número.</translation>
        </message>
        <message>
            <source>'%1' is not a benchmark. Write them as id=height, for example BM1=100.000, and add a tolerance as BM2=103.750±0.002 to hold one with a weight rather than exactly.</source>
            <translation>'%1' no es un punto de referencia. Escríbalos como id=altitud, por ejemplo BM1=100.000, y añada una tolerancia como BM2=103.750±0.002 para fijarlo con peso en lugar de exactamente.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts reduced levelling lines as a one-dimensional network: the same least squares, the same global test, the same data snooping and reliability as any other GeoComp adjustment.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Two weighting models, and the choice is yours.&lt;/b&gt; A reduced line arrives carrying an uncertainty propagated from its staff readings. That figure is rigorous and usually optimistic: it knows nothing of refraction, of staff calibration, or of a tripod settling between backsight and foresight. The &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt; and &lt;code&gt;k &amp;times; &amp;radic;n&lt;/code&gt; models are fitted to lines that suffered all three. Length weighting suits long lines with consistent sight lengths; setup weighting suits short, irregular ones where the per-setup reading error dominates. Leaving both coefficients at zero keeps the propagated uncertainty, and the report says which was used.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Benchmarks&lt;/b&gt; are entered as &lt;code&gt;id=height&lt;/code&gt; pairs, separated by commas or semicolons; add &lt;code&gt;±sigma&lt;/code&gt; to hold one with a weight rather than exactly, for example &lt;code&gt;BM1=100.000, BM2=103.750±0.002&lt;/code&gt;. With none, the network is free, which is often the right thing to adjust first: it shows the observations' internal consistency without a datum's errors mixed in.&lt;/p&gt;&lt;p&gt;Mixing orthometric and ellipsoidal heights without a geoid model is refused. The error would be the geoid undulation &amp;mdash; tens of metres across much of Brazil &amp;mdash; and the result would look entirely reasonable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The report gives relative height uncertainties between pairs of benchmarks&lt;/b&gt;, which is the 1D analogue of the error ellipse and usually the number a levelling network was built to produce. It is not the difference of the two individual uncertainties, because adjusted heights are correlated.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced lines&lt;/b&gt; &amp;mdash; the document a reduction produced. &lt;b&gt;Benchmarks&lt;/b&gt; &amp;mdash; as above. &lt;b&gt;Weighting&lt;/b&gt;, and the coefficient for each model (m per root km, m per root setup); zero means that model is not configured.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Trigonometric height differences&lt;/b&gt; &amp;mdash; optional: the document &lt;i&gt;Trigonometric levelling&lt;/i&gt; writes. Its differences join the lines as one network, each with its own propagated uncertainty, and a point only they reach is added. &lt;b&gt;Estimate a variance component per technique&lt;/b&gt; (advanced) &amp;mdash; scales each technique's uncertainties by a factor estimated from the residuals, and reports the factors.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Free network&lt;/b&gt; &amp;mdash; ignore the benchmarks and remove the datum defect with an inner constraint.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence&lt;/b&gt;, &lt;b&gt;alpha&lt;/b&gt; and &lt;b&gt;beta&lt;/b&gt; &amp;mdash; for the global test, data snooping and the minimal detectable bias.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Heights&lt;/b&gt; &amp;mdash; CSV.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No map layers.&lt;/b&gt; A levelling network has no planimetry: it determines heights and nothing else, so every station would be drawn at the same point. Use the network algorithm in the Analysis menu on a network document that carries coordinates, or wait for the project store that holds both. Scalars: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt; and &lt;code&gt;WORST_HEIGHT_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta líneas de nivelación reducidas como una red unidimensional: los mismos mínimos cuadrados, la misma prueba global, el mismo data snooping y la misma fiabilidad que cualquier otro ajuste de GeoComp.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dos modelos de ponderación, y la elección es suya.&lt;/b&gt; Una línea reducida llega con una incertidumbre propagada a partir de sus lecturas de mira. Ese valor es riguroso y habitualmente optimista: no sabe nada de la refracción, de la calibración de la mira, ni del asentamiento del trípode entre la espalda y el frente. Los modelos &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt; y &lt;code&gt;k &amp;times; &amp;radic;n&lt;/code&gt; se ajustaron a líneas que sufrieron los tres. La ponderación por longitud conviene a líneas largas con visuales de longitud consistente; la ponderación por estacionamientos conviene a líneas cortas e irregulares, donde domina el error de lectura por estacionamiento. Dejar ambos coeficientes en cero mantiene la incertidumbre propagada, y el informe indica cuál se usó.&lt;/p&gt;&lt;p&gt;Los &lt;b&gt;puntos de referencia&lt;/b&gt; se introducen como pares &lt;code&gt;id=altitud&lt;/code&gt;, separados por comas o puntos y comas; añada &lt;code&gt;±sigma&lt;/code&gt; para fijar uno con peso en lugar de exactamente, por ejemplo &lt;code&gt;BM1=100.000, BM2=103.750±0.002&lt;/code&gt;. Sin ninguno, la red es libre, lo que a menudo es el primer ajuste correcto: muestra la consistencia interna de las observaciones sin los errores de un datum de por medio.&lt;/p&gt;&lt;p&gt;Mezclar alturas ortométricas y elipsoidales sin un modelo geoidal se rechaza. El error sería la ondulación geoidal &amp;mdash; decenas de metros en gran parte de Brasil &amp;mdash; y el resultado parecería perfectamente razonable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El informe presenta las incertidumbres relativas de altitud entre pares de referencias&lt;/b&gt;, que son el análogo 1D de la elipse de error y habitualmente el número que una red de nivelación fue construida para producir. No es la diferencia de las dos incertidumbres individuales, porque las altitudes ajustadas están correlacionadas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; el documento producido por una reducción. &lt;b&gt;Puntos de referencia&lt;/b&gt; &amp;mdash; como arriba. &lt;b&gt;Ponderación&lt;/b&gt;, y el coeficiente de cada modelo (m por raíz de km, m por raíz de estacionamiento); cero significa que ese modelo no está configurado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Desniveles trigonométricos&lt;/b&gt; &amp;mdash; opcional: el documento que escribe la &lt;i&gt;Nivelación trigonométrica&lt;/i&gt;. Sus desniveles se unen a las líneas en una sola red, cada uno con su propia incertidumbre propagada, y se añade un punto que solo ellos alcanzan. &lt;b&gt;Estimar una componente de varianza por técnica&lt;/b&gt; (avanzado) &amp;mdash; escala las incertidumbres de cada técnica por un factor estimado a partir de los residuos, e informa de los factores.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Red libre&lt;/b&gt; &amp;mdash; ignora los puntos de referencia y elimina la deficiencia de datum con una constricción interna.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confianza&lt;/b&gt;, &lt;b&gt;alfa&lt;/b&gt; y &lt;b&gt;beta&lt;/b&gt; &amp;mdash; para la prueba global, el data snooping y el sesgo mínimo detectable.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Altitudes&lt;/b&gt; &amp;mdash; CSV.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sin capas de mapa.&lt;/b&gt; Una red de nivelación no tiene planimetría: determina altitudes y nada más, por lo que todas las estaciones se dibujarían en el mismo punto. Use el algoritmo de red del menú Análisis sobre un documento de red que contenga coordenadas, o espere al repositorio de proyecto que contenga ambos. Escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt; y &lt;code&gt;WORST_HEIGHT_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjust levelling lines as a 1D network, by length or setup weighting.</source>
            <translation>Ajusta líneas de nivelación como una red 1D, ponderando por longitud o por número de estacionamientos.</translation>
        </message>
        <message>
            <source>Adjust lines that failed their tolerance</source>
            <translation>Ajustar líneas que no cumplieron la tolerancia</translation>
        </message>
        <message>
            <source>Adjusted although it failed its tolerance, as acknowledged: %1.</source>
            <translation>Ajustado aunque no cumplió la tolerancia, según lo reconocido: %1.</translation>
        </message>
        <message>
            <source>Adjusted heights</source>
            <translation>Altitudes ajustadas</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
        </message>
        <message>
            <source>Apply the normal orthometric correction</source>
            <translation>Aplicar la corrección ortométrica normal</translation>
        </message>
        <message>
            <source>Benchmarks</source>
            <translation>Puntos de referencia</translation>
        </message>
        <message>
            <source>By line length</source>
            <translation>Por la longitud de la línea</translation>
        </message>
        <message>
            <source>By number of setups</source>
            <translation>Por el número de estacionamientos</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Candidates, not rejections. GeoComp never removes an observation on its own: in a monitoring network the displacement being measured is exactly what an automatic outlier remover would delete.</source>
            <translation>Candidatos, no rechazos. GeoComp nunca elimina una observación por su cuenta: en una red de monitorización, el desplazamiento que se está midiendo es exactamente lo que un eliminador automático de errores groseros borraría.</translation>
        </message>
        <message>
            <source>Closures before adjustment</source>
            <translation>Cierres antes del ajuste</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Correction (mm)</source>
            <translation>Corrección (mm)</translation>
        </message>
        <message>
            <source>Critical value</source>
            <translation>Valor crítico</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Data snooping significance (alpha)</source>
            <translation>Significancia del data snooping (alfa)</translation>
        </message>
        <message>
            <source>Data snooping type II error rate (beta)</source>
            <translation>Tasa de error tipo II del data snooping (beta)</translation>
        </message>
        <message>
            <source>Datum</source>
            <translation>Datum</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Degrees of freedom %1; variance factor %2.</source>
            <translation>Grados de libertad %1; factor de varianza %2.</translation>
        </message>
        <message>
            <source>Each line between two benchmarks against the difference of their heights, and each section levelled more than once against its first run, on the section's one-way length. A line that failed is adjusted only when 'Adjust lines that failed their tolerance' is on, and the provenance records which.</source>
            <translation>Cada línea entre dos puntos de referencia, frente a la diferencia de sus alturas, y cada sección nivelada más de una vez, frente a su primera corrida, sobre la longitud de la sección en un solo sentido. Una línea que no cumplió solo se ajusta cuando 'Ajustar líneas que no cumplieron la tolerancia' está activo, y la procedencia registra cuáles.</translation>
        </message>
        <message>
            <source>Each technique's declared uncertainties were scaled by its factor, estimated from the residuals until both settled. A factor near one says the technique was declared about right; four says its uncertainties were half what they should have been.</source>
            <translation>Las incertidumbres declaradas de cada técnica se escalaron por su factor, estimado a partir de los residuos hasta que ambos se estabilizaron. Un factor cercano a uno indica que la técnica se declaró aproximadamente bien; cuatro indica que sus incertidumbres eran la mitad de lo que debían ser.</translation>
        </message>
        <message>
            <source>Estimate a variance component per technique</source>
            <translation>Estimar una componente de varianza por técnica</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>Factor</source>
            <translation>Factor</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>Free network</source>
            <translation>Red libre</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>GeoComp network (*.json)</source>
            <translation>Red GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height (m)</source>
            <translation>Altitud (m)</translation>
        </message>
        <message>
            <source>Height type</source>
            <translation>Tipo de altitud</translation>
        </message>
        <message>
            <source>Heights</source>
            <translation>Altitudes</translation>
        </message>
        <message>
            <source>Kind</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Length (km)</source>
            <translation>Longitud (km)</translation>
        </message>
        <message>
            <source>Levelling network adjustment</source>
            <translation>Ajuste de red de nivelación</translation>
        </message>
        <message>
            <source>Line</source>
            <translation>Línea</translation>
        </message>
        <message>
            <source>Lines</source>
            <translation>Líneas</translation>
        </message>
        <message>
            <source>Mean height (m)</source>
            <translation>Altura media (m)</translation>
        </message>
        <message>
            <source>Mean latitude</source>
            <translation>Latitud media</translation>
        </message>
        <message>
            <source>Misclosure (mm)</source>
            <translation>Error de cierre (mm)</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>OUT OF TOLERANCE, %1 mm permitted</source>
            <translation>FUERA DE TOLERANCIA, %1 mm permitidos</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Orthometric correction, line %1: %2 mm.</source>
            <translation>Corrección ortométrica, línea %1: %2 mm.</translation>
        </message>
        <message>
            <source>Orthometric corrections</source>
            <translation>Correcciones ortométricas</translation>
        </message>
        <message>
            <source>Outlier candidate: %1 (w = %2).</source>
            <translation>Candidato a error grosero: %1 (w = %2).</translation>
        </message>
        <message>
            <source>Outlier candidates</source>
            <translation>Candidatos a error grosero</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reduced lines</source>
            <translation>Líneas reducidas</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Reference epoch, decimal year (0 = the network's own)</source>
            <translation>Época de referencia, año decimal (0 = la de la propia red)</translation>
        </message>
        <message>
            <source>Relative height uncertainties</source>
            <translation>Incertidumbres relativas de altitud</translation>
        </message>
        <message>
            <source>Relative uncertainty (mm)</source>
            <translation>Incertidumbre relativa (mm)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Section</source>
            <translation>Sección</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Standard deviation</source>
            <translation>Desviación estándar</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Station id field</source>
            <translation>Campo del identificador de la estación</translation>
        </message>
        <message>
            <source>Station positions (for the orthometric correction)</source>
            <translation>Posiciones de las estaciones (para la corrección ortométrica)</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Summary</source>
            <translation>Resumen</translation>
        </message>
        <message>
            <source>Technique</source>
            <translation>Técnica</translation>
        </message>
        <message>
            <source>The global test failed. Either the observations disagree more than their weights allow, or the weights are wrong — the test cannot distinguish the two. A levelling network weighted by propagated staff readings routinely fails it, because that model omits refraction, staff calibration and settlement.</source>
            <translation>La prueba global falló. O las observaciones difieren más de lo que sus pesos permiten, o los pesos son incorrectos — la prueba no distingue ambos casos. Una red de nivelación ponderada por las lecturas de mira propagadas la falla rutinariamente, porque ese modelo omite la refracción, la calibración de la mira y el asentamiento del trípode.</translation>
        </message>
        <message>
            <source>The global test failed. Either the observations disagree with each other more than their weights allow, or the weights are wrong — the test cannot tell you which.</source>
            <translation>La prueba global falló. O las observaciones difieren entre sí más de lo que sus pesos permiten, o los pesos son incorrectos — la prueba no distingue ambos casos.</translation>
        </message>
        <message>
            <source>The lines fall into %1 disconnected pieces, so they cannot be adjusted as one network whatever the datum. Level between them, or adjust each piece separately.</source>
            <translation>Las líneas forman %1 partes desconectadas, por lo que no pueden ajustarse como una sola red, sea cual sea el datum. Nivele entre ellas, o ajuste cada parte por separado.</translation>
        </message>
        <message>
            <source>The normal orthometric correction, from the ellipsoid's gravity field, added to each levelled difference before adjustment. Its uncertainty is taken as a tenth of the correction, a stand-in for the normality assumption that no propagation can express. Below 0.1 mm it is smaller than the noise of any levelling.</source>
            <translation>La corrección ortométrica normal, a partir del campo de gravedad del elipsoide, sumada a cada desnivel nivelado antes del ajuste. Su incertidumbre se toma como una décima parte de la corrección, un sustituto de la hipótesis de normalidad que ninguna propagación puede expresar. Por debajo de 0,1 mm es menor que el ruido de cualquier nivelación.</translation>
        </message>
        <message>
            <source>The orthometric correction needs approximate heights, and a free network has none: its heights hang from an arbitrary zero. Give at least one benchmark and do not adjust the network as free, or turn the correction off.</source>
            <translation>La corrección ortométrica necesita alturas aproximadas, y una red libre no las tiene: sus alturas parten de un cero arbitrario. Indique al menos un punto de referencia y no ajuste la red como libre, o desactive la corrección.</translation>
        </message>
        <message>
            <source>The orthometric correction needs the stations' latitudes. Give a point layer of station positions and the field holding each station's id, or turn the correction off.</source>
            <translation>La corrección ortométrica necesita las latitudes de las estaciones. Indique una capa de puntos con las posiciones de las estaciones y el campo con el identificador de cada estación, o desactive la corrección.</translation>
        </message>
        <message>
            <source>The relative uncertainty is the 1D analogue of the relative error ellipse, and is usually what a levelling network was built to produce. It is not the difference of the two individual uncertainties: adjusted heights are correlated, and two marks at the ends of one well-observed line know their separation far better than either knows its own height.</source>
            <translation>La incertidumbre relativa es el análogo 1D de la elipse de error relativa y suele ser lo que una red de nivelación fue construida para producir. No es la diferencia de las dos incertidumbres individuales: las altitudes ajustadas están correlacionadas, y dos referencias en los extremos de una línea bien observada conocen su separación mucho mejor de lo que cualquiera de ellas conoce su propia altitud.</translation>
        </message>
        <message>
            <source>The station positions layer has no valid CRS, so its points cannot be read as latitudes. Set the layer's CRS.</source>
            <translation>La capa de posiciones de las estaciones no tiene un SRC válido, así que sus puntos no pueden leerse como latitudes. Defina el SRC de la capa.</translation>
        </message>
        <message>
            <source>The trigonometric height differences cannot be read: %1</source>
            <translation>Los desniveles trigonométricos no se pueden leer: %1</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Tolerance coefficient k (m per root km; 0 judges nothing)</source>
            <translation>Coeficiente de tolerancia k (m por raíz de km; 0 no evalúa nada)</translation>
        </message>
        <message>
            <source>Trigonometric height differences (optional)</source>
            <translation>Desniveles trigonométricos (opcional)</translation>
        </message>
        <message>
            <source>Uncertainty (mm)</source>
            <translation>Incertidumbre (mm)</translation>
        </message>
        <message>
            <source>Uncertainty per root kilometre (m)</source>
            <translation>Incertidumbre por raíz de kilómetro (m)</translation>
        </message>
        <message>
            <source>Uncertainty per root setup (m)</source>
            <translation>Incertidumbre por raíz de estacionamiento (m)</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Variance components</source>
            <translation>Componentes de varianza</translation>
        </message>
        <message>
            <source>Variance components by technique</source>
            <translation>Componentes de varianza por técnica</translation>
        </message>
        <message>
            <source>Variance factor</source>
            <translation>Factor de varianza</translation>
        </message>
        <message>
            <source>Variance factor of %1: %2 ± %3 (%4 observations)</source>
            <translation>Factor de varianza de %1: %2 ± %3 (%4 observaciones)</translation>
        </message>
        <message>
            <source>Verdict</source>
            <translation>Veredicto</translation>
        </message>
        <message>
            <source>Weighting</source>
            <translation>Ponderación</translation>
        </message>
        <message>
            <source>What was applied</source>
            <translation>Qué se aplicó</translation>
        </message>
        <message>
            <source>What was checked</source>
            <translation>Qué se verificó</translation>
        </message>
        <message>
            <source>Why these are not the individual figures</source>
            <translation>Por qué estos no son los valores individuales</translation>
        </message>
        <message>
            <source>dH (m)</source>
            <translation>dH (m)</translation>
        </message>
        <message>
            <source>not judged — no tolerance coefficient was configured</source>
            <translation>no evaluado — no se configuró ningún coeficiente de tolerancia</translation>
        </message>
        <message>
            <source>passed</source>
            <translation>aprobó</translation>
        </message>
        <message>
            <source>propagated from the staff readings</source>
            <translation>propagada a partir de las lecturas de mira</translation>
        </message>
        <message>
            <source>w</source>
            <translation>w</translation>
        </message>
        <message>
            <source>within the %1 mm permitted</source>
            <translation>dentro de los %1 mm permitidos</translation>
        </message>
    </context>
    <context>
        <name>MonitoringCompareEpochsAlgorithm</name>
        <message>
            <source>&lt;p&gt;Compares two solutions of the same network and says which stations moved, by how much, and with what confidence.&lt;/p&gt;&lt;p&gt;Before anything is differenced, the epochs are checked: a solution without an epoch, heights of different types or geoid models, a free datum against a held one, and two projections are refused by name, because each would put a systematic difference into every displacement. Geocentric solutions in different frames are transformed, and the transformation's own uncertainty is carried.&lt;/p&gt;&lt;p&gt;The &lt;b&gt;reference stations&lt;/b&gt; are the pillars assumed stable. Their congruency is tested first; if they moved relative to one another, the analysis names the stations and &lt;b&gt;refuses&lt;/b&gt; to report displacements against them, after writing the report with every localisation step. Leave the field empty to take the stations marked REFERENCE in the network document.&lt;/p&gt;&lt;p&gt;Every displacement is tested against its own covariance and reported as &lt;i&gt;significant&lt;/i&gt; or &lt;i&gt;not significant&lt;/i&gt; with its value, never as zero. Without the covariance between the epochs, they are taken as independent and the result says so, and which way that errs.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;First / second epoch&lt;/b&gt; &amp;mdash; solution documents written by an adjustment algorithm.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Network document&lt;/b&gt; &amp;mdash; optional; where the monitoring roles are read from, and where a heights-only network's stations are placed on the map.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum of the displacements&lt;/b&gt; &amp;mdash; what the reference block fixes: translation (heights, geocentric), translation and rotation (a plan), or a similarity.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Alert thresholds&lt;/b&gt; &amp;mdash; a CSV file of &lt;code&gt;kind, limit, stations, group&lt;/code&gt;: kind is magnitude, horizontal, vertical or significance; limits in metres; stations separated by spaces or semicolons, empty for all. A station over its limit is flagged whether or not its motion is significant.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exaggeration&lt;/b&gt; &amp;mdash; the factor the arrows and ellipses are drawn at, stated in the layer names; 0 fits it to the network.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Compara dos soluciones de la misma red y dice qué estaciones se movieron, cuánto, y con qué confianza.&lt;/p&gt;&lt;p&gt;Antes de diferenciar nada, se verifican las épocas: una solución sin época, alturas de tipos o modelos geoidales distintos, un datum libre frente a uno fijado, y dos proyecciones se rechazan por su nombre, porque cada uno introduciría una diferencia sistemática en todos los desplazamientos. Las soluciones geocéntricas en marcos distintos se transforman, y se propaga la incertidumbre propia de la transformación.&lt;/p&gt;&lt;p&gt;Las &lt;b&gt;estaciones de referencia&lt;/b&gt; son los pilares supuestos estables. Primero se prueba su congruencia; si se movieron unas respecto de otras, el análisis nombra las estaciones y &lt;b&gt;se niega&lt;/b&gt; a dar desplazamientos contra ellas, tras escribir el informe con cada paso de la localización. Deje el campo vacío para tomar las estaciones marcadas REFERENCE en el documento de la red.&lt;/p&gt;&lt;p&gt;Cada desplazamiento se prueba contra su propia covarianza y se informa como &lt;i&gt;significativo&lt;/i&gt; o &lt;i&gt;no significativo&lt;/i&gt; con su valor, nunca como cero. Sin la covarianza entre las épocas, se toman como independientes y el resultado lo dice, y en qué sentido yerra.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Primera / segunda época&lt;/b&gt; &amp;mdash; documentos de solución escritos por un algoritmo de ajuste.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Documento de la red&lt;/b&gt; &amp;mdash; opcional; de donde se leen los roles de monitoreo, y donde se sitúan en el mapa las estaciones de una red solo de alturas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum de los desplazamientos&lt;/b&gt; &amp;mdash; lo que fija el bloque de referencia: traslación (alturas, geocéntrico), traslación y rotación (planimetría), o una semejanza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbrales de alerta&lt;/b&gt; &amp;mdash; un archivo CSV de &lt;code&gt;kind, limit, stations, group&lt;/code&gt;: kind es magnitude, horizontal, vertical o significance; límites en metros; estaciones separadas por espacios o punto y coma, vacío para todas. Una estación por encima de su límite se señala sea o no significativo su movimiento.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración&lt;/b&gt; &amp;mdash; el factor con que se dibujan flechas y elipses, indicado en los nombres de las capas; 0 lo ajusta a la red.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Alert thresholds (CSV)</source>
            <translation>Umbrales de alerta (CSV)</translation>
        </message>
        <message>
            <source>Alert thresholds crossed at: %1.</source>
            <translation>Umbrales de alerta superados en: %1.</translation>
        </message>
        <message>
            <source>Analysis document</source>
            <translation>Documento del análisis</translation>
        </message>
        <message>
            <source>Arrows and ellipses are drawn exaggerated %1x.</source>
            <translation>Las flechas y elipses se dibujan exageradas %1x.</translation>
        </message>
        <message>
            <source>Compare two epochs</source>
            <translation>Comparar dos épocas</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Datum of the displacements</source>
            <translation>Datum de los desplazamientos</translation>
        </message>
        <message>
            <source>Displacement ellipses (layer)</source>
            <translation>Elipses de los desplazamientos (capa)</translation>
        </message>
        <message>
            <source>Displacements (layer)</source>
            <translation>Desplazamientos (capa)</translation>
        </message>
        <message>
            <source>Displacements between two epochs, tested against the reference block.</source>
            <translation>Desplazamientos entre dos épocas, probados contra el bloque de referencia.</translation>
        </message>
        <message>
            <source>Exaggeration of arrows and ellipses (0 = from the network's extent)</source>
            <translation>Exageración de flechas y elipses (0 = según la extensión de la red)</translation>
        </message>
        <message>
            <source>First epoch (solution)</source>
            <translation>Primera época (solución)</translation>
        </message>
        <message>
            <source>GeoComp monitoring document (*.json)</source>
            <translation>Documento de monitoreo GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Monitoring report</source>
            <translation>Informe de monitoreo</translation>
        </message>
        <message>
            <source>Network document (monitoring roles)</source>
            <translation>Documento de la red (roles de monitoreo)</translation>
        </message>
        <message>
            <source>Object stations (comma-separated; empty for all others)</source>
            <translation>Estaciones objeto (separadas por comas; vacío para todas las demás)</translation>
        </message>
        <message>
            <source>Reference stations (comma-separated)</source>
            <translation>Estaciones de referencia (separadas por comas)</translation>
        </message>
        <message>
            <source>Second epoch (solution)</source>
            <translation>Segunda época (solución)</translation>
        </message>
        <message>
            <source>Separate rigid-body motion from strain</source>
            <translation>Separar el movimiento de cuerpo rígido de la deformación</translation>
        </message>
        <message>
            <source>Significant motion at %1 of %2 stations: %3.</source>
            <translation>Movimiento significativo en %1 de %2 estaciones: %3.</translation>
        </message>
        <message>
            <source>Strain was not computed: the object points do not span an area.</source>
            <translation>La deformación no se calculó: los puntos objeto no abarcan un área.</translation>
        </message>
        <message>
            <source>The epochs were taken as independent; the displacements' uncertainty is overstated if they share reference stations or products, so real motion may be reported not significant.</source>
            <translation>Las épocas se tomaron como independientes; la incertidumbre de los desplazamientos se sobreestima si comparten estaciones de referencia o productos, y un movimiento real puede declararse no significativo.</translation>
        </message>
        <message>
            <source>The localisation is recorded in: %1</source>
            <translation>La localización queda registrada en: %1</translation>
        </message>
        <message>
            <source>The stations have no plan position, so nothing is drawn on the map. Give the network document to place a heights-only network's stations.</source>
            <translation>Las estaciones no tienen posición planimétrica, así que no se dibuja nada en el mapa. Indique el documento de la red para situar las estaciones de una red solo de alturas.</translation>
        </message>
        <message>
            <source>Transformed %1 at %2 into %3, accuracy %4 mm, common to every station.</source>
            <translation>Transformado de %1 en %2 a %3, exactitud %4 mm, común a todas las estaciones.</translation>
        </message>
        <message>
            <source>none</source>
            <translation>ninguna</translation>
        </message>
    </context>
    <context>
        <name>MonitoringReportAlgorithm</name>
        <message>
            <source>&lt;p&gt;Renders the monitoring report: the epochs and every transformation applied, the reference block's test and its localisation, the displacements with their significance decisions, a displacement map, the deformation, the alerts, and the time series and velocities.&lt;/p&gt;&lt;p&gt;Built from the documents &lt;i&gt;Compare two epochs&lt;/i&gt; and &lt;i&gt;Time series and velocities&lt;/i&gt; write, and nothing else, so it renders the same report from the saved files at any later date.&lt;/p&gt;&lt;p&gt;Three sections are placed even by a template that leaves them out: the uncertainty mode with the direction of its bias, the compatibility findings and transformations, and the reference block's test. Every decision in the report rests on them.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Analysis document&lt;/b&gt; and &lt;b&gt;Series document&lt;/b&gt; &amp;mdash; at least one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report template&lt;/b&gt; &amp;mdash; optional HTML template (FR-931).&lt;/p&gt;</source>
            <translation>&lt;p&gt;Genera el informe de monitoreo: las épocas y cada transformación aplicada, la prueba del bloque de referencia y su localización, los desplazamientos con sus decisiones de significancia, un mapa de los desplazamientos, la deformación, las alertas, y las series temporales y velocidades.&lt;/p&gt;&lt;p&gt;Se construye a partir de los documentos que escriben &lt;i&gt;Comparar dos épocas&lt;/i&gt; y &lt;i&gt;Series temporales y velocidades&lt;/i&gt;, y nada más, así que genera el mismo informe a partir de los archivos guardados en cualquier fecha posterior.&lt;/p&gt;&lt;p&gt;Tres secciones se incluyen aunque una plantilla las omita: el modo de incertidumbre con el sentido de su sesgo, los hallazgos de compatibilidad y las transformaciones, y la prueba del bloque de referencia. Todas las decisiones del informe se apoyan en ellas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Documento del análisis&lt;/b&gt; y &lt;b&gt;Documento de la serie&lt;/b&gt; &amp;mdash; al menos uno.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Plantilla del informe&lt;/b&gt; &amp;mdash; plantilla HTML opcional (FR-931).&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Analysis document (Compare two epochs)</source>
            <translation>Documento del análisis (Comparar dos épocas)</translation>
        </message>
        <message>
            <source>Exaggeration of the map (0 = from the network's extent)</source>
            <translation>Exageración del mapa (0 = según la extensión de la red)</translation>
        </message>
        <message>
            <source>Give an analysis document, a series document, or both.</source>
            <translation>Indique un documento de análisis, un documento de serie, o ambos.</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Monitoring report</source>
            <translation>Informe de monitoreo</translation>
        </message>
        <message>
            <source>Render the monitoring report from a comparison, a series, or both.</source>
            <translation>Generar el informe de monitoreo a partir de una comparación, una serie, o ambas.</translation>
        </message>
        <message>
            <source>Report template (optional)</source>
            <translation>Plantilla de informe (opcional)</translation>
        </message>
        <message>
            <source>Report written.</source>
            <translation>Informe escrito.</translation>
        </message>
        <message>
            <source>Series document (Time series and velocities)</source>
            <translation>Documento de la serie (Series temporales y velocidades)</translation>
        </message>
        <message>
            <source>The template places no: </source>
            <translation>La plantilla no incluye: </translation>
        </message>
    </context>
    <context>
        <name>MonitoringTimeSeriesAlgorithm</name>
        <message>
            <source>%1 stations over %2 epochs; velocity significant at: %3.</source>
            <translation>%1 estaciones en %2 épocas; velocidad significativa en: %3.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Follows every station through any number of epochs: its offset from the first epoch with each epoch's own uncertainty, and its velocity by weighted least squares, with the velocity's uncertainty and a test of whether it differs from zero.&lt;/p&gt;&lt;p&gt;Every epoch is referred to the &lt;b&gt;reference stations&lt;/b&gt; by an S-transformation, and their congruency with the first epoch is tested at every epoch: a velocity measured against a pillar that moved is the pillar's. The run refuses at the first epoch where the block fails, and names it. Leave the field empty to take the stations marked REFERENCE in the network document; with none there either, the epochs are taken in their own datums, which is right only if they were all held the same way.&lt;/p&gt;&lt;p&gt;The velocity layer is tied to its series: select a station on it and the time-series panel plots that station.&lt;/p&gt;&lt;p&gt;The epochs are taken as independent, and the result is marked approximate.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solutions&lt;/b&gt; &amp;mdash; two or more solution documents of the same network, in any order; they are sorted by epoch.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Alert thresholds&lt;/b&gt; &amp;mdash; a CSV file of &lt;code&gt;kind, limit, stations, group&lt;/code&gt;; a &lt;i&gt;velocity&lt;/i&gt; row sets a limit in metres a year on the horizontal speed, or the vertical rate of a heights-only series.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exaggeration&lt;/b&gt; &amp;mdash; the factor a year's motion is drawn at; 0 fits it to the network.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Sigue cada estación a lo largo de cualquier número de épocas: su desplazamiento respecto a la primera época con la incertidumbre propia de cada época, y su velocidad por mínimos cuadrados ponderados, con la incertidumbre de la velocidad y una prueba de si difiere de cero.&lt;/p&gt;&lt;p&gt;Cada época se refiere a las &lt;b&gt;estaciones de referencia&lt;/b&gt; mediante una transformación S, y su congruencia con la primera época se prueba en cada época: una velocidad medida contra un pilar que se movió es la del pilar. La ejecución se detiene en la primera época en que el bloque falla, y la nombra. Deje el campo vacío para tomar las estaciones marcadas REFERENCE en el documento de la red; si tampoco hay ninguna allí, las épocas se toman en sus propios datums, lo que solo es correcto si todas se fijaron del mismo modo.&lt;/p&gt;&lt;p&gt;La capa de velocidades está ligada a su serie: seleccione en ella una estación y el panel de series temporales dibuja esa estación.&lt;/p&gt;&lt;p&gt;Las épocas se toman como independientes, y el resultado se marca como aproximado.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Soluciones&lt;/b&gt; &amp;mdash; dos o más documentos de solución de la misma red, en cualquier orden; se ordenan por época.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbrales de alerta&lt;/b&gt; &amp;mdash; un archivo CSV de &lt;code&gt;kind, limit, stations, group&lt;/code&gt;; una fila &lt;i&gt;velocity&lt;/i&gt; fija un límite en metros por año sobre la rapidez horizontal, o sobre la tasa vertical de una serie solo de alturas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración&lt;/b&gt; &amp;mdash; el factor con que se dibuja el movimiento de un año; 0 lo ajusta a la red.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A series needs two epochs at least; %1 was given.</source>
            <translation>Una serie necesita al menos dos épocas; se dio %1.</translation>
        </message>
        <message>
            <source>Alert thresholds (CSV)</source>
            <translation>Umbrales de alerta (CSV)</translation>
        </message>
        <message>
            <source>At the epoch of '%1' (%2): </source>
            <translation>En la época de '%1' (%2): </translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Datum of the offsets</source>
            <translation>Datum de los desplazamientos respecto a la primera época</translation>
        </message>
        <message>
            <source>Every station's offsets across the epochs, and its velocity.</source>
            <translation>Los desplazamientos de cada estación a lo largo de las épocas, y su velocidad.</translation>
        </message>
        <message>
            <source>Exaggeration of a year's motion (0 = from the network's extent)</source>
            <translation>Exageración del movimiento de un año (0 = según la extensión de la red)</translation>
        </message>
        <message>
            <source>GeoComp monitoring document (*.json)</source>
            <translation>Documento de monitoreo GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Monitoring report</source>
            <translation>Informe de monitoreo</translation>
        </message>
        <message>
            <source>Network document (monitoring roles)</source>
            <translation>Documento de la red (roles de monitoreo)</translation>
        </message>
        <message>
            <source>No reference stations: each epoch is taken in its own datum, which is right only if every epoch was held the same way.</source>
            <translation>Sin estaciones de referencia: cada época se toma en su propio datum, lo que solo es correcto si todas las épocas se fijaron del mismo modo.</translation>
        </message>
        <message>
            <source>Reference block congruent between %1 and %2.</source>
            <translation>Bloque de referencia congruente entre %1 y %2.</translation>
        </message>
        <message>
            <source>Reference stations (comma-separated)</source>
            <translation>Estaciones de referencia (separadas por comas)</translation>
        </message>
        <message>
            <source>Series document</source>
            <translation>Documento de la serie</translation>
        </message>
        <message>
            <source>Series table</source>
            <translation>Tabla de la serie</translation>
        </message>
        <message>
            <source>Solutions, one per epoch</source>
            <translation>Soluciones, una por época</translation>
        </message>
        <message>
            <source>The stations have no plan position, so nothing is drawn on the map. Give the network document to place a heights-only network's stations.</source>
            <translation>Las estaciones no tienen posición planimétrica, así que no se dibuja nada en el mapa. Indique el documento de la red para situar las estaciones de una red solo de alturas.</translation>
        </message>
        <message>
            <source>Time series and velocities</source>
            <translation>Series temporales y velocidades</translation>
        </message>
        <message>
            <source>Velocities (layer)</source>
            <translation>Velocidades (capa)</translation>
        </message>
        <message>
            <source>Velocity thresholds crossed at: %1.</source>
            <translation>Umbrales de velocidad superados en: %1.</translation>
        </message>
        <message>
            <source>none</source>
            <translation>ninguna</translation>
        </message>
    </context>
    <context>
        <name>NetworkAdjustAlgorithm</name>
        <message>
            <source>%1 observation(s) exceed the w-test critical value.</source>
            <translation>%1 observación(es) supera(n) el valor crítico de la prueba w.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts a geodetic network by least squares using the parametric model, iterating the linearised solution to convergence, and reports the adjusted coordinates with their full covariance matrix, the residuals, and the statistical tests that say whether the result may be believed.&lt;/p&gt;&lt;p&gt;1D, 2D and 3D networks are all supported, free or constrained. The weight matrix is built from the observation covariances, including correlations between the observations of a correlated cluster such as a GNSS baseline.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Non-convergence is reported as a failure&lt;/b&gt;, never returned as a result. A set of coordinates that is really iteration seven of a diverging sequence is worse than no result, because nothing about it says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours; re-adjusting after removing one is a second, explicit run. Automatic iterative rejection deletes real signal, which in deformation monitoring is the very thing being measured.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D. It decides which parameters exist and which observations can contribute.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;i&gt;Constrained&lt;/i&gt; and &lt;i&gt;Fixed&lt;/i&gt; hold the stations the network declares as constrained. &lt;i&gt;Inner constraint&lt;/i&gt; gives a free network whose solution is the trace minimum over all stations. &lt;i&gt;Minimum constraint&lt;/i&gt; does the same over the chosen stations, which is what a deformation analysis needs: holding a station that has itself moved spreads its motion across the network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; comma-separated; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the global test, the w-test and the error ellipses, between 0 and 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared the global test compares against.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Convergence threshold&lt;/b&gt; &amp;mdash; the largest parameter correction accepted as converged, in metres. &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; after which non-convergence is reported.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the decimal year the coordinates refer to. It is recorded on the solution because comparing two epochs is only meaningful when both say which they are. 0, the default unless Global Settings states one, takes the network's own; where the network states none either, the solution carries 2000.0 marked as assumed, and no comparison accepts it.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a JSON document holding the adjusted coordinates, the full covariance matrix, the per-observation results and the provenance. It is the same structure an external engine's result fills, so everything downstream is engine-independent.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; and &lt;b&gt;Residuals&lt;/b&gt; &amp;mdash; CSV tables for a spreadsheet or a model.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Result layers&lt;/b&gt; &amp;mdash; five optional map layers, arriving styled and ready to read (FR-905): adjusted stations sized by their positional uncertainty, error ellipses, observations coloured by what the w-test decided about them, the measured network by observation type, and the coordinate correction vectors. None is created unless asked for, so an adjustment run to feed another algorithm writes nothing extra.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ellipse exaggeration&lt;/b&gt; &amp;mdash; real ellipses are invisible at map scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to the network's own extent. Whatever factor is used is stated in the layer's name, which is what reaches the legend: an unstated exaggeration turns a quality visualisation into a misrepresentation.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta una red geodésica por mínimos cuadrados usando el modelo paramétrico, iterando la solución linealizada hasta la convergencia, e informa de las coordenadas ajustadas con su matriz de covarianzas completa, los residuos y las pruebas estadísticas que dicen si el resultado puede creerse.&lt;/p&gt;&lt;p&gt;Se admiten redes 1D, 2D y 3D, libres o ligadas. La matriz de pesos se construye a partir de las covarianzas de las observaciones, incluidas las correlaciones entre las observaciones de un agrupamiento correlacionado, como una línea base GNSS.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La no convergencia se comunica como un fallo&lt;/b&gt;, nunca se devuelve como resultado. Un conjunto de coordenadas que en realidad es la séptima iteración de una sucesión divergente es peor que ningún resultado, porque nada en él lo indica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya; reajustar tras eliminar una es una segunda ejecución, explícita. El rechazo iterativo automático borra señal real, que en el seguimiento de deformaciones es precisamente lo que se está midiendo.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D o 3D. Decide qué parámetros existen y qué observaciones pueden contribuir.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina la deficiencia de datum. &lt;i&gt;Ligada&lt;/i&gt; y &lt;i&gt;Fija&lt;/i&gt; mantienen las estaciones que la red declara constreñidas. &lt;i&gt;Constricción interna&lt;/i&gt; da una red libre cuya solución es la traza mínima sobre todas las estaciones. &lt;i&gt;Constricción mínima&lt;/i&gt; hace lo mismo sobre las estaciones elegidas, que es lo que exige un análisis de deformación: mantener una estación que se ha movido reparte su movimiento por toda la red.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Estaciones del datum&lt;/b&gt; &amp;mdash; separadas por comas; vacío significa todas ellas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la prueba global, la prueba w y las elipses de errores, entre 0 y 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Factor de varianza a priori&lt;/b&gt; &amp;mdash; el sigma-cero al cuadrado supuesto con el que compara la prueba global.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbral de convergencia&lt;/b&gt; &amp;mdash; la mayor corrección de parámetro aceptada como convergida, en metros. &lt;b&gt;Número máximo de iteraciones&lt;/b&gt; &amp;mdash; tras el cual se comunica la no convergencia.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significación&lt;/b&gt; y &lt;b&gt;error tipo II&lt;/b&gt; &amp;mdash; alfa y beta para el sesgo mínimo detectable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Época de referencia&lt;/b&gt; &amp;mdash; el año decimal al que se refieren las coordenadas. Se registra en la solución porque comparar dos épocas solo tiene sentido cuando ambas dicen cuáles son. 0, el valor por defecto cuando la Configuración global no declara una, toma la de la propia red; cuando la red tampoco declara ninguna, la solución lleva 2000.0 marcada como supuesta, y ninguna comparación la acepta.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; un documento JSON con las coordenadas ajustadas, la matriz de covarianzas completa, los resultados por observación y la procedencia. Es la misma estructura que rellena el resultado de un motor externo, de modo que todo lo que viene después es independiente del motor.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; y &lt;b&gt;Residuos&lt;/b&gt; &amp;mdash; tablas CSV para una hoja de cálculo o un modelo.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; y &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Capas de resultado&lt;/b&gt; &amp;mdash; cinco capas opcionales, que llegan con estilo y listas para leer (FR-905): estaciones ajustadas dimensionadas por su incertidumbre posicional, elipses de error, observaciones coloreadas según lo que decidió la prueba w, la red medida por tipo de observación y los vectores de corrección de coordenadas. Ninguna se crea sin solicitarla, de modo que un ajuste ejecutado para alimentar otro algoritmo no escribe nada de más.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración de las elipses&lt;/b&gt; &amp;mdash; las elipses reales son invisibles a escala de mapa, por lo que se dibujan ampliadas. Déjelo en 0 y se ajusta un factor a la propia extensión de la red. Sea cual sea el factor utilizado, se declara en el nombre de la capa, que es lo que llega a la leyenda: una exageración no declarada convierte una visualización de calidad en una tergiversación.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A posteriori variance factor</source>
            <translation>Factor de varianza a posteriori</translation>
        </message>
        <message>
            <source>A priori variance factor</source>
            <translation>Factor de varianza a priori</translation>
        </message>
        <message>
            <source>Adjust network</source>
            <translation>Ajustar red</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estaciones ajustadas</translation>
        </message>
        <message>
            <source>Adjusted stations (table)</source>
            <translation>Estaciones ajustadas (tabla)</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
        </message>
        <message>
            <source>Adjustment</source>
            <translation>Ajuste</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Condition number</source>
            <translation>Número de condición</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Converged in %1 iteration(s); largest correction %2 m.</source>
            <translation>Convergió en %1 iteración(es); mayor corrección %2 m.</translation>
        </message>
        <message>
            <source>Convergence threshold (m)</source>
            <translation>Umbral de convergencia (m)</translation>
        </message>
        <message>
            <source>Coordinate frame</source>
            <translation>Marco de coordenadas</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Deficiencia de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1 (removed by: %2).</source>
            <translation>Deficiencia de datum: %1 (eliminada por: %2).</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>Datum stations (comma-separated; empty = all)</source>
            <translation>Estaciones del datum (separadas por comas; vacío = todas)</translation>
        </message>
        <message>
            <source>Decision</source>
            <translation>Decisión</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>External effect</source>
            <translation>Efecto externo</translation>
        </message>
        <message>
            <source>Fails</source>
            <translation>Falla</translation>
        </message>
        <message>
            <source>Flag</source>
            <translation>Marca</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_adjust</source>
            <translation>Generado por GeoComp — geocomp:analysis_network_adjust</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solución GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iteraciones</translation>
        </message>
        <message>
            <source>Largest final correction (m)</source>
            <translation>Mayor corrección final (m)</translation>
        </message>
        <message>
            <source>Least-squares adjustment with the global test, data snooping and reliability.</source>
            <translation>Ajuste por mínimos cuadrados con la prueba global, el data snooping y la fiabilidad.</translation>
        </message>
        <message>
            <source>Lower critical value</source>
            <translation>Valor crítico inferior</translation>
        </message>
        <message>
            <source>Maximum iterations</source>
            <translation>Número máximo de iteraciones</translation>
        </message>
        <message>
            <source>Minimal detectable bias</source>
            <translation>Sesgo mínimo detectable (MDB)</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>Network adjustment report</source>
            <translation>Informe de ajuste de la red</translation>
        </message>
        <message>
            <source>Network document</source>
            <translation>Documento de la red</translation>
        </message>
        <message>
            <source>No observation exceeds the w-test critical value.</source>
            <translation>Ninguna observación supera el valor crítico de la prueba w.</translation>
        </message>
        <message>
            <source>Nothing has been rejected: removing an observation is your decision.</source>
            <translation>No se ha rechazado nada: eliminar una observación es decisión suya.</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Observation equations</source>
            <translation>Ecuaciones de observación</translation>
        </message>
        <message>
            <source>Observations exceeding the critical value are candidates, not rejections. Nothing has been removed: investigate the largest, decide, re-adjust, and test again.</source>
            <translation>Las observaciones que superan el valor crítico son candidatas, no rechazos. No se ha eliminado nada: investigue la mayor, decida, reajuste y vuelva a probar.</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Passes</source>
            <translation>Pasa</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Reference epoch, decimal year (0 = the network's own)</source>
            <translation>Época de referencia, año decimal (0 = la de la propia red)</translation>
        </message>
        <message>
            <source>Reliability</source>
            <translation>Fiabilidad</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Residual</source>
            <translation>Residuo</translation>
        </message>
        <message>
            <source>Residuals (table)</source>
            <translation>Residuos (tabla)</translation>
        </message>
        <message>
            <source>Residuals and data snooping</source>
            <translation>Residuos y data snooping</translation>
        </message>
        <message>
            <source>Semi-major (m)</source>
            <translation>Semieje mayor (m)</translation>
        </message>
        <message>
            <source>Semi-minor (m)</source>
            <translation>Semieje menor (m)</translation>
        </message>
        <message>
            <source>Significance for the minimal detectable bias</source>
            <translation>Significación para el sesgo mínimo detectable</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solución</translation>
        </message>
        <message>
            <source>Solving method</source>
            <translation>Método de solución</translation>
        </message>
        <message>
            <source>Standardised residual</source>
            <translation>Residuo estandarizado</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estadístico</translation>
        </message>
        <message>
            <source>Std dev X (m)</source>
            <translation>Desviación típica X (m)</translation>
        </message>
        <message>
            <source>Std dev Y (m)</source>
            <translation>Desviación típica Y (m)</translation>
        </message>
        <message>
            <source>Std dev Z (m)</source>
            <translation>Desviación típica Z (m)</translation>
        </message>
        <message>
            <source>The global test fails: %1</source>
            <translation>La prueba global falla: %1</translation>
        </message>
        <message>
            <source>The global test passes.</source>
            <translation>La prueba global pasa.</translation>
        </message>
        <message>
            <source>Type II error for the minimal detectable bias</source>
            <translation>Error tipo II para el sesgo mínimo detectable</translation>
        </message>
        <message>
            <source>Upper critical value</source>
            <translation>Valor crítico superior</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Variance factor %1 on %2 degree(s) of freedom.</source>
            <translation>Factor de varianza %1 con %2 grado(s) de libertad.</translation>
        </message>
        <message>
            <source>X (m)</source>
            <translation>X (m)</translation>
        </message>
        <message>
            <source>Y (m)</source>
            <translation>Y (m)</translation>
        </message>
        <message>
            <source>Z (m)</source>
            <translation>Z (m)</translation>
        </message>
        <message>
            <source>candidate</source>
            <translation>candidata</translation>
        </message>
        <message>
            <source>uncheckable</source>
            <translation>no verificable</translation>
        </message>
    </context>
    <context>
        <name>NetworkInspectAlgorithm</name>
        <message>
            <source>%1 station(s), %2 observation(s), %3 active.</source>
            <translation>%1 estación(es), %2 observación(es), %3 activa(s).</translation>
        </message>
        <message>
            <source>(unnamed)</source>
            <translation>(sin nombre)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Checks a geodetic network for the problems that stop an adjustment or make its result mean something other than what the user expects: stations that take part in no observation, a network that falls into disconnected pieces each with its own datum, observation types the in-house adjustment does not implement, observations that cannot contribute to the chosen dimensionality, repeated observations, and missing approximate coordinates.&lt;/p&gt;&lt;p&gt;Findings are graded. &lt;b&gt;Blocking&lt;/b&gt; means the adjustment cannot run. &lt;b&gt;Warning&lt;/b&gt; means it can, but the result may not mean what you expect. &lt;b&gt;Information&lt;/b&gt; is worth seeing and is not a problem.&lt;/p&gt;&lt;p&gt;Every finding is reported in one pass, so a network with several problems needs one run rather than one run per problem.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; which of 1D, 2D and 3D the network is to be adjusted in. It decides which observations can contribute and how many observations a station needs.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fail if the network cannot be adjusted&lt;/b&gt; &amp;mdash; when set, a blocking finding stops the algorithm, so a model that chains inspect into adjust does not proceed on a network that cannot be adjusted. When unset, the algorithm always succeeds and reports its findings, which is what an interactive check wants.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; destination HTML file. &lt;b&gt;Findings table&lt;/b&gt; &amp;mdash; destination CSV, one row per finding, for use in a model or a spreadsheet.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;CAN_ADJUST&lt;/code&gt; (boolean), &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;, &lt;code&gt;WARNING_COUNT&lt;/code&gt; and &lt;code&gt;COMPONENT_COUNT&lt;/code&gt; &amp;mdash; the number of connected pieces, which is 1 for a network that hangs together.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Comprueba en una red geodésica los problemas que impiden un ajuste o hacen que su resultado signifique algo distinto de lo que el usuario espera: estaciones que no participan en ninguna observación, una red que se divide en partes desconectadas, cada una con su propio datum, tipos de observación que el ajuste propio aún no implementa, observaciones que no pueden contribuir a la dimensionalidad elegida, observaciones repetidas y coordenadas aproximadas ausentes.&lt;/p&gt;&lt;p&gt;Los hallazgos están graduados. &lt;b&gt;Bloqueante&lt;/b&gt; significa que el ajuste no puede ejecutarse. &lt;b&gt;Advertencia&lt;/b&gt; significa que sí puede, pero el resultado quizá no signifique lo que se espera. &lt;b&gt;Información&lt;/b&gt; merece verse y no es un problema.&lt;/p&gt;&lt;p&gt;Todos los hallazgos se comunican en una sola pasada, de modo que una red con varios problemas requiere una ejecución, y no una ejecución por problema.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; si la red se ajustará en 1D, 2D o 3D. Ello decide qué observaciones pueden contribuir y cuántas observaciones necesita una estación.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fallar si la red no puede ajustarse&lt;/b&gt; &amp;mdash; cuando se marca, un hallazgo bloqueante detiene el algoritmo, de modo que un modelo que encadena la inspección con el ajuste no prosiga sobre una red que no puede ajustarse. Cuando no se marca, el algoritmo siempre tiene éxito y comunica sus hallazgos, que es lo que quiere una comprobación interactiva.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; archivo HTML de destino. &lt;b&gt;Tabla de hallazgos&lt;/b&gt; &amp;mdash; archivo CSV de destino, una fila por hallazgo, para su uso en un modelo o en una hoja de cálculo.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;CAN_ADJUST&lt;/code&gt; (booleano), &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;, &lt;code&gt;WARNING_COUNT&lt;/code&gt; y &lt;code&gt;COMPONENT_COUNT&lt;/code&gt; &amp;mdash; el número de partes conectadas, que es 1 para una red que se mantiene unida.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Active observations</source>
            <translation>Observaciones activas</translation>
        </message>
        <message>
            <source>Blocking</source>
            <translation>Bloqueante</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Check a network for the problems that block or distort an adjustment.</source>
            <translation>Comprueba en una red los problemas que impiden o distorsionan un ajuste.</translation>
        </message>
        <message>
            <source>Code</source>
            <translation>Código</translation>
        </message>
        <message>
            <source>Connected pieces</source>
            <translation>Partes conectadas</translation>
        </message>
        <message>
            <source>Coordinate frame</source>
            <translation>Marco de coordenadas</translation>
        </message>
        <message>
            <source>Each piece has its own datum. They cannot be adjusted together until an observation joins them.</source>
            <translation>Cada parte tiene su propio datum. No pueden ajustarse conjuntamente mientras ninguna observación las una.</translation>
        </message>
        <message>
            <source>Fail if the network cannot be adjusted</source>
            <translation>Fallar si la red no puede ajustarse</translation>
        </message>
        <message>
            <source>Finding</source>
            <translation>Hallazgo</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>Findings table</source>
            <translation>Tabla de hallazgos</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_inspect</source>
            <translation>Generado por GeoComp — geocomp:analysis_network_inspect</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Información</translation>
        </message>
        <message>
            <source>Inspect network</source>
            <translation>Inspeccionar red</translation>
        </message>
        <message>
            <source>Inspecting network '%1'…</source>
            <translation>Inspeccionando la red '%1'…</translation>
        </message>
        <message>
            <source>Involves</source>
            <translation>Implica</translation>
        </message>
        <message>
            <source>Members</source>
            <translation>Integrantes</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>Network document</source>
            <translation>Documento de la red</translation>
        </message>
        <message>
            <source>Network inspection report</source>
            <translation>Informe de inspección de la red</translation>
        </message>
        <message>
            <source>No problems found.</source>
            <translation>No se encontró ningún problema.</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observaciones</translation>
        </message>
        <message>
            <source>Piece</source>
            <translation>Parte</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Severity</source>
            <translation>Severidad</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>Summary</source>
            <translation>Resumen</translation>
        </message>
        <message>
            <source>The network can be adjusted.</source>
            <translation>La red puede ajustarse.</translation>
        </message>
        <message>
            <source>The network cannot be adjusted as it stands.</source>
            <translation>La red no puede ajustarse tal como está.</translation>
        </message>
        <message>
            <source>The network has %1 blocking problem(s) and cannot be adjusted.</source>
            <translation>La red tiene %1 problema(s) bloqueante(s) y no puede ajustarse.</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Advertencia</translation>
        </message>
    </context>
    <context>
        <name>NetworkPreAnalysisAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes what a &lt;i&gt;planned&lt;/i&gt; network would achieve. The covariance of the adjusted coordinates depends only on the geometry of the planned observations and on their assumed precisions, so it can be computed before the first observation is made.&lt;/p&gt;&lt;p&gt;The planned observations therefore need only a type, the stations they connect, and an assumed standard deviation. Any values they carry are ignored, which is why the simulation is exact rather than an approximation.&lt;/p&gt;&lt;p&gt;Two things are reported, and both matter. &lt;b&gt;Precision&lt;/b&gt; &amp;mdash; the expected error ellipse and positional uncertainty of each station. &lt;b&gt;Reliability&lt;/b&gt; &amp;mdash; the smallest blunder the design could detect in each observation, and the effect on the coordinates of one that slipped through. A design can be precise and still unable to detect a blunder anywhere, so reporting precision alone gives half the answer.&lt;/p&gt;&lt;p&gt;By default the datum is defined by inner constraints, because a design should be judged on its own geometry rather than through the distortion a particular fixed station imposes.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON) describing the planned stations and observations.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; for a minimum-constraint solution, the comma-separated stations the datum is defined on; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Required positional uncertainty&lt;/b&gt; &amp;mdash; the specification the design must meet, in metres, at the stated confidence level. Leave at 0 to report without judging.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the error ellipses, between 0 and 1. &lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared. &lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias; the geodetic defaults 0.001 and 0.20 give the familiar non-centrality 4.13.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;MEETS_TOLERANCE&lt;/code&gt;, &lt;code&gt;WORST_STATION&lt;/code&gt;, &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; &amp;mdash; observations no blunder in which could ever be detected.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula lo que alcanzaría una red &lt;i&gt;planificada&lt;/i&gt;. La covarianza de las coordenadas ajustadas depende únicamente de la geometría de las observaciones planificadas y de sus precisiones supuestas, por lo que puede calcularse antes de realizar la primera observación.&lt;/p&gt;&lt;p&gt;Las observaciones planificadas necesitan, por tanto, solo un tipo, las estaciones que enlazan y una desviación típica supuesta. Cualesquiera valores que lleven se ignoran, y por eso la simulación es exacta y no aproximada.&lt;/p&gt;&lt;p&gt;Se comunican dos cosas, y ambas importan. &lt;b&gt;Precisión&lt;/b&gt; &amp;mdash; la elipse de errores y la incertidumbre posicional esperadas de cada estación. &lt;b&gt;Fiabilidad&lt;/b&gt; &amp;mdash; el menor error grosero que el diseño podría detectar en cada observación, y el efecto sobre las coordenadas de uno que pasara inadvertido. Un diseño puede ser preciso y aun así incapaz de detectar un error grosero en ningún sitio, de modo que comunicar solo la precisión da la mitad de la respuesta.&lt;/p&gt;&lt;p&gt;Por omisión el datum se define mediante constricciones internas, porque un diseño debe juzgarse por su propia geometría y no a través de la distorsión que impone una estación fija concreta.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON) que describe las estaciones y observaciones planificadas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D o 3D.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina la deficiencia de datum. &lt;b&gt;Estaciones del datum&lt;/b&gt; &amp;mdash; para una solución con constricción mínima, las estaciones, separadas por comas, sobre las que se define el datum; vacío significa todas ellas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Incertidumbre posicional exigida&lt;/b&gt; &amp;mdash; la especificación que el diseño debe cumplir, en metros, al nivel de confianza indicado. Déjela en 0 para informar sin juzgar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para las elipses de errores, entre 0 y 1. &lt;b&gt;Factor de varianza a priori&lt;/b&gt; &amp;mdash; el sigma-cero al cuadrado supuesto. &lt;b&gt;Significación&lt;/b&gt; y &lt;b&gt;error tipo II&lt;/b&gt; &amp;mdash; alfa y beta para el sesgo mínimo detectable; los valores geodésicos habituales 0,001 y 0,20 dan el familiar parámetro de no centralidad 4,13.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;MEETS_TOLERANCE&lt;/code&gt;, &lt;code&gt;WORST_STATION&lt;/code&gt;, &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt; y &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; &amp;mdash; observaciones en las que ningún error grosero podría detectarse jamás.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A priori variance factor</source>
            <translation>Factor de varianza a priori</translation>
        </message>
        <message>
            <source>At least one station does not meet the required %1 m.</source>
            <translation>Al menos una estación no cumple los %1 m exigidos.</translation>
        </message>
        <message>
            <source>Azimuth</source>
            <translation>Acimut</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Compute the precision and reliability a planned network would achieve, before any observation exists.</source>
            <translation>Calcula la precisión y la fiabilidad que alcanzaría una red planificada, antes de que exista observación alguna.</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
        </message>
        <message>
            <source>Coordinate frame</source>
            <translation>Marco de coordenadas</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Deficiencia de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1</source>
            <translation>Deficiencia de datum: %1</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definición del datum</translation>
        </message>
        <message>
            <source>Datum stations (comma-separated; empty = all)</source>
            <translation>Estaciones del datum (separadas por comas; vacío = todas)</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Grados de libertad</translation>
        </message>
        <message>
            <source>Design</source>
            <translation>Diseño</translation>
        </message>
        <message>
            <source>Every station meets the required %1 m.</source>
            <translation>Todas las estaciones cumplen los %1 m exigidos.</translation>
        </message>
        <message>
            <source>Expected precision</source>
            <translation>Precisión esperada</translation>
        </message>
        <message>
            <source>Expected reliability</source>
            <translation>Fiabilidad esperada</translation>
        </message>
        <message>
            <source>Expected station precision (table)</source>
            <translation>Precisión esperada de las estaciones (tabla)</translation>
        </message>
        <message>
            <source>External effect (m)</source>
            <translation>Efecto externo (m)</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_preanalysis</source>
            <translation>Generado por GeoComp — geocomp:analysis_network_preanalysis</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Minimal detectable bias</source>
            <translation>Sesgo mínimo detectable (MDB)</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Red</translation>
        </message>
        <message>
            <source>Network pre-analysis report</source>
            <translation>Informe de preanálisis de la red</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observación</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parámetros</translation>
        </message>
        <message>
            <source>Planned network document</source>
            <translation>Documento de la red planificada</translation>
        </message>
        <message>
            <source>Planned observations</source>
            <translation>Observaciones planificadas</translation>
        </message>
        <message>
            <source>Positional uncertainty (m)</source>
            <translation>Incertidumbre posicional (m)</translation>
        </message>
        <message>
            <source>Pre-analyse network design</source>
            <translation>Preanalizar el diseño de la red</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Redundancy: %1 (%2 observations, %3 parameters).</source>
            <translation>Redundancia: %1 (%2 observaciones, %3 parámetros).</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Required positional uncertainty (m, 0 = do not judge)</source>
            <translation>Incertidumbre posicional exigida (m; 0 = no juzgar)</translation>
        </message>
        <message>
            <source>Semi-major (m)</source>
            <translation>Semieje mayor (m)</translation>
        </message>
        <message>
            <source>Semi-minor (m)</source>
            <translation>Semieje menor (m)</translation>
        </message>
        <message>
            <source>Significance for the minimal detectable bias</source>
            <translation>Significación para el sesgo mínimo detectable</translation>
        </message>
        <message>
            <source>Simulating the design…</source>
            <translation>Simulando el diseño…</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>The design does not meet the required %1 m.</source>
            <translation>El diseño no cumple los %1 m exigidos.</translation>
        </message>
        <message>
            <source>The minimal detectable bias is the smallest blunder the design could find in an observation, at the stated significance and power.</source>
            <translation>El sesgo mínimo detectable (MDB) es el menor error grosero que el diseño podría encontrar en una observación, con la significación y la potencia indicadas.</translation>
        </message>
        <message>
            <source>Type II error for the minimal detectable bias</source>
            <translation>Error tipo II para el sesgo mínimo detectable</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Advertencia</translation>
        </message>
        <message>
            <source>Worst station: %1 at %2 m.</source>
            <translation>Peor estación: %1, con %2 m.</translation>
        </message>
    </context>
    <context>
        <name>PreprocessAlgorithm</name>
        <message>
            <source>%1 pointing(s) reduced, %2 usable.</source>
            <translation>%1 visual(es) reducida(s), %2 utilizable(s).</translation>
        </message>
        <message>
            <source>(the built-in default)</source>
            <translation>(el valor interno por defecto)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Takes the readings produced by Import field book and runs the whole pre-processing chain: face reduction, instrument corrections, the first-velocity atmospheric correction, the EDM corrections, and the basic reductions to a horizontal distance and a height difference.&lt;/p&gt;&lt;p&gt;Every stage propagates covariance, so each result carries an uncertainty rather than a bare number. The distance and the zenith angle of one pointing are correlated through the common sighting, and that correlation is kept.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The diagnostics are the reason to run this rather than just averaging the two faces.&lt;/b&gt; A face pair reveals the horizontal collimation, the vertical index error and whether the two faces agreed on the distance. A pair whose distances disagree beyond the instrument's own precision is flagged as blocking and left out of the observations: the mean of two distances a metre apart is not a measurement of anything, and passing it on would let a known-bad number acquire a residual as though it were real.&lt;/p&gt;&lt;p&gt;Corrections the instrument already applied are not applied again. Applying a prism constant twice is a silent error of twice the constant, and nothing downstream can detect it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Readings&lt;/b&gt; &amp;mdash; the document Import field book produced. &lt;b&gt;Instrument profiles&lt;/b&gt; &amp;mdash; a profile library (JSON); empty uses a generic total station.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Temperature&lt;/b&gt; (&amp;deg;C), &lt;b&gt;pressure&lt;/b&gt; (hPa) and &lt;b&gt;relative humidity&lt;/b&gt; (%) &amp;mdash; the conditions the distances were measured in. Their uncertainties propagate: a &amp;plusmn; 2 &amp;deg;C error is about &amp;plusmn; 2 ppm, which is 2 mm over a kilometre and nothing at all over twenty metres. The propagation makes that visible instead of assumed.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Apply the atmospheric correction&lt;/b&gt; &amp;mdash; unset it to skip the stage entirely, which is a legitimate choice on short sights and one worth making explicitly.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Collimation tolerance&lt;/b&gt; (rad) and &lt;b&gt;face distance tolerance&lt;/b&gt; (m) &amp;mdash; beyond these a pair is reported. A distance tolerance of 0 derives it from the instrument's own EDM specification, which is the right threshold.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distance/zenith correlation&lt;/b&gt; &amp;mdash; between -1 and 1, or -2 for unknown. Unknown is recorded as an assumption rather than silently treated as zero, and the result is marked approximate.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; a JSON document. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML, with the per-pair diagnostics. &lt;b&gt;Reductions&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;POINTING_COUNT&lt;/code&gt;, &lt;code&gt;USABLE_COUNT&lt;/code&gt; and &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Toma las lecturas producidas por Importar libreta de campo y ejecuta toda la cadena de preprocesamiento: reducción de los pares de posiciones, correcciones instrumentales, corrección atmosférica de primera velocidad, correcciones del MED y las reducciones básicas a una distancia horizontal y un desnivel.&lt;/p&gt;&lt;p&gt;Cada etapa propaga covarianza, de modo que cada resultado lleva una incertidumbre en lugar de un número desnudo. La distancia y el ángulo cenital de una misma visual están correlacionados por la puntería común, y esa correlación se conserva.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Los diagnósticos son la razón para ejecutar esto en lugar de limitarse a promediar las dos posiciones.&lt;/b&gt; Un par de posiciones revela la colimación horizontal, el error de índice vertical y si las dos posiciones coincidieron en la distancia. Un par cuyas distancias discrepan más allá de la precisión del propio instrumento se marca como bloqueante y se deja fuera de las observaciones: la media de dos distancias separadas por un metro no es la medida de nada, y transmitirla permitiría que un número que se sabe defectuoso adquiriera un residuo como si fuera real.&lt;/p&gt;&lt;p&gt;Las correcciones que el instrumento ya aplicó no se aplican de nuevo. Aplicar una constante de prisma dos veces es un error silencioso del doble de la constante, y nada aguas abajo puede detectarlo.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Lecturas&lt;/b&gt; &amp;mdash; el documento producido por Importar libreta de campo. &lt;b&gt;Perfiles de instrumento&lt;/b&gt; &amp;mdash; una biblioteca de perfiles (JSON); vacío utiliza una estación total genérica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Temperatura&lt;/b&gt; (&amp;deg;C), &lt;b&gt;presión&lt;/b&gt; (hPa) y &lt;b&gt;humedad relativa&lt;/b&gt; (%) &amp;mdash; las condiciones en que se midieron las distancias. Sus incertidumbres se propagan: un error de &amp;plusmn; 2 &amp;deg;C es alrededor de &amp;plusmn; 2 ppm, que son 2 mm en un kilómetro y absolutamente nada en veinte metros. La propagación lo hace visible en lugar de supuesto.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Aplicar la corrección atmosférica&lt;/b&gt; &amp;mdash; desmárquela para omitir la etapa por completo, lo cual es una elección legítima en visuales cortas y que conviene hacer explícitamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerancia de la colimación&lt;/b&gt; (rad) y &lt;b&gt;tolerancia de la distancia entre posiciones&lt;/b&gt; (m) &amp;mdash; más allá de ellas se informa de un par. Una tolerancia de distancia de 0 la deriva de la propia especificación del MED del instrumento, que es el umbral correcto.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Correlación distancia/cenital&lt;/b&gt; &amp;mdash; entre -1 y 1, o -2 para desconocida. Desconocida se registra como una suposición en lugar de tratarse en silencio como cero, y el resultado se marca como aproximado.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; un documento JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML, con los diagnósticos por par. &lt;b&gt;Reducciones&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;POINTING_COUNT&lt;/code&gt;, &lt;code&gt;USABLE_COUNT&lt;/code&gt; y &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Apply the atmospheric correction</source>
            <translation>Aplicar la corrección atmosférica</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Collimation spread (%1)</source>
            <translation>Dispersión de la colimación (%1)</translation>
        </message>
        <message>
            <source>Collimation tolerance (rad)</source>
            <translation>Tolerancia de la colimación (rad)</translation>
        </message>
        <message>
            <source>Direction</source>
            <translation>Dirección</translation>
        </message>
        <message>
            <source>Distance/zenith correlation (-2 = unknown)</source>
            <translation>Correlación distancia/cenital (-2 = desconocida)</translation>
        </message>
        <message>
            <source>Face distance tolerance (m, 0 = from the instrument)</source>
            <translation>Tolerancia de la distancia entre posiciones (m; 0 = la del instrumento)</translation>
        </message>
        <message>
            <source>Face pairs</source>
            <translation>Pares de posiciones</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>Generalised pre-processing</source>
            <translation>Preprocesamiento generalizado</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_preprocess</source>
            <translation>Generado por GeoComp — geocomp:totalstation_preprocess</translation>
        </message>
        <message>
            <source>GeoComp reductions (*.json)</source>
            <translation>Reducciones GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height difference (%1)</source>
            <translation>Desnivel (%1)</translation>
        </message>
        <message>
            <source>Horizontal distance (%1)</source>
            <translation>Distancia horizontal (%1)</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfiles de instrumento</translation>
        </message>
        <message>
            <source>Instrumental diagnostics</source>
            <translation>Diagnósticos instrumentales</translation>
        </message>
        <message>
            <source>Mean collimation (%1)</source>
            <translation>Colimación media (%1)</translation>
        </message>
        <message>
            <source>Mean index error (%1)</source>
            <translation>Error de índice medio (%1)</translation>
        </message>
        <message>
            <source>Pre-processing report</source>
            <translation>Informe de preprocesamiento</translation>
        </message>
        <message>
            <source>Pressure (hPa)</source>
            <translation>Presión (hPa)</translation>
        </message>
        <message>
            <source>Pressure uncertainty (hPa)</source>
            <translation>Incertidumbre de la presión (hPa)</translation>
        </message>
        <message>
            <source>Readings</source>
            <translation>Lecturas</translation>
        </message>
        <message>
            <source>Reduce face pairs, apply the instrument, atmospheric and EDM corrections, and report what the pairs revealed.</source>
            <translation>Reduce los pares de posiciones, aplica las correcciones instrumentales, atmosféricas y del MED, e informa de lo que revelaron los pares.</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Reduced pointings</source>
            <translation>Visuales reducidas</translation>
        </message>
        <message>
            <source>Reducing station %1…</source>
            <translation>Reduciendo la estación %1…</translation>
        </message>
        <message>
            <source>Reductions</source>
            <translation>Reducciones</translation>
        </message>
        <message>
            <source>Relative humidity (%)</source>
            <translation>Humedad relativa (%)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Std dev (mm)</source>
            <translation>Desviación típica (mm)</translation>
        </message>
        <message>
            <source>Target</source>
            <translation>Objetivo</translation>
        </message>
        <message>
            <source>Temperature (°C)</source>
            <translation>Temperatura (°C)</translation>
        </message>
        <message>
            <source>Temperature uncertainty (°C)</source>
            <translation>Incertidumbre de la temperatura (°C)</translation>
        </message>
        <message>
            <source>The correlation between each distance and its zenith angle was not supplied, so they were treated as independent and the results are marked approximate.</source>
            <translation>No se proporcionó la correlación entre cada distancia y su ángulo cenital, por lo que se trataron como independientes y los resultados están marcados como aproximados.</translation>
        </message>
        <message>
            <source>The readings were taken with instrument(s) %1, which the profile library %2 does not contain. Supply the same library the field book was imported with: the reduction needs that instrument's constants, and using another instrument's would corrupt every number after it.</source>
            <translation>Las lecturas se tomaron con el/los instrumento(s) %1, que la biblioteca de perfiles %2 no contiene. Proporcione la misma biblioteca con la que se importó la libreta de campo: la reducción necesita las constantes de ese instrumento, y usar las de otro corrompería todos los números posteriores.</translation>
        </message>
        <message>
            <source>Usable</source>
            <translation>Utilizable</translation>
        </message>
        <message>
            <source>Zenith</source>
            <translation>Cenit</translation>
        </message>
        <message>
            <source>no</source>
            <translation>no</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sí</translation>
        </message>
    </context>
    <context>
        <name>PrintLayoutAlgorithm</name>
        <message>
            <source>&lt;p&gt;Makes a print layout in the project from one of three templates: a network map with its error ellipses, a displacement map, and a quality map drawn by one of the thematic maps. The layout has the title, the map, a legend, a scale bar and a north arrow, and lands in the project's layout manager to edit, print or export like any other.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The exaggeration is stated.&lt;/b&gt; Every exaggerated layer names its factor, so the legend states it, and the notes say that the scale bar measures the map and not the ellipses or vectors.&lt;/p&gt;&lt;p&gt;With no layers chosen, the layout draws the GeoComp result layers in the project that suit it, and any configured base map already there. A template of your own -- a shipped one adapted in the layout designer -- can be given instead; its items are found by their ids: title, map, legend, scalebar, north, notes, footer.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Crea un diseño de impresión en el proyecto a partir de una de tres plantillas: un mapa de la red con sus elipses de error, un mapa de los desplazamientos y un mapa de calidad dibujado por uno de los mapas temáticos. El diseño tiene el título, el mapa, una leyenda, una barra de escala y una flecha de norte, y queda en el administrador de diseños del proyecto para editar, imprimir o exportar como cualquier otro.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La exageración se declara.&lt;/b&gt; Cada capa exagerada indica su factor, así que la leyenda lo declara, y las notas dicen que la barra de escala mide el mapa y no las elipses ni los vectores.&lt;/p&gt;&lt;p&gt;Sin capas elegidas, el diseño dibuja las capas de resultado de GeoComp del proyecto que le corresponden, y cualquier mapa base configurado que ya esté allí. En su lugar puede darse una plantilla propia -- una de las incluidas, adaptada en el diseñador de impresión; sus elementos se encuentran por sus identificadores: title, map, legend, scalebar, north, notes, footer.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A print layout for a network map, a displacement map or a quality map, ready to adapt.</source>
            <translation>Un diseño de impresión para un mapa de la red, un mapa de los desplazamientos o un mapa de calidad, listo para adaptar.</translation>
        </message>
        <message>
            <source>Coloured by %1.</source>
            <translation>Coloreado por %1.</translation>
        </message>
        <message>
            <source>Create print layout</source>
            <translation>Crear diseño de impresión</translation>
        </message>
        <message>
            <source>Deliverable</source>
            <translation>Producto</translation>
        </message>
        <message>
            <source>Displacement map</source>
            <translation>Mapa de los desplazamientos</translation>
        </message>
        <message>
            <source>Ellipses and vectors are drawn exaggerated, %1, as each legend entry states. The scale bar measures the map, not them.</source>
            <translation>Las elipses y los vectores se dibujan exagerados, %1, como indica cada entrada de la leyenda. La barra de escala mide el mapa, no a ellos.</translation>
        </message>
        <message>
            <source>GeoComp %1 · %2</source>
            <translation>GeoComp %1 · %2</translation>
        </message>
        <message>
            <source>Its classes are fitted to this network, so the map is relative to it; the legend states every bound.</source>
            <translation>Sus clases se ajustan a esta red, así que el mapa es relativo a ella; la leyenda indica todos los límites.</translation>
        </message>
        <message>
            <source>Layers (empty: the project's GeoComp result layers)</source>
            <translation>Capas (vacío: las capas de resultado de GeoComp del proyecto)</translation>
        </message>
        <message>
            <source>Layout</source>
            <translation>Diseño</translation>
        </message>
        <message>
            <source>Layout '%1': %2 layer(s).</source>
            <translation>Diseño '%1': %2 capa(s).</translation>
        </message>
        <message>
            <source>Layout name (empty: from the title)</source>
            <translation>Nombre del diseño (vacío: a partir del título)</translation>
        </message>
        <message>
            <source>Legend</source>
            <translation>Leyenda</translation>
        </message>
        <message>
            <source>Network map</source>
            <translation>Mapa de la red</translation>
        </message>
        <message>
            <source>Network map with error ellipses</source>
            <translation>Mapa de la red con elipses de error</translation>
        </message>
        <message>
            <source>Network quality</source>
            <translation>Calidad de la red</translation>
        </message>
        <message>
            <source>None of these layers has the '%1' map; they are drawn in their own styles. Run the adjustment again to give its layers their thematic maps.</source>
            <translation>Ninguna de estas capas tiene el mapa '%1'; se dibujan con sus propios estilos. Ejecute el ajuste de nuevo para dar a sus capas los mapas temáticos.</translation>
        </message>
        <message>
            <source>Quality map</source>
            <translation>Mapa de calidad</translation>
        </message>
        <message>
            <source>Quality map drawn by</source>
            <translation>Mapa de calidad dibujado por</translation>
        </message>
        <message>
            <source>Template of your own (.qpt)</source>
            <translation>Plantilla propia (.qpt)</translation>
        </message>
        <message>
            <source>The template %1 could not be read: %2</source>
            <translation>No se pudo leer la plantilla %1: %2</translation>
        </message>
        <message>
            <source>The template %1 has no map item with the id 'map'.</source>
            <translation>La plantilla %1 no tiene ningún elemento de mapa con el identificador 'map'.</translation>
        </message>
        <message>
            <source>The template %1 is not a QGIS layout template.</source>
            <translation>La plantilla %1 no es una plantilla de diseño de QGIS.</translation>
        </message>
        <message>
            <source>There is nothing to draw: no layers were chosen and the project holds no GeoComp result layers for this map. Run an adjustment with its layers, or choose the layers.</source>
            <translation>No hay nada que dibujar: no se eligió ninguna capa y el proyecto no contiene capas de resultado de GeoComp para este mapa. Ejecute un ajuste con sus capas, o elija las capas.</translation>
        </message>
        <message>
            <source>Title</source>
            <translation>Título</translation>
        </message>
    </context>
    <context>
        <name>ProjectBaseMapAlgorithm</name>
        <message>
            <source>&lt;p&gt;Adds one of the configured base map services to the current project, at the bottom of the layer tree so it does not hide the results.&lt;/p&gt;&lt;p&gt;The services come from the catalogue file named in Global Settings, or from GeoComp's two openly licensed defaults when none is configured. Nothing is bundled and nothing is hard-coded: replace the catalogue and the list changes entirely.&lt;/p&gt;&lt;p&gt;A service already present in the project is reused rather than added again &amp;mdash; matched on its URL, since a layer's name is yours to change.&lt;/p&gt;&lt;p&gt;Services requiring authentication reference an entry in the QGIS authentication database. GeoComp never stores a credential itself, and refuses a service URL with one embedded in it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Service&lt;/b&gt; &amp;mdash; the id of a service in the catalogue. Leave empty to use the one configured as the default; if none is configured, nothing is added, rather than a layer you did not ask for.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Añade al proyecto actual uno de los servicios de mapa base configurados, al final del árbol de capas para que no oculte los resultados.&lt;/p&gt;&lt;p&gt;Los servicios provienen del archivo de catálogo indicado en la Configuración Global, o de los dos predeterminados de licencia abierta de GeoComp cuando no hay ninguno configurado. Nada viene incorporado ni fijado en el código: cambie el catálogo y la lista cambia por completo.&lt;/p&gt;&lt;p&gt;Un servicio ya presente en el proyecto se reutiliza en lugar de añadirse de nuevo &amp;mdash; identificado por su URL, ya que el nombre de una capa es suyo para cambiarlo.&lt;/p&gt;&lt;p&gt;Los servicios que requieren autenticación referencian una entrada de la base de autenticación de QGIS. GeoComp nunca almacena credenciales y rechaza una URL de servicio con una incrustada.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Servicio&lt;/b&gt; &amp;mdash; el identificador de un servicio del catálogo. Déjelo vacío para usar el configurado como predeterminado; si no hay ninguno configurado, no se añade nada, en lugar de una capa que usted no pidió.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Add a configured base map service to the project, for context.</source>
            <translation>Añade al proyecto un servicio de mapa base configurado, como contexto.</translation>
        </message>
        <message>
            <source>Add base map</source>
            <translation>Añadir mapa base</translation>
        </message>
        <message>
            <source>Attribution: </source>
            <translation>Atribución: </translation>
        </message>
        <message>
            <source>No base map is configured as the default, so none was added. Name a service, or set one in Global Settings; the available ids are: </source>
            <translation>No hay ningún mapa base configurado como predeterminado, por lo que no se añadió ninguno. Indique un servicio o defina uno en la Configuración Global; los identificadores disponibles son: </translation>
        </message>
        <message>
            <source>Reuse a base map already in the project</source>
            <translation>Reutilizar un mapa base ya presente en el proyecto</translation>
        </message>
        <message>
            <source>Service id (empty for the configured default)</source>
            <translation>Identificador del servicio (vacío para el predeterminado configurado)</translation>
        </message>
        <message>
            <source>The base map service could not be loaded: </source>
            <translation>No se pudo cargar el servicio de mapa base: </translation>
        </message>
    </context>
    <context>
        <name>ProjectExportAlgorithm</name>
        <message>
            <source>&lt;p&gt;Writes the five tables of an adjustment: stations, observations, adjusted values, residuals and statistics. Only tables with content are written &amp;mdash; an empty residuals table beside an unadjusted network would invite the reader to conclude the residuals were zero.&lt;/p&gt;&lt;p&gt;Every uncertainty is exported beside its value, and every value is written to full precision, so a figure read back into another tool is the figure GeoComp computed rather than a rounded version of it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a solution document written by an adjustment algorithm.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; optional. Supplying it adds the station and observation tables, which describe what was adjusted rather than what came out; without it only the adjusted values, residuals and statistics are written.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Format&lt;/b&gt; &amp;mdash; one CSV per table, or a single spreadsheet holding all of them.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Escribe las cinco tablas de un ajuste: estaciones, observaciones, valores ajustados, residuos y estadísticas. Solo se escriben las tablas con contenido &amp;mdash; una tabla de residuos vacía junto a una red sin ajustar llevaría al lector a concluir que los residuos eran nulos.&lt;/p&gt;&lt;p&gt;Cada incertidumbre se exporta junto a su valor, y cada valor se escribe con precisión completa, de modo que una cifra leída en otra herramienta es la que GeoComp calculó y no una versión redondeada de ella.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; un documento de solución escrito por un algoritmo de ajuste.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; opcional. Aportarla añade las tablas de estaciones y observaciones, que describen lo que se ajustó y no lo que salió; sin ella solo se escriben los valores ajustados, los residuos y las estadísticas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Formato&lt;/b&gt; &amp;mdash; un CSV por tabla, o una sola hoja de cálculo con todas.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Choose a destination folder for the CSV files.</source>
            <translation>Elija una carpeta de destino para los archivos CSV.</translation>
        </message>
        <message>
            <source>Choose a destination spreadsheet, or export as CSV instead.</source>
            <translation>Elija una hoja de cálculo de destino, o exporte como CSV.</translation>
        </message>
        <message>
            <source>Excel workbooks (*.xlsx)</source>
            <translation>Libros de Excel (*.xlsx)</translation>
        </message>
        <message>
            <source>Export solution tables</source>
            <translation>Exportar tablas de la solución</translation>
        </message>
        <message>
            <source>Folder for the CSV files</source>
            <translation>Carpeta para los archivos CSV</translation>
        </message>
        <message>
            <source>Format</source>
            <translation>Formato</translation>
        </message>
        <message>
            <source>Network document (optional)</source>
            <translation>Documento de red (opcional)</translation>
        </message>
        <message>
            <source>Nothing was written: the solution and network carry no rows for any table. An empty file would say the tables were empty, which is a different claim.</source>
            <translation>No se escribió nada: la solución y la red no tienen filas para ninguna tabla. Un archivo vacío afirmaría que las tablas estaban vacías, que es otra cosa.</translation>
        </message>
        <message>
            <source>One CSV per table</source>
            <translation>Un CSV por tabla</translation>
        </message>
        <message>
            <source>One spreadsheet (.xlsx)</source>
            <translation>Una sola hoja de cálculo (.xlsx)</translation>
        </message>
        <message>
            <source>Solution document</source>
            <translation>Documento de solución</translation>
        </message>
        <message>
            <source>Spreadsheet</source>
            <translation>Hoja de cálculo</translation>
        </message>
        <message>
            <source>Write stations, observations, adjusted values, residuals and statistics.</source>
            <translation>Escribe estaciones, observaciones, valores ajustados, residuos y estadísticas.</translation>
        </message>
    </context>
    <context>
        <name>ProjectReportAlgorithm</name>
        <message>
            <source>&lt;p&gt;Renders the complete adjustment report: identification, inputs, effective parameters and where each came from, adjusted coordinates, statistics, observation results, reliability, error ellipses, provenance and software versions.&lt;/p&gt;&lt;p&gt;Built from the solution alone, so it renders a solution read back out of a project store exactly as it rendered on the day it was computed. Nothing in it reads the clock.&lt;/p&gt;&lt;p&gt;Three things are never omitted whatever a template does with the rest: the uncertainty mode and the strategies behind it, the provenance with its input digests, and the uncheckable observations. Presenting an approximate figure as a rigorously propagated one misrepresents the survey, and monitoring decisions are made on these numbers.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a solution document written by an adjustment algorithm.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; optional. Adds the observation descriptions the solution does not carry, so the observation results table names stations rather than only observation ids.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Template&lt;/b&gt; &amp;mdash; optional HTML template (FR-931). Sections it does not place are listed in the log, because leaving one out is an editorial choice that should be visible.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Genera el informe completo de ajuste: identificación, entradas, parámetros efectivos y el origen de cada uno, coordenadas ajustadas, estadísticas, resultados de las observaciones, fiabilidad, elipses de error, procedencia y versiones de los programas.&lt;/p&gt;&lt;p&gt;Construido únicamente a partir de la solución, de modo que una solución leída de un repositorio de proyecto se presenta exactamente como el día en que se calculó. Nada en él consulta el reloj.&lt;/p&gt;&lt;p&gt;Tres cosas nunca se omiten, haga la plantilla lo que haga con el resto: el modo de incertidumbre y las estrategias que hay detrás, la procedencia con los resúmenes criptográficos de las entradas, y las observaciones no verificables. Presentar una cifra aproximada como rigurosamente propagada tergiversa el levantamiento, y las decisiones de monitoreo se toman sobre estos números.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; un documento de solución escrito por un algoritmo de ajuste.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; opcional. Añade las descripciones de observación que la solución no lleva, para que la tabla de resultados nombre estaciones y no solo identificadores de observación.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Plantilla&lt;/b&gt; &amp;mdash; plantilla HTML opcional (FR-931). Las secciones que no coloca se listan en el registro, porque dejar una fuera es una decisión editorial que debe quedar visible.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjustment report</source>
            <translation>Informe de ajuste</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Network document (optional)</source>
            <translation>Documento de red (opcional)</translation>
        </message>
        <message>
            <source>Render the full adjustment report from a solution document.</source>
            <translation>Genera el informe completo de ajuste a partir de un documento de solución.</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Report template (optional)</source>
            <translation>Plantilla de informe (opcional)</translation>
        </message>
        <message>
            <source>Report written.</source>
            <translation>Informe escrito.</translation>
        </message>
        <message>
            <source>Solution document</source>
            <translation>Documento de solución</translation>
        </message>
        <message>
            <source>The template places no: </source>
            <translation>La plantilla no incluye: </translation>
        </message>
    </context>
    <context>
        <name>ProjectStoreAlgorithm</name>
        <message>
            <source>&lt;p&gt;Writes a network, a solution, or both into a GeoComp project store: a GeoPackage holding networks, observations, sessions, settings, solutions and their provenance, with the covariances stored so that they reload bit-identically.&lt;/p&gt;&lt;p&gt;By default the solution is &lt;b&gt;added&lt;/b&gt; to whatever the store already holds, because the opposite mistake cannot be undone: replacing a project that was meant to be added to loses it. Replacing is available and says so.&lt;/p&gt;&lt;p&gt;A store already holding solutions computed from these observations will refuse to have them deleted (FR-135). To record that a new solution replaces an older one, name the older one under &lt;i&gt;Supersedes&lt;/i&gt;: it is kept and marked, because in monitoring the earlier answer still matters after it stops being the current one.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Project store&lt;/b&gt; &amp;mdash; the GeoPackage to write to. It is created if it does not exist; an older schema version is migrated after a backup, and a newer one is refused.&lt;/p&gt;&lt;p&gt;&lt;b&gt;PostgreSQL connection&lt;/b&gt; and &lt;b&gt;Schema&lt;/b&gt; &amp;mdash; instead of a GeoPackage, a project in a PostGIS database, through a connection saved in QGIS and its login. Give one or the other. If someone else saves to the same project while you work, your save is refused rather than overwriting theirs; open the project again and redo the change.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; and &lt;b&gt;Network&lt;/b&gt; &amp;mdash; documents written by earlier algorithms. At least one is required.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Escribe una red, una solución, o ambas en un repositorio de proyecto de GeoComp: un GeoPackage con redes, observaciones, sesiones, configuración, soluciones y su procedencia, con las covarianzas almacenadas de modo que se recarguen bit a bit idénticas.&lt;/p&gt;&lt;p&gt;De forma predeterminada la solución se &lt;b&gt;añade&lt;/b&gt; a lo que el repositorio ya contiene, porque el error contrario no tiene vuelta atrás: reemplazar un proyecto al que se pretendía añadir significa perderlo. Reemplazar está disponible y dice lo que hace.&lt;/p&gt;&lt;p&gt;Un repositorio que ya contenga soluciones calculadas a partir de esas observaciones se negará a que se eliminen (FR-135). Para registrar que una nueva solución reemplaza a una anterior, indique la anterior en &lt;i&gt;Reemplaza a&lt;/i&gt;: se conserva y se marca, porque en monitoreo la respuesta anterior sigue importando después de dejar de ser la actual.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Repositorio del proyecto&lt;/b&gt; &amp;mdash; el GeoPackage donde escribir. Se crea si no existe; una versión de esquema anterior se migra tras una copia de seguridad, y una más reciente se rechaza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Conexión PostgreSQL&lt;/b&gt; y &lt;b&gt;Esquema&lt;/b&gt; &amp;mdash; en lugar de un GeoPackage, un proyecto en una base de datos PostGIS, mediante una conexión guardada en QGIS y su inicio de sesión. Indique uno u otro. Si otra persona guarda en el mismo proyecto mientras usted trabaja, su guardado se rechaza en lugar de sobrescribir el de ella; abra el proyecto de nuevo y rehaga el cambio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; y &lt;b&gt;Red&lt;/b&gt; &amp;mdash; documentos escritos por algoritmos anteriores. Al menos uno es obligatorio.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>GeoPackage (*.gpkg)</source>
            <translation>GeoPackage (*.gpkg)</translation>
        </message>
        <message>
            <source>Give a solution document, a network document, or both.</source>
            <translation>Indique un documento de solución, un documento de red, o ambos.</translation>
        </message>
        <message>
            <source>Give either a GeoPackage or a PostgreSQL connection to save to.</source>
            <translation>Indique un GeoPackage o una conexión PostgreSQL donde guardar, uno de los dos.</translation>
        </message>
        <message>
            <source>Id of the solution this one replaces (optional)</source>
            <translation>Identificador de la solución que esta reemplaza (opcional)</translation>
        </message>
        <message>
            <source>Migrated %1 from schema %2 to %3; the backup is %4</source>
            <translation>%1 migrado del esquema %2 al %3; la copia de seguridad es %4</translation>
        </message>
        <message>
            <source>Network document (optional)</source>
            <translation>Documento de red (opcional)</translation>
        </message>
        <message>
            <source>PostgreSQL connection (instead of a GeoPackage)</source>
            <translation>Conexión PostgreSQL (en lugar de un GeoPackage)</translation>
        </message>
        <message>
            <source>Project id</source>
            <translation>Identificador del proyecto</translation>
        </message>
        <message>
            <source>Project store</source>
            <translation>Repositorio del proyecto</translation>
        </message>
        <message>
            <source>Replace everything in the store rather than adding</source>
            <translation>Reemplazar todo el contenido del repositorio en lugar de añadir</translation>
        </message>
        <message>
            <source>Save to project store</source>
            <translation>Guardar en el repositorio del proyecto</translation>
        </message>
        <message>
            <source>Schema</source>
            <translation>Esquema</translation>
        </message>
        <message>
            <source>Solution document (optional)</source>
            <translation>Documento de solución (opcional)</translation>
        </message>
        <message>
            <source>The superseded solution is kept, not deleted: what was believed and when is part of a monitoring record.</source>
            <translation>La solución reemplazada se conserva, no se elimina: lo que se creía y cuándo forma parte del registro de monitoreo.</translation>
        </message>
        <message>
            <source>Write a network and its solution into a GeoComp project: a GeoPackage or a PostGIS schema.</source>
            <translation>Escribe una red y su solución en un proyecto de GeoComp: un GeoPackage o un esquema PostGIS.</translation>
        </message>
    </context>
    <context>
        <name>RadiationAlgorithm</name>
        <message>
            <source>%1 point(s) radiated from %2 setup(s).</source>
            <translation>%1 punto(s) radiado(s) desde %2 estacionamiento(s).</translation>
        </message>
        <message>
            <source>3D radiation</source>
            <translation>Radiación 3D</translation>
        </message>
        <message>
            <source>3D radiation report</source>
            <translation>Informe de la radiación 3D</translation>
        </message>
        <message>
            <source>&lt;p&gt;Computes three-dimensional coordinates for every point a setup sighted, from the reduced direction, the zenith angle, the slope distance, the two heights and the setup's orientation. Batch radiation of many detail points from one setup is the routine production case and is what this is built for.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The full 3&amp;times;3 covariance is the result, not an extra.&lt;/b&gt; The three coordinates come from one pointing and are strongly correlated through it, and treating them as independent is wrong. The CSV carries the covariance so nothing downstream has to assume otherwise.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The orientation is derived from the pointings wherever it can be.&lt;/b&gt; Any target whose coordinates are known gives the setup's orientation directly, which is how a surveyor orients one: sight a known point and everything else follows. Where several are known the orientations they imply are averaged circularly and their spread is reported &amp;mdash; a large spread means one of the known points is not where it is supposed to be. Where none is known the orientation must be given explicitly.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Known stations&lt;/b&gt; &amp;mdash; a JSON object mapping station names to &lt;code&gt;[easting, northing, up]&lt;/code&gt; in metres. A setup must appear here for its points to be radiated.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Orientations&lt;/b&gt; &amp;mdash; an optional JSON object mapping a setup to its orientation in degrees, for setups that sighted no known point.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument height&lt;/b&gt; and &lt;b&gt;target height&lt;/b&gt; (m) &amp;mdash; used where the readings carry none of their own.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distance/zenith correlation&lt;/b&gt; &amp;mdash; between -1 and 1, or -2 for unknown, which is recorded as an assumption rather than silently treated as zero.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Points&lt;/b&gt; &amp;mdash; JSON, in the shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Points table&lt;/b&gt; &amp;mdash; CSV with the full covariance. Scalars: &lt;code&gt;POINT_COUNT&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula coordenadas tridimensionales para cada punto que un estacionamiento visó, a partir de la dirección reducida, el ángulo cenital, la distancia inclinada, las dos alturas y la orientación del estacionamiento. La radiación por lotes de muchos puntos de detalle desde un estacionamiento es el caso rutinario de producción y es para lo que esto está construido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La matriz de covarianzas 3&amp;times;3 completa es el resultado, no un extra.&lt;/b&gt; Las tres coordenadas provienen de una sola visual y están fuertemente correlacionadas por ella, y tratarlas como independientes es incorrecto. El CSV lleva la covarianza, de modo que nada aguas abajo tenga que suponer lo contrario.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La orientación se deriva de las propias visuales siempre que es posible.&lt;/b&gt; Cualquier objetivo cuyas coordenadas se conozcan da directamente la orientación del estacionamiento, que es como un topógrafo orienta uno: visa un punto conocido y todo lo demás se sigue. Donde se conocen varios, las orientaciones que implican se promedian circularmente y se comunica su dispersión &amp;mdash; una dispersión grande significa que uno de los puntos conocidos no está donde debería. Donde no se conoce ninguno, la orientación debe indicarse explícitamente.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Estaciones conocidas&lt;/b&gt; &amp;mdash; un objeto JSON que asocia nombres de estaciones a &lt;code&gt;[E, N, altitud]&lt;/code&gt; en metros. Un estacionamiento debe aparecer aquí para que sus puntos se radien.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Orientaciones&lt;/b&gt; &amp;mdash; un objeto JSON opcional que asocia un estacionamiento a su orientación en grados, para estacionamientos que no visaron ningún punto conocido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura del instrumento&lt;/b&gt; y &lt;b&gt;altura de la señal&lt;/b&gt; (m) &amp;mdash; usadas donde las lecturas no llevan las suyas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Correlación distancia/cenital&lt;/b&gt; &amp;mdash; entre -1 y 1, o -2 para desconocida, que se registra como una suposición en lugar de tratarse en silencio como cero.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Puntos&lt;/b&gt; &amp;mdash; JSON, con el formato que la Red clásica toma como coordenadas aproximadas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Tabla de puntos&lt;/b&gt; &amp;mdash; CSV con la covarianza completa. Escalares: &lt;code&gt;POINT_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Compute 3D coordinates of every point radiated from a known, oriented setup.</source>
            <translation>Calcula las coordenadas 3D de cada punto radiado desde un estacionamiento conocido y orientado.</translation>
        </message>
        <message>
            <source>Correlation E,N</source>
            <translation>Correlación E,N</translation>
        </message>
        <message>
            <source>Distance/zenith correlation (-2 = unknown)</source>
            <translation>Correlación distancia/cenital (-2 = desconocida)</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_radiation</source>
            <translation>Generado por GeoComp — geocomp:totalstation_radiation</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Instrument height (m)</source>
            <translation>Altura del instrumento (m)</translation>
        </message>
        <message>
            <source>Known stations</source>
            <translation>Estaciones conocidas</translation>
        </message>
        <message>
            <source>No point could be radiated. A setup needs known coordinates, an orientation, and at least one pointing with a distance to a station that is not itself known.</source>
            <translation>No se pudo radiar ningún punto. Un estacionamiento necesita coordenadas conocidas, una orientación y al menos una visual con distancia a una estación que no sea ella misma conocida.</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Orientation</source>
            <translation>Orientación</translation>
        </message>
        <message>
            <source>Orientations</source>
            <translation>Orientaciones</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Punto</translation>
        </message>
        <message>
            <source>Points</source>
            <translation>Puntos</translation>
        </message>
        <message>
            <source>Points table</source>
            <translation>Tabla de puntos</translation>
        </message>
        <message>
            <source>Radiated points</source>
            <translation>Puntos radiados</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Setup orientations</source>
            <translation>Orientaciones de los estacionamientos</translation>
        </message>
        <message>
            <source>Source</source>
            <translation>Origen</translation>
        </message>
        <message>
            <source>Spread (%1)</source>
            <translation>Dispersión (%1)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Station '%1' has no known coordinates; its points were skipped.</source>
            <translation>La estación '%1' no tiene coordenadas conocidas; sus puntos se omitieron.</translation>
        </message>
        <message>
            <source>Station '%1' is not three numbers.</source>
            <translation>La estación '%1' no está compuesta por tres números.</translation>
        </message>
        <message>
            <source>Station '%1' sighted no known point and has no orientation given; its points were skipped.</source>
            <translation>La estación '%1' no visó ningún punto conocido y no tiene orientación indicada; sus puntos se omitieron.</translation>
        </message>
        <message>
            <source>Std dev E (mm)</source>
            <translation>Desviación típica E (mm)</translation>
        </message>
        <message>
            <source>Std dev N (mm)</source>
            <translation>Desviación típica N (mm)</translation>
        </message>
        <message>
            <source>Std dev U (mm)</source>
            <translation>Desviación típica Alt (mm)</translation>
        </message>
        <message>
            <source>Target height (m)</source>
            <translation>Altura de la señal (m)</translation>
        </message>
        <message>
            <source>The known points sighted from '%1' imply orientations spread over %2 %4, against %3 %4 expected from the pointing precision. One of them is probably not where it is recorded, and every point radiated from this setup carries that error.</source>
            <translation>Los puntos conocidos visados desde '%1' implican orientaciones dispersas en %2 %4, frente a %3 %4 esperados por la precisión de puntería. Uno de ellos probablemente no está donde se registró, y todo punto radiado desde este estacionamiento arrastra ese error.</translation>
        </message>
        <message>
            <source>The known stations document is empty.</source>
            <translation>El documento de estaciones conocidas está vacío.</translation>
        </message>
        <message>
            <source>The orientations document must map each station to a number of degrees.</source>
            <translation>El documento de orientaciones debe asociar cada estación a un número de grados.</translation>
        </message>
        <message>
            <source>The three coordinates of a radiated point come from one pointing and are correlated through it. The CSV carries the full covariance so nothing downstream has to assume they are independent.</source>
            <translation>Las tres coordenadas de un punto radiado provienen de una sola visual y están correlacionadas por ella. El CSV lleva la matriz de covarianzas completa, de modo que nada aguas abajo tenga que suponerlas independientes.</translation>
        </message>
        <message>
            <source>Up (m)</source>
            <translation>Altitud (m)</translation>
        </message>
        <message>
            <source>Where a setup sighted several known points they should all imply the same orientation. A large spread means one of them is not where it is supposed to be.</source>
            <translation>Cuando un estacionamiento visó varios puntos conocidos, todos deben implicar la misma orientación. Una dispersión grande significa que uno de ellos no está donde debería.</translation>
        </message>
        <message>
            <source>from known points</source>
            <translation>de puntos conocidos</translation>
        </message>
        <message>
            <source>given</source>
            <translation>indicada</translation>
        </message>
    </context>
    <context>
        <name>RelativeKinematicAlgorithm</name>
        <message>
            <source>Post-processed kinematic positioning against a base station.</source>
            <translation>Posicionamiento cinemático pospro­cesado respecto a una estación base.</translation>
        </message>
        <message>
            <source>Relative — Kinematic</source>
            <translation>Relativo — Cinemático</translation>
        </message>
    </context>
    <context>
        <name>RelativeStaticAlgorithm</name>
        <message>
            <source>A static baseline between two simultaneously observing stations.</source>
            <translation>Una línea base estática entre dos estaciones observando simultáneamente.</translation>
        </message>
        <message>
            <source>Relative — Static</source>
            <translation>Relativo — Estático</translation>
        </message>
    </context>
    <context>
        <name>ResectionAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes the coordinates of the occupied station from the directions it observed to known points, by least squares over any number of them with the setup's orientation estimated as a third unknown. Three points give a unique solution; more give residuals and a covariance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The danger circle is detected and refused, not solved.&lt;/b&gt; When the occupied station lies on the circle through three known points, every point on that circle sees the three in the same directions, so they do not determine a position there. A number returned from that configuration looks exactly like a coordinate and is not one, so GeoComp refuses and names the three points involved. Add a fourth point off the circle, or a distance.&lt;/p&gt;&lt;p&gt;Three known points in a straight line define no circle at all, which is a different impossibility and gets its own message.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Occupied station&lt;/b&gt; &amp;mdash; which setup in it to resect.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Known points&lt;/b&gt; &amp;mdash; a JSON object mapping each known station to &lt;code&gt;[easting, northing]&lt;/code&gt; in metres. Only the points the setup actually sighted are used.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Approximate easting&lt;/b&gt; and &lt;b&gt;northing&lt;/b&gt; (m) &amp;mdash; a starting point for the iteration, and what the danger-circle check is evaluated at before any computation begins. Leave both at 0 to start from the centroid of the known points, which converges from anywhere inside the figure.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Position&lt;/b&gt; &amp;mdash; a JSON document in the same shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SIGMA_EASTING&lt;/code&gt;, &lt;code&gt;SIGMA_NORTHING&lt;/code&gt; in metres and &lt;code&gt;ORIENTATION&lt;/code&gt; in degrees.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula las coordenadas de la estación ocupada a partir de las direcciones que observó a puntos conocidos, por mínimos cuadrados sobre cualquier número de ellos, con la orientación del estacionamiento estimada como una tercera incógnita. Tres puntos dan una solución única; más dan residuos y una covarianza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El círculo peligroso se detecta y se rechaza, no se resuelve.&lt;/b&gt; Cuando la estación ocupada se halla sobre el círculo que pasa por tres puntos conocidos, todo punto de ese círculo ve los tres en las mismas direcciones, de modo que no determinan allí una posición. Un número devuelto desde esa configuración parece exactamente una coordenada y no lo es, de modo que GeoComp lo rechaza y nombra los tres puntos implicados. Añada un cuarto punto fuera del círculo, o una distancia.&lt;/p&gt;&lt;p&gt;Tres puntos conocidos en línea recta no definen círculo alguno, lo cual es una imposibilidad distinta y recibe su propio mensaje.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Estación ocupada&lt;/b&gt; &amp;mdash; qué estacionamiento de él determinar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Puntos conocidos&lt;/b&gt; &amp;mdash; un objeto JSON que asocia cada estación conocida a &lt;code&gt;[E, N]&lt;/code&gt; en metros. Solo se utilizan los puntos que el estacionamiento visó efectivamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;E aproximado&lt;/b&gt; y &lt;b&gt;N aproximado&lt;/b&gt; (m) &amp;mdash; un punto de partida para la iteración, y donde se evalúa la comprobación del círculo peligroso antes de que comience cálculo alguno. Deje ambos en 0 para partir del centroide de los puntos conocidos, que converge desde cualquier lugar dentro de la figura.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Posición&lt;/b&gt; &amp;mdash; un documento JSON con el mismo formato que la Red clásica toma como coordenadas aproximadas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SIGMA_EASTING&lt;/code&gt;, &lt;code&gt;SIGMA_NORTHING&lt;/code&gt; en metros y &lt;code&gt;ORIENTATION&lt;/code&gt; en grados.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Approximate easting (m)</source>
            <translation>E aproximado (m)</translation>
        </message>
        <message>
            <source>Approximate northing (m)</source>
            <translation>N aproximado (m)</translation>
        </message>
        <message>
            <source>Correlation</source>
            <translation>Correlación</translation>
        </message>
        <message>
            <source>E %1 ± %2 mm, N %3 ± %4 mm.</source>
            <translation>E %1 ± %2 mm, N %3 ± %4 mm.</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>Fix the occupied station from directions to three or more known points.</source>
            <translation>Determina la estación ocupada a partir de direcciones a tres o más puntos conocidos.</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_resection</source>
            <translation>Generado por GeoComp — geocomp:totalstation_resection</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Known point</source>
            <translation>Punto conocido</translation>
        </message>
        <message>
            <source>Known point '%1' is not a pair of numbers.</source>
            <translation>El punto conocido '%1' no es un par de números.</translation>
        </message>
        <message>
            <source>Known points</source>
            <translation>Puntos conocidos</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Occupied station</source>
            <translation>Estación ocupada</translation>
        </message>
        <message>
            <source>Position</source>
            <translation>Posición</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Resecting station '%1' from %2 known point(s).</source>
            <translation>Determinando la estación '%1' a partir de %2 punto(s) conocido(s).</translation>
        </message>
        <message>
            <source>Resection</source>
            <translation>Intersección inversa</translation>
        </message>
        <message>
            <source>Resection report</source>
            <translation>Informe de la intersección inversa</translation>
        </message>
        <message>
            <source>Residual (%1)</source>
            <translation>Residuo (%1)</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Residuos</translation>
        </message>
        <message>
            <source>Setup orientation</source>
            <translation>Orientación del estacionamiento</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Station '%1' sighted only %2 of the known points. A resection needs at least three: two directions cannot fix a position and an orientation.</source>
            <translation>La estación '%1' visó solo %2 de los puntos conocidos. Una intersección inversa necesita al menos tres: dos direcciones no determinan una posición y una orientación.</translation>
        </message>
        <message>
            <source>Std dev E (mm)</source>
            <translation>Desviación típica E (mm)</translation>
        </message>
        <message>
            <source>Std dev N (mm)</source>
            <translation>Desviación típica N (mm)</translation>
        </message>
        <message>
            <source>The known points document is empty.</source>
            <translation>El documento de puntos conocidos está vacío.</translation>
        </message>
        <message>
            <source>The reduced observations contain no setup at station '%1'.</source>
            <translation>Las observaciones reducidas no contienen estacionamiento en la estación '%1'.</translation>
        </message>
        <message>
            <source>Three known points give a unique solution, so the residuals are zero by construction and say nothing about the quality of the observations. A fourth point is what makes them informative.</source>
            <translation>Tres puntos conocidos dan una solución única, de modo que los residuos son nulos por construcción y no dicen nada sobre la calidad de las observaciones. Un cuarto punto es lo que los hace informativos.</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
    </context>
    <context>
        <name>ScanSessionsAlgorithm</name>
        <message>
            <source>  %1: %2 to %3</source>
            <translation>  %1: %2 hasta %3</translation>
        </message>
        <message>
            <source>%1 session(s), %2 simultaneous group(s), %3 unreadable file(s)</source>
            <translation>%1 sesión(es), %2 grupo(s) simultáneo(s), %3 archivo(s) ilegible(s)</translation>
        </message>
        <message>
            <source>%1: %2</source>
            <translation>%1: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads the header of every RINEX observation file in a folder and reports the sessions it found: station, receiver, antenna, start and end, sampling interval, and the navigation files paired with each.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The header decides, not the file name.&lt;/b&gt; A file named for one station whose header names another is reported as a mismatch rather than silently resolved either way.&lt;/p&gt;&lt;p&gt;Groups sessions by simultaneity, since only sessions that actually overlap in time can form a baseline, and lists every file it could not read rather than stopping at the first.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee la cabecera de cada archivo de observación RINEX de una carpeta e informa de las sesiones que encontró: estación, receptor, antena, inicio y fin, intervalo de muestreo, y los archivos de navegación emparejados con cada una.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La cabecera decide, no el nombre del archivo.&lt;/b&gt; Un archivo nombrado por una estación cuya cabecera nombra otra se informa como discrepancia, en lugar de resolverse en silencio a favor de una de las dos.&lt;/p&gt;&lt;p&gt;Agrupa las sesiones por simultaneidad, ya que solo las sesiones que realmente se solapan en el tiempo pueden formar una línea base, y enumera todos los archivos que no pudo leer en lugar de detenerse en el primero.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Could not read %1: %2</source>
            <translation>No se pudo leer %1: %2</translation>
        </message>
        <message>
            <source>Discover GNSS sessions in a folder, from the RINEX headers.</source>
            <translation>Descubre sesiones GNSS en una carpeta, a partir de las cabeceras RINEX.</translation>
        </message>
        <message>
            <source>Folder of RINEX observations</source>
            <translation>Carpeta con observaciones RINEX</translation>
        </message>
        <message>
            <source>JSON files (*.json)</source>
            <translation>Archivos JSON (*.json)</translation>
        </message>
        <message>
            <source>Scan sessions</source>
            <translation>Explorar sesiones</translation>
        </message>
        <message>
            <source>Sessions</source>
            <translation>Sesiones</translation>
        </message>
    </context>
    <context>
        <name>SystemReportAlgorithm</name>
        <message>
            <source>&lt;p&gt;Produces a report describing the GeoComp installation: plugin and QGIS versions, the Python runtime, availability and versions of the external processing engines, and every GeoComp setting with its effective value and the scope that value came from.&lt;/p&gt;&lt;p&gt;Attach this report to a bug report or a support request. Because settings resolve through run, project and global scopes in that order, the origin column is usually what explains a result that differs between two machines.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; destination HTML file. Leave empty to write to a temporary file.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Genera un informe que describe la instalación de GeoComp: versiones del complemento y de QGIS, el entorno Python, la disponibilidad y las versiones de los motores de procesamiento externos, y cada configuración de GeoComp con su valor efectivo y el ámbito del que proviene ese valor.&lt;/p&gt;&lt;p&gt;Adjunte este informe a un reporte de error o a una solicitud de soporte. Como las configuraciones se resuelven en los ámbitos ejecución, proyecto y global, en ese orden, la columna de origen suele ser lo que explica un resultado que difiere entre dos equipos.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; archivo HTML de destino. Déjelo vacío para escribir en un archivo temporal.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Architecture</source>
            <translation>Arquitectura</translation>
        </message>
        <message>
            <source>Collecting environment information…</source>
            <translation>Recopilando información del entorno…</translation>
        </message>
        <message>
            <source>Detail</source>
            <translation>Detalle</translation>
        </message>
        <message>
            <source>Effective value</source>
            <translation>Valor efectivo</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Environment</source>
            <translation>Entorno</translation>
        </message>
        <message>
            <source>GeoComp system report</source>
            <translation>Informe del sistema GeoComp</translation>
        </message>
        <message>
            <source>GeoComp version</source>
            <translation>Versión de GeoComp</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Installed</source>
            <translation>Instalado</translation>
        </message>
        <message>
            <source>Installed, a version GeoComp has not been tested with</source>
            <translation>Instalado, en una versión con la que GeoComp no se ha probado</translation>
        </message>
        <message>
            <source>Not installed</source>
            <translation>No instalado</translation>
        </message>
        <message>
            <source>Origin</source>
            <translation>Origen</translation>
        </message>
        <message>
            <source>Platform</source>
            <translation>Plataforma</translation>
        </message>
        <message>
            <source>Processing engines</source>
            <translation>Motores de procesamiento</translation>
        </message>
        <message>
            <source>Python version</source>
            <translation>Versión de Python</translation>
        </message>
        <message>
            <source>QGIS release</source>
            <translation>Versión de lanzamiento de QGIS</translation>
        </message>
        <message>
            <source>QGIS version</source>
            <translation>Versión de QGIS</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Report GeoComp versions, engine availability and effective settings.</source>
            <translation>Informa las versiones de GeoComp, la disponibilidad de los motores y las configuraciones efectivas.</translation>
        </message>
        <message>
            <source>Report written.</source>
            <translation>Informe escrito.</translation>
        </message>
        <message>
            <source>Resolving settings…</source>
            <translation>Resolviendo configuraciones…</translation>
        </message>
        <message>
            <source>Setting</source>
            <translation>Configuración</translation>
        </message>
        <message>
            <source>Settings</source>
            <translation>Configuraciones</translation>
        </message>
        <message>
            <source>Settings resolve in the order: run parameter, project, global, built-in default. The origin column shows which scope supplied the effective value.</source>
            <translation>Las configuraciones se resuelven en el orden: parámetro de ejecución, proyecto, global, valor predeterminado interno. La columna de origen muestra qué ámbito proporcionó el valor efectivo.</translation>
        </message>
        <message>
            <source>Status</source>
            <translation>Estado</translation>
        </message>
    </context>
    <context>
        <name>TraverseAlgorithm</name>
        <message>
            <source>%1 leg(s) over %2 station(s).</source>
            <translation>%1 lado(s) sobre %2 estación(es).</translation>
        </message>
        <message>
            <source>&lt;p&gt;Walks a traverse through the reduced pointings, computes its angular and linear misclosure, compares them against the configured tolerances, and distributes the misclosure by the compass (Bowditch) or transit rule.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The classical rules are not least squares.&lt;/b&gt; They produce no residuals, no redundancy numbers and no rigorous covariance, so their coordinates are labelled approximate and the uncertainties reported are the misclosure spread over the traverse rather than a propagated variance. For the rigorous path use Classical network. Running the same data both ways is the point: the student sees what the classical rule approximates.&lt;/p&gt;&lt;p&gt;&lt;b&gt;An open traverse has no misclosure at all&lt;/b&gt;, which is different from a misclosure of zero. Nothing about it can be checked and a blunder anywhere in it is invisible, so GeoComp reports that rather than a perfect closure.&lt;/p&gt;&lt;p&gt;Whichever rule is used, the result is also a good set of approximate coordinates for a rigorous network adjustment, which is the other reason to run it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Route&lt;/b&gt; &amp;mdash; the stations in order, comma-separated, for example &lt;code&gt;1,2,3,4,1&lt;/code&gt;. &lt;b&gt;Initial backsight&lt;/b&gt; &amp;mdash; the station the first setup sighted before turning the angle.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Start easting&lt;/b&gt;, &lt;b&gt;start northing&lt;/b&gt; (m) and &lt;b&gt;start azimuth&lt;/b&gt; (degrees) &amp;mdash; the known point and the orientation of the initial backsight.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Kind&lt;/b&gt; &amp;mdash; closed (returns to its start), connected (arrives at another known point) or open. &lt;b&gt;Closing easting&lt;/b&gt;, &lt;b&gt;closing northing&lt;/b&gt; and &lt;b&gt;closing azimuth&lt;/b&gt; &amp;mdash; for a connected traverse.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distribution&lt;/b&gt; &amp;mdash; compass, transit, or none to report the misclosure without absorbing it, which is what a check measurement is for.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Angular tolerance per station&lt;/b&gt; (degrees) and &lt;b&gt;required relative precision&lt;/b&gt; (the N in 1:N).&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Coordinates&lt;/b&gt; &amp;mdash; a JSON document ready to use as the approximate coordinates for Classical network. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Stations&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;ANGULAR_MISCLOSURE&lt;/code&gt; in degrees, &lt;code&gt;LINEAR_MISCLOSURE&lt;/code&gt; in metres, &lt;code&gt;RELATIVE_PRECISION&lt;/code&gt; and &lt;code&gt;WITHIN_TOLERANCE&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Recorre una poligonal a través de las visuales reducidas, calcula sus errores angular y lineal de cierre, los compara con las tolerancias configuradas y distribuye el error mediante la regla del compás (Bowditch) o del tránsito.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las reglas clásicas no son mínimos cuadrados.&lt;/b&gt; No producen residuos, ni números de redundancia, ni covarianza rigurosa, de modo que sus coordenadas se etiquetan como aproximadas y las incertidumbres comunicadas son el error de cierre repartido por la poligonal, y no una varianza propagada. Para la vía rigurosa use Red clásica. Ejecutar los mismos datos de ambos modos es el objetivo: el estudiante ve qué aproxima la regla clásica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Una poligonal abierta no tiene error de cierre alguno&lt;/b&gt;, lo cual es distinto de un error de cierre nulo. Nada en ella puede comprobarse y un error grosero en cualquier punto es invisible, de modo que GeoComp lo comunica en lugar de un cierre perfecto.&lt;/p&gt;&lt;p&gt;Sea cual sea la regla utilizada, el resultado es también un buen conjunto de coordenadas aproximadas para un ajuste riguroso de red, que es la otra razón para ejecutarla.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Recorrido&lt;/b&gt; &amp;mdash; las estaciones en orden, separadas por comas, por ejemplo &lt;code&gt;1,2,3,4,1&lt;/code&gt;. &lt;b&gt;Espalda inicial&lt;/b&gt; &amp;mdash; la estación que el primer estacionamiento visó antes de girar el ángulo.&lt;/p&gt;&lt;p&gt;&lt;b&gt;E inicial&lt;/b&gt;, &lt;b&gt;N inicial&lt;/b&gt; (m) y &lt;b&gt;acimut inicial&lt;/b&gt; (grados) &amp;mdash; el punto conocido y la orientación de la espalda inicial.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tipo&lt;/b&gt; &amp;mdash; cerrada (vuelve a su inicio), encuadrada (llega a otro punto conocido) o abierta. &lt;b&gt;E de llegada&lt;/b&gt;, &lt;b&gt;N de llegada&lt;/b&gt; y &lt;b&gt;acimut de llegada&lt;/b&gt; &amp;mdash; para una poligonal encuadrada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distribución&lt;/b&gt; &amp;mdash; compás, tránsito, o ninguna para informar del error sin absorberlo, que es para lo que sirve una medida de comprobación.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerancia angular por estación&lt;/b&gt; (grados) y &lt;b&gt;precisión relativa exigida&lt;/b&gt; (la N en 1:N).&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Coordenadas&lt;/b&gt; &amp;mdash; un documento JSON listo para usarse como coordenadas aproximadas de la Red clásica. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;ANGULAR_MISCLOSURE&lt;/code&gt; en grados, &lt;code&gt;LINEAR_MISCLOSURE&lt;/code&gt; en metros, &lt;code&gt;RELATIVE_PRECISION&lt;/code&gt; y &lt;code&gt;WITHIN_TOLERANCE&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A classical distribution is not least squares: it produces no residuals and no rigorous covariance, so these coordinates are approximate. For the rigorous path, use Classical network on the same data.</source>
            <translation>Una distribución clásica no es mínimos cuadrados: no produce residuos ni covarianza rigurosa, por lo que estas coordenadas son aproximadas. Para la vía rigurosa, use Red clásica sobre los mismos datos.</translation>
        </message>
        <message>
            <source>A connected traverse arrives at a known point, so the closing easting and northing are required. Without them there is no closure and nothing about the traverse can be checked.</source>
            <translation>Una poligonal encuadrada llega a un punto conocido, por lo que la coordenada E y la coordenada N de cierre son obligatorias. Sin ellas no hay cierre y nada de la poligonal puede comprobarse.</translation>
        </message>
        <message>
            <source>A traverse needs at least two stations in its route.</source>
            <translation>Una poligonal necesita al menos dos estaciones en su recorrido.</translation>
        </message>
        <message>
            <source>Angular misclosure %1 %2.</source>
            <translation>Error angular de cierre %1 %2.</translation>
        </message>
        <message>
            <source>Angular misclosure (%1)</source>
            <translation>Error angular de cierre (%1)</translation>
        </message>
        <message>
            <source>Angular tolerance per station (°)</source>
            <translation>Tolerancia angular por estación (°)</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Closed</source>
            <translation>Cerrada</translation>
        </message>
        <message>
            <source>Closes to 1:%1.</source>
            <translation>Cierra en 1:%1.</translation>
        </message>
        <message>
            <source>Closing azimuth (°)</source>
            <translation>Acimut de llegada (°)</translation>
        </message>
        <message>
            <source>Closing easting (m)</source>
            <translation>E de llegada (m)</translation>
        </message>
        <message>
            <source>Closing northing (m)</source>
            <translation>N de llegada (m)</translation>
        </message>
        <message>
            <source>Compass (Bowditch)</source>
            <translation>Compás (Bowditch)</translation>
        </message>
        <message>
            <source>Compute a traverse's misclosures and distribute them by a classical rule.</source>
            <translation>Calcula los errores de cierre de una poligonal y los distribuye mediante una regla clásica.</translation>
        </message>
        <message>
            <source>Connected</source>
            <translation>Encuadrada</translation>
        </message>
        <message>
            <source>Coordinates</source>
            <translation>Coordenadas</translation>
        </message>
        <message>
            <source>Distribution</source>
            <translation>Distribución</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_traverse</source>
            <translation>Generado por GeoComp — geocomp:totalstation_traverse</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Initial backsight station</source>
            <translation>Estación de espalda inicial</translation>
        </message>
        <message>
            <source>Kind</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Linear misclosure (m)</source>
            <translation>Error lineal de cierre (m)</translation>
        </message>
        <message>
            <source>No closing azimuth was given and none can be inferred, so the angular misclosure is not computed and the angles are not checked. Give the closing azimuth to check them.</source>
            <translation>No se indicó ningún acimut de cierre ni puede inferirse, por lo que el error de cierre angular no se calcula y los ángulos no se comprueban. Indique el acimut de cierre para comprobarlos.</translation>
        </message>
        <message>
            <source>No closing azimuth was given. This loop backsights '%1' and returns from it, so it closes on the line the start azimuth refers to, and that is what the angular misclosure is measured against.</source>
            <translation>No se indicó ningún acimut de cierre. Esta poligonal cerrada visa la espalda '%1' y regresa de ella, por lo que cierra sobre la misma línea a la que se refiere el acimut inicial, y es contra ella que se mide el error de cierre angular.</translation>
        </message>
        <message>
            <source>None — report the misclosure only</source>
            <translation>Ninguna — solo informar del error de cierre</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Open</source>
            <translation>Abierta</translation>
        </message>
        <message>
            <source>Perimeter %1 %2.</source>
            <translation>Perímetro %1 %2.</translation>
        </message>
        <message>
            <source>Perimeter (%1)</source>
            <translation>Perímetro (%1)</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propiedad</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Relative precision</source>
            <translation>Precisión relativa</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Required relative precision (1:N)</source>
            <translation>Precisión relativa exigida (1:N)</translation>
        </message>
        <message>
            <source>Route (comma-separated stations)</source>
            <translation>Recorrido (estaciones separadas por comas)</translation>
        </message>
        <message>
            <source>Start azimuth (°)</source>
            <translation>Acimut inicial (°)</translation>
        </message>
        <message>
            <source>Start easting (m)</source>
            <translation>E inicial (m)</translation>
        </message>
        <message>
            <source>Start northing (m)</source>
            <translation>N inicial (m)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estación</translation>
        </message>
        <message>
            <source>Station '%1' has no usable pointing to '%2'.</source>
            <translation>La estación '%1' no tiene visual utilizable a '%2'.</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estaciones</translation>
        </message>
        <message>
            <source>The initial backsight station is required: it is what the start azimuth refers to.</source>
            <translation>La estación de espalda inicial es obligatoria: es a ella a la que se refiere el acimut inicial.</translation>
        </message>
        <message>
            <source>The pointing from '%1' to '%2' carries no distance.</source>
            <translation>La visual de '%1' a '%2' no lleva distancia.</translation>
        </message>
        <message>
            <source>The reduced observations contain no setup at station '%1'.</source>
            <translation>Las observaciones reducidas no contienen estacionamiento en la estación '%1'.</translation>
        </message>
        <message>
            <source>Transit</source>
            <translation>Tránsito</translation>
        </message>
        <message>
            <source>Traverse</source>
            <translation>Poligonal</translation>
        </message>
        <message>
            <source>Traverse report</source>
            <translation>Informe de la poligonal</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
    </context>
    <context>
        <name>TrigonometricLevellingAlgorithm</name>
        <message>
            <source>%1 height difference(s) computed.</source>
            <translation>%1 desnivel(es) calculado(s).</translation>
        </message>
        <message>
            <source>'Refraction surviving' is the fraction of the refraction uncertainty the method did not remove: 0 means the two sights were equal and it cancelled entirely, 1 means it did not cancel at all. It depends only on the two sight lengths, which is what makes it something the surveyor controls.</source>
            <translation>'Refracción remanente' es la fracción de la incertidumbre de la refracción que el método no eliminó: 0 significa que las dos visuales eran iguales y se canceló por completo, 1 significa que no se canceló en absoluto. Depende únicamente de las dos longitudes de visual, que es lo que la hace algo que el topógrafo controla.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Computes height differences from the reduced zenith angles and slope distances, with the curvature-and-refraction correction applied and its uncertainty propagated. On a 100 m sight the correction is 0.7 mm; at 1 km it is 68 mm; at 5 km it is 1.7 m.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radial&lt;/b&gt; computes a height difference from the occupied station to each target it sighted. The instrument height, the target height and the refraction all contribute in full.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Leap-frog&lt;/b&gt; takes each setup that sighted exactly two targets as a free station between them, and produces one height difference from the first to the second. Two things then cancel. The &lt;b&gt;instrument height cancels exactly&lt;/b&gt; and never has to be measured, which removes what is routinely the dominant error in a short trigonometric height. And the &lt;b&gt;refraction largely cancels&lt;/b&gt;, because both sights pass through the same air at the same moment and share one coefficient &amp;mdash; a shared dependence carried through a single Jacobian, so the cancellation shows in the uncertainty and not only in the value. With balanced sights the refraction uncertainty leaves the result entirely.&lt;/p&gt;&lt;p&gt;How much cancels depends on how equal the two sights are, which the surveyor controls by where they stand, so an imbalanced pair is reported along with the fraction of the refraction uncertainty that survived.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Mode&lt;/b&gt; &amp;mdash; radial or leap-frog.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument height&lt;/b&gt; and &lt;b&gt;target height&lt;/b&gt; (m) &amp;mdash; used in radial mode where the readings do not carry their own. Ignored in leap-frog mode, where the instrument height cancels.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Refraction coefficient&lt;/b&gt; and its &lt;b&gt;uncertainty&lt;/b&gt; &amp;mdash; dimensionless. The coefficient is poorly known and varies through the day, and it is the dominant error source on long sights, which is why its uncertainty is an input rather than an assumption.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Earth radius&lt;/b&gt; (m) and &lt;b&gt;sight imbalance tolerance&lt;/b&gt; (as a fraction of the longer sight).&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Height differences&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Differences&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;RESULT_COUNT&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula desniveles a partir de los ángulos cenitales y las distancias inclinadas reducidos, con la corrección de curvatura y refracción aplicada y su incertidumbre propagada. En una visual de 100 m la corrección es de 0,7 mm; en 1 km es de 68 mm; en 5 km es de 1,7 m.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radial&lt;/b&gt; calcula un desnivel de la estación ocupada a cada objetivo que visó. La altura del instrumento, la altura de la señal y la refracción contribuyen todas íntegramente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Leap-frog&lt;/b&gt; toma cada estacionamiento que visó exactamente dos objetivos como una estación libre entre ellos, y produce un desnivel del primero al segundo. Dos cosas se cancelan entonces. La &lt;b&gt;altura del instrumento se cancela exactamente&lt;/b&gt; y nunca hay que medirla, lo cual elimina lo que es habitualmente el error dominante en un desnivel trigonométrico corto. Y la &lt;b&gt;refracción se cancela en gran parte&lt;/b&gt;, porque ambas visuales atraviesan el mismo aire en el mismo instante y comparten un coeficiente &amp;mdash; una dependencia compartida conducida por un único jacobiano, de modo que la cancelación aparece en la incertidumbre y no solo en el valor. Con visuales equilibradas la incertidumbre de la refracción abandona el resultado por completo.&lt;/p&gt;&lt;p&gt;Cuánto se cancela depende de lo iguales que sean las dos visuales, lo cual el topógrafo controla por dónde se sitúa, de modo que un par desequilibrado se comunica junto con la fracción de la incertidumbre de la refracción que sobrevivió.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Modo&lt;/b&gt; &amp;mdash; radial o leap-frog.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura del instrumento&lt;/b&gt; y &lt;b&gt;altura de la señal&lt;/b&gt; (m) &amp;mdash; usadas en modo radial donde las lecturas no llevan las suyas. Ignoradas en modo leap-frog, donde la altura del instrumento se cancela.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coeficiente de refracción&lt;/b&gt; y su &lt;b&gt;incertidumbre&lt;/b&gt; &amp;mdash; adimensionales. El coeficiente es mal conocido y varía a lo largo del día, y es la fuente de error dominante en visuales largas, razón por la cual su incertidumbre es una entrada y no una suposición.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radio de la Tierra&lt;/b&gt; (m) y &lt;b&gt;tolerancia de desequilibrio de las visuales&lt;/b&gt; (como fracción de la visual más larga).&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;RESULT_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Archivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Differences</source>
            <translation>Desniveles</translation>
        </message>
        <message>
            <source>Earth radius (m)</source>
            <translation>Radio de la Tierra (m)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Hallazgos</translation>
        </message>
        <message>
            <source>From</source>
            <translation>Desde</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_trig_levelling</source>
            <translation>Generado por GeoComp — geocomp:totalstation_trig_levelling</translation>
        </message>
        <message>
            <source>GeoComp height differences (*.json)</source>
            <translation>Desniveles GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Archivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height difference (%1)</source>
            <translation>Desnivel (%1)</translation>
        </message>
        <message>
            <source>Height differences</source>
            <translation>Desniveles</translation>
        </message>
        <message>
            <source>Height differences from zenith angles and distances, radial or leap-frog.</source>
            <translation>Desniveles a partir de ángulos cenitales y distancias, radial o leap-frog.</translation>
        </message>
        <message>
            <source>Instrument height (m)</source>
            <translation>Altura del instrumento (m)</translation>
        </message>
        <message>
            <source>Leap-frog</source>
            <translation>Leap-frog</translation>
        </message>
        <message>
            <source>Mode</source>
            <translation>Modo</translation>
        </message>
        <message>
            <source>No height difference could be computed. Radial mode needs pointings with a distance; leap-frog mode needs setups that sighted exactly two targets.</source>
            <translation>No se pudo calcular ningún desnivel. El modo radial necesita visuales con distancia; el modo leap-frog necesita estacionamientos que visaron exactamente dos objetivos.</translation>
        </message>
        <message>
            <source>Radial</source>
            <translation>Radial</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Refraction coefficient</source>
            <translation>Coeficiente de refracción</translation>
        </message>
        <message>
            <source>Refraction coefficient uncertainty</source>
            <translation>Incertidumbre del coeficiente de refracción</translation>
        </message>
        <message>
            <source>Refraction surviving</source>
            <translation>Refracción remanente</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Informe</translation>
        </message>
        <message>
            <source>Sight imbalance (m)</source>
            <translation>Desequilibrio de las visuales (m)</translation>
        </message>
        <message>
            <source>Sight imbalance tolerance (relative to the longer sight)</source>
            <translation>Tolerancia del desequilibrio de las visuales (relativa a la visual más larga)</translation>
        </message>
        <message>
            <source>Std dev (mm)</source>
            <translation>Desviación típica (mm)</translation>
        </message>
        <message>
            <source>Target height (m)</source>
            <translation>Altura de la señal (m)</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Trigonometric levelling</source>
            <translation>Nivelación trigonométrica</translation>
        </message>
        <message>
            <source>Trigonometric levelling report</source>
            <translation>Informe de la nivelación trigonométrica</translation>
        </message>
    </context>
    <context>
        <name>TutorialDatasetAlgorithm</name>
        <message>
            <source>%1 file(s) copied to %2.</source>
            <translation>%1 archivo(s) copiado(s) a %2.</translation>
        </message>
        <message>
            <source>%1 file(s) were already there and were left alone: %2. Turn on Overwrite to replace them.</source>
            <translation>%1 archivo(s) ya estaban allí y se dejaron intactos: %2. Active Sobrescribir para reemplazarlos.</translation>
        </message>
        <message>
            <source>(none shipped)</source>
            <translation>(ninguno incluido)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Copies a reference dataset that ships with GeoComp into a directory of your choosing, with its tutorial. The plugin's own directory is usually not writable, and outputs have to go somewhere.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RD-01&lt;/b&gt; is the author's own total-station triangle: three stations, six pointings, each observed on both faces. It is the smallest complete survey there is and it exercises the entire total-station chain, from field book to adjusted network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;It contains two real errors, and that is the point.&lt;/b&gt; One face pair disagrees by exactly 1.000 m in distance &amp;mdash; a transcription blunder, which pre-processing blocks rather than averages away. And the network's global test fails, correctly: the distances disagree between the two ends by far more than the instrument's stated precision allows. A tutorial in which nothing is wrong teaches you which buttons to press; this one teaches you what the software is for.&lt;/p&gt;&lt;p&gt;The copied &lt;code&gt;README.md&lt;/code&gt; walks through the whole chain and explains both, along with why a network with no known point and no azimuth can only be adjusted with inner constraints.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Dataset&lt;/b&gt; &amp;mdash; which shipped dataset to install. &lt;b&gt;Destination folder&lt;/b&gt; &amp;mdash; where to put it; a subfolder named after the dataset is created inside. &lt;b&gt;Overwrite&lt;/b&gt; &amp;mdash; replace files already there, which is off by default so an edited tutorial file is not lost.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;OUTPUT_DIRECTORY&lt;/code&gt; &amp;mdash; where the files landed. &lt;code&gt;FILE_COUNT&lt;/code&gt; &amp;mdash; how many were copied.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Copia un conjunto de datos de referencia que se distribuye con GeoComp a un directorio de su elección, junto con su tutorial. El propio directorio del complemento no suele ser escribible, y las salidas tienen que ir a algún sitio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RD-01&lt;/b&gt; es el triángulo de estación total del propio autor: tres estaciones, seis visuales, cada una observada en las dos posiciones del anteojo. Es el levantamiento completo más pequeño que existe y ejercita toda la cadena de estación total, de la libreta de campo a la red ajustada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Contiene dos errores reales, y ese es precisamente el objetivo.&lt;/b&gt; Un par de posiciones discrepa exactamente 1,000 m en la distancia &amp;mdash; un error grosero de transcripción, que el preprocesamiento bloquea en lugar de diluirlo en la media. Y la prueba global de la red falla, correctamente: las distancias discrepan entre ambos extremos mucho más de lo que permite la precisión declarada del instrumento. Un tutorial en el que nada está mal enseña qué botones pulsar; este enseña para qué sirve el programa.&lt;/p&gt;&lt;p&gt;El &lt;code&gt;README.md&lt;/code&gt; copiado recorre toda la cadena y explica ambos casos, junto con por qué una red sin punto conocido y sin acimut solo puede ajustarse con constricciones internas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Conjunto de datos&lt;/b&gt; &amp;mdash; cuál instalar. &lt;b&gt;Carpeta de destino&lt;/b&gt; &amp;mdash; dónde ponerlo; dentro se crea una subcarpeta con el nombre del conjunto. &lt;b&gt;Sobrescribir&lt;/b&gt; &amp;mdash; reemplazar los archivos ya presentes, desactivado por defecto para no perder un archivo de tutorial editado.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;OUTPUT_DIRECTORY&lt;/code&gt; &amp;mdash; dónde quedaron los archivos. &lt;code&gt;FILE_COUNT&lt;/code&gt; &amp;mdash; cuántos se copiaron.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Copy a shipped reference dataset and its tutorial to a folder you choose.</source>
            <translation>Copia un conjunto de datos de referencia y su tutorial a una carpeta de su elección.</translation>
        </message>
        <message>
            <source>Dataset</source>
            <translation>Conjunto de datos</translation>
        </message>
        <message>
            <source>Destination folder</source>
            <translation>Carpeta de destino</translation>
        </message>
        <message>
            <source>Install tutorial dataset</source>
            <translation>Instalar conjunto de datos del tutorial</translation>
        </message>
        <message>
            <source>No datasets ship with this build. That means the package was built without its resources, which is a packaging fault rather than something you can correct here.</source>
            <translation>Ningún conjunto de datos acompaña a esta compilación. Eso significa que el paquete se construyó sin sus recursos, lo que es un fallo de empaquetado y no algo que pueda corregir aquí.</translation>
        </message>
        <message>
            <source>Overwrite existing files</source>
            <translation>Sobrescribir los archivos existentes</translation>
        </message>
        <message>
            <source>Start with README.md there: it walks through the whole chain.</source>
            <translation>Empiece por el README.md que está allí: recorre toda la cadena.</translation>
        </message>
        <message>
            <source>The destination folder '%1' does not exist.</source>
            <translation>La carpeta de destino '%1' no existe.</translation>
        </message>
    </context>
</TS>
