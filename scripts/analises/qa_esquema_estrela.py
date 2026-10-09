"""
PT: QA do retrato do esquema estrela no DuckDB (#45, ADR 0027), por um
    caminho diferente da exportação: o DuckDB lê os Parquets, e o resultado
    é comparado com o que o Databricks calculou.

    O que é conferido:

    1. **Arquivos.** O views.sql está em dia com o retrato. O sha256 de cada
       Parquet bate com o manifesto. No dataset publicado (--origem hf), o
       sha256 vem da API do Hub, sem baixar nada; o dataset tem exatamente
       os Parquets, o cartão e o .gitattributes, sem nenhum caminho de
       evaluation/; e o cartão publicado é o versionado.
    2. **Esquema.** Cada view tem as colunas e os tipos do
       evaluation/gabarito/esquema_estrela.json, o mesmo retrato com que o
       CI confere que o SQL do gabarito roda no DuckDB.
    3. **Totais por período.** Linhas e soma de cada medida, por mês (ou por
       ano e trimestre), no DuckDB, iguais aos do manifesto, que o Databricks
       calculou. Contagem e soma decimal batem exatamente. Com
       --com-databricks, os totais são calculados de novo no Databricks, para
       pegar um retrato que ficou para trás.
    4. **Gabarito.** Os SQL do gabarito rodam no DuckDB, e cada célula é
       comparada com a resposta versionada (evaluation/gabarito/respostas/)
       e, com --com-databricks, com o mesmo SQL rodado agora no Databricks.
       A tolerância de cada coluna é a do pré-registro
       (hipoteses.yml#comparacao.tolerancia), pela classificação do
       validar_registro. O relatório mostra a maior diferença relativa de
       cada consulta, para uma diferença real entre os motores não se
       esconder dentro da banda. O mês de referência das respostas tem de ser
       o do retrato.

    Uma divergência é reportada, e não ajustada: o SQL do gabarito está
    congelado pelo registro da #47.

EN: QA of the star schema snapshot on DuckDB, by a path other than the
    export: DuckDB reads the Parquet files and the result is compared with
    what Databricks computed. Checks the files (views in sync, sha256 against
    the manifest; on the published dataset, via the Hub API, the exact file
    set and the published card), the schema of every view, the per-period
    totals (exact), and every answer key SQL cell by cell against the
    versioned answers and, with --com-databricks, against a live Databricks
    run, within the pre-registered per-column tolerance. Divergences are
    reported, never adjusted.

Uso / Usage:
    uv run python -m scripts.analises.qa_esquema_estrela
    uv run python -m scripts.analises.qa_esquema_estrela --com-databricks
    uv run python -m scripts.analises.qa_esquema_estrela --origem hf
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
import urllib.request
from decimal import Decimal, InvalidOperation

import duckdb

from correcao.tolerancia import banda
from ingestion.baixar import sha256
from scripts.esquema_estrela_duckdb import (
    CARTAO,
    LOCAL,
    REPOSITORIO_HF,
    VIEWS,
    carregar_manifesto,
    conectar,
    esquema_esperado,
    sql_dos_totais,
    texto_das_views,
)
from scripts.gerar_gabarito import GABARITO, PASTA_SQL, carregar, consultas_do_gabarito
from scripts.validar_gabarito import tipo_no_duckdb
from scripts.validar_registro import HIPOTESES, RAIZ, classe_de_tolerancia, ler_respostas

API_DO_HUB = "https://huggingface.co/api/datasets"


class Conferencia:
    """
    PT: Acumula as conferências e as falhas, e diz no fim se tudo passou.
    EN: Accumulates checks and failures.
    """

    def __init__(self) -> None:
        self.total = 0
        self.falhas: list[str] = []

    def checar(self, ok: bool, mensagem: str) -> None:
        """PT: conta uma conferência e guarda a falha / EN: count one check, keep the failure"""
        self.total += 1
        if not ok:
            self.falhas.append(mensagem)


# -----------------------------------------------------------------------------
# PT: Arquivos / EN: files
# -----------------------------------------------------------------------------

def texto_lf(caminho) -> bytes:
    """PT: o texto com LF, como é publicado / EN: LF text, as published"""
    return caminho.read_bytes().replace(b"\r\n", b"\n")


def oid_git(conteudo: bytes) -> str:
    """PT: o sha1 de blob do git, que o Hub mostra / EN: git blob sha1"""
    return hashlib.sha1(b"blob %d\0" % len(conteudo) + conteudo).hexdigest()


def arvore_do_dataset(revisao: str) -> list[dict]:
    """
    PT: Os arquivos do dataset numa revisão, pela API pública do Hub, sem
        token nenhum.
    EN: The dataset's files at a revision, via the public Hub API, no token.
    """
    url = f"{API_DO_HUB}/{REPOSITORIO_HF}/tree/{revisao}?recursive=true"
    with urllib.request.urlopen(url, timeout=60) as resposta:
        return [e for e in json.loads(resposta.read()) if e.get("type") == "file"]


def conferir_arquivos(c: Conferencia, manifesto: dict, origem: str) -> None:
    """PT: views, sha256 e, no Hub, o conjunto de arquivos / EN: files"""
    tabelas = manifesto["tabelas"]
    c.checar(
        texto_lf(VIEWS) == texto_das_views(list(esquema_esperado())).encode("utf-8"),
        "views.sql fora de dia com o retrato; rode scripts.exportar_esquema_estrela",
    )
    if origem == "local":
        for tabela, dados in tabelas.items():
            arquivo = LOCAL / dados["arquivo"]
            c.checar(arquivo.exists() and sha256(arquivo) == dados["sha256"], f"{tabela}: sha256 local diferente do manifesto")
        return

    arvore = {e["path"]: e for e in arvore_do_dataset(manifesto["revisao_hf"])}
    esperados = {".gitattributes", "README.md", *(d["arquivo"] for d in tabelas.values())}
    c.checar(set(arvore) == esperados, f"arquivos do dataset diferentes do esperado: a mais {sorted(set(arvore) - esperados)}, a menos {sorted(esperados - set(arvore))}")
    c.checar(not any(p.startswith("evaluation") or "/evaluation" in p for p in arvore), "o dataset tem caminho de evaluation/")
    for tabela, dados in tabelas.items():
        sha = (arvore.get(dados["arquivo"], {}).get("lfs") or {}).get("oid")
        c.checar(sha == dados["sha256"], f"{tabela}: sha256 no Hub {sha}, no manifesto {dados['sha256']}")
    c.checar(arvore.get("README.md", {}).get("oid") == oid_git(texto_lf(CARTAO)), "o cartão publicado não é o esquema_estrela/README.md versionado")


# -----------------------------------------------------------------------------
# PT: Esquema e totais / EN: schema and totals
# -----------------------------------------------------------------------------

def conferir_esquema(c: Conferencia, banco: duckdb.DuckDBPyConnection) -> None:
    """
    PT: Cada view com os tipos do retrato, pelo nome que o DuckDB dá a eles.
    EN: Each view with the snapshot's types, as DuckDB names them.
    """
    referencia = duckdb.connect()
    for tabela, colunas in esquema_esperado().items():
        definicao = ", ".join(f"{nome} {tipo_no_duckdb(tipo)}" for nome, tipo in colunas)
        referencia.execute(f"create table {tabela} ({definicao})")
        esperado = [linha[:2] for linha in referencia.execute(f"describe {tabela}").fetchall()]
        obtido = [linha[:2] for linha in banco.execute(f"describe {tabela}").fetchall()]
        c.checar(obtido == esperado, f"{tabela}: esquema no DuckDB {obtido} diferente do retrato {esperado}")


def como_texto(valor) -> str | None:
    """
    PT: Um valor do DuckDB no formato em que a API do Databricks o devolve.
        Ponto flutuante com 10 algarismos significativos, como o
        gerar_gabarito grava.
    EN: A DuckDB value in the Databricks API's text form; floats to 10
        significant digits, as the answer key stores them.
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, float):
        return f"{valor:.10g}"
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor.isoformat()
    return str(valor)


def numero(valor: str | None) -> Decimal | None:
    """PT: o texto como Decimal, ou None se não for número / EN: text as Decimal, or None"""
    if valor is None:
        return None
    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def conferir_totais(c: Conferencia, banco: duckdb.DuckDBPyConnection, manifesto: dict, ao_vivo: dict | None) -> None:
    """
    PT: Totais por período no DuckDB iguais aos do manifesto, exatamente; e,
        com o Databricks ao vivo, o manifesto igual ao Databricks de agora.
    EN: DuckDB per-period totals exactly equal to the manifest's; with a live
        Databricks, the manifest equal to today's Databricks.
    """
    for tabela, colunas in esquema_esperado().items():
        no_manifesto = manifesto["tabelas"][tabela]["totais"]
        no_duckdb = [[como_texto(v) for v in linha] for linha in banco.execute(sql_dos_totais(tabela, colunas)).fetchall()]
        referencias = [("manifesto", no_manifesto["linhas"])]
        if ao_vivo is not None:
            referencias.append(("Databricks", ao_vivo[tabela]))
        for nome, linhas in referencias:
            iguais = len(linhas) == len(no_duckdb) and all(
                a[0] == b[0] and [numero(x) for x in a[1:]] == [numero(y) for y in b[1:]]
                for a, b in zip(no_duckdb, linhas)
            )
            c.checar(iguais, f"{tabela}: totais por período do DuckDB diferentes do {nome}")
        periodos = len(no_duckdb)
        print(f"  {tabela:24} {periodos:>3} períodos, {len(no_manifesto['colunas']) - 1} totais por período")


# -----------------------------------------------------------------------------
# PT: Gabarito / EN: answer key
# -----------------------------------------------------------------------------

def dentro(classe: str, obtido: str | None, esperado: str | None) -> tuple[bool, Decimal]:
    """
    PT: Uma célula dentro da tolerância da sua classe, e a diferença relativa.
        Texto, data e booleano têm de ser idênticos: aqui se comparam dois
        motores, e não a resposta da IA, então nem a caixa das letras pode
        mudar.
    EN: One cell within its class tolerance, and the relative difference.
        Text, dates and booleans must be identical: this compares two
        engines, not the AI's answer, so not even letter case may differ.
    """
    if obtido is None or esperado is None:
        return obtido is None and esperado is None, Decimal(0)
    if classe in ("identidade", "classificacao"):
        return obtido == esperado, Decimal(0)
    a, b = numero(obtido), numero(esperado)
    if a is None or b is None:
        return obtido == esperado, Decimal(0)
    diferenca = abs(a - b)
    relativa = diferenca / abs(b) if b else diferenca
    # PT: as faixas do pré-registro, as mesmas do corretor (correcao.tolerancia).
    # EN: the pre-registered bands, shared with the grader.
    return diferenca <= banda(classe, b), relativa


def comparar_resultado(consulta: str, obtido: dict, esperado: dict, regra: dict) -> tuple[list[str], Decimal, str]:
    """
    PT: Mesmas colunas, mesmas linhas e cada célula dentro da tolerância.
        Devolve as falhas, a maior diferença relativa e a coluna dela.
    EN: Same columns, same rows, every cell within tolerance. Returns the
        failures, the largest relative difference and its column.
    """
    if obtido["colunas"] != esperado["colunas"]:
        return [f"{consulta}: colunas {obtido['colunas']}, esperado {esperado['colunas']}"], Decimal(0), ""
    if len(obtido["linhas"]) != len(esperado["linhas"]):
        return [f"{consulta}: {len(obtido['linhas'])} linhas, esperado {len(esperado['linhas'])}"], Decimal(0), ""
    classes = [classe_de_tolerancia(c, t, regra) for c, t in zip(esperado["colunas"], esperado["tipos"])]
    falhas, maior, coluna_da_maior = [], Decimal(0), ""
    for numero_da_linha, (linha_obtida, linha_esperada) in enumerate(zip(obtido["linhas"], esperado["linhas"]), start=1):
        for coluna, classe, a, b in zip(esperado["colunas"], classes, linha_obtida, linha_esperada):
            ok, relativa = dentro(classe, a, b)
            if relativa > maior:
                maior, coluna_da_maior = relativa, coluna
            if not ok:
                falhas.append(f"{consulta} linha {numero_da_linha} {coluna} ({classe}): DuckDB {a}, esperado {b}")
    return falhas, maior, coluna_da_maior


def rodar_no_duckdb(banco: duckdb.DuckDBPyConnection, consulta: str) -> dict:
    """PT: um SQL do gabarito no DuckDB / EN: one answer key SQL on DuckDB"""
    cursor = banco.execute((PASTA_SQL / consulta).read_text(encoding="utf-8"))
    colunas = [d[0] for d in cursor.description]
    return {"colunas": colunas, "linhas": [[como_texto(v) for v in linha] for linha in cursor.fetchall()]}


def conferir_gabarito(c: Conferencia, banco: duckdb.DuckDBPyConnection, manifesto: dict, ao_vivo: dict | None) -> None:
    """PT: cada SQL do gabarito no DuckDB / EN: every answer key SQL on DuckDB"""
    regra = carregar(RAIZ / HIPOTESES)["comparacao"]["tolerancia"]
    respostas = ler_respostas()
    meses = {r["mes_de_referencia"] for r in respostas.values()}
    c.checar(meses == {manifesto["mes_de_referencia"]}, f"respostas de {sorted(meses)}, retrato de {manifesto['mes_de_referencia']}")

    print(f"\n  {'consulta':32} {'linhas':>6}  {'maior dif. relativa':>20}  coluna")
    for consulta in consultas_do_gabarito(carregar(GABARITO)):
        obtido = rodar_no_duckdb(banco, consulta)
        referencias = [("respostas", respostas[consulta])]
        if ao_vivo is not None:
            referencias.append(("Databricks", ao_vivo[consulta]))
        maior, coluna = Decimal(0), ""
        for nome, esperado in referencias:
            falhas, relativa, col = comparar_resultado(consulta, obtido, esperado, regra)
            c.checar(not falhas, f"contra {nome}: " + "; ".join(falhas[:3]) + (f" (+{len(falhas) - 3})" if len(falhas) > 3 else ""))
            if relativa > maior:
                maior, coluna = relativa, col
        print(f"  {consulta:32} {len(obtido['linhas']):>6}  {float(maior):>20.3e}  {coluna}")


# -----------------------------------------------------------------------------
# PT: Databricks ao vivo / EN: live Databricks
# -----------------------------------------------------------------------------

def referencias_ao_vivo(manifesto: dict) -> tuple[dict, dict]:
    """
    PT: Os totais e os resultados do gabarito calculados agora no Databricks.
    EN: Totals and answer key results computed now on Databricks.
    """
    from ingestion.databricks import cliente, consultar, warehouse
    from scripts.gerar_gabarito import rodar

    w = cliente()
    wid = warehouse(w)
    catalogo, esquema = manifesto["origem"].split(".")
    totais = {
        tabela: consultar(w, wid, sql_dos_totais(tabela, colunas, f"{manifesto['origem']}.")).linhas
        for tabela, colunas in esquema_esperado().items()
    }
    gabarito = {}
    for consulta in consultas_do_gabarito(carregar(GABARITO)):
        resultado = rodar(w, wid, catalogo, esquema, consulta)
        gabarito[consulta] = {"colunas": resultado.colunas, "tipos": resultado.tipos, "linhas": resultado.linhas}
    return totais, gabarito


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--origem", choices=["local", "hf"], default="local", help="Parquet local ou dataset publicado")
    parser.add_argument("--com-databricks", action="store_true", help="compara também com o Databricks ao vivo")
    argumentos = parser.parse_args()

    manifesto = carregar_manifesto()
    if not manifesto:
        raise SystemExit("Sem manifesto: rode scripts.exportar_esquema_estrela / no manifest")
    if argumentos.origem == "hf" and not manifesto.get("revisao_hf"):
        raise SystemExit(
            "O manifesto não tem revisao_hf: o retrato exportado ainda não foi publicado. Rode "
            "scripts.publicar_esquema_estrela. / The exported snapshot has not been published yet."
        )
    print(f"Retrato de {manifesto['mes_de_referencia']}, origem {argumentos.origem}"
          + (f", revisão {manifesto.get('revisao_hf')}" if argumentos.origem == "hf" else ""))

    c = Conferencia()
    conferir_arquivos(c, manifesto, argumentos.origem)
    totais_ao_vivo, gabarito_ao_vivo = referencias_ao_vivo(manifesto) if argumentos.com_databricks else (None, None)

    banco = conectar(argumentos.origem, materializar=argumentos.origem == "hf")
    conferir_esquema(c, banco)
    print("\nTotais por período / per-period totals:")
    conferir_totais(c, banco, manifesto, totais_ao_vivo)
    conferir_gabarito(c, banco, manifesto, gabarito_ao_vivo)

    print(f"\n{c.total} conferências, {len(c.falhas)} falhas / checks, failures")
    for falha in c.falhas:
        print(f"  ERRO {falha}")
    if c.falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
