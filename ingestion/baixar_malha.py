"""
PT: Etapa 1 da malha das UFs (issue #67). Baixa a malha das 27 UFs da API de
    malhas v3 do IBGE e grava a resposta como veio, em data/raw/ibge/. A
    etapa 2, que simplifica a malha para o site, fica em
    scripts/gerar_malha_do_dashboard.py.

    Diferente das outras fontes, a malha não vai ao Databricks: só o site do
    dashboard a usa, no mapa por UF. Ela segue o padrão da ingestão mesmo
    assim, com a resposta guardada como veio e a identidade registrada no
    manifesto. O IBGE pode republicar a malha sem aviso, e o sha256 novo
    aparece no diff do manifesto.

    Antes de gravar, confere que a resposta traz as 27 UFs de dim_uf, pelo
    código do IBGE, cada uma uma vez e só com polígonos. Se o IBGE mudar a
    estrutura da resposta, a ingestão para aqui, em vez de gravar uma malha
    que o site não sabe ler.

EN: State mesh step 1. Downloads the mesh of the 27 states from IBGE's mesh
    API v3 and stores the response as is. Step 2, simplifying it for the
    site, is scripts/gerar_malha_do_dashboard.py. The mesh does not go to
    Databricks, but follows the ingestion pattern: raw response kept, identity
    in the manifest, so a republication shows up as a new sha256. Before
    writing, it checks the response carries the 27 states of dim_uf by IBGE
    code, once each, as polygons only.

Uso / Usage:
    uv run python -m ingestion.baixar_malha
"""

from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from collections import Counter

import yaml

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import DIR_RAW_IBGE, MALHA_UFS, RAIZ

NOME = "malha_ufs_2022.json"
DIMENSOES = RAIZ / "ontology" / "dimensoes.yml"
GEOMETRIAS = {"Polygon", "MultiPolygon"}


def ufs_da_ontologia() -> dict[str, str]:
    """
    PT: As 27 UFs de dim_uf, do código do IBGE para a sigla. A ontologia é a
        fonte única desse par, e a malha não traz a sigla.
    EN: The 27 states of dim_uf, from IBGE code to abbreviation. The ontology
        is the single source of that pair; the mesh carries no abbreviation.
    """
    documento = yaml.safe_load(DIMENSOES.read_text(encoding="utf-8"))
    dim_uf = next(d for d in documento["dimensoes"] if d["id"] == "dim_uf")
    return {str(v["codigo_ibge"]): v["rotulo_no_dado"] for v in dim_uf["valores"]}


def validar(malha: dict, ufs: dict[str, str]) -> list[str]:
    """
    PT: Confere a forma da resposta: uma coleção de feições, uma por UF,
        identificada pelo código do IBGE em `codarea`, só com polígonos.
    EN: Checks the response shape: one feature per state, identified by the
        IBGE code in `codarea`, polygons only.
    """
    if malha.get("type") != "FeatureCollection":
        return [f"tipo de topo {malha.get('type')!r}, esperado 'FeatureCollection'"]
    feicoes = malha.get("features", [])
    codigos = [f.get("properties", {}).get("codarea") for f in feicoes]
    erros = [f"código repetido: {c}" for c, n in Counter(codigos).items() if n > 1]
    faltando = sorted(set(ufs) - set(codigos))
    a_mais = sorted({str(c) for c in codigos} - set(ufs))
    if faltando:
        erros.append(f"UFs faltando: {[ufs[c] for c in faltando]}")
    if a_mais:
        erros.append(f"códigos fora de dim_uf: {a_mais}")
    tipos = {f.get("geometry", {}).get("type") for f in feicoes}
    if not tipos <= GEOMETRIAS:
        erros.append(f"geometrias fora de {sorted(GEOMETRIAS)}: {sorted(map(str, tipos - GEOMETRIAS))}")
    return erros


def baixar() -> bytes:
    """
    PT: A resposta da API, como veio. O servidor do IBGE comprime a resposta
        com gzip mesmo quando o pedido não diz que aceita (medido em
        2026-10-01). A compressão é só transporte: o que fica gravado, e o
        que o sha256 identifica, é o GeoJSON que ela carrega.
    EN: The API response, as is. IBGE's server gzips it even when the request
        does not accept it; compression is transport only, so the stored file
        and its sha256 are the GeoJSON it carries.
    """
    req = urllib.request.Request(MALHA_UFS, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        corpo = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            corpo = gzip.decompress(corpo)
    return corpo


def main() -> None:
    bruto = baixar()
    novo_hash = hashlib.sha256(bruto).hexdigest()
    malha = json.loads(bruto)
    erros = validar(malha, ufs_da_ontologia())
    if erros:
        raise ValueError("Malha do IBGE: " + "; ".join(erros))

    dados = manifesto.carregar()
    secao = dados.setdefault("ibge", {})
    anterior = secao.get(NOME, {})
    if anterior and anterior.get("sha256") != novo_hash:
        print(f"  ! {NOME}: o IBGE republicou a malha / IBGE republished the mesh", flush=True)

    DIR_RAW_IBGE.mkdir(parents=True, exist_ok=True)
    (DIR_RAW_IBGE / NOME).write_bytes(bruto)

    secao[NOME] = {
        "url": MALHA_UFS,
        "bytes": len(bruto),
        "sha256": novo_hash,
        "feicoes": len(malha["features"]),
    }
    manifesto.salvar(dados)
    print(f"  > {NOME}: {len(malha['features'])} UFs, {len(bruto)} bytes, sha256 {novo_hash[:12]}", flush=True)


if __name__ == "__main__":
    main()
