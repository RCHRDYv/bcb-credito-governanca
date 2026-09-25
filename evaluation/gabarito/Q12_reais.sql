-- PT: Q12, leitura em reais. Crescimento da carteira por habitante em 12 meses,
--     por UF. Cada mês usa a estimativa de população do próprio ano.
-- EN: Q12, reading in reais. 12-month growth of the portfolio per inhabitant by
--     state, each month with its own year's population estimate.
with por_uf as (

    select data_base, uf, sum(carteira_ativa) as carteira_ativa
    from fct_carteira
    group by data_base, uf

),

por_habitante as (

    select
        c.data_base,
        c.uf,
        p.populacao,
        cast(c.carteira_ativa as double) / p.populacao as carteira_por_habitante
    from por_uf c
    join fct_populacao p
        on p.uf = c.uf
       and p.ano = year(c.data_base)

),

ultimo as (

    select max(data_base) as data_base from fct_carteira

),

comparado as (

    select
        atual.uf,
        anterior.carteira_por_habitante as carteira_por_habitante_12_meses_antes,
        atual.carteira_por_habitante as carteira_por_habitante_no_ultimo_mes,
        atual.carteira_por_habitante - anterior.carteira_por_habitante as crescimento_por_habitante_em_reais,
        100 * (atual.carteira_por_habitante / anterior.carteira_por_habitante - 1)
            as crescimento_por_habitante_pct
    from por_habitante atual
    join ultimo
        on atual.data_base = ultimo.data_base
    join por_habitante anterior
        on anterior.uf = atual.uf
       and anterior.data_base = last_day(ultimo.data_base - interval '12' month)

)

select
    row_number() over (order by crescimento_por_habitante_em_reais desc) as posicao,
    uf,
    carteira_por_habitante_12_meses_antes,
    carteira_por_habitante_no_ultimo_mes,
    crescimento_por_habitante_em_reais,
    crescimento_por_habitante_pct
from comparado
order by posicao
