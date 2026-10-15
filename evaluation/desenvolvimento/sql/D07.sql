-- PT: D07. Meses distintos com dado de carteira.
-- EN: D07. Distinct months with portfolio data.
select count(distinct data_base) as meses_com_dado
from fct_carteira
