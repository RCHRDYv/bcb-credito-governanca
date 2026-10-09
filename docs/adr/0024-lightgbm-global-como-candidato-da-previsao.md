# ADR 0024: A previsão escolhe por campeão e desafiante, com um LightGBM global e outros desafiantes contra a tendência

**Status:** Aceito. Complementa o [ADR 0023](0023-previsao-da-carteira-escolhida-pelo-backtest.md) e substitui a regra de escolha da decisão 3 dele. O resultado da execução contra o mart está em [`docs/previsao.md`](../previsao.md).
**Data:** 2026-10-06

## Contexto

A previsão do ADR 0023 escolhia, para cada uma das 41 séries, o melhor de quatro candidatos estatísticos simples. Nenhum era de aprendizado de máquina. Na revisão do mockup da Tela 3, pedi que um modelo de aprendizado de máquina disputasse a previsão no mesmo teste (#98).

**O histórico é curto para um modelo por série.** São 31 meses, e um modelo treinado só com uma série teria uns 20 pontos para aprender. Nas competições de previsão, o aprendizado de máquina perdeu para os métodos estatísticos com séries isoladas (M4) e venceu quando um modelo só aprendeu com milhares de séries parecidas ao mesmo tempo, com variáveis externas (M5). Aqui há 351 séries de UF por modalidade, que dão dezenas de vezes mais exemplos.

**A primeira execução com o LightGBM revelou três problemas,** e cada um virou uma decisão:
- **A quebra de set/2025:** o LightGBM aprendeu como padrão de setembro o degrau da divergência entre V1 e V2. A carteira PJ subiu 4,3% na V2 e 1,2% na V1 naquele mês. A tendência também lia o degrau: a inclinação do Brasil passava de R$ 16,1 bi para R$ 18,9 bi por mês.
- **A faixa:** a faixa de um mês distante podia sair mais estreita que a de um mês próximo.
- **A regra de escolha:** escolher pela janela antiga ignorava os testes recentes. Escolher pela menor diferença em qualquer janela trocaria de modelo por ruído, porque no Brasil a tendência e o LightGBM erraram 1,23% e 1,25% nos 16 testes.

**Registro de ordem.** As decisões 5, 7, 8, 9, 10 e 11 vieram depois de ver o resultado da primeira execução. Tomei-as em 2026-10-06 como prática de MLOps: em previsão em produção, os modelos são acompanhados, retreinados e trocados pelo desempenho observado. O cuidado que vale é publicar, ao lado do erro do backtest, um erro medido em testes que não escolheram o modelo (decisão 11). O pré-registro é exigência do experimento de ontologia contra RAG (ADR 0013), que é um teste de hipótese, e não desta previsão.

## Decisões

### 1. Um LightGBM global, treinado com as 351 séries de UF por modalidade

O LightGBM aprende com todas as células de UF por modalidade da carteira ativa PJ ao mesmo tempo. A previsão de cada célula é somada para o Brasil, as 13 modalidades e as 27 UFs.
- **Células de fora:** a célula que teve algum mês abaixo de R$ 1 milhão no treino fica fora do modelo, porque a variação de uma carteira quase nula não ensina nada e explode no logaritmo. Na soma, ela entra com o último valor.
- **Peso:** cada exemplo pesa pelo tamanho da carteira da célula. Sem isso, uma célula de R$ 5 milhões contaria tanto quanto uma de R$ 500 bilhões.

### 2. A Selic entra como variável externa

A meta da Selic no fim do mês (`fct_selic`, [ADR 0010](0010-selic-e-a-meta-do-copom-vigente-no-fim-do-mes.md)) entra no LightGBM pelo nível no mês da origem e pela variação em três meses, e no SARIMAX pela defasagem de três meses (decisão 10). É uma série só, nacional, com 31 valores: ela tende a funcionar como marca do tempo, e só é apresentada como causa se a importância das variáveis e o backtest sustentarem isso.

### 3. O desenho do LightGBM

- **Previsão direta:** um modelo por horizonte, de 1 a 3 meses.
- **Alvo:** o logaritmo da razão entre a carteira da célula no mês previsto e no mês da origem.
- **Variáveis da célula no mês da origem:**
  - as três últimas variações mensais, em logaritmo;
  - a variação média dos últimos 12 meses, ou de todos os meses disponíveis, se forem menos;
  - o mês do ano do mês previsto;
  - o tamanho da carteira, em logaritmo;
  - a UF e a modalidade, como categorias;
  - a Selic, como na decisão 2.
- **Sem vazamento:** em cada origem do backtest, o modelo treina só com meses até ela. O autoteste confere isso mudando os meses depois da origem e exigindo a mesma previsão.

### 4. Hiperparâmetros fixos, sem ajuste

Os hiperparâmetros são conservadores e foram fixados antes da primeira execução. Não são ajustados em nenhuma janela:
- 300 árvores, com taxa de aprendizado de 0,03;
- até 15 folhas e profundidade 4;
- pelo menos 40 exemplos por folha;
- 80% das variáveis por árvore e regularização L2 de 1;
- semente 27, uma thread e modo determinístico.

O modelo é treinado pela API nativa do LightGBM, sem o scikit-learn.

### 5. A faixa de 80% do LightGBM vem dos erros dele fora da amostra, e nunca encolhe

Previsões de quantis não se somam entre células. Por isso, a faixa de cada série sai dos erros relativos do LightGBM nessa série:
- **Em cada origem:** a faixa vai até o erro que o modelo não passou em 80% das origens que já tinham terminado antes dela, em cada horizonte.
- **Com menos de quatro origens anteriores:** a faixa usa o desvio das variações mensais do treino.
- **Para todos os horizontes:** a faixa nunca fica mais estreita num mês mais distante, porque a incerteza não diminui com a distância. Decidi em 2026-10-06.

### 6. O arquivo dos testes, para a Tela 3

O gráfico do erro da Tela 3 mostra o que a projeção dizia num teste contra o que aconteceu. Para isso, o script grava `testes_da_projecao.json`: a previsão do modelo escolhido em cada um dos quatro testes recentes, com a faixa e o realizado, por série e horizonte.

### 7. Os modelos de uma série descontam a quebra de set/2025

A divergência entre V1 e V2 de set/2025 (`ontology/dimensoes.yml`, `divergencia_entre_versoes`) é um degrau de publicação, e não do crédito. Decidi em 2026-10-06:
- **Nos modelos de uma série:** a série de treino desconta o degrau. Os meses antes da quebra sobem pelo degrau, e a projeção parte do nível de hoje. O degrau é o excesso da variação do mês da quebra sobre a variação mediana dos outros meses, medido em cada teste só com os meses que o treino conhece.
- **No LightGBM:** os exemplos cuja janela cruza a quebra ficam fora do treino. O degrau medido célula a célula é ruído, e metade das células sairia com degrau negativo.
- **A medida conferida pela V1:** no Brasil, o degrau estimado é de R$ 97 bi, e a diferença entre a V2 e a V1 no mês dá R$ 84 bi.

### 8. A escala do MASE é a mesma para todos os candidatos

O MASE de cada origem divide o erro pelo erro médio de repetir o mês anterior no treino, já sem o degrau da quebra. Sem isso, o salto de set/2025 inflaria a escala de todas as origens depois dele.

### 9. Campeão e desafiante, pela janela que cresce e pelo teste de Diebold-Mariano

Substitui a regra da decisão 3 do ADR 0023. Decidi em 2026-10-06:
- **O campeão é a tendência (deriva)** em todas as séries. É o modelo de referência, e no Brasil nenhum outro se provou melhor.
- **Um desafiante só assume uma série se errar menos com significância,** no teste de Diebold-Mariano unilateral:
  - **as diferenças:** o erro escalado do desafiante menos o do campeão, origem a origem, na média dos três horizontes;
  - **a variância:** de Newey-West até a defasagem 2, porque origens vizinhas dividem meses previstos;
  - **a amostra pequena:** a correção de Harvey, Leybourne e Newbold, contra a t de Student;
  - **o nível:** p < 0,10, com a correção de Holm entre os desafiantes.
- **Entre os que passam,** fica o de menor MASE médio.
- **A janela é a que cresce:** contam todas as origens completas até a data. A cada mês novo de dado, o teste novo entra, e a escolha roda de novo.

### 10. Cinco desafiantes clássicos e uma combinação

Todos rodam nas mesmas origens, sobre a série sem o degrau:
- **Theta:** o `ThetaModel` do `statsmodels`, vencedor da M3, sem dessazonalizar enquanto a série tiver menos de 36 meses.
- **ARIMA:**
  - **como:** o `ARIMA` do `statsmodels` com uma diferença e tendência, e a ordem de menor AICc entre (0,1,0), (1,1,0), (0,1,1) e (1,1,1);
  - **por que a grade pequena:** a carteira cresce, e com 13 a 31 pontos um teste de raiz unitária tem pouco poder para escolher a diferença, e uma grade maior escolheria a ordem por ruído.
- **SARIMAX:**
  - **como:** o ARIMA com a Selic de três meses antes como variável externa, para os três meses projetados usarem valores já conhecidos;
  - **a parte sazonal:** fica de fora até a série ter 36 meses.
- **Prophet:** sazonalidade anual só a partir de 24 meses, pontos de mudança com escala 0,01 e semente fixa. A fama dele em competições de previsão é fraca, e ele entra como desafiante, sem garantia de nada.
- **Combinação:** a média simples da tendência, do Holt e do LightGBM, previsões e limites. A composição foi fixada antes de rodar.

A ordem de simplicidade, para o desempate:
1. ingênuo;
2. deriva;
3. ingênuo sazonal;
4. Theta;
5. Holt;
6. ARIMA;
7. SARIMAX;
8. Prophet;
9. combinação;
10. LightGBM.

### 11. O erro honesto do procedimento e o interval score

- **Erro honesto:** em cada um dos quatro testes recentes, a escolha é refeita só com as origens que já tinham terminado antes dele, e o erro do escolhido naquele teste entra na média. É o erro que se esperaria do procedimento inteiro, com a escolha dentro dele, e é publicado ao lado do erro do backtest.
- **Interval score de Winkler:** julga a faixa de 80% pela largura e pela falta de cobertura juntas, dividido pelo realizado. A cobertura sozinha, com cerca de 12 casos por série, não diz se a faixa é larga demais.
- **Monitoramento:** a partir da próxima atualização, o erro da projeção do mês anterior contra o realizado que chegar é o árbitro fora da amostra. Isso entra com a rotina de retreino no Databricks.

## Alternativas descartadas

- **Um LightGBM por série:** cerca de 20 exemplos por série, pouco para um modelo de árvores.
- **Rede neural de séries temporais:** mais dado e mais tempo do que 31 meses sustentam.
- **Ajustar os hiperparâmetros por validação cruzada:** com 16 origens, o ajuste consumiria os testes e deixaria a comparação com os candidatos simples desigual.
- **Escolher pela menor diferença, sem teste:** com 1,23% contra 1,25%, a série trocaria de campeão por ruído a cada mês, e quem lê a tela veria a projeção mudar sem motivo.
- **Uma margem fixa de 5% no MASE:** mais simples de explicar, mas o limiar é arbitrário e não leva em conta quantos testes há nem quanto eles variam.
- **`pmdarima` para o ARIMA automático:** tem problemas de compatibilidade com o numpy atual, e a grade pequena no `statsmodels` faz o mesmo papel.
- **Ajustar a quebra célula a célula no LightGBM:** o degrau medido nas células é ruído.

## Consequências

- **A Q27 continua com a tendência em SQL,** independente do campeão. Decidi em 2026-10-06. Com o ajuste da quebra, a tela e a Q27 podem diferir em alguns bilhões, dentro da tolerância da regra de comparação da #47.
- **As projeções das séries não somam entre si.** Cada série tem o próprio campeão, e a tela não convida a somar. A reconciliação hierárquica fica para a #99, na v0.3.
- **Testes sobrepostos:** os erros a 2 e 3 meses de origens vizinhas dividem meses, e a amostra efetiva é menor que 16. O Diebold-Mariano corrige a variância por isso, e o relatório declara.
- **Novas dependências:** o `lightgbm` e o `prophet`, no `pyproject.toml`. O Prophet traz o Stan compilado.
- **Tempo de execução:** o Prophet e o ARIMA dominam o tempo, e o autoteste do CI leva cerca de dois minutos.

## Resultado

A execução contra o mart, em 2026-10-06, com data-base 2026-07-31, está em [`docs/previsao.md`](../previsao.md), no formato de cartão de modelo. Em resumo:
- **Campeões:** a tendência em 30 séries, a combinação em 6, o Theta em 3 e repetir o último mês em 2. O LightGBM, o Prophet, o ARIMA e o SARIMAX não venceram nenhuma série sozinhos; o LightGBM entra nas 6 séries da combinação.
- **Brasil:** a tendência continua campeã e projeta R$ 2,926 tri em ago/2026 e R$ 2,957 tri em out/2026. O desafiante mais perto foi a combinação, com MASE de 0,89 contra 1,06 da tendência nos 16 testes e p = 0,031. Com nove desafiantes, a correção de Holm pedia p ≤ 0,011.
- **Faixa:** os campeões cobriram 81% dos casos recentes. O Prophet e o SARIMAX têm faixas estreitas demais no Brasil, com 25% e 17%.
- **Erro honesto do procedimento:** mediana de 1,92% nas 41 séries, contra 1,55% do erro do backtest nos mesmos testes recentes. A diferença é o otimismo de escolher e medir nos mesmos testes.
- **Importância das variáveis no LightGBM:** as variações recentes somam 55%, a modalidade 10%, o tamanho 10%, a UF 9%, o mês do ano 9% e a Selic 7%.
