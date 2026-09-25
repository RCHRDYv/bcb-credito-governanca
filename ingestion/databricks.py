"""
PT: Acesso ao Databricks compartilhado pelas etapas da ingestão.

    A autenticação é a do perfil do CLI (~/.databrickscfg), por OAuth, com o
    token guardado no cofre do sistema operacional. Nenhuma credencial passa
    por este código, por variável de ambiente ou por arquivo do repositório.

EN: Databricks access shared by the ingestion steps.

    Authentication is the CLI profile's (~/.databrickscfg), via OAuth, with
    the token kept in the operating system's vault. No credential goes
    through this code, an environment variable or a repository file.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

from ingestion.fontes import PERFIL, WAREHOUSE_ID

ESTADOS_FINAIS = {StatementState.SUCCEEDED, StatementState.FAILED, StatementState.CANCELED, StatementState.CLOSED}


def cliente() -> WorkspaceClient:
    """PT: cliente autenticado pelo perfil / EN: client authenticated by profile"""
    return WorkspaceClient(profile=PERFIL)


def warehouse(w: WorkspaceClient) -> str:
    """
    PT: Usa o warehouse informado por variável de ambiente ou, na falta dele,
        o primeiro do workspace. No Free Edition existe um só.
    EN: Uses the warehouse given by environment variable or, failing that,
        the workspace's first one. Free Edition has exactly one.
    """
    if WAREHOUSE_ID:
        return WAREHOUSE_ID
    primeiro = next(iter(w.warehouses.list()), None)
    if primeiro is None:
        raise SystemExit("Nenhum SQL warehouse no workspace / no SQL warehouse in the workspace")
    return primeiro.id


def _executar(
    w: WorkspaceClient,
    warehouse_id: str,
    sql: str,
    catalogo: str | None = None,
    esquema: str | None = None,
):
    """
    PT: Executa uma instrução e espera o fim. Um CREATE TABLE sobre dezenas de
        milhões de linhas passa do tempo máximo de espera síncrona da API, por
        isso a função acompanha o estado até a conclusão. Catálogo e esquema,
        quando informados, viram o padrão da sessão, e o SQL pode citar as
        tabelas sem prefixo.
    EN: Runs one statement and waits for completion, polling past the API's
        synchronous wait limit. Catalog and schema, when given, become the
        session default, so the SQL can cite tables without a prefix.
    """
    resp = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s",
        catalog=catalogo,
        schema=esquema,
    )
    while resp.status.state not in ESTADOS_FINAIS:
        time.sleep(5)
        resp = w.statement_execution.get_statement(resp.statement_id)

    if resp.status.state != StatementState.SUCCEEDED:
        erro = resp.status.error.message if resp.status.error else resp.status.state
        raise RuntimeError(f"SQL falhou / SQL failed: {erro}\n{sql[:300]}")
    return resp


def executar_sql(w: WorkspaceClient, warehouse_id: str, sql: str) -> list[list[str]]:
    """
    PT: Executa uma instrução e devolve as linhas do primeiro bloco de
        resultado, que basta para instruções de carga e consultas pequenas.
    EN: Runs one statement and returns the first result chunk's rows, enough
        for load statements and small queries.
    """
    resp = _executar(w, warehouse_id, sql)
    return (resp.result.data_array or []) if resp.result else []


@dataclass(frozen=True)
class Resultado:
    """
    PT: Resultado de uma consulta: nomes e tipos das colunas, e as linhas com
        os valores como texto, do jeito que a API os serializa.
    EN: A query result: column names and types, and rows with values as text,
        as the API serialises them.
    """

    colunas: list[str]
    tipos: list[str]
    linhas: list[list[str | None]]


def consultar(
    w: WorkspaceClient,
    warehouse_id: str,
    sql: str,
    catalogo: str | None = None,
    esquema: str | None = None,
) -> Resultado:
    """
    PT: Executa uma consulta e devolve colunas, tipos e todas as linhas,
        inclusive as dos blocos seguintes ao primeiro. A conversão de tipo
        fica com quem chama.
    EN: Runs a query and returns columns, types and every row, including the
        chunks after the first. Type conversion is up to the caller.
    """
    resp = _executar(w, warehouse_id, sql, catalogo, esquema)
    esquema_do_resultado = resp.manifest.schema.columns if resp.manifest else []
    linhas = list((resp.result.data_array or []) if resp.result else [])

    total_de_blocos = (resp.manifest.total_chunk_count or 1) if resp.manifest else 1
    for indice in range(1, total_de_blocos):
        bloco = w.statement_execution.get_statement_result_chunk_n(resp.statement_id, indice)
        linhas.extend(bloco.data_array or [])

    return Resultado(
        colunas=[c.name for c in esquema_do_resultado],
        tipos=[c.type_name.value if c.type_name else "" for c in esquema_do_resultado],
        linhas=linhas,
    )
