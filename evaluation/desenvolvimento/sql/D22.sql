-- PT: D22. Modalidades da carteira PJ por ativo problemático em dezembro de
--     2025.
-- EN: D22. Corporate portfolio modalities by problem assets, December 2025.
with por_modalidade as (

    select m.codigo_modalidade, m.modalidade, sum(f.ativo_problematico) as ativo_problematico
    from fct_carteira as f
    join dim_modalidade as m on m.codigo_submodalidade = f.codigo_submodalidade
    where f.cliente = 'PJ'
      and f.data_base = date '2025-12-31'
    group by m.codigo_modalidade, m.modalidade

)

select
    codigo_modalidade,
    modalidade,
    ativo_problematico
from por_modalidade
order by ativo_problematico desc
