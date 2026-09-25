-- =============================================================================
-- PT: A classificação da matriz é coerente com a própria regra (ADR 0014):
--     - toda célula avaliada tem quadrante, carteira acima do corte, os dois
--       meses de comparação e o denominador de empresas;
--     - toda célula fora da matriz está marcada como "não avaliada", com o
--       motivo, e sem custo de errar.
--     Uma linha aqui quer dizer que uma célula pequena ou incompleta entrou
--     na recomendação, ou que uma célula válida ficou de fora sem motivo.
-- EN: The matrix classification is consistent with its own rule: every rated
--     cell has a quadrant, a portfolio above the cut, both comparison months
--     and a company denominator; every unrated cell is marked with a reason
--     and carries no cost.
-- =============================================================================

select uf, codigo_modalidade, quadrante, motivo_nao_avaliada
from {{ ref('mrt_decisao') }}
where (
        avaliada
        and (
            quadrante = 'não avaliada'
            or carteira_ativa < {{ var('decisao_carteira_minima') }}
            or variacao_taxa_inadimplencia is null
            or empresas is null
            or custo_do_risco is null
        )
    )
    or (
        not avaliada
        and (
            quadrante != 'não avaliada'
            or motivo_nao_avaliada is null
            or custo_de_nao_entrar is not null
            or custo_do_risco is not null
        )
    )
