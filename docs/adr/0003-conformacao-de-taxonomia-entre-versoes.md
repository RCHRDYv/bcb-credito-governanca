# ADR 0003: Conformação de taxonomia entre as versões V1 e V2

**Status:** Aceito
**Data:** 2026-08-25

## Contexto

O SCR.data trocou de taxonomia de modalidades em 2025, e as duas versões **não compartilham nenhum valor**. A V1 usava uma agregação própria do relatório, organizada por produto e tipo de cliente ("PF - Cartão de Crédito", "PJ - Capital de Giro"). A V2 expõe a hierarquia oficial do Anexo 3 do documento 3040, em dois níveis (modalidade e submodalidade).

Isso cria o problema clássico de **conformação de dimensão através de quebra de taxonomia**, que em modelagem dimensional é um dos casos genuinamente difíceis. Qualquer análise que atravesse a quebra precisa de uma decisão explícita sobre como reconciliar, e decisões implícitas aqui produzem número errado de forma silenciosa.

O BCB publica uma tabela oficial de equivalência (`Equivalencia_Modalidades.xlsx`), o que dispensa inferência. Ela tem três abas, separadas por tipo de cliente e, para pessoa jurídica, por tipo de origem dos recursos.

## Investigação que precedeu a decisão

Antes de escolher a abordagem, foi medida a ambiguidade real da correspondência, em vez de assumida.

**Dados extraídos da tabela oficial:** 222 linhas de correspondência, 16 modalidades V1, 13 modalidades V2, 76 submodalidades distintas.

**Espalhamento na direção V1 para V2:** severo. "PF - Outros Créditos" atravessa 12 das 13 modalidades da V2. "PJ - Financiamento de Infraestrutura/Desenvolvimento" com recursos direcionados também atravessa 12.

**Ambiguidade na direção V2 para V1: zero.** Nenhuma submodalidade mapeia para mais de uma modalidade V1 dentro do mesmo recorte de cliente e origem.

Esse resultado é o que torna a decisão possível, e por isso a verificação veio antes da escolha.

## Decisão

**A conformação acontece na direção V2 para V1, por lookup determinístico.**

A chave é a tupla:

```
(modalidade_v2, submodalidade_v2, cliente, origem) -> modalidade_v1
```

Como a ambiguidade medida é zero, esse é um relacionamento **muitos-para-um**, o que significa:

- Join sem risco de fan-out, porque cada linha da fonte encontra no máximo uma correspondência
- Nenhum rateio, nenhuma estimativa, nenhum fator de alocação
- A série no padrão V1 é **reconstruída a partir do dado V2**, não estimada

A tabela de correspondência entra como **seed do dbt**, derivada da planilha oficial por script versionado, nunca digitada à mão.

**A direção inversa, V1 para V2, é declarada impossível e não será implementada.** O dado da V1 não tem submodalidade, então não há informação suficiente para desagregar. Qualquer tentativa exigiria rateio, e rateio transformaria fato em estimativa sem sinalizar isso ao consumidor.

**Validade temporal é parte da chave.** As Cartas Circulares 3.617/2013, 3.773/2016, 3.806/2017 e 3.817/2017 incluíram, excluíram e renomearam submodalidades. A tabela publicada reflete o estado atual, então cada correspondência carrega o período em que é válida, no padrão de dimensão que muda lentamente (SCD Tipo 2).

## Alternativas descartadas

**Tabela ponte muitos-para-muitos.** Seria a escolha correta se houvesse ambiguidade real. Como a medição mostrou zero, a ponte só acrescentaria risco de dupla contagem para quem fizesse join sem entender a cardinalidade, sem nenhum ganho de fidelidade.

**Fatores de rateio para produzir série contínua nos dois sentidos.** Descartado por transformar fato em estimativa. Se alguém precisar da série V1 desagregada em V2, o correto é dizer que o dado não permite, e não entregar um número plausível cuja origem é uma suposição.

**Manter as duas séries separadas, sem conformação.** É a opção mais honesta e a menos útil. Foi descartada porque a conformação é possível sem perda na direção que importa, e recusá-la seria conservadorismo sem benefício.

**Descer ao nível atômico da submodalidade e reconstruir os dois agrupamentos por cima.** Conceitualmente elegante, mas o nível atômico também se move: as Cartas Circulares alteraram submodalidades. A decisão adotada incorpora o que essa alternativa tem de bom, através da validade temporal, sem depender da premissa falsa de que existe um nível estável.

## Consequências

**Positivas.** A série histórica no padrão V1 pode ser reconstruída a partir do dado V2 sem perda e sem estimativa. O join é seguro por construção. A tabela de correspondência é derivada de fonte oficial e regenerável por script.

**Negativas, e são reais.** A conformação só funciona em uma direção, o que precisa ser comunicado com clareza a quem consumir os marts, senão alguém vai tentar o caminho inverso. A validade temporal acrescenta complexidade ao modelo. E a correspondência depende de um arquivo XLSX publicado pelo BCB, que pode mudar de formato ou de endereço sem aviso, o que é uma dependência externa frágil.

**Mitigação da última:** a planilha baixada é versionada em cópia própria junto do script de extração, com a data de download registrada, de modo que uma mudança na origem seja detectável em vez de silenciosa.

## Nota de método

O ponto que decide este ADR não é a escolha da abordagem, é o fato de **a ambiguidade ter sido medida antes**. As três alternativas descartadas seriam defensáveis sob a suposição de que a correspondência era muitos-para-muitos, que era a suposição inicial. Ela estava errada, e só a medição mostrou isso.
