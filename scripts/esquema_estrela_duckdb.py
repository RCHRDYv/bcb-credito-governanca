"""
PT: O retrato do esquema estrela em Parquet e as views do DuckDB (#45, ADR
    0027). Peças comuns à exportação, ao QA e à publicação:

    - a lista do que pode sair: as tabelas dim_* e fct_*, com as colunas e
      os tipos do evaluation/gabarito/esquema_estrela.json, que só é lido;
    - o SQL dos totais por período, o mesmo texto no Databricks e no DuckDB;
    - o esquema_estrela/views.sql, que cria uma view por tabela, com o nome
      do dbt, sobre o Parquet local ou sobre o dataset do Hugging Face;
    - o esquema_estrela/manifesto.json, que fixa o retrato: mês de
      referência, linhas, sha256 e totais de cada tabela, e a revisão do
      dataset publicado.

EN: The star schema snapshot in Parquet and the DuckDB views. Shared by
    export, QA and publication: the allowlist of tables, columns and types
    (read from the answer key's star schema snapshot), the per-period totals
    SQL that runs unchanged on Databricks and DuckDB, the views file, and the
    manifest that pins the snapshot.

Uso / Usage:
    from scripts.esquema_estrela_duckdb import conectar
    banco = conectar("local")          # data/esquema_estrela/
    banco = conectar("hf")             # dataset, na revisão do manifesto
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb

from scripts.gerar_gabarito import gravar_json

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "esquema_estrela"
MANIFESTO = PASTA / "manifesto.json"
VIEWS = PASTA / "views.sql"
CARTAO = PASTA / "README.md"
LOCAL = RAIZ / "data" / "esquema_estrela"
ESQUEMA_ESTRELA = RAIZ / "evaluation" / "gabarito" / "esquema_estrela.json"

REPOSITORIO_HF = "vidayuri/bcb-credito-governanca"
ESQUEMA_NO_DATABRICKS = "workspace.bcb_scr_marts"
TABELA_DO_ESQUEMA_ESTRELA = re.compile(r"^(dim|fct)_[a-z0-9_]+$")

# PT: coluna de período de cada fato. Os totais da reconciliação são por
#     período; as dimensões têm um total só.
# EN: each fact's period column; dimensions have a single total.
PERIODO = {
    "fct_carteira": "data_base",
    "fct_carteira_v1": "data_base",
    "fct_empresas_ativas": "data_base",
    "fct_pix": "data_base",
    "fct_populacao": "ano",
    "fct_renda_do_trabalho": "fim_do_trimestre",
    "fct_selic": "data_base",
}
# PT: colunas numéricas que são calendário, e não medida.
# EN: numeric columns that are calendar, not measure.
CALENDARIO = {"ano", "mes", "trimestre"}
TIPO_NUMERICO = re.compile(r"^(decimal\(\d+,\d+\)|bigint|int)$")

# PT: nomes de coluna que indicariam dado pessoal ou identificador de
#     empresa. Nenhum pode sair, mesmo que entre no esquema estrela.
# EN: column names that would point to personal data or a company
#     identifier; none may leave, even if it reaches the star schema.
NOME_PROIBIDO = re.compile(
    r"cpf|cnpj|razao_social|nome_empresarial|nome_fantasia|email|e_mail|telefone|logradouro|endereco|cep\b|^nome$"
)


# -----------------------------------------------------------------------------
# PT: O que pode sair / EN: what may leave
# -----------------------------------------------------------------------------

def esquema_esperado() -> dict[str, list[list[str]]]:
    """
    PT: Tabelas, colunas e tipos do esquema estrela, na ordem do dbt.
    EN: Star schema tables, columns and types, in dbt order.
    """
    return json.loads(ESQUEMA_ESTRELA.read_text(encoding="utf-8"))


def checar_lista_permitida(esquema: dict[str, list[list[str]]]) -> list[str]:
    """
    PT: Só dim_* e fct_*, e nenhuma coluna com nome de dado pessoal.
    EN: Only dim_* and fct_*, and no column named like personal data.
    """
    erros = [f"{t}: fora do esquema estrela" for t in esquema if not TABELA_DO_ESQUEMA_ESTRELA.match(t)]
    erros += [
        f"{t}.{coluna}: nome de dado pessoal ou de identificador"
        for t, colunas in esquema.items()
        for coluna, _ in colunas
        if NOME_PROIBIDO.search(coluna)
    ]
    return erros


def medidas(tabela: str, colunas: list[list[str]]) -> list[str]:
    """
    PT: As colunas somadas nos totais: as numéricas de um fato, menos o
        calendário. Dimensão não tem medida.
    EN: Columns summed in the totals: a fact's numeric columns, calendar
        excluded. Dimensions have none.
    """
    if not tabela.startswith("fct_"):
        return []
    return [c for c, tipo in colunas if TIPO_NUMERICO.match(tipo) and c not in CALENDARIO]


def sql_dos_totais(tabela: str, colunas: list[list[str]], prefixo: str = "") -> str:
    """
    PT: Linhas e soma de cada medida, por período, em SQL que o Databricks e
        o DuckDB aceitam igual. O período sai como texto, para as duas
        pontas compararem pela mesma chave.
    EN: Rows and the sum of each measure per period, in SQL both engines
        accept. The period comes out as text so both sides share the key.
    """
    periodo = f"cast({PERIODO[tabela]} as string)" if tabela in PERIODO else "'tudo'"
    somas = "".join(f", sum({m}) as {m}" for m in medidas(tabela, colunas))
    return f"select {periodo} as periodo, count(*) as linhas{somas} from {prefixo}{tabela} group by 1 order by 1"


# -----------------------------------------------------------------------------
# PT: Views do DuckDB / EN: DuckDB views
# -----------------------------------------------------------------------------

def texto_das_views(tabelas: list[str]) -> str:
    """
    PT: O esquema_estrela/views.sql: uma view por tabela, com o nome do dbt,
        lendo o Parquet a partir da variável base.
    EN: The views file: one view per table, with the dbt name, reading the
        Parquet from the base variable.
    """
    cabecalho = f"""-- PT: Views do esquema estrela no DuckDB, com os nomes de tabela do dbt
--     (#45, ADR 0027). O SQL do gabarito e do experimento roda sobre elas
--     sem mudar nada. Defina a base antes, local ou no Hugging Face, de
--     preferência na revisão fixada em esquema_estrela/manifesto.json:
--       set variable base = 'data/esquema_estrela';
--       set variable base = 'hf://datasets/{REPOSITORIO_HF}@<revisao_hf>';
-- EN: Star schema views on DuckDB, with the dbt table names. Set the base
--     variable first, local or on Hugging Face, ideally at the revision
--     pinned in the manifest.
-- Gerado por scripts/exportar_esquema_estrela.py / generated, do not edit.
"""
    linhas = [
        f"create or replace view {t} as select * from read_parquet(getvariable('base') || '/data/{t}.parquet');"
        for t in tabelas
    ]
    return cabecalho + "\n" + "\n".join(linhas) + "\n"


def base(origem: str, revisao: str | None = None) -> str:
    """
    PT: Onde estão os Parquets: a pasta local ou o dataset, numa revisão.
    EN: Where the Parquet files live: the local folder or the dataset.
    """
    if origem == "local":
        return LOCAL.as_posix()
    if origem == "hf":
        if not revisao:
            raise SystemExit("O manifesto não tem revisao_hf: publique antes / no revision in the manifest")
        return f"hf://datasets/{REPOSITORIO_HF}@{revisao}"
    raise ValueError(f"origem desconhecida / unknown origin: {origem}")


def conectar(origem: str = "local", revisao: str | None = None, materializar: bool = False) -> duckdb.DuckDBPyConnection:
    """
    PT: Um DuckDB em memória com as views do esquema estrela. Na origem hf,
        a revisão padrão é a do manifesto. Com materializar, cada tabela é
        lida uma vez para a memória, em vez de a cada consulta: é o que o QA
        usa no dataset remoto, para não baixar o fct_carteira 56 vezes.
    EN: An in-memory DuckDB with the star schema views. For hf the default
        revision is the manifest's. With materializar, each table is read
        into memory once instead of on every query.
    """
    if origem == "hf" and revisao is None:
        revisao = carregar_manifesto().get("revisao_hf")
    banco = duckdb.connect()
    banco.execute("set variable base = ?", [base(origem, revisao)])
    banco.execute(VIEWS.read_text(encoding="utf-8"))
    if materializar:
        for (tabela,) in banco.execute("select view_name from duckdb_views() where not internal").fetchall():
            banco.execute(f"create table {tabela}__m as select * from {tabela}")
            banco.execute(f"drop view {tabela}")
            banco.execute(f"alter table {tabela}__m rename to {tabela}")
    return banco


# -----------------------------------------------------------------------------
# PT: Manifesto / EN: manifest
# -----------------------------------------------------------------------------

def carregar_manifesto() -> dict:
    """PT: o manifesto, ou vazio / EN: the manifest, or empty"""
    if not MANIFESTO.exists():
        return {}
    return json.loads(MANIFESTO.read_text(encoding="utf-8"))


def gravar_manifesto(manifesto: dict) -> None:
    """
    PT: Grava o manifesto no mesmo JSON estável das respostas do gabarito.
    EN: Writes the manifest in the answer key's stable JSON format.
    """
    gravar_json(MANIFESTO, manifesto)
