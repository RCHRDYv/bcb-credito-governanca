-- =============================================================================
-- PT: No total do país, o que foi pago é o que foi recebido, mês a mês, em
--     valor e em quantidade: todo PIX tem um pagador e um recebedor. Uma
--     diferença quer dizer que o dado chegou incompleto de um lado, ou que a
--     conversão perdeu linha. A linha sem UF entra na conta, porque é parte
--     do total.
--
--     O próprio dado publicado quebra a igualdade em dois meses, medido nos
--     JSONs brutos da API em 2026-09-24: em ago/2025 o pago supera o recebido
--     em R$ 1.205.108,81 e 502 transações, e em set/2025 em R$ 1.124.436,09 e
--     627 transações, sobre cerca de R$ 2,6 tri por mês. Nos outros 30 meses
--     a igualdade é exata. O teste avisa com esses dois e falha com um
--     terceiro, no padrão das outras exceções publicadas: a conhecida não
--     trava o build, e uma nova não passa em silêncio.
-- EN: Nationally, what was paid equals what was received, monthly, in value
--     and count. The published data itself breaks this in Aug and Sep 2025,
--     by about R$ 1.2 million each; the test warns on those two and fails on
--     a third.
-- =============================================================================

{{ config(warn_if='>0', error_if='>2') }}

select
    data_base,
    sum(case when lado = 'pagador' then valor end) as valor_pago,
    sum(case when lado = 'recebedor' then valor end) as valor_recebido,
    sum(case when lado = 'pagador' then quantidade end) as quantidade_paga,
    sum(case when lado = 'recebedor' then quantidade end) as quantidade_recebida
from {{ ref('fct_pix') }}
group by data_base
having sum(case when lado = 'pagador' then valor end) != sum(case when lado = 'recebedor' then valor end)
    or sum(case when lado = 'pagador' then quantidade end) != sum(case when lado = 'recebedor' then quantidade end)
