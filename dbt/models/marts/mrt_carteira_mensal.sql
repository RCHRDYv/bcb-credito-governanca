-- =============================================================================
-- PT: Mart de apresentação das telas 1 e 2 do dashboard, e do histórico que a
--     tela 3 vai usar na v0.2. Grão: mês, tipo de cliente, UF e modalidade.
--
--     Fica fora do experimento (ADR 0007), porque pré-responde perguntas: as
--     taxas já vêm calculadas. É justamente o que o dashboard precisa, e é o
--     motivo de ele existir separado do esquema estrela.
--
--     Três escolhas que valem registrar:
--
--     1. **Taxa é razão de somas, calculada uma vez aqui.** Média de taxas
--        entre recortes de tamanhos diferentes dá número errado e plausível.
--        Calculando no mart, o dashboard e qualquer consulta derivada herdam a
--        conta certa em vez de refazê-la.
--
--     2. **A comparação no tempo é por data, e não por posição.** Uma
--        combinação de cliente, UF e modalidade pode não ter linha em algum
--        mês, e a submodalidade de ARO, por exemplo, só existe em dois. Olhar
--        "seis linhas atrás" pularia meses sem avisar. Por isso o mês anterior
--        é encontrado pela data exata, seis ou doze meses antes.
--
--     3. **A janela que cruza a quebra do ativo problemático é marcada.** A
--        distância entre ativo problemático e inadimplência muda de definição
--        em jan/2025, e uma variação que atravesse essa data compara dois
--        critérios. A data vem da ontologia, pela dim_tempo e pelo seed de
--        quebras, e não está escrita aqui.
--
-- EN: Presentation mart for dashboard screens 1 and 2, and the history screen 3
--     will use in v0.2. Grain: month, client type, state and modality. Kept out
--     of the experiment (ADR 0007) because it pre-answers questions. Rates are
--     ratios of sums, computed once; period comparisons match by exact date,
--     not by row position, because some combinations skip months; and windows
--     crossing the problem-asset criterion change are flagged, with the date
--     coming from the ontology.
-- =============================================================================

with fato as (

    select
        f.data_base,
        f.cliente,
        f.uf,
        m.codigo_modalidade,
        m.modalidade,
        f.carteira_ativa,
        f.carteira_inadimplencia,
        f.ativo_problematico
    from {{ ref('fct_carteira') }} f
    join {{ ref('dim_modalidade') }} m
        on m.codigo_submodalidade = f.codigo_submodalidade

),

mensal as (

    select
        data_base,
        cliente,
        uf,
        codigo_modalidade,
        modalidade,
        sum(carteira_ativa) as carteira_ativa,
        sum(carteira_inadimplencia) as carteira_inadimplencia,
        sum(ativo_problematico) as ativo_problematico
    from fato
    group by data_base, cliente, uf, codigo_modalidade, modalidade

),

com_taxas as (

    select
        *,
        carteira_inadimplencia / nullif(carteira_ativa, 0) as taxa_inadimplencia,
        ativo_problematico / nullif(carteira_ativa, 0) as taxa_ativo_problematico
    from mensal

),

quebra_ativo_problematico as (

    select to_date(data) as data
    from {{ ref('ontologia_quebra') }}
    where id = 'criterio_ativo_problematico'

)

select

    atual.data_base,
    tempo.ano_mes,
    atual.cliente,
    atual.uf,
    atual.codigo_modalidade,
    atual.modalidade,

    -- -------------------------------------------------------------------------
    -- PT: Níveis e taxas do mês.
    -- EN: The month's levels and rates.
    -- -------------------------------------------------------------------------
    atual.carteira_ativa,
    atual.carteira_inadimplencia,
    atual.ativo_problematico,
    atual.taxa_inadimplencia,
    atual.taxa_ativo_problematico,

    -- PT: Participação na carteira do mesmo tipo de cliente no país.
    -- EN: Share of the same client type's national portfolio.
    atual.carteira_ativa
        / sum(atual.carteira_ativa) over (partition by atual.data_base, atual.cliente)
        as participacao_na_carteira_do_cliente,

    -- PT: Distância entre as duas métricas de risco, em pontos percentuais da
    --     carteira. Antecipa deterioração que o atraso ainda não mostra.
    -- EN: Gap between the two risk metrics, in portfolio percentage points.
    atual.taxa_ativo_problematico - atual.taxa_inadimplencia as distancia_ap_inadimplencia,

    -- -------------------------------------------------------------------------
    -- PT: Comparações no tempo, pela data exata.
    -- EN: Period comparisons, by exact date.
    -- -------------------------------------------------------------------------
    doze.carteira_ativa as carteira_ativa_12m_antes,
    atual.carteira_ativa / nullif(doze.carteira_ativa, 0) - 1 as variacao_carteira_12m,

    seis.taxa_inadimplencia as taxa_inadimplencia_6m_antes,
    atual.taxa_inadimplencia - seis.taxa_inadimplencia as variacao_taxa_inadimplencia_6m,

    -- -------------------------------------------------------------------------
    -- PT: Avisos, vindos da ontologia.
    -- EN: Warnings, from the ontology.
    -- -------------------------------------------------------------------------
    tempo.criterio_ativo_problematico,

    -- PT: Verdadeiro quando a janela de seis meses que termina neste mês
    --     contém a mudança de critério do ativo problemático. As mesmas
    --     janelas contêm o salto da carteira inadimplida em jan/2025, cuja
    --     causa ainda está em investigação na issue #20.
    -- EN: True when the six-month window ending this month contains the
    --     problem-asset criterion change. The same windows contain the Jan/2025
    --     non-performing jump still under investigation in issue #20.
    (
        quebra.data > last_day(add_months(atual.data_base, -6))
        and quebra.data <= atual.data_base
    ) as janela_6m_cruza_quebra_ativo_problematico

from com_taxas atual
cross join quebra_ativo_problematico quebra
join {{ ref('dim_tempo') }} tempo
    on tempo.data_base = atual.data_base
left join com_taxas doze
    on doze.cliente = atual.cliente
   and doze.uf = atual.uf
   and doze.codigo_modalidade = atual.codigo_modalidade
   and doze.data_base = last_day(add_months(atual.data_base, -12))
left join com_taxas seis
    on seis.cliente = atual.cliente
   and seis.uf = atual.uf
   and seis.codigo_modalidade = atual.codigo_modalidade
   and seis.data_base = last_day(add_months(atual.data_base, -6))
