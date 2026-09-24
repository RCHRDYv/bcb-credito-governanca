-- =============================================================================
-- PT: Mart de apresentação do erro da reconstrução do estoque de empresas
--     ativas (ADR 0009), para a tela 4 do dashboard, que declara o que o dado
--     não permite afirmar. Grão: retrato e UF.
--
--     Em cada retrato, compara a contagem real de matrizes ativas com a
--     reconstruída a partir do retrato mais recente, na data da extração.
--     No retrato mais recente o erro é zero por construção, e isso é testado.
--
-- EN: Presentation mart for the reconstruction error of the active-company
--     stock, for dashboard screen 4. Grain: snapshot and state. In the latest
--     snapshot the error is zero by construction, which is tested.
-- =============================================================================

select * from {{ ref('int_cnpj_validacao_reconstrucao') }}
