<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Linha de base de exemplo do RTKLIB — uma sessão GNSS que roda em dois minutos

Versão em português do README.md; os números, os nomes e os valores digitados são os mesmos. No texto, os
números usam a vírgula decimal; o que o GeoComp escreve no registro é citado como ele o escreve, com ponto.

Dois receptores que observaram ao mesmo tempo em 2 de abril de 2005, a 3,3 km um do outro, e as efemérides
transmitidas do dia. São **os próprios dados de exemplo do RTKLIB**, copiados sem alteração do repositório do
RTKLIB-EX no commit `06e8644`; o RTKLIB tem licença BSD de 2 cláusulas, e o seu aviso está em
`RTKLIB-license.txt` ao lado deste arquivo.

| Arquivo | O que é |
|---|---|
| `30400920.05o` | Estação `3040`, `RINEX 2.10`, GPS, 30 s. **A base.** |
| `07590920.05o` | Estação `0759`, o mesmo dia, o mesmo modelo de receptor e de antena. **A móvel.** |
| `brdc_0759.05n.gz` | O arquivo de navegação transmitida daquele dia. O GeoComp o lê compactado. |

---

## Passo a passo

### 1. Instalar conjunto de dados do tutorial — `geocomp:project_tutorial_dataset`

Se você está lendo isto na pasta onde ele foi instalado, este passo está feito. Se não, ele está no menu, em
*GeoComp ▸ Projeto*.

- **Conjunto de dados**: *rtklib-sample*
- **Pasta de destino**: uma pasta onde você possa escrever

### 2. Relativo — Estático — `geocomp:gnss_relative_static`

Pelo menu, *GeoComp ▸ GNSS ▸ Relativo — Estático*.

- **Pasta com observações RINEX**: a pasta que o passo 1 instalou
- **Estação base**: `3040`
- **Estação móvel**: `0759`
- **Solução**: algum lugar onde você a encontre
- **Resumo de qualidade**: algum lugar onde você o encontre
- **Épocas da solução (camada)**: deixe-a carregar

Deixe o resto como está. O `rnx2rtkp` roda. **Você não precisa instalá-lo:** o GeoComp traz o seu, e o
registro diz *Usando RTKLIB-EX* `2.5.1` e onde ele está.

## O que você deve ver

**120 épocas** na primeira hora (00:00 a 00:59:30), **117 delas com as ambiguidades fixadas** e três flutuantes.
O registro o diz assim:

> 120 épocas, 97.5% com ambiguidades resolvidas

O registro diz, das observações de cada estação, que o nome do arquivo de navegação não diz de que dia ele é:

> o nome de nenhum arquivo de navegação informa o dia desta sessão, portanto todos os arquivos de navegação da
> pasta (1) lhe são oferecidos. Nomeie os arquivos de navegação pelo seu dia, ou mantenha na pasta apenas os
> desta sessão.

Isso é esperado aqui, e inofensivo: há um só arquivo de navegação, e é o certo.

E diz em que a base é mantida:

> A base 3040 não está no banco de estações de referência, por isso o RTKLIB a mantém na posição aproximada do
> cabeçalho RINEX, e os resultados não estão em nenhum referencial declarado.

## O que isto não mostra

**O encadeamento, não a acurácia.** Estas duas estações não têm coordenadas oficiais publicadas que este projeto
consiga obter, então a linha de base é mantida na posição aproximada do cabeçalho, e nada aqui diz que as
coordenadas estão certas. O que isto mostra é a cadeia inteira funcionando — a descoberta das sessões, o motor,
a leitura da solução, os indicadores de qualidade, a camada do mapa — e as ambiguidades se resolvendo. O
conjunto de dados que validaria a acurácia é o RD-06 (`specs/22-reference-data-sources.md` §5).
