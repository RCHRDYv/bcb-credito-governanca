-- =============================================================================
-- PT: Fato legado da V1, agregado por mês, UF, modalidade da V1 e origem.
--
--     Existe por uma consequência da decisão de que a IA consulta só o esquema
--     estrela (ADR 0007). Três perguntas pré-registradas comparam as duas
--     versões do SCR.data, e a Q39 pergunta se elas fecham no total. Sem um
--     fato da V1 no esquema estrela, essas perguntas ficariam impossíveis por
--     construção para a IA, o que mediria a ausência da tabela e não o efeito
--     da documentação.
--
--     O grão é agregado de propósito. A V1 tem 29,5 milhões de linhas, a maior
--     parte vinda de colunas que a V2 removeu (subclasse do CNAE, segmento
--     prudencial e o tcb, descontinuado em jul/2025), e nenhuma pergunta
--     precisa delas. O que as perguntas precisam é comparar totais por mês e
--     por modalidade, e é isso que este grão entrega.
--
--     A medida de inadimplência mantém o nome da V1, carteira_inadimplida_
--     arrastada. A definição é a mesma da V2, com outro nome, e manter o nome
--     original preserva a armadilha que o experimento mede.
--
-- EN: Legacy V1 fact, aggregated by month, state, V1 modality and funding
--     origin. It exists because the AI queries only the star schema (ADR
--     0007): three pre-registered questions compare the two SCR.data versions,
--     and without a V1 fact they would be impossible for the AI by
--     construction. The grain is aggregated on purpose, since most of V1's 29.5
--     million rows come from columns V2 dropped and no question needs them. The
--     default measure keeps V1's name, preserving the renaming trap.
-- =============================================================================

select
    data_base,
    uf,

    -- PT: Na V1, cliente é redundante com o prefixo da modalidade. Fica aqui
    --     por conveniência de junção com o fato da V2.
    -- EN: In V1, the client type is redundant with the modality prefix. Kept
    --     here for joining convenience with the V2 fact.
    cliente,
    modalidade as modalidade_v1,
    origem,

    sum(carteira_ativa) as carteira_ativa,
    sum(carteira_inadimplida_arrastada) as carteira_inadimplida_arrastada,
    sum(ativo_problematico) as ativo_problematico

from {{ ref('stg_scr_v1') }}
group by data_base, uf, cliente, modalidade, origem
