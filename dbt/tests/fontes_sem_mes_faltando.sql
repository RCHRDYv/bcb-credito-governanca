-- =============================================================================
-- PT: A série mensal de cada fonte não pode ter buraco. Um mês que falhou no
--     download ou no envio some do bronze sem gerar erro nenhum, e toda
--     variação calculada por cima dele fica errada em silêncio.
--     O teste falha se houver algum mês faltando entre o primeiro e o último.
-- EN: Each source's monthly series must have no gap. A month that failed to
--     download or upload vanishes from bronze without raising any error, and
--     every change computed over it goes silently wrong.
--     The test fails if any month is missing between the first and the last.
-- =============================================================================

with meses as (

    select 'v2' as versao, to_date(trim(data_base)) as data_base
    from {{ source('bcb_scr', 'bronze_scr_v2') }}
    group by all

    union all

    select 'v1' as versao, to_date(trim(data_base)) as data_base
    from {{ source('bcb_scr', 'bronze_scr_v1') }}
    group by all

),

limites as (

    select versao, min(data_base) as primeiro, max(data_base) as ultimo
    from meses
    group by versao

),

esperados as (

    select
        versao,
        last_day(add_months(primeiro, n)) as data_base
    from limites
    -- PT: months_between entre dois últimos dias de mês é sempre inteiro.
    -- EN: months_between two month-end dates is always a whole number.
    lateral view explode(
        sequence(0, cast(months_between(ultimo, primeiro) as int))
    ) meses_seq as n

)

select e.versao, e.data_base as mes_faltando
from esperados e
left join meses m
    on m.versao = e.versao
   and m.data_base = e.data_base
where m.data_base is null
