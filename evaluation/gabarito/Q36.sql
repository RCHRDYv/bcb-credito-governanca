-- PT: Q36. Parcela da carteira, e das linhas, em recortes sem contagem de
--     operações divulgada. Vêm o último mês e o recorte inteiro.
-- EN: Q36. Share of the portfolio, and of rows, in slices without a disclosed
--     operation count, in the latest month and over the whole window.
with ultimo as (

    select max(data_base) as data_base from fct_carteira

)

select
    100 * cast(sum(case when f.data_base = ultimo.data_base and f.contagem_suprimida then f.carteira_ativa else 0 end) as double)
        / cast(sum(case when f.data_base = ultimo.data_base then f.carteira_ativa else 0 end) as double)
        as carteira_sem_contagem_no_ultimo_mes_pct,
    100 * cast(sum(case when f.data_base = ultimo.data_base and f.contagem_suprimida then 1 else 0 end) as double)
        / cast(sum(case when f.data_base = ultimo.data_base then 1 else 0 end) as double)
        as linhas_sem_contagem_no_ultimo_mes_pct,
    100 * cast(sum(case when f.contagem_suprimida then f.carteira_ativa else 0 end) as double)
        / cast(sum(f.carteira_ativa) as double) as carteira_sem_contagem_no_recorte_pct,
    100 * cast(sum(case when f.contagem_suprimida then 1 else 0 end) as double)
        / cast(count(*) as double) as linhas_sem_contagem_no_recorte_pct
from fct_carteira f
cross join ultimo
