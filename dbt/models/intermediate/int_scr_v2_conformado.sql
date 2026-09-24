-- =============================================================================
-- PT: O fato da V2 com as dimensões resolvidas. É aqui que a interpretação
--     acontece, e por isso ela fica separada do staging, que só corrige forma
--     (ADR 0006).
--
--     Três coisas entram, e nenhuma linha é filtrada, agregada ou removida:
--
--     1. **O código da submodalidade.** O dado publicado não traz código
--        nenhum, só rótulo. O código vem da ontologia pela junção do PAR
--        modalidade e submodalidade, porque cinco rótulos de submodalidade
--        ocorrem em mais de uma modalidade e o rótulo sozinho não identifica.
--
--     2. **A desambiguação das duas colunas polimórficas**, no formato que a V1
--        usava. Com ela, agrupar por `porte_desambiguado` é seguro, e agrupar
--        por `porte` continua misturando faixa de renda com tamanho de empresa.
--        As duas colunas ficam disponíveis de propósito: a segunda é a
--        armadilha, e o experimento precisa dela para medir se a IA cai nela.
--
--     3. **A modalidade da V1 correspondente**, pelo seed oficial de
--        equivalência (ADR 0003). A junção é muitos-para-um pela chave código,
--        cliente e origem, medida sem ambiguidade e sem fan-out.
--
--     O que NÃO acontece aqui: escolher entre correspondência oficial e
--     inferida em silêncio. A coluna `modalidade_v1_efetiva` existe para não
--     obrigar toda consulta a repetir o coalesce, e ao lado dela vai sempre
--     `origem_da_modalidade_v1`, dizendo de onde o valor veio.
--
-- EN: The V2 fact with its dimensions resolved. Interpretation happens here,
--     which is why it is kept out of staging, where only form is fixed.
--
--     Three things are added and no row is filtered, aggregated or dropped: the
--     Annex 3 sub-modality code (joined by the modality and sub-modality PAIR,
--     because five sub-modality labels occur under more than one modality); the
--     disambiguation of the two polymorphic columns, in the format V1 used, with
--     the ambiguous originals kept on purpose because the experiment needs them;
--     and the matching V1 modality from the official equivalence seed, a
--     many-to-one join measured free of ambiguity and fan-out.
--
--     What does not happen here: silently choosing between the official and the
--     inferred correspondence. `modalidade_v1_efetiva` spares every query the
--     coalesce, and `origem_da_modalidade_v1` always travels next to it.
-- =============================================================================

with fato as (

    select * from {{ ref('stg_scr_v2') }}

),

modalidade as (

    select
        codigo_submodalidade,
        modalidade,
        submodalidade
    from {{ ref('int_dim_modalidade') }}

),

correspondencia as (

    -- PT: O seed guarda ausência como texto vazio, porque CSV não tem nulo.
    --     Aqui vazio volta a ser nulo, para as regras abaixo poderem usar
    --     `is null` em vez de comparar com string.
    -- EN: The seed stores absence as an empty string, because CSV has no null.
    --     Here empty becomes null again, so the rules below can use `is null`.
    select
        codigo_submodalidade_v2,
        cliente,
        origem,
        nullif(modalidade_v1, '') as modalidade_v1,
        nullif(modalidade_v1_alternativa, '') as modalidade_v1_alternativa,
        nullif(modalidade_v1_inferida, '') as modalidade_v1_inferida,
        regra,
        nullif(ambiguidade, '') as ambiguidade
    from {{ ref('correspondencia_modalidade_v2_v1') }}

)

select

    -- PT: Todo o staging passa inalterado. A lista não é repetida aqui de
    --     propósito: este modelo acrescenta colunas e não muda nenhuma, e
    --     reescrever as 29 colunas do staging só criaria duas listas para
    --     manter em sincronia.
    -- EN: All of staging passes through untouched. The column list is
    --     deliberately not repeated: this model adds columns and changes none,
    --     and restating staging's 29 columns would create two lists to keep in
    --     sync.
    fato.*,

    -- -------------------------------------------------------------------------
    -- PT: 1. Código da submodalidade, a chave que o dado publicado não tem.
    -- EN: 1. Sub-modality code, the key the published data lacks.
    -- -------------------------------------------------------------------------
    modalidade.codigo_submodalidade,
    substring(modalidade.codigo_submodalidade, 1, 2) as codigo_modalidade,

    -- -------------------------------------------------------------------------
    -- PT: 2. As duas colunas polimórficas, desambiguadas por cliente.
    -- EN: 2. The two polymorphic columns, disambiguated by client type.
    -- -------------------------------------------------------------------------
    concat(fato.cliente, ' - ', fato.porte) as porte_desambiguado,
    concat(fato.cliente, ' - ', fato.cnae_ocupacao) as cnae_ocupacao_desambiguado,

    -- -------------------------------------------------------------------------
    -- PT: 3. Conformação com a taxonomia da V1.
    -- EN: 3. Conformance with V1's taxonomy.
    -- -------------------------------------------------------------------------
    correspondencia.modalidade_v1,
    correspondencia.modalidade_v1_alternativa,
    correspondencia.modalidade_v1_inferida,
    coalesce(
        correspondencia.modalidade_v1,
        correspondencia.modalidade_v1_inferida
    ) as modalidade_v1_efetiva,

    -- PT: De onde veio o valor efetivo. "oficial_ambigua" marca as linhas em que
    --     a planilha oficial dá duas candidatas e a escolha dependeria da
    --     Natureza da operação, campo que o SCR.data não publica: 2,71% da
    --     carteira. "inferida_pelo_projeto" marca as duas combinações que a
    --     planilha simplesmente não cobre: 0,02% da carteira.
    -- EN: Where the effective value came from. "oficial_ambigua" marks rows where
    --     the official sheet offers two candidates and the choice would depend on
    --     a field SCR.data does not publish (2.71% of the portfolio);
    --     "inferida_pelo_projeto" marks the two combinations the sheet does not
    --     cover at all (0.02%).
    case
        when correspondencia.ambiguidade = 'natureza_nao_publicada' then 'oficial_ambigua'
        when correspondencia.modalidade_v1 is not null then 'oficial'
        when correspondencia.modalidade_v1_inferida is not null then 'inferida_pelo_projeto'
    end as origem_da_modalidade_v1,

    correspondencia.regra as regra_de_correspondencia,
    correspondencia.ambiguidade as ambiguidade_da_correspondencia

from fato

-- PT: As duas junções são left de propósito. Se alguma linha ficasse sem par, o
--     resultado tem que ser nulo visível e teste vermelho, e não linha
--     desaparecida. Os testes de relacionamento provam que hoje não há nenhuma.
-- EN: Both joins are left on purpose. If any row lost its match, the result must
--     be a visible null and a red test, not a vanished row. The relationship
--     tests prove there is none today.
left join modalidade
    on modalidade.modalidade = fato.modalidade
   and modalidade.submodalidade = fato.submodalidade

left join correspondencia
    on correspondencia.codigo_submodalidade_v2 = modalidade.codigo_submodalidade
   and correspondencia.cliente = fato.cliente
   and correspondencia.origem = fato.origem
