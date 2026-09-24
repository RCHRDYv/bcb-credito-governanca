"""
PT: Etapa 5. Prova que o bronze no Databricks é o dado publicado pelo BCB,
    sem perda nem alteração, e reporta a reconciliação entre V1 e V2.

    Três checagens:
    1. Linhas por arquivo mensal no bronze iguais às do manifesto, que por sua
       vez foram conferidas contra o CSV original na conversão.
    2. Totais mensais das três medidas principais calculados no Databricks
       iguais aos calculados localmente sobre os mesmos Parquets.
    3. Reconciliação V1 contra V2 na carteira ativa. É informativa e não
       reprova: as duas versões divergem de fato (docs/analise-v1-v2.md).
    4. Linhas por arquivo das fontes externas (CNPJ da Receita e população
       do IBGE, issue #25, séries do SGS, issue #37, e PIX, issue #36) iguais às do
       manifesto, e cada ZIP do CNPJ
       conferido contra a Receita, e não só contra o espelho.

    Sai com código 1 se a checagem 1, a 2 ou a 4 falhar.

EN: Step 5. Proves that bronze on Databricks is the data the BCB published,
    with nothing lost or altered, and reports the V1 versus V2
    reconciliation. Checks 1 and 2 fail the run; check 3 is informational,
    because the two versions do diverge. Check 4 compares the external
    sources' rows per file against the manifest and also fails the run.

Uso / Usage:
    uv run python -m ingestion.verificar_bronze
"""

from __future__ import annotations

import sys

import polars as pl

from ingestion import manifesto
from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import CATALOGO, DIR_LANDING, SCHEMA

# PT: Nome da coluna de inadimplência em cada versão (renomeada na V2, com a
#     mesma definição; ver ontology/metricas.yml).
# EN: Delinquency column name per version (renamed in V2 with the same
#     definition; see ontology/metricas.yml).
MEDIDAS = {
    "v1": ["carteira_ativa", "carteira_inadimplida_arrastada", "ativo_problematico"],
    "v2": ["carteira_ativa", "carteira_inadimplencia", "ativo_problematico"],
}
TOLERANCIA_RELATIVA = 1e-9  # PT: só erro de arredondamento de ponto flutuante / EN: float rounding only


def checar_linhas(w, wid: str, dados: dict) -> list[str]:
    """PT: linhas por arquivo contra o manifesto / EN: rows per file vs manifest"""
    # PT: arquivo_origem tem a forma "scrdata_2024.zip/scrdata_202401.csv".
    # EN: arquivo_origem looks like "scrdata_2024.zip/scrdata_202401.csv".
    esperado = {
        f"{nome_zip}/{nome_zip.split('_')[0]}_{mes}.csv": info["linhas"]
        for nome_zip, reg in dados["arquivos"].items()
        for mes, info in reg["meses"].items()
    }
    obtido = {}
    for versao in MEDIDAS:
        sql = f"SELECT arquivo_origem, count(*) FROM {CATALOGO}.{SCHEMA}.bronze_scr_{versao} GROUP BY 1"
        obtido.update({arq: int(n) for arq, n in executar_sql(w, wid, sql)})

    falhas = [f"{arq}: esperado {n:,}, bronze {obtido.get(arq, 0):,}"
              for arq, n in esperado.items() if obtido.get(arq) != n]
    falhas += [f"{arq}: no bronze mas fora do manifesto" for arq in obtido.keys() - esperado.keys()]
    print(f"  1. linhas: {len(esperado)} arquivos conferidos, {len(falhas)} divergências")
    return falhas


def checar_fontes_externas(w, wid: str, dados: dict) -> list[str]:
    """
    PT: Linhas por arquivo das fontes externas contra o manifesto (issue
        #25). No CNPJ, cada ZIP vira várias partes, e o manifesto guarda o
        total de linhas por ZIP. No IBGE, há um arquivo só.
    EN: Rows per file for the external sources against the manifest. Each
        CNPJ ZIP becomes several parts, and the manifest keeps the total per
        ZIP; IBGE has a single file.
    """
    esperado: dict[tuple[str, str], int] = {}
    for chave, reg in dados.get("cnpj", {}).items():
        conv = reg.get("conversao") or {}
        if conv:
            esperado[(conv["tabela"], f"{chave}/{conv['arquivo_interno']}")] = conv["linhas"]
    for nome, reg in dados.get("ibge", {}).items():
        esperado[("ibge_populacao", nome)] = reg["linhas"]
    for nome, reg in dados.get("sgs", {}).items():
        esperado[("sgs_series", nome)] = reg["linhas"]
    for nome, reg in dados.get("pix", {}).items():
        esperado[("pix_municipio", nome)] = reg["linhas"]

    obtido: dict[tuple[str, str], int] = {}
    for tabela in sorted({t for t, _ in esperado}):
        # PT: as tabelas do CNPJ são registradas sem o prefixo da fonte.
        # EN: CNPJ tables are recorded without the source prefix.
        nome_bronze = tabela if tabela.startswith(("ibge_", "sgs_", "pix_")) else f"cnpj_{tabela}"
        sql = f"SELECT arquivo_origem, count(*) FROM {CATALOGO}.{SCHEMA}.bronze_{nome_bronze} GROUP BY 1"
        obtido.update({(tabela, arq): int(n) for arq, n in executar_sql(w, wid, sql)})

    falhas = [f"{t} {arq}: esperado {n:,}, bronze {obtido.get((t, arq), 0):,}"
              for (t, arq), n in esperado.items() if obtido.get((t, arq)) != n]
    falhas += [f"{t} {arq}: no bronze mas fora do manifesto" for t, arq in obtido.keys() - esperado.keys()]
    # PT: O bronze só confere com a fonte se cada ZIP do CNPJ foi conferido
    #     contra a Receita, e não só contra o espelho de onde veio. Com a
    #     Receita fora do ar, o download segue e marca "pendente", mas esta
    #     verificação não passa até a conferência ser feita (ADR 0009).
    #     Apontado pela revisão do Copilot na PR #42.
    # EN: Bronze only matches the source if every CNPJ ZIP was checked
    #     against Receita, not just the mirror. With Receita down, download
    #     proceeds and marks "pendente", but this check fails until verified.
    pendentes = [chave for chave, reg in dados.get("cnpj", {}).items()
                 if reg.get("conferencia_com_a_receita") != "conferido"]
    falhas += [f"cnpj {chave}: sem conferência com a Receita, só com o espelho" for chave in pendentes]

    total = sum(esperado.values())
    print(f"  4. fontes externas: {len(esperado)} arquivos, {total:,} linhas conferidas, "
          f"{len(pendentes)} sem conferência com a Receita, {len(falhas)} divergências")
    return falhas


def soma_texto(coluna: str) -> str:
    """PT: SQL que converte texto com vírgula decimal e soma / EN: SQL cast-and-sum"""
    return f"sum(cast(replace(trim({coluna}), ',', '.') AS DOUBLE))"


def totais_databricks(w, wid: str, versao: str) -> pl.DataFrame:
    colunas = MEDIDAS[versao]
    sql = (
        f"SELECT trim(data_base), {', '.join(soma_texto(c) for c in colunas)} "
        f"FROM {CATALOGO}.{SCHEMA}.bronze_scr_{versao} GROUP BY 1"
    )
    linhas = executar_sql(w, wid, sql)
    return pl.DataFrame(linhas, schema=["data_base", *colunas], orient="row").with_columns(
        [pl.col(c).cast(pl.Float64) for c in colunas]
    )


def totais_locais(versao: str) -> pl.DataFrame:
    colunas = MEDIDAS[versao]
    return (
        pl.scan_parquet(DIR_LANDING / versao / "*" / "*.parquet")
        .group_by(pl.col("data_base").str.strip_chars())
        .agg([pl.col(c).str.strip_chars().str.replace(",", ".").cast(pl.Float64).sum() for c in colunas])
        .collect()
    )


def checar_totais(w, wid: str) -> tuple[list[str], dict[str, pl.DataFrame]]:
    """PT: totais mensais Databricks contra local / EN: monthly totals vs local"""
    falhas, por_versao = [], {}
    for versao, colunas in MEDIDAS.items():
        remoto = totais_databricks(w, wid, versao)
        local = totais_locais(versao)
        comp = local.join(remoto, on="data_base", how="full", suffix="_db", coalesce=True)
        for c in colunas:
            dif = comp.filter(
                ((pl.col(c) - pl.col(f"{c}_db")).abs() / pl.col(c).abs() > TOLERANCIA_RELATIVA)
                | pl.col(f"{c}_db").is_null() | pl.col(c).is_null()
            )
            falhas += [f"{versao} {r['data_base']} {c}: local {r[c]}, bronze {r[f'{c}_db']}"
                       for r in dif.iter_rows(named=True)]
        por_versao[versao] = remoto
        print(f"  2. totais {versao}: {comp.height} meses x {len(colunas)} medidas conferidos")
    return falhas, por_versao


def reconciliar(por_versao: dict[str, pl.DataFrame]) -> None:
    """PT: informativo, V1 contra V2 / EN: informational, V1 vs V2"""
    rec = (
        por_versao["v1"].select("data_base", pl.col("carteira_ativa").alias("v1"))
        .join(por_versao["v2"].select("data_base", pl.col("carteira_ativa").alias("v2")), on="data_base")
        .sort("data_base")
        .with_columns(((pl.col("v2") / pl.col("v1") - 1) * 100).alias("dif_pct"))
    )
    print("  3. reconciliação V1 x V2, carteira ativa (informativa):")
    for r in rec.iter_rows(named=True):
        print(f"     {r['data_base']}  V1 {r['v1'] / 1e9:>9,.1f}  V2 {r['v2'] / 1e9:>9,.1f}  V2/V1 {r['dif_pct']:+.2f}%")


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    dados = manifesto.carregar()

    falhas = checar_linhas(w, wid, dados)
    falhas_totais, por_versao = checar_totais(w, wid)
    falhas += falhas_totais
    reconciliar(por_versao)
    falhas += checar_fontes_externas(w, wid, dados)

    if falhas:
        print("\nFALHOU / FAILED:")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)
    print("\nBronze confere com a fonte / bronze matches the source.")


if __name__ == "__main__":
    main()
