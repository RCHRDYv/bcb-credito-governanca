"""
PT: Corpus e índice do RAG das condições C e D do experimento (issue #46,
    ADR 0028). Cada etapa é um módulo executável, com as dependências do
    grupo rag do uv:

        uv run python -m ingestion.baixar_documentos
        uv run --group rag python -m rag.construir
        uv run --group rag python -m rag.avaliar

    A busca que a #49 consome é rag.indice.buscar.

EN: Corpus and index for the RAG of the experiment's conditions C and D.
    Each step is a runnable module (see above). The search that #49
    consumes is rag.indice.buscar.
"""
