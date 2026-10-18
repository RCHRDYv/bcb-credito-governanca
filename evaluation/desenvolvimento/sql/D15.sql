-- PT: D15. Participação das operações pós-fixadas na carteira PJ, julho de
--     2026.
-- EN: D15. Share of post-fixed operations in the corporate portfolio, July
--     2026.
select
    100 * cast(sum(case when indexador = 'Pós-fixado' then carteira_ativa else 0 end) as double)
        / cast(sum(carteira_ativa) as double) as participacao_pos_fixado_pct
from fct_carteira
where cliente = 'PJ'
  and data_base = date '2026-07-31'
