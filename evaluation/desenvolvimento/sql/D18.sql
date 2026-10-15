-- PT: D18. UFs por empresas ativas (dezembro de 2025) por mil habitantes
--     (população de 2025).
-- EN: D18. States by active companies (Dec 2025) per thousand inhabitants
--     (2025 population).
with empresas as (

    select uf, sum(empresas_ativas) as empresas_ativas
    from fct_empresas_ativas
    where data_base = date '2025-12-31'
    group by uf

),

razao as (

    select
        e.uf,
        e.empresas_ativas,
        p.populacao,
        1000 * cast(e.empresas_ativas as double) / cast(p.populacao as double) as empresas_por_mil_habitantes
    from empresas as e
    join fct_populacao as p on p.uf = e.uf and p.ano = 2025

)

select
    row_number() over (order by empresas_por_mil_habitantes desc) as posicao,
    uf,
    empresas_ativas,
    populacao,
    empresas_por_mil_habitantes
from razao
order by posicao
