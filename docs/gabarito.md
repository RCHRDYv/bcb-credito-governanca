# Gabarito das perguntas do experimento

**Mês de referência:** jul/2026. Gerado por `scripts/gerar_gabarito.py` a partir de [`evaluation/gabarito.yml`](../evaluation/gabarito.yml) e dos SQL em [`evaluation/gabarito/`](../evaluation/gabarito/). Nenhum número deste documento é digitado à mão: para atualizar, rode o script de novo.

São 41 perguntas, do conjunto v2 registrado antes de qualquer execução ([`questions_v2.yml`](../evaluation/questions_v2.yml)). 38 têm resposta nesta versão, com 47 leituras e 52 consultas, e 3 dependem de fonte ou modelo que ainda não está no projeto.

## Como ler

- **Tipo de acerto.** Em `valor`, acerta quem chega ao número ou à lista. Em `valor_com_ressalva`, acerta quem chega ao número e declara a ressalva obrigatória. Em `abstencao`, acerta quem reconhece que o dado não responde e diz o que faltaria.
- **Leituras aceitas.** Quando a pergunta admite mais de uma interpretação razoável, cada uma tem o próprio SQL e vale como acerto, desde que a resposta diga qual usou. As leituras foram registradas antes de qualquer execução do experimento ([ADR 0015](adr/0015-gabarito-com-leituras-aceitas-em-sql-portatil.md)).
- **Janelas.** Quando a pergunta não diz o período, a mesma consulta traz 12 meses e o recorte inteiro, e vale a janela que a resposta declarar.
- **Unidades.** Taxas e participações em percentual; variações de taxa em pontos percentuais (p.p.); valores em reais.
- **Fonte.** Os ids no formato `arquivo.id` são conceitos e avisos da ontologia, em [`ontology/`](../ontology/).

## Monitoramento e benchmark de mercado

### Q01. Qual o volume total da carteira ativa de crédito no Brasil no último mês disponível, e como se compara ao mesmo mês do ano anterior?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.carteira_ativa`

**Como se responde:** Carteira ativa total no último mês e no mesmo mês do ano anterior, com a variação em reais e em percentual.

[`Q01.sql`](../evaluation/gabarito/Q01.sql)

| Mês | Carteira ativa | Mês do ano anterior | Carteira ativa do ano anterior | Variação em reais | Variação |
|---|---|---|---|---|---|
| jul/2026 | R$ 7.590,7 bi | jul/2025 | R$ 6.941,0 bi | R$ 649,7 bi | 9,36% |

### Q02. Quais as cinco modalidades de crédito com maior crescimento de carteira nos últimos 12 meses?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.carteira_ativa`, `modalidades.modalidade_e_conta_contabil`

**Leitura `percentual`:** Crescimento da carteira em 12 meses, em percentual, no nível de modalidade. As cinco primeiras do ranking.

[`Q02_percentual.sql`](../evaluation/gabarito/Q02_percentual.sql)

| Posição | Código modalidade | Modalidade | Carteira 12 meses antes | Carteira no último mês | Crescimento em reais | Crescimento |
|---|---|---|---|---|---|---|
| 1 | 10 | Financiamentos de títulos e valores mobiliários | R$ 99,1 mi | R$ 176,2 mi | R$ 77,1 mi | 77,78% |
| 2 | 13 | Outros créditos | R$ 690,2 bi | R$ 783,5 bi | R$ 93,3 bi | 13,52% |
| 3 | 09 | Financiamentos imobiliários | R$ 1.328,5 bi | R$ 1.496,2 bi | R$ 167,8 bi | 12,63% |
| 4 | 04 | Financiamentos | R$ 1.180,7 bi | R$ 1.312,2 bi | R$ 131,6 bi | 11,14% |
| 5 | 01 | Adiantamentos a depositantes | R$ 1,7 bi | R$ 1,9 bi | R$ 166,4 mi | 9,56% |
| 6 | 02 | Empréstimos | R$ 2.422,0 bi | R$ 2.625,5 bi | R$ 203,5 bi | 8,40% |
| 7 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | R$ 778,8 bi | R$ 841,2 bi | R$ 62,4 bi | 8,01% |
| 8 | 12 | Operações de arrendamento | R$ 25,9 bi | R$ 27,1 bi | R$ 1,2 bi | 4,62% |
| 9 | 05 | Financiamentos à exportação | R$ 324,6 bi | R$ 323,4 bi | -R$ 1,3 bi | -0,40% |
| 10 | 11 | Financiamentos de infraestrutura e desenvolvimento | R$ 124,9 bi | R$ 123,1 bi | -R$ 1,8 bi | -1,48% |
| 11 | 03 | Direitos creditórios descontados | R$ 39,5 bi | R$ 37,8 bi | -R$ 1,6 bi | -4,16% |
| 12 | 06 | Financiamentos à importação | R$ 20,6 bi | R$ 16,7 bi | -R$ 3,9 bi | -19,08% |
| 13 | 07 | Financiamentos com interveniência | R$ 3,4 bi | R$ 1,8 bi | -R$ 1,6 bi | -47,14% |

**Leitura `reais`:** Crescimento da carteira em 12 meses, em reais, no nível de modalidade. As cinco primeiras do ranking.

[`Q02_reais.sql`](../evaluation/gabarito/Q02_reais.sql)

| Posição | Código modalidade | Modalidade | Carteira 12 meses antes | Carteira no último mês | Crescimento em reais | Crescimento |
|---|---|---|---|---|---|---|
| 1 | 02 | Empréstimos | R$ 2.422,0 bi | R$ 2.625,5 bi | R$ 203,5 bi | 8,40% |
| 2 | 09 | Financiamentos imobiliários | R$ 1.328,5 bi | R$ 1.496,2 bi | R$ 167,8 bi | 12,63% |
| 3 | 04 | Financiamentos | R$ 1.180,7 bi | R$ 1.312,2 bi | R$ 131,6 bi | 11,14% |
| 4 | 13 | Outros créditos | R$ 690,2 bi | R$ 783,5 bi | R$ 93,3 bi | 13,52% |
| 5 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | R$ 778,8 bi | R$ 841,2 bi | R$ 62,4 bi | 8,01% |
| 6 | 12 | Operações de arrendamento | R$ 25,9 bi | R$ 27,1 bi | R$ 1,2 bi | 4,62% |
| 7 | 01 | Adiantamentos a depositantes | R$ 1,7 bi | R$ 1,9 bi | R$ 166,4 mi | 9,56% |
| 8 | 10 | Financiamentos de títulos e valores mobiliários | R$ 99,1 mi | R$ 176,2 mi | R$ 77,1 mi | 77,78% |
| 9 | 05 | Financiamentos à exportação | R$ 324,6 bi | R$ 323,4 bi | -R$ 1,3 bi | -0,40% |
| 10 | 07 | Financiamentos com interveniência | R$ 3,4 bi | R$ 1,8 bi | -R$ 1,6 bi | -47,14% |
| 11 | 03 | Direitos creditórios descontados | R$ 39,5 bi | R$ 37,8 bi | -R$ 1,6 bi | -4,16% |
| 12 | 11 | Financiamentos de infraestrutura e desenvolvimento | R$ 124,9 bi | R$ 123,1 bi | -R$ 1,8 bi | -1,48% |
| 13 | 06 | Financiamentos à importação | R$ 20,6 bi | R$ 16,7 bi | -R$ 3,9 bi | -19,08% |

**Observação:** No percentual, uma modalidade de base muito pequena pode liderar o ranking com pouco dinheiro. É o motivo de a leitura em reais também valer.

### Q03. Qual a participação de pessoa física versus pessoa jurídica na carteira total, e como evoluiu nos últimos 24 meses?

**Tipo de acerto:** `valor`

**Fonte da definição:** `dimensoes.dim_cliente`, `metricas.carteira_ativa`

**Como se responde:** Participação de PF e PJ na carteira ativa, mês a mês, do mês 24 meses antes do último até o último.

[`Q03.sql`](../evaluation/gabarito/Q03.sql)

<details><summary>25 linhas</summary>

| Mês | Carteira PF | Carteira PJ | Participação PF | Participação PJ |
|---|---|---|---|---|
| jul/2024 | R$ 3.805,1 bi | R$ 2.465,4 bi | 60,68% | 39,32% |
| ago/2024 | R$ 3.850,0 bi | R$ 2.490,1 bi | 60,72% | 39,28% |
| set/2024 | R$ 3.893,9 bi | R$ 2.531,3 bi | 60,60% | 39,40% |
| out/2024 | R$ 3.943,8 bi | R$ 2.548,1 bi | 60,75% | 39,25% |
| nov/2024 | R$ 3.998,6 bi | R$ 2.600,8 bi | 60,59% | 39,41% |
| dez/2024 | R$ 4.044,4 bi | R$ 2.644,2 bi | 60,47% | 39,53% |
| jan/2025 | R$ 4.087,0 bi | R$ 2.561,4 bi | 61,47% | 38,53% |
| fev/2025 | R$ 4.117,4 bi | R$ 2.602,2 bi | 61,27% | 38,73% |
| mar/2025 | R$ 4.155,6 bi | R$ 2.625,5 bi | 61,28% | 38,72% |
| abr/2025 | R$ 4.188,8 bi | R$ 2.626,6 bi | 61,46% | 38,54% |
| mai/2025 | R$ 4.206,5 bi | R$ 2.664,8 bi | 61,22% | 38,78% |
| jun/2025 | R$ 4.241,7 bi | R$ 2.681,7 bi | 61,27% | 38,73% |
| jul/2025 | R$ 4.272,4 bi | R$ 2.668,6 bi | 61,55% | 38,45% |
| ago/2025 | R$ 4.313,8 bi | R$ 2.694,8 bi | 61,55% | 38,45% |
| set/2025 | R$ 4.351,9 bi | R$ 2.809,7 bi | 60,77% | 39,23% |
| out/2025 | R$ 4.416,0 bi | R$ 2.805,4 bi | 61,15% | 38,85% |
| nov/2025 | R$ 4.475,5 bi | R$ 2.827,1 bi | 61,29% | 38,71% |
| dez/2025 | R$ 4.525,1 bi | R$ 2.919,2 bi | 60,79% | 39,21% |
| jan/2026 | R$ 4.566,4 bi | R$ 2.867,3 bi | 61,43% | 38,57% |
| fev/2026 | R$ 4.592,7 bi | R$ 2.852,9 bi | 61,68% | 38,32% |
| mar/2026 | R$ 4.642,0 bi | R$ 2.898,2 bi | 61,56% | 38,44% |
| abr/2026 | R$ 4.667,0 bi | R$ 2.888,1 bi | 61,77% | 38,23% |
| mai/2026 | R$ 4.693,1 bi | R$ 2.901,2 bi | 61,80% | 38,20% |
| jun/2026 | R$ 4.685,4 bi | R$ 2.951,7 bi | 61,35% | 38,65% |
| jul/2026 | R$ 4.680,6 bi | R$ 2.910,1 bi | 61,66% | 38,34% |

</details>

### Q04. Qual o crescimento da carteira por segmento de instituição, separando bancos tradicionais de instituições de pagamento e fintechs?

**Tipo de acerto:** `valor`

**Fonte da definição:** `dimensoes.dim_segmento`, `metricas.carteira_ativa`

**Como se responde:** Crescimento da carteira por segmento de instituição, em 12 meses e no recorte inteiro. Banco tradicional é o segmento Banco; instituição de pagamento e fintech são segmentos próprios da V2.

[`Q04.sql`](../evaluation/gabarito/Q04.sql)

| Segmento | Início do recorte | Carteira no início do recorte | Carteira 12 meses antes | Carteira no último mês | Crescimento 12 meses | Crescimento no recorte |
|---|---|---|---|---|---|---|
| Instituição de pagamento | jan/2024 | R$ 65,3 bi | R$ 90,9 bi | R$ 121,7 bi | 33,93% | 86,54% |
| Fintech | jan/2024 | R$ 2,3 bi | R$ 6,1 bi | R$ 8,1 bi | 32,35% | 256,18% |
| Financeira | jan/2024 | R$ 231,6 bi | R$ 343,6 bi | R$ 414,4 bi | 20,62% | 78,93% |
| Cooperativa | jan/2024 | R$ 396,1 bi | R$ 482,9 bi | R$ 527,0 bi | 9,13% | 33,03% |
| Banco | jan/2024 | R$ 4.900,3 bi | R$ 5.605,3 bi | R$ 6.079,9 bi | 8,47% | 24,07% |
| Arrendamento | jan/2024 | R$ 13,8 bi | R$ 18,9 bi | R$ 20,4 bi | 7,96% | 48,46% |
| Outros | jan/2024 | R$ 5,6 bi | R$ 6,1 bi | R$ 6,6 bi | 7,63% | 17,60% |
| Desenvolvimento/Fomento | jan/2024 | R$ 346,1 bi | R$ 387,1 bi | R$ 412,4 bi | 6,54% | 19,14% |

### Q05. Qual percentual da carteira nacional está concentrado nas cinco UFs de maior volume?

**Tipo de acerto:** `valor`

**Fonte da definição:** `dimensoes.dim_uf`, `dimensoes.uf_e_domicilio_ou_sede`

**Como se responde:** Participação acumulada das cinco UFs de maior carteira ativa no último mês.

[`Q05.sql`](../evaluation/gabarito/Q05.sql)

| Posição | UF | Carteira ativa | Participação | Participação acumulada |
|---|---|---|---|---|
| 1 | SP | R$ 2.277,7 bi | 30,01% | 30,01% |
| 2 | MG | R$ 672,1 bi | 8,85% | 38,86% |
| 3 | RJ | R$ 571,9 bi | 7,53% | 46,40% |
| 4 | PR | R$ 566,4 bi | 7,46% | 53,86% |
| 5 | RS | R$ 534,5 bi | 7,04% | 60,90% |

## Risco e inadimplência

### Q06. Qual a taxa de inadimplência atual por modalidade, ordenada da maior para a menor?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.indicador_inadimplencia`

**Como se responde:** Taxa de inadimplência por modalidade no último mês, como razão de somas: carteira inadimplida sobre carteira ativa. A média das taxas dos recortes não é a taxa da modalidade.

[`Q06.sql`](../evaluation/gabarito/Q06.sql)

| Código modalidade | Modalidade | Carteira ativa | Carteira inadimplência | Taxa inadimplência |
|---|---|---|---|---|
| 01 | Adiantamentos a depositantes | R$ 1,9 bi | R$ 1,1 bi | 57,24% |
| 02 | Empréstimos | R$ 2.625,5 bi | R$ 227,6 bi | 8,67% |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | R$ 841,2 bi | R$ 54,9 bi | 6,52% |
| 03 | Direitos creditórios descontados | R$ 37,8 bi | R$ 1,7 bi | 4,40% |
| 04 | Financiamentos | R$ 1.312,2 bi | R$ 45,5 bi | 3,47% |
| 09 | Financiamentos imobiliários | R$ 1.496,2 bi | R$ 19,6 bi | 1,31% |
| 12 | Operações de arrendamento | R$ 27,1 bi | R$ 245,3 mi | 0,91% |
| 13 | Outros créditos | R$ 783,5 bi | R$ 6,9 bi | 0,88% |
| 05 | Financiamentos à exportação | R$ 323,4 bi | R$ 2,5 bi | 0,77% |
| 07 | Financiamentos com interveniência | R$ 1,8 bi | R$ 7,3 mi | 0,40% |
| 11 | Financiamentos de infraestrutura e desenvolvimento | R$ 123,1 bi | R$ 40,9 mi | 0,03% |
| 06 | Financiamentos à importação | R$ 16,7 bi | R$ 4,0 mi | 0,02% |
| 10 | Financiamentos de títulos e valores mobiliários | R$ 176,2 mi | R$ 26.835,17 | 0,02% |

### Q07. Quais modalidades tiveram maior deterioração de inadimplência nos últimos seis meses?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.indicador_inadimplencia`

**Leitura `pontos`:** Variação da taxa de inadimplência em 6 meses, por modalidade, em pontos percentuais.

[`Q07_pontos.sql`](../evaluation/gabarito/Q07_pontos.sql)

| Posição | Código modalidade | Modalidade | Taxa 6 meses antes | Taxa no último mês | Variação | Variação relativa |
|---|---|---|---|---|---|---|
| 1 | 01 | Adiantamentos a depositantes | 56,27% | 57,24% | 0,98 p.p. | 1,73% |
| 2 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 5,75% | 6,52% | 0,77 p.p. | 13,41% |
| 3 | 02 | Empréstimos | 8,04% | 8,67% | 0,63 p.p. | 7,83% |
| 4 | 03 | Direitos creditórios descontados | 3,87% | 4,40% | 0,52 p.p. | 13,48% |
| 5 | 04 | Financiamentos | 3,06% | 3,47% | 0,40 p.p. | 13,15% |
| 6 | 07 | Financiamentos com interveniência | 0,35% | 0,40% | 0,05 p.p. | 14,61% |
| 7 | 13 | Outros créditos | 0,83% | 0,88% | 0,05 p.p. | 5,41% |
| 8 | 11 | Financiamentos de infraestrutura e desenvolvimento | 0,01% | 0,03% | 0,02 p.p. | 165,70% |
| 9 | 10 | Financiamentos de títulos e valores mobiliários | 0,00% | 0,02% | 0,02 p.p. |  |
| 10 | 05 | Financiamentos à exportação | 0,76% | 0,77% | 0,01 p.p. | 1,84% |
| 11 | 06 | Financiamentos à importação | 0,02% | 0,02% | 0,00 p.p. | 10,86% |
| 12 | 09 | Financiamentos imobiliários | 1,36% | 1,31% | -0,05 p.p. | -3,48% |
| 13 | 12 | Operações de arrendamento | 1,50% | 0,91% | -0,60 p.p. | -39,71% |

**Leitura `relativa`:** Variação relativa da taxa de inadimplência em 6 meses, por modalidade, em percentual da taxa anterior.

[`Q07_relativa.sql`](../evaluation/gabarito/Q07_relativa.sql)

| Posição | Código modalidade | Modalidade | Taxa 6 meses antes | Taxa no último mês | Variação | Variação relativa |
|---|---|---|---|---|---|---|
| 1 | 11 | Financiamentos de infraestrutura e desenvolvimento | 0,01% | 0,03% | 0,02 p.p. | 165,70% |
| 2 | 07 | Financiamentos com interveniência | 0,35% | 0,40% | 0,05 p.p. | 14,61% |
| 3 | 03 | Direitos creditórios descontados | 3,87% | 4,40% | 0,52 p.p. | 13,48% |
| 4 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 5,75% | 6,52% | 0,77 p.p. | 13,41% |
| 5 | 04 | Financiamentos | 3,06% | 3,47% | 0,40 p.p. | 13,15% |
| 6 | 06 | Financiamentos à importação | 0,02% | 0,02% | 0,00 p.p. | 10,86% |
| 7 | 02 | Empréstimos | 8,04% | 8,67% | 0,63 p.p. | 7,83% |
| 8 | 13 | Outros créditos | 0,83% | 0,88% | 0,05 p.p. | 5,41% |
| 9 | 05 | Financiamentos à exportação | 0,76% | 0,77% | 0,01 p.p. | 1,84% |
| 10 | 01 | Adiantamentos a depositantes | 56,27% | 57,24% | 0,98 p.p. | 1,73% |
| 11 | 09 | Financiamentos imobiliários | 1,36% | 1,31% | -0,05 p.p. | -3,48% |
| 12 | 12 | Operações de arrendamento | 1,50% | 0,91% | -0,60 p.p. | -39,71% |
| 13 | 10 | Financiamentos de títulos e valores mobiliários | 0,00% | 0,02% | 0,02 p.p. |  |

### Q08. A inadimplência do cartão de crédito rotativo está acima ou abaixo da média histórica de cinco anos?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.sub_0204`, `modalidades.cartao_de_credito_em_tres_modalidades`, `metricas.indicador_inadimplencia`

**Como se responde:** Taxa de inadimplência do rotativo do cartão, só a submodalidade 0204, no último mês, contra a média das taxas mensais em todo o recorte disponível.

[`Q08.sql`](../evaluation/gabarito/Q08.sql)

| Mês | Taxa no último mês | Média das taxas mensais | Início da média | Meses na média | Acima da média |
|---|---|---|---|---|---|
| jul/2026 | 13,47% | 13,99% | jan/2024 | 31 | não |

**Observação:** A pergunta pede a média de cinco anos, e o recorte do projeto é menor (triagem da ontologia, item 1.3). A resposta precisa dizer a janela que usou. Somar o cartão parcelado (0210, 0218, 0406) ou o lojista (1304) ao rotativo é erro.

### Q09. Qual a diferença entre inadimplência e ativo problemático nesta base, e qual o gap entre as duas métricas por modalidade?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `metricas.carteira_inadimplencia`, `metricas.ativo_problematico`

**Como se responde:** Distância entre ativo problemático e carteira inadimplida, por modalidade, no último mês, em reais e em pontos percentuais da carteira.

[`Q09.sql`](../evaluation/gabarito/Q09.sql)

| Código modalidade | Modalidade | Carteira ativa | Carteira inadimplência | Ativo problemático | Distância em reais | Distância | Critério ativo problemático |
|---|---|---|---|---|---|---|---|
| 07 | Financiamentos com interveniência | R$ 1,8 bi | R$ 7,3 mi | R$ 763,2 mi | R$ 755,9 mi | 41,59 p.p. | Característica especial 19, informada pela instituição |
| 01 | Adiantamentos a depositantes | R$ 1,9 bi | R$ 1,1 bi | R$ 1,2 bi | R$ 142,7 mi | 7,48 p.p. | Característica especial 19, informada pela instituição |
| 03 | Direitos creditórios descontados | R$ 37,8 bi | R$ 1,7 bi | R$ 4,1 bi | R$ 2,4 bi | 6,34 p.p. | Característica especial 19, informada pela instituição |
| 11 | Financiamentos de infraestrutura e desenvolvimento | R$ 123,1 bi | R$ 40,9 mi | R$ 6,0 bi | R$ 5,9 bi | 4,81 p.p. | Característica especial 19, informada pela instituição |
| 02 | Empréstimos | R$ 2.625,5 bi | R$ 227,6 bi | R$ 347,4 bi | R$ 119,8 bi | 4,56 p.p. | Característica especial 19, informada pela instituição |
| 09 | Financiamentos imobiliários | R$ 1.496,2 bi | R$ 19,6 bi | R$ 74,3 bi | R$ 54,7 bi | 3,66 p.p. | Característica especial 19, informada pela instituição |
| 05 | Financiamentos à exportação | R$ 323,4 bi | R$ 2,5 bi | R$ 13,5 bi | R$ 11,0 bi | 3,40 p.p. | Característica especial 19, informada pela instituição |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | R$ 841,2 bi | R$ 54,9 bi | R$ 78,5 bi | R$ 23,6 bi | 2,81 p.p. | Característica especial 19, informada pela instituição |
| 04 | Financiamentos | R$ 1.312,2 bi | R$ 45,5 bi | R$ 80,4 bi | R$ 34,9 bi | 2,66 p.p. | Característica especial 19, informada pela instituição |
| 13 | Outros créditos | R$ 783,5 bi | R$ 6,9 bi | R$ 27,3 bi | R$ 20,4 bi | 2,61 p.p. | Característica especial 19, informada pela instituição |
| 12 | Operações de arrendamento | R$ 27,1 bi | R$ 245,3 mi | R$ 816,9 mi | R$ 571,6 mi | 2,11 p.p. | Característica especial 19, informada pela instituição |
| 06 | Financiamentos à importação | R$ 16,7 bi | R$ 4,0 mi | R$ 7,3 mi | R$ 3,3 mi | 0,02 p.p. | Característica especial 19, informada pela instituição |
| 10 | Financiamentos de títulos e valores mobiliários | R$ 176,2 mi | R$ 26.835,17 | R$ 26.835,17 | R$ 0,00 | 0,00 p.p. | Característica especial 19, informada pela instituição |

**Ressalva obrigatória:**

- São duas medidas diferentes. A carteira inadimplida soma as operações com alguma parcela vencida há mais de 90 dias. O ativo problemático inclui essas e também as operações com indício de que não serão pagas, como reestruturações.
- O critério do ativo problemático mudou em janeiro de 2025: desde então conta só o que a própria instituição marca como problemático (característica especial 19). A distância antes e depois dessa data não é comparável.

### Q10. Existe alguma modalidade onde a carteira cresce e a inadimplência cai ao mesmo tempo?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.indicador_inadimplencia`, `metricas.carteira_ativa`

**Como se responde:** Modalidades em que a carteira cresce e a taxa de inadimplência cai na mesma janela, em 12 meses e no recorte inteiro.

[`Q10.sql`](../evaluation/gabarito/Q10.sql)

| Código modalidade | Modalidade | Crescimento 12 meses | Variação taxa 12 meses | Cresce e inadimplência cai em 12 meses | Crescimento no recorte | Variação taxa no recorte | Cresce e inadimplência cai no recorte |
|---|---|---|---|---|---|---|---|
| 01 | Adiantamentos a depositantes | 9,56% | -5,99 p.p. | sim | 24,99% | 7,05 p.p. | não |
| 02 | Empréstimos | 8,40% | 0,93 p.p. | não | 26,51% | 2,12 p.p. | não |
| 03 | Direitos creditórios descontados | -4,16% | 0,67 p.p. | não | 5,70% | 0,90 p.p. | não |
| 04 | Financiamentos | 11,14% | 0,67 p.p. | não | 28,46% | 1,27 p.p. | não |
| 05 | Financiamentos à exportação | -0,40% | -0,05 p.p. | não | 24,47% | 0,58 p.p. | não |
| 06 | Financiamentos à importação | -19,08% | 0,00 p.p. | não | 6,04% | -0,06 p.p. | sim |
| 07 | Financiamentos com interveniência | -47,14% | 0,01 p.p. | não | -46,12% | 0,28 p.p. | não |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 8,01% | 3,10 p.p. | não | 21,42% | 5,64 p.p. | não |
| 09 | Financiamentos imobiliários | 12,63% | 0,16 p.p. | não | 34,46% | -0,17 p.p. | sim |
| 10 | Financiamentos de títulos e valores mobiliários | 77,78% | 0,02 p.p. | não | -88,13% | 0,01 p.p. | não |
| 11 | Financiamentos de infraestrutura e desenvolvimento | -1,48% | 0,02 p.p. | não | 11,39% | 0,03 p.p. | não |
| 12 | Operações de arrendamento | 4,62% | 0,15 p.p. | não | 25,99% | 0,29 p.p. | não |
| 13 | Outros créditos | 13,52% | 0,16 p.p. | não | 28,67% | -0,12 p.p. | sim |

## Expansão geográfica e priorização

### Q11. Quais UFs têm maior carteira de crédito de pessoa jurídica por habitante?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.populacao_residente_estimada`, `dimensoes.uf_e_domicilio_ou_sede`

**Como se responde:** Carteira de PJ por habitante, por UF, no último mês, com a estimativa de população do IBGE do mesmo ano.

[`Q11.sql`](../evaluation/gabarito/Q11.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Carteira PJ | População | Ano da população | Carteira PJ por habitante |
|---|---|---|---|---|---|
| 1 | DF | R$ 68,5 bi | 3.009.996 | 2.026 | R$ 22.758,75 |
| 2 | SP | R$ 1.027,7 bi | 46.179.008 | 2.026 | R$ 22.254,31 |
| 3 | SC | R$ 184,8 bi | 8.312.759 | 2.026 | R$ 22.234,98 |
| 4 | MT | R$ 84,1 bi | 3.950.330 | 2.026 | R$ 21.290,38 |
| 5 | PR | R$ 211,9 bi | 11.952.456 | 2.026 | R$ 17.727,56 |
| 6 | RS | R$ 189,7 bi | 11.233.317 | 2.026 | R$ 16.886,69 |
| 7 | RJ | R$ 279,3 bi | 17.225.410 | 2.026 | R$ 16.217,04 |
| 8 | MS | R$ 39,1 bi | 2.946.317 | 2.026 | R$ 13.285,89 |
| 9 | ES | R$ 53,4 bi | 4.150.692 | 2.026 | R$ 12.861,26 |
| 10 | GO | R$ 88,5 bi | 7.495.033 | 2.026 | R$ 11.809,11 |
| 11 | MG | R$ 226,1 bi | 21.460.311 | 2.026 | R$ 10.534,83 |
| 12 | TO | R$ 16,2 bi | 1.595.994 | 2.026 | R$ 10.149,40 |
| 13 | PI | R$ 28,3 bi | 3.392.617 | 2.026 | R$ 8.342,66 |
| 14 | AP | R$ 6,3 bi | 809.953 | 2.026 | R$ 7.767,24 |
| 15 | AM | R$ 33,8 bi | 4.360.926 | 2.026 | R$ 7.756,63 |
| 16 | BA | R$ 103,8 bi | 14.889.472 | 2.026 | R$ 6.972,45 |
| 17 | RO | R$ 12,0 bi | 1.757.338 | 2.026 | R$ 6.852,15 |
| 18 | CE | R$ 58,6 bi | 9.302.211 | 2.026 | R$ 6.302,70 |
| 19 | PA | R$ 54,8 bi | 8.756.324 | 2.026 | R$ 6.261,26 |
| 20 | RN | R$ 18,8 bi | 3.463.737 | 2.026 | R$ 5.442,08 |
| 21 | AC | R$ 4,8 bi | 887.794 | 2.026 | R$ 5.427,17 |
| 22 | PE | R$ 50,7 bi | 9.583.176 | 2.026 | R$ 5.289,15 |
| 23 | AL | R$ 16,6 bi | 3.221.128 | 2.026 | R$ 5.140,60 |
| 24 | RR | R$ 3,7 bi | 761.012 | 2.026 | R$ 4.852,41 |
| 25 | SE | R$ 9,4 bi | 2.307.255 | 2.026 | R$ 4.088,77 |
| 26 | MA | R$ 24,7 bi | 7.024.557 | 2.026 | R$ 3.513,73 |
| 27 | PB | R$ 14,2 bi | 4.182.828 | 2.026 | R$ 3.402,54 |

</details>

**Observação:** A população é estimativa anual, com referência em 1º de julho, aplicada a todos os meses do ano.

### Q12. Quais UFs mais cresceram em carteira nos últimos 12 meses, ajustado por população?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.populacao_residente_estimada`

**Leitura `reais`:** Crescimento da carteira por habitante em 12 meses, por UF, em reais.

[`Q12_reais.sql`](../evaluation/gabarito/Q12_reais.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Carteira por habitante 12 meses antes | Carteira por habitante no último mês | Crescimento por habitante em reais | Crescimento por habitante |
|---|---|---|---|---|---|
| 1 | SP | R$ 43.666,43 | R$ 49.324,12 | R$ 5.657,69 | 12,96% |
| 2 | PR | R$ 43.471,95 | R$ 47.391,44 | R$ 3.919,49 | 9,02% |
| 3 | RS | R$ 43.934,14 | R$ 47.585,65 | R$ 3.651,51 | 8,31% |
| 4 | SC | R$ 46.480,78 | R$ 50.076,97 | R$ 3.596,19 | 7,74% |
| 5 | ES | R$ 28.682,84 | R$ 31.876,72 | R$ 3.193,88 | 11,14% |
| 6 | TO | R$ 33.989,71 | R$ 36.792,66 | R$ 2.802,95 | 8,25% |
| 7 | RR | R$ 19.291,94 | R$ 22.045,27 | R$ 2.753,33 | 14,27% |
| 8 | GO | R$ 43.112,74 | R$ 45.804,53 | R$ 2.691,79 | 6,24% |
| 9 | AP | R$ 21.469,54 | R$ 24.070,82 | R$ 2.601,29 | 12,12% |
| 10 | MS | R$ 45.955,81 | R$ 48.415,41 | R$ 2.459,59 | 5,35% |
| 11 | MT | R$ 64.360,87 | R$ 66.776,07 | R$ 2.415,20 | 3,75% |
| 12 | CE | R$ 16.660,98 | R$ 18.915,07 | R$ 2.254,08 | 13,53% |
| 13 | MG | R$ 29.160,12 | R$ 31.318,85 | R$ 2.158,73 | 7,40% |
| 14 | PI | R$ 18.479,71 | R$ 20.427,67 | R$ 1.947,96 | 10,54% |
| 15 | RO | R$ 34.716,53 | R$ 36.633,54 | R$ 1.917,01 | 5,52% |
| 16 | RN | R$ 19.065,54 | R$ 20.963,54 | R$ 1.898,00 | 9,96% |
| 17 | PA | R$ 17.344,12 | R$ 19.236,97 | R$ 1.892,85 | 10,91% |
| 18 | AC | R$ 20.593,11 | R$ 22.452,82 | R$ 1.859,70 | 9,03% |
| 19 | BA | R$ 18.129,17 | R$ 19.916,34 | R$ 1.787,17 | 9,86% |
| 20 | PE | R$ 16.358,15 | R$ 18.118,63 | R$ 1.760,48 | 10,76% |
| 21 | PB | R$ 16.764,04 | R$ 18.499,33 | R$ 1.735,29 | 10,35% |
| 22 | AM | R$ 16.656,06 | R$ 18.381,42 | R$ 1.725,36 | 10,36% |
| 23 | AL | R$ 17.174,32 | R$ 18.668,75 | R$ 1.494,42 | 8,70% |
| 24 | MA | R$ 15.168,18 | R$ 16.292,63 | R$ 1.124,45 | 7,41% |
| 25 | RJ | R$ 32.549,50 | R$ 33.203,22 | R$ 653,72 | 2,01% |
| 26 | SE | R$ 18.379,44 | R$ 18.451,98 | R$ 72,54 | 0,39% |
| 27 | DF | R$ 53.257,61 | R$ 52.850,44 | -R$ 407,17 | -0,76% |

</details>

**Leitura `percentual`:** Crescimento da carteira por habitante em 12 meses, por UF, em percentual.

[`Q12_percentual.sql`](../evaluation/gabarito/Q12_percentual.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Carteira por habitante 12 meses antes | Carteira por habitante no último mês | Crescimento por habitante em reais | Crescimento por habitante |
|---|---|---|---|---|---|
| 1 | RR | R$ 19.291,94 | R$ 22.045,27 | R$ 2.753,33 | 14,27% |
| 2 | CE | R$ 16.660,98 | R$ 18.915,07 | R$ 2.254,08 | 13,53% |
| 3 | SP | R$ 43.666,43 | R$ 49.324,12 | R$ 5.657,69 | 12,96% |
| 4 | AP | R$ 21.469,54 | R$ 24.070,82 | R$ 2.601,29 | 12,12% |
| 5 | ES | R$ 28.682,84 | R$ 31.876,72 | R$ 3.193,88 | 11,14% |
| 6 | PA | R$ 17.344,12 | R$ 19.236,97 | R$ 1.892,85 | 10,91% |
| 7 | PE | R$ 16.358,15 | R$ 18.118,63 | R$ 1.760,48 | 10,76% |
| 8 | PI | R$ 18.479,71 | R$ 20.427,67 | R$ 1.947,96 | 10,54% |
| 9 | AM | R$ 16.656,06 | R$ 18.381,42 | R$ 1.725,36 | 10,36% |
| 10 | PB | R$ 16.764,04 | R$ 18.499,33 | R$ 1.735,29 | 10,35% |
| 11 | RN | R$ 19.065,54 | R$ 20.963,54 | R$ 1.898,00 | 9,96% |
| 12 | BA | R$ 18.129,17 | R$ 19.916,34 | R$ 1.787,17 | 9,86% |
| 13 | AC | R$ 20.593,11 | R$ 22.452,82 | R$ 1.859,70 | 9,03% |
| 14 | PR | R$ 43.471,95 | R$ 47.391,44 | R$ 3.919,49 | 9,02% |
| 15 | AL | R$ 17.174,32 | R$ 18.668,75 | R$ 1.494,42 | 8,70% |
| 16 | RS | R$ 43.934,14 | R$ 47.585,65 | R$ 3.651,51 | 8,31% |
| 17 | TO | R$ 33.989,71 | R$ 36.792,66 | R$ 2.802,95 | 8,25% |
| 18 | SC | R$ 46.480,78 | R$ 50.076,97 | R$ 3.596,19 | 7,74% |
| 19 | MA | R$ 15.168,18 | R$ 16.292,63 | R$ 1.124,45 | 7,41% |
| 20 | MG | R$ 29.160,12 | R$ 31.318,85 | R$ 2.158,73 | 7,40% |
| 21 | GO | R$ 43.112,74 | R$ 45.804,53 | R$ 2.691,79 | 6,24% |
| 22 | RO | R$ 34.716,53 | R$ 36.633,54 | R$ 1.917,01 | 5,52% |
| 23 | MS | R$ 45.955,81 | R$ 48.415,41 | R$ 2.459,59 | 5,35% |
| 24 | MT | R$ 64.360,87 | R$ 66.776,07 | R$ 2.415,20 | 3,75% |
| 25 | RJ | R$ 32.549,50 | R$ 33.203,22 | R$ 653,72 | 2,01% |
| 26 | SE | R$ 18.379,44 | R$ 18.451,98 | R$ 72,54 | 0,39% |
| 27 | DF | R$ 53.257,61 | R$ 52.850,44 | -R$ 407,17 | -0,76% |

</details>

**Observação:** Os doze meses atravessam dois anos de estimativa de população, e cada mês usa a do próprio ano.

### Q13. Existe correlação entre renda média por UF e taxa de inadimplência?

**Tipo de acerto:** `valor`

**Pendente:** depende de #38. Renda média por UF ainda não está no projeto.

### Q14. Quais UFs estão sub-atendidas em crédito de pessoa jurídica, considerando o número de empresas ativas na região?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `fontes_externas.empresa_ativa`, `fontes_externas.estoque_reconstruido`, `fontes_externas.grupo_de_natureza_juridica`, `fontes_externas.mei`, `dimensoes.uf_e_domicilio_ou_sede`

**Leitura `empresariais_sem_mei`:** Carteira PJ por empresa ativa de natureza empresarial, sem MEI, que é o denominador da camada de decisão (ADR 0014). Sub-atendida é a UF abaixo da mediana das UFs.

[`Q14_empresariais_sem_mei.sql`](../evaluation/gabarito/Q14_empresariais_sem_mei.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Carteira PJ | Empresas ativas | Carteira por empresa | Mediana das UFs | Abaixo da mediana |
|---|---|---|---|---|---|---|
| 1 | PB | R$ 14,2 bi | 127.890 | R$ 111.284,95 | R$ 227.622,39 | sim |
| 2 | MA | R$ 24,7 bi | 175.472 | R$ 140.662,74 | R$ 227.622,39 | sim |
| 3 | SE | R$ 9,4 bi | 66.324 | R$ 142.238,50 | R$ 227.622,39 | sim |
| 4 | RN | R$ 18,8 bi | 118.031 | R$ 159.703,24 | R$ 227.622,39 | sim |
| 5 | RO | R$ 12,0 bi | 69.759 | R$ 172.616,45 | R$ 227.622,39 | sim |
| 6 | PE | R$ 50,7 bi | 286.571 | R$ 176.873,48 | R$ 227.622,39 | sim |
| 7 | RR | R$ 3,7 bi | 19.733 | R$ 187.135,38 | R$ 227.622,39 | sim |
| 8 | CE | R$ 58,6 bi | 307.338 | R$ 190.764,13 | R$ 227.622,39 | sim |
| 9 | AL | R$ 16,6 bi | 86.131 | R$ 192.248,37 | R$ 227.622,39 | sim |
| 10 | MG | R$ 226,1 bi | 1.118.115 | R$ 202.198,14 | R$ 227.622,39 | sim |
| 11 | AC | R$ 4,8 bi | 23.348 | R$ 206.364,90 | R$ 227.622,39 | sim |
| 12 | GO | R$ 88,5 bi | 422.064 | R$ 209.706,75 | R$ 227.622,39 | sim |
| 13 | BA | R$ 103,8 bi | 490.565 | R$ 211.625,53 | R$ 227.622,39 | sim |
| 14 | PA | R$ 54,8 bi | 240.862 | R$ 227.622,39 | R$ 227.622,39 | não |
| 15 | TO | R$ 16,2 bi | 70.659 | R$ 229.247,36 | R$ 227.622,39 | não |
| 16 | PR | R$ 211,9 bi | 885.978 | R$ 239.157,01 | R$ 227.622,39 | não |
| 17 | ES | R$ 53,4 bi | 218.108 | R$ 244.755,53 | R$ 227.622,39 | não |
| 18 | MS | R$ 39,1 bi | 154.522 | R$ 253.326,02 | R$ 227.622,39 | não |
| 19 | PI | R$ 28,3 bi | 107.315 | R$ 263.741,92 | R$ 227.622,39 | não |
| 20 | AP | R$ 6,3 bi | 23.713 | R$ 265.301,76 | R$ 227.622,39 | não |
| 21 | RS | R$ 189,7 bi | 713.304 | R$ 265.936,52 | R$ 227.622,39 | não |
| 22 | AM | R$ 33,8 bi | 121.446 | R$ 278.527,94 | R$ 227.622,39 | não |
| 23 | SC | R$ 184,8 bi | 653.782 | R$ 282.715,05 | R$ 227.622,39 | não |
| 24 | SP | R$ 1.027,7 bi | 3.564.816 | R$ 288.284,69 | R$ 227.622,39 | não |
| 25 | DF | R$ 68,5 bi | 220.809 | R$ 310.239,89 | R$ 227.622,39 | não |
| 26 | MT | R$ 84,1 bi | 246.423 | R$ 341.299,37 | R$ 227.622,39 | não |
| 27 | RJ | R$ 279,3 bi | 809.405 | R$ 345.124,00 | R$ 227.622,39 | não |

</details>

**Leitura `todas_as_empresas`:** Carteira PJ por empresa ativa, com todas as empresas, inclusive MEI e entidades sem fins lucrativos. Sub-atendida é a UF abaixo da mediana das UFs.

[`Q14_todas_as_empresas.sql`](../evaluation/gabarito/Q14_todas_as_empresas.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Carteira PJ | Empresas ativas | Carteira por empresa | Mediana das UFs | Abaixo da mediana |
|---|---|---|---|---|---|---|
| 1 | PB | R$ 14,2 bi | 337.597 | R$ 42.157,46 | R$ 95.084,41 | sim |
| 2 | SE | R$ 9,4 bi | 164.473 | R$ 57.357,90 | R$ 95.084,41 | sim |
| 3 | RN | R$ 18,8 bi | 290.294 | R$ 64.933,94 | R$ 95.084,41 | sim |
| 4 | MA | R$ 24,7 bi | 356.212 | R$ 69.291,25 | R$ 95.084,41 | sim |
| 5 | PE | R$ 50,7 bi | 729.361 | R$ 69.494,82 | R$ 95.084,41 | sim |
| 6 | AL | R$ 16,6 bi | 224.065 | R$ 73.900,63 | R$ 95.084,41 | sim |
| 7 | RO | R$ 12,0 bi | 160.221 | R$ 75.155,89 | R$ 95.084,41 | sim |
| 8 | RR | R$ 3,7 bi | 47.053 | R$ 78.480,49 | R$ 95.084,41 | sim |
| 9 | MG | R$ 226,1 bi | 2.804.249 | R$ 80.620,79 | R$ 95.084,41 | sim |
| 10 | CE | R$ 58,6 bi | 713.307 | R$ 82.193,31 | R$ 95.084,41 | sim |
| 11 | BA | R$ 103,8 bi | 1.204.849 | R$ 86.165,22 | R$ 95.084,41 | sim |
| 12 | GO | R$ 88,5 bi | 995.913 | R$ 88.872,89 | R$ 95.084,41 | sim |
| 13 | ES | R$ 53,4 bi | 579.915 | R$ 92.053,38 | R$ 95.084,41 | sim |
| 14 | TO | R$ 16,2 bi | 170.358 | R$ 95.084,41 | R$ 95.084,41 | não |
| 15 | AC | R$ 4,8 bi | 50.636 | R$ 95.153,80 | R$ 95.084,41 | não |
| 16 | PA | R$ 54,8 bi | 518.659 | R$ 105.706,42 | R$ 95.084,41 | não |
| 17 | MS | R$ 39,1 bi | 356.576 | R$ 109.778,68 | R$ 95.084,41 | não |
| 18 | PR | R$ 211,9 bi | 1.915.018 | R$ 110.645,36 | R$ 95.084,41 | não |
| 19 | RS | R$ 189,7 bi | 1.659.581 | R$ 114.302,09 | R$ 95.084,41 | não |
| 20 | PI | R$ 28,3 bi | 230.799 | R$ 122.632,52 | R$ 95.084,41 | não |
| 21 | AM | R$ 33,8 bi | 271.845 | R$ 124.431,59 | R$ 95.084,41 | não |
| 22 | SC | R$ 184,8 bi | 1.482.087 | R$ 124.711,98 | R$ 95.084,41 | não |
| 23 | SP | R$ 1.027,7 bi | 8.180.743 | R$ 125.622,07 | R$ 95.084,41 | não |
| 24 | RJ | R$ 279,3 bi | 2.198.492 | R$ 127.062,14 | R$ 95.084,41 | não |
| 25 | AP | R$ 6,3 bi | 47.375 | R$ 132.793,68 | R$ 95.084,41 | não |
| 26 | DF | R$ 68,5 bi | 452.122 | R$ 151.516,09 | R$ 95.084,41 | não |
| 27 | MT | R$ 84,1 bi | 535.474 | R$ 157.064,61 | R$ 95.084,41 | não |

</details>

**Ressalva obrigatória:**

- A UF do SCR é a do domicílio da pessoa ou da sede da empresa, e não o lugar onde o crédito foi usado.

**Observação:** O número de empresas é reconstruído de um único retrato do CNPJ, com erro medido por UF (ADR 0009).

### Q15. A relação entre carteira de pessoa física e massa salarial regional sugere sobre-endividamento em alguma UF?

**Tipo de acerto:** `valor`

**Pendente:** depende de #38. Massa salarial por UF ainda não está no projeto.

## Modalidade e produto

### Q16. Qual a evolução do crédito consignado versus crédito pessoal não consignado nos últimos três anos?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.sub_0202`, `modalidades.sub_0203`

**Como se responde:** Carteira de crédito pessoal com consignação (0202) e sem consignação (0203), mês a mês, com o crescimento acumulado de cada uma no recorte.

[`Q16.sql`](../evaluation/gabarito/Q16.sql)

<details><summary>31 linhas</summary>

| Mês | Consignado | Não consignado | Participação do consignado | Crescimento acumulado consignado | Crescimento acumulado não consignado |
|---|---|---|---|---|---|
| jan/2024 | R$ 643,2 bi | R$ 271,5 bi | 70,32% | 0,00% | 0,00% |
| fev/2024 | R$ 650,0 bi | R$ 276,8 bi | 70,13% | 1,05% | 1,94% |
| mar/2024 | R$ 654,1 bi | R$ 280,6 bi | 69,98% | 1,70% | 3,36% |
| abr/2024 | R$ 658,0 bi | R$ 283,7 bi | 69,87% | 2,30% | 4,49% |
| mai/2024 | R$ 661,7 bi | R$ 286,6 bi | 69,77% | 2,87% | 5,57% |
| jun/2024 | R$ 665,6 bi | R$ 287,6 bi | 69,83% | 3,48% | 5,93% |
| jul/2024 | R$ 671,8 bi | R$ 291,5 bi | 69,74% | 4,45% | 7,35% |
| ago/2024 | R$ 676,7 bi | R$ 296,8 bi | 69,51% | 5,21% | 9,30% |
| set/2024 | R$ 681,3 bi | R$ 301,1 bi | 69,35% | 5,92% | 10,88% |
| out/2024 | R$ 685,4 bi | R$ 308,1 bi | 68,99% | 6,56% | 13,48% |
| nov/2024 | R$ 689,4 bi | R$ 313,8 bi | 68,72% | 7,18% | 15,56% |
| dez/2024 | R$ 690,9 bi | R$ 315,4 bi | 68,66% | 7,41% | 16,16% |
| jan/2025 | R$ 698,3 bi | R$ 324,6 bi | 68,27% | 8,56% | 19,54% |
| fev/2025 | R$ 706,0 bi | R$ 330,0 bi | 68,14% | 9,76% | 21,55% |
| mar/2025 | R$ 711,9 bi | R$ 333,4 bi | 68,10% | 10,68% | 22,80% |
| abr/2025 | R$ 718,5 bi | R$ 340,3 bi | 67,86% | 11,70% | 25,32% |
| mai/2025 | R$ 723,7 bi | R$ 343,4 bi | 67,82% | 12,51% | 26,47% |
| jun/2025 | R$ 720,0 bi | R$ 347,9 bi | 67,42% | 11,95% | 28,14% |
| jul/2025 | R$ 723,9 bi | R$ 353,6 bi | 67,18% | 12,54% | 30,24% |
| ago/2025 | R$ 729,4 bi | R$ 356,8 bi | 67,15% | 13,40% | 31,40% |
| set/2025 | R$ 735,1 bi | R$ 359,8 bi | 67,14% | 14,29% | 32,53% |
| out/2025 | R$ 743,4 bi | R$ 367,8 bi | 66,90% | 15,58% | 35,46% |
| nov/2025 | R$ 749,5 bi | R$ 370,1 bi | 66,94% | 16,52% | 36,32% |
| dez/2025 | R$ 751,8 bi | R$ 368,7 bi | 67,10% | 16,88% | 35,77% |
| jan/2026 | R$ 765,7 bi | R$ 376,4 bi | 67,04% | 19,05% | 38,62% |
| fev/2026 | R$ 774,9 bi | R$ 380,7 bi | 67,06% | 20,48% | 40,20% |
| mar/2026 | R$ 783,8 bi | R$ 380,7 bi | 67,31% | 21,86% | 40,20% |
| abr/2026 | R$ 790,0 bi | R$ 382,2 bi | 67,39% | 22,82% | 40,78% |
| mai/2026 | R$ 796,1 bi | R$ 383,1 bi | 67,51% | 23,77% | 41,09% |
| jun/2026 | R$ 797,9 bi | R$ 375,4 bi | 68,01% | 24,05% | 38,25% |
| jul/2026 | R$ 791,8 bi | R$ 373,7 bi | 67,94% | 23,10% | 37,64% |

</details>

**Observação:** A pergunta pede três anos, e o recorte do projeto é menor. A resposta precisa dizer a janela que usou.

### Q17. Modalidades com garantia real apresentam inadimplência sistematicamente menor? Quantifique.

**Tipo de acerto:** `abstencao`

**Fonte da definição:** `modalidades.garantia_nao_declarada`, `modalidades.sub_0211`

**A resposta certa é reconhecer o limite.** O dado não diz quais modalidades têm garantia real. Entre as definições normativas, só a do home equity (0211) declara garantia real: operações garantidas por hipoteca ou alienação fiduciária de imóvel residencial. As de capital de giro (0215 e 0216) citam "garantias" apenas como item do contrato, sem dizer qual. O SCR.data não publica o campo de garantias do documento 3040. A única comparação possível é a do home equity com o restante da carteira de pessoa física, e ela não generaliza para "modalidades com garantia real".

**O que faltaria:** O tipo de garantia por operação, que existe no documento 3040 (Anexo 12 do leiaute) e não é publicado no SCR.data.

**Como se responde:** A prova da ausência, pelas definições que citam garantia, e a taxa de inadimplência do home equity contra o restante da PF em todos os meses do recorte.

[`Q17_definicoes.sql`](../evaluation/gabarito/Q17_definicoes.sql)

| Código submodalidade | Modalidade | Submodalidade | Definição |
|---|---|---|---|
| 0211 | Empréstimos | Home Equity | empréstimos a pessoas físicas, garantidos por hipoteca ou por alienação fiduciária de bens imóveis residenciais, sem vinculação a aquisição de bens |
| 0215 | Empréstimos | Capital de giro com prazo de vencimento até 365 dias | operações de crédito voltadas para o financiamento de curto prazo (igual ou inferior a 365 dias) das pessoas jurídicas, vinculadas às necessidades de capital de giro e a um contrato específico que estabeleça prazos, taxas e garantias |
| 0216 | Empréstimos | Capital de giro com prazo de vencimento superior a 365 dias | operações de crédito voltadas para o financiamento de médio e longo prazo (superior a 365 dias) das pessoas jurídicas, vinculadas às necessidades de capital de giro e a um contrato específico que estabeleça prazos, taxas e garantias |

[`Q17_home_equity.sql`](../evaluation/gabarito/Q17_home_equity.sql)

| Meses | Meses com home equity abaixo | Média home equity | Média restante PF | Mínima home equity | Máxima home equity |
|---|---|---|---|---|---|
| 31 | 31 | 2,26% | 4,55% | 1,93% | 2,72% |

### Q18. Qual o ticket médio implícito por modalidade, e a base permite esse cálculo?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `metricas.numero_de_operacoes`, `docs/sentinela-numero-de-operacoes.md`

**Como se responde:** Ticket médio por modalidade no último mês: carteira dividida pelo número de operações, só nos recortes com contagem divulgada, e a parcela da carteira que fica de fora.

[`Q18.sql`](../evaluation/gabarito/Q18.sql)

| Código modalidade | Modalidade | Carteira com contagem | Operações divulgadas | Ticket medio | Carteira sem contagem |
|---|---|---|---|---|---|
| 11 | Financiamentos de infraestrutura e desenvolvimento | R$ 73,1 bi | 6.778 | R$ 10,8 mi | 40,66% |
| 05 | Financiamentos à exportação | R$ 247,6 bi | 36.714 | R$ 6,7 mi | 23,43% |
| 06 | Financiamentos à importação | R$ 13,6 bi | 8.605 | R$ 1,6 mi | 18,73% |
| 12 | Operações de arrendamento | R$ 17,8 bi | 31.551 | R$ 565.417,05 | 34,14% |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | R$ 805,9 bi | 3.304.530 | R$ 243.865,72 | 4,20% |
| 09 | Financiamentos imobiliários | R$ 1.480,0 bi | 9.491.321 | R$ 155.933,02 | 1,08% |
| 10 | Financiamentos de títulos e valores mobiliários | R$ 1,9 mi | 19 | R$ 102.626,25 | 98,89% |
| 04 | Financiamentos | R$ 1.141,8 bi | 24.839.851 | R$ 45.966,89 | 12,99% |
| 03 | Direitos creditórios descontados | R$ 32,7 bi | 5.446.017 | R$ 5.997,72 | 13,66% |
| 02 | Empréstimos | R$ 2.552,6 bi | 632.995.272 | R$ 4.032,50 | 2,78% |
| 13 | Outros créditos | R$ 748,0 bi | 263.814.797 | R$ 2.835,31 | 4,54% |
| 01 | Adiantamentos a depositantes | R$ 1,9 bi | 1.897.638 | R$ 988,05 | 1,69% |
| 07 | Financiamentos com interveniência | R$ 3,4 mi | 5.974 | R$ 565,71 | 99,81% |

**Ressalva obrigatória:**

- O ticket médio só é calculável sobre os recortes com contagem de operações divulgada. Os recortes sem contagem (o -1 do dado publicado) ficam de fora, e a exclusão não é aleatória: concentra-se em nichos, em UFs menores e em PJ. Tratar o -1 como número dá resultado sem sentido.

### Q19. O crédito rural se comportou de forma diferente do restante da carteira de pessoa jurídica?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.mod_08`, `modalidades.sub_0440`

**Como se responde:** Financiamentos rurais (modalidade 08) de PJ contra o restante da carteira PJ, em crescimento e em taxa de inadimplência, em 12 meses e no recorte inteiro.

[`Q19.sql`](../evaluation/gabarito/Q19.sql)

| Grupo | Crescimento 12 meses | Crescimento no recorte | Taxa no último mês | Variação taxa 12 meses | Variação taxa no recorte |
|---|---|---|---|---|---|
| Financiamentos rurais | 23,82% | 47,14% | 0,79% | 0,36 p.p. | 0,56 p.p. |
| Restante da carteira PJ | 8,29% | 23,06% | 3,15% | 0,35 p.p. | 0,77 p.p. |

**Observação:** O crédito agroindustrial saiu da modalidade rural em 2017 e é a submodalidade 0440, em Financiamentos. Ele fica no restante da carteira PJ.

## Concentração e competição

### Q20. Qual a concentração da carteira entre segmentos de instituição, e ela aumentou ou diminuiu?

**Tipo de acerto:** `valor`

**Fonte da definição:** `dimensoes.dim_segmento`

**Leitura `herfindahl`:** Índice de Herfindahl-Hirschman das participações dos segmentos, de 0 a 10.000, e a variação em 12 meses e no recorte inteiro.

[`Q20_herfindahl.sql`](../evaluation/gabarito/Q20_herfindahl.sql)

| HHI no início do recorte | HHI 12 meses antes | HHI no último mês | Variação 12 meses | Variação no recorte |
|---|---|---|---|---|
| 6.851,77 | 6.627,49 | 6.525,79 | -101,71 | -325,99 |

**Leitura `maior_segmento`:** Participação do maior segmento na carteira, e a variação em 12 meses e no recorte inteiro.

[`Q20_maior_segmento.sql`](../evaluation/gabarito/Q20_maior_segmento.sql)

| Maior segmento | Participação no início do recorte | Participação 12 meses antes | Participação no último mês | Variação 12 meses | Variação no recorte |
|---|---|---|---|---|---|
| Banco | 82,20% | 80,76% | 80,10% | -0,66 p.p. | -2,11 p.p. |

### Q21. Instituições de pagamento e fintechs ganharam participação de mercado em quais modalidades?

**Tipo de acerto:** `valor`

**Fonte da definição:** `dimensoes.dim_segmento`, `dimensoes.granularidade_encolhe_em_julho_de_2025`

**Como se responde:** Participação de instituições de pagamento e de fintechs na carteira de cada modalidade, e o ganho em pontos percentuais em 12 meses e no recorte inteiro.

[`Q21.sql`](../evaluation/gabarito/Q21.sql)

| Código modalidade | Modalidade | Participação IP no último mês | Ganho IP 12 meses | Ganho IP no recorte | Participação fintech no último mês | Ganho fintech 12 meses | Ganho fintech no recorte |
|---|---|---|---|---|---|---|---|
| 01 | Adiantamentos a depositantes | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | -0,00 p.p. |
| 02 | Empréstimos | 0,01% | -0,00 p.p. | -0,04 p.p. | 0,23% | 0,04 p.p. | 0,13 p.p. |
| 03 | Direitos creditórios descontados | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,01% | -0,32 p.p. | -0,01 p.p. |
| 04 | Financiamentos | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,05% | 0,03 p.p. | 0,04 p.p. |
| 05 | Financiamentos à exportação | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 06 | Financiamentos à importação | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 07 | Financiamentos com interveniência | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 09 | Financiamentos imobiliários | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,03% | 0,00 p.p. | 0,03 p.p. |
| 10 | Financiamentos de títulos e valores mobiliários | 0,00% | 0,00 p.p. | 0,00 p.p. | 56,20% | 56,20 p.p. | 56,20 p.p. |
| 11 | Financiamentos de infraestrutura e desenvolvimento | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 12 | Operações de arrendamento | 0,00% | 0,00 p.p. | 0,00 p.p. | 0,00% | 0,00 p.p. | 0,00 p.p. |
| 13 | Outros créditos | 15,52% | 2,37 p.p. | 4,96 p.p. | 0,11% | 0,01 p.p. | 0,09 p.p. |

**Observação:** Em modalidade muito pequena, um ganho grande de participação é pouco dinheiro. A queda de recortes de julho de 2025 atinge as instituições de pagamento, mas não a carteira, e por isso não afeta a participação.

## PIX e mudança estrutural

### Q22. Qual a evolução do volume financeiro de PIX nos últimos 24 meses?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.volume_de_pix`, `fontes_externas.pix_por_uf_depende_do_lado`

**Como se responde:** Volume mensal do PIX liquidado no SPI, do mês 24 meses antes do último até o último, pelo lado pagador e com a linha sem UF, que pertence ao total do país.

[`Q22.sql`](../evaluation/gabarito/Q22.sql)

<details><summary>25 linhas</summary>

| Mês | Volume | Crescimento desde o início da janela |
|---|---|---|
| jul/2024 | R$ 1.954,8 bi | 0,00% |
| ago/2024 | R$ 1.948,2 bi | -0,34% |
| set/2024 | R$ 1.937,1 bi | -0,91% |
| out/2024 | R$ 2.088,4 bi | 6,84% |
| nov/2024 | R$ 2.081,6 bi | 6,49% |
| dez/2024 | R$ 2.329,1 bi | 19,15% |
| jan/2025 | R$ 2.076,8 bi | 6,24% |
| fev/2025 | R$ 2.044,4 bi | 4,59% |
| mar/2025 | R$ 2.172,4 bi | 11,14% |
| abr/2025 | R$ 2.254,1 bi | 15,31% |
| mai/2025 | R$ 2.379,2 bi | 21,71% |
| jun/2025 | R$ 2.395,4 bi | 22,54% |
| jul/2025 | R$ 2.562,0 bi | 31,07% |
| ago/2025 | R$ 2.550,2 bi | 30,46% |
| set/2025 | R$ 2.651,6 bi | 35,65% |
| out/2025 | R$ 2.635,8 bi | 34,84% |
| nov/2025 | R$ 2.607,7 bi | 33,40% |
| dez/2025 | R$ 3.146,8 bi | 60,98% |
| jan/2026 | R$ 2.699,9 bi | 38,12% |
| fev/2026 | R$ 2.525,4 bi | 29,19% |
| mar/2026 | R$ 3.012,6 bi | 54,12% |
| abr/2026 | R$ 2.896,6 bi | 48,18% |
| mai/2026 | R$ 2.957,4 bi | 51,30% |
| jun/2026 | R$ 3.044,1 bi | 55,73% |
| jul/2026 | R$ 3.223,3 bi | 64,90% |

</details>

**Observação:** Somar pagador e recebedor conta cada transação duas vezes. O PIX liquidado nos livros do próprio participante não está no dado.

### Q23. O crescimento do PIX coincide com retração em alguma modalidade de crédito específica?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.volume_de_pix`, `modalidades.modalidade_e_conta_contabil`

**Leitura `modalidade`:** Modalidades cuja carteira caiu enquanto o PIX cresceu, em 12 meses e no recorte inteiro.

[`Q23_modalidade.sql`](../evaluation/gabarito/Q23_modalidade.sql)

| Código | Nome | Carteira 12 meses | Carteira no recorte | PIX 12 meses | PIX no recorte | Retraiu em 12 meses | Retraiu no recorte |
|---|---|---|---|---|---|---|---|
| 10 | Financiamentos de títulos e valores mobiliários | 77,78% | -88,13% | 25,81% | 117,32% | não | sim |
| 07 | Financiamentos com interveniência | -47,14% | -46,12% | 25,81% | 117,32% | sim | sim |
| 03 | Direitos creditórios descontados | -4,16% | 5,70% | 25,81% | 117,32% | sim | não |
| 06 | Financiamentos à importação | -19,08% | 6,04% | 25,81% | 117,32% | sim | não |
| 11 | Financiamentos de infraestrutura e desenvolvimento | -1,48% | 11,39% | 25,81% | 117,32% | sim | não |
| 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 8,01% | 21,42% | 25,81% | 117,32% | não | não |
| 05 | Financiamentos à exportação | -0,40% | 24,47% | 25,81% | 117,32% | sim | não |
| 01 | Adiantamentos a depositantes | 9,56% | 24,99% | 25,81% | 117,32% | não | não |
| 12 | Operações de arrendamento | 4,62% | 25,99% | 25,81% | 117,32% | não | não |
| 02 | Empréstimos | 8,40% | 26,51% | 25,81% | 117,32% | não | não |
| 04 | Financiamentos | 11,14% | 28,46% | 25,81% | 117,32% | não | não |
| 13 | Outros créditos | 13,52% | 28,67% | 25,81% | 117,32% | não | não |
| 09 | Financiamentos imobiliários | 12,63% | 34,46% | 25,81% | 117,32% | não | não |

**Leitura `submodalidade`:** Submodalidades cuja carteira caiu enquanto o PIX cresceu, em 12 meses e no recorte inteiro.

[`Q23_submodalidade.sql`](../evaluation/gabarito/Q23_submodalidade.sql)

<details><summary>64 linhas</summary>

| Código | Nome | Carteira 12 meses | Carteira no recorte | PIX 12 meses | PIX no recorte | Retraiu em 12 meses | Retraiu no recorte |
|---|---|---|---|---|---|---|---|
| 0208 | Compror | -99,52% | -99,86% | 25,81% | 117,32% | sim | sim |
| 0701 | Aquisição de bens com interveniência - veículos autom. | -92,58% | -94,33% | 25,81% | 117,32% | sim | sim |
| 1001 | Financiamento de TVM | 77,78% | -88,13% | 25,81% | 117,32% | não | sim |
| 0303 | Antecipação de fatura de cartão de crédito | -59,40% | -83,19% | 25,81% | 117,32% | sim | sim |
| 1202 | Arrendamento financeiro imobiliário | -70,90% | -77,20% | 25,81% | 117,32% | sim | sim |
| 0790 | Financiamento de projeto | -4,39% | -71,44% | 25,81% | 117,32% | sim | sim |
| 0406 | Cartão de crédito - compra ou fatura parcelada pela instituição financeira emitente do cartão | -27,12% | -49,19% | 25,81% | 117,32% | sim | sim |
| 0702 | Aquisição de bens com interveniência - outros bens | -49,17% | -47,91% | 25,81% | 117,32% | sim | sim |
| 0207 | Vendor | -35,28% | -41,30% | 25,81% | 117,32% | sim | sim |
| 1303 | Títulos e créditos a receber | 36,60% | -36,85% | 25,81% | 117,32% | não | sim |
| 0398 | Outros direitos creditórios descontados | -21,22% | -29,84% | 25,81% | 117,32% | sim | sim |
| 0302 | Desconto de cheques | -13,18% | -21,19% | 25,81% | 117,32% | sim | sim |
| 0450 | Recebíveis adquiridos | -1,70% | -14,80% | 25,81% | 117,32% | sim | sim |
| 0405 | Compror | 9,36% | -14,01% | 25,81% | 117,32% | não | sim |
| 0204 | Crédito rotativo vinculado a cartão de crédito | -6,54% | -13,21% | 25,81% | 117,32% | sim | sim |
| 0404 | Vendor | 9,77% | -5,84% | 25,81% | 117,32% | não | sim |
| 0903 | Financiamento imobiliário - empreendim, exceto habitac. | 6,21% | 0,81% | 25,81% | 117,32% | não | não |
| 0217 | Capital de giro com teto rotativo | -10,01% | 1,23% | 25,81% | 117,32% | sim | não |
| 0801 | Custeio | -4,15% | 1,26% | 25,81% | 117,32% | sim | não |
| 1350 | Recebíveis adquiridos | 10,00% | 5,21% | 25,81% | 117,32% | não | não |
| 0601 | Financiamento à importação | -19,08% | 6,04% | 25,81% | 117,32% | sim | não |
| 0403 | Microcrédito | -4,31% | 9,49% | 25,81% | 117,32% | sim | não |
| 1101 | Financiamento de infraestrutura e desenvolvimento | 1,20% | 10,44% | 25,81% | 117,32% | não | não |
| 0250 | Recebíveis adquiridos | 21,93% | 11,85% | 25,81% | 117,32% | não | não |
| 0599 | Outros financiamentos à exportação | -13,80% | 11,97% | 25,81% | 117,32% | sim | não |
| 0299 | Outros empréstimos | 11,02% | 12,25% | 25,81% | 117,32% | não | não |
| 0301 | Desconto de duplicatas | -3,45% | 14,01% | 25,81% | 117,32% | sim | não |
| 0503 | Adiantamento sobre cambiais entregues | -24,46% | 14,60% | 25,81% | 117,32% | sim | não |
| 0490 | Financiamento de projeto | 7,89% | 16,17% | 25,81% | 117,32% | não | não |
| 0212 | Microcrédito | -7,95% | 16,29% | 25,81% | 117,32% | sim | não |
| 0501 | Financiamento à exportação | 3,32% | 16,97% | 25,81% | 117,32% | não | não |
| 0504 | Créd decorrentes de contratos de exportação-export note | 9,36% | 19,68% | 25,81% | 117,32% | não | não |
| 0216 | Capital de giro com prazo de vencimento superior a 365 dias | 7,95% | 20,59% | 25,81% | 117,32% | não | não |
| 0214 | Conta Garantida | 1,88% | 21,19% | 25,81% | 117,32% | não | não |
| 0213 | Cheque especial | 10,66% | 21,23% | 25,81% | 117,32% | não | não |
| 1205 | Arrendamento operacional | -4,27% | 21,40% | 25,81% | 117,32% | sim | não |
| 0202 | Crédito pessoal - com consignação em folha de pagam. | 9,38% | 23,10% | 25,81% | 117,32% | não | não |
| 1201 | Arrendamento financeiro exceto veículos automotores e imóveis | 4,16% | 23,39% | 25,81% | 117,32% | não | não |
| 1302 | Devedores por compra de valores e bens | -0,59% | 24,27% | 25,81% | 117,32% | sim | não |
| 0101 | Adiantamentos a depositantes | 9,56% | 24,99% | 25,81% | 117,32% | não | não |
| 1190 | Financiamento de projeto | -28,14% | 26,63% | 25,81% | 117,32% | sim | não |
| 0401 | Aquisição de bens - veículos automotores | 8,33% | 28,44% | 25,81% | 117,32% | não | não |
| 0402 | Aquisição de bens - outros bens | 4,55% | 28,70% | 25,81% | 117,32% | não | não |
| 0901 | Financiamento habitacional - SFH | 11,34% | 31,02% | 25,81% | 117,32% | não | não |
| 0802 | Investimento | 14,10% | 32,56% | 25,81% | 117,32% | não | não |
| 0440 | Financiamentos agroindustriais | 23,05% | 33,73% | 25,81% | 117,32% | não | não |
| 0210 | Cartão de crédito - compra, fatura parcelada ou saque financiado pela instituição financeira emitente do cartão | 2,26% | 34,45% | 25,81% | 117,32% | não | não |
| 1304 | Cartão de crédito - compra à vista e parcelado lojista | 12,71% | 34,83% | 25,81% | 117,32% | não | não |
| 0203 | Crédito pessoal - sem consignação em folha de pagam. | 5,68% | 37,64% | 25,81% | 117,32% | não | não |
| 0502 | Adiantamento sobre contratos de câmbio | 1,10% | 39,15% | 25,81% | 117,32% | não | não |
| 0803 | Comercialização | 11,58% | 42,17% | 25,81% | 117,32% | não | não |
| 0399 | Outros títulos descontados | 27,35% | 43,13% | 25,81% | 117,32% | não | não |
| 0804 | Industrialização | 34,18% | 49,35% | 25,81% | 117,32% | não | não |
| 1206 | Arrendamento financeiro de veículos automotores | 13,51% | 50,70% | 25,81% | 117,32% | não | não |
| 0290 | Financiamento de projeto | 11,04% | 54,21% | 25,81% | 117,32% | não | não |
| 0211 | Home Equity | 20,34% | 61,61% | 25,81% | 117,32% | não | não |
| 0902 | Financiamento habitacional  exceto SFH | 22,05% | 67,36% | 25,81% | 117,32% | não | não |
| 0218 | Cartão de crédito - não migrado | 27,36% | 70,75% | 25,81% | 117,32% | não | não |
| 0499 | Outros financiamentos | 37,19% | 83,98% | 25,81% | 117,32% | não | não |
| 1399 | Outros com característica de crédito | 149,13% | 114,33% | 25,81% | 117,32% | não | não |
| 0215 | Capital de giro com prazo de vencimento até 365 dias | 9,66% | 194,26% | 25,81% | 117,32% | não | não |
| 0799 | Outros financiamentos com interveniência | 474,85% | 195,62% | 25,81% | 117,32% | não | não |
| 1301 | Avais e fianças honrados | 18,26% | 435,15% | 25,81% | 117,32% | não | não |
| 0990 | Financiamento de projeto | 75,95% | 1.864,99% | 25,81% | 117,32% | não | não |

</details>

**Observação:** Coincidência no tempo não é causa, e a série é curta.

### Q24. Qual a razão entre volume de PIX e carteira de crédito, por UF?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.pix_por_uf_depende_do_lado`, `fontes_externas.volume_de_pix`

**Leitura `pagador`:** Volume de PIX do último mês pela UF do pagador, dividido pela carteira ativa da UF.

[`Q24_pagador.sql`](../evaluation/gabarito/Q24_pagador.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Volume PIX | Carteira ativa | Razão PIX sobre carteira |
|---|---|---|---|---|
| 1 | SP | R$ 1.222,8 bi | R$ 2.277,7 bi | 0,537 |
| 2 | AM | R$ 42,9 bi | R$ 80,2 bi | 0,535 |
| 3 | PB | R$ 38,5 bi | R$ 77,4 bi | 0,497 |
| 4 | RJ | R$ 267,8 bi | R$ 571,9 bi | 0,468 |
| 5 | ES | R$ 61,1 bi | R$ 132,3 bi | 0,461 |
| 6 | PE | R$ 78,7 bi | R$ 173,6 bi | 0,453 |
| 7 | CE | R$ 79,6 bi | R$ 176,0 bi | 0,453 |
| 8 | DF | R$ 71,3 bi | R$ 159,1 bi | 0,448 |
| 9 | MA | R$ 51,0 bi | R$ 114,4 bi | 0,446 |
| 10 | SE | R$ 17,7 bi | R$ 42,6 bi | 0,417 |
| 11 | RR | R$ 6,8 bi | R$ 16,8 bi | 0,407 |
| 12 | PA | R$ 67,9 bi | R$ 168,4 bi | 0,403 |
| 13 | BA | R$ 116,6 bi | R$ 296,5 bi | 0,393 |
| 14 | AL | R$ 23,2 bi | R$ 60,1 bi | 0,386 |
| 15 | PR | R$ 217,5 bi | R$ 566,4 bi | 0,384 |
| 16 | PI | R$ 26,6 bi | R$ 69,3 bi | 0,384 |
| 17 | MG | R$ 255,6 bi | R$ 672,1 bi | 0,380 |
| 18 | AC | R$ 7,2 bi | R$ 19,9 bi | 0,362 |
| 19 | RN | R$ 26,1 bi | R$ 72,6 bi | 0,360 |
| 20 | AP | R$ 6,9 bi | R$ 19,5 bi | 0,356 |
| 21 | SC | R$ 142,1 bi | R$ 416,3 bi | 0,341 |
| 22 | TO | R$ 19,1 bi | R$ 58,7 bi | 0,325 |
| 23 | GO | R$ 101,2 bi | R$ 343,3 bi | 0,295 |
| 24 | RO | R$ 18,8 bi | R$ 64,4 bi | 0,292 |
| 25 | MT | R$ 70,5 bi | R$ 263,8 bi | 0,267 |
| 26 | RS | R$ 141,4 bi | R$ 534,5 bi | 0,264 |
| 27 | MS | R$ 37,6 bi | R$ 142,6 bi | 0,264 |

</details>

**Leitura `recebedor`:** Volume de PIX do último mês pela UF do recebedor, dividido pela carteira ativa da UF.

[`Q24_recebedor.sql`](../evaluation/gabarito/Q24_recebedor.sql)

<details><summary>27 linhas</summary>

| Posição | UF | Volume PIX | Carteira ativa | Razão PIX sobre carteira |
|---|---|---|---|---|
| 1 | DF | R$ 100,2 bi | R$ 159,1 bi | 0,630 |
| 2 | SP | R$ 1.247,7 bi | R$ 2.277,7 bi | 0,548 |
| 3 | AM | R$ 42,4 bi | R$ 80,2 bi | 0,529 |
| 4 | PB | R$ 38,2 bi | R$ 77,4 bi | 0,494 |
| 5 | RJ | R$ 260,2 bi | R$ 571,9 bi | 0,455 |
| 6 | ES | R$ 59,7 bi | R$ 132,3 bi | 0,452 |
| 7 | PE | R$ 76,0 bi | R$ 173,6 bi | 0,438 |
| 8 | CE | R$ 76,4 bi | R$ 176,0 bi | 0,434 |
| 9 | MA | R$ 47,7 bi | R$ 114,4 bi | 0,417 |
| 10 | SE | R$ 17,4 bi | R$ 42,6 bi | 0,408 |
| 11 | RR | R$ 6,6 bi | R$ 16,8 bi | 0,393 |
| 12 | BA | R$ 114,7 bi | R$ 296,5 bi | 0,387 |
| 13 | PA | R$ 65,1 bi | R$ 168,4 bi | 0,387 |
| 14 | PR | R$ 216,6 bi | R$ 566,4 bi | 0,382 |
| 15 | MG | R$ 249,2 bi | R$ 672,1 bi | 0,371 |
| 16 | PI | R$ 25,5 bi | R$ 69,3 bi | 0,368 |
| 17 | AL | R$ 21,9 bi | R$ 60,1 bi | 0,365 |
| 18 | RN | R$ 25,3 bi | R$ 72,6 bi | 0,348 |
| 19 | AP | R$ 6,6 bi | R$ 19,5 bi | 0,340 |
| 20 | AC | R$ 6,8 bi | R$ 19,9 bi | 0,340 |
| 21 | SC | R$ 132,8 bi | R$ 416,3 bi | 0,319 |
| 22 | TO | R$ 18,5 bi | R$ 58,7 bi | 0,315 |
| 23 | GO | R$ 101,3 bi | R$ 343,3 bi | 0,295 |
| 24 | RO | R$ 18,7 bi | R$ 64,4 bi | 0,290 |
| 25 | RS | R$ 137,1 bi | R$ 534,5 bi | 0,257 |
| 26 | MT | R$ 67,6 bi | R$ 263,8 bi | 0,256 |
| 27 | MS | R$ 35,9 bi | R$ 142,6 bi | 0,251 |

</details>

**Observação:** PIX é fluxo do mês e carteira é saldo: a razão compara grandezas de natureza diferente.

## Contexto econômico

### Q25. Como a inadimplência se comportou frente à trajetória da Selic nos últimos três anos?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.selic_meta`, `metricas.indicador_inadimplencia`

**Como se responde:** Meta da Selic do Copom e taxa de inadimplência total, mês a mês, no recorte inteiro.

[`Q25.sql`](../evaluation/gabarito/Q25.sql)

<details><summary>31 linhas</summary>

| Mês | Selic meta | Taxa inadimplência |
|---|---|---|
| jan/2024 | 11,75% | 3,18% |
| fev/2024 | 11,25% | 3,19% |
| mar/2024 | 10,75% | 3,14% |
| abr/2024 | 10,75% | 3,17% |
| mai/2024 | 10,50% | 3,22% |
| jun/2024 | 10,50% | 3,11% |
| jul/2024 | 10,50% | 3,13% |
| ago/2024 | 10,50% | 3,16% |
| set/2024 | 10,75% | 3,14% |
| out/2024 | 10,75% | 3,10% |
| nov/2024 | 11,25% | 3,06% |
| dez/2024 | 12,25% | 2,99% |
| jan/2025 | 13,25% | 3,30% |
| fev/2025 | 13,25% | 3,41% |
| mar/2025 | 14,25% | 3,41% |
| abr/2025 | 14,25% | 3,63% |
| mai/2025 | 14,75% | 3,72% |
| jun/2025 | 15,00% | 3,74% |
| jul/2025 | 15,00% | 3,93% |
| ago/2025 | 15,00% | 4,10% |
| set/2025 | 15,00% | 3,99% |
| out/2025 | 15,00% | 4,17% |
| nov/2025 | 15,00% | 4,19% |
| dez/2025 | 15,00% | 4,10% |
| jan/2026 | 15,00% | 4,42% |
| fev/2026 | 15,00% | 4,65% |
| mar/2026 | 14,75% | 4,53% |
| abr/2026 | 14,50% | 4,75% |
| mai/2026 | 14,50% | 4,84% |
| jun/2026 | 14,25% | 4,63% |
| jul/2026 | 14,25% | 4,74% |

</details>

**Observação:** A pergunta pede três anos, e o recorte do projeto é menor. É a meta do Copom, e não a taxa efetiva (ADR 0010).

### Q26. Existe defasagem entre variação da Selic e variação da inadimplência? De quantos meses?

**Tipo de acerto:** `valor`

**Fonte da definição:** `fontes_externas.selic_meta`, `metricas.indicador_inadimplencia`

**Como se responde:** Correlação entre a variação mensal da meta da Selic e a variação mensal da taxa de inadimplência, com a inadimplência deslocada de 0 a 12 meses. A defasagem candidata é a de maior correlação.

[`Q26.sql`](../evaluation/gabarito/Q26.sql)

| Defasagem em meses | Correlação | Pares |
|---|---|---|
| 0 | 0,113 | 30 |
| 1 | 0,312 | 29 |
| 2 | 0,220 | 28 |
| 3 | 0,159 | 27 |
| 4 | 0,295 | 26 |
| 5 | 0,216 | 25 |
| 6 | -0,061 | 24 |
| 7 | 0,354 | 23 |
| 8 | 0,118 | 22 |
| 9 | -0,064 | 21 |
| 10 | 0,092 | 20 |
| 11 | -0,116 | 19 |
| 12 | -0,224 | 18 |

**Observação:** A série é curta e tem poucas decisões do Copom. A resposta precisa tratar a defasagem como estimativa, com esse limite declarado, e não afirmar um número de meses como fato.

### Q27. Qual a projeção de carteira para os próximos três meses, com intervalo de confiança?

**Tipo de acerto:** `valor`

**Pendente:** depende de #27. A projeção entra na v0.2, com backtest e erro publicado.

## Automação do trabalho repetitivo

### Q28. Gerar o resumo executivo mensal: carteira total, variação mensal e anual, três modalidades que mais cresceram, e três com maior deterioração de inadimplência.

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.carteira_ativa`, `metricas.indicador_inadimplencia`

**Leitura `no_mes`:** Carteira total com a variação mensal e a anual, e as três modalidades de maior crescimento e de maior deterioração da inadimplência no mês.

[`Q28_totais.sql`](../evaluation/gabarito/Q28_totais.sql)

| Mês | Carteira ativa | Variação mensal | Variação anual |
|---|---|---|---|
| jul/2026 | R$ 7.590,7 bi | -0,61% | 9,36% |

[`Q28_crescimento_no_mes.sql`](../evaluation/gabarito/Q28_crescimento_no_mes.sql)

| Posição | Código modalidade | Modalidade | Crescimento |
|---|---|---|---|
| 1 | 10 | Financiamentos de títulos e valores mobiliários | 6,51% |
| 2 | 05 | Financiamentos à exportação | 1,81% |
| 3 | 01 | Adiantamentos a depositantes | 0,54% |

[`Q28_deterioracao_no_mes.sql`](../evaluation/gabarito/Q28_deterioracao_no_mes.sql)

| Posição | Código modalidade | Modalidade | Variação |
|---|---|---|---|
| 1 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 0,88 p.p. |
| 2 | 01 | Adiantamentos a depositantes | 0,81 p.p. |
| 3 | 03 | Direitos creditórios descontados | 0,25 p.p. |

**Leitura `em_12_meses`:** Carteira total com a variação mensal e a anual, e as três modalidades de maior crescimento e de maior deterioração da inadimplência em 12 meses.

[`Q28_totais.sql`](../evaluation/gabarito/Q28_totais.sql)

| Mês | Carteira ativa | Variação mensal | Variação anual |
|---|---|---|---|
| jul/2026 | R$ 7.590,7 bi | -0,61% | 9,36% |

[`Q28_crescimento_12_meses.sql`](../evaluation/gabarito/Q28_crescimento_12_meses.sql)

| Posição | Código modalidade | Modalidade | Crescimento |
|---|---|---|---|
| 1 | 10 | Financiamentos de títulos e valores mobiliários | 77,78% |
| 2 | 13 | Outros créditos | 13,52% |
| 3 | 09 | Financiamentos imobiliários | 12,63% |

[`Q28_deterioracao_12_meses.sql`](../evaluation/gabarito/Q28_deterioracao_12_meses.sql)

| Posição | Código modalidade | Modalidade | Variação |
|---|---|---|---|
| 1 | 08 | Financiamentos rurais  (ex-financiamentos rurais e agroindustriais) | 3,10 p.p. |
| 2 | 02 | Empréstimos | 0,93 p.p. |
| 3 | 04 | Financiamentos | 0,67 p.p. |

### Q29. Quais métricas mudaram de comportamento de forma estatisticamente atípica no último mês frente à tendência?

**Tipo de acerto:** `valor`

**Fonte da definição:** `metricas.carteira_ativa`, `metricas.indicador_inadimplencia`, `metricas.indicador_ativo_problematico`

**Leitura `12_meses`:** Variação do último mês de cada métrica nacional contra a média e o desvio padrão amostral das 12 variações anteriores. Atípica quando o z passa de 2 em módulo.

[`Q29_12_meses.sql`](../evaluation/gabarito/Q29_12_meses.sql)

| Métrica | Unidade | Mês | Variação no último mês | Média das variações anteriores | Desvio padrão | Variações no histórico | Z | Atípica |
|---|---|---|---|---|---|---|---|---|
| carteira_ativa | percentual | jul/2026 | -0,61 | 0,82 | 0,72 | 12 | -1,995 | não |
| carteira_a_vencer | percentual | jul/2026 | -0,64 | 0,77 | 0,81 | 12 | -1,754 | não |
| carteira_vencida | percentual | jul/2026 | 0,43 | 2,60 | 3,39 | 12 | -0,642 | não |
| taxa_ativo_problematico | pontos | jul/2026 | 0,15 | 0,06 | 0,15 | 12 | 0,587 | não |
| ativo_problematico | percentual | jul/2026 | 1,16 | 1,56 | 1,45 | 12 | -0,277 | não |
| taxa_inadimplencia | pontos | jul/2026 | 0,12 | 0,07 | 0,17 | 12 | 0,246 | não |
| carteira_inadimplencia | percentual | jul/2026 | 1,89 | 2,69 | 3,52 | 12 | -0,227 | não |

**Leitura `24_meses`:** A mesma regra contra as 24 variações anteriores.

[`Q29_24_meses.sql`](../evaluation/gabarito/Q29_24_meses.sql)

| Métrica | Unidade | Mês | Variação no último mês | Média das variações anteriores | Desvio padrão | Variações no histórico | Z | Atípica |
|---|---|---|---|---|---|---|---|---|
| carteira_ativa | percentual | jul/2026 | -0,61 | 0,85 | 0,64 | 24 | -2,293 | sim |
| carteira_a_vencer | percentual | jul/2026 | -0,64 | 0,80 | 0,72 | 24 | -2,019 | sim |
| carteira_vencida | percentual | jul/2026 | 0,43 | 2,67 | 3,43 | 24 | -0,653 | não |
| taxa_ativo_problematico | pontos | jul/2026 | 0,15 | 0,05 | 0,18 | 24 | 0,545 | não |
| taxa_inadimplencia | pontos | jul/2026 | 0,12 | 0,06 | 0,14 | 24 | 0,373 | não |
| carteira_inadimplencia | percentual | jul/2026 | 1,89 | 2,58 | 3,27 | 24 | -0,213 | não |
| ativo_problematico | percentual | jul/2026 | 1,16 | 1,51 | 2,10 | 24 | -0,166 | não |

**Observação:** O resultado depende da janela, do limiar e do desvio padrão usado (amostral ou populacional), e uma métrica pode ficar perto do limiar. Na janela de 24 meses, o histórico inclui a mudança de critério do ativo problemático de janeiro de 2025.

### Q30. Quais modalidades mudaram de classificação ou taxonomia ao longo do período, e como isso afeta a comparabilidade da série histórica?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `docs/analise-v1-v2.md`, `docs/adr/0003-conformacao-de-taxonomia-entre-versoes.md`, `modalidades.nem_todo_par_ocorre_em_todo_mes`

**Como se responde:** As submodalidades da V2 que não aparecem em todos os meses, e a série no padrão da V1 reconstruída a partir da V2, contra a V1 publicada, por modalidade da V1, no último mês.

[`Q30_presenca.sql`](../evaluation/gabarito/Q30_presenca.sql)

| Código submodalidade | Modalidade | Submodalidade | Meses com dado | Meses no recorte | Primeiro mês | Último mês |
|---|---|---|---|---|---|---|
| 0209 | Empréstimos | ARO - adiantamento de receitas orçamentárias | 2 | 31 | dez/2024 | jan/2025 |
| 0590 | Financiamentos à exportação | Financiamento de projeto | 16 | 31 | abr/2025 | jul/2026 |

[`Q30_comparabilidade.sql`](../evaluation/gabarito/Q30_comparabilidade.sql)

<details><summary>16 linhas</summary>

| Modalidade V1 | Carteira V1 publicada | Carteira V2 conformada | Diferenca |
|---|---|---|---|
| PJ - Outros créditos | R$ 207,1 bi | R$ 375,5 bi | 81,29% |
| PJ - Comércio exterior | R$ 257,8 bi | R$ 302,8 bi | 17,44% |
| PJ - Investimento | R$ 311,0 bi | R$ 335,8 bi | 7,96% |
| PJ - Financiamento de infraestrutura/desenvolvimento/projeto e outros créditos | R$ 653,1 bi | R$ 697,0 bi | 6,72% |
| PF - Empréstimo com consignação em folha | R$ 754,9 bi | R$ 791,8 bi | 4,88% |
| PJ - Operações com recebíveis | R$ 192,8 bi | R$ 200,1 bi | 3,78% |
| PF - Cartão de crédito | R$ 717,7 bi | R$ 743,5 bi | 3,61% |
| PJ - Rural e agroindustrial | R$ 88,7 bi | R$ 91,8 bi | 3,45% |
| PF - Veículos | R$ 408,3 bi | R$ 422,1 bi | 3,36% |
| PJ - Capital de giro | R$ 761,9 bi | R$ 781,0 bi | 2,50% |
| PF - Empréstimo sem consignação em folha | R$ 369,2 bi | R$ 373,7 bi | 1,22% |
| PF - Outros créditos | R$ 261,0 bi | R$ 263,4 bi | 0,90% |
| PJ - Cheque especial e conta garantida | R$ 64,2 bi | R$ 64,7 bi | 0,75% |
| PF - Habitacional | R$ 1.402,3 bi | R$ 1.405,2 bi | 0,21% |
| PF - Rural e agroindustrial | R$ 680,8 bi | R$ 681,0 bi | 0,03% |
| PJ - Habitacional | R$ 61,4 bi | R$ 61,4 bi | 0,00% |

</details>

**Ressalva obrigatória:**

- A V1 e a V2 não têm nenhum valor de modalidade em comum: a V1 classifica pela finalidade do crédito, e a V2 pela natureza contábil da operação. Uma série que agrupe por modalidade atravessando as duas soma categorias incomparáveis.
- A série reconstruída no padrão da V1 reproduz a classificação, e não os totais: a diferença contra a V1 publicada não é uniforme por modalidade.
- A V1 continua publicada, ao contrário do que diz o portal de dados abertos.

## Armadilhas de classificação (novo em 2026-09-22)

### Q31. Qual o total de crédito de cartão de crédito no país, somando todas as formas em que ele aparece na base?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.cartao_de_credito_em_tres_modalidades`

**Como se responde:** Soma da carteira das cinco submodalidades de cartão (0204, 0210, 0218, 0406 e 1304), de três modalidades, no último mês.

[`Q31.sql`](../evaluation/gabarito/Q31.sql)

| Código submodalidade | Modalidade | Submodalidade | Carteira ativa | Participação no cartao | Total do cartao |
|---|---|---|---|---|---|
| 1304 | Outros créditos | Cartão de crédito - compra à vista e parcelado lojista | R$ 601,2 bi | 75,06% | R$ 800,9 bi |
| 0210 | Empréstimos | Cartão de crédito - compra, fatura parcelada ou saque financiado pela instituição financeira emitente do cartão | R$ 100,4 bi | 12,53% | R$ 800,9 bi |
| 0218 | Empréstimos | Cartão de crédito - não migrado | R$ 75,1 bi | 9,37% | R$ 800,9 bi |
| 0204 | Empréstimos | Crédito rotativo vinculado a cartão de crédito | R$ 24,1 bi | 3,01% | R$ 800,9 bi |
| 0406 | Financiamentos | Cartão de crédito - compra ou fatura parcelada pela instituição financeira emitente do cartão | R$ 187,9 mi | 0,02% | R$ 800,9 bi |

### Q32. Qual a composição da modalidade 'Outros créditos', e o que isso implica para um ranking de modalidades?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.mod_13`, `metricas.outros_creditos_balde_de_supressao`

**Como se responde:** Composição de Outros créditos por submodalidade no último mês, e o peso da modalidade na carteira total.

[`Q32.sql`](../evaluation/gabarito/Q32.sql)

| Código submodalidade | Submodalidade | Carteira ativa | Participação na modalidade | Participação da modalidade na carteira |
|---|---|---|---|---|
| 1304 | Cartão de crédito - compra à vista e parcelado lojista | R$ 601,2 bi | 76,72% | 10,32% |
| 1350 | Recebíveis adquiridos | R$ 149,1 bi | 19,03% | 10,32% |
| 1399 | Outros com característica de crédito | R$ 14,8 bi | 1,89% | 10,32% |
| 1301 | Avais e fianças honrados | R$ 9,0 bi | 1,15% | 10,32% |
| 1303 | Títulos e créditos a receber | R$ 6,6 bi | 0,85% | 10,32% |
| 1302 | Devedores por compra de valores e bens | R$ 2,9 bi | 0,37% | 10,32% |

**Observação:** O nome sugere resíduo, mas a maior parte é compra no cartão sem juros (1304). Um ranking de modalidades que trate Outros créditos como sobra interpreta errado uma das maiores fatias da carteira.

### Q33. Qual a distribuição da carteira por porte do cliente?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `dimensoes.colunas_polimorficas`, `dimensoes.dim_porte`

**Como se responde:** Carteira por porte no último mês, separada por tipo de cliente, com a participação dentro de cada cliente.

[`Q33.sql`](../evaluation/gabarito/Q33.sql)

<details><summary>14 linhas</summary>

| Cliente | Porte desambiguado | Taxonomia | Carteira ativa | Participação no cliente |
|---|---|---|---|---|
| PF | PF - Acima de 20 salários mínimos | Faixa de rendimento em salários mínimos | R$ 985,8 bi | 21,06% |
| PF | PF - Mais de 5 a 10 salários mínimos | Faixa de rendimento em salários mínimos | R$ 858,7 bi | 18,35% |
| PF | PF - Mais de 3 a 5 salários mínimos | Faixa de rendimento em salários mínimos | R$ 693,8 bi | 14,82% |
| PF | PF - Mais de 1 a 2 salários mínimos | Faixa de rendimento em salários mínimos | R$ 622,8 bi | 13,31% |
| PF | PF - Mais de 10 a 20 salários mínimos | Faixa de rendimento em salários mínimos | R$ 609,6 bi | 13,02% |
| PF | PF - Mais de 2 a 3 salários mínimos | Faixa de rendimento em salários mínimos | R$ 484,8 bi | 10,36% |
| PF | PF - Até 1 salário mínimo | Faixa de rendimento em salários mínimos | R$ 297,6 bi | 6,36% |
| PF | PF - Indisponível | Faixa de rendimento em salários mínimos | R$ 97,5 bi | 2,08% |
| PF | PF - Sem rendimento | Faixa de rendimento em salários mínimos | R$ 29,9 bi | 0,64% |
| PJ | PJ - Grande | Porte da empresa | R$ 1.514,7 bi | 52,05% |
| PJ | PJ - Médio | Porte da empresa | R$ 718,1 bi | 24,68% |
| PJ | PJ - Pequeno | Porte da empresa | R$ 445,6 bi | 15,31% |
| PJ | PJ - Micro | Porte da empresa | R$ 127,8 bi | 4,39% |
| PJ | PJ - Indisponível | Porte da empresa | R$ 103,8 bi | 3,57% |

</details>

**Ressalva obrigatória:**

- Porte tem dois significados: faixa de renda em salários mínimos para PF, e tamanho da empresa para PJ. Agrupar sem separar o cliente mistura duas taxonomias.

### Q34. Qual o total do crédito habitacional fora do Sistema Financeiro de Habitação?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.sub_0902`

**Como se responde:** Carteira da submodalidade 0902, financiamento habitacional fora do SFH, no último mês.

[`Q34.sql`](../evaluation/gabarito/Q34.sql)

| Mês | Carteira ativa |
|---|---|
| jul/2026 | R$ 197,1 bi |

**Observação:** O rótulo da 0902 traz um caractere de controle invisível no lugar do traço. Filtrar pelo texto escrito à mão devolve vazio, sem erro.

### Q35. Existem operações de crédito pessoal consignado com cliente pessoa jurídica? Se sim, o que isso significa?

**Tipo de acerto:** `valor`

**Fonte da definição:** `modalidades.sub_0202`, `docs/adr/0003-conformacao-de-taxonomia-entre-versoes.md`

**Como se responde:** Operações de crédito pessoal consignado (0202) com cliente PJ: em quantos meses aparecem, de que tamanho, e a que modalidade da V1 a tabela oficial de equivalência as atribui.

[`Q35.sql`](../evaluation/gabarito/Q35.sql)

| Modalidade V1 atribuída | Meses com ocorrência | Recortes | Primeiro mês | Último mês | Maior carteira mensal | Maior participação no consignado |
|---|---|---|---|---|---|---|
| PF - Empréstimo com consignação em folha | 14 | 17 | jan/2024 | set/2025 | R$ 3,4 mi | 0,00% |

**Observação:** Existem e são poucas. A tabela de equivalência as atribui à modalidade de PF, o que mostra que o cliente informado nem sempre é o tomador final.

## Limites do dado e comparabilidade (novo em 2026-09-22)

### Q36. Que parcela da carteira está em recortes cuja quantidade de operações não é divulgada, e o que isso impede de calcular?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `metricas.numero_de_operacoes`, `docs/sentinela-numero-de-operacoes.md`

**Como se responde:** Parcela da carteira e das linhas em recortes sem contagem de operações divulgada, no último mês e no recorte inteiro.

[`Q36.sql`](../evaluation/gabarito/Q36.sql)

| Carteira sem contagem no último mês | Linhas sem contagem no último mês | Carteira sem contagem no recorte | Linhas sem contagem no recorte |
|---|---|---|---|
| 6,27% | 26,56% | 6,71% | 26,74% |

**Ressalva obrigatória:**

- A supressão impede calcular o total de operações, o ticket médio e qualquer razão por operação sem viés. O critério da supressão não é publicado, e não é o número de operações.

### Q37. Quantas operações de crédito existem no total na base, no último mês disponível?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `metricas.numero_de_operacoes`

**Como se responde:** Soma do número de operações no último mês, com quantos recortes e quanta carteira não têm contagem divulgada.

[`Q37.sql`](../evaluation/gabarito/Q37.sql)

| Mês | Operações limite inferior | Recortes sem contagem | Carteira sem contagem | Carteira sem contagem |
|---|---|---|---|---|
| jul/2026 | 941.879.067 | 82.407 | R$ 475,9 bi | 6,27% |

**Ressalva obrigatória:**

- A soma é um limite inferior, e não o total: os recortes sem contagem divulgada ficam de fora dela.

### Q38. A comparação do ativo problemático entre dezembro de 2024 e janeiro de 2025 é válida? Quantifique o efeito.

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `metricas.ativo_problematico`, `metricas.carteira_inadimplencia`, `docs/cadeia-normativa.md`

**Leitura `v2`:** Variação de carteira, carteira inadimplida e ativo problemático no mês da mudança de critério, na V2, contra a menor e a maior variação mensal dos outros meses.

[`Q38_v2.sql`](../evaluation/gabarito/Q38_v2.sql)

| Medida | Mês da quebra | Valor no mês anterior | Valor no mês da quebra | Variação na quebra | Menor variação nos outros meses | Maior variação nos outros meses |
|---|---|---|---|---|---|---|
| ativo_problematico | jan/2025 | R$ 435,4 bi | R$ 466,8 bi | 7,20% | -0,92% | 6,18% |
| ativo_problematico_sem_atraso_acima_de_90_dias | jan/2025 | R$ 235,4 bi | R$ 247,6 bi | 5,21% | -3,23% | 11,58% |
| carteira_ativa | jan/2025 | R$ 6.688,6 bi | R$ 6.648,4 bi | -0,60% | -0,61% | 2,18% |
| carteira_inadimplida | jan/2025 | R$ 200,1 bi | R$ 219,2 bi | 9,55% | -3,78% | 7,64% |

**Leitura `v1`:** A mesma comparação na V1, que publica as mesmas medidas com a taxonomia antiga.

[`Q38_v1.sql`](../evaluation/gabarito/Q38_v1.sql)

| Medida | Mês da quebra | Valor no mês anterior | Valor no mês da quebra | Variação na quebra | Menor variação nos outros meses | Maior variação nos outros meses |
|---|---|---|---|---|---|---|
| ativo_problematico | jan/2025 | R$ 421,0 bi | R$ 452,6 bi | 7,49% | -0,97% | 4,58% |
| ativo_problematico_sem_atraso_acima_de_90_dias | jan/2025 | R$ 225,7 bi | R$ 238,2 bi | 5,55% | -3,37% | 8,12% |
| carteira_ativa | jan/2025 | R$ 6.397,9 bi | R$ 6.395,6 bi | -0,04% | -0,59% | 1,84% |
| carteira_inadimplida | jan/2025 | R$ 195,4 bi | R$ 214,4 bi | 9,74% | -3,81% | 7,87% |

**Ressalva obrigatória:**

- A comparação entre dezembro de 2024 e janeiro de 2025 não é válida sem ressalva: em janeiro de 2025 o ativo problemático passou a ser só o que a instituição marca como problemático (característica especial 19), com a Resolução CMN 4.966.
- O dado não permite separar o efeito da definição de uma piora real. A carteira inadimplida, cuja definição não mudou, também saltou no mesmo mês.

### Q39. As duas versões publicadas do SCR.data fecham no total para o mesmo mês? Se não, de quanto é a diferença e quando ela mudou de patamar?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `docs/analise-v1-v2.md`, `metricas.divergencia_com_outras_publicacoes`

**Como se responde:** Carteira ativa total da V1 e da V2, mês a mês, com a diferença e a mudança da diferença de um mês para o outro. O degrau é a maior mudança.

[`Q39.sql`](../evaluation/gabarito/Q39.sql)

<details><summary>31 linhas</summary>

| Mês | Carteira V1 | Carteira V2 | Diferenca | Diferenca | Mudanca da diferenca |
|---|---|---|---|---|---|
| jan/2024 | R$ 5.714,3 bi | R$ 5.961,1 bi | R$ 246,9 bi | 4,32% |  |
| fev/2024 | R$ 5.742,5 bi | R$ 5.977,7 bi | R$ 235,2 bi | 4,10% | -0,22 p.p. |
| mar/2024 | R$ 5.820,4 bi | R$ 6.063,2 bi | R$ 242,7 bi | 4,17% | 0,07 p.p. |
| abr/2024 | R$ 5.842,9 bi | R$ 6.091,0 bi | R$ 248,1 bi | 4,25% | 0,08 p.p. |
| mai/2024 | R$ 5.880,5 bi | R$ 6.132,3 bi | R$ 251,8 bi | 4,28% | 0,04 p.p. |
| jun/2024 | R$ 5.966,7 bi | R$ 6.236,4 bi | R$ 269,7 bi | 4,52% | 0,24 p.p. |
| jul/2024 | R$ 5.995,0 bi | R$ 6.270,6 bi | R$ 275,5 bi | 4,60% | 0,08 p.p. |
| ago/2024 | R$ 6.062,0 bi | R$ 6.340,1 bi | R$ 278,1 bi | 4,59% | -0,01 p.p. |
| set/2024 | R$ 6.141,9 bi | R$ 6.425,2 bi | R$ 283,3 bi | 4,61% | 0,02 p.p. |
| out/2024 | R$ 6.202,7 bi | R$ 6.491,9 bi | R$ 289,2 bi | 4,66% | 0,05 p.p. |
| nov/2024 | R$ 6.292,7 bi | R$ 6.599,4 bi | R$ 306,7 bi | 4,87% | 0,21 p.p. |
| dez/2024 | R$ 6.397,9 bi | R$ 6.688,6 bi | R$ 290,7 bi | 4,54% | -0,33 p.p. |
| jan/2025 | R$ 6.395,6 bi | R$ 6.648,4 bi | R$ 252,8 bi | 3,95% | -0,59 p.p. |
| fev/2025 | R$ 6.448,2 bi | R$ 6.719,7 bi | R$ 271,5 bi | 4,21% | 0,26 p.p. |
| mar/2025 | R$ 6.514,7 bi | R$ 6.781,1 bi | R$ 266,4 bi | 4,09% | -0,12 p.p. |
| abr/2025 | R$ 6.535,8 bi | R$ 6.815,4 bi | R$ 279,6 bi | 4,28% | 0,19 p.p. |
| mai/2025 | R$ 6.594,1 bi | R$ 6.871,3 bi | R$ 277,1 bi | 4,20% | -0,08 p.p. |
| jun/2025 | R$ 6.622,1 bi | R$ 6.923,4 bi | R$ 301,3 bi | 4,55% | 0,35 p.p. |
| jul/2025 | R$ 6.638,3 bi | R$ 6.941,0 bi | R$ 302,7 bi | 4,56% | 0,01 p.p. |
| ago/2025 | R$ 6.697,9 bi | R$ 7.008,6 bi | R$ 310,7 bi | 4,64% | 0,08 p.p. |
| set/2025 | R$ 6.759,9 bi | R$ 7.161,7 bi | R$ 401,8 bi | 5,94% | 1,30 p.p. |
| out/2025 | R$ 6.825,9 bi | R$ 7.221,4 bi | R$ 395,5 bi | 5,79% | -0,15 p.p. |
| nov/2025 | R$ 6.906,4 bi | R$ 7.302,5 bi | R$ 396,1 bi | 5,73% | -0,06 p.p. |
| dez/2025 | R$ 7.033,4 bi | R$ 7.444,3 bi | R$ 410,9 bi | 5,84% | 0,11 p.p. |
| jan/2026 | R$ 7.029,6 bi | R$ 7.433,7 bi | R$ 404,0 bi | 5,75% | -0,10 p.p. |
| fev/2026 | R$ 7.063,5 bi | R$ 7.445,7 bi | R$ 382,1 bi | 5,41% | -0,34 p.p. |
| mar/2026 | R$ 7.152,5 bi | R$ 7.540,2 bi | R$ 387,7 bi | 5,42% | 0,01 p.p. |
| abr/2026 | R$ 7.164,5 bi | R$ 7.555,2 bi | R$ 390,7 bi | 5,45% | 0,03 p.p. |
| mai/2026 | R$ 7.199,7 bi | R$ 7.594,3 bi | R$ 394,6 bi | 5,48% | 0,03 p.p. |
| jun/2026 | R$ 7.235,1 bi | R$ 7.637,1 bi | R$ 402,0 bi | 5,56% | 0,08 p.p. |
| jul/2026 | R$ 7.192,4 bi | R$ 7.590,7 bi | R$ 398,3 bi | 5,54% | -0,02 p.p. |

</details>

**Ressalva obrigatória:**

- A causa da diferença não está identificada. O degrau coincide no tempo com a IN BCB 659, de setembro de 2025, e isso é coincidência temporal, e não causa verificada.

### Q40. Ao reconstruir a série no padrão antigo de modalidades a partir do dado atual, que parcela da carteira não pode ser atribuída com certeza a uma modalidade antiga, e por quê?

**Tipo de acerto:** `valor_com_ressalva`

**Fonte da definição:** `docs/adr/0003-conformacao-de-taxonomia-entre-versoes.md`

**Como se responde:** Parcela da carteira em que a modalidade da V1 é ambígua ou inferida pelo projeto, no último mês e no recorte inteiro.

[`Q40.sql`](../evaluation/gabarito/Q40.sql)

| Ambígua no último mês | Inferida no último mês | Ambígua no recorte | Inferida no recorte | Linhas ambiguas no recorte |
|---|---|---|---|---|
| 2,46% | 0,02% | 2,71% | 0,02% | 295.134 |

**Ressalva obrigatória:**

- O porquê: uma regra da tabela oficial de equivalência depende do campo Natureza da operação, que o SCR.data não publica. Nessas linhas há duas modalidades candidatas, e nenhuma é escolhida em silêncio.

### Q41. Qual a rentabilidade média por modalidade de crédito?

**Tipo de acerto:** `abstencao`

**Fonte da definição:** `docs/recomendacao.md`

**A resposta certa é reconhecer o limite.** O SCR.data não traz taxa de juros, receita, custo de captação nem perda. Sem isso não existe rentabilidade para calcular, e qualquer número seria estimativa sem base no dado.

**O que faltaria:** Taxa de juros por modalidade, custo de captação e perda esperada, idealmente por instituição. As taxas de juros por modalidade existem em outra publicação do BCB, mas não fazem parte deste dado.
