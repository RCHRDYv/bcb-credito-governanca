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


def executar_sql(w: WorkspaceClient, warehouse_id: str, sql: str) -> list[list[str]]:
    """
    PT: Executa uma instrução e espera o fim. Um CREATE TABLE sobre dezenas de
        milhões de linhas passa do tempo máximo de espera síncrona da API, por
        isso a função acompanha o estado até a conclusão.
    EN: Runs one statement and waits for completion. A CREATE TABLE over tens
        of millions of rows exceeds the API's synchronous wait limit, so the
        function polls the state until done.
    """
    resp = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id, statement=sql, wait_timeout="50s"
    )
    while resp.status.state not in ESTADOS_FINAIS:
        time.sleep(5)
        resp = w.statement_execution.get_statement(resp.statement_id)

    if resp.status.state != StatementState.SUCCEEDED:
        erro = resp.status.error.message if resp.status.error else resp.status.state
        raise RuntimeError(f"SQL falhou / SQL failed: {erro}\n{sql[:300]}")
    return (resp.result.data_array or []) if resp.result else []
