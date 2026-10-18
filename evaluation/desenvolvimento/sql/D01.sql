-- PT: D01. A meta da Selic no último mês da própria tabela.
-- EN: D01. The Selic target in the table's latest month.
select
    data_base as mes,
    selic_meta as meta_selic_pct
from fct_selic
where data_base = (select max(data_base) from fct_selic)
