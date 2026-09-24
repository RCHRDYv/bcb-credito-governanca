-- =============================================================================
-- PT: Dimensão de tempo, um registro por data-base.
--
--     É aqui que as quebras da série ficam visíveis no próprio mart, e não só
--     na documentação, como pede a issue #15. As três quebras datadas vêm do
--     seed ontologia_quebra, gerado da ontologia, então nenhuma data de quebra
--     está escrita neste SQL: o modelo sabe QUAL quebra procura pelo id, e a
--     ontologia diz QUANDO ela acontece e o que muda.
--
--     Cada quebra vira uma coluna de regime, com o texto de "antes" ou de
--     "depois" da ontologia, para que qualquer consulta que atravesse a data
--     carregue junto a informação de que atravessou.
--
-- EN: Time dimension, one record per reference date. This is where the series
--     breaks become visible in the mart itself, as issue #15 asks. The three
--     dated breaks come from the ontology-generated seed, so no break date is
--     written in this SQL: the model knows WHICH break it wants by id, and the
--     ontology says WHEN it happens and what changes. Each break becomes a
--     regime column carrying the ontology's before or after text.
-- =============================================================================

with meses as (

    select distinct data_base
    from {{ ref('int_scr_v2_conformado') }}

),

quebras as (

    select id, to_date(data) as data, antes, depois
    from {{ ref('ontologia_quebra') }}

),

-- PT: Uma CTE por quebra usada. Se o id sumir da ontologia, a junção cruzada
--     abaixo zera a dimensão, e todo teste de relacionamento do fato fica
--     vermelho. É o comportamento desejado: quebra removida em silêncio não
--     pode produzir dimensão sem aviso.
-- EN: One CTE per break used. If the id disappears from the ontology, the cross
--     join below empties the dimension and every relationship test goes red.
ativo_problematico as (select * from quebras where id = 'criterio_ativo_problematico'),
granularidade as (select * from quebras where id = 'granularidade_da_publicacao'),
versoes as (select * from quebras where id = 'divergencia_entre_versoes'),

quebras_do_mes as (

    select data, concat_ws('; ', sort_array(collect_list(id))) as quebras
    from quebras
    group by data

)

select

    meses.data_base,
    year(meses.data_base) as ano,
    month(meses.data_base) as mes,
    quarter(meses.data_base) as trimestre,
    date_format(meses.data_base, 'yyyy-MM') as ano_mes,
    meses.data_base = max(meses.data_base) over () as eh_mes_mais_recente,

    -- -------------------------------------------------------------------------
    -- PT: Regime de cada quebra no mês.
    -- EN: Each break's regime in the month.
    -- -------------------------------------------------------------------------
    case
        when meses.data_base >= ativo_problematico.data then ativo_problematico.depois
        else ativo_problematico.antes
    end as criterio_ativo_problematico,

    -- PT: Falso só no mês da quebra: comparar esse mês com o anterior compara
    --     duas definições de ativo problemático.
    -- EN: False only in the break month: comparing it with the previous month
    --     compares two definitions of problem assets.
    meses.data_base != ativo_problematico.data as ativo_problematico_comparavel_com_mes_anterior,

    case
        when meses.data_base >= granularidade.data then granularidade.depois
        else granularidade.antes
    end as granularidade_da_publicacao,

    case
        when meses.data_base >= versoes.data then versoes.depois
        else versoes.antes
    end as divergencia_entre_versoes,

    -- PT: As quebras que começam exatamente neste mês, ou nulo.
    -- EN: The breaks that start exactly in this month, or null.
    quebras_do_mes.quebras as quebras_no_mes

from meses
cross join ativo_problematico
cross join granularidade
cross join versoes
left join quebras_do_mes
    on quebras_do_mes.data = meses.data_base
