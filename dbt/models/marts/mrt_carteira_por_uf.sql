-- =============================================================================
-- PT: Mart de apresentação da tela 1 do dashboard: onde está o crédito hoje,
--     e onde ele é escasso por empresa ou por habitante. Grão: mês e UF.
--
--     Fica fora do experimento (ADR 0007), porque já traz as razões
--     calculadas. Cada razão é razão de somas, calculada uma vez aqui.
--
--     O denominador de empresas é o do ADR 0014: matrizes ativas de natureza
--     empresarial, sem MEI, com o mesmo filtro do mrt_decisao. Até a issue
--     #69 havia duas versões aqui, todas as matrizes e as sem MEI, que o ADR
--     descartou, e a tela 1 não tinha como mostrar "todas as modalidades"
--     com o denominador da decisão (decidido em 2026-10-01). A população é a
--     estimativa do ano da data-base, sem interpolar.
--
--     O número de empresas é reconstruído de um retrato só do CNPJ, e não
--     observado mês a mês (ADR 0009). Para que ninguém o leia como contagem
--     observada, cada linha diz de qual retrato ele vem e a quantos meses
--     dele está. O erro medido cresce com essa distância.
--
--     A carteira por empresa de cada UF é comparada com a mediana das UFs
--     no mesmo mês, como o mrt_decisao faz por modalidade, e só entre as UFs
--     acima do corte de materialidade. No total da carteira PJ, todas as 27
--     passam do corte (a menor, RR, tinha R$ 3,7 bi em jul/2026), mas o
--     corte fica escrito, para a regra ser uma só.
--
--     Para a tela mostrar o tamanho de cada mercado e o da oportunidade, e
--     não só a razão (revisão da Tela 1, na #69, em 2026-10-01), o mart traz
--     também a participação da UF na carteira PJ do país e o crédito que
--     faltaria para a UF chegar à mediana. Essa segunda conta é a mesma do
--     custo de não entrar do mrt_decisao (ADR 0014, decisão 5), só nas UFs
--     abaixo da mediana.
--
-- EN: Presentation mart for dashboard screen 1: where credit is today, and
--     where it is scarce per company or per inhabitant. Grain: month and
--     state. Kept out of the experiment because the ratios come computed.
--     Every ratio is a ratio of sums, computed once. The company denominator
--     is ADR 0014's (business entities, no MEI), and each state is compared
--     with the median across states above the materiality cut in the same
--     month. Population is the reference year's estimate.
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

-- PT: O denominador do ADR 0014, com o mesmo filtro do mrt_decisao.
-- EN: ADR 0014's denominator, with the same filter as mrt_decisao.
empresas as (

    select
        data_base,
        uf,
        sum(empresas_ativas) as empresas
    from {{ ref('fct_empresas_ativas') }}
    where grupo_natureza_juridica = '{{ var("decisao_grupo_natureza_juridica") }}'
      and not mei
    group by data_base, uf

),

-- PT: As razões em double, como no mrt_decisao: a divisão entre decimais no
--     Spark arredonda para 6 casas.
-- EN: Ratios as double, as in mrt_decisao.
por_empresa as (

    select
        c.data_base,
        c.uf,
        cast(c.carteira_pj as double) / e.empresas as carteira_por_empresa,
        c.carteira_pj >= {{ var('decisao_carteira_minima') }} as acima_do_corte
    from carteira as c
    left join empresas as e
        on e.data_base = c.data_base and e.uf = c.uf

),

mediana as (

    select
        data_base,
        percentile_cont(0.5) within group (order by carteira_por_empresa) as mediana_carteira_por_empresa
    from por_empresa
    where acima_do_corte
    group by data_base

)

select
    c.data_base,
    c.uf,

    c.carteira_pj,
    c.carteira_pf,
    c.carteira_total,
    c.carteira_inadimplida_pj,
    e.empresas,
    p.populacao,

    -- PT: de onde vem o denominador de empresas, e a que distância
    -- EN: where the company denominator comes from, and how far
    r.retrato_do_cnpj,
    cast(months_between(to_date(concat(r.retrato_do_cnpj, '-01')), trunc(c.data_base, 'MM')) as int)
        as meses_ate_o_retrato,

    pe.carteira_por_empresa,
    m.mediana_carteira_por_empresa,
    pe.carteira_por_empresa / m.mediana_carteira_por_empresa as indice_de_espaco,

    -- PT: o crédito que faltaria para chegar à mediana, como o custo de não
    --     entrar do mrt_decisao (ADR 0014, decisão 5)
    -- EN: credit missing to reach the median, as mrt_decisao's cost of not
    --     entering
    case
        when pe.carteira_por_empresa < m.mediana_carteira_por_empresa
            then (m.mediana_carteira_por_empresa - pe.carteira_por_empresa) * e.empresas
    end as custo_de_nao_entrar,

    -- PT: a fatia da UF na carteira PJ do país, no mesmo mês
    -- EN: the state's share of the country's PJ portfolio, same month
    cast(c.carteira_pj as double) / sum(c.carteira_pj) over (partition by c.data_base)
        as participacao_na_carteira_pj,
    c.carteira_total / p.populacao as carteira_por_habitante,
    c.carteira_pf / p.populacao as carteira_pf_por_habitante,
    c.carteira_inadimplida_pj / c.carteira_pj as taxa_inadimplencia_pj

from carteira as c
left join empresas as e
    on e.data_base = c.data_base and e.uf = c.uf
left join por_empresa as pe
    on pe.data_base = c.data_base and pe.uf = c.uf
left join mediana as m
    on m.data_base = c.data_base
left join {{ ref('fct_populacao') }} as p
    on p.ano = year(c.data_base) and p.uf = c.uf
cross join retrato as r
