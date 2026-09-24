-- =============================================================================
-- PT: O fato legado da V1 agrega o staging, e agregar não pode perder nem
--     inventar carteira. Compara meses e as três somas entre os dois.
-- EN: The legacy V1 fact aggregates staging, and aggregating must neither lose
--     nor invent portfolio. Compares months and the three sums between them.
-- =============================================================================

with staging as (

    select
        count(distinct data_base) as meses,
        sum(carteira_ativa) as carteira_ativa,
        sum(carteira_inadimplida_arrastada) as carteira_inadimplida_arrastada,
        sum(ativo_problematico) as ativo_problematico
    from {{ ref('stg_scr_v1') }}

),

fato as (

    select
        count(distinct data_base) as meses,
        sum(carteira_ativa) as carteira_ativa,
        sum(carteira_inadimplida_arrastada) as carteira_inadimplida_arrastada,
        sum(ativo_problematico) as ativo_problematico
    from {{ ref('fct_carteira_v1') }}

)

select 'staging' as lado, * from (select * from staging except select * from fato)
union all
select 'fato' as lado, * from (select * from fato except select * from staging)
