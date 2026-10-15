-- PT: D16. Os três segmentos com maior carteira de crédito rural (modalidade
--     08), julho de 2026.
-- EN: D16. The three segments with the largest rural credit portfolio
--     (modality 08), July 2026.
with por_segmento as (

    select f.segmento, sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira as f
    join dim_modalidade as m on m.codigo_submodalidade = f.codigo_submodalidade
    where m.codigo_modalidade = '08'
      and f.data_base = date '2026-07-31'
    group by f.segmento

)

select
    row_number() over (order by carteira_ativa desc) as posicao,
    segmento,
    carteira_ativa
from por_segmento
order by posicao
