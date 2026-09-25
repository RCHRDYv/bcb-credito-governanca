"""
PT: Valida os três conjuntos de perguntas do experimento, sem precisar de
    credencial. Roda no CI.

    O que é conferido:

    1. Estrutura de cada arquivo: id único, enunciado em português e em
       inglês, dependência semântica com valor permitido, tipo de acerto com
       valor permitido, e total declarado igual ao total real.
    2. **Integridade da preservação:** o conjunto v2 precisa conter os 30 ids
       originais com o enunciado idêntico, palavra por palavra. É o que
       sustenta a afirmação de que nenhuma pergunta foi reescrita depois dos
       achados. Correção de nota é permitida, e só no campo errata.
    3. **Passagem do v2 para o v3:** as mesmas 41 perguntas, com o mesmo tipo
       de acerto, a mesma dependência, a mesma nota e a mesma errata. Um
       enunciado só muda com o campo alteracao_v3, e esse campo precisa citar
       o enunciado do v2, palavra por palavra. Nota nova só no campo
       errata_v3.

EN: Validates both question sets with no credential needed; runs in CI.
    Checks each file's structure (unique ids, both languages, allowed values,
    declared total) and, above all, the preservation integrity: the v2 set
    must carry the 30 original ids with byte-identical wording. That is what
    backs the claim that no question was rewritten after the findings. Note
    corrections are allowed, and only in the errata field. The v3 set keeps
    the 41 v2 questions; a wording may change only with an alteracao_v3 field
    quoting the v2 wording verbatim, and new notes go only in errata_v3.

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
V3 = PASTA / "questions_v3.yml"

# PT: o conjunto que vale para o experimento, lido pelos outros validadores e
#     pelo gerador do gabarito. Um conjunto novo muda só esta linha.
# EN: the set that counts for the experiment, read by the other validators
#     and the answer key generator. A new set changes only this line.
VIGENTE = V3

# PT: campos que o v3 herda do v2 sem mudança.
# EN: fields v3 inherits from v2 unchanged.
CAMPOS_HERDADOS = ("tipo_de_acerto", "dependencia_semantica", "nota", "errata")
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


def checar_v3(v2: dict[str, dict], v3: dict[str, dict]) -> list[str]:
    """
    PT: O v3 só pode mudar a janela de um enunciado, declarando a mudança e
        citando o enunciado do v2, e acrescentar errata nova no errata_v3.
    EN: v3 may only change a wording's window, declaring it and quoting the
        v2 wording, and add new notes in errata_v3.
    """
    erros = [f"pergunta do v2 ausente do v3: {i}" for i in sorted(set(v2) - set(v3))]
    erros += [f"pergunta nova no v3, o que esta versão não prevê: {i}" for i in sorted(set(v3) - set(v2))]
    alteradas = []
    for id_ in sorted(set(v2) & set(v3)):
        antes, depois = v2[id_], v3[id_]
        for campo in CAMPOS_HERDADOS:
            if antes.get(campo) != depois.get(campo):
                erros.append(f"{id_}: campo {campo} mudou do v2 para o v3")
        mudou = antes["pergunta"] != depois["pergunta"] or antes["question"] != depois["question"]
        alteracao = " ".join(str(depois.get("alteracao_v3", "")).split())
        if mudou:
            alteradas.append(id_)
            if not alteracao:
                erros.append(f"{id_}: enunciado mudou no v3 sem o campo alteracao_v3")
            elif " ".join(antes["pergunta"].split()) not in alteracao:
                erros.append(f"{id_}: alteracao_v3 não cita o enunciado do v2 palavra por palavra")
        elif alteracao:
            erros.append(f"{id_}: alteracao_v3 declarada, mas o enunciado não mudou")

    com_errata = sorted(i for i, p in v3.items() if p.get("errata_v3"))
    print(f"  v2 para v3: {len(v3)} perguntas, {len(alteradas)} com janela alterada {alteradas}, "
          f"{len(com_errata)} com errata nova {com_errata}")
    return erros


def main() -> None:
    meta_original, original = perguntas(ORIGINAL)
    meta_v2, v2 = perguntas(V2)
    meta_v3, v3 = perguntas(V3)

    erros = checar_arquivo("questions.yml", meta_original, original, meta_original["total"])
    erros += checar_arquivo("questions_v2.yml", meta_v2, v2, meta_v2["total"])
    erros += checar_preservacao(original, v2)
    erros += checar_arquivo("questions_v3.yml", meta_v3, v3, meta_v3["total"])
    erros += checar_v3(v2, v3)

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nPerguntas coerentes e pré-registro preservado / questions coherent, pre-registration preserved.")


if __name__ == "__main__":
    main()
