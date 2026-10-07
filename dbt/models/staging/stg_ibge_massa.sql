-- =============================================================================
-- PT: Staging da massa de rendimento mensal do trabalho por UF, tabela 6474
--     do SIDRA (PNAD Contínua trimestral, issue #38). 1:1 com o bronze (ADR
--     0006). Os nomes de campo do SIDRA viram nomes que dizem o que são, o
--     trimestre AAAATT vira ano e trimestre, e o valor vira número.
--
--     As duas variáveis ficam em linhas, como vieram: 6288 é o valor
--     nominal, em milhões de reais, e 6289 é o coeficiente de variação, em
--     %. A conversão para reais acontece no fato.
-- EN: Staging for total monthly labor income by state, SIDRA table 6474.
--     1:1 with bronze. Both variables stay as rows: 6288 is the nominal value
--     in millions of reais, 6289 the coefficient of variation in %. The
--     conversion to reais happens in the fact.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_ibge_massa') }}

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
