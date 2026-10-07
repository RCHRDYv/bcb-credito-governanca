-- =============================================================================
-- PT: Fato de renda do trabalho: rendimento médio e massa de rendimento
--     mensal do trabalho por UF e trimestre, da PNAD Contínua do IBGE
--     (tabelas 6472 e 6474 do SIDRA, issue #38, ADR 0025). Denominador das
--     perguntas Q13 e Q15.
--
--     O grão é o trimestre, e não o mês: a PNAD publica um valor mensal
--     médio por trimestre. Para cruzar com a carteira mensal, cada mês usa o
--     último trimestre encerrado até a data-base, e fim_do_trimestre existe
--     para essa junção (ontology/fontes_externas.yml,
--     rendimento_medio_do_trabalho).
--
--     Os valores são nominais, como os do SCR. A massa chega em milhões de
--     reais e sai em reais, na mesma unidade da carteira.
--
-- EN: Labor income fact: average and total monthly labor income by state and
--     quarter, from IBGE's PNAD Contínua. The grain is the quarter; each
--     monthly reference date uses the last quarter ended by it, and
--     fim_do_trimestre exists for that join. Values are nominal, like the
--     SCR's; total income arrives in millions of reais and leaves in reais.
-- =============================================================================

with rendimento as (

    select
        ano,
        trimestre,
        codigo_ibge_uf,
        max(case when codigo_variavel = '5929' then valor end) as rendimento_medio,
        max(case when codigo_variavel = '5937' then valor end) as cv_rendimento_medio
    from {{ ref('stg_ibge_rendimento') }}
    group by ano, trimestre, codigo_ibge_uf

),

massa as (

    select
        ano,
        trimestre,
        codigo_ibge_uf,
        max(case when codigo_variavel = '6288' then valor end) * 1000000 as massa_de_rendimento,
        max(case when codigo_variavel = '6289' then valor end) as cv_massa_de_rendimento
    from {{ ref('stg_ibge_massa') }}
    group by ano, trimestre, codigo_ibge_uf

)

select
    r.ano,
    r.trimestre,
    last_day(make_date(r.ano, r.trimestre * 3, 1)) as fim_do_trimestre,
    u.valor as uf,
    r.rendimento_medio,
    r.cv_rendimento_medio,
    cast(m.massa_de_rendimento as decimal(20, 2)) as massa_de_rendimento,
    m.cv_massa_de_rendimento
from rendimento as r
inner join massa as m
    on m.ano = r.ano and m.trimestre = r.trimestre and m.codigo_ibge_uf = r.codigo_ibge_uf
inner join {{ ref('ontologia_dimensao') }} as u
    on u.dimensao = 'uf' and u.codigo_ibge = r.codigo_ibge_uf
