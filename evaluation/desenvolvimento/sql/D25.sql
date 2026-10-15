-- PT: D25. Variação do valor médio por transação de PIX paga por pessoas
--     físicas de julho de 2025 a julho de 2026.
-- EN: D25. Change in the average value per PIX transaction paid by
--     individuals, July 2025 to July 2026.
with por_mes as (

    select data_base, cast(sum(valor) as double) / cast(sum(quantidade) as double) as valor_medio
    from fct_pix
    where cliente = 'PF'
      and lado = 'pagador'
      and data_base in (date '2025-07-31', date '2026-07-31')
    group by data_base

)

select
    max(case when data_base = date '2025-07-31' then valor_medio end) as valor_medio_julho_2025,
    max(case when data_base = date '2026-07-31' then valor_medio end) as valor_medio_julho_2026,
    100 * (max(case when data_base = date '2026-07-31' then valor_medio end)
        / max(case when data_base = date '2025-07-31' then valor_medio end) - 1) as variacao_pct
from por_mes
