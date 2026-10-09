"""
PT: Assistente de dados com resposta auditável (issue #49, ADR 0029).
    Text-to-SQL sobre o esquema estrela no DuckDB, com a ontologia e os
    trechos do RAG como blocos de contexto que se ligam e desligam nas
    condições A, B, C e D do ADR 0013. O mesmo componente serve ao
    experimento, em lote (#48 e #50), e ao uso interativo local:

        uv run python -m assistente "pergunta" --condicao B
        uv run --group rag python -m assistente "pergunta" --condicao D
        uv run --group assistente --group rag python -m assistente.interface

    O modelo roda no Ollama local. As condições C e D buscam trechos no
    índice do RAG e precisam do grupo rag do uv.

EN: Data assistant with auditable answers. Text-to-SQL over the star schema
    in DuckDB, with the ontology and RAG excerpts as context blocks switched
    on and off across conditions A to D. The same component serves the
    batch experiment and local interactive use (see above). The model runs
    on local Ollama; C and D need the rag group.
"""
