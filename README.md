# Governança de dados e consumo por IA: um estudo com dados de crédito do Banco Central

**Quanto uma camada semântica e uma ontologia melhoram a acurácia de um LLM ao responder perguntas de negócio sobre dado corporativo real?**

*How much do a semantic layer and an ontology improve an LLM's accuracy when answering business questions over real enterprise data?*

> **Status:** v0.1 em construção. Este aviso será substituído por resultados conforme cada versão for publicada.

---

## O problema

Toda empresa que tenta colocar IA sobre seus próprios dados esbarra na mesma parede: o modelo não erra por falta de capacidade, erra por falta de contexto. Nome de coluna críptico, valor sentinela não documentado, taxonomia que mudou no meio da série, duas métricas parecidas com definições regulatórias diferentes. O dado está lá, mas o significado não.

Este projeto mede esse efeito com dado público real, e com método que qualquer pessoa pode auditar e reproduzir.

## O que este projeto é, e o que não é

**Não é** descoberta científica. O efeito de metadado sobre acurácia de text-to-SQL já está estabelecido na literatura (ver `docs/referencias.md`) e já é premissa de produtos comerciais como Databricks Genie, Snowflake Cortex Analyst e a camada semântica do dbt.

**É** uma demonstração transparente desse efeito em domínio novo: dado regulatório brasileiro, em português, com deriva de taxonomia verdadeira e documentada. Replicação em contexto real, com método aberto.

## Por que os dados do SCR

O [SCR.data](https://dadosabertos.bcb.gov.br/dataset/scr_data) do Banco Central publica a carteira de crédito do sistema financeiro nacional, mensalmente, com recorte por UF, modalidade, porte, setor e tipo de cliente.

Três características o tornam ideal para este estudo:

1. **A bagunça é real e não foi plantada.** Valor sentinela `-1` para supressão por sigilo estatístico, delimitador `;` dentro de campo entre aspas, vírgula decimal em texto, codificação latin-1, e duas métricas distintas com nomes parecidos (`carteira_inadimplencia` e `ativo_problematico`).
2. **A taxonomia mudou de verdade.** Há quebra metodológica documentada entre a Versão 1 (descontinuada em junho de 2025) e a Versão 2, com PDFs oficiais explicando cada uma. Isso permite testar a pergunta mais difícil do conjunto: como uma mudança de classificação afeta a comparabilidade da série histórica.
3. **O significado é auditável na fonte.** A ontologia deste projeto é destilada dos normativos oficiais do BCB, não inventada. Cada definição cita o documento de origem.

## Arquitetura

```
Fonte oficial (ZIP anual, ~97 MB por mês de CSV)
        ↓  ingestão em Python
Databricks (Delta / Unity Catalog)
        ↓  dbt: staging → intermediate → marts
Camada semântica + ontologia versionada
        ↓
   ┌────┴────┐
Dashboard   Interface de IA + avaliação medida
(estático)  (com e sem ontologia)
```

**Decisão de desenho central:** a dimensão de modalidade não é escrita à mão no dbt, ela é **gerada a partir de `ontology/modalidades.yml`**. A ontologia é fonte do modelo, não documentação sobre ele. Assim, divergência entre documentação e dado se torna estruturalmente impossível.

As decisões de arquitetura e suas alternativas descartadas estão registradas em `docs/adr/`.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `ingestion/` | Download e parse das fontes oficiais |
| `ontology/` | Ontologia, glossário e contratos de dados, com citação normativa |
| `dbt/` | Camada semântica: staging, intermediate, marts, testes |
| `evaluation/` | Perguntas de negócio, gabarito e análise estatística |
| `dashboard/` | Visualização estática |
| `scripts/` | Utilitários e verificadores |
| `docs/adr/` | Registro de decisões de arquitetura |

### Documentação

| Documento | O que traz |
|---|---|
| [Especificação](docs/especificacao.md) | Arquitetura, esquema da fonte, camadas do dbt, desenho do experimento |
| [Referências](docs/referencias.md) | Literatura e premissa de mercado que sustentam a tese |
| [Desenvolvimento com IA](docs/desenvolvimento-com-ia.md) | Contabilidade honesta do processo, incluindo os erros da IA e como foram pegos |
| [ADR 0001](docs/adr/0001-credenciais-e-dado-bruto-fora-do-repositorio.md) | Credenciais e dado bruto fora do repositório |
| [Perguntas do experimento](evaluation/questions.yml) | As 30 perguntas, pré-registradas antes de qualquer execução |

## Segurança

Repositório público tem duas propriedades que mudam o cálculo de risco: qualquer pessoa lê, e **o histórico do git é permanente**. Apagar um segredo do arquivo não o remove do histórico.

**Nenhuma credencial existe neste repositório, em nenhum commit.** A autenticação no Databricks usa OAuth, então nenhum token é sequer gerado. O `profiles.yml` real vive em `~/.dbt/`, fora do projeto, e o repositório publica apenas um `.example` com placeholders.

**Três camadas de defesa, porque uma só é frágil:**

| Camada | O que faz | Por que não basta sozinha |
|---|---|---|
| `.gitignore` | Cobre o caso normal | Contornável por engano com `git add -f` |
| Hooks de pre-commit | `gitleaks`, detecção de chave privada, bloqueio de arquivo grande, e verificador próprio de dado bruto | Depende de quem clona ter instalado os hooks |
| CI no GitHub Actions | Roda os mesmos verificadores no servidor | Não depende da máquina de ninguém |

O verificador de dado bruto (`scripts/check_no_raw_data.py`) foi testado contra violação real, não apenas assumido como funcional.

O raciocínio completo, com as alternativas descartadas, está em [`docs/adr/0001`](docs/adr/0001-credenciais-e-dado-bruto-fora-do-repositorio.md).

## Notas de honestidade

**Sobre o volume:** cada CSV mensal tem cerca de 97 MB. O conjunto de 2024 a 2026 chega a vários gigabytes e dezenas de milhões de linhas. O uso de Databricks é justificado pelo volume, não é vitrine.

**Sobre o desenvolvimento com IA:** este projeto foi construído com assistência de IA, e isso está documentado em `docs/desenvolvimento-com-ia.md`, incluindo o que foi acelerado, o que exigiu julgamento humano e onde a IA errou e foi corrigida. Um projeto sobre habilitar IA no negócio deveria ser transparente quanto a isso.

**Sobre o experimento:** as perguntas de avaliação são registradas antes de qualquer execução, para evitar seleção a posteriori. As limitações metodológicas conhecidas estão declaradas junto dos resultados.

---

# English

**Question:** how much do a semantic layer and an ontology improve an LLM's accuracy when answering business questions over real enterprise data?

This is a **demonstration, not a discovery**. The effect of metadata on text-to-SQL accuracy is established in the literature and already underpins commercial products. What this project adds is a transparent, auditable replication in a new domain: Brazilian regulatory credit data, in Portuguese, with genuine and officially documented taxonomy drift.

The dataset is the Brazilian Central Bank's credit registry (SCR), published monthly with breakdowns by state, credit modality, company size, sector and client type. It was chosen because its messiness is real rather than manufactured: undocumented sentinel values, delimiters inside quoted fields, Brazilian decimal notation, latin-1 encoding, and two similarly named metrics with different regulatory definitions.

The ontology is distilled from the Central Bank's own official normative documents, with each definition citing its source, rather than authored from scratch. The modality dimension is generated from the versioned ontology file rather than hand-written in dbt, which makes drift between documentation and data structurally impossible.

Architecture decisions and their discarded alternatives are recorded in `docs/adr/`. Methodological limitations are declared alongside results.

## License

MIT
