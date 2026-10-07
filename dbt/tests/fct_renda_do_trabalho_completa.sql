-- =============================================================================
-- PT: Três garantias da renda do trabalho (issue #38):
--     1. cada trimestre tem as 27 UFs, cada uma uma vez. Uma UF que não
--        casasse pelo código do IBGE sumiria na junção interna do fato;
--     2. os trimestres são contíguos, sem buraco;
--     3. todo mês do SCR tem um trimestre encerrado até a data-base. Sem
--        isso, a Q13 e a Q15 perderiam o denominador do mês sem erro.
--     Os valores precisam ser positivos.
-- EN: Labor income guarantees: all 27 states once per quarter, contiguous
--     quarters, every SCR month with a quarter ended by its reference date,
--     and positive values.
-- =============================================================================

with por_trimestre as (

    select ano, trimestre, count(*) as ufs, count(distinct uf) as ufs_distintas
    from {{ ref('fct_renda_do_trabalho') }}
    group by ano, trimestre

),

sequencia as (

    select
        ano * 4 + trimestre as indice,
        lag(ano * 4 + trimestre) over (order by ano, trimestre) as anterior
    from por_trimestre

)

select 'trimestre sem as 27 UFs' as problema, cast(ano * 100 + trimestre as string) as onde
from por_trimestre
where ufs != 27 or ufs_distintas != 27

union all

select 'trimestre com buraco antes', cast(indice as string)
from sequencia
where anterior is not null and indice - anterior != 1

union all

select 'mês do SCR sem trimestre encerrado', cast(t.data_base as string)
from {{ ref('dim_tempo') }} as t
where not exists (
    select 1 from {{ ref('fct_renda_do_trabalho') }} as r
    where r.fim_do_trimestre <= t.data_base
)

union all

select 'valor não positivo', concat(uf, ' ', ano, 'T', trimestre)
from {{ ref('fct_renda_do_trabalho') }}
where rendimento_medio <= 0 or massa_de_rendimento <= 0
   or cv_rendimento_medio <= 0 or cv_massa_de_rendimento <= 0
