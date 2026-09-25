-- PT: Q02, leitura em percentual. Modalidades ordenadas pelo crescimento da carteira
--     em 12 meses. A pergunta pede as cinco primeiras.
-- EN: Q02, reading in percent. Modalities ranked by 12-month portfolio growth.
with por_modalidade as (

    select f.data_base, m.codigo_modalidade, m.modalidade, sum(f.carteira_ativa) as carteira_ativa
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
        anterior.carteira_ativa as carteira_12_meses_antes,
        atual.carteira_ativa as carteira_no_ultimo_mes,
        atual.carteira_ativa - anterior.carteira_ativa as crescimento_em_reais,
        100 * (cast(atual.carteira_ativa as double) / cast(anterior.carteira_ativa as double) - 1)
            as crescimento_pct
    from por_modalidade atual
    join ultimo
        on atual.data_base = ultimo.data_base
    join por_modalidade anterior
        on anterior.codigo_modalidade = atual.codigo_modalidade
       and anterior.data_base = last_day(ultimo.data_base - interval '12' month)

)

select
    row_number() over (order by crescimento_pct desc nulls last) as posicao,
    codigo_modalidade,
    modalidade,
    carteira_12_meses_antes,
    carteira_no_ultimo_mes,
    crescimento_em_reais,
    crescimento_pct
from comparado
order by posicao
