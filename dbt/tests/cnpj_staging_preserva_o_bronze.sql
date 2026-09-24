-- =============================================================================
-- PT: O staging do CNPJ e do IBGE é 1:1 com o bronze (ADR 0006): seleciona
--     colunas, mas não filtra linha. Filtrar matriz ativa é interpretação, e
--     acontece no intermediate, onde é visível.
-- EN: CNPJ and IBGE staging is 1:1 with bronze: it selects columns but never
--     filters rows.
-- =============================================================================

with contagens as (

    select 'estabelecimentos' as tabela,
           (select count(*) from {{ source('externas', 'bronze_cnpj_estabelecimentos') }}) as no_bronze,
           (select count(*) from {{ ref('stg_cnpj_estabelecimentos') }}) as no_staging
    union all
    select 'empresas',
           (select count(*) from {{ source('externas', 'bronze_cnpj_empresas') }}),
           (select count(*) from {{ ref('stg_cnpj_empresas') }})
    union all
    select 'simples',
           (select count(*) from {{ source('externas', 'bronze_cnpj_simples') }}),
           (select count(*) from {{ ref('stg_cnpj_simples') }})
    union all
    select 'populacao',
           (select count(*) from {{ source('externas', 'bronze_ibge_populacao') }}),
           (select count(*) from {{ ref('stg_ibge_populacao') }})

)

select * from contagens where no_bronze != no_staging
