-- =============================================================================
-- PT: O grão declarado de cada versão precisa identificar a linha. Se duas
--     linhas compartilharem o mesmo recorte, toda soma por dimensão passa a
--     contar duas vezes sem erro nenhum, e um mês republicado que entre duas
--     vezes no volume aparece exatamente assim.
--
--     Medido em 2026-09-23: zero repetições nas duas versões, 9.687.811 linhas
--     na V2 com dez dimensões e 29.471.540 na V1 com doze.
--
--     Os nulos entram como "(nulo)" de propósito. As colunas da V1 que marcam
--     ausência são nulas em milhões de linhas, e concat_ws salta nulo em
--     silêncio: sem o coalesce, dois recortes diferentes poderiam gerar a mesma
--     chave e o teste acusaria repetição que não existe.
--
-- EN: Each version's declared grain must identify the row. If two rows shared a
--     slice, every sum by dimension would silently double count, which is
--     exactly how a republished month loaded twice would look. Measured on
--     2026-09-23: zero repetitions in both versions.
--
--     Nulls are coalesced to "(nulo)" on purpose: V1's absence-marking columns
--     are null in millions of rows and concat_ws silently skips nulls, so
--     without the coalesce two different slices could produce the same key.
-- =============================================================================

with v2 as (

    select
        'v2' as versao,
        concat_ws(
            ' | ',
            data_base, uf, segmento, cliente, cnae_ocupacao, porte,
            modalidade, submodalidade, origem, indexador
        ) as recorte,
        count(*) as linhas
    from {{ ref('stg_scr_v2') }}
    group by all
    having count(*) > 1

),

v1 as (

    select
        'v1' as versao,
        concat_ws(
            ' | ',
            data_base,
            uf,
            coalesce(tcb, '(nulo)'),
            coalesce(sr, '(nulo)'),
            cliente,
            coalesce(ocupacao, '(nulo)'),
            coalesce(cnae_secao, '(nulo)'),
            coalesce(cnae_subclasse, '(nulo)'),
            porte,
            modalidade,
            origem,
            indexador
        ) as recorte,
        count(*) as linhas
    from {{ ref('stg_scr_v1') }}
    group by all
    having count(*) > 1

)

select * from v2
union all
select * from v1
