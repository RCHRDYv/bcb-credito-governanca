-- PT: D23. Crescimento da carteira das UFs do Nordeste de julho de 2025 a
--     julho de 2026.
-- EN: D23. Portfolio growth of the Northeast states, July 2025 to July 2026.
with por_uf as (

    select
        f.uf,
        u.nome_da_uf,
        sum(case when f.data_base = date '2025-07-31' then f.carteira_ativa else 0 end) as carteira_julho_2025,
        sum(case when f.data_base = date '2026-07-31' then f.carteira_ativa else 0 end) as carteira_julho_2026
    from fct_carteira as f
    join dim_uf as u on u.uf = f.uf
    where f.uf in ('MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA')
      and f.data_base in (date '2025-07-31', date '2026-07-31')
    group by f.uf, u.nome_da_uf

)

select
    row_number() over (order by cast(carteira_julho_2026 as double) / cast(carteira_julho_2025 as double) desc)
        as posicao,
    uf,
    nome_da_uf,
    100 * (cast(carteira_julho_2026 as double) / cast(carteira_julho_2025 as double) - 1) as crescimento_pct
from por_uf
order by posicao
