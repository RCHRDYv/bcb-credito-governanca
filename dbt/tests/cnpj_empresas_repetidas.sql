-- =============================================================================
-- PT: A tabela Empresas do retrato de set/2026 traz uma empresa duas vezes,
--     no mesmo arquivo: 08314885, com uma linha completa e outra vazia
--     (natureza 0000, sem razão social e sem porte). Medido em 2026-09-24. O
--     intermediate fica com a linha completa.
--
--     O teste avisa com uma repetição e falha com duas, no mesmo padrão da
--     linha publicada com erro em stg_scr_v2_carteira_ativa: a exceção
--     conhecida não trava o build, e uma segunda não passa em silêncio.
-- EN: The Companies table repeats one company in the same file, with one
--     complete row and one empty row. The test warns at one repetition and
--     fails at two, so a second one does not pass silently.
-- =============================================================================

{{ config(warn_if='>0', error_if='>1') }}

select retrato, cnpj_basico, count(*) as linhas
from {{ ref('stg_cnpj_empresas') }}
group by retrato, cnpj_basico
having count(*) > 1
