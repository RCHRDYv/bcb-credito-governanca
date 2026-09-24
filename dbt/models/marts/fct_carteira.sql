-- =============================================================================
-- PT: O fato do esquema estrela, no grão cheio da V2: um registro por recorte
--     publicado, 9.687.811 no recorte de 2024 a 2026.
--
--     É o que a IA consulta no experimento, nas duas condições (ADR 0007).
--     Por isso ele fica no grão cheio, e não agregado: qualquer agregação
--     escolheria de antemão quais perguntas são fáceis, e o experimento
--     perderia justamente as que cruzam dimensões.
--
--     Leva só chaves e medidas. Os rótulos, as definições e os avisos moram
--     nas dimensões, e a consulta precisa fazer a junção, como num data
--     warehouse de verdade. Saem as oito faixas de vencimento, que nenhuma
--     pergunta usa, e as colunas de linhagem, que continuam no staging.
--
-- EN: The star schema's fact at V2's full grain: one record per published
--     slice, 9,687,811 in the 2024 to 2026 scope. It is what the AI queries in
--     the experiment, in both conditions (ADR 0007), which is why it is not
--     aggregated: any aggregation would decide in advance which questions are
--     easy. It carries keys and measures only; labels, definitions and warnings
--     live in the dimensions, and queries must join, as in a real warehouse.
-- =============================================================================

select

    -- -------------------------------------------------------------------------
    -- PT: Chaves das dimensões.
    -- EN: Dimension keys.
    -- -------------------------------------------------------------------------
    data_base,
    uf,
    segmento,
    codigo_submodalidade,
    porte_desambiguado,
    cnae_ocupacao_desambiguado,

    -- PT: Dimensões degeneradas: dois ou seis valores cada, sem atributo além
    --     do rótulo, então não justificam tabela própria.
    -- EN: Degenerate dimensions: two to six values each, with no attribute
    --     beyond the label, so they do not warrant their own table.
    cliente,
    origem,
    indexador,

    -- -------------------------------------------------------------------------
    -- PT: Contagem de operações. Nula onde o arquivo trazia -1, com a marca ao
    --     lado. Somar esta coluna num grupo com linhas suprimidas dá limite
    --     inferior, e não total.
    -- EN: Operation count. Null where the file had -1, flagged next to it.
    --     Summing it over a group with suppressed rows gives a lower bound.
    -- -------------------------------------------------------------------------
    numero_de_operacoes,
    contagem_suprimida,

    -- -------------------------------------------------------------------------
    -- PT: Medidas de carteira, em reais. Todas aditivas. Taxa é razão de somas,
    --     calculada na consulta, nunca média de taxas.
    -- EN: Portfolio measures, in reais. All additive. A rate is a ratio of
    --     sums, computed at query time, never an average of rates.
    -- -------------------------------------------------------------------------
    carteira_a_vencer,
    carteira_vencida,
    carteira_ativa,
    carteira_inadimplencia,
    ativo_problematico,

    -- -------------------------------------------------------------------------
    -- PT: Conformação com a taxonomia da V1, com a origem declarada ao lado.
    -- EN: Conformance with V1's taxonomy, with its provenance alongside.
    -- -------------------------------------------------------------------------
    modalidade_v1_efetiva,
    origem_da_modalidade_v1

from {{ ref('int_scr_v2_conformado') }}
