# Previsão da carteira PJ: o resultado do backtest

**Data:** 2026-10-06
**Decisão que motivou:** [ADR 0023](adr/0023-previsao-da-carteira-escolhida-pelo-backtest.md), pela #27 (Q27 da especificação).
**Script:** `scripts/analises/previsao_da_carteira.py`, sobre o `mrt_carteira_mensal` no Databricks, carteira ativa PJ de jan/2024 a jul/2026.
**Arquivos:** `dashboard/public/data/projecao_da_carteira.json` e `backtest_da_projecao.json`, data-base 2026-07-31.

## Resumo

- **A carteira ativa PJ do país deve ficar perto de R$ 2,93 trilhões em agosto e de R$ 2,97 trilhões em outubro de 2026.** O modelo é a deriva, que segue a inclinação média da série.
- **No país, o erro da avaliação fica abaixo de 1%** nos três horizontes. A deriva ganha do ingênuo a 2 e a 3 meses e perde a 1 mês. O intervalo de 80% cobriu os quatro meses de cada horizonte.
- **Nas 41 séries, repetir o último mês é difícil de bater a 1 mês.** Em 33 séries a janela de escolha ficou com um candidato diferente do ingênuo. Na avaliação, esse candidato ganha do ingênuo em 15 delas a 1 mês, em 19 a 2 meses e em 20 a 3 meses.
- **O intervalo de 80% cobriu 76% dos casos da avaliação,** perto do nominal e um pouco otimista. Em sete séries, cobriu metade dos casos ou menos.
- **Cinco séries têm uma mudança de nível dentro da janela de avaliação** que nenhuma das três quebras registradas explica: as modalidades 07, 10 e 11 e as UFs AC e TO. Nelas, o erro mede a mudança, e não o modelo.

## Como ler as medidas

- **MASE:** o erro absoluto médio dividido pelo erro médio de um passo do ingênuo no treino da mesma origem. Abaixo de 1, o erro fica menor que o passo típico da série no treino. **Isso não é o mesmo que ganhar do ingênuo no mesmo horizonte.** Para essa comparação, as tabelas trazem o MASE do ingênuo ao lado, na mesma janela.
- **MAPE:** o erro percentual médio, para ler em reais.
- **Cobertura:** a fração dos meses da avaliação em que o realizado caiu dentro do intervalo de 80%.

A janela de avaliação tem quatro origens por horizonte. Uma diferença como a do país a 1 mês, 0,70 contra 0,59, está dentro do ruído de quatro casos.

## A projeção do país

| Mês | Realizado | Projeção | Intervalo de 80% |
|---|---|---|---|
| mai/2026 | R$ 2,901 tri | | |
| jun/2026 | R$ 2,952 tri | | |
| jul/2026 | R$ 2,910 tri | | |
| ago/2026 | | R$ 2,929 tri | R$ 2,876 a 2,982 tri |
| set/2026 | | R$ 2,948 tri | R$ 2,871 a 3,024 tri |
| out/2026 | | R$ 2,967 tri | R$ 2,871 a 3,062 tri |

## O erro por recorte

Os números estão na ordem 1 mês / 2 meses / 3 meses. **Em negrito,** o horizonte em que o escolhido ganha do ingênuo na avaliação. Quando o escolhido é o próprio ingênuo, as duas colunas coincidem.

### País

| Recorte | Escolhido | MASE do escolhido | MASE do ingênuo | MAPE do escolhido | Cobertura |
|---|---|---|---|---|---|
| Brasil | deriva | 0,70 / **0,58** / **0,76** | 0,59 / 0,95 / 1,02 | 0,9% / 0,7% / 0,9% | 100% / 100% / 100% |

### Modalidades

| Recorte | Escolhido | MASE do escolhido | MASE do ingênuo | MAPE do escolhido | Cobertura |
|---|---|---|---|---|---|
| 01 Adiantamentos a depositantes | Holt amortecido | **0,24** / **0,30** / **0,47** | 0,44 / 0,62 / 0,83 | 2,0% / 2,6% / 4,2% | 100% / 100% / 100% |
| 02 Empréstimos | deriva | 0,89 / **0,80** / 1,43 | 0,60 / 1,00 / 1,05 | 1,1% / 1,0% / 1,8% | 75% / 75% / 75% |
| 03 Direitos creditórios descontados | Holt amortecido | **0,85** / **0,56** / 0,77 | 0,95 / 0,88 / 0,26 | 3,9% / 2,6% / 3,5% | 50% / 75% / 75% |
| 04 Financiamentos | deriva | 0,39 / **0,56** / **0,54** | 0,39 / 1,03 / 1,54 | 0,5% / 0,7% / 0,7% | 100% / 100% / 100% |
| 05 Financiamentos à exportação | ingênuo | 1,12 / 1,31 / 1,46 | 1,12 / 1,31 / 1,46 | 1,7% / 2,0% / 2,2% | 75% / 75% / 100% |
| 06 Financiamentos à importação | ingênuo | 0,87 / 0,82 / 2,43 | 0,87 / 0,82 / 2,43 | 2,6% / 2,5% / 8,1% | 75% / 100% / 75% |
| 07 Financiamentos com interveniência | Holt amortecido | 6,55 / 10,48 / **14,18** | 5,05 / 9,90 / 14,29 | 11,8% / 21,6% / 32,6% | 50% / 25% / 25% |
| 08 Financiamentos rurais | deriva | **0,69** / **1,24** / **1,44** | 1,39 / 2,64 / 3,30 | 1,0% / 1,9% / 2,1% | 100% / 100% / 100% |
| 09 Financiamentos imobiliários | deriva | **0,37** / **0,61** / **1,20** | 0,80 / 1,86 / 2,12 | 0,5% / 0,9% / 1,7% | 100% / 100% / 75% |
| 10 Financiamentos de títulos e valores mobiliários | ingênuo | 0,02 / 0,04 / 0,06 | 0,02 / 0,04 / 0,06 | 4,9% / 9,4% / 14,3% | 100% / 100% / 100% |
| 11 Financiamentos de infraestrutura e desenvolvimento | Holt amortecido | 2,74 / 4,17 / 5,35 | 1,69 / 2,69 / 3,45 | 1,7% / 2,6% / 3,3% | 0% / 0% / 0% |
| 12 Operações de arrendamento | deriva | **0,59** / **0,51** / **1,65** | 0,90 / 1,38 / 2,08 | 0,5% / 0,5% / 1,5% | 100% / 100% / 75% |
| 13 Outros créditos | ingênuo sazonal | **0,34** / **0,70** / 1,06 | 0,86 / 1,18 / 0,56 | 2,5% / 4,9% / 7,6% | 100% / 75% / 50% |

### UFs

| Recorte | Escolhido | MASE do escolhido | MASE do ingênuo | MAPE do escolhido | Cobertura |
|---|---|---|---|---|---|
| AC | deriva | 2,90 / 3,74 / 3,97 | 2,80 / 3,29 / 3,28 | 2,4% / 3,2% / 3,4% | 50% / 50% / 25% |
| AL | Holt amortecido | 2,93 / 2,50 / **1,76** | 1,50 / 2,29 / 2,59 | 5,3% / 4,5% / 3,0% | 50% / 75% / 50% |
| AM | Holt amortecido | 1,03 / 1,10 / 1,13 | 0,45 / 0,83 / 1,06 | 2,0% / 2,2% / 2,2% | 100% / 50% / 50% |
| AP | deriva | 1,39 / 2,11 / **2,70** | 1,26 / 2,06 / 2,97 | 3,6% / 5,5% / 7,0% | 75% / 50% / 100% |
| BA | Holt amortecido | **0,21** / **0,56** / **0,53** | 0,55 / 1,44 / 1,99 | 0,3% / 0,7% / 0,7% | 100% / 75% / 75% |
| CE | deriva | **0,81** / **1,63** / **1,88** | 1,00 / 2,23 / 3,37 | 1,1% / 2,2% / 2,4% | 75% / 75% / 75% |
| DF | ingênuo | 0,23 / 0,58 / 0,91 | 0,23 / 0,58 / 0,91 | 0,4% / 1,1% / 1,8% | 100% / 100% / 100% |
| ES | deriva | 0,65 / 1,12 / 1,65 | 0,56 / 0,67 / 0,46 | 1,1% / 2,0% / 2,9% | 75% / 100% / 100% |
| GO | deriva | 1,09 / 1,86 / 1,83 | 0,73 / 1,78 / 1,64 | 1,0% / 1,7% / 1,7% | 75% / 50% / 75% |
| MA | deriva | **0,30** / 1,01 / 2,20 | 0,56 / 0,95 / 1,39 | 0,2% / 0,8% / 1,7% | 100% / 75% / 50% |
| MG | Holt amortecido | **0,76** / **0,72** / **0,74** | 1,14 / 1,11 / 1,06 | 1,1% / 1,0% / 1,0% | 50% / 50% / 50% |
| MS | ingênuo | 1,19 / 1,90 / 1,89 | 1,19 / 1,90 / 1,89 | 1,3% / 2,0% / 2,0% | 75% / 50% / 75% |
| MT | ingênuo | 0,64 / 0,88 / 1,09 | 0,64 / 0,88 / 1,09 | 1,0% / 1,4% / 1,7% | 75% / 75% / 100% |
| PA | deriva | **0,85** / **0,98** / **0,64** | 0,92 / 2,09 / 2,78 | 0,9% / 1,0% / 0,7% | 75% / 100% / 100% |
| PB | deriva | **0,21** / **0,46** / **2,07** | 0,75 / 1,44 / 2,44 | 0,2% / 0,5% / 2,4% | 100% / 100% / 75% |
| PE | deriva | 1,47 / 2,12 / **1,52** | 1,41 / 1,99 / 1,67 | 1,9% / 2,7% / 1,9% | 75% / 75% / 100% |
| PI | deriva | 0,96 / 1,90 / 2,52 | 0,33 / 0,43 / 0,58 | 1,6% / 3,2% / 4,2% | 100% / 100% / 75% |
| PR | deriva | **0,68** / **1,20** / **1,44** | 1,12 / 2,21 / 2,51 | 0,6% / 1,1% / 1,3% | 75% / 75% / 100% |
| RJ | ingênuo | 0,94 / 1,07 / 1,04 | 0,94 / 1,07 / 1,04 | 1,2% / 1,4% / 1,4% | 75% / 100% / 100% |
| RN | deriva | 1,21 / 1,41 / 1,84 | 0,85 / 0,78 / 0,89 | 1,2% / 1,4% / 1,9% | 75% / 100% / 75% |
| RO | ingênuo | 0,56 / 0,58 / 1,15 | 0,56 / 0,58 / 1,15 | 0,5% / 0,6% / 1,1% | 100% / 100% / 100% |
| RR | deriva | 0,42 / 0,81 / 1,44 | 0,21 / 0,44 / 0,74 | 0,6% / 1,2% / 2,2% | 100% / 100% / 100% |
| RS | Holt amortecido | 1,48 / 1,27 / **1,16** | 0,60 / 1,01 / 1,62 | 1,8% / 1,6% / 1,4% | 25% / 25% / 50% |
| SC | Holt amortecido | **0,36** / **0,55** / **0,63** | 0,55 / 1,49 / 2,07 | 0,3% / 0,5% / 0,5% | 100% / 75% / 50% |
| SE | deriva | **1,20** / **2,35** / **3,69** | 2,04 / 4,17 / 5,12 | 1,2% / 2,2% / 3,6% | 75% / 50% / 25% |
| SP | deriva | 0,78 / **0,64** / 0,69 | 0,55 / 0,76 / 0,64 | 1,5% / 1,2% / 1,3% | 100% / 100% / 100% |
| TO | deriva | 2,53 / **3,59** / **4,83** | 2,53 / 4,02 / 6,14 | 2,8% / 4,0% / 5,7% | 50% / 25% / 0% |

## As séries em que o erro mede uma mudança, e não o modelo

A janela de avaliação prevê os meses de fevereiro a julho de 2026. Em cinco séries, o nível mudou de um jeito que nenhum candidato treinado antes podia ver. A causa de cada mudança não foi verificada.

- **07 Financiamentos com interveniência:** ficou entre R$ 3,3 e 3,5 bilhões até dez/2025 e caiu todo mês desde então, até R$ 1,81 bilhão em jul/2026, 49% abaixo. A janela de avaliação é exatamente a queda, e o MAPE chega a 33% a 3 meses.
- **10 Financiamentos de títulos e valores mobiliários:** caiu de R$ 1,5 a 4,0 bilhões em 2024 para R$ 0,09 bilhão em abr/2025 e fica entre R$ 0,09 e 0,16 bilhão desde então. Os saltos de 2024 inflam a escala do MASE, e o 0,02 não indica acerto. A leitura honesta é o MAPE, de 5% a 14%. A queda começa em jan/2025, o mês da mudança de critério do ativo problemático, que pela ontologia não muda a carteira ativa. A relação entre as duas não foi verificada.
- **11 Financiamentos de infraestrutura e desenvolvimento:** subiu de R$ 110 para 126 bilhões e caiu R$ 4 bilhões em mai/2026, 3,1%. O MAPE é pequeno, de 1,7% a 3,3%, mas a série é tão lisa que o passo típico do treino também é pequeno, e o MASE sobe. O intervalo, estreito pelo mesmo motivo, não cobriu nenhum dos doze casos.
- **AC e TO:** os dois saltaram em abr/2026, o AC 4% e o TO 9%. O AC voltou ao nível anterior no mês seguinte, e o TO ficou acima dele.

Nenhuma dessas mudanças coincide com a publicação mais grossa (jul/2025) ou com a divergência entre V1 e V2 (set/2025).

## O que o resultado diz

- **A projeção do país é a mais confiável das 41:** a série é a soma de todas as outras, o erro fica abaixo de 1% e o intervalo cobriu todos os casos.
- **A 1 mês, o ingênuo é a régua difícil.** A janela de escolha preferiu outro candidato em 33 séries, e menos da metade delas manteve a vantagem na avaliação. A 2 e 3 meses, a vantagem se mantém em 19 e 20 das 33.
- **O erro publicado não é o do vencedor da própria disputa,** porque a escolha e a medida usam janelas separadas. As janelas cobrem períodos diferentes, e o erro de uma não prevê o da outra: no país, o MASE da deriva foi de 0,97 a 1,33 na escolha e de 0,58 a 0,76 na avaliação.
- **A tela precisa mostrar o ingênuo ao lado do escolhido e a cobertura** (RF-302), porque o MASE sozinho não diz se o modelo ganha do ingênuo.

## Limitações

- **Quatro origens por horizonte.** O erro publicado é uma estimativa ruidosa, e diferenças pequenas entre o escolhido e o ingênuo não sustentam conclusão.
- **31 meses.** A sazonalidade só entra pelo ingênuo sazonal, que foi escolhido em uma série. A suavização exponencial sazonal volta a ser candidata acima de 36 meses (ADR 0023, decisão 2).
- **As mudanças de nível das cinco séries acima** não estão explicadas. Se forem reclassificação de operações entre modalidades ou UFs, o país não muda, mas o erro dos recortes sim.

## Como reproduzir

Na máquina local, com o perfil OAuth do Databricks:

```bash
uv run python -m scripts.analises.previsao_da_carteira
```

A projeção do país também sai em SQL, pela deriva, na Q27 do gabarito (`evaluation/gabarito/Q27.sql`, ADR 0023, decisão 6), com o mesmo resultado.

O autoteste do método roda sem Databricks e está no CI:

```bash
uv run python -m scripts.analises.previsao_da_carteira --autoteste
```
