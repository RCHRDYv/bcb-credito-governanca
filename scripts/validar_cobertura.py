"""
PT: Valida a matriz de cobertura da camada gold (evaluation/cobertura.yml),
    sem precisar de credencial. Roda no CI.

    É o critério de pronto da issue #15 transformado em verificação: cada
    pergunta do experimento e cada tela do dashboard precisa apontar os
    modelos que a respondem, ou a issue que ainda a bloqueia.

    O que é conferido:

    1. **Completude.** Os 41 ids do conjunto v2 das perguntas estão na matriz,
       sem faltar e sem sobrar, e as quatro telas também.
    2. **Existência.** Todo modelo citado existe como arquivo .sql em
       dbt/models/. Um modelo renomeado ou apagado quebra aqui, e não no dia
       de escrever o gabarito.
    3. **A regra do experimento.** Perguntas citam só o esquema estrela
       (dim_* e fct_*), porque é o que a IA consulta nas duas condições (ADR
       0007). Uma pergunta que só um mart de apresentação respondesse seria
       impossível por construção para a IA.
    4. **Bloqueio rastreável.** Toda entrada tem modelos ou depende de issue,
       e toda dependência cita uma issue no formato #número.

EN: Validates the gold layer's coverage matrix with no credential needed; runs
    in CI. It turns issue #15's definition of done into a check: all 41 v2
    question ids and the four screens are present; every cited model exists as
    a .sql file; questions cite only the star schema, which is what the AI
    queries (ADR 0007); and every entry has models or a traceable blocking
    issue.

Uso / Usage:
    uv run python -m scripts.validar_cobertura
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from scripts.validar_perguntas import V2, perguntas

RAIZ = Path(__file__).resolve().parents[1]
COBERTURA = RAIZ / "evaluation" / "cobertura.yml"
MODELOS = RAIZ / "dbt" / "models"
TELAS = ("tela_1", "tela_2", "tela_3", "tela_4")
ISSUE = re.compile(r"^#\d+$")

# PT: prefixos do esquema estrela, o que a IA consulta no experimento.
# EN: star schema prefixes, what the AI queries in the experiment.
ESQUEMA_ESTRELA = ("dim_", "fct_")


def modelos_existentes() -> set[str]:
    """PT: nomes de todos os modelos dbt / EN: names of every dbt model"""
    return {p.stem for p in MODELOS.rglob("*.sql")}


def checar_entrada(nome: str, entrada: dict, existentes: set[str], so_estrela: bool) -> list[str]:
    """
    PT: Confere uma pergunta ou uma tela.
    EN: Checks one question or one screen.
    """
    erros = []
    modelos = entrada.get("modelos", [])
    dependencias = entrada.get("depende_de", [])

    if not modelos and not dependencias:
        erros.append(f"{nome}: sem modelos e sem issue de bloqueio")

    for modelo in modelos:
        if modelo not in existentes:
            erros.append(f"{nome}: modelo inexistente '{modelo}'")
        if so_estrela and not modelo.startswith(ESQUEMA_ESTRELA):
            erros.append(f"{nome}: pergunta cita '{modelo}', fora do esquema estrela que a IA consulta")

    erros += [f"{nome}: dependência fora do formato #número: '{d}'" for d in dependencias if not ISSUE.match(str(d))]
    return erros


def situacao(entrada: dict) -> str:
    """PT: respondível, parcial ou bloqueada / EN: answerable, partial or blocked"""
    if entrada.get("modelos") and not entrada.get("depende_de"):
        return "respondível"
    if entrada.get("modelos"):
        return "parcial"
    return "bloqueada"


def main() -> None:
    matriz = yaml.safe_load(COBERTURA.read_text(encoding="utf-8"))
    _, por_id = perguntas(V2)
    existentes = modelos_existentes()
    erros: list[str] = []

    # -------------------------------------------------------------------------
    # PT: Completude
    # EN: Completeness
    # -------------------------------------------------------------------------
    na_matriz = set(matriz["perguntas"])
    erros += [f"pergunta sem cobertura: {i}" for i in sorted(set(por_id) - na_matriz)]
    erros += [f"id na matriz que não existe no conjunto v2: {i}" for i in sorted(na_matriz - set(por_id))]
    erros += [f"tela sem cobertura: {t}" for t in TELAS if t not in matriz["telas"]]

    # -------------------------------------------------------------------------
    # PT: Cada entrada
    # EN: Each entry
    # -------------------------------------------------------------------------
    for id_, entrada in matriz["perguntas"].items():
        erros += checar_entrada(id_, entrada, existentes, so_estrela=True)
    for tela, entrada in matriz["telas"].items():
        erros += checar_entrada(tela, entrada, existentes, so_estrela=False)

    # -------------------------------------------------------------------------
    # PT: Resumo
    # EN: Summary
    # -------------------------------------------------------------------------
    for grupo in ("perguntas", "telas"):
        contagem: dict[str, list[str]] = {}
        for nome, entrada in matriz[grupo].items():
            contagem.setdefault(situacao(entrada), []).append(nome)
        partes = [f"{len(v)} {k}" for k, v in sorted(contagem.items())]
        print(f"  {grupo}: {len(matriz[grupo])}, " + ", ".join(partes))
        for chave in ("parcial", "bloqueada"):
            if chave in contagem:
                print(f"     {chave}: {', '.join(contagem[chave])}")

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nCobertura completa e coerente / coverage complete and consistent.")


if __name__ == "__main__":
    main()
