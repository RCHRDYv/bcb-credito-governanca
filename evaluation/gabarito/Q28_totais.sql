-- PT: Q28, parte 1. Carteira total no último mês, com a variação mensal e a
--     anual.
-- EN: Q28, part 1. Total portfolio in the latest month, with monthly and
--     yearly change.
with mensal as (

    select data_base, cast(sum(carteira_ativa) as double) as carteira_ativa
    from fct_carteira
    group by data_base

),

ultimo as (

    select max(data_base) as data_base from mensal

)

select
    atual.data_base as mes,
    atual.carteira_ativa,
    100 * (atual.carteira_ativa / mes_anterior.carteira_ativa - 1) as variacao_mensal_pct,
    100 * (atual.carteira_ativa / ano_anterior.carteira_ativa - 1) as variacao_anual_pct
from ultimo
join mensal atual
    on atual.data_base = ultimo.data_base
join mensal mes_anterior
    on mes_anterior.data_base = last_day(ultimo.data_base - interval '1' month)
join mensal ano_anterior
    on ano_anterior.data_base = last_day(ultimo.data_base - interval '12' month)
