-- PT: Q16. Carteira de crédito pessoal com consignação (0202) e sem
--     consignação (0203), mês a mês, do mês 24 meses antes do último até o
--     último, com o crescimento acumulado desde o início da janela.
-- EN: Q16. Payroll-deducted (0202) and non-payroll (0203) personal loans,
--     month by month, from 24 months before the latest month up to it, with
--     cumulative growth since the window's start.
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

),

ultimo as (

    select max(data_base) as data_base from mensal

)

select
    mensal.data_base as mes,
    mensal.consignado,
    mensal.nao_consignado,
    100 * mensal.consignado / (mensal.consignado + mensal.nao_consignado) as participacao_do_consignado_pct,
    100 * (mensal.consignado / first_value(mensal.consignado) over (order by mensal.data_base) - 1)
        as crescimento_acumulado_consignado_pct,
    100 * (mensal.nao_consignado / first_value(mensal.nao_consignado) over (order by mensal.data_base) - 1)
        as crescimento_acumulado_nao_consignado_pct
from mensal
cross join ultimo
where mensal.data_base >= last_day(ultimo.data_base - interval '24' month)
order by mes
