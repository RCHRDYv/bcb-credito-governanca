-- PT: Q27. Projeção da carteira ativa PJ do país para os três meses seguintes
--     ao último mês do dado, pela deriva, com o intervalo de 80%. A deriva é
--     o modelo que o backtest da #27 escolheu para o país (ADR 0023), e a
--     conta é a mesma de scripts/analises/previsao_da_carteira.py: a
--     inclinação vai do primeiro ao último mês, o desvio vem dos resíduos das
--     variações mensais com um grau a menos, e o desvio de h meses à frente é
--     o desvio vezes a raiz de h * (1 + h / (n - 1)). O z do intervalo de 80%
--     é o quantil 0,90 da normal, com as mesmas casas do script.
-- EN: Q27. Drift forecast of the country's PJ active portfolio for the three
--     months after the latest month, with the 80% interval, the same
--     arithmetic as the forecast script.
with mensal as (

    select data_base, cast(sum(carteira_ativa) as double) as carteira_ativa
    from fct_carteira
    where cliente = 'PJ'
    group by data_base

),

extremos as (

    select
        min(data_base) as primeiro_mes,
        max(data_base) as ultimo_mes,
        count(*) as meses
    from mensal

),

reta as (

    select
        extremos.ultimo_mes,
        extremos.meses,
        ultimo.carteira_ativa as ultimo_valor,
        (ultimo.carteira_ativa - primeiro.carteira_ativa) / (extremos.meses - 1) as inclinacao
    from extremos
    join mensal primeiro
        on primeiro.data_base = extremos.primeiro_mes
    join mensal ultimo
        on ultimo.data_base = extremos.ultimo_mes

),

variacoes as (

    select carteira_ativa - lag(carteira_ativa) over (order by data_base) as variacao
    from mensal

),

desvio as (

    select sqrt(sum(power(variacoes.variacao - reta.inclinacao, 2)) / (reta.meses - 2)) as sigma
    from variacoes
    cross join reta
    where variacoes.variacao is not null
    group by reta.meses

),

horizontes as (

    select 1 as h
    union all
    select 2 as h
    union all
    select 3 as h

)

select
    case horizontes.h
        when 1 then last_day(reta.ultimo_mes + interval '1' month)
        when 2 then last_day(reta.ultimo_mes + interval '2' month)
        else last_day(reta.ultimo_mes + interval '3' month)
    end as mes,
    horizontes.h as horizonte_em_meses,
    reta.ultimo_valor + reta.inclinacao * horizontes.h as carteira_projetada,
    reta.ultimo_valor + reta.inclinacao * horizontes.h
        - 1.2815515655446004 * desvio.sigma * sqrt(horizontes.h * (1 + horizontes.h / (reta.meses - 1.0))) as carteira_no_limite_inferior,
    reta.ultimo_valor + reta.inclinacao * horizontes.h
        + 1.2815515655446004 * desvio.sigma * sqrt(horizontes.h * (1 + horizontes.h / (reta.meses - 1.0))) as carteira_no_limite_superior
from reta
cross join desvio
cross join horizontes
order by mes
