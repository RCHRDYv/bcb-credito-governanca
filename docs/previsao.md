# Previsão da carteira PJ: cartão do modelo

**Data:** 2026-10-06 · **Data-base:** 2026-07-31
**Decisões:** [ADR 0023](adr/0023-previsao-da-carteira-escolhida-pelo-backtest.md) (#27) e [ADR 0024](adr/0024-lightgbm-global-como-candidato-da-previsao.md) (#98).
**Código:** `scripts/analises/previsao_da_carteira.py`, sobre o `mrt_carteira_mensal` e o `fct_selic` no Databricks.
**Arquivos:** `dashboard/public/data/projecao_da_carteira.json`, `backtest_da_projecao.json` e `testes_da_projecao.json`.

## Uso

- **Para que serve:** projetar a carteira ativa PJ três meses à frente, por país, modalidade e UF, com uma faixa provável de 80%, para a Tela 3 do dashboard e a Q27 do experimento. A projeção de cada UF e modalidade alimenta a camada de decisão (#55), e o monitoramento mês a mês ajuda a detectar mudança de patamar numa série (#95).
- **Para que não serve:** não é meta nem expectativa do Banco Central, não prevê choque, mudança de norma ou de publicação, e não diz por que a carteira cresce. As projeções das séries não somam entre si: o Brasil não é a soma das UFs.

## Resumo

- **No Brasil, o campeão é a tendência,** com a quebra de set/2025 descontada. Ela projeta R$ 2,926 tri em agosto e R$ 2,957 tri em outubro de 2026.
- **Nove desafiantes disputaram cada série,** entre eles o LightGBM global, o Prophet, o ARIMA, o SARIMAX, o Theta e a combinação. Um desafiante só tira a tendência se errar menos com significância, no teste de Diebold-Mariano com a correção de Holm.
- **No Brasil, nenhum desafiante passou.** O mais perto foi a combinação, que errou menos nos testes (MASE de 0,89 contra 1,06), com p = 0,031. Com nove desafiantes, o primeiro precisaria de p ≤ 0,011.
- **Nas 41 séries, a tendência ficou em 30.** A combinação venceu em 6, o Theta em 3 e repetir o último mês em 2. O LightGBM, o Prophet, o ARIMA e o SARIMAX não venceram nenhuma sozinhos.
- **A faixa provável dos campeões cobriu 81% dos casos recentes,** perto dos 80% nominais.
- **O erro honesto do procedimento,** com a escolha refeita em cada teste recente só com os testes anteriores, tem mediana de 1,92% nas 41 séries.

## Dados

- **Série:** carteira ativa PJ do SCR.data V2, mensal, de jan/2024 a jul/2026, 31 meses. O Brasil, as 13 modalidades e as 27 UFs, somadas das 351 células de UF por modalidade.
- **Selic:** a meta do Copom no fim de cada mês ([ADR 0010](adr/0010-selic-e-a-meta-do-copom-vigente-no-fim-do-mes.md)), usada pelo LightGBM e pelo SARIMAX.
- **Quebra de set/2025:** a divergência entre V1 e V2 (`ontology/dimensoes.yml`). A carteira PJ subiu 4,3% na V2 e 1,2% na V1 naquele mês. Os modelos de uma série descontam o degrau, medido em cada teste só com os meses conhecidos; o LightGBM não treina com exemplo que cruza a quebra (ADR 0024, decisão 7).

## Método

**Os testes.** São 16 testes com meses que já aconteceram. Em cada um, os modelos só conhecem a carteira até um mês e preveem os três seguintes. Os 4 últimos, com previsões de fevereiro a julho de 2026, são os testes recentes que a tela mostra.

**Os candidatos,** do mais simples ao menos simples:
1. **repetir o último mês** (o ingênuo);
2. **a tendência** (a deriva): o último mês mais o crescimento médio mensal da série;
3. **repetir o mês do ano anterior** (o ingênuo sazonal);
4. **Theta:** o vencedor da competição M3;
5. **Holt amortecido:** a suavização exponencial com tendência que perde força;
6. **ARIMA:** a ordem de menor AICc numa grade pequena;
7. **SARIMAX:** o ARIMA com a Selic de três meses antes;
8. **Prophet;**
9. **a combinação:** a média da tendência, do Holt e do LightGBM;
10. **o LightGBM global:** um modelo de aprendizado de máquina treinado com as 351 células ao mesmo tempo, com as variações recentes, o mês do ano, o tamanho, a UF, a modalidade e a Selic.

**A escolha: campeão e desafiante.**
- **O campeão:** a tendência.
- **A comparação:** em cada série, cada desafiante é comparado com ela em todos os 16 testes, pelo teste de Diebold-Mariano. A variância é corrigida pela sobreposição dos horizontes e pela amostra pequena.
- **A correção de Holm:** com nove desafiantes, o teste corrige as comparações múltiplas.
- **Quem assume:** só um desafiante que passe, e, entre os que passam, o de menor erro. Assim a série não troca de modelo por ruído a cada mês.

## A projeção do país

| Mês | Projeção | Faixa provável de 80% |
|---|---|---|
| ago/2026 | R$ 2,926 tri | R$ 2,878 a 2,973 tri |
| set/2026 | R$ 2,941 tri | R$ 2,873 a 3,010 tri |
| out/2026 | R$ 2,957 tri | R$ 2,872 a 3,042 tri |

## O Brasil, candidato a candidato

| Modelo | MASE nos 16 testes | p contra a tendência | Erro médio recente | Faixa acertou | Interval score |
|---|---|---|---|---|---|
| repetir o último mês | 1,58 | 0,999 | 1,03% | 100% | 0,049 |
| tendência | 1,06 | campeão | 0,65% | 100% | 0,047 |
| repetir o mês do ano anterior | 6,39 | 1,000 | 5,55% | 100% | 0,184 |
| Theta | 1,16 | 0,861 | 0,65% | 100% | 0,038 |
| Holt amortecido | 0,96 | 0,308 | 0,48% | 83% | 0,025 |
| ARIMA | 1,18 | 0,704 | 1,02% | 75% | 0,037 |
| SARIMAX | 1,43 | 0,877 | 1,90% | 17% | 0,098 |
| Prophet | 1,22 | 0,696 | 1,15% | 25% | 0,093 |
| combinação | 0,89 | 0,031 | 0,53% | 100% | 0,043 |
| LightGBM | 1,09 | 0,540 | 0,61% | 100% | 0,059 |

- **O MASE** é o erro dividido pelo passo típico da série no treino. Abaixo de 1, o modelo erra menos que repetir o último mês de um passo.
- **O p** é o do teste de Diebold-Mariano de que o desafiante erra menos que a tendência, antes da correção de Holm.
- **O interval score** julga a faixa pela largura e pela falta de cobertura juntas. Menor é melhor.

**Leitura:**
- Nos testes recentes, o Holt, a combinação e o LightGBM erraram menos que a tendência. Mas são 4 testes, e nos 16 testes a diferença não passou no teste.
- O Prophet e o SARIMAX têm faixas estreitas demais: acertaram 25% e 17% dos casos recentes, contra 80% nominais.

## Onde um desafiante assumiu

- **03 Direitos creditórios descontados:** Theta, com p = 0,001.
- **05 Financiamentos à exportação:** Theta, com p = 0,002.
- **06 Financiamentos à importação:** Theta, com p = 0,010.
- **13 Outros créditos:** combinação, com p = 0,001.
- **AL:** combinação, com p = 0,000.
- **BA:** combinação, com p = 0,003.
- **DF:** repetir o último mês, com p = 0,000.
- **MG:** combinação, com p = 0,001.
- **PI:** combinação, com p = 0,005.
- **RJ:** repetir o último mês, com p = 0,000.
- **SC:** combinação, com p = 0,005.

## As métricas

- **Erro do backtest, nos testes recentes:** mediana de 1,55% nas 41 séries. Esses testes também entram na escolha, e por isso o número sai otimista.
- **Erro honesto do procedimento:**
  - **mediana:** 1,92%;
  - **média:** 4,57%, puxada pela modalidade 10, uma carteira de R$ 0,1 bi que mudou de patamar;
  - **como sai:** em cada teste recente, a escolha é refeita só com os testes que já tinham terminado. É o número a esperar do procedimento inteiro.
- **Faixa provável:** os campeões cobriram 81% dos casos recentes.
- **Importância das variáveis no LightGBM,** no treino final: {'variacao_1': '19%', 'variacao_3': '13%', 'variacao_media': '12%', 'variacao_2': '11%', 'modalidade': '10%', 'tamanho': '10%', 'uf': '9%', 'mes_previsto': '9%', 'selic': '4%', 'variacao_da_selic': '3%'}. A Selic pesa pouco e funciona mais como marca do tempo do que como causa.

## O erro por série

Nota é o MASE nos 16 testes. O melhor desafiante é o de menor nota, com o p dele contra a tendência, antes da correção de Holm. O erro recente é o do campeão nos 4 testes recentes, e o erro honesto, o do procedimento.

### País

| Recorte | Campeão | Nota da tendência | Melhor desafiante | Nota dele | p | Erro recente | Erro honesto |
|---|---|---|---|---|---|---|---|
| Brasil | tendência | 1,06 | combinação | 0,89 | 0,031 | 0,65% | 0,62% |

### Modalidades

| Recorte | Campeão | Nota da tendência | Melhor desafiante | Nota dele | p | Erro recente | Erro honesto |
|---|---|---|---|---|---|---|---|
| 01 Adiantamentos a depositantes | tendência | 1,13 | Holt amortecido | 0,93 | 0,150 | 6,50% | 6,50% |
| 02 Empréstimos | tendência | 1,52 | ARIMA | 1,59 | 0,709 | 1,19% | 1,19% |
| 03 Direitos creditórios descontados | Theta | 0,65 | Theta | 0,53 | 0,001 | 2,87% | 3,35% |
| 04 Financiamentos | tendência | 1,50 | combinação | 1,35 | 0,159 | 0,62% | 0,62% |
| 05 Financiamentos à exportação | Theta | 1,85 | repetir o último mês | 1,24 | 0,066 | 2,16% | 2,23% |
| 06 Financiamentos à importação | Theta | 1,66 | repetir o último mês | 1,05 | 0,026 | 5,15% | 6,06% |
| 07 Financiamentos com interveniência | tendência | 4,42 | ARIMA | 4,13 | 0,271 | 21,37% | 21,37% |
| 08 Financiamentos rurais | tendência | 2,61 | ARIMA | 2,72 | 0,842 | 1,77% | 3,80% |
| 09 Financiamentos imobiliários | tendência | 1,10 | SARIMAX | 1,03 | 0,292 | 1,05% | 1,05% |
| 10 Financiamentos de títulos e valores mobiliários | tendência | 0,32 | LightGBM | 0,11 | 0,014 | 80,54% | 80,54% |
| 11 Financiamentos de infraestrutura e desenvolvimento | tendência | 1,86 | Theta | 1,44 | 0,056 | 2,55% | 2,55% |
| 12 Operações de arrendamento | tendência | 0,77 | combinação | 0,69 | 0,191 | 0,81% | 0,79% |
| 13 Outros créditos | combinação | 0,94 | combinação | 0,67 | 0,001 | 3,87% | 3,87% |

### UFs

| Recorte | Campeão | Nota da tendência | Melhor desafiante | Nota dele | p | Erro recente | Erro honesto |
|---|---|---|---|---|---|---|---|
| AC | tendência | 1,40 | Theta | 1,30 | 0,317 | 3,00% | 3,00% |
| AL | combinação | 2,40 | LightGBM | 2,20 | 0,027 | 2,93% | 3,27% |
| AM | tendência | 1,04 | Holt amortecido | 0,90 | 0,205 | 2,29% | 2,77% |
| AP | tendência | 1,22 | Theta | 1,14 | 0,239 | 5,35% | 5,35% |
| BA | combinação | 1,03 | Holt amortecido | 0,80 | 0,091 | 0,74% | 0,73% |
| CE | tendência | 1,71 | LightGBM | 1,65 | 0,351 | 1,92% | 1,92% |
| DF | repetir o último mês | 3,09 | repetir o último mês | 2,78 | 0,000 | 1,11% | 1,11% |
| ES | tendência | 0,89 | combinação | 0,72 | 0,256 | 2,04% | 2,04% |
| GO | tendência | 1,13 | combinação | 1,03 | 0,153 | 1,46% | 1,46% |
| MA | tendência | 0,93 | Holt amortecido | 0,90 | 0,434 | 0,87% | 0,87% |
| MG | combinação | 1,11 | combinação | 0,83 | 0,001 | 0,93% | 1,19% |
| MS | tendência | 1,34 | Theta | 1,07 | 0,107 | 1,45% | 1,45% |
| MT | tendência | 0,89 | repetir o último mês | 0,81 | 0,278 | 1,11% | 1,22% |
| PA | tendência | 0,66 | ARIMA | 0,67 | 0,967 | 0,86% | 0,86% |
| PB | tendência | 1,30 | Theta | 1,29 | 0,490 | 1,09% | 1,09% |
| PE | tendência | 1,54 | combinação | 1,45 | 0,161 | 2,16% | 2,16% |
| PI | combinação | 1,89 | Theta | 1,54 | 0,105 | 1,98% | 2,94% |
| PR | tendência | 1,00 | Theta | 0,89 | 0,284 | 1,01% | 1,01% |
| RJ | repetir o último mês | 1,11 | repetir o último mês | 0,87 | 0,000 | 1,36% | 1,36% |
| RN | tendência | 1,36 | SARIMAX | 0,98 | 0,028 | 1,55% | 1,45% |
| RO | tendência | 1,32 | repetir o último mês | 0,95 | 0,260 | 1,85% | 2,02% |
| RR | tendência | 2,62 | Theta | 2,51 | 0,287 | 1,30% | 4,07% |
| RS | tendência | 0,99 | Theta | 0,82 | 0,213 | 0,94% | 1,31% |
| SC | combinação | 0,73 | combinação | 0,60 | 0,005 | 0,41% | 0,49% |
| SE | tendência | 1,84 | ARIMA | 1,90 | 0,842 | 2,33% | 2,33% |
| SP | tendência | 1,67 | combinação | 1,55 | 0,233 | 1,16% | 1,16% |
| TO | tendência | 1,78 | LightGBM | 1,75 | 0,424 | 4,17% | 4,17% |

## As séries em que o erro mede uma mudança, e não o modelo

A janela de avaliação prevê os meses de fevereiro a julho de 2026. Em cinco séries, o nível mudou de um jeito que nenhum candidato treinado antes podia ver. A causa de cada mudança não foi verificada.

- **07 Financiamentos com interveniência:** ficou entre R$ 3,3 e 3,5 bilhões até dez/2025 e caiu todo mês desde então, até R$ 1,81 bilhão em jul/2026, 49% abaixo. A janela de avaliação é exatamente a queda, e o erro médio chega a 33% a 3 meses.
- **10 Financiamentos de títulos e valores mobiliários:** caiu de R$ 1,5 a 4,0 bilhões em 2024 para R$ 0,09 bilhão em abr/2025 e fica entre R$ 0,09 e 0,16 bilhão desde então. Os saltos de 2024 inflam a escala do MASE, e o 0,02 não indica acerto. A leitura honesta é o erro médio, de 5% a 14%. A queda começa em jan/2025, o mês da mudança de critério do ativo problemático, que pela ontologia não muda a carteira ativa. A relação entre as duas não foi verificada.
- **11 Financiamentos de infraestrutura e desenvolvimento:** subiu de R$ 110 para 126 bilhões e caiu R$ 4 bilhões em mai/2026, 3,1%. O erro médio é pequeno, de 1,7% a 3,3%, mas a série é tão lisa que o passo típico do treino também é pequeno, e o MASE sobe. A faixa, estreita pelo mesmo motivo, não cobriu nenhum dos doze casos.
- **AC e TO:** os dois saltaram em abr/2026, o AC 4% e o TO 9%. O AC voltou ao nível anterior no mês seguinte, e o TO ficou acima dele.

Nenhuma dessas mudanças coincide com a publicação mais grossa (jul/2025) ou com a divergência entre V1 e V2 (set/2025).

## Limitações

- **31 meses.** Cada mês do ano aparece duas ou três vezes, e a sazonalidade completa só pode ser testada acima de 36 meses.
- **Testes sobrepostos.** Os erros a 2 e 3 meses de testes vizinhos dividem meses, e a amostra efetiva é menor que 16. O teste de Diebold-Mariano corrige a variância por isso.
- **Mudanças depois de ver o resultado.** O LightGBM, o ajuste da quebra, a faixa que não encolhe, a regra de campeão e desafiante e os cinco desafiantes clássicos vieram depois da primeira execução, como prática de MLOps, todos registrados no ADR 0024 com data e motivo. O erro honesto e, a partir de agora, o monitoramento mês a mês são o árbitro.
- **Sem reconciliação.** O Brasil não é a soma das UFs nem das modalidades. A reconciliação hierárquica fica para a v0.3 (#99).
- **As mudanças de nível de cinco séries** não estão explicadas (#95).

## Monitoramento

A cada mês novo de dado, a previsão roda de novo: os testes ganham um mês, a escolha é refeita, e o erro da projeção do mês anterior contra o realizado vira o árbitro fora da amostra. A rotina vai para um job no Databricks, com o histórico no MLflow e numa tabela Delta, numa issue própria ligada à #22.

## Como reproduzir

Na máquina local, com o perfil OAuth do Databricks:

```bash
uv run python -m scripts.analises.previsao_da_carteira
```

A execução é determinística: os modelos usam semente fixa, e duas execuções seguidas gravam arquivos idênticos. Leva cerca de 13 minutos, a maior parte no Prophet e no ARIMA.

A Q27 do gabarito tem a tendência do país em SQL, sobre a série publicada (`evaluation/gabarito/Q27.sql`). A tela desconta o degrau de set/2025, e os dois números diferem em cerca de R$ 10 bi em outubro.

O autoteste do método roda sem Databricks e está no CI:

```bash
uv run python -m scripts.analises.previsao_da_carteira --autoteste
```
