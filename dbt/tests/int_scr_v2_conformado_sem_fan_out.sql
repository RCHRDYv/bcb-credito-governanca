-- =============================================================================
-- PT: A camada intermediária faz duas junções, e junção é onde o número
--     silenciosamente dobra. Se a dimensão de modalidade tivesse dois registros
--     para o mesmo par de rótulos, ou o seed de correspondência duas linhas para
--     a mesma chave, cada linha do fato viraria duas e TODA soma da camada de
--     cima ficaria maior, sem erro nenhum aparecer.
--
--     Este teste compara contagem e soma entre o staging e o conformado. É a
--     verificação mais barata contra o erro mais caro: linha e carteira ativa
--     precisam ser exatamente as mesmas, porque a camada não filtra nem agrega.
--
--     O `except` nos dois sentidos devolve zero linha quando tudo é igual e, na
--     divergência, uma linha de cada lado, para a comparação ficar legível.
--
-- EN: The intermediate layer makes two joins, and joins are where numbers
--     silently double. If the modality dimension held two records for the same
--     label pair, or the correspondence seed two rows for the same key, every
--     fact row would become two and every sum above would grow with no error
--     surfacing. This test compares row count and sums between staging and the
--     conformed model: the cheapest check against the most expensive mistake.
-- =============================================================================

with staging as (

    select
        count(*) as linhas,
        count(distinct data_base) as meses,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(ativo_problematico) as soma_ativo_problematico
    from {{ ref('stg_scr_v2') }}

),

conformado as (

    select
        count(*) as linhas,
        count(distinct data_base) as meses,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(ativo_problematico) as soma_ativo_problematico
    from {{ ref('int_scr_v2_conformado') }}

)

select 'staging' as lado, * from (select * from staging except select * from conformado)
union all
select 'conformado' as lado, * from (select * from conformado except select * from staging)
