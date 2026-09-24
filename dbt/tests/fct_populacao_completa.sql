-- =============================================================================
-- PT: Cada ano da população tem as 27 UFs, cada uma uma vez. Uma UF que não
--     casasse pelo código do IBGE sumiria na junção interna de fct_populacao,
--     e a carteira por habitante dela ficaria nula sem erro.
-- EN: Every population year has all 27 states, once each. A state failing to
--     match on the IBGE code would vanish in the inner join silently.
-- =============================================================================

select ano, count(*) as ufs, count(distinct uf) as ufs_distintas
from {{ ref('fct_populacao') }}
group by ano
having count(*) != 27 or count(distinct uf) != 27
