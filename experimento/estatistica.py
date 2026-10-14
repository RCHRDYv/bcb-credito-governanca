"""
PT: A estatística do experimento, como o evaluation/hipoteses.yml registrou
    (bloco estatistica), em funções puras: sem arquivo, sem rede e sem
    estado. O resumo (scripts.resumir_experimento), o validador e o notebook
    usam as mesmas funções, e o código fica congelado por errata antes da
    primeira execução (decisão 4 de 2026-10-14, ADR 0031).

    A unidade é a pergunta, com o acerto binário da maioria de 5, pareada
    entre condições. Para duas condições X e Y nas mesmas perguntas, a
    tabela pareada segue a notação de Newcombe (1998, Tabela I):

    - e: X e Y acertam;
    - f: só X acerta;
    - g: só Y acerta;
    - h: as duas erram.

    A diferença é X − Y = (f − g)/n.

    Os testes:

    - McNemar exato unilateral (H1 a H3): binomial sobre os discordantes,
      p = P(Bin(f + g, 1/2) >= f), exato em frações;
    - intervalo de Newcombe pareado, método 10 (Newcombe, 1998, Statistics
      in Medicine 17, p. 2639): intervalos de score de Wilson das duas
      marginais, combinados pelo φ, com o numerador do φ trocado por
      max(eh − fg − n/2, 0) quando eh > fg, e φ = 0 quando o denominador
      é zero;
    - não inferioridade (H4): o p é o menor α em que o limite inferior
      unilateral de 1 − α fica acima da margem de −0,05, achado por uma
      varredura em z com passo de 0,01 e bisseção até 1e-12;
    - interação da H5: permutação dos rótulos de grupo e bootstrap de
      percentil dentro de cada grupo, cada um com o próprio
      numpy.random.default_rng(47), o PCG64 do NumPy;
    - Holm na família H1 a H4, separado por modelo; Q de Cochran
      descritivo nas quatro condições.

EN: The pre-registered statistics as pure functions. Paired 2x2 tables use
    Newcombe's notation (e both right, f only X, g only Y, h neither) and
    the difference X − Y = (f − g)/n. One-sided exact McNemar, Newcombe's
    paired method 10 (Wilson score marginals combined through a
    continuity-corrected phi, phi = 0 on a zero denominator),
    non-inferiority p by inverting the interval (grid on z plus
    bisection), H5 interaction by label permutation and within-group
    percentile bootstrap (each with numpy default_rng(47), PCG64), Holm on
    H1–H4 per model and a descriptive Cochran's Q.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from statistics import NormalDist

import numpy as np
from scipy.stats import chi2

from correcao.acerto import EXECUCOES_POR_PERGUNTA, MAIORIA

# PT: a margem da H4 e a confiança do tamanho de efeito, como o registro
#     escreve em texto (estatistica.testes e tamanho_de_efeito). O validador
#     confere que o texto continua dizendo isto. A maioria de 3 em 5 vem do
#     correcao.acerto, a mesma regra do corretor.
# EN: the H4 margin and the effect size confidence, as the registry text
#     says. The 3-of-5 majority comes from correcao.acerto.
MARGEM_DE_NAO_INFERIORIDADE = -0.05
CONFIANCA_DO_EFEITO = 0.95

# PT: a inversão do intervalo da H4 / EN: inverting the H4 interval
PASSO_DA_VARREDURA_EM_Z = 0.01
Z_MAXIMO = 40.0
TOLERANCIA_DA_BISSECAO = 1e-12

CASAS = 6
_NORMAL = NormalDist()


# -----------------------------------------------------------------------------
# PT: Tabela pareada / EN: paired table
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Tabela:
    """
    PT: Tabela 2x2 pareada, na notação de Newcombe (1998): e as duas
        acertam, f só a primeira, g só a segunda, h nenhuma.
    EN: Paired 2x2 table in Newcombe's notation.
    """

    e: int
    f: int
    g: int
    h: int

    @property
    def n(self) -> int:
        return self.e + self.f + self.g + self.h

    @property
    def diferenca(self) -> float:
        """PT: primeira menos segunda / EN: first minus second"""
        return (self.f - self.g) / self.n


def tabela_pareada(primeira: list[bool], segunda: list[bool]) -> Tabela:
    """PT: a tabela de dois vetores de acerto pareados / EN: from paired vectors"""
    if len(primeira) != len(segunda) or not primeira:
        raise ValueError("vetores pareados precisam ter o mesmo tamanho, maior que zero")
    pares = list(zip(primeira, segunda))
    return Tabela(e=pares.count((True, True)), f=pares.count((True, False)),
                  g=pares.count((False, True)), h=pares.count((False, False)))


# -----------------------------------------------------------------------------
# PT: Testes e intervalos / EN: tests and intervals
# -----------------------------------------------------------------------------

def mcnemar_exato_unilateral(a_favor: int, contra: int) -> float:
    """
    PT: P(Bin(a_favor + contra, 1/2) >= a_favor), exato. Sem discordantes,
        p = 1.
    EN: Exact one-sided binomial p over the discordant pairs; 1 if none.
    """
    n = a_favor + contra
    if n == 0:
        return 1.0
    return float(Fraction(sum(math.comb(n, k) for k in range(a_favor, n + 1)), 2 ** n))


def wilson(acertos: int, n: int, z: float) -> tuple[float, float]:
    """
    PT: As raízes de |m − x/n| = z·sqrt(m(1 − m)/n), o intervalo de score de
        Wilson sem correção de continuidade.
    EN: Wilson score interval without continuity correction.
    """
    p = acertos / n
    centro = (2 * acertos + z * z) / (2 * (n + z * z))
    meia = z * math.sqrt(z * z + 4 * acertos * (1 - p)) / (2 * (n + z * z))
    return max(0.0, centro - meia), min(1.0, centro + meia)


def phi_do_metodo_10(t: Tabela) -> float:
    """
    PT: O φ do método 10: (eh − fg) / sqrt((e+f)(g+h)(e+g)(f+h)), com o
        numerador trocado por max(eh − fg − n/2, 0) quando eh > fg, e 0
        quando o denominador é zero (Newcombe, 1998, p. 2638-2639).
    EN: Method 10's continuity-corrected phi; 0 on a zero denominator.
    """
    denominador = (t.e + t.f) * (t.g + t.h) * (t.e + t.g) * (t.f + t.h)
    if denominador == 0:
        return 0.0
    numerador = t.e * t.h - t.f * t.g
    if numerador > 0:
        numerador = max(numerador - t.n / 2, 0)
    return numerador / math.sqrt(denominador)


def _limites_por_z(t: Tabela, z: float) -> tuple[float, float]:
    """PT: os limites do método 10 para um z / EN: method 10 limits for one z"""
    p1, p2 = (t.e + t.f) / t.n, (t.e + t.g) / t.n
    l1, u1 = wilson(t.e + t.f, t.n, z)
    l2, u2 = wilson(t.e + t.g, t.n, z)
    phi = phi_do_metodo_10(t)
    dl1, du1, dl2, du2 = p1 - l1, u1 - p1, p2 - l2, u2 - p2
    delta = math.sqrt(max(dl1 * dl1 - 2 * phi * dl1 * du2 + du2 * du2, 0.0))
    epsilon = math.sqrt(max(du1 * du1 - 2 * phi * du1 * dl2 + dl2 * dl2, 0.0))
    return t.diferenca - delta, t.diferenca + epsilon


def newcombe_pareado(t: Tabela, confianca: float = CONFIANCA_DO_EFEITO) -> tuple[float, float]:
    """
    PT: O intervalo bilateral de Newcombe (método 10) para a diferença
        pareada, primeira menos segunda.
    EN: Newcombe's two-sided method 10 interval for the paired difference.
    """
    return _limites_por_z(t, _NORMAL.inv_cdf(1 - (1 - confianca) / 2))


def p_de_nao_inferioridade(t: Tabela, margem: float = MARGEM_DE_NAO_INFERIORIDADE) -> float:
    """
    PT: O menor α a partir do qual o limite inferior unilateral de 1 − α (o
        inferior do bilateral de 1 − 2α) fica acima da margem em todo α
        maior. Em z: o primeiro z, subindo de 0, em que o limite inferior
        chega à margem. A busca varre z com passo de 0,01 e afina por
        bisseção. Assim o p é coerente com a regra registrada mesmo se o
        limite inferior não for monótono em z (com φ alto): p < α implica
        não inferior no nível α. Com a diferença na margem ou abaixo dela,
        nenhum α até 0,5 serve, e o p é 1.
    EN: Smallest α from which the one-sided 1 − α lower limit stays above
        the margin for every larger α: the first z, going up from 0, where
        the limit reaches the margin; grid on z, then bisection. p < α
        implies non-inferiority at α even if the limit is not monotone in
        z. 1 if the estimate is at or below the margin.
    """
    if t.diferenca <= margem:
        return 1.0

    def acima(z: float) -> bool:
        return _limites_por_z(t, z)[0] > margem

    passos = int(round(Z_MAXIMO / PASSO_DA_VARREDURA_EM_Z))
    baixo = None
    for i in range(1, passos + 1):
        z = i * PASSO_DA_VARREDURA_EM_Z
        if not acima(z):
            baixo = z - PASSO_DA_VARREDURA_EM_Z
            break
    if baixo is None:
        return _NORMAL.cdf(-Z_MAXIMO)
    alto = baixo + PASSO_DA_VARREDURA_EM_Z
    while alto - baixo > TOLERANCIA_DA_BISSECAO:
        meio = (baixo + alto) / 2
        if acima(meio):
            baixo = meio
        else:
            alto = meio
    return _NORMAL.cdf(-baixo)


def holm(ps: dict[str, float]) -> dict[str, float]:
    """
    PT: Os p ajustados de Holm: em ordem crescente (empate pelo nome),
        p_(i) vezes (m − i + 1), com máximo acumulado e teto de 1.
    EN: Holm-adjusted p values, step-down with running maximum.
    """
    ordem = sorted(ps, key=lambda nome: (ps[nome], nome))
    m, ajustados, acumulado = len(ps), {}, 0.0
    for i, nome in enumerate(ordem):
        acumulado = max(acumulado, min(1.0, (m - i) * ps[nome]))
        ajustados[nome] = acumulado
    return {nome: ajustados[nome] for nome in ps}


def q_de_cochran(matriz: list[list[bool]]) -> dict:
    """
    PT: O Q de Cochran de uma matriz perguntas × condições, com o p pela
        qui-quadrado de k − 1 graus de liberdade. Sem variação dentro das
        perguntas, o Q não se define e sai nulo.
    EN: Cochran's Q over questions × conditions; null when undefined.
    """
    k = len(matriz[0])
    colunas = [sum(linha[j] for linha in matriz) for j in range(k)]
    linhas = [sum(linha) for linha in matriz]
    total = sum(linhas)
    denominador = k * total - sum(r * r for r in linhas)
    if denominador == 0:
        return {"q": None, "graus_de_liberdade": k - 1, "p": None}
    q = (k - 1) * (k * sum(c * c for c in colunas) - total * total) / denominador
    return {"q": q, "graus_de_liberdade": k - 1, "p": float(chi2.sf(q, k - 1))}


def interacao_por_permutacao(diferencas: list[int], no_grupo: list[bool], permutacoes: int,
                             reamostragens: int, seed: int) -> dict:
    """
    PT: A estatística da H5: média de (B − C) no grupo marcado menos a média
        no outro. O p é a parcela das permutações dos rótulos (mesmo tamanho
        dos grupos) com estatística maior ou igual à observada; a comparação
        é feita em inteiros, multiplicando pelos dois tamanhos, sem erro de
        ponto flutuante. O intervalo de 95% é o bootstrap de percentil
        (interpolação linear do NumPy), reamostrando perguntas dentro de
        cada grupo. A permutação e o bootstrap têm cada um o próprio
        gerador com a seed registrada.
    EN: H5 statistic, permutation p (ties count, compared in integers) and
        a within-group percentile bootstrap, each with its own seeded
        generator.
    """
    d = np.asarray(diferencas, dtype=np.int64)
    marcado = np.asarray(no_grupo, dtype=bool)
    n_g, n_o = int(marcado.sum()), int((~marcado).sum())
    total = int(d.sum())

    def escalada(soma_do_grupo: int) -> int:
        # PT: n_o·n_g·(média do grupo − média do outro), em inteiros.
        # EN: the statistic times both group sizes, as an integer.
        return n_o * soma_do_grupo - n_g * (total - soma_do_grupo)

    observada = escalada(int(d[marcado].sum()))
    gerador = np.random.default_rng(seed)
    maiores = 0
    for _ in range(permutacoes):
        ordem = gerador.permutation(len(d))
        if escalada(int(d[ordem[:n_g]].sum())) >= observada:
            maiores += 1

    gerador = np.random.default_rng(seed)
    do_grupo, do_outro = d[marcado], d[~marcado]
    reamostradas = np.empty(reamostragens)
    for i in range(reamostragens):
        reamostradas[i] = (gerador.choice(do_grupo, size=n_g, replace=True).mean()
                           - gerador.choice(do_outro, size=n_o, replace=True).mean())
    inferior, superior = np.percentile(reamostradas, [2.5, 97.5])
    return {
        "estatistica": observada / (n_g * n_o),
        "media_no_grupo": float(do_grupo.mean()),
        "media_no_outro": float(do_outro.mean()),
        "tamanhos": [n_g, n_o],
        "p": maiores / permutacoes,
        "ic95": [float(inferior), float(superior)],
    }


# -----------------------------------------------------------------------------
# PT: A análise de um modelo / EN: one model's analysis
# -----------------------------------------------------------------------------

def _r(x: float | None) -> float | None:
    return None if x is None else round(float(x), CASAS)


def _pp(x: float) -> float:
    """PT: proporção em pontos percentuais / EN: proportion in pp"""
    return round(100 * x, CASAS - 2)


def efeito(t: Tabela) -> dict:
    """
    PT: O tamanho de efeito registrado: a diferença pareada em pontos
        percentuais, com o intervalo de Newcombe de 95%.
    EN: The registered effect size: paired difference in pp with 95% CI.
    """
    inferior, superior = newcombe_pareado(t)
    return {"perguntas": t.n, "tabela": asdict(t), "diferenca_pp": _pp(t.diferenca),
            "ic95_pp": [_pp(inferior), _pp(superior)]}


def comparacoes_registradas(hipoteses: dict) -> list[tuple[str, str]]:
    """
    PT: Os pares das hipóteses, na ordem em que aparecem; a H4 entra como D
        contra B e D contra C.
    EN: The hypotheses' pairs in order; H4 as D vs B and D vs C.
    """
    pares: list[tuple[str, str]] = []
    for h in hipoteses["hipoteses"].values():
        c = h["comparacao"]
        for par in ([(c[0], c[1])] if len(c) == 2 else [(c[0], outra) for outra in c[1:]]):
            if par not in pares:
                pares.append(par)
    return pares


def _acertos(certas: dict[str, dict[str, int]], condicao: str, ids: list[str]) -> list[bool]:
    return [certas[condicao][i] >= MAIORIA for i in ids]


def analisar(certas: dict[str, dict[str, int]], tipos: dict[str, str], hipoteses: dict) -> dict:
    """
    PT: A análise inteira de um modelo. certas[condição][pergunta] é o
        número de execuções certas, de 0 a 5, com tudo julgado; tipos traz
        o tipo de acerto de cada pergunta, na ordem do questions_v3.yml.
        Devolve as condições, o Q de Cochran, as comparações com o efeito
        (também por tipo), as cinco hipóteses, o Holm e a variância, com os
        dados de cada passo para a memória de cálculo.
    EN: One model's full analysis from the 0–5 counts per condition and
        question; returns every intermediate needed for the notebook.
    """
    est = hipoteses["estatistica"]
    alfa = float(est["alfa"])
    ids = list(tipos)
    condicoes = sorted(certas)
    nomes_dos_tipos = list(dict.fromkeys(tipos.values()))

    resumo_das_condicoes = {}
    for c in condicoes:
        acertos = _acertos(certas, c, ids)
        resumo_das_condicoes[c] = {
            "perguntas_certas": sum(acertos),
            "proporcao": _r(sum(acertos) / len(ids)),
            "por_tipo": {t: sum(a for a, i in zip(acertos, ids) if tipos[i] == t) for t in nomes_dos_tipos},
        }

    matriz = [[certas[c][i] >= MAIORIA for c in condicoes] for i in ids]
    omnibus = q_de_cochran(matriz)
    omnibus = {**omnibus, "q": _r(omnibus["q"]), "p": _r(omnibus["p"])}

    comparacoes = []
    for x, y in comparacoes_registradas(hipoteses):
        geral = efeito(tabela_pareada(_acertos(certas, x, ids), _acertos(certas, y, ids)))
        por_tipo = {}
        for t in nomes_dos_tipos:
            sub = [i for i in ids if tipos[i] == t]
            por_tipo[t] = efeito(tabela_pareada(_acertos(certas, x, sub), _acertos(certas, y, sub)))
        comparacoes.append({"comparacao": f"{x}−{y}", "primeira": x, "segunda": y, **geral, "por_tipo": por_tipo})

    # PT: os p exatos, sem arredondar: o Holm, o maior p da H4 e a decisão
    #     usam estes; o arredondamento só vale na saída.
    # EN: exact p values for Holm, the H4 maximum and the decision.
    resultados, exatos = {}, {}
    for nome, h in hipoteses["hipoteses"].items():
        sub = [i for i in ids if tipos[i] in h["tipos_de_acerto"]]
        if h["teste"] == "mcnemar_exato_unilateral":
            x, y = h["comparacao"]
            t = tabela_pareada(_acertos(certas, x, sub), _acertos(certas, y, sub))
            exatos[nome] = mcnemar_exato_unilateral(t.f, t.g)
            resultados[nome] = {"teste": h["teste"], "familia": h["familia"], "comparacao": f"{x}−{y}",
                                "tipos_de_acerto": h["tipos_de_acerto"], **efeito(t),
                                "discordantes_a_favor": t.f, "discordantes_contra": t.g, "p": _r(exatos[nome])}
        elif h["teste"] == "nao_inferioridade_intersecao_uniao":
            d, *outras = h["comparacao"]
            partes, ps = {}, []
            for y in outras:
                t = tabela_pareada(_acertos(certas, d, sub), _acertos(certas, y, sub))
                inferior_90 = newcombe_pareado(t, 0.90)[0]
                ps.append(p_de_nao_inferioridade(t))
                partes[f"{d}−{y}"] = {**efeito(t), "limite_inferior_ic90_pp": _pp(inferior_90),
                                      "nao_inferior": inferior_90 > MARGEM_DE_NAO_INFERIORIDADE, "p": _r(ps[-1])}
            exatos[nome] = max(ps)
            resultados[nome] = {"teste": h["teste"], "familia": h["familia"],
                                "tipos_de_acerto": h["tipos_de_acerto"],
                                "margem_pp": _pp(MARGEM_DE_NAO_INFERIORIDADE), "comparacoes": partes,
                                "p": _r(exatos[nome])}
        elif h["teste"] == "permutacao_unilateral_da_interacao":
            x, y = h["comparacao"]
            grupos = h["grupos"]
            marcado_nome = next(g for g in grupos if g != "valor")
            diferencas = [int(certas[x][i] >= MAIORIA) - int(certas[y][i] >= MAIORIA) for i in sub]
            no_grupo = [tipos[i] in grupos[marcado_nome] for i in sub]
            sim = est["simulacao"]
            r = interacao_por_permutacao(diferencas, no_grupo, int(sim["permutacoes"]),
                                         int(sim["reamostragens_bootstrap"]), int(sim["seed"]))
            exatos[nome] = r["p"]
            resultados[nome] = {"teste": h["teste"], "familia": h["familia"], "comparacao": f"{x}−{y}",
                                "grupos": {marcado_nome: r["tamanhos"][0], "valor": r["tamanhos"][1]},
                                "media_no_grupo_pp": _pp(r["media_no_grupo"]),
                                "media_no_valor_pp": _pp(r["media_no_outro"]),
                                "estatistica_pp": _pp(r["estatistica"]), "p": _r(r["p"]),
                                "ic95_pp": [_pp(r["ic95"][0]), _pp(r["ic95"][1])]}
        else:
            raise ValueError(f"teste desconhecido no registro: {h['teste']}")

    familia = list(est["correcao"]["familia"])
    ajustados = holm({h: exatos[h] for h in familia})
    for nome, r in resultados.items():
        r["p_ajustado"] = _r(ajustados[nome]) if nome in ajustados else None
        decisivo = ajustados.get(nome, exatos[nome])
        r["decisao"] = "sustentada" if decisivo <= alfa else "nao_sustentada"
    holm_passos = [{"hipotese": h, "p": resultados[h]["p"], "multiplicador": len(familia) - i,
                    "p_ajustado": resultados[h]["p_ajustado"]}
                   for i, h in enumerate(sorted(familia, key=lambda h: (exatos[h], h)))]

    return {
        "perguntas": len(ids),
        "condicoes": resumo_das_condicoes,
        "omnibus": omnibus,
        "comparacoes": comparacoes,
        "hipoteses": resultados,
        "holm": {"familia": familia, "alfa": alfa, "passos": holm_passos},
        "variancia": variancia(certas, ids),
    }


def variancia(certas: dict[str, dict[str, int]], ids: list[str]) -> dict:
    """
    PT: A variância registrada (execucao.variancia): por condição, quantas
        perguntas tiveram 0, 1, ..., 5 execuções certas, e a parcela em que
        as 5 concordam (0 ou 5 certas).
    EN: Per condition, the 0–5 distribution and the share where all 5 agree.
    """
    saida = {}
    for c in sorted(certas):
        contagens = [certas[c][i] for i in ids]
        saida[c] = {"distribuicao": [contagens.count(k) for k in range(EXECUCOES_POR_PERGUNTA + 1)],
                    "parcela_em_que_as_5_concordam": _r(sum(k in (0, EXECUCOES_POR_PERGUNTA) for k in contagens)
                                                        / len(ids))}
    return saida
