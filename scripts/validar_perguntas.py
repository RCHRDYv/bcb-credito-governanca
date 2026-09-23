"""
PT: Valida os dois conjuntos de perguntas do experimento, sem precisar de
    credencial. Roda no CI.

    O que é conferido:

    1. Estrutura de cada arquivo: id único, enunciado em português e em
       inglês, dependência semântica com valor permitido, tipo de acerto com
       valor permitido, e total declarado igual ao total real.
    2. **Integridade da preservação:** o conjunto v2 precisa conter os 30 ids
       originais com o enunciado idêntico, palavra por palavra. É o que
       sustenta a afirmação de que nenhuma pergunta foi reescrita depois dos
       achados. Correção de nota é permitida, e só no campo errata.

EN: Validates both question sets with no credential needed; runs in CI.
    Checks each file's structure (unique ids, both languages, allowed values,
    declared total) and, above all, the preservation integrity: the v2 set
    must carry the 30 original ids with byte-identical wording. That is what
    backs the claim that no question was rewritten after the findings. Note
    corrections are allowed, and only in the errata field.

Uso / Usage:
    uv run python -m scripts.validar_perguntas
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PASTA = Path(__file__).resolve().parents[1] / "evaluation"
ORIGINAL = PASTA / "questions.yml"
V2 = PASTA / "questions_v2.yml"
DEPENDENCIAS = {"baixa", "media", "alta", "maxima"}
TIPOS_DE_ACERTO = {"valor", "valor_com_ressalva", "abstencao"}


def perguntas(arquivo: Path) -> tuple[dict, dict[str, dict]]:
    """PT: metadados e perguntas por id / EN: metadata and questions by id"""
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    por_id = {p["id"]: p for bloco in dados["blocos"] for p in bloco["perguntas"]}
    return dados["metadata"], por_id


def checar_arquivo(nome: str, metadados: dict, por_id: dict[str, dict], total_esperado: int) -> list[str]:
    erros = []
    if len(por_id) != total_esperado:
        erros.append(f"{nome}: {len(por_id)} perguntas, metadata declara {total_esperado}")
    for id_, p in por_id.items():
        if not p.get("pergunta") or not p.get("question"):
            erros.append(f"{nome} {id_}: falta enunciado em português ou em inglês")
        if p.get("dependencia_semantica") not in DEPENDENCIAS:
            erros.append(f"{nome} {id_}: dependencia_semantica inválida '{p.get('dependencia_semantica')}'")
        tipo = p.get("tipo_de_acerto")
        if tipo is not None and tipo not in TIPOS_DE_ACERTO:
            erros.append(f"{nome} {id_}: tipo_de_acerto inválido '{tipo}'")
    print(f"  {nome}: {len(por_id)} perguntas, {len(erros)} problemas")
    return erros


def checar_preservacao(original: dict[str, dict], v2: dict[str, dict]) -> list[str]:
    """PT: o v2 não pode reescrever enunciado / EN: v2 must not rewrite wording"""
    erros = []
    faltando = sorted(set(original) - set(v2))
    erros += [f"pergunta original ausente do v2: {i}" for i in faltando]
    for id_, p in original.items():
        if id_ in v2 and v2[id_]["pergunta"] != p["pergunta"]:
            erros.append(f"{id_}: enunciado alterado no v2, o que o pré-registro não permite")
        if id_ in v2 and v2[id_]["question"] != p["question"]:
            erros.append(f"{id_}: enunciado em inglês alterado no v2")

    novas = sorted(set(v2) - set(original))
    com_errata = sorted(i for i, p in v2.items() if p.get("errata"))
    print(f"  preservação: {len(original)} originais mantidos, {len(novas)} novas, {len(com_errata)} com errata")
    print(f"     novas: {novas}")
    print(f"     errata: {com_errata}")
    return erros


def main() -> None:
    meta_original, original = perguntas(ORIGINAL)
    meta_v2, v2 = perguntas(V2)

    erros = checar_arquivo("questions.yml", meta_original, original, meta_original["total"])
    erros += checar_arquivo("questions_v2.yml", meta_v2, v2, meta_v2["total"])
    erros += checar_preservacao(original, v2)

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nPerguntas coerentes e pré-registro preservado / questions coherent, pre-registration preserved.")


if __name__ == "__main__":
    main()
