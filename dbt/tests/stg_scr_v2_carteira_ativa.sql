-- =============================================================================
-- PT: A identidade principal da V2: carteira ativa = a vencer + vencida. É a
--     própria definição da métrica ("Somatório da carteira a vencer e da
--     carteira vencida", Metodologia V2, seção 3.w).
--
--     Este teste tem uma exceção conhecida, medida em 2026-09-23: UMA linha
--     entre 9.687.811 não fecha, e ela vem assim do arquivo publicado.
--
--       data_base 2024-12-31, PR, Fintech, PF, "Mais de 1 a 2 salários mínimos",
--       Empréstimos, "Crédito pessoal - com consignação em folha de pagam.",
--       Sem destinação específica, Prefixado, 63 operações.
--       A vencer 345.658,37 + vencida 2.844,62 = 348.502,99, contra carteira
--       ativa publicada de 345.414,46. Diferença de R$ 3.088,53, e a carteira a
--       vencer sozinha já é maior que a ativa.
--
--     Por isso a severidade é graduada em vez de a exceção ser excluída por
--     filtro: uma linha continua aparecendo como aviso em cada execução, e a
--     segunda linha divergente falha o build. Excluir a exceção por chave
--     esconderia a mudança justamente no dia em que ela acontecesse, e é o
--     oposto do que este projeto defende.
--
-- EN: V2's main identity: active portfolio equals performing plus overdue,
--     which is the metric's own definition. The test has one known exception,
--     measured on 2026-09-23: one row out of 9,687,811 does not add up, and it
--     comes that way from the published file (Dec/2024, Paraná, Fintech, PF,
--     payroll-deducted personal loan: 345,658.37 + 2,844.62 against a published
--     active portfolio of 345,414.46).
--
--     Severity is therefore graduated instead of the exception being filtered
--     out: one row keeps showing up as a warning on every run, and a second
--     divergent row fails the build. Excluding the exception by key would hide
--     the change on the very day it happened.
-- =============================================================================

{{ config(warn_if = '>0', error_if = '>1') }}

select
    data_base,
    uf,
    segmento,
    cliente,
    modalidade,
    submodalidade,
    carteira_a_vencer,
    carteira_vencida,
    carteira_ativa,
    carteira_a_vencer + carteira_vencida - carteira_ativa as diferenca,
    arquivo_origem

from {{ ref('stg_scr_v2') }}

where carteira_ativa != carteira_a_vencer + carteira_vencida
