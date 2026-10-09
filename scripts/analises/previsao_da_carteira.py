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

    - **Um quinto candidato é de aprendizado de máquina** (ADR 0024, #98): um
      LightGBM global, treinado com as 351 células de UF por modalidade e a
      Selic, cuja previsão é somada para cada recorte. Ele disputa a escolha
      com a mesma regra e nas mesmas origens que os outros quatro.

    A série vem do mrt_carteira_mensal, e a Selic do fct_selic, pelo OAuth do
    Databricks, na máquina local. O Python só soma a carteira entre UFs e
    modalidades, sem calcular razão (ADR 0007). Os três arquivos da visão 3
    são gravados no formato do contrato do dashboard, e o manifesto é refeito.

EN: PJ portfolio forecast three months ahead, with backtest. For each cut
    (country, 13 modalities, 27 states), picks the model by backtest among
    four simple candidates and a global LightGBM trained on the 351
    state-by-modality cells, using a selection window and a later evaluation
    window, so the published error is never the selection error. MASE against
    the naive model, MAPE and 80% interval coverage. Reads the marts through
    Databricks OAuth locally and writes view 3's three contract files.

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
from collections.abc import Callable
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

UNIVARIADOS = ("ingenuo", "deriva", "ingenuo_sazonal", "theta", "holt_amortecido", "arima", "sarimax", "prophet")
"""
PT: os candidatos de uma série só, na ordem de simplicidade: o ingênuo
    repete o último mês; a deriva segue a inclinação média da série; o
    ingênuo sazonal repete o mesmo mês do ano anterior; o Theta (M3)
    combina a tendência com a suavização; a suavização exponencial com
    tendência amortecida (Holt) acompanha a tendência e a deixa perder
    força; o ARIMA escolhe a ordem pelo AICc; o SARIMAX é o ARIMA com a
    Selic defasada; o Prophet é o modelo aditivo do Meta (ADR 0024).
EN: single-series candidates, in order of simplicity.
"""

CANDIDATOS = (*UNIVARIADOS, "combinacao", "lightgbm")
"""
PT: todos os candidatos; a ordem desempata a escolha, e o LightGBM global é
    o menos simples (ADR 0024) / EN: all candidates; order breaks ties
"""

CAMPEAO = "deriva"
"""
PT: o modelo de referência, que só perde a série para um desafiante que
    erre menos com significância (decidido em 2026-10-06, ADR 0024,
    decisão 9) / EN: the reference model, the default champion
"""

SIGNIFICANCIA = 0.10
"""PT: o nível do teste de Diebold-Mariano, com Holm / EN: Diebold-Mariano level, Holm-corrected"""

COMBINADOS = ("deriva", "holt_amortecido", "lightgbm")
"""PT: a combinação é a média simples destes três, fixada antes de rodar / EN: fixed combination members"""

ORDENS_DO_ARIMA = ((0, 1, 0), (1, 1, 0), (0, 1, 1), (1, 1, 1))
"""
PT: a grade do ARIMA, com uma diferença e tendência: a carteira cresce, e
    com 31 pontos um teste de raiz unitária tem pouco poder para escolher d
EN: the ARIMA grid, with one difference and a trend
"""

DEFASAGEM_DA_SELIC = 3
"""
PT: o SARIMAX usa a Selic de três meses antes, já conhecida nos três meses
    projetados / EN: SARIMAX uses the Selic lagged three months
"""

PARAMETROS_DO_PROPHET = {
    "weekly_seasonality": False,
    "daily_seasonality": False,
    "changepoint_prior_scale": 0.01,
    "interval_width": NIVEL,
}
"""PT: fixos antes de rodar; a sazonalidade anual só entra com 24 meses / EN: fixed before running"""

MESES_PARA_SAZONALIDADE_ANUAL = 24

LIMIAR_DA_CELULA = 1e6
"""
PT: a célula com algum mês abaixo de R$ 1 milhão no treino fica fora do
    LightGBM e entra na soma pelo último valor / EN: cells below R$ 1 million
    in any training month stay out of the model
"""

DEFASAGENS = 3
"""PT: variações mensais usadas como variáveis / EN: monthly changes used as features"""

JANELA_DA_TENDENCIA = 12

QUEBRAS_DA_CARTEIRA = ("2025-09-30",)
"""
PT: meses em que a carteira ativa da V2 dá um degrau que não é do crédito:
    a divergência entre V1 e V2 de set/2025 (ontology/dimensoes.yml,
    divergencia_entre_versoes; #19). O LightGBM não treina com exemplo cuja
    janela cruza um desses meses, para não ler o degrau como padrão do mês
    do ano (decidido em 2026-10-06, ADR 0024, decisão 7)
EN: months with a V2 level step that is not credit behavior; LightGBM skips
    training examples whose window crosses them
"""

PARAMETROS_DO_LIGHTGBM = {
    "objective": "regression",
    "num_iterations": 300,
    "learning_rate": 0.03,
    "num_leaves": 15,
    "max_depth": 4,
    "min_data_in_leaf": 40,
    "feature_fraction": 0.8,
    "lambda_l2": 1.0,
    "seed": 27,
    "num_threads": 1,
    "deterministic": True,
    "force_row_wise": True,
    "verbose": -1,
}
"""
PT: fixos, conservadores e escolhidos antes da primeira execução; não são
    ajustados em nenhuma janela (ADR 0024, decisão 4) / EN: fixed, never tuned
"""

VARIAVEIS = (
    "variacao_1",
    "variacao_2",
    "variacao_3",
    "variacao_media",
    "mes_previsto",
    "tamanho",
    "uf",
    "modalidade",
    "selic",
    "variacao_da_selic",
)
CATEGORIAS = ("uf", "modalidade")

MARTS = "workspace.bcb_scr_marts"
PROJECAO = "projecao_da_carteira.json"
BACKTEST = "backtest_da_projecao.json"
TESTES = "testes_da_projecao.json"


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


def prever(
    modelo: str,
    treino: np.ndarray,
    horizonte: int = HORIZONTE,
    meses: list[str] | None = None,
    selic: np.ndarray | None = None,
) -> Previsao:
    """
    PT: A previsão de um candidato de uma série só, com o intervalo de 80%.
        Os três modelos de referência usam o intervalo das fórmulas
        clássicas, com o desvio dos resíduos no treino; os outros, o do
        próprio modelo. O Prophet precisa dos meses, e o SARIMAX, da Selic
        dos mesmos meses do treino.
    EN: One single-series candidate's forecast with its 80% interval.
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
    if modelo == "theta":
        return _theta(treino, horizonte)
    if modelo == "arima":
        return _arima(treino, horizonte)
    if modelo == "sarimax":
        if selic is None:
            raise ValueError("o SARIMAX precisa da Selic")
        return _arima(treino, horizonte, selic[:n])
    if modelo == "prophet":
        if meses is None:
            raise ValueError("o Prophet precisa dos meses")
        return _prophet(treino, horizonte, meses[:n])
    raise ValueError(f"modelo desconhecido: {modelo}")


def _theta(treino: np.ndarray, horizonte: int) -> Previsao:
    """
    PT: O método Theta do statsmodels, sem dessazonalizar enquanto a série
        tiver menos de 36 meses, sobre a série dividida pela média.
    EN: statsmodels' Theta method on a mean-scaled series.
    """
    import pandas as pd
    from statsmodels.tsa.forecasting.theta import ThetaModel

    escala = float(np.mean(treino))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ajuste = ThetaModel(pd.Series(treino / escala), period=SAZONALIDADE, deseasonalize=len(treino) >= 36).fit()
        media = np.asarray(ajuste.forecast(horizonte))
        faixa = np.asarray(ajuste.prediction_intervals(horizonte, alpha=1 - NIVEL))
    return Previsao(media * escala, faixa[:, 0] * escala, faixa[:, 1] * escala)


def _arima(treino: np.ndarray, horizonte: int, selic: np.ndarray | None = None) -> Previsao:
    """
    PT: O ARIMA com a ordem de menor AICc na grade, sobre a série dividida
        pela média. Com a Selic, vira o SARIMAX: a variável externa é a
        Selic de três meses antes, e os três primeiros meses saem do treino,
        porque não têm a Selic defasada. Se nenhuma ordem ajustar, devolve a
        deriva, e isso não acontece nas séries da carteira.
    EN: ARIMA with the lowest-AICc order in the grid; with the Selic, SARIMAX.
    """
    import pandas as pd
    from statsmodels.tsa.arima.model import ARIMA

    escala = float(np.mean(treino))
    y = treino / escala
    externa = futura = None
    if selic is not None:
        d = DEFASAGEM_DA_SELIC
        y = y[d:]
        externa = selic[: len(treino) - d]
        futura = selic[len(treino) - d : len(treino) - d + horizonte]
    melhor = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for ordem in ORDENS_DO_ARIMA:
            try:
                ajuste = ARIMA(pd.Series(y), exog=externa, order=ordem, trend="t").fit()
            except (ValueError, np.linalg.LinAlgError):
                continue
            if np.isfinite(ajuste.aicc) and (melhor is None or ajuste.aicc < melhor.aicc):
                melhor = ajuste
        if melhor is None:
            return prever("deriva", treino, horizonte)
        quadro = melhor.get_forecast(horizonte, exog=futura).summary_frame(alpha=1 - NIVEL)
    return Previsao(
        np.asarray(quadro["mean"]) * escala,
        np.asarray(quadro["mean_ci_lower"]) * escala,
        np.asarray(quadro["mean_ci_upper"]) * escala,
    )


def _prophet(treino: np.ndarray, horizonte: int, meses: list[str]) -> Previsao:
    """
    PT: O Prophet sobre a série dividida pela média, com a sazonalidade anual
        só a partir de 24 meses e poucos pontos de mudança. A semente fixa
        o ajuste e a amostragem da faixa, para a execução se repetir igual.
    EN: Prophet on a mean-scaled series, seeded for reproducibility.
    """
    import logging

    import pandas as pd

    for nome in ("cmdstanpy", "prophet", "prophet.plot"):
        logging.getLogger(nome).disabled = True
    from prophet import Prophet

    escala = float(np.mean(treino))
    quadro = pd.DataFrame({"ds": pd.to_datetime(meses), "y": treino / escala})
    modelo = Prophet(yearly_seasonality=len(treino) >= MESES_PARA_SAZONALIDADE_ANUAL, **PARAMETROS_DO_PROPHET)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo.fit(quadro, seed=27)
        futuro = pd.DataFrame({"ds": pd.to_datetime(meses_seguintes(meses[-1], horizonte))})
        np.random.seed(27)
        previsto = modelo.predict(futuro)
    return Previsao(
        np.asarray(previsto["yhat"]) * escala,
        np.asarray(previsto["yhat_lower"]) * escala,
        np.asarray(previsto["yhat_upper"]) * escala,
    )


def ajustar_quebras(treino: np.ndarray, meses: list[str]) -> np.ndarray:
    """
    PT: Desconta do treino o degrau de cada quebra conhecida da carteira
        (QUEBRAS_DA_CARTEIRA): os meses antes da quebra sobem pelo degrau,
        e a série fica contínua no nível de hoje. O degrau é o excesso da
        variação do mês da quebra sobre a variação mediana dos outros meses
        do treino, medido só com os meses que o treino conhece (ADR 0024,
        decisão 7).
    EN: Removes each known break's level step from the training series,
        lifting the months before it, using only the training months.
    """
    serie = treino.astype(float).copy()
    n = len(serie)
    for quebra in QUEBRAS_DA_CARTEIRA:
        if quebra not in meses[:n]:
            continue
        i = meses.index(quebra)
        anteriores = serie[:-1]
        if i < 2 or np.any(anteriores <= 0):
            continue
        variacao = np.diff(serie) / anteriores
        degrau = (variacao[i - 1] - float(np.median(np.delete(variacao, i - 1)))) * serie[i - 1]
        serie[:i] += degrau
    return serie


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
# PT: O LightGBM global (ADR 0024) / EN: global LightGBM
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Painel:
    meses: list[str]
    celulas: list[tuple[str, str]]
    """PT: (UF, modalidade) / EN: (state, modality)"""
    valores: np.ndarray
    """PT: células por meses, em reais / EN: cells by months"""
    selic: np.ndarray
    """PT: a meta da Selic no fim de cada mês / EN: end-of-month Selic target"""


def montar_painel(linhas: list[tuple[str, str, str, float]], selic: dict[str, float]) -> Painel:
    """
    PT: A carteira de cada célula de UF por modalidade, mês a mês, com a
        Selic do mesmo mês. A célula que não existe num mês conta como zero.
    EN: Each state-by-modality cell's portfolio by month, with the Selic.
    """
    meses = sorted({mes for mes, _, _, _ in linhas})
    celulas = sorted({(uf, modalidade) for _, uf, modalidade, _ in linhas})
    posicao_mes = {mes: i for i, mes in enumerate(meses)}
    posicao_celula = {celula: i for i, celula in enumerate(celulas)}
    valores = np.zeros((len(celulas), len(meses)))
    for mes, uf, modalidade, carteira in linhas:
        valores[posicao_celula[(uf, modalidade)], posicao_mes[mes]] += carteira
    faltam = [mes for mes in meses if mes not in selic]
    if faltam:
        raise SystemExit(f"Selic ausente em / Selic missing for: {faltam}")
    return Painel(meses, celulas, valores, np.array([selic[mes] for mes in meses], dtype=float))


def _variaveis(painel: Painel, ativas: np.ndarray, t: int, h: int, codigos: np.ndarray) -> np.ndarray:
    """
    PT: As variáveis das células ativas no mês t, para prever o mês t + h.
        Só usa meses até t.
    EN: Features of the active cells at month t, to predict month t + h.
    """
    log = np.log(painel.valores[ativas, : t + 1])
    janela = min(t, JANELA_DA_TENDENCIA)
    mes_previsto = (int(painel.meses[t][5:7]) - 1 + h) % 12 + 1
    quantas = len(ativas)
    return np.column_stack(
        [
            log[:, t] - log[:, t - 1],
            log[:, t - 1] - log[:, t - 2],
            log[:, t - 2] - log[:, t - 3],
            (log[:, t] - log[:, t - janela]) / janela,
            np.full(quantas, mes_previsto),
            log[:, t],
            codigos[ativas, 0],
            codigos[ativas, 1],
            np.full(quantas, painel.selic[t]),
            np.full(quantas, painel.selic[t] - painel.selic[t - DEFASAGENS]),
        ]
    )


def cruza_quebra(meses: list[str], t: int, h: int) -> bool:
    """PT: se a janela de t a t + h cruza uma quebra / EN: whether t..t+h crosses a break"""
    return any(meses[t] < quebra <= meses[t + h] for quebra in QUEBRAS_DA_CARTEIRA)


def prever_celulas(painel: Painel, n: int) -> tuple[np.ndarray, dict[str, float]]:
    """
    PT: A previsão de cada célula para os três meses seguintes aos n
        primeiros, com um LightGBM por horizonte, treinado só com esses n
        meses. O alvo é o logaritmo da razão entre o mês previsto e o mês da
        origem, e cada exemplo pesa pelo tamanho da célula. A célula de fora
        do modelo repete o último valor. Devolve também a importância de cada
        variável, pelo ganho, somada nos três horizontes.
    EN: Each cell's forecast for the three months after the first n, one
        LightGBM per horizon trained on those n months only.
    """
    import lightgbm as lgb

    treino = painel.valores[:, :n]
    previsto = np.repeat(treino[:, -1:], HORIZONTE, axis=1)
    ativas = np.flatnonzero(np.all(treino >= LIMIAR_DA_CELULA, axis=1))
    ufs = sorted({uf for uf, _ in painel.celulas})
    modalidades = sorted({m for _, m in painel.celulas})
    codigos = np.array([[ufs.index(uf), modalidades.index(m)] for uf, m in painel.celulas])
    importancia = dict.fromkeys(VARIAVEIS, 0.0)
    for h in range(1, HORIZONTE + 1):
        exemplos = [t for t in range(DEFASAGENS, n - h) if not cruza_quebra(painel.meses, t, h)]
        x = np.vstack([_variaveis(painel, ativas, t, h, codigos) for t in exemplos])
        y = np.concatenate([np.log(treino[ativas, t + h] / treino[ativas, t]) for t in exemplos])
        peso = np.concatenate([treino[ativas, t] for t in exemplos])
        dados = lgb.Dataset(
            x,
            label=y,
            weight=peso / peso.mean(),
            feature_name=list(VARIAVEIS),
            categorical_feature=list(CATEGORIAS),
        )
        modelo = lgb.train(PARAMETROS_DO_LIGHTGBM, dados)
        variacao = modelo.predict(_variaveis(painel, ativas, n - 1, h, codigos))
        previsto[ativas, h - 1] = treino[ativas, -1] * np.exp(variacao)
        ganho = modelo.feature_importance(importance_type="gain")
        for nome, valor in zip(VARIAVEIS, ganho, strict=True):
            importancia[nome] += float(valor)
    return previsto, importancia


def somar_recortes(painel: Painel, por_celula: np.ndarray) -> dict[tuple[str, str], np.ndarray]:
    """
    PT: A soma das células para o país, cada modalidade e cada UF, como em
        montar_series.
    EN: Sums cells into the country, each modality and each state.
    """
    somas: dict[tuple[str, str], np.ndarray] = {}
    for (uf, modalidade), linha in zip(painel.celulas, por_celula, strict=True):
        for chave in (("pais", "BR"), ("modalidade", modalidade), ("uf", uf)):
            somas[chave] = somas.get(chave, 0) + linha
    return somas


def medias_globais(painel: Painel, tamanhos: list[int]) -> tuple[dict[tuple[str, str], dict[int, np.ndarray]], dict]:
    """
    PT: A previsão do LightGBM somada por recorte, em cada tamanho de treino,
        e a importância das variáveis no treino com a série inteira.
    EN: The LightGBM forecast summed by cut for each training size.
    """
    por_recorte: dict[tuple[str, str], dict[int, np.ndarray]] = {}
    importancia: dict[str, float] = {}
    for n in tamanhos:
        por_celula, importancia_n = prever_celulas(painel, n)
        for chave, media in somar_recortes(painel, por_celula).items():
            por_recorte.setdefault(chave, {})[n] = media
        if n == len(painel.meses):
            importancia = importancia_n
    return por_recorte, importancia


# -----------------------------------------------------------------------------
# PT: O backtest / EN: backtest
# -----------------------------------------------------------------------------


def origens(tamanho: int) -> tuple[list[int], list[int]]:
    """
    PT: Os tamanhos de treino do backtest. Cada origem prevê os três meses
        seguintes, e a última usa o treino que deixa os três meses dentro da
        série. Todas as origens decidem o campeão (ADR 0024, decisão 9); as
        últimas são os testes recentes, que o arquivo dos testes e a tela
        mostram.
    EN: Backtest training sizes; all of them pick the champion, and the last
        ones are the recent tests the screen shows.
    """
    todas = list(range(TREINO_MINIMO, tamanho - HORIZONTE + 1))
    return todas[:-ORIGENS_NA_AVALIACAO], todas[-ORIGENS_NA_AVALIACAO:]


@dataclass(frozen=True)
class Medida:
    mase: float
    mape: float
    cobertura: float
    escore: float
    """PT: o interval score dividido pelo realizado / EN: interval score over the actual"""


@dataclass(frozen=True)
class Teste:
    """PT: o erro de um candidato numa origem e num horizonte / EN: one origin and horizon"""

    escalado: float
    relativo: float
    dentro: bool
    escore: float


Previsor = Callable[[int], Previsao]
"""PT: a previsão a partir dos n primeiros meses / EN: forecast from the first n months"""


def previsor_univariado(modelo: str, serie: Serie, selic: np.ndarray | None) -> Previsor:
    """
    PT: Um candidato de uma série só, treinado na série sem o degrau das
        quebras, medido só com os meses que o treino conhece.
    EN: A single-series candidate trained on the break-adjusted series.
    """
    return lambda n: prever(
        modelo, ajustar_quebras(serie.valores[:n], serie.meses), meses=serie.meses[:n], selic=selic
    )


def previsor_global(valores: np.ndarray, medias: dict[int, np.ndarray], tamanhos: list[int]) -> Previsor:
    """
    PT: O LightGBM de um recorte. A faixa de 80% de cada origem sai dos erros
        relativos dele nas origens que já tinham terminado antes dela, até o
        quantil de 80% em cada horizonte. Com menos de quatro, a faixa usa o
        desvio das variações mensais do treino. A faixa é simétrica, contém
        a previsão e nunca encolhe de um mês para o seguinte (ADR 0024,
        decisão 5).
    EN: One cut's LightGBM, with the 80% band from its errors at origins that
        were complete before each one.
    """

    def prever_n(n: int) -> Previsao:
        media = medias[n]
        anteriores = [m for m in tamanhos if m + HORIZONTE <= n]
        if len(anteriores) >= 4:
            faixa = [
                float(np.quantile([abs(valores[m + h] / medias[m][h] - 1) for m in anteriores], NIVEL))
                for h in range(HORIZONTE)
            ]
        else:
            treino = valores[:n]
            desvio = float(np.std(np.diff(treino) / treino[:-1]))
            faixa = [Z * desvio * math.sqrt(h + 1) for h in range(HORIZONTE)]
        faixa = np.maximum.accumulate(faixa)
        return Previsao(media, media * (1 - faixa), media * (1 + faixa))

    return prever_n


def previsor_combinado(membros: list[Previsor]) -> Previsor:
    """
    PT: A combinação: a média simples das previsões e dos limites dos membros
        (COMBINADOS), fixada antes de rodar.
    EN: The combination: simple mean of members' forecasts and bounds.
    """

    def prever_n(n: int) -> Previsao:
        previsoes = [membro(n) for membro in membros]
        return Previsao(
            np.mean([p.media for p in previsoes], axis=0),
            np.mean([p.inferior for p in previsoes], axis=0),
            np.mean([p.superior for p in previsoes], axis=0),
        )

    return prever_n


def testar(serie: Serie, previsor: Previsor, tamanhos: list[int]) -> dict[int, list[Teste]]:
    """
    PT: O erro de um candidato em cada origem e horizonte. A escala do MASE
        é o erro médio do ingênuo no treino da origem, na série sem o degrau
        das quebras, a mesma para todos os candidatos.
    EN: A candidate's error at each origin and horizon.
    """
    alfa = 1 - NIVEL
    resultado: dict[int, list[Teste]] = {}
    for n in tamanhos:
        escala = float(np.mean(np.abs(np.diff(ajustar_quebras(serie.valores[:n], serie.meses)))))
        previsao = previsor(n)
        testes = []
        for h in range(HORIZONTE):
            real = float(serie.valores[n + h])
            inferior, superior = float(previsao.inferior[h]), float(previsao.superior[h])
            erro = abs(real - float(previsao.media[h]))
            escore = (superior - inferior) + (2 / alfa) * (max(inferior - real, 0) + max(real - superior, 0))
            testes.append(Teste(erro / escala, erro / abs(real), inferior <= real <= superior, escore / abs(real)))
        resultado[n] = testes
    return resultado


def medidas(testes: dict[int, list[Teste]], tamanhos: list[int]) -> list[Medida]:
    """PT: as medidas por horizonte nas origens dadas / EN: per-horizon measures"""
    return [
        Medida(
            mase=float(np.mean([testes[n][h].escalado for n in tamanhos])),
            mape=float(np.mean([testes[n][h].relativo for n in tamanhos])),
            cobertura=float(np.mean([testes[n][h].dentro for n in tamanhos])),
            escore=float(np.mean([testes[n][h].escore for n in tamanhos])),
        )
        for h in range(HORIZONTE)
    ]


def diebold_mariano(diferencas: np.ndarray, horizonte: int = HORIZONTE) -> float:
    """
    PT: O p-valor unilateral do teste de Diebold-Mariano de que o desafiante
        erra menos que o campeão, com a variância de longo prazo de
        Newey-West até a defasagem horizonte - 1 (as origens vizinhas
        dividem meses) e a correção de amostra pequena de Harvey, Leybourne
        e Newbold, contra a t de Student. As diferenças são o erro escalado
        do desafiante menos o do campeão, por origem.
    EN: One-sided Diebold-Mariano p-value that the challenger errs less, with
        Newey-West variance and the Harvey-Leybourne-Newbold correction.
    """
    from scipy.stats import t as student

    d = np.asarray(diferencas, dtype=float)
    tamanho = len(d)
    media = float(d.mean())
    centrada = d - media
    variancia = float(centrada @ centrada) / tamanho
    for k in range(1, horizonte):
        variancia += 2 * float(centrada[k:] @ centrada[:-k]) / tamanho
    if variancia <= 0 or tamanho < 3:
        return 1.0 if media >= 0 else 0.0
    estatistica = media / math.sqrt(variancia / tamanho)
    estatistica *= math.sqrt((tamanho + 1 - 2 * horizonte + horizonte * (horizonte - 1) / tamanho) / tamanho)
    return float(student.cdf(estatistica, tamanho - 1))


def escolher(testes: dict[str, dict[int, list[Teste]]], tamanhos: list[int]) -> tuple[str, dict[str, float]]:
    """
    PT: Campeão e desafiante (ADR 0024, decisão 9). A deriva é o campeão. Um
        desafiante só assume se o teste de Diebold-Mariano, com a correção
        de Holm entre os desafiantes, disser que ele erra menos ao nível
        SIGNIFICANCIA, nas origens dadas. Entre os que passam, fica o de
        menor MASE médio, e o empate vai para o mais simples.
    EN: Champion and challenger: the drift keeps the series unless a
        challenger beats it in a Holm-corrected Diebold-Mariano test.
    """

    def por_origem(modelo: str) -> np.ndarray:
        return np.array([np.mean([x.escalado for x in testes[modelo][n]]) for n in tamanhos])

    campeao = por_origem(CAMPEAO)
    desafiantes = [m for m in CANDIDATOS if m in testes and m != CAMPEAO]
    p = {m: diebold_mariano(por_origem(m) - campeao) for m in desafiantes}
    vencem: list[str] = []
    for posicao, m in enumerate(sorted(desafiantes, key=lambda x: p[x])):
        if p[m] > SIGNIFICANCIA / (len(desafiantes) - posicao):
            break
        vencem.append(m)
    nota = {m: float(por_origem(m).mean()) for m in [CAMPEAO, *vencem]}
    escolhido = min(nota, key=lambda m: (nota[m], CANDIDATOS.index(m)))
    return escolhido, p


@dataclass(frozen=True)
class Resultado:
    serie: Serie
    escolhido: str
    na_escolha: dict[str, list[Medida]]
    """PT: em todas as origens, as que decidem o campeão / EN: all origins, which pick the champion"""
    na_avaliacao: dict[str, list[Medida]]
    """PT: nos testes recentes / EN: recent tests"""
    p_valor: dict[str, float]
    projecao: Previsao
    testes: list[tuple[int, Previsao]]
    """PT: as previsões do escolhido nos testes recentes / EN: chosen model's recent forecasts"""
    erro_honesto: float
    """
    PT: o erro relativo médio do procedimento nos testes recentes, com a
        escolha refeita em cada um só com as origens que já tinham terminado
        antes dele / EN: the procedure's mean relative error on recent tests
    """
    escolhidos_no_procedimento: list[str]


def avaliar(serie: Serie, globais: dict[int, np.ndarray] | None = None, selic: np.ndarray | None = None) -> Resultado:
    """
    PT: Mede todos os candidatos em todas as origens, escolhe pelo campeão e
        desafiante e projeta com o escolhido, ajustado na série inteira.
        Mede também o erro honesto do procedimento nos testes recentes. Sem
        as previsões do LightGBM, a combinação e o LightGBM ficam de fora;
        sem a Selic, o SARIMAX fica de fora.
    EN: Measures every candidate at every origin, picks by champion and
        challenger and forecasts with the chosen one.
    """
    escolha, recentes = origens(len(serie.valores))
    todas = [*escolha, *recentes]
    previsores = {m: previsor_univariado(m, serie, selic) for m in UNIVARIADOS if m != "sarimax" or selic is not None}
    if globais is not None:
        previsores["lightgbm"] = previsor_global(serie.valores, globais, todas)
        previsores["combinacao"] = previsor_combinado([previsores[m] for m in COMBINADOS])
    candidatos = [m for m in CANDIDATOS if m in previsores]
    testes = {m: testar(serie, previsores[m], todas) for m in candidatos}
    escolhido, p_valor = escolher(testes, todas)

    honestos: list[float] = []
    escolhidos: list[str] = []
    for n in recentes:
        anteriores = [m for m in todas if m + HORIZONTE <= n]
        modelo, _ = escolher(testes, anteriores)
        escolhidos.append(modelo)
        honestos += [x.relativo for x in testes[modelo][n]]

    previsor = previsores[escolhido]
    return Resultado(
        serie,
        escolhido,
        {m: medidas(testes[m], todas) for m in candidatos},
        {m: medidas(testes[m], recentes) for m in candidatos},
        p_valor,
        previsor(len(serie.valores)),
        [(n, previsor(n)) for n in recentes],
        float(np.mean(honestos)),
        escolhidos,
    )


def prever_tudo(
    linhas: list[tuple[str, str, str, float]], selic: dict[str, float]
) -> tuple[list[Resultado], dict[str, float]]:
    """
    PT: As 41 séries, com o LightGBM treinado uma vez por origem e somado
        por recorte, e a importância das variáveis no treino final.
    EN: The 41 series, with LightGBM trained once per origin.
    """
    series = montar_series(linhas)
    painel = montar_painel(linhas, selic)
    escolha, recentes = origens(len(painel.meses))
    globais, importancia = medias_globais(painel, [*escolha, *recentes, len(painel.meses)])
    return [avaliar(s, globais[(s.tipo, s.recorte)], painel.selic) for s in series], importancia


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
    PT: Uma linha por recorte, candidato e horizonte: o MASE em todas as
        origens, que decidem o campeão, o p-valor do desafiante contra a
        deriva e, nos testes recentes, o MASE, o MAPE, a cobertura e o
        interval score da faixa.
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
            "p_valor",
            "mase",
            "mape",
            "cobertura",
            "escore_da_faixa",
        )
    }
    for r in resultados:
        for modelo in sorted(r.na_escolha):
            for h in range(HORIZONTE):
                colunas["tipo_de_recorte"].append(r.serie.tipo)
                colunas["recorte"].append(r.serie.recorte)
                colunas["modelo"].append(modelo)
                colunas["horizonte"].append(h + 1)
                colunas["escolhido"].append(modelo == r.escolhido)
                colunas["mase_na_escolha"].append(_seis(r.na_escolha[modelo][h].mase))
                colunas["p_valor"].append(None if modelo == CAMPEAO else _seis(r.p_valor[modelo]))
                colunas["mase"].append(_seis(r.na_avaliacao[modelo][h].mase))
                colunas["mape"].append(_seis(r.na_avaliacao[modelo][h].mape))
                colunas["cobertura"].append(_seis(r.na_avaliacao[modelo][h].cobertura))
                colunas["escore_da_faixa"].append(_seis(r.na_avaliacao[modelo][h].escore))
    return colunas


def colunas_dos_testes(resultados: list[Resultado]) -> dict[str, list]:
    """
    PT: Uma linha por recorte, origem da janela de avaliação e horizonte: o
        que o modelo escolhido previa naquele teste, com a faixa, contra o
        que aconteceu. É o gráfico do erro da Tela 3 (ADR 0024, decisão 6).
    EN: One row per cut, evaluation origin and horizon: what the chosen model
        forecast in that test, against what happened.
    """
    colunas: dict[str, list] = {
        nome: []
        for nome in (
            "tipo_de_recorte",
            "recorte",
            "data_do_teste",
            "horizonte",
            "data_base",
            "realizado",
            "projecao",
            "limite_inferior",
            "limite_superior",
            "modelo",
        )
    }
    for r in resultados:
        for n, previsao in r.testes:
            for h in range(HORIZONTE):
                colunas["tipo_de_recorte"].append(r.serie.tipo)
                colunas["recorte"].append(r.serie.recorte)
                colunas["data_do_teste"].append(r.serie.meses[n - 1])
                colunas["horizonte"].append(h + 1)
                colunas["data_base"].append(r.serie.meses[n + h])
                colunas["realizado"].append(_reais(float(r.serie.valores[n + h])))
                colunas["projecao"].append(_reais(float(previsao.media[h])))
                colunas["limite_inferior"].append(_reais(float(previsao.inferior[h])))
                colunas["limite_superior"].append(_reais(float(previsao.superior[h])))
                colunas["modelo"].append(r.escolhido)
    return colunas


def ler_do_mart() -> tuple[str, list[tuple[str, str, str, float]], dict[str, float]]:
    """
    PT: A carteira ativa PJ por mês, UF e modalidade, do mrt_carteira_mensal,
        com o mesmo filtro do carteira_mensal_pj.json, e a meta da Selic de
        cada mês, do fct_selic.
    EN: PJ portfolio by month, state and modality, from the mart, and the
        monthly Selic target.
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
    selic = consultar(w, wid, f"select cast(data_base as string), selic_meta from {MARTS}.fct_selic")
    return max(mes for mes, _, _, _ in linhas), linhas, {mes: float(valor) for mes, valor in selic.linhas}


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
    gravar(DESTINO / TESTES, texto_de_dados(TESTES, data_base, colunas_dos_testes(resultados)))
    data_dos_outros, textos = ler_exportados(contrato)
    if data_dos_outros != data_base:
        raise SystemExit(
            f"A previsão é de {data_base}, e os outros arquivos, de {data_dos_outros}. "
            "Rode a exportação antes / run the export first."
        )
    gravar_auxiliares(contrato, data_base, textos)


def resumo(resultados: list[Resultado], importancia: dict[str, float]) -> None:
    """
    PT: O campeão de cada recorte, o MASE médio em todas as origens do
        escolhido, da deriva e do melhor desafiante, com o p-valor dele, o
        erro honesto do procedimento e a importância das variáveis do LightGBM.
    EN: Champion per cut, with mean MASE, best challenger p-value and the
        procedure's honest error.
    """

    def nota(r: Resultado, modelo: str) -> float:
        return float(np.mean([m.mase for m in r.na_escolha[modelo]]))

    print(f"\n{'recorte':16} {'escolhido':16} {'nota':>6} {'deriva':>7} {'melhor desafiante':>18} {'nota':>6} {'p':>6} {'honesto':>8}")
    for r in resultados:
        melhor = min((m for m in r.na_escolha if m != CAMPEAO), key=lambda m: nota(r, m))
        print(
            f"{r.serie.tipo + ' ' + r.serie.recorte:16} {r.escolhido:16} {nota(r, r.escolhido):6.2f} "
            f"{nota(r, CAMPEAO):7.2f} {melhor:>18} {nota(r, melhor):6.2f} {r.p_valor[melhor]:6.3f} "
            f"{r.erro_honesto:8.2%}"
        )
    escolhas = {m: sum(r.escolhido == m for r in resultados) for m in CANDIDATOS}
    print("\nescolhidos / chosen:", escolhas)
    print(f"erro honesto médio / honest error: {np.mean([r.erro_honesto for r in resultados]):.2%}")
    total = sum(importancia.values()) or 1.0
    print("importância no LightGBM / importance:", {k: f"{v / total:.0%}" for k, v in sorted(importancia.items(), key=lambda x: -x[1])})


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
    checar(
        r.escolhido == CAMPEAO or r.p_valor[r.escolhido] <= SIGNIFICANCIA,
        f"na tendência, {r.escolhido} assumiu sem vencer o teste",
    )
    ganho = np.mean([m.mase for m in r.na_avaliacao[r.escolhido]])
    checar(ganho < np.mean([m.mase for m in r.na_avaliacao["ingenuo"]]), "na tendência, não ganhou do ingênuo")

    passeio = Serie("teste", "passeio", meses, 1000 + np.cumsum(gerador.normal(0, 10, 31)))
    r = avaliar(passeio)
    mase = np.mean([m.mase for m in r.na_avaliacao["ingenuo"]])
    checar(0.3 < mase < 3, f"no passeio aleatório, o MASE do ingênuo saiu {mase:.2f}")

    sazonal = Serie("teste", "sazonal", meses, 1000 + 50 * np.sin(2 * np.pi * t / 12) + gerador.normal(0, 2, 31))
    r = avaliar(sazonal)
    nota = {m: np.mean([x.mase for x in r.na_escolha[m]]) for m in UNIVARIADOS if m != "sarimax"}
    checar(nota["ingenuo_sazonal"] < nota["ingenuo"], "na série sazonal, o ingênuo sazonal não ganhou do ingênuo")

    selic_teste = np.linspace(10.0, 12.0, 31)
    for modelo in UNIVARIADOS:
        p = prever(modelo, tendencia.valores, meses=meses, selic=selic_teste)
        checar(len(p.media) == HORIZONTE, f"{modelo}: não devolveu três meses")
        checar(
            bool(np.all(p.inferior <= p.media) and np.all(p.media <= p.superior)),
            f"{modelo}: o intervalo não contém a média",
        )

    # PT: o ajuste da quebra tira um degrau sintético em set/2025
    # EN: break adjustment removes a synthetic step
    fins_teste = meses_seguintes("2023-12-31", 31)
    quebra = fins_teste.index(QUEBRAS_DA_CARTEIRA[0])
    crescente = 1000 * 1.01**t + np.where(np.arange(31) >= quebra, 300.0, 0.0)
    ajustada = ajustar_quebras(crescente, fins_teste)
    passos = np.diff(ajustada)
    checar(
        abs(passos[quebra - 1] - np.median(passos)) < 0.2 * np.median(passos),
        f"o ajuste não tirou o degrau da quebra: passo de {passos[quebra - 1]:.1f} contra {np.median(passos):.1f}",
    )
    checar(bool(ajustada[-1] == crescente[-1]), "o ajuste mudou o nível de hoje")
    checar(
        bool(np.array_equal(ajustar_quebras(crescente[:quebra], fins_teste), crescente[:quebra])),
        "o ajuste mexeu antes da quebra existir",
    )

    # PT: Diebold-Mariano, Holm e a escolha
    # EN: Diebold-Mariano, Holm and the choice
    ruido = gerador.normal(0, 0.2, 16)
    checar(diebold_mariano(-0.01 + ruido) > SIGNIFICANCIA, "uma diferença pequena passou no teste")
    checar(diebold_mariano(-1.0 + ruido) < 0.01, "uma diferença grande não passou no teste")
    tamanhos = list(range(16))

    def falsos(erro: float, desvio: float) -> dict[int, list[Teste]]:
        return {n: [Teste(erro + gerador.normal(0, desvio), 0.0, True, 0.0)] * HORIZONTE for n in tamanhos}

    quase = {CAMPEAO: falsos(1.0, 0.1), "theta": falsos(0.98, 0.1)}
    checar(escolher(quase, tamanhos)[0] == CAMPEAO, "um desafiante quase igual tirou o campeão")
    claro = {CAMPEAO: falsos(1.0, 0.1), "theta": falsos(0.98, 0.1), "arima": falsos(0.5, 0.1)}
    checar(escolher(claro, tamanhos)[0] == "arima", "um desafiante claramente melhor não assumiu")
    fixo = lambda valor: (lambda n: Previsao(np.full(3, valor), np.full(3, valor - 1), np.full(3, valor + 1)))  # noqa: E731
    combinada = previsor_combinado([fixo(1.0), fixo(2.0), fixo(6.0)])(10)
    checar(bool(np.allclose(combinada.media, 3.0)), "a combinação não é a média dos membros")

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

    # PT: o LightGBM global num painel sintético de 6 UFs por 5 modalidades,
    #     com tendência própria de cada célula, sazonalidade comum e ruído
    # EN: global LightGBM on a synthetic 6-by-5 panel
    fins = [meses_seguintes("2023-12-31", 31)[i] for i in range(31)]
    linhas_painel = []
    for u in range(6):
        for m in range(5):
            nivel = 1e9 * (1 + u + 2 * m)
            crescimento = 0.004 * (u - m)
            for i, mes in enumerate(fins):
                valor = nivel * np.exp(crescimento * i + 0.04 * np.sin(2 * np.pi * i / 12) + gerador.normal(0, 0.005))
                linhas_painel.append((mes, f"U{u}", f"M{m}", float(valor)))
    linhas_painel += [(mes, "U0", "M9", 1e5 + 100.0 * i) for i, mes in enumerate(fins)]
    selic = {mes: 10.0 + (i // 6) * 0.5 for i, mes in enumerate(fins)}
    painel = montar_painel(linhas_painel, selic)

    previsto, _ = prever_celulas(painel, 20)
    pequena = painel.celulas.index(("U0", "M9"))
    checar(bool(np.all(previsto[pequena] == painel.valores[pequena, 19])), "a célula pequena não repetiu o último valor")
    futuro = painel.valores.copy()
    futuro[:, 20:] *= 3
    alterado = Painel(painel.meses, painel.celulas, futuro, painel.selic * np.r_[np.ones(20), np.full(11, 2.0)])
    checar(bool(np.allclose(prever_celulas(alterado, 20)[0], previsto)), "o LightGBM usou meses depois da origem")

    somas = somar_recortes(painel, painel.valores)
    for s in montar_series(linhas_painel):
        checar(bool(np.allclose(somas[(s.tipo, s.recorte)], s.valores)), f"a soma das células não é a série {s.recorte}")

    escolha_p, recentes_p = origens(31)
    globais, importancia = medias_globais(painel, [*escolha_p, *recentes_p, 31])
    checar(set(importancia) == set(VARIAVEIS), "a importância não cobre as variáveis")
    serie_pais = next(s for s in montar_series(linhas_painel) if s.tipo == "pais")
    pais = avaliar(serie_pais, globais[("pais", "BR")], painel.selic)
    checar({"lightgbm", "combinacao", "sarimax"} <= set(pais.na_escolha), "faltam candidatos no painel")
    for n, p in [*pais.testes, (31, pais.projecao)]:
        checar(bool(np.all(p.inferior <= p.media) and np.all(p.media <= p.superior)), f"lightgbm, origem {n}: faixa fora de ordem")
    nota = {m: np.mean([x.mase for x in pais.na_escolha[m]]) for m in ("lightgbm", "ingenuo")}
    checar(nota["lightgbm"] < nota["ingenuo"], f"no painel sintético, o LightGBM não ganhou do ingênuo: {nota}")
    checar(len(pais.testes) == ORIGENS_NA_AVALIACAO, "os testes não são as origens da avaliação")
    larguras = (pais.projecao.superior - pais.projecao.media) / pais.projecao.media
    checar(bool(np.all(np.diff(larguras) >= -1e-12)), "a faixa encolheu num horizonte mais distante")
    datas = ["2025-07-31", "2025-08-31", "2025-09-30", "2025-10-31"]
    checar(cruza_quebra(datas, 1, 1) and cruza_quebra(datas, 0, 2), "a janela que cruza set/2025 não foi marcada")
    checar(not cruza_quebra(datas, 2, 1) and not cruza_quebra(datas, 0, 1), "a janela que não cruza set/2025 foi marcada")
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

    data_base, linhas, selic = ler_do_mart()
    resultados, importancia = prever_tudo(linhas, selic)
    resumo(resultados, importancia)
    gravar_arquivos(data_base, resultados)
    print(f"\nGravados / written: {PROJECAO}, {BACKTEST}, {TESTES} e o manifesto, data-base {data_base}")


if __name__ == "__main__":
    main()
