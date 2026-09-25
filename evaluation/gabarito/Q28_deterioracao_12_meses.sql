-- PT: Q28, parte 3, leitura em 12 meses. As três modalidades de maior aumento da
--     taxa de inadimplência, em pontos percentuais.
-- EN: Q28, part 3, reading over 12 months. The three modalities with the largest rise
--     in default rate, in percentage points.
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
        atual.taxa_inadimplencia_pct - anterior.taxa_inadimplencia_pct as variacao_pp
    from por_modalidade atual
    join ultimo
        on atual.data_base = ultimo.data_base
    join por_modalidade anterior
        on anterior.codigo_modalidade = atual.codigo_modalidade
       and anterior.data_base = last_day(ultimo.data_base - interval '12' month)

)

select
    row_number() over (order by variacao_pp desc) as posicao,
    codigo_modalidade,
    modalidade,
    variacao_pp
from comparado
order by posicao
limit 3
