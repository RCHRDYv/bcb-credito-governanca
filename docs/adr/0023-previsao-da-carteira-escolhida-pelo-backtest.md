# ADR 0023: A previsão da carteira é escolhida pelo backtest, com o erro medido numa janela separada

**Status:** Aceito. O resultado da primeira execução contra o mart está em [`docs/previsao.md`](../previsao.md).
**Data:** 2026-10-06

## Contexto

A Q27 pergunta qual é a projeção da carteira para os próximos três meses, com intervalo. A especificação e o [ADR 0005](0005-projeto-termina-em-recomendacao.md) puseram a projeção na v0.2, com uma condição: ela só entra com backtest e erro publicado. A #27 faz o modelo, e a Tela 3 (#72) mostra o resultado.

**O histórico é curto.** A V2 do SCR.data começa em jan/2024, e em jul/2026 o `mrt_carteira_mensal` tem 31 meses. Não há série mais longa comparável: a V1 tem outra taxonomia de modalidades, e a V2 fica de 4% a 6% acima dela ([ADR 0003](0003-conformacao-de-taxonomia-entre-versoes.md)). Com 31 meses, cada mês do ano aparece duas ou três vezes, e um modelo com sazonalidade de 12 meses tem pouco para estimar.

**As três quebras da série** estão em `ontology/dimensoes.yml`, e nenhuma muda a carteira ativa total da V2:
- **o critério do ativo problemático,** em jan/2025, afeta só o ativo problemático;
- **a publicação mais grossa,** em jul/2025, afeta a contagem de recortes, e não o total;
- **a divergência entre V1 e V2,** em set/2025, afeta a comparação entre as versões.

As decisões 1, 2 e 5 foram tomadas pelo Yuri em 2026-10-06, no planejamento da #27. A leitura do MASE, na decisão 3, e a decisão 6 foram tomadas por ele no mesmo dia, na revisão do resultado.

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
- **MASE:** o erro absoluto médio dividido pelo erro médio do ingênuo de um passo no treino da mesma origem. Abaixo de 1, o erro fica menor que o passo típico da série no treino. Ganhar do ingênuo se lê comparando o MASE dos dois no mesmo horizonte.
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

**Em 2026-10-06, o Databricks não ligou o warehouse.** A alternativa de ler o `carteira_mensal_pj.json` já exportado foi apresentada, e o Yuri manteve o mart como fonte. O warehouse voltou mais tarde, no mesmo dia, e a execução leu o mart.

### 6. A resposta de referência da Q27 é a deriva da carteira PJ do país, em SQL

O gabarito exige SQL portátil sobre o esquema estrela ([ADR 0015](0015-gabarito-com-leituras-aceitas-em-sql-portatil.md)), e a projeção deste ADR fica num arquivo do dashboard, fora dele. A deriva cabe em SQL, e foi o modelo que o backtest escolheu para o país. Por isso a referência da Q27 é a deriva da carteira ativa PJ, em `evaluation/gabarito/Q27.sql`, com a mesma conta do script. Em 2026-10-06, o Yuri decidiu que a Q27 continua com a deriva qualquer que seja o campeão da tela ([ADR 0024](0024-lightgbm-global-como-candidato-da-previsao.md)).
- **Recorte:** só a carteira PJ. A Q27 não diz PF ou PJ, e uma resposta com a carteira total não vale.
- **Tolerância:** a da regra de comparação com o gabarito, que a #47 registra.
- **Se outro modelo virar o campeão do país** numa atualização, a Q27 continua com a deriva, por decisão do Yuri de 2026-10-06 (ADR 0024).

## Alternativas descartadas

- **Um modelo só para todas as séries, sem backtest:** não diria se ganha do ingênuo, e a especificação exige o erro publicado.
- **Sazonalidade obrigatória:** com 31 meses, o modelo decoraria o ruído dos dois anos e meio.
- **Escolher e medir na mesma janela:** o erro publicado sairia otimista, porque seria o do vencedor da própria disputa.
- **Modelo Python no dbt:** exigiria rodar Python no Databricks Free Edition, e o resultado não precisa morar num mart.
- **Pôr a projeção no esquema estrela, para a Q27:** contradiria a decisão de não guardar o resultado num mart, e a deriva já responde em SQL.
- **Mudar o tipo de acerto da Q27 por errata:** a pergunta tem resposta, e a deriva a dá sem sair do esquema estrela.

## Consequências

- **A janela de avaliação é pequena.** São quatro origens por horizonte, e o erro publicado é uma estimativa ruidosa. A tela diz isso.
- **As janelas acompanham a série.** Com um mês novo, a escolha ganha uma origem, e a avaliação continua com as quatro últimas.
- **A Q27 sai da lista de pendentes do gabarito,** com a resposta de referência da decisão 6.
- **A nova dependência:** o `statsmodels`, no `pyproject.toml`.

## Resultado

A primeira execução contra o mart, em 2026-10-06, com data-base 2026-07-31, teve só os quatro candidatos deste ADR. No mesmo dia, o [ADR 0024](0024-lightgbm-global-como-candidato-da-previsao.md) acrescentou o LightGBM global, e o resultado vigente, com os cinco candidatos, está em [`docs/previsao.md`](../previsao.md). O resumo abaixo é o da primeira execução, guardado como registro:
- **Escolhidos:** a deriva em 22 séries, o Holt amortecido em 10, o ingênuo em 8 e o ingênuo sazonal em 1.
- **País:** a deriva projeta R$ 2,93 trilhões em ago/2026 e R$ 2,97 trilhões em out/2026. Na avaliação, o MAPE fica abaixo de 1%, a deriva ganha do ingênuo a 2 e 3 meses e perde a 1 mês, e o intervalo cobriu todos os casos.
- **As 33 séries em que o escolhido não é o ingênuo:** ele ganha do ingênuo na avaliação em 15 a 1 mês, em 19 a 2 meses e em 20 a 3 meses.
- **Cobertura do intervalo de 80%:** 76% dos casos da avaliação.
- **Cinco séries mudaram de nível dentro da janela de avaliação:** as modalidades 07, 10 e 11 e as UFs AC e TO. Nenhuma das três quebras registradas explica essas mudanças, e a causa não foi verificada.

São quatro origens por horizonte. Diferenças pequenas entre o escolhido e o ingênuo ficam dentro do ruído.
