-- PT: Q01. Carteira ativa total no último mês e no mesmo mês do ano anterior.
-- EN: Q01. Total active portfolio in the latest month and a year earlier.
with mensal as (

    select data_base, sum(carteira_ativa) as carteira_ativa
    from fct_carteira
    group by data_base

),

atual as (

    select * from mensal
    where data_base = (select max(data_base) from mensal)

)

select
    atual.data_base as mes,
    atual.carteira_ativa,
    anterior.data_base as mes_do_ano_anterior,
    anterior.carteira_ativa as carteira_ativa_do_ano_anterior,
    atual.carteira_ativa - anterior.carteira_ativa as variacao_em_reais,
    100 * (cast(atual.carteira_ativa as double) / cast(anterior.carteira_ativa as double) - 1) as variacao_pct
from atual
join mensal anterior
    on anterior.data_base = last_day(atual.data_base - interval '12' month)
