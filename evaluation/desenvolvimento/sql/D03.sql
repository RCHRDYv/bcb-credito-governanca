-- PT: D03. População de Pernambuco em 2025.
-- EN: D03. Population of Pernambuco in 2025.
select
    ano as ano_da_populacao,
    populacao
from fct_populacao
where uf = 'PE'
  and ano = 2025
