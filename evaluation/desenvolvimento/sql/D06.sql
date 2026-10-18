-- PT: D06. Carteira vencida do país no último mês da tabela.
-- EN: D06. Country's overdue portfolio in the table's latest month.
select
    max(data_base) as mes,
    sum(carteira_vencida) as carteira_vencida
from fct_carteira
where data_base = (select max(data_base) from fct_carteira)
