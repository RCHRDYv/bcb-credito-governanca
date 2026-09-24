-- =============================================================================
-- PT: O dashboard e a IA precisam ver os mesmos números.
--
--     O dashboard lê os marts de apresentação, e a IA lê o esquema estrela
--     (ADR 0007). Se as duas famílias divergirem, o projeto passa a ter duas
--     verdades, e a recomendação da tela 4 deixa de bater com o gabarito das
--     perguntas. Este teste compara, mês a mês, cada total dos marts de
--     apresentação com o mesmo total calculado direto dos fatos.
--
--     Devolve uma linha por mês e por conferência que divergir.
--
-- EN: The dashboard and the AI must see the same numbers. The dashboard reads
--     the presentation marts and the AI reads the star schema; if the two
--     families diverge, the project has two truths. This test compares, month
--     by month, every presentation-mart total with the same total computed
--     straight from the facts, and returns one row per month and check that
--     diverges.
-- =============================================================================

with fato_v2 as (

    select data_base,
           sum(carteira_ativa) as carteira_ativa,
           sum(carteira_inadimplencia) as carteira_inadimplencia,
           sum(ativo_problematico) as ativo_problematico
    from {{ ref('fct_carteira') }}
    group by data_base

),

fato_v1 as (

    select data_base, sum(carteira_ativa) as carteira_ativa
    from {{ ref('fct_carteira_v1') }}
    group by data_base

),

carteira_mensal as (

    select data_base,
           sum(carteira_ativa) as carteira_ativa,
           sum(carteira_inadimplencia) as carteira_inadimplencia,
           sum(ativo_problematico) as ativo_problematico
    from {{ ref('mrt_carteira_mensal') }}
    group by data_base

),

reconciliacao as (

    select data_base,
           sum(carteira_v2_conformada) as carteira_v2,
           sum(carteira_v1_publicada) as carteira_v1
    from {{ ref('mrt_reconciliacao_versoes') }}
    group by data_base

),

limites as (

    select data_base, carteira_v2, carteira_v1_publicada as carteira_v1
    from {{ ref('mrt_limites_do_dado') }}

),

conferencias as (

    select f.data_base, 'mrt_carteira_mensal: carteira ativa' as conferencia,
           m.carteira_ativa as no_mart, f.carteira_ativa as no_fato
    from fato_v2 f left join carteira_mensal m on m.data_base = f.data_base

    union all
    select f.data_base, 'mrt_carteira_mensal: carteira inadimplida',
           m.carteira_inadimplencia, f.carteira_inadimplencia
    from fato_v2 f left join carteira_mensal m on m.data_base = f.data_base

    union all
    select f.data_base, 'mrt_carteira_mensal: ativo problemático',
           m.ativo_problematico, f.ativo_problematico
    from fato_v2 f left join carteira_mensal m on m.data_base = f.data_base

    union all
    select f.data_base, 'mrt_reconciliacao_versoes: V2 conformada',
           r.carteira_v2, f.carteira_ativa
    from fato_v2 f left join reconciliacao r on r.data_base = f.data_base

    union all
    select f.data_base, 'mrt_reconciliacao_versoes: V1 publicada',
           r.carteira_v1, f.carteira_ativa
    from fato_v1 f left join reconciliacao r on r.data_base = f.data_base

    union all
    select f.data_base, 'mrt_limites_do_dado: V2',
           l.carteira_v2, f.carteira_ativa
    from fato_v2 f left join limites l on l.data_base = f.data_base

    union all
    select f.data_base, 'mrt_limites_do_dado: V1',
           l.carteira_v1, f.carteira_ativa
    from fato_v1 f left join limites l on l.data_base = f.data_base

)

select *
from conferencias
where no_mart is null
   or no_mart != no_fato
