"""
PT: Valida ontology/modalidades.yml em duas camadas.

    1. Estrutura: ids únicos, hierarquia coerente (toda submodalidade aponta
       para uma modalidade existente, e o código começa pelo código dela),
       confiança com valor permitido, definição presente sempre que a
       confiança não for "lacuna", e fonte em todo conceito.
    2. Dado: todo par (modalidade, submodalidade) do bronze V2 casa com
       exatamente um conceito pelo rótulo exato, e todo conceito aparece no
       dado. É o teste que impede a ontologia de descrever um dado que não
       existe, ou de deixar de fora um que existe.

    Sai com código 1 se qualquer checagem falhar.

EN: Validates ontology/modalidades.yml in two layers: structure (unique
    ids, coherent hierarchy, allowed confidence values, definitions and
    sources present) and data (every (modality, sub-modality) pair in the V2
    bronze matches exactly one concept by exact label, and every concept
    appears in the data). Exits with code 1 on any failure.

Uso / Usage:
    uv run python -m scripts.validar_modalidades
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import CATALOGO, SCHEMA

ARQUIVO = Path(__file__).resolve().parents[1] / "ontology" / "modalidades.yml"
CONFIANCAS = {"verbatim", "parafraseado", "inferido", "lacuna"}
OBRIGATORIOS = ("id", "notation", "tipo", "prefLabel_pt", "rotulo_no_dado", "confianca", "fonte")


# -----------------------------------------------------------------------------
# PT: Camada 1, estrutura
# EN: Layer 1, structure
# -----------------------------------------------------------------------------

def checar_estrutura(conceitos: list[dict]) -> list[str]:
    """PT: coerência interna do arquivo / EN: internal consistency of the file"""
    erros = []
    por_id = {c.get("id"): c for c in conceitos}

    for campo in ("id", "notation"):
        repetidos = [v for v, n in Counter(c.get(campo) for c in conceitos).items() if n > 1]
        erros += [f"{campo} repetido: {v}" for v in repetidos]

    for c in conceitos:
        faltando = [campo for campo in OBRIGATORIOS if not c.get(campo)]
        if faltando:
            erros.append(f"{c.get('id')}: faltam {faltando}")
        if c.get("confianca") not in CONFIANCAS:
            erros.append(f"{c.get('id')}: confianca inválida '{c.get('confianca')}'")
        if c.get("confianca") != "lacuna" and not c.get("definition"):
            erros.append(f"{c.get('id')}: sem definição, mas confianca não é lacuna")

        if c.get("tipo") == "submodalidade":
            pai = por_id.get(c.get("broader"))
            if not pai or pai.get("tipo") != "modalidade":
                erros.append(f"{c['id']}: broader '{c.get('broader')}' não é uma modalidade existente")
            elif not str(c["notation"]).startswith(str(pai["notation"])):
                erros.append(f"{c['id']}: código {c['notation']} não começa pelo da modalidade {pai['notation']}")
        elif c.get("tipo") != "modalidade":
            erros.append(f"{c.get('id')}: tipo inválido '{c.get('tipo')}'")

    return erros


# -----------------------------------------------------------------------------
# PT: Camada 2, dado
# EN: Layer 2, data
# -----------------------------------------------------------------------------

def pares_da_ontologia(conceitos: list[dict]) -> tuple[dict[tuple[str, str], str], list[str]]:
    """
    PT: Monta a chave de junção (rótulo da modalidade, rótulo da
        submodalidade) de cada submodalidade. A chave precisa ser única, ou
        o join com o dado duplicaria linhas.
    EN: Builds the join key for each sub-modality. The key must be unique,
        otherwise the join with the data would duplicate rows.
    """
    rotulo_mod = {c["id"]: c["rotulo_no_dado"] for c in conceitos if c.get("tipo") == "modalidade"}
    pares, erros = {}, []
    for c in conceitos:
        if c.get("tipo") != "submodalidade":
            continue
        chave = (rotulo_mod.get(c.get("broader"), "?"), c["rotulo_no_dado"])
        if chave in pares:
            erros.append(f"chave de junção repetida {chave}: {pares[chave]} e {c['id']}")
        pares[chave] = c["id"]
    return pares, erros


def pares_do_dado() -> dict[tuple[str, str], int]:
    """PT: pares distintos no bronze V2, com linhas / EN: distinct pairs with row counts"""
    w = cliente()
    sql = f"""
        SELECT trim(modalidade), trim(submodalidade), count(*)
        FROM {CATALOGO}.{SCHEMA}.bronze_scr_v2
        GROUP BY 1, 2"""
    return {(m, s): int(n) for m, s, n in executar_sql(w, warehouse(w), sql)}


def checar_dado(conceitos: list[dict]) -> list[str]:
    """PT: ontologia e dado se cobrem mutuamente / EN: ontology and data cover each other"""
    pares, erros = pares_da_ontologia(conceitos)
    dado = pares_do_dado()

    sem_conceito = sorted(set(dado) - set(pares))
    sem_dado = sorted(set(pares) - set(dado))
    erros += [f"no dado sem conceito: {p!r} ({dado[p]:,} linhas)" for p in sem_conceito]
    erros += [f"conceito sem ocorrência no dado: {pares[p]} {p!r}" for p in sem_dado]

    cobertas = sum(n for p, n in dado.items() if p in pares)
    print(f"  dado: {len(dado)} pares distintos, {sum(dado.values()):,} linhas")
    print(f"  ontologia: {len(pares)} submodalidades")
    print(f"  linhas cobertas pela ontologia: {cobertas:,} de {sum(dado.values()):,}")
    return erros


def main() -> None:
    dados = yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))
    conceitos = dados["conceitos"]
    mods = sum(c.get("tipo") == "modalidade" for c in conceitos)
    lacunas = [c["id"] for c in conceitos if c.get("confianca") == "lacuna"]
    print(f"  {len(conceitos)} conceitos: {mods} modalidades, {len(conceitos) - mods} submodalidades")
    print(f"  confianca lacuna: {lacunas}")

    erros = checar_estrutura(conceitos)
    print(f"  1. estrutura: {len(erros)} problemas")
    erros_dado = checar_dado(conceitos)
    print(f"  2. dado: {len(erros_dado)} problemas")
    erros += erros_dado

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nOntologia de modalidades confere com o dado / modality ontology matches the data.")


if __name__ == "__main__":
    main()
