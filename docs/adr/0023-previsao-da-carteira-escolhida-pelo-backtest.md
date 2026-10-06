# ADR 0023: A previsão da carteira é escolhida pelo backtest, com o erro medido numa janela separada

**Status:** Aceito. Os números do resultado entram com a primeira execução contra o mart.
**Data:** 2026-10-06

## Contexto

A Q27 pergunta qual é a projeção da carteira para os próximos três meses, com intervalo. A especificação e o [ADR 0005](0005-projeto-termina-em-recomendacao.md) puseram a projeção na v0.2, com uma condição: ela só entra com backtest e erro publicado. A #27 faz o modelo, e a Tela 3 (#72) mostra o resultado.

**O histórico é curto.** A V2 do SCR.data começa em jan/2024, e em jul/2026 o `mrt_carteira_mensal` tem 31 meses. Não há série mais longa comparável: a V1 tem outra taxonomia de modalidades, e a V2 fica de 4% a 6% acima dela ([ADR 0003](0003-conformacao-de-taxonomia-entre-versoes.md)). Com 31 meses, cada mês do ano aparece duas ou três vezes, e um modelo com sazonalidade de 12 meses tem pouco para estimar.

**As três quebras da série** estão em `ontology/dimensoes.yml`, e nenhuma muda a carteira ativa total da V2:
- **o critério do ativo problemático,** em jan/2025, afeta só o ativo problemático;
- **a publicação mais grossa,** em jul/2025, afeta a contagem de recortes, e não o total;
- **a divergência entre V1 e V2,** em set/2025, afeta a comparação entre as versões.

As decisões 1, 2 e 5 foram tomadas pelo Yuri em 2026-10-06, no planejamento da #27.

## Decisões

### 1. Os recortes são o país, as 13 modalidades e as 27 UFs

São 41 séries da carteira ativa PJ mensal, todas do `mrt_carteira_mensal`, com `cliente = 'PJ'`:
- o país soma todas as UFs e modalidades;
- cada modalidade soma as UFs;
- cada UF soma as modalidades.

O script só soma, sem calcular razão ([ADR 0007](0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md)). A UF por modalidade ficou de fora, porque muitas células são pequenas e ruidosas, e o erro seria difícil de explicar na tela.

### 2. Quatro candidatos, do mais simples ao menos simples

- **Ingênuo:** repete o último mês. É a régua de todos os outros.
- **Deriva:** segue a inclinação média da série, do primeiro ao último mês do treino.
- **Ingênuo sazonal:** repete o mesmo mês do ano anterior.
- **Holt amortecido:** a suavização exponencial com erro aditivo e tendência aditiva amortecida, do `statsmodels`. Acompanha a tendência e a deixa perder força com o horizonte.

A suavização exponencial com sazonalidade de 12 meses ficou de fora: ela precisa de dois anos de treino e, com 31 meses, só teria uma origem na janela de escolha. A sazonalidade fica representada pelo ingênuo sazonal. Ela volta a ser candidata quando a série passar de 36 meses.

### 3. O backtest escolhe numa janela e mede o erro em outra

O backtest é em origem móvel. Cada origem treina com os meses até ela e prevê os três seguintes. O treino vai de 13 meses, o que dá ao ingênuo sazonal um ano inteiro para trás em todos os horizontes, até o tamanho que deixa os três meses dentro da série. Com 31 meses, são 16 origens.

- **Janela de escolha:** as 12 primeiras origens. Nela, cada recorte fica com o candidato de menor MASE médio, nos três horizontes. O empate fica com o mais simples.
- **Janela de avaliação:** as 4 últimas origens, depois da escolha. O erro publicado é o desta janela.

Assim, o erro publicado nunca é o mesmo que escolheu o modelo, e não sai otimista. O arquivo traz as medidas de todos os candidatos, inclusive do ingênuo, para a tela comparar (RF-302).

**As medidas,** por recorte, candidato e horizonte:
- **MASE:** o erro absoluto médio dividido pelo erro médio do ingênuo de um passo no treino da mesma origem. Abaixo de 1, o modelo ganha do ingênuo.
- **MAPE:** o erro percentual médio, por ser fácil de ler.
- **Cobertura:** a fração dos meses da avaliação em que o realizado caiu dentro do intervalo de 80%.

### 4. A projeção usa a série inteira e leva o intervalo de 80%

O candidato escolhido é ajustado nos 31 meses e projeta os três meses seguintes à data-base. O intervalo de 80% vem:
- para o ingênuo, a deriva e o ingênuo sazonal, das fórmulas clássicas, com o desvio dos resíduos no treino;
- para o Holt amortecido, do próprio modelo.

A cobertura da janela de avaliação mostra se esse intervalo é otimista.

### 5. O script roda na máquina local e grava os arquivos da visão 3 no contrato

O script `scripts/analises/previsao_da_carteira.py` lê o mart pelo OAuth do Databricks, como a exportação, e grava dois arquivos no contrato do dashboard, com a chave `gerado_por`:
- **`projecao_da_carteira.json`:** os meses realizados, os projetados e o intervalo, por recorte;
- **`backtest_da_projecao.json`:** as medidas do backtest.

A exportação só lê esses dois arquivos do disco, para o manifesto. O CI valida os arquivos e roda o autoteste do método, sem credencial.

**Em 2026-10-06, o Databricks não ligou o warehouse.** A alternativa de ler o `carteira_mensal_pj.json` já exportado foi apresentada, e o Yuri manteve o mart como fonte.

## Alternativas descartadas

- **Um modelo só para todas as séries, sem backtest:** não diria se ganha do ingênuo, e a especificação exige o erro publicado.
- **Sazonalidade obrigatória:** com 31 meses, o modelo decoraria o ruído dos dois anos e meio.
- **Escolher e medir na mesma janela:** o erro publicado sairia otimista, porque seria o do vencedor da própria disputa.
- **Modelo Python no dbt:** exigiria rodar Python no Databricks Free Edition, e o resultado não precisa morar num mart.

## Consequências

- **A janela de avaliação é pequena.** São quatro origens por horizonte, e o erro publicado é uma estimativa ruidosa. A tela diz isso.
- **As janelas acompanham a série.** Com um mês novo, a escolha ganha uma origem, e a avaliação continua com as quatro últimas.
- **A Q27 continua pendente no gabarito.** Se a resposta de referência é a projeção do país e com que tolerância, é decisão do Yuri na revisão da #27.
- **A nova dependência:** o `statsmodels`, no `pyproject.toml`.

## Resultado

Entra com a primeira execução contra o mart: o modelo escolhido por recorte, o MASE e o MAPE na avaliação e a cobertura do intervalo.
