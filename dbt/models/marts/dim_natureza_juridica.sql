-- =============================================================================
-- PT: Dimensão do grupo de natureza jurídica, 6 registros (os cinco grupos e o "não informada"), gerada da
--     ontologia pelo seed ontologia_fonte_externa_valor. Existe porque nem
--     todo CNPJ ativo é empresa que produz: há órgãos públicos, entidades sem
--     fins lucrativos e organizações internacionais. Qual grupo entra no
--     denominador é escolha da camada de decisão (issue #26).
-- EN: Legal nature group dimension, 5 records, generated from the ontology.
--     Not every active CNPJ is a producing company; which groups enter the
--     denominator is the decision layer's choice.
-- =============================================================================

select
    v.codigo as grupo_natureza_juridica,
    v.rotulo as natureza_juridica
from {{ ref('ontologia_fonte_externa_valor') }} as v
where v.conceito = 'grupo_de_natureza_juridica'
