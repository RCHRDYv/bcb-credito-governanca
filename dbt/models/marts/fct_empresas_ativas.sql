-- =============================================================================
-- PT: Fato de empresas ativas: matrizes ativas no fim de cada mês do SCR, por
--     UF, porte da Receita, grupo de natureza jurídica e condição de MEI.
--     Denominador das perguntas Q12 e Q14 e do indicador de espaço.
--
--     O número é reconstruído de um retrato só do CNPJ, e não lido de um
--     retrato de cada mês (ADR 0009). O erro da reconstrução, medido contra
--     retratos reais, está em mrt_erro_da_reconstrucao e no ADR.
--
--     Conta matrizes, e não estabelecimentos, porque no SCR a UF de pessoa
--     jurídica é a da sede. Só chaves e medida, como fct_carteira (ADR 0007).
--
-- EN: Active companies fact: active head offices at each SCR month end, by
--     state, Receita size, legal nature group and MEI status. Rebuilt from a
--     single CNPJ snapshot (ADR 0009); the error measured against real
--     snapshots is in mrt_erro_da_reconstrucao. Counts head offices, not
--     establishments, because the SCR's company state is the headquarters.
-- =============================================================================

select
    data_base,
    uf,
    porte_empresa,
    grupo_natureza_juridica,
    mei,
    empresas_ativas
from {{ ref('int_cnpj_empresas_ativas_mensal') }}
