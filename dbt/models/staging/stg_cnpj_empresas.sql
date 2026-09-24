-- =============================================================================
-- PT: Staging da tabela Empresas do CNPJ aberto. 1:1 com o bronze (ADR 0006).
--     Traz o que é da empresa, e não do estabelecimento: natureza jurídica e
--     porte. A razão social fica no bronze, porque nada a usa e, no caso do
--     MEI, ela é o nome de uma pessoa.
-- EN: Staging for the Companies table. 1:1 with bronze. Brings what belongs
--     to the company rather than the establishment: legal nature and size.
--     The company name stays in bronze: nothing uses it, and for individual
--     micro-entrepreneurs it is a person's name.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_cnpj_empresas') }}

)

select
    retrato,
    to_date(data_extracao) as data_extracao,
    {{ rotulo('cnpj_basico') }} as cnpj_basico,

    -- PT: Código de quatro dígitos. O primeiro dígito é o grupo (ontology/
    --     fontes_externas.yml, grupo_de_natureza_juridica).
    -- EN: Four-digit code; the first digit is the group.
    {{ rotulo('natureza_juridica') }} as natureza_juridica,

    -- PT: Não equivale ao porte do SCR (porte_da_empresa_na_receita).
    -- EN: Not equivalent to the SCR's company size.
    {{ rotulo('porte_empresa') }} as porte_empresa,

    arquivo_origem

from bronze
