"""
PT: Etapas 1 e 2 das séries do SGS do BCB (issue #37). Para cada série de
    SERIES_SGS em ingestion/fontes.py, baixa a resposta da API do início do
    recorte até a data da extração, grava como veio em data/raw/sgs/ e
    converte para Parquet só texto em data/landing/sgs/{nome}/.

    As duas etapas ficam juntas porque cada série é pequena: a meta da Selic
    tem uma linha por dia, cerca de mil desde 2024.

    A data final da consulta é sempre a da extração. Sem ela, a API devolve
    datas no futuro: o SGS repete a meta vigente até a próxima reunião do
    Copom. O dado gravado é exatamente o que a API devolveu para essa
    consulta, e a consulta fica registrada no manifesto.

    O SGS não informa data de publicação, então a identidade do arquivo é o
    sha256 da resposta. Como a data final muda a cada dia, o sha256 também
    muda, e o diff do manifesto mostra quantas linhas entraram.

EN: SGS series steps 1 and 2. For each series in SERIES_SGS, downloads the
    API response from the start of the scope to the extraction date, stores
    it as is and converts it to text-only Parquet. The query always carries
    the extraction date as its end: without it the API returns future dates,
    because SGS repeats the current Selic target until the next Copom
    meeting. SGS reports no publication date, so the file identity is the
    response's sha256.

Uso / Usage:
    uv run python -m ingestion.baixar_sgs
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.request

import polars as pl

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import DIR_LANDING_SGS, DIR_RAW_SGS, SERIES_SGS, SGS_DATA_INICIAL, SGS_URL, SerieSgs


def url_da_consulta(serie: SerieSgs, extracao: dt.date) -> str:
    """PT: consulta do início do recorte até a extração / EN: scope start to extraction"""
    return SGS_URL.format(codigo=serie.codigo, inicio=SGS_DATA_INICIAL, fim=extracao.strftime("%d/%m/%Y"))


def validar(linhas: list[dict], serie: SerieSgs, extracao: dt.date) -> None:
    """
    PT: Estrutura esperada e nenhuma data além da extração. A segunda
        conferência é a que pega a armadilha das datas no futuro, caso a API
        passe a ignorar a data final.
    EN: Expected structure and no date past the extraction, which catches
        the future-dates trap if the API starts ignoring the end date.
    """
    erros = []
    if not linhas:
        erros.append("resposta vazia")
    campos = {tuple(sorted(l)) for l in linhas}
    if campos and campos != {("data", "valor")}:
        erros.append(f"campos inesperados: {campos}")
    futuras = [l["data"] for l in linhas if dt.datetime.strptime(l["data"], "%d/%m/%Y").date() > extracao]
    if futuras:
        erros.append(f"{len(futuras)} datas depois da extração, a primeira {futuras[0]}")
    if erros:
        raise ValueError(f"SGS {serie.codigo} ({serie.nome}): " + "; ".join(erros))


def ingerir(serie: SerieSgs, secao: dict, extracao: dt.date) -> None:
    """PT: baixa, valida, grava o bruto e o Parquet / EN: download, validate, store"""
    url = url_da_consulta(serie, extracao)
    req = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        bruto = resp.read()

    linhas = json.loads(bruto)
    validar(linhas, serie, extracao)
    novo_hash = hashlib.sha256(bruto).hexdigest()
    nome = f"{serie.nome}_{serie.codigo}.json"

    DIR_RAW_SGS.mkdir(parents=True, exist_ok=True)
    (DIR_RAW_SGS / nome).write_bytes(bruto)

    destino = DIR_LANDING_SGS / serie.nome / f"{serie.nome}_{serie.codigo}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    (
        pl.DataFrame(linhas, schema={"data": pl.String, "valor": pl.String})
        .with_columns(
            pl.lit(str(serie.codigo)).alias("codigo_serie"),
            pl.lit(serie.nome).alias("serie"),
            pl.lit(extracao.isoformat()).alias("data_extracao"),
            pl.lit(nome).alias("arquivo_origem"),
            pl.lit(novo_hash).alias("sha256_arquivo"),
        )
        .write_parquet(destino, compression="zstd")
    )

    secao[nome] = {
        "url": url,
        "codigo": serie.codigo,
        "descricao": serie.descricao,
        "data_extracao": extracao.isoformat(),
        "bytes": len(bruto),
        "sha256": novo_hash,
        "linhas": len(linhas),
    }
    print(f"  > {nome}: {len(linhas)} linhas, de {linhas[0]['data']} a {linhas[-1]['data']}", flush=True)


def main() -> None:
    dados = manifesto.carregar()
    secao = dados.setdefault("sgs", {})
    extracao = dt.date.today()
    for serie in SERIES_SGS:
        ingerir(serie, secao, extracao)
    manifesto.salvar(dados)


if __name__ == "__main__":
    main()
