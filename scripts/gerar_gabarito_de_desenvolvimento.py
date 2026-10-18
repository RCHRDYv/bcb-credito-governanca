"""
PT: Gera as respostas do gabarito do conjunto de desenvolvimento (#118, ADR
    0032) no DuckDB local, sobre o retrato do esquema estrela em
    data/esquema_estrela/. Roda cada SQL de evaluation/desenvolvimento/sql/ e
    grava um JSON por consulta em evaluation/desenvolvimento/respostas/, no
    formato das respostas do teste: consulta, mes_de_referencia, colunas,
    tipos e linhas, tudo em texto.

    Os tipos do DuckDB viram os nomes que o gabarito do teste usa (STRING,
    DATE, BOOLEAN, DOUBLE, DECIMAL, INT, LONG), porque o corretor decide a
    tolerância por eles. O mapa é estrito: tipo desconhecido para o script.
    Com --conferir-mapa, roda os 56 SQL do teste no DuckDB e confere que cada
    coluna cai na mesma classe de tolerância que os tipos congelados das
    respostas do teste dão.

    Nunca grava fora de evaluation/desenvolvimento/respostas/.

EN: Generates the development set's answers on the local DuckDB snapshot,
    one JSON per query in the test answers' format. DuckDB types map strictly
    to the answer key's type names, which drive the grader's tolerance;
    --conferir-mapa checks the map on the 56 test queries. Never writes
    outside the development answers folder.

Uso / Usage:
    uv run python -m scripts.gerar_gabarito_de_desenvolvimento
    uv run python -m scripts.gerar_gabarito_de_desenvolvimento --conferir-mapa
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from assistente.sql import uma_thread
from scripts.analises.qa_esquema_estrela import como_texto
from scripts.esquema_estrela_duckdb import conectar
from scripts.validar_registro import HIPOTESES, PASTA_SQL, RAIZ, classe_de_tolerancia, ler_respostas

PASTA = RAIZ / "evaluation" / "desenvolvimento"
PASTA_SQL_DEV = PASTA / "sql"
PASTA_RESPOSTAS_DEV = PASTA / "respostas"

# PT: tipo do DuckDB para o nome do gabarito. DECIMAL(p,s) vira DECIMAL.
# EN: DuckDB type to the answer key's type name.
TIPOS = {
    "VARCHAR": "STRING",
    "DATE": "DATE",
    "BOOLEAN": "BOOLEAN",
    "DOUBLE": "DOUBLE",
    "FLOAT": "DOUBLE",
    "TINYINT": "INT",
    "SMALLINT": "INT",
    "INTEGER": "INT",
    "BIGINT": "LONG",
    "HUGEINT": "LONG",
}
DECIMAL = re.compile(r"^DECIMAL\(\d+,\s*\d+\)$")


def tipo_do_gabarito(tipo_duckdb: str) -> str:
    """
    PT: O nome do tipo no gabarito. Tipo fora do mapa para o script.
    EN: The answer key type name; unknown types stop the script.
    """
    tipo = str(tipo_duckdb).upper()
    if DECIMAL.match(tipo):
        return "DECIMAL"
    if tipo not in TIPOS:
        raise SystemExit(f"ERRO tipo do DuckDB sem correspondência no gabarito: {tipo}")
    return TIPOS[tipo]


def rodar(banco, arquivo: Path) -> dict:
    """PT: um SQL no DuckDB, com colunas, tipos e linhas em texto / EN: one SQL"""
    cursor = banco.execute(arquivo.read_text(encoding="utf-8"))
    colunas = [d[0] for d in cursor.description]
    tipos = [tipo_do_gabarito(d[1]) for d in cursor.description]
    return {"colunas": colunas, "tipos": tipos, "linhas": [[como_texto(v) for v in l] for l in cursor.fetchall()]}


def conferir_mapa(banco) -> tuple[list[str], int]:
    """
    PT: Os 56 SQL do teste no DuckDB: cada coluna tem de cair na mesma classe
        de tolerância que o tipo congelado na resposta do teste.
    EN: Each test column must land in the same tolerance class as the frozen
        answer type.
    """
    regra = yaml.safe_load((RAIZ / HIPOTESES).read_text(encoding="utf-8"))["comparacao"]["tolerancia"]
    erros, colunas = [], 0
    for consulta, resposta in ler_respostas().items():
        obtido = rodar(banco, RAIZ / PASTA_SQL / consulta)
        if obtido["colunas"] != resposta["colunas"]:
            erros.append(f"{consulta}: colunas {obtido['colunas']} diferem das congeladas")
            continue
        for coluna, tipo, congelado in zip(obtido["colunas"], obtido["tipos"], resposta["tipos"]):
            colunas += 1
            # PT: a classe de tolerância e também o tipo: DATE e STRING caem
            #     os dois em identidade, mas o corretor compara data pelo mês.
            #     INT e LONG se equivalem no corretor.
            # EN: tolerance class and exact type; INT and LONG are equivalent.
            mesmo_tipo = tipo == congelado or {tipo, congelado} <= {"INT", "LONG"}
            if classe_de_tolerancia(coluna, tipo, regra) != classe_de_tolerancia(coluna, congelado, regra) \
                    or not mesmo_tipo:
                erros.append(f"{consulta} {coluna}: {tipo} no DuckDB, {congelado} no gabarito do teste")
    return erros, colunas


def gravar(respostas: dict[str, dict], referencia: str) -> None:
    """
    PT: Um JSON por consulta, só na pasta de desenvolvimento. Resposta de
        consulta que saiu é apagada, só ali.
    EN: One JSON per query, only in the development folder.
    """
    PASTA_RESPOSTAS_DEV.mkdir(parents=True, exist_ok=True)
    esperadas = {Path(c).with_suffix(".json").name for c in respostas}
    for antiga in PASTA_RESPOSTAS_DEV.glob("*.json"):
        if antiga.name not in esperadas:
            antiga.unlink()
    for consulta, r in respostas.items():
        conteudo = {"consulta": consulta, "mes_de_referencia": referencia, **r}
        (PASTA_RESPOSTAS_DEV / Path(consulta).with_suffix(".json").name).write_text(
            json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--conferir-mapa", action="store_true", help="confere o mapa de tipos nos SQL do teste")
    args = parser.parse_args()

    # PT: uma thread só, como o banco do assistente: o gabarito sai igual em
    #     toda rodada.
    # EN: single thread, like the assistant's database.
    banco = uma_thread(conectar())
    if args.conferir_mapa:
        erros, colunas = conferir_mapa(banco)
        print(f"  {colunas} colunas do teste conferidas, {len(erros)} divergências")
        for erro in erros:
            print(f"ERRO {erro}")
        sys.exit(1 if erros else 0)

    referencia = banco.execute("select max(data_base) from fct_carteira").fetchone()[0].isoformat()
    respostas = {arquivo.name: rodar(banco, arquivo) for arquivo in sorted(PASTA_SQL_DEV.glob("D*.sql"))}
    vazias = [c for c, r in respostas.items() if not r["linhas"]]
    if vazias:
        raise SystemExit(f"ERRO consultas sem linha: {vazias}")
    gravar(respostas, referencia)
    print(f"  {len(respostas)} respostas gravadas em {PASTA_RESPOSTAS_DEV.relative_to(RAIZ).as_posix()}, "
          f"retrato de {referencia}")


if __name__ == "__main__":
    main()
