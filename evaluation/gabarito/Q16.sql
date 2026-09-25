-- PT: Q16. Carteira de crédito pessoal com consignação (0202) e sem
--     consignação (0203), mês a mês, com o crescimento acumulado desde o
--     primeiro mês. A pergunta pede três anos, e o recorte é menor.
-- EN: Q16. Payroll-deducted (0202) and non-payroll (0203) personal loans,
--     month by month, with cumulative growth since the first month.
with mensal as (

    select
        data_base,
        cast(sum(case when codigo_submodalidade = '0202' then carteira_ativa else 0 end) as double)
            as consignado,
        cast(sum(case when codigo_submodalidade = '0203' then carteira_ativa else 0 end) as double)
            as nao_consignado
    from fct_carteira
    where codigo_submodalidade in ('0202', '0203')
    group by data_base

)

select
    data_base as mes,
    consignado,
    nao_consignado,
    100 * consignado / (consignado + nao_consignado) as participacao_do_consignado_pct,
    100 * (consignado / first_value(consignado) over (order by data_base) - 1)
        as crescimento_acumulado_consignado_pct,
    100 * (nao_consignado / first_value(nao_consignado) over (order by data_base) - 1)
        as crescimento_acumulado_nao_consignado_pct
from mensal
order by mes
