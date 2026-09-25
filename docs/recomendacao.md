# Recomendação: onde crescer em crédito para empresas, e onde o risco pesa

**Data-base:** jul/2026. Gerado por `scripts/gerar_recomendacao.py` a partir do `mrt_decisao`. Nenhum número deste documento é digitado à mão: para atualizar, rode o script de novo.

A pergunta de negócio (ADR 0005): uma financeira quer crescer em crédito para pessoa jurídica. Em quais estados e modalidades vale aumentar a exposição, e onde o risco está piorando rápido demais para isso?

## O que este dado não permite afirmar

Esta lista vem antes da recomendação de propósito. Uma recomendação sem ela é palpite com gráfico.

- **Rentabilidade, spread e custo de captação.** O SCR.data não tem taxa de juros nem receita. "Entrar" quer dizer que há espaço de carteira e que o risco não piora mais que no país, e não que a operação dá lucro.
- **Instituição específica.** O dado é agregado por segmento, e não diz como um banco ou uma financeira em particular se comporta.
- **Risco de um cliente ou de uma safra.** Não há dado por operação nem por data de contratação.
- **Local da operação.** A UF é a do domicílio da pessoa ou da sede da empresa, e não onde o crédito foi usado.
- **Número exato de empresas por mês.** O denominador é reconstruído de um único retrato do cadastro da Receita (ADR 0009). O erro medido chegou a 2,30% por UF no retrato mais antigo (jun/2024).
- **Número de operações em parte do dado.** A contagem aparece suprimida em 26,7% das linhas do SCR, e por isso a matriz não usa contagem de operações.
- **O custo de errar é ordem de grandeza, e não perda.** O custo do risco mede o aumento da carteira inadimplida atribuível à piora da taxa. Sem taxa de recuperação, não dá para dizer quanto disso vira prejuízo.

## A regra

Cada célula é uma UF e uma modalidade de crédito, só para pessoa jurídica, em jul/2026, comparada com jan/2026. A regra completa, com as alternativas descartadas, está no [ADR 0014](adr/0014-matriz-de-decisao-espaco-contra-risco.md).

- **Espaço:** a carteira PJ da modalidade na UF, dividida pelo número de empresas ativas de natureza empresarial, sem MEI, da UF. Abaixo da mediana das UFs na mesma modalidade, o espaço é alto.
- **Risco:** a variação da taxa de inadimplência em 6 meses. Se sobe mais que a da mesma modalidade no país inteiro, o risco está piorando.
- **Materialidade:** só entram células com carteira PJ de pelo menos R$ 1,0 bi, em modalidades com pelo menos 3 UFs acima desse corte.

| | Risco estável ou melhorando | Risco piorando |
|---|---|---|
| **Espaço alto** | **Entrar** | **Observar:** há espaço, mas o risco pede espera |
| **Espaço baixo** | **Manter** | **Não entrar** |

**O custo de errar vai nas duas direções.** Deixar de entrar onde havia espaço custa a carteira que faltaria para a UF chegar à mediana. Entrar onde o risco piora custa o aumento da carteira inadimplida atribuível à piora.

**O alerta antecipado** marca a célula em que a distância entre ativo problemático e carteira inadimplida abriu mais que a do país. É a piora que o atraso ainda não mostra, e não muda o quadrante.

## Resumo

| Quadrante | Células | Carteira PJ (R$ bi) | Custo de não entrar (R$ bi) | Custo do risco (R$ bi) | Com alerta antecipado |
|---|---|---|---|---|---|
| Entrar | 35 | 485,5 | 141,1 | 0,8 | 10 |
| Observar | 35 | 369,2 | 106,3 | 2,3 | 14 |
| Não entrar | 30 | 574,9 |  | 4,9 | 10 |
| Manter | 47 | 1.436,2 |  | 3,5 | 10 |
| Não avaliada | 162 | 44,2 |  |  |  |

## Onde entrar (35 células)

Espaço acima da mediana e risco que não piora mais que o país. Ordenado pelo custo de não entrar: o topo da lista é onde deixar de crescer custa mais.

| UF | Modalidade | Carteira PJ (R$ bi) | Carteira por empresa (R$ mil) | Índice de espaço | Taxa de inadimplência | Variação da taxa (p.p.) | Variação no país (p.p.) | Custo de não entrar (R$ bi) | Custo do risco (R$ mi) | Alerta |
|---|---|---|---|---|---|---|---|---|---|---|
| SP | Financiamentos | 219,4 | 61,6 | 0,87 | 0,93% | +0,15 | +0,19 | 34,1 | 334,4 |  |
| SP | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 35,4 | 9,9 | 0,55 | 0,38% | +0,09 | +0,19 | 28,9 | 31,4 | sim |
| SP | Financiamentos de infraestrutura e desenvolvimento | 25,5 | 7,1 | 0,62 | 0,00% | 0,00 | +0,02 | 15,6 | 0,0 | sim |
| RJ | Empréstimos | 52,5 | 64,9 | 0,86 | 7,60% | +0,40 | +0,70 | 8,3 | 209,8 |  |
| MG | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 14,0 | 12,5 | 0,70 | 0,35% | -0,02 | +0,19 | 6,1 | 0,0 | sim |
| PB | Financiamentos | 4,4 | 34,3 | 0,48 | 1,28% | +0,14 | +0,19 | 4,7 | 6,3 | sim |
| PE | Financiamentos à exportação | 1,8 | 6,1 | 0,27 | 0,46% | -0,34 | +0,01 | 4,7 | 0,0 |  |
| MG | Financiamentos de infraestrutura e desenvolvimento | 8,8 | 7,8 | 0,68 | 0,00% | 0,00 | +0,02 | 4,1 | 0,2 |  |
| CE | Empréstimos | 19,2 | 62,5 | 0,83 | 7,84% | +0,19 | +0,70 | 3,9 | 35,6 | sim |
| BA | Financiamentos à exportação | 7,5 | 15,4 | 0,68 | 1,01% | -0,30 | +0,01 | 3,5 | 0,0 | sim |
| SC | Financiamentos de infraestrutura e desenvolvimento | 4,3 | 6,5 | 0,57 | 0,00% | -0,01 | +0,02 | 3,3 | 0,0 |  |
| RS | Financiamentos de infraestrutura e desenvolvimento | 5,9 | 8,3 | 0,72 | 0,01% | +0,01 | +0,02 | 2,3 | 0,8 |  |
| GO | Outros créditos | 3,8 | 8,9 | 0,67 | 2,89% | +0,20 | +0,27 | 1,9 | 7,6 |  |
| PR | Financiamentos de infraestrutura e desenvolvimento | 8,4 | 9,5 | 0,82 | 0,02% | +0,01 | +0,02 | 1,8 | 1,2 |  |
| RN | Empréstimos | 7,1 | 60,0 | 0,80 | 9,06% | +0,59 | +0,70 | 1,8 | 41,5 | sim |
| BA | Financiamentos imobiliários | 1,3 | 2,7 | 0,44 | 0,04% | -0,69 | +0,29 | 1,7 | 0,0 |  |
| AM | Financiamentos à exportação | 1,1 | 8,7 | 0,39 | 0,00% | 0,00 | +0,01 | 1,7 | 0,0 |  |
| MG | Financiamentos imobiliários | 5,2 | 4,7 | 0,76 | 0,71% | -0,53 | +0,29 | 1,7 | 0,0 |  |
| PE | Empréstimos | 20,0 | 69,6 | 0,93 | 7,43% | +0,56 | +0,70 | 1,6 | 110,9 |  |
| PR | Financiamentos à importação | 1,5 | 1,7 | 0,51 | 0,00% | 0,00 | 0,00 | 1,5 | 0,0 |  |
| SE | Empréstimos | 3,8 | 57,4 | 0,76 | 8,15% | -1,47 | +0,70 | 1,2 | 0,0 | sim |
| PA | Outros créditos | 2,2 | 9,2 | 0,69 | 1,47% | -0,09 | +0,27 | 1,0 | 0,0 |  |
| PI | Financiamentos à exportação | 1,4 | 13,3 | 0,59 | 0,00% | 0,00 | +0,01 | 1,0 | 0,0 |  |
| ES | Financiamentos de infraestrutura e desenvolvimento | 1,6 | 7,2 | 0,63 | 0,00% | 0,00 | +0,02 | 0,9 | 0,0 |  |
| MA | Outros créditos | 1,4 | 8,2 | 0,61 | 2,50% | +0,15 | +0,27 | 0,9 | 2,2 |  |
| AL | Financiamentos à exportação | 1,2 | 14,1 | 0,63 | 0,00% | 0,00 | +0,01 | 0,7 | 0,0 |  |
| PB | Outros créditos | 1,2 | 9,5 | 0,71 | 38,29% | -6,77 | +0,27 | 0,5 | 0,0 |  |
| MS | Outros créditos | 1,6 | 10,5 | 0,78 | 2,24% | -0,69 | +0,27 | 0,5 | 0,0 |  |
| CE | Financiamentos de infraestrutura e desenvolvimento | 3,2 | 10,3 | 0,90 | 0,00% | 0,00 | +0,02 | 0,4 | 0,0 | sim |
| CE | Outros créditos | 3,8 | 12,5 | 0,93 | 7,53% | +0,22 | +0,27 | 0,3 | 8,4 |  |
| PI | Financiamentos de infraestrutura e desenvolvimento | 1,0 | 9,6 | 0,83 | 0,00% | 0,00 | +0,02 | 0,2 | 0,0 |  |
| AM | Outros créditos | 1,4 | 11,9 | 0,89 | 0,38% | -2,97 | +0,27 | 0,2 | 0,0 |  |
| MS | Empréstimos | 11,5 | 74,2 | 0,99 | 10,05% | -0,28 | +0,70 | 0,1 | 0,0 | sim |
| RR | Empréstimos | 1,4 | 71,2 | 0,95 | 8,91% | +0,46 | +0,70 | 0,1 | 6,5 |  |
| MS | Financiamentos de infraestrutura e desenvolvimento | 1,7 | 11,1 | 0,96 | 0,00% | 0,00 | +0,02 | 0,1 | 0,0 |  |

## Onde observar (35 células)

Há espaço, mas a inadimplência sobe mais que no país. Ordenado pelo custo do risco: o topo é onde entrar agora pesaria mais.

| UF | Modalidade | Carteira PJ (R$ bi) | Carteira por empresa (R$ mil) | Índice de espaço | Taxa de inadimplência | Variação da taxa (p.p.) | Variação no país (p.p.) | Custo de não entrar (R$ bi) | Custo do risco (R$ mi) | Alerta |
|---|---|---|---|---|---|---|---|---|---|---|
| PR | Financiamentos | 44,8 | 50,6 | 0,71 | 3,11% | +0,65 | +0,19 | 18,2 | 289,4 | sim |
| BA | Empréstimos | 32,6 | 66,4 | 0,88 | 8,09% | +0,78 | +0,70 | 4,3 | 255,6 |  |
| MA | Empréstimos | 10,4 | 59,2 | 0,79 | 12,47% | +2,28 | +0,70 | 2,8 | 236,7 | sim |
| RS | Financiamentos | 50,4 | 70,7 | 0,99 | 2,27% | +0,38 | +0,19 | 0,3 | 192,9 |  |
| PI | Empréstimos | 6,3 | 58,3 | 0,78 | 9,04% | +2,52 | +0,70 | 1,8 | 157,5 |  |
| GO | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 7,2 | 17,0 | 0,94 | 3,60% | +2,00 | +0,19 | 0,4 | 144,1 |  |
| MG | Financiamentos | 57,4 | 51,3 | 0,72 | 2,09% | +0,23 | +0,19 | 22,1 | 131,7 | sim |
| GO | Financiamentos | 25,8 | 61,2 | 0,86 | 3,53% | +0,49 | +0,19 | 4,2 | 125,4 | sim |
| PR | Financiamentos à exportação | 17,1 | 19,3 | 0,86 | 1,39% | +0,58 | +0,01 | 2,9 | 99,8 |  |
| TO | Empréstimos | 5,0 | 70,6 | 0,94 | 10,19% | +1,50 | +0,70 | 0,3 | 75,0 |  |
| RS | Outros créditos | 8,2 | 11,5 | 0,86 | 2,50% | +0,84 | +0,27 | 1,3 | 68,7 |  |
| PB | Empréstimos | 6,7 | 52,7 | 0,70 | 9,45% | +0,85 | +0,70 | 2,9 | 57,4 | sim |
| PE | Financiamentos | 13,7 | 47,8 | 0,67 | 1,38% | +0,35 | +0,19 | 6,7 | 48,2 | sim |
| MG | Direitos creditórios descontados | 3,6 | 3,2 | 0,97 | 5,26% | +1,20 | +0,48 | 0,1 | 43,1 |  |
| SE | Financiamentos | 2,6 | 39,1 | 0,55 | 3,30% | +1,46 | +0,19 | 2,1 | 38,0 | sim |
| RS | Direitos creditórios descontados | 2,2 | 3,1 | 0,94 | 5,73% | +1,67 | +0,48 | 0,1 | 37,2 |  |
| PE | Financiamentos imobiliários | 1,1 | 4,0 | 0,64 | 5,49% | +3,21 | +0,29 | 0,6 | 36,6 |  |
| MA | Financiamentos | 10,4 | 59,2 | 0,83 | 3,06% | +0,33 | +0,19 | 2,1 | 34,5 | sim |
| RS | Financiamentos imobiliários | 3,6 | 5,0 | 0,81 | 2,64% | +0,85 | +0,29 | 0,8 | 30,6 |  |
| ES | Financiamentos | 13,6 | 62,2 | 0,87 | 1,81% | +0,22 | +0,19 | 1,9 | 29,9 | sim |
| AC | Empréstimos | 1,7 | 71,9 | 0,96 | 12,29% | +1,54 | +0,70 | 0,1 | 25,9 |  |
| PR | Operações de arrendamento | 1,6 | 1,8 | 0,97 | 2,33% | +1,60 | -0,69 | 0,0 | 25,8 | sim |
| AL | Financiamentos | 5,1 | 59,5 | 0,84 | 1,73% | +0,50 | +0,19 | 1,0 | 25,5 |  |
| GO | Financiamentos à exportação | 6,4 | 15,2 | 0,68 | 0,70% | +0,36 | +0,01 | 3,1 | 23,3 |  |
| SC | Outros créditos | 7,4 | 11,3 | 0,84 | 2,69% | +0,28 | +0,27 | 1,4 | 20,9 |  |
| RN | Financiamentos | 6,8 | 57,9 | 0,81 | 1,32% | +0,28 | +0,19 | 1,6 | 19,1 | sim |
| PA | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 1,2 | 5,0 | 0,28 | 6,04% | +1,09 | +0,19 | 3,1 | 13,0 |  |
| RO | Financiamentos | 3,8 | 54,5 | 0,77 | 4,23% | +0,22 | +0,19 | 1,2 | 8,5 | sim |
| RJ | Direitos creditórios descontados | 1,3 | 1,7 | 0,50 | 4,00% | +0,55 | +0,48 | 1,4 | 7,3 | sim |
| ES | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 1,5 | 6,8 | 0,37 | 0,61% | +0,47 | +0,19 | 2,5 | 6,9 |  |
| RJ | Operações de arrendamento | 1,3 | 1,6 | 0,87 | 1,90% | +0,34 | -0,69 | 0,2 | 4,5 |  |
| MT | Financiamentos imobiliários | 1,1 | 4,3 | 0,70 | 1,35% | +0,31 | +0,29 | 0,5 | 3,3 |  |
| CE | Financiamentos à exportação | 1,2 | 3,9 | 0,17 | 0,27% | +0,27 | +0,01 | 5,7 | 3,2 | sim |
| MT | Financiamentos de infraestrutura e desenvolvimento | 1,3 | 5,2 | 0,45 | 0,15% | +0,15 | +0,02 | 1,6 | 2,0 |  |
| SP | Financiamentos à importação | 4,8 | 1,3 | 0,41 | 0,02% | +0,02 | 0,00 | 7,0 | 0,9 |  |

## Onde não entrar (30 células)

Carteira por empresa já acima da mediana e risco piorando mais que o país. Ordenado pelo custo do risco.

| UF | Modalidade | Carteira PJ (R$ bi) | Carteira por empresa (R$ mil) | Índice de espaço | Taxa de inadimplência | Variação da taxa (p.p.) | Variação no país (p.p.) | Custo de não entrar (R$ bi) | Custo do risco (R$ mi) | Alerta |
|---|---|---|---|---|---|---|---|---|---|---|
| RS | Empréstimos | 76,8 | 107,7 | 1,43 | 6,36% | +1,26 | +0,70 |  | 968,6 |  |
| PR | Empréstimos | 81,0 | 91,5 | 1,22 | 6,60% | +0,83 | +0,70 |  | 668,7 | sim |
| MG | Empréstimos | 84,0 | 75,1 | 1,00 | 6,37% | +0,74 | +0,70 |  | 625,5 |  |
| RJ | Outros créditos | 19,6 | 24,2 | 1,81 | 5,33% | +2,96 | +0,27 |  | 580,5 |  |
| GO | Empréstimos | 31,9 | 75,5 | 1,01 | 8,45% | +0,98 | +0,70 |  | 312,6 |  |
| SC | Financiamentos | 67,1 | 102,6 | 1,44 | 1,77% | +0,42 | +0,19 |  | 284,3 | sim |
| ES | Empréstimos | 23,8 | 109,3 | 1,45 | 5,71% | +0,92 | +0,70 |  | 218,6 | sim |
| MT | Empréstimos | 21,7 | 88,0 | 1,17 | 9,11% | +0,87 | +0,70 |  | 188,8 |  |
| RS | Financiamentos à exportação | 22,0 | 30,8 | 1,37 | 1,30% | +0,79 | +0,01 |  | 172,9 |  |
| AM | Empréstimos | 11,4 | 94,1 | 1,25 | 9,30% | +1,40 | +0,70 |  | 160,3 | sim |
| AM | Financiamentos | 16,8 | 138,0 | 1,94 | 1,91% | +0,71 | +0,19 |  | 118,5 | sim |
| PA | Financiamentos | 17,7 | 73,6 | 1,04 | 2,94% | +0,53 | +0,19 |  | 93,8 | sim |
| RO | Empréstimos | 5,6 | 80,5 | 1,07 | 9,13% | +1,33 | +0,70 |  | 74,4 | sim |
| RS | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 18,8 | 26,4 | 1,46 | 1,49% | +0,38 | +0,19 |  | 71,2 |  |
| PR | Financiamentos imobiliários | 6,5 | 7,4 | 1,20 | 2,01% | +0,83 | +0,29 |  | 54,4 |  |
| BA | Outros créditos | 7,0 | 14,3 | 1,07 | 1,11% | +0,60 | +0,27 |  | 42,2 |  |
| MS | Financiamentos à exportação | 6,4 | 41,5 | 1,85 | 1,23% | +0,62 | +0,01 |  | 39,6 |  |
| DF | Outros créditos | 4,5 | 20,3 | 1,52 | 1,05% | +0,80 | +0,27 |  | 36,1 |  |
| PR | Direitos creditórios descontados | 3,5 | 3,9 | 1,19 | 4,37% | +0,83 | +0,48 |  | 28,9 |  |
| GO | Financiamentos imobiliários | 4,6 | 10,8 | 1,76 | 0,90% | +0,56 | +0,29 |  | 25,6 |  |
| BA | Financiamentos de infraestrutura e desenvolvimento | 6,8 | 13,8 | 1,20 | 0,31% | +0,31 | +0,02 |  | 20,9 |  |
| AP | Financiamentos | 3,2 | 136,2 | 1,92 | 1,90% | +0,51 | +0,19 |  | 16,4 |  |
| MS | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 4,6 | 29,7 | 1,64 | 0,90% | +0,30 | +0,19 |  | 13,8 |  |
| AP | Empréstimos | 1,9 | 78,9 | 1,05 | 10,89% | +0,72 | +0,70 |  | 13,5 | sim |
| GO | Direitos creditórios descontados | 1,4 | 3,3 | 1,00 | 5,21% | +0,83 | +0,48 |  | 11,6 | sim |
| RR | Financiamentos | 1,6 | 79,4 | 1,12 | 1,63% | +0,42 | +0,19 |  | 6,5 | sim |
| PA | Financiamentos à exportação | 5,5 | 22,9 | 1,02 | 0,55% | +0,07 | +0,01 |  | 4,1 |  |
| SC | Financiamentos à exportação | 14,7 | 22,5 | 1,00 | 0,40% | +0,01 | +0,01 |  | 1,8 |  |
| MG | Operações de arrendamento | 3,2 | 2,9 | 1,55 | 0,24% | -0,06 | -0,69 |  | 0,0 |  |
| SC | Operações de arrendamento | 1,2 | 1,9 | 1,00 | 0,04% | -0,01 | -0,69 |  | 0,0 |  |

## Onde manter (47 células)

Carteira por empresa já acima da mediana e risco que não piora mais que o país. Ordenado pela carteira.

| UF | Modalidade | Carteira PJ (R$ bi) | Carteira por empresa (R$ mil) | Índice de espaço | Taxa de inadimplência | Variação da taxa (p.p.) | Variação no país (p.p.) | Custo de não entrar (R$ bi) | Custo do risco (R$ mi) | Alerta |
|---|---|---|---|---|---|---|---|---|---|---|
| SP | Empréstimos | 459,0 | 128,8 | 1,71 | 3,88% | +0,56 | +0,70 |  | 2.582,2 |  |
| RJ | Financiamentos | 137,0 | 169,2 | 2,38 | 0,27% | +0,03 | +0,19 |  | 34,7 |  |
| SP | Financiamentos à exportação | 106,4 | 29,9 | 1,33 | 0,27% | -0,02 | +0,01 |  | 0,0 | sim |
| SP | Outros créditos | 106,3 | 29,8 | 2,23 | 1,55% | +0,14 | +0,27 |  | 148,1 | sim |
| SC | Empréstimos | 65,6 | 100,3 | 1,33 | 5,52% | +0,54 | +0,70 |  | 354,5 | sim |
| RJ | Financiamentos à exportação | 44,7 | 55,2 | 2,45 | 0,00% | -0,28 | +0,01 |  | 0,0 | sim |
| SP | Financiamentos imobiliários | 43,0 | 12,1 | 1,96 | 0,96% | +0,05 | +0,29 |  | 20,6 | sim |
| BA | Financiamentos | 34,9 | 71,1 | 1,00 | 1,49% | +0,11 | +0,19 |  | 39,8 |  |
| PR | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 34,6 | 39,0 | 2,17 | 0,18% | +0,06 | +0,19 |  | 19,8 |  |
| CE | Financiamentos | 28,3 | 92,2 | 1,30 | 0,79% | -0,47 | +0,19 |  | 0,0 | sim |
| MG | Financiamentos à exportação | 26,4 | 23,6 | 1,05 | 0,93% | -0,30 | +0,01 |  | 0,0 |  |
| DF | Empréstimos | 26,0 | 117,6 | 1,57 | 4,48% | -0,06 | +0,70 |  | 0,0 |  |
| MT | Financiamentos | 24,7 | 100,2 | 1,41 | 4,15% | -0,07 | +0,19 |  | 0,0 |  |
| MG | Outros créditos | 22,3 | 20,0 | 1,49 | 2,07% | -0,26 | +0,27 |  | 0,0 |  |
| DF | Financiamentos | 22,3 | 101,1 | 1,42 | 0,41% | -0,10 | +0,19 |  | 0,0 |  |
| PA | Empréstimos | 22,0 | 91,3 | 1,22 | 7,44% | +0,61 | +0,70 |  | 134,6 | sim |
| PI | Financiamentos | 18,0 | 167,5 | 2,35 | 0,74% | +0,05 | +0,19 |  | 9,2 |  |
| MT | Financiamentos à exportação | 15,9 | 64,4 | 2,86 | 0,53% | -0,34 | +0,01 |  | 0,0 |  |
| RJ | Financiamentos de infraestrutura e desenvolvimento | 14,0 | 17,3 | 1,50 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| MT | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 14,0 | 56,7 | 3,14 | 1,08% | +0,16 | +0,19 |  | 22,2 | sim |
| SP | Direitos creditórios descontados | 13,6 | 3,8 | 1,15 | 3,96% | +0,16 | +0,48 |  | 21,9 | sim |
| DF | Financiamentos de infraestrutura e desenvolvimento | 12,9 | 58,5 | 5,07 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| PR | Outros créditos | 12,8 | 14,4 | 1,08 | 1,84% | -0,18 | +0,27 |  | 0,0 |  |
| SP | Operações de arrendamento | 12,5 | 3,5 | 1,87 | 0,72% | -1,75 | -0,69 |  | 0,0 |  |
| MS | Financiamentos | 12,2 | 79,1 | 1,11 | 4,21% | -0,29 | +0,19 |  | 0,0 |  |
| BA | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 12,1 | 24,6 | 1,37 | 0,22% | +0,05 | +0,19 |  | 6,4 |  |
| SC | Financiamentos rurais (ex-financiamentos rurais e agroindustriais) | 11,8 | 18,0 | 1,00 | 0,34% | +0,15 | +0,19 |  | 17,4 |  |
| RJ | Financiamentos imobiliários | 8,3 | 10,2 | 1,66 | 1,43% | +0,27 | +0,29 |  | 22,3 | sim |
| AL | Empréstimos | 7,9 | 91,3 | 1,21 | 6,11% | +0,42 | +0,70 |  | 33,2 |  |
| PE | Financiamentos de infraestrutura e desenvolvimento | 7,7 | 27,0 | 2,34 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| TO | Financiamentos | 7,2 | 101,3 | 1,42 | 2,52% | -0,93 | +0,19 |  | 0,0 |  |
| ES | Financiamentos à exportação | 6,1 | 27,7 | 1,23 | 0,11% | -0,96 | +0,01 |  | 0,0 |  |
| GO | Financiamentos de infraestrutura e desenvolvimento | 5,4 | 12,9 | 1,12 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| SC | Financiamentos imobiliários | 4,8 | 7,3 | 1,19 | 0,61% | -0,29 | +0,29 |  | 0,0 |  |
| PE | Outros créditos | 4,8 | 16,6 | 1,24 | 0,51% | +0,18 | +0,27 |  | 8,4 |  |
| SC | Direitos creditórios descontados | 4,8 | 7,3 | 2,19 | 3,08% | -0,47 | +0,48 |  | 0,0 |  |
| PA | Financiamentos de infraestrutura e desenvolvimento | 4,6 | 19,2 | 1,67 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| MT | Outros créditos | 4,0 | 16,2 | 1,21 | 5,08% | -1,45 | +0,27 |  | 0,0 |  |
| ES | Outros créditos | 3,4 | 15,6 | 1,17 | 2,19% | -0,23 | +0,27 |  | 0,0 |  |
| SC | Financiamentos à importação | 3,1 | 4,8 | 1,44 | 0,00% | 0,00 | 0,00 |  | 0,0 |  |
| RN | Financiamentos de infraestrutura e desenvolvimento | 2,8 | 23,8 | 2,06 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| AC | Financiamentos | 2,2 | 93,7 | 1,32 | 1,14% | -0,28 | +0,19 |  | 0,0 |  |
| ES | Financiamentos à importação | 1,6 | 7,3 | 2,19 | 0,00% | 0,00 | 0,00 |  | 0,0 |  |
| GO | Financiamentos à importação | 1,4 | 3,3 | 1,00 | 0,00% | 0,00 | 0,00 |  | 0,0 |  |
| TO | Financiamentos de infraestrutura e desenvolvimento | 1,1 | 15,8 | 1,37 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| AL | Financiamentos de infraestrutura e desenvolvimento | 1,0 | 11,9 | 1,04 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |
| SE | Financiamentos de infraestrutura e desenvolvimento | 1,0 | 15,2 | 1,32 | 0,00% | 0,00 | +0,02 |  | 0,0 |  |

## Fora da matriz

Células que ficam de fora, com o motivo. Continuam no `mrt_decisao`, marcadas como não avaliadas.

| Motivo | Células | Carteira PJ (R$ bi) |
|---|---|---|
| Carteira abaixo do corte de materialidade | 161 | 42,7 |
| Modalidade com poucas UFs acima do corte | 1 | 1,6 |
