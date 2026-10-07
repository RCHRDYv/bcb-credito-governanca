"""
PT: Etapas 1 e 2 das tabelas do SIDRA, do IBGE (ingestion/fontes.py,
    TABELAS_SIDRA): a população residente estimada por UF (6579, issue #25)
    e o rendimento médio e a massa de rendimento do trabalho da PNAD
    Contínua (6472 e 6474, issue #38). Grava cada resposta da API como veio,
    em data/raw/ibge/, e converte para Parquet só texto, em
    data/landing/ibge/<nome>/.

    As duas etapas ficam juntas porque os arquivos são pequenos: 27 UFs por
    período e por variável.

    Os períodos pedidos são explícitos. A população pede os anos do projeto.
    A PNAD pede do trimestre anterior ao primeiro mês do SCR até o último
    publicado, lido da API de agregados do IBGE: o SIDRA ignora em silêncio
    um período que ainda não saiu, e a lista explícita deixa a validação
    conferir que nenhum trimestre faltou.

    O SIDRA não informa data de publicação na resposta, então a identidade
    do arquivo é o sha256. Se ele muda e os períodos são os mesmos, o IBGE
    revisou a tabela, e o script avisa. Se entrou período novo, é a
    atualização normal.

    A conversão segue as regras do projeto: sem perda e sem interpretação.
    A primeira linha da resposta é o dicionário das colunas, e não um dado,
    e vira a descrição dos nomes em vez de linha da tabela. O resto entra
    como texto, com os nomes de campo do próprio SIDRA (V, D1C, D1N...).

EN: Steps 1 and 2 for the SIDRA tables: estimated population by state and
    average and total labor income from the PNAD Contínua. Stores each API
    response as is and converts it into text-only Parquet. Periods are
    explicit: the project's years for population, and for the PNAD from the
    quarter before the first SCR month to the latest published one, read
    from IBGE's aggregates API, since SIDRA silently skips unpublished
    periods. The file's identity is the response's sha256: a new hash with
    the same periods means IBGE revised the table.

Uso / Usage:
    uv run python -m ingestion.baixar_ibge
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import urllib.request

import polars as pl

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import (
    ANOS,
    DIR_LANDING_IBGE,
    DIR_RAW_IBGE,
    PRIMEIRO_TRIMESTRE_PNAD,
    SIDRA_PERIODOS,
    SIDRA_URL,
    TABELAS_SIDRA,
    TabelaSidra,
)

UFS = 27

# PT: Marcadores do SIDRA para valor ausente, sigiloso ou não aplicável. Em
#     qualquer variável, eles param a ingestão: o fato precisa de número em
#     toda UF e período.
# EN: SIDRA markers for missing, confidential or not applicable values.
MARCADORES = {"-", "..", "...", "X"}


def ler_json(url: str) -> bytes:
    """
    PT: A resposta, como veio. A API de agregados do IBGE manda gzip mesmo
        sem o pedido aceitar, como a de malhas (ingestion/baixar_malha.py).
    EN: The response, as is. IBGE's aggregates API gzips it even unasked.
    """
    req = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        corpo = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            corpo = gzip.decompress(corpo)
        return corpo


def periodos(tabela: TabelaSidra) -> tuple[list[str], str | None]:
    """
    PT: Os períodos a pedir e a data de modificação do mais recente, como o
        IBGE informa. A população tem os anos do projeto fixos.
    EN: Periods to request and the latest one's modification date.
    """
    if tabela.periodo == "Ano":
        return [str(a) for a in ANOS], None
    publicados = json.loads(ler_json(SIDRA_PERIODOS.format(tabela=tabela.tabela)))
    escolhidos = sorted((p for p in publicados if p["id"] >= PRIMEIRO_TRIMESTRE_PNAD), key=lambda p: p["id"])
    return [p["id"] for p in escolhidos], escolhidos[-1]["modificacao"]


def trimestres_contiguos(lista: list[str]) -> bool:
    """PT: AAAATT sem buraco / EN: YYYYQQ with no gap"""
    seguinte = [f"{int(p[:4]) + (p[4:] == '04')}{int(p[4:]) % 4 + 1:02d}" for p in lista[:-1]]
    return seguinte == lista[1:]


def validar(tabela: TabelaSidra, linhas: list[dict], pedidos: list[str]) -> None:
    """PT: estrutura e completude / EN: structure and completeness"""
    esperado_no_dicionario = {
        "V": "Valor",
        "D1C": "Unidade da Federação (Código)",
        "D1N": "Unidade da Federação",
        "D2C": "Variável (Código)",
        "D3C": f"{tabela.periodo} (Código)",
    }
    dicionario, dados = linhas[0], linhas[1:]
    erros = [
        f"campo {k}: esperado '{v}', veio '{dicionario.get(k)}'"
        for k, v in esperado_no_dicionario.items() if dicionario.get(k) != v
    ]
    esperado = UFS * len(tabela.variaveis) * len(pedidos)
    if len(dados) != esperado:
        erros.append(
            f"{len(dados)} linhas, esperado {esperado} "
            f"({UFS} UFs x {len(tabela.variaveis)} variáveis x {len(pedidos)} períodos)"
        )
    if {d["D3C"] for d in dados} != set(pedidos):
        erros.append(f"períodos na resposta: {sorted({d['D3C'] for d in dados})}")
    if {d["D2C"] for d in dados} != set(tabela.variaveis):
        erros.append(f"variáveis na resposta: {sorted({d['D2C'] for d in dados})}")
    if len({d["D1C"] for d in dados}) != UFS:
        erros.append(f"{len({d['D1C'] for d in dados})} UFs na resposta")
    if len({(d["D1C"], d["D2C"], d["D3C"]) for d in dados}) != len(dados):
        erros.append("UF, variável e período repetidos")
    marcados = [d for d in dados if d["V"].strip() in MARCADORES]
    if marcados:
        erros.append(f"{len(marcados)} valores sem número, como {marcados[0]['D1N']} {marcados[0]['D3C']}: '{marcados[0]['V']}'")
    if tabela.periodo == "Trimestre" and (pedidos[0] != PRIMEIRO_TRIMESTRE_PNAD or not trimestres_contiguos(pedidos)):
        erros.append(f"trimestres publicados não começam em {PRIMEIRO_TRIMESTRE_PNAD} ou têm buraco: {pedidos}")
    if erros:
        raise ValueError(f"SIDRA {tabela.tabela}: " + "; ".join(erros))


def ingerir(tabela: TabelaSidra, secao: dict) -> None:
    pedidos, modificacao = periodos(tabela)
    url = SIDRA_URL.format(tabela=tabela.tabela, variaveis=",".join(tabela.variaveis), periodos=",".join(pedidos))
    bruto = ler_json(url)
    novo_hash = hashlib.sha256(bruto).hexdigest()
    linhas = json.loads(bruto)
    validar(tabela, linhas, pedidos)

    anterior = secao.get(tabela.arquivo, {})
    mudou = anterior.get("sha256") != novo_hash
    if anterior and mudou:
        if anterior.get("periodos", pedidos) == pedidos:
            print(f"  ! {tabela.arquivo}: o IBGE revisou a tabela / IBGE revised the table", flush=True)
        else:
            novos = sorted(set(pedidos) - set(anterior.get("periodos", [])))
            print(f"  + {tabela.arquivo}: períodos novos / new periods {novos}", flush=True)

    DIR_RAW_IBGE.mkdir(parents=True, exist_ok=True)
    (DIR_RAW_IBGE / tabela.arquivo).write_bytes(bruto)

    destino = DIR_LANDING_IBGE / tabela.nome / tabela.arquivo.replace(".json", ".parquet")
    destino.parent.mkdir(parents=True, exist_ok=True)
    (
        pl.DataFrame(linhas[1:], schema={k: pl.String for k in linhas[0]})
        .with_columns(
            pl.lit(tabela.arquivo).alias("arquivo_origem"),
            pl.lit(novo_hash).alias("sha256_arquivo"),
        )
        .write_parquet(destino, compression="zstd")
    )

    # PT: A data da extração só muda quando o conteúdo muda, para o manifesto
    #     não ganhar diff numa rodada que baixou a mesma coisa.
    # EN: Extraction date only changes with the content, so a rerun that
    #     fetched the same bytes leaves no manifest diff.
    registro = {
        "tabela": f"ibge_{tabela.nome}",
        "url": url,
        "bytes": len(bruto),
        "sha256": novo_hash,
        "linhas": len(linhas) - 1,
        "periodos": pedidos,
        "data_extracao": dt.date.today().isoformat() if mudou else anterior.get("data_extracao", dt.date.today().isoformat()),
    }
    if modificacao:
        registro["modificacao_no_ibge"] = modificacao
    secao[tabela.arquivo] = registro
    print(
        f"  > {tabela.arquivo}: {len(linhas) - 1} linhas, {pedidos[0]} a {pedidos[-1]}, sha256 {novo_hash[:12]}",
        flush=True,
    )


def main() -> None:
    dados = manifesto.carregar()
    secao = dados.setdefault("ibge", {})
    for tabela in TABELAS_SIDRA:
        ingerir(tabela, secao)
    manifesto.salvar(dados)


if __name__ == "__main__":
    main()
