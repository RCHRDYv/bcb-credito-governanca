-- PT: Q17, a única resposta possível. Taxa de inadimplência do home equity
--     (0211), a única modalidade com garantia real declarada, contra o
--     restante da carteira de pessoa física, em todos os meses do recorte.
-- EN: Q17, the only possible answer: home equity (0211) default rate against
--     the rest of the individual portfolio, over every month in the window.
with mensal as (

    select
        data_base,
        100 * cast(sum(case when codigo_submodalidade = '0211' then carteira_inadimplencia else 0 end) as double)
            / cast(sum(case when codigo_submodalidade = '0211' then carteira_ativa else 0 end) as double)
            as taxa_home_equity_pct,
        100 * cast(sum(case when codigo_submodalidade <> '0211' then carteira_inadimplencia else 0 end) as double)
            / cast(sum(case when codigo_submodalidade <> '0211' then carteira_ativa else 0 end) as double)
            as taxa_restante_pf_pct
    from fct_carteira
    where cliente = 'PF'
    group by data_base

)

select
    count(*) as meses,
    sum(case when taxa_home_equity_pct < taxa_restante_pf_pct then 1 else 0 end) as meses_com_home_equity_abaixo,
    avg(taxa_home_equity_pct) as media_home_equity_pct,
    avg(taxa_restante_pf_pct) as media_restante_pf_pct,
    min(taxa_home_equity_pct) as minima_home_equity_pct,
    max(taxa_home_equity_pct) as maxima_home_equity_pct
from mensal
