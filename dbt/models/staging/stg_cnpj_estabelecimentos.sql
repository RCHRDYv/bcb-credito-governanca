-- =============================================================================
-- PT: Staging da tabela Estabelecimentos do CNPJ aberto da Receita.
--
--     Relação 1:1 com o bronze, como todo staging do projeto (ADR 0006):
--     mesma quantidade de linhas, nos três retratos, com matrizes e filiais,
--     ativas e baixadas. Filtrar matriz ativa é interpretação, e fica no
--     intermediate.
--
--     A diferença para o staging do SCR é a seleção de colunas. O bronze
--     guarda o estabelecimento inteiro, incluindo nome fantasia, endereço,
--     telefone e e-mail, e nada disso é usado. Esses campos param no bronze e
--     não chegam a nenhuma tabela que o projeto consulta.
--
-- EN: Staging for the Establishments table of Receita's open CNPJ data. 1:1
--     with bronze, like every staging model (ADR 0006): all three snapshots,
--     head offices and branches, active and closed. Filtering active head
--     offices is interpretation and belongs in intermediate. Only the columns
--     used are selected: trade name, address, phone and e-mail stop at bronze.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_cnpj_estabelecimentos') }}

)

select

    -- -------------------------------------------------------------------------
    -- PT: Retrato e linhagem. O retrato é o mês da publicação ("2026-09"), e a
    --     data de extração é o dia em que a Receita gerou o arquivo.
    -- EN: Snapshot and lineage.
    -- -------------------------------------------------------------------------
    retrato,
    to_date(data_extracao) as data_extracao,

    -- -------------------------------------------------------------------------
    -- PT: Identificação. cnpj_basico identifica a empresa, e cnpj_ordem o
    --     estabelecimento dentro dela.
    -- EN: Identification. cnpj_basico identifies the company, cnpj_ordem the
    --     establishment within it.
    -- -------------------------------------------------------------------------
    {{ rotulo('cnpj_basico') }} as cnpj_basico,
    {{ rotulo('cnpj_ordem') }} as cnpj_ordem,
    {{ rotulo('cnpj_dv') }} as cnpj_dv,

    -- PT: Códigos do leiaute, mantidos como código. Ver
    --     ontology/fontes_externas.yml, empresa_ativa.
    -- EN: Layout codes, kept as codes.
    {{ rotulo('identificador_matriz_filial') }} as identificador_matriz_filial,
    {{ rotulo('situacao_cadastral') }} as situacao_cadastral,
    {{ rotulo('motivo_situacao_cadastral') }} as motivo_situacao_cadastral,

    -- PT: As duas datas que permitem reconstruir o estoque de cada mês.
    -- EN: The two dates that allow rebuilding each month's stock.
    {{ data_da_receita('data_situacao_cadastral') }} as data_situacao_cadastral,
    {{ data_da_receita('data_inicio_atividade') }} as data_inicio_atividade,

    {{ rotulo('cnae_fiscal_principal') }} as cnae_fiscal_principal,
    {{ rotulo('uf') }} as uf,

    arquivo_origem

from bronze
