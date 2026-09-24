-- =============================================================================
-- PT: Dimensão de UF, 27 registros, gerada da ontologia pelo seed
--     ontologia_dimensao.
--
--     A definição normativa viaja em coluna de propósito: é nela que está o
--     aviso de que a UF é o domicílio da pessoa física ou a sede da pessoa
--     jurídica, e não o local onde o crédito foi tomado ou usado. Assim o
--     aviso chega a quem consulta o mart sem abrir a documentação.
--
--     O código do IBGE é a chave pela qual as fontes externas chegam à UF. A
--     população e as empresas ativas, que a issue #25 trouxe, não moram aqui:
--     elas mudam no tempo, e por isso são fatos (fct_populacao e
--     fct_empresas_ativas).
--
-- EN: State dimension, 27 records, generated from the ontology. The normative
--     definition travels as a column on purpose: it holds the warning that the
--     state is the individual's domicile or the company's headquarters. The
--     IBGE code is how external sources reach the state. Population and active
--     companies change over time, so they are facts, not attributes here.
-- =============================================================================

select
    valor as uf,
    significado as nome_da_uf,
    codigo_ibge,
    definicao_da_dimensao as definicao_da_uf
from {{ ref('ontologia_dimensao') }}
where dimensao = 'uf'
