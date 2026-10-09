# Levantamento combinado, Curitiba — GNSS e uma estação total ajustados juntos, e aquela que exagerou a sua precisão

O tutorial de integração (`specs/13-module-integration.md`, FR-952). Versão em português do README.md; os
números, os nomes e os valores digitados são os mesmos.

Seis estações em cerca de 3 km perto de Curitiba. Linhas de base GNSS ligam dois marcos de controle, CTB1 e CTB2,
às outras quatro, processadas em ITRF2014 em 2020,0. Uma estação total ocupa quatro das estações e mede direções,
ângulos zenitais e distâncias inclinadas para todas as estações que consegue ver, com mais um ângulo e um
azimute: 44 observações, em referencial nenhum, como uma estação total não tem.

A estação total declara a sua precisão como 2 mm numa distância, 1,5″ numa direção e 3″ num ângulo zenital.
**Ela mediu três vezes pior que isso.**

**Estes dados são construídos, e isto é dito.** Cada medida foi calculada a partir de posições escolhidas de
antemão e perturbada com uma semente fixa; as da estação total, com três vezes os desvios-padrão que ela declara.
É o levantamento em que a integração do GeoComp é validada contra o DynAdjust (`tests/combined_network.py`,
`specs/07` §6.3), com essa única mudança. Ninguém o percorreu.

**Números.** No texto, os números usam a vírgula decimal. O que o GeoComp escreve no registro é citado como ele
o escreve, com ponto.

---

## Os arquivos

| Arquivo | O que é |
|---|---|
| `gnss.json` | As linhas de base GNSS e uma altura elipsoidal, em ITRF2014 em 2020,0, com CTB1 e CTB2 nas suas posições conhecidas (um documento de rede do GeoComp) |
| `total-station.json` | As observações da estação total, sem referencial (um documento de rede) |

---

## Passo a passo

### 1. GNSS e estação total — `geocomp:integration_gnss_total_station`

- **Rede GNSS (de Construir linhas de base)**: `gnss.json`
- **Rede de estação total (de Rede clássica)**: `total-station.json`
- **Referencial da combinação**: *ITRF2020*
- **Estações fixas (separadas por vírgula)**: `CTB1,CTB2`
- **Estimar um componente de variância por técnica**: desmarcado

As duas entradas são combinadas em ITRF2020: as linhas de base GNSS levadas de ITRF2014, as observações da
estação total dadas segundo a vertical de cada estação. O registro o diz: *2 entradas combinadas (gnss,
total_station) em ITRF2020; 7 transformação(ões) aplicada(s).*

**41 graus de liberdade, e o teste global falha**, com um fator de variância de **5,80**. Algo no levantamento
combinado discorda da sua precisão declarada. O teste global não pode dizer o quê. O registro, porém, o detalha
por técnica:

> GNSS: 5 observação(ões), 20.6% da redundância, vᵀPv/r 1.375. Estação total: 44 observação(ões), 79.4% da
> redundância, vᵀPv/r 6.950.

Os quadrados ponderados dos resíduos de cada técnica sobre a sua parcela da redundância: **6,950 para a estação
total**, contra 1,375 para o GNSS. É uma leitura rápida de como os pesos de uma técnica se ajustam, e o
relatório o diz; ainda não é um componente de variância, que o próximo passo estima.

### 2. GNSS e estação total — `geocomp:integration_gnss_total_station`

O mesmo, deixando que os dados pesem cada técnica.

- **Rede GNSS (de Construir linhas de base)**: `gnss.json`
- **Rede de estação total (de Rede clássica)**: `total-station.json`
- **Referencial da combinação**: *ITRF2020*
- **Estações fixas (separadas por vírgula)**: `CTB1,CTB2`
- **Estimar um componente de variância por técnica**: marcado

A seção *Técnicas* do relatório, sob *Componentes de variância*, dá à estação total um componente de
**7,19 ± 1,76** e ao GNSS **0,56 ± 0,46**. Um componente é o fator pelo qual as variâncias declaradas de uma
técnica são multiplicadas: os desvios-padrão da estação total foram subestimados em cerca de **2,7** vezes, onde
o levantamento foi feito com 3, e os do GNSS estão quase certos, o 1 no seu componente estando dentro da sua
incerteza.

O teste global agora passa, e isso não diz nada: os componentes foram estimados para que passasse. O que é
informação são os próprios componentes, e que o peso da estação total na solução é agora o que ela mereceu. A
sua parcela da redundância vai de 79,4 % para **88,5 %**.

---

## O que levar disto

- **O teste global de um ajustamento combinado diz que algo discorda, não qual técnica.** O detalhamento por
  técnica diz qual.
- **Os componentes de variância pesam cada técnica pelo que ela mediu, não pelo que declarou.** São uma
  estimativa com a sua própria incerteza, e precisam de redundância dentro de cada técnica para serem
  estimáveis.
- **Depois dos componentes de variância, um teste global aprovado não é evidência.** Os componentes são.
