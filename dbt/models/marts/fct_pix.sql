-- =============================================================================
-- PT: Fato do PIX: valor, quantidade de transações e pessoas, por mês, UF,
--     lado (pagador ou recebedor) e tipo de cliente. Serve às perguntas Q22,
--     Q23 e Q24 (issue #36, ADR 0011).
--
--     Quatro cuidados, que o fato não esconde:
--     - **lado.** No total do país, pagador e recebedor somam o mesmo valor,
--       porque todo PIX tem os dois. Por UF eles diferem, e somar os dois
--       lados conta cada transação duas vezes. Um teste confere a igualdade
--       nacional mês a mês;
--     - **UF nula.** A linha "N/D" da API, sem município informado, entra com
--       UF nula. Ela pertence ao total nacional e fica fora de qualquer
--       recorte por UF;
--     - **escopo.** Só o PIX liquidado no SPI; o liquidado nos livros do
--       próprio participante não está no dado;
--     - **fluxo.** É o que circulou no mês, e não saldo, ao contrário da
--       carteira de crédito.
--
--     Os meses são os do SCR, para todos os fatos dividirem a mesma
--     dim_tempo. O PIX publica um mês a mais, que fica de fora.
--
--     Pessoas não somam entre lados nem entre meses: a mesma pessoa pode
--     pagar e receber, e aparecer em vários meses.
--
-- EN: PIX fact: value, transaction count and people, by month, state, side
--     (payer or receiver) and client type. Payer and receiver add up to the
--     same national total, and summing both sides double counts; a test
--     checks the national equality monthly. The "N/D" row gets a null state
--     and belongs only to the national total. Only PIX settled in SPI. It is
--     a flow, not a balance. Months are the SCR's. People do not add across
--     sides or months.
-- =============================================================================

with meses as (

    select distinct data_base from {{ ref('stg_scr_v2') }}

),

pix as (

    select p.*, u.valor as uf
    from {{ ref('stg_pix_municipio') }} as p
    inner join meses as m
        on m.data_base = p.data_base
    left join {{ ref('ontologia_dimensao') }} as u
        on u.dimensao = 'uf' and u.codigo_ibge = p.codigo_ibge_uf

),

-- PT: De colunas por lado e cliente para linhas, uma por combinação.
-- EN: From columns per side and client to rows, one per combination.
em_linhas as (

    select data_base, uf, 'pagador' as lado, 'PF' as cliente,
           valor_pagador_pf as valor, quantidade_pagador_pf as quantidade, pessoas_pagador_pf as pessoas
    from pix
    union all
    select data_base, uf, 'pagador', 'PJ', valor_pagador_pj, quantidade_pagador_pj, pessoas_pagador_pj from pix
    union all
    select data_base, uf, 'recebedor', 'PF', valor_recebedor_pf, quantidade_recebedor_pf, pessoas_recebedor_pf from pix
    union all
    select data_base, uf, 'recebedor', 'PJ', valor_recebedor_pj, quantidade_recebedor_pj, pessoas_recebedor_pj from pix

)

select
    data_base,
    uf,
    lado,
    cliente,
    sum(valor) as valor,
    sum(quantidade) as quantidade,
    sum(pessoas) as pessoas
from em_linhas
group by data_base, uf, lado, cliente
