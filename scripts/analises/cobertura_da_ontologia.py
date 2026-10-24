"""
PT: A cobertura da ontologia recuperada por pergunta (#120, ADR 0033), para
    escolher o k da V5. Para cada pergunta do conjunto de desenvolvimento,
    os ids da ontologia do campo fonte do gabarito
    (evaluation/desenvolvimento/gabarito.yml) são o alvo, e a busca do
    rag/ontologia.py traz os k itens mais próximos. Para k de 1 a 30, mostra:

    - a cobertura média: a parcela dos ids do fonte que a busca trouxe, em
      média por pergunta;
    - as perguntas cobertas por inteiro, com todos os ids do fonte;
    - os tokens estimados do maior bloco da ontologia, pela mesma conta de
      caracteres do assistente (assistente/cliente.estimar_tokens).

    Só o conjunto de desenvolvimento entra. As 41 perguntas do teste e o
    gabarito delas ficam de fora, para o k não se ajustar a elas. Fonte que
    não é item da ontologia (o esquema estrela, por exemplo) não conta, e a
    pergunta sem nenhum item fica fora da média.

EN: Coverage of the per-question ontology search on the development set,
    to choose V5's k: for k from 1 to 30, the mean share of the answer
    key's ontology ids retrieved, fully covered questions and the largest
    block's estimated tokens. Test questions stay out.

Uso / Usage:
    uv run --group rag python -m scripts.analises.cobertura_da_ontologia
"""

from __future__ import annotations

import math

import yaml

from assistente import ontologia, parametros
from experimento.desenvolvimento import GABARITO
from experimento.desenvolvimento import perguntas as perguntas_de_desenvolvimento
from rag.ontologia import buscar_itens

MAIOR_K = 30


def alvos() -> dict[str, set[str]]:
    """
    PT: Os ids da ontologia do fonte de cada pergunta, sem as perguntas que
        não citam nenhum item.
    EN: Each question's ontology ids from the answer key's fonte.
    """
    conhecidos = {id_ for id_, _, _ in ontologia.itens()}
    gabarito = yaml.safe_load(GABARITO.read_text(encoding="utf-8"))["perguntas"]
    saida = {i: {f for f in p.get("fonte") or [] if f in conhecidos} for i, p in gabarito.items()}
    return {i: ids for i, ids in saida.items() if ids}


def main() -> None:
    _, por_id = perguntas_de_desenvolvimento()
    alvo = alvos()
    caracteres_por_token = parametros.carregar().caracteres_por_token_na_estimativa
    ordem = {i: [r["id"] for r in buscar_itens(por_id[i]["pergunta"], MAIOR_K)] for i in alvo}

    print(f"  {len(alvo)} de {len(por_id)} perguntas citam itens da ontologia no fonte "
          f"({sum(map(len, alvo.values()))} ids)\n")
    print("   k | cobertura média | cobertas por inteiro | tokens do maior bloco")
    print("  ---|-----------------|----------------------|----------------------")
    for k in range(1, MAIOR_K + 1):
        parcelas = [len(alvo[i] & set(ordem[i][:k])) / len(alvo[i]) for i in alvo]
        inteiras = sum(p == 1 for p in parcelas)
        tokens = max(math.ceil(len(ontologia.bloco(ids=ordem[i][:k])) / caracteres_por_token) for i in alvo)
        print(f"  {k:>2} | {100 * sum(parcelas) / len(parcelas):>14.1f}% | {inteiras:>11} de {len(alvo):<8} | "
              f"{tokens:>21}")
    inteira = math.ceil(len(ontologia.bloco()) / caracteres_por_token)
    print(f"\n  A ontologia inteira, como na V4: {len(ontologia.itens())} itens, uns {inteira} tokens estimados.")


if __name__ == "__main__":
    main()
