-- PT: D24. Crescimento da massa de rendimento do trabalho do país, 2º tri de
--     2025 ao 2º tri de 2026.
-- EN: D24. Growth of the country's total labor income, Q2 2025 to Q2 2026.
with por_ano as (

    select ano, sum(massa_de_rendimento) as massa
    from fct_renda_do_trabalho
    where trimestre = 2
      and ano in (2025, 2026)
    group by ano

)

select
    max(case when ano = 2025 then massa end) as massa_2025,
    max(case when ano = 2026 then massa end) as massa_2026,
    100 * (cast(max(case when ano = 2026 then massa end) as double)
        / cast(max(case when ano = 2025 then massa end) as double) - 1) as crescimento_pct
from por_ano
