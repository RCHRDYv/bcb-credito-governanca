-- =============================================================================
-- PT: A identidade da V1. Ela não publica carteira_a_vencer nem
--     carteira_vencida, então a carteira ativa é a soma das seis faixas a vencer
--     com a coluna única de vencidos acima de 15 dias.
--
--     Fecha em todas as 29.471.540 linhas, sem uma única exceção. Vale registrar
--     o contraste: a fonte legada, mais antiga e com taxonomia mais pobre, é a
--     que tem consistência aritmética perfeita, enquanto a V2 tem uma linha
--     divergente.
--
-- EN: V1's identity. It publishes neither the performing nor the overdue
--     aggregate, so the active portfolio is the six performing buckets plus the
--     single over-15-days overdue column. It holds in all 29,471,540 rows with
--     no exception, in contrast with V2's one divergent row.
-- =============================================================================

select
    data_base,
    uf,
    cliente,
    modalidade,
    carteira_ativa,
    a_vencer_ate_90_dias + a_vencer_de_91_ate_360_dias
        + a_vencer_de_361_ate_1080_dias + a_vencer_de_1081_ate_1800_dias
        + a_vencer_de_1801_ate_5400_dias + a_vencer_acima_de_5400_dias
        + vencido_acima_de_15_dias as soma_das_parcelas,
    arquivo_origem

from {{ ref('stg_scr_v1') }}

where carteira_ativa != a_vencer_ate_90_dias + a_vencer_de_91_ate_360_dias
        + a_vencer_de_361_ate_1080_dias + a_vencer_de_1081_ate_1800_dias
        + a_vencer_de_1801_ate_5400_dias + a_vencer_acima_de_5400_dias
        + vencido_acima_de_15_dias
