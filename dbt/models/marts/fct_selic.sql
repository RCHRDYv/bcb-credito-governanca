-- =============================================================================
-- PT: Fato da Selic: a meta definida pelo Copom vigente no fim de cada mês do
--     SCR, em % ao ano. Serve às perguntas Q25 e Q26 (issue #37, ADR 0010).
--
--     É a meta, e não a taxa efetiva, porque a Q25 registrada em inglês pede
--     a "Selic policy rate". E é o valor vigente no último dia do mês, que é
--     a data-base do SCR, e não a média do mês: num mês com reunião do
--     Copom, a média seria uma taxa que nunca vigorou.
--
--     O valor é buscado como "o último publicado até a data-base", e não pela
--     data exata, para não depender de a série ter linha em todo dia.
--     data_do_valor diz de que dia ele veio.
--
-- EN: Selic fact: the Copom target in force at each SCR month end, in % per
--     year. The target, not the effective rate, because Q25 asks for the
--     "Selic policy rate"; and the value in force on the month's last day,
--     not the monthly mean, which in a month with a Copom meeting would be a
--     rate that never applied. Looked up as the latest value up to the
--     reference date; data_do_valor says which day it came from.
-- =============================================================================

with meses as (

    select distinct data_base from {{ ref('stg_scr_v2') }}

),

meta as (

    select data, valor
    from {{ ref('stg_sgs_series') }}
    where codigo_serie = 432

),

candidatos as (

    select
        m.data_base,
        s.data as data_do_valor,
        s.valor as selic_meta,
        row_number() over (partition by m.data_base order by s.data desc) as ordem
    from meses as m
    inner join meta as s
        on s.data <= m.data_base

)

select data_base, selic_meta, data_do_valor
from candidatos
where ordem = 1
