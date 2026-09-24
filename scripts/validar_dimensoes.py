"""
PT: Valida ontology/dimensoes.yml em duas camadas.

    1. Estrutura: id e coluna únicos, definição e fonte em todo conceito,
       confiança com valor permitido, e valores sem rótulo repetido dentro da
       mesma dimensão.
    2. Dado: para cada dimensão com valores enumerados, todo valor distinto do
       bronze V2 tem conceito, todo conceito ocorre no dado, e o campo
       aplica_a bate com os tipos de cliente em que o valor realmente aparece.

    A terceira checagem é a que importa para a tese: ela impede que a
    ontologia afirme "este valor é de pessoa física" sem que o dado concorde.
    É o que transforma a armadilha do polimorfismo em algo verificável.

EN: Validates ontology/dimensoes.yml in two layers: structure (unique ids and
    columns, definition and source everywhere, allowed confidence, no repeated
    labels) and data (every distinct value in V2 bronze has a concept, every
    concept occurs in the data, and the aplica_a field matches the client types
    the value actually appears with).

Uso / Usage:
    uv run python -m scripts.validar_dimensoes
    uv run python -m scripts.validar_dimensoes --estrutura   # sem Databricks
"""

from __future__ import annotations

import calendar
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

ARQUIVO = Path(__file__).resolve().parents[1] / "ontology" / "dimensoes.yml"
CONFIANCAS = {"verbatim", "parafraseado", "inferido", "lacuna"}
CLIENTES_VALIDOS = {"PF", "PJ", "PF e PJ"}
CAMPOS_DA_QUEBRA = ("id", "data", "afeta", "descricao", "antes", "depois", "consequencia", "confianca", "fonte")


def carregar() -> dict:
    return yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))


def checar_estrutura(dados: dict) -> list[str]:
    """PT: coerência interna do arquivo / EN: internal consistency"""
    erros = []
    dimensoes = dados["dimensoes"] + dados.get("dimensoes_removidas_na_v2", [])

    for campo in ("id", "coluna"):
        repetidos = [v for v, n in Counter(d.get(campo) for d in dimensoes).items() if n > 1]
        erros += [f"{campo} repetido: {v}" for v in repetidos]

    for d in dimensoes:
        if not d.get("definition"):
            erros.append(f"{d.get('id')}: sem definição")
        if not d.get("fonte"):
            erros.append(f"{d.get('id')}: sem fonte")
        if d.get("confianca") not in CONFIANCAS:
            erros.append(f"{d.get('id')}: confianca inválida '{d.get('confianca')}'")

        rotulos = [v["rotulo_no_dado"] for v in d.get("valores", [])]
        repetidos = [r for r, n in Counter(rotulos).items() if n > 1]
        erros += [f"{d['id']}: valor repetido '{r}'" for r in repetidos]
        for v in d.get("valores", []):
            if "aplica_a" in v and v["aplica_a"] not in CLIENTES_VALIDOS:
                erros.append(f"{d['id']}: aplica_a inválido '{v['aplica_a']}' em '{v['rotulo_no_dado']}'")

    enumeradas = [d["id"] for d in dados["dimensoes"] if d.get("valores")]
    print(f"  1. estrutura: {len(dimensoes)} dimensões, {len(enumeradas)} com valores enumerados, {len(erros)} problemas")
    return erros + checar_quebras(dados)


def checar_quebras(dados: dict) -> list[str]:
    """
    PT: Confere a lista de quebras da série. A checagem que mais importa é a da
        data: ela precisa ser o último dia do mês, porque a dim_tempo junta
        pela igualdade com data_base, e uma quebra datada no dia 1 nunca
        casaria, sem erro nenhum.
    EN: Checks the series-break list. The check that matters most is the date:
        it must be the last day of the month, because dim_tempo joins on
        equality with data_base, and a break dated on the 1st would silently
        never match.
    """
    erros = []
    data_base = next((d for d in dados["dimensoes"] if d.get("coluna") == "data_base"), {})
    quebras = data_base.get("quebras", [])

    repetidos = [v for v, n in Counter(q.get("id") for q in quebras).items() if n > 1]
    erros += [f"quebra com id repetido: {v}" for v in repetidos]

    for q in quebras:
        faltando = [c for c in CAMPOS_DA_QUEBRA if not q.get(c)]
        if faltando:
            erros.append(f"quebra {q.get('id')}: campos vazios {faltando}")
        if q.get("confianca") not in CONFIANCAS:
            erros.append(f"quebra {q.get('id')}: confianca inválida '{q.get('confianca')}'")
        try:
            dia = date.fromisoformat(str(q.get("data")))
        except ValueError:
            erros.append(f"quebra {q.get('id')}: data inválida '{q.get('data')}'")
            continue
        ultimo = calendar.monthrange(dia.year, dia.month)[1]
        if dia.day != ultimo:
            erros.append(f"quebra {q.get('id')}: {dia} não é o último dia do mês, e nunca casaria com data_base")

    print(f"     quebras da série: {len(quebras)}, {len(erros)} problemas")
    return erros


def valores_do_dado(coluna: str) -> dict[str, str]:
    """
    PT: Para cada valor distinto da coluna no bronze V2, os tipos de cliente em
        que ele aparece, no mesmo formato do campo aplica_a.
    EN: For each distinct value in the V2 bronze column, the client types it
        appears with, in the same format as the aplica_a field.
    """
    from ingestion.databricks import cliente, executar_sql, warehouse
    from ingestion.fontes import CATALOGO, SCHEMA

    w = cliente()
    sql = f"""
        SELECT trim({coluna}), concat_ws(' e ', sort_array(collect_set(trim(cliente))))
        FROM {CATALOGO}.{SCHEMA}.bronze_scr_v2
        GROUP BY 1"""
    return {valor: clientes for valor, clientes in executar_sql(w, warehouse(w), sql)}


def checar_dado(dados: dict) -> list[str]:
    """PT: ontologia e dado se cobrem / EN: ontology and data cover each other"""
    erros = []
    for d in dados["dimensoes"]:
        if not d.get("valores"):
            continue
        na_ontologia = {v["rotulo_no_dado"]: v.get("aplica_a") for v in d["valores"]}
        no_dado = valores_do_dado(d["coluna"])

        faltando = sorted(set(no_dado) - set(na_ontologia))
        sobrando = sorted(set(na_ontologia) - set(no_dado))
        erros += [f"{d['coluna']}: valor no dado sem conceito: {v!r}" for v in faltando]
        erros += [f"{d['coluna']}: conceito sem ocorrência no dado: {v!r}" for v in sobrando]

        divergentes = [
            f"{d['coluna']}: {v!r} declara aplica_a '{na_ontologia[v]}', o dado mostra '{no_dado[v]}'"
            for v in sorted(set(na_ontologia) & set(no_dado))
            if na_ontologia[v] != no_dado[v]
        ]
        erros += divergentes
        print(f"  {d['coluna']}: {len(no_dado)} valores no dado, {len(na_ontologia)} na ontologia, "
              f"{len(faltando) + len(sobrando)} sem par, {len(divergentes)} com aplica_a divergente")
    return erros


def main() -> None:
    so_estrutura = "--estrutura" in sys.argv[1:]
    dados = carregar()

    erros = checar_estrutura(dados)
    if not so_estrutura:
        print("  2. dado:")
        erros += checar_dado(dados)

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    if so_estrutura:
        print("\nEstrutura da ontologia de dimensões está coerente / dimension ontology structure is coherent.")
    else:
        print("\nOntologia de dimensões confere com o dado / dimension ontology matches the data.")


if __name__ == "__main__":
    main()
