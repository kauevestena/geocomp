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
            <translation>&lt;p&gt;Lee cada solución &lt;code&gt;.pos&lt;/code&gt; ECEF de una carpeta y construye la línea base que cada una determinó: el vector entre las dos marcas, con su covarianza 3x3 completa.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las alturas de antena se reducen una sola vez.&lt;/b&gt; El vector que determinó el motor es entre puntos de referencia de antena; el ajuste quiere el vector entre las marcas. Aplicar la reducción dos veces se detecta y se rechaza.&lt;/p&gt;&lt;p&gt;&lt;b&gt;De forma predeterminada solo se conserva el subconjunto independiente.&lt;/b&gt; Procesar todos los pares de n estaciones observando simultáneamente produce n(n-1)/2 líneas base, de las cuales solo n-1 son independientes; usarlas todas infla la redundancia aparente del ajuste. Las dependientes se marcan en la salida en lugar de descartarse.&lt;/p&gt;&lt;p&gt;El resultado es un agrupamiento: las observaciones comparten una matriz de covarianza y llegan a DynAdjust como una medición G o X con ella intacta.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La capa opcional dibuja todas las líneas base construidas&lt;/b&gt;, incluidas las dependientes cuando no se conservaron, porque ver qué pares no aportaron información nueva es precisamente el motivo de dibujarlas. La columna &lt;code&gt;independent&lt;/code&gt; y el símbolo discontinuo dicen cuál es cuál; la salida JSON lleva solo lo que se conservó.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El documento de red&lt;/b&gt; es lo que el menú Integración combina con otras técnicas: las líneas base en las épocas medias de sus sesiones y la posición inicial de cada marca. Necesita &lt;i&gt;Marco de las coordenadas de la base&lt;/i&gt;, que un archivo &lt;code&gt;.pos&lt;/code&gt; no indica y GeoComp no supone.&lt;/p&gt;</translation>
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
            <source>&lt;p&gt;Assembles the reduced pointings into a geodetic network and adjusts it by least squares, with the global test, data snooping and reliability analysis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulation, trilateration and triangulateration are not three different computations.&lt;/b&gt; They are one adjustment over three different observation sets, and which one a survey is depends on what was measured. This algorithm adjusts whatever the pointings contain.&lt;/p&gt;&lt;p&gt;Free and constrained solutions are both available, which is the comparison between &lt;i&gt;redes livres&lt;/i&gt; and &lt;i&gt;redes amarradas&lt;/i&gt; the research project names as a teaching goal. A free network is adjusted with inner constraints and is the honest choice when nothing external orients or positions the survey.&lt;/p&gt;&lt;p&gt;The network document is written out as well as the solution, so the chain &lt;i&gt;pre-process &amp;rarr; build &amp;rarr; inspect &amp;rarr; adjust&lt;/i&gt; can be assembled in the graphical modeller using the Analysis algorithms.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Approximate coordinates&lt;/b&gt; &amp;mdash; a JSON object mapping each station to &lt;code&gt;[easting, northing, up]&lt;/code&gt;. Required, not derived: the linearised model needs a point to linearise about, and a traverse or a resection is how a surveyor obtains one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimension&lt;/b&gt; &amp;mdash; which of 2D, 3D and 1D to adjust in. It decides which reduced quantities become observations: a 2D adjustment takes directions and horizontal distances, a 3D one takes directions, zenith angles and slope distances. Emitting all of them would use the same measurement twice.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;b&gt;Fixed stations&lt;/b&gt; &amp;mdash; comma-separated; their approximate coordinates are held exactly.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt;, &lt;b&gt;reference epoch&lt;/b&gt; and &lt;b&gt;CRS&lt;/b&gt; &amp;mdash; recorded on the solution.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; and &lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON documents; the first feeds the Analysis algorithms, the second holds the adjusted coordinates with their full covariance and provenance. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; and &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Result layers&lt;/b&gt; &amp;mdash; five optional map layers, arriving styled and ready to read (FR-905): adjusted stations sized by their positional uncertainty, error ellipses, observations coloured by what the w-test decided about them, the measured network by observation type, and the coordinate correction vectors. None is created unless asked for, so an adjustment run to feed another algorithm writes nothing extra.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ellipse exaggeration&lt;/b&gt; &amp;mdash; real ellipses are invisible at map scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to the network's own extent. Whatever factor is used is stated in the layer's name, which is what reaches the legend: an unstated exaggeration turns a quality visualisation into a misrepresentation.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reúne las visuales reducidas en una red geodésica y la ajusta por mínimos cuadrados, con la prueba global, el data snooping y el análisis de fiabilidad.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulación, trilateración y triangulateración no son tres cálculos distintos.&lt;/b&gt; Son un único ajuste sobre tres conjuntos de observaciones distintos, y cuál de ellos es un levantamiento depende de lo que se midió. Este algoritmo ajusta lo que contengan las visuales.&lt;/p&gt;&lt;p&gt;Las soluciones libres y ligadas están ambas disponibles, que es la comparación entre &lt;i&gt;redes libres&lt;/i&gt; y &lt;i&gt;redes ligadas&lt;/i&gt; que el proyecto de investigación nombra como objetivo pedagógico. Una red libre se ajusta con constricciones internas y es la elección honesta cuando nada externo orienta o posiciona el levantamiento.&lt;/p&gt;&lt;p&gt;El documento de la red se escribe además de la solución, de modo que la cadena &lt;i&gt;preprocesar &amp;rarr; construir &amp;rarr; inspeccionar &amp;rarr; ajustar&lt;/i&gt; pueda montarse en el modelador gráfico usando los algoritmos de Análisis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordenadas aproximadas&lt;/b&gt; &amp;mdash; un objeto JSON que asocia cada estación a &lt;code&gt;[E, N, altitud]&lt;/code&gt;. Exigidas, no derivadas: el modelo linealizado necesita un punto en torno al cual linealizar, y una poligonal o una intersección inversa es como un topógrafo lo obtiene.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimensión&lt;/b&gt; &amp;mdash; en cuál de 2D, 3D y 1D ajustar. Ello decide qué magnitudes reducidas se convierten en observaciones: un ajuste 2D toma direcciones y distancias horizontales, uno 3D toma direcciones, ángulos cenitales y distancias inclinadas. Emitirlas todas usaría la misma medida dos veces.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina el defecto de datum. &lt;b&gt;Estaciones fijas&lt;/b&gt; &amp;mdash; separadas por comas; sus coordenadas aproximadas se mantienen exactamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt;, &lt;b&gt;época de referencia&lt;/b&gt; y &lt;b&gt;SRC&lt;/b&gt; &amp;mdash; registrados en la solución.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; y &lt;b&gt;Solución&lt;/b&gt; &amp;mdash; documentos JSON; el primero alimenta los algoritmos de Análisis, el segundo contiene las coordenadas ajustadas con su matriz de covarianzas completa y la procedencia. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; y &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Capas de resultado&lt;/b&gt; &amp;mdash; cinco capas opcionales, que llegan con estilo y listas para leer (FR-905): estaciones ajustadas dimensionadas por su incertidumbre posicional, elipses de error, observaciones coloreadas según lo que decidió la prueba w, la red medida por tipo de observación y los vectores de corrección de coordenadas. Ninguna se crea sin solicitarla, de modo que un ajuste ejecutado para alimentar otro algoritmo no escribe nada de más.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración de las elipses&lt;/b&gt; &amp;mdash; las elipses reales son invisibles a escala de mapa, por lo que se dibujan ampliadas. Déjelo en 0 y se ajusta un factor a la propia extensión de la red. Sea cual sea el factor utilizado, se declara en el nombre de la capa, que es lo que llega a la leyenda: una exageración no declarada convierte una visualización de calidad en una tergiversación.&lt;/p&gt;</translation>
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
            <source>Critical value</source>
            <translation>Valor crítico</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Defecto de datum</translation>
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
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observaciones reducidas</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundancia</translation>
        </message>
        <message>
            <source>Reference epoch (decimal year)</source>
            <translation>Época de referencia (año decimal)</translation>
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
            <source>&lt;p&gt;Adjusts a geodetic network using &lt;b&gt;DynAdjust&lt;/b&gt;, Geoscience Australia's least-squares suite, and reads its output back into the same solution structure GeoComp's own adjustment produces. Everything downstream &amp;mdash; reports, map layers, storage, multi-epoch comparison &amp;mdash; works the same way whichever engine produced the result.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust must be installed separately.&lt;/b&gt; It is not bundled: it is a large native program under a different licence, and shipping a copy inside a QGIS plugin would make GeoComp responsible for its build. If it is not found, this algorithm says so and names what is missing.&lt;/p&gt;&lt;p&gt;DynAdjust is a suite, not one program. This runs, in order, &lt;code&gt;dnaimport&lt;/code&gt;, then &lt;code&gt;dnareftran&lt;/code&gt; if the target frame or epoch differs from the network's, then &lt;code&gt;dnageoid&lt;/code&gt; if orthometric heights take part, then &lt;code&gt;dnasegment&lt;/code&gt; for a network too large to adjust in one piece, then &lt;code&gt;dnaadjust&lt;/code&gt;. Which stages ran, and why each other one did not, is recorded in the solution's provenance.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference frame&lt;/b&gt; and &lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the frame and epoch to adjust in. Leave them empty to use the network's own. Neither is ever guessed: a frame GeoComp inferred rather than knew is a datum shift absorbed into the residuals.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Geoid grid&lt;/b&gt; &amp;mdash; an NTv2 file, required when the network has orthometric heights, because the height systems cannot be related without one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the chi-square test and the positional uncertainties. &lt;b&gt;Convergence threshold&lt;/b&gt; and &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; passed to DynAdjust unchanged.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Segmentation threshold&lt;/b&gt; &amp;mdash; above this many stations the network is segmented and adjusted in phases, which is rigorous: the block solutions and their variances equal the simultaneous ones.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust directory&lt;/b&gt; &amp;mdash; where the programs are, when they are not on the system path. &lt;b&gt;Timeout&lt;/b&gt; &amp;mdash; seconds before a stage is abandoned and its process group killed.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Keep the working files&lt;/b&gt; &amp;mdash; writes the generated input and the raw DynAdjust output to a folder instead of a temporary directory. An adjustment that surprises you is answerable only from the files that produced it.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON: adjusted coordinates, the full variance matrix, per-observation residuals, the statistics, and the provenance recording every command line that ran.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;ENGINE_VERSION&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;CONVERGED&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; and &lt;code&gt;ADJUSTMENT_MODE&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta una red geodésica usando &lt;b&gt;DynAdjust&lt;/b&gt;, el conjunto de programas de mínimos cuadrados de Geoscience Australia, y lee su salida de vuelta en la misma estructura de solución que produce el ajuste propio de GeoComp. Todo lo que viene después &amp;mdash; informes, capas de mapa, almacenamiento, comparación multiépoca &amp;mdash; funciona igual, sea cual sea el motor que produjo el resultado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;DynAdjust debe instalarse por separado.&lt;/b&gt; No se distribuye junto: es un programa nativo grande, bajo otra licencia, y llevar una copia dentro de un complemento de QGIS haría a GeoComp responsable de su compilación. Si no se encuentra, este algoritmo lo indica y nombra lo que falta.&lt;/p&gt;&lt;p&gt;DynAdjust es un conjunto de programas, no uno solo. Este algoritmo ejecuta, en este orden, &lt;code&gt;dnaimport&lt;/code&gt;, luego &lt;code&gt;dnareftran&lt;/code&gt; si el marco o la época de destino difieren de los de la red, luego &lt;code&gt;dnageoid&lt;/code&gt; si participan alturas ortométricas, luego &lt;code&gt;dnasegment&lt;/code&gt; para una red demasiado grande para ajustarse de una vez, y por último &lt;code&gt;dnaadjust&lt;/code&gt;. Qué etapas se ejecutaron, y por qué cada una de las otras no, queda registrado en la procedencia de la solución.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de referencia&lt;/b&gt; y &lt;b&gt;Época de referencia&lt;/b&gt; &amp;mdash; el marco y la época en que ajustar. Déjelos vacíos para usar los de la propia red. Ninguno se adivina nunca: un marco que GeoComp infirió en lugar de conocer es un desplazamiento de datum absorbido por los residuos.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Malla del geoide&lt;/b&gt; &amp;mdash; un archivo NTv2, obligatorio cuando la red tiene alturas ortométricas, porque los sistemas de alturas no pueden relacionarse sin él.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la prueba ji-cuadrado y las incertidumbres posicionales. &lt;b&gt;Umbral de convergencia&lt;/b&gt; y &lt;b&gt;Número máximo de iteraciones&lt;/b&gt; &amp;mdash; se pasan a DynAdjust sin cambios.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbral de segmentación&lt;/b&gt; &amp;mdash; por encima de este número de estaciones la red se segmenta y se ajusta por fases, lo cual es riguroso: las soluciones de los bloques y sus varianzas son iguales a las simultáneas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Directorio de DynAdjust&lt;/b&gt; &amp;mdash; dónde están los programas, cuando no están en la ruta del sistema. &lt;b&gt;Tiempo límite&lt;/b&gt; &amp;mdash; segundos antes de abandonar una etapa y terminar su grupo de procesos.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Conservar los archivos de trabajo&lt;/b&gt; &amp;mdash; escribe la entrada generada y la salida sin procesar de DynAdjust en una carpeta en vez de un directorio temporal. Un ajuste que sorprende sólo puede responderse a partir de los archivos que lo produjeron.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON: coordenadas ajustadas, la matriz de varianzas completa, residuos por observación, las estadísticas y la procedencia con cada línea de comandos que se ejecutó.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;ENGINE_VERSION&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;CONVERGED&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; y &lt;code&gt;ADJUSTMENT_MODE&lt;/code&gt;.&lt;/p&gt;</translation>
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
            <source>DynAdjust directory (empty = search the system path)</source>
            <translation>Directorio de DynAdjust (vacío = buscar en la ruta del sistema)</translation>
        </message>
        <message>
            <source>DynAdjust was not found. Install it and put its programs on the system path, or give the directory holding them in the 'DynAdjust directory' parameter. GeoComp does not bundle it: it is a separate program under its own licence.</source>
            <translation>No se encontró DynAdjust. Instálelo y ponga sus programas en la ruta del sistema, o indique el directorio que los contiene en el parámetro 'Directorio de DynAdjust'. GeoComp no lo distribuye: es un programa aparte, con su propia licencia.</translation>
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
        <name>EqualSightsAlgorithm</name>
        <message>
            <source>%1 line(s) are exactly balanced. On those the collimation error does not enter the result at all, whatever its value.</source>
            <translation>%1 línea(s) están exactamente equilibradas. En ellas, el error de colimación no entra en absoluto en el resultado, sea cual sea su valor.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reduces each levelling line to one height difference between its two end marks, propagating the uncertainty of every staff reading.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Equal sights is the preferred method&lt;/b&gt; because equal backsight and foresight lengths cancel, to first order, the instrument's collimation error and the effects of curvature and refraction. GeoComp checks the balance and reports the &lt;b&gt;accumulated&lt;/b&gt; imbalance, which is the figure that actually matters: imbalances of opposite sign at successive setups cancel each other, and it is their sum that multiplies the collimation.&lt;/p&gt;&lt;p&gt;The line is reduced as a whole, with the collimation carried once rather than per setup. So on a balanced line the collimation contributes neither a correction nor an uncertainty &amp;mdash; whatever its value, and whatever its own uncertainty. On an imbalanced line it contributes both, and the report shows the raw and corrected differences side by side.&lt;/p&gt;&lt;p&gt;A setup carrying more than one foresight has its extra points reported as side shots. They are correlated with each other through the shared backsight; use &lt;b&gt;Extreme sights&lt;/b&gt; when that correlation matters.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; the document the importer produced.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt;, &lt;b&gt;level id&lt;/b&gt;, &lt;b&gt;collimation&lt;/b&gt; (rad) and its &lt;b&gt;uncertainty&lt;/b&gt; &amp;mdash; where the two-peg test result comes from. A collimation given here overrides the profile's, because a test done this morning beats a profile written last year. With no collimation at all, no correction is applied and the imbalance is reported instead.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Longest sight&lt;/b&gt;, &lt;b&gt;largest imbalance per setup&lt;/b&gt; and &lt;b&gt;largest imbalance per line&lt;/b&gt; (m) &amp;mdash; limits from the specification the work is under. Zero disables a check.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced lines&lt;/b&gt; &amp;mdash; JSON, the input to Closures and to Network adjustment. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Lines&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;LINE_COUNT&lt;/code&gt;, &lt;code&gt;WORST_IMBALANCE&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reduce cada línea de nivelación a un único desnivel entre sus dos referencias extremas, propagando la incertidumbre de cada lectura de mira.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las visuales iguales son el método preferente&lt;/b&gt; porque longitudes iguales de espalda y de frente cancelan, en primer orden, el error de colimación del instrumento y los efectos de la curvatura y la refracción. GeoComp verifica el equilibrio y reporta el desequilibrio &lt;b&gt;acumulado&lt;/b&gt;, que es el valor que realmente importa: desequilibrios de signo contrario en estaciones sucesivas se cancelan, y es su suma la que multiplica la colimación.&lt;/p&gt;&lt;p&gt;La línea se reduce como un todo, con la colimación propagada una sola vez en lugar de por estación. Así, en una línea equilibrada la colimación no aporta ni corrección ni incertidumbre &amp;mdash; sea cual sea su valor y su propia incertidumbre. En una línea desequilibrada aporta ambas, y el informe muestra lado a lado los desniveles bruto y corregido.&lt;/p&gt;&lt;p&gt;Una estación con más de una visual de frente reporta sus puntos adicionales como puntos radiados. Estos están correlacionados entre sí a través de la visual de espalda compartida; use las &lt;b&gt;visuales extremas&lt;/b&gt; cuando esa correlación importe.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estaciones&lt;/b&gt; &amp;mdash; el documento producido por el importador.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt;, &lt;b&gt;identificador del nivel&lt;/b&gt;, &lt;b&gt;colimación&lt;/b&gt; (rad) y su &lt;b&gt;incertidumbre&lt;/b&gt; &amp;mdash; de dónde procede el resultado del ensayo de las dos estacas. Una colimación indicada aquí prevalece sobre la del perfil, porque un ensayo hecho esta mañana vale más que un perfil escrito el año pasado. Sin colimación alguna, no se aplica corrección y en su lugar se reporta el desequilibrio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Visual más larga&lt;/b&gt;, &lt;b&gt;mayor desequilibrio por estación&lt;/b&gt; y &lt;b&gt;mayor desequilibrio por línea&lt;/b&gt; (m) &amp;mdash; límites de la especificación bajo la que se trabaja. Cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; JSON, la entrada de los cierres y del ajuste de la red. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Líneas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;LINE_COUNT&lt;/code&gt;, &lt;code&gt;WORST_IMBALANCE&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
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
            <translation>Mayor desequilibrio por estación (m)</translation>
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
            <translation>Estación</translation>
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
            <translation>Los puntos radiados se nivelan desde una estación de la línea sin que la línea pase por ellos. Un punto observado una sola vez no tiene redundancia, por lo que no se ajusta; use las visuales extremas cuando importe la correlación entre varios de esos puntos.</translation>
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
            <translation>&lt;p&gt;Combina observaciones recíprocas a través de un obstáculo &amp;mdash; un río es el caso que la propuesta menciona &amp;mdash; donde una estación de visuales iguales es imposible.&lt;/p&gt;&lt;p&gt;El instrumento de cada orilla lee la mira de su propio lado en una visual corta y la mira del otro lado del agua en una visual larga. La visual larga carga casi todo el error, y este entra en las dos determinaciones con &lt;b&gt;signo contrario&lt;/b&gt;, por lo que se cancela en su media. Esa cancelación es el método.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La incertidumbre es deliberadamente más conservadora que la de las visuales iguales.&lt;/b&gt; La refracción sobre el agua varía rápida y asimétricamente, y las dos observaciones no fueron simultáneas, por lo que la simetría en la que se apoya el método solo se cumple aproximadamente. La varianza propagada se multiplica por el factor de inflación y el resultado se marca como escalado empírico, que lo acompaña en todos los informes. Fijar el factor en uno está permitido y se reporta como advertencia, porque afirma que las dos observaciones vieron exactamente el mismo aire.&lt;/p&gt;&lt;p&gt;Se reporta la &lt;b&gt;discrepancia&lt;/b&gt; entre las dos determinaciones. Su valor esperado es cero; una discrepancia grande indica que la refracción cambió entre ellas, que es precisamente el supuesto del método, por lo que se muestra en lugar de diluirse en la media.&lt;/p&gt;&lt;h3&gt;Disposición de los datos&lt;/h3&gt;&lt;p&gt;Cada travesía son &lt;b&gt;dos estaciones&lt;/b&gt; en la libreta importada, cada una con una visual de espalda (la mira cercana) y una de frente (la mira lejana), observando la segunda estación las mismas dos estaciones en sentido inverso. Las estaciones se emparejan en el orden en que aparecen.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estaciones&lt;/b&gt; &amp;mdash; el documento producido por el importador. &lt;b&gt;Inflación de la varianza&lt;/b&gt; &amp;mdash; al menos uno. &lt;b&gt;Tolerancia de la discrepancia&lt;/b&gt; (m) &amp;mdash; por encima de la cual se reporta la divergencia entre las orillas; cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Travesías&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;CROSSING_COUNT&lt;/code&gt; y &lt;code&gt;WORST_DISCREPANCY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A reciprocal crossing is two setups, one from each bank, so the book must hold an even number of at least two. It holds %1.</source>
            <translation>Una travesía recíproca son dos estaciones, una desde cada orilla, por lo que la libreta debe contener un número par de al menos dos. Contiene %1.</translation>
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
            <translation>La estación '%1' tiene varias visuales de frente. Una travesía recíproca tiene una mira cercana y una mira lejana por orilla.</translation>
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
            <translation>&lt;p&gt;Reduce cada estación del instrumento a un desnivel por cada visual de frente, conservando la &lt;b&gt;covarianza completa&lt;/b&gt; entre ellos.&lt;/p&gt;&lt;p&gt;Todas las visuales de frente de una estación restan la misma lectura de espalda, por lo que comparten su error. Entre dos de ellas la visual de espalda &lt;b&gt;se cancela exactamente&lt;/b&gt;: su desnivel es una visual de frente menos la otra, y la de espalda no aparece. Tratarlas como independientes añade dos veces la varianza de la espalda que no está ahí y reporta una incertidumbre demasiado &lt;b&gt;grande&lt;/b&gt; &amp;mdash; lo contrario del fallo habitual, y puede llevar a declarar inadecuada una red que en realidad está bien.&lt;/p&gt;&lt;p&gt;El informe presenta ambos: el desnivel de la estación visada de espalda a cada visual de frente, y el desnivel entre cada par de visuales de frente calculado a través de la covarianza, junto a lo que un tratamiento independiente habría afirmado.&lt;/p&gt;&lt;p&gt;La correlación se lleva al documento de salida como una covarianza, por lo que un ajuste de red construido a partir de estas estaciones la conserva.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estaciones&lt;/b&gt; &amp;mdash; el documento producido por el importador. &lt;b&gt;Solo estaciones con varias visuales de frente&lt;/b&gt; &amp;mdash; omite las estaciones ordinarias de una sola visual, que no tienen correlación que mostrar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt; e &lt;b&gt;identificador del nivel&lt;/b&gt; &amp;mdash; de dónde procede la precisión de las lecturas. &lt;b&gt;Visual más larga&lt;/b&gt; y &lt;b&gt;mayor desequilibrio por estación&lt;/b&gt; (m) &amp;mdash; límites; cero desactiva la verificación.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON con las covarianzas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;DIFFERENCE_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
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
            <translation>Desniveles desde cada estación</translation>
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
            <translation>Mayor desequilibrio por estación (m)</translation>
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
            <translation>Ninguna estación tiene varias visuales de frente. Las visuales extremas son para una estación que niveló un conjunto de puntos a la vez; desmarque 'Solo estaciones con varias visuales de frente' para reducir también las estaciones ordinarias.</translation>
        </message>
        <message>
            <source>Only setups with several foresights</source>
            <translation>Solo estaciones con varias visuales de frente</translation>
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
            <translation>Estación</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamientos</translation>
        </message>
        <message>
            <source>Several foresights from one setup, kept correlated through the backsight.</source>
            <translation>Varias visuales de frente desde una estación, mantenidas correlacionadas por la visual de espalda.</translation>
        </message>
        <message>
            <source>The backsight cancels between two foresights of one setup, so these differences are better determined than independent treatment would suggest. The last column is how much an independent treatment would have overstated the uncertainty by.</source>
            <translation>La visual de espalda se cancela entre dos visuales de frente de la misma estación, por lo que estos desniveles quedan mejor determinados de lo que un tratamiento independiente sugeriría. La última columna indica en cuánto un tratamiento independiente habría sobrestimado la incertidumbre.</translation>
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
            <translation>Agrupaciones correlacionadas</translation>
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
            <source>Redundancy</source>
            <translation>Redundancia</translation>
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
            <source>Analysis</source>
            <translation>Análisis</translation>
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
        <name>GeoCompGnss</name>
        <message>
            <source>%1: used the %2 orbit, as Global Settings allow; recorded in provenance.</source>
            <translation>%1: se usó la órbita %2, como permite la Configuración Global; registrado en la procedencia.</translation>
        </message>
        <message>
            <source>&lt;p&gt;&lt;b&gt;Absolute (PPP) processing in RTKLIB is limited.&lt;/b&gt; Its precise point positioning is not equivalent to a dedicated PPP service: convergence is slower, the ambiguity handling is simpler, and the result is typically decimetre-level rather than centimetre-level. Prefer Relative processing where a base station is available, and treat an Absolute solution as indicative unless you have checked it against an independent determination.&lt;/p&gt;</source>
            <translation>&lt;p&gt;&lt;b&gt;El procesamiento Absoluto (PPP) en RTKLIB es limitado.&lt;/b&gt; Su posicionamiento puntual preciso no equivale a un servicio PPP dedicado: la convergencia es más lenta, el tratamiento de ambigüedades es más simple y el resultado es típicamente decimétrico en lugar de centimétrico. Prefiera el procesamiento Relativo cuando haya una estación base disponible, y trate una solución Absoluta como indicativa a menos que la haya contrastado con una determinación independiente.&lt;/p&gt;</translation>
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
            <source>The configured antenna file does not exist: %1</source>
            <translation>El archivo de antena configurado no existe: %1</translation>
        </message>
        <message>
            <source>The configured product directory does not exist: %1</source>
            <translation>El directorio de productos configurado no existe: %1</translation>
        </message>
        <message>
            <source>Unknown download service: %1. Known services: %2</source>
            <translation>Servicio de descarga desconocido: %1. Servicios conocidos: %2</translation>
        </message>
        <message>
            <source>Unknown processing profile: %1</source>
            <translation>Perfil de procesamiento desconocido: %1</translation>
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
            <translation>Mínimo error detectable</translation>
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
            <translation>Altura del prisma</translation>
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
            <source>%1 is not a GeoComp project store: it holds other tables (%2). GeoComp does not write into a store it did not create; choose a new file or schema.</source>
            <translation>%1 no es un repositorio de proyecto de GeoComp: contiene otras tablas (%2). GeoComp no escribe en un repositorio que no creó; elija un archivo o esquema nuevo.</translation>
        </message>
        <message>
            <source>%1 station(s) are reached only through heights, so nothing determines where they are horizontally: %2. Tie them in with a GNSS vector or a total-station observation, hold them horizontally, or adjust the levelling on its own.</source>
            <translation>%1 estación(es) se alcanzan solo mediante alturas, así que nada determina dónde están horizontalmente: %2. Vincúlelas con un vector GNSS o una observación de estación total, fíjelas horizontalmente o ajuste la nivelación por separado.</translation>
        </message>
        <message>
            <source>'%1' holds no readings: expected %2.</source>
            <translation>'%1' no contiene lecturas: se esperaba %2.</translation>
        </message>
        <message>
            <source>'%1' is not a datum GeoComp can refer displacements to. Choose one of: %2.</source>
            <translation>'%1' no es un datum al que GeoComp pueda referir desplazamientos. Elija uno de: %2.</translation>
        </message>
        <message>
            <source>(not set)</source>
            <translation>(no definido)</translation>
        </message>
        <message>
            <source>A counter reading of %1 is outside the gravimeter's calibration table: expected %2.</source>
            <translation>Una lectura de contador de %1 está fuera de la tabla de calibración del gravímetro: se esperaba %2.</translation>
        </message>
        <message>
            <source>A download service could not be read: %1. Each needs an 'id', a 'name' and 'templates' keyed like 'orbit/final'.</source>
            <translation>No se pudo leer un servicio de descarga: %1. Cada uno necesita 'id', 'name' y 'templates' con claves como 'orbit/final'.</translation>
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
            <source>A position must move from epoch %1 and no velocity was given for it. Supply one in the velocities file.</source>
            <translation>Una posición debe llevarse desde la época %1 y no se dio velocidad para ella. Indique una en el archivo de velocidades.</translation>
        </message>
        <message>
            <source>A project store at schema %1 cannot be brought forward by this version of GeoComp: a migration step is missing. Report this; do not edit the store by hand.</source>
            <translation>Esta versión de GeoComp no puede actualizar un repositorio de proyecto en el esquema %1: falta un paso de migración. Informe del problema; no edite el repositorio a mano.</translation>
        </message>
        <message>
            <source>A series needs two epochs at least; %1 was given.</source>
            <translation>Una serie necesita al menos dos épocas; se dio %1.</translation>
        </message>
        <message>
            <source>Correlated cluster '%1' supplies %2 observation rows but a %3 covariance matrix. The two must agree, in the same order.</source>
            <translation>El grupo correlacionado '%1' aporta %2 filas de observación pero una matriz de covarianzas %3. Ambos deben coincidir, en el mismo orden.</translation>
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
            <source>Every station in this network is held fixed, so there is nothing to estimate. %1</source>
            <translation>Todas las estaciones de esta red están fijas, por lo que no hay nada que estimar. %1</translation>
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
            <source>In the input '%1', %2 must be moved to the combination's epoch, and no velocity was given for it. Supply one in the velocities file; zero is not assumed -- it is a decimetre a decade in most of Brazil.</source>
            <translation>En la entrada '%1', %2 debe llevarse a la época de la combinación, y no se dio velocidad para él. Indique una en el archivo de velocidades; no se supone cero -- es un decímetro por década en la mayor parte de Brasil.</translation>
        </message>
        <message>
            <source>Line %1 of '%2' could not be read: %3. Correct or remove the line and run again.</source>
            <translation>No se pudo leer la línea %1 de '%2': %3. Corrija o elimine la línea y ejecute de nuevo.</translation>
        </message>
        <message>
            <source>Line %1 of '%2' gives the time '%3' without its offset from UTC. The tide depends on the time to the minute, so a time without a zone is a guess; write it as, for example, 2013-09-15T05:57:01Z or 2013-09-15T02:57:01-03:00.</source>
            <translation>La línea %1 de '%2' indica la hora '%3' sin su desfase respecto a UTC. La marea depende de la hora al minuto, así que una hora sin zona es una conjetura; escríbala, por ejemplo, como 2013-09-15T05:57:01Z o 2013-09-15T02:57:01-03:00.</translation>
        </message>
        <message>
            <source>No gravimeter profile was named and the profile library sets no default. Add one to the library, or run without a library to use the file's own instrument names.</source>
            <translation>No se indicó ningún perfil de gravímetro y la biblioteca de perfiles no define uno predeterminado. Añada uno a la biblioteca, o ejecute sin biblioteca para usar los nombres de instrumento del propio archivo.</translation>
        </message>
        <message>
            <source>No observations were supplied. %1</source>
            <translation>No se suministró ninguna observación. %1</translation>
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
            <source>No stations were given to define the datum on. %1</source>
            <translation>No se indicó ninguna estación para definir el datum. %1</translation>
        </message>
        <message>
            <source>Observation '%1' between %2 has no horizontal separation at the approximate coordinates, so the zenith angle cannot be linearised there. Correct the approximate coordinates.</source>
            <translation>La observación '%1' entre %2 no tiene separación horizontal en las coordenadas aproximadas, por lo que el ángulo cenital no puede linealizarse allí. Corrija las coordenadas aproximadas.</translation>
        </message>
        <message>
            <source>Observation '%1' carries no uncertainty, so it cannot be weighted. %2</source>
            <translation>La observación '%1' no tiene incertidumbre, por lo que no puede ponderarse. %2</translation>
        </message>
        <message>
            <source>Observation '%1' connects stations that are at the same approximate position (%2), so its direction is undefined. Correct the approximate coordinates.</source>
            <translation>La observación '%1' une estaciones que están en la misma posición aproximada (%2), por lo que su dirección es indefinida. Corrija las coordenadas aproximadas.</translation>
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
            <source>Row %1 of the alert thresholds file cannot be read: '%2'. Expected %3. Each row is kind, limit, stations, group.</source>
            <translation>La fila %1 del archivo de umbrales de alerta no se puede leer: '%2'. Se esperaba %3. Cada fila es tipo, límite, estaciones, grupo.</translation>
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
            <source>Someone else saved %1 since you opened it (revision %2 now; you read %3). Nothing was written. Open the project again and redo your change, so their save is not overwritten.</source>
            <translation>Otra persona guardó %1 desde que usted lo abrió (revisión %2 ahora; usted leyó la %3). No se escribió nada. Abra el proyecto de nuevo y rehaga su cambio, para no sobrescribir lo que guardó.</translation>
        </message>
        <message>
            <source>State the epoch of the combination (a decimal year). None of the inputs states one GeoComp could take, and it does not assume one.</source>
            <translation>Indique la época de la combinación (un año decimal). Ninguna de las entradas indica una que GeoComp pueda tomar, y no supone una.</translation>
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
            <source>Station '%1' is held fixed but carries no position, so there is no value to hold it at. Give it coordinates, or release the constraint.</source>
            <translation>La estación '%1' está fija pero no tiene posición, por lo que no hay valor en el que mantenerla. Asígnele coordenadas, o libere la constricción.</translation>
        </message>
        <message>
            <source>Strain cannot be computed here: %1. It needs three object points at least, spread over an area.</source>
            <translation>La deformación no se puede calcular aquí: %1. Se necesitan al menos tres puntos objeto, distribuidos en un área.</translation>
        </message>
        <message>
            <source>The %1 threshold's limit is %2; it must be positive.</source>
            <translation>El límite del umbral %1 es %2; debe ser positivo.</translation>
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
            <source>The adjustment of '%1' did not converge: after %2 iteration(s) the largest correction was still %3, against a threshold of %4. Approximate coordinates that are far from the truth are the usual cause; a blunder large enough to drag the solution is the other. No coordinates are returned, because iterate %2 of a diverging sequence is not a result.</source>
            <translation>El ajuste de '%1' no convergió: tras %2 iteración(es) la mayor corrección seguía siendo %3, frente a un umbral de %4. Unas coordenadas aproximadas lejanas de la verdad son la causa habitual; un error grosero suficientemente grande como para arrastrar la solución es la otra. No se devuelve ninguna coordenada, porque la iteración %2 de una sucesión divergente no es un resultado.</translation>
        </message>
        <message>
            <source>The adjustment of '%1' produced no iterations at all. This is an internal error; please report it with the network that caused it.</source>
            <translation>El ajuste de '%1' no produjo iteración alguna. Se trata de un error interno; comuníquelo junto con la red que lo provocó.</translation>
        </message>
        <message>
            <source>The archive refused the login for %1 (HTTP %2). Check the QGIS authentication configuration named for this service in the download services file.</source>
            <translation>El archivo rechazó el inicio de sesión para %1 (HTTP %2). Compruebe la configuración de autenticación de QGIS indicada para este servicio en el archivo de servicios de descarga.</translation>
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
            <source>The drift of session '%1' cannot be estimated with the station values: no station was read again at enough different times for a degree-%2 drift. Re-occupy a station in that session, lower the degree, or split the session.</source>
            <translation>La deriva de la sesión '%1' no puede estimarse junto con los valores de las estaciones: ninguna estación se volvió a leer en suficientes instantes distintos para una deriva de grado %2. Reocupe una estación en esa sesión, reduzca el grado o divida la sesión.</translation>
        </message>
        <message>
            <source>The frames %1 are related only at epoch %2, and the second solution is at another. Carrying a position between epochs along a velocity is exactly the motion being measured, so GeoComp will not do it here. Give both epochs in frames related at every epoch (the ITRFs), or in the same frame.</source>
            <translation>Los marcos %1 se relacionan solo en la época %2, y la segunda solución está en otra. Llevar una posición entre épocas a lo largo de una velocidad es exactamente el movimiento que se mide, por eso GeoComp no lo hace aquí. Indique ambas épocas en marcos relacionados en cualquier época (los ITRF), o en el mismo marco.</translation>
        </message>
        <message>
            <source>The height difference '%1' does not say whether it is orthometric or ellipsoidal. Rebuild its network with the current GeoComp, which records it.</source>
            <translation>El desnivel '%1' no dice si es ortométrico o elipsoidal. Reconstruya su red con el GeoComp actual, que lo registra.</translation>
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
            <source>The network '%1' has no active observations, so there is nothing to adjust. Observations marked as rejected do not take part; re-activate the ones you want to use.</source>
            <translation>La red '%1' no tiene observaciones activas, por lo que no hay nada que ajustar. Las observaciones marcadas como rechazadas no participan; reactive las que desee utilizar.</translation>
        </message>
        <message>
            <source>The network '%1' is not internally consistent: %2. Run Inspect network to see every problem at once.</source>
            <translation>La red '%1' no es internamente consistente: %2. Ejecute Inspeccionar red para ver todos los problemas de una vez.</translation>
        </message>
        <message>
            <source>The network does not determine %1 combination(s) of unknowns: %2. Add observations that fix them, or define the datum with inner or minimum constraints so the remaining freedom is removed deliberately.</source>
            <translation>La red no determina %1 combinación(es) de incógnitas: %2. Añada observaciones que las fijen, o defina el datum con constricciones internas o mínimas, de modo que la libertad restante se elimine deliberadamente.</translation>
        </message>
        <message>
            <source>The observation %1 cannot be deleted: the stored solutions %2 were computed from it (FR-135). Supersede those solutions first, or keep the observation.</source>
            <translation>La observación %1 no se puede eliminar: las soluciones almacenadas %2 se calcularon a partir de ella (FR-135). Reemplace antes esas soluciones, o conserve la observación.</translation>
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
            <source>The planned network '%1' contains no observations, so there is no design to evaluate. Add the observations you intend to make, with their assumed precisions.</source>
            <translation>La red planificada '%1' no contiene observaciones, por lo que no hay diseño que evaluar. Añada las observaciones que pretende realizar, con sus precisiones supuestas.</translation>
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
            <source>The reading '%1' appears twice. Remove the duplicate line and run again.</source>
            <translation>La lectura '%1' aparece dos veces. Elimine la línea duplicada y ejecute de nuevo.</translation>
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
            <source>The setting '%1' cannot be greater than %2 (received %3).</source>
            <translation>La configuración '%1' no puede ser mayor que %2 (se recibió %3).</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be less than %2 (received %3).</source>
            <translation>La configuración '%1' no puede ser menor que %2 (se recibió %3).</translation>
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
            <source>The solution %1 cannot supersede itself; name the earlier solution it replaces.</source>
            <translation>La solución %1 no puede reemplazarse a sí misma; indique la solución anterior a la que reemplaza.</translation>
        </message>
        <message>
            <source>The solution '%1' has no position components to compare (%2).</source>
            <translation>La solución '%1' no tiene componentes de posición que comparar (%2).</translation>
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
            <source>The station '%1' is held by two inputs (%2) at positions %3 m apart. Hold it in one input only, or correct the one that is wrong: two holds a distance apart force that distance into the residuals.</source>
            <translation>La estación '%1' está fijada por dos entradas (%2) en posiciones a %3 m entre sí. Fíjela en una sola entrada o corrija la equivocada: dos fijaciones separadas por una distancia fuerzan esa distancia en los residuos.</translation>
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
            <source>There is no GeoComp project at %1. Check the name, or choose to create it.</source>
            <translation>No hay ningún proyecto de GeoComp en %1. Compruebe el nombre, o elija crearlo.</translation>
        </message>
        <message>
            <source>There is no PostgreSQL connection named '%1' in QGIS. Add it in the Browser panel under PostgreSQL, or choose one that exists.</source>
            <translation>No hay ninguna conexión PostgreSQL llamada '%1' en QGIS. Añádala en el panel Navegador bajo PostgreSQL, o elija una que exista.</translation>
        </message>
        <message>
            <source>There is no solution %1 in this project store.</source>
            <translation>No hay ninguna solución %1 en este repositorio de proyecto.</translation>
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
            <source>This JSON file is not a GeoComp network document: it has no network identifier. Expected %1.</source>
            <translation>Este archivo JSON no es un documento de red de GeoComp: no tiene identificador de red. Se esperaba: %1.</translation>
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
            <source>This file is not a gravimeter export GeoComp can read. Expected %1.</source>
            <translation>Este archivo no es una exportación de gravímetro que GeoComp pueda leer. Se esperaba %1.</translation>
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
            <source>This project file holds %1 networks, so GeoComp cannot tell which one you mean. Export the network you want to analyse and choose that file instead.</source>
            <translation>Este archivo de proyecto contiene %1 redes, por lo que GeoComp no puede saber a cuál se refiere. Exporte la red que desea analizar y elija ese archivo.</translation>
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
        <name>GeoCompPrompts</name>
        <message>
            <source>Choose a field book</source>
            <translation>Elija una libreta de campo</translation>
        </message>
        <message>
            <source>Field books (*.csv *.txt);;All files (*)</source>
            <translation>Libretas de campo (*.csv *.txt);;Todos los archivos (*)</translation>
        </message>
    </context>
    <context>
        <name>GeoCompReport</name>
        <message>
            <source>not defined</source>
            <translation>no definido</translation>
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
            <translation>Tolerancia de distancia entre caras (m; 0 = del distanciómetro del instrumento)</translation>
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
            <translation>Mayor desequilibrio permitido por estación (m)</translation>
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
            <translation>Proporcional al número de estaciones</translation>
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
            <source>this project</source>
            <translation>este proyecto</translation>
        </message>
        <message>
            <source>this run</source>
            <translation>esta ejecución</translation>
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
            <translation>&lt;p&gt;Ajusta las lecturas que el &lt;i&gt;Preprocesamiento (escala, marea, deriva)&lt;/i&gt; redujo: las ocupaciones de cada sesión se convierten en diferencias de gravedad, los valores absolutos entran ponderados, y el resultado pasa por la misma prueba global, detección de errores groseros y análisis de fiabilidad que cualquier otro ajuste de GeoComp.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Deriva.&lt;/b&gt; Estimada junto con los valores de las estaciones por defecto, un polinomio por sesión: toda reocupación contribuye, no solo las de una estación base. &lt;i&gt;Ajustada antes a las lecturas de la base&lt;/i&gt; es el método clásico de campo, conservado para comparar y para sesiones que no reocupan nada más que su base. Las diferencias llevan su covarianza exacta en ambos casos: las diferencias sucesivas comparten una ocupación y están correlacionadas, y la incertidumbre del factor de calibración es común a todas las lecturas de un instrumento.&lt;/p&gt;&lt;p&gt;La &lt;b&gt;gravedad conocida&lt;/b&gt; se introduce como pares &lt;code&gt;estación=valor&lt;/code&gt; en mGal, separados por comas o puntos y comas. Con &lt;code&gt;±sigma&lt;/code&gt; el valor es una determinación absoluta y se pondera por su incertidumbre, por ejemplo &lt;code&gt;RG26=979197.5759±0.0106&lt;/code&gt;; sin él la estación se mantiene fija exactamente, lo que la convierte en el datum y toda incertidumbre relativa a ella. Sin ninguna, la red se ajusta con una constricción interna y todo valor es relativo a su media; el informe dice cuál fue el caso.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Un valor debe referirse a la marca.&lt;/b&gt; Indique al preprocesamiento una altura del sensor, o las lecturas tomadas 20 cm por encima de la marca diferirán de un valor absoluto indicado en ella en unos 60 µGal.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las observaciones no verificables se enumeran por nombre.&lt;/b&gt; Una red gravimétrica es pequeña y poco redundante, y una diferencia con redundancia cercana a cero puede ocultar un error grosero que ninguna prueba encontrará. Un valor absoluto aislado siempre es una de ellas. El informe las enumera y las capas las dibujan con un color propio.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Lecturas reducidas&lt;/b&gt; &amp;mdash; el documento que escribió el preprocesamiento. &lt;b&gt;Gravedad conocida&lt;/b&gt; &amp;mdash; como arriba. &lt;b&gt;Tratamiento de la deriva&lt;/b&gt; y &lt;b&gt;grado de la deriva&lt;/b&gt; toman por defecto las configuraciones del Gravímetro.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Considerar la correlación entre diferencias&lt;/b&gt; (avanzado) &amp;mdash; activado por defecto. Desactivado reproduce MCGravi y pyGrav, que tratan las diferencias como independientes, y el resultado registra esa suposición. &lt;b&gt;Confianza&lt;/b&gt;, &lt;b&gt;alfa&lt;/b&gt; y &lt;b&gt;beta&lt;/b&gt; &amp;mdash; para las pruebas.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON, en m/s². &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Gravedad&lt;/b&gt; &amp;mdash; CSV. &lt;b&gt;Estaciones gravimétricas&lt;/b&gt; y &lt;b&gt;Diferencias de gravedad&lt;/b&gt; &amp;mdash; capas, ubicadas donde se tomaron las lecturas; valores en la unidad de visualización de las configuraciones del Gravímetro, que una columna indica. Escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; y &lt;code&gt;DATUM_DEFECT&lt;/code&gt; (solo de las observaciones relativas).&lt;/p&gt;</translation>
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
            <translation>Defecto de datum de las diferencias</translation>
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
            <translation>%1 estación(es) en %2 línea(s).</translation>
        </message>
        <message>
            <source>'%1' could not be read as a levelling field mapping: %2</source>
            <translation>'%1' no pudo leerse como un mapeo de campos de nivelación: %2</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads a levelling field book and assembles it into instrument setups and lines, attaching an uncertainty to every reading.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Two layouts are recognised&lt;/b&gt;, and which one a file is in is worked out from the columns the mapping names rather than asked for. One row per setup, backsight and foresight side by side, is what a spreadsheet naturally produces. One row per reading, each carrying a setup identifier, is what an instrument exports &amp;mdash; and the only layout that can express a setup with several foresights at all.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Three-wire readings&lt;/b&gt; may replace a single reading in either layout. They buy the sight distance for free by stadia, which is what makes the sight-balance check possible on a book that never recorded a distance, and a half-sum check that catches a misread wire.&lt;/p&gt;&lt;p&gt;Numbers are read locale-independently: a comma decimal separator is handled here, at the boundary, and never again.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Field book&lt;/b&gt; &amp;mdash; the CSV. &lt;b&gt;Field mapping&lt;/b&gt; &amp;mdash; a saved mapping document describing the layout.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt; and &lt;b&gt;level id&lt;/b&gt; &amp;mdash; where the reading precision comes from. With neither, a generic level is assumed and the report says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Default staff-reading uncertainty&lt;/b&gt; (m) &amp;mdash; the last resort before refusing. Zero means not configured; GeoComp does not invent a sigma, because a fabricated weight corrupts every statistic computed from it.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Stadia factor&lt;/b&gt; &amp;mdash; used only when three wires are read and no level profile is available.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Setups&lt;/b&gt; &amp;mdash; JSON, the input to the reduction algorithms. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;LINE_COUNT&lt;/code&gt; and &lt;code&gt;REJECTED_ROWS&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lee una libreta de nivelación y la organiza en estaciones del instrumento y líneas, asignando una incertidumbre a cada lectura.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Se reconocen dos disposiciones&lt;/b&gt;, y cuál usa el fichero se deduce de las columnas que indica el mapeo, en lugar de preguntarse. Una fila por estación, con espalda y frente lado a lado, es lo que una hoja de cálculo produce de forma natural. Una fila por lectura, cada una con el identificador de la estación, es lo que exporta un instrumento &amp;mdash; y la única disposición capaz de expresar una estación con varias visuales de frente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Las lecturas de los tres hilos&lt;/b&gt; pueden sustituir a una lectura única en cualquiera de las disposiciones. Dan gratis la distancia de la visual por estadimetría, que es lo que hace posible la verificación del equilibrio en una libreta que nunca registró distancias, y una verificación de la semisuma que detecta un hilo mal leído.&lt;/p&gt;&lt;p&gt;Los números se leen con independencia de la configuración regional: una coma decimal se trata aquí, en la frontera, y nunca más.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Libreta&lt;/b&gt; &amp;mdash; el CSV. &lt;b&gt;Mapeo de campos&lt;/b&gt; &amp;mdash; un documento de mapeo guardado que describe la disposición.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfiles de instrumento&lt;/b&gt; e &lt;b&gt;identificador del nivel&lt;/b&gt; &amp;mdash; de dónde procede la precisión de las lecturas. Sin ninguno de ellos se asume un nivel genérico y el informe lo dice.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Incertidumbre por defecto de la lectura de mira&lt;/b&gt; (m) &amp;mdash; el último recurso antes de rechazar. Cero significa no configurado; GeoComp no inventa un sigma, porque un peso fabricado corrompe todas las estadísticas calculadas a partir de él.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Constante estadimétrica&lt;/b&gt; &amp;mdash; se usa solo cuando se leen tres hilos y no hay perfil de nivel disponible.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Estaciones&lt;/b&gt; &amp;mdash; JSON, la entrada de los algoritmos de reducción. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;SETUP_COUNT&lt;/code&gt;, &lt;code&gt;LINE_COUNT&lt;/code&gt; y &lt;code&gt;REJECTED_ROWS&lt;/code&gt;.&lt;/p&gt;</translation>
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
            <translation>Estaciones de GeoComp (*.json)</translation>
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
            <translation>No se leyó ninguna estación utilizable. Todas las filas fueron rechazadas; el informe indica por qué, fila a fila.</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Magnitud</translation>
        </message>
        <message>
            <source>Read a CSV levelling book into setups and lines, with findings.</source>
            <translation>Lee una libreta de nivelación en CSV, produciendo estaciones, líneas y hallazgos.</translation>
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
            <translation>Estaciones montadas</translation>
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
            <translation>&lt;p&gt;Calcula el error de cierre de un circuito o de una línea de nivelación y lo compara con el error admisible &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt;, con &lt;i&gt;L&lt;/i&gt; en kilómetros.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sin una k configurada no hay veredicto.&lt;/b&gt; El error de cierre se sigue reportando &amp;mdash; es el número que importa &amp;mdash; pero si es aceptable no, porque inventar una tolerancia solo para tener con qué comparar sería peor que no decir nada. GeoComp no incluye ninguna tabla nacional de tolerancias: &lt;i&gt;k&lt;/i&gt; difiere de país a país, de clase a clase dentro de un país y de edición a edición de la norma, y un valor equivocado no falla de forma ruidosa, acepta silenciosamente una línea que debería haberse repetido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La distribución entre estaciones viene con una salvedad que forma parte de la respuesta.&lt;/b&gt; Distribuir proporcionalmente un error de cierre es la corrección clásica y muchas especificaciones la exigen, por lo que se calcula. Pero la distribución proporcional &lt;b&gt;no localiza nada&lt;/b&gt;: cada estación recibe su parte, esté o no donde entró el error, por lo que un error grosero se reparte uniformemente por la línea y resulta más difícil de encontrar.&lt;/p&gt;&lt;p&gt;Por eso el error de cierre se compara también con &lt;b&gt;su propia desviación típica propagada&lt;/b&gt;. Una razón pequeña significa que la línea cerró tan bien como indican sus propias lecturas, y distribuir ese error es exactamente lo correcto. Una razón grande significa que ocurrió algo que las precisiones de las lecturas no explican, y repartirlo uniformemente es la única respuesta que garantiza ocultarlo &amp;mdash; ajuste la red y deje que el data snooping lo encuentre. El informe indica en qué caso está.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; el documento producido por una reducción. &lt;b&gt;Modo&lt;/b&gt; &amp;mdash; circuito (las líneas deben encadenarse y volver al punto de partida; una línea introducida en sentido inverso se trata a partir de los identificadores de las estaciones) o línea (solo la primera, contra un desnivel conocido).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Desnivel conocido&lt;/b&gt; y su &lt;b&gt;incertidumbre&lt;/b&gt; (m) &amp;mdash; de las altitudes publicadas de las dos referencias. La incertidumbre entra en la del error de cierre: una línea cerrada contra dos referencias de tercer orden no se ha comprobado tan severamente como una cerrada contra dos de primer orden.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coeficiente de tolerancia k&lt;/b&gt; (m por raíz de kilómetro) &amp;mdash; cero para ningún veredicto. &lt;b&gt;Distribuir por&lt;/b&gt; &amp;mdash; longitud de la línea o número de estaciones.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Cierre&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Distribución&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;MISCLOSURE&lt;/code&gt; y &lt;code&gt;PERMISSIBLE&lt;/code&gt; en metros, y &lt;code&gt;PASSED&lt;/code&gt; (1, 0, o -1 para no evaluado).&lt;/p&gt;</translation>
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
            <translation>Corrección sobre la incertidumbre de la propia estación</translation>
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
            <translation>Distribución entre estaciones</translation>
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
            <translation>Número de estaciones</translation>
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
            <translation>Estación</translation>
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
            <source>'%1' does not hold a number.</source>
            <translation>'%1' no contiene un número.</translation>
        </message>
        <message>
            <source>'%1' is not a benchmark. Write them as id=height, for example BM1=100.000, and add a tolerance as BM2=103.750±0.002 to hold one with a weight rather than exactly.</source>
            <translation>'%1' no es un punto de referencia. Escríbalos como id=altitud, por ejemplo BM1=100.000, y añada una tolerancia como BM2=103.750±0.002 para fijarlo con peso en lugar de exactamente.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts reduced levelling lines as a one-dimensional network: the same least squares, the same global test, the same data snooping and reliability as any other GeoComp adjustment.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Two weighting models, and the choice is yours.&lt;/b&gt; A reduced line arrives carrying an uncertainty propagated from its staff readings. That figure is rigorous and usually optimistic: it knows nothing of refraction, of staff calibration, or of a tripod settling between backsight and foresight. The &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt; and &lt;code&gt;k &amp;times; &amp;radic;n&lt;/code&gt; models are fitted to lines that suffered all three. Length weighting suits long lines with consistent sight lengths; setup weighting suits short, irregular ones where the per-setup reading error dominates. Leaving both coefficients at zero keeps the propagated uncertainty, and the report says which was used.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Benchmarks&lt;/b&gt; are entered as &lt;code&gt;id=height&lt;/code&gt; pairs, separated by commas or semicolons; add &lt;code&gt;±sigma&lt;/code&gt; to hold one with a weight rather than exactly, for example &lt;code&gt;BM1=100.000, BM2=103.750±0.002&lt;/code&gt;. With none, the network is free, which is often the right thing to adjust first: it shows the observations' internal consistency without a datum's errors mixed in.&lt;/p&gt;&lt;p&gt;Mixing orthometric and ellipsoidal heights without a geoid model is refused. The error would be the geoid undulation &amp;mdash; tens of metres across much of Brazil &amp;mdash; and the result would look entirely reasonable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The report gives relative height uncertainties between pairs of benchmarks&lt;/b&gt;, which is the 1D analogue of the error ellipse and usually the number a levelling network was built to produce. It is not the difference of the two individual uncertainties, because adjusted heights are correlated.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced lines&lt;/b&gt; &amp;mdash; the document a reduction produced. &lt;b&gt;Benchmarks&lt;/b&gt; &amp;mdash; as above. &lt;b&gt;Weighting&lt;/b&gt;, and the coefficient for each model (m per root km, m per root setup); zero means that model is not configured.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Free network&lt;/b&gt; &amp;mdash; ignore the benchmarks and remove the datum defect with an inner constraint.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence&lt;/b&gt;, &lt;b&gt;alpha&lt;/b&gt; and &lt;b&gt;beta&lt;/b&gt; &amp;mdash; for the global test, data snooping and the minimal detectable bias.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Heights&lt;/b&gt; &amp;mdash; CSV.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No map layers.&lt;/b&gt; A levelling network has no planimetry: it determines heights and nothing else, so every station would be drawn at the same point. Use the network algorithm in the Analysis menu on a network document that carries coordinates, or wait for the project store that holds both. Scalars: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt; and &lt;code&gt;WORST_HEIGHT_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta líneas de nivelación reducidas como una red unidimensional: los mismos mínimos cuadrados, la misma prueba global, el mismo data snooping y la misma fiabilidad que cualquier otro ajuste de GeoComp.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dos modelos de ponderación, y la elección es suya.&lt;/b&gt; Una línea reducida llega con una incertidumbre propagada a partir de sus lecturas de mira. Ese valor es riguroso y habitualmente optimista: no sabe nada de la refracción, de la calibración de la mira, ni del asentamiento del trípode entre la espalda y el frente. Los modelos &lt;code&gt;k &amp;times; &amp;radic;L&lt;/code&gt; y &lt;code&gt;k &amp;times; &amp;radic;n&lt;/code&gt; se ajustaron a líneas que sufrieron los tres. La ponderación por longitud conviene a líneas largas con visuales de longitud consistente; la ponderación por estaciones conviene a líneas cortas e irregulares, donde domina el error de lectura por estación. Dejar ambos coeficientes en cero mantiene la incertidumbre propagada, y el informe indica cuál se usó.&lt;/p&gt;&lt;p&gt;Los &lt;b&gt;puntos de referencia&lt;/b&gt; se introducen como pares &lt;code&gt;id=altitud&lt;/code&gt;, separados por comas o puntos y comas; añada &lt;code&gt;±sigma&lt;/code&gt; para fijar uno con peso en lugar de exactamente, por ejemplo &lt;code&gt;BM1=100.000, BM2=103.750±0.002&lt;/code&gt;. Sin ninguno, la red es libre, lo que a menudo es el primer ajuste correcto: muestra la consistencia interna de las observaciones sin los errores de un datum de por medio.&lt;/p&gt;&lt;p&gt;Mezclar altitudes ortométricas y elipsoidales sin un modelo geoidal se rechaza. El error sería la ondulación geoidal &amp;mdash; decenas de metros en gran parte de Brasil &amp;mdash; y el resultado parecería perfectamente razonable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;El informe presenta las incertidumbres relativas de altitud entre pares de referencias&lt;/b&gt;, que son el análogo 1D de la elipse de error y habitualmente el número que una red de nivelación fue construida para producir. No es la diferencia de las dos incertidumbres individuales, porque las altitudes ajustadas están correlacionadas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Líneas reducidas&lt;/b&gt; &amp;mdash; el documento producido por una reducción. &lt;b&gt;Puntos de referencia&lt;/b&gt; &amp;mdash; como arriba. &lt;b&gt;Ponderación&lt;/b&gt;, y el coeficiente de cada modelo (m por raíz de km, m por raíz de estación); cero significa que ese modelo no está configurado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Red libre&lt;/b&gt; &amp;mdash; ignora los puntos de referencia y elimina el defecto de datum con una constricción interna.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confianza&lt;/b&gt;, &lt;b&gt;alfa&lt;/b&gt; y &lt;b&gt;beta&lt;/b&gt; &amp;mdash; para la prueba global, el data snooping y el mínimo error detectable.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Altitudes&lt;/b&gt; &amp;mdash; CSV.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Sin capas de mapa.&lt;/b&gt; Una red de nivelación no tiene planimetría: determina altitudes y nada más, por lo que todas las estaciones se dibujarían en el mismo punto. Use el algoritmo de red del menú Análisis sobre un documento de red que contenga coordenadas, o espere al repositorio de proyecto que contenga ambos. Escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt; y &lt;code&gt;WORST_HEIGHT_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjust levelling lines as a 1D network, by length or setup weighting.</source>
            <translation>Ajusta líneas de nivelación como una red 1D, ponderando por longitud o por número de estaciones.</translation>
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
            <translation>Por el número de estaciones</translation>
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
            <source>Epoch (decimal year)</source>
            <translation>Época (año decimal)</translation>
        </message>
        <message>
            <source>FAILED</source>
            <translation>FALLÓ</translation>
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
            <source>To</source>
            <translation>Hasta</translation>
        </message>
        <message>
            <source>Tolerance coefficient k (m per root km; 0 judges nothing)</source>
            <translation>Coeficiente de tolerancia k (m por raíz de km; 0 no evalúa nada)</translation>
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
            <translation>Incertidumbre por raíz de estación (m)</translation>
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
            <source>&lt;p&gt;Adjusts a geodetic network by least squares using the parametric model, iterating the linearised solution to convergence, and reports the adjusted coordinates with their full covariance matrix, the residuals, and the statistical tests that say whether the result may be believed.&lt;/p&gt;&lt;p&gt;1D, 2D and 3D networks are all supported, free or constrained. The weight matrix is built from the observation covariances, including correlations between the observations of a correlated cluster such as a GNSS baseline.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Non-convergence is reported as a failure&lt;/b&gt;, never returned as a result. A set of coordinates that is really iteration seven of a diverging sequence is worse than no result, because nothing about it says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours; re-adjusting after removing one is a second, explicit run. Automatic iterative rejection deletes real signal, which in deformation monitoring is the very thing being measured.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D. It decides which parameters exist and which observations can contribute.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;i&gt;Constrained&lt;/i&gt; and &lt;i&gt;Fixed&lt;/i&gt; hold the stations the network declares as constrained. &lt;i&gt;Inner constraint&lt;/i&gt; gives a free network whose solution is the trace minimum over all stations. &lt;i&gt;Minimum constraint&lt;/i&gt; does the same over the chosen stations, which is what a deformation analysis needs: holding a station that has itself moved spreads its motion across the network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; comma-separated; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the global test, the w-test and the error ellipses, between 0 and 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared the global test compares against.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Convergence threshold&lt;/b&gt; &amp;mdash; the largest parameter correction accepted as converged, in metres. &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; after which non-convergence is reported.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the decimal year the coordinates refer to. It is recorded on the solution because comparing two epochs is only meaningful when both say which they are.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a JSON document holding the adjusted coordinates, the full covariance matrix, the per-observation results and the provenance. It is the same structure an external engine's result fills, so everything downstream is engine-independent.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; and &lt;b&gt;Residuals&lt;/b&gt; &amp;mdash; CSV tables for a spreadsheet or a model.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Result layers&lt;/b&gt; &amp;mdash; five optional map layers, arriving styled and ready to read (FR-905): adjusted stations sized by their positional uncertainty, error ellipses, observations coloured by what the w-test decided about them, the measured network by observation type, and the coordinate correction vectors. None is created unless asked for, so an adjustment run to feed another algorithm writes nothing extra.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ellipse exaggeration&lt;/b&gt; &amp;mdash; real ellipses are invisible at map scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to the network's own extent. Whatever factor is used is stated in the layer's name, which is what reaches the legend: an unstated exaggeration turns a quality visualisation into a misrepresentation.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta una red geodésica por mínimos cuadrados usando el modelo paramétrico, iterando la solución linealizada hasta la convergencia, e informa de las coordenadas ajustadas con su matriz de covarianzas completa, los residuos y las pruebas estadísticas que dicen si el resultado puede creerse.&lt;/p&gt;&lt;p&gt;Se admiten redes 1D, 2D y 3D, libres o ligadas. La matriz de pesos se construye a partir de las covarianzas de las observaciones, incluidas las correlaciones entre las observaciones de un grupo correlacionado, como una línea base GNSS.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La no convergencia se comunica como un fallo&lt;/b&gt;, nunca se devuelve como resultado. Un conjunto de coordenadas que en realidad es la séptima iteración de una sucesión divergente es peor que ningún resultado, porque nada en él lo indica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya; reajustar tras eliminar una es una segunda ejecución, explícita. El rechazo iterativo automático borra señal real, que en el seguimiento de deformaciones es precisamente lo que se está midiendo.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D o 3D. Decide qué parámetros existen y qué observaciones pueden contribuir.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina el defecto de datum. &lt;i&gt;Ligada&lt;/i&gt; y &lt;i&gt;Fija&lt;/i&gt; mantienen las estaciones que la red declara constreñidas. &lt;i&gt;Constricción interna&lt;/i&gt; da una red libre cuya solución es la traza mínima sobre todas las estaciones. &lt;i&gt;Constricción mínima&lt;/i&gt; hace lo mismo sobre las estaciones elegidas, que es lo que exige un análisis de deformación: mantener una estación que se ha movido reparte su movimiento por toda la red.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Estaciones del datum&lt;/b&gt; &amp;mdash; separadas por comas; vacío significa todas ellas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la prueba global, la prueba w y las elipses de errores, entre 0 y 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Factor de varianza a priori&lt;/b&gt; &amp;mdash; el sigma-cero al cuadrado supuesto con el que compara la prueba global.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbral de convergencia&lt;/b&gt; &amp;mdash; la mayor corrección de parámetro aceptada como convergida, en metros. &lt;b&gt;Número máximo de iteraciones&lt;/b&gt; &amp;mdash; tras el cual se comunica la no convergencia.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significación&lt;/b&gt; y &lt;b&gt;error tipo II&lt;/b&gt; &amp;mdash; alfa y beta para el mínimo error detectable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Época de referencia&lt;/b&gt; &amp;mdash; el año decimal al que se refieren las coordenadas. Se registra en la solución porque comparar dos épocas solo tiene sentido cuando ambas dicen cuáles son.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; un documento JSON con las coordenadas ajustadas, la matriz de covarianzas completa, los resultados por observación y la procedencia. Es la misma estructura que rellena el resultado de un motor externo, de modo que todo lo que viene después es independiente del motor.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; y &lt;b&gt;Residuos&lt;/b&gt; &amp;mdash; tablas CSV para una hoja de cálculo o un modelo.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; y &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Capas de resultado&lt;/b&gt; &amp;mdash; cinco capas opcionales, que llegan con estilo y listas para leer (FR-905): estaciones ajustadas dimensionadas por su incertidumbre posicional, elipses de error, observaciones coloreadas según lo que decidió la prueba w, la red medida por tipo de observación y los vectores de corrección de coordenadas. Ninguna se crea sin solicitarla, de modo que un ajuste ejecutado para alimentar otro algoritmo no escribe nada de más.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exageración de las elipses&lt;/b&gt; &amp;mdash; las elipses reales son invisibles a escala de mapa, por lo que se dibujan ampliadas. Déjelo en 0 y se ajusta un factor a la propia extensión de la red. Sea cual sea el factor utilizado, se declara en el nombre de la capa, que es lo que llega a la leyenda: una exageración no declarada convierte una visualización de calidad en una tergiversación.&lt;/p&gt;</translation>
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
            <translation>Defecto de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1 (removed by: %2).</source>
            <translation>Defecto de datum: %1 (eliminado por: %2).</translation>
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
            <translation>Mínimo error detectable</translation>
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
            <source>Reference epoch (decimal year)</source>
            <translation>Época de referencia (año decimal)</translation>
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
            <translation>Significación para el mínimo error detectable</translation>
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
            <translation>Error tipo II para el mínimo error detectable</translation>
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
            <translation>&lt;p&gt;Calcula lo que alcanzaría una red &lt;i&gt;planificada&lt;/i&gt;. La covarianza de las coordenadas ajustadas depende únicamente de la geometría de las observaciones planificadas y de sus precisiones supuestas, por lo que puede calcularse antes de realizar la primera observación.&lt;/p&gt;&lt;p&gt;Las observaciones planificadas necesitan, por tanto, solo un tipo, las estaciones que enlazan y una desviación típica supuesta. Cualesquiera valores que lleven se ignoran, y por eso la simulación es exacta y no aproximada.&lt;/p&gt;&lt;p&gt;Se comunican dos cosas, y ambas importan. &lt;b&gt;Precisión&lt;/b&gt; &amp;mdash; la elipse de errores y la incertidumbre posicional esperadas de cada estación. &lt;b&gt;Fiabilidad&lt;/b&gt; &amp;mdash; el menor error grosero que el diseño podría detectar en cada observación, y el efecto sobre las coordenadas de uno que pasara inadvertido. Un diseño puede ser preciso y aun así incapaz de detectar un error grosero en ningún sitio, de modo que comunicar solo la precisión da la mitad de la respuesta.&lt;/p&gt;&lt;p&gt;Por omisión el datum se define mediante constricciones internas, porque un diseño debe juzgarse por su propia geometría y no a través de la distorsión que impone una estación fija concreta.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON) que describe las estaciones y observaciones planificadas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D o 3D.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina el defecto de datum. &lt;b&gt;Estaciones del datum&lt;/b&gt; &amp;mdash; para una solución con constricción mínima, las estaciones, separadas por comas, sobre las que se define el datum; vacío significa todas ellas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Incertidumbre posicional exigida&lt;/b&gt; &amp;mdash; la especificación que el diseño debe cumplir, en metros, al nivel de confianza indicado. Déjela en 0 para informar sin juzgar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para las elipses de errores, entre 0 y 1. &lt;b&gt;Factor de varianza a priori&lt;/b&gt; &amp;mdash; el sigma-cero al cuadrado supuesto. &lt;b&gt;Significación&lt;/b&gt; y &lt;b&gt;error tipo II&lt;/b&gt; &amp;mdash; alfa y beta para el mínimo error detectable; los valores geodésicos habituales 0,001 y 0,20 dan el familiar parámetro de no centralidad 4,13.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;MEETS_TOLERANCE&lt;/code&gt;, &lt;code&gt;WORST_STATION&lt;/code&gt;, &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt; y &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; &amp;mdash; observaciones en las que ningún error grosero podría detectarse jamás.&lt;/p&gt;</translation>
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
            <translation>Defecto de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1</source>
            <translation>Defecto de datum: %1</translation>
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
            <translation>Mínimo error detectable</translation>
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
            <translation>Significación para el mínimo error detectable</translation>
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
            <translation>El mínimo error detectable es el menor error grosero que el diseño podría encontrar en una observación, con la significación y la potencia indicadas.</translation>
        </message>
        <message>
            <source>Type II error for the minimal detectable bias</source>
            <translation>Error tipo II para el mínimo error detectable</translation>
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
            <translation>&lt;p&gt;Calcula coordenadas tridimensionales para cada punto que un estacionamiento visó, a partir de la dirección reducida, el ángulo cenital, la distancia inclinada, las dos alturas y la orientación del estacionamiento. La radiación por lotes de muchos puntos de detalle desde un estacionamiento es el caso rutinario de producción y es para lo que esto está construido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La matriz de covarianzas 3&amp;times;3 completa es el resultado, no un extra.&lt;/b&gt; Las tres coordenadas provienen de una sola visual y están fuertemente correlacionadas por ella, y tratarlas como independientes es incorrecto. El CSV lleva la covarianza, de modo que nada aguas abajo tenga que suponer lo contrario.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La orientación se deriva de las propias visuales siempre que es posible.&lt;/b&gt; Cualquier objetivo cuyas coordenadas se conozcan da directamente la orientación del estacionamiento, que es como un topógrafo orienta uno: visa un punto conocido y todo lo demás se sigue. Donde se conocen varios, las orientaciones que implican se promedian circularmente y se comunica su dispersión &amp;mdash; una dispersión grande significa que uno de los puntos conocidos no está donde debería. Donde no se conoce ninguno, la orientación debe indicarse explícitamente.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Estaciones conocidas&lt;/b&gt; &amp;mdash; un objeto JSON que asocia nombres de estaciones a &lt;code&gt;[E, N, altitud]&lt;/code&gt; en metros. Un estacionamiento debe aparecer aquí para que sus puntos se radien.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Orientaciones&lt;/b&gt; &amp;mdash; un objeto JSON opcional que asocia un estacionamiento a su orientación en grados, para estacionamientos que no visaron ningún punto conocido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura del instrumento&lt;/b&gt; y &lt;b&gt;altura del objetivo&lt;/b&gt; (m) &amp;mdash; usadas donde las lecturas no llevan las suyas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Correlación distancia/cenital&lt;/b&gt; &amp;mdash; entre -1 y 1, o -2 para desconocida, que se registra como una suposición en lugar de tratarse en silencio como cero.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Puntos&lt;/b&gt; &amp;mdash; JSON, con el formato que la Red clásica toma como coordenadas aproximadas. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Tabla de puntos&lt;/b&gt; &amp;mdash; CSV con la covarianza completa. Escalares: &lt;code&gt;POINT_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
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
            <translation>Altura del objetivo (m)</translation>
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
            <translation>&lt;p&gt;Calcula desniveles a partir de los ángulos cenitales y las distancias inclinadas reducidos, con la corrección de curvatura y refracción aplicada y su incertidumbre propagada. En una visual de 100 m la corrección es de 0,7 mm; en 1 km es de 68 mm; en 5 km es de 1,7 m.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radial&lt;/b&gt; calcula un desnivel de la estación ocupada a cada objetivo que visó. La altura del instrumento, la altura del objetivo y la refracción contribuyen todas íntegramente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Leap-frog&lt;/b&gt; toma cada estacionamiento que visó exactamente dos objetivos como una estación libre entre ellos, y produce un desnivel del primero al segundo. Dos cosas se cancelan entonces. La &lt;b&gt;altura del instrumento se cancela exactamente&lt;/b&gt; y nunca hay que medirla, lo cual elimina lo que es habitualmente el error dominante en un desnivel trigonométrico corto. Y la &lt;b&gt;refracción se cancela en gran parte&lt;/b&gt;, porque ambas visuales atraviesan el mismo aire en el mismo instante y comparten un coeficiente &amp;mdash; una dependencia compartida conducida por un único jacobiano, de modo que la cancelación aparece en la incertidumbre y no solo en el valor. Con visuales equilibradas la incertidumbre de la refracción abandona el resultado por completo.&lt;/p&gt;&lt;p&gt;Cuánto se cancela depende de lo iguales que sean las dos visuales, lo cual el topógrafo controla por dónde se sitúa, de modo que un par desequilibrado se comunica junto con la fracción de la incertidumbre de la refracción que sobrevivió.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado. &lt;b&gt;Modo&lt;/b&gt; &amp;mdash; radial o leap-frog.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura del instrumento&lt;/b&gt; y &lt;b&gt;altura del objetivo&lt;/b&gt; (m) &amp;mdash; usadas en modo radial donde las lecturas no llevan las suyas. Ignoradas en modo leap-frog, donde la altura del instrumento se cancela.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coeficiente de refracción&lt;/b&gt; y su &lt;b&gt;incertidumbre&lt;/b&gt; &amp;mdash; adimensionales. El coeficiente es mal conocido y varía a lo largo del día, y es la fuente de error dominante en visuales largas, razón por la cual su incertidumbre es una entrada y no una suposición.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radio de la Tierra&lt;/b&gt; (m) y &lt;b&gt;tolerancia de desequilibrio de las visuales&lt;/b&gt; (como fracción de la visual más larga).&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Desniveles&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;RESULT_COUNT&lt;/code&gt; y &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; en metros.&lt;/p&gt;</translation>
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
            <translation>Altura del objetivo (m)</translation>
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
            <translation>&lt;p&gt;Copia un conjunto de datos de referencia que se distribuye con GeoComp a un directorio de su elección, junto con su tutorial. El propio directorio del complemento no suele ser escribible, y las salidas tienen que ir a algún sitio.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RD-01&lt;/b&gt; es el triángulo de estación total del propio autor: tres estaciones, seis visuales, cada una observada en las dos posiciones del anteojo. Es el levantamiento completo más pequeño que existe y ejercita toda la cadena de estación total, de la libreta de campo a la red ajustada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Contiene dos errores reales, y ese es precisamente el objetivo.&lt;/b&gt; Un par de posiciones discrepa exactamente 1,000 m en la distancia &amp;mdash; un error de transcripción, que el preprocesamiento bloquea en lugar de diluirlo en la media. Y la prueba global de la red falla, correctamente: las distancias discrepan entre ambos extremos mucho más de lo que permite la precisión declarada del instrumento. Un tutorial en el que nada está mal enseña qué botones pulsar; este enseña para qué sirve el programa.&lt;/p&gt;&lt;p&gt;El &lt;code&gt;README.md&lt;/code&gt; copiado recorre toda la cadena y explica ambos casos, junto con por qué una red sin punto conocido y sin acimut solo puede ajustarse con constricciones internas.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Conjunto de datos&lt;/b&gt; &amp;mdash; cuál instalar. &lt;b&gt;Carpeta de destino&lt;/b&gt; &amp;mdash; dónde ponerlo; dentro se crea una subcarpeta con el nombre del conjunto. &lt;b&gt;Sobrescribir&lt;/b&gt; &amp;mdash; reemplazar los archivos ya presentes, desactivado por defecto para no perder un archivo de tutorial editado.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;OUTPUT_DIRECTORY&lt;/code&gt; &amp;mdash; dónde quedaron los archivos. &lt;code&gt;FILE_COUNT&lt;/code&gt; &amp;mdash; cuántos se copiaron.&lt;/p&gt;</translation>
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
