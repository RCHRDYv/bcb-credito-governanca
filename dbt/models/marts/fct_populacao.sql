-- =============================================================================
-- PT: Fato de população: população residente estimada por UF e ano, do IBGE
--     (tabela 6579 do SIDRA). Denominador das perguntas Q11 e Q12.
--
--     O grão é o ano, e não o mês: o IBGE publica uma estimativa por ano,
--     com referência em 1º de julho. Para cruzar com a carteira mensal, a
--     junção é pelo ano da data-base, sem interpolar (ontology/
--     fontes_externas.yml, populacao_residente_estimada).
--
--     A UF chega pelo código do IBGE, que está na ontologia.
--
-- EN: Population fact: estimated resident population by state and year, from
--     IBGE. The grain is the year: IBGE publishes one estimate per year, dated
--     July 1st. Joining to the monthly portfolio goes through the reference
--     date's year, with no interpolation.
-- =============================================================================

select
    p.ano,
    u.valor as uf,
    p.populacao
from {{ ref('stg_ibge_populacao') }} as p
inner join {{ ref('ontologia_dimensao') }} as u
    on u.dimensao = 'uf' and u.codigo_ibge = p.codigo_ibge_uf
