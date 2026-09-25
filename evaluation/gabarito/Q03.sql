-- PT: Q03. Participação de pessoa física e jurídica na carteira, mês a mês,
--     do mês 24 meses antes do último até o último.
-- EN: Q03. Individual and corporate share of the portfolio, month by month,
--     from 24 months before the latest month up to it.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

)

select
    f.data_base as mes,
    sum(case when f.cliente = 'PF' then f.carteira_ativa else 0 end) as carteira_pf,
    sum(case when f.cliente = 'PJ' then f.carteira_ativa else 0 end) as carteira_pj,
    100 * cast(sum(case when f.cliente = 'PF' then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as participacao_pf_pct,
    100 * cast(sum(case when f.cliente = 'PJ' then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as participacao_pj_pct
from fct_carteira f
cross join ultimo
where f.data_base >= last_day(ultimo.data_base - interval '24' month)
group by f.data_base
order by mes
