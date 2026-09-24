-- =============================================================================
-- PT: No retrato mais recente, a reconstrução precisa bater exatamente com a
--     contagem real, UF por UF. Na data da própria extração, nenhuma empresa
--     pode ter mudado de situação depois, então qualquer diferença é erro na
--     implementação da regra, e não limite do método. O teste prova só isso:
--     que int_cnpj_matriz_intervalo reproduz a regra. Ele não valida o
--     passado, porque o retrato que constrói é o mesmo que confere. O passado
--     é medido pelos retratos antigos, em mrt_erro_da_reconstrucao (ADR 0009).
-- EN: In the latest snapshot the reconstruction must match the real count
--     exactly, state by state: on the extraction date itself no company can
--     have changed status afterwards, so any gap is a bug in the interval
--     rule, not a limit of the method.
-- =============================================================================

select *
from {{ ref('int_cnpj_validacao_reconstrucao') }}
where retrato = (select max(retrato) from {{ ref('stg_cnpj_empresas') }})
  and diferenca != 0
