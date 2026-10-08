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

import http.client
import io
import time
import urllib.request
from dataclasses import dataclass

import polars as pl
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Disposition, Format, StatementState

from ingestion.fontes import PERFIL, WAREHOUSE_ID

ESTADOS_FINAIS = {StatementState.SUCCEEDED, StatementState.FAILED, StatementState.CANCELED, StatementState.CLOSED}

# PT: tentativas de baixar cada bloco Arrow, com espera crescente entre
#     elas. Na exportação de 2026-10-07, cerca de 20 dos blocos do
#     fct_carteira foram cortados no meio do download, e dois só passaram na
#     terceira tentativa.
# EN: attempts to download each Arrow chunk, with growing waits; on
#     2026-10-07 about 20 fct_carteira chunks were cut mid-transfer, and two
#     only passed on the third attempt.
TENTATIVAS_DE_DOWNLOAD = 8


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
    em_arrow: bool = False,
):
    """
    PT: Executa uma instrução e espera o fim. Um CREATE TABLE sobre dezenas de
        milhões de linhas passa do tempo máximo de espera síncrona da API, por
        isso a função acompanha o estado até a conclusão. Catálogo e esquema,
        quando informados, viram o padrão da sessão, e o SQL pode citar as
        tabelas sem prefixo.
        Com em_arrow, o resultado vem em Arrow, por links externos, que é o
        caminho para tabelas grandes e preserva os tipos.
    EN: Runs one statement and waits for completion, polling past the API's
        synchronous wait limit. Catalog and schema, when given, become the
        session default, so the SQL can cite tables without a prefix. With
        em_arrow, the result comes as Arrow through external links, the path
        for large tables, which keeps the types.
    """
    formato = {"format": Format.ARROW_STREAM, "disposition": Disposition.EXTERNAL_LINKS} if em_arrow else {}
    resp = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s",
        catalog=catalogo,
        schema=esquema,
        **formato,
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


def tipo_no_polars(tipo: str) -> pl.DataType:
    """
    PT: Tipo do Databricks, como o information_schema ou o manifesto do
        resultado o escrevem, para o tipo do polars.
    EN: Databricks type, as information_schema or the result manifest spell
        it, to the polars type.
    """
    tipo = tipo.lower()
    if tipo.startswith("decimal("):
        precisao, escala = tipo.removeprefix("decimal(").removesuffix(")").split(",")
        return pl.Decimal(int(precisao), int(escala))
    return {"string": pl.String, "date": pl.Date, "int": pl.Int32, "bigint": pl.Int64, "boolean": pl.Boolean}[tipo]


def _baixar_bloco(w: WorkspaceClient, statement_id: str, indice: int, url: str) -> bytes:
    """
    PT: Baixa um bloco pelo link pré-assinado, sem o cabeçalho de
        autenticação do Databricks, que o armazenamento não precisa ver. A
        cada nova tentativa, pede ao Databricks um link novo para o mesmo
        bloco, porque o link expira em minutos, e repetir um link vencido só
        devolveria o mesmo erro.
    EN: Downloads one chunk by its presigned link, without the Databricks
        auth header. Each retry asks Databricks for a fresh link to the same
        chunk, since links expire within minutes and retrying a dead one only
        repeats the error.
    """
    for tentativa in range(1, TENTATIVAS_DE_DOWNLOAD + 1):
        try:
            with urllib.request.urlopen(url, timeout=300) as resposta:
                return resposta.read()
        except (OSError, http.client.HTTPException) as erro:
            if tentativa == TENTATIVAS_DE_DOWNLOAD:
                raise
            print(f"    download do bloco {indice} interrompido ({type(erro).__name__}), tentativa {tentativa + 1}")
            time.sleep(2**tentativa)
            novo = w.statement_execution.get_statement_result_chunk_n(statement_id, indice)
            url = next(link.external_link for link in novo.external_links if link.chunk_index == indice)
    raise AssertionError("inalcançável / unreachable")


def consultar_em_arrow(w: WorkspaceClient, warehouse_id: str, sql: str) -> pl.DataFrame:
    """
    PT: Executa uma consulta e devolve o resultado inteiro como DataFrame do
        polars, com os tipos do Databricks: decimal, data, booleano e inteiro
        chegam como tais, e não como texto. Serve para tabelas que passam do
        limite do resultado em linha, como o fct_carteira. Um resultado sem
        linhas não tem bloco, e volta como DataFrame vazio com as colunas e
        os tipos do manifesto do resultado.
    EN: Runs a query and returns the whole result as a polars DataFrame with
        Databricks types intact. Meant for tables beyond the inline result
        limit, such as fct_carteira. A result with no rows has no chunk and
        comes back as an empty DataFrame with the result manifest's schema.
    """
    resp = _executar(w, warehouse_id, sql, em_arrow=True)
    partes = []
    for indice in range(resp.manifest.total_chunk_count or 0):
        bloco = resp.result if indice == 0 else w.statement_execution.get_statement_result_chunk_n(
            resp.statement_id, indice
        )
        for link in bloco.external_links or []:
            conteudo = _baixar_bloco(w, resp.statement_id, link.chunk_index, link.external_link)
            partes.append(pl.read_ipc_stream(io.BytesIO(conteudo)))
    if not partes:
        return pl.DataFrame(
            schema={c.name: tipo_no_polars(c.type_text) for c in resp.manifest.schema.columns}
        )
    return pl.concat(partes)
