-- =============================================================================
-- PT: A dimensão de CNAE e ocupação, com a ambiguidade da V2 desfeita.
--
--     É a segunda coluna polimórfica: para pessoa jurídica traz a Seção do
--     CNAE, e para pessoa física a natureza da ocupação. Os dois conjuntos não
--     têm valor em comum, então o rótulo sozinho quase sempre revela de onde
--     vem, mas "Outros" é natureza de ocupação e "Outras atividades de
--     serviços" é seção do CNAE, e confundir os dois é fácil.
--
--     A V1 separava isso em três colunas (`ocupacao`, `cnae_secao` e
--     `cnae_subclasse`) e prefixava os valores. A V2 colapsou em uma coluna,
--     perdeu a subclasse de sete dígitos e tirou o prefixo: perda de
--     granularidade e ganho de ambiguidade na mesma mudança.
--
-- EN: The economic-activity dimension, with V2's ambiguity undone. It is the
--     second polymorphic column: CNAE section for companies, occupation nature
--     for individuals. The two sets share no value, so the label almost always
--     reveals its origin, but "Outros" is an occupation and "Outras atividades
--     de serviços" is a CNAE section, and the two are easy to confuse.
-- =============================================================================

select
    cliente,
    valor,
    valor_desambiguado,
    taxonomia,
    aplica_a,
    nullif(aviso, '') as aviso

from {{ ref('ontologia_dimensao') }}
where dimensao = 'cnae_ocupacao'
