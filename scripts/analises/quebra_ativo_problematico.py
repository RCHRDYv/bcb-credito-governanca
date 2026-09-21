"""
PT: Mede a quebra do ativo problemático em janeiro de 2025 e os controles
    que impedem atribuí-la só à mudança de definição.

    1. Série mensal de jan/2024 a dez/2025: carteira ativa, carteira
       inadimplida e ativo problemático.
    2. Controle de sazonalidade: a virada dez/2023 para jan/2024.
    3. Decomposição por modalidade da virada dez/2024 para jan/2025.

    Usa a V1 do SCR.data, que cobre 2023 a 2025 com a mesma taxonomia, para
    que nenhuma diferença venha de troca de classificação de modalidade.

    Pré-requisito: planilha_2023.zip, planilha_2024.zip e planilha_2025.zip
    em data/raw/, baixados de https://www.bcb.gov.br/pda/desig/. A pasta está
    no .gitignore e nenhum dado bruto entra no repositório.

EN: Measures the January 2025 problem-asset break and the controls that
    prevent attributing it to the definition change alone.

    1. Monthly series from Jan/2024 to Dec/2025: active portfolio,
       non-performing portfolio and problem assets.
    2. Seasonality control: the Dec/2023 to Jan/2024 turn.
    3. Per-modality breakdown of the Dec/2024 to Jan/2025 turn.

    Uses SCR.data V1, which covers 2023 to 2025 with the same taxonomy, so no
    difference comes from a modality reclassification.

    Prerequisite: planilha_2023.zip, planilha_2024.zip and planilha_2025.zip
    in data/raw/, downloaded from https://www.bcb.gov.br/pda/desig/. The
    folder is gitignored and no raw data enters the repository.

Uso / Usage:
    uv run --with polars python scripts/analises/quebra_ativo_problematico.py
"""

import io
import zipfile
from pathlib import Path

import polars as pl

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
MEDIDAS = ["carteira_ativa", "carteira_inadimplida_arrastada", "ativo_problematico"]
BI = 1e9


# -----------------------------------------------------------------------------
# PT: Leitura
# EN: Reading
# -----------------------------------------------------------------------------

def ler_mes(mes: str) -> pl.DataFrame:
    """
    PT: Lê um CSV mensal da V1 (mes no formato AAAAMM). Tudo entra como
        texto, porque a V1 tem valores com espaços à direita e vírgula
        decimal, e a inferência de tipo erraria em silêncio. O BOM do UTF-8
        é removido do nome da primeira coluna.
    EN: Reads one V1 monthly CSV (mes as YYYYMM). Everything is read as text,
        because V1 has right-padded values and decimal commas, and type
        inference would fail silently. The UTF-8 BOM is stripped from the
        first column name.
    """
    with zipfile.ZipFile(RAW / f"planilha_{mes[:4]}.zip") as z:
        bruto = z.read(f"planilha_{mes}.csv")
    df = pl.read_csv(io.BytesIO(bruto), separator=";", infer_schema=False)
    df = df.rename({c: c.lstrip("﻿").strip() for c in df.columns})
    return df.select(
        pl.col("modalidade").str.strip_chars(),
        *[
            pl.col(m).str.strip_chars().str.replace(",", ".").cast(pl.Float64)
            for m in MEDIDAS
        ],
    )


def por_modalidade(mes: str) -> pl.DataFrame:
    """PT: totais por modalidade / EN: per-modality totals"""
    return ler_mes(mes).group_by("modalidade").agg(*[pl.sum(m) for m in MEDIDAS])


# -----------------------------------------------------------------------------
# PT: Análises
# EN: Analyses
# -----------------------------------------------------------------------------

def serie_mensal(meses: list[str]) -> pl.DataFrame:
    """
    PT: Total do sistema por mês, com as razões e a variação mensal.
        'diferenca' é o ativo problemático que não está em atraso acima de
        90 dias, isto é, a parte que depende do critério de classificação.
    EN: System total per month, with ratios and month-on-month change.
        'diferenca' is the problem-asset amount not overdue beyond 90 days,
        the part that depends on the classification criterion.
    """
    linhas = [por_modalidade(m).sum().with_columns(pl.lit(m).alias("mes")) for m in meses]
    return (
        pl.concat(linhas)
        .select("mes", *MEDIDAS)
        .with_columns(
            (pl.col("carteira_inadimplida_arrastada") / pl.col("carteira_ativa") * 100).alias("inad_pct"),
            (pl.col("ativo_problematico") / pl.col("carteira_ativa") * 100).alias("ap_pct"),
            (pl.col("ativo_problematico") - pl.col("carteira_inadimplida_arrastada")).alias("diferenca"),
            (pl.col("carteira_inadimplida_arrastada").pct_change() * 100).alias("inad_var"),
            (pl.col("ativo_problematico").pct_change() * 100).alias("ap_var"),
        )
    )


def comparar_meses(antes: str, depois: str) -> pl.DataFrame:
    """PT: variação por modalidade entre dois meses / EN: per-modality change"""
    a, d = por_modalidade(antes), por_modalidade(depois)
    return (
        a.join(d, on="modalidade", how="full", coalesce=True, suffix="_depois")
        .fill_null(0)
        .with_columns(
            (pl.col("carteira_inadimplida_arrastada_depois") - pl.col("carteira_inadimplida_arrastada")).alias("d_inad"),
            (pl.col("ativo_problematico_depois") - pl.col("ativo_problematico")).alias("d_ap"),
        )
        .sort("d_ap", descending=True)
    )


# -----------------------------------------------------------------------------
# PT: Relatório
# EN: Report
# -----------------------------------------------------------------------------

def imprimir_serie(serie: pl.DataFrame) -> None:
    print("\n=== SÉRIE MENSAL, V1, R$ bi ===")
    print("  mês      ativa     inad (%)        AP (%)          AP-inad  var inad  var AP")
    for r in serie.iter_rows(named=True):
        print(
            f"  {r['mes']}  {r['carteira_ativa']/BI:>8,.1f}"
            f"  {r['carteira_inadimplida_arrastada']/BI:>6,.1f} ({r['inad_pct']:.2f}%)"
            f"  {r['ativo_problematico']/BI:>6,.1f} ({r['ap_pct']:.2f}%)"
            f"  {r['diferenca']/BI:>7,.1f}"
            f"  {r['inad_var'] or 0:>+7.1f}%  {r['ap_var'] or 0:>+6.1f}%"
        )


def imprimir_comparacao(comp: pl.DataFrame, rotulo: str) -> None:
    tot = comp.select(pl.sum("d_inad"), pl.sum("d_ap"))
    print(f"\n=== {rotulo}, variação em R$ bi ===")
    print(f"  TOTAL  inad {tot['d_inad'][0]/BI:>+6.1f}   AP {tot['d_ap'][0]/BI:>+6.1f}")
    for r in comp.iter_rows(named=True):
        print(
            f"  inad {r['d_inad']/BI:>+6.1f}   AP {r['d_ap']/BI:>+6.1f}"
            f"   (AP {r['ativo_problematico']/BI:.1f} -> {r['ativo_problematico_depois']/BI:.1f})"
            f"   {r['modalidade']}"
        )


def main() -> None:
    meses = [f"{ano}{m:02d}" for ano in (2024, 2025) for m in range(1, 13)]
    imprimir_serie(serie_mensal(meses))
    imprimir_comparacao(comparar_meses("202312", "202401"), "CONTROLE DEZ/2023 -> JAN/2024")
    imprimir_comparacao(comparar_meses("202412", "202501"), "QUEBRA DEZ/2024 -> JAN/2025")


if __name__ == "__main__":
    main()
