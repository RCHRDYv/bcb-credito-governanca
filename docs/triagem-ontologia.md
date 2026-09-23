# Triagem da ontologia: o que precisa de decisão humana

**Data:** 2026-08-25
**Objetivo deste documento:** tornar a revisão possível de verdade.

## Atualização: o que foi decidido

As quatro decisões do Bloco 1 foram tomadas em 2026-09-21, e os dois achados do Bloco 3 foram investigados. O registro completo está em [`cadeia-normativa.md`](cadeia-normativa.md). **O texto abaixo fica como estava**, para registrar como a decisão foi apresentada na época.

| Item | Decisão, e o que aconteceu depois |
|---|---|
| 1.1 Sentinela `-1` | Testar empiricamente. O teste foi feito e **refutou** a hipótese herdada da V1: o critério de supressão não é o número de operações ([`sentinela-numero-de-operacoes.md`](sentinela-numero-de-operacoes.md)) |
| 1.2 "Outros créditos" | Segue tratado como balde de supressão, com a ressalva visível. Medido depois: 74,8% da modalidade é compra no cartão de crédito, e o componente genérico é 1,8% |
| 1.3 Recorte da série | De 2024 em diante |
| 1.4 Anexo 3 | Buscado. A ontologia de modalidades saiu das Instruções de Preenchimento do documento 3040, com a página citada em cada definição |
| 3.1 Rótulo duplo na planilha | Não é corrupção de formatação: é renomeação oficial registrada no histórico do leiaute |
| 3.2 76 contra 55 submodalidades | Resolvido em parte. A contagem certa é por par de modalidade e submodalidade: 66 pares e 56 rótulos no recorte de 2024 a 2026. A atribuição das ausentes continua pendente ([`cadeia-normativa.md`](cadeia-normativa.md), seção 3) |

---

Revisar 99 termos em YAML não acontece na prática. Este documento separa o que **exige decisão sua** do que você pode conferir por amostragem, para que a atenção fique onde ela muda o resultado.

---

## Bloco 1: exige decisão sua

Quatro itens. Nenhum tem resposta correta óbvia, e todos afetam análise.

### 1.1 O sentinela `-1`: publicar como inferência ou buscar confirmação?

**Situação.** A metodologia V2 não documenta o valor `-1` em `numero_de_operacoes`. A inferência de que significa supressão vem da V1, que declarava o limiar de 15 operações e usava o rótulo `<= 15`.

**A decisão.** Três caminhos:

| Opção | O que ganha | O que custa |
|---|---|---|
| Publicar como `inferido`, citando a V1 | Honesto, rápido, já documentado | Fica uma incerteza no centro de uma coluna usada em várias perguntas |
| **Testar empiricamente** | Evidência própria: verificar se linhas com `-1` têm carteira sistematicamente menor que linhas com contagem | Custa um script, mas é barato |
| Perguntar ao BCB | Resposta definitiva e citável | Depende de terceiro e de prazo indefinido |

**Minha recomendação:** a segunda. Se as linhas com `-1` tiverem distribuição de carteira compatível com poucas operações, a inferência passa de `inferido` para `inferido com evidência`, o que é bem mais defensável. É o tipo de verificação que o projeto inteiro defende.

### 1.2 "Outros créditos" ainda é balde de supressão?

**Situação.** A metodologia V1 avisava, na introdução, que agregações com poucas operações são agrupadas em "Outros Créditos", e que por isso o total dessa modalidade não representa o total dela no Sistema Financeiro. **Esse aviso não existe na V2.**

**Por que importa.** "Outros créditos" é **10,42% da carteira ativa** em junho de 2026. Se a regra continua valendo, essa fatia está inflada por supressão, e qualquer ranking por modalidade está distorcido.

**A decisão.** A remoção do aviso significa que a regra mudou, ou apenas que deixou de ser comunicada?

| Opção | Consequência |
|---|---|
| Tratar como ainda válido e avisar o usuário | Conservador. Adiciona ressalva a toda análise por modalidade |
| Tratar a remoção como mudança real | Arriscado. Se a regra continua valendo, a análise fica errada em silêncio |
| Registrar as duas leituras e sinalizar como não resolvido | Honesto, e transfere a decisão para quem consome |

**Minha recomendação:** a terceira, com a ressalva visível no mart, e não só na documentação. Mas essa é uma decisão de domínio e você tem mais repertório de crédito que eu.

### 1.3 Até onde a série histórica vai?

**Situação.** A série começa em junho de 2012. Entre lá e hoje há, no mínimo: mudança de limiar de valor em junho de 2016, quatro Cartas Circulares alterando submodalidades (2013, 2016, 2017 duas vezes), mudança de definição do ativo problemático em janeiro de 2025, e a troca de taxonomia V1 para V2 em 2025.

**A decisão.** Cada ano a mais multiplica o trabalho de conformação.

| Recorte | Quebras a tratar | Esforço |
|---|---|---|
| 2024 em diante | Apenas ativo problemático (jan/2025) e V1 para V2 | Baixo |
| 2017 em diante | Acrescenta duas Cartas Circulares | Médio |
| 2012 em diante, a série completa | Todas | Alto |

**Minha recomendação:** começar em 2024, publicar a v0.1, e estender depois se fizer sentido. O experimento não precisa de série longa para funcionar, e série longa é onde o projeto pode empacar.

### 1.4 Ir atrás do Anexo 3 do documento 3040?

**Situação.** As definições das 13 modalidades e das submodalidades **não estão nas metodologias**. Ambas remetem ao Anexo 3 do Leiaute do documento 3040, um nível abaixo. A pergunta Q17 do experimento, sobre garantia real, também depende disso.

**A decisão.** Buscar esse documento ou trabalhar sem ele?

**Minha recomendação:** buscar. É a maior lacuna restante, e sem ele a ontologia de modalidades fica só com rótulos, sem definição. Mas é trabalho adicional e você decide se entra na v0.1 ou fica para a v0.2.

---

## Bloco 2: confira por amostragem, se quiser

Tudo em `ontology/metricas.yml` marcado como `verbatim` é transcrição literal, com seção citada. Você pode abrir o PDF e conferir qualquer uma em segundos.

**As três que eu conferiria, se fosse conferir só três:**

1. `carteira_inadimplencia`, seção 3.x da V2, contra a seção 4.u da V1. É a afirmação de que as definições são idênticas, que é a base de dizer que a série é contínua
2. `ativo_problematico`, seção 2.d, o trecho sobre janeiro de 2025
3. O aviso de "Outros créditos" na introdução da V1

---

## Bloco 3: achados que precisam do seu olho de domínio

### 3.1 Rótulo corrompido na planilha oficial

A célula da planilha do BCB traz `PJ - Capital de Giro Rotativo PJ - Cheque Espe...`, aparentemente **duas modalidades concatenadas numa célula só**. No dado da V1 elas aparecem separadas: "PJ - Capital de giro rotativo" e "PJ - Cheque especial e conta garantida".

Provavelmente é erro de formatação na fonte oficial. Preciso decidir como tratar, e a decisão afeta duas linhas do mapeamento.

### 3.2 Divergência de contagem de submodalidades

A planilha de equivalência tem **76** submodalidades distintas. O dado de junho de 2026 tem **55**.

Hipóteses: submodalidades que existem no leiaute mas não tiveram operação no mês, ou que foram descontinuadas por Carta Circular e permanecem na planilha por referência histórica. Precisa ser verificado antes de a ontologia afirmar qualquer coisa.

---

## O que já está pronto e não precisa de você

| Artefato | Estado |
|---|---|
| `ontology/metricas.yml` | Completo, com todas as medidas e os avisos verificados |
| Decisão de conformação V1 para V2 | ADR 0003, com a ambiguidade medida antes da escolha |
| Respostas às cinco perguntas abertas | `docs/leitura-normativos.md` |
| Análise da quebra entre versões | `docs/analise-v1-v2.md` |

## O que falta, e depende das decisões acima

| Artefato | Bloqueado por |
|---|---|
| `ontology/modalidades.yml` | Item 1.4, definições estão no Anexo 3 |
| `ontology/submodalidades.yml` | Itens 1.4 e 3.2 |
| Seed da correspondência V1 para V2 | Item 3.1, e o recorte temporal do item 1.3 |
| `ontology/contratos.yml` | Depende dos anteriores |

---

## Resumo em uma linha

**Quatro decisões suas destravam o resto.** As duas de maior impacto são "Outros créditos" (item 1.2), porque afeta 10% da carteira e várias perguntas do experimento, e o recorte temporal (item 1.3), porque define o tamanho do projeto.
