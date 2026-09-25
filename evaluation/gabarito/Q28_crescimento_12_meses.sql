-- PT: Q28, parte 2, leitura em 12 meses. As três modalidades de maior crescimento
--     percentual da carteira.
-- EN: Q28, part 2, reading over 12 months. The three modalities with the highest
--     percentage portfolio growth.
with por_modalidade as (

    select f.data_base, m.codigo_modalidade, m.modalidade, cast(sum(f.carteira_ativa) as double) as carteira_ativa
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
        100 * (atual.carteira_ativa / anterior.carteira_ativa - 1) as crescimento_pct
    from por_modalidade atual
    join ultimo
        on atual.data_base = ultimo.data_base
    join por_modalidade anterior
        on anterior.codigo_modalidade = atual.codigo_modalidade
       and anterior.data_base = last_day(ultimo.data_base - interval '12' month)

)

select
    row_number() over (order by crescimento_pct desc) as posicao,
    codigo_modalidade,
    modalidade,
    crescimento_pct
from comparado
order by posicao
limit 3
