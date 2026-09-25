-- PT: Q33. Distribuição da carteira por porte no último mês, separada por
--     tipo de cliente: para PF o porte é faixa de renda, e para PJ é o
--     tamanho da empresa. A participação é dentro do próprio cliente.
-- EN: Q33. Portfolio by client size in the latest month, split by client
--     type, since size means income band for individuals and company size
--     for firms. Shares are within each client type.
select
    p.cliente,
    p.porte_desambiguado,
    p.taxonomia,
    sum(f.carteira_ativa) as carteira_ativa,
    100 * cast(sum(f.carteira_ativa) as double)
        / sum(cast(sum(f.carteira_ativa) as double)) over (partition by p.cliente)
        as participacao_no_cliente_pct
from fct_carteira f
join dim_porte p
    on p.porte_desambiguado = f.porte_desambiguado
where f.data_base = (select max(data_base) from fct_carteira)
group by p.cliente, p.porte_desambiguado, p.taxonomia
order by p.cliente, carteira_ativa desc
