-- =============================================================================
-- PT: Dimensão de porte, 14 registros para 13 valores. A chave é o porte
--     desambiguado pelo tipo de cliente, no formato que a V1 usava, porque a
--     coluna carrega duas taxonomias: faixa de renda para pessoa física e
--     tamanho de empresa para pessoa jurídica.
--
--     O rótulo ambíguo continua como atributo, de propósito. Agrupar por ele
--     reproduz a armadilha, e o experimento mede se a IA cai nela.
--
-- EN: Client-size dimension, 14 records for 13 values, keyed by the size
--     disambiguated by client type. The ambiguous label stays as an attribute
--     on purpose: grouping by it reproduces the trap the experiment measures.
-- =============================================================================

select
    valor_desambiguado as porte_desambiguado,
    cliente,
    valor as porte,
    taxonomia,
    aviso
from {{ ref('int_dim_porte') }}
