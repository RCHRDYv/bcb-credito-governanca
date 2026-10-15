-- PT: D04. Carteira a vencer de Goiás no último mês da tabela.
-- EN: D04. Goiás's current (not overdue) portfolio in the table's latest
--     month.
select
    max(data_base) as mes,
    sum(carteira_a_vencer) as carteira_a_vencer
from fct_carteira
where uf = 'GO'
  and data_base = (select max(data_base) from fct_carteira)
