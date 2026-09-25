-- PT: Q37. Operações de crédito no último mês. A soma da coluna é limite
--     inferior, porque os recortes sem contagem divulgada ficam de fora.
-- EN: Q37. Credit operations in the latest month. The column's sum is a lower
--     bound, because slices without a disclosed count are left out.
select
    max(data_base) as mes,
    sum(numero_de_operacoes) as operacoes_limite_inferior,
    sum(case when contagem_suprimida then 1 else 0 end) as recortes_sem_contagem,
    sum(case when contagem_suprimida then carteira_ativa else 0 end) as carteira_sem_contagem,
    100 * cast(sum(case when contagem_suprimida then carteira_ativa else 0 end) as double)
        / cast(sum(carteira_ativa) as double) as carteira_sem_contagem_pct
from fct_carteira
where data_base = (select max(data_base) from fct_carteira)
