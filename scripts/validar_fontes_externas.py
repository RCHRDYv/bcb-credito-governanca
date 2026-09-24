"""
PT: Valida a estrutura de ontology/fontes_externas.yml, sem precisar de
    credencial. Roda no CI.

    O que é conferido, no mesmo padrão de scripts/validar_dimensoes.py:
    1. ids únicos entre fontes, conceitos e avisos;
    2. definição (ou descrição, nos avisos), fonte e confiança em tudo, com a
       confiança num dos quatro níveis do ADR 0002;
    3. toda fonte com publicador, endereço, periodicidade e data de
       referência, que é o que permite a quem lê saber de quando é o
       denominador.

EN: Validates the structure of ontology/fontes_externas.yml with no
    credential; runs in CI. Checks unique ids, definition, source and a valid
    confidence level everywhere, and that every source declares publisher,
    address, periodicity and reference date.

Uso / Usage:
    uv run python -m scripts.validar_fontes_externas
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
ONTOLOGIA = RAIZ / "ontology" / "fontes_externas.yml"

CONFIANCAS = {"verbatim", "parafraseado", "inferido", "lacuna"}
CAMPOS_DA_FONTE = ("publicador", "endereco", "periodicidade", "data_de_referencia")


def checar(dados: dict) -> list[str]:
    """PT: coerência interna do arquivo / EN: internal consistency"""
    erros = []
    grupos = {nome: dados.get(nome, []) for nome in ("fontes", "conceitos", "avisos")}

    ids = [item.get("id") for itens in grupos.values() for item in itens]
    erros += [f"id repetido: {i}" for i, n in Counter(ids).items() if n > 1]

    for nome, itens in grupos.items():
        if not itens:
            erros.append(f"{nome}: lista vazia")
        for item in itens:
            ident = f"{nome}.{item.get('id')}"
            texto = item.get("definition") or item.get("descricao") or item.get("prefLabel_pt")
            if not texto:
                erros.append(f"{ident}: sem definição")
            if not item.get("fonte"):
                erros.append(f"{ident}: sem fonte")
            if item.get("confianca") not in CONFIANCAS:
                erros.append(f"{ident}: confianca inválida '{item.get('confianca')}'")

    # PT: Códigos enumerados viram chave de junção no seed: repetido ou sem
    #     rótulo, a junção duplica ou perde linhas.
    # EN: Enumerated codes become join keys in the seed.
    for conceito in grupos["conceitos"]:
        codigos = [str(v.get("codigo", "")) for v in conceito.get("valores", [])]
        erros += [f"conceitos.{conceito['id']}: código repetido '{c}'" for c, n in Counter(codigos).items() if n > 1]
        erros += [f"conceitos.{conceito['id']}: valor sem código ou rótulo"
                  for v in conceito.get("valores", []) if not v.get("codigo") or not v.get("rotulo")]

    for fonte in grupos["fontes"]:
        erros += [f"fontes.{fonte.get('id')}: sem {c}" for c in CAMPOS_DA_FONTE if not fonte.get(c)]

    contagem = ", ".join(f"{len(v)} {k}" for k, v in grupos.items())
    print(f"  estrutura: {contagem}, {len(erros)} problemas")
    return erros


def main() -> None:
    erros = checar(yaml.safe_load(ONTOLOGIA.read_text(encoding="utf-8")))
    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nOntologia das fontes externas coerente / external sources ontology is coherent.")


if __name__ == "__main__":
    main()
