"""
PT: Das execuções corrigidas à contagem do experimento (#50, ADR 0031): por
    modelo, condição e pergunta, as situações das 5 execuções e quantas
    acertaram, de 0 a 5, e os erros por motivo. É a entrada da
    experimento.estatistica.analisar, e fica congelada junto dela antes da
    primeira execução.

EN: From graded runs to the experiment's counts: per model, condition and
    question, the 5 run situations, how many were right (0–5) and the
    error reasons. Input to experimento.estatistica.analisar, frozen with
    it before the first run.
"""

from __future__ import annotations

from collections import Counter

from assistente.parametros import CONDICOES
from correcao.acerto import motivo_do_erro


def contar(corrigidas: list[dict], modelo: str, ids: list[str]) -> tuple[dict, dict, dict]:
    """
    PT: Para um modelo, a partir das execuções corrigidas com a condição
        (correcao.acerto.corrigir_todas com com_condicao): as situações das
        execuções em ordem de seed e o número de certas, por condição e
        pergunta, e os erros por motivo em cada condição.
    EN: One model's run situations (by seed), right counts per condition
        and question, and error reasons per condition.
    """
    situacoes = {c: {i: [] for i in ids} for c in CONDICOES}
    erros = {c: Counter() for c in CONDICOES}
    for c in sorted(corrigidas, key=lambda c: c["seed"]):
        if c["candidato"] != modelo:
            continue
        situacoes[c["condicao"]][c["pergunta"]].append(c["situacao"])
        if motivo := motivo_do_erro(c):
            erros[c["condicao"]][motivo] += 1
    certas = {c: {i: s.count("certo") for i, s in por.items()} for c, por in situacoes.items()}
    return situacoes, certas, {c: dict(sorted(e.items())) for c, e in erros.items()}
