-- =============================================================================
-- PT: Cada mart de apresentação tem um grão declarado, e ele precisa
--     identificar a linha. Uma repetição aqui vira número dobrado no dashboard,
--     que exporta essas tabelas direto para JSON sem outra agregação por cima.
-- EN: Each presentation mart has a declared grain that must identify the row.
--     A repetition here becomes a doubled number on the dashboard, which
--     exports these tables straight to JSON.
-- =============================================================================

with carteira_mensal as (

    select 'mrt_carteira_mensal' as mart,
           concat_ws(' | ', data_base, cliente, uf, codigo_modalidade) as chave,
           count(*) as linhas
    from {{ ref('mrt_carteira_mensal') }}
    group by data_base, cliente, uf, codigo_modalidade
    having count(*) > 1

),

reconciliacao as (

    select 'mrt_reconciliacao_versoes' as mart,
           concat_ws(' | ', data_base, modalidade_v1, origem) as chave,
           count(*) as linhas
    from {{ ref('mrt_reconciliacao_versoes') }}
    group by data_base, modalidade_v1, origem
    having count(*) > 1

),

limites as (

    select 'mrt_limites_do_dado' as mart,
           cast(data_base as string) as chave,
           count(*) as linhas
    from {{ ref('mrt_limites_do_dado') }}
    group by data_base
    having count(*) > 1

)

select * from carteira_mensal
union all
select * from reconciliacao
union all
select * from limites
