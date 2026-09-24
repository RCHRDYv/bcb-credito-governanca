-- =============================================================================
-- PT: Dimensão do porte da empresa no CNPJ, 4 registros, gerada da ontologia
--     pelo seed ontologia_fonte_externa_valor.
--
--     Não se liga à dim_porte, de propósito. O porte da Receita (micro, EPP,
--     demais) e o porte de pessoa jurídica do SCR (micro, pequeno, médio,
--     grande) têm critérios diferentes, e não existe correspondência oficial.
--     O aviso viaja em coluna, para chegar a quem consulta.
--
-- EN: Company size in the CNPJ register, 4 records, generated from the
--     ontology. Deliberately unlinked to dim_porte: Receita's and the SCR's
--     size classes use different criteria and have no official mapping.
-- =============================================================================

select
    v.codigo as porte_empresa,
    v.rotulo as porte_receita,
    'Não equivale ao porte de pessoa jurídica do SCR (dim_porte): critérios diferentes e sem correspondência oficial.' as aviso
from {{ ref('ontologia_fonte_externa_valor') }} as v
where v.conceito = 'porte_da_empresa_na_receita'
