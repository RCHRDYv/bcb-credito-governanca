-- PT: Q20, leitura pelo índice de Herfindahl-Hirschman: soma dos quadrados
--     das participações dos segmentos, de 0 a 10.000. Vêm as duas janelas:
--     12 meses e o recorte inteiro.
-- EN: Q20, Herfindahl-Hirschman reading: sum of squared segment shares, 0 to
--     10,000, over 12 months and over the whole window.
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

indice as (

    select data_base, sum(participacao_pct * participacao_pct) as hhi
    from participacao
    group by data_base

)

select
    inicio.hhi as hhi_no_inicio_do_recorte,
    doze.hhi as hhi_12_meses_antes,
    atual.hhi as hhi_no_ultimo_mes,
    atual.hhi - doze.hhi as variacao_12_meses,
    atual.hhi - inicio.hhi as variacao_no_recorte
from limites
join indice atual
    on atual.data_base = limites.ultimo
join indice doze
    on doze.data_base = last_day(limites.ultimo - interval '12' month)
join indice inicio
    on inicio.data_base = limites.primeiro
