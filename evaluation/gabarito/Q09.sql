-- PT: Q09. Distância entre ativo problemático e carteira inadimplida, por
--     modalidade, no último mês, com o critério do ativo problemático em
--     vigor naquele mês.
-- EN: Q09. Gap between problem assets and non-performing portfolio by
--     modality in the latest month, with the problem-asset criterion in force.
select
    m.codigo_modalidade,
    m.modalidade,
    sum(f.carteira_ativa) as carteira_ativa,
    sum(f.carteira_inadimplencia) as carteira_inadimplencia,
    sum(f.ativo_problematico) as ativo_problematico,
    sum(f.ativo_problematico) - sum(f.carteira_inadimplencia) as distancia_em_reais,
    100 * (cast(sum(f.ativo_problematico) as double) - cast(sum(f.carteira_inadimplencia) as double))
        / cast(sum(f.carteira_ativa) as double) as distancia_pp,
    t.criterio_ativo_problematico
from fct_carteira f
join dim_modalidade m
    on m.codigo_submodalidade = f.codigo_submodalidade
join dim_tempo t
    on t.data_base = f.data_base
where f.data_base = (select max(data_base) from fct_carteira)
group by m.codigo_modalidade, m.modalidade, t.criterio_ativo_problematico
order by distancia_pp desc
