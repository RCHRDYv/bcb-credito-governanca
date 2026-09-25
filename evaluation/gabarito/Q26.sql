-- PT: Q26. Correlação entre a variação mensal da meta da Selic e a variação
--     mensal da taxa de inadimplência, com a inadimplência deslocada de 0 a
--     12 meses para frente. A defasagem de maior correlação é a candidata, e
--     a série curta limita a confiança.
-- EN: Q26. Correlation between monthly changes in the Selic target and in the
--     default rate, lagging default by 0 to 12 months. The highest one is the
--     candidate lag, and the short series limits confidence.
with mensal as (

    select
        f.data_base,
        cast(s.selic_meta as double) as selic_meta,
        100 * cast(sum(f.carteira_inadimplencia) as double) / cast(sum(f.carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira f
    join fct_selic s
        on s.data_base = f.data_base
    group by f.data_base, s.selic_meta

),

variacao as (

    select
        row_number() over (order by data_base) as indice,
        selic_meta - lag(selic_meta) over (order by data_base) as variacao_selic_pp,
        taxa_inadimplencia_pct - lag(taxa_inadimplencia_pct) over (order by data_base) as variacao_taxa_pp
    from mensal

),

defasagens as (

    select defasagem
    from (values (0), (1), (2), (3), (4), (5), (6), (7), (8), (9), (10), (11), (12)) as d(defasagem)

)

select
    d.defasagem as defasagem_em_meses,
    corr(selic.variacao_selic_pp, taxa.variacao_taxa_pp) as correlacao,
    count(selic.variacao_selic_pp + taxa.variacao_taxa_pp) as pares
from defasagens d
join variacao selic
    on 1 = 1
join variacao taxa
    on taxa.indice = selic.indice + d.defasagem
group by d.defasagem
order by d.defasagem
