"""
PT: Ingestão do SCR.data: da fonte oficial do Banco Central até a camada
    bronze no Databricks. Cada etapa é um módulo executável:

        uv run python -m ingestion.baixar
        uv run python -m ingestion.converter_parquet
        uv run python -m ingestion.enviar_volume
        uv run python -m ingestion.criar_bronze
        uv run python -m ingestion.verificar_bronze

EN: SCR.data ingestion: from the Central Bank's official source to the
    bronze layer on Databricks. Each step is a runnable module (see above).
"""
