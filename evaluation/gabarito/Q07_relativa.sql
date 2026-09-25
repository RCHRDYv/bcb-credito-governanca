-- PT: Q07, leitura relativa. Variação da taxa de inadimplência em 6 meses,
--     por modalidade, da maior deterioração para a menor.
-- EN: Q07, reading relative. Six-month change in the default rate by modality.
with por_modalidade as (

    select
        f.data_base,
        m.codigo_modalidade,
        m.modalidade,
        100 * cast(sum(f.carteira_inadimplencia) as double) / cast(sum(f.carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    group by f.data_base, m.codigo_modalidade, m.modalidade

),

ultimo as (

    select max(data_base) as data_base from fct_carteira

),

comparado as (

    select
        atual.codigo_modalidade,
        atual.modalidade,
        anterior.taxa_inadimplencia_pct as taxa_6_meses_antes_pct,
        atual.taxa_inadimplencia_pct as taxa_no_ultimo_mes_pct,
        atual.taxa_inadimplencia_pct - anterior.taxa_inadimplencia_pct as variacao_pp,
        100 * (atual.taxa_inadimplencia_pct / nullif(anterior.taxa_inadimplencia_pct, 0) - 1)
            as variacao_relativa_pct
    from por_modalidade atual
    join ultimo
        on atual.data_base = ultimo.data_base
    join por_modalidade anterior
        on anterior.codigo_modalidade = atual.codigo_modalidade
       and anterior.data_base = last_day(ultimo.data_base - interval '6' month)

)

select
    row_number() over (order by variacao_relativa_pct desc nulls last) as posicao,
    codigo_modalidade,
    modalidade,
    taxa_6_meses_antes_pct,
    taxa_no_ultimo_mes_pct,
    variacao_pp,
    variacao_relativa_pct
from comparado
order by posicao
