-- PT: Q05. As cinco UFs de maior carteira no último mês e a participação
--     acumulada delas na carteira nacional.
-- EN: Q05. The five largest states by portfolio in the latest month and
--     their cumulative share of the national portfolio.
with por_uf as (

    select uf, sum(carteira_ativa) as carteira_ativa
    from fct_carteira
    where data_base = (select max(data_base) from fct_carteira)
    group by uf

),

ordenado as (

    select
        uf,
        carteira_ativa,
        row_number() over (order by carteira_ativa desc) as posicao,
        100 * cast(carteira_ativa as double) / sum(cast(carteira_ativa as double)) over ()
            as participacao_pct
    from por_uf

)

select
    posicao,
    uf,
    carteira_ativa,
    participacao_pct,
    sum(participacao_pct) over (order by posicao rows between unbounded preceding and current row)
        as participacao_acumulada_pct
from ordenado
where posicao <= 5
order by posicao
