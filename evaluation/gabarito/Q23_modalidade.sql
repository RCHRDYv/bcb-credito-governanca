-- PT: Q23, leitura por modalidade. Crescimento da carteira e do volume de PIX nas
--     duas janelas, 12 meses e o recorte inteiro, com a marca de retração.
--     Coincidência no tempo não é causa.
-- EN: Q23, reading by modality. Portfolio and PIX growth over 12 months and over the
--     whole window, flagging contraction. Coincidence is not causation.
with carteira as (

    select f.data_base, m.codigo_modalidade as codigo, m.modalidade as nome, cast(sum(f.carteira_ativa) as double) as carteira_ativa
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    group by f.data_base, m.codigo_modalidade, m.modalidade

),

pix as (

    select data_base, cast(sum(valor) as double) as volume
    from fct_pix
    where lado = 'pagador'
    group by data_base

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

),

crescimento_do_pix as (

    select
        100 * (atual.volume / doze.volume - 1) as pix_12_meses_pct,
        100 * (atual.volume / inicio.volume - 1) as pix_no_recorte_pct
    from limites
    join pix atual
        on atual.data_base = limites.ultimo
    join pix doze
        on doze.data_base = last_day(limites.ultimo - interval '12' month)
    join pix inicio
        on inicio.data_base = limites.primeiro

)

select
    atual.codigo,
    atual.nome,
    100 * (atual.carteira_ativa / doze.carteira_ativa - 1) as carteira_12_meses_pct,
    100 * (atual.carteira_ativa / inicio.carteira_ativa - 1) as carteira_no_recorte_pct,
    crescimento_do_pix.pix_12_meses_pct,
    crescimento_do_pix.pix_no_recorte_pct,
    atual.carteira_ativa < doze.carteira_ativa as retraiu_em_12_meses,
    atual.carteira_ativa < inicio.carteira_ativa as retraiu_no_recorte
from limites
cross join crescimento_do_pix
join carteira atual
    on atual.data_base = limites.ultimo
join carteira doze
    on doze.codigo = atual.codigo
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
join carteira inicio
    on inicio.codigo = atual.codigo
   and inicio.data_base = limites.primeiro
order by carteira_no_recorte_pct
