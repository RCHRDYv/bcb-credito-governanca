-- =============================================================================
-- PT: Staging do rendimento médio mensal do trabalho por UF, tabela 6472 do
--     SIDRA (PNAD Contínua trimestral, issue #38). 1:1 com o bronze (ADR
--     0006). Os nomes de campo do SIDRA viram nomes que dizem o que são, o
--     trimestre AAAATT vira ano e trimestre, e o valor vira número.
--
--     As duas variáveis ficam em linhas, como vieram: 5929 é o valor
--     nominal, em reais, e 5937 é o coeficiente de variação, em %. A sigla
--     da UF não vem do IBGE: a junção pelo código acontece no fato, com a
--     ontologia.
-- EN: Staging for average monthly labor income by state, SIDRA table 6472.
--     1:1 with bronze. SIDRA field names become meaningful names, the YYYYQQ
--     quarter becomes year and quarter, and the value becomes a number. Both
--     variables stay as rows: 5929 is the nominal value in reais, 5937 the
--     coefficient of variation in %.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_ibge_rendimento') }}

)

select
    cast(substr(trim(D3C), 1, 4) as int) as ano,
    cast(substr(trim(D3C), 5, 2) as int) as trimestre,
    trim(D1C) as codigo_ibge_uf,
    trim(D1N) as nome_uf,
    trim(D2C) as codigo_variavel,
    cast(trim(V) as decimal(18, 2)) as valor,

    arquivo_origem,
    sha256_arquivo

from bronze
