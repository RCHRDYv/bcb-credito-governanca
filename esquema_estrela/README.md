---
license: odbl
language:
  - pt
pretty_name: "Crédito no Brasil: esquema estrela do SCR.data com fontes externas"
tags:
  - finance
  - credit
  - brazil
  - central-bank
  - star-schema
  - duckdb
size_categories:
  - 1M<n<10M
configs:
  - config_name: fct_carteira
    data_files: data/fct_carteira.parquet
    default: true
  - config_name: fct_carteira_v1
    data_files: data/fct_carteira_v1.parquet
  - config_name: fct_empresas_ativas
    data_files: data/fct_empresas_ativas.parquet
  - config_name: fct_pix
    data_files: data/fct_pix.parquet
  - config_name: fct_populacao
    data_files: data/fct_populacao.parquet
  - config_name: fct_renda_do_trabalho
    data_files: data/fct_renda_do_trabalho.parquet
  - config_name: fct_selic
    data_files: data/fct_selic.parquet
  - config_name: dim_tempo
    data_files: data/dim_tempo.parquet
  - config_name: dim_modalidade
    data_files: data/dim_modalidade.parquet
  - config_name: dim_uf
    data_files: data/dim_uf.parquet
  - config_name: dim_segmento
    data_files: data/dim_segmento.parquet
  - config_name: dim_porte
    data_files: data/dim_porte.parquet
  - config_name: dim_cnae_ocupacao
    data_files: data/dim_cnae_ocupacao.parquet
  - config_name: dim_porte_receita
    data_files: data/dim_porte_receita.parquet
  - config_name: dim_natureza_juridica
    data_files: data/dim_natureza_juridica.parquet
---

# Crédito no Brasil: esquema estrela do SCR.data

O esquema estrela do projeto [bcb-credito-governanca](https://github.com/RCHRDYv/bcb-credito-governanca): a carteira de crédito do SCR.data do Banco Central, no grão em que o BCB publica, com dimensões e fatos externos do IBGE, do SGS, do Pix e do CNPJ. São as mesmas tabelas `dim_*` e `fct_*` que o dbt constrói no Databricks, exportadas em Parquet para consulta sem Databricks e sem credencial.

**Mês de referência:** julho de 2026 (2026-07-31). O retrato é fixado pela revisão deste dataset, registrada com o sha256 e os totais de cada arquivo em [`esquema_estrela/manifesto.json`](https://github.com/RCHRDYv/bcb-credito-governanca/blob/main/esquema_estrela/manifesto.json).

## Tabelas

| Tabela | Grão |
|---|---|
| `fct_carteira` | Um registro por recorte publicado na V2 do SCR.data: mês, UF, segmento, submodalidade, porte, atividade, tipo de cliente, origem e indexador. Só chaves e medidas |
| `fct_carteira_v1` | V1 do SCR.data, agregada por mês, UF, tipo de cliente, modalidade da V1 e origem |
| `fct_empresas_ativas` | Matrizes ativas no fim de cada mês, por UF, porte da Receita, grupo de natureza jurídica e MEI, reconstruídas de um retrato do CNPJ. Só contagens |
| `fct_pix` | Pix liquidado no SPI por mês, UF, lado (pagador ou recebedor) e tipo de cliente. É fluxo do mês |
| `fct_populacao` | População residente estimada por UF e ano (IBGE) |
| `fct_renda_do_trabalho` | Rendimento médio e massa de rendimento do trabalho por UF e trimestre, nominais (PNAD Contínua, IBGE) |
| `fct_selic` | Meta da Selic vigente no último dia de cada mês, em % ao ano (SGS 432) |
| `dim_tempo` | Um registro por data-base, com as quebras da série |
| `dim_modalidade` | Os 66 pares de modalidade e submodalidade do SCR.data |
| `dim_uf` | As 27 UFs, com o código do IBGE |
| `dim_segmento` | Os 8 segmentos de instituição financeira da V2 |
| `dim_porte`, `dim_cnae_ocupacao` | Porte e atividade, desambiguados pelo tipo de cliente |
| `dim_porte_receita`, `dim_natureza_juridica` | Porte e grupo de natureza jurídica do CNPJ |

As definições, os avisos e as armadilhas de cada conceito estão na [ontologia do projeto](https://github.com/RCHRDYv/bcb-credito-governanca/tree/main/ontology), com a fonte normativa de onde vieram. Dois exemplos: a UF é o domicílio do cliente ou a sede da empresa, e não o local da operação; e somar o Pix dos dois lados conta cada transação duas vezes.

## Como consultar com DuckDB

O arquivo [`esquema_estrela/views.sql`](https://github.com/RCHRDYv/bcb-credito-governanca/blob/main/esquema_estrela/views.sql) cria uma view por tabela, com o nome do dbt:

```sql
set variable base = 'hf://datasets/vidayuri/bcb-credito-governanca';
-- cole aqui o conteúdo de views.sql
select d.ano, sum(f.carteira_ativa) as carteira_ativa
from fct_carteira f join dim_tempo d using (data_base)
where f.cliente = 'PJ'
group by 1 order by 1;
```

Para reproduzir um resultado, use a revisão do manifesto: `hf://datasets/vidayuri/bcb-credito-governanca@<revisao_hf>`.

## Dado pessoal

Não há. As tabelas são fatos agregados e dimensões. O CNPJ entra só como contagem de empresas por UF, porte, natureza jurídica e MEI. Nenhum cadastro, nome, CPF ou CNPJ sai do projeto.

## Fontes e licença

O dataset é publicado sob a [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), porque as três fontes do Banco Central são publicadas sob ela, e a ODbL pede a mesma licença para a base derivada. As fontes, com os termos conferidos em 2026-10-07:

| Fonte | Publicador | Licença |
|---|---|---|
| [SCR.data](https://dadosabertos.bcb.gov.br/dataset/scr_data) | Banco Central do Brasil | ODbL |
| [SGS 432, meta da Selic](https://dadosabertos.bcb.gov.br/dataset/432-taxa-de-juros---meta-selic-definida-pelo-copom) | Banco Central do Brasil | ODbL |
| [Estatísticas do Pix](https://dadosabertos.bcb.gov.br/dataset/pix) | Banco Central do Brasil | ODbL |
| [CNPJ](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj) | Receita Federal do Brasil | Creative Commons Attribution |
| [SIDRA, tabelas 6579, 6472 e 6474](https://sidra.ibge.gov.br/) | IBGE | Licença aberta, com crédito da autoria |

## English summary

The star schema of the [bcb-credito-governanca](https://github.com/RCHRDYv/bcb-credito-governanca) project: Brazil's Central Bank SCR.data credit portfolio at its published grain, with IBGE, SGS, Pix and CNPJ facts, exported to Parquet so it can be queried with DuckDB without Databricks or credentials. Reference month: July 2026 (2026-07-31). One Parquet per `dim_*` and `fct_*` table; `esquema_estrela/views.sql` creates views with the dbt table names. Aggregated facts and dimensions only, with no personal data. Released under ODbL 1.0, as required by the Central Bank sources.
