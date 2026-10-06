"""
PT: Previsão da carteira PJ três meses à frente, com backtest (#27, ADR 0023).

    Para cada recorte (o país, as 13 modalidades e as 27 UFs, sempre a
    carteira ativa PJ), escolhe o modelo pelo backtest entre quatro
    candidatos simples e projeta os três meses seguintes, com intervalo de
    80%. O histórico é curto, 31 meses da V2, e por isso o método é cuidadoso
    com o otimismo:

    - **As origens do backtest se dividem em duas janelas.** A janela de
      escolha decide o modelo de cada recorte; a janela de avaliação, que vem
      depois, mede o erro que é publicado. O erro publicado nunca é o da
      escolha.
    - **A régua é o ingênuo.** O MASE divide o erro pelo erro médio de
      repetir o mês anterior no treino: abaixo de 1, o modelo ganha do
      ingênuo. O MAPE vai junto, por ser fácil de ler, e a cobertura diz se o
      intervalo de 80% cobriu o realizado na avaliação.

    A série vem do mrt_carteira_mensal, pelo OAuth do Databricks, na máquina
    local. O Python só soma a carteira entre UFs e modalidades, sem calcular
    razão (ADR 0007). Os dois arquivos da visão 3 são gravados no formato do
    contrato do dashboard, e o manifesto é refeito.

EN: PJ portfolio forecast three months ahead, with backtest. For each cut
    (country, 13 modalities, 27 states), picks the model by backtest among
    four simple candidates, using a selection window and a later evaluation
    window, so the published error is never the selection error. MASE against
    the naive model, MAPE and 80% interval coverage. Reads the mart through
    Databricks OAuth locally and writes view 3's two contract files.

Uso / Usage:
    uv run python -m scripts.analises.previsao_da_carteira
    uv run python -m scripts.analises.previsao_da_carteira --autoteste
"""

from __future__ import annotations

import argparse
import calendar
import math
import sys
import warnings
from dataclasses import dataclass
from datetime import date

import numpy as np

HORIZONTE = 3
"""PT: meses à frente (Q27) / EN: months ahead"""

NIVEL = 0.80
"""PT: o intervalo da projeção / EN: projection interval level"""

Z = 1.2815515655446004
"""PT: o quantil 90% da normal, para o intervalo de 80% / EN: normal 90% quantile"""

TREINO_MINIMO = 13
"""
PT: o menor treino do backtest: 13 meses dão ao ingênuo sazonal um ano
    inteiro para trás em todos os horizontes / EN: smallest training size
"""

ORIGENS_NA_AVALIACAO = 4
"""
PT: as últimas origens do backtest, que medem o erro publicado; as
    anteriores escolhem o modelo / EN: last origins measure the published error
"""

SAZONALIDADE = 12

CANDIDATOS = ("ingenuo", "deriva", "ingenuo_sazonal", "holt_amortecido")
"""
PT: na ordem de simplicidade, que desempata a escolha: o ingênuo repete o
    último mês; a deriva segue a inclinação média da série; o ingênuo
    sazonal repete o mesmo mês do ano anterior; a suavização exponencial com
    tendência amortecida (Holt) acompanha a tendência e a deixa perder força.
EN: in order of simplicity, which breaks ties.
"""

MARTS = "workspace.bcb_scr_marts"
PROJECAO = "projecao_da_carteira.json"
BACKTEST = "backtest_da_projecao.json"


# -----------------------------------------------------------------------------
# PT: As séries / EN: series
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Serie:
    tipo: str
    """PT: pais, modalidade ou uf / EN: cut type"""
    recorte: str
    """PT: BR, o código da modalidade ou a sigla da UF / EN: cut code"""
    meses: list[str]
    valores: np.ndarray


def montar_series(linhas: list[tuple[str, str, str, float]]) -> list[Serie]:
    """
    PT: As 41 séries a partir das linhas de mês, UF, modalidade e carteira:
        o país soma tudo, cada modalidade soma as UFs, e cada UF soma as
        modalidades. A célula que não existe num mês conta como zero.
    EN: The series from month, state, modality and portfolio rows.
    """
    meses = sorted({mes for mes, _, _, _ in linhas})
    posicao = {mes: i for i, mes in enumerate(meses)}
    somas: dict[tuple[str, str], np.ndarray] = {}

    def somar(chave: tuple[str, str], mes: str, valor: float) -> None:
        somas.setdefault(chave, np.zeros(len(meses)))[posicao[mes]] += valor

    for mes, uf, modalidade, carteira in linhas:
        somar(("pais", "BR"), mes, carteira)
        somar(("modalidade", modalidade), mes, carteira)
        somar(("uf", uf), mes, carteira)
    return [Serie(tipo, recorte, meses, valores) for (tipo, recorte), valores in sorted(somas.items())]


def meses_seguintes(ultimo: str, quantos: int) -> list[str]:
    """PT: os fins de mês seguintes / EN: the following month ends"""
    ano, mes = int(ultimo[:4]), int(ultimo[5:7])
    datas = []
    for _ in range(quantos):
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
        datas.append(date(ano, mes, calendar.monthrange(ano, mes)[1]).isoformat())
    return datas


# -----------------------------------------------------------------------------
# PT: Os candidatos / EN: candidates
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Previsao:
    media: np.ndarray
    inferior: np.ndarray
    superior: np.ndarray


def _normal(media: np.ndarray, desvio: np.ndarray) -> Previsao:
    return Previsao(media, media - Z * desvio, media + Z * desvio)


def _desvio(residuos: np.ndarray, parametros: int) -> float:
    graus = max(len(residuos) - parametros, 1)
    return float(math.sqrt(np.sum(residuos**2) / graus))


def prever(modelo: str, treino: np.ndarray, horizonte: int = HORIZONTE) -> Previsao:
    """
    PT: A previsão de um candidato, com o intervalo de 80%. Os três modelos
        de referência usam o intervalo das fórmulas clássicas, com o desvio
        dos resíduos no treino; o Holt usa o do próprio modelo.
    EN: One candidate's forecast with its 80% interval.
    """
    n = len(treino)
    k = np.arange(1, horizonte + 1)
    if modelo == "ingenuo":
        sigma = _desvio(np.diff(treino), 0)
        return _normal(np.full(horizonte, treino[-1]), sigma * np.sqrt(k))
    if modelo == "deriva":
        inclinacao = (treino[-1] - treino[0]) / (n - 1)
        sigma = _desvio(np.diff(treino) - inclinacao, 1)
        return _normal(treino[-1] + inclinacao * k, sigma * np.sqrt(k * (1 + k / (n - 1))))
    if modelo == "ingenuo_sazonal":
        media = np.array([treino[n - SAZONALIDADE + (h - 1) % SAZONALIDADE] for h in k])
        sigma = _desvio(treino[SAZONALIDADE:] - treino[:-SAZONALIDADE], 0)
        return _normal(media, sigma * np.sqrt((k - 1) // SAZONALIDADE + 1))
    if modelo == "holt_amortecido":
        return _holt_amortecido(treino, horizonte)
    raise ValueError(f"modelo desconhecido: {modelo}")


def _holt_amortecido(treino: np.ndarray, horizonte: int) -> Previsao:
    """
    PT: Suavização exponencial com erro aditivo e tendência aditiva
        amortecida, do statsmodels. A série é dividida pela média antes do
        ajuste, porque a carteira chega a trilhões e atrapalha a otimização,
        e o resultado volta à escala.
    EN: Additive-error, damped additive-trend ETS on a mean-scaled series.
    """
    import pandas as pd
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel

    escala = float(np.mean(treino))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # PT: a previsão do ETSModel pede uma série do pandas, e não um vetor
        # EN: ETSModel's prediction needs a pandas series, not an array
        serie = pd.Series(treino / escala)
        ajuste = ETSModel(serie, error="add", trend="add", damped_trend=True).fit(disp=False)
        quadro = ajuste.get_prediction(start=len(treino), end=len(treino) + horizonte - 1).summary_frame(
            alpha=1 - NIVEL
        )
    return Previsao(
        np.asarray(quadro["mean"]) * escala,
        np.asarray(quadro["pi_lower"]) * escala,
        np.asarray(quadro["pi_upper"]) * escala,
    )


# -----------------------------------------------------------------------------
# PT: O backtest / EN: backtest
# -----------------------------------------------------------------------------


def origens(tamanho: int) -> tuple[list[int], list[int]]:
    """
    PT: Os tamanhos de treino do backtest, divididos em escolha e avaliação.
        Cada origem prevê os três meses seguintes, e a última usa o treino
        que deixa os três meses dentro da série.
    EN: Backtest training sizes, split into selection and evaluation.
    """
    todas = list(range(TREINO_MINIMO, tamanho - HORIZONTE + 1))
    return todas[:-ORIGENS_NA_AVALIACAO], todas[-ORIGENS_NA_AVALIACAO:]


@dataclass(frozen=True)
class Medida:
    mase: float
    mape: float
    cobertura: float


def medir(valores: np.ndarray, modelo: str, tamanhos: list[int]) -> list[Medida]:
    """
    PT: As medidas de um candidato nas origens dadas, uma por horizonte. A
        escala do MASE é o erro médio do ingênuo no treino de cada origem.
    EN: A candidate's measures over the given origins, one per horizon.
    """
    erros: dict[int, list[tuple[float, float, bool]]] = {h: [] for h in range(1, HORIZONTE + 1)}
    for n in tamanhos:
        treino = valores[:n]
        escala = float(np.mean(np.abs(np.diff(treino))))
        previsao = prever(modelo, treino)
        for h in range(1, HORIZONTE + 1):
            real = float(valores[n + h - 1])
            erro = abs(real - float(previsao.media[h - 1]))
            dentro = float(previsao.inferior[h - 1]) <= real <= float(previsao.superior[h - 1])
            erros[h].append((erro / escala, erro / abs(real), dentro))
    return [
        Medida(
            mase=float(np.mean([e[0] for e in erros[h]])),
            mape=float(np.mean([e[1] for e in erros[h]])),
            cobertura=float(np.mean([e[2] for e in erros[h]])),
        )
        for h in range(1, HORIZONTE + 1)
    ]


@dataclass(frozen=True)
class Resultado:
    serie: Serie
    escolhido: str
    na_escolha: dict[str, list[Medida]]
    na_avaliacao: dict[str, list[Medida]]
    projecao: Previsao


def avaliar(serie: Serie) -> Resultado:
    """
    PT: Escolhe o modelo do recorte pelo MASE médio na janela de escolha,
        mede todos os candidatos na janela de avaliação e projeta com o
        escolhido, ajustado na série inteira. O empate fica com o mais simples.
    EN: Picks by mean MASE in the selection window, measures every candidate
        in the evaluation window and forecasts with the chosen one.
    """
    escolha, avaliacao = origens(len(serie.valores))
    na_escolha = {m: medir(serie.valores, m, escolha) for m in CANDIDATOS}
    na_avaliacao = {m: medir(serie.valores, m, avaliacao) for m in CANDIDATOS}
    nota = {m: float(np.mean([medida.mase for medida in na_escolha[m]])) for m in CANDIDATOS}
    escolhido = min(CANDIDATOS, key=lambda m: (nota[m], CANDIDATOS.index(m)))
    return Resultado(serie, escolhido, na_escolha, na_avaliacao, prever(escolhido, serie.valores))


# -----------------------------------------------------------------------------
# PT: Os arquivos da visão 3 / EN: view 3 files
# -----------------------------------------------------------------------------


def _reais(valor: float | None) -> int | None:
    return None if valor is None else int(round(valor))


def _seis(valor: float) -> float:
    return round(valor, 6)


def colunas_da_projecao(resultados: list[Resultado]) -> dict[str, list]:
    """
    PT: Uma linha por recorte e mês: os 31 meses realizados e os 3 projetados.
    EN: One row per cut and month: the actual months and the projected ones.
    """
    colunas: dict[str, list] = {
        nome: []
        for nome in (
            "tipo_de_recorte",
            "recorte",
            "data_base",
            "realizado",
            "projecao",
            "limite_inferior",
            "limite_superior",
            "modelo",
        )
    }
    for r in resultados:
        futuros = meses_seguintes(r.serie.meses[-1], HORIZONTE)
        linhas = [(mes, float(valor), None, None, None) for mes, valor in zip(r.serie.meses, r.serie.valores, strict=True)]
        linhas += [
            (mes, None, float(r.projecao.media[i]), float(r.projecao.inferior[i]), float(r.projecao.superior[i]))
            for i, mes in enumerate(futuros)
        ]
        for mes, realizado, projecao, inferior, superior in linhas:
            colunas["tipo_de_recorte"].append(r.serie.tipo)
            colunas["recorte"].append(r.serie.recorte)
            colunas["data_base"].append(mes)
            colunas["realizado"].append(_reais(realizado))
            colunas["projecao"].append(_reais(projecao))
            colunas["limite_inferior"].append(_reais(inferior))
            colunas["limite_superior"].append(_reais(superior))
            colunas["modelo"].append(r.escolhido)
    return colunas


def colunas_do_backtest(resultados: list[Resultado]) -> dict[str, list]:
    """
    PT: Uma linha por recorte, candidato e horizonte: o MASE na escolha e, na
        avaliação, o MASE, o MAPE e a cobertura do intervalo.
    EN: One row per cut, candidate and horizon.
    """
    colunas: dict[str, list] = {
        nome: []
        for nome in (
            "tipo_de_recorte",
            "recorte",
            "modelo",
            "horizonte",
            "escolhido",
            "mase_na_escolha",
            "mase",
            "mape",
            "cobertura",
        )
    }
    for r in resultados:
        for modelo in sorted(CANDIDATOS):
            for h in range(HORIZONTE):
                colunas["tipo_de_recorte"].append(r.serie.tipo)
                colunas["recorte"].append(r.serie.recorte)
                colunas["modelo"].append(modelo)
                colunas["horizonte"].append(h + 1)
                colunas["escolhido"].append(modelo == r.escolhido)
                colunas["mase_na_escolha"].append(_seis(r.na_escolha[modelo][h].mase))
                colunas["mase"].append(_seis(r.na_avaliacao[modelo][h].mase))
                colunas["mape"].append(_seis(r.na_avaliacao[modelo][h].mape))
                colunas["cobertura"].append(_seis(r.na_avaliacao[modelo][h].cobertura))
    return colunas


def ler_do_mart() -> tuple[str, list[tuple[str, str, str, float]]]:
    """
    PT: A carteira ativa PJ por mês, UF e modalidade, do mrt_carteira_mensal,
        com o mesmo filtro do carteira_mensal_pj.json.
    EN: PJ portfolio by month, state and modality, from the mart.
    """
    from ingestion.databricks import cliente, consultar, warehouse

    w = cliente()
    wid = warehouse(w)
    resultado = consultar(
        w,
        wid,
        f"select cast(data_base as string), uf, codigo_modalidade, sum(carteira_ativa) "
        f"from {MARTS}.mrt_carteira_mensal where cliente = 'PJ' "
        "group by data_base, uf, codigo_modalidade order by data_base, uf, codigo_modalidade",
    )
    linhas = [(mes, uf, codigo, float(carteira)) for mes, uf, codigo, carteira in resultado.linhas]
    return max(mes for mes, _, _, _ in linhas), linhas


def gravar_arquivos(data_base: str, resultados: list[Resultado]) -> None:
    """
    PT: Grava os dois arquivos no formato do contrato e refaz o manifesto,
        que guarda o sha256 deles. A data-base precisa ser a dos outros
        arquivos do site.
    EN: Writes both files in contract format and rebuilds the manifest.
    """
    from scripts.contrato_do_dashboard import DESTINO, carregar_contrato, gravar, texto_de_dados
    from scripts.exportar_dados_do_dashboard import gravar_auxiliares, ler_exportados

    contrato = carregar_contrato()
    gravar(DESTINO / PROJECAO, texto_de_dados(PROJECAO, data_base, colunas_da_projecao(resultados)))
    gravar(DESTINO / BACKTEST, texto_de_dados(BACKTEST, data_base, colunas_do_backtest(resultados)))
    data_dos_outros, textos = ler_exportados(contrato)
    if data_dos_outros != data_base:
        raise SystemExit(
            f"A previsão é de {data_base}, e os outros arquivos, de {data_dos_outros}. "
            "Rode a exportação antes / run the export first."
        )
    gravar_auxiliares(contrato, data_base, textos)


def resumo(resultados: list[Resultado]) -> None:
    """PT: o modelo e o erro de cada recorte / EN: model and error per cut"""
    print(f"\n{'recorte':16} {'modelo':16} {'MASE (aval.) h1 h2 h3':>26} {'ingênuo h1 h2 h3':>22} {'cobertura':>9}")
    for r in resultados:
        escolhido = r.na_avaliacao[r.escolhido]
        ingenuo = r.na_avaliacao["ingenuo"]
        print(
            f"{r.serie.tipo + ' ' + r.serie.recorte:16} {r.escolhido:16} "
            f"{'  '.join(f'{m.mase:5.2f}' for m in escolhido):>26} "
            f"{'  '.join(f'{m.mase:5.2f}' for m in ingenuo):>22} "
            f"{np.mean([m.cobertura for m in escolhido]):9.0%}"
        )


# -----------------------------------------------------------------------------
# PT: Autoteste, sem Databricks / EN: self-test, no Databricks
# -----------------------------------------------------------------------------


def autoteste() -> list[str]:
    """
    PT: Confere o método com séries sintéticas de 31 meses, de comportamento
        conhecido, e a montagem das séries com linhas inventadas.
    EN: Checks the method on synthetic 31-month series of known behavior.
    """
    gerador = np.random.default_rng(27)
    t = np.arange(31)
    meses = [date(2024 + (i // 12), i % 12 + 1, 1).isoformat() for i in range(31)]
    falhas: list[str] = []

    def checar(condicao: bool, mensagem: str) -> None:
        if not condicao:
            falhas.append(mensagem)

    escolha, avaliacao = origens(31)
    checar(len(avaliacao) == ORIGENS_NA_AVALIACAO, "a avaliação não tem as origens previstas")
    checar(max(escolha) < min(avaliacao), "as janelas de escolha e de avaliação se cruzam")
    checar(max(avaliacao) + HORIZONTE == 31, "a última origem não chega ao fim da série")

    tendencia = Serie("teste", "tendencia", meses, 1000 + 10 * t + gerador.normal(0, 3, 31))
    r = avaliar(tendencia)
    checar(r.escolhido in {"deriva", "holt_amortecido"}, f"na tendência, escolheu {r.escolhido}")
    ganho = np.mean([m.mase for m in r.na_avaliacao[r.escolhido]])
    checar(ganho < np.mean([m.mase for m in r.na_avaliacao["ingenuo"]]), "na tendência, não ganhou do ingênuo")

    passeio = Serie("teste", "passeio", meses, 1000 + np.cumsum(gerador.normal(0, 10, 31)))
    r = avaliar(passeio)
    mase = np.mean([m.mase for m in r.na_avaliacao["ingenuo"]])
    checar(0.3 < mase < 3, f"no passeio aleatório, o MASE do ingênuo saiu {mase:.2f}")

    sazonal = Serie("teste", "sazonal", meses, 1000 + 50 * np.sin(2 * np.pi * t / 12) + gerador.normal(0, 2, 31))
    r = avaliar(sazonal)
    nota = {m: np.mean([x.mase for x in r.na_escolha[m]]) for m in CANDIDATOS}
    checar(nota["ingenuo_sazonal"] < nota["ingenuo"], "na série sazonal, o ingênuo sazonal não ganhou do ingênuo")

    for modelo in CANDIDATOS:
        p = prever(modelo, tendencia.valores)
        checar(
            bool(np.all(p.inferior <= p.media) and np.all(p.media <= p.superior)),
            f"{modelo}: o intervalo não contém a média",
        )

    linhas = [
        ("2024-01-31", "SP", "02", 10.0),
        ("2024-01-31", "MG", "02", 5.0),
        ("2024-01-31", "SP", "04", 3.0),
        ("2024-02-29", "SP", "02", 11.0),
        ("2024-02-29", "MG", "04", 2.0),
    ]
    series = {(s.tipo, s.recorte): s.valores for s in montar_series(linhas)}
    pais = series[("pais", "BR")]
    checar(list(pais) == [18.0, 13.0], f"o país não é a soma: {list(pais)}")
    for tipo in ("uf", "modalidade"):
        soma = sum(v for (k, _), v in series.items() if k == tipo)
        checar(list(soma) == list(pais), f"a soma das séries de {tipo} não é o país")
    checar(meses_seguintes("2026-07-31", 3) == ["2026-08-31", "2026-09-30", "2026-10-31"], "meses seguintes errados")
    checar(meses_seguintes("2025-12-31", 2) == ["2026-01-31", "2026-02-28"], "a virada do ano está errada")
    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="confere o método sem Databricks / self-test")
    argumentos = parser.parse_args()

    if argumentos.autoteste:
        falhas = autoteste()
        for falha in falhas:
            print(f"  FALHA: {falha}")
        print("Autoteste da previsão:", "falhou" if falhas else "ok")
        sys.exit(1 if falhas else 0)

    data_base, linhas = ler_do_mart()
    resultados = [avaliar(serie) for serie in montar_series(linhas)]
    resumo(resultados)
    gravar_arquivos(data_base, resultados)
    print(f"\nGravados / written: {PROJECAO}, {BACKTEST} e o manifesto, data-base {data_base}")


if __name__ == "__main__":
    main()
