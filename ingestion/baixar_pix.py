"""
PT: Etapas 1 e 2 do PIX por município (issue #36). Baixa o recurso
    TransacoesPixPorMunicipio da API OData do BCB, do início do recorte até o
    último mês fechado, um mês por consulta. Grava cada mês como veio em
    data/raw/pix/ e converte o conjunto para Parquet só texto em
    data/landing/pix/municipio/.

    Três cuidados, todos medidos na API em 2026-09-24 (ADR 0011):
    - **o parâmetro DataBase é "a partir de".** Cada consulta filtra o mês
      exato que pede;
    - **o mês corrente vem incompleto,** e fica de fora: só são pedidos os
      meses anteriores ao da extração, e a validação recusa se ele aparecer;
    - **o recurso não aceita paginação.** A documentação o marca como
      "naoPaginavel", e $skip devolve erro 500. Como a resposta inteira passa
      de 100 mil linhas, a consulta é feita mês a mês, com filtro de mês
      exato, e cada mês fica num arquivo bruto próprio.

    Os números vêm como texto, exatamente como estão no JSON: a leitura usa
    parse_float e parse_int que devolvem o texto original, e nenhum valor
    passa por ponto flutuante na conversão.

    Validação antes de gravar: todo mês do recorte presente, e nenhum
    município some de um mês para o seguinte. O conjunto cresce, e isso é
    real: medido em 2026-09-24, Campo Grande e Januário Cicco (RN) só
    aparecem a partir de abr/2025, e Boa Esperança do Norte (MT), município
    novo, a partir de out/2025. Cada entrada é listada na saída.

EN: PIX by municipality steps 1 and 2. Downloads TransacoesPixPorMunicipio
    from BCB's OData API, from the scope start to the last closed month, page
    month by month, storing each month as is and converting the whole to
    text-only Parquet. DataBase means "from", so each query filters its exact
    month; the current month is partial and is not requested; the resource
    rejects paging ($skip returns error 500), so it goes one month per
    query. Numbers are kept as their original JSON text. Validated before
    writing: every month present, and no municipality disappears from one
    month to the next (the set grows, and entries are listed).

Uso / Usage:
    uv run python -m ingestion.baixar_pix
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from collections import Counter

import polars as pl

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import DIR_LANDING_PIX, DIR_RAW_PIX, PIX_INICIO, PIX_PAGINA, PIX_URL

NOME = "pix_municipio"


def mes_da_extracao(extracao: dt.date) -> int:
    """PT: AAAAMM do mês corrente, o primeiro que fica fora / EN: current month, the first excluded"""
    return extracao.year * 100 + extracao.month


def url_do_mes(mes: str) -> str:
    """
    PT: A consulta de um mês. DataBase é o próprio mês, e o filtro corta o
        "a partir de" no mês exato.
    EN: One month's query. DataBase is the month itself, and the filter cuts
        "from" down to the exact month.
    """
    parametros = {
        "@DataBase": f"'{mes}'",
        "$filter": f"AnoMes eq {mes}",
        "$top": str(PIX_PAGINA),
        "$format": "json",
    }
    return f"{PIX_URL}?{urllib.parse.urlencode(parametros, quote_via=urllib.parse.quote)}"


def como_texto(bruto: bytes) -> list[dict]:
    """PT: lê o JSON sem converter número / EN: reads JSON without converting numbers"""
    return json.loads(bruto, parse_float=str, parse_int=str)["value"]


def meses_esperados(fim_exclusivo: int) -> list[str]:
    """PT: todos os AAAAMM do início até o último mês fechado / EN: every month in scope"""
    ano, mes = int(PIX_INICIO[:4]), int(PIX_INICIO[4:])
    meses = []
    while ano * 100 + mes < fim_exclusivo:
        meses.append(f"{ano}{mes:02d}")
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return meses


def validar(linhas: list[dict], fim_exclusivo: int) -> None:
    """PT: recorte completo e estável / EN: complete, stable scope"""
    por_mes = Counter(l["AnoMes"] for l in linhas)
    esperados = meses_esperados(fim_exclusivo)
    erros = []
    faltando = [m for m in esperados if m not in por_mes]
    sobrando = [m for m in por_mes if m not in esperados]
    if faltando:
        erros.append(f"meses faltando: {faltando}")
    if sobrando:
        erros.append(f"meses fora do recorte, como o mês corrente incompleto: {sobrando}")
    municipios: dict[str, set] = {}
    for l in linhas:
        municipios.setdefault(l["AnoMes"], set()).add(l["Municipio_Ibge"])
    meses = sorted(municipios)
    for anterior, atual in zip(meses, meses[1:]):
        saem = municipios[anterior] - municipios[atual]
        entram = municipios[atual] - municipios[anterior]
        if saem:
            erros.append(f"{atual}: somem municípios que existiam em {anterior}: {sorted(saem, key=str)}")
        if entram:
            print(f"  + {atual}: entram {sorted(entram, key=str)}", flush=True)
    if erros:
        raise ValueError("PIX: " + "; ".join(erros))


def main() -> None:
    extracao = dt.date.today()
    fim = mes_da_extracao(extracao)
    DIR_RAW_PIX.mkdir(parents=True, exist_ok=True)
    for velha in DIR_RAW_PIX.glob(f"{NOME}_*.json"):
        velha.unlink()

    linhas: list[dict] = []
    hash_do_conjunto = hashlib.sha256()
    for mes in meses_esperados(fim):
        req = urllib.request.Request(url_do_mes(mes), headers=CABECALHOS)
        with urllib.request.urlopen(req, timeout=300) as resp:
            bruto = resp.read()
        do_mes = como_texto(bruto)
        # PT: uma resposta do tamanho do limite pode ter sido cortada.
        # EN: a response as large as the limit may have been truncated.
        if len(do_mes) >= PIX_PAGINA:
            raise ValueError(f"PIX {mes}: {len(do_mes)} linhas, no limite da consulta; pode estar cortado")
        (DIR_RAW_PIX / f"{NOME}_{mes}.json").write_bytes(bruto)
        hash_do_conjunto.update(bruto)
        linhas += do_mes
        print(f"  {mes}: {len(do_mes):,} municípios", flush=True)

    validar(linhas, fim)
    novo_hash = hash_do_conjunto.hexdigest()

    destino = DIR_LANDING_PIX / "municipio" / f"{NOME}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    colunas = list(linhas[0])
    (
        pl.DataFrame(linhas, schema={c: pl.String for c in colunas})
        .with_columns(
            pl.lit(extracao.isoformat()).alias("data_extracao"),
            pl.lit(f"{NOME}.json").alias("arquivo_origem"),
            pl.lit(novo_hash).alias("sha256_arquivo"),
        )
        .write_parquet(destino, compression="zstd")
    )

    dados = manifesto.carregar()
    dados.setdefault("pix", {})[f"{NOME}.json"] = {
        "url_do_primeiro_mes": url_do_mes(meses_esperados(fim)[0]),
        "data_extracao": extracao.isoformat(),
        "sha256": novo_hash,
        "linhas": len(linhas),
        "meses": len(meses_esperados(fim)),
    }
    manifesto.salvar(dados)
    print(f"  > {NOME}: {len(linhas):,} linhas em {len(meses_esperados(fim))} meses", flush=True)


if __name__ == "__main__":
    main()
