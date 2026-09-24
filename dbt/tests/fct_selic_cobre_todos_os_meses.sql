-- =============================================================================
-- PT: Todo mês do SCR tem a meta da Selic, e ela é a do próprio último dia do
--     mês. Um mês sem linha, ou com valor de um dia anterior, quer dizer que
--     a série parou de chegar ou mudou de forma, e a Q26 mediria defasagem
--     sobre um dado velho sem perceber.
-- EN: Every SCR month has the Selic target, taken from its own last day. A
--     missing month, or a value from an earlier day, means the series stopped
--     or changed shape.
-- =============================================================================

select t.data_base, s.data_do_valor
from {{ ref('dim_tempo') }} as t
left join {{ ref('fct_selic') }} as s
    on s.data_base = t.data_base
where s.data_base is null
   or s.data_do_valor != t.data_base
