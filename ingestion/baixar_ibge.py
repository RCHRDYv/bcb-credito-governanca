"""
PT: Etapas 1 e 2 da população do IBGE. Baixa a estimativa de população
    residente por UF da tabela 6579 do SIDRA, grava a resposta da API como
    veio, em data/raw/ibge/, e converte para Parquet só texto, em
    data/landing/ibge/populacao/.

    As duas etapas ficam juntas porque o arquivo é pequeno: 27 UFs por ano.

    O SIDRA não informa data de publicação, então a identidade do arquivo é
    o sha256 da resposta. Isso importa: o IBGE revisa estimativas de anos
    anteriores, e uma revisão aparece como sha256 novo no diff do manifesto.

    A conversão segue as regras do projeto: sem perda e sem interpretação.
    A primeira linha da resposta é o dicionário das colunas, e não um dado,
    e vira a descrição dos nomes em vez de linha da tabela. O resto entra
    como texto, com os nomes de campo do próprio SIDRA (V, D1C, D1N...).

EN: IBGE population steps 1 and 2. Downloads the estimated resident
    population by state from SIDRA table 6579, stores the API response as
    is, and converts it into text-only Parquet. SIDRA reports no
    publication date, so the file's identity is the response's sha256; IBGE
    revises past estimates, and a revision shows up as a new sha256 in the
    manifest diff. The response's first row is the column dictionary, not
    data, and is dropped from the table after checking it.

Uso / Usage:
    uv run python -m ingestion.baixar_ibge
"""

from __future__ import annotations

import hashlib
import json
import urllib.request

import polars as pl

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import ANOS_POPULACAO, DIR_LANDING_IBGE, DIR_RAW_IBGE, SIDRA_POPULACAO

NOME = "populacao_6579.json"

# PT: O dicionário que a primeira linha precisa trazer. Se o IBGE mudar a
#     estrutura da tabela, a ingestão para aqui, em vez de gravar colunas
#     trocadas.
# EN: The dictionary the first row must carry. If IBGE changes the table's
#     structure, ingestion stops here instead of writing swapped columns.
DICIONARIO_ESPERADO = {
    "V": "Valor",
    "D1C": "Unidade da Federação (Código)",
    "D1N": "Unidade da Federação",
    "D2C": "Variável (Código)",
    "D3C": "Ano (Código)",
}
UFS = 27


def baixar() -> bytes:
    """PT: resposta da API, como veio / EN: the API response, as is"""
    url = SIDRA_POPULACAO.format(anos=",".join(str(a) for a in ANOS_POPULACAO))
    req = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def validar(linhas: list[dict]) -> None:
    """PT: estrutura e completude / EN: structure and completeness"""
    dicionario, dados = linhas[0], linhas[1:]
    erros = [
        f"campo {k}: esperado '{v}', veio '{dicionario.get(k)}'"
        for k, v in DICIONARIO_ESPERADO.items() if dicionario.get(k) != v
    ]
    esperado = UFS * len(ANOS_POPULACAO)
    if len(dados) != esperado:
        erros.append(f"{len(dados)} linhas, esperado {esperado} ({UFS} UFs x {len(ANOS_POPULACAO)} anos)")
    anos = {d["D3C"] for d in dados}
    if anos != {str(a) for a in ANOS_POPULACAO}:
        erros.append(f"anos na resposta: {sorted(anos)}")
    if erros:
        raise ValueError("SIDRA 6579: " + "; ".join(erros))


def main() -> None:
    bruto = baixar()
    novo_hash = hashlib.sha256(bruto).hexdigest()
    linhas = json.loads(bruto)
    validar(linhas)

    dados = manifesto.carregar()
    secao = dados.setdefault("ibge", {})
    anterior = secao.get(NOME, {})
    if anterior and anterior.get("sha256") != novo_hash:
        print(f"  ! {NOME}: o IBGE revisou a tabela / IBGE revised the table", flush=True)

    DIR_RAW_IBGE.mkdir(parents=True, exist_ok=True)
    (DIR_RAW_IBGE / NOME).write_bytes(bruto)

    destino = DIR_LANDING_IBGE / "populacao" / "populacao_6579.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    (
        pl.DataFrame(linhas[1:], schema={k: pl.String for k in linhas[0]})
        .with_columns(
            pl.lit(NOME).alias("arquivo_origem"),
            pl.lit(novo_hash).alias("sha256_arquivo"),
        )
        .write_parquet(destino, compression="zstd")
    )

    secao[NOME] = {
        "url": SIDRA_POPULACAO.format(anos=",".join(str(a) for a in ANOS_POPULACAO)),
        "bytes": len(bruto),
        "sha256": novo_hash,
        "linhas": len(linhas) - 1,
    }
    manifesto.salvar(dados)
    print(f"  > {NOME}: {len(linhas) - 1} linhas, {len(ANOS_POPULACAO)} anos, sha256 {novo_hash[:12]}", flush=True)


if __name__ == "__main__":
    main()
