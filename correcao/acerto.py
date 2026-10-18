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

    O experimento (#50) reaproveita o módulo com a condição na chave: o id
    opaco, o agrupamento e a pasta passam a levar a condição, e a fila de
    julgamento traz todas as pendentes, porque a contagem de 0 a 5 sai
    exata (decisão 1 de 2026-10-14, ADR 0031). Sem condição, tudo fica como
    na seleção.

EN: Run and question correctness, combining the script grader and blind
    judgments. A question is right when 3 or more of its 5 runs are right,
    and wrong once the right ones can no longer reach 3; a decided question
    needs no further judgment. The experiment (#50) adds the condition to
    ids, groups and folders, and judges every pending run; without a
    condition everything stays as in the selection.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from correcao.corretor import Gabarito, carregar_gabarito, corrigir
from ingestion.fontes import RAIZ

PASTA_DA_SELECAO = RAIZ / "data" / "selecao"
PASTA_DO_EXPERIMENTO = RAIZ / "data" / "experimento"
PADRAO_DA_SELECAO = "*/Q*_seed*.json"
PADRAO_DO_EXPERIMENTO = "*/*/Q*_seed*.json"
EXECUCOES_POR_PERGUNTA = 5
MAIORIA = 3


def acerto_da_execucao(correcao: dict, julgamento: dict | None) -> str:
    """PT: certo, errado ou pendente / EN: right, wrong or pending"""
    if correcao["situacao"] != "pendente":
        return correcao["situacao"]
    julgamento = julgamento or {}
    if not correcao["julgar"]:
        return "pendente"
    if any(julgamento.get(a) is False for a in correcao["julgar"]):
        return "errado"
    if all(julgamento.get(a) is True for a in correcao["julgar"]):
        return "certo"
    return "pendente"


def motivo_do_erro(c: dict) -> str:
    """
    PT: O motivo de uma execução corrigida errada: o do corretor por script,
        ou o aspecto reprovado na correção às cegas. Vazio se não está
        errada.
    EN: Why a graded run is wrong: the script reason or the rejected blind
        aspect; empty otherwise.
    """
    if c["correcao"]["situacao"] == "errado":
        return c["correcao"]["motivo"]
    negados = [a for a in c["correcao"]["julgar"] if (c["julgamento"] or {}).get(a) is False]
    return f"julgamento_{negados[0]}" if negados else ""


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


def id_do_item(candidato: str, pergunta: str, seed: int, condicao: str | None = None) -> str:
    """
    PT: Identificador opaco de uma execução, para o julgamento às cegas não
        revelar o candidato nem a condição. Sem condição, é o id da seleção,
        que não muda.
    EN: Opaque run id, so blind grading reveals neither candidate nor
        condition. Without a condition it is the selection's id, unchanged.
    """
    chave = f"{candidato}|{pergunta}|{seed}" if condicao is None else f"{candidato}|{condicao}|{pergunta}|{seed}"
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()[:16]


def ler_execucoes(pasta: Path = PASTA_DA_SELECAO, padrao: str = PADRAO_DA_SELECAO) -> list[dict]:
    """
    PT: Os registros gravados pela seleção, ou, com o padrão do experimento,
        os de data/experimento/execucoes/<modelo>/<condição>/.
    EN: The selection's run records, or the experiment's with its pattern.
    """
    return [json.loads(a.read_text(encoding="utf-8")) for a in sorted((pasta / "execucoes").glob(padrao))]


def execucoes_vigentes(execucoes: list[dict], candidatos: list[str], ids: list[str]) -> list[dict]:
    """
    PT: Só as execuções de candidatos do selecao.yml e de perguntas do
        conjunto vigente: um registro antigo não conta nem vai a julgamento.
    EN: Only runs of current candidates and current questions.
    """
    return [r for r in execucoes if r["candidato"] in candidatos and r["id_pergunta"] in ids]


def ler_julgamentos(pasta: Path = PASTA_DA_SELECAO) -> dict[str, dict]:
    arquivo = pasta / "julgamentos.json"
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}


def corrigir_todas(execucoes: list[dict], julgamentos: dict[str, dict],
                   gabarito: Gabarito | None = None, com_condicao: bool = False) -> list[dict]:
    """
    PT: Cada execução com a correção do script, o id do item e a situação
        depois dos julgamentos que já existem. Com com_condicao, a condição
        do registro entra no id e na saída (o experimento). Sem ela, a saída
        é a da seleção, mesmo que o registro traga a condição A.
    EN: Each run with its script grading, item id and current situation.
        com_condicao puts the record's condition in the id and the output.
    """
    g = gabarito or carregar_gabarito()
    corrigidas = []
    for r in execucoes:
        condicao = r["condicao"] if com_condicao else None
        item = id_do_item(r["candidato"], r["id_pergunta"], r["seed"], condicao)
        correcao = corrigir(r["id_pergunta"], r, g)
        corrigida = {
            "candidato": r["candidato"], "pergunta": r["id_pergunta"], "seed": r["seed"], "item": item,
            "correcao": correcao, "julgamento": julgamentos.get(item),
            "situacao": acerto_da_execucao(correcao, julgamentos.get(item)),
        }
        if com_condicao:
            corrigida["condicao"] = condicao
        corrigidas.append(corrigida)
    return corrigidas


def chave_da_pergunta(c: dict) -> tuple[str, ...]:
    """
    PT: candidato e pergunta, ou candidato, condição e pergunta no
        experimento / EN: candidate and question, plus the condition
    """
    return (c["candidato"], c["condicao"], c["pergunta"]) if "condicao" in c else (c["candidato"], c["pergunta"])


def por_pergunta(corrigidas: list[dict]) -> dict[tuple[str, ...], list[dict]]:
    """
    PT: as execuções agrupadas por candidato e pergunta (e pela condição,
        no experimento) / EN: runs grouped by candidate and question
    """
    grupos: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for c in corrigidas:
        grupos[chave_da_pergunta(c)].append(c)
    return {k: sorted(v, key=lambda c: c["seed"]) for k, v in grupos.items()}


def a_julgar(corrigidas: list[dict], todas: bool = False) -> list[dict]:
    """
    PT: As execuções pendentes de perguntas ainda não decididas: só o que
        pode mudar o acerto. Com todas, todas as pendentes, decididas ou
        não, para a contagem de 0 a 5 do experimento sair exata.
    EN: Pending runs of undecided questions; with todas, every pending run,
        so the experiment's 0–5 count is exact.
    """
    return [
        c
        for grupo in por_pergunta(corrigidas).values()
        if todas or acerto_da_pergunta([c["situacao"] for c in grupo]) == "pendente"
        for c in grupo if c["situacao"] == "pendente"
    ]
