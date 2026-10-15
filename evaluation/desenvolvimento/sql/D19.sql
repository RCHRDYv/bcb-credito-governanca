-- PT: D19. Crescimento da carteira de aposentados e pensionistas de julho de
--     2025 a julho de 2026.
-- EN: D19. Growth of the retirees' and pensioners' portfolio, July 2025 to
--     July 2026.
with por_mes as (

    select data_base, sum(carteira_ativa) as carteira_ativa
    from fct_carteira
    where cnae_ocupacao_desambiguado = 'PF - Aposentado/pensionista'
      and data_base in (date '2025-07-31', date '2026-07-31')
    group by data_base

)

select
    max(case when data_base = date '2025-07-31' then carteira_ativa end) as carteira_julho_2025,
    max(case when data_base = date '2026-07-31' then carteira_ativa end) as carteira_julho_2026,
    100 * (cast(max(case when data_base = date '2026-07-31' then carteira_ativa end) as double)
        / cast(max(case when data_base = date '2025-07-31' then carteira_ativa end) as double) - 1) as crescimento_pct
from por_mes
