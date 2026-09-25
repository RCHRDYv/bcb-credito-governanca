-- PT: Q14, leitura com as empresas de natureza empresarial, sem MEI (o denominador do ADR 0014).
--     Carteira PJ por empresa ativa, por UF, no último mês. Sub-atendida é a
--     UF abaixo da mediana das UFs. A lista vai da menor carteira por
--     empresa para a maior.
-- EN: Q14, reading with business-law companies, excluding MEI (ADR 0014's denominator). Corporate portfolio per active company by state in
--     the latest month; underserved means below the median of the states.
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

),

empresas as (

    select e.uf, sum(e.empresas_ativas) as empresas_ativas
    from fct_empresas_ativas e
    join ultimo
        on e.data_base = ultimo.data_base
    where e.grupo_natureza_juridica = '2' and not e.mei
    group by e.uf

),

por_empresa as (

    select
        carteira.uf,
        carteira.carteira_pj,
        empresas.empresas_ativas,
        cast(carteira.carteira_pj as double) / empresas.empresas_ativas as carteira_por_empresa
    from carteira
    join empresas
        on empresas.uf = carteira.uf

),

mediana as (

    select percentile_cont(0.5) within group (order by carteira_por_empresa) as mediana
    from por_empresa

)

select
    row_number() over (order by por_empresa.carteira_por_empresa) as posicao,
    por_empresa.uf,
    por_empresa.carteira_pj,
    por_empresa.empresas_ativas,
    por_empresa.carteira_por_empresa,
    mediana.mediana as mediana_das_ufs,
    por_empresa.carteira_por_empresa < mediana.mediana as abaixo_da_mediana
from por_empresa
cross join mediana
order by posicao
