# ADR 0005: O projeto termina numa recomendação, com a fronteira do dado declarada

**Status:** Aceito
**Data:** 2026-09-22

## Contexto

Até aqui o projeto tinha uma pergunta só, de método: quanto uma camada semântica e uma ontologia melhoram a acurácia de um LLM sobre dado real. É uma boa pergunta para quem avalia engenharia de dados e habilitação de IA.

Para quem avalia um analista de dados ou de BI, ela responde à pergunta errada. O avaliador quer saber se a pessoa pega um problema de negócio e chega a uma recomendação. Quem abrisse o repositório encontrava um estudo sobre IA, e não alguém que ajuda a decidir.

Ao mesmo tempo, o dado do SCR tem limites reais. Ele é agregado, público, sem taxa e sem receita. Qualquer recomendação construída sobre ele tem uma fronteira estreita, e ignorar essa fronteira produz o tipo de análise que não sobrevive a uma pergunta de gestor.

## Decisão

**O projeto passa a terminar numa recomendação de negócio, e a fronteira do dado é parte da entrega, não uma ressalva no fim.**

Em termos concretos:

1. A pergunta de negócio é onde crescer em crédito para pessoa jurídica e onde o risco está piorando. Ela é composta por perguntas que já estavam pré-registradas, então o experimento não é contaminado.
2. A recomendação sai de uma matriz de espaço contra risco, por UF e modalidade, e cada linha dela vem com o custo de errar.
3. Junto da recomendação vai a lista do que o dado **não** permite afirmar: rentabilidade, spread, comportamento de instituição específica, risco por cliente ou safra, contagem de operações onde há supressão, e comparação de ativo problemático através de janeiro de 2025.
4. O dashboard conta a decisão, uma pergunta por tela, em vez de expor indicadores soltos.
5. O experimento de IA passa a medir acerto **nas perguntas de que a decisão depende**, o que liga as duas metades do projeto.

## Alternativas descartadas

**Ficar apenas no descritivo, com dashboard de indicadores.** É o que a maioria dos projetos de portfólio faz, e é exatamente o que este projeto quer superar. Descartado porque não mostra julgamento, só ferramenta.

**Criar um projeto novo, separado, para a parte de decisão.** Descartado por três motivos: divide a atenção de quem avalia, exige repetir toda a infraestrutura, e a base do SCR já sustenta a pergunta. Profundidade num projeto vale mais que amplitude em cinco.

**Simular rentabilidade para fechar o caso de negócio.** Seria possível estimar spread por modalidade com dados externos e concluir onde a margem é maior. Descartado porque transforma a entrega em modelo com premissas inventadas, o que contradiz o princípio do projeto de não plantar o dado que depois se analisa. A fronteira declarada é mais valiosa que a conclusão completa.

**Esperar a v0.3 e o resultado do experimento antes de pensar em decisão.** Descartado porque a estrutura dos marts depende de saber qual decisão eles sustentam. Deixar para depois produziria marts desenhados para responder perguntas soltas.

## Consequências

**Positivas.** O projeto responde às duas perguntas que dois tipos de avaliador fazem, sem virar dois projetos. O dashboard passa a ter um propósito claro. E a fronteira do dado, escrita antes de qualquer resultado, protege a análise de conclusão que o dado não sustenta.

**Negativas, e são reais.** A previsão e o agrupamento de UFs acrescentam escopo, e por isso foram empurrados para a v0.2 em vez de entrar na v0.1. A recomendação depende de fonte externa para o número de empresas ativas por UF, o que acrescenta uma dependência de dado fora do BCB. E existe o risco de alguém ler a recomendação como consultoria, o que o próprio texto do dashboard precisa evitar.

## Nota

Esta decisão nasceu de uma revisão do repositório com foco em vaga de analista, e não de uma necessidade técnica. Está registrada como ADR porque muda o que o projeto entrega e o desenho dos marts, e porque as alternativas descartadas dizem mais sobre o critério do que a escolha em si.
