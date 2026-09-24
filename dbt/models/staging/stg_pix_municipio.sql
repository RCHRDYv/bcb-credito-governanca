-- =============================================================================
-- PT: Staging do PIX por município (issue #36). 1:1 com o bronze (ADR 0006):
--     os nomes da API viram nomes que dizem o que são, o mês AAAAMM vira a
--     data-base de fim de mês que o SCR usa, valores viram decimal e
--     contagens viram inteiro. A linha "N/D", sem município nem UF, continua
--     aqui: o total nacional depende dela.
-- EN: Staging for PIX by municipality. 1:1 with bronze: API names become
--     meaningful names, the YYYYMM month becomes the SCR's month-end
--     reference date, values become decimals and counts integers. The "N/D"
--     row, with no municipality or state, stays: the national total needs it.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_pix_municipio') }}

)

select
    cast(AnoMes as int) as ano_mes,
    last_day(to_date(AnoMes, 'yyyyMM')) as data_base,

    Municipio_Ibge as codigo_ibge_municipio,
    Municipio as municipio,
    Estado_Ibge as codigo_ibge_uf,
    Estado as nome_uf,

    -- PT: valor em reais e quantidade de transações, pelos dois lados
    -- EN: value in reais and transaction count, for both sides
    cast(VL_PagadorPF as decimal(20, 2)) as valor_pagador_pf,
    cast(VL_PagadorPJ as decimal(20, 2)) as valor_pagador_pj,
    cast(VL_RecebedorPF as decimal(20, 2)) as valor_recebedor_pf,
    cast(VL_RecebedorPJ as decimal(20, 2)) as valor_recebedor_pj,
    cast(QT_PagadorPF as bigint) as quantidade_pagador_pf,
    cast(QT_PagadorPJ as bigint) as quantidade_pagador_pj,
    cast(QT_RecebedorPF as bigint) as quantidade_recebedor_pf,
    cast(QT_RecebedorPJ as bigint) as quantidade_recebedor_pj,

    -- PT: pessoas distintas que pagaram ou receberam no mês, no município
    -- EN: distinct people who paid or received in the month, in the municipality
    cast(QT_PES_PagadorPF as bigint) as pessoas_pagador_pf,
    cast(QT_PES_PagadorPJ as bigint) as pessoas_pagador_pj,
    cast(QT_PES_RecebedorPF as bigint) as pessoas_recebedor_pf,
    cast(QT_PES_RecebedorPJ as bigint) as pessoas_recebedor_pj,

    to_date(data_extracao) as data_extracao,
    arquivo_origem

from bronze
