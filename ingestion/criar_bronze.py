"""
PT: Etapa 4. Cria as tabelas bronze no Databricks a partir dos Parquets do
    volume, executando ingestion/bronze.sql no SQL warehouse.

    CREATE OR REPLACE torna a etapa idempotente: rodar de novo depois de uma
    republicação reconstrói a tabela a partir dos arquivos atuais.

EN: Step 4. Creates the bronze tables on Databricks from the volume's
    Parquet files, running ingestion/bronze.sql on the SQL warehouse.
    CREATE OR REPLACE makes the step idempotent.

Uso / Usage:
    uv run python -m ingestion.criar_bronze
"""

from __future__ import annotations

from pathlib import Path

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import CAMINHO_VOLUME, CATALOGO, SCHEMA

ARQUIVO_SQL = Path(__file__).with_name("bronze.sql")


def instrucoes() -> list[str]:
    """
    PT: Lê o SQL, preenche os marcadores e separa as instruções. A API de
        execução aceita uma instrução por chamada.
    EN: Reads the SQL, fills the placeholders and splits the statements. The
        execution API takes one statement per call.

    PT: A separação é por ";", então bronze.sql não pode ter ";" dentro de
        texto, como nos COMMENT das tabelas.
    EN: Splitting is on ";", so bronze.sql must not have ";" inside string
        literals, such as the tables' COMMENT.
    """
    sem_comentarios = "\n".join(
        linha for linha in ARQUIVO_SQL.read_text(encoding="utf-8").splitlines()
        if not linha.lstrip().startswith("--")
    )
    preenchido = sem_comentarios.format(catalogo=CATALOGO, schema=SCHEMA, volume=CAMINHO_VOLUME)
    return [s.strip() for s in preenchido.split(";") if s.strip()]


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    for sql in instrucoes():
        tabela = sql.split()[4]  # PT: CREATE OR REPLACE TABLE <nome> / EN: same
        print(f"  ... {tabela}")
        executar_sql(w, wid, sql)
        linhas = executar_sql(w, wid, f"SELECT count(*) FROM {tabela}")[0][0]
        print(f"  ok  {tabela}: {int(linhas):,} linhas")


if __name__ == "__main__":
    main()
