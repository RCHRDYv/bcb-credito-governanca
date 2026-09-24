-- =============================================================================
-- PT: Grão das tabelas do CNPJ. Um estabelecimento aparece uma vez por
--     retrato, e o Simples uma vez por CNPJ básico. Uma repetição no Simples
--     multiplicaria a matriz na junção de int_cnpj_matriz_intervalo, e o
--     estoque sairia inflado sem aviso. A tabela Empresas tem teste próprio,
--     porque já vem com uma repetição publicada (cnpj_empresas_repetidas).
-- EN: CNPJ table grains. Companies has its own test, since it ships with one
--     published repetition.
-- =============================================================================

select 'estabelecimentos' as tabela, concat_ws('|', retrato, cnpj_basico, cnpj_ordem) as chave, count(*) as linhas
from {{ ref('stg_cnpj_estabelecimentos') }}
group by retrato, cnpj_basico, cnpj_ordem
having count(*) > 1

union all

select 'simples', concat_ws('|', retrato, cnpj_basico), count(*)
from {{ ref('stg_cnpj_simples') }}
group by retrato, cnpj_basico
having count(*) > 1
