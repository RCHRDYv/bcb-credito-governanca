-- PT: Q19. Financiamentos rurais (modalidade 08) contra o restante da
--     carteira de pessoa jurídica, em crescimento e em inadimplência. O
--     crédito agroindustrial (0440) está em Financiamentos desde 2017 e fica
--     no restante. Vêm as duas janelas: 12 meses e o recorte inteiro.
-- EN: Q19. Rural financing (modality 08) against the rest of the corporate
--     portfolio; agro-industrial credit (0440) sits in Financiamentos since
--     2017. Both windows: 12 months and the whole window.
with mensal as (

    select
        f.data_base,
        case when m.codigo_modalidade = '08' then 'Financiamentos rurais' else 'Restante da carteira PJ' end
            as grupo,
        cast(sum(f.carteira_ativa) as double) as carteira_ativa,
        100 * cast(sum(f.carteira_inadimplencia) as double) / cast(sum(f.carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    where f.cliente = 'PJ'
    group by f.data_base, case when m.codigo_modalidade = '08' then 'Financiamentos rurais' else 'Restante da carteira PJ' end

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

)

select
    atual.grupo,
    100 * (atual.carteira_ativa / doze.carteira_ativa - 1) as crescimento_12_meses_pct,
    100 * (atual.carteira_ativa / inicio.carteira_ativa - 1) as crescimento_no_recorte_pct,
    atual.taxa_inadimplencia_pct as taxa_no_ultimo_mes_pct,
    atual.taxa_inadimplencia_pct - doze.taxa_inadimplencia_pct as variacao_taxa_12_meses_pp,
    atual.taxa_inadimplencia_pct - inicio.taxa_inadimplencia_pct as variacao_taxa_no_recorte_pp
from limites
join mensal atual
    on atual.data_base = limites.ultimo
join mensal doze
    on doze.grupo = atual.grupo
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
join mensal inicio
    on inicio.grupo = atual.grupo
   and inicio.data_base = limites.primeiro
order by atual.grupo
