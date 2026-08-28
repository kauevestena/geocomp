<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="es">
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
            <source>Engine integration arrives in later development phases.</source>
            <translation>La integración con los motores de procesamiento llegará en fases posteriores del desarrollo.</translation>
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
            <source>Adjusted coordinates</source>
            <translation>Coordenadas ajustadas</translation>
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
            <source>Every observation in this adjustment is checkable.</source>
            <translation>Todas las observaciones de este ajuste son verificables.</translation>
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
            <source>FAILED</source>
            <translation>FALLÓ</translation>
        </message>
        <message>
            <source>Field</source>
            <translation>Campo</translation>
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
            <source>GeoComp in-house core</source>
            <translation>Núcleo propio de GeoComp</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Prueba global</translation>
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
            <source>Lower critical</source>
            <translation>Crítico inferior</translation>
        </message>
        <message>
            <source>MDB</source>
            <translation>MDB</translation>
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
            <source>Orientation (rad)</source>
            <translation>Orientación (rad)</translation>
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
            <source>Results</source>
            <translation>Resultados</translation>
        </message>
        <message>
            <source>Row</source>
            <translation>Fila</translation>
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
            <source>Superseded by</source>
            <translation>Sustituida por</translation>
        </message>
        <message>
            <source>Test</source>
            <translation>Prueba</translation>
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
            <source>Uncertainty</source>
            <translation>Incertidumbre</translation>
        </message>
        <message>
            <source>Uncertainty mode</source>
            <translation>Modo de incertidumbre</translation>
        </message>
        <message>
            <source>Uncheckable observations</source>
            <translation>Observaciones no verificables</translation>
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
            <source>What a failed global test means</source>
            <translation>Qué significa una prueba global fallida</translation>
        </message>
        <message>
            <source>Where each value came from</source>
            <translation>De dónde vino cada valor</translation>
        </message>
        <message>
            <source>accepted</source>
            <translation>aceptada</translation>
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
            <source>Requirement</source>
            <translation>Requisito</translation>
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
            <source>Coordinate corrections (%1)</source>
            <translation>Correcciones de coordenadas (%1)</translation>
        </message>
        <message>
            <source>Coordinate corrections (layer)</source>
            <translation>Correcciones de coordenadas (capa)</translation>
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
            <source>Error ellipses (%1)</source>
            <translation>Elipses de error (%1)</translation>
        </message>
        <message>
            <source>Error ellipses (layer)</source>
            <translation>Elipses de error (capa)</translation>
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
            <source>Residuals</source>
            <translation>Residuos</translation>
        </message>
        <message>
            <source>Residuals (layer)</source>
            <translation>Residuos (capa)</translation>
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
            <source>Total Station</source>
            <translation>Estación Total</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMessages</name>
        <message>
            <source>(not set)</source>
            <translation>(no definido)</translation>
        </message>
        <message>
            <source>Correlated cluster '%1' supplies %2 observation rows but a %3 covariance matrix. The two must agree, in the same order.</source>
            <translation>El grupo correlacionado '%1' aporta %2 filas de observación pero una matriz de covarianzas %3. Ambos deben coincidir, en el mismo orden.</translation>
        </message>
        <message>
            <source>Every station in this network is held fixed, so there is nothing to estimate. %1</source>
            <translation>Todas las estaciones de esta red están fijas, por lo que no hay nada que estimar. %1</translation>
        </message>
        <message>
            <source>GeoComp could not complete the operation (%1). See the GeoComp tab of the Log Messages panel for details.</source>
            <translation>GeoComp no pudo completar la operación (%1). Consulte la pestaña GeoComp del panel Mensajes de Registro para más detalles.</translation>
        </message>
        <message>
            <source>No observations were supplied. %1</source>
            <translation>No se suministró ninguna observación. %1</translation>
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
            <source>Station '%1' has no approximate %2, and the linearised adjustment needs a point to linearise about. Supply approximate coordinates, or generate them from the observations.</source>
            <translation>La estación '%1' no tiene %2 aproximada, y el ajuste linealizado necesita un punto en torno al cual linealizar. Proporcione coordenadas aproximadas, o genérelas a partir de las observaciones.</translation>
        </message>
        <message>
            <source>Station '%1' is held fixed but carries no position, so there is no value to hold it at. Give it coordinates, or release the constraint.</source>
            <translation>La estación '%1' está fija pero no tiene posición, por lo que no hay valor en el que mantenerla. Asígnele coordenadas, o libere la constricción.</translation>
        </message>
        <message>
            <source>The '%1' engine is required for this operation but is not installed. Install it from Global Settings, under Paths and engines.</source>
            <translation>El motor '%1' es necesario para esta operación, pero no está instalado. Instálelo desde Configuraciones Globales, en Rutas y motores.</translation>
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
            <source>The datum constraints do not remove the network's remaining freedom (%1 constraint(s) applied). Check that the stations defining the datum are enough to fix it.</source>
            <translation>Las constricciones de datum no eliminan la libertad restante de la red (%1 constricción(es) aplicada(s)). Compruebe que las estaciones que definen el datum bastan para fijarlo.</translation>
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
            <source>The planned network '%1' contains no observations, so there is no design to evaluate. Add the observations you intend to make, with their assumed precisions.</source>
            <translation>La red planificada '%1' no contiene observaciones, por lo que no hay diseño que evaluar. Añada las observaciones que pretende realizar, con sus precisiones supuestas.</translation>
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
            <source>This JSON file is not a GeoComp network document: it has no network identifier. Expected %1.</source>
            <translation>Este archivo JSON no es un documento de red de GeoComp: no tiene identificador de red. Se esperaba: %1.</translation>
        </message>
        <message>
            <source>This file does not hold a GeoComp network: its top level is %1, and a network document is a JSON object. Check that you chose the right file.</source>
            <translation>Este archivo no contiene una red de GeoComp: su nivel superior es %1, y un documento de red es un objeto JSON. Compruebe que ha elegido el archivo correcto.</translation>
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
        <name>GeoCompSettings</name>
        <message>
            <source>(not editable in this version)</source>
            <translation>(no editable en esta versión)</translation>
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
            <source>Basic</source>
            <translation>Básico</translation>
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
            <source>Default height-difference standard deviation (m)</source>
            <translation>Desviación típica de los desniveles (m)</translation>
        </message>
        <message>
            <source>Default pressure (hPa)</source>
            <translation>Presión por defecto (hPa)</translation>
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
            <source>English</source>
            <translation>Inglés</translation>
        </message>
        <message>
            <source>Español</source>
            <translation>Español</translation>
        </message>
        <message>
            <source>Face-pair distance tolerance (m)</source>
            <translation>Tolerancia de distancia entre las dos posiciones del anteojo (m)</translation>
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
            <source>Height-difference weighting</source>
            <translation>Ponderación de los desniveles</translation>
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
            <source>Least squares</source>
            <translation>Mínimos cuadrados</translation>
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
            <source>Metre</source>
            <translation>Metro</translation>
        </message>
        <message>
            <source>No settings in this section yet. They are added by the development phase that implements this equipment type.</source>
            <translation>Todavía no hay configuraciones en esta sección. Se añaden en la fase de desarrollo que implementa este tipo de equipo.</translation>
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
            <source>Reference systems</source>
            <translation>Sistemas de referencia</translation>
        </message>
        <message>
            <source>Required relative precision (1:N)</source>
            <translation>Precisión relativa exigida (1:N)</translation>
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
            <source>this project</source>
            <translation>este proyecto</translation>
        </message>
        <message>
            <source>this run</source>
            <translation>esta ejecución</translation>
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
            <source>Ellipse azimuth (°)</source>
            <translation>Acimut de la elipse (°)</translation>
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
            <source>Residual (")</source>
            <translation>Residuo (")</translation>
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
            <source>Adjusted heights</source>
            <translation>Altitudes ajustadas</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
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
            <source>Confidence level</source>
            <translation>Nivel de confianza</translation>
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
            <source>Levelling network adjustment</source>
            <translation>Ajuste de red de nivelación</translation>
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
            <source>The relative uncertainty is the 1D analogue of the relative error ellipse, and is usually what a levelling network was built to produce. It is not the difference of the two individual uncertainties: adjusted heights are correlated, and two marks at the ends of one well-observed line know their separation far better than either knows its own height.</source>
            <translation>La incertidumbre relativa es el análogo 1D de la elipse de error relativa y suele ser lo que una red de nivelación fue construida para producir. No es la diferencia de las dos incertidumbres individuales: las altitudes ajustadas están correlacionadas, y dos referencias en los extremos de una línea bien observada conocen su separación mucho mejor de lo que cualquiera de ellas conoce su propia altitud.</translation>
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
            <source>Weighting</source>
            <translation>Ponderación</translation>
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
            <source>Azimuth (rad)</source>
            <translation>Acimut (rad)</translation>
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
            <source>Collimation spread (")</source>
            <translation>Dispersión de la colimación (")</translation>
        </message>
        <message>
            <source>Collimation tolerance (rad)</source>
            <translation>Tolerancia de la colimación (rad)</translation>
        </message>
        <message>
            <source>Direction (°)</source>
            <translation>Dirección (°)</translation>
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
            <source>Height difference (m)</source>
            <translation>Desnivel (m)</translation>
        </message>
        <message>
            <source>Horizontal distance (m)</source>
            <translation>Distancia horizontal (m)</translation>
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
            <source>Mean collimation (")</source>
            <translation>Colimación media (")</translation>
        </message>
        <message>
            <source>Mean index error (")</source>
            <translation>Error de índice medio (")</translation>
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
            <source>Zenith (°)</source>
            <translation>Cenital (°)</translation>
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
            <source>Orientation (°)</source>
            <translation>Orientación (°)</translation>
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
            <source>Spread (")</source>
            <translation>Dispersión (")</translation>
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
            <source>The known points sighted from '%1' imply orientations spread over %2 arcsec, against %3 expected from the pointing precision. One of them is probably not where it is recorded, and every point radiated from this setup carries that error.</source>
            <translation>Los puntos conocidos visados desde '%1' implican orientaciones con una dispersión de %2 segundos de arco, frente a %3 esperados por la precisión de la puntería. Probablemente uno de ellos no está donde figura, y todo punto radiado desde esta estación arrastra ese error.</translation>
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
            <source>Residual (")</source>
            <translation>Residuo (")</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Residuos</translation>
        </message>
        <message>
            <source>Setup orientation (°)</source>
            <translation>Orientación del estacionamiento (°)</translation>
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
            <source>Arrives in phase P6</source>
            <translation>Llega en la fase P6</translation>
        </message>
        <message>
            <source>Arrives in phase P7</source>
            <translation>Llega en la fase P7</translation>
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
            <source>Not integrated yet</source>
            <translation>Aún no integrado</translation>
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
            <source>Angular misclosure %1 arcsec.</source>
            <translation>Error angular de cierre %1 segundos de arco.</translation>
        </message>
        <message>
            <source>Angular misclosure (")</source>
            <translation>Error angular de cierre (")</translation>
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
            <source>Perimeter %1 m.</source>
            <translation>Perímetro %1 m.</translation>
        </message>
        <message>
            <source>Perimeter (m)</source>
            <translation>Perímetro (m)</translation>
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
            <source>Height difference (m)</source>
            <translation>Desnivel (m)</translation>
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
            <source>Sight imbalance tolerance</source>
            <translation>Tolerancia de desequilibrio de las visuales</translation>
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
