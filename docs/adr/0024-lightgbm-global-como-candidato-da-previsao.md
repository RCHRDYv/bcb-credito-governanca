# ADR 0024: Um LightGBM global entra como candidato da previsão

**Status:** Aceito. Complementa o [ADR 0023](0023-previsao-da-carteira-escolhida-pelo-backtest.md). O resultado da execução contra o mart está em [`docs/previsao.md`](../previsao.md).
**Data:** 2026-10-06

## Contexto

A previsão do ADR 0023 escolhe, para cada uma das 41 séries, o melhor de quatro candidatos estatísticos simples. No Brasil venceu a deriva, a tendência que prolonga a inclinação média da série. Nenhum candidato era de aprendizado de máquina. Na revisão do mockup da Tela 3, o Yuri pediu que um modelo de aprendizado de máquina dispute a previsão no mesmo teste (#98).

**O histórico é curto para um modelo por série.** São 31 meses, e um modelo treinado só com uma série teria uns 20 pontos para aprender. Nas competições de previsão, o aprendizado de máquina perdeu para os métodos estatísticos com séries isoladas (M4) e venceu quando um modelo só aprendeu com milhares de séries parecidas ao mesmo tempo, com variáveis externas (M5). Aqui há 351 séries de UF por modalidade, que dão dezenas de vezes mais exemplos.

**Registro de ordem.** Este candidato entrou depois de os resultados da janela de avaliação do ADR 0023 terem sido vistos. A regra de escolha não muda, e o erro publicado continua vindo da janela de avaliação, que nenhum candidato usa para escolher ou ajustar. Mas a decisão de acrescentar um candidato veio depois do resultado, e fica registrada aqui.

As decisões 1 e 2 foram tomadas pelo Yuri em 2026-10-06. As outras são o desenho do modelo, fixado antes da primeira execução.

## Decisões

### 1. Um modelo global, treinado com as 351 séries de UF por modalidade

O LightGBM aprende com todas as células de UF por modalidade da carteira ativa PJ ao mesmo tempo. A previsão de cada célula é somada para o Brasil, as 13 modalidades e as 27 UFs, as mesmas 41 séries do ADR 0023.
- **Células de fora:** a célula que teve algum mês abaixo de R$ 1 milhão no treino fica fora do modelo, porque a variação de uma carteira quase nula não ensina nada e explode no logaritmo. Na soma, ela entra com o último valor, como no ingênuo.
- **Peso:** cada exemplo pesa pelo tamanho da carteira da célula. Sem isso, uma célula de R$ 5 milhões contaria tanto quanto uma de R$ 500 bilhões, e o erro das séries somadas vem das grandes.

### 2. A Selic entra como variável externa

A meta da Selic no fim do mês (`fct_selic`, [ADR 0010](0010-selic-e-a-meta-do-copom-vigente-no-fim-do-mes.md)) entra pelo nível no mês da origem e pela variação em três meses. É uma série só, nacional, com 31 valores: ela tende a funcionar como marca do tempo, e só é apresentada como causa se a importância das variáveis e o backtest sustentarem isso.

### 3. O desenho do modelo

- **Previsão direta:** um modelo por horizonte, de 1 a 3 meses.
- **Alvo:** o logaritmo da razão entre a carteira da célula no mês previsto e no mês da origem.
- **Variáveis da célula no mês da origem:**
  - as três últimas variações mensais, em logaritmo;
  - a variação média dos últimos 12 meses, ou de todos os meses disponíveis, se forem menos;
  - o mês do ano do mês previsto;
  - o tamanho da carteira, em logaritmo;
  - a UF e a modalidade, como categorias;
  - a Selic, como na decisão 2.
- **Sem vazamento:** em cada origem do backtest, o modelo treina só com meses até ela, e o alvo de todo exemplo de treino também está antes dela.

### 4. Hiperparâmetros fixos, sem ajuste

Os hiperparâmetros são conservadores e foram fixados antes da primeira execução. Não são ajustados em nenhuma janela:
- 300 árvores, com taxa de aprendizado de 0,03;
- até 15 folhas e profundidade 4;
- pelo menos 40 exemplos por folha;
- 80% das variáveis por árvore e regularização L2 de 1;
- semente 27, uma thread e modo determinístico, para a execução se repetir igual.

### 5. A faixa de 80% vem dos erros do próprio modelo fora da amostra

Previsões de quantis não se somam entre células. Por isso, a faixa de cada série sai dos erros relativos do LightGBM nessa série, nas origens que ele não viu ao treinar:
- **Avaliação:** a faixa vai até o erro que o modelo não passou em 80% das 12 origens da janela de escolha, em cada horizonte, para os dois lados.
- **Projeção:** mesma conta, com as 16 origens.

São 12 erros por horizonte, e o quantil de 80% sai aproximado. A cobertura na janela de avaliação mostra se a faixa ficou estreita.

### 6. O LightGBM é o quinto candidato, com a mesma regra

O LightGBM disputa a escolha com os quatro candidatos do ADR 0023:
- **Mesmas origens:** as mesmas 12 origens de escolha e 4 de avaliação;
- **Mesma regra:** o menor MASE médio na escolha vence;
- **Desempate:** fica com o candidato mais simples, e o LightGBM é o menos simples.

Se ele não ganhar numa série, a tendência ou outro candidato continua, e o relatório mostra o confronto.

### 7. O arquivo dos testes, para a Tela 3

O gráfico do erro da Tela 3 mostra o que a projeção dizia num teste contra o que aconteceu. Para isso, o script grava `testes_da_projecao.json`: a previsão do modelo escolhido em cada origem da janela de avaliação, com a faixa e o realizado, por série e horizonte.

## Alternativas descartadas

- **Um LightGBM por série:** cerca de 20 exemplos por série, pouco para um modelo de árvores.
- **Só as 41 séries no treino:** menos exemplos que as 351 células, e o mesmo modelo ainda precisaria somar UFs e modalidades de jeitos diferentes.
- **Rede neural de séries temporais:** mais dado e mais tempo do que 31 meses sustentam.
- **Ajustar os hiperparâmetros por validação cruzada:** com 16 origens, o ajuste consumiria a janela de escolha e deixaria a comparação com os candidatos simples desigual.

## Consequências

- **A Q27 pode mudar.** A resposta de referência da Q27 é a deriva da carteira PJ do país, em SQL (ADR 0023, decisão 6). Um LightGBM não cabe em SQL portátil ([ADR 0015](0015-gabarito-com-leituras-aceitas-em-sql-portatil.md)). Se ele vencer no Brasil, a tela e o gabarito passam a ter números diferentes, e o Yuri decide se a Q27 ganha errata ou continua com a deriva.
- **As projeções das séries não somam entre si.** O Brasil pode usar um modelo e cada UF outro, como já acontecia com o ADR 0023. A tela não convida a somar.
- **Nova dependência:** o `lightgbm`, no `pyproject.toml`. O modelo é treinado pela API nativa, sem o scikit-learn.

## Resultado

A execução contra o mart, em 2026-10-06, com data-base 2026-07-31, está em [`docs/previsao.md`](../previsao.md). Duas execuções seguidas gravaram arquivos idênticos. Em resumo:
- **Escolhidos:** o LightGBM em 15 séries, a deriva em 12, o Holt amortecido em 7, o ingênuo em 6 e o ingênuo sazonal em 1.
- **Brasil:** o LightGBM venceu a escolha por pouco, com MASE médio de 1,15 contra 1,17 da deriva. Na avaliação, errou 0,4%, 0,5% e 1,1% a 1, 2 e 3 meses, contra 0,9%, 0,7% e 0,9% da deriva. A faixa cobriu os 12 casos.
- **Nas 41 séries, na avaliação:** o LightGBM teve MASE médio menor que a deriva em 21 e menor que o ingênuo em 24.
- **Importância das variáveis no treino final:** as variações recentes somam 53%, o tamanho 13%, o mês do ano 10%, a modalidade 10%, a UF 8% e a Selic 6%.
- **A Q27 foi atingida:** o Brasil passou a usar o LightGBM, e a referência da Q27 é a deriva. A decisão é do Yuri.
