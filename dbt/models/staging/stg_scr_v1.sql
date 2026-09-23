-- =============================================================================
-- PT: Staging da V1 do SCR.data, a fonte legada.
--
--     Mesmas regras do staging da V2: relação 1:1 com o bronze, nenhum filtro,
--     nenhuma regra de negócio. Três diferenças vêm da própria fonte:
--
--     1. O sentinela de supressão é outro. A V1 publica o texto "<= 15" em
--        22.120.146 linhas, 75% do total, e a regra está documentada: "Casos em
--        que o número de operações seja inferior ou igual a 15, a informação
--        divulgada será '<= 15'" (Metodologia V1, item 4.l). Por isso a V1 tem
--        intervalo conhecido, de 1 a 15, e a V2 não tem nenhum.
--
--     2. Quatro colunas usam o marcador "-" onde não se aplicam, e o marcador
--        não está documentado. Viram nulo aqui.
--
--     3. A taxonomia é outra. Modalidades e portes vêm prefixados por "PF - " e
--        "PJ - ", e a V1 tem 16 modalidades contra 13 modalidades e 66
--        submodalidades na V2. A conformação entre as duas NÃO acontece aqui: é
--        papel da camada intermediária, com o seed
--        correspondencia_modalidade_v2_v1 e o ADR 0003. O staging preserva os
--        rótulos como publicados.
--
-- EN: Staging for SCR.data V1, the legacy source.
--
--     Same rules as the V2 staging: 1:1 with bronze, no filter, no business
--     logic. Three differences come from the source itself: the suppression
--     sentinel is the documented "<= 15" text, so V1 has a known interval of 1
--     to 15 while V2 has none; four columns use an undocumented "-" marker
--     where they do not apply, turned into null here; and the taxonomy differs,
--     with labels prefixed by "PF - " and "PJ - ", whose conformance to V2
--     belongs to the intermediate layer, not here.
-- =============================================================================

with bronze as (

    select * from {{ source('bcb_scr', 'bronze_scr_v1') }}

)

select

    -- -------------------------------------------------------------------------
    -- PT: Dimensões. As que a V2 removeu (`sr` e `cnae_subclasse`) estão
    --     registradas em ontology/dimensoes.yml, dimensoes_removidas_na_v2.
    -- EN: Dimensions. The ones V2 dropped (`sr` and `cnae_subclasse`) are
    --     recorded in ontology/dimensoes.yml, dimensoes_removidas_na_v2.
    -- -------------------------------------------------------------------------
    {{ data_de_referencia('data_base') }} as data_base,
    {{ rotulo('uf') }} as uf,

    -- PT: Tipo de Consolidado Bancário, o antecessor de `segmento` na V2, com
    --     três valores em vez de oito. Traz "-" em 11.799.814 linhas, e aqui o
    --     motivo não é "não se aplica": é ausência de classificação.
    -- EN: Banking consolidation type, the predecessor of V2's `segmento`, with
    --     three values instead of eight. Carries "-" in 11,799,814 rows, and
    --     here the reason is not "does not apply": it is missing classification.
    {{ rotulo_sem_marcador('tcb') }} as tcb,

    -- PT: Segmento prudencial da Resolução CMN 4.553, de S1 a S5. Já vem nulo
    --     em 62.767 linhas, sem marcador. Sem substituto na V2.
    -- EN: Prudential segment from CMN Resolution 4,553, S1 to S5. Already null
    --     in 62,767 rows, with no marker. No substitute in V2.
    {{ rotulo('sr') }} as sr,

    -- PT: Na V1 esta coluna é redundante: ela é o prefixo da modalidade. Não
    --     existe uma linha com modalidade de PF e cliente PJ em 29,5 milhões.
    --     Na V2 a coluna passou a ser independente da modalidade.
    -- EN: In V1 this column is redundant: it is the modality's prefix. There is
    --     not one row with a PF modality and a PJ client in 29.5 million. In V2
    --     the column became independent of the modality.
    {{ rotulo('cliente') }} as cliente,

    -- PT: O que a V2 colapsou numa coluna só, `cnae_ocupacao`, a V1 separava em
    --     três. `ocupacao` traz "-" nas 25.227.055 linhas de PJ e `cnae_secao`
    --     nas 4.244.485 de PF, por simetria: cada uma só existe para um tipo de
    --     cliente.
    -- EN: What V2 collapsed into a single `cnae_ocupacao` column, V1 split into
    --     three. `ocupacao` carries "-" in all 25,227,055 PJ rows and
    --     `cnae_secao` in all 4,244,485 PF rows, symmetrically: each exists for
    --     one client type only.
    {{ rotulo_sem_marcador('ocupacao') }} as ocupacao,
    {{ rotulo_sem_marcador('cnae_secao') }} as cnae_secao,

    -- PT: CNAE de sete dígitos, o maior detalhe que existiu na série e que a V2
    --     perdeu. O "-" aqui significa duas coisas diferentes com o mesmo
    --     símbolo: nas 4.244.485 linhas de PF a coluna não se aplica, e nas
    --     989.730 linhas de PJ ela foi suprimida pela regra documentada de
    --     divulgar a subclasse só quando a combinação subclasse, UF e porte tem
    --     mais de 5 CNPJs (Metodologia V1, seção 4.h). A distinção só é
    --     recuperável olhando `cliente`, e é isso que a coluna ao lado marca.
    -- EN: Seven-digit CNAE, the finest detail the series ever had and which V2
    --     lost. "-" here means two different things with the same symbol: in the
    --     4,244,485 PF rows the column does not apply, and in 989,730 PJ rows it
    --     was suppressed by the documented rule of disclosing the subclass only
    --     when subclass, state and size together have more than 5 taxpayer IDs.
    --     The distinction is recoverable only by looking at `cliente`, which is
    --     what the next column does.
    {{ rotulo_sem_marcador('cnae_subclasse') }} as cnae_subclasse,
    (trim(cliente) = 'PJ' and trim(cnae_subclasse) = '-') as subclasse_suprimida,

    -- PT: Mesmos valores da V2, prefixados por "PF - " ou "PJ - ". São 14 aqui
    --     contra 13 na V2, e a diferença é o "Indisponível", que na V1 existia
    --     uma vez para cada tipo de cliente e na V2 ficou ambíguo.
    -- EN: Same values as V2, prefixed by "PF - " or "PJ - ". Fourteen here
    --     against thirteen in V2, the difference being "Indisponível", which in
    --     V1 existed once per client type and in V2 became ambiguous.
    {{ rotulo('porte') }} as porte,

    -- PT: Taxonomia da V1, com 16 modalidades e sem submodalidade. Não é
    --     comparável com a modalidade da V2 sem o seed de correspondência.
    -- EN: V1 taxonomy, 16 modalities and no sub-modality. Not comparable with
    --     V2's modality without the correspondence seed.
    {{ rotulo('modalidade') }} as modalidade,

    {{ rotulo('origem') }} as origem,
    {{ rotulo('indexador') }} as indexador,

    -- -------------------------------------------------------------------------
    -- PT: Contagem de operações, com o sentinela documentado da V1.
    --     Diferente da V2, aqui o limite é conhecido, então o intervalo fica
    --     registrado em vez de perdido. Nas linhas com contagem divulgada o
    --     intervalo é o próprio valor, para que as duas colunas possam ser
    --     usadas sem `case` em cima.
    -- EN: Operation count, with V1's documented sentinel. Unlike V2, the bound
    --     is known here, so the interval is recorded instead of lost. On rows
    --     with a disclosed count the interval is the value itself, so both
    --     columns can be used without a `case` on top.
    -- -------------------------------------------------------------------------
    {{ contagem_sem_sentinela('numero_de_operacoes', '<= 15') }} as numero_de_operacoes,
    (trim(numero_de_operacoes) = '<= 15') as contagem_suprimida,
    coalesce({{ contagem_sem_sentinela('numero_de_operacoes', '<= 15') }}, cast(1 as bigint)) as contagem_min,
    coalesce({{ contagem_sem_sentinela('numero_de_operacoes', '<= 15') }}, cast(15 as bigint)) as contagem_max,

    -- -------------------------------------------------------------------------
    -- PT: Medidas, em reais. A V1 não traz `carteira_a_vencer` nem
    --     `carteira_vencida`: a carteira ativa é a soma das seis faixas a vencer
    --     com a coluna única de vencidos acima de 15 dias, identidade que fecha
    --     em todas as 29.471.540 linhas (teste stg_scr_v1_carteira_ativa).
    --     Nenhum agregado é calculado aqui: derivar é papel das camadas acima.
    -- EN: Measures, in reais. V1 has no `carteira_a_vencer` and no
    --     `carteira_vencida`: the active portfolio is the six performing buckets
    --     plus the single over-15-days overdue column, an identity that holds in
    --     all 29,471,540 rows. No aggregate is computed here.
    -- -------------------------------------------------------------------------
    {{ valor_em_reais('a_vencer_ate_90_dias') }} as a_vencer_ate_90_dias,
    {{ valor_em_reais('a_vencer_de_91_ate_360_dias') }} as a_vencer_de_91_ate_360_dias,
    {{ valor_em_reais('a_vencer_de_361_ate_1080_dias') }} as a_vencer_de_361_ate_1080_dias,
    {{ valor_em_reais('a_vencer_de_1081_ate_1800_dias') }} as a_vencer_de_1081_ate_1800_dias,
    {{ valor_em_reais('a_vencer_de_1801_ate_5400_dias') }} as a_vencer_de_1801_ate_5400_dias,
    {{ valor_em_reais('a_vencer_acima_de_5400_dias') }} as a_vencer_acima_de_5400_dias,
    {{ valor_em_reais('vencido_acima_de_15_dias') }} as vencido_acima_de_15_dias,
    {{ valor_em_reais('carteira_ativa') }} as carteira_ativa,

    -- PT: Mesma definição da `carteira_inadimplencia` da V2, com outro nome. A
    --     renomeação entre versões não mudou o conceito, e é o caso mais claro
    --     de por que a junção entre versões precisa passar pela ontologia.
    -- EN: Same definition as V2's `carteira_inadimplencia` under another name.
    --     The rename between versions did not change the concept, and it is the
    --     clearest case for why joining versions must go through the ontology.
    {{ valor_em_reais('carteira_inadimplida_arrastada') }} as carteira_inadimplida_arrastada,

    {{ valor_em_reais('ativo_problematico') }} as ativo_problematico,

    -- -------------------------------------------------------------------------
    -- PT: Linhagem, igual à da V2.
    -- EN: Lineage, same as V2's.
    -- -------------------------------------------------------------------------
    arquivo_origem,
    versao_fonte,
    sha256_zip,
    ingerido_em

from bronze
