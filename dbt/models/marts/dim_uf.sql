-- =============================================================================
-- PT: Dimensão de UF, 27 registros, gerada da ontologia pelo seed
--     ontologia_dimensao.
--
--     A definição normativa viaja em coluna de propósito: é nela que está o
--     aviso de que a UF é o domicílio da pessoa física ou a sede da pessoa
--     jurídica, e não o local onde o crédito foi tomado ou usado. Assim o
--     aviso chega a quem consulta o mart sem abrir a documentação.
--
--     A issue #25 acrescenta população e empresas ativas a esta dimensão, que
--     são os denominadores das perguntas Q11, Q12 e Q14.
--
-- EN: State dimension, 27 records, generated from the ontology. The normative
--     definition travels as a column on purpose: it holds the warning that the
--     state is the individual's domicile or the company's headquarters, not
--     where the credit was taken or used. Issue #25 adds population and active
--     companies here.
-- =============================================================================

select
    valor as uf,
    definicao_da_dimensao as definicao_da_uf
from {{ ref('ontologia_dimensao') }}
where dimensao = 'uf'
