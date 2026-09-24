# Especificação do projeto

## Tese

Documentação de negócio estruturada e ontologia tornam dado corporativo confiável para consumo por IA, e **isso é mensurável**.

A pergunta central: uma IA consegue responder corretamente perguntas de negócio sobre crédito brasileiro a partir do dado cru do Banco Central? E quanto essa taxa de acerto muda quando existe uma camada semântica e uma ontologia derivada dos normativos oficiais?

**Posicionamento:** demonstração, não descoberta. Ver [`referencias.md`](referencias.md).

## Fonte de dados

Verificado em 2026-08-20. **O SCR.data não é uma API OData.** OData vale para as estatísticas do PIX, não para o SCR. A ingestão precisa lidar com dois tipos de fonte, o que é mais realista como engenharia.

### SCR.data: download de ZIP anual

| Recurso | URL |
|---|---|
| Dados V2 (atual, publicada também para anos anteriores a 2025) | `https://www.bcb.gov.br/pda/desig/scrdata_{ANO}.zip` |
| Dados V1 (legada, ainda publicada em 2026) | `https://www.bcb.gov.br/pda/desig/planilha_{ANO}.zip` |
| Metodologia V1 | `https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf` |
| Metodologia V2 | `https://www.bcb.gov.br/pda/desig/metodologia_versao2.pdf` |
| Tutorial | `https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/tutorial.pdf` |

**Cobertura verificada em 2026-09-21**, abrindo os arquivos em vez de acreditar na descrição do portal: as duas versões cobrem de janeiro de 2024 a julho de 2026 (a V2 existe também para 2023). O portal descreve a V1 como encerrada em junho de 2025, e o dado contradiz isso. O BCB também republica arquivos antigos sem aviso, o que a ingestão detecta pelo manifesto (ver [ADR 0004](adr/0004-ingestao-em-camada-bronze.md)).

**A quebra metodológica entre V1 e V2 é o achado que sustenta a pergunta mais difícil do experimento.** É um caso real, datado e oficialmente documentado de mudança de taxonomia afetando comparabilidade de série histórica. Os dois PDFs de metodologia são a documentação de negócio da qual a ontologia é destilada.

### Volume verificado

Medido na ingestão de 2026-09-21, de janeiro de 2024 a julho de 2026: 31 CSVs mensais por versão, de cerca de 100 MB (V2) e 300 MB (V1) cada, somando 12,7 GB descompactados e 1,5 GB compactados. São 9,7 milhões de linhas na V2 e 29,5 milhões na V1. A contagem exata por arquivo está em `ingestion/manifesto.json`.

### Esquema do SCR: 24 colunas

**Dimensões:** `data_base`, `uf`, `segmento`, `cliente`, `cnae_ocupacao`, `porte`, `modalidade`, `submodalidade`, `origem`, `indexador`

**Medidas:** `numero_de_operacoes`, seis faixas de `a_vencer_*`, `carteira_a_vencer`, `vencido_de_15_ate_90_dias`, `vencido_acima_de_90_dias`, `carteira_vencida`, `carteira_ativa`, `carteira_inadimplencia`, `ativo_problematico`

### Armadilhas confirmadas em amostra real

Todas verificadas no arquivo, e todas são material para a camada de staging e para o experimento:

1. **Sentinela `-1`** em `numero_de_operacoes`, marcando contagem não divulgada, por critério não publicado e que não é o limiar de 15 operações da V1 (ver [`sentinela-numero-de-operacoes.md`](sentinela-numero-de-operacoes.md)). Somar essa coluna sem tratar produz número sem sentido
2. **Delimitador dentro de campo entre aspas.** O arquivo usa `;` e há valores de `cnae_ocupacao` contendo `;`, por exemplo `"Comércio; reparação de veículos automotores e motocicletas"`
3. **Vírgula decimal** em formato brasileiro, com números vindo entre aspas como texto
4. **Codificação UTF-8 com BOM.** Ler com `utf-8-sig`. Ler com `latin-1` **não gera erro**, apenas corrompe silenciosamente todo acento, o que é o pior tipo de falha
5. **Espaços à direita nos valores**, que exigem `trim` antes de qualquer comparação ou junção. Medido em 2026-09-23: acontece em `porte` em todas as linhas da V1, e em `submodalidade` em 720.339 linhas da V2
6. **`carteira_inadimplencia` e `ativo_problematico` são colunas distintas**, com definição normativa diferente
7. **As faixas de vencimento somam `carteira_a_vencer`**, o que rende um teste de qualidade natural

### PIX: esse sim é OData

Portal: https://dadosabertos.bcb.gov.br/
Swagger: https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/swagger-ui3

## Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---|---|---|
| Fonte da verdade da ontologia | Arquivo YAML versionado | Evita deriva entre duas superfícies de autoria |
| Documentação para humano | Gerada do YAML, publicada com `dbt docs` | Público e navegável, sem exigir login |
| Dashboard consultando o banco | Não. Exportação estática de JSON | Credencial em JavaScript é pública. Dado mensal não precisa de tempo real |
| Onde a IA roda | Hugging Face Spaces | Databricks não serve aplicação pública |
| Credenciais | OAuth, nada em disco | Ver [ADR 0001](adr/0001-credenciais-e-dado-bruto-fora-do-repositorio.md) |

## Estrutura

```
├── ingestion/     Download e parse das fontes oficiais
├── ontology/      Ontologia, glossário e contratos, com citação normativa
├── dbt/           staging → intermediate → marts
├── evaluation/    Perguntas pré-registradas, gabarito, análise estatística
├── dashboard/     Visualização estática
├── scripts/       Utilitários e verificadores
└── docs/adr/      Decisões de arquitetura
```

## Camadas do dbt

**staging:** um modelo por fonte, relação um para um. Renomeia, converte tipo, trata sentinela. Zero regra de negócio.

**intermediate:** dimensões conformadas entre fontes com granularidade e código diferentes. É onde mora o trabalho real desta base.

**marts:** duas famílias, com papéis diferentes ([ADR 0007](adr/0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md)). O **esquema estrela** (`dim_tempo`, `dim_modalidade`, `dim_uf`, `dim_segmento`, `dim_porte`, `dim_cnae_ocupacao`, `fct_carteira` e o fato legado `fct_carteira_v1`) responde às perguntas e é o que a IA consulta no experimento. Os **marts de apresentação** (`mrt_carteira_mensal`, `mrt_reconciliacao_versoes`, `mrt_limites_do_dado`) são agregados no grão das telas do dashboard, com as taxas calculadas uma vez, e ficam fora do experimento porque pré-respondem perguntas.

**Decisão que prova a tese estruturalmente:** `dim_modalidade` não é escrita à mão, é gerada por seed a partir de `ontology/modalidades.yml`. A ontologia é fonte do modelo, não documentação sobre ele.

## Arquitetura de documentação

Sete artefatos, cada um com um público e uma origem versionada. A coluna de situação diz o que já existe, para a tabela não descrever como pronto o que ainda é plano:

| Artefato | Público | Origem | Situação |
|---|---|---|---|
| Problema de negócio | Qualquer leitor | README | Entregue |
| Glossário de negócio | Negócio | `ontology/modalidades.yml`, `ontology/dimensoes.yml`, `ontology/metricas.yml` | Entregue |
| Dicionário de dados | Técnico | Arquivos `_*.yml` do dbt | Entregue para staging e seeds |
| ADR | Técnico sênior | `docs/adr/` | Entregue, seis decisões |
| Linhagem | Ambos | Gerada pelo `dbt docs` | v0.2 |
| Contrato de dados | Consumidor | `ontology/contratos.yml` | v0.2 |
| Runbook | Operação | `docs/runbook.md` | v0.2 |

A publicação como site, estruturada segundo **Diátaxis** para separar tutorial, guia prático, referência e explicação, fica para a v0.2, junto do `dbt docs`.

**Modelo de ontologia:** três padrões complementares, decididos em [ADR 0002](adr/0002-modelo-de-ontologia-skos-datacube-xkos.md).

| Camada | Padrão | Papel |
|---|---|---|
| Vocabulário | **SKOS** | Conceito, esquema, hierarquia `broader`/`narrower`, definição, nota de escopo |
| Estrutura | **RDF Data Cube** (`qb:`) | Dimensões e medidas do cubo estatístico. Alinhado ao modelo SDMX usado por bancos centrais |
| Versionamento da classificação | **XKOS** | Correspondência entre as taxonomias V1 e V2, com tipo (exata, aproximada, mais ampla, mais restrita) |

**Autoria em YAML, emissão em RDF.** A fonte da verdade é YAML versionado, e o RDF é gerado por script. O motivo é que revisão humana sobre Turtle não acontece na prática, e revisão que não acontece é controle que não existe.

**OWL foi descartado** por não haver regra de inferência a derivar nesta taxonomia.

### Escopo da ontologia, levantado do dado antes de ler normativo

99 termos: 13 modalidades, 55 submodalidades (em 65 pares), 13 portes, 8 segmentos, 6 indexadores, 2 valores de cliente e 2 de origem.

**Medido depois, no recorte inteiro de 2024 a 2026:** são 56 rótulos distintos de submodalidade em 66 pares com a modalidade, e nenhum mês isolado tem os 66, porque dois pares ocorrem só em parte da série (ver `ontology/modalidades.yml`).

**Armadilha semântica já identificada:** a coluna `porte` mistura **duas taxonomias distintas**. Pessoa jurídica usa porte de empresa (Micro, Pequeno, Médio, Grande) e pessoa física usa faixa de renda em salários mínimos. Agrupar por `porte` sem filtrar `cliente` mistura categorias incompatíveis. Isso não está em lugar nenhum do esquema, e é exatamente o tipo de conhecimento que só a ontologia carrega. O mesmo vale para `cnae_ocupacao`, que é seção do CNAE para pessoa jurídica e natureza da ocupação para pessoa física.

## Camada de decisão

Acrescentada em 2026-09-22. Até aqui o projeto respondia "quanto a ontologia melhora a acurácia de um LLM", que é pergunta de método. Esta camada acrescenta a pergunta de negócio que o mesmo dado sustenta, e faz o projeto terminar numa recomendação em vez de terminar num número de acurácia.

### A pergunta de negócio

> **Uma financeira de médio porte quer crescer em crédito para pessoa jurídica. Em quais modalidades e em quais estados vale entrar ou aumentar exposição, e onde o risco está piorando rápido demais para isso?**

Ela não é nova no projeto: três perguntas pré-registradas em [`../evaluation/questions.yml`](../evaluation/questions.yml) já a compõem.

| Pergunta | O que entrega para a decisão |
|---|---|
| **Q14** | Onde há espaço: carteira de PJ por empresa ativa, por UF |
| **Q07** | Onde o risco está piorando: modalidades com maior deterioração de inadimplência em seis meses |
| **Q27** | Para onde a carteira aponta: projeção de três meses com intervalo |

O pré-registro não muda. A camada de decisão consome os marts e o gabarito, e o experimento com IA continua como está.

### O que entra na recomendação

1. **Indicador de espaço,** por UF e modalidade: carteira PJ por empresa ativa, comparada à mediana nacional. Exige fonte externa para o número de empresas ativas por UF, declarada junto.
2. **Indicador de risco,** por UF e modalidade: nível e tendência de inadimplência em seis meses, mais a distância entre ativo problemático e carteira inadimplida, que antecipa deterioração que o atraso ainda não mostra.
3. **Projeção** da carteira por recorte, com intervalo, usando modelo simples de série temporal com sazonalidade.
4. **Agrupamento de UFs** por perfil, combinando nível de crédito por empresa, tendência de risco e composição da carteira. Serve para tratar estados parecidos com a mesma estratégia.
5. **A recomendação,** numa matriz espaço contra risco: onde entrar, onde manter, onde não entrar. Cada recomendação vem com o custo de errar e com a fronteira do dado.

### A fronteira do dado, declarada junto da recomendação

O SCR.data é agregado e público. Com ele **é possível** dizer onde há menos crédito por empresa, onde a inadimplência piora e como a composição da carteira difere entre estados.

Com ele **não é possível** dizer:
- rentabilidade, spread ou custo de captação, porque o dado não tem taxa nem receita;
- comportamento de uma instituição específica, porque o dado é agregado por segmento;
- risco de um cliente ou de uma safra, porque não há informação por operação nem por data de contratação;
- número de operações em 26,7% das linhas, por causa da supressão não documentada ([`sentinela-numero-de-operacoes.md`](sentinela-numero-de-operacoes.md));
- comparação direta de ativo problemático entre dez/2024 e jan/2025, por causa da mudança de critério ([`cadeia-normativa.md`](cadeia-normativa.md)).

Declarar essa fronteira é parte da entrega. Uma recomendação sem ela é palpite com gráfico.

### O dashboard conta a decisão

Uma pergunta por tela, com o texto da conclusão junto do gráfico, e não uma galeria de indicadores:

1. Onde está o crédito PJ hoje, e onde ele é escasso por empresa
2. Onde o risco está piorando, com a distinção entre inadimplência e ativo problemático
3. Para onde a carteira aponta nos próximos três meses, com intervalo. **Movida para a v0.2 em 2026-09-24**, junto com a previsão da issue #27: a v0.1 conta a decisão sem ela, e a projeção só entra com backtest e erro publicado
4. A recomendação, com o custo de errar e o que o dado não permite afirmar

### Relação com o experimento de IA

As perguntas que sustentam a decisão são as mesmas do gabarito. Isso liga as duas metades do projeto: o experimento deixa de medir acurácia no abstrato e passa a medir **se a IA acerta justamente as perguntas de que a decisão depende.** Uma taxa alta de acerto em perguntas irrelevantes não vale nada, e essa ligação torna isso visível.

## Desenho do experimento

- **Condição A:** o modelo recebe apenas o esquema cru, sem descrição
- **Condição B:** esquema mais ontologia, descrições e regras de negócio
- **O que as duas condições consultam:** o esquema estrela da camada gold, e só ele. Os marts de apresentação ficam de fora, porque já trazem taxas e diferenças calculadas e desarmariam as armadilhas nas duas condições por igual ([ADR 0007](adr/0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md))
- **Métrica:** acerto da resposta final contra gabarito calculado por SQL
- **Teste:** McNemar, apropriado para dado binário pareado, com tamanho de efeito reportado

**O que conta como acerto, definido em 2026-09-22.** O conjunto v2 das perguntas ([`../evaluation/questions_v2.yml`](../evaluation/questions_v2.yml)) declara, por pergunta, o tipo de acerto esperado:

| Tipo | Acerto é |
|---|---|
| `valor` | Chegar ao número ou à lista certa |
| `valor_com_ressalva` | Chegar ao número **e** declarar o limite que o torna interpretável, como a quebra de janeiro de 2025 ou a supressão da contagem de operações |
| `abstencao` | Reconhecer que o dado não permite responder, e dizer o que faltaria |

Sem essa distinção, uma resposta numérica confiante sobre pergunta impossível contaria como acerto, ou o reconhecimento correto de um limite contaria como erro. O critério de penalizar resposta errada em vez de tratá-la como empate vem do TrustSQL (ver [`referencias.md`](referencias.md)).

**Três exigências de rigor, declaradas junto dos resultados:**

1. Perguntas **pré-registradas**, com data de registro anterior a qualquer execução: o conjunto original em [`../evaluation/questions.yml`](../evaluation/questions.yml), de 2026-08-20, preservado sem alteração, e o conjunto v2 em [`../evaluation/questions_v2.yml`](../evaluation/questions_v2.yml), de 2026-09-22, que vale para o experimento. O v2 mantém os 30 enunciados originais, corrige três notas erradas no campo `errata` e acrescenta 11 perguntas nascidas de achados posteriores
2. Temperatura zero, ou múltiplas execuções por pergunta com variância reportada
3. **No mínimo dois modelos** de níveis diferentes, para que o efeito não seja artefato de um modelo específico

A limitação de tamanho de amostra é declarada, não escondida.

## Ordem de execução

A ordem importa: perguntas antes de modelagem, porque são elas que determinam o que os marts precisam responder.

1. Registrar as perguntas de negócio
2. Destilar a ontologia dos normativos, citando fonte de cada definição
3. Ingestão
4. Modelos dbt com testes
5. Gabarito via SQL
6. Exportação estática e dashboard
7. Publicar

## Versões

| Versão | Escopo |
|---|---|
| **v0.1** | Ingestão, ontologia, dbt, gabarito, dashboard que conta a decisão |
| **v0.2** | `dbt docs` publicado, contratos de dados, emissão SKOS, previsão e agrupamento de UFs |
| **v0.3** | Camada de IA, suíte de avaliação, análise estatística |
| **v0.4** | LLMOps: versionamento de prompt, tracing, reavaliação automática mensal quando o BCB publica dado novo |
