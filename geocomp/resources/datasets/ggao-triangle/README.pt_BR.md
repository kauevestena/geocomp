<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Triângulo GGAO — três receptores GNSS, duas horas, e um circuito que diz em qual hora confiar

Versão em português do README.md; os números, os nomes e os valores digitados são os mesmos. No texto, os
números usam a vírgula decimal; o que o GeoComp escreve no registro é citado como ele o escreve, com ponto.

Três estações GNSS permanentes no Goddard Geophysical and Astronomical Observatory da NASA, em Greenbelt,
Maryland: **GODN**, **GODE** e **GODS**, a poucos passos uma da outra, observando juntas em 1 de janeiro de 2025.
Duas horas desse dia, cada uma na sua pasta:

| Pasta | Hora (tempo GPS) | O que contém |
|---|---|---|
| `hour-00` | 00:00 a 00:59:30 | Uma hora comum |
| `hour-11` | 11:00 a 11:59:30 | A hora em que a própria validação do GeoComp encontrou falha (`specs/22-reference-data-sources.md` §5.1) |

Cada pasta tem as observações das três estações, `godn0010.25o`, `gode0010.25o` e `gods0010.25o`, e o arquivo
de navegação transmitida do dia, `brdc0010.25n.gz`.

**Os dados são da NOAA.** Vêm da rede NOAA CORS, operada pelo National Geodetic Survey; o Goddard da NASA
forneceu as observações. Cada arquivo de observação é o arquivo publicado pela NOAA para o dia, cortado na hora
e reduzido ao GPS e aos oito observáveis que uma solução GPS de dupla frequência lê. Nenhum valor foi alterado,
e `scripts/make_ggao_triangle.py` refaz os arquivos a partir dos da NOAA. O `NOTICE.md`, ao lado deste
arquivo, traz a atribuição e os termos.

O tutorial é sobre uma verificação, o **fechamento do circuito**: três linhas de base em volta de um triângulo
deveriam somar zero. Ele não precisa de nenhuma coordenada publicada, e diz quando um conjunto de linhas de base
discorda de si mesmo.

---

## Passo a passo

### 1. Instalar conjunto de dados do tutorial — `geocomp:project_tutorial_dataset`

Se você está lendo isto na pasta onde ele foi instalado, este passo está feito. Se não, ele está no menu, em
*GeoComp ▸ Projeto*.

- **Conjunto de dados**: *ggao-triangle*
- **Pasta de destino**: uma pasta onde você possa escrever

### 2. Relativo — Estático — `geocomp:gnss_relative_static`

Pelo menu, *GeoComp ▸ GNSS ▸ Relativo — Estático*. O primeiro lado do triângulo da meia-noite.

- **Pasta com observações RINEX**: `hour-00`
- **Estação base**: `GODN`
- **Estação móvel**: `GODE`
- **Solução**: `solutions-00/godn-gode.pos`, numa pasta nova ao lado de `hour-00`

Deixe o resto como está. O registro diz como foi:

> 120 épocas, 96.7% com ambiguidades resolvidas

Todas as épocas menos as quatro primeiras, enquanto a solução se acomodava, têm as ambiguidades fixadas. O
registro também diz em que a base é mantida:

> A base GODN não está no banco de estações de referência, por isso o RTKLIB a mantém na posição aproximada do
> cabeçalho RINEX, e os resultados não estão em nenhum referencial declarado.

Aqui isso basta: um fechamento precisa dos vetores entre as estações, não de onde as estações estão.

### 3. Relativo — Estático — `geocomp:gnss_relative_static`

O segundo lado.

- **Pasta com observações RINEX**: `hour-00`
- **Estação base**: `GODN`
- **Estação móvel**: `GODS`
- **Solução**: `solutions-00/godn-gods.pos`

### 4. Relativo — Estático — `geocomp:gnss_relative_static`

O terceiro lado, o que fecha o triângulo.

- **Pasta com observações RINEX**: `hour-00`
- **Estação base**: `GODE`
- **Estação móvel**: `GODS`
- **Solução**: `solutions-00/gode-gods.pos`

Cada um dos três fixa a mesma parcela das suas épocas, 96,7%.

### 5. Construir linhas de base — `geocomp:gnss_build_baselines`

Pelo menu, *GeoComp ▸ GNSS ▸ Construir linhas de base*.

- **Pasta com soluções .pos**: `solutions-00`
- **Linhas de base**: algum lugar onde você as encontre

> 3 linha(s) de base: 2 independentes, 1 dependentes

Duas das três linhas de base bastam para situar as três estações; a terceira é *dependente*, e é isso que faz
dela uma verificação. Dando a volta no triângulo pelas três:

> O circuito GODN → GODE → GODS → GODN fecha com 0.37 mm em 282.2 m de linhas de base (1.33 ppm).

**O triângulo fecha com 0,37 mm.** Três vetores medidos de forma independente, cada um na sua execução,
concordam entre si em menos de meio milímetro.

---

## A hora das onze

Agora as mesmas três execuções na outra pasta.

### 6. Relativo — Estático — `geocomp:gnss_relative_static`

- **Pasta com observações RINEX**: `hour-11`
- **Estação base**: `GODN`
- **Estação móvel**: `GODE`
- **Solução**: `solutions-11/godn-gode.pos`, numa pasta nova ao lado de `hour-11`

> 120 épocas, 48.3% com ambiguidades resolvidas

Metade das épocas fixadas, não 96,7%. O registro diz o que o motor viu:

> Perdas de ciclo detectadas pelo motor: 6, em G21.

### 7. Relativo — Estático — `geocomp:gnss_relative_static`

- **Pasta com observações RINEX**: `hour-11`
- **Estação base**: `GODN`
- **Estação móvel**: `GODS`
- **Solução**: `solutions-11/godn-gods.pos`

> 120 épocas, 47.5% com ambiguidades resolvidas

### 8. Relativo — Estático — `geocomp:gnss_relative_static`

- **Pasta com observações RINEX**: `hour-11`
- **Estação base**: `GODE`
- **Estação móvel**: `GODS`
- **Solução**: `solutions-11/gode-gods.pos`

> 120 épocas, 97.5% com ambiguidades resolvidas

O lado sem a GODN fixa tão bem quanto qualquer lado à meia-noite.

### 9. Construir linhas de base — `geocomp:gnss_build_baselines`

- **Pasta com soluções .pos**: `solutions-11`
- **Linhas de base**: algum lugar onde você as encontre

> O circuito GODN → GODE → GODS → GODN fecha com 7.62 mm em 282.3 m de linhas de base (26.98 ppm).

**O triângulo erra por 7,62 mm**, vinte vezes o circuito da meia-noite sobre o mesmo terreno. As linhas de base
dessa hora discordam entre si.

---

## O que levar disto

- **O fechamento de um circuito detecta; não localiza.** O circuito diz que um dos três lados está errado, não
  qual. Aqui as próprias execuções apontam: os dois lados da GODN fixaram metade das épocas, e uma linha de base
  é tirada da última época, que nos dois não está fixada. Processe esses dois de novo — um intervalo mais longo,
  outra hora — antes de usá-los.
- **Um circuito que fecha não quer dizer que as estações estão certas.** Um erro comum aos dois lados de uma
  estação entra no circuito duas vezes, com sinais opostos, e se cancela. Com as configurações padrão do GeoComp
  estas execuções não aplicam calibração de antena nenhuma, e o circuito da meia-noite ainda fecha com 0,37 mm,
  porque o erro de cada antena está em dois lados. Quando a validação do GeoComp comparou linhas de base como
  estas com as coordenadas publicadas pelo NGS, elas discordaram em milímetros enquanto os circuitos fechavam
  em uma fração de um (`specs/22-reference-data-sources.md` §5).
- **A parcela fixada faz parte da resposta.** A hora que não fechou é a hora que não fixou. Leia os indicadores
  de qualidade antes de ler as coordenadas.
