-- PT: Q25. Meta da Selic definida pelo Copom e taxa de inadimplência total,
--     mês a mês, do mês 24 meses antes do último até o último.
-- EN: Q25. Copom's Selic target and the total default rate, month by month,
--     from 24 months before the latest month up to it.
with inadimplencia as (

    select
        data_base,
        100 * cast(sum(carteira_inadimplencia) as double) / cast(sum(carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira
    group by data_base

),

ultimo as (

    select max(data_base) as data_base from inadimplencia

)

select
    i.data_base as mes,
    s.selic_meta as selic_meta_pct,
    i.taxa_inadimplencia_pct
from inadimplencia i
cross join ultimo
join fct_selic s
    on s.data_base = i.data_base
where i.data_base >= last_day(ultimo.data_base - interval '24' month)
order by mes
