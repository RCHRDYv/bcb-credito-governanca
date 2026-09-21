"""
PT: Etapa 2. Converte cada CSV mensal dos ZIPs em um Parquet, em
    data/landing/{versao}/{ano}/.

    A conversão é sem perda e sem interpretação:
    - todas as colunas entram como texto, sem trim e sem conversão de tipo.
      A V1 tem valores com espaços à direita e vírgula decimal, e inferência
      de tipo erraria em silêncio. Limpar e tipar é papel do staging no dbt;
    - a única alteração é remover o BOM do UTF-8 do nome da primeira coluna,
      que de outro modo viraria "\\ufeffdata_base";
    - três colunas de linhagem são acrescentadas: arquivo_origem,
      versao_fonte e sha256_zip.

    Cada arquivo é validado antes de ser gravado: número de colunas igual ao
    contrato da fonte, número de linhas igual ao do CSV e uma única
    data_base, coerente com o nome do arquivo.

EN: Step 2. Converts each monthly CSV inside the ZIPs into one Parquet file,
    under data/landing/{version}/{year}/.

    The conversion is lossless and interpretation-free: every column stays
    as text, untrimmed and uncast; the only change is stripping the UTF-8 BOM
    from the first column name; three lineage columns are added. Each file
    is validated (column count, row count, single data_base) before writing.

Uso / Usage:
    uv run python -m ingestion.converter_parquet
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import polars as pl

from ingestion import manifesto
from ingestion.fontes import DIR_LANDING, DIR_RAW, FONTES, Fonte

FONTE_POR_VERSAO = {f.versao: f for f in FONTES}


def ler_csv(bruto: bytes) -> pl.DataFrame:
    """
    PT: Lê o CSV como texto puro. O separador é ";" e há ";" dentro de
        campos entre aspas, que o leitor de CSV respeita.
    EN: Reads the CSV as plain text. The separator is ";" and there are ";"
        inside quoted fields, which the CSV reader honours.
    """
    df = pl.read_csv(io.BytesIO(bruto), separator=";", infer_schema=False, encoding="utf8")
    return df.rename({c: c.lstrip("﻿") for c in df.columns})


def contar_linhas(bruto: bytes) -> int:
    """
    PT: Linhas de dado no CSV original, sem o cabeçalho. Serve de conferência
        independente do leitor: se os dois divergirem, algo foi perdido.
    EN: Data rows in the original CSV, excluding the header. An independent
        check on the reader: if they disagree, something was lost.
    """
    return bruto.rstrip(b"\r\n").count(b"\n")


def validar(df: pl.DataFrame, bruto: bytes, fonte: Fonte, ano_mes: str, entrada: str) -> None:
    """PT: contrato mínimo antes de gravar / EN: minimal contract before writing"""
    erros = []
    if len(df.columns) != fonte.colunas_esperadas:
        erros.append(f"{len(df.columns)} colunas, esperado {fonte.colunas_esperadas}")
    if df.height != contar_linhas(bruto):
        erros.append(f"{df.height} linhas lidas, {contar_linhas(bruto)} no CSV")
    datas = df["data_base"].str.strip_chars().unique().to_list()
    if len(datas) != 1 or datas[0].replace("-", "")[:6] != ano_mes:
        erros.append(f"data_base inesperada: {datas}")
    if erros:
        raise ValueError(f"{entrada}: " + "; ".join(erros))


def ja_convertido(destino: Path, sha_zip: str) -> bool:
    """
    PT: O Parquet existente vale se veio do mesmo ZIP. Se o BCB republicou,
        o sha256 muda e o arquivo é refeito.
    EN: An existing Parquet is valid if it came from the same ZIP. If the BCB
        republished, the sha256 changes and the file is rebuilt.
    """
    if not destino.exists():
        return False
    marca = pl.read_parquet(destino, columns=["sha256_zip"], n_rows=1)
    return marca["sha256_zip"][0] == sha_zip


def converter_zip(nome_zip: str, registro: dict) -> None:
    """PT: converte todos os meses de um ZIP / EN: converts every month of a ZIP"""
    fonte = FONTE_POR_VERSAO[registro["versao"]]
    pasta = DIR_LANDING / fonte.versao / str(registro["ano"])
    pasta.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(DIR_RAW / nome_zip) as z:
        for entrada in sorted(n for n in z.namelist() if n.lower().endswith(".csv")):
            ano_mes = Path(entrada).stem.split("_")[-1]
            destino = pasta / f"{Path(entrada).stem}.parquet"
            if ano_mes in registro["meses"] and ja_convertido(destino, registro["sha256"]):
                print(f"  = {entrada}: já convertido / already converted")
                continue

            bruto = z.read(entrada)
            df = ler_csv(bruto)
            validar(df, bruto, fonte, ano_mes, entrada)
            df = df.with_columns(
                pl.lit(f"{nome_zip}/{entrada}").alias("arquivo_origem"),
                pl.lit(fonte.versao).alias("versao_fonte"),
                pl.lit(registro["sha256"]).alias("sha256_zip"),
            )
            df.write_parquet(destino, compression="zstd")

            registro["meses"][ano_mes] = {"linhas": df.height}
            print(
                f"  > {entrada}: {df.height:,} linhas, "
                f"{len(bruto) / 1e6:,.0f} MB -> {destino.stat().st_size / 1e6:,.1f} MB"
            )


def main() -> None:
    dados = manifesto.carregar()
    if not dados["arquivos"]:
        raise SystemExit("Manifesto vazio: rode ingestion.baixar antes / empty manifest: run ingestion.baixar first")
    for nome_zip, registro in sorted(dados["arquivos"].items()):
        converter_zip(nome_zip, registro)
        # PT: grava a cada ZIP, para não perder o progresso se algo falhar.
        # EN: saves after each ZIP, so progress survives a later failure.
        manifesto.salvar(dados)


if __name__ == "__main__":
    main()
