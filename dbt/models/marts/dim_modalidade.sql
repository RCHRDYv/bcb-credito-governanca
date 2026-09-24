-- =============================================================================
-- PT: Dimensão de modalidade para o esquema estrela, 66 registros. É a mesma
--     da camada intermediária, que já vem gerada da ontologia. A chave é o
--     código do Anexo 3, e os rótulos exatos do dado ficam como atributo.
--
--     Segue a linha de neutralidade do ADR 0007: a dimensão traz código,
--     rótulo, nome oficial, definição e confiança, e nenhuma coluna que
--     responda uma pergunta específica. Não existe aqui uma marca de "é cartão
--     de crédito", por exemplo: o cartão está em cinco submodalidades de três
--     modalidades, e descobrir isso é justamente o que o experimento mede.
--
-- EN: Modality dimension for the star schema, 66 records, taken from the
--     ontology-generated intermediate dimension. Following the ADR 0007
--     neutrality line, it carries code, label, official name, definition and
--     confidence, and no column answering a specific question: there is no
--     "is credit card" flag, because finding the five card sub-modalities is
--     exactly what the experiment measures.
-- =============================================================================

select
    codigo_submodalidade,
    codigo_modalidade,
    modalidade,
    submodalidade,
    nome_oficial_modalidade,
    nome_oficial_submodalidade,
    definicao,
    confianca,
    sem_definicao_oficial,
    fonte
from {{ ref('int_dim_modalidade') }}
