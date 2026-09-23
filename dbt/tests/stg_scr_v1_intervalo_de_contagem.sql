-- =============================================================================
-- PT: O intervalo de contagem da V1 precisa dizer a verdade nos dois casos.
--     Onde a contagem foi suprimida, o arquivo garante de 1 a 15 operações, e
--     nada além disso. Onde a contagem foi divulgada, o intervalo é o próprio
--     valor, para que quem consome as duas colunas não precise saber qual dos
--     dois casos está olhando.
--
--     Este teste existe porque o intervalo é a única coisa que a V1 tem e a V2
--     não: na V2 a supressão não traz limite nenhum, e um recorte suprimido pode
--     ter meia dúzia ou meio milhão de operações
--     (docs/sentinela-numero-de-operacoes.md). Confundir os dois regimes é o
--     tipo de erro que o intervalo preenchido errado tornaria invisível.
--
-- EN: V1's count interval must tell the truth in both cases. Where the count was
--     suppressed, the file guarantees 1 to 15 operations and nothing more. Where
--     it was disclosed, the interval is the value itself, so a consumer of both
--     columns need not know which case they are looking at.
--
--     The test exists because the interval is the one thing V1 has and V2 does
--     not: in V2 suppression carries no bound at all, and a suppressed slice may
--     hold half a dozen or half a million operations.
-- =============================================================================

select
    contagem_suprimida,
    numero_de_operacoes,
    contagem_min,
    contagem_max,
    arquivo_origem

from {{ ref('stg_scr_v1') }}

where
    -- PT: suprimida: intervalo fechado de 1 a 15 e nenhuma contagem.
    -- EN: suppressed: closed interval of 1 to 15 and no count.
    (contagem_suprimida and (contagem_min != 1 or contagem_max != 15 or numero_de_operacoes is not null))

    -- PT: divulgada: o intervalo colapsa no valor publicado.
    -- EN: disclosed: the interval collapses onto the published value.
    or (not contagem_suprimida and (contagem_min != numero_de_operacoes or contagem_max != numero_de_operacoes))
