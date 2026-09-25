-- PT: Q34. Crédito habitacional fora do SFH (submodalidade 0902) no último
--     mês. O filtro é pelo código, porque o rótulo traz um caractere de
--     controle invisível no lugar do traço.
-- EN: Q34. Housing credit outside SFH (submodality 0902) in the latest month,
--     filtered by code because the label carries an invisible control
--     character in place of the dash.
select
    max(data_base) as mes,
    sum(carteira_ativa) as carteira_ativa
from fct_carteira
where codigo_submodalidade = '0902'
  and data_base = (select max(data_base) from fct_carteira)
