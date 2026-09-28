"""
PT: Exporta os marts de apresentação para os JSON que o site do dashboard lê
    (#66, ADRs 0007 e 0016).

    O que exportar vem do contrato, dashboard/contrato-dos-dados.yml: as
    colunas, o filtro e a ordem das linhas de cada arquivo. Este script não
    tem regra própria por arquivo. Roda na máquina local, com o login OAuth
    do Databricks (ADR 0001), e grava em dashboard/public/data/:
    - um JSON por mart, por coluna;
    - o ontologia.json, gerado de ontology/*.yml;
    - o manifesto.json, com a data-base, os parâmetros da decisão e o sha256
      de cada arquivo, sem data de geração.

    Rodar de novo com o mesmo dado produz os mesmos arquivos, byte a byte.

    Depois de gravar, confere cada arquivo contra o mart com uma consulta
    independente: a contagem de linhas e a soma das colunas de reais e de
    empresas. Qualquer diferença fora do arredondamento faz o script falhar.

    Com --sem-databricks, refaz só o ontologia.json e o manifesto.json a
    partir dos arquivos já exportados. É o que o CI roda para conferir que os
    dois estão em dia com a ontologia e com os dados versionados.

EN: Exports the presentation marts to the JSON files the dashboard site
    reads. What to export comes from the contract; this script has no
    per-file rule. Runs locally with the Databricks OAuth login, writes one
    column-oriented JSON per mart plus ontologia.json and manifesto.json, and
    checks each file against its mart with an independent query. Same data,
    same bytes. With --sem-databricks it only rebuilds the ontology and the
    manifest from the files already exported, which is what CI runs.

Uso / usage:
    uv run python -m scripts.exportar_dados_do_dashboard
    uv run python -m scripts.exportar_dados_do_dashboard --sem-databricks
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from decimal import Decimal

from ingestion.databricks import cliente, consultar, warehouse
from scripts.contrato_do_dashboard import (
    DESTINO,
    MANIFESTO,
    ONTOLOGIA,
    RAIZ,
    carregar_contrato,
    codigos_de_modalidade,
    converter,
    gravar,
    montar_manifesto,
    montar_ontologia,
    texto_de_dados,
    texto_de_registro,
)

MARTS = "workspace.bcb_scr_marts"

# PT: Colunas que o QA soma, pela unidade. Reais por empresa ficam fora,
#     porque a soma de uma razão não quer dizer nada.
# EN: Columns the QA sums, by unit.
UNIDADES_SOMADAS = {"reais", "empresas"}


# -----------------------------------------------------------------------------
# PT: Consulta aos marts / EN: querying the marts
# -----------------------------------------------------------------------------


def data_base_da_exportacao(w, wid) -> str:
    """
    PT: A data-base da exportação: o último mês do SCR no mrt_decisao.
    EN: The export's data-base: the last SCR month in mrt_decisao.
    """
    return consultar(w, wid, f"select max(data_base) from {MARTS}.mrt_decisao").linhas[0][0][:10]


def clausula_onde(w, wid, spec: dict, data_base: str) -> str:
    """
    PT: Monta o `where` a partir das chaves do contrato: `onde`, `ultimo_mes`
        e `meses`. Os meses são contados do último para trás, entre os que o
        mart tem, e nunca passam da data-base da exportação.
    EN: Builds the `where` from the contract keys.
    """
    condicoes = []
    if spec.get("onde"):
        condicoes.append(f"({spec['onde']})")
    if spec.get("ultimo_mes"):
        condicoes.append(f"data_base = date'{data_base}'")
    if spec.get("meses"):
        condicoes.append(f"data_base <= date'{data_base}'")
        onde = " where " + " and ".join(condicoes)
        meses = consultar(
            w, wid, f"select distinct data_base from {MARTS}.{spec['origem']}{onde} order by data_base"
        ).linhas
        primeiro = [linha[0][:10] for linha in meses][-int(spec["meses"])]
        condicoes.append(f"data_base >= date'{primeiro}'")
    return " where " + " and ".join(condicoes) if condicoes else ""


def exportar_arquivo(w, wid, spec: dict, data_base: str, onde: str) -> str:
    """
    PT: Lê do mart as colunas do contrato, na ordem do grão, e devolve o
        texto do JSON.
    EN: Reads the contract's columns from the mart, in grain order, and
        returns the JSON text.
    """
    nomes = [coluna["nome"] for coluna in spec["colunas"]]
    sql = (
        f"select {', '.join(nomes)} from {MARTS}.{spec['origem']}{onde} "
        f"order by {', '.join(spec['ordem'])}"
    )
    resultado = consultar(w, wid, sql)
    colunas = {
        coluna["nome"]: [converter(linha[indice], coluna) for linha in resultado.linhas]
        for indice, coluna in enumerate(spec["colunas"])
    }
    return texto_de_dados(spec["arquivo"], data_base, colunas)


def conferir_contra_o_mart(w, wid, spec: dict, onde: str, conteudo: dict) -> list[tuple]:
    """
    PT: QA independente: uma consulta de agregação, feita à parte, com a
        contagem de linhas e a soma de cada coluna de reais e de empresas.
        Reais podem diferir até meio real por linha, pelo arredondamento;
        contagens precisam bater exatamente.
    EN: Independent QA: a separate aggregate query with the row count and the
        sum of every reais and companies column. Reais may differ by up to
        half a real per row from rounding; counts must match exactly.
    """
    somadas = [coluna for coluna in spec["colunas"] if coluna["unidade"] in UNIDADES_SOMADAS]
    expressoes = ["count(*)"] + [f"sum({coluna['nome']})" for coluna in somadas]
    linha = consultar(w, wid, f"select {', '.join(expressoes)} from {MARTS}.{spec['origem']}{onde}").linhas[0]

    colunas = conteudo["colunas"]
    linhas_no_json = len(next(iter(colunas.values())))
    resultados = [(spec["arquivo"], "linhas", Decimal(linha[0]), Decimal(linhas_no_json), Decimal(0))]
    for coluna, soma_no_mart in zip(somadas, linha[1:], strict=True):
        valores = [v for v in colunas[coluna["nome"]] if v is not None]
        tolerancia = Decimal("0.5") * len(valores) if coluna["unidade"] == "reais" else Decimal(0)
        resultados.append(
            (spec["arquivo"], coluna["nome"], Decimal(soma_no_mart or 0), Decimal(sum(valores)), tolerancia)
        )
    return resultados


# -----------------------------------------------------------------------------
# PT: Arquivos auxiliares / EN: auxiliary files
# -----------------------------------------------------------------------------


def gravar_auxiliares(contrato: dict, data_base: str, textos: dict[str, str]) -> None:
    """
    PT: Monta e grava o ontologia.json e o manifesto.json. O manifesto vem
        por último, porque guarda o sha256 dos outros.
    EN: Builds and writes ontologia.json and manifesto.json, the manifest
        last because it holds the others' sha256.
    """
    conteudos = {nome: json.loads(texto) for nome, texto in textos.items()}
    ontologia = montar_ontologia(contrato, codigos_de_modalidade(conteudos))
    textos[ONTOLOGIA] = texto_de_registro(ontologia)
    gravar(DESTINO / ONTOLOGIA, textos[ONTOLOGIA])

    textos[MANIFESTO] = texto_de_registro(montar_manifesto(contrato, data_base, textos))
    gravar(DESTINO / MANIFESTO, textos[MANIFESTO])


def resumo(textos: dict[str, str]) -> None:
    """PT: linhas e peso de cada arquivo / EN: rows and size per file"""
    print("\nArquivos / files (bytes, gzip nível 9):")
    for nome, texto in textos.items():
        dados = texto.encode("utf-8")
        comprimido = len(gzip.compress(dados, compresslevel=9, mtime=0))
        print(f"  {nome:28} {len(dados):>9} B  {comprimido:>8} B gz")


# -----------------------------------------------------------------------------
# PT: Execução / EN: entry point
# -----------------------------------------------------------------------------


def exportar_do_databricks(contrato: dict) -> tuple[str, dict[str, str]]:
    """
    PT: Exporta cada arquivo do contrato e faz o QA contra os marts.
    EN: Exports each contract file and runs the QA against the marts.
    """
    w = cliente()
    wid = warehouse(w)
    data_base = data_base_da_exportacao(w, wid)
    print(f"Data-base da exportação / export data-base: {data_base}")

    textos: dict[str, str] = {}
    conferencias: list[tuple] = []
    for spec in contrato["arquivos"]:
        onde = clausula_onde(w, wid, spec, data_base)
        texto = exportar_arquivo(w, wid, spec, data_base, onde)
        gravar(DESTINO / spec["arquivo"], texto)
        textos[spec["arquivo"]] = texto
        conferencias += conferir_contra_o_mart(w, wid, spec, onde, json.loads(texto))
        print(f"  gravado / written: {spec['arquivo']}")

    print("\nQA contra os marts / QA against the marts:")
    falhas = 0
    for arquivo, medida, no_mart, no_json, tolerancia in conferencias:
        ok = abs(no_mart - no_json) <= tolerancia
        falhas += not ok
        diferenca = no_json - no_mart
        print(f"  {'ok ' if ok else 'ERRO'} {arquivo:28} {medida:32} mart={no_mart:>22} json={no_json:>20} dif={diferenca}")
    if falhas:
        print(f"\n{falhas} conferências fora da tolerância / checks out of tolerance")
        sys.exit(1)
    return data_base, textos


def ler_exportados(contrato: dict) -> tuple[str, dict[str, str]]:
    """
    PT: Lê os arquivos de dados já exportados, sem o Databricks.
    EN: Reads the data files already exported, without Databricks.
    """
    textos = {
        spec["arquivo"]: (DESTINO / spec["arquivo"]).read_text(encoding="utf-8") for spec in contrato["arquivos"]
    }
    datas = {json.loads(texto)["data_base"] for texto in textos.values()}
    if len(datas) != 1:
        raise SystemExit(f"Os arquivos têm datas-base diferentes / files disagree on data-base: {sorted(datas)}")
    return datas.pop(), textos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--sem-databricks",
        action="store_true",
        help="refaz só o ontologia.json e o manifesto.json / only rebuild ontology and manifest",
    )
    argumentos = parser.parse_args()

    contrato = carregar_contrato()
    if argumentos.sem_databricks:
        data_base, textos = ler_exportados(contrato)
    else:
        data_base, textos = exportar_do_databricks(contrato)

    gravar_auxiliares(contrato, data_base, textos)
    resumo(textos)
    print(f"\nGravado em / written to: {DESTINO.relative_to(RAIZ).as_posix()}/")


if __name__ == "__main__":
    main()
