<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="pt_BR">
    <context>
        <name>ClassicalNetworkAlgorithm</name>
        <message>
            <source>%1 observation(s) exceed the w-test critical value; none was rejected.</source>
            <translation>%1 observação(ões) excede(m) o valor crítico do teste w; nenhuma foi rejeitada.</translation>
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
            <translation>&lt;p&gt;Reúne as visadas reduzidas em uma rede geodésica e a ajusta por mínimos quadrados, com o teste global, o data snooping e a análise de confiabilidade.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Triangulação, trilateração e triangulateração não são três cálculos diferentes.&lt;/b&gt; São um único ajustamento sobre três conjuntos de observações diferentes, e qual deles um levantamento é depende do que foi medido. Este algoritmo ajusta o que quer que as visadas contenham.&lt;/p&gt;&lt;p&gt;Soluções livres e amarradas estão ambas disponíveis, que é a comparação entre &lt;i&gt;redes livres&lt;/i&gt; e &lt;i&gt;redes amarradas&lt;/i&gt; que o projeto de pesquisa nomeia como objetivo pedagógico. Uma rede livre é ajustada com injunções internas e é a escolha honesta quando nada externo orienta ou posiciona o levantamento.&lt;/p&gt;&lt;p&gt;O documento da rede é gravado além da solução, de modo que a cadeia &lt;i&gt;pré-processar &amp;rarr; construir &amp;rarr; inspecionar &amp;rarr; ajustar&lt;/i&gt; possa ser montada no modelador gráfico usando os algoritmos de Análise.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nenhuma observação é rejeitada automaticamente.&lt;/b&gt; O data snooping relata candidatas e a decisão é sua.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; o documento produzido pelo Pré-processamento generalizado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordenadas aproximadas&lt;/b&gt; &amp;mdash; um objeto JSON associando cada estação a &lt;code&gt;[E, N, altitude]&lt;/code&gt;. Exigidas, não derivadas: o modelo linearizado precisa de um ponto em torno do qual linearizar, e uma poligonal ou uma interseção inversa é como um topógrafo o obtém.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Dimensão&lt;/b&gt; &amp;mdash; em qual de 2D, 3D e 1D ajustar. Isso decide quais grandezas reduzidas se tornam observações: um ajustamento 2D toma direções e distâncias horizontais, um 3D toma direções, ângulos zenitais e distâncias inclinadas. Emitir todas elas usaria a mesma medida duas vezes.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definição do datum&lt;/b&gt; &amp;mdash; como o defeito de datum é removido. &lt;b&gt;Estações fixas&lt;/b&gt; &amp;mdash; separadas por vírgula; suas coordenadas aproximadas são mantidas exatamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nível de confiança&lt;/b&gt;, &lt;b&gt;época de referência&lt;/b&gt; e &lt;b&gt;SRC&lt;/b&gt; &amp;mdash; registrados na solução.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Rede&lt;/b&gt; e &lt;b&gt;Solução&lt;/b&gt; &amp;mdash; documentos JSON; o primeiro alimenta os algoritmos de Análise, o segundo contém as coordenadas ajustadas com sua matriz de covariâncias completa e a proveniência. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estações ajustadas&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;VARIANCE_FACTOR&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt; e &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Camadas de resultado&lt;/b&gt; &amp;mdash; cinco camadas opcionais, que chegam estilizadas e prontas para leitura (FR-905): estações ajustadas dimensionadas pela sua incerteza posicional, elipses de erro, observações coloridas conforme a decisão do teste w, a rede medida por tipo de observação e os vetores de correção de coordenadas. Nenhuma é criada sem ser solicitada, de modo que um ajustamento executado para alimentar outro algoritmo não escreve nada a mais.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exagero das elipses&lt;/b&gt; &amp;mdash; elipses reais são invisíveis na escala do mapa, por isso são desenhadas ampliadas. Deixe em 0 e um fator é ajustado à própria extensão da rede. Qualquer que seja o fator usado, ele é declarado no nome da camada, que é o que chega à legenda: um exagero não declarado transforma uma visualização de qualidade em uma representação enganosa.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estações ajustadas</translation>
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
            <translation>As coordenadas aproximadas da estação '%1' não são três números.</translation>
        </message>
        <message>
            <source>Build a triangulation, trilateration or triangulateration network from reduced pointings and adjust it.</source>
            <translation>Constrói uma rede de triangulação, trilateração ou triangulateração a partir das visadas reduzidas e a ajusta.</translation>
        </message>
        <message>
            <source>CRS authority code</source>
            <translation>Código do SRC</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Classical network</source>
            <translation>Rede clássica</translation>
        </message>
        <message>
            <source>Classical network report</source>
            <translation>Relatório da rede clássica</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nível de confiança</translation>
        </message>
        <message>
            <source>Converged in %1 iteration(s); %2 degree(s) of freedom.</source>
            <translation>Convergiu em %1 iteração(ões); %2 grau(s) de liberdade.</translation>
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
            <translation>Defeito de datum</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definição do datum</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Graus de liberdade</translation>
        </message>
        <message>
            <source>Dimension</source>
            <translation>Dimensão</translation>
        </message>
        <message>
            <source>Fixed stations (comma-separated)</source>
            <translation>Estações fixas (separadas por vírgula)</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_network</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_network</translation>
        </message>
        <message>
            <source>GeoComp network (*.json)</source>
            <translation>Rede GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solução GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Teste global</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Inspection</source>
            <translation>Inspeção</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iterações</translation>
        </message>
        <message>
            <source>Lower critical value</source>
            <translation>Valor crítico inferior</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Rede</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observação</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observações</translation>
        </message>
        <message>
            <source>Observations exceeding the critical value are candidates, not rejections. Nothing has been removed.</source>
            <translation>As observações que excedem o valor crítico são candidatas, não rejeições. Nada foi removido.</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Grandeza</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundância</translation>
        </message>
        <message>
            <source>Reference epoch (decimal year)</source>
            <translation>Época de referência (ano decimal)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieixo maior (mm)</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solução</translation>
        </message>
        <message>
            <source>Standardised residual</source>
            <translation>Resíduo padronizado</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estações</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estatística</translation>
        </message>
        <message>
            <source>Std dev X (mm)</source>
            <translation>Desvio padrão X (mm)</translation>
        </message>
        <message>
            <source>Std dev Y (mm)</source>
            <translation>Desvio padrão Y (mm)</translation>
        </message>
        <message>
            <source>The approximate coordinates document is empty.</source>
            <translation>O documento de coordenadas aproximadas está vazio.</translation>
        </message>
        <message>
            <source>The global test fails.</source>
            <translation>O teste global falha.</translation>
        </message>
        <message>
            <source>The global test fails: %1</source>
            <translation>O teste global falha: %1</translation>
        </message>
        <message>
            <source>The global test passes.</source>
            <translation>O teste global passa.</translation>
        </message>
        <message>
            <source>The network cannot be adjusted: %1</source>
            <translation>A rede não pode ser ajustada: %1</translation>
        </message>
        <message>
            <source>These fixed stations have no approximate coordinates: %1</source>
            <translation>Estas estações fixas não possuem coordenadas aproximadas: %1</translation>
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
            <translation>Fator de variância</translation>
        </message>
        <message>
            <source>Variance factor %1.</source>
            <translation>Fator de variância %1.</translation>
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
            <translation>Um framework para pré-análise, processamento GNSS e ajustamento de redes geodésicas dentro do QGIS.</translation>
        </message>
        <message>
            <source>About GeoComp</source>
            <translation>Sobre o GeoComp</translation>
        </message>
        <message>
            <source>Developed at the Departamento de Geomática, Setor de Ciências da Terra, Universidade Federal do Paraná.</source>
            <translation>Desenvolvido no Departamento de Geomática, Setor de Ciências da Terra, Universidade Federal do Paraná.</translation>
        </message>
        <message>
            <source>Engine integration arrives in later development phases.</source>
            <translation>A integração com os motores de processamento será entregue em fases posteriores do desenvolvimento.</translation>
        </message>
        <message>
            <source>GeoComp is free software under the GNU General Public License, version 2 or later. You may use it, including commercially, study it, modify it and redistribute it.</source>
            <translation>O GeoComp é software livre sob a GNU General Public License, versão 2 ou posterior. Você pode utilizá-lo, inclusive comercialmente, estudá-lo, modificá-lo e redistribuí-lo.</translation>
        </message>
        <message>
            <source>GeoComp runs external engines as separate programs. They are not part of GeoComp and carry their own licences:</source>
            <translation>O GeoComp executa motores externos como programas separados. Eles não fazem parte do GeoComp e possuem suas próprias licenças:</translation>
        </message>
        <message>
            <source>Licence</source>
            <translation>Licença</translation>
        </message>
        <message>
            <source>Processing engines</source>
            <translation>Motores de processamento</translation>
        </message>
        <message>
            <source>Source code</source>
            <translation>Código-fonte</translation>
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
            <translation>Não foi possível ler '%1' como uma rede do GeoComp. %2</translation>
        </message>
        <message>
            <source>'%1' could not be read: %2</source>
            <translation>Não foi possível ler '%1': %2</translation>
        </message>
        <message>
            <source>'%1' is not valid JSON: %2</source>
            <translation>'%1' não é um JSON válido: %2</translation>
        </message>
        <message>
            <source>1D — gravity values</source>
            <translation>1D — valores de gravidade</translation>
        </message>
        <message>
            <source>1D — heights only</source>
            <translation>1D — somente altitudes</translation>
        </message>
        <message>
            <source>2D — planimetric (easting, northing)</source>
            <translation>2D — planimétrico (E, N)</translation>
        </message>
        <message>
            <source>3D — easting, northing, up</source>
            <translation>3D — E, N, altitude</translation>
        </message>
        <message>
            <source>Constrained — hold the stations the network fixes</source>
            <translation>Amarrada — mantém as estações que a rede fixa</translation>
        </message>
        <message>
            <source>Fixed — hold the constrained stations exactly</source>
            <translation>Fixa — mantém exatamente as estações injuncionadas</translation>
        </message>
        <message>
            <source>Inner constraint — free network, trace minimum</source>
            <translation>Injunção interna — rede livre, traço mínimo</translation>
        </message>
        <message>
            <source>Minimum constraint — over chosen stations</source>
            <translation>Injunção mínima — sobre as estações escolhidas</translation>
        </message>
        <message>
            <source>No network document was given for parameter '%1'.</source>
            <translation>Nenhum documento de rede foi informado para o parâmetro '%1'.</translation>
        </message>
        <message>
            <source>The network document '%1' does not exist.</source>
            <translation>O documento de rede '%1' não existe.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompLayers</name>
        <message>
            <source>%1% confidence, exaggerated %2x</source>
            <translation>%1% de confiança, exagero de %2x</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estações ajustadas</translation>
        </message>
        <message>
            <source>Adjusted stations (layer)</source>
            <translation>Estações ajustadas (camada)</translation>
        </message>
        <message>
            <source>Coordinate corrections (%1)</source>
            <translation>Correções de coordenadas (%1)</translation>
        </message>
        <message>
            <source>Coordinate corrections (layer)</source>
            <translation>Correções de coordenadas (camada)</translation>
        </message>
        <message>
            <source>Ellipse exaggeration (0 = from the network's extent)</source>
            <translation>Exagero das elipses (0 = a partir da extensão da rede)</translation>
        </message>
        <message>
            <source>Ellipses and correction vectors are drawn exaggerated %1x.</source>
            <translation>As elipses e os vetores de correção são desenhados com exagero de %1x.</translation>
        </message>
        <message>
            <source>Error ellipses (%1)</source>
            <translation>Elipses de erro (%1)</translation>
        </message>
        <message>
            <source>Error ellipses (layer)</source>
            <translation>Elipses de erro (camada)</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observações</translation>
        </message>
        <message>
            <source>Observations (layer)</source>
            <translation>Observações (camada)</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Resíduos</translation>
        </message>
        <message>
            <source>Residuals (layer)</source>
            <translation>Resíduos (camada)</translation>
        </message>
        <message>
            <source>The style file '%1' could not be applied: %2</source>
            <translation>O arquivo de estilo '%1' não pôde ser aplicado: %2</translation>
        </message>
        <message>
            <source>The style file '%1' is missing, so the layer is unstyled.</source>
            <translation>O arquivo de estilo '%1' não foi encontrado, portanto a camada ficou sem estilo.</translation>
        </message>
        <message>
            <source>exaggerated %1x</source>
            <translation>exagero de %1x</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMapping</name>
        <message>
            <source>%1 (required)</source>
            <translation>%1 (obrigatório)</translation>
        </message>
        <message>
            <source>'%1' could not be read as a field mapping: %2</source>
            <translation>'%1' não pôde ser lido como um mapeamento de campos: %2</translation>
        </message>
        <message>
            <source>'%1' could not be written: %2</source>
            <translation>'%1' não pôde ser gravado: %2</translation>
        </message>
        <message>
            <source>(none)</source>
            <translation>(nenhum)</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato dos ângulos</translation>
        </message>
        <message>
            <source>Backsight station</source>
            <translation>Estação de ré</translation>
        </message>
        <message>
            <source>Comma</source>
            <translation>Vírgula</translation>
        </message>
        <message>
            <source>Decimal degrees</source>
            <translation>Graus decimais</translation>
        </message>
        <message>
            <source>Decimal separator</source>
            <translation>Separador decimal</translation>
        </message>
        <message>
            <source>Degrees, minutes and seconds in one column</source>
            <translation>Graus, minutos e segundos em uma coluna</translation>
        </message>
        <message>
            <source>Degrees, minutes and seconds in three columns</source>
            <translation>Graus, minutos e segundos em três colunas</translation>
        </message>
        <message>
            <source>Detect automatically</source>
            <translation>Detectar automaticamente</translation>
        </message>
        <message>
            <source>Face</source>
            <translation>Posição da luneta</translation>
        </message>
        <message>
            <source>Fields</source>
            <translation>Campos</translation>
        </message>
        <message>
            <source>Foresight station</source>
            <translation>Estação de vante</translation>
        </message>
        <message>
            <source>Format</source>
            <translation>Formato</translation>
        </message>
        <message>
            <source>GeoComp field mapping (*.json)</source>
            <translation>Mapeamento de campos do GeoComp (*.json)</translation>
        </message>
        <message>
            <source>GeoComp — Field mapping</source>
            <translation>GeoComp — Mapeamento de campos</translation>
        </message>
        <message>
            <source>Gon</source>
            <translation>Grado</translation>
        </message>
        <message>
            <source>Horizontal degrees</source>
            <translation>Graus do ângulo horizontal</translation>
        </message>
        <message>
            <source>Horizontal direction</source>
            <translation>Direção horizontal</translation>
        </message>
        <message>
            <source>Horizontal minutes</source>
            <translation>Minutos do ângulo horizontal</translation>
        </message>
        <message>
            <source>Horizontal seconds</source>
            <translation>Segundos do ângulo horizontal</translation>
        </message>
        <message>
            <source>Instrument</source>
            <translation>Instrumento</translation>
        </message>
        <message>
            <source>Instrument height</source>
            <translation>Altura do instrumento</translation>
        </message>
        <message>
            <source>Load mapping</source>
            <translation>Carregar mapeamento</translation>
        </message>
        <message>
            <source>Load mapping…</source>
            <translation>Carregar mapeamento…</translation>
        </message>
        <message>
            <source>Mapping not loaded</source>
            <translation>Mapeamento não carregado</translation>
        </message>
        <message>
            <source>Mapping not saved</source>
            <translation>Mapeamento não salvo</translation>
        </message>
        <message>
            <source>Nothing to fix.</source>
            <translation>Nada a corrigir.</translation>
        </message>
        <message>
            <source>Occupied station</source>
            <translation>Estação ocupada</translation>
        </message>
        <message>
            <source>One value for every row, for a quantity that was recorded once.</source>
            <translation>Um único valor para todas as linhas, para uma grandeza registrada uma só vez.</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Ponto</translation>
        </message>
        <message>
            <source>Pressure</source>
            <translation>Pressão</translation>
        </message>
        <message>
            <source>Problems</source>
            <translation>Problemas</translation>
        </message>
        <message>
            <source>Radians</source>
            <translation>Radianos</translation>
        </message>
        <message>
            <source>Reflector</source>
            <translation>Refletor</translation>
        </message>
        <message>
            <source>Relative humidity</source>
            <translation>Umidade relativa</translation>
        </message>
        <message>
            <source>Save mapping</source>
            <translation>Salvar mapeamento</translation>
        </message>
        <message>
            <source>Save mapping…</source>
            <translation>Salvar mapeamento…</translation>
        </message>
        <message>
            <source>Set number</source>
            <translation>Número da série</translation>
        </message>
        <message>
            <source>Sighted (backsight or foresight)</source>
            <translation>Visada (ré ou vante)</translation>
        </message>
        <message>
            <source>Slope distance</source>
            <translation>Distância inclinada</translation>
        </message>
        <message>
            <source>Source: %1</source>
            <translation>Origem: %1</translation>
        </message>
        <message>
            <source>Target</source>
            <translation>Alvo</translation>
        </message>
        <message>
            <source>Target height</source>
            <translation>Altura do alvo</translation>
        </message>
        <message>
            <source>Temperature</source>
            <translation>Temperatura</translation>
        </message>
        <message>
            <source>Zenith angle</source>
            <translation>Ângulo zenital</translation>
        </message>
        <message>
            <source>Zenith degrees</source>
            <translation>Graus do ângulo zenital</translation>
        </message>
        <message>
            <source>Zenith minutes</source>
            <translation>Minutos do ângulo zenital</translation>
        </message>
        <message>
            <source>Zenith seconds</source>
            <translation>Segundos do ângulo zenital</translation>
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
            <translation>Análise</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>Global Settings…</source>
            <translation>Configurações Globais…</translation>
        </message>
        <message>
            <source>Gravimetry</source>
            <translation>Gravimetria</translation>
        </message>
        <message>
            <source>Integration</source>
            <translation>Integração</translation>
        </message>
        <message>
            <source>Level</source>
            <translation>Nível</translation>
        </message>
        <message>
            <source>No operations available yet in this version.</source>
            <translation>Nenhuma operação disponível nesta versão ainda.</translation>
        </message>
        <message>
            <source>Total Station</source>
            <translation>Estação Total</translation>
        </message>
    </context>
    <context>
        <name>GeoCompMessages</name>
        <message>
            <source>(not set)</source>
            <translation>(não definido)</translation>
        </message>
        <message>
            <source>Correlated cluster '%1' supplies %2 observation rows but a %3 covariance matrix. The two must agree, in the same order.</source>
            <translation>O agrupamento correlacionado '%1' fornece %2 linhas de observação mas uma matriz de covariâncias %3. Os dois devem coincidir, na mesma ordem.</translation>
        </message>
        <message>
            <source>Every station in this network is held fixed, so there is nothing to estimate. %1</source>
            <translation>Todas as estações desta rede estão fixas, portanto não há nada a estimar. %1</translation>
        </message>
        <message>
            <source>GeoComp could not complete the operation (%1). See the GeoComp tab of the Log Messages panel for details.</source>
            <translation>O GeoComp não conseguiu concluir a operação (%1). Consulte a aba GeoComp do painel Mensagens de Log para mais detalhes.</translation>
        </message>
        <message>
            <source>No observations were supplied. %1</source>
            <translation>Nenhuma observação foi fornecida. %1</translation>
        </message>
        <message>
            <source>No stations were given to define the datum on. %1</source>
            <translation>Nenhuma estação foi indicada para definir o datum. %1</translation>
        </message>
        <message>
            <source>Observation '%1' between %2 has no horizontal separation at the approximate coordinates, so the zenith angle cannot be linearised there. Correct the approximate coordinates.</source>
            <translation>A observação '%1' entre %2 não possui separação horizontal nas coordenadas aproximadas, de modo que o ângulo zenital não pode ser linearizado ali. Corrija as coordenadas aproximadas.</translation>
        </message>
        <message>
            <source>Observation '%1' carries no uncertainty, so it cannot be weighted. %2</source>
            <translation>A observação '%1' não possui incerteza, portanto não pode ser ponderada. %2</translation>
        </message>
        <message>
            <source>Observation '%1' connects stations that are at the same approximate position (%2), so its direction is undefined. Correct the approximate coordinates.</source>
            <translation>A observação '%1' liga estações que estão na mesma posição aproximada (%2), de modo que sua direção é indefinida. Corrija as coordenadas aproximadas.</translation>
        </message>
        <message>
            <source>Observation '%1' is of type %2, which is not a gravity observation, so it cannot take part in a gravity adjustment.</source>
            <translation>A observação '%1' é do tipo %2, que não é uma observação gravimétrica, portanto não pode participar de um ajustamento de gravidade.</translation>
        </message>
        <message>
            <source>Observation '%1' is of type %2, which the in-house adjustment does not implement. %3</source>
            <translation>A observação '%1' é do tipo %2, que o ajustamento próprio do GeoComp ainda não implementa. %3</translation>
        </message>
        <message>
            <source>Observation '%1' of type %2 cannot contribute to a %3 adjustment. Choose a coordinate frame the observation can constrain, or exclude it.</source>
            <translation>A observação '%1', do tipo %2, não pode contribuir para um ajustamento %3. Escolha um referencial de coordenadas que a observação possa injuncionar, ou exclua-a.</translation>
        </message>
        <message>
            <source>Station '%1' has no approximate %2, and the linearised adjustment needs a point to linearise about. Supply approximate coordinates, or generate them from the observations.</source>
            <translation>A estação '%1' não possui %2 aproximada, e o ajustamento linearizado precisa de um ponto em torno do qual linearizar. Forneça coordenadas aproximadas, ou gere-as a partir das observações.</translation>
        </message>
        <message>
            <source>Station '%1' is held fixed but carries no position, so there is no value to hold it at. Give it coordinates, or release the constraint.</source>
            <translation>A estação '%1' está fixa mas não possui posição, portanto não há valor no qual mantê-la. Atribua-lhe coordenadas, ou libere a injunção.</translation>
        </message>
        <message>
            <source>The '%1' engine is required for this operation but is not installed. Install it from Global Settings, under Paths and engines.</source>
            <translation>O motor '%1' é necessário para esta operação, mas não está instalado. Instale-o em Configurações Globais, na seção Caminhos e motores.</translation>
        </message>
        <message>
            <source>The adjustment of '%1' did not converge: after %2 iteration(s) the largest correction was still %3, against a threshold of %4. Approximate coordinates that are far from the truth are the usual cause; a blunder large enough to drag the solution is the other. No coordinates are returned, because iterate %2 of a diverging sequence is not a result.</source>
            <translation>O ajustamento de '%1' não convergiu: após %2 iteração(ões) a maior correção ainda era %3, contra um limiar de %4. Coordenadas aproximadas distantes da verdade são a causa usual; um erro grosseiro grande o bastante para arrastar a solução é a outra. Nenhuma coordenada é devolvida, porque a iteração %2 de uma sequência divergente não é um resultado.</translation>
        </message>
        <message>
            <source>The adjustment of '%1' produced no iterations at all. This is an internal error; please report it with the network that caused it.</source>
            <translation>O ajustamento de '%1' não produziu iteração alguma. Este é um erro interno; por favor relate-o junto com a rede que o causou.</translation>
        </message>
        <message>
            <source>The datum constraints do not remove the network's remaining freedom (%1 constraint(s) applied). Check that the stations defining the datum are enough to fix it.</source>
            <translation>As injunções de datum não removem a liberdade remanescente da rede (%1 injunção(ões) aplicada(s)). Verifique se as estações que definem o datum bastam para fixá-lo.</translation>
        </message>
        <message>
            <source>The network '%1' has no active observations, so there is nothing to adjust. Observations marked as rejected do not take part; re-activate the ones you want to use.</source>
            <translation>A rede '%1' não possui observações ativas, portanto não há nada a ajustar. Observações marcadas como rejeitadas não participam; reative aquelas que deseja utilizar.</translation>
        </message>
        <message>
            <source>The network '%1' is not internally consistent: %2. Run Inspect network to see every problem at once.</source>
            <translation>A rede '%1' não é internamente consistente: %2. Execute Inspecionar rede para ver todos os problemas de uma vez.</translation>
        </message>
        <message>
            <source>The network does not determine %1 combination(s) of unknowns: %2. Add observations that fix them, or define the datum with inner or minimum constraints so the remaining freedom is removed deliberately.</source>
            <translation>A rede não determina %1 combinação(ões) de incógnitas: %2. Acrescente observações que as fixem, ou defina o datum com injunções internas ou mínimas, de modo que a liberdade remanescente seja removida deliberadamente.</translation>
        </message>
        <message>
            <source>The planned network '%1' contains no observations, so there is no design to evaluate. Add the observations you intend to make, with their assumed precisions.</source>
            <translation>A rede planejada '%1' não contém observações, portanto não há projeto a avaliar. Acrescente as observações que pretende realizar, com suas precisões supostas.</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be greater than %2 (received %3).</source>
            <translation>A configuração '%1' não pode ser maior que %2 (recebido %3).</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be less than %2 (received %3).</source>
            <translation>A configuração '%1' não pode ser menor que %2 (recebido %3).</translation>
        </message>
        <message>
            <source>The setting '%1' cannot be set to '%2'. Permitted values are: %3.</source>
            <translation>A configuração '%1' não pode ser definida como '%2'. Os valores permitidos são: %3.</translation>
        </message>
        <message>
            <source>The setting '%1' expects a value of type %2, but received %3. Correct it in Global Settings, or restore the default.</source>
            <translation>A configuração '%1' espera um valor do tipo %2, mas recebeu %3. Corrija-a em Configurações Globais ou restaure o padrão.</translation>
        </message>
        <message>
            <source>This JSON file is not a GeoComp network document: it has no network identifier. Expected %1.</source>
            <translation>Este arquivo JSON não é um documento de rede do GeoComp: não possui identificador de rede. Esperado: %1.</translation>
        </message>
        <message>
            <source>This file does not hold a GeoComp network: its top level is %1, and a network document is a JSON object. Check that you chose the right file.</source>
            <translation>Este arquivo não contém uma rede do GeoComp: seu nível superior é %1, e um documento de rede é um objeto JSON. Verifique se escolheu o arquivo certo.</translation>
        </message>
        <message>
            <source>This network document could not be read: %1. It may have been written by a different version of GeoComp, or edited by hand.</source>
            <translation>Não foi possível ler este documento de rede: %1. Ele pode ter sido gravado por outra versão do GeoComp, ou editado à mão.</translation>
        </message>
        <message>
            <source>This project file holds %1 networks, so GeoComp cannot tell which one you mean. Export the network you want to analyse and choose that file instead.</source>
            <translation>Este arquivo de projeto contém %1 redes, de modo que o GeoComp não pode saber a qual delas você se refere. Exporte a rede que deseja analisar e escolha esse arquivo.</translation>
        </message>
    </context>
    <context>
        <name>GeoCompPlugin</name>
        <message>
            <source>About GeoComp…</source>
            <translation>Sobre o GeoComp…</translation>
        </message>
        <message>
            <source>GeoComp</source>
            <translation>GeoComp</translation>
        </message>
        <message>
            <source>GeoComp Global Settings</source>
            <translation>Configurações Globais do GeoComp</translation>
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
            <translation>%1 estação(ões), %2 observação(ões), %3 grau(s) de liberdade. Pior: %4 mm em %5.</translation>
        </message>
        <message>
            <source>(none)</source>
            <translation>(nenhuma)</translation>
        </message>
        <message>
            <source>Add station</source>
            <translation>Adicionar estação</translation>
        </message>
        <message>
            <source>Azimuth</source>
            <translation>Azimute</translation>
        </message>
        <message>
            <source>Click on the map to…</source>
            <translation>Clique no mapa para…</translation>
        </message>
        <message>
            <source>Connect</source>
            <translation>Conectar</translation>
        </message>
        <message>
            <source>Connect draws</source>
            <translation>Conectar desenha</translation>
        </message>
        <message>
            <source>Design</source>
            <translation>Projeto</translation>
        </message>
        <message>
            <source>Direction</source>
            <translation>Direção</translation>
        </message>
        <message>
            <source>Expected precision</source>
            <translation>Precisão esperada</translation>
        </message>
        <message>
            <source>Expected precision (ellipses exaggerated %1x)</source>
            <translation>Precisão esperada (elipses com exagero de %1x)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>GeoComp — Interactive pre-analysis</source>
            <translation>GeoComp — Pré-análise interativa</translation>
        </message>
        <message>
            <source>Height difference</source>
            <translation>Desnível</translation>
        </message>
        <message>
            <source>Horizontal distance</source>
            <translation>Distância horizontal</translation>
        </message>
        <message>
            <source>Move</source>
            <translation>Mover</translation>
        </message>
        <message>
            <source>Nothing to evaluate yet.</source>
            <translation>Ainda não há nada a avaliar.</translation>
        </message>
        <message>
            <source>Nothing to report.</source>
            <translation>Nada a relatar.</translation>
        </message>
        <message>
            <source>Positional uncertainty (mm)</source>
            <translation>Incerteza posicional (mm)</translation>
        </message>
        <message>
            <source>Redo</source>
            <translation>Refazer</translation>
        </message>
        <message>
            <source>Remove</source>
            <translation>Remover</translation>
        </message>
        <message>
            <source>Required precision</source>
            <translation>Precisão requerida</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieixo maior (mm)</translation>
        </message>
        <message>
            <source>Semi-minor (mm)</source>
            <translation>Semieixo menor (mm)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Undo</source>
            <translation>Desfazer</translation>
        </message>
    </context>
    <context>
        <name>GeoCompPrompts</name>
        <message>
            <source>Choose a field book</source>
            <translation>Escolha uma caderneta de campo</translation>
        </message>
        <message>
            <source>Field books (*.csv *.txt);;All files (*)</source>
            <translation>Cadernetas de campo (*.csv *.txt);;Todos os arquivos (*)</translation>
        </message>
    </context>
    <context>
        <name>GeoCompReport</name>
        <message>
            <source>not defined</source>
            <translation>não definido</translation>
        </message>
    </context>
    <context>
        <name>GeoCompSettings</name>
        <message>
            <source>(not editable in this version)</source>
            <translation>(não editável nesta versão)</translation>
        </message>
        <message>
            <source>Advanced</source>
            <translation>Avançado</translation>
        </message>
        <message>
            <source>Angle decimal places</source>
            <translation>Casas decimais dos ângulos</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato dos ângulos</translation>
        </message>
        <message>
            <source>Basic</source>
            <translation>Básico</translation>
        </message>
        <message>
            <source>Coordinate decimal places</source>
            <translation>Casas decimais das coordenadas</translation>
        </message>
        <message>
            <source>Critical</source>
            <translation>Crítico</translation>
        </message>
        <message>
            <source>Debug</source>
            <translation>Depuração</translation>
        </message>
        <message>
            <source>Decimal degrees</source>
            <translation>Graus decimais</translation>
        </message>
        <message>
            <source>Degrees, minutes, seconds</source>
            <translation>Graus, minutos, segundos</translation>
        </message>
        <message>
            <source>Distance unit</source>
            <translation>Unidade de distância</translation>
        </message>
        <message>
            <source>English</source>
            <translation>Inglês</translation>
        </message>
        <message>
            <source>Español</source>
            <translation>Espanhol</translation>
        </message>
        <message>
            <source>Follow QGIS</source>
            <translation>Seguir o QGIS</translation>
        </message>
        <message>
            <source>Foot</source>
            <translation>Pé</translation>
        </message>
        <message>
            <source>GNSS</source>
            <translation>GNSS</translation>
        </message>
        <message>
            <source>GeoComp — Global Settings</source>
            <translation>GeoComp — Configurações Globais</translation>
        </message>
        <message>
            <source>Gon</source>
            <translation>Grado</translation>
        </message>
        <message>
            <source>Gravimeter</source>
            <translation>Gravímetro</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Informação</translation>
        </message>
        <message>
            <source>Interface</source>
            <translation>Interface</translation>
        </message>
        <message>
            <source>Language</source>
            <translation>Idioma</translation>
        </message>
        <message>
            <source>Level</source>
            <translation>Nível</translation>
        </message>
        <message>
            <source>Log verbosity</source>
            <translation>Detalhamento do log</translation>
        </message>
        <message>
            <source>Metre</source>
            <translation>Metro</translation>
        </message>
        <message>
            <source>No settings in this section yet. They are added by the development phase that implements this equipment type.</source>
            <translation>Ainda não há configurações nesta seção. Elas são adicionadas pela fase de desenvolvimento que implementa este tipo de equipamento.</translation>
        </message>
        <message>
            <source>Paths and engines</source>
            <translation>Caminhos e motores</translation>
        </message>
        <message>
            <source>Português (Brasil)</source>
            <translation>Português (Brasil)</translation>
        </message>
        <message>
            <source>Radian</source>
            <translation>Radiano</translation>
        </message>
        <message>
            <source>Reference systems</source>
            <translation>Sistemas de referência</translation>
        </message>
        <message>
            <source>Settings resolve in the order: this run, this project, global, default.</source>
            <translation>As configurações são resolvidas na ordem: esta execução, este projeto, global, padrão.</translation>
        </message>
        <message>
            <source>Show the GeoComp toolbar</source>
            <translation>Exibir a barra de ferramentas do GeoComp</translation>
        </message>
        <message>
            <source>Stochastic model</source>
            <translation>Modelo estocástico</translation>
        </message>
        <message>
            <source>Total Station</source>
            <translation>Estação Total</translation>
        </message>
        <message>
            <source>US survey foot</source>
            <translation>Pé americano (US survey foot)</translation>
        </message>
        <message>
            <source>Usage mode</source>
            <translation>Modo de uso</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Aviso</translation>
        </message>
        <message>
            <source>default</source>
            <translation>padrão</translation>
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
            <translation>este projeto</translation>
        </message>
        <message>
            <source>this run</source>
            <translation>esta execução</translation>
        </message>
    </context>
    <context>
        <name>GeoCompTotalStation</name>
        <message>
            <source>'%1' contains no setups, so there is nothing to process.</source>
            <translation>'%1' não contém estacionamentos, portanto não há nada a processar.</translation>
        </message>
        <message>
            <source>'%1' could not be read as a field mapping: %2</source>
            <translation>Não foi possível ler '%1' como um mapeamento de campos: %2</translation>
        </message>
        <message>
            <source>'%1' could not be read as an instrument profile library. %2</source>
            <translation>Não foi possível ler '%1' como uma biblioteca de perfis de instrumento. %2</translation>
        </message>
        <message>
            <source>'%1' could not be read as readings: %2</source>
            <translation>Não foi possível ler '%1' como leituras: %2</translation>
        </message>
        <message>
            <source>'%1' does not contain a GeoComp document: its top level is not an object.</source>
            <translation>'%1' não contém um documento do GeoComp: seu nível superior não é um objeto.</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp readings document. Run Import field book first, or choose the file it produced.</source>
            <translation>'%1' não é um documento de leituras do GeoComp. Execute primeiro Importar caderneta de campo, ou escolha o arquivo que ela produziu.</translation>
        </message>
        <message>
            <source>'%1' is not a GeoComp reductions document. Run Generalised pre-processing first, or choose the file it produced.</source>
            <translation>'%1' não é um documento de reduções do GeoComp. Execute primeiro o Pré-processamento generalizado, ou escolha o arquivo que ele produziu.</translation>
        </message>
        <message>
            <source>'%1' is not valid JSON: %2</source>
            <translation>'%1' não é um JSON válido: %2</translation>
        </message>
        <message>
            <source>Blocking</source>
            <translation>Impeditivo</translation>
        </message>
        <message>
            <source>Code</source>
            <translation>Código</translation>
        </message>
        <message>
            <source>Finding</source>
            <translation>Constatação</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Informação</translation>
        </message>
        <message>
            <source>Involves</source>
            <translation>Envolve</translation>
        </message>
        <message>
            <source>No file was given for parameter '%1'.</source>
            <translation>Nenhum arquivo foi informado para o parâmetro '%1'.</translation>
        </message>
        <message>
            <source>Nothing to report.</source>
            <translation>Nada a relatar.</translation>
        </message>
        <message>
            <source>Severity</source>
            <translation>Severidade</translation>
        </message>
        <message>
            <source>The file '%1' does not exist.</source>
            <translation>O arquivo '%1' não existe.</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Aviso</translation>
        </message>
    </context>
    <context>
        <name>ImportFieldBookAlgorithm</name>
        <message>
            <source>%1 record(s) read into %2 setup(s); %3 rejected.</source>
            <translation>%1 registro(s) lido(s) em %2 estacionamento(s); %3 rejeitado(s).</translation>
        </message>
        <message>
            <source>%1 record(s) were rejected; see the findings.</source>
            <translation>%1 registro(s) foram rejeitados; veja as constatações.</translation>
        </message>
        <message>
            <source>(constant %1)</source>
            <translation>(constante %1)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Reads a total-station field book from a CSV file and writes a GeoComp readings document the other Total Station algorithms take as input.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The field mapping is a saved, reusable object.&lt;/b&gt; The same organisation imports the same instrument export layout every week, and re-mapping columns by hand each time is exactly the manual handling this plugin exists to remove. Leave the mapping empty and GeoComp infers one from the header, which is right for the layouts it recognises; the report then states every column it mapped, so an inferred mapping is never silently trusted.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Every bad record is reported and none stops the import.&lt;/b&gt; A field book with six problems needs one run and produces six findings, each naming its source row.&lt;/p&gt;&lt;p&gt;An uncertainty is attached to every reading here, at the boundary, from the instrument profile or from the per-type defaults below. Where neither supplies one the import refuses: GeoComp does not invent a standard deviation, because a fabricated weight silently corrupts every statistic computed from it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Field book&lt;/b&gt; &amp;mdash; the CSV file. &lt;b&gt;Field mapping&lt;/b&gt; &amp;mdash; a saved mapping document (JSON); empty infers one.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument profiles&lt;/b&gt; &amp;mdash; a profile library (JSON). Empty uses a generic total station of 2 mm + 2 ppm and 5 arcseconds, and everything computed from it is marked approximate.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Default direction, zenith and distance precision&lt;/b&gt; &amp;mdash; used where the instrument profile supplies none. In radians and metres; 0 means not configured.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fail if any record was rejected&lt;/b&gt; &amp;mdash; when set, a rejected record stops the algorithm, so a model does not carry on with a partial import.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Readings&lt;/b&gt; &amp;mdash; the JSON document. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Findings&lt;/b&gt; &amp;mdash; CSV, one row per problem. Scalars: &lt;code&gt;RECORD_COUNT&lt;/code&gt;, &lt;code&gt;SETUP_COUNT&lt;/code&gt; and &lt;code&gt;REJECTED_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Lê uma caderneta de campo de estação total a partir de um arquivo CSV e grava um documento de leituras do GeoComp que os demais algoritmos de Estação Total tomam como entrada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;O mapeamento de campos é um objeto salvo e reutilizável.&lt;/b&gt; A mesma organização importa o mesmo layout de exportação do instrumento toda semana, e remapear colunas à mão a cada vez é exatamente a manipulação manual que este plugin existe para eliminar. Deixe o mapeamento vazio e o GeoComp infere um a partir do cabeçalho, o que é correto para os layouts que ele reconhece; o relatório então declara cada coluna que mapeou, de modo que um mapeamento inferido nunca é silenciosamente confiado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Todo registro ruim é relatado e nenhum interrompe a importação.&lt;/b&gt; Uma caderneta com seis problemas exige uma execução e produz seis constatações, cada uma nomeando sua linha de origem.&lt;/p&gt;&lt;p&gt;Uma incerteza é anexada a cada leitura aqui, na fronteira, a partir do perfil do instrumento ou dos padrões por tipo abaixo. Onde nenhum dos dois fornece uma, a importação recusa: o GeoComp não inventa um desvio padrão, porque um peso fabricado corrompe silenciosamente toda estatística calculada a partir dele.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Caderneta de campo&lt;/b&gt; &amp;mdash; o arquivo CSV. &lt;b&gt;Mapeamento de campos&lt;/b&gt; &amp;mdash; um documento de mapeamento salvo (JSON); vazio infere um.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Perfis de instrumento&lt;/b&gt; &amp;mdash; uma biblioteca de perfis (JSON). Vazio utiliza uma estação total genérica de 2 mm + 2 ppm e 5 segundos de arco, e tudo o que for calculado a partir dela é marcado como aproximado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Precisão padrão de direção, zenital e de distância&lt;/b&gt; &amp;mdash; usadas onde o perfil do instrumento não fornece nenhuma. Em radianos e metros; 0 significa não configurado.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Falhar se algum registro for rejeitado&lt;/b&gt; &amp;mdash; quando marcado, um registro rejeitado interrompe o algoritmo, de modo que um modelo não prossiga com uma importação parcial.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Leituras&lt;/b&gt; &amp;mdash; o documento JSON. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Constatações&lt;/b&gt; &amp;mdash; CSV, uma linha por problema. Escalares: &lt;code&gt;RECORD_COUNT&lt;/code&gt;, &lt;code&gt;SETUP_COUNT&lt;/code&gt; e &lt;code&gt;REJECTED_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Angle format</source>
            <translation>Formato do ângulo</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Column not mapped</source>
            <translation>Coluna não mapeada</translation>
        </message>
        <message>
            <source>Columns not mapped, and therefore not imported: %1</source>
            <translation>Colunas não mapeadas, e portanto não importadas: %1</translation>
        </message>
        <message>
            <source>Default direction precision (rad)</source>
            <translation>Precisão padrão das direções (rad)</translation>
        </message>
        <message>
            <source>Default distance precision (m)</source>
            <translation>Precisão padrão das distâncias (m)</translation>
        </message>
        <message>
            <source>Default zenith angle precision (rad)</source>
            <translation>Precisão padrão dos ângulos zenitais (rad)</translation>
        </message>
        <message>
            <source>Fail if any record was rejected</source>
            <translation>Falhar se algum registro for rejeitado</translation>
        </message>
        <message>
            <source>Field book</source>
            <translation>Caderneta de campo</translation>
        </message>
        <message>
            <source>Field book import report</source>
            <translation>Relatório de importação da caderneta de campo</translation>
        </message>
        <message>
            <source>Field mapping</source>
            <translation>Mapeamento de campos</translation>
        </message>
        <message>
            <source>Field mapping used</source>
            <translation>Mapeamento de campos utilizado</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_import_fieldbook</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_import_fieldbook</translation>
        </message>
        <message>
            <source>GeoComp field</source>
            <translation>Campo do GeoComp</translation>
        </message>
        <message>
            <source>GeoComp readings (*.json)</source>
            <translation>Leituras GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Import</source>
            <translation>Importação</translation>
        </message>
        <message>
            <source>Import field book</source>
            <translation>Importar caderneta de campo</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfis de instrumento</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Read a CSV field book through a saved, reusable field mapping.</source>
            <translation>Lê uma caderneta de campo em CSV através de um mapeamento de campos salvo e reutilizável.</translation>
        </message>
        <message>
            <source>Reading '%1' with mapping '%2'…</source>
            <translation>Lendo '%1' com o mapeamento '%2'…</translation>
        </message>
        <message>
            <source>Readings</source>
            <translation>Leituras</translation>
        </message>
        <message>
            <source>Records</source>
            <translation>Registros</translation>
        </message>
        <message>
            <source>Rejected records</source>
            <translation>Registros rejeitados</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Rows read</source>
            <translation>Linhas lidas</translation>
        </message>
        <message>
            <source>Setups</source>
            <translation>Estacionamentos</translation>
        </message>
        <message>
            <source>Source column</source>
            <translation>Coluna de origem</translation>
        </message>
        <message>
            <source>The field book '%1' does not exist.</source>
            <translation>A caderneta de campo '%1' não existe.</translation>
        </message>
        <message>
            <source>The field book '%1' is empty.</source>
            <translation>A caderneta de campo '%1' está vazia.</translation>
        </message>
        <message>
            <source>Unit</source>
            <translation>Unidade</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
    </context>
    <context>
        <name>IntersectionAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes the coordinates of a point sighted from two or more known stations whose orientation is known, by least squares. Two stations give a unique solution; more give residuals and a covariance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Weak geometry is reported rather than left to be discovered.&lt;/b&gt; Near-parallel rays do not determine a point however precise each sighting is, and the error ellipse is where that shows: when it comes out more than ten times longer than it is wide, the run says so. Rays that are exactly parallel are refused, because there is no intersection to return.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Sightings&lt;/b&gt; &amp;mdash; a JSON object mapping each observing station to its position and the azimuth it observed:&lt;/p&gt;&lt;pre&gt;{"A": {"position": [0, 0], "azimuth": 57.99},
 "B": {"position": [1000, 0], "azimuth": 300.02}}&lt;/pre&gt;&lt;p&gt;Positions in metres, azimuths in degrees from north, clockwise. Azimuths rather than circle readings: an intersection is computed from &lt;i&gt;oriented&lt;/i&gt; stations, and where the orientation is unknown the station has to be resected first.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Target&lt;/b&gt; &amp;mdash; the name to give the computed point. &lt;b&gt;Azimuth precision&lt;/b&gt; (degrees) &amp;mdash; applied to every sighting that does not state its own, and what the resulting ellipse is scaled by.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the reported ellipse.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Position&lt;/b&gt; &amp;mdash; a JSON document in the shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SEMI_MAJOR&lt;/code&gt;, &lt;code&gt;SEMI_MINOR&lt;/code&gt; in metres and &lt;code&gt;WEAK_GEOMETRY&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula as coordenadas de um ponto visado a partir de duas ou mais estações conhecidas cuja orientação é conhecida, por mínimos quadrados. Duas estações dão uma solução única; mais dão resíduos e uma covariância.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A geometria fraca é relatada em vez de deixada para ser descoberta.&lt;/b&gt; Raios quase paralelos não determinam um ponto por mais precisa que seja cada visada, e a elipse de erros é onde isso aparece: quando ela sai mais de dez vezes mais longa do que larga, a execução avisa. Raios exatamente paralelos são recusados, porque não há interseção a devolver.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Visadas&lt;/b&gt; &amp;mdash; um objeto JSON associando cada estação observadora à sua posição e ao azimute que observou:&lt;/p&gt;&lt;pre&gt;{"A": {"position": [0, 0], "azimuth": 57.99},
 "B": {"position": [1000, 0], "azimuth": 300.02}}&lt;/pre&gt;&lt;p&gt;Posições em metros, azimutes em graus a partir do norte, no sentido horário. Azimutes e não leituras de círculo: uma interseção direta é calculada a partir de estações &lt;i&gt;orientadas&lt;/i&gt;, e onde a orientação é desconhecida a estação precisa antes ser determinada por interseção inversa.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Alvo&lt;/b&gt; &amp;mdash; o nome a dar ao ponto calculado. &lt;b&gt;Precisão do azimute&lt;/b&gt; (graus) &amp;mdash; aplicada a toda visada que não declare a sua, e é por ela que a elipse resultante é escalada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nível de confiança&lt;/b&gt; &amp;mdash; para a elipse relatada.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Posição&lt;/b&gt; &amp;mdash; um documento JSON no formato que a Rede clássica toma como coordenadas aproximadas. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SEMI_MAJOR&lt;/code&gt;, &lt;code&gt;SEMI_MINOR&lt;/code&gt; em metros e &lt;code&gt;WEAK_GEOMETRY&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>At least two sightings are needed; the document holds %1.</source>
            <translation>São necessárias ao menos duas visadas; o documento contém %1.</translation>
        </message>
        <message>
            <source>Azimuth precision (°)</source>
            <translation>Precisão do azimute (°)</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nível de confiança</translation>
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
            <translation>Azimute da elipse (°)</translation>
        </message>
        <message>
            <source>Fix a sighted point from two or more oriented known stations.</source>
            <translation>Determina um ponto visado a partir de duas ou mais estações conhecidas e orientadas.</translation>
        </message>
        <message>
            <source>Forward intersection</source>
            <translation>Interseção direta</translation>
        </message>
        <message>
            <source>Forward intersection report</source>
            <translation>Relatório da interseção direta</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_intersection</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_intersection</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Geometry</source>
            <translation>Geometria</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Intersecting '%1' from %2 station(s).</source>
            <translation>Interseccionando '%1' a partir de %2 estação(ões).</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Ponto</translation>
        </message>
        <message>
            <source>Position</source>
            <translation>Posição</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Residual (")</source>
            <translation>Resíduo (")</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Resíduos</translation>
        </message>
        <message>
            <source>Semi-major (mm)</source>
            <translation>Semieixo maior (mm)</translation>
        </message>
        <message>
            <source>Semi-minor (mm)</source>
            <translation>Semieixo menor (mm)</translation>
        </message>
        <message>
            <source>Sighting '%1' does not hold numbers.</source>
            <translation>A visada '%1' não contém números.</translation>
        </message>
        <message>
            <source>Sighting '%1' must be an object with a 'position' pair and an 'azimuth'.</source>
            <translation>A visada '%1' deve ser um objeto com um par 'position' e um 'azimuth'.</translation>
        </message>
        <message>
            <source>Sightings</source>
            <translation>Visadas</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Target name</source>
            <translation>Nome do alvo</translation>
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
            <translation>%1 observação(ões) excede(m) o valor crítico do teste w.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Adjusts a geodetic network by least squares using the parametric model, iterating the linearised solution to convergence, and reports the adjusted coordinates with their full covariance matrix, the residuals, and the statistical tests that say whether the result may be believed.&lt;/p&gt;&lt;p&gt;1D, 2D and 3D networks are all supported, free or constrained. The weight matrix is built from the observation covariances, including correlations between the observations of a correlated cluster such as a GNSS baseline.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Non-convergence is reported as a failure&lt;/b&gt;, never returned as a result. A set of coordinates that is really iteration seven of a diverging sequence is worse than no result, because nothing about it says so.&lt;/p&gt;&lt;p&gt;&lt;b&gt;No observation is rejected automatically.&lt;/b&gt; Data snooping reports candidates and the decision is yours; re-adjusting after removing one is a second, explicit run. Automatic iterative rejection deletes real signal, which in deformation monitoring is the very thing being measured.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D. It decides which parameters exist and which observations can contribute.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;i&gt;Constrained&lt;/i&gt; and &lt;i&gt;Fixed&lt;/i&gt; hold the stations the network declares as constrained. &lt;i&gt;Inner constraint&lt;/i&gt; gives a free network whose solution is the trace minimum over all stations. &lt;i&gt;Minimum constraint&lt;/i&gt; does the same over the chosen stations, which is what a deformation analysis needs: holding a station that has itself moved spreads its motion across the network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; comma-separated; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the global test, the w-test and the error ellipses, between 0 and 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared the global test compares against.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Convergence threshold&lt;/b&gt; &amp;mdash; the largest parameter correction accepted as converged, in metres. &lt;b&gt;Maximum iterations&lt;/b&gt; &amp;mdash; after which non-convergence is reported.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Reference epoch&lt;/b&gt; &amp;mdash; the decimal year the coordinates refer to. It is recorded on the solution because comparing two epochs is only meaningful when both say which they are.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solution&lt;/b&gt; &amp;mdash; a JSON document holding the adjusted coordinates, the full covariance matrix, the per-observation results and the provenance. It is the same structure an external engine's result fills, so everything downstream is engine-independent.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Adjusted stations&lt;/b&gt; and &lt;b&gt;Residuals&lt;/b&gt; &amp;mdash; CSV tables for a spreadsheet or a model.&lt;/p&gt;&lt;p&gt;Scalar outputs: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Result layers&lt;/b&gt; &amp;mdash; five optional map layers, arriving styled and ready to read (FR-905): adjusted stations sized by their positional uncertainty, error ellipses, observations coloured by what the w-test decided about them, the measured network by observation type, and the coordinate correction vectors. None is created unless asked for, so an adjustment run to feed another algorithm writes nothing extra.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ellipse exaggeration&lt;/b&gt; &amp;mdash; real ellipses are invisible at map scale, so they are drawn enlarged. Leave it at 0 and a factor is fitted to the network's own extent. Whatever factor is used is stated in the layer's name, which is what reaches the legend: an unstated exaggeration turns a quality visualisation into a misrepresentation.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Ajusta uma rede geodésica por mínimos quadrados usando o modelo paramétrico, iterando a solução linearizada até a convergência, e relata as coordenadas ajustadas com sua matriz de covariâncias completa, os resíduos e os testes estatísticos que dizem se o resultado pode ser acreditado.&lt;/p&gt;&lt;p&gt;Redes 1D, 2D e 3D são todas suportadas, livres ou amarradas. A matriz dos pesos é construída a partir das covariâncias das observações, incluindo correlações entre as observações de um agrupamento correlacionado, como uma linha de base GNSS.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A não convergência é relatada como falha&lt;/b&gt;, nunca devolvida como resultado. Um conjunto de coordenadas que na verdade é a sétima iteração de uma sequência divergente é pior do que nenhum resultado, porque nada nele diz isso.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nenhuma observação é rejeitada automaticamente.&lt;/b&gt; O data snooping relata candidatas e a decisão é sua; reajustar após remover uma é uma segunda execução, explícita. A rejeição iterativa automática apaga sinal real, que no monitoramento de deformações é justamente aquilo que está sendo medido.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Rede&lt;/b&gt; &amp;mdash; um documento de rede do GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Referencial de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D ou 3D. Decide quais parâmetros existem e quais observações podem contribuir.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definição do datum&lt;/b&gt; &amp;mdash; como o defeito de datum é removido. &lt;i&gt;Amarrada&lt;/i&gt; e &lt;i&gt;Fixa&lt;/i&gt; mantêm as estações que a rede declara como injuncionadas. &lt;i&gt;Injunção interna&lt;/i&gt; fornece uma rede livre cuja solução é o traço mínimo sobre todas as estações. &lt;i&gt;Injunção mínima&lt;/i&gt; faz o mesmo sobre as estações escolhidas, que é o que uma análise de deformação exige: manter uma estação que ela própria se moveu espalha seu movimento por toda a rede.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Estações do datum&lt;/b&gt; &amp;mdash; separadas por vírgula; vazio significa todas elas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nível de confiança&lt;/b&gt; &amp;mdash; para o teste global, o teste w e as elipses de erros, entre 0 e 1.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fator de variância a priori&lt;/b&gt; &amp;mdash; o sigma-zero ao quadrado suposto com o qual o teste global compara.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Limiar de convergência&lt;/b&gt; &amp;mdash; a maior correção de parâmetro aceita como convergida, em metros. &lt;b&gt;Número máximo de iterações&lt;/b&gt; &amp;mdash; após o qual a não convergência é relatada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Significância&lt;/b&gt; e &lt;b&gt;erro tipo II&lt;/b&gt; &amp;mdash; alfa e beta para o menor erro detectável.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Época de referência&lt;/b&gt; &amp;mdash; o ano decimal a que as coordenadas se referem. É registrada na solução porque comparar duas épocas só faz sentido quando ambas dizem quais são.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Solução&lt;/b&gt; &amp;mdash; um documento JSON contendo as coordenadas ajustadas, a matriz de covariâncias completa, os resultados por observação e a proveniência. É a mesma estrutura que o resultado de um motor externo preenche, de modo que tudo a jusante é independente do motor.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estações ajustadas&lt;/b&gt; e &lt;b&gt;Resíduos&lt;/b&gt; &amp;mdash; tabelas CSV para uma planilha ou um modelo.&lt;/p&gt;&lt;p&gt;Saídas escalares: &lt;code&gt;VARIANCE_FACTOR_APOSTERIORI&lt;/code&gt;, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt;, &lt;code&gt;ITERATIONS&lt;/code&gt;, &lt;code&gt;GLOBAL_TEST_PASSED&lt;/code&gt;, &lt;code&gt;OUTLIER_COUNT&lt;/code&gt;, &lt;code&gt;WORST_OUTLIER&lt;/code&gt; e &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt;.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Camadas de resultado&lt;/b&gt; &amp;mdash; cinco camadas opcionais, que chegam estilizadas e prontas para leitura (FR-905): estações ajustadas dimensionadas pela sua incerteza posicional, elipses de erro, observações coloridas conforme a decisão do teste w, a rede medida por tipo de observação e os vetores de correção de coordenadas. Nenhuma é criada sem ser solicitada, de modo que um ajustamento executado para alimentar outro algoritmo não escreve nada a mais.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Exagero das elipses&lt;/b&gt; &amp;mdash; elipses reais são invisíveis na escala do mapa, por isso são desenhadas ampliadas. Deixe em 0 e um fator é ajustado à própria extensão da rede. Qualquer que seja o fator usado, ele é declarado no nome da camada, que é o que chega à legenda: um exagero não declarado transforma uma visualização de qualidade em uma representação enganosa.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A posteriori variance factor</source>
            <translation>Fator de variância a posteriori</translation>
        </message>
        <message>
            <source>A priori variance factor</source>
            <translation>Fator de variância a priori</translation>
        </message>
        <message>
            <source>Adjust network</source>
            <translation>Ajustar rede</translation>
        </message>
        <message>
            <source>Adjusted stations</source>
            <translation>Estações ajustadas</translation>
        </message>
        <message>
            <source>Adjusted stations (table)</source>
            <translation>Estações ajustadas (tabela)</translation>
        </message>
        <message>
            <source>Adjusting…</source>
            <translation>Ajustando…</translation>
        </message>
        <message>
            <source>Adjustment</source>
            <translation>Ajustamento</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Condition number</source>
            <translation>Número de condição</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nível de confiança</translation>
        </message>
        <message>
            <source>Converged in %1 iteration(s); largest correction %2 m.</source>
            <translation>Convergiu em %1 iteração(ões); maior correção %2 m.</translation>
        </message>
        <message>
            <source>Convergence threshold (m)</source>
            <translation>Limiar de convergência (m)</translation>
        </message>
        <message>
            <source>Coordinate frame</source>
            <translation>Referencial de coordenadas</translation>
        </message>
        <message>
            <source>Data snooping</source>
            <translation>Data snooping</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Defeito de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1 (removed by: %2).</source>
            <translation>Defeito de datum: %1 (removido por: %2).</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definição do datum</translation>
        </message>
        <message>
            <source>Datum stations (comma-separated; empty = all)</source>
            <translation>Estações do datum (separadas por vírgula; vazio = todas)</translation>
        </message>
        <message>
            <source>Decision</source>
            <translation>Decisão</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Graus de liberdade</translation>
        </message>
        <message>
            <source>External effect</source>
            <translation>Efeito externo</translation>
        </message>
        <message>
            <source>Fails</source>
            <translation>Falha</translation>
        </message>
        <message>
            <source>Flag</source>
            <translation>Marcação</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_adjust</source>
            <translation>Gerado pelo GeoComp — geocomp:analysis_network_adjust</translation>
        </message>
        <message>
            <source>GeoComp solution (*.json)</source>
            <translation>Solução GeoComp (*.json)</translation>
        </message>
        <message>
            <source>Global test</source>
            <translation>Teste global</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Iterations</source>
            <translation>Iterações</translation>
        </message>
        <message>
            <source>Largest final correction (m)</source>
            <translation>Maior correção final (m)</translation>
        </message>
        <message>
            <source>Least-squares adjustment with the global test, data snooping and reliability.</source>
            <translation>Ajustamento por mínimos quadrados com o teste global, o data snooping e a confiabilidade.</translation>
        </message>
        <message>
            <source>Lower critical value</source>
            <translation>Valor crítico inferior</translation>
        </message>
        <message>
            <source>Maximum iterations</source>
            <translation>Número máximo de iterações</translation>
        </message>
        <message>
            <source>Minimal detectable bias</source>
            <translation>Menor erro detectável</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Rede</translation>
        </message>
        <message>
            <source>Network adjustment report</source>
            <translation>Relatório de ajustamento da rede</translation>
        </message>
        <message>
            <source>Network document</source>
            <translation>Documento da rede</translation>
        </message>
        <message>
            <source>No observation exceeds the w-test critical value.</source>
            <translation>Nenhuma observação excede o valor crítico do teste w.</translation>
        </message>
        <message>
            <source>Nothing has been rejected: removing an observation is your decision.</source>
            <translation>Nada foi rejeitado: remover uma observação é decisão sua.</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observação</translation>
        </message>
        <message>
            <source>Observation equations</source>
            <translation>Equações de observação</translation>
        </message>
        <message>
            <source>Observations exceeding the critical value are candidates, not rejections. Nothing has been removed: investigate the largest, decide, re-adjust, and test again.</source>
            <translation>As observações que excedem o valor crítico são candidatas, não rejeições. Nada foi removido: investigue a maior, decida, reajuste e teste novamente.</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parâmetros</translation>
        </message>
        <message>
            <source>Passes</source>
            <translation>Passa</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Quantity</source>
            <translation>Grandeza</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundância</translation>
        </message>
        <message>
            <source>Reference epoch (decimal year)</source>
            <translation>Época de referência (ano decimal)</translation>
        </message>
        <message>
            <source>Reliability</source>
            <translation>Confiabilidade</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Residual</source>
            <translation>Resíduo</translation>
        </message>
        <message>
            <source>Residuals (table)</source>
            <translation>Resíduos (tabela)</translation>
        </message>
        <message>
            <source>Residuals and data snooping</source>
            <translation>Resíduos e data snooping</translation>
        </message>
        <message>
            <source>Semi-major (m)</source>
            <translation>Semieixo maior (m)</translation>
        </message>
        <message>
            <source>Semi-minor (m)</source>
            <translation>Semieixo menor (m)</translation>
        </message>
        <message>
            <source>Significance for the minimal detectable bias</source>
            <translation>Significância para o menor erro detectável</translation>
        </message>
        <message>
            <source>Solution</source>
            <translation>Solução</translation>
        </message>
        <message>
            <source>Solving method</source>
            <translation>Método de solução</translation>
        </message>
        <message>
            <source>Standardised residual</source>
            <translation>Resíduo padronizado</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Statistic</source>
            <translation>Estatística</translation>
        </message>
        <message>
            <source>Std dev X (m)</source>
            <translation>Desvio padrão X (m)</translation>
        </message>
        <message>
            <source>Std dev Y (m)</source>
            <translation>Desvio padrão Y (m)</translation>
        </message>
        <message>
            <source>Std dev Z (m)</source>
            <translation>Desvio padrão Z (m)</translation>
        </message>
        <message>
            <source>The global test fails: %1</source>
            <translation>O teste global falha: %1</translation>
        </message>
        <message>
            <source>The global test passes.</source>
            <translation>O teste global passa.</translation>
        </message>
        <message>
            <source>Type II error for the minimal detectable bias</source>
            <translation>Erro tipo II para o menor erro detectável</translation>
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
            <translation>Fator de variância %1 com %2 grau(s) de liberdade.</translation>
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
            <translation>não verificável</translation>
        </message>
    </context>
    <context>
        <name>NetworkInspectAlgorithm</name>
        <message>
            <source>%1 station(s), %2 observation(s), %3 active.</source>
            <translation>%1 estação(ões), %2 observação(ões), %3 ativa(s).</translation>
        </message>
        <message>
            <source>(unnamed)</source>
            <translation>(sem nome)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Checks a geodetic network for the problems that stop an adjustment or make its result mean something other than what the user expects: stations that take part in no observation, a network that falls into disconnected pieces each with its own datum, observation types the in-house adjustment does not implement, observations that cannot contribute to the chosen dimensionality, repeated observations, and missing approximate coordinates.&lt;/p&gt;&lt;p&gt;Findings are graded. &lt;b&gt;Blocking&lt;/b&gt; means the adjustment cannot run. &lt;b&gt;Warning&lt;/b&gt; means it can, but the result may not mean what you expect. &lt;b&gt;Information&lt;/b&gt; is worth seeing and is not a problem.&lt;/p&gt;&lt;p&gt;Every finding is reported in one pass, so a network with several problems needs one run rather than one run per problem.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; which of 1D, 2D and 3D the network is to be adjusted in. It decides which observations can contribute and how many observations a station needs.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Fail if the network cannot be adjusted&lt;/b&gt; &amp;mdash; when set, a blocking finding stops the algorithm, so a model that chains inspect into adjust does not proceed on a network that cannot be adjusted. When unset, the algorithm always succeeds and reports its findings, which is what an interactive check wants.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Report&lt;/b&gt; &amp;mdash; destination HTML file. &lt;b&gt;Findings table&lt;/b&gt; &amp;mdash; destination CSV, one row per finding, for use in a model or a spreadsheet.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;CAN_ADJUST&lt;/code&gt; (boolean), &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;, &lt;code&gt;WARNING_COUNT&lt;/code&gt; and &lt;code&gt;COMPONENT_COUNT&lt;/code&gt; &amp;mdash; the number of connected pieces, which is 1 for a network that hangs together.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Verifica em uma rede geodésica os problemas que impedem um ajustamento ou fazem com que seu resultado signifique algo diferente do que o usuário espera: estações que não participam de nenhuma observação, uma rede que se divide em partes desconectadas, cada uma com seu próprio datum, tipos de observação que o ajustamento próprio ainda não implementa, observações que não podem contribuir para a dimensionalidade escolhida, observações repetidas e coordenadas aproximadas ausentes.&lt;/p&gt;&lt;p&gt;As constatações são graduadas. &lt;b&gt;Impeditivo&lt;/b&gt; significa que o ajustamento não pode ser executado. &lt;b&gt;Aviso&lt;/b&gt; significa que pode, mas o resultado talvez não signifique o que se espera. &lt;b&gt;Informação&lt;/b&gt; merece ser vista e não é um problema.&lt;/p&gt;&lt;p&gt;Todas as constatações são relatadas em uma única passagem, de modo que uma rede com vários problemas exige uma execução, e não uma execução por problema.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Rede&lt;/b&gt; &amp;mdash; um documento de rede do GeoComp (JSON).&lt;/p&gt;&lt;p&gt;&lt;b&gt;Referencial de coordenadas&lt;/b&gt; &amp;mdash; se a rede será ajustada em 1D, 2D ou 3D. Isso decide quais observações podem contribuir e quantas observações uma estação necessita.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Falhar se a rede não puder ser ajustada&lt;/b&gt; &amp;mdash; quando marcado, uma constatação impeditiva interrompe o algoritmo, de modo que um modelo que encadeia a inspeção com o ajustamento não prossiga sobre uma rede que não pode ser ajustada. Quando desmarcado, o algoritmo sempre tem sucesso e relata suas constatações, que é o que uma verificação interativa deseja.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; arquivo HTML de destino. &lt;b&gt;Tabela de constatações&lt;/b&gt; &amp;mdash; arquivo CSV de destino, uma linha por constatação, para uso em um modelo ou em uma planilha.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;CAN_ADJUST&lt;/code&gt; (booleano), &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;, &lt;code&gt;WARNING_COUNT&lt;/code&gt; e &lt;code&gt;COMPONENT_COUNT&lt;/code&gt; &amp;mdash; o número de partes conectadas, que é 1 para uma rede que se mantém unida.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Active observations</source>
            <translation>Observações ativas</translation>
        </message>
        <message>
            <source>Blocking</source>
            <translation>Impeditivo</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Check a network for the problems that block or distort an adjustment.</source>
            <translation>Verifica em uma rede os problemas que impedem ou distorcem um ajustamento.</translation>
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
            <translation>Referencial de coordenadas</translation>
        </message>
        <message>
            <source>Each piece has its own datum. They cannot be adjusted together until an observation joins them.</source>
            <translation>Cada parte possui seu próprio datum. Elas não podem ser ajustadas em conjunto enquanto nenhuma observação as unir.</translation>
        </message>
        <message>
            <source>Fail if the network cannot be adjusted</source>
            <translation>Falhar se a rede não puder ser ajustada</translation>
        </message>
        <message>
            <source>Finding</source>
            <translation>Constatação</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>Findings table</source>
            <translation>Tabela de constatações</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_inspect</source>
            <translation>Gerado pelo GeoComp — geocomp:analysis_network_inspect</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Information</source>
            <translation>Informação</translation>
        </message>
        <message>
            <source>Inspect network</source>
            <translation>Inspecionar rede</translation>
        </message>
        <message>
            <source>Inspecting network '%1'…</source>
            <translation>Inspecionando a rede '%1'…</translation>
        </message>
        <message>
            <source>Involves</source>
            <translation>Envolve</translation>
        </message>
        <message>
            <source>Members</source>
            <translation>Integrantes</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Rede</translation>
        </message>
        <message>
            <source>Network document</source>
            <translation>Documento da rede</translation>
        </message>
        <message>
            <source>Network inspection report</source>
            <translation>Relatório de inspeção da rede</translation>
        </message>
        <message>
            <source>No problems found.</source>
            <translation>Nenhum problema encontrado.</translation>
        </message>
        <message>
            <source>Observations</source>
            <translation>Observações</translation>
        </message>
        <message>
            <source>Piece</source>
            <translation>Parte</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Severity</source>
            <translation>Severidade</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estações</translation>
        </message>
        <message>
            <source>Summary</source>
            <translation>Resumo</translation>
        </message>
        <message>
            <source>The network can be adjusted.</source>
            <translation>A rede pode ser ajustada.</translation>
        </message>
        <message>
            <source>The network cannot be adjusted as it stands.</source>
            <translation>A rede não pode ser ajustada como está.</translation>
        </message>
        <message>
            <source>The network has %1 blocking problem(s) and cannot be adjusted.</source>
            <translation>A rede possui %1 problema(s) impeditivo(s) e não pode ser ajustada.</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Aviso</translation>
        </message>
    </context>
    <context>
        <name>NetworkPreAnalysisAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes what a &lt;i&gt;planned&lt;/i&gt; network would achieve. The covariance of the adjusted coordinates depends only on the geometry of the planned observations and on their assumed precisions, so it can be computed before the first observation is made.&lt;/p&gt;&lt;p&gt;The planned observations therefore need only a type, the stations they connect, and an assumed standard deviation. Any values they carry are ignored, which is why the simulation is exact rather than an approximation.&lt;/p&gt;&lt;p&gt;Two things are reported, and both matter. &lt;b&gt;Precision&lt;/b&gt; &amp;mdash; the expected error ellipse and positional uncertainty of each station. &lt;b&gt;Reliability&lt;/b&gt; &amp;mdash; the smallest blunder the design could detect in each observation, and the effect on the coordinates of one that slipped through. A design can be precise and still unable to detect a blunder anywhere, so reporting precision alone gives half the answer.&lt;/p&gt;&lt;p&gt;By default the datum is defined by inner constraints, because a design should be judged on its own geometry rather than through the distortion a particular fixed station imposes.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Network&lt;/b&gt; &amp;mdash; a GeoComp network document (JSON) describing the planned stations and observations.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coordinate frame&lt;/b&gt; &amp;mdash; 1D, 2D or 3D.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Datum definition&lt;/b&gt; &amp;mdash; how the datum defect is removed. &lt;b&gt;Datum stations&lt;/b&gt; &amp;mdash; for a minimum-constraint solution, the comma-separated stations the datum is defined on; empty means all of them.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Required positional uncertainty&lt;/b&gt; &amp;mdash; the specification the design must meet, in metres, at the stated confidence level. Leave at 0 to report without judging.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Confidence level&lt;/b&gt; &amp;mdash; for the error ellipses, between 0 and 1. &lt;b&gt;A priori variance factor&lt;/b&gt; &amp;mdash; the assumed sigma-nought squared. &lt;b&gt;Significance&lt;/b&gt; and &lt;b&gt;Type II error&lt;/b&gt; &amp;mdash; alpha and beta for the minimal detectable bias; the geodetic defaults 0.001 and 0.20 give the familiar non-centrality 4.13.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;MEETS_TOLERANCE&lt;/code&gt;, &lt;code&gt;WORST_STATION&lt;/code&gt;, &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt; and &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; &amp;mdash; observations no blunder in which could ever be detected.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula o que uma rede &lt;i&gt;planejada&lt;/i&gt; alcançaria. A covariância das coordenadas ajustadas depende apenas da geometria das observações planejadas e de suas precisões supostas, de modo que pode ser calculada antes de a primeira observação ser realizada.&lt;/p&gt;&lt;p&gt;As observações planejadas precisam, portanto, apenas de um tipo, das estações que ligam e de um desvio padrão suposto. Quaisquer valores que carreguem são ignorados, e é por isso que a simulação é exata, e não aproximada.&lt;/p&gt;&lt;p&gt;Duas coisas são relatadas, e ambas importam. &lt;b&gt;Precisão&lt;/b&gt; &amp;mdash; a elipse de erros e a incerteza posicional esperadas de cada estação. &lt;b&gt;Confiabilidade&lt;/b&gt; &amp;mdash; o menor erro grosseiro que o projeto conseguiria detectar em cada observação, e o efeito sobre as coordenadas de um que passasse despercebido. Um projeto pode ser preciso e ainda assim incapaz de detectar um erro grosseiro em qualquer lugar, de modo que relatar apenas a precisão dá metade da resposta.&lt;/p&gt;&lt;p&gt;Por padrão o datum é definido por injunções internas, porque um projeto deve ser julgado por sua própria geometria, e não através da distorção que uma estação fixa em particular impõe.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Rede&lt;/b&gt; &amp;mdash; um documento de rede do GeoComp (JSON) descrevendo as estações e observações planejadas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Referencial de coordenadas&lt;/b&gt; &amp;mdash; 1D, 2D ou 3D.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Definição do datum&lt;/b&gt; &amp;mdash; como o defeito de datum é removido. &lt;b&gt;Estações do datum&lt;/b&gt; &amp;mdash; para uma solução com injunção mínima, as estações, separadas por vírgula, sobre as quais o datum é definido; vazio significa todas elas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Incerteza posicional exigida&lt;/b&gt; &amp;mdash; a especificação que o projeto deve atender, em metros, no nível de confiança indicado. Deixe em 0 para relatar sem julgar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Nível de confiança&lt;/b&gt; &amp;mdash; para as elipses de erros, entre 0 e 1. &lt;b&gt;Fator de variância a priori&lt;/b&gt; &amp;mdash; o sigma-zero ao quadrado suposto. &lt;b&gt;Significância&lt;/b&gt; e &lt;b&gt;erro tipo II&lt;/b&gt; &amp;mdash; alfa e beta para o menor erro detectável; os valores geodésicos usuais 0,001 e 0,20 fornecem o familiar parâmetro de não centralidade 4,13.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;MEETS_TOLERANCE&lt;/code&gt;, &lt;code&gt;WORST_STATION&lt;/code&gt;, &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; em metros, &lt;code&gt;DEGREES_OF_FREEDOM&lt;/code&gt; e &lt;code&gt;UNCHECKABLE_COUNT&lt;/code&gt; &amp;mdash; observações em que nenhum erro grosseiro jamais poderia ser detectado.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A priori variance factor</source>
            <translation>Fator de variância a priori</translation>
        </message>
        <message>
            <source>At least one station does not meet the required %1 m.</source>
            <translation>Ao menos uma estação não atende aos %1 m exigidos.</translation>
        </message>
        <message>
            <source>Azimuth (rad)</source>
            <translation>Azimute (rad)</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Component</source>
            <translation>Componente</translation>
        </message>
        <message>
            <source>Compute the precision and reliability a planned network would achieve, before any observation exists.</source>
            <translation>Calcula a precisão e a confiabilidade que uma rede planejada alcançaria, antes que exista qualquer observação.</translation>
        </message>
        <message>
            <source>Confidence level</source>
            <translation>Nível de confiança</translation>
        </message>
        <message>
            <source>Coordinate frame</source>
            <translation>Referencial de coordenadas</translation>
        </message>
        <message>
            <source>Datum defect</source>
            <translation>Defeito de datum</translation>
        </message>
        <message>
            <source>Datum defect: %1</source>
            <translation>Defeito de datum: %1</translation>
        </message>
        <message>
            <source>Datum definition</source>
            <translation>Definição do datum</translation>
        </message>
        <message>
            <source>Datum stations (comma-separated; empty = all)</source>
            <translation>Estações do datum (separadas por vírgula; vazio = todas)</translation>
        </message>
        <message>
            <source>Degrees of freedom</source>
            <translation>Graus de liberdade</translation>
        </message>
        <message>
            <source>Design</source>
            <translation>Projeto</translation>
        </message>
        <message>
            <source>Every station meets the required %1 m.</source>
            <translation>Todas as estações atendem aos %1 m exigidos.</translation>
        </message>
        <message>
            <source>Expected precision</source>
            <translation>Precisão esperada</translation>
        </message>
        <message>
            <source>Expected reliability</source>
            <translation>Confiabilidade esperada</translation>
        </message>
        <message>
            <source>Expected station precision (table)</source>
            <translation>Precisão esperada das estações (tabela)</translation>
        </message>
        <message>
            <source>External effect (m)</source>
            <translation>Efeito externo (m)</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:analysis_network_preanalysis</source>
            <translation>Gerado pelo GeoComp — geocomp:analysis_network_preanalysis</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Minimal detectable bias</source>
            <translation>Menor erro detectável</translation>
        </message>
        <message>
            <source>Network</source>
            <translation>Rede</translation>
        </message>
        <message>
            <source>Network pre-analysis report</source>
            <translation>Relatório de pré-análise da rede</translation>
        </message>
        <message>
            <source>Observation</source>
            <translation>Observação</translation>
        </message>
        <message>
            <source>Parameters</source>
            <translation>Parâmetros</translation>
        </message>
        <message>
            <source>Planned network document</source>
            <translation>Documento da rede planejada</translation>
        </message>
        <message>
            <source>Planned observations</source>
            <translation>Observações planejadas</translation>
        </message>
        <message>
            <source>Positional uncertainty (m)</source>
            <translation>Incerteza posicional (m)</translation>
        </message>
        <message>
            <source>Pre-analyse network design</source>
            <translation>Pré-analisar o projeto da rede</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Redundancy</source>
            <translation>Redundância</translation>
        </message>
        <message>
            <source>Redundancy: %1 (%2 observations, %3 parameters).</source>
            <translation>Redundância: %1 (%2 observações, %3 parâmetros).</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Required positional uncertainty (m, 0 = do not judge)</source>
            <translation>Incerteza posicional exigida (m; 0 = não julgar)</translation>
        </message>
        <message>
            <source>Semi-major (m)</source>
            <translation>Semieixo maior (m)</translation>
        </message>
        <message>
            <source>Semi-minor (m)</source>
            <translation>Semieixo menor (m)</translation>
        </message>
        <message>
            <source>Significance for the minimal detectable bias</source>
            <translation>Significância para o menor erro detectável</translation>
        </message>
        <message>
            <source>Simulating the design…</source>
            <translation>Simulando o projeto…</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>The design does not meet the required %1 m.</source>
            <translation>O projeto não atende aos %1 m exigidos.</translation>
        </message>
        <message>
            <source>The minimal detectable bias is the smallest blunder the design could find in an observation, at the stated significance and power.</source>
            <translation>O menor erro detectável é o menor erro grosseiro que o projeto conseguiria encontrar em uma observação, na significância e no poder indicados.</translation>
        </message>
        <message>
            <source>Type II error for the minimal detectable bias</source>
            <translation>Erro tipo II para o menor erro detectável</translation>
        </message>
        <message>
            <source>Value</source>
            <translation>Valor</translation>
        </message>
        <message>
            <source>Warning</source>
            <translation>Aviso</translation>
        </message>
        <message>
            <source>Worst station: %1 at %2 m.</source>
            <translation>Pior estação: %1, com %2 m.</translation>
        </message>
    </context>
    <context>
        <name>PreprocessAlgorithm</name>
        <message>
            <source>%1 pointing(s) reduced, %2 usable.</source>
            <translation>%1 visada(s) reduzida(s), %2 utilizável(is).</translation>
        </message>
        <message>
            <source>&lt;p&gt;Takes the readings produced by Import field book and runs the whole pre-processing chain: face reduction, instrument corrections, the first-velocity atmospheric correction, the EDM corrections, and the basic reductions to a horizontal distance and a height difference.&lt;/p&gt;&lt;p&gt;Every stage propagates covariance, so each result carries an uncertainty rather than a bare number. The distance and the zenith angle of one pointing are correlated through the common sighting, and that correlation is kept.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The diagnostics are the reason to run this rather than just averaging the two faces.&lt;/b&gt; A face pair reveals the horizontal collimation, the vertical index error and whether the two faces agreed on the distance. A pair whose distances disagree beyond the instrument's own precision is flagged as blocking and left out of the observations: the mean of two distances a metre apart is not a measurement of anything, and passing it on would let a known-bad number acquire a residual as though it were real.&lt;/p&gt;&lt;p&gt;Corrections the instrument already applied are not applied again. Applying a prism constant twice is a silent error of twice the constant, and nothing downstream can detect it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Readings&lt;/b&gt; &amp;mdash; the document Import field book produced. &lt;b&gt;Instrument profiles&lt;/b&gt; &amp;mdash; a profile library (JSON); empty uses a generic total station.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Temperature&lt;/b&gt; (&amp;deg;C), &lt;b&gt;pressure&lt;/b&gt; (hPa) and &lt;b&gt;relative humidity&lt;/b&gt; (%) &amp;mdash; the conditions the distances were measured in. Their uncertainties propagate: a &amp;plusmn; 2 &amp;deg;C error is about &amp;plusmn; 2 ppm, which is 2 mm over a kilometre and nothing at all over twenty metres. The propagation makes that visible instead of assumed.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Apply the atmospheric correction&lt;/b&gt; &amp;mdash; unset it to skip the stage entirely, which is a legitimate choice on short sights and one worth making explicitly.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Collimation tolerance&lt;/b&gt; (rad) and &lt;b&gt;face distance tolerance&lt;/b&gt; (m) &amp;mdash; beyond these a pair is reported. A distance tolerance of 0 derives it from the instrument's own EDM specification, which is the right threshold.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distance/zenith correlation&lt;/b&gt; &amp;mdash; between -1 and 1, or -2 for unknown. Unknown is recorded as an assumption rather than silently treated as zero, and the result is marked approximate.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; a JSON document. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML, with the per-pair diagnostics. &lt;b&gt;Reductions&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;POINTING_COUNT&lt;/code&gt;, &lt;code&gt;USABLE_COUNT&lt;/code&gt; and &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Toma as leituras produzidas por Importar caderneta de campo e executa toda a cadeia de pré-processamento: redução dos pares de posições, correções instrumentais, correção atmosférica de primeira velocidade, correções do MED e as reduções básicas a uma distância horizontal e a um desnível.&lt;/p&gt;&lt;p&gt;Cada etapa propaga covariância, de modo que cada resultado carrega uma incerteza em vez de um número nu. A distância e o ângulo zenital de uma mesma visada são correlacionados pela pontaria comum, e essa correlação é preservada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Os diagnósticos são a razão para executar isto em vez de simplesmente promediar as duas posições.&lt;/b&gt; Um par de posições revela a colimação horizontal, o erro de índice vertical e se as duas posições concordaram quanto à distância. Um par cujas distâncias discordam além da precisão do próprio instrumento é sinalizado como impeditivo e deixado fora das observações: a média de duas distâncias com um metro de diferença não é a medida de coisa alguma, e repassá-la permitiria que um número sabidamente ruim adquirisse um resíduo como se fosse real.&lt;/p&gt;&lt;p&gt;Correções que o instrumento já aplicou não são aplicadas novamente. Aplicar uma constante de prisma duas vezes é um erro silencioso do dobro da constante, e nada a jusante consegue detectá-lo.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Leituras&lt;/b&gt; &amp;mdash; o documento produzido por Importar caderneta de campo. &lt;b&gt;Perfis de instrumento&lt;/b&gt; &amp;mdash; uma biblioteca de perfis (JSON); vazio utiliza uma estação total genérica.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Temperatura&lt;/b&gt; (&amp;deg;C), &lt;b&gt;pressão&lt;/b&gt; (hPa) e &lt;b&gt;umidade relativa&lt;/b&gt; (%) &amp;mdash; as condições em que as distâncias foram medidas. Suas incertezas propagam-se: um erro de &amp;plusmn; 2 &amp;deg;C é cerca de &amp;plusmn; 2 ppm, o que são 2 mm em um quilômetro e absolutamente nada em vinte metros. A propagação torna isso visível em vez de suposto.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Aplicar a correção atmosférica&lt;/b&gt; &amp;mdash; desmarque para pular a etapa inteiramente, o que é uma escolha legítima em visadas curtas e que vale a pena fazer explicitamente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerância da colimação&lt;/b&gt; (rad) e &lt;b&gt;tolerância da distância entre posições&lt;/b&gt; (m) &amp;mdash; além delas um par é relatado. Uma tolerância de distância igual a 0 a deriva da própria especificação do MED do instrumento, que é o limiar correto.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Correlação distância/zenital&lt;/b&gt; &amp;mdash; entre -1 e 1, ou -2 para desconhecida. Desconhecida é registrada como uma suposição em vez de ser silenciosamente tratada como zero, e o resultado é marcado como aproximado.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; um documento JSON. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML, com os diagnósticos por par. &lt;b&gt;Reduções&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;POINTING_COUNT&lt;/code&gt;, &lt;code&gt;USABLE_COUNT&lt;/code&gt; e &lt;code&gt;BLOCKING_COUNT&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Apply the atmospheric correction</source>
            <translation>Aplicar a correção atmosférica</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Collimation spread (")</source>
            <translation>Dispersão da colimação (")</translation>
        </message>
        <message>
            <source>Collimation tolerance (rad)</source>
            <translation>Tolerância da colimação (rad)</translation>
        </message>
        <message>
            <source>Direction (°)</source>
            <translation>Direção (°)</translation>
        </message>
        <message>
            <source>Distance/zenith correlation (-2 = unknown)</source>
            <translation>Correlação distância/zenital (-2 = desconhecida)</translation>
        </message>
        <message>
            <source>Face distance tolerance (m, 0 = from the instrument)</source>
            <translation>Tolerância da distância entre posições (m; 0 = a do instrumento)</translation>
        </message>
        <message>
            <source>Face pairs</source>
            <translation>Pares de posições</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>Generalised pre-processing</source>
            <translation>Pré-processamento generalizado</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_preprocess</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_preprocess</translation>
        </message>
        <message>
            <source>GeoComp reductions (*.json)</source>
            <translation>Reduções GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height difference (m)</source>
            <translation>Desnível (m)</translation>
        </message>
        <message>
            <source>Horizontal distance (m)</source>
            <translation>Distância horizontal (m)</translation>
        </message>
        <message>
            <source>Instrument profiles</source>
            <translation>Perfis de instrumento</translation>
        </message>
        <message>
            <source>Instrumental diagnostics</source>
            <translation>Diagnósticos instrumentais</translation>
        </message>
        <message>
            <source>Mean collimation (")</source>
            <translation>Colimação média (")</translation>
        </message>
        <message>
            <source>Mean index error (")</source>
            <translation>Erro de índice médio (")</translation>
        </message>
        <message>
            <source>Pre-processing report</source>
            <translation>Relatório de pré-processamento</translation>
        </message>
        <message>
            <source>Pressure (hPa)</source>
            <translation>Pressão (hPa)</translation>
        </message>
        <message>
            <source>Pressure uncertainty (hPa)</source>
            <translation>Incerteza da pressão (hPa)</translation>
        </message>
        <message>
            <source>Readings</source>
            <translation>Leituras</translation>
        </message>
        <message>
            <source>Reduce face pairs, apply the instrument, atmospheric and EDM corrections, and report what the pairs revealed.</source>
            <translation>Reduz os pares de posições, aplica as correções instrumentais, atmosféricas e do MED, e relata o que os pares revelaram.</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Reduced pointings</source>
            <translation>Visadas reduzidas</translation>
        </message>
        <message>
            <source>Reducing station %1…</source>
            <translation>Reduzindo a estação %1…</translation>
        </message>
        <message>
            <source>Reductions</source>
            <translation>Reduções</translation>
        </message>
        <message>
            <source>Relative humidity (%)</source>
            <translation>Umidade relativa (%)</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Std dev (mm)</source>
            <translation>Desvio padrão (mm)</translation>
        </message>
        <message>
            <source>Target</source>
            <translation>Alvo</translation>
        </message>
        <message>
            <source>Temperature (°C)</source>
            <translation>Temperatura (°C)</translation>
        </message>
        <message>
            <source>Temperature uncertainty (°C)</source>
            <translation>Incerteza da temperatura (°C)</translation>
        </message>
        <message>
            <source>The correlation between each distance and its zenith angle was not supplied, so they were treated as independent and the results are marked approximate.</source>
            <translation>A correlação entre cada distância e seu ângulo zenital não foi fornecida, de modo que foram tratados como independentes e os resultados estão marcados como aproximados.</translation>
        </message>
        <message>
            <source>Usable</source>
            <translation>Utilizável</translation>
        </message>
        <message>
            <source>Zenith (°)</source>
            <translation>Zenital (°)</translation>
        </message>
        <message>
            <source>no</source>
            <translation>não</translation>
        </message>
        <message>
            <source>yes</source>
            <translation>sim</translation>
        </message>
    </context>
    <context>
        <name>RadiationAlgorithm</name>
        <message>
            <source>%1 point(s) radiated from %2 setup(s).</source>
            <translation>%1 ponto(s) irradiado(s) a partir de %2 estacionamento(s).</translation>
        </message>
        <message>
            <source>3D radiation</source>
            <translation>Irradiação 3D</translation>
        </message>
        <message>
            <source>3D radiation report</source>
            <translation>Relatório da irradiação 3D</translation>
        </message>
        <message>
            <source>&lt;p&gt;Computes three-dimensional coordinates for every point a setup sighted, from the reduced direction, the zenith angle, the slope distance, the two heights and the setup's orientation. Batch radiation of many detail points from one setup is the routine production case and is what this is built for.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The full 3&amp;times;3 covariance is the result, not an extra.&lt;/b&gt; The three coordinates come from one pointing and are strongly correlated through it, and treating them as independent is wrong. The CSV carries the covariance so nothing downstream has to assume otherwise.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The orientation is derived from the pointings wherever it can be.&lt;/b&gt; Any target whose coordinates are known gives the setup's orientation directly, which is how a surveyor orients one: sight a known point and everything else follows. Where several are known the orientations they imply are averaged circularly and their spread is reported &amp;mdash; a large spread means one of the known points is not where it is supposed to be. Where none is known the orientation must be given explicitly.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Known stations&lt;/b&gt; &amp;mdash; a JSON object mapping station names to &lt;code&gt;[easting, northing, up]&lt;/code&gt; in metres. A setup must appear here for its points to be radiated.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Orientations&lt;/b&gt; &amp;mdash; an optional JSON object mapping a setup to its orientation in degrees, for setups that sighted no known point.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument height&lt;/b&gt; and &lt;b&gt;target height&lt;/b&gt; (m) &amp;mdash; used where the readings carry none of their own.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distance/zenith correlation&lt;/b&gt; &amp;mdash; between -1 and 1, or -2 for unknown, which is recorded as an assumption rather than silently treated as zero.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Points&lt;/b&gt; &amp;mdash; JSON, in the shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Points table&lt;/b&gt; &amp;mdash; CSV with the full covariance. Scalars: &lt;code&gt;POINT_COUNT&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula coordenadas tridimensionais para cada ponto que um estacionamento visou, a partir da direção reduzida, do ângulo zenital, da distância inclinada, das duas alturas e da orientação do estacionamento. A irradiação em lote de muitos pontos de detalhe a partir de um estacionamento é o caso rotineiro de produção e é para isso que isto foi construído.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A matriz de covariâncias 3&amp;times;3 completa é o resultado, não um extra.&lt;/b&gt; As três coordenadas provêm de uma única visada e são fortemente correlacionadas por ela, e tratá-las como independentes é errado. O CSV carrega a covariância, de modo que nada a jusante precise supor o contrário.&lt;/p&gt;&lt;p&gt;&lt;b&gt;A orientação é derivada das próprias visadas sempre que possível.&lt;/b&gt; Qualquer alvo cujas coordenadas sejam conhecidas fornece diretamente a orientação do estacionamento, que é como um topógrafo orienta um: visa um ponto conhecido e todo o resto decorre. Onde vários são conhecidos, as orientações que implicam são promediadas circularmente e sua dispersão é relatada &amp;mdash; uma dispersão grande significa que um dos pontos conhecidos não está onde deveria. Onde nenhum é conhecido, a orientação precisa ser informada explicitamente.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; o documento produzido pelo Pré-processamento generalizado. &lt;b&gt;Estações conhecidas&lt;/b&gt; &amp;mdash; um objeto JSON associando nomes de estações a &lt;code&gt;[E, N, altitude]&lt;/code&gt; em metros. Um estacionamento precisa aparecer aqui para que seus pontos sejam irradiados.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Orientações&lt;/b&gt; &amp;mdash; um objeto JSON opcional associando um estacionamento à sua orientação em graus, para estacionamentos que não visaram nenhum ponto conhecido.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura do instrumento&lt;/b&gt; e &lt;b&gt;altura do alvo&lt;/b&gt; (m) &amp;mdash; usadas onde as leituras não trazem as suas.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Correlação distância/zenital&lt;/b&gt; &amp;mdash; entre -1 e 1, ou -2 para desconhecida, que é registrada como uma suposição em vez de ser silenciosamente tratada como zero.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Pontos&lt;/b&gt; &amp;mdash; JSON, no formato que a Rede clássica toma como coordenadas aproximadas. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Tabela de pontos&lt;/b&gt; &amp;mdash; CSV com a covariância completa. Escalares: &lt;code&gt;POINT_COUNT&lt;/code&gt; e &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; em metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Compute 3D coordinates of every point radiated from a known, oriented setup.</source>
            <translation>Calcula as coordenadas 3D de cada ponto irradiado a partir de um estacionamento conhecido e orientado.</translation>
        </message>
        <message>
            <source>Correlation E,N</source>
            <translation>Correlação E,N</translation>
        </message>
        <message>
            <source>Distance/zenith correlation (-2 = unknown)</source>
            <translation>Correlação distância/zenital (-2 = desconhecida)</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>From</source>
            <translation>De</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_radiation</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_radiation</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Instrument height (m)</source>
            <translation>Altura do instrumento (m)</translation>
        </message>
        <message>
            <source>Known stations</source>
            <translation>Estações conhecidas</translation>
        </message>
        <message>
            <source>No point could be radiated. A setup needs known coordinates, an orientation, and at least one pointing with a distance to a station that is not itself known.</source>
            <translation>Nenhum ponto pôde ser irradiado. Um estacionamento precisa de coordenadas conhecidas, uma orientação e ao menos uma visada com distância para uma estação que não seja ela própria conhecida.</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Orientation (°)</source>
            <translation>Orientação (°)</translation>
        </message>
        <message>
            <source>Orientations</source>
            <translation>Orientações</translation>
        </message>
        <message>
            <source>Point</source>
            <translation>Ponto</translation>
        </message>
        <message>
            <source>Points</source>
            <translation>Pontos</translation>
        </message>
        <message>
            <source>Points table</source>
            <translation>Tabela de pontos</translation>
        </message>
        <message>
            <source>Radiated points</source>
            <translation>Pontos irradiados</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Setup orientations</source>
            <translation>Orientações dos estacionamentos</translation>
        </message>
        <message>
            <source>Source</source>
            <translation>Origem</translation>
        </message>
        <message>
            <source>Spread (")</source>
            <translation>Dispersão (")</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Station '%1' has no known coordinates; its points were skipped.</source>
            <translation>A estação '%1' não possui coordenadas conhecidas; seus pontos foram ignorados.</translation>
        </message>
        <message>
            <source>Station '%1' is not three numbers.</source>
            <translation>A estação '%1' não é composta por três números.</translation>
        </message>
        <message>
            <source>Station '%1' sighted no known point and has no orientation given; its points were skipped.</source>
            <translation>A estação '%1' não visou nenhum ponto conhecido e não tem orientação informada; seus pontos foram ignorados.</translation>
        </message>
        <message>
            <source>Std dev E (mm)</source>
            <translation>Desvio padrão E (mm)</translation>
        </message>
        <message>
            <source>Std dev N (mm)</source>
            <translation>Desvio padrão N (mm)</translation>
        </message>
        <message>
            <source>Std dev U (mm)</source>
            <translation>Desvio padrão Alt (mm)</translation>
        </message>
        <message>
            <source>Target height (m)</source>
            <translation>Altura do alvo (m)</translation>
        </message>
        <message>
            <source>The known points sighted from '%1' imply orientations spread over %2 arcsec, against %3 expected from the pointing precision. One of them is probably not where it is recorded, and every point radiated from this setup carries that error.</source>
            <translation>Os pontos conhecidos visados a partir de '%1' implicam orientações com dispersão de %2 segundos de arco, contra %3 esperados pela precisão da pontaria. Provavelmente um deles não está onde está registrado, e todo ponto irradiado desta estação carrega esse erro.</translation>
        </message>
        <message>
            <source>The known stations document is empty.</source>
            <translation>O documento de estações conhecidas está vazio.</translation>
        </message>
        <message>
            <source>The orientations document must map each station to a number of degrees.</source>
            <translation>O documento de orientações deve associar cada estação a um número de graus.</translation>
        </message>
        <message>
            <source>The three coordinates of a radiated point come from one pointing and are correlated through it. The CSV carries the full covariance so nothing downstream has to assume they are independent.</source>
            <translation>As três coordenadas de um ponto irradiado provêm de uma única visada e são correlacionadas por ela. O CSV carrega a matriz de covariâncias completa, de modo que nada a jusante precise supô-las independentes.</translation>
        </message>
        <message>
            <source>Up (m)</source>
            <translation>Altitude (m)</translation>
        </message>
        <message>
            <source>Where a setup sighted several known points they should all imply the same orientation. A large spread means one of them is not where it is supposed to be.</source>
            <translation>Quando um estacionamento visou vários pontos conhecidos, todos devem implicar a mesma orientação. Uma dispersão grande significa que um deles não está onde deveria.</translation>
        </message>
        <message>
            <source>from known points</source>
            <translation>de pontos conhecidos</translation>
        </message>
        <message>
            <source>given</source>
            <translation>informada</translation>
        </message>
    </context>
    <context>
        <name>ResectionAlgorithm</name>
        <message>
            <source>&lt;p&gt;Computes the coordinates of the occupied station from the directions it observed to known points, by least squares over any number of them with the setup's orientation estimated as a third unknown. Three points give a unique solution; more give residuals and a covariance.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The danger circle is detected and refused, not solved.&lt;/b&gt; When the occupied station lies on the circle through three known points, every point on that circle sees the three in the same directions, so they do not determine a position there. A number returned from that configuration looks exactly like a coordinate and is not one, so GeoComp refuses and names the three points involved. Add a fourth point off the circle, or a distance.&lt;/p&gt;&lt;p&gt;Three known points in a straight line define no circle at all, which is a different impossibility and gets its own message.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Occupied station&lt;/b&gt; &amp;mdash; which setup in it to resect.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Known points&lt;/b&gt; &amp;mdash; a JSON object mapping each known station to &lt;code&gt;[easting, northing]&lt;/code&gt; in metres. Only the points the setup actually sighted are used.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Approximate easting&lt;/b&gt; and &lt;b&gt;northing&lt;/b&gt; (m) &amp;mdash; a starting point for the iteration, and what the danger-circle check is evaluated at before any computation begins. Leave both at 0 to start from the centroid of the known points, which converges from anywhere inside the figure.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Position&lt;/b&gt; &amp;mdash; a JSON document in the same shape Classical network takes as approximate coordinates. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. Scalars: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SIGMA_EASTING&lt;/code&gt;, &lt;code&gt;SIGMA_NORTHING&lt;/code&gt; in metres and &lt;code&gt;ORIENTATION&lt;/code&gt; in degrees.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula as coordenadas da estação ocupada a partir das direções que ela observou a pontos conhecidos, por mínimos quadrados sobre qualquer número deles, com a orientação do estacionamento estimada como uma terceira incógnita. Três pontos dão uma solução única; mais dão resíduos e uma covariância.&lt;/p&gt;&lt;p&gt;&lt;b&gt;O círculo perigoso é detectado e recusado, não resolvido.&lt;/b&gt; Quando a estação ocupada está sobre o círculo que passa por três pontos conhecidos, todo ponto desse círculo vê os três nas mesmas direções, de modo que eles não determinam ali uma posição. Um número devolvido a partir dessa configuração parece exatamente uma coordenada e não é uma, de modo que o GeoComp recusa e nomeia os três pontos envolvidos. Acrescente um quarto ponto fora do círculo, ou uma distância.&lt;/p&gt;&lt;p&gt;Três pontos conhecidos em linha reta não definem círculo algum, o que é uma impossibilidade diferente e recebe sua própria mensagem.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; o documento produzido pelo Pré-processamento generalizado. &lt;b&gt;Estação ocupada&lt;/b&gt; &amp;mdash; qual estacionamento nele determinar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Pontos conhecidos&lt;/b&gt; &amp;mdash; um objeto JSON associando cada estação conhecida a &lt;code&gt;[E, N]&lt;/code&gt; em metros. Apenas os pontos que o estacionamento efetivamente visou são utilizados.&lt;/p&gt;&lt;p&gt;&lt;b&gt;E aproximado&lt;/b&gt; e &lt;b&gt;N aproximado&lt;/b&gt; (m) &amp;mdash; um ponto de partida para a iteração, e onde a verificação do círculo perigoso é avaliada antes de qualquer cálculo começar. Deixe ambos em 0 para partir do centroide dos pontos conhecidos, que converge de qualquer lugar dentro da figura.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Posição&lt;/b&gt; &amp;mdash; um documento JSON no mesmo formato que a Rede clássica toma como coordenadas aproximadas. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. Escalares: &lt;code&gt;EASTING&lt;/code&gt;, &lt;code&gt;NORTHING&lt;/code&gt;, &lt;code&gt;SIGMA_EASTING&lt;/code&gt;, &lt;code&gt;SIGMA_NORTHING&lt;/code&gt; em metros e &lt;code&gt;ORIENTATION&lt;/code&gt; em graus.&lt;/p&gt;</translation>
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
            <translation>Correlação</translation>
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
            <translation>Determina a estação ocupada a partir de direções para três ou mais pontos conhecidos.</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_resection</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_resection</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Known point</source>
            <translation>Ponto conhecido</translation>
        </message>
        <message>
            <source>Known point '%1' is not a pair of numbers.</source>
            <translation>O ponto conhecido '%1' não é um par de números.</translation>
        </message>
        <message>
            <source>Known points</source>
            <translation>Pontos conhecidos</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Occupied station</source>
            <translation>Estação ocupada</translation>
        </message>
        <message>
            <source>Position</source>
            <translation>Posição</translation>
        </message>
        <message>
            <source>Property</source>
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Resecting station '%1' from %2 known point(s).</source>
            <translation>Determinando a estação '%1' a partir de %2 ponto(s) conhecido(s).</translation>
        </message>
        <message>
            <source>Resection</source>
            <translation>Interseção inversa</translation>
        </message>
        <message>
            <source>Resection report</source>
            <translation>Relatório da interseção inversa</translation>
        </message>
        <message>
            <source>Residual (")</source>
            <translation>Resíduo (")</translation>
        </message>
        <message>
            <source>Residuals</source>
            <translation>Resíduos</translation>
        </message>
        <message>
            <source>Setup orientation (°)</source>
            <translation>Orientação do estacionamento (°)</translation>
        </message>
        <message>
            <source>Station</source>
            <translation>Estação</translation>
        </message>
        <message>
            <source>Station '%1' sighted only %2 of the known points. A resection needs at least three: two directions cannot fix a position and an orientation.</source>
            <translation>A estação '%1' visou apenas %2 dos pontos conhecidos. Uma interseção inversa precisa de ao menos três: duas direções não determinam uma posição e uma orientação.</translation>
        </message>
        <message>
            <source>Std dev E (mm)</source>
            <translation>Desvio padrão E (mm)</translation>
        </message>
        <message>
            <source>Std dev N (mm)</source>
            <translation>Desvio padrão N (mm)</translation>
        </message>
        <message>
            <source>The known points document is empty.</source>
            <translation>O documento de pontos conhecidos está vazio.</translation>
        </message>
        <message>
            <source>The reduced observations contain no setup at station '%1'.</source>
            <translation>As observações reduzidas não contêm estacionamento na estação '%1'.</translation>
        </message>
        <message>
            <source>Three known points give a unique solution, so the residuals are zero by construction and say nothing about the quality of the observations. A fourth point is what makes them informative.</source>
            <translation>Três pontos conhecidos dão uma solução única, de modo que os resíduos são nulos por construção e nada dizem sobre a qualidade das observações. Um quarto ponto é o que os torna informativos.</translation>
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
            <translation>&lt;p&gt;Gera um relatório descrevendo a instalação do GeoComp: versões do plugin e do QGIS, o ambiente Python, a disponibilidade e as versões dos motores de processamento externos, e cada configuração do GeoComp com seu valor efetivo e o escopo de onde esse valor veio.&lt;/p&gt;&lt;p&gt;Anexe este relatório a um relato de bug ou a um pedido de suporte. Como as configurações são resolvidas nos escopos execução, projeto e global, nessa ordem, a coluna de origem costuma ser o que explica um resultado que difere entre duas máquinas.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; arquivo HTML de destino. Deixe vazio para gravar em um arquivo temporário.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Architecture</source>
            <translation>Arquitetura</translation>
        </message>
        <message>
            <source>Arrives in phase P6</source>
            <translation>Chega na fase P6</translation>
        </message>
        <message>
            <source>Arrives in phase P7</source>
            <translation>Chega na fase P7</translation>
        </message>
        <message>
            <source>Collecting environment information…</source>
            <translation>Coletando informações do ambiente…</translation>
        </message>
        <message>
            <source>Detail</source>
            <translation>Detalhe</translation>
        </message>
        <message>
            <source>Effective value</source>
            <translation>Valor efetivo</translation>
        </message>
        <message>
            <source>Engine</source>
            <translation>Motor</translation>
        </message>
        <message>
            <source>Environment</source>
            <translation>Ambiente</translation>
        </message>
        <message>
            <source>GeoComp system report</source>
            <translation>Relatório do sistema GeoComp</translation>
        </message>
        <message>
            <source>GeoComp version</source>
            <translation>Versão do GeoComp</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Not integrated yet</source>
            <translation>Ainda não integrado</translation>
        </message>
        <message>
            <source>Origin</source>
            <translation>Origem</translation>
        </message>
        <message>
            <source>Platform</source>
            <translation>Plataforma</translation>
        </message>
        <message>
            <source>Processing engines</source>
            <translation>Motores de processamento</translation>
        </message>
        <message>
            <source>Python version</source>
            <translation>Versão do Python</translation>
        </message>
        <message>
            <source>QGIS release</source>
            <translation>Versão de lançamento do QGIS</translation>
        </message>
        <message>
            <source>QGIS version</source>
            <translation>Versão do QGIS</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Report GeoComp versions, engine availability and effective settings.</source>
            <translation>Relata as versões do GeoComp, a disponibilidade dos motores e as configurações efetivas.</translation>
        </message>
        <message>
            <source>Report written.</source>
            <translation>Relatório gravado.</translation>
        </message>
        <message>
            <source>Resolving settings…</source>
            <translation>Resolvendo configurações…</translation>
        </message>
        <message>
            <source>Setting</source>
            <translation>Configuração</translation>
        </message>
        <message>
            <source>Settings</source>
            <translation>Configurações</translation>
        </message>
        <message>
            <source>Settings resolve in the order: run parameter, project, global, built-in default. The origin column shows which scope supplied the effective value.</source>
            <translation>As configurações são resolvidas na ordem: parâmetro da execução, projeto, global, padrão interno. A coluna de origem mostra qual escopo forneceu o valor efetivo.</translation>
        </message>
        <message>
            <source>Status</source>
            <translation>Situação</translation>
        </message>
    </context>
    <context>
        <name>TraverseAlgorithm</name>
        <message>
            <source>%1 leg(s) over %2 station(s).</source>
            <translation>%1 lado(s) sobre %2 estação(ões).</translation>
        </message>
        <message>
            <source>&lt;p&gt;Walks a traverse through the reduced pointings, computes its angular and linear misclosure, compares them against the configured tolerances, and distributes the misclosure by the compass (Bowditch) or transit rule.&lt;/p&gt;&lt;p&gt;&lt;b&gt;The classical rules are not least squares.&lt;/b&gt; They produce no residuals, no redundancy numbers and no rigorous covariance, so their coordinates are labelled approximate and the uncertainties reported are the misclosure spread over the traverse rather than a propagated variance. For the rigorous path use Classical network. Running the same data both ways is the point: the student sees what the classical rule approximates.&lt;/p&gt;&lt;p&gt;&lt;b&gt;An open traverse has no misclosure at all&lt;/b&gt;, which is different from a misclosure of zero. Nothing about it can be checked and a blunder anywhere in it is invisible, so GeoComp reports that rather than a perfect closure.&lt;/p&gt;&lt;p&gt;Whichever rule is used, the result is also a good set of approximate coordinates for a rigorous network adjustment, which is the other reason to run it.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Route&lt;/b&gt; &amp;mdash; the stations in order, comma-separated, for example &lt;code&gt;1,2,3,4,1&lt;/code&gt;. &lt;b&gt;Initial backsight&lt;/b&gt; &amp;mdash; the station the first setup sighted before turning the angle.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Start easting&lt;/b&gt;, &lt;b&gt;start northing&lt;/b&gt; (m) and &lt;b&gt;start azimuth&lt;/b&gt; (degrees) &amp;mdash; the known point and the orientation of the initial backsight.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Kind&lt;/b&gt; &amp;mdash; closed (returns to its start), connected (arrives at another known point) or open. &lt;b&gt;Closing easting&lt;/b&gt;, &lt;b&gt;closing northing&lt;/b&gt; and &lt;b&gt;closing azimuth&lt;/b&gt; &amp;mdash; for a connected traverse.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distribution&lt;/b&gt; &amp;mdash; compass, transit, or none to report the misclosure without absorbing it, which is what a check measurement is for.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Angular tolerance per station&lt;/b&gt; (degrees) and &lt;b&gt;required relative precision&lt;/b&gt; (the N in 1:N).&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Coordinates&lt;/b&gt; &amp;mdash; a JSON document ready to use as the approximate coordinates for Classical network. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Stations&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;ANGULAR_MISCLOSURE&lt;/code&gt; in degrees, &lt;code&gt;LINEAR_MISCLOSURE&lt;/code&gt; in metres, &lt;code&gt;RELATIVE_PRECISION&lt;/code&gt; and &lt;code&gt;WITHIN_TOLERANCE&lt;/code&gt;.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Percorre uma poligonal através das visadas reduzidas, calcula seus erros angular e linear de fechamento, compara-os com as tolerâncias configuradas e distribui o erro pela regra do compasso (Bowditch) ou do trânsito.&lt;/p&gt;&lt;p&gt;&lt;b&gt;As regras clássicas não são mínimos quadrados.&lt;/b&gt; Não produzem resíduos, nem números de redundância, nem covariância rigorosa, de modo que suas coordenadas são rotuladas como aproximadas e as incertezas relatadas são o erro de fechamento espalhado pela poligonal, e não uma variância propagada. Para o caminho rigoroso use Rede clássica. Executar os mesmos dados dos dois modos é o objetivo: o estudante vê o que a regra clássica aproxima.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Uma poligonal aberta não possui erro de fechamento algum&lt;/b&gt;, o que é diferente de um erro de fechamento nulo. Nada nela pode ser verificado e um erro grosseiro em qualquer ponto é invisível, de modo que o GeoComp relata isso em vez de um fechamento perfeito.&lt;/p&gt;&lt;p&gt;Qualquer que seja a regra utilizada, o resultado também é um bom conjunto de coordenadas aproximadas para um ajustamento rigoroso de rede, que é a outra razão para executá-la.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; o documento produzido pelo Pré-processamento generalizado. &lt;b&gt;Percurso&lt;/b&gt; &amp;mdash; as estações em ordem, separadas por vírgula, por exemplo &lt;code&gt;1,2,3,4,1&lt;/code&gt;. &lt;b&gt;Ré inicial&lt;/b&gt; &amp;mdash; a estação que o primeiro estacionamento visou antes de girar o ângulo.&lt;/p&gt;&lt;p&gt;&lt;b&gt;E inicial&lt;/b&gt;, &lt;b&gt;N inicial&lt;/b&gt; (m) e &lt;b&gt;azimute inicial&lt;/b&gt; (graus) &amp;mdash; o ponto conhecido e a orientação da ré inicial.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tipo&lt;/b&gt; &amp;mdash; fechada (retorna ao seu início), enquadrada (chega a outro ponto conhecido) ou aberta. &lt;b&gt;E de chegada&lt;/b&gt;, &lt;b&gt;N de chegada&lt;/b&gt; e &lt;b&gt;azimute de chegada&lt;/b&gt; &amp;mdash; para uma poligonal enquadrada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Distribuição&lt;/b&gt; &amp;mdash; compasso, trânsito, ou nenhuma para relatar o erro sem absorvê-lo, que é para o que serve uma medida de verificação.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Tolerância angular por estação&lt;/b&gt; (graus) e &lt;b&gt;precisão relativa exigida&lt;/b&gt; (o N em 1:N).&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Coordenadas&lt;/b&gt; &amp;mdash; um documento JSON pronto para uso como coordenadas aproximadas da Rede clássica. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Estações&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;ANGULAR_MISCLOSURE&lt;/code&gt; em graus, &lt;code&gt;LINEAR_MISCLOSURE&lt;/code&gt; em metros, &lt;code&gt;RELATIVE_PRECISION&lt;/code&gt; e &lt;code&gt;WITHIN_TOLERANCE&lt;/code&gt;.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>A classical distribution is not least squares: it produces no residuals and no rigorous covariance, so these coordinates are approximate. For the rigorous path, use Classical network on the same data.</source>
            <translation>Uma distribuição clássica não é mínimos quadrados: não produz resíduos nem covariância rigorosa, de modo que estas coordenadas são aproximadas. Para o caminho rigoroso, use Rede clássica sobre os mesmos dados.</translation>
        </message>
        <message>
            <source>A traverse needs at least two stations in its route.</source>
            <translation>Uma poligonal precisa de ao menos duas estações em seu percurso.</translation>
        </message>
        <message>
            <source>Angular misclosure %1 arcsec.</source>
            <translation>Erro angular de fechamento %1 segundos de arco.</translation>
        </message>
        <message>
            <source>Angular misclosure (")</source>
            <translation>Erro angular de fechamento (")</translation>
        </message>
        <message>
            <source>Angular tolerance per station (°)</source>
            <translation>Tolerância angular por estação (°)</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Closed</source>
            <translation>Fechada</translation>
        </message>
        <message>
            <source>Closes to 1:%1.</source>
            <translation>Fecha em 1:%1.</translation>
        </message>
        <message>
            <source>Closing azimuth (°)</source>
            <translation>Azimute de chegada (°)</translation>
        </message>
        <message>
            <source>Closing easting (m)</source>
            <translation>E de chegada (m)</translation>
        </message>
        <message>
            <source>Closing northing (m)</source>
            <translation>N de chegada (m)</translation>
        </message>
        <message>
            <source>Compass (Bowditch)</source>
            <translation>Compasso (Bowditch)</translation>
        </message>
        <message>
            <source>Compute a traverse's misclosures and distribute them by a classical rule.</source>
            <translation>Calcula os erros de fechamento de uma poligonal e os distribui por uma regra clássica.</translation>
        </message>
        <message>
            <source>Connected</source>
            <translation>Enquadrada</translation>
        </message>
        <message>
            <source>Coordinates</source>
            <translation>Coordenadas</translation>
        </message>
        <message>
            <source>Distribution</source>
            <translation>Distribuição</translation>
        </message>
        <message>
            <source>Easting (m)</source>
            <translation>E (m)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_traverse</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_traverse</translation>
        </message>
        <message>
            <source>GeoComp coordinates (*.json)</source>
            <translation>Coordenadas GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Initial backsight station</source>
            <translation>Estação de ré inicial</translation>
        </message>
        <message>
            <source>Kind</source>
            <translation>Tipo</translation>
        </message>
        <message>
            <source>Linear misclosure (m)</source>
            <translation>Erro linear de fechamento (m)</translation>
        </message>
        <message>
            <source>No closing azimuth was given and none can be inferred, so the angular misclosure is not computed and the angles are not checked. Give the closing azimuth to check them.</source>
            <translation>Nenhum azimute de fechamento foi informado e nenhum pode ser inferido, portanto o erro de fechamento angular não é calculado e os ângulos não são verificados. Informe o azimute de fechamento para verificá-los.</translation>
        </message>
        <message>
            <source>No closing azimuth was given. This loop backsights '%1' and returns from it, so it closes on the line the start azimuth refers to, and that is what the angular misclosure is measured against.</source>
            <translation>Nenhum azimute de fechamento foi informado. Esta poligonal fechada visa a ré '%1' e retorna dela, portanto fecha sobre a mesma linha a que se refere o azimute inicial, e é contra ela que o erro de fechamento angular é medido.</translation>
        </message>
        <message>
            <source>None — report the misclosure only</source>
            <translation>Nenhuma — apenas relatar o erro de fechamento</translation>
        </message>
        <message>
            <source>Northing (m)</source>
            <translation>N (m)</translation>
        </message>
        <message>
            <source>Open</source>
            <translation>Aberta</translation>
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
            <translation>Propriedade</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Relative precision</source>
            <translation>Precisão relativa</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Required relative precision (1:N)</source>
            <translation>Precisão relativa exigida (1:N)</translation>
        </message>
        <message>
            <source>Route (comma-separated stations)</source>
            <translation>Percurso (estações separadas por vírgula)</translation>
        </message>
        <message>
            <source>Start azimuth (°)</source>
            <translation>Azimute inicial (°)</translation>
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
            <translation>Estação</translation>
        </message>
        <message>
            <source>Station '%1' has no usable pointing to '%2'.</source>
            <translation>A estação '%1' não possui visada utilizável para '%2'.</translation>
        </message>
        <message>
            <source>Stations</source>
            <translation>Estações</translation>
        </message>
        <message>
            <source>The initial backsight station is required: it is what the start azimuth refers to.</source>
            <translation>A estação de ré inicial é obrigatória: é a ela que o azimute inicial se refere.</translation>
        </message>
        <message>
            <source>The pointing from '%1' to '%2' carries no distance.</source>
            <translation>A visada de '%1' para '%2' não possui distância.</translation>
        </message>
        <message>
            <source>The reduced observations contain no setup at station '%1'.</source>
            <translation>As observações reduzidas não contêm estacionamento na estação '%1'.</translation>
        </message>
        <message>
            <source>Transit</source>
            <translation>Trânsito</translation>
        </message>
        <message>
            <source>Traverse</source>
            <translation>Poligonal</translation>
        </message>
        <message>
            <source>Traverse report</source>
            <translation>Relatório da poligonal</translation>
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
            <translation>%1 desnível(is) calculado(s).</translation>
        </message>
        <message>
            <source>'Refraction surviving' is the fraction of the refraction uncertainty the method did not remove: 0 means the two sights were equal and it cancelled entirely, 1 means it did not cancel at all. It depends only on the two sight lengths, which is what makes it something the surveyor controls.</source>
            <translation>'Refração remanescente' é a fração da incerteza da refração que o método não removeu: 0 significa que as duas visadas eram iguais e ela cancelou inteiramente, 1 significa que não cancelou de modo algum. Depende apenas dos dois comprimentos de visada, que é o que a torna algo sob controle do topógrafo.</translation>
        </message>
        <message>
            <source>&lt;p&gt;Computes height differences from the reduced zenith angles and slope distances, with the curvature-and-refraction correction applied and its uncertainty propagated. On a 100 m sight the correction is 0.7 mm; at 1 km it is 68 mm; at 5 km it is 1.7 m.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radial&lt;/b&gt; computes a height difference from the occupied station to each target it sighted. The instrument height, the target height and the refraction all contribute in full.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Leap-frog&lt;/b&gt; takes each setup that sighted exactly two targets as a free station between them, and produces one height difference from the first to the second. Two things then cancel. The &lt;b&gt;instrument height cancels exactly&lt;/b&gt; and never has to be measured, which removes what is routinely the dominant error in a short trigonometric height. And the &lt;b&gt;refraction largely cancels&lt;/b&gt;, because both sights pass through the same air at the same moment and share one coefficient &amp;mdash; a shared dependence carried through a single Jacobian, so the cancellation shows in the uncertainty and not only in the value. With balanced sights the refraction uncertainty leaves the result entirely.&lt;/p&gt;&lt;p&gt;How much cancels depends on how equal the two sights are, which the surveyor controls by where they stand, so an imbalanced pair is reported along with the fraction of the refraction uncertainty that survived.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Reduced observations&lt;/b&gt; &amp;mdash; the document Generalised pre-processing produced. &lt;b&gt;Mode&lt;/b&gt; &amp;mdash; radial or leap-frog.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Instrument height&lt;/b&gt; and &lt;b&gt;target height&lt;/b&gt; (m) &amp;mdash; used in radial mode where the readings do not carry their own. Ignored in leap-frog mode, where the instrument height cancels.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Refraction coefficient&lt;/b&gt; and its &lt;b&gt;uncertainty&lt;/b&gt; &amp;mdash; dimensionless. The coefficient is poorly known and varies through the day, and it is the dominant error source on long sights, which is why its uncertainty is an input rather than an assumption.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Earth radius&lt;/b&gt; (m) and &lt;b&gt;sight imbalance tolerance&lt;/b&gt; (as a fraction of the longer sight).&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Height differences&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Report&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Differences&lt;/b&gt; &amp;mdash; CSV. Scalars: &lt;code&gt;RESULT_COUNT&lt;/code&gt; and &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; in metres.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Calcula desníveis a partir dos ângulos zenitais e das distâncias inclinadas reduzidos, com a correção de curvatura e refração aplicada e sua incerteza propagada. Em uma visada de 100 m a correção é de 0,7 mm; em 1 km é de 68 mm; em 5 km é de 1,7 m.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Radial&lt;/b&gt; calcula um desnível da estação ocupada para cada alvo que ela visou. A altura do instrumento, a altura do alvo e a refração contribuem todas integralmente.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Leap-frog&lt;/b&gt; toma cada estacionamento que visou exatamente dois alvos como uma estação livre entre eles, e produz um desnível do primeiro para o segundo. Duas coisas então se cancelam. A &lt;b&gt;altura do instrumento cancela-se exatamente&lt;/b&gt; e nunca precisa ser medida, o que remove o que é rotineiramente o erro dominante em um desnível trigonométrico curto. E a &lt;b&gt;refração cancela-se em grande parte&lt;/b&gt;, porque ambas as visadas atravessam o mesmo ar no mesmo instante e compartilham um coeficiente &amp;mdash; uma dependência compartilhada conduzida por um único jacobiano, de modo que o cancelamento aparece na incerteza e não apenas no valor. Com visadas equilibradas a incerteza da refração deixa o resultado inteiramente.&lt;/p&gt;&lt;p&gt;Quanto se cancela depende de quão iguais são as duas visadas, o que o topógrafo controla por onde se posiciona, de modo que um par desequilibrado é relatado junto com a fração da incerteza da refração que sobreviveu.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Observações reduzidas&lt;/b&gt; &amp;mdash; o documento produzido pelo Pré-processamento generalizado. &lt;b&gt;Modo&lt;/b&gt; &amp;mdash; radial ou leap-frog.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Altura do instrumento&lt;/b&gt; e &lt;b&gt;altura do alvo&lt;/b&gt; (m) &amp;mdash; usadas no modo radial onde as leituras não trazem as suas. Ignoradas no modo leap-frog, onde a altura do instrumento se cancela.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Coeficiente de refração&lt;/b&gt; e sua &lt;b&gt;incerteza&lt;/b&gt; &amp;mdash; adimensionais. O coeficiente é mal conhecido e varia ao longo do dia, e é a fonte de erro dominante em visadas longas, razão pela qual sua incerteza é uma entrada e não uma suposição.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Raio da Terra&lt;/b&gt; (m) e &lt;b&gt;tolerância de desequilíbrio das visadas&lt;/b&gt; (como fração da visada mais longa).&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Desníveis&lt;/b&gt; &amp;mdash; JSON. &lt;b&gt;Relatório&lt;/b&gt; &amp;mdash; HTML. &lt;b&gt;Desníveis&lt;/b&gt; &amp;mdash; CSV. Escalares: &lt;code&gt;RESULT_COUNT&lt;/code&gt; e &lt;code&gt;WORST_UNCERTAINTY&lt;/code&gt; em metros.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>CSV files (*.csv)</source>
            <translation>Arquivos CSV (*.csv)</translation>
        </message>
        <message>
            <source>Differences</source>
            <translation>Desníveis</translation>
        </message>
        <message>
            <source>Earth radius (m)</source>
            <translation>Raio da Terra (m)</translation>
        </message>
        <message>
            <source>Findings</source>
            <translation>Constatações</translation>
        </message>
        <message>
            <source>From</source>
            <translation>De</translation>
        </message>
        <message>
            <source>Generated by GeoComp — geocomp:totalstation_trig_levelling</source>
            <translation>Gerado pelo GeoComp — geocomp:totalstation_trig_levelling</translation>
        </message>
        <message>
            <source>GeoComp height differences (*.json)</source>
            <translation>Desníveis GeoComp (*.json)</translation>
        </message>
        <message>
            <source>HTML files (*.html)</source>
            <translation>Arquivos HTML (*.html)</translation>
        </message>
        <message>
            <source>Height difference (m)</source>
            <translation>Desnível (m)</translation>
        </message>
        <message>
            <source>Height differences</source>
            <translation>Desníveis</translation>
        </message>
        <message>
            <source>Height differences from zenith angles and distances, radial or leap-frog.</source>
            <translation>Desníveis a partir de ângulos zenitais e distâncias, radial ou leap-frog.</translation>
        </message>
        <message>
            <source>Instrument height (m)</source>
            <translation>Altura do instrumento (m)</translation>
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
            <translation>Nenhum desnível pôde ser calculado. O modo radial precisa de visadas com distância; o modo leap-frog precisa de estacionamentos que visaram exatamente dois alvos.</translation>
        </message>
        <message>
            <source>Radial</source>
            <translation>Radial</translation>
        </message>
        <message>
            <source>Reduced observations</source>
            <translation>Observações reduzidas</translation>
        </message>
        <message>
            <source>Refraction coefficient</source>
            <translation>Coeficiente de refração</translation>
        </message>
        <message>
            <source>Refraction coefficient uncertainty</source>
            <translation>Incerteza do coeficiente de refração</translation>
        </message>
        <message>
            <source>Refraction surviving</source>
            <translation>Refração remanescente</translation>
        </message>
        <message>
            <source>Report</source>
            <translation>Relatório</translation>
        </message>
        <message>
            <source>Sight imbalance (m)</source>
            <translation>Desequilíbrio das visadas (m)</translation>
        </message>
        <message>
            <source>Sight imbalance tolerance</source>
            <translation>Tolerância de desequilíbrio das visadas</translation>
        </message>
        <message>
            <source>Std dev (mm)</source>
            <translation>Desvio padrão (mm)</translation>
        </message>
        <message>
            <source>Target height (m)</source>
            <translation>Altura do alvo (m)</translation>
        </message>
        <message>
            <source>To</source>
            <translation>Para</translation>
        </message>
        <message>
            <source>Trigonometric levelling</source>
            <translation>Nivelamento trigonométrico</translation>
        </message>
        <message>
            <source>Trigonometric levelling report</source>
            <translation>Relatório do nivelamento trigonométrico</translation>
        </message>
    </context>
    <context>
        <name>TutorialDatasetAlgorithm</name>
        <message>
            <source>%1 file(s) copied to %2.</source>
            <translation>%1 arquivo(s) copiado(s) para %2.</translation>
        </message>
        <message>
            <source>%1 file(s) were already there and were left alone: %2. Turn on Overwrite to replace them.</source>
            <translation>%1 arquivo(s) já estavam lá e foram mantidos: %2. Ative Sobrescrever para substituí-los.</translation>
        </message>
        <message>
            <source>(none shipped)</source>
            <translation>(nenhum incluído)</translation>
        </message>
        <message>
            <source>&lt;p&gt;Copies a reference dataset that ships with GeoComp into a directory of your choosing, with its tutorial. The plugin's own directory is usually not writable, and outputs have to go somewhere.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RD-01&lt;/b&gt; is the author's own total-station triangle: three stations, six pointings, each observed on both faces. It is the smallest complete survey there is and it exercises the entire total-station chain, from field book to adjusted network.&lt;/p&gt;&lt;p&gt;&lt;b&gt;It contains two real errors, and that is the point.&lt;/b&gt; One face pair disagrees by exactly 1.000 m in distance &amp;mdash; a transcription blunder, which pre-processing blocks rather than averages away. And the network's global test fails, correctly: the distances disagree between the two ends by far more than the instrument's stated precision allows. A tutorial in which nothing is wrong teaches you which buttons to press; this one teaches you what the software is for.&lt;/p&gt;&lt;p&gt;The copied &lt;code&gt;README.md&lt;/code&gt; walks through the whole chain and explains both, along with why a network with no known point and no azimuth can only be adjusted with inner constraints.&lt;/p&gt;&lt;h3&gt;Parameters&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Dataset&lt;/b&gt; &amp;mdash; which shipped dataset to install. &lt;b&gt;Destination folder&lt;/b&gt; &amp;mdash; where to put it; a subfolder named after the dataset is created inside. &lt;b&gt;Overwrite&lt;/b&gt; &amp;mdash; replace files already there, which is off by default so an edited tutorial file is not lost.&lt;/p&gt;&lt;h3&gt;Outputs&lt;/h3&gt;&lt;p&gt;&lt;code&gt;OUTPUT_DIRECTORY&lt;/code&gt; &amp;mdash; where the files landed. &lt;code&gt;FILE_COUNT&lt;/code&gt; &amp;mdash; how many were copied.&lt;/p&gt;</source>
            <translation>&lt;p&gt;Copia um conjunto de dados de referência que acompanha o GeoComp para um diretório à sua escolha, junto com o tutorial. O próprio diretório do plugin normalmente não é gravável, e as saídas precisam ir para algum lugar.&lt;/p&gt;&lt;p&gt;&lt;b&gt;RD-01&lt;/b&gt; é o triângulo de estação total do próprio autor: três estações, seis visadas, cada uma observada nas duas posições da luneta. É o levantamento completo mais simples que existe e exercita toda a cadeia de estação total, da caderneta de campo à rede ajustada.&lt;/p&gt;&lt;p&gt;&lt;b&gt;Ele contém dois erros reais, e é justamente esse o ponto.&lt;/b&gt; Um par de posições diverge em exatamente 1,000 m na distância &amp;mdash; um erro de transcrição, que o pré-processamento bloqueia em vez de dissolver na média. E o teste global da rede falha, corretamente: as distâncias divergem entre as duas extremidades muito mais do que a precisão declarada do instrumento permite. Um tutorial em que nada está errado ensina quais botões apertar; este ensina para que serve o programa.&lt;/p&gt;&lt;p&gt;O &lt;code&gt;README.md&lt;/code&gt; copiado percorre toda a cadeia e explica os dois casos, além de por que uma rede sem ponto conhecido e sem azimute só pode ser ajustada com injunções internas.&lt;/p&gt;&lt;h3&gt;Parâmetros&lt;/h3&gt;&lt;p&gt;&lt;b&gt;Conjunto de dados&lt;/b&gt; &amp;mdash; qual conjunto instalar. &lt;b&gt;Pasta de destino&lt;/b&gt; &amp;mdash; onde colocá-lo; uma subpasta com o nome do conjunto é criada dentro dela. &lt;b&gt;Sobrescrever&lt;/b&gt; &amp;mdash; substituir arquivos já existentes, desativado por padrão para que um arquivo de tutorial editado não se perca.&lt;/p&gt;&lt;h3&gt;Saídas&lt;/h3&gt;&lt;p&gt;&lt;code&gt;OUTPUT_DIRECTORY&lt;/code&gt; &amp;mdash; onde os arquivos foram parar. &lt;code&gt;FILE_COUNT&lt;/code&gt; &amp;mdash; quantos foram copiados.&lt;/p&gt;</translation>
        </message>
        <message>
            <source>Copy a shipped reference dataset and its tutorial to a folder you choose.</source>
            <translation>Copia um conjunto de dados de referência e seu tutorial para uma pasta à sua escolha.</translation>
        </message>
        <message>
            <source>Dataset</source>
            <translation>Conjunto de dados</translation>
        </message>
        <message>
            <source>Destination folder</source>
            <translation>Pasta de destino</translation>
        </message>
        <message>
            <source>Install tutorial dataset</source>
            <translation>Instalar conjunto de dados do tutorial</translation>
        </message>
        <message>
            <source>No datasets ship with this build. That means the package was built without its resources, which is a packaging fault rather than something you can correct here.</source>
            <translation>Nenhum conjunto de dados acompanha esta compilação. Isso significa que o pacote foi construído sem seus recursos, o que é uma falha de empacotamento e não algo que você possa corrigir aqui.</translation>
        </message>
        <message>
            <source>Overwrite existing files</source>
            <translation>Sobrescrever arquivos existentes</translation>
        </message>
        <message>
            <source>Start with README.md there: it walks through the whole chain.</source>
            <translation>Comece pelo README.md que está lá: ele percorre toda a cadeia.</translation>
        </message>
        <message>
            <source>The destination folder '%1' does not exist.</source>
            <translation>A pasta de destino '%1' não existe.</translation>
        </message>
    </context>
</TS>
