-- PT: Q20, leitura pela participação do maior segmento no último mês, e a
--     do mesmo segmento 12 meses antes e no início do recorte.
-- EN: Q20, reading by the largest segment's share in the latest month, and
--     the same segment's share 12 months earlier and at the window's start.
with por_segmento as (

    select data_base, segmento, cast(sum(carteira_ativa) as double) as carteira_ativa
    from fct_carteira
    group by data_base, segmento

),

participacao as (

    select
        data_base,
        segmento,
        100 * carteira_ativa / sum(carteira_ativa) over (partition by data_base) as participacao_pct
    from por_segmento

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

),

maior as (

    select p.segmento
    from participacao p
    join limites
        on p.data_base = limites.ultimo
    order by p.participacao_pct desc
    limit 1

)

select
    maior.segmento as maior_segmento,
    inicio.participacao_pct as participacao_no_inicio_do_recorte_pct,
    doze.participacao_pct as participacao_12_meses_antes_pct,
    atual.participacao_pct as participacao_no_ultimo_mes_pct,
    atual.participacao_pct - doze.participacao_pct as variacao_12_meses_pp,
    atual.participacao_pct - inicio.participacao_pct as variacao_no_recorte_pp
from maior
cross join limites
join participacao atual
    on atual.segmento = maior.segmento
   and atual.data_base = limites.ultimo
join participacao doze
    on doze.segmento = maior.segmento
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
join participacao inicio
    on inicio.segmento = maior.segmento
   and inicio.data_base = limites.primeiro
