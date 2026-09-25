-- PT: Q32. Composição da modalidade "Outros créditos" (13) no último mês, e o
--     peso dela na carteira total.
-- EN: Q32. Composition of the "Outros créditos" modality (13) in the latest
--     month, and its weight in the total portfolio.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

),

total as (

    select sum(f.carteira_ativa) as carteira_total
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base

),

por_submodalidade as (

    select f.codigo_submodalidade, m.submodalidade, sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    where m.codigo_modalidade = '13'
    group by f.codigo_submodalidade, m.submodalidade

)

select
    s.codigo_submodalidade,
    s.submodalidade,
    s.carteira_ativa,
    100 * cast(s.carteira_ativa as double) / sum(cast(s.carteira_ativa as double)) over ()
        as participacao_na_modalidade_pct,
    100 * sum(cast(s.carteira_ativa as double)) over () / cast(total.carteira_total as double)
        as participacao_da_modalidade_na_carteira_pct
from por_submodalidade s
cross join total
order by s.carteira_ativa desc
