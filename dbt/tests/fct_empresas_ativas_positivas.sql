-- =============================================================================
-- PT: Estoque de empresas não pode ser negativo. Um valor negativo quer dizer
--     que algum trecho saiu antes de entrar, erro na lógica de eventos de
--     int_cnpj_empresas_ativas_mensal, que o modelo não esconde.
-- EN: A company stock cannot be negative; a negative means some segment left
--     before it entered, a bug in the event logic.
-- =============================================================================

select * from {{ ref('fct_empresas_ativas') }} where empresas_ativas <= 0
