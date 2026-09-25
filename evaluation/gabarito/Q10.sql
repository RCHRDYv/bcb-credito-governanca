-- PT: Q10. Modalidades em que a carteira cresce e a taxa de inadimplência cai
--     ao mesmo tempo. A pergunta não diz o período, então vêm as duas
--     janelas: 12 meses e o recorte inteiro.
-- EN: Q10. Modalities whose portfolio grows while the default rate falls,
--     over 12 months and over the whole window.
with por_modalidade as (

    select
        f.data_base,
        m.codigo_modalidade,
        m.modalidade,
        cast(sum(f.carteira_ativa) as double) as carteira_ativa,
        100 * cast(sum(f.carteira_inadimplencia) as double) / cast(sum(f.carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    group by f.data_base, m.codigo_modalidade, m.modalidade

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

)

select
    atual.codigo_modalidade,
    atual.modalidade,
    100 * (atual.carteira_ativa / doze.carteira_ativa - 1) as crescimento_12_meses_pct,
    atual.taxa_inadimplencia_pct - doze.taxa_inadimplencia_pct as variacao_taxa_12_meses_pp,
    (atual.carteira_ativa > doze.carteira_ativa and atual.taxa_inadimplencia_pct < doze.taxa_inadimplencia_pct)
        as cresce_e_inadimplencia_cai_em_12_meses,
    100 * (atual.carteira_ativa / inicio.carteira_ativa - 1) as crescimento_no_recorte_pct,
    atual.taxa_inadimplencia_pct - inicio.taxa_inadimplencia_pct as variacao_taxa_no_recorte_pp,
    (atual.carteira_ativa > inicio.carteira_ativa and atual.taxa_inadimplencia_pct < inicio.taxa_inadimplencia_pct)
        as cresce_e_inadimplencia_cai_no_recorte
from limites
join por_modalidade atual
    on atual.data_base = limites.ultimo
join por_modalidade doze
    on doze.codigo_modalidade = atual.codigo_modalidade
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
join por_modalidade inicio
    on inicio.codigo_modalidade = atual.codigo_modalidade
   and inicio.data_base = limites.primeiro
order by atual.codigo_modalidade
