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
            <source>&lt;p&gt;Assembles the reduced pointings into a geodetic network and adjusts it by least squares, with the global test, data snooping and reliability analysis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulation, trilateration and triangulateration are not three different computations.&lt;/b&gt; They are one adjustment over three different observation sets, and which one a survey is depends on what was measured. This algorithm adjusts whatever the pointings contain.&lt;/p&gt;&lt;p&gt;Free and constrained solutions are both available, which is the comparison between &lt;i&gt;redes livres&lt;/i&gt; and &lt;i&gt;redes amarradas&lt;/i&gt; the research project names as a teaching goal. A free network is adjusted with inner constraints and is the honest choice when nothing external orients or positions the survey.&lt;/p&gt;&lt;p&gt;The network document is written out as well as the solution, so the chain &lt;i&gt;pre-process &amp;rarr; build &amp;rarr; inspect &amp;rarr; adjust&lt;/i&gt; can be assembled in the graphical modeller using the Analysis algorithms.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Approximate coordinates&lt;/b&gt; &amp;mdash; a JSON object mapping each station to &lt;code&gt;[easting, northing, up]&lt;/code&gt;. Required, not derived: the linearised model needs a point to linearise about, and a traverse or a resection is how a surveyor obtains one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimension&lt;/b&gt; &amp;mdash; which of 2D, 3D and 1D to adjust in. It decides which reduced quantities become observations: a 2D adjustment takes directions and horizontal distances, a 3D one takes directions, zenith angles and slope distances. Emitting all of them would use the same measurement twice.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;b&gt;Fixed stations&lt;/b&gt; &amp;mdash; comma-separated; their approximate coordinates are held exactly.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt;, &lt;b&gt;reference epoch&lt;/b&gt; and &lt;b&gt;CRS&lt;/b&gt; &amp;mdash; recorded on the solution.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; and &lt;b&gt;Solution&lt;/b&gt; &amp;mdash; JSON documents; the first feeds the Analysis algorithms, the second holds the adjusted coordinates with their full covariance and provenance. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; and &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Reúne las visuales reducidas en una red geodésica y la ajusta por mínimos cuadrados, con la prueba global, el data snooping y el análisis de fiabilidad.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulación, trilateración y triangulateración no son tres cálculos distintos.&lt;/b&gt; Son un único ajuste sobre tres conjuntos de observaciones distintos, y cuál de ellos es un levantamiento depende de lo que se midió. Este algoritmo ajusta lo que contengan las visuales.&lt;/p&gt;&lt;p&gt;Las soluciones libres y ligadas están ambas disponibles, que es la comparación entre &lt;i&gt;redes libres&lt;/i&gt; y &lt;i&gt;redes ligadas&lt;/i&gt; que el proyecto de investigación nombra como objetivo pedagógico. Una red libre se ajusta con constricciones internas y es la elección honesta cuando nada externo orienta o posiciona el levantamiento.&lt;/p&gt;&lt;p&gt;El documento de la red se escribe además de la solución, de modo que la cadena &lt;i&gt;preprocesar &amp;rarr; construir &amp;rarr; inspeccionar &amp;rarr; ajustar&lt;/i&gt; pueda montarse en el modelador gráfico usando los algoritmos de Análisis.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observaciones reducidas&lt;/b&gt; &amp;mdash; el documento producido por el Preprocesamiento generalizado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordenadas aproximadas&lt;/b&gt; &amp;mdash; un objeto JSON que asocia cada estación a &lt;code&gt;[E, N, altitud]&lt;/code&gt;. Exigidas, no derivadas: el modelo linealizado necesita un punto en torno al cual linealizar, y una poligonal o una intersección inversa es como un topógrafo lo obtiene.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimensión&lt;/b&gt; &amp;mdash; en cuál de 2D, 3D y 1D ajustar. Ello decide qué magnitudes reducidas se convierten en observaciones: un ajuste 2D toma direcciones y distancias horizontales, uno 3D toma direcciones, ángulos cenitales y distancias inclinadas. Emitirlas todas usaría la misma medida dos veces.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina el defecto de datum. &lt;b&gt;Estaciones fijas&lt;/b&gt; &amp;mdash; separadas por comas; sus coordenadas aproximadas se mantienen exactamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt;, &lt;b&gt;época de referencia&lt;/b&gt; y &lt;b&gt;SRC&lt;/b&gt; &amp;mdash; registrados en la solución.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; y &lt;b&gt;Solución&lt;/b&gt; &amp;mdash; documentos JSON; el primero alimenta los algoritmos de Análisis, el segundo contiene las coordenadas ajustadas con su matriz de covarianzas completa y la procedencia. &lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; y &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
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
            <source>CRS authority code</source>
            <translation>Código del SRC</translation>
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
            <source>That file is not a GeoComp reductions document. Run Generalised pre-processing first, or choose the file it produced.</source>
            <translation>Ese archivo no es un documento de reducciones de GeoComp. Ejecute primero el Preprocesamiento generalizado, o elija el archivo que produjo.</translation>
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
            <source>Basic</source>
            <translation>Básico</translation>
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
            <source>Level</source>
            <translation>Nivel</translation>
        </message>
        <message>
            <source>Log verbosity</source>
            <translation>Detalle del registro</translation>
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
            <source>Paths and engines</source>
            <translation>Rutas y motores</translation>
        </message>
        <message>
            <source>Português (Brasil)</source>
            <translation>Portugués (Brasil)</translation>
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
            <source>US survey foot</source>
            <translation>Pie topográfico estadounidense</translation>
        </message>
        <message>
            <source>Usage mode</source>
            <translation>Modo de uso</translation>
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
        <name>NetworkAdjustAlgorithm</name>
        <message>
            <source>%1 observation(s) exceed the w-test critical value.</source>
            <translation>%1 observación(es) supera(n) el valor crítico de la prueba w.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts a geodetic network by least squares using the parametric model, iterating the linearised solution to convergence, and reports the adjusted coordinates with their full covariance matrix, the residuals, and the statistical tests that say whether the result may be believed.&lt;/p&gt;&lt;p&gt;1D, 2D and 3D networks are all supported, free or constrained. The weight matrix is built from the observation covariances, including correlations between the observations of a correlated cluster such as a GNSS baseline.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Non-convergence is reported as a failure&lt;/b&gt;, never returned as a result. A set of coordinates that is really iteration seven of a diverging sequence is worse than no result, because nothing about it says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours; re-adjusting after removing one is a second, explicit run. Automatic iterative rejection deletes real signal, which in deformation monitoring is the very thing being measured.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D. It decides which parameters exist and which observations can contribute.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;i&gt;Constrained&lt;/i&gt; and &lt;i&gt;Fixed&lt;/i&gt; hold the stations the network declares as constrained. &lt;i&gt;Inner constraint&lt;/i&gt; gives a free network whose solution is the trace minimum over all stations. &lt;i&gt;Minimum constraint&lt;/i&gt; does the same over the chosen stations, which is what a deformation analysis needs: holding a station that has itself moved spreads its motion across the network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; comma-separated; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the global test, the w-test and the error ellipses, between 0 and 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared the global test compares against.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Convergence threshold&lt;/b&gt; &amp;mdash; the largest parameter correction accepted as converged, in metres. &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; after which non-convergence is reported.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the decimal year the coordinates refer to. It is recorded on the solution because comparing two epochs is only meaningful when both say which they are.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a JSON document holding the adjusted coordinates, the full covariance matrix, the per-observation results and the provenance. It is the same structure an external engine's result fills, so everything downstream is engine-independent.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; and &lt;b&gt;Residuals&lt;/b&gt; &amp;mdash; CSV tables for a spreadsheet or a model.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta una red geodésica por mínimos cuadrados usando el modelo paramétrico, iterando la solución linealizada hasta la convergencia, e informa de las coordenadas ajustadas con su matriz de covarianzas completa, los residuos y las pruebas estadísticas que dicen si el resultado puede creerse.&lt;/p&gt;&lt;p&gt;Se admiten redes 1D, 2D y 3D, libres o ligadas. La matriz de pesos se construye a partir de las covarianzas de las observaciones, incluidas las correlaciones entre las observaciones de un grupo correlacionado, como una línea base GNSS.&lt;/p&gt;&lt;p&gt;&lt;b&gt;La no convergencia se comunica como un fallo&lt;/b&gt;, nunca se devuelve como resultado. Un conjunto de coordenadas que en realidad es la séptima iteración de una sucesión divergente es peor que ningún resultado, porque nada en él lo indica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ninguna observación se rechaza automáticamente.&lt;/b&gt; El data snooping informa de candidatas y la decisión es suya; reajustar tras eliminar una es una segunda ejecución, explícita. El rechazo iterativo automático borra señal real, que en el seguimiento de deformaciones es precisamente lo que se está midiendo.&lt;/p&gt;&lt;h3&gt;Parámetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Red&lt;/b&gt; &amp;mdash; un documento de red de GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Marco de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D o 3D. Decide qué parámetros existen y qué observaciones pueden contribuir.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definición del datum&lt;/b&gt; &amp;mdash; cómo se elimina el defecto de datum. &lt;i&gt;Ligada&lt;/i&gt; y &lt;i&gt;Fija&lt;/i&gt; mantienen las estaciones que la red declara constreñidas. &lt;i&gt;Constricción interna&lt;/i&gt; da una red libre cuya solución es la traza mínima sobre todas las estaciones. &lt;i&gt;Constricción mínima&lt;/i&gt; hace lo mismo sobre las estaciones elegidas, que es lo que exige un análisis de deformación: mantener una estación que se ha movido reparte su movimiento por toda la red.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Estaciones del datum&lt;/b&gt; &amp;mdash; separadas por comas; vacío significa todas ellas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nivel de confianza&lt;/b&gt; &amp;mdash; para la prueba global, la prueba w y las elipses de errores, entre 0 y 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Factor de varianza a priori&lt;/b&gt; &amp;mdash; el sigma-cero al cuadrado supuesto con el que compara la prueba global.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Umbral de convergencia&lt;/b&gt; &amp;mdash; la mayor corrección de parámetro aceptada como convergida, en metros. &lt;b&gt;Número máximo de iteraciones&lt;/b&gt; &amp;mdash; tras el cual se comunica la no convergencia.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significación&lt;/b&gt; y &lt;b&gt;error tipo II&lt;/b&gt; &amp;mdash; alfa y beta para el mínimo error detectable.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Época de referencia&lt;/b&gt; &amp;mdash; el año decimal al que se refieren las coordenadas. Se registra en la solución porque comparar dos épocas solo tiene sentido cuando ambas dicen cuáles son.&lt;/p&gt;&lt;h3&gt;Salidas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solución&lt;/b&gt; &amp;mdash; un documento JSON con las coordenadas ajustadas, la matriz de covarianzas completa, los resultados por observación y la procedencia. Es la misma estructura que rellena el resultado de un motor externo, de modo que todo lo que viene después es independiente del motor.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Informe&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estaciones ajustadas&lt;/b&gt; y &lt;b&gt;Residuos&lt;/b&gt; &amp;mdash; tablas CSV para una hoja de cálculo o un modelo.&lt;/p&gt;&lt;p&gt;Salidas escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; y &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
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
</TS>
