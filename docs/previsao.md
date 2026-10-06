# Previsão da carteira PJ: o resultado do backtest

**Data:** 2026-10-06
**Decisões que motivaram:** [ADR 0023](adr/0023-previsao-da-carteira-escolhida-pelo-backtest.md), pela #27, e [ADR 0024](adr/0024-lightgbm-global-como-candidato-da-previsao.md), pela #98 (Q27 da especificação).
**Script:** `scripts/analises/previsao_da_carteira.py`, sobre o `mrt_carteira_mensal` e o `fct_selic` no Databricks, carteira ativa PJ de jan/2024 a jul/2026.
**Arquivos:** `dashboard/public/data/projecao_da_carteira.json`, `backtest_da_projecao.json` e `testes_da_projecao.json`, data-base 2026-07-31.

## Resumo

- **No Brasil, o modelo escolhido é o LightGBM,** um modelo de aprendizado de máquina treinado com as 351 séries de UF por modalidade ao mesmo tempo. Ele projeta R$ 2,92 trilhões em agosto e R$ 3,00 trilhões em setembro e outubro de 2026. O salto de setembro vem de uma quebra da série que o modelo leu como padrão do mês, e ainda depende de decisão (ver a projeção do país).
- **Nos meses de teste, o LightGBM errou menos que a tendência e que a regra simples a 1 e 2 meses no Brasil:** 0,4% e 0,5% de erro médio, contra 0,9% e 0,7% da tendência e 0,7% e 1,1% de repetir o último mês. A 3 meses, a tendência errou menos: 0,9% contra 1,1%.
- **A escolha no Brasil foi apertada.** Na janela de escolha, o LightGBM teve MASE médio de 1,15 e a tendência de 1,17. A diferença apareceu depois, na janela de avaliação, que nenhum dos dois usou para escolher.
- **Nas 41 séries, o LightGBM foi escolhido em 15.** A tendência ficou com 12, o Holt amortecido com 7, repetir o último mês com 6 e repetir o mês do ano anterior com 1. Na avaliação, o LightGBM errou menos que a tendência em 21 séries e menos que a regra simples em 24.
- **A faixa provável de 80% cobriu 74% dos casos da avaliação,** um pouco abaixo do nominal.
- **Cinco séries mudaram de nível dentro da janela de avaliação:** as modalidades 07, 10 e 11 e as UFs AC e TO. Nelas, o erro mede a mudança, e não o modelo.

## Como a previsão é feita

Cinco métodos disputam cada série num teste com meses que já aconteceram, como se o resultado ainda não fosse conhecido:
- **repetir o último mês** (o ingênuo), a régua de todos os outros;
- **a tendência** (a deriva), que prolonga a inclinação média da série;
- **repetir o mesmo mês do ano anterior** (o ingênuo sazonal);
- **a suavização exponencial com tendência amortecida** (Holt), que segue a tendência e a deixa perder força;
- **o LightGBM global,** que aprende com as 351 séries de UF por modalidade ao mesmo tempo, a partir das variações recentes de cada uma, do mês do ano, do tamanho, da UF, da modalidade e da Selic (ADR 0024).

Os testes andam mês a mês. Cada um usa só os meses até ele e prevê os três seguintes. Os 12 primeiros testes escolhem o método de cada série, e os 4 últimos, de fevereiro a julho de 2026, medem o erro que é publicado. Assim, o erro mostrado nunca é o do vencedor da própria disputa.

**Registro de ordem:** o LightGBM entrou depois de os resultados dos quatro primeiros candidatos terem sido vistos, por decisão do Yuri. A regra de escolha e as janelas não mudaram (ADR 0024).

## Como ler as medidas

- **MASE:** o erro médio dividido pelo passo típico da série no treino, que é o erro de um mês de repetir o último mês. Abaixo de 1, o erro ficou menor que esse passo. Ganhar da regra simples se lê comparando o MASE dos dois no mesmo horizonte.
- **Erro médio do escolhido (MAPE):** o erro em percentual da carteira, para ler em reais.
- **Faixa acertou:** a fração dos meses da avaliação em que o valor real caiu dentro da faixa provável de 80%.

A janela de avaliação tem quatro testes por horizonte. Diferenças pequenas ficam dentro do ruído de quatro casos.

## A projeção do país

| Mês | Realizado | Projeção | Faixa provável de 80% |
|---|---|---|---|
| mai/2026 | R$ 2,901 tri | | |
| jun/2026 | R$ 2,952 tri | | |
| jul/2026 | R$ 2,910 tri | | |
| ago/2026 | | R$ 2,920 tri | R$ 2,888 a 2,952 tri |
| set/2026 | | R$ 3,003 tri | R$ 2,920 a 3,087 tri |
| out/2026 | | R$ 3,000 tri | R$ 2,955 a 3,045 tri |

**O salto de setembro vem de uma quebra, e não do crédito.** A projeção sobe 2,8% de agosto para setembro e fica parada em outubro. Duas conferências explicam isso:
- **O modelo:** com o mês do ano trocado por agosto, a projeção de setembro cai de R$ 3,003 tri para R$ 2,954 tri, e a de outubro de R$ 3,000 tri para R$ 2,951 tri. O salto vem dessa variável.
- **O dado:** em setembro de 2024, a carteira PJ subiu 1,7% na V2 e 1,7% na V1. Em setembro de 2025, subiu 4,3% na V2 e só 1,2% na V1. Uns 3 pontos do salto de 2025 são a divergência entre as versões, a quebra de set/2025 já registrada em `ontology/dimensoes.yml` (#19). Na V2, o salto de 2025 se concentra em Financiamentos (R$ 54 bi) e Empréstimos (R$ 44 bi).

O LightGBM aprendeu como padrão de setembro um degrau que aconteceu uma vez. Nenhum mês de teste da avaliação foi um setembro, então o erro publicado não mede esse efeito. A decisão sobre como tratar isso é do Yuri.

**A faixa de outubro é mais estreita que a de setembro,** e o limite de baixo de outubro (R$ 2,955 tri) fica acima do limite de cima de agosto (R$ 2,952 tri). A faixa de cada mês sai dos erros do modelo nos 16 testes, e nesses testes ele errou menos a 3 meses que a 2. Com o salto de setembro, isso produz uma faixa que diz mais do que o dado sustenta.

## O confronto, série a série

MASE na janela de avaliação, na ordem 1 mês / 2 meses / 3 meses, do LightGBM, da tendência e de repetir o último mês. O erro médio e a faixa são os do método escolhido.

### País

| Recorte | Escolhido | LightGBM | Tendência | Ingênuo | Erro médio do escolhido | Faixa acertou |
|---|---|---|---|---|---|---|
| Brasil | LightGBM | 0,33 / 0,38 / 0,90 | 0,70 / 0,58 / 0,76 | 0,59 / 0,95 / 1,02 | 0,4% / 0,5% / 1,1% | 100% |

### Modalidades

| Recorte | Escolhido | LightGBM | Tendência | Ingênuo | Erro médio do escolhido | Faixa acertou |
|---|---|---|---|---|---|---|
| 01 Adiantamentos a depositantes | Holt amortecido | 0,37 / 0,52 / 0,92 | 0,55 / 0,84 / 1,17 | 0,44 / 0,62 / 0,83 | 2,0% / 2,6% / 4,2% | 100% |
| 02 Empréstimos | tendência | 0,82 / 1,25 / 1,53 | 0,89 / 0,80 / 1,43 | 0,60 / 1,00 / 1,05 | 1,1% / 1,0% / 1,8% | 75% |
| 03 Direitos creditórios descontados | Holt amortecido | 0,56 / 0,60 / 0,54 | 1,00 / 0,83 / 0,51 | 0,95 / 0,88 / 0,26 | 3,9% / 2,6% / 3,5% | 67% |
| 04 Financiamentos | LightGBM | 0,43 / 0,74 / 0,92 | 0,39 / 0,56 / 0,54 | 0,39 / 1,03 / 1,54 | 0,5% / 0,9% / 1,1% | 100% |
| 05 Financiamentos à exportação | ingênuo | 1,25 / 1,26 / 1,23 | 1,15 / 1,47 / 2,26 | 1,12 / 1,31 / 1,46 | 1,7% / 2,0% / 2,2% | 83% |
| 06 Financiamentos à importação | ingênuo | 0,85 / 0,99 / 3,06 | 0,91 / 1,38 / 3,32 | 0,87 / 0,82 / 2,43 | 2,6% / 2,5% / 8,1% | 83% |
| 07 Financiamentos com interveniência | Holt amortecido | 4,94 / 11,62 / 16,38 | 4,72 / 9,24 / 13,30 | 5,05 / 9,90 / 14,29 | 11,8% / 21,6% / 32,6% | 33% |
| 08 Financiamentos rurais | tendência | 0,80 / 1,32 / 1,10 | 0,69 / 1,24 / 1,44 | 1,39 / 2,64 / 3,30 | 1,0% / 1,9% / 2,1% | 100% |
| 09 Financiamentos imobiliários | tendência | 0,41 / 0,80 / 1,28 | 0,37 / 0,61 / 1,20 | 0,80 / 1,86 / 2,12 | 0,5% / 0,9% / 1,7% | 92% |
| 10 Financiamentos de títulos e valores mobiliários | LightGBM | 0,02 / 0,04 / 0,06 | 0,16 / 0,33 / 0,51 | 0,02 / 0,04 / 0,06 | 4,9% / 9,4% / 14,3% | 100% |
| 11 Financiamentos de infraestrutura e desenvolvimento | Holt amortecido | 1,98 / 4,29 / 5,82 | 2,28 / 4,18 / 5,85 | 1,69 / 2,69 / 3,45 | 1,7% / 2,6% / 3,3% | 0% |
| 12 Operações de arrendamento | tendência | 0,80 / 1,05 / 2,19 | 0,59 / 0,51 / 1,65 | 0,90 / 1,38 / 2,08 | 0,5% / 0,5% / 1,5% | 92% |
| 13 Outros créditos | ingênuo sazonal | 0,36 / 0,46 / 0,57 | 0,87 / 1,16 / 0,39 | 0,86 / 1,18 / 0,56 | 2,5% / 4,9% / 7,6% | 75% |

### UFs

| Recorte | Escolhido | LightGBM | Tendência | Ingênuo | Erro médio do escolhido | Faixa acertou |
|---|---|---|---|---|---|---|
| AC | tendência | 3,09 / 3,96 / 4,15 | 2,90 / 3,74 / 3,97 | 2,80 / 3,29 / 3,28 | 2,4% / 3,2% / 3,4% | 42% |
| AL | LightGBM | 1,87 / 2,37 / 1,25 | 1,68 / 2,21 / 1,78 | 1,50 / 2,29 / 2,59 | 3,3% / 4,2% / 2,2% | 50% |
| AM | LightGBM | 0,90 / 1,39 / 1,96 | 0,82 / 1,45 / 1,26 | 0,45 / 0,83 / 1,06 | 1,8% / 2,8% / 3,8% | 58% |
| AP | tendência | 1,61 / 2,01 / 2,61 | 1,39 / 2,11 / 2,70 | 1,26 / 2,06 / 2,97 | 3,6% / 5,5% / 7,0% | 75% |
| BA | Holt amortecido | 0,44 / 0,64 / 0,82 | 0,28 / 0,59 / 0,67 | 0,55 / 1,44 / 1,99 | 0,3% / 0,7% / 0,7% | 83% |
| CE | LightGBM | 0,93 / 1,77 / 1,65 | 0,81 / 1,63 / 1,88 | 1,00 / 2,23 / 3,37 | 1,3% / 2,4% / 2,1% | 75% |
| DF | ingênuo | 0,40 / 0,92 / 0,54 | 0,38 / 0,80 / 1,50 | 0,23 / 0,58 / 0,91 | 0,4% / 1,1% / 1,8% | 100% |
| ES | LightGBM | 0,64 / 0,79 / 1,22 | 0,65 / 1,12 / 1,65 | 0,56 / 0,67 / 0,46 | 1,1% / 1,4% / 2,2% | 83% |
| GO | tendência | 0,65 / 1,73 / 2,41 | 1,09 / 1,86 / 1,83 | 0,73 / 1,78 / 1,64 | 1,0% / 1,7% / 1,7% | 67% |
| MA | tendência | 0,60 / 1,32 / 2,86 | 0,30 / 1,01 / 2,20 | 0,56 / 0,95 / 1,39 | 0,2% / 0,8% / 1,7% | 75% |
| MG | Holt amortecido | 0,75 / 0,62 / 0,67 | 1,16 / 0,89 / 0,55 | 1,14 / 1,11 / 1,06 | 1,1% / 1,0% / 1,0% | 50% |
| MS | ingênuo | 1,00 / 1,73 / 1,02 | 1,27 / 1,69 / 0,98 | 1,19 / 1,90 / 1,89 | 1,3% / 2,0% / 2,0% | 67% |
| MT | ingênuo | 0,92 / 1,06 / 0,75 | 0,67 / 0,76 / 0,71 | 0,64 / 0,88 / 1,09 | 1,0% / 1,4% / 1,7% | 83% |
| PA | tendência | 0,78 / 0,74 / 0,57 | 0,85 / 0,98 / 0,64 | 0,92 / 2,09 / 2,78 | 0,9% / 1,0% / 0,7% | 92% |
| PB | LightGBM | 0,50 / 0,62 / 1,89 | 0,21 / 0,46 / 2,07 | 0,75 / 1,44 / 2,44 | 0,6% / 0,7% / 2,2% | 92% |
| PE | LightGBM | 1,75 / 2,36 / 1,72 | 1,47 / 2,12 / 1,52 | 1,41 / 1,99 / 1,67 | 2,2% / 3,0% / 2,2% | 50% |
| PI | tendência | 0,80 / 1,65 / 3,04 | 0,96 / 1,90 / 2,52 | 0,33 / 0,43 / 0,58 | 1,6% / 3,2% / 4,2% | 92% |
| PR | LightGBM | 1,04 / 1,57 / 1,51 | 0,68 / 1,20 / 1,44 | 1,12 / 2,21 / 2,51 | 1,0% / 1,4% / 1,4% | 67% |
| RJ | ingênuo | 0,55 / 0,74 / 0,99 | 0,91 / 1,20 / 1,34 | 0,94 / 1,07 / 1,04 | 1,2% / 1,4% / 1,4% | 92% |
| RN | LightGBM | 0,78 / 1,26 / 1,83 | 1,21 / 1,41 / 1,84 | 0,85 / 0,78 / 0,89 | 0,8% / 1,2% / 1,8% | 83% |
| RO | LightGBM | 0,92 / 1,82 / 3,59 | 0,85 / 1,62 / 3,22 | 0,56 / 0,58 / 1,15 | 0,9% / 1,8% / 3,5% | 58% |
| RR | LightGBM | 0,78 / 0,50 / 1,29 | 0,42 / 0,81 / 1,44 | 0,21 / 0,44 / 0,74 | 1,2% / 0,8% / 1,9% | 75% |
| RS | Holt amortecido | 0,54 / 0,32 / 1,05 | 0,61 / 0,83 / 0,83 | 0,60 / 1,01 / 1,62 | 1,8% / 1,6% / 1,4% | 33% |
| SC | LightGBM | 0,81 / 0,68 / 0,78 | 0,71 / 0,56 / 0,33 | 0,55 / 1,49 / 2,07 | 0,7% / 0,6% / 0,7% | 92% |
| SE | tendência | 0,94 / 2,27 / 3,48 | 1,20 / 2,35 / 3,69 | 2,04 / 4,17 / 5,12 | 1,2% / 2,2% / 3,6% | 50% |
| SP | tendência | 0,33 / 0,52 / 0,99 | 0,78 / 0,64 / 0,69 | 0,55 / 0,76 / 0,64 | 1,5% / 1,2% / 1,3% | 100% |
| TO | LightGBM | 2,58 / 3,41 / 5,07 | 2,53 / 3,59 / 4,83 | 2,53 / 4,02 / 6,14 | 2,9% / 3,7% / 5,9% | 33% |

## As séries em que o erro mede uma mudança, e não o modelo

A janela de avaliação prevê os meses de fevereiro a julho de 2026. Em cinco séries, o nível mudou de um jeito que nenhum candidato treinado antes podia ver. A causa de cada mudança não foi verificada.

- **07 Financiamentos com interveniência:** ficou entre R$ 3,3 e 3,5 bilhões até dez/2025 e caiu todo mês desde então, até R$ 1,81 bilhão em jul/2026, 49% abaixo. A janela de avaliação é exatamente a queda, e o erro médio chega a 33% a 3 meses.
- **10 Financiamentos de títulos e valores mobiliários:** caiu de R$ 1,5 a 4,0 bilhões em 2024 para R$ 0,09 bilhão em abr/2025 e fica entre R$ 0,09 e 0,16 bilhão desde então. Os saltos de 2024 inflam a escala do MASE, e o 0,02 não indica acerto. A leitura honesta é o erro médio, de 5% a 14%. A queda começa em jan/2025, o mês da mudança de critério do ativo problemático, que pela ontologia não muda a carteira ativa. A relação entre as duas não foi verificada.
- **11 Financiamentos de infraestrutura e desenvolvimento:** subiu de R$ 110 para 126 bilhões e caiu R$ 4 bilhões em mai/2026, 3,1%. O erro médio é pequeno, de 1,7% a 3,3%, mas a série é tão lisa que o passo típico do treino também é pequeno, e o MASE sobe. A faixa, estreita pelo mesmo motivo, não cobriu nenhum dos doze casos.
- **AC e TO:** os dois saltaram em abr/2026, o AC 4% e o TO 9%. O AC voltou ao nível anterior no mês seguinte, e o TO ficou acima dele.

Nenhuma dessas mudanças coincide com a publicação mais grossa (jul/2025) ou com a divergência entre V1 e V2 (set/2025).

## O que o resultado diz

- **O aprendizado de máquina acrescentou informação no Brasil a 1 e 2 meses,** onde a tendência perdia para a regra simples. A 3 meses, a tendência continua melhor.
- **O LightGBM não é melhor em toda parte.** Ele foi escolhido em 15 séries e, nelas, errou menos que a regra simples em 8 na avaliação. Em séries pequenas ou que mudaram de nível, nenhum método se sustenta.
- **A Selic pesou pouco.** Pela importância das variáveis no treino final, as variações recentes da carteira somam 53%, o tamanho da célula 13%, o mês do ano 10%, a modalidade 10%, a UF 8% e a Selic 6%. Com 31 meses de uma série nacional, a Selic funciona mais como marca do tempo do que como causa, e a tela não a apresenta como motivo da projeção.
- **As projeções das séries não somam entre si.** O Brasil usa o LightGBM, e cada UF e modalidade usa o próprio método escolhido.

## Limitações

- **Quatro testes por horizonte.** O erro publicado é uma estimativa ruidosa.
- **31 meses.** Cada mês do ano aparece duas ou três vezes, e um degrau único, como o de set/2025, pode ser lido como padrão do mês. A sazonalidade completa só pode ser testada acima de 36 meses (ADR 0023, decisão 2).
- **A escolha do Brasil foi por pouco** na janela de escolha. Com um mês a mais de dado, ela pode mudar.
- **O LightGBM entrou depois de o resultado dos outros ser visto.** A regra de escolha e as janelas não mudaram, e o registro fica no ADR 0024.
- **As mudanças de nível das cinco séries acima** não estão explicadas (#95).

## Como reproduzir

Na máquina local, com o perfil OAuth do Databricks:

```bash
uv run python -m scripts.analises.previsao_da_carteira
```

A execução é determinística: o LightGBM usa semente, uma thread e modo determinístico, e duas execuções seguidas gravam arquivos idênticos.

A Q27 do gabarito tem a deriva do país em SQL (`evaluation/gabarito/Q27.sql`, ADR 0023, decisão 6). Com o LightGBM escolhido no Brasil, o número da Q27 e o da Tela 3 deixam de ser o mesmo (ADR 0024, Consequências).

O autoteste do método roda sem Databricks e está no CI:

```bash
uv run python -m scripts.analises.previsao_da_carteira --autoteste
```
