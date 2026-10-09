"""
PT: O acerto de uma execução e de uma pergunta (evaluation/hipoteses.yml,
    execucao.acerto_binario e comparacao.acerto_por_tipo). Junta a parte por
    script (correcao.corretor) e o julgamento às cegas (correcao.as_cegas):

    - a execução está certa se o script diz certo, ou se diz pendente e todo
      aspecto a julgar foi julgado sim; errada se o script diz errado, ou se
      algum aspecto foi julgado não; pendente enquanto falta julgamento;
    - a pergunta acerta se 3 ou mais das 5 execuções acertam, e erra quando
      as certas já não podem chegar a 3.

    Uma pergunta já decidida dispensa o julgamento das execuções que
    faltam, e o resultado é o mesmo de julgar tudo (decisão de 2026-10-09).

EN: Run and question correctness, combining the script grader and blind
    judgments. A question is right when 3 or more of its 5 runs are right,
    and wrong once the right ones can no longer reach 3; a decided question
    needs no further judgment.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from correcao.corretor import Gabarito, carregar_gabarito, corrigir
from ingestion.fontes import RAIZ

PASTA_DA_SELECAO = RAIZ / "data" / "selecao"
EXECUCOES_POR_PERGUNTA = 5
MAIORIA = 3


def acerto_da_execucao(correcao: dict, julgamento: dict | None) -> str:
    """PT: certo, errado ou pendente / EN: right, wrong or pending"""
    if correcao["situacao"] != "pendente":
        return correcao["situacao"]
    julgamento = julgamento or {}
    if any(julgamento.get(a) is False for a in correcao["julgar"]):
        return "errado"
    if all(julgamento.get(a) is True for a in correcao["julgar"]):
        return "certo"
    return "pendente"


def acerto_da_pergunta(situacoes: list[str], total: int = EXECUCOES_POR_PERGUNTA) -> str:
    """
    PT: certo com 3 certas, errado quando as certas já não chegam a 3 (as
        que faltam rodar contam como possíveis), pendente no resto.
    EN: right at 3 right runs, wrong once 3 is out of reach, else pending.
    """
    certas = situacoes.count("certo")
    possiveis = certas + situacoes.count("pendente") + (total - len(situacoes))
    if certas >= MAIORIA:
        return "certo"
    if possiveis < MAIORIA:
        return "errado"
    return "pendente"


def id_do_item(candidato: str, pergunta: str, seed: int) -> str:
    """
    PT: Identificador opaco de uma execução, para o julgamento às cegas não
        revelar o candidato.
    EN: Opaque run id, so blind grading does not reveal the candidate.
    """
    return hashlib.sha256(f"{candidato}|{pergunta}|{seed}".encode("utf-8")).hexdigest()[:16]


def ler_execucoes(pasta: Path = PASTA_DA_SELECAO) -> list[dict]:
    """PT: os registros gravados pela seleção / EN: the selection's run records"""
    return [json.loads(a.read_text(encoding="utf-8")) for a in sorted((pasta / "execucoes").glob("*/Q*_seed*.json"))]


def ler_julgamentos(pasta: Path = PASTA_DA_SELECAO) -> dict[str, dict]:
    arquivo = pasta / "julgamentos.json"
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}


def corrigir_todas(execucoes: list[dict], julgamentos: dict[str, dict],
                   gabarito: Gabarito | None = None) -> list[dict]:
    """
    PT: Cada execução com a correção do script, o id do item e a situação
        depois dos julgamentos que já existem.
    EN: Each run with its script grading, item id and current situation.
    """
    g = gabarito or carregar_gabarito()
    corrigidas = []
    for r in execucoes:
        item = id_do_item(r["candidato"], r["id_pergunta"], r["seed"])
        correcao = corrigir(r["id_pergunta"], r, g)
        corrigidas.append({
            "candidato": r["candidato"], "pergunta": r["id_pergunta"], "seed": r["seed"], "item": item,
            "correcao": correcao, "julgamento": julgamentos.get(item),
            "situacao": acerto_da_execucao(correcao, julgamentos.get(item)),
        })
    return corrigidas


def por_pergunta(corrigidas: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """PT: as execuções agrupadas por candidato e pergunta / EN: grouped runs"""
    grupos: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in corrigidas:
        grupos[(c["candidato"], c["pergunta"])].append(c)
    return {k: sorted(v, key=lambda c: c["seed"]) for k, v in grupos.items()}


def a_julgar(corrigidas: list[dict]) -> list[dict]:
    """
    PT: As execuções pendentes de perguntas ainda não decididas: só o que
        pode mudar o acerto.
    EN: Pending runs of undecided questions: only what can change the result.
    """
    return [
        c
        for grupo in por_pergunta(corrigidas).values()
        if acerto_da_pergunta([c["situacao"] for c in grupo]) == "pendente"
        for c in grupo if c["situacao"] == "pendente"
    ]
