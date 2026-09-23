-- =============================================================================
-- PT: Mesma conferência do staging_v2_preserva_o_bronze, com o que é próprio da
--     V1: as quatro colunas em que o marcador "-" virou nulo e a marca de
--     subclasse suprimida.
--
--     Cada coluna tratada é conferida contra a contagem do marcador no arquivo.
--     É o que impede o tratamento de virar silenciosamente amplo demais: um
--     `nullif` aplicado à coluna errada, ou uma comparação que também pegasse
--     valores como "- " ou "--", anularia linhas que o arquivo preenchia, e a
--     divergência apareceria aqui.
--
-- EN: Same check as staging_v2_preserva_o_bronze, plus what is specific to V1:
--     the four columns where the "-" marker became null and the suppressed
--     subclass flag. Each treated column is checked against the marker's count
--     in the file, which is what stops the treatment from silently growing too
--     broad: a `nullif` on the wrong column, or a comparison that also caught
--     values like "- " or "--", would null rows the file had filled, and the
--     divergence would surface here.
-- =============================================================================

with staging as (

    select
        count(*) as linhas,
        count(distinct data_base) as meses,
        count_if(contagem_suprimida) as contagens_suprimidas,
        count_if(numero_de_operacoes is null) as contagens_nulas,
        count_if(tcb is null) as tcb_nulo,
        count_if(sr is null) as sr_nulo,
        count_if(ocupacao is null) as ocupacao_nula,
        count_if(cnae_secao is null) as cnae_secao_nula,
        count_if(cnae_subclasse is null) as cnae_subclasse_nula,
        count_if(subclasse_suprimida) as subclasses_suprimidas,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(carteira_inadimplida_arrastada) as soma_carteira_inadimplida,
        sum(ativo_problematico) as soma_ativo_problematico
    from {{ ref('stg_scr_v1') }}

),

bronze as (

    select
        count(*) as linhas,
        count(distinct trim(data_base)) as meses,
        count_if(trim(numero_de_operacoes) = '<= 15') as contagens_suprimidas,
        count_if(trim(numero_de_operacoes) = '<= 15') as contagens_nulas,
        count_if(trim(tcb) = '-') as tcb_nulo,
        -- PT: a V1 traz nulo em `sr`, sem marcador. É o único caso.
        -- EN: V1 carries a plain null in `sr`, with no marker. The only such case.
        count_if(sr is null) as sr_nulo,
        count_if(trim(ocupacao) = '-') as ocupacao_nula,
        count_if(trim(cnae_secao) = '-') as cnae_secao_nula,
        count_if(trim(cnae_subclasse) = '-') as cnae_subclasse_nula,
        count_if(trim(cliente) = 'PJ' and trim(cnae_subclasse) = '-') as subclasses_suprimidas,
        sum({{ valor_em_reais('carteira_ativa') }}) as soma_carteira_ativa,
        sum({{ valor_em_reais('carteira_inadimplida_arrastada') }}) as soma_carteira_inadimplida,
        sum({{ valor_em_reais('ativo_problematico') }}) as soma_ativo_problematico
    from {{ source('bcb_scr', 'bronze_scr_v1') }}

)

select 'staging' as lado, * from (select * from staging except select * from bronze)
union all
select 'bronze' as lado, * from (select * from bronze except select * from staging)
