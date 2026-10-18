"""
PT: Valida o experimento 2x2 (#50, ADR 0031) sem modelo, sem rede e sem
    dado. Roda no workflow próprio .github/workflows/experimento.yml.

    O que é conferido:

    1. **Pré-registro.** O que a estatística toma do registro em texto
       (margem de −0,05, intervalo de 95% pelo método 10, 5 execuções e
       maioria de 3) continua escrito lá; a família do Holm são as
       hipóteses confirmatórias; todo teste do registro é conhecido; os
       grupos da H5 cobrem os três tipos de acerto.
    2. **Estatística.** O intervalo de Newcombe bate com os 18 casos do
       método 10 na Tabela III do artigo de 1998; o McNemar exato
       unilateral bate com valores calculados à mão; o p da não
       inferioridade, levado de volta ao intervalo, cai na margem; o Holm
       segue o passo a passo; o Q de Cochran com duas condições é o
       qui-quadrado do McNemar; a permutação se repete com a mesma seed.
    3. **Cegamento e fila.** O id do item é opaco, muda com a condição e,
       sem ela, é o da seleção; a visão cega não depende de modelo,
       condição, SQL ou trechos, e muda quando a resposta muda; a fila do
       experimento traz as pendentes de perguntas já decididas; as
       condições ficam em grupos separados.
    4. **Executor.** A ordem das condições é uma permutação por pergunta,
       determinística e variada; um erro de servidor não grava a execução,
       entra nas repetições e para; um erro de tempo é gravado.
    5. **Análise.** Numa contagem sintética, as cinco hipóteses saem com
       efeito, intervalo, p, p ajustado na família e decisão coerente com
       o alfa; a página se gera.
    6. **Resultado, quando existe.** Os dois modelos, a análise refeita das
       contagens publicadas, a recorreção dos registros publicados e a
       página regenerada sem diferença.

    Com --autoteste, troca uma peça por vez por uma versão estragada e
    confere que a validação reprova cada uma pelo motivo certo.

EN: Validates the 2x2 experiment with no model, network or data:
    pre-registration text the statistics relies on, the statistics against
    Newcombe's Table III and hand-computed values, blinding and the judging
    queue, the runner's condition order and server-error rule, a synthetic
    analysis and, when present, the published result. --autoteste swaps
    one piece at a time for a broken version.

Uso / Usage:
    uv run python -m scripts.validar_experimento
    uv run python -m scripts.validar_experimento --autoteste
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import hashlib
import io
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import numpy as np
import yaml

from assistente import parametros
from assistente.cliente import ClienteFalso, ErroDeGeracao
from assistente.parametros import CONDICOES
from assistente.sql import banco_vazio
from correcao import acerto, as_cegas
from correcao.corretor import Gabarito, carregar_gabarito
from experimento import estatistica
from experimento.estatistica import Tabela
from scripts import executar_experimento, resumir_experimento
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import HIPOTESES, REGISTRO, RAIZ

# PT: o método 10 na Tabela III de Newcombe (1998): (e, f, g, h) e os
#     limites do intervalo de 95%, com 4 casas.
# EN: method 10 rows of Newcombe's (1998) Table III.
TABELA_III = [
    ((36, 12, 2, 0), (0.0569, 0.3404)), ((20, 12, 2, 16), (0.0562, 0.3292)), ((18, 12, 2, 18), (0.0562, 0.3290)),
    ((36, 14, 0, 0), (0.1528, 0.4167)), ((35, 14, 0, 1), (0.1461, 0.4175)), ((18, 14, 0, 18), (0.1441, 0.3963)),
    ((2, 97, 1, 0), (0.8721, 0.9854)), ((1, 97, 1, 1), (0.8736, 0.9850)), ((0, 29, 1, 0), (0.6666, 0.9882)),
    ((2, 98, 0, 0), (0.9178, 0.9945)), ((1, 98, 0, 1), (0.9171, 0.9916)), ((0, 30, 0, 0), (0.8395, 1.0)),
    ((54, 0, 0, 0), (-0.0664, 0.0664)), ((53, 0, 0, 1), (-0.0729, 0.0729)), ((30, 0, 0, 24), (-0.0358, 0.0358)),
    ((29, 0, 0, 25), (-0.0354, 0.0354)), ((28, 0, 0, 26), (-0.0352, 0.0352)), ((27, 0, 0, 27), (-0.0351, 0.0351)),
]
# PT: meia unidade da quarta casa, mais folga para o arredondamento da tabela
# EN: half a unit of the 4th decimal plus slack for the table's rounding
TOLERANCIA_DA_TABELA = 1e-4
TESTES_CONHECIDOS = {"mcnemar_exato_unilateral", "nao_inferioridade_intersecao_uniao",
                     "permutacao_unilateral_da_interacao"}
HEX16 = re.compile(r"^[0-9a-f]{16}$")


# -----------------------------------------------------------------------------
# PT: 1. Pré-registro / EN: pre-registration
# -----------------------------------------------------------------------------

def checar_pre_registro(hipoteses: dict, tipos: dict[str, str]) -> list[str]:
    erros = []
    est, execucao = hipoteses["estatistica"], hipoteses["execucao"]
    testes = " ".join(est["testes"]["nao_inferioridade_intersecao_uniao"].split())
    if "−0,05" not in testes or estatistica.MARGEM_DE_NAO_INFERIORIDADE != -0.05:
        erros.append("pré-registro: a margem da H4 não é mais −0,05 no registro ou no código")
    efeito = " ".join(est["tamanho_de_efeito"].split())
    if "95%" not in efeito or "método 10" not in efeito or estatistica.CONFIANCA_DO_EFEITO != 0.95:
        erros.append("pré-registro: o tamanho de efeito não é mais o Newcombe de 95%, método 10")
    if not (execucao["execucoes_por_pergunta"] == acerto.EXECUCOES_POR_PERGUNTA
            and acerto.MAIORIA == 3 and "3 ou mais das 5" in execucao["acerto_binario"]):
        erros.append("pré-registro: execuções por pergunta ou maioria diferentes do registro")
    confirmatorias = [n for n, h in hipoteses["hipoteses"].items() if h["familia"] == "confirmatoria"]
    if list(est["correcao"]["familia"]) != confirmatorias or est["correcao"]["metodo"] != "holm":
        erros.append("pré-registro: a família do Holm não são as hipóteses confirmatórias")
    if desconhecidos := {h["teste"] for h in hipoteses["hipoteses"].values()} - TESTES_CONHECIDOS:
        erros.append(f"pré-registro: teste sem implementação {sorted(desconhecidos)}")
    for nome, h in hipoteses["hipoteses"].items():
        if h.get("grupos") and set(sum(h["grupos"].values(), [])) != set(tipos.values()):
            erros.append(f"pré-registro: os grupos da {nome} não cobrem os tipos de acerto")
    if not all(k in est["simulacao"] for k in ("permutacoes", "reamostragens_bootstrap", "seed")):
        erros.append("pré-registro: a simulação sem permutações, reamostragens ou seed")
    return erros


# -----------------------------------------------------------------------------
# PT: 2. Estatística / EN: statistics
# -----------------------------------------------------------------------------

def checar_estatistica() -> list[str]:
    erros = []
    for celulas, esperado in TABELA_III:
        obtido = estatistica.newcombe_pareado(Tabela(*celulas))
        if any(abs(a - b) > TOLERANCIA_DA_TABELA for a, b in zip(obtido, esperado)):
            erros.append(f"Newcombe: {celulas} deu {[round(x, 4) for x in obtido]}, a Tabela III diz {esperado}")

    for a_favor, contra, esperado in [(5, 1, 7 / 64), (3, 0, 1 / 8), (0, 0, 1.0), (0, 4, 1.0), (2, 2, 11 / 16),
                                      (10, 2, 79 / 4096)]:
        if abs(estatistica.mcnemar_exato_unilateral(a_favor, contra) - esperado) > 1e-12:
            erros.append(f"McNemar: ({a_favor}, {contra}) deu {estatistica.mcnemar_exato_unilateral(a_favor, contra)}, "
                         f"esperado {esperado}")

    margem = estatistica.MARGEM_DE_NAO_INFERIORIDADE
    for celulas in [(20, 5, 1, 15), (10, 3, 3, 25), (30, 2, 4, 5), (12, 0, 0, 29), (0, 1, 0, 40), (5, 6, 2, 28)]:
        t = Tabela(*celulas)
        p = estatistica.p_de_nao_inferioridade(t)
        if t.diferenca <= margem:
            if p != 1.0:
                erros.append(f"não inferioridade: {celulas} na margem ou abaixo deu p {p}, esperado 1")
            continue
        if 1e-9 < p < 0.5 and abs(estatistica.newcombe_pareado(t, 1 - 2 * p)[0] - margem) > 1e-6:
            erros.append(f"não inferioridade: o p de {celulas} não leva o limite inferior à margem")
        nao_inferior = estatistica.newcombe_pareado(t, 0.90)[0] > margem
        if nao_inferior != (p < 0.05):
            erros.append(f"não inferioridade: {celulas} com p {p:.4f} e não inferior {nao_inferior}, incoerentes")

    ajustados = estatistica.holm({"H1": 0.01, "H2": 0.04, "H3": 0.03, "H4": 0.5})
    esperado = {"H1": 0.04, "H2": 0.09, "H3": 0.09, "H4": 0.5}
    if any(abs(ajustados[k] - v) > 1e-12 for k, v in esperado.items()):
        erros.append(f"Holm: {ajustados}, esperado {esperado}")

    # PT: com duas condições, o Q de Cochran é (f − g)²/(f + g).
    # EN: with two conditions, Cochran's Q equals McNemar's chi-square.
    matriz = [[True, True]] * 7 + [[True, False]] * 6 + [[False, True]] * 2 + [[False, False]] * 9
    q = estatistica.q_de_cochran(matriz)["q"]
    if q is None or abs(q - (6 - 2) ** 2 / (6 + 2)) > 1e-12:
        erros.append(f"Cochran: duas condições deram Q {q}, esperado 2")
    if estatistica.q_de_cochran([[True] * 4] * 5 + [[False] * 4] * 3)["q"] is not None:
        erros.append("Cochran: sem variação dentro das perguntas o Q precisa sair nulo")

    diferencas = [1, 1, 0, 1, -1, 0, 0, 1, 0, 0, -1, 0, 1, 0]
    grupo = [True] * 5 + [False] * 9
    um = estatistica.interacao_por_permutacao(diferencas, grupo, 500, 500, 47)
    dois = estatistica.interacao_por_permutacao(diferencas, grupo, 500, 500, 47)
    if um != dois:
        erros.append("permutação: a mesma seed deu resultados diferentes")
    if abs(um["estatistica"] - (2 / 5 - 1 / 9)) > 1e-12 or not 0 <= um["p"] <= 1:
        erros.append(f"permutação: estatística {um['estatistica']} ou p {um['p']} errados")
    return erros


# -----------------------------------------------------------------------------
# PT: 3. Cegamento e fila / EN: blinding and queue
# -----------------------------------------------------------------------------

def _registro(id_: str, condicao: str, candidato: str, sql: str, interpretacao: str = "x", ressalva: str = "",
              abstencao: str = "") -> dict:
    return {"candidato": candidato, "id_pergunta": id_, "seed": 1, "condicao": condicao, "erro": None,
            "trechos": [{"texto": f"trecho-de-{condicao}"}], "proveniencia": {"sql": sql},
            "resposta": {"interpretacao": interpretacao, "sql": sql, "ressalva": ressalva, "abstencao": abstencao,
                         "valores": {"colunas": [], "linhas": []}}}


def checar_cegamento(g: Gabarito) -> list[str]:
    erros = []
    ids = {c: acerto.id_do_item("modelo", "Q41", 1, c) for c in CONDICOES}
    if len(set(ids.values())) != len(CONDICOES) or not all(HEX16.match(i) for i in ids.values()):
        erros.append(f"cegamento: o id do item não é opaco ou não muda com a condição: {ids}")
    legado = hashlib.sha256("modelo|Q41|1".encode("utf-8")).hexdigest()[:16]
    if acerto.id_do_item("modelo", "Q41", 1) != legado:
        erros.append("cegamento: sem condição, o id do item deixou de ser o da seleção")

    # PT: a fonte do contexto vira "o contexto", e o conteúdo fica (frases
    #     no formato das respostas da fumaça de 2026-10-14).
    # EN: the context source becomes "o contexto"; content stays.
    fontes = {
        "Mas a ontologia indica que a coluna porte é polimórfica.": "Mas o contexto indica que a coluna porte é polimórfica.",
        "O documento de metodologia menciona o recorte.": "O contexto menciona o recorte.",
        "Segundo os trechos recuperados e a documentação, sim.": "Segundo o contexto e o contexto, sim.",
        "A meta definida pelo Copom, série 4189 do SGS.": "A meta definida pelo Copom, série 4189 do SGS.",
    }
    for texto, esperado in fontes.items():
        if as_cegas.sem_citacoes(texto) != esperado:
            erros.append(f"cegamento: a fonte do contexto ficou em '{as_cegas.sem_citacoes(texto)}'")

    a = _registro("Q41", "A", "modelo-a", "select segredo_a", abstencao="falta a taxa")
    d = _registro("Q41", "D", "modelo-b", "select segredo_d", abstencao="falta a taxa")
    outra = _registro("Q41", "A", "modelo-a", "select segredo_a", abstencao="falta o cliente")
    ca, cd, co = acerto.corrigir_todas([a, d, outra], {}, g, com_condicao=True)
    if as_cegas.visao_cega(ca, a) != as_cegas.visao_cega(cd, d):
        erros.append("visão cega: muda com o modelo, a condição, o SQL ou os trechos")
    if as_cegas.visao_cega(ca, a) == as_cegas.visao_cega(co, outra):
        erros.append("visão cega: não muda quando a resposta muda")
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        as_cegas.mostrar({**cd, "item": as_cegas.visao_cega(cd, d)}, d, "enunciado", g, 1)
    if any(s in saida.getvalue() for s in ("modelo-b", "segredo_d", "trecho-de-D")):
        erros.append("cegamento: o item do experimento mostra o modelo, o SQL ou os trechos")

    def item(seed, situacao, condicao="A"):
        return {"candidato": "c", "condicao": condicao, "pergunta": "Q09", "seed": seed, "situacao": situacao,
                "item": f"{condicao}{seed}"}
    decidida = [item(1, "certo"), item(2, "certo"), item(3, "certo"), item(4, "pendente"), item(5, "pendente")]
    if len(acerto.a_julgar(decidida, todas=True)) != 2 or acerto.a_julgar(decidida):
        erros.append("fila: a do experimento precisa trazer as pendentes de pergunta decidida, e a da seleção não")
    duas = [item(s, "certo", "A") for s in range(1, 4)] + [item(s, "pendente", "B") for s in range(1, 3)]
    if len(acerto.por_pergunta(duas)) != 2 or len(acerto.a_julgar(duas)) != 2:
        erros.append("fila: condições diferentes da mesma pergunta caíram no mesmo grupo")
    return erros


# -----------------------------------------------------------------------------
# PT: 4. Executor / EN: runner
# -----------------------------------------------------------------------------

class _ClienteQueFalha(ClienteFalso):
    """PT: falha toda chamada com o tipo dado / EN: fails every call"""

    def __init__(self, tipo: str):
        super().__init__([])
        self.tipo = tipo

    def gerar(self, mensagens, esquema, seed):
        raise ErroDeGeracao(self.tipo, f"falha de {self.tipo} do ensaio")


def checar_executor(por_id: dict[str, dict]) -> list[str]:
    erros = []
    modelos = executar_experimento.modelos_do_experimento()
    for m in modelos:
        ordens = [executar_experimento.ordem_das_condicoes(m["nome"], i) for i in por_id]
        if any(sorted(o) != sorted(CONDICOES) for o in ordens):
            erros.append(f"ordem: {m['nome']} tem pergunta sem as quatro condições")
        if ordens != [executar_experimento.ordem_das_condicoes(m["nome"], i) for i in por_id]:
            erros.append(f"ordem: {m['nome']} não é determinística")
        if {o[0] for o in ordens} != set(CONDICOES) or len({tuple(o) for o in ordens}) < len(CONDICOES):
            erros.append(f"ordem: {m['nome']} não varia entre as perguntas")

    modelo = modelos[0]
    p = dataclasses.replace(parametros.carregar(modelo=modelo["ollama"]), seeds=(1,))
    uma = dict(list(por_id.items())[:1])
    comum = {"banco": banco_vazio(), "modelo_de_prompt": parametros.modelo_de_prompt(),
             "buscar": lambda pergunta: executar_experimento.TRECHOS_DE_ENSAIO,
             "indice": executar_experimento.INDICE_DE_ENSAIO}
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
        pasta = Path(tmp)
        try:
            executar_experimento.rodar_modelo(modelo, p, uma, pasta, cliente_para=lambda i, s: _ClienteQueFalha(
                "servidor"), **comum)
            erros.append("servidor: o erro de servidor não parou o executor")
        except executar_experimento.ParadaPorServidor:
            pass
        gravadas = list((pasta / "execucoes").rglob("*.json")) if (pasta / "execucoes").exists() else []
        arquivo = pasta / executar_experimento.REPETICOES
        repeticoes = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else []
        if gravadas or len(repeticoes) != 1:
            erros.append(f"servidor: {len(gravadas)} execuções gravadas e {len(repeticoes)} repetições anotadas, "
                         "esperado 0 e 1")
        executar_experimento.rodar_modelo(modelo, p, uma, pasta, cliente_para=lambda i, s: _ClienteQueFalha("tempo"),
                                          **comum)
        gravadas = sorted((pasta / "execucoes").rglob("*.json"))
        tipos = {json.loads(a.read_text(encoding="utf-8"))["erro"]["tipo"] for a in gravadas}
        if len(gravadas) != len(CONDICOES) or tipos != {"tempo"}:
            erros.append(f"servidor: o erro de tempo devia ser gravado nas {len(CONDICOES)} condições, foram "
                         f"{len(gravadas)}")
        # PT: trechos gravados com outro índice param o executor.
        # EN: excerpts stored from another index stop the runner.
        id_, pergunta = next(iter(uma.items()))
        outro = {**executar_experimento.INDICE_DE_ENSAIO, "sha256_trechos": "outro"}
        try:
            executar_experimento.trechos_da_pergunta(pasta, id_, pergunta["pergunta"], comum["buscar"], outro)
            erros.append("trechos: o cache de outro índice foi aceito")
        except SystemExit:
            pass
    return erros


# -----------------------------------------------------------------------------
# PT: 5. Análise / EN: analysis
# -----------------------------------------------------------------------------

def checar_analise(analise: dict, hipoteses: dict, rotulo: str) -> list[str]:
    """PT: a forma e a coerência de uma análise / EN: shape and coherence"""
    erros = []
    alfa = float(hipoteses["estatistica"]["alfa"])
    familia = list(hipoteses["estatistica"]["correcao"]["familia"])
    if faltam := [h for h in hipoteses["hipoteses"] if h not in analise["hipoteses"]]:
        erros.append(f"{rotulo}: falta a hipótese {faltam}")
        return erros
    for nome, r in analise["hipoteses"].items():
        partes = list(r["comparacoes"].values()) if "comparacoes" in r else [r]
        for parte in partes:
            efeito, ic = parte.get("diferenca_pp", parte.get("estatistica_pp")), parte.get("ic95_pp")
            if efeito is None or not ic or not ic[0] - 1e-9 <= efeito <= ic[1] + 1e-9:
                erros.append(f"{rotulo}: {nome} sem efeito dentro do intervalo de 95%")
        if "comparacoes" in r and r["p"] != max(p["p"] for p in partes):
            erros.append(f"{rotulo}: o p da {nome} não é o maior das duas comparações")
        if "comparacoes" in r and any(p["p"] < alfa - 1e-5 and not p["nao_inferior"] for p in partes):
            erros.append(f"{rotulo}: na {nome}, p abaixo do alfa sem não inferioridade no IC de 90%")
        if (r["p_ajustado"] is None) == (nome in familia):
            erros.append(f"{rotulo}: p ajustado da {nome} fora da família do Holm")
        decisivo = r["p_ajustado"] if r["p_ajustado"] is not None else r["p"]
        # PT: a decisão sai do p exato; o publicado tem 6 casas, então a
        #     coerência só se cobra fora da vizinhança do alfa.
        # EN: decisions use the exact p; skip the rounding neighbourhood.
        if abs(decisivo - alfa) > 1e-5 and (r["decisao"] == "sustentada") != (decisivo <= alfa):
            erros.append(f"{rotulo}: decisão da {nome} incoerente com o alfa")

    # PT: o Holm refeito à parte, pelo passo a passo.
    # EN: Holm recomputed independently, step by step.
    ordem = sorted(familia, key=lambda h: (analise["hipoteses"][h]["p"], h))
    acumulado = 0.0
    for i, h in enumerate(ordem):
        acumulado = max(acumulado, min(1.0, (len(ordem) - i) * analise["hipoteses"][h]["p"]))
        if abs(analise["hipoteses"][h]["p_ajustado"] - acumulado) > 1e-5:
            erros.append(f"{rotulo}: Holm da {h} deu {analise['hipoteses'][h]['p_ajustado']}, esperado {acumulado}")
    for c, v in analise["variancia"].items():
        if sum(v["distribuicao"]) != analise["perguntas"]:
            erros.append(f"{rotulo}: distribuição de 0 a 5 da condição {c} não soma as perguntas")
    return erros


def contagem_sintetica(ids: list[str]) -> dict[str, dict[str, int]]:
    """PT: contagens de 0 a 5 inventadas, variadas / EN: invented 0–5 counts"""
    return {c: {i: (n * 7 + k * 3 + (n * k) % 4) % 6 for n, i in enumerate(ids)}
            for k, c in enumerate(sorted(CONDICOES))}


def checar_sintetico(hipoteses: dict, tipos: dict[str, str]) -> list[str]:
    analise = estatistica.analisar(contagem_sintetica(list(tipos)), tipos, hipoteses)
    erros = checar_analise(analise, hipoteses, "análise sintética")
    resultado = {"metadata": {"hipoteses": HIPOTESES, "perguntas": len(tipos), "execucoes_por_pergunta": 5,
                              "maioria": 3, "mes_de_referencia": "2000-01-31", "execucao": 2, "variacao": ["V0"],
                              "tipos_de_acerto": {t: list(tipos.values()).count(t) for t in set(tipos.values())}},
                 "limite_declarado": "limite", "repeticoes_por_servidor": [],
                 "modelos": {"sintetico": {"analise": analise,
                                           "erros_por_motivo": {c: {"abstencao_indevida": 1} for c in CONDICOES}}}}
    texto = resumir_experimento.pagina({2: resultado}, hipoteses)
    if faltam := [h for h in hipoteses["hipoteses"] if f"| {h}:" not in texto]:
        erros.append(f"página: faltam as hipóteses {faltam}")
    return erros


# -----------------------------------------------------------------------------
# PT: 6. Resultado / EN: result
# -----------------------------------------------------------------------------

def checar_resultado(resultado: dict, hipoteses: dict, tipos: dict[str, str]) -> list[str]:
    erros = []
    execucao = resultado["metadata"].get("execucao")
    # PT: as duas execuções rodam com os modelos do parametros.yml (ADR 0032).
    # EN: both runs use the parametros.yml models.
    esperados = sorted(m["nome"] for m in executar_experimento.modelos_do_experimento())
    if sorted(resultado["modelos"]) != esperados:
        erros.append(f"resultado: modelos {list(resultado['modelos'])} na execução {execucao}, esperado {esperados}")
    if resultado["metadata"].get("numpy") != np.__version__:
        erros.append(f"resultado: gerado com o numpy {resultado['metadata'].get('numpy')}, este ambiente tem "
                     f"{np.__version__}; a simulação da H5 só se refaz no mesmo numpy (Python fixado no workflow)")
    for nome, m in resultado["modelos"].items():
        for c, por in m["execucoes"].items():
            # PT: na execução 1, tudo julgado; na 2, pendente só em
            #     pergunta já decidida pela maioria (ADR 0032).
            # EN: run 1 fully judged; run 2 pending only in decided questions.
            if any(len(s) != acerto.EXECUCOES_POR_PERGUNTA for s in por.values()):
                erros.append(f"resultado: {nome} {c} com pergunta sem 5 execuções")
            if any("pendente" in s and (execucao == 1 or acerto.acerto_da_pergunta(s) == "pendente")
                   for s in por.values()):
                erros.append(f"resultado: {nome} {c} com pergunta sem julgamento que decide")
            if any(m["certas"][c][i] != s.count("certo") for i, s in por.items()):
                erros.append(f"resultado: {nome} {c} com contagem diferente das execuções")
        if m["analise"] is None:
            erros.append(f"resultado: {nome} sem análise")
            continue
        erros += checar_analise(m["analise"], hipoteses, f"resultado {nome}")
        if estatistica.analisar(m["certas"], tipos, hipoteses) != m["analise"]:
            erros.append(f"resultado: a análise de {nome} refeita das contagens difere da publicada")
    return erros


def checar_recorrecao(resultados: dict[int, dict], hipoteses: dict) -> list[str]:
    """
    PT: Recorrige os registros publicados de cada execução com os
        julgamentos publicados e confere que o resultado e a página saem
        iguais.
    EN: Regrades each run's published records and compares result and page.
    """
    erros = []
    for execucao, resultado in resultados.items():
        if not resumir_experimento.execucoes_de(execucao).exists():
            erros.append(f"resultado: execucoes.jsonl.gz da execução {execucao} não publicado")
            continue
        refeito, problemas = resumir_experimento.montar(*resumir_experimento.ler_publicado(execucao), hipoteses,
                                                        execucao=execucao)
        erros += [f"resultado da execução {execucao}: {p}" for p in problemas]
        if refeito != resultado:
            erros.append(f"resultado: a execução {execucao} recorrigida dos registros publicados difere do "
                         "resultado.json")
    pagina = resumir_experimento.PAGINA
    if not pagina.exists() or pagina.read_text(encoding="utf-8") != resumir_experimento.pagina(resultados, hipoteses):
        erros.append("página: docs/experimento.md difere da regenerada")
    return erros


# -----------------------------------------------------------------------------
# PT: Validação / EN: validation
# -----------------------------------------------------------------------------

@dataclass
class Dados:
    hipoteses: dict
    registro: dict
    resultados: dict[int, dict]
    tipos: dict[str, str]
    por_id: dict[str, dict]


def ler() -> Dados:
    _, por_id = perguntas(VIGENTE)
    return Dados(
        hipoteses=yaml.safe_load((RAIZ / HIPOTESES).read_text(encoding="utf-8")),
        registro=yaml.safe_load((RAIZ / REGISTRO).read_text(encoding="utf-8")),
        resultados=resumir_experimento.resultados_publicados(),
        tipos={i: p.get("tipo_de_acerto", "valor") for i, p in por_id.items()},
        por_id=por_id,
    )


def validar(d: Dados, g: Gabarito, recorrigir: bool = True) -> list[str]:
    erros = checar_pre_registro(d.hipoteses, d.tipos) + checar_estatistica() + checar_cegamento(g)
    erros += checar_executor(d.por_id) + checar_sintetico(d.hipoteses, d.tipos)
    for resultado in d.resultados.values():
        erros += checar_resultado(resultado, d.hipoteses, d.tipos)
    if d.resultados and recorrigir:
        erros += checar_recorrecao(d.resultados, d.hipoteses)
    return erros


def autoteste(d: Dados, g: Gabarito) -> list[str]:
    """
    PT: Cada caso estraga uma peça e diz o trecho que a reprovação precisa
        trazer.
    EN: Each case breaks one piece and names the expected fragment.
    """
    if problemas := validar(d, g):
        return [f"a validação já falha antes do autoteste: {problemas[:3]}"]

    def margem_mudada():
        copia = copy.deepcopy(d)
        texto = copia.hipoteses["estatistica"]["testes"]["nao_inferioridade_intersecao_uniao"]
        copia.hipoteses["estatistica"]["testes"]["nao_inferioridade_intersecao_uniao"] = texto.replace("−0,05", "−0,10")
        return copia

    def resultado_adulterado():
        copia = copy.deepcopy(d)
        if copia.resultados:
            modelo = next(iter(next(iter(copia.resultados.values()))["modelos"].values()))
            pergunta = next(iter(modelo["certas"]["B"]))
            modelo["certas"]["B"][pergunta] = 5 - modelo["certas"]["B"][pergunta]
        return copia

    def sem_h5(*args, **kwargs):
        analise = _analisar_original(*args, **kwargs)
        analise["hipoteses"].pop("H5")
        return analise

    _analisar_original = estatistica.analisar
    _id_original = acerto.id_do_item
    _visao_original = as_cegas.visao_cega
    _a_julgar_original = acerto.a_julgar
    negativos = [
        ("margem da H4 mudada no registro", margem_mudada, None, "margem da H4"),
        ("phi sem a correção do método 10", lambda: d, mock.patch.object(
            estatistica, "phi_do_metodo_10",
            lambda t: 0.0 if not (t.e + t.f) * (t.g + t.h) * (t.e + t.g) * (t.f + t.h) else
            (t.e * t.h - t.f * t.g) / ((t.e + t.f) * (t.g + t.h) * (t.e + t.g) * (t.f + t.h)) ** 0.5), "Tabela III"),
        ("McNemar bilateral", lambda: d, mock.patch.object(
            estatistica, "mcnemar_exato_unilateral",
            lambda a, b: 1.0 if a + b == 0 else min(1.0, 2 * min(
                sum(estatistica.math.comb(a + b, k) for k in range(a, a + b + 1)),
                sum(estatistica.math.comb(a + b, k) for k in range(0, a + 1))) / 2 ** (a + b))), "McNemar"),
        ("Holm sem ajuste", lambda: d, mock.patch.object(estatistica, "holm", lambda ps: dict(ps)), "Holm"),
        ("análise sem a H5", lambda: d, mock.patch.object(estatistica, "analisar", sem_h5), "falta a hipótese"),
        ("id que revela a condição", lambda: d, mock.patch.object(
            acerto, "id_do_item", lambda c, p, s, cond=None: (cond or "") + _id_original(c, p, s, cond)[:15]),
         "id do item"),
        ("visão cega com o SQL", lambda: d, mock.patch.object(
            as_cegas, "visao_cega", lambda c, r: _visao_original(c, r) + (r.get("resposta") or {}).get("sql", "")),
         "visão cega"),
        ("fila do experimento só com o que decide", lambda: d, mock.patch.object(
            acerto, "a_julgar", lambda corrigidas, todas=False: _a_julgar_original(corrigidas)), "fila"),
        ("ordem das condições fixa", lambda: d, mock.patch.object(
            executar_experimento, "ordem_das_condicoes", lambda m, p: sorted(CONDICOES)), "não varia"),
        ("erro de servidor sem anotação", lambda: d, mock.patch.object(
            executar_experimento, "registrar_repeticao", lambda pasta, registro: None), "repetições anotadas"),
        ("fonte do contexto sem neutralizar", lambda: d, mock.patch.object(
            as_cegas, "_FONTES", re.compile(r"(?!)")), "fonte do contexto"),
        ("cache de trechos sem conferir o índice", lambda: d, mock.patch.object(
            executar_experimento, "trechos_da_pergunta",
            lambda pasta, id_, pergunta, buscar, indice: buscar(pergunta)), "cache de outro índice"),
    ]
    if d.resultados:
        negativos.append(("resultado adulterado numa contagem", resultado_adulterado, None, "resultado"))
    falhas = []
    for descricao, montar, remendo, trecho in negativos:
        with remendo or contextlib.nullcontext():
            problemas = validar(montar(), g, recorrigir=False)
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas[:3]}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    args = parser.parse_args()

    d, g = ler(), carregar_gabarito()
    if args.autoteste:
        falhas = autoteste(d, g)
    else:
        falhas = validar(d, g)
        print(f"  estatística: {len(TABELA_III)} casos da Tabela III de Newcombe; executor, cegamento e análise "
              f"sintética conferidos; resultado "
              f"{f'conferido nas execuções {sorted(d.resultados)}' if d.resultados else 'ainda não gerado'}")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
