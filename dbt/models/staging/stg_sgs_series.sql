-- =============================================================================
-- PT: Staging das séries do SGS do BCB (issue #37). 1:1 com o bronze (ADR
--     0006): a data em DD/MM/AAAA vira data, e o valor vira número. Hoje a
--     única série é a meta da Selic (432), em % ao ano.
-- EN: Staging for BCB SGS series. 1:1 with bronze: the DD/MM/YYYY date
--     becomes a date and the value a number. Today the only series is the
--     Selic target (432), in % per year.
-- =============================================================================

with bronze as (

    select * from {{ source('externas', 'bronze_sgs_series') }}

)

select
    cast(codigo_serie as int) as codigo_serie,
    serie,
    to_date(trim(data), 'dd/MM/yyyy') as data,
    cast(trim(valor) as decimal(9, 4)) as valor,
    to_date(data_extracao) as data_extracao,
    arquivo_origem,
    sha256_arquivo
from bronze
