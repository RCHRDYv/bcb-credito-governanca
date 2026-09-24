-- =============================================================================
-- PT: A dimensão de porte, com a ambiguidade da V2 desfeita.
--
--     `porte` é uma coluna polimórfica: para pessoa física ela é faixa de
--     rendimento em salários mínimos, e para pessoa jurídica é tamanho de
--     empresa. A V1 resolvia isso prefixando o valor ("PF - Grande"), e a V2
--     removeu o prefixo, o que fez "Indisponível" virar um valor com dois
--     significados e tornou possível somar categorias incompatíveis sem que
--     nada no esquema avise.
--
--     Esta dimensão devolve a desambiguação, e a chave é o par (cliente, valor),
--     nunca o valor sozinho. São 14 registros para 13 valores: "Indisponível"
--     aparece duas vezes, uma por tipo de cliente, que é exatamente a contagem
--     que a V1 tinha.
--
-- EN: The client-size dimension, with V2's ambiguity undone. `porte` is a
--     polymorphic column: income bracket for individuals, company size for
--     companies. V1 disambiguated it with a prefix ("PJ - Grande") and V2
--     dropped the prefix, which turned "Indisponível" into one value with two
--     meanings. The key here is the (client, value) pair, never the value alone:
--     14 records for 13 values, which is exactly V1's count.
-- =============================================================================

select
    cliente,
    valor,

    -- PT: chave da dimensão, no formato que a V1 usava.
    -- EN: the dimension's key, in the format V1 used.
    valor_desambiguado,

    -- PT: qual das duas taxonomias este registro pertence.
    -- EN: which of the two taxonomies this record belongs to.
    taxonomia,

    -- PT: em que tipos de cliente o valor ocorre no dado, medido.
    -- EN: which client types the value occurs with in the data, measured.
    aplica_a,
    nullif(aviso, '') as aviso

from {{ ref('ontologia_dimensao') }}
where dimensao = 'porte'
