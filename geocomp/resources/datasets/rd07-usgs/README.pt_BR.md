# RD-07 USGS — uma rede gravimétrica cuja resposta outra pessoa publicou, e um gravímetro que lê 3 % a mais

**Conjunto de dados de referência RD-07, a sua metade do USGS** (`specs/20-testing-and-validation.md` §3,
`specs/22-reference-data-sources.md` §5.6, FR-950, FR-952), o tutorial de gravimetria. Versão em português do
README.md; os números, os nomes e os valores digitados são os mesmos.

Dois levantamentos de gravimetria relativa de cinco estações, sta1 a sta5, cada estação visitada duas ou três
vezes numa tarde com o gravímetro B44, onze leituras por levantamento. São **os levantamentos sintéticos de
teste do USGS para o GSadjust**, copiados sem alteração do repositório do GSadjust no commit `17bb3ca`. O USGS os
gerou a partir de uma verdade que publicou ao lado deles, então a resposta é conhecida e não é a do próprio
GeoComp:

| | sta1 | sta2 | sta3 | sta4 | sta5 | Deriva | Escala do gravímetro |
|---|---|---|---|---|---|---|---|
| **Verdade**, mGal | 50,000 | 48,000 | 45,000 | 48,500 | 46,000 | | |
| `Test2.txt` | | | | | | 0,01 mGal por hora | correta |
| `Test3.txt` | | | | | | 0,01 mGal por hora | **lê 3 % a mais** |

Cada leitura tem 3 µGal de ruído. Os arquivos estão em domínio público nos Estados Unidos e dedicados ao mundo
inteiro sob CC0; o `GSadjust-LICENSE.md` ao lado deles o diz.

**Números.** No texto, os números usam a vírgula decimal. Os valores entre crases são digitados como
aparecem: o campo *Gravidade conhecida (mGal)* separa as estações por vírgulas, e nele a gravidade se escreve
com ponto.

---

## Os arquivos

| Arquivo | O que é |
|---|---|
| `Test2.txt`, `Test3.txt` | Os dois levantamentos, no formato de exportação Burris que o GeoComp lê |
| `profiles.json` | O gravímetro B44: 3 µGal por leitura, maré já removida, **sem calibração** — como um gravímetro está antes de alguém medir a sua escala |
| `profiles-calibrated.json` | O mesmo gravímetro com a calibração com que o Teste 3 foi gerado: um fator de 1/1,03 |
| `GSadjust-LICENSE.md` | A licença do USGS para os levantamentos |

---

## Passo a passo

### 1. Pré-processamento (escala, maré, deriva) — `geocomp:gravimetry_preprocess`

- **Arquivo do gravímetro**: `Test2.txt`
- **Perfis de gravímetro**: `profiles.json`
- **Piso de precisão (mGal)**: `0`
- **Leituras reduzidas**: `test2.json`

Onze leituras, onze ocupações, uma sessão. Uma exportação Burris não declara nem a precisão nem o fuso horário,
e o registro diz o que foi suposto para cada um: os 3 µGal do perfil, e UTC. Ele também ajusta a deriva às três
leituras de sta1 sozinha, a base: **0,01008 ± 0,00142 mGal por hora**.

### 2. Ajustamento de rede gravimétrica — `geocomp:gravimetry_network`

- **Leituras reduzidas**: `test2.json`
- **Gravidade conhecida (mGal)**: `sta1=50.000`
- **Tratamento da deriva**: *Estimada junto com os valores das estações*

O ajustamento tem **5 graus de liberdade**, e o teste global passa com um fator de variância de **1,17**. A
deriva é estimada junto com as estações, a partir de todas as leituras em vez das três da base:
**0,00915 ± 0,00109 mGal por hora**, para os 0,01 que o USGS pôs.

E as estações voltam como o USGS as publicou. sta2 está a **1,3 µGal** da sua verdade, sta3 a **2,6**, sta4 a
**0,9** e sta5 a **2,0**, cada uma dentro do seu próprio desvio-padrão de cerca de 3 µGal.

### 3. Pré-processamento (escala, maré, deriva) — `geocomp:gravimetry_preprocess`

O segundo levantamento, com o mesmo perfil.

- **Arquivo do gravímetro**: `Test3.txt`
- **Perfis de gravímetro**: `profiles.json`
- **Piso de precisão (mGal)**: `0`
- **Leituras reduzidas**: `test3.json`

### 4. Ajustamento de rede gravimétrica — `geocomp:gravimetry_network`

Desta vez a gravidade de sta3 também é conhecida, como um gravímetro absoluto a daria.

- **Leituras reduzidas**: `test3.json`
- **Gravidade conhecida (mGal)**: `sta1=50.000,sta3=45.000`
- **Tratamento da deriva**: *Estimada junto com os valores das estações*

**O teste global falha**, com um fator de variância de **525**. As diferenças do gravímetro não cabem entre dois
valores que são ambos conhecidos.

**Experimente:** mantenha só sta1, `sta1=50.000`. O teste global passa, com um fator de variância de **1,51**,
e sta3 sai com **44,846 mGal**, a **154 µGal** da sua verdade. Nada no ajustamento o diz. Um gravímetro que lê
toda diferença 3 % a mais é coerente consigo mesmo: cada diferença está errada na mesma proporção, a rede fecha,
e os resíduos são os de um levantamento correto. Rode de novo com `profiles-calibrated.json` e o fator de
variância é o mesmo, 1,51, em todos os dígitos mostrados.

### 5. Pré-processamento (escala, maré, deriva) — `geocomp:gravimetry_preprocess`

O segundo levantamento de novo, com a calibração do gravímetro.

- **Arquivo do gravímetro**: `Test3.txt`
- **Perfis de gravímetro**: `profiles-calibrated.json`
- **Piso de precisão (mGal)**: `0`
- **Leituras reduzidas**: `test3-calibrated.json`

### 6. Ajustamento de rede gravimétrica — `geocomp:gravimetry_network`

- **Leituras reduzidas**: `test3-calibrated.json`
- **Gravidade conhecida (mGal)**: `sta1=50.000,sta3=45.000`
- **Tratamento da deriva**: *Estimada junto com os valores das estações*

O teste global passa, com um fator de variância de **1,56**, e as três estações desconhecidas ficam a menos de
**2,5 µGal** da sua verdade.

---

## O que levar disto

- **Uma rede verifica a coerência do gravímetro, não a sua escala.** Um erro de calibração deixa toda estatística
  como estava; só algo que conheça o tamanho de uma diferença pode encontrá-lo, como um segundo valor absoluto ou
  uma linha de calibração.
- **Uma estação conhecida dá um datum e nada com que verificá-lo.** Duas põem a escala à prova.
- **A deriva é estimada com mais precisão a partir de todas as leituras do que só pelas da base** (±0,00109
  contra ±0,00142 mGal por hora aqui), e o GeoComp a estima junto com as estações, a menos que se diga o
  contrário.
