-- PT: Q06. Taxa de inadimplência por modalidade no último mês, como razão de
--     somas (carteira inadimplida sobre carteira ativa), e não média de taxas.
-- EN: Q06. Default rate by modality in the latest month, as a ratio of sums.
select
    m.codigo_modalidade,
    m.modalidade,
    sum(f.carteira_ativa) as carteira_ativa,
    sum(f.carteira_inadimplencia) as carteira_inadimplencia,
    100 * cast(sum(f.carteira_inadimplencia) as double) / cast(sum(f.carteira_ativa) as double)
        as taxa_inadimplencia_pct
from fct_carteira f
join dim_modalidade m
    on m.codigo_submodalidade = f.codigo_submodalidade
where f.data_base = (select max(data_base) from fct_carteira)
group by m.codigo_modalidade, m.modalidade
order by taxa_inadimplencia_pct desc
