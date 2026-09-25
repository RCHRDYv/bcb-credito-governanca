-- PT: Q29, leitura contra os 24 meses anteriores. Variação do último mês
--     de cada métrica nacional contra a média e o desvio padrão das 24
--     variações anteriores. Atípica quando o z passa de 2 em módulo. As
--     medidas em reais variam em percentual; as taxas, em pontos.
-- EN: Q29, reading against the previous 24 months. Latest monthly change
--     of each national metric against the mean and standard deviation of the
--     previous 24 changes; atypical when |z| > 2.
with mensal as (

    select
        data_base,
        cast(sum(carteira_ativa) as double) as carteira_ativa,
        cast(sum(carteira_a_vencer) as double) as carteira_a_vencer,
        cast(sum(carteira_vencida) as double) as carteira_vencida,
        cast(sum(carteira_inadimplencia) as double) as carteira_inadimplencia,
        cast(sum(ativo_problematico) as double) as ativo_problematico
    from fct_carteira
    group by data_base

),

metricas as (

    select data_base, 'carteira_ativa' as metrica, 'percentual' as unidade, carteira_ativa as valor from mensal
    union all
    select data_base, 'carteira_a_vencer', 'percentual', carteira_a_vencer from mensal
    union all
    select data_base, 'carteira_vencida', 'percentual', carteira_vencida from mensal
    union all
    select data_base, 'carteira_inadimplencia', 'percentual', carteira_inadimplencia from mensal
    union all
    select data_base, 'ativo_problematico', 'percentual', ativo_problematico from mensal
    union all
    select data_base, 'taxa_inadimplencia', 'pontos', 100 * carteira_inadimplencia / carteira_ativa from mensal
    union all
    select data_base, 'taxa_ativo_problematico', 'pontos', 100 * ativo_problematico / carteira_ativa from mensal

),

variacoes as (

    select
        metrica,
        unidade,
        data_base,
        case
            when unidade = 'percentual'
                then 100 * (valor / lag(valor) over (partition by metrica order by data_base) - 1)
            else valor - lag(valor) over (partition by metrica order by data_base)
        end as variacao,
        row_number() over (partition by metrica order by data_base desc) as recencia
    from metricas

),

historico as (

    select
        metrica,
        avg(variacao) as media,
        stddev_samp(variacao) as desvio_padrao,
        count(variacao) as variacoes_no_historico
    from variacoes
    where recencia between 2 and 25
    group by metrica

)

select
    v.metrica,
    v.unidade,
    v.data_base as mes,
    v.variacao as variacao_no_ultimo_mes,
    h.media as media_das_variacoes_anteriores,
    h.desvio_padrao,
    h.variacoes_no_historico,
    (v.variacao - h.media) / h.desvio_padrao as z,
    abs((v.variacao - h.media) / h.desvio_padrao) > 2 as atipica
from variacoes v
join historico h
    on h.metrica = v.metrica
where v.recencia = 1
order by abs((v.variacao - h.media) / h.desvio_padrao) desc
