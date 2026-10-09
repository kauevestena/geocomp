# RD-01 — um triângulo de estação total, com dois erros reais

**Conjunto de dados de referência RD-01** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952). Versão em
português do README.md; os números, os nomes e os valores digitados são os mesmos.

Três estações, seis visadas, cada uma observada nas duas posições da luneta. É o menor levantamento completo de
estação total que existe, e exercita toda a primeira fatia vertical do GeoComp: importação da caderneta de
campo, redução das posições, as reduções básicas, montagem da rede, testes estatísticos e ajustamento.

São também **dados reais com dois erros reais**, e é por isso que este é o tutorial. Um tutorial em que nada
está errado ensina quais botões apertar. Este ensina para que serve o programa.

**Números.** No texto, os números usam a vírgula decimal. Os valores entre crases são digitados como
aparecem, e o que o GeoComp escreve no registro é citado como ele o escreve, com ponto.

---

## Os arquivos

| Arquivo | O que é |
|---|---|
| `raw_data.csv` | A caderneta de campo como foi registrada: estação, ré, vante, posição da luneta, ângulos sexagesimais, distância inclinada, alturas do instrumento e do alvo |
| `mapping.json` | Qual coluna alimenta qual campo (FR-160). Definido uma vez, reutilizável em toda exportação do mesmo instrumento |
| `profiles.json` | As precisões nominais do instrumento. Sem elas o GeoComp se recusa a importar, em vez de inventar um sigma |
| `approximate.json` | Coordenadas iniciais do ajustamento, num referencial local com a estação 1 na origem |

As coordenadas são locais, não projetadas. O RD-01 não tem ponto conhecido nem azimute medido, então nada o
liga a um datum — veja *A rede é livre* mais abaixo.

---

## Passo a passo

O documento que cada passo escreve é a entrada do seguinte, então o tutorial inteiro também se monta como um
modelo no modelador gráfico.

### 1. Importar caderneta de campo — `geocomp:totalstation_import_fieldbook`

- **Caderneta de campo**: `raw_data.csv`
- **Mapeamento de campos**: `mapping.json`
- **Perfis de instrumento**: `profiles.json`

Doze registros, três estacionamentos, nenhum rejeitado. Cada leitura sai com uma incerteza, tirada do perfil do
instrumento: as incertezas são atribuídas na fronteira, porque um valor que entra no sistema sem uma nunca pode
adquiri-la honestamente depois.

**Experimente:** rode de novo sem os perfis. Ele se recusa, e diz do que precisa. O GeoComp não inventa um
desvio-padrão, porque um sigma inventado se propaga por todos os números seguintes e transforma uma qualidade
desconhecida numa qualidade declarada.

### 2. Pré-processamento generalizado — `geocomp:totalstation_preprocess`

- **Leituras**: o documento que o passo 1 escreveu
- **Perfis de instrumento**: `profiles.json` de novo

Os perfis são necessários uma segunda vez, e isso não é descuido: as leituras registram *qual* instrumento as
fez, e reduzir um par de posições precisa da colimação, do índice vertical e das constantes do distanciômetro
desse instrumento. O GeoComp não põe as de outro no lugar — recusa e diz o nome do que procurava, porque uma
substituição silenciosa deixaria errado todo número seguinte de um jeito que nada poderia detectar.

Seis visadas reduzidas a partir de doze leituras. **Cinco são utilizáveis e uma está bloqueada**, e a bloqueada é
o primeiro erro real: a visada da estação 3 para a estação 2, cujas duas posições discordam na distância em
1,000 m. O registro diz, da estação 3:

> As duas posições para 2 discordam na distância em +1.0000 m, contra uma tolerância de 0.0087 m. A média das
> duas não é medida de coisa alguma; verifique a caderneta de campo antes de usar este par.

Um par de posições mede a mesma linha duas vezes. Os ângulos concordam em segundos; as distâncias diferem em um
metro redondo. Isso não é ruído, é um erro de transcrição — um algarismo anotado errado na caderneta. Fazer a
média dos dois esconderia um erro de meio metro na média e produziria uma distância plausível e errada. O
GeoComp bloqueia a visada e diz por quê, e as outras cinco seguem adiante.

**Olhe o relatório.** Os erros de colimação e de índice vertical são estimados a partir dos próprios pares de
posições e relatados por estacionamento, que é para isso que serve a segunda posição: observar nas duas os
cancela, e o tamanho deles diz se o instrumento precisa de retificação.

### 3. Rede clássica — `geocomp:totalstation_network`

- **Observações reduzidas**: o documento que o passo 2 escreveu
- **Coordenadas aproximadas**: `approximate.json`
- **Dimensão**: *2D — planimétrico*
- **Definição do datum**: *Injunção interna — rede livre, traço mínimo*
- **Código de SRC, por exemplo EPSG:31982**: `EPSG:31982` (UTM 22S), ou o SRC projetado da sua própria região

As coordenadas do RD-01 são locais, mas um SRC continua obrigatório e o GeoComp não inventa um: coordenadas
ajustadas não significam nada sem saber *em que* são coordenadas, e um palpite ficaria registrado na solução
como se alguém o tivesse escolhido.

O ajustamento converge com **4 graus de liberdade**, e **o teste global falha**, com um fator de variância de
**140,67**. Essa é a resposta correta, e a segunda coisa que este conjunto de dados ensina.

As distâncias entre as estações discordam em cerca de 15 mm conforme a ponta de onde foram medidas, contra a
precisão de 2 mm que o perfil do instrumento declara. O teste global compara os resíduos com o modelo
estocástico, e o modelo diz que os dados deveriam ser melhores do que são. Algo está errado: ou o instrumento é
menos preciso do que o declarado, ou a centragem foi pior do que o suposto, ou ainda há um erro grosseiro menor
ali dentro. Um teste que passasse aqui não estaria testando nada.

**Olhe a camada de resíduos.** As observações são coloridas pelo que o teste w decidiu sobre cada uma, e nenhuma
observação foi removida — o GeoComp aponta candidatas e deixa a decisão com você (FR-255). Rejeitar uma medida é
um julgamento sobre o levantamento, não um passo aritmético.

### 4. O mapa

Peça ao passo 3 as camadas de resultado, as saídas cujos nomes terminam em *(camada)*. Elas chegam estilizadas:
estações dimensionadas pela incerteza posicional, elipses de erro, resíduos pela significância, a rede pelo tipo
de observação, e os vetores de correção.

**O nome da camada de elipses declara o seu fator de exagero.** Um semieixo de 2 mm é invisível em qualquer
escala de mapa, então as elipses desenhadas são sempre ampliadas, e um exagero não declarado transforma uma
visualização de qualidade numa representação enganosa. Mude o fator e veja o nome mudar com ele.

---

## A rede é livre

O RD-01 não contém ponto conhecido, nem azimute medido, nem altura fixa. A sua deficiência de datum é, portanto,
**três**: duas translações e uma rotação. As distâncias fixam a escala; nada fixa onde o triângulo está nem para
onde ele aponta.

Uma rede livre só pode ser ajustada com injunções internas ou mínimas. Isso não é uma limitação do programa, é
uma propriedade dos dados: o levantamento realmente não sabe onde está.

**Experimente:** rode o passo 3 de novo com **Definição do datum** em *Injunção mínima — sobre as estações
escolhidas* e **Estações do datum (separadas por vírgula; vazio = todas)** em `1,2`, para que duas das três
estações definam o datum em vez de todas, e compare. Os resíduos, os 4 graus de liberdade e o fator de variância
de 140,67 são os mesmos, e só as coordenadas se movem. Essa é a lição: a injunção escolhe um referencial, não
acrescenta informação.

Manter também a estação 1, nomeando-a em **Estações fixas (separadas por vírgula)**, é recusado. Uma estação
mantida já remove parte da deficiência de datum, e as injunções a removeriam uma segunda vez, distorcendo a rede
para atender às duas. Nem a estação 1 sozinha pode ser o datum, mantida em *Amarrada — mantém as estações que a
rede fixa*: ela fixa as duas translações e deixa a rotação, e o GeoComp o diz.

---

## O terceiro erro, que não está nos dados

O `processed_data.csv` na pasta `topo_test/` do repositório é a saída do caderno protótipo de onde este conjunto
de dados veio, e **uma das suas seis direções reduzidas está 180° fora**. O protótipo fazia a média aritmética das
duas posições. As direções são circulares: as duas posições de uma visada diferem em cerca de 180°, então a
média aritmética cai a meio caminho entre elas em vez de sobre uma delas, e para uma visada daqui isso cai
exatamente a meia volta da verdade.

Isso é demonstrado de duas formas, não afirmado. O valor publicado dá um triângulo cujos ângulos internos somam
38,24° em vez de 180°, e implica uma distância 2–3 de 4,43 m contra os 24,35 m que foram medidos. As duas
verificações estão em `tests/test_reference_total_station.py`.

O GeoComp reduz as posições de forma circular e obtém 199,110°, onde o protótipo publicou 19,110°. Se você está
comparando os números do GeoComp com aquele arquivo, esta é a única linha que não vai bater, e o GeoComp está
certo.
