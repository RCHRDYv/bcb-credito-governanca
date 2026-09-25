-- PT: Q39. Carteira ativa total da V1 e da V2, mês a mês, a diferença, e
--     quanto a diferença mudou de um mês para o outro. O degrau aparece como
--     a maior mudança.
-- EN: Q39. V1 and V2 total active portfolio month by month, the gap, and the
--     month-on-month change in the gap; the step shows as the largest change.
with v2 as (

    select data_base, cast(sum(carteira_ativa) as double) as carteira_ativa
    from fct_carteira
    group by data_base

),

v1 as (

    select data_base, cast(sum(carteira_ativa) as double) as carteira_ativa
    from fct_carteira_v1
    group by data_base

),

comparado as (

    select
        v2.data_base,
        v1.carteira_ativa as carteira_v1,
        v2.carteira_ativa as carteira_v2,
        v2.carteira_ativa - v1.carteira_ativa as diferenca,
        100 * (v2.carteira_ativa / v1.carteira_ativa - 1) as diferenca_pct
    from v2
    join v1
        on v1.data_base = v2.data_base

)

select
    data_base as mes,
    carteira_v1,
    carteira_v2,
    diferenca,
    diferenca_pct,
    diferenca_pct - lag(diferenca_pct) over (order by data_base) as mudanca_da_diferenca_pp
from comparado
order by mes
