-- =============================================================================
-- PT: Mart de apresentação da tela 1 do dashboard: onde está o crédito hoje,
--     e onde ele é escasso por empresa ou por habitante. Grão: mês e UF.
--
--     Fica fora do experimento (ADR 0007), porque já traz as razões
--     calculadas. Cada razão é razão de somas, calculada uma vez aqui.
--
--     Duas versões do denominador de empresas, porque a escolha é da camada
--     de decisão (issue #26): todas as matrizes ativas, e só as que não são
--     MEI no mês. A população é a estimativa do ano da data-base, sem
--     interpolar.
--
--     A mediana nacional e a comparação entre UFs ficam na camada de
--     decisão, que lê daqui.
--
-- EN: Presentation mart for dashboard screen 1: where credit is today, and
--     where it is scarce per company or per inhabitant. Grain: month and
--     state. Kept out of the experiment because the ratios come computed.
--     Every ratio is a ratio of sums, computed once. Two company
--     denominators, with and without MEIs, since the choice belongs to the
--     decision layer. Population is the reference year's estimate.
-- =============================================================================

with carteira as (

    select
        data_base,
        uf,
        sum(case when cliente = 'PJ' then carteira_ativa end) as carteira_pj,
        sum(case when cliente = 'PF' then carteira_ativa end) as carteira_pf,
        sum(carteira_ativa) as carteira_total,
        sum(case when cliente = 'PJ' then carteira_inadimplencia end) as carteira_inadimplida_pj
    from {{ ref('fct_carteira') }}
    group by data_base, uf

),

empresas as (

    select
        data_base,
        uf,
        sum(empresas_ativas) as empresas_ativas,
        sum(case when not mei then empresas_ativas else 0 end) as empresas_ativas_sem_mei
    from {{ ref('fct_empresas_ativas') }}
    group by data_base, uf

)

select
    c.data_base,
    c.uf,

    c.carteira_pj,
    c.carteira_pf,
    c.carteira_total,
    c.carteira_inadimplida_pj,
    e.empresas_ativas,
    e.empresas_ativas_sem_mei,
    p.populacao,

    c.carteira_pj / e.empresas_ativas as carteira_pj_por_empresa_ativa,
    c.carteira_pj / e.empresas_ativas_sem_mei as carteira_pj_por_empresa_ativa_sem_mei,
    c.carteira_total / p.populacao as carteira_por_habitante,
    c.carteira_pf / p.populacao as carteira_pf_por_habitante,
    c.carteira_inadimplida_pj / c.carteira_pj as taxa_inadimplencia_pj

from carteira as c
left join empresas as e
    on e.data_base = c.data_base and e.uf = c.uf
left join {{ ref('fct_populacao') }} as p
    on p.ano = year(c.data_base) and p.uf = c.uf
