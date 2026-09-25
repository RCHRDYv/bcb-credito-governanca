-- PT: Q38, leitura na V1 (fct_carteira_v1). Variação de cada medida no mês da mudança de
--     critério do ativo problemático (o mês que a dim_tempo marca como não
--     comparável com o anterior), contra a menor e a maior variação mensal
--     dos outros meses do recorte.
-- EN: Q38, reading on V1. Each measure's change in the month of the problem-
--     asset criterion change, against the smallest and largest monthly change
--     in the other months of the window.
with mensal as (

    select
        data_base,
        cast(sum(carteira_ativa) as double) as carteira_ativa,
        cast(sum(carteira_inadimplida_arrastada) as double) as carteira_inadimplida,
        cast(sum(ativo_problematico) as double) as ativo_problematico
    from fct_carteira_v1
    group by data_base

),

medidas as (

    select data_base, 'carteira_ativa' as medida, carteira_ativa as valor from mensal
    union all
    select data_base, 'carteira_inadimplida', carteira_inadimplida from mensal
    union all
    select data_base, 'ativo_problematico', ativo_problematico from mensal
    union all
    select data_base, 'ativo_problematico_sem_atraso_acima_de_90_dias', ativo_problematico - carteira_inadimplida
    from mensal

),

variacoes as (

    select
        medida,
        data_base,
        lag(valor) over (partition by medida order by data_base) as valor_no_mes_anterior,
        valor,
        100 * (valor / lag(valor) over (partition by medida order by data_base) - 1) as variacao_pct
    from medidas

),

quebra as (

    select data_base
    from dim_tempo
    where not ativo_problematico_comparavel_com_mes_anterior

),

outros_meses as (

    select v.medida, min(v.variacao_pct) as menor_variacao_pct, max(v.variacao_pct) as maior_variacao_pct
    from variacoes v
    cross join quebra
    where v.data_base <> quebra.data_base
      and v.variacao_pct is not null
    group by v.medida

)

select
    v.medida,
    v.data_base as mes_da_quebra,
    v.valor_no_mes_anterior,
    v.valor as valor_no_mes_da_quebra,
    v.variacao_pct as variacao_na_quebra_pct,
    o.menor_variacao_pct as menor_variacao_nos_outros_meses_pct,
    o.maior_variacao_pct as maior_variacao_nos_outros_meses_pct
from variacoes v
join quebra
    on v.data_base = quebra.data_base
join outros_meses o
    on o.medida = v.medida
order by v.medida
