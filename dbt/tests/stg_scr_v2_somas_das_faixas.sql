-- =============================================================================
-- PT: As duas identidades internas da V2 que o próprio arquivo declara:
--       carteira_a_vencer = soma das seis faixas a vencer;
--       carteira_vencida  = vencido de 15 a 90 dias + vencido acima de 90 dias.
--
--     É o teste que pega erro de conversão. Uma vírgula decimal mal tratada, um
--     separador trocado ou uma coluna deslocada na leitura do CSV aparecem aqui
--     como divergência, e não como número plausível e errado. Fecha em todas as
--     9.687.811 linhas.
--
-- EN: V2's two internal identities, declared by the file itself: performing
--     portfolio equals the six performing buckets, and overdue portfolio equals
--     the two overdue buckets. This is the test that catches conversion errors:
--     a mishandled decimal comma, a swapped separator or a column shifted while
--     reading the CSV shows up here as a divergence instead of as a plausible
--     wrong number. Holds in all 9,687,811 rows.
-- =============================================================================

select
    data_base,
    uf,
    modalidade,
    submodalidade,
    carteira_a_vencer,
    a_vencer_ate_90_dias + a_vencer_de_91_ate_360_dias
        + a_vencer_de_361_ate_1080_dias + a_vencer_de_1081_ate_1800_dias
        + a_vencer_de_1801_ate_5400_dias + a_vencer_acima_de_5400_dias as soma_das_faixas_a_vencer,
    carteira_vencida,
    vencido_de_15_ate_90_dias + vencido_acima_de_90_dias as soma_das_faixas_vencidas,
    arquivo_origem

from {{ ref('stg_scr_v2') }}

where carteira_a_vencer != a_vencer_ate_90_dias + a_vencer_de_91_ate_360_dias
        + a_vencer_de_361_ate_1080_dias + a_vencer_de_1081_ate_1800_dias
        + a_vencer_de_1801_ate_5400_dias + a_vencer_acima_de_5400_dias
   or carteira_vencida != vencido_de_15_ate_90_dias + vencido_acima_de_90_dias
