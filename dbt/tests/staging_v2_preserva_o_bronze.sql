-- =============================================================================
-- PT: O staging não pode perder nem inventar nada em relação ao bronze. É a
--     conferência que protege contra o erro mais fácil de cometer e mais difícil
--     de notar: um filtro que entra num modelo de staging meses depois, "só para
--     testar", e nunca sai. Todo número dos marts passaria a estar certo sobre
--     um recorte que ninguém pediu.
--
--     Compara, entre o staging e a fonte: linhas, meses distintos, linhas com a
--     contagem suprimida e a soma das três medidas de nível de carteira. A soma
--     de decimal é exata, então a comparação é de igualdade, sem tolerância.
--
--     As linhas com contagem suprimida são conferidas duas vezes, por caminhos
--     diferentes: pela marca `contagem_suprimida` e pelo nulo em
--     `numero_de_operacoes`. As duas precisam bater com o -1 do arquivo, o que
--     garante que a marca e o nulo andem sempre juntos.
--
--     O `except` nos dois sentidos devolve zero linha quando tudo é igual e, na
--     divergência, uma linha de cada lado, para a comparação ficar legível no
--     resultado do teste.
--
-- EN: Staging must neither lose nor invent anything relative to bronze. This is
--     the check that guards against the easiest mistake to make and the hardest
--     to notice: a filter that lands in a staging model months later, "just to
--     test", and never leaves. Every number in the marts would then be right
--     about a slice nobody asked for.
--
--     It compares row count, distinct months, suppressed-count rows and the sum
--     of the three portfolio-level measures. Decimal sums are exact, so the
--     comparison is equality with no tolerance. Suppressed rows are checked
--     twice by different paths, through the flag and through the null, so flag
--     and null can never drift apart. The two-way `except` returns nothing when
--     all is equal and one row per side otherwise.
-- =============================================================================

with staging as (

    select
        count(*) as linhas,
        count(distinct data_base) as meses,
        count_if(contagem_suprimida) as contagens_suprimidas,
        count_if(numero_de_operacoes is null) as contagens_nulas,
        sum(carteira_ativa) as soma_carteira_ativa,
        sum(carteira_inadimplencia) as soma_carteira_inadimplencia,
        sum(ativo_problematico) as soma_ativo_problematico
    from {{ ref('stg_scr_v2') }}

),

bronze as (

    select
        count(*) as linhas,
        count(distinct trim(data_base)) as meses,
        count_if(trim(numero_de_operacoes) = '-1') as contagens_suprimidas,
        count_if(trim(numero_de_operacoes) = '-1') as contagens_nulas,
        sum({{ valor_em_reais('carteira_ativa') }}) as soma_carteira_ativa,
        sum({{ valor_em_reais('carteira_inadimplencia') }}) as soma_carteira_inadimplencia,
        sum({{ valor_em_reais('ativo_problematico') }}) as soma_ativo_problematico
    from {{ source('bcb_scr', 'bronze_scr_v2') }}

)

select 'staging' as lado, * from (select * from staging except select * from bronze)
union all
select 'bronze' as lado, * from (select * from bronze except select * from staging)
