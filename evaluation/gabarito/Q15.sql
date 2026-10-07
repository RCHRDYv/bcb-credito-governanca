-- PT: Q15. Carteira de pessoa física por UF, no último mês, dividida pela
--     massa de rendimento mensal do trabalho da UF, no último trimestre da
--     PNAD encerrado até a data-base (ADR 0025). A razão se lê em meses de
--     renda do trabalho. A UF sugere sobre-endividamento quando a razão fica
--     acima da do Brasil, que é a soma das carteiras sobre a soma das
--     massas das 27 UFs.
-- EN: Q15. Individuals' portfolio by state in the latest month over the
--     state's monthly labor income in the last PNAD quarter ended by that
--     date, read as months of labor income. A state suggests over-indebtedness
--     when its ratio is above Brazil's, the sum of portfolios over the sum of
--     incomes across the 27 states.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

),

trimestre as (

    select max(r.fim_do_trimestre) as fim_do_trimestre
    from fct_renda_do_trabalho r
    join ultimo
        on r.fim_do_trimestre <= ultimo.data_base

),

carteira as (

    select f.uf, sum(f.carteira_ativa) as carteira_pf
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base
    where f.cliente = 'PF'
    group by f.uf

),

por_uf as (

    select
        c.uf,
        c.carteira_pf,
        r.massa_de_rendimento,
        r.ano * 100 + r.trimestre as trimestre_da_renda,
        cast(c.carteira_pf as double) / cast(r.massa_de_rendimento as double) as meses_de_renda
    from carteira c
    cross join trimestre t
    join fct_renda_do_trabalho r
        on r.uf = c.uf and r.fim_do_trimestre = t.fim_do_trimestre

),

brasil as (

    select cast(sum(carteira_pf) as double) / cast(sum(massa_de_rendimento) as double) as meses_de_renda_no_brasil
    from por_uf

)

select
    row_number() over (order by p.meses_de_renda desc) as posicao,
    p.uf,
    ultimo.data_base,
    p.trimestre_da_renda,
    p.carteira_pf,
    p.massa_de_rendimento,
    p.meses_de_renda,
    b.meses_de_renda_no_brasil,
    100 * (p.meses_de_renda / b.meses_de_renda_no_brasil - 1) as diferenca_para_o_brasil_pct,
    p.meses_de_renda > b.meses_de_renda_no_brasil as acima_da_razao_nacional
from por_uf p
cross join brasil b
cross join ultimo
order by posicao
