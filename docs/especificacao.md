# Especificação do projeto

## Tese

Documentação de negócio estruturada e ontologia tornam dado corporativo confiável para consumo por IA, e **isso é mensurável**.

A pergunta central: uma IA consegue responder corretamente perguntas de negócio sobre crédito brasileiro a partir do dado cru do Banco Central? E quanto essa taxa de acerto muda quando existe uma camada semântica e uma ontologia derivada dos normativos oficiais?

**Posicionamento:** demonstração, não descoberta. Ver [`referencias.md`](referencias.md).

## Fonte de dados

Verificado em 2026-08-20. **O SCR.data não é uma API OData.** Isso vale para as estatísticas do PIX, não para o SCR. A ingestão lida com duas modalidades de fonte, o que é mais realista como engenharia.

### SCR.data: download de ZIP anual

| Recurso | URL |
|---|---|
| Dados V2 (atual) | `https://www.bcb.gov.br/pda/desig/scrdata_{ANO}.zip` |
| Dados V1 (descontinuada em jun/2025) | `https://www.bcb.gov.br/pda/desig/planilha_{ANO}.zip` |
| Metodologia V1 | `https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf` |
| Metodologia V2 | `https://www.bcb.gov.br/pda/desig/metodologia_versao2.pdf` |
| Tutorial | `https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/tutorial.pdf` |

**A quebra metodológica entre V1 e V2 é o achado que sustenta a pergunta mais difícil do experimento.** É um caso real, datado e oficialmente documentado de mudança de taxonomia afetando comparabilidade de série histórica. Os dois PDFs de metodologia são a documentação de negócio da qual a ontologia é destilada.

### Volume verificado

O ZIP de 2026 tem 86,57 MB comprimidos e contém seis CSVs mensais de aproximadamente 97 MB cada. O conjunto de 2024 a 2026 chega à casa de vários gigabytes e dezenas de milhões de linhas.

### Esquema do SCR: 24 colunas

**Dimensões:** `data_base`, `uf`, `segmento`, `cliente`, `cnae_ocupacao`, `porte`, `modalidade`, `submodalidade`, `origem`, `indexador`

**Medidas:** `numero_de_operacoes`, seis faixas de `a_vencer_*`, `carteira_a_vencer`, `vencido_de_15_ate_90_dias`, `vencido_acima_de_90_dias`, `carteira_vencida`, `carteira_ativa`, `carteira_inadimplencia`, `ativo_problematico`

### Armadilhas confirmadas em amostra real

Todas verificadas no arquivo, e todas são material para a camada de staging e para o experimento:

1. **Sentinela `-1`** em `numero_de_operacoes`, indicando supressão por sigilo estatístico. Somar essa coluna sem tratar produz número sem sentido
2. **Delimitador dentro de campo entre aspas.** O arquivo usa `;` e há valores de `cnae_ocupacao` contendo `;`, por exemplo `"Comércio; reparação de veículos automotores e motocicletas"`
3. **Vírgula decimal** em formato brasileiro, com números vindo entre aspas como texto
4. **Codificação latin-1**, não UTF-8
5. **`carteira_inadimplencia` e `ativo_problematico` são colunas distintas**, com definição normativa diferente
6. **Faixas de aging devem somar** para `carteira_a_vencer`, o que dá teste de qualidade natural

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

**marts:** modelo dimensional voltado a negócio. `dim_modalidade`, `dim_uf`, `dim_tempo`, `fct_carteira_credito`, `fct_inadimplencia`.

**Decisão que prova a tese estruturalmente:** `dim_modalidade` não é escrita à mão, é gerada por seed a partir de `ontology/modalidades.yml`. A ontologia é fonte do modelo, não documentação sobre ele.

## Arquitetura de documentação

Sete artefatos, todos gerados de fonte versionada:

| Artefato | Público | Origem |
|---|---|---|
| Problema de negócio | Qualquer leitor | README |
| Glossário de negócio | Negócio | `ontology/modalidades.yml` |
| Dicionário de dados | Técnico | `schema.yml` do dbt |
| Contrato de dados | Consumidor | `ontology/contratos.yml` |
| ADR | Técnico sênior | `docs/adr/` |
| Linhagem | Ambos | Gerada pelo `dbt docs` |
| Runbook | Operação | `docs/runbook.md` |

Site estruturado segundo **Diátaxis**, separando tutorial, guia prático, referência e explicação.

**Formalidade da ontologia:** o YAML é, tecnicamente, um vocabulário controlado. O projeto emite **SKOS/RDF como artefato gerado**, que é o padrão W3C para taxonomia, tornando o termo "ontologia" defensável sem o peso do OWL.

## Desenho do experimento

- **Condição A:** o modelo recebe apenas o esquema cru, sem descrição
- **Condição B:** esquema mais ontologia, descrições e regras de negócio
- **Métrica:** acerto da resposta final contra gabarito calculado por SQL
- **Teste:** McNemar, apropriado para dado binário pareado, com tamanho de efeito reportado

**Três exigências de rigor, declaradas junto dos resultados:**

1. Perguntas **pré-registradas** em [`../evaluation/questions.yml`](../evaluation/questions.yml), com data de registro anterior a qualquer execução
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
| **v0.1** | Ingestão, ontologia, dbt, gabarito, dashboard estático |
| **v0.2** | `dbt docs` publicado, contratos de dados, emissão SKOS |
| **v0.3** | Camada de IA, suíte de avaliação, análise estatística |
| **v0.4** | LLMOps: versionamento de prompt, tracing, reavaliação automática mensal quando o BCB publica dado novo |
