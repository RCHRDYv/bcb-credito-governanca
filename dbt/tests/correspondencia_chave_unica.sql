-- =============================================================================
-- PT: A chave da correspondência precisa ser única. Se o mesmo recorte
--     aparecer duas vezes no seed, o join com a camada de staging duplica
--     linhas e infla a carteira, sem erro nenhum. É o tipo de falha que
--     aparece como "o total não fecha" semanas depois.
-- EN: The correspondence key must be unique. A duplicated slice in the seed
--     would fan out the join against staging and inflate the portfolio, with
--     no error at all.
-- =============================================================================

select
    codigo_submodalidade_v2,
    cliente,
    origem,
    count(*) as linhas
from {{ ref('correspondencia_modalidade_v2_v1') }}
group by all
having count(*) > 1
