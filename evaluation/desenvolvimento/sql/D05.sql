-- PT: D05. Rendimento médio do trabalho no Rio Grande do Norte, 2º trimestre
--     de 2026.
-- EN: D05. Average labor income in Rio Grande do Norte, Q2 2026.
select rendimento_medio
from fct_renda_do_trabalho
where uf = 'RN'
  and ano = 2026
  and trimestre = 2
