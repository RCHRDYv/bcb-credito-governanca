-- PT: Q11. Carteira de pessoa jurídica por habitante, por UF, no último mês,
--     com a estimativa de população do IBGE do mesmo ano.
-- EN: Q11. Corporate portfolio per inhabitant by state in the latest month,
--     with the same year's IBGE population estimate.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

),

carteira as (

    select f.uf, sum(f.carteira_ativa) as carteira_pj
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base
    where f.cliente = 'PJ'
    group by f.uf

)

select
    row_number() over (order by cast(carteira.carteira_pj as double) / p.populacao desc) as posicao,
    carteira.uf,
    carteira.carteira_pj,
    p.populacao,
    p.ano as ano_da_populacao,
    cast(carteira.carteira_pj as double) / p.populacao as carteira_pj_por_habitante
from carteira
cross join ultimo
join fct_populacao p
    on p.uf = carteira.uf
   and p.ano = year(ultimo.data_base)
order by posicao
