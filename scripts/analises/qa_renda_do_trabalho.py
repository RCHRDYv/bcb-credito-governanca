"""
PT: QA da renda do trabalho (issue #38, ADR 0025), independente do dbt e do
    SQL do gabarito.

    Por que existe: o fato, o teste de completude e o SQL de Q13 e Q15 foram
    escritos juntos, e a #47 congela as respostas. Este script refaz as
    contas por outro caminho: lê do Databricks só somas simples da carteira e
    o fato como está, e faz a junção pelo trimestre, as janelas, a
    correlação e a razão do Brasil em polars.

    O que confere:
    1. **O fato contra a fonte.** Cada UF e trimestre do fato contra o
       Parquet local da ingestão: a UF pelo código do IBGE na ontologia, a
       massa convertida de milhões para reais, os coeficientes de variação e
       o fim do trimestre. Também o grão: uma linha por UF e trimestre.
    2. **A junção com o mês.** Cada mês do SCR com o último trimestre
       encerrado até a data-base, e a regra no limite: o mês que fecha o
       trimestre usa o próprio trimestre.
    3. **A Q13, nas duas leituras e nas duas janelas,** contra as respostas
       geradas.
    4. **A Q15** contra a resposta gerada, UF por UF.

EN: Labor income QA, independent from dbt and from the answer key SQL. It
    reads plain portfolio sums and the fact from Databricks, then redoes the
    quarter join, windows, correlation and national ratio in polars, and
    checks the fact against the local ingestion Parquet.

Uso / Usage:
    uv run python -m scripts.analises.qa_renda_do_trabalho
"""

from __future__ import annotations

import datetime as dt
import json

import polars as pl
import yaml

from ingestion.databricks import cliente, consultar, warehouse
from ingestion.fontes import DIR_LANDING_IBGE, RAIZ

MARTS = "workspace.bcb_scr_marts"
RESPOSTAS = RAIZ / "evaluation" / "gabarito" / "respostas"
TOLERANCIA = 1e-8


def tabela(w, wid: str, sql: str) -> pl.DataFrame:
    r = consultar(w, wid, sql)
    return pl.DataFrame(r.linhas, schema=r.colunas, orient="row")


def resposta(nome: str) -> pl.DataFrame:
    d = json.loads((RESPOSTAS / f"{nome}.json").read_text(encoding="utf-8"))
    return pl.DataFrame(d["linhas"], schema=d["colunas"], orient="row")


def perto(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCIA * max(1.0, abs(a), abs(b))


def conferir_fato(fato: pl.DataFrame) -> list[str]:
    dims = yaml.safe_load((RAIZ / "ontology" / "dimensoes.yml").read_text(encoding="utf-8"))
    uf = next(d for d in dims["dimensoes"] if d["coluna"] == "uf")
    codigo = {str(v["codigo_ibge"]): v["rotulo_no_dado"] for v in uf["valores"]}

    def larga(nome: str, valor: str, cv: str) -> pl.DataFrame:
        return (
            pl.read_parquet(DIR_LANDING_IBGE / nome / "*.parquet")
            .with_columns(pl.col("V").cast(pl.Float64))
            .pivot(on="D2C", index=["D1C", "D3C"], values="V")
            .rename({valor: f"fonte_{nome}", cv: f"fonte_cv_{nome}"})
        )

    fonte = (
        larga("rendimento", "5929", "5937")
        .join(larga("massa", "6288", "6289"), on=["D1C", "D3C"])
        .with_columns(pl.col("D1C").replace_strict(codigo).alias("uf"), pl.col("D3C").cast(pl.Int64).alias("codigo"))
    )
    junto = fato.join(fonte, on=["uf", "codigo"], how="full", coalesce=True)
    fim = pl.date(pl.col("codigo") // 100, (pl.col("codigo") % 100) * 3, 1).dt.month_end()
    erradas = junto.filter(
        pl.col("rendimento_medio").is_null()
        | pl.col("fonte_rendimento").is_null()
        | (pl.col("rendimento_medio") != pl.col("fonte_rendimento"))
        | (pl.col("massa_de_rendimento") != pl.col("fonte_massa") * 1_000_000)
        | (pl.col("cv_rendimento_medio") != pl.col("fonte_cv_rendimento"))
        | (pl.col("cv_massa_de_rendimento") != pl.col("fonte_cv_massa"))
        | (pl.col("fim_do_trimestre") != fim)
    )
    chaves = fato.select("uf", "codigo").unique().height
    print(f"  1. fato: {fato.height} linhas, {chaves} UF x trimestre distintos, "
          f"{fonte.height} na fonte, {erradas.height} divergências")
    problemas = [f"fato: {erradas.height} linhas diferentes da fonte"] if erradas.height else []
    if chaves != fato.height:
        problemas.append("fato: UF e trimestre repetidos")
    return problemas


def trimestre_de_cada_mes(meses: pl.DataFrame, fato: pl.DataFrame) -> pl.DataFrame:
    """PT: junção pelo último trimestre encerrado / EN: as-of join on quarter end"""
    fins = fato.select("fim_do_trimestre", "codigo").unique().sort("fim_do_trimestre")
    return meses.sort("data_base").join_asof(fins, left_on="data_base", right_on="fim_do_trimestre", strategy="backward")


def conferir_juncao(mapa: pl.DataFrame) -> list[str]:
    esperado = {dt.date(2024, 1, 31): 202304, dt.date(2024, 2, 29): 202304, dt.date(2024, 3, 31): 202401,
                dt.date(2024, 4, 30): 202401, dt.date(2026, 7, 31): 202602}
    obtido = dict(mapa.select("data_base", "codigo").iter_rows())
    errados = {m: (c, obtido.get(m)) for m, c in esperado.items() if obtido.get(m) != c}
    sem = mapa.filter(pl.col("codigo").is_null()).height
    print(f"  2. junção: {mapa.height} meses, {sem} sem trimestre, casos de limite "
          f"{'conferem' if not errados else errados}")
    return (["junção: mês sem trimestre"] if sem else []) + ([f"junção: {errados}"] if errados else [])


def conferir_q13(carteira: pl.DataFrame, mapa: pl.DataFrame, fato: pl.DataFrame) -> list[str]:
    ultimo = carteira["data_base"].max()
    inicio_12 = (pl.Series([ultimo]).dt.offset_by("-12mo").dt.month_end())[0]
    renda = fato.select("uf", "codigo", "rendimento_medio")
    problemas = []
    print("  3. Q13:")
    for leitura, filtro in (("pf", pl.col("cliente") == "PF"), ("total", pl.lit(True))):
        por_mes = (
            carteira.filter(filtro)
            .group_by("data_base", "uf")
            .agg(pl.col("inadimplencia").sum(), pl.col("ativa").sum())
            .join(mapa.select("data_base", "codigo"), on="data_base")
            .join(renda, on=["uf", "codigo"])
        )
        gabarito = resposta(f"Q13_{leitura}")
        for janela, corte in (("12 meses", pl.col("data_base") > inicio_12), ("recorte inteiro", pl.lit(True))):
            por_uf = (
                por_mes.filter(corte)
                .group_by("uf")
                .agg(
                    pl.col("rendimento_medio").mean(),
                    (100 * pl.col("inadimplencia").sum() / pl.col("ativa").sum()).alias("taxa"),
                )
            )
            r = por_uf.select(pl.corr("rendimento_medio", "taxa"))[0, 0]
            g = float(gabarito.filter(pl.col("janela") == janela)["correlacao"][0])
            pares = int(gabarito.filter(pl.col("janela") == janela)["pares"][0])
            ok = perto(r, g) and pares == por_uf.height
            print(f"     {leitura}, {janela}: QA {r:.10f}, gabarito {g:.10f}, pares {por_uf.height}/{pares}, "
                  f"{'confere' if ok else 'DIFERE'}")
            if not ok:
                problemas.append(f"Q13 {leitura} {janela}")
    return problemas


def conferir_q15(carteira: pl.DataFrame, mapa: pl.DataFrame, fato: pl.DataFrame) -> list[str]:
    ultimo = carteira["data_base"].max()
    codigo = mapa.filter(pl.col("data_base") == ultimo)["codigo"][0]
    qa = (
        carteira.filter((pl.col("data_base") == ultimo) & (pl.col("cliente") == "PF"))
        .group_by("uf")
        .agg(pl.col("ativa").sum().alias("carteira_pf"))
        .join(fato.filter(pl.col("codigo") == codigo).select("uf", "massa_de_rendimento"), on="uf")
    )
    brasil = qa["carteira_pf"].sum() / qa["massa_de_rendimento"].sum()
    qa = qa.with_columns((pl.col("carteira_pf") / pl.col("massa_de_rendimento")).alias("meses"))
    gabarito = resposta("Q15").with_columns(
        pl.col("meses_de_renda").cast(pl.Float64),
        pl.col("meses_de_renda_no_brasil").cast(pl.Float64),
        (pl.col("acima_da_razao_nacional") == "true").alias("acima"),
    )
    junto = qa.join(gabarito, on="uf", how="full", coalesce=True)
    erradas = [
        linha["uf"] for linha in junto.iter_rows(named=True)
        if linha["meses"] is None or linha["meses_de_renda"] is None
        or not perto(linha["meses"], linha["meses_de_renda"])
        or (linha["meses"] > brasil) != linha["acima"]
    ]
    g_brasil = gabarito["meses_de_renda_no_brasil"][0]
    acima = qa.filter(pl.col("meses") > brasil).height
    print(f"  4. Q15: trimestre {codigo}, Brasil QA {brasil:.8f}, gabarito {g_brasil:.8f}, "
          f"{acima} UFs acima, {len(erradas)} UFs divergentes")
    return ([f"Q15: {erradas}"] if erradas else []) + ([] if perto(brasil, g_brasil) else ["Q15: razão do Brasil"])


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    fato = tabela(w, wid, f"""
        select uf, ano * 100 + trimestre as codigo, fim_do_trimestre,
               cast(rendimento_medio as double) as rendimento_medio,
               cast(massa_de_rendimento as double) as massa_de_rendimento,
               cast(cv_rendimento_medio as double) as cv_rendimento_medio,
               cast(cv_massa_de_rendimento as double) as cv_massa_de_rendimento
        from {MARTS}.fct_renda_do_trabalho
    """).with_columns(
        pl.col("codigo").cast(pl.Int64),
        pl.col("fim_do_trimestre").str.to_date(),
        pl.col("rendimento_medio", "massa_de_rendimento", "cv_rendimento_medio", "cv_massa_de_rendimento").cast(pl.Float64),
    )
    carteira = tabela(w, wid, f"""
        select data_base, uf, cliente,
               cast(sum(carteira_inadimplencia) as double) as inadimplencia,
               cast(sum(carteira_ativa) as double) as ativa
        from {MARTS}.fct_carteira
        group by data_base, uf, cliente
    """).with_columns(pl.col("data_base").str.to_date(), pl.col("inadimplencia", "ativa").cast(pl.Float64))

    mapa = trimestre_de_cada_mes(carteira.select("data_base").unique(), fato)
    problemas = conferir_fato(fato)
    problemas += conferir_juncao(mapa)
    problemas += conferir_q13(carteira, mapa, fato)
    problemas += conferir_q15(carteira, mapa, fato)

    if problemas:
        raise SystemExit("\nQA da renda do trabalho reprovou / labor income QA failed: " + "; ".join(problemas))
    print("\nRenda do trabalho e gabarito conferem / labor income and answer key match.")


if __name__ == "__main__":
    main()
