-- =============================================================================
-- PT: O fato do esquema estrela precisa ter exatamente as linhas e os totais da
--     camada intermediária. Ele não filtra nem agrega, então qualquer
--     diferença é defeito: uma linha a mais multiplica totais em silêncio, e
--     uma a menos esconde parte da carteira.
--
--     O `except` nos dois sentidos devolve zero linha quando tudo é igual e,
--     na divergência, uma linha de cada lado.
--
-- EN: The star schema's fact must hold exactly the intermediate layer's rows
--     and totals. It neither filters nor aggregates, so any difference is a
--     defect. The two-way `except` returns nothing when all is equal.
-- =============================================================================

with intermediario as (

    select
        count(*) as linhas,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(carteira_inadimplencia) as soma_carteira_inadimplencia,
        sum(ativo_problematico) as soma_ativo_problematico,
        sum(numero_de_operacoes) as soma_operacoes_divulgadas
    from {{ ref('int_scr_v2_conformado') }}

),

fato as (

    select
        count(*) as linhas,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(carteira_inadimplencia) as soma_carteira_inadimplencia,
        sum(ativo_problematico) as soma_ativo_problematico,
        sum(numero_de_operacoes) as soma_operacoes_divulgadas
    from {{ ref('fct_carteira') }}

)

select 'intermediario' as lado, * from (select * from intermediario except select * from fato)
union all
select 'fato' as lado, * from (select * from fato except select * from intermediario)
