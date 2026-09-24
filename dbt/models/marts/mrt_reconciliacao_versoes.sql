-- =============================================================================
-- PT: Mart de apresentação da reconciliação entre as duas versões do SCR.data.
--     Grão: mês, modalidade da V1 e origem dos recursos.
--
--     Compara a V1 publicada com a série da V1 reconstruída a partir da V2 pela
--     tabela oficial de equivalência. É a medição que mostrou que a
--     divergência entre as versões não é uniforme: 14 das 16 modalidades ficam
--     entre 0% e 8,3%, e "PJ - Outros créditos" fica 82,7% acima em jun/2026
--     (docs/analise-v1-v2.md, seção 6). Serve à investigação da issue #19 e ao
--     dashboard, e fica fora do experimento (ADR 0007), porque a diferença já
--     vem calculada.
--
--     A junção é externa completa de propósito: uma combinação que exista só
--     de um lado aparece com o outro lado nulo, em vez de sumir da comparação.
--
-- EN: Presentation mart reconciling the two SCR.data versions, by month, V1
--     modality and funding origin: V1 as published against the V1 series
--     rebuilt from V2 through the official equivalence table. Serves issue #19
--     and the dashboard, and stays out of the experiment because the gap comes
--     pre-computed. The full outer join keeps one-sided combinations visible.
-- =============================================================================

with v2 as (

    select
        data_base,
        modalidade_v1_efetiva as modalidade_v1,
        origem,
        sum(carteira_ativa) as carteira_v2_conformada,
        sum(case when origem_da_modalidade_v1 = 'oficial_ambigua' then carteira_ativa else 0 end)
            as carteira_conformacao_ambigua,
        sum(case when origem_da_modalidade_v1 = 'inferida_pelo_projeto' then carteira_ativa else 0 end)
            as carteira_conformacao_inferida
    from {{ ref('fct_carteira') }}
    group by data_base, modalidade_v1_efetiva, origem

),

v1 as (

    select
        data_base,
        modalidade_v1,
        origem,
        sum(carteira_ativa) as carteira_v1_publicada
    from {{ ref('fct_carteira_v1') }}
    group by data_base, modalidade_v1, origem

),

comparado as (

    select
        coalesce(v2.data_base, v1.data_base) as data_base,
        coalesce(v2.modalidade_v1, v1.modalidade_v1) as modalidade_v1,
        coalesce(v2.origem, v1.origem) as origem,
        v1.carteira_v1_publicada,
        v2.carteira_v2_conformada,
        v2.carteira_conformacao_ambigua,
        v2.carteira_conformacao_inferida
    from v2
    full outer join v1
        on v1.data_base = v2.data_base
       and v1.modalidade_v1 = v2.modalidade_v1
       and v1.origem = v2.origem

)

select

    comparado.data_base,
    tempo.ano_mes,
    comparado.modalidade_v1,
    comparado.origem,

    comparado.carteira_v1_publicada,
    comparado.carteira_v2_conformada,
    comparado.carteira_v2_conformada - comparado.carteira_v1_publicada as diferenca,
    comparado.carteira_v2_conformada / nullif(comparado.carteira_v1_publicada, 0) - 1
        as diferenca_relativa,

    -- PT: Quanto da carteira reconstruída depende de escolha que o dado não
    --     sustenta sozinho: a Natureza não publicada (ambígua) ou a lacuna da
    --     planilha oficial (inferida pelo projeto).
    -- EN: How much of the rebuilt portfolio depends on a choice the data cannot
    --     back on its own.
    comparado.carteira_conformacao_ambigua / nullif(comparado.carteira_v2_conformada, 0)
        as parcela_conformacao_ambigua,
    comparado.carteira_conformacao_inferida / nullif(comparado.carteira_v2_conformada, 0)
        as parcela_conformacao_inferida,

    -- PT: Patamar da divergência entre versões no mês, vindo da ontologia.
    -- EN: The month's divergence level between versions, from the ontology.
    tempo.divergencia_entre_versoes

from comparado
join {{ ref('dim_tempo') }} tempo
    on tempo.data_base = comparado.data_base
