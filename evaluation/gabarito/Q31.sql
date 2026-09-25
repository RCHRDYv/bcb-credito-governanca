-- PT: Q31. Cartão de crédito em todas as formas em que aparece: cinco
--     submodalidades de três modalidades, no último mês. Filtrar a
--     modalidade por "cartão" não acha nada, e esquecer a 1304 deixa de fora
--     a maior parte.
-- EN: Q31. Credit card in every form it appears: five submodalities across
--     three modalities, in the latest month.
with por_submodalidade as (

    select
        f.codigo_submodalidade,
        m.modalidade,
        m.submodalidade,
        sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    where f.data_base = (select max(data_base) from fct_carteira)
      and f.codigo_submodalidade in ('0204', '0210', '0218', '0406', '1304')
    group by f.codigo_submodalidade, m.modalidade, m.submodalidade

)

select
    codigo_submodalidade,
    modalidade,
    submodalidade,
    carteira_ativa,
    100 * cast(carteira_ativa as double) / sum(cast(carteira_ativa as double)) over () as participacao_no_cartao_pct,
    sum(carteira_ativa) over () as total_do_cartao
from por_submodalidade
order by carteira_ativa desc
