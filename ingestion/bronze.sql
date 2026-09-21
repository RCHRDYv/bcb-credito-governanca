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
