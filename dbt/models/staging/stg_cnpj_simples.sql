-- =============================================================================
-- PT: Staging da tabela Simples do CNPJ aberto. 1:1 com o bronze (ADR 0006).
--     Traz a opção pelo MEI com as datas de entrada e de saída, que permitem
--     saber se a empresa era MEI no fim de cada mês.
-- EN: Staging for the Simples table. 1:1 with bronze. Brings the MEI option
--     with entry and exit dates, which tell whether a company was an MEI at
--     each month end.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_cnpj_simples') }}

)

select
    retrato,
    to_date(data_extracao) as data_extracao,
    {{ rotulo('cnpj_basico') }} as cnpj_basico,

    {{ rotulo('opcao_simples') }} as opcao_simples,
    {{ data_da_receita('data_opcao_simples') }} as data_opcao_simples,
    {{ data_da_receita('data_exclusao_simples') }} as data_exclusao_simples,

    {{ rotulo('opcao_mei') }} as opcao_mei,
    {{ data_da_receita('data_opcao_mei') }} as data_opcao_mei,
    {{ data_da_receita('data_exclusao_mei') }} as data_exclusao_mei,

    arquivo_origem

from bronze
