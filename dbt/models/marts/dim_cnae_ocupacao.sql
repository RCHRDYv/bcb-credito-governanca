-- =============================================================================
-- PT: Dimensão de atividade econômica, 30 registros. Seção do CNAE para pessoa
--     jurídica e natureza da ocupação para pessoa física, com a chave
--     desambiguada pelo tipo de cliente. O rótulo ambíguo fica como atributo,
--     pelo mesmo motivo da dim_porte.
-- EN: Economic-activity dimension, 30 records: CNAE section for companies and
--     occupation nature for individuals, keyed by client type. The ambiguous
--     label stays as an attribute, for the same reason as in dim_porte.
-- =============================================================================

select
    valor_desambiguado as cnae_ocupacao_desambiguado,
    cliente,
    valor as cnae_ocupacao,
    taxonomia,
    aviso
from {{ ref('int_dim_cnae_ocupacao') }}
