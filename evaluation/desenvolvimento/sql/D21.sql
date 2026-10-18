-- PT: D21. Variação da taxa de inadimplência das microempresas de julho de
--     2025 a julho de 2026, em pontos percentuais.
-- EN: D21. Change in micro-enterprises' default rate, July 2025 to July 2026,
--     in percentage points.
with por_mes as (

    select
        data_base,
        100 * cast(sum(carteira_inadimplencia) as double) / cast(sum(carteira_ativa) as double) as taxa
    from fct_carteira
    where porte_desambiguado = 'PJ - Micro'
      and data_base in (date '2025-07-31', date '2026-07-31')
    group by data_base

)

select
    max(case when data_base = date '2025-07-31' then taxa end) as taxa_julho_2025_pct,
    max(case when data_base = date '2026-07-31' then taxa end) as taxa_julho_2026_pct,
    max(case when data_base = date '2026-07-31' then taxa end) - max(case when data_base = date '2025-07-31' then taxa end)
        as variacao_pp
from por_mes
