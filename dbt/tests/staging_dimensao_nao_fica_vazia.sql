-- =============================================================================
-- PT: Uma dimensão pode parar de ser publicada no meio da série, e isso não
--     quebra nada: o arquivo continua vindo, com o mesmo número de colunas, e a
--     coluna passa a vir vazia. Foi o que aconteceu com `tcb` na V1 em julho de
--     2025, e o efeito colateral é grave. Uma série agrupada pela coluna termina
--     no mês anterior, e um gráfico mostra a categoria caindo a zero, o que não
--     aconteceu: a carteira continua no dado, agregada.
--
--     O teste compara cada mês com o anterior e acusa a coluna que tinha valor e
--     passou a não ter nenhum. Ele olha a série, e não o total, porque no total
--     uma coluna descontinuada é indistinguível de uma coluna com dado faltante.
--     Esse foi exatamente o erro 11 de docs/desenvolvimento-com-ia.md.
--
--     A quebra conhecida está declarada abaixo, com data. Aqui a exclusão por
--     chave é a escolha certa, ao contrário do teste stg_scr_v2_carteira_ativa:
--     lá a exceção é uma linha de dado que o BCB pode corrigir a qualquer
--     republicação, e um aviso permanente faz sentido; aqui o evento é
--     estrutural, datado e entendido, e um aviso que nunca sai deixa de ser
--     lido. O que este teste precisa detectar é o PRÓXIMO evento.
--
-- EN: A dimension can stop being published mid-series without breaking
--     anything: the file keeps arriving with the same column count, and the
--     column simply comes empty. That is what happened to V1's `tcb` in July
--     2025. A series grouped by the column then ends in the previous month, and
--     a chart shows the category dropping to zero, which never happened.
--
--     The test compares each month with the previous one and flags a column that
--     had values and stopped having any. It looks at the series, not at the
--     total, because in a total a discontinued column is indistinguishable from
--     a column with missing data.
--
--     The known break is declared below, with its date. Excluding it by key is
--     the right choice here, unlike in stg_scr_v2_carteira_ativa: there the
--     exception is one data row the BCB may fix on any republication, so a
--     standing warning earns its place; here the event is structural, dated and
--     understood, and a warning that never goes away stops being read. What this
--     test must catch is the NEXT event.
-- =============================================================================

with v1 as (

    -- PT: count(coluna) conta os não nulos. Zero significa coluna vazia no mês.
    -- EN: count(column) counts non-nulls. Zero means an empty column that month.
    select
        data_base,
        count(uf) as uf,
        count(tcb) as tcb,
        count(sr) as sr,
        count(cliente) as cliente,
        count(ocupacao) as ocupacao,
        count(cnae_secao) as cnae_secao,
        count(cnae_subclasse) as cnae_subclasse,
        count(porte) as porte,
        count(modalidade) as modalidade,
        count(origem) as origem,
        count(indexador) as indexador
    from {{ ref('stg_scr_v1') }}
    group by data_base

),

v2 as (

    select
        data_base,
        count(uf) as uf,
        count(segmento) as segmento,
        count(cliente) as cliente,
        count(cnae_ocupacao) as cnae_ocupacao,
        count(porte) as porte,
        count(modalidade) as modalidade,
        count(submodalidade) as submodalidade,
        count(origem) as origem,
        count(indexador) as indexador
    from {{ ref('stg_scr_v2') }}
    group by data_base

),

longo as (

    select 'v1' as versao, data_base, coluna, preenchidas
    from v1
    lateral view stack(
        11,
        'uf', uf, 'tcb', tcb, 'sr', sr, 'cliente', cliente, 'ocupacao', ocupacao,
        'cnae_secao', cnae_secao, 'cnae_subclasse', cnae_subclasse, 'porte', porte,
        'modalidade', modalidade, 'origem', origem, 'indexador', indexador
    ) desempilhado as coluna, preenchidas

    union all

    select 'v2' as versao, data_base, coluna, preenchidas
    from v2
    lateral view stack(
        9,
        'uf', uf, 'segmento', segmento, 'cliente', cliente,
        'cnae_ocupacao', cnae_ocupacao, 'porte', porte, 'modalidade', modalidade,
        'submodalidade', submodalidade, 'origem', origem, 'indexador', indexador
    ) desempilhado as coluna, preenchidas

),

com_mes_anterior as (

    select
        versao,
        coluna,
        data_base,
        preenchidas,
        lag(preenchidas) over (partition by versao, coluna order by data_base) as no_mes_anterior
    from longo

)

select versao, coluna, data_base, preenchidas, no_mes_anterior

from com_mes_anterior

where preenchidas = 0
  and no_mes_anterior > 0

  -- PT: quebra conhecida e registrada: ontology/dimensoes.yml,
  --     avisos_gerais.tcb_descontinuado_em_julho_de_2025, e
  --     docs/analise-v1-v2.md, seção 7.
  -- EN: known and documented break, recorded in the dimension ontology and in
  --     the V1 versus V2 analysis.
  and not (versao = 'v1' and coluna = 'tcb' and data_base = date '2025-07-31')
