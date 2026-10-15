-- PT: D29. Linhas de carteira da base em junho e em julho de 2025.
-- EN: D29. Portfolio rows in the data in June and July 2025.
select
    data_base as mes,
    count(*) as recortes,
    sum(carteira_ativa) as carteira_ativa
from fct_carteira
where data_base in (date '2025-06-30', date '2025-07-31')
group by data_base
order by data_base
