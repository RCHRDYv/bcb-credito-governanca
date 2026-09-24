-- =============================================================================
-- PT: A fronteira do dado como número medido, um registro por mês.
--
--     É o mart da tela 4 do dashboard. O ADR 0005 decidiu que a recomendação
--     vem acompanhada do que o dado NÃO permite afirmar, e não como ressalva no
--     fim. Este mart transforma essa lista em medida: em vez de a tela dizer
--     "há supressão de contagem", ela mostra quanto da carteira do mês está
--     nessa situação, e o número muda quando o dado muda.
--
--     Cada coluna responde a um limite concreto:
--       - contagem suprimida: quanto da carteira não tem número de operações;
--       - operações divulgadas: é limite inferior, e não total;
--       - conformação ambígua e inferida: quanto da série antiga reconstruída
--         depende de escolha que o dado não sustenta;
--       - diferença entre versões: o universo das duas publicações não é o mesmo;
--       - regime das quebras: vindo da ontologia, pela dim_tempo.
--
-- EN: The data's boundary as a measured number, one record per month. It is
--     dashboard screen 4's mart: ADR 0005 decided the recommendation comes with
--     what the data does NOT allow claiming, and this mart turns that list into
--     measures that move when the data moves.
-- =============================================================================

with v2 as (

    select
        data_base,
        count(*) as recortes,
        count_if(contagem_suprimida) as recortes_com_contagem_suprimida,
        sum(carteira_ativa) as carteira_ativa,
        sum(case when contagem_suprimida then carteira_ativa else 0 end) as carteira_com_contagem_suprimida,
        sum(numero_de_operacoes) as operacoes_divulgadas,
        sum(case when origem_da_modalidade_v1 = 'oficial_ambigua' then carteira_ativa else 0 end)
            as carteira_conformacao_ambigua,
        sum(case when origem_da_modalidade_v1 = 'inferida_pelo_projeto' then carteira_ativa else 0 end)
            as carteira_conformacao_inferida
    from {{ ref('fct_carteira') }}
    group by data_base

),

v1 as (

    select data_base, sum(carteira_ativa) as carteira_ativa
    from {{ ref('fct_carteira_v1') }}
    group by data_base

)

select

    v2.data_base,
    tempo.ano_mes,

    -- -------------------------------------------------------------------------
    -- PT: Contagem de operações.
    -- EN: Operation count.
    -- -------------------------------------------------------------------------
    v2.recortes,
    v2.recortes_com_contagem_suprimida / v2.recortes as parcela_recortes_contagem_suprimida,
    v2.carteira_com_contagem_suprimida / v2.carteira_ativa as parcela_carteira_contagem_suprimida,

    -- PT: Nomeada como limite inferior de propósito: somar a contagem com
    --     linhas suprimidas no grupo nunca dá o total de operações.
    -- EN: Named as a lower bound on purpose.
    v2.operacoes_divulgadas as operacoes_limite_inferior,

    -- -------------------------------------------------------------------------
    -- PT: Conformação com a taxonomia da V1.
    -- EN: Conformance with V1's taxonomy.
    -- -------------------------------------------------------------------------
    v2.carteira_conformacao_ambigua / v2.carteira_ativa as parcela_carteira_conformacao_ambigua,
    v2.carteira_conformacao_inferida / v2.carteira_ativa as parcela_carteira_conformacao_inferida,

    -- -------------------------------------------------------------------------
    -- PT: Diferença de universo entre as duas publicações.
    -- EN: Universe difference between the two publications.
    -- -------------------------------------------------------------------------
    v1.carteira_ativa as carteira_v1_publicada,
    v2.carteira_ativa as carteira_v2,
    v2.carteira_ativa / nullif(v1.carteira_ativa, 0) - 1 as diferenca_v2_sobre_v1,

    -- -------------------------------------------------------------------------
    -- PT: Regime das quebras no mês, vindo da ontologia.
    -- EN: The month's break regimes, from the ontology.
    -- -------------------------------------------------------------------------
    tempo.criterio_ativo_problematico,
    tempo.ativo_problematico_comparavel_com_mes_anterior,
    tempo.granularidade_da_publicacao,
    tempo.divergencia_entre_versoes,
    tempo.quebras_no_mes

from v2
join v1
    on v1.data_base = v2.data_base
join {{ ref('dim_tempo') }} tempo
    on tempo.data_base = v2.data_base
