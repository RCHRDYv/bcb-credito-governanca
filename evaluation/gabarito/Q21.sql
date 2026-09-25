-- PT: Q21. Participação de instituições de pagamento e de fintechs na
--     carteira de cada modalidade, e o ganho em pontos percentuais. Vêm as
--     duas janelas: 12 meses e o recorte inteiro.
-- EN: Q21. Payment institutions' and fintechs' share of each modality's
--     portfolio, and the gain in percentage points, over both windows.
with por_modalidade as (

    select
        f.data_base,
        m.codigo_modalidade,
        m.modalidade,
        cast(sum(f.carteira_ativa) as double) as carteira_ativa,
        cast(sum(case when f.segmento = 'Instituição de pagamento' then f.carteira_ativa else 0 end) as double)
            as carteira_ip,
        cast(sum(case when f.segmento = 'Fintech' then f.carteira_ativa else 0 end) as double)
            as carteira_fintech
    from fct_carteira f
    join dim_modalidade m
        on m.codigo_submodalidade = f.codigo_submodalidade
    group by f.data_base, m.codigo_modalidade, m.modalidade

),

participacao as (

    select
        data_base,
        codigo_modalidade,
        modalidade,
        100 * carteira_ip / carteira_ativa as participacao_ip_pct,
        100 * carteira_fintech / carteira_ativa as participacao_fintech_pct
    from por_modalidade

),

limites as (

    select min(data_base) as primeiro, max(data_base) as ultimo from fct_carteira

)

select
    atual.codigo_modalidade,
    atual.modalidade,
    atual.participacao_ip_pct as participacao_ip_no_ultimo_mes_pct,
    atual.participacao_ip_pct - doze.participacao_ip_pct as ganho_ip_12_meses_pp,
    atual.participacao_ip_pct - inicio.participacao_ip_pct as ganho_ip_no_recorte_pp,
    atual.participacao_fintech_pct as participacao_fintech_no_ultimo_mes_pct,
    atual.participacao_fintech_pct - doze.participacao_fintech_pct as ganho_fintech_12_meses_pp,
    atual.participacao_fintech_pct - inicio.participacao_fintech_pct as ganho_fintech_no_recorte_pp
from limites
join participacao atual
    on atual.data_base = limites.ultimo
join participacao doze
    on doze.codigo_modalidade = atual.codigo_modalidade
   and doze.data_base = last_day(limites.ultimo - interval '12' month)
join participacao inicio
    on inicio.codigo_modalidade = atual.codigo_modalidade
   and inicio.data_base = limites.primeiro
order by atual.codigo_modalidade
