# Referências

PT: Este projeto é uma **demonstração**, não uma descoberta. O efeito que ele mede já está estabelecido na literatura e já é premissa de produtos comerciais. Esta página existe para deixar isso explícito e para dar ao leitor as fontes que sustentam a tese.

EN: This project is a **demonstration**, not a discovery. The effect it measures is already established in the literature and already underpins commercial products. This page exists to make that explicit and to give the reader the sources behind the thesis.

## Literatura

### BIRD-SQL

O benchmark mais relevante para esta tese, porque foi construído justamente sobre a constatação de que modelos falham em bases reais e sujas sem conhecimento externo de domínio.

O BIRD reúne 12.751 pares de pergunta e SQL sobre 95 bases de dados e, diferentemente de benchmarks anteriores, mantém os valores no formato original e frequentemente "sujo" com que foram coletados. Ele introduziu explicitamente o conceito de **evidência de conhecimento externo**, uma frase de contexto por pergunta que explica o que um campo significa no negócio.

**O número que importa para este projeto:** o GPT-4 atinge **54,89%** de acurácia de execução no conjunto de teste quando recebe a evidência de conhecimento externo curada, e cai para **34,88%** sem ela.

São 20 pontos percentuais de diferença, atribuíveis exclusivamente a metadado semântico. É exatamente o efeito que este projeto replica em domínio brasileiro.

- Site do benchmark: https://bird-bench.github.io/
- Artigo: https://arxiv.org/abs/2305.03111

### Spider

Benchmark anterior de text-to-SQL, com bases mais limpas e normalizadas. Vale como contraste: a diferença de desempenho dos modelos entre Spider e BIRD é, em boa medida, a diferença entre dado de laboratório e dado real.

### Ruído em benchmarks de text-to-SQL

Existe trabalho que examina o efeito de ruído e ambiguidade dentro do próprio BIRD, o que reforça que qualidade de metadado e qualidade de anotação são variáveis de primeira ordem, não detalhe.

- https://arxiv.org/abs/2402.12243

### Camada semântica medida em protocolo pareado

O trabalho mais próximo do desenho deste projeto, com outro conjunto de dados. Três modelos de fronteira responderam 100 perguntas sobre uma base analítica, cada um duas vezes: só com o esquema, e com o esquema mais um documento de 4 KB descrevendo medidas e convenções.

**Os números:** de 45,5% a 50,5% de acerto só com o esquema, contra 67,7% a 68,7% com o documento semântico. O estudo mede acurácia e alucinação juntas.

- https://arxiv.org/abs/2604.25149

### Confiabilidade e abstenção: TrustSQL

O TrustSQL propõe pontuar text-to-SQL pela capacidade de **se abster** quando a pergunta não é respondível com o dado, penalizando resposta errada em vez de tratá-la como empate. É a origem do campo `tipo_de_acerto: abstencao` no conjunto v2 das perguntas deste projeto.

- https://arxiv.org/abs/2403.15879

### Por que o modelo prefere chutar a dizer que não sabe

Duas linhas de trabalho explicam o comportamento que aparece quando um modelo responde com confiança sobre dado que não entende:

- **Incentivo de avaliação.** As avaliações dão zero para "não sei" e ponto para acerto, então o chute confiante pontua melhor que a dúvida honesta. https://arxiv.org/abs/2509.04664
- **Bajulação.** Treino por preferência humana favorece a resposta que agrada quem pergunta, inclusive quando isso significa abandonar a resposta correta. https://arxiv.org/abs/2310.13548

Elas não são o objeto deste projeto, que mede efeito de metadado, mas explicam por que um erro de interpretação costuma vir com aparência de segurança. É o motivo pelo qual o gabarito trata reconhecimento de limite como acerto.

## Premissa de mercado

A indústria já concluiu que LLM sobre esquema cru não funciona de forma confiável. Produtos construídos sobre essa premissa:

| Produto | Premissa |
|---|---|
| **Databricks Genie** | Espaço curado por domínio, com instruções e exemplos, entre o modelo e o dado |
| **Snowflake Cortex Analyst** | Modelo semântico declarado em YAML como camada obrigatória |
| **dbt Semantic Layer / MetricFlow** | Métricas definidas uma vez, consumidas por ferramentas e agentes |

O padrão é o mesmo nos três: ninguém aponta o modelo direto para as tabelas.

## O que este projeto acrescenta

O resultado não é novo. O que o projeto acrescenta é:

1. **Replicação em domínio novo**: dado regulatório brasileiro, em português, publicado por um banco central
2. **Deriva de taxonomia verdadeira**: a quebra metodológica entre as Versões 1 e 2 do SCR, documentada oficialmente, permite testar o efeito num caso que benchmarks sintéticos não capturam
3. **Ontologia derivada de fonte oficial**, não autoral, o que remove a circularidade de quem escreve a ontologia e o gabarito ao mesmo tempo
4. **Método aberto e auditável**: perguntas pré-registradas, gabarito calculado por SQL, teste estatístico declarado

## Nota sobre verificação

PT: Todos os números citados aqui foram verificados na fonte antes de entrar nesta página, incluindo os acrescentados em 2026-09-22. Nenhuma métrica neste documento foi reproduzida de memória.

EN: Every figure cited here was verified at the source before entering this page, including those added on 2026-09-22. No metric in this document was reproduced from memory.
