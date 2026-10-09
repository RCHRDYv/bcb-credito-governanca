"""
PT: A ferramenta de SQL do assistente: guarda, banco travado e execução
    com limite de linhas e de tempo (ADR 0012, decisão 1; ADR 0029).

    Guarda, antes de rodar, pela árvore do próprio DuckDB:
    1. um comando só, do tipo SELECT (duckdb.extract_statements);
    2. a árvore sai do json_serialize_sql, que só aceita SELECT: pragma,
       comando de escrita e afins reprovam aqui;
    3. lista do que é permitido: só tabela base com nome dim_* ou fct_*, ou
       uma CTE do próprio comando, sem prefixo de esquema ou de catálogo.
       Função de tabela (read_parquet, glob, query e afins) e as referências
       de SHOW e DESCRIBE reprovam.

    Banco: o DuckDB em memória com as views do retrato (#45). Depois de
    criar as views, o acesso a arquivo fica restrito à pasta do retrato, o
    acesso externo é desligado e a configuração é travada. Assim, mesmo um
    SQL que escapasse da guarda não leria outro arquivo.

    Execução: na própria conexão, uma consulta por vez (um cursor seria
    outra conexão, sem a variável base que as views leem); o limite de tempo
    interrompe a consulta por conexao.interrupt(), num timer; o limite de linhas é aplicado por fora do
    SQL: busca N+1 linhas e, só quando passa de N, conta o total com
    count(*) sobre o próprio comando, dentro do mesmo limite de tempo, e
    marca o corte (decisão de 2026-10-08). Contar buscando as linhas no
    Python levava 104 s no fct_carteira inteiro (medido em 2026-10-08). Os valores saem como texto, no formato das respostas do
    gabarito.

EN: The assistant's SQL tool: guard, locked database and execution with row
    and time limits. The guard uses DuckDB's own parser: a single SELECT,
    serialized by json_serialize_sql, reading only dim_*/fct_* base tables
    or its own CTEs, with no schema or catalog prefix and no table functions.
    The database restricts file access to the snapshot folder, disables
    external access and locks its configuration. Time limit by interrupt();
    row limit applied outside the SQL: fetch N+1 rows and, only when cut,
    count the total with count(*) over the same statement.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field

import duckdb

from scripts.analises.qa_esquema_estrela import como_texto
from scripts.esquema_estrela_duckdb import LOCAL, TABELA_DO_ESQUEMA_ESTRELA, conectar, esquema_esperado
from scripts.validar_gabarito import tipo_no_duckdb

# PT: tipos de referência de tabela que nunca passam. BASE_TABLE passa só
#     pela lista do que é permitido; SUBQUERY, JOIN, EMPTY e
#     EXPRESSION_LIST (VALUES) são estrutura do próprio comando.
# EN: table reference types that never pass.
REFERENCIA_PROIBIDA = {"TABLE_FUNCTION", "SHOW_REF", "COLUMN_DATA", "DELIM_GET"}

# PT: uma consulta por vez na conexão; a interface pode chamar de outra thread.
# EN: one query at a time on the connection; the interface may call from
#     another thread.
_UMA_POR_VEZ = threading.Lock()


class ErroDeSQL(Exception):
    """
    PT: Falha da ferramenta de SQL. O tipo é guarda, sql ou tempo, e vira o
        tipo do erro da execução (falhas do pré-registro, sem nova
        tentativa).
    EN: SQL tool failure; the type becomes the run's error type.
    """

    def __init__(self, tipo: str, mensagem: str):
        super().__init__(mensagem)
        self.tipo = tipo


@dataclass
class Analise:
    """PT: o que a guarda achou no SQL / EN: what the guard found in the SQL"""

    problemas: list[str] = field(default_factory=list)
    tabelas: set[str] = field(default_factory=set)
    colunas: set[str] = field(default_factory=set)
    literais: set[str] = field(default_factory=set)


# -----------------------------------------------------------------------------
# PT: Guarda / EN: guard
# -----------------------------------------------------------------------------

def _nos(no):
    """PT: todos os dicionários da árvore / EN: every dict in the tree"""
    if isinstance(no, dict):
        yield no
        for valor in no.values():
            yield from _nos(valor)
    elif isinstance(no, list):
        for valor in no:
            yield from _nos(valor)


def analisar(sql: str) -> Analise:
    """
    PT: Confere o SQL e devolve as tabelas, as colunas e os literais de texto
        que ele lê, para a proveniência. Problema na lista reprova.
    EN: Checks the SQL and returns the tables, columns and text literals it
        reads, for provenance. Any problem rejects it.
    """
    analise = Analise()
    try:
        comandos = duckdb.extract_statements(sql)
    except duckdb.Error as erro:
        analise.problemas.append(f"SQL não interpretável: {str(erro).splitlines()[0]}")
        return analise
    if len(comandos) != 1:
        analise.problemas.append(f"{len(comandos)} comandos; só um é aceito")
        return analise
    if comandos[0].type != duckdb.StatementType.SELECT:
        analise.problemas.append(f"comando {comandos[0].type.name}; só SELECT é aceito")
        return analise

    arvore = json.loads(duckdb.connect().execute("select json_serialize_sql(?)", [sql]).fetchone()[0])
    if arvore.get("error"):
        analise.problemas.append(f"comando recusado: {arvore.get('error_message', '')}")
        return analise

    nos = list(_nos(arvore))
    ctes = {par["key"] for no in nos if isinstance(no.get("cte_map"), dict) for par in no["cte_map"]["map"]}
    for no in nos:
        # PT: "type" também é o tipo de dado de uma constante, um dicionário.
        # EN: "type" is also a constant's data type, a dict.
        tipo = no.get("type") if isinstance(no.get("type"), str) else None
        if tipo in REFERENCIA_PROIBIDA:
            nome = (no.get("function") or {}).get("function_name", tipo)
            analise.problemas.append(f"{nome}: função de tabela ou referência proibida")
        elif tipo == "BASE_TABLE":
            nome, esquema, catalogo = no.get("table_name", ""), no.get("schema_name", ""), no.get("catalog_name", "")
            if esquema or catalogo:
                analise.problemas.append(f"{catalogo}.{esquema}.{nome}: prefixo de esquema ou catálogo")
            elif nome in ctes:
                continue
            elif TABELA_DO_ESQUEMA_ESTRELA.match(nome):
                analise.tabelas.add(nome)
            else:
                analise.problemas.append(f"{nome}: tabela fora do esquema estrela")
        if no.get("class") == "COLUMN_REF":
            analise.colunas.add(no["column_names"][-1])
        if no.get("class") == "CONSTANT" and no["value"]["type"]["id"] == "VARCHAR" and not no["value"]["is_null"]:
            analise.literais.add(no["value"]["value"])
    return analise


# -----------------------------------------------------------------------------
# PT: Banco / EN: database
# -----------------------------------------------------------------------------

def travar(banco: duckdb.DuckDBPyConnection, pasta_permitida: str | None) -> duckdb.DuckDBPyConnection:
    """
    PT: Restringe o acesso a arquivo à pasta do retrato (ou a nenhuma),
        desliga o acesso externo e trava a configuração.
    EN: Restricts file access to the snapshot folder (or none), disables
        external access and locks the configuration.
    """
    # PT: literal de texto do SQL, com o apóstrofo dobrado; o repr do Python
    #     poria aspas duplas num caminho com apóstrofo.
    # EN: SQL string literal with the quote doubled.
    pastas = ["'" + pasta_permitida.replace("'", "''") + "'"] if pasta_permitida else []
    banco.execute(f"set allowed_directories = [{', '.join(pastas)}]")
    banco.execute("set enable_external_access = false")
    banco.execute("set lock_configuration = true")
    return banco


def abrir_banco() -> duckdb.DuckDBPyConnection:
    """
    PT: O retrato local do esquema estrela (data/esquema_estrela/), travado.
    EN: The local star schema snapshot, locked.
    """
    if not (LOCAL / "data").exists():
        raise SystemExit("ERRO retrato local ausente: rode scripts.exportar_esquema_estrela / snapshot missing")
    return travar(conectar("local"), LOCAL.as_posix() + "/")


def banco_vazio() -> duckdb.DuckDBPyConnection:
    """
    PT: Tabelas vazias com as colunas e os tipos do esquema estrela, travado.
        É o banco dos testes no CI, que não tem o dado.
    EN: Empty tables with the star schema columns and types, locked; the CI
        test database, which has no data.
    """
    banco = duckdb.connect()
    for tabela, colunas in esquema_esperado().items():
        definicao = ", ".join(f"{nome} {tipo_no_duckdb(tipo)}" for nome, tipo in colunas)
        banco.execute(f"create table {tabela} ({definicao})")
    return travar(banco, None)


# -----------------------------------------------------------------------------
# PT: Execução / EN: execution
# -----------------------------------------------------------------------------

def executar(banco: duckdb.DuckDBPyConnection, sql: str, limite_de_linhas: int, limite_de_tempo: float) -> dict:
    """
    PT: Roda o SQL uma vez. Devolve colunas, tipos, as N
        primeiras linhas em texto, o total de linhas e se houve corte.
        Levanta ErroDeSQL com o tipo guarda, sql ou tempo.
    EN: Runs the SQL once. Returns columns, types, the
        first N rows as text, the total row count and whether it was cut.
        Raises ErroDeSQL typed guarda, sql or tempo.
    """
    analise = analisar(sql)
    if analise.problemas:
        raise ErroDeSQL("guarda", "; ".join(analise.problemas))

    comando = sql.strip().rstrip(";").strip()
    estourou = threading.Event()

    def interromper():
        estourou.set()
        banco.interrupt()

    with _UMA_POR_VEZ:
        relogio = threading.Timer(limite_de_tempo, interromper)
        inicio = time.perf_counter()
        relogio.start()
        try:
            banco.execute(comando)
            colunas = [d[0] for d in banco.description]
            tipos = [str(d[1]) for d in banco.description]
            linhas = banco.fetchmany(limite_de_linhas + 1)
            total = len(linhas)
            if total > limite_de_linhas:
                linhas = linhas[:limite_de_linhas]
                # PT: quebra de linha antes do parêntese: um comentário -- no
                #     fim do comando não engole o fechamento.
                # EN: newline before the parenthesis, so a trailing -- comment
                #     does not swallow it.
                total = banco.execute(f"select count(*) from (\n{comando}\n) as resultado").fetchone()[0]
        except duckdb.Error as erro:
            # PT: interrompida no meio da busca, a consulta não levanta
            #     InterruptException; a marca do relógio é que diz.
            # EN: interrupted mid-fetch, the query does not raise
            #     InterruptException; the timer's flag tells.
            if estourou.is_set():
                raise ErroDeSQL("tempo", f"passou de {limite_de_tempo:g} s") from None
            raise ErroDeSQL("sql", str(erro).splitlines()[0]) from None
        finally:
            relogio.cancel()
        # PT: interrompida sem erro, a busca pode ter devolvido linhas pela
        #     metade; o tempo esgotado vale do mesmo jeito.
        # EN: interrupted without an error, the fetch may be partial; still
        #     a timeout.
        if estourou.is_set():
            raise ErroDeSQL("tempo", f"passou de {limite_de_tempo:g} s")
        segundos = round(time.perf_counter() - inicio, 3)
    return {
        "colunas": colunas,
        "tipos": tipos,
        "linhas": [[como_texto(v) for v in linha] for linha in linhas],
        "total_de_linhas": total,
        "cortado": total > len(linhas),
        "segundos": segundos,
        "tabelas": sorted(analise.tabelas),
        "colunas_lidas": sorted(analise.colunas),
        "literais": sorted(analise.literais),
    }
