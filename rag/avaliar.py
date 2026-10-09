"""
PT: Mede a recuperação de cada candidato no gabarito de recuperação
    (evaluation/recuperacao.yml) e escolhe o modelo de embeddings do
    experimento (evaluation/hipoteses.yml, rag.modelo_de_embeddings),
    pela regra decidida em 2026-10-07:

    - métrica de escolha: acerto@5, a parcela dos conceitos em que algum
      dos 5 trechos trazidos cai no lugar citado pela ontologia;
    - empate: vence a menor memória dos pesos (ADR 0026 usa a menor VRAM;
      aqui tudo roda na CPU, e a memória dos pesos é a medida comparável);
    - diagnóstico, que não entra na escolha: MRR (recíproco da posição do
      primeiro acerto, zero sem acerto), acerto@5 por documento e acerto@5
      nas perguntas do experimento, consultadas pelo enunciado como no
      pré-registro, contra os conceitos que o evaluation/gabarito.yml cita
      como fonte. Usar as perguntas na escolha seria escolher o modelo pelo
      conjunto de teste.

    Grava rag/avaliacao.json e o escolhido em rag/manifesto.json.

EN: Measures each candidate's retrieval on the retrieval answer key and
    picks the experiment's embedding model: hit@5 decides, smallest weight
    memory breaks ties. MRR, per-document hit@5 and hit@5 on the experiment
    questions are diagnostics only, so the model is not chosen on the test
    set. Writes rag/avaliacao.json and the choice into rag/manifesto.json.

Uso / Usage:
    uv run --group rag python -m rag.avaliar
"""

from __future__ import annotations

import json
import re

import numpy as np
import yaml

from rag.indice import carregar_indice, embeddings_das_consultas, melhores
from rag.parametros import (AVALIACAO, CANDIDATOS, GABARITO_DE_RECUPERACAO, MANIFESTO_RAG, QUANTIDADE_DE_TRECHOS,
                            RAIZ, Candidato)

PERGUNTAS = RAIZ / "evaluation" / "questions_v3.yml"
GABARITO = RAIZ / "evaluation" / "gabarito.yml"

# -----------------------------------------------------------------------------
# PT: Quando um trecho cai no alvo.
# EN: When a chunk falls on a target.
# -----------------------------------------------------------------------------


def casa_secao(citada: str, secao: str) -> bool:
    """
    PT: A seção citada no gabarito corresponde à seção do trecho? Igual,
        ou, no leiaute, "Doc3040, bloco c" contra "Doc3040: (NR1) c. ...",
        ou, no CNPJ, "tabela SIMPLES" contra "DADOS DO SIMPLES".
    EN: Does the cited section match the chunk's section?
    """
    if citada == secao:
        return True
    if m := re.fullmatch(r"Doc3040, bloco ([a-z])", citada):
        return re.match(rf"^Doc3040: (?:\(NR\d*\)\s*)?{m.group(1)}\.\s", secao) is not None
    if m := re.fullmatch(r"tabela (.+)", citada):
        return m.group(1).casefold() in secao.casefold()
    return False


def casa_pagina(paginas: list[int], inicial: str | None, final: str | None) -> bool:
    """PT: o trecho toca alguma página citada? / EN: does the chunk touch a cited page?"""
    if inicial is None or not inicial.isdigit():
        return False
    return any(int(inicial) <= p <= int(final) for p in paginas)


def casa(alvo: dict, trecho: dict) -> bool:
    """
    PT: Um trecho acerta o alvo quando é do documento e cai na página ou na
        seção citada, ou em qualquer lugar do documento quando o alvo é o
        documento inteiro.
    EN: A chunk hits the target when it is from the document and falls on
        the cited page or section, or anywhere for a document-level target.
    """
    if trecho["documento"] != alvo["documento"]:
        return False
    if alvo["granularidade"] == "documento":
        return True
    if alvo["granularidade"] == "pagina":
        return casa_pagina(alvo["paginas"], trecho["pagina_inicial"], trecho["pagina_final"])
    return any(casa_secao(s, trecho["secao"]) for s in alvo["secoes"])


def posicao_do_acerto(alvos: list[dict], trazidos: list[dict]) -> int | None:
    """PT: posição (1 a 5) do primeiro trecho que acerta / EN: rank of the first hit"""
    for posicao, trecho in enumerate(trazidos, 1):
        if any(casa(a, trecho) for a in alvos):
            return posicao
    return None


# -----------------------------------------------------------------------------
# PT: Leitura dos gabaritos.
# EN: Reading the answer keys.
# -----------------------------------------------------------------------------


def perguntas_do_experimento() -> dict[str, str]:
    """PT: {id: enunciado em português} das perguntas vigentes / EN: current questions"""
    perguntas: dict[str, str] = {}

    def percorrer(no):
        if isinstance(no, dict):
            if "id" in no and "pergunta" in no:
                perguntas[no["id"]] = no["pergunta"]
            for valor in no.values():
                percorrer(valor)
        elif isinstance(no, list):
            for valor in no:
                percorrer(valor)

    percorrer(yaml.safe_load(PERGUNTAS.read_text(encoding="utf-8")))
    return perguntas


def alvos_das_perguntas(alvos_por_conceito: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    PT: Para cada pergunta, os alvos dos conceitos que o gabarito.yml cita
        como fonte. Pergunta sem conceito com alvo fica fora do diagnóstico.
    EN: For each question, the targets of the concepts its answer key cites.
    """
    gabarito = yaml.safe_load(GABARITO.read_text(encoding="utf-8"))["perguntas"]
    resultado = {}
    for pergunta, item in gabarito.items():
        alvos = [a for ref in item.get("fonte") or [] for a in alvos_por_conceito.get(ref, [])]
        if alvos:
            resultado[pergunta] = alvos
    return resultado


# -----------------------------------------------------------------------------
# PT: Medida e escolha.
# EN: Measure and choice.
# -----------------------------------------------------------------------------


def recuperar(c: Candidato, consultas: list[str]) -> list[list[dict]]:
    """PT: os 5 trechos de cada consulta / EN: the top 5 chunks per query"""
    trechos, vetores = carregar_indice(c)
    similaridades = embeddings_das_consultas(c, consultas) @ vetores.T
    return [[trechos.row(int(i), named=True) for i in melhores(linha, QUANTIDADE_DE_TRECHOS)]
            for linha in similaridades]


def medir(posicoes: list[int | None]) -> dict:
    """PT: acertos, acerto@5 e MRR / EN: hits, hit@5 and MRR"""
    acertos = sum(p is not None for p in posicoes)
    return {
        "consultas": len(posicoes),
        "acertos": acertos,
        "acerto_em_5": round(acertos / len(posicoes), 4) if posicoes else None,
        "mrr": round(float(np.mean([1 / p if p else 0 for p in posicoes])), 4) if posicoes else None,
    }


def avaliar_candidato(c: Candidato, gabarito: list[dict], perguntas: dict[str, str],
                      alvos_por_pergunta: dict[str, list[dict]]) -> dict:
    """PT: medidas de um candidato / EN: one candidate's measures"""
    trazidos = recuperar(c, [g["consulta"] for g in gabarito])
    posicoes = {g["conceito"]: posicao_do_acerto(g["alvos"], t) for g, t in zip(gabarito, trazidos)}

    por_documento: dict[str, list[int | None]] = {}
    for g in gabarito:
        por_documento.setdefault(g["alvos"][0]["documento"], []).append(posicoes[g["conceito"]])

    ids = sorted(alvos_por_pergunta)
    trazidos_nas_perguntas = recuperar(c, [perguntas[i] for i in ids])
    posicoes_nas_perguntas = {i: posicao_do_acerto(alvos_por_pergunta[i], t) for i, t in zip(ids, trazidos_nas_perguntas)}

    return {
        "gabarito_de_recuperacao": medir(list(posicoes.values())),
        "por_documento": {d: medir(p) for d, p in sorted(por_documento.items())},
        "diagnostico_nas_perguntas": medir(list(posicoes_nas_perguntas.values())),
        "posicao_por_conceito": posicoes,
        "posicao_por_pergunta": posicoes_nas_perguntas,
    }


def escolher(resultados: dict, manifesto_rag: dict) -> dict:
    """
    PT: Maior número de acertos no gabarito; empate pela menor memória dos
        pesos. Devolve o escolhido, com a regra e os números que decidiram.
    EN: Most hits on the answer key; ties by smallest weight memory.
    """
    def chave(nome):
        return (-resultados[nome]["gabarito_de_recuperacao"]["acertos"],
                manifesto_rag["candidatos"][nome]["memoria_dos_pesos_em_mb"])

    ordem = sorted(resultados, key=chave)
    vencedor = ordem[0]
    empate = len(ordem) > 1 and chave(ordem[0])[0] == chave(ordem[1])[0]
    info = manifesto_rag["candidatos"][vencedor]
    return {
        "nome": vencedor,
        "repositorio": info["repositorio"],
        "revisao": info["revisao"],
        "regra": "maior acerto@5 no gabarito de recuperação; empate pela menor memória dos pesos (decisão de 2026-10-07)",
        "decidido_por": "memória dos pesos, em empate" if empate else "acerto@5",
        "acerto_em_5": resultados[vencedor]["gabarito_de_recuperacao"]["acerto_em_5"],
        "sha256_trechos": info["sha256_trechos"],
        "sha256_embeddings": info["sha256_embeddings"],
    }


def main() -> None:
    from transformers.utils import logging as logging_do_transformers

    logging_do_transformers.set_verbosity_error()
    gabarito_de_recuperacao = yaml.safe_load(GABARITO_DE_RECUPERACAO.read_text(encoding="utf-8"))
    gabarito = gabarito_de_recuperacao["alvos"]
    alvos_por_conceito = {g["conceito"]: g["alvos"] for g in gabarito}
    perguntas = perguntas_do_experimento()
    alvos_por_pergunta = alvos_das_perguntas(alvos_por_conceito)
    manifesto_rag = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8"))

    resultados = {}
    for c in CANDIDATOS:
        resultados[c.nome] = avaliar_candidato(c, gabarito, perguntas, alvos_por_pergunta)
        r = resultados[c.nome]
        print(f"  > {c.nome}: acerto@5 {r['gabarito_de_recuperacao']['acerto_em_5']:.1%} "
              f"({r['gabarito_de_recuperacao']['acertos']}/{len(gabarito)}), MRR {r['gabarito_de_recuperacao']['mrr']}, "
              f"perguntas {r['diagnostico_nas_perguntas']['acerto_em_5']:.1%}", flush=True)

    escolhido = escolher(resultados, manifesto_rag)
    saida = {
        "issue": 46,
        "gabarito": {"arquivo": "evaluation/recuperacao.yml", **gabarito_de_recuperacao["metadata"]},
        "perguntas_no_diagnostico": len(alvos_por_pergunta),
        "candidatos": resultados,
        "escolhido": escolhido,
    }
    AVALIACAO.write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifesto_rag["escolhido"] = escolhido
    MANIFESTO_RAG.write_text(json.dumps(manifesto_rag, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  > escolhido / chosen: {escolhido['nome']} ({escolhido['decidido_por']})")


if __name__ == "__main__":
    main()
