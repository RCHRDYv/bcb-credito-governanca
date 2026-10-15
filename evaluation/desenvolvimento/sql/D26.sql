-- PT: D26. Rendimento médio do trabalho em Roraima, 2º trimestre de 2026, com
--     o coeficiente de variação.
-- EN: D26. Average labor income in Roraima, Q2 2026, with its coefficient of
--     variation.
select
    rendimento_medio,
    cv_rendimento_medio
from fct_renda_do_trabalho
where uf = 'RR'
  and ano = 2026
  and trimestre = 2
