-- PT: Q08. Inadimplência do rotativo do cartão (submodalidade 0204, e só
--     ela) no último mês, contra a média das taxas mensais. A pergunta pede
--     cinco anos, e a média usa todo o recorte disponível, que é menor.
-- EN: Q08. Revolving credit card default (submodality 0204 only) in the
--     latest month against the average of monthly rates over the available
--     window, which is shorter than the five years asked.
with mensal as (

    select
        data_base,
        100 * cast(sum(carteira_inadimplencia) as double) / cast(sum(carteira_ativa) as double)
            as taxa_inadimplencia_pct
    from fct_carteira
    where codigo_submodalidade = '0204'
    group by data_base

),

ultimo as (

    select data_base, taxa_inadimplencia_pct
    from mensal
    where data_base = (select max(data_base) from mensal)

),

historico as (

    select
        min(data_base) as inicio_da_media,
        count(*) as meses_na_media,
        avg(taxa_inadimplencia_pct) as media_das_taxas_mensais_pct
    from mensal

)

select
    ultimo.data_base as mes,
    ultimo.taxa_inadimplencia_pct as taxa_no_ultimo_mes_pct,
    historico.media_das_taxas_mensais_pct,
    historico.inicio_da_media,
    historico.meses_na_media,
    ultimo.taxa_inadimplencia_pct > historico.media_das_taxas_mensais_pct as acima_da_media
from ultimo
cross join historico
