-- PT: D27. Parcela da carteira PF com renda indisponível (não informada),
--     julho de 2026.
-- EN: D27. Share of the individuals' portfolio with unavailable (unreported)
--     income, July 2026.
select
    100 * cast(sum(case when porte_desambiguado = 'PF - Indisponível' then carteira_ativa else 0 end) as double)
        / cast(sum(carteira_ativa) as double) as participacao_renda_indisponivel_pct
from fct_carteira
where cliente = 'PF'
  and data_base = date '2026-07-31'
