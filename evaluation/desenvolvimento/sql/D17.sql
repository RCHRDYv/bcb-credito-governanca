-- PT: D17. O mês de 2025 com o maior volume de PIX recebido por pessoas
--     físicas, em valor e em quantidade.
-- EN: D17. The month of 2025 with the largest PIX volume received by
--     individuals, by value and count.
with por_mes as (

    select data_base, sum(valor) as volume, sum(quantidade) as quantidade
    from fct_pix
    where cliente = 'PF'
      and lado = 'recebedor'
      and year(data_base) = 2025
    group by data_base

)

select
    data_base as mes,
    volume,
    quantidade
from por_mes
order by volume desc
limit 1
