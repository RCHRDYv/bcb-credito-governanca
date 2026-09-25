-- PT: Q04. Crescimento da carteira por segmento de instituição. A pergunta
--     não diz o período, então vêm as duas janelas: 12 meses e o recorte
--     inteiro, desde o primeiro mês do dado.
-- EN: Q04. Portfolio growth by institution segment, over 12 months and over
--     the whole window, since the question does not state a period.
with por_segmento as (

    select data_base, segmento, sum(carteira_ativa) as carteira_ativa
    from fct_carteira
    group by data_base, segmento

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

)

select
    atual.segmento,
    limites.primeiro as inicio_do_recorte,
    inicio.carteira_ativa as carteira_no_inicio_do_recorte,
    doze.carteira_ativa as carteira_12_meses_antes,
    atual.carteira_ativa as carteira_no_ultimo_mes,
    100 * (cast(atual.carteira_ativa as double) / cast(doze.carteira_ativa as double) - 1)
        as crescimento_12_meses_pct,
    100 * (cast(atual.carteira_ativa as double) / cast(inicio.carteira_ativa as double) - 1)
        as crescimento_no_recorte_pct
from limites
join por_segmento atual
    on atual.data_base = limites.ultimo
left join por_segmento doze
    on doze.segmento = atual.segmento
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
left join por_segmento inicio
    on inicio.segmento = atual.segmento
   and inicio.data_base = limites.primeiro
order by crescimento_12_meses_pct desc
