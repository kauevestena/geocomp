# RD-08 barragem — duas épocas de uma estrutura monitorada, e o único ponto que se moveu

**Conjunto de dados de referência RD-08, a sua metade sintética** (`specs/20-testing-and-validation.md` §3,
FR-950, FR-952), o tutorial de monitoramento. Versão em português do README.md; os números, os nomes e os
valores digitados são os mesmos.

Quatro pilares de referência em terreno estável em volta de uma estrutura, R1 a R4, num terreno de 1200 m por
900 m, e cinco alvos na própria estrutura, O1 a O5. Cada par dos nove é medido por distância, 36 distâncias em
cada época, cada uma a 1 mm. A rede foi medida em 2025 e de novo em 2026. Nesse intervalo, **O2 moveu-se 8 mm
para leste e 6 mm para sul.**

**Estes dados são construídos, e isto é dito.** As distâncias foram geradas a partir de posições escolhidas de
antemão, com 1 mm de ruído de uma semente fixa em cada época, e o movimento foi posto nas posições da segunda
época. É assim que a resposta é conhecida exatamente, e é assim que o monitoramento do GeoComp é testado
(`tests/monitoring_network.py`). Não é uma estrutura que alguém levantou.

O tutorial ajusta cada época, compara as duas, encontra O2, e depois mostra o que acontece quando as estações
tomadas como estáveis não o são.

**Números.** No texto, os números usam a vírgula decimal. Os valores entre crases são digitados como
aparecem. A mensagem que o GeoComp dá no último passo é citada como ele a escreve.

---

## Os arquivos

| Arquivo | O que é |
|---|---|
| `epoch-2025.json` | A primeira época, como medida: a posição aproximada de cada estação e as 36 distâncias (um documento de rede do GeoComp) |
| `epoch-2026.json` | A segunda época, da mesma forma |
| `thresholds.csv` | Um limiar de alerta: 5 mm de movimento em qualquer um dos cinco alvos |

---

## Passo a passo

### 1. Ajustar rede — `geocomp:analysis_network_adjust`

A primeira época, apoiada nos quatro pilares.

- **Documento da rede**: `epoch-2025.json`
- **Referencial de coordenadas**: *2D — planimétrico (E, N)*
- **Definição do datum**: *Injunção mínima — sobre as estações escolhidas*
- **Estações do datum (separadas por vírgula; vazio = todas)**: `R1,R2,R3,R4`
- **Solução**: `solution-2025.json`

Trinta e seis distâncias e nove estações: **21 graus de liberdade.** O teste global passa, com um fator de
variância a posteriori de **1,14**: as distâncias concordam entre si tão bem quanto o seu 1 mm diz que deveriam.

O data snooping lista **3** observações cujo teste w excede o valor crítico de 1,94, a maior com **2,37**. São
ruído. Com 95 % de confiança, uma observação boa em vinte excede o valor crítico por acaso, e 36 delas dão cerca
de duas. O GeoComp não rejeita nenhuma, e no monitoramento isso importa: uma observação removida porque discorda
das outras pode ser o movimento que se veio medir.

### 2. Ajustar rede — `geocomp:analysis_network_adjust`

A segunda época, da mesma forma.

- **Documento da rede**: `epoch-2026.json`
- **Referencial de coordenadas**: *2D — planimétrico (E, N)*
- **Definição do datum**: *Injunção mínima — sobre as estações escolhidas*
- **Estações do datum (separadas por vírgula; vazio = todas)**: `R1,R2,R3,R4`
- **Solução**: `solution-2026.json`

O teste global passa de novo, com um fator de variância de **1,18**. Nada em nenhum dos dois ajustamentos diz
que algo se moveu. Uma época sozinha não pode dizer: o movimento está entre elas.

### 3. Comparar duas épocas — `geocomp:monitoring_compare_epochs`

- **Primeira época (solução)**: `solution-2025.json`
- **Segunda época (solução)**: `solution-2026.json`
- **Estações de referência (separadas por vírgula)**: `R1,R2,R3,R4`
- **Limiares de alerta (CSV)**: `thresholds.csv`
- **Documento da análise**: `comparison.json`
- **Relatório de monitoramento**: algum lugar onde você possa abri-lo

Pelo menu, *GeoComp ▸ Análise ▸ Comparar duas épocas* mostra primeiro se as duas soluções podem ser comparadas:
o mesmo referencial, épocas declaradas, as mesmas estações. Estas podem.

**O bloco de referência é testado primeiro**, porque todo deslocamento é medido em relação a ele. O seu teste de
congruência dá **0,59** contra um valor crítico de **2,44**: os pilares não se moveram uns em relação aos outros.
O da rede inteira dá **16,07** contra **1,91**: outra coisa se moveu.

**Movimento significativo numa estação: O2**, de **10,8 mm**, 8,7 mm para leste e 6,5 mm para sul. O seu teste
dá **77,1** contra **3,22**. Foi movido 10,0 mm; os outros 0,8 mm são o ruído da medição de duas épocas, bem
dentro da sua elipse de 95 % de **3,0 por 2,1 mm**. Dos outros alvos, o maior deslocamento é o de O3, de
**2,0 mm**, e nenhum é significativo.

O limiar de alerta é ultrapassado apenas em O2. É uma questão distinta da significância. Um movimento
significativo menor que o limiar é real, mas tolerável; um movimento maior que o limiar que não é significativo
não se distingue do ruído, e o relatório diz qual é qual.

**Experimente:** ajuste as duas épocas de novo com *Definição do datum* em *Injunção interna — rede livre, traço
mínimo*, que não fixa nenhuma estação em particular, e compare-as. Os deslocamentos saem iguais, até o décimo de
micrômetro. A comparação transforma as duas épocas para o bloco de referência antes de medir qualquer coisa,
então o datum em que cada época foi ajustada não importa. **Importa quais estações são a referência.**

### 4. Um bloco de referência que se moveu

Compare de novo, dando as **Estações de referência (separadas por vírgula)** como `R1,R2,R3,R4,O2`: como se O2
fosse um pilar. O GeoComp recusa:

> O bloco de referência moveu-se: o seu teste de congruência dá 28.8678 contra um valor crítico de 2.2371, e a
> localização implica O2. A análise não prossegue sobre um bloco que se moveu, porque esse movimento seria
> distribuído por todas as outras estações. As estações que permanecem estáveis são R1, R2, R3, R4. Verifique os
> pilares implicados e analise de novo com eles entre os pontos objeto.

e diz onde escreveu a localização. Tomado como estável, os 10,8 mm de O2 teriam sido repartidos entre os outros
quatro pilares e aparecido, menores e na direção errada, em todos os alvos da estrutura.

---

## O que levar disto

- **O movimento está entre as épocas.** Cada ajustamento sozinho passa, e nada tem a dizer sobre ele.
- **O bloco de referência é testado antes de qualquer coisa ser medida em relação a ele.** Um pilar que se moveu
  e é tomado como estável move todo o resto.
- **O datum de cada época não importa; a escolha das estações de referência importa.**
- **Significativo e alarmante são perguntas diferentes.** A significância é medida contra a incerteza do próprio
  deslocamento; um limiar é um limite de engenharia.
- **O data snooping a 95 % aponta observações boas por acaso.** O GeoComp as lista e não rejeita nenhuma.
