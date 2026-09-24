-- =============================================================================
-- PT: O modelo usa o retrato mais recente de Empresas como retrato do modelo
--     (int_cnpj_matriz_intervalo). Isso só é seguro se esse retrato estiver
--     completo: Estabelecimentos, Empresas e Simples, os três com linhas. Um
--     retrato novo baixado pela metade seria escolhido sozinho e zeraria o
--     porte ou o MEI em silêncio. Apontado pela revisão do Copilot na PR #42.
-- EN: The model uses the latest Companies snapshot. That is only safe if the
--     snapshot is complete, with rows in all three tables; a half-downloaded
--     new snapshot would otherwise be picked silently.
-- =============================================================================

with retrato as (

    select max(retrato) as retrato from {{ ref('stg_cnpj_empresas') }}

),

tabelas as (

    select 'estabelecimentos' as tabela,
           (select count(*) from {{ ref('stg_cnpj_estabelecimentos') }} e, retrato r where e.retrato = r.retrato) as linhas
    union all
    select 'empresas',
           (select count(*) from {{ ref('stg_cnpj_empresas') }} e, retrato r where e.retrato = r.retrato)
    union all
    select 'simples',
           (select count(*) from {{ ref('stg_cnpj_simples') }} e, retrato r where e.retrato = r.retrato)

)

select * from tabelas where linhas = 0
