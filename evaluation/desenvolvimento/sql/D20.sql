-- PT: D20. Parcela da carteira com destinação específica em cada mês do 1º
--     semestre de 2026.
-- EN: D20. Share of the portfolio with specific allocation in each month of H1
--     2026.
with por_mes as (

    select
        t.data_base,
        t.mes,
        sum(case when f.origem = 'Com destinação específica' then f.carteira_ativa else 0 end) as com_destinacao,
        sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira as f
    join dim_tempo as t on t.data_base = f.data_base
    where t.ano = 2026
      and t.mes <= 6
    group by t.data_base, t.mes

)

select
    data_base as mes,
    100 * cast(com_destinacao as double) / cast(carteira_ativa as double) as participacao_destinacao_especifica_pct
from por_mes
order by data_base
