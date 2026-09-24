-- =============================================================================
-- PT: Camada bronze. Uma tabela por versão do SCR.data, com o dado exatamente
--     como publicado: todas as colunas como texto, sem trim, sem conversão.
--     Limpeza, tipagem e tratamento do sentinela -1 são papel do staging.
-- EN: Bronze layer. One table per SCR.data version, with the data exactly as
--     published: every column as text, untrimmed, uncast. Cleaning, typing
--     and handling the -1 sentinel belong to staging.
--
-- PT: Os marcadores {catalogo}, {schema} e {volume} são preenchidos por
--     ingestion/criar_bronze.py a partir de ingestion/fontes.py.
-- EN: The {catalogo}, {schema} and {volume} placeholders are filled by
--     ingestion/criar_bronze.py from ingestion/fontes.py.
-- =============================================================================

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_scr_v2
COMMENT 'SCR.data V2 (scrdata_AAAA.zip) como publicado pelo BCB, todas as colunas como texto. Fonte principal do projeto. Linhagem por arquivo em arquivo_origem e sha256_zip. Identidade de cada ZIP em ingestion/manifesto.json.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/v2/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_scr_v1
COMMENT 'SCR.data V1 (planilha_AAAA.zip) como publicado pelo BCB, todas as colunas como texto. Fonte legada, mantida para reconciliação com a V2 e para a conformação de taxonomia do ADR 0003.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/v1/*/*.parquet', format => 'parquet');

-- =============================================================================
-- PT: Fontes externas por UF (issue #25, ADR 0009). Mesma regra do SCR: o
--     dado como publicado, todas as colunas como texto. As tabelas da
--     Receita guardam também contato e endereço, porque o bronze é o dado
--     inteiro, e o staging seleciona só as colunas usadas, então esses
--     campos não passam daqui.
-- EN: External sources by state. Same rule as the SCR: data as published,
--     every column as text. Receita's tables also hold contact and address
--     fields, since bronze is the whole data, and staging selects only the
--     columns used, so those fields go no further.
-- =============================================================================

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_cnpj_estabelecimentos
COMMENT 'CNPJ aberto da Receita Federal, tabela Estabelecimentos, como publicada, todas as colunas como texto. Três retratos: o mais recente alimenta o modelo e os dois antigos medem o erro da reconstrução mensal (ADR 0009). Linhagem em arquivo_origem, retrato, data_extracao e sha256_zip.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/cnpj/estabelecimentos/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_cnpj_empresas
COMMENT 'CNPJ aberto da Receita Federal, tabela Empresas, como publicada, todas as colunas como texto. Traz natureza jurídica e porte da empresa.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/cnpj/empresas/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_cnpj_simples
COMMENT 'CNPJ aberto da Receita Federal, tabela Simples, como publicada, todas as colunas como texto. Traz a opção pelo MEI com as datas de entrada e de saída.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/cnpj/simples/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_cnpj_naturezas
COMMENT 'CNPJ aberto da Receita Federal, tabela de domínio das naturezas jurídicas, como publicada.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/cnpj/naturezas/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_cnpj_cnaes
COMMENT 'CNPJ aberto da Receita Federal, tabela de domínio da CNAE, como publicada.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/cnpj/cnaes/*/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_ibge_populacao
COMMENT 'População residente estimada por UF, IBGE, tabela 6579 do SIDRA, como a API devolveu, todas as colunas como texto e com os nomes de campo do SIDRA. Data de referência em 1º de julho de cada ano.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/ibge/populacao/*.parquet', format => 'parquet');

CREATE OR REPLACE TABLE {catalogo}.{schema}.bronze_sgs_series
COMMENT 'Séries do SGS do BCB, uma linha por dia e por série, como a API devolveu, todas as colunas como texto. Hoje só a meta da Selic definida pelo Copom (série 432, issue 37). Data no formato DD/MM/AAAA e valor com ponto decimal. A consulta termina na data da extração, registrada em data_extracao.'
AS
SELECT
  *,
  current_timestamp() AS ingerido_em
FROM read_files('{volume}/sgs/*/*.parquet', format => 'parquet');
