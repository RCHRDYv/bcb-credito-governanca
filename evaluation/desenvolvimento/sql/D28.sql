-- PT: D28. Meta da Selic no fim de cada trimestre de 2025.
-- EN: D28. Selic target at the end of each quarter of 2025.
select
    data_base as mes,
    selic_meta as meta_selic_pct
from fct_selic
where data_base in (date '2025-03-31', date '2025-06-30', date '2025-09-30', date '2025-12-31')
order by data_base
