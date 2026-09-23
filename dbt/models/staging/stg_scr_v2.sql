-- =============================================================================
-- PT: Staging da V2 do SCR.data, a fonte principal do projeto.
--
--     Relação 1:1 com o bronze: mesma quantidade de linhas, mesmo grão, nenhum
--     filtro e nenhuma regra de negócio. O que muda é só o que impede usar o
--     dado como dado:
--       1. rótulos com trim, para virarem chave de junção com a ontologia;
--       2. vírgula decimal convertida para decimal(18,2);
--       3. data-base convertida para data;
--       4. o sentinela -1 de `numero_de_operacoes` convertido em nulo, com a
--          supressão preservada numa coluna própria.
--
--     O grão é único: as dez dimensões abaixo identificam a linha, verificado
--     em 9.687.811 registros sem uma única repetição (teste staging_grao_unico).
--
-- EN: Staging for SCR.data V2, the project's main source.
--
--     1:1 with bronze: same row count, same grain, no filter and no business
--     logic. Only what prevents using the data as data changes: labels trimmed
--     into ontology join keys, decimal commas cast to decimal(18,2), the
--     reference date cast to date, and the -1 sentinel in `numero_de_operacoes`
--     turned into null with the suppression kept in its own column.
--
--     The grain is unique: the ten dimensions below identify the row, verified
--     over 9,687,811 records with not one repetition.
-- =============================================================================

with bronze as (

    select * from {{ source('bcb_scr', 'bronze_scr_v2') }}

)

select

    -- -------------------------------------------------------------------------
    -- PT: Dimensões. Definição de cada uma em ontology/dimensoes.yml.
    --     Duas delas são polimórficas: `porte` e `cnae_ocupacao` mudam de
    --     taxonomia conforme `cliente`, e agrupar por elas sem separar por
    --     cliente soma categorias incompatíveis.
    -- EN: Dimensions. Each one defined in ontology/dimensoes.yml. Two are
    --     polymorphic: `porte` and `cnae_ocupacao` switch taxonomy depending on
    --     `cliente`, and grouping by them without splitting by client type adds
    --     up incompatible categories.
    -- -------------------------------------------------------------------------
    {{ data_de_referencia('data_base') }} as data_base,
    {{ rotulo('uf') }} as uf,
    {{ rotulo('segmento') }} as segmento,
    {{ rotulo('cliente') }} as cliente,
    {{ rotulo('cnae_ocupacao') }} as cnae_ocupacao,
    {{ rotulo('porte') }} as porte,

    -- PT: A chave de junção com ontology/modalidades.yml é o PAR modalidade e
    --     submodalidade, nunca a submodalidade sozinha: cinco rótulos de
    --     submodalidade aparecem em mais de uma modalidade, cobrindo 15 dos 66
    --     pares ("Microcrédito", "Vendor", "Compror", "Recebíveis adquiridos" e
    --     "Financiamento de projeto").
    -- EN: The join key into ontology/modalidades.yml is the PAIR of modality
    --     and sub-modality, never the sub-modality alone: five sub-modality
    --     labels appear under more than one modality, covering 15 of the 66
    --     pairs.
    {{ rotulo('modalidade') }} as modalidade,
    {{ rotulo('submodalidade') }} as submodalidade,

    {{ rotulo('origem') }} as origem,
    {{ rotulo('indexador') }} as indexador,

    -- -------------------------------------------------------------------------
    -- PT: Contagem de operações e a supressão.
    --     O -1 não é contagem: é contagem não divulgada, e o critério da
    --     supressão não está publicado em lugar nenhum. Está medido que ele NÃO
    --     é "até 15 operações": a V2 divulga contagens de 1 a 15 abertamente, e
    --     um mesmo recorte alterna entre -1 e contagens de até 514.490
    --     operações (docs/sentinela-numero-de-operacoes.md).
    --     Consequência que o mart precisa carregar: somar esta coluna num grupo
    --     com linhas suprimidas dá limite inferior, não total. São 26,7% das
    --     linhas e 6,71% da carteira.
    -- EN: Operation count and its suppression. -1 is not a count: it is a count
    --     not disclosed, and the suppression criterion is published nowhere. It
    --     is measured that it is NOT "up to 15 operations". Summing this column
    --     over a group containing suppressed rows yields a lower bound, not a
    --     total: 26.7% of rows and 6.71% of the portfolio.
    -- -------------------------------------------------------------------------
    {{ contagem_sem_sentinela('numero_de_operacoes', '-1') }} as numero_de_operacoes,
    (trim(numero_de_operacoes) = '-1') as contagem_suprimida,

    -- -------------------------------------------------------------------------
    -- PT: Medidas, em reais. Definição em ontology/metricas.yml.
    --     As seis faixas a vencer somam `carteira_a_vencer`, as duas vencidas
    --     somam `carteira_vencida`, e as duas somam `carteira_ativa`. As três
    --     identidades são testadas, e a última tem uma exceção conhecida de uma
    --     linha em dez/2024, publicada assim pelo BCB.
    -- EN: Measures, in reais. Defined in ontology/metricas.yml. The six
    --     performing buckets add up to `carteira_a_vencer`, the two overdue ones
    --     to `carteira_vencida`, and both to `carteira_ativa`. All three
    --     identities are tested, and the last has one known exception in
    --     Dec/2024, published that way by the BCB.
    -- -------------------------------------------------------------------------
    {{ valor_em_reais('a_vencer_ate_90_dias') }} as a_vencer_ate_90_dias,
    {{ valor_em_reais('a_vencer_de_91_ate_360_dias') }} as a_vencer_de_91_ate_360_dias,
    {{ valor_em_reais('a_vencer_de_361_ate_1080_dias') }} as a_vencer_de_361_ate_1080_dias,
    {{ valor_em_reais('a_vencer_de_1081_ate_1800_dias') }} as a_vencer_de_1081_ate_1800_dias,
    {{ valor_em_reais('a_vencer_de_1801_ate_5400_dias') }} as a_vencer_de_1801_ate_5400_dias,
    {{ valor_em_reais('a_vencer_acima_de_5400_dias') }} as a_vencer_acima_de_5400_dias,
    {{ valor_em_reais('carteira_a_vencer') }} as carteira_a_vencer,

    {{ valor_em_reais('vencido_de_15_ate_90_dias') }} as vencido_de_15_ate_90_dias,
    {{ valor_em_reais('vencido_acima_de_90_dias') }} as vencido_acima_de_90_dias,
    {{ valor_em_reais('carteira_vencida') }} as carteira_vencida,

    {{ valor_em_reais('carteira_ativa') }} as carteira_ativa,

    -- PT: Valor absoluto em reais, NÃO percentual, apesar do nome. A
    --     inadimplência como indicador é uma razão, e a colisão de nome entre a
    --     coluna e o indicador é a armadilha (ontology/metricas.yml).
    -- EN: Absolute value in reais, NOT a percentage, despite the name. Default
    --     as an indicator is a ratio, and the name collision between column and
    --     indicator is the trap.
    {{ valor_em_reais('carteira_inadimplencia') }} as carteira_inadimplencia,

    -- PT: Muda de critério em janeiro de 2025, sem aviso no dado e sem quebra de
    --     série visível (docs/cadeia-normativa.md, seção 6). Comparar antes e
    --     depois de jan/2025 compara duas definições diferentes.
    -- EN: Changes criterion in January 2025, with no warning in the data and no
    --     visible series break. Comparing across Jan/2025 compares two
    --     different definitions.
    {{ valor_em_reais('ativo_problematico') }} as ativo_problematico,

    -- -------------------------------------------------------------------------
    -- PT: Linhagem. Vem do bronze e atravessa todas as camadas, para que
    --     qualquer número possa ser rastreado até o arquivo publicado. O
    --     sha256 muda quando o BCB republica um ZIP (ingestion/manifesto.json).
    -- EN: Lineage. Comes from bronze and travels through every layer, so any
    --     number can be traced back to the published file. The sha256 changes
    --     when the BCB republishes a ZIP.
    -- -------------------------------------------------------------------------
    arquivo_origem,
    versao_fonte,
    sha256_zip,
    ingerido_em

from bronze
