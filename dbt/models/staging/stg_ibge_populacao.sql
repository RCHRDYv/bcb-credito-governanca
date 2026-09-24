-- =============================================================================
-- PT: Staging da população residente estimada por UF, tabela 6579 do SIDRA.
--     1:1 com o bronze (ADR 0006). Os nomes de campo do SIDRA (V, D1C, D3C)
--     viram nomes que dizem o que são, e os números viram número. A sigla da
--     UF não vem do IBGE: a junção pelo código acontece no intermediate, com
--     a ontologia.
-- EN: Staging for estimated resident population by state, SIDRA table 6579.
--     1:1 with bronze. SIDRA field names become meaningful names and numbers
--     become numbers. The state abbreviation does not come from IBGE: the
--     join by code happens in intermediate, through the ontology.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_ibge_populacao') }}

)

select
    cast(trim(D3C) as int) as ano,
    trim(D1C) as codigo_ibge_uf,
    trim(D1N) as nome_uf,

    -- PT: 9324 é a população residente estimada. Mantida para o teste
    --     conferir que nenhuma outra variável entrou.
    -- EN: 9324 is estimated resident population.
    trim(D2C) as codigo_variavel,
    cast(trim(V) as bigint) as populacao,

    arquivo_origem,
    sha256_arquivo

from bronze
