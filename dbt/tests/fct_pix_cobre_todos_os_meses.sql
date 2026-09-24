-- =============================================================================
-- PT: Todo mês do SCR tem PIX, e com as 27 UFs. Um mês faltando quer dizer
--     que a ingestão parou antes, e "os últimos 24 meses" da Q22 sairiam com
--     um buraco sem aviso.
-- EN: Every SCR month has PIX, with all 27 states.
-- =============================================================================

select t.data_base, count(distinct p.uf) as ufs
from {{ ref('dim_tempo') }} as t
left join {{ ref('fct_pix') }} as p
    on p.data_base = t.data_base
group by t.data_base
having count(distinct p.uf) != 27
