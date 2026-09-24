-- =============================================================================
-- PT: A dimensão de modalidade, com os 66 pares de modalidade e submodalidade.
--
--     Ela não é escrita à mão: vem do seed gerado por
--     scripts/gerar_seeds_da_ontologia.py a partir de ontology/modalidades.yml.
--     A ontologia é fonte do modelo, não documentação sobre ele, e é isso que
--     torna impossível a documentação divergir do dado sem alguém notar.
--
--     A chave é o CÓDIGO da submodalidade, o do Anexo 3 do documento 3040, e
--     não o rótulo. Os rótulos existem aqui para a junção com o dado publicado,
--     que não traz código nenhum.
--
-- EN: The modality dimension, with all 66 modality and sub-modality pairs. It
--     is not hand-written: it comes from the seed generated from the ontology,
--     which makes documentation drift impossible to hide. The key is the Annex 3
--     sub-modality code; the labels exist for joining with the published data,
--     which carries no codes at all.
-- =============================================================================

select

    -- PT: chave do modelo dimensional.
    -- EN: the dimensional model's key.
    codigo_submodalidade,
    codigo_modalidade,

    -- PT: Rótulos exatos do dado, com as imperfeições preservadas, porque é por
    --     eles que a junção acontece. Um deles traz um caractere de controle no
    --     lugar do travessão, e outro tem espaço duplo interno.
    -- EN: Exact data labels, imperfections preserved, because the join happens
    --     through them. One carries a control character instead of a dash, and
    --     another has an internal double space.
    modalidade,
    submodalidade,

    -- PT: Nome oficial das Instruções de Preenchimento, que divergem do rótulo
    --     do dado em vários códigos. Para cruzar documentos, use o código.
    -- EN: Official name from the filling instructions, which diverges from the
    --     data label in several codes. To cross documents, use the code.
    nome_oficial_modalidade,
    nome_oficial_submodalidade,

    -- PT: A definição normativa e o quanto ela é confiável. Vazia nas quatro
    --     submodalidades marcadas como lacuna na ontologia: elas existem no
    --     Anexo 3, ocorrem no dado, e nenhum documento consultado as define.
    --     O nulo aqui é informação, não falha de carga.
    -- EN: The normative definition and how much it can be trusted. Empty in the
    --     four sub-modalities marked as a gap in the ontology: they exist in
    --     Annex 3, occur in the data, and no consulted document defines them.
    --     The null here is information, not a load failure.
    nullif(definicao, '') as definicao,
    confianca,
    fonte,
    (confianca = 'lacuna') as sem_definicao_oficial

from {{ ref('ontologia_modalidade') }}
