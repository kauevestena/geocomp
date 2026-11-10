# RD-04 circuito — um circuito de nivelamento que não fecha, e por que o ajustamento não sabe dizer onde

**Conjunto de dados de referência RD-04** (`specs/20-testing-and-validation.md` §3, FR-950, FR-952), o
tutorial de nivelamento. Versão em português do README.md; os números, os nomes e os valores digitados são os
mesmos.

Três linhas de nivelamento geométrico entre três referências de nível — BM1 a BM2, BM2 a BM4 e de volta a BM1
—, dez estacionamentos e vinte leituras de mira, com as visadas equilibradas em todo estacionamento. Uma leitura
de vante na linha BM2 a BM4 foi anotada 12 mm errada.

**Estes dados são construídos, e isto é dito.** As leituras foram geradas a partir de altitudes escolhidas de
antemão — BM1 100,000 m, BM2 103,750 m, BM4 106,480 m — com 0,3 mm de ruído de uma semente fixa, e depois uma
leitura foi estragada. É assim que a resposta é conhecida exatamente, e é assim que o nivelamento do GeoComp é
testado (`tests/reference_levelling.py`). Não é um levantamento que alguém percorreu.

O tutorial mostra o circuito sem fechar, um ajustamento que esconde o erro em vez de encontrá-lo, e as duas
altitudes conhecidas que o encontram.

**Números.** No texto, os números usam a vírgula decimal. Os valores entre crases são digitados como
aparecem: o campo *Referências de nível* separa as referências por vírgulas, e nele a altitude se escreve
com ponto.

---

## Os arquivos

| Arquivo | O que é |
|---|---|
| `loop.csv` | A caderneta de campo: uma linha por leitura de mira — estacionamento, ponto, `BS` ou `FS`, a leitura e a distância da visada em metros, e a linha |
| `mapping.json` | Qual coluna alimenta qual campo (FR-160) |
| `profiles.json` | O nível: 0,5 mm por leitura de mira, 0,7 mm por raiz de quilômetro. Sem ele o GeoComp se recusa a importar, em vez de inventar uma precisão |

---

## Passo a passo

O documento que cada passo escreve é a entrada do passo seguinte.

### 1. Importar caderneta de nivelamento — `geocomp:levelling_import`

- **Caderneta de campo**: `loop.csv`
- **Mapeamento de campos**: `mapping.json`
- **Perfis de instrumento**: `profiles.json`

Dez estacionamentos em três linhas, nenhuma linha do arquivo rejeitada. O arquivo tem uma linha por leitura,
que é o que um nível digital exporta; o GeoComp deduz isso das colunas que o mapeamento nomeia.

### 2. Visadas iguais — `geocomp:levelling_equal_sights`

- **Estacionamentos**: o documento que o passo 1 escreveu
- **Perfis de instrumento**: `profiles.json`

Cada linha vira um desnível com a sua incerteza. As visadas estão equilibradas em todo estacionamento, então o
desequilíbrio acumulado é zero e um erro de colimação se cancela; a pior linha, BM2 a BM4, tem 1,6 mm.

### 3. Fechamentos e tolerâncias — `geocomp:levelling_closures`

- **Linhas reduzidas**: o documento que o passo 2 escreveu
- **Modo**: *Circuito*
- **Coeficiente de tolerância k (m por raiz de km)**: `0.008` — 8 mm √K, uma tolerância comum para o
  nivelamento ordinário

Os três desníveis deveriam somar zero ao longo do circuito. Somam **−15,7 mm**, para um permitido de
**7,0 mm** nos 0,76 km do circuito. **O circuito não fecha.**

É tudo o que um circuito pode dizer: algo nele está errado. Não pode dizer o quê, porque toda linha contribui
para a mesma soma.

**Experimente:** rode de novo com o coeficiente de tolerância em `0`. O erro de fechamento é o mesmo, e não há
veredito, nem aprovado nem reprovado: o GeoComp não cobra de um circuito uma tolerância que ninguém declarou.

### 4. Ajustamento de rede de nivelamento — `geocomp:levelling_network`

Mantenha só BM1.

- **Linhas reduzidas**: o documento que o passo 2 escreveu
- **Referências de nível**: `BM1=100.000`
- **Coeficiente de tolerância k (m por raiz de km; 0 não avalia nada)**: `0.008`
- **Incerteza por raiz de quilômetro (m)**: `0.0007`, o valor do próprio nível

O ajustamento roda. Antes de ajustar, ele fecha cada linha que corre entre duas altitudes conhecidas, e com só
BM1 conhecida não há nenhuma; julgar um circuito é tarefa do algoritmo de fechamentos, e a verificação do
próprio ajustamento é o teste global (`specs/10` §3). Três desníveis, duas altitudes desconhecidas: **um grau
de liberdade.** O teste global falha, com um fator de variância a posteriori de **662**: os dados discordam da
precisão declarada muito mais do que o acaso permite.

**Agora procure o culpado.** O data snooping testa o resíduo de cada linha, e todas marcam **1,00**, abaixo do
valor crítico de 1,96, então **nenhum erro grosseiro é apontado.** Não é que o teste o deixou passar. Com um
grau de liberdade há a informação de um resíduo só, e ela é repartida entre as três linhas na proporção do seu
comprimento: 3,7 mm em BM1 a BM2, 10,3 mm em BM2 a BM4, 1,7 mm em BM4 de volta a BM1. Qualquer uma delas
poderia conter o erro, e os resíduos seriam os mesmos.

As altitudes também estão erradas, e nada nelas o diz: BM2 sai com 103,7525 m, **2,5 mm** de onde está. O
ajustamento escondeu o erro espalhando-o.

### 5. As referências de nível que o encontram

Rode o ajustamento de rede de novo, dando as **Referências de nível** como `BM1=100.000,BM2=103.750,BM4=106.480`
— as altitudes que um cadastro de referências de nível publicaria para elas.

O GeoComp recusa:

> 1 fechamento(s) não cumpriram a tolerância: BM2-BM4. O GeoComp não ajusta uma linha que não cumpriu a
> tolerância sem um reconhecimento explícito. Refaça a linha, ou ative 'Ajustar linhas que não cumpriram a
> tolerância' nesta execução ou nas Configurações Globais (Nivelamento).

Com toda linha agora correndo entre altitudes conhecidas, cada linha fecha por si só, e apenas **BM2 a BM4**
falha. É a linha a nivelar de novo. O circuito disse que algo estava errado; as referências de nível disseram
onde.

**Experimente:** ative *Ajustar linhas que não cumpriram a tolerância* e rode mais uma vez. O GeoComp recusa de
novo, por outro motivo: com as três referências de nível mantidas não sobra nada a estimar.

---

## O que levar disto

- **O fechamento de um circuito detecta; não localiza.** Tampouco um ajustamento com um grau de liberdade,
  por mais cuidadosas que sejam as suas estatísticas.
- **Um ajustamento pode fazer um erro grosseiro parecer precisão.** As altitudes do passo 4 vêm com incertezas
  de poucos milímetros e estão erradas em outro tanto, o que só um teste global reprovado avisou.
- **São as altitudes conhecidas que localizam um erro**, dando a cada linha algo próprio contra o que fechar.
