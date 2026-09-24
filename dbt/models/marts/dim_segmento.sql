-- =============================================================================
-- PT: Dimensão de segmento da instituição financeira, 8 registros, gerada da
--     ontologia pelo seed ontologia_dimensao. A composição de cada segmento,
--     por exemplo que "Fintech" reúne Sociedade de Empréstimo entre Pessoas e
--     Sociedade de Crédito Direto, fica na ontologia, e não aqui, pela linha de
--     neutralidade do ADR 0007.
-- EN: Financial-institution segment dimension, 8 records, generated from the
--     ontology. Each segment's composition stays in the ontology rather than
--     here, per the ADR 0007 neutrality line.
-- =============================================================================

select
    valor as segmento,
    definicao_da_dimensao as definicao_do_segmento
from {{ ref('ontologia_dimensao') }}
where dimensao = 'segmento'
