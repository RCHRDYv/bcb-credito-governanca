-- PT: Q25. Meta da Selic definida pelo Copom e taxa de inadimplência total,
--     mês a mês, no recorte inteiro. A pergunta pede três anos, e o recorte
--     é menor.
-- EN: Q25. Copom's Selic target and the total default rate, month by month,
--     over the whole window, which is shorter than the three years asked.
with inadimplencia as (

    select
        data_base,
        100 * cast(sum(carteira_inadimplencia) as double) / cast(sum(carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira
    group by data_base

)

select
    i.data_base as mes,
    s.selic_meta as selic_meta_pct,
    i.taxa_inadimplencia_pct
from inadimplencia i
join fct_selic s
    on s.data_base = i.data_base
order by mes
