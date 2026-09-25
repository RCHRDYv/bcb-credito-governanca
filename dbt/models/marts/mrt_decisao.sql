-- =============================================================================
-- PT: A matriz de espaço contra risco da camada de decisão (issue #26, ADR
--     0014). Grão: UF e modalidade, só cliente PJ, no último mês do SCR.
--
--     A regra, em quatro partes, com os parâmetros em dbt_project.yml:
--
--     1. **Espaço.** Carteira PJ da modalidade na UF dividida pelas empresas
--        ativas da UF, só de natureza empresarial e sem MEI. Comparada com a
--        mediana das UFs na mesma modalidade: abaixo dela, o espaço é alto.
--     2. **Risco.** Variação da taxa de inadimplência na janela da tendência,
--        na célula, contra a mesma variação da modalidade no país. Se sobe
--        mais que o país, o risco está piorando. Toda taxa é razão de somas.
--     3. **Quadrante.** Entrar (espaço alto, risco estável), observar (espaço
--        alto, risco piorando), manter (espaço baixo, risco estável) e não
--        entrar (espaço baixo, risco piorando).
--     4. **Custo de errar, em reais, nas duas direções.** Deixar de entrar
--        onde havia espaço custa a carteira que faltaria para chegar à
--        mediana. Entrar onde o risco piora custa, em ordem de grandeza, o
--        aumento da carteira inadimplida atribuível à piora da taxa. Não é
--        perda: o dado não tem recuperação nem taxa de juros.
--
--     Fica fora da matriz, como "não avaliada" e com o motivo em coluna: a
--     célula abaixo do corte de materialidade, a modalidade com poucas UFs
--     acima do corte, e a célula sem o mês de comparação.
--
--     O alerta antecipado não muda o quadrante: é a distância entre ativo
--     problemático e inadimplência abrindo mais que a do país, a piora que o
--     atraso ainda não mostra (ADR 0005).
--
--     Mart de apresentação: a IA do experimento não o consulta (ADR 0007).
--
-- EN: The decision layer's room-to-grow versus risk matrix. Grain: state and
--     modality, corporate clients only, latest SCR month. Room: PJ portfolio
--     per active company (business entities, no MEI) against the modality's
--     median across states. Risk: the default-rate change over the trend
--     window against the country's for the same modality. Four quadrants, two
--     costs of being wrong in reais, cells below the materiality cut or in
--     thinly covered modalities left unrated with the reason, and an early
--     warning when the problem-asset gap widens faster than the country's.
-- =============================================================================

with referencia as (

    select
        max(data_base) as data_base,
        last_day(add_months(max(data_base), -{{ var('decisao_meses_de_tendencia') }})) as data_base_anterior
    from {{ ref('mrt_carteira_mensal') }}

),

-- -----------------------------------------------------------------------------
-- PT: Cada célula com os dois meses lado a lado.
-- EN: Each cell with both months side by side.
-- -----------------------------------------------------------------------------
celula as (

    select
        m.uf,
        m.codigo_modalidade,
        max(m.modalidade) as modalidade,
        sum(case when m.data_base = r.data_base then m.carteira_ativa end) as carteira_ativa,
        sum(case when m.data_base = r.data_base then m.carteira_inadimplencia end) as carteira_inadimplencia,
        sum(case when m.data_base = r.data_base then m.ativo_problematico end) as ativo_problematico,
        sum(case when m.data_base = r.data_base_anterior then m.carteira_ativa end) as carteira_ativa_anterior,
        sum(case when m.data_base = r.data_base_anterior then m.carteira_inadimplencia end) as carteira_inadimplencia_anterior,
        sum(case when m.data_base = r.data_base_anterior then m.ativo_problematico end) as ativo_problematico_anterior
    from {{ ref('mrt_carteira_mensal') }} as m
    cross join referencia as r
    where m.cliente = 'PJ'
      and m.data_base in (r.data_base, r.data_base_anterior)
    group by m.uf, m.codigo_modalidade

),

-- -----------------------------------------------------------------------------
-- PT: A mesma modalidade no país inteiro, todas as UFs, para a referência do
--     risco. Razão de somas, e não média das taxas das UFs.
-- EN: The same modality nationwide, all states, as the risk reference.
-- -----------------------------------------------------------------------------
-- PT: As razões são calculadas em double, e as somas continuam em decimal. A
--     divisão entre decimais no Spark arredonda para 6 casas: bom para
--     exibir uma taxa, mas multiplicado por uma carteira de centenas de
--     bilhões vira desvio de centenas de milhares de reais no custo de errar.
--     Medido pelo QA independente em 2026-09-24.
-- EN: Ratios are computed as double, sums stay decimal. Spark's decimal
--     division rounds to 6 places, which multiplied by a large portfolio
--     shifts the cost of being wrong by hundreds of thousands of reais.
pais as (

    select
        codigo_modalidade,
        cast(sum(carteira_inadimplencia) as double) / cast(sum(carteira_ativa) as double) as taxa_pais,
        cast(sum(carteira_inadimplencia_anterior) as double)
            / cast(sum(carteira_ativa_anterior) as double) as taxa_pais_anterior,
        cast(sum(ativo_problematico) - sum(carteira_inadimplencia) as double)
            / cast(sum(carteira_ativa) as double) as distancia_pais,
        cast(sum(ativo_problematico_anterior) - sum(carteira_inadimplencia_anterior) as double)
            / cast(sum(carteira_ativa_anterior) as double) as distancia_pais_anterior
    from celula
    group by codigo_modalidade

),

-- PT: O denominador: empresas ativas de natureza empresarial, sem MEI.
-- EN: The denominator: active business-entity companies, no MEI.
empresas as (

    select e.uf, sum(e.empresas_ativas) as empresas
    from {{ ref('fct_empresas_ativas') }} as e
    cross join referencia as r
    where e.data_base = r.data_base
      and e.grupo_natureza_juridica = '{{ var("decisao_grupo_natureza_juridica") }}'
      and not e.mei
    group by e.uf

),

medidas as (

    select
        c.*,
        e.empresas,
        cast(c.carteira_ativa as double) / e.empresas as carteira_por_empresa,

        cast(c.carteira_inadimplencia as double) / cast(c.carteira_ativa as double) as taxa_inadimplencia,
        cast(c.carteira_inadimplencia_anterior as double)
            / cast(c.carteira_ativa_anterior as double) as taxa_inadimplencia_anterior,
        cast(c.ativo_problematico - c.carteira_inadimplencia as double)
            / cast(c.carteira_ativa as double) as distancia_ap_inadimplencia,
        cast(c.ativo_problematico_anterior - c.carteira_inadimplencia_anterior as double)
            / cast(c.carteira_ativa_anterior as double) as distancia_ap_inadimplencia_anterior,

        c.carteira_ativa >= {{ var('decisao_carteira_minima') }} as acima_do_corte
    from celula as c
    left join empresas as e
        on e.uf = c.uf
    -- PT: célula que existia no mês anterior e sumiu não tem o que avaliar
    -- EN: a cell that existed before and vanished has nothing to rate
    where c.carteira_ativa is not null

),

-- -----------------------------------------------------------------------------
-- PT: A mediana só entre as células acima do corte, e só nas modalidades com
--     UFs suficientes para ela comparar alguma coisa.
-- EN: The median only over cells above the cut, in modalities with enough
--     states for it to compare anything.
-- -----------------------------------------------------------------------------
modalidade as (

    select
        codigo_modalidade,
        count(*) as ufs_acima_do_corte,
        percentile_cont(0.5) within group (order by carteira_por_empresa) as mediana_carteira_por_empresa
    from medidas
    where acima_do_corte
    group by codigo_modalidade

),

avaliacao as (

    select
        m.*,
        md.ufs_acima_do_corte,
        md.mediana_carteira_por_empresa,
        p.taxa_pais,
        p.taxa_pais_anterior,
        m.taxa_inadimplencia - m.taxa_inadimplencia_anterior as variacao_taxa_inadimplencia,
        p.taxa_pais - p.taxa_pais_anterior as variacao_taxa_pais,
        (m.distancia_ap_inadimplencia - m.distancia_ap_inadimplencia_anterior) as variacao_distancia,
        (p.distancia_pais - p.distancia_pais_anterior) as variacao_distancia_pais,

        case
            when not m.acima_do_corte then 'carteira abaixo do corte de materialidade'
            when coalesce(md.ufs_acima_do_corte, 0) < {{ var('decisao_minimo_de_ufs') }}
                then 'modalidade com poucas UFs acima do corte'
            when m.carteira_ativa_anterior is null then 'sem o mês de comparação'
        end as motivo_nao_avaliada
    from medidas as m
    left join modalidade as md
        on md.codigo_modalidade = m.codigo_modalidade
    left join pais as p
        on p.codigo_modalidade = m.codigo_modalidade

)

select
    r.data_base,
    r.data_base_anterior,
    a.uf,
    a.codigo_modalidade,
    a.modalidade,

    -- -------------------------------------------------------------------------
    -- PT: Espaço
    -- EN: Room to grow
    -- -------------------------------------------------------------------------
    a.carteira_ativa,
    a.empresas,
    a.carteira_por_empresa,
    a.mediana_carteira_por_empresa,
    a.carteira_por_empresa / a.mediana_carteira_por_empresa as indice_de_espaco,
    a.ufs_acima_do_corte,

    -- -------------------------------------------------------------------------
    -- PT: Risco
    -- EN: Risk
    -- -------------------------------------------------------------------------
    a.taxa_inadimplencia,
    a.taxa_inadimplencia_anterior,
    a.variacao_taxa_inadimplencia,
    a.taxa_pais,
    a.variacao_taxa_pais,

    -- -------------------------------------------------------------------------
    -- PT: Classificação
    -- EN: Classification
    -- -------------------------------------------------------------------------
    a.motivo_nao_avaliada is null as avaliada,
    a.motivo_nao_avaliada,
    case
        when a.motivo_nao_avaliada is not null then 'não avaliada'
        when a.carteira_por_empresa < a.mediana_carteira_por_empresa
             and a.variacao_taxa_inadimplencia <= a.variacao_taxa_pais then 'entrar'
        when a.carteira_por_empresa < a.mediana_carteira_por_empresa then 'observar'
        when a.variacao_taxa_inadimplencia <= a.variacao_taxa_pais then 'manter'
        else 'não entrar'
    end as quadrante,

    -- -------------------------------------------------------------------------
    -- PT: Custo de errar, em reais
    -- EN: Cost of being wrong, in reais
    -- -------------------------------------------------------------------------
    case
        when a.motivo_nao_avaliada is null and a.carteira_por_empresa < a.mediana_carteira_por_empresa
            then (a.mediana_carteira_por_empresa - a.carteira_por_empresa) * a.empresas
    end as custo_de_nao_entrar,
    case
        when a.motivo_nao_avaliada is null
            then a.carteira_ativa * greatest(a.variacao_taxa_inadimplencia, 0)
    end as custo_do_risco,

    -- -------------------------------------------------------------------------
    -- PT: Alerta antecipado
    -- EN: Early warning
    -- -------------------------------------------------------------------------
    a.distancia_ap_inadimplencia,
    a.variacao_distancia,
    a.variacao_distancia_pais,
    coalesce(
        a.motivo_nao_avaliada is null
        and a.variacao_distancia > 0
        and a.variacao_distancia > a.variacao_distancia_pais,
        false
    ) as alerta_antecipado

from avaliacao as a
cross join referencia as r
