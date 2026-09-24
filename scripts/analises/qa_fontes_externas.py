"""
PT: QA das fontes externas por UF (issue #25), independente do dbt.

    Por que existe: a reconstrução do estoque de empresas ativas (ADR 0009) é
    a regra mais delicada do projeto, e o modelo e o teste do dbt foram
    escritos juntos. Este script refaz a mesma reconstrução por outro
    caminho, em polars e sobre os Parquets locais, sem Databricks. Se os dois
    derem o mesmo número, a regra está certa; se derem números diferentes, um
    dos dois tem erro.

    O que confere:
    1. **A data de corte de cada retrato.** A data mais recente que aparece
       no próprio retrato, que pode ir um dia além da do nome do arquivo.
    2. **A identidade no retrato mais recente.** A reconstrução, na data de
       corte dele, precisa bater exatamente com a contagem real, UF por UF.
    3. **O erro nos retratos antigos.** Real contra reconstruído, no total e
       por UF. É o número que o ADR 0009 declara como limite.
    4. **Casos que a regra não sabe situar.** Matriz não ativa sem data de
       saída e matriz ativa sem data de início.
    5. **A população.** A soma das UFs de cada ano contra o total do Brasil,
       pedido separadamente ao SIDRA.

EN: External sources QA, independent from dbt. It redoes the active-company
    stock reconstruction by another path, in polars over the local Parquet
    files, without Databricks, and checks: each snapshot's effective cutoff
    date; exact identity in the latest snapshot; the error in older
    snapshots, overall and by state; cases the rule cannot place; and that
    state populations add up to the national total SIDRA reports.

Uso / Usage:
    uv run python -m scripts.analises.qa_fontes_externas
"""

from __future__ import annotations

import json
import urllib.request

import polars as pl
import yaml

from ingestion.baixar import CABECALHOS
from ingestion.fontes import DIR_LANDING_CNPJ, DIR_LANDING_IBGE, RAIZ, RETRATO_DO_MODELO

ONTOLOGIA_DIMENSOES = RAIZ / "ontology" / "dimensoes.yml"
SIDRA_BRASIL = "https://apisidra.ibge.gov.br/values/t/6579/n1/all/v/9324/p/{anos}"


def ufs_da_ontologia() -> list[str]:
    """PT: as 27 UFs, lidas da ontologia / EN: the 27 states, from the ontology"""
    dados = yaml.safe_load(ONTOLOGIA_DIMENSOES.read_text(encoding="utf-8"))
    uf = next(d for d in dados["dimensoes"] if d["coluna"] == "uf")
    return [v["rotulo_no_dado"] for v in uf["valores"]]


def data_da_receita(coluna: str) -> pl.Expr:
    """
    PT: Mesma regra da macro data_da_receita do dbt: "0" e "00000000" são
        ausentes, e o resto é AAAAMMDD estrito.
    EN: Same rule as the dbt macro: "0" and "00000000" are missing, the rest
        is strict YYYYMMDD.
    """
    texto = pl.col(coluna).str.strip_chars()
    return pl.when(texto.is_in(["0", "00000000"])).then(None).otherwise(texto).str.to_date("%Y%m%d", strict=True)


def matrizes() -> pl.LazyFrame:
    """PT: matrizes dos três retratos, com datas tipadas / EN: head offices, typed dates"""
    return (
        pl.scan_parquet(DIR_LANDING_CNPJ / "estabelecimentos" / "*" / "*.parquet")
        .filter(pl.col("identificador_matriz_filial") == "1")
        .select(
            "retrato",
            "cnpj_basico",
            "cnpj_ordem",
            "uf",
            "situacao_cadastral",
            data_da_receita("data_situacao_cadastral").alias("data_situacao"),
            data_da_receita("data_inicio_atividade").alias("data_inicio"),
        )
    )


def reconstruir(modelo: pl.DataFrame, data: object, ufs: list[str]) -> pl.DataFrame:
    """
    PT: Matrizes ativas por UF numa data, só com o retrato do modelo. A mesma
        regra de int_cnpj_matriz_intervalo, escrita de novo.
    EN: Active head offices by state on a date, from the model snapshot only.
    """
    ativa = pl.col("situacao_cadastral") == "02"
    inicio = pl.when(ativa).then(pl.max_horizontal("data_inicio", "data_situacao")).otherwise(pl.col("data_inicio"))
    fim = pl.when(ativa).then(None).otherwise(pl.col("data_situacao"))
    uma_por_empresa = (
        modelo.sort(ativa.not_(), "data_inicio", "cnpj_ordem", nulls_last=False)
        .unique(subset="cnpj_basico", keep="first", maintain_order=True)
    )
    return (
        uma_por_empresa.filter(pl.col("uf").is_in(ufs))
        .with_columns(inicio.alias("inicio"), fim.alias("fim"))
        .filter(~(~ativa & pl.col("data_situacao").is_null()))
        .filter((pl.col("inicio") <= data) & (pl.col("fim").is_null() | (pl.col("fim") > data)))
        .group_by("uf")
        .agg(pl.len().cast(pl.Int64).alias("reconstruido"))
    )


def conferir_cnpj() -> None:
    ufs = ufs_da_ontologia()
    base = matrizes().collect()

    cortes = base.group_by("retrato").agg(
        pl.max_horizontal("data_inicio", "data_situacao").max().alias("data_de_corte")
    ).sort("retrato")
    print("  1. data de corte de cada retrato:")
    for retrato, corte in cortes.iter_rows():
        print(f"     {retrato}: {corte}")

    modelo = base.filter(pl.col("retrato") == RETRATO_DO_MODELO)
    sem_saida = modelo.filter((pl.col("situacao_cadastral") != "02") & pl.col("data_situacao").is_null()).height
    ativa_sem_inicio = modelo.filter((pl.col("situacao_cadastral") == "02") & pl.col("data_inicio").is_null()).height
    print(f"\n  4. casos sem como situar, retrato {RETRATO_DO_MODELO}: "
          f"{sem_saida:,} não ativas sem data de saída, {ativa_sem_inicio:,} ativas sem início")

    print("\n  2 e 3. real contra reconstruído, na data de corte:")
    for retrato, corte in cortes.iter_rows():
        real = (
            base.filter((pl.col("retrato") == retrato) & (pl.col("situacao_cadastral") == "02") & pl.col("uf").is_in(ufs))
            .group_by("uf").agg(pl.col("cnpj_basico").n_unique().cast(pl.Int64).alias("real"))
        )
        comp = real.join(reconstruir(modelo, corte, ufs), on="uf", how="left").with_columns(
            ((pl.col("reconstruido") - pl.col("real")) / pl.col("real") * 100).alias("erro_pct")
        )
        total_real, total_rec = comp["real"].sum(), comp["reconstruido"].sum()
        pior = comp.sort(pl.col("erro_pct").abs(), descending=True).row(0, named=True)
        print(f"     {retrato}: real {total_real:,}, reconstruído {total_rec:,}, "
              f"erro {(total_rec / total_real - 1) * 100:+.2f}%, por UF de {comp['erro_pct'].min():+.2f}% "
              f"a {comp['erro_pct'].max():+.2f}% (pior: {pior['uf']})")
        if retrato == RETRATO_DO_MODELO and total_real != total_rec:
            print("     FALHA: no retrato do modelo a reconstrução precisa ser exata")


def conferir_populacao() -> None:
    """PT: soma das UFs contra o total do Brasil / EN: states' sum vs national total"""
    ufs = pl.read_parquet(DIR_LANDING_IBGE / "populacao" / "*.parquet")
    anos = sorted(ufs["D3C"].unique().to_list())
    req = urllib.request.Request(SIDRA_BRASIL.format(anos=",".join(anos)), headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        brasil = {linha["D3C"]: int(linha["V"]) for linha in json.loads(resp.read())[1:]}

    print("\n  5. população, soma das UFs contra o total do Brasil:")
    for ano in anos:
        soma = ufs.filter(pl.col("D3C") == ano)["V"].cast(pl.Int64).sum()
        situacao = "confere" if soma == brasil[ano] else f"DIFERE em {soma - brasil[ano]:,}"
        print(f"     {ano}: UFs {soma:,}, Brasil {brasil[ano]:,}, {situacao}")


def main() -> None:
    conferir_cnpj()
    conferir_populacao()


if __name__ == "__main__":
    main()
