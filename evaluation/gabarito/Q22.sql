-- PT: Q22. Volume financeiro mensal do PIX liquidado no SPI, do mês 24 meses
--     antes do último até o último. Usa só o lado pagador, porque somar
--     pagador e recebedor contaria cada transação duas vezes; a linha sem UF
--     entra, porque pertence ao total do país.
-- EN: Q22. Monthly PIX value settled in SPI, from 24 months before the latest
--     month up to it. Payer side only, since adding both sides would count
--     each transaction twice; the row without a state belongs to the total.
with mensal as (

    select data_base, cast(sum(valor) as double) as volume
    from fct_pix
    where lado = 'pagador'
    group by data_base

),

ultimo as (

    select max(data_base) as data_base from mensal

)

select
    mensal.data_base as mes,
    mensal.volume,
    100 * (mensal.volume / first_value(mensal.volume) over (order by mensal.data_base) - 1)
        as crescimento_desde_o_inicio_da_janela_pct
from mensal
cross join ultimo
where mensal.data_base >= last_day(ultimo.data_base - interval '24' month)
order by mes
