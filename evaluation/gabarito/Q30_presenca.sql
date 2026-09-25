-- PT: Q30, parte 1. Submodalidades da V2 que não aparecem em todos os meses
--     do recorte: entram, saem ou falham meses no meio da série.
-- EN: Q30, part 1. V2 submodalities missing from some months of the window.
with presenca as (

    select
        codigo_submodalidade,
        count(distinct data_base) as meses_com_dado,
        min(data_base) as primeiro_mes,
        max(data_base) as ultimo_mes
    from fct_carteira
    group by codigo_submodalidade

),

total as (

    select count(distinct data_base) as meses_no_recorte from fct_carteira

)

select
    p.codigo_submodalidade,
    m.modalidade,
    m.submodalidade,
    p.meses_com_dado,
    total.meses_no_recorte,
    p.primeiro_mes,
    p.ultimo_mes
from presenca p
cross join total
join dim_modalidade m
    on m.codigo_submodalidade = p.codigo_submodalidade
where p.meses_com_dado < total.meses_no_recorte
order by p.codigo_submodalidade
