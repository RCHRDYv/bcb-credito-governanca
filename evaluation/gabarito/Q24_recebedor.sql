-- PT: Q24, leitura pela UF do recebedor. Volume de PIX do mês dividido pela
--     carteira ativa, por UF, no último mês. PIX é fluxo e carteira é saldo.
-- EN: Q24, reading by the recebedor side's state. Monthly PIX value over the
--     active portfolio by state in the latest month (flow over stock).
with ultimo as (

    select max(data_base) as data_base from fct_carteira

),

pix as (

    select p.uf, sum(p.valor) as volume_pix
    from fct_pix p
    join ultimo
        on p.data_base = ultimo.data_base
    where p.lado = 'recebedor'
      and p.uf is not null
    group by p.uf

),

carteira as (

    select f.uf, sum(f.carteira_ativa) as carteira_ativa
    from fct_carteira f
    join ultimo
        on f.data_base = ultimo.data_base
    group by f.uf

)

select
    row_number() over (order by cast(pix.volume_pix as double) / cast(carteira.carteira_ativa as double) desc)
        as posicao,
    carteira.uf,
    pix.volume_pix,
    carteira.carteira_ativa,
    cast(pix.volume_pix as double) / cast(carteira.carteira_ativa as double) as razao_pix_sobre_carteira
from carteira
join pix
    on pix.uf = carteira.uf
order by posicao
