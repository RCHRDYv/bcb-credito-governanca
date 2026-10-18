"""
PT: QA da estatística do experimento (#50) por outro caminho. Confere o
    experimento.estatistica contra implementações independentes, sem usar
    nenhuma função dele como referência:

    - McNemar exato unilateral contra o scipy.stats.binomtest, e o
      bilateral derivado contra o mcnemar(exact=True) do statsmodels;
    - Q de Cochran contra o cochrans_q do statsmodels;
    - Holm contra o multipletests do statsmodels;
    - intervalo de Newcombe contra uma reimplementação com o Wilson na
      forma (p + z²/2n ± z·sqrt(p(1−p)/n + z²/4n²))/(1 + z²/n);
    - p da não inferioridade contra uma busca em grade fina de α;
    - p da permutação contra a enumeração exata de todos os rótulos num
      caso pequeno.

    Com o resultado publicado, refaz o p da H1 a H3 de cada modelo pelo
    scipy, a partir das contagens publicadas, e reconta as execuções do
    execucoes.jsonl.gz.

EN: QA of the experiment statistics by independent paths: scipy and
    statsmodels for McNemar, Cochran and Holm, a re-derived Wilson form for
    Newcombe, a fine grid for the non-inferiority p, exact enumeration for
    the permutation p and, when published, the H1–H3 p values and run
    counts recomputed from the published files.

Uso / Usage:
    uv run python -m scripts.analises.qa_experimento
"""

from __future__ import annotations

import gzip
import itertools
import json
import math
import random
import sys
from collections import Counter
from statistics import NormalDist

import numpy as np
from scipy.stats import binomtest
from statsmodels.stats.contingency_tables import cochrans_q, mcnemar
from statsmodels.stats.multitest import multipletests

from experimento import estatistica
from experimento.estatistica import Tabela
from scripts import resumir_experimento
from scripts.validar_perguntas import VIGENTE, perguntas

# PT: semente do sorteio dos casos de teste / EN: seed of the test cases
SEED_DO_QA = 2026
CASOS = 300


class Conferencia:
    """PT: acumula conferências e divergências / EN: collects checks"""

    def __init__(self) -> None:
        self.total = 0
        self.falhas: list[str] = []

    def perto(self, rotulo: str, obtido: float, esperado: float, tolerancia: float) -> None:
        self.total += 1
        if not math.isclose(obtido, esperado, abs_tol=tolerancia):
            self.falhas.append(f"{rotulo}: {obtido} contra {esperado}")


# -----------------------------------------------------------------------------
# PT: Testes / EN: tests
# -----------------------------------------------------------------------------

def contra_scipy_e_statsmodels(conf: Conferencia, sorteio: random.Random) -> None:
    for _ in range(CASOS):
        f, g = sorteio.randint(0, 25), sorteio.randint(0, 25)
        unilateral = estatistica.mcnemar_exato_unilateral(f, g)
        if f + g:
            conf.perto(f"McNemar ({f}, {g})", unilateral, binomtest(f, f + g, 0.5, alternative="greater").pvalue, 1e-12)
            bilateral = min(1.0, 2 * min(unilateral, estatistica.mcnemar_exato_unilateral(g, f)))
            conf.perto(f"McNemar bilateral ({f}, {g})", bilateral,
                       mcnemar([[0, f], [g, 0]], exact=True).pvalue, 1e-12)

    for _ in range(CASOS):
        matriz = (np.random.default_rng(sorteio.randint(0, 10 ** 9)).random((41, 4)) < sorteio.random()).tolist()
        nosso = estatistica.q_de_cochran(matriz)
        if nosso["q"] is None:
            continue
        deles = cochrans_q(np.asarray(matriz, dtype=int))
        conf.perto("Cochran Q", nosso["q"], deles.statistic, 1e-9)
        conf.perto("Cochran p", nosso["p"], deles.pvalue, 1e-9)

    for _ in range(CASOS):
        ps = {f"H{i}": sorteio.random() ** 3 for i in range(1, 5)}
        nossos = estatistica.holm(ps)
        deles = multipletests(list(ps.values()), method="holm")[1]
        for (nome, _), ajustado in zip(ps.items(), deles):
            conf.perto(f"Holm {nome}", nossos[nome], ajustado, 1e-12)


def _wilson_outra_forma(x: int, n: int, z: float) -> tuple[float, float]:
    p = x / n
    centro = p + z * z / (2 * n)
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centro - meia) / (1 + z * z / n), (centro + meia) / (1 + z * z / n)


def _newcombe_outra_forma(e: int, f: int, g: int, h: int, confianca: float) -> tuple[float, float]:
    n = e + f + g + h
    z = NormalDist().inv_cdf(1 - (1 - confianca) / 2)
    p1, p2 = (e + f) / n, (e + g) / n
    l1, u1 = _wilson_outra_forma(e + f, n, z)
    l2, u2 = _wilson_outra_forma(e + g, n, z)
    produto = (e + f) * (g + h) * (e + g) * (f + h)
    numerador = e * h - f * g
    if numerador > 0:
        numerador = max(numerador - n / 2, 0)
    phi = 0.0 if produto == 0 else numerador / math.sqrt(produto)
    delta = math.sqrt(max((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2, 0))
    epsilon = math.sqrt(max((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2, 0))
    return (f - g) / n - delta, (f - g) / n + epsilon


def contra_newcombe_e_inversao(conf: Conferencia, sorteio: random.Random) -> None:
    for _ in range(CASOS):
        partes = sorted(sorteio.sample(range(0, 42), 3))
        e, f, g, h = partes[0], partes[1] - partes[0], partes[2] - partes[1], 41 - partes[2]
        for confianca in (0.90, 0.95):
            nosso = estatistica.newcombe_pareado(Tabela(e, f, g, h), confianca)
            outro = _newcombe_outra_forma(e, f, g, h, confianca)
            conf.perto(f"Newcombe {e, f, g, h} inferior", nosso[0], outro[0], 1e-9)
            conf.perto(f"Newcombe {e, f, g, h} superior", nosso[1], outro[1], 1e-9)

    margem = estatistica.MARGEM_DE_NAO_INFERIORIDADE
    alfas = np.arange(1e-5, 0.5, 1e-5)
    for _ in range(40):
        partes = sorted(sorteio.sample(range(0, 42), 3))
        e, f, g, h = partes[0], partes[1] - partes[0], partes[2] - partes[1], 41 - partes[2]
        if (f - g) / 41 <= margem:
            continue
        acima = [a for a in alfas if _newcombe_outra_forma(e, f, g, h, 1 - 2 * a)[0] > margem]
        if not acima:
            continue
        conf.perto(f"não inferioridade {e, f, g, h}", estatistica.p_de_nao_inferioridade(Tabela(e, f, g, h)),
                   float(acima[0]), 2e-5)


def contra_enumeracao(conf: Conferencia) -> None:
    """
    PT: Com 10 perguntas e 3 no grupo, há 120 rotulagens: o p exato é a
        parcela delas com estatística maior ou igual à observada. A
        permutação com 10.000 sorteios tem de ficar a menos de 0,02.
    EN: Exact enumeration of the 120 labelings against 10,000 permutations.
    """
    d = [1, 1, 0, -1, 0, 1, 0, 0, -1, 0]
    grupo = [True, True, True] + [False] * 7

    def estatistica_de(rotulos: tuple[int, ...]) -> float:
        dentro = [d[i] for i in rotulos]
        fora = [d[i] for i in range(len(d)) if i not in rotulos]
        return sum(dentro) / len(dentro) - sum(fora) / len(fora)

    observada = estatistica_de((0, 1, 2))
    rotulagens = list(itertools.combinations(range(len(d)), 3))
    exato = sum(estatistica_de(r) >= observada - 1e-12 for r in rotulagens) / len(rotulagens)
    r = estatistica.interacao_por_permutacao(d, grupo, 10000, 2000, 47)
    conf.perto("permutação contra enumeração", r["p"], exato, 0.02)
    conf.perto("estatística da permutação", r["estatistica"], observada, 1e-12)


# -----------------------------------------------------------------------------
# PT: Resultado publicado / EN: published result
# -----------------------------------------------------------------------------

def contra_o_publicado(conf: Conferencia) -> bool:
    """PT: cada execução publicada / EN: each published run"""
    publicadas = [n for n in resumir_experimento.EXECUCOES_DO_EXPERIMENTO if resumir_experimento.resultado_de(n).exists()]
    for execucao in publicadas:
        contra_uma_execucao(conf, execucao)
    return bool(publicadas)


def contra_uma_execucao(conf: Conferencia, execucao: int) -> None:
    resultado = json.loads(resumir_experimento.resultado_de(execucao).read_text(encoding="utf-8"))
    with gzip.open(resumir_experimento.execucoes_de(execucao), "rt", encoding="utf-8") as arquivo:
        registros = [json.loads(linha) for linha in arquivo]
    por_celula = Counter((r["candidato"], r["condicao"], r["id_pergunta"]) for r in registros)
    tipos = {i: p.get("tipo_de_acerto", "valor") for i, p in perguntas(VIGENTE)[1].items()}
    for nome, m in resultado["modelos"].items():
        for c, por in m["certas"].items():
            for i in por:
                conf.perto(f"execuções de {nome} {c} {i}", por_celula[(nome, c, i)], 5, 0)
        for h, r in m["analise"]["hipoteses"].items():
            if r["teste"] != "mcnemar_exato_unilateral":
                continue
            x, y = r["comparacao"].split("−")
            sub = [i for i in m["certas"][x] if tipos[i] in r["tipos_de_acerto"]]
            a_favor = sum(m["certas"][x][i] >= 3 and m["certas"][y][i] < 3 for i in sub)
            contra = sum(m["certas"][x][i] < 3 and m["certas"][y][i] >= 3 for i in sub)
            esperado = binomtest(a_favor, a_favor + contra, 0.5, alternative="greater").pvalue if a_favor + contra else 1
            conf.perto(f"execução {execucao} {nome} {h} p pelo scipy", r["p"], esperado, 1e-6)


def main() -> None:
    conf, sorteio = Conferencia(), random.Random(SEED_DO_QA)
    contra_scipy_e_statsmodels(conf, sorteio)
    contra_newcombe_e_inversao(conf, sorteio)
    contra_enumeracao(conf)
    publicado = contra_o_publicado(conf)
    print(f"  {conf.total} conferências, {len(conf.falhas)} divergências; resultado publicado "
          f"{'conferido' if publicado else 'ainda não gerado'}")
    if conf.falhas:
        print("FALHOU / FAILED:")
        for falha in conf.falhas[:30]:
            print(f"  - {falha}")
        sys.exit(1)
    print("  A estatística do experimento bate com as implementações independentes.")


if __name__ == "__main__":
    main()
