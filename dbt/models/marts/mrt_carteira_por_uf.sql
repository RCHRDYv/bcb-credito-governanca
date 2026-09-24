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
--     O número de empresas é reconstruído de um retrato só do CNPJ, e não
--     observado mês a mês (ADR 0009). Para que ninguém o leia como contagem
--     observada, cada linha diz de qual retrato ele vem e a quantos meses
--     dele está. O erro medido cresce com essa distância.
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

retrato as (

    select max(retrato) as retrato_do_cnpj from {{ ref('stg_cnpj_empresas') }}

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

    -- PT: de onde vem o denominador de empresas, e a que distância
    -- EN: where the company denominator comes from, and how far
    r.retrato_do_cnpj,
    cast(months_between(to_date(concat(r.retrato_do_cnpj, '-01')), trunc(c.data_base, 'MM')) as int)
        as meses_ate_o_retrato,

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
cross join retrato as r
