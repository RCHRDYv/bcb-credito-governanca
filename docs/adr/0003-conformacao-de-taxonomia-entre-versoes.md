# ADR 0003: Conformação de taxonomia entre as versões V1 e V2

**Status:** Aceito
**Data:** 2026-08-25

## Contexto

O SCR.data trocou de taxonomia de modalidades em 2025, e as duas versões **não compartilham nenhum valor**. A V1 usava uma agregação própria do relatório, organizada por produto e tipo de cliente ("PF - Cartão de Crédito", "PJ - Capital de Giro"). A V2 expõe a hierarquia oficial do Anexo 3 do documento 3040, em dois níveis (modalidade e submodalidade).

Isso cria o problema clássico de **conformação de dimensão diante de uma quebra de taxonomia**, que em modelagem dimensional é um dos casos genuinamente difíceis. Qualquer análise que atravesse a quebra precisa de uma decisão explícita sobre como reconciliar, e decisão implícita aqui produz número errado em silêncio.

O BCB publica uma tabela oficial de equivalência (`Equivalencia_Modalidades.xlsx`), o que dispensa inferência. Ela tem três abas, separadas por tipo de cliente e, para pessoa jurídica, por tipo de origem dos recursos.

## Investigação que precedeu a decisão

Antes de escolher a abordagem, a ambiguidade real da correspondência foi medida, em vez de suposta.

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

**Negativas, e são reais.** A conformação só funciona em uma direção, o que precisa ser comunicado com clareza a quem consumir os marts, senão alguém vai tentar o caminho inverso. A validade temporal acrescenta complexidade ao modelo. A correspondência também depende de um arquivo XLSX publicado pelo BCB, que pode mudar de formato ou de endereço sem aviso, e essa é uma dependência externa frágil.

**Mitigação da última:** a planilha em si não entra no repositório, porque é dado bruto (ADR 0001). O que entra é o seed gerado a partir dela, versionado, mais o script que o gera. Uma mudança na origem fica detectável de duas formas: o script falha quando um nome da planilha não casa mais com o rótulo do dado, e qualquer alteração de conteúdo aparece como diff no seed quando ele é regerado.

## Atualização de 2026-09-21: universo diferente

A ingestão mostrou que **a carteira ativa da V2 é de 3,95% a 5,94% maior que a da V1** em todos os 31 meses em que as duas coexistem (`docs/analise-v1-v2.md`, seção 6). A decisão deste ADR continua de pé para o que ela resolve, a **classificação**: o lookup V2 para V1 segue determinístico e sem fan-out. Já "reconstruir a série V1 a partir da V2 sem perda" vale para a taxonomia, não para os valores. A série reconstruída tem a classificação da V1 aplicada ao universo da V2, e não reproduz os totais que a V1 publicou. Todo mart que usar a conformação precisa dizer isso.

## Atualização de 2026-09-24: a divergência não é uniforme, e isso é mais grave

Com a camada intermediária pronta, a comparação foi feita modalidade por modalidade, e não só no total (`docs/analise-v1-v2.md`, seção 6). **Quatorze das dezesseis modalidades da V1 ficam entre 0% e 8,3% acima do publicado, e duas fogem: "PJ - Comércio exterior" com +17,1% e "PJ - Outros créditos" com +82,7%.**

No caso extremo, a submodalidade 0299, "Outros empréstimos", sozinha põe R$ 226,2 bi em "PJ - Outros créditos", mais que a modalidade inteira publicada pela V1 no mês. Todas essas linhas vêm da tabela oficial, com `regra = base`, sem inferência do projeto.

Isso não invalida a decisão, e refina o alcance dela: **a tabela de equivalência é correspondência de taxonomia, não receita para reproduzir agregado publicado.** A consequência prática para os marts é que a ressalva deixa de ser um número global de 4% a 6% e passa a ser por modalidade, com duas delas incomparáveis na prática. Onde a V1 classificava essas operações é pergunta aberta na issue #19.

## Atualização de 2026-09-22: o que apareceu ao gerar o seed

A extração da planilha oficial confirmou a parte central da decisão e acrescentou três limites que a investigação original não tinha visto. Seed em `dbt/seeds/correspondencia_modalidade_v2_v1.csv`, gerado por `scripts/gerar_seed_correspondencia.py` e verificado por `scripts/validar_correspondencia.py`.

**Confirmado:** ambiguidade zero dentro de cada aba, agora medida pelo código da submodalidade, e não pelo nome. As 16 modalidades da V1 que aparecem no dado são exatamente as 16 citadas pela planilha, e cada um dos 199 recortes distintos do dado da V2 encontra uma linha do seed.

**Limite 1: a chave da planilha não é só (submodalidade, cliente, origem).** A aba `OutrasInformacoes` traz dois tratamentos adicionais:

| Tratamento | Regra | Efeito |
|---|---|---|
| 1 | Submodalidades 0202 e 0203 com cliente PJ usam a modalidade **PF** | Aplicável. São 4 linhas do seed, e no dado essas combinações existem: 17 linhas em 0202 e 253 em 0203 |
| 2 | Submodalidades 0401, 0407, 0701, 1201, 1206 e 1207 com cliente PJ usam a modalidade PF **somente se a Natureza da operação for 4** | **Não aplicável com o dado publicado.** O SCR.data não traz o campo Natureza |

A Natureza 4 do Anexo 2 é "operações adquiridas em negociação com pessoa integrante do SFN com retenção substancial de risco". Na prática, é o caso em que o cliente informado é a empresa cedente, mas a operação é de varejo. A V1 reclassificava isso; o dado publicado não permite reproduzir a reclassificação.

**Quanto isso pesa:** 2,71% da carteira, em 295.134 linhas, cai em recortes onde a modalidade V1 depende da Natureza. O seed registra as duas candidatas, em `modalidade_v1` e `modalidade_v1_alternativa`, com `ambiguidade = natureza_nao_publicada`. Nenhuma das duas é escolhida em silêncio.

**Limite 2: a planilha oficial é incompleta.** Para cliente PF, as submodalidades 1303 (títulos e créditos a receber) e 1399 (outros com característica de crédito) não aparecem em nenhuma aba, e o dado tem linhas nas duas: 0,02% da carteira, em 120.177 linhas. O seed traz essas linhas com `modalidade_v1` vazia e a inferência do projeto em coluna separada, `modalidade_v1_inferida`, marcada como tal.

**Limite 3: a validade temporal deixa de importar no recorte atual.** Todas as inclusões, exclusões e renomeações de submodalidade documentadas na planilha são de 2014 a 2017, anteriores ao recorte do projeto, que começa em 2024. A única mudança de agrupamento sem data declarada é a da submodalidade 0440 (nota "e"). Por isso o seed é de versão única, com a ressalva registrada, em vez de dimensão que muda lentamente. A estrutura SCD Tipo 2 volta a ser necessária se o recorte retroceder a 2017 ou antes.

## Nota de método

O ponto que decide este ADR não é a escolha da abordagem, é o fato de **a ambiguidade ter sido medida antes**. As três alternativas descartadas seriam defensáveis sob a suposição de que a correspondência era muitos-para-muitos, que era a suposição inicial. Ela estava errada, e só a medição mostrou isso.
