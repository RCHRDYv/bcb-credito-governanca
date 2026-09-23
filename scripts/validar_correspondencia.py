"""
PT: Valida o seed de correspondência V2 para V1 em três camadas.

    1. Estrutura: a chave (código, cliente, origem) é única, toda linha tem
       destino oficial ou inferência declarada, e os valores de regra e de
       ambiguidade são os previstos.
    2. Rótulos: toda modalidade V1 citada pelo seed existe no bronze da V1, e
       toda modalidade V1 do bronze é citada pelo seed. Isso pega erro de
       grafia, que faria o join falhar em silêncio.
    3. Cobertura e impacto: todo recorte (modalidade, submodalidade, cliente,
       origem) do bronze V2 encontra exatamente uma linha do seed, e mede
       quanto da carteira cai nas linhas ambíguas ou sem correspondência
       oficial. Esse número é o que o mart precisa declarar.

EN: Validates the V2 to V1 correspondence seed in three layers: structure
    (unique key, declared target or inference, allowed rule values), labels
    (every V1 modality in the seed exists in V1 bronze and vice versa) and
    coverage (every V2 slice finds exactly one seed row), plus how much
    portfolio falls on ambiguous or unmapped rows.

Uso / Usage:
    uv run python -m scripts.validar_correspondencia
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "dbt" / "seeds" / "correspondencia_modalidade_v2_v1.csv"
REGRAS = {"base", "tratamento_1", "tratamento_2", "ausente_na_planilha"}
AMBIGUIDADES = {"", "natureza_nao_publicada", "ausente_na_planilha"}
VALOR = "cast(replace(trim(carteira_ativa), ',', '.') AS DOUBLE)"


def ler_seed() -> list[dict]:
    with SEED.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def checar_estrutura(seed: list[dict]) -> list[str]:
    erros = []
    chaves = Counter((l["codigo_submodalidade_v2"], l["cliente"], l["origem"]) for l in seed)
    erros += [f"chave repetida: {k}" for k, n in chaves.items() if n > 1]
    for l in seed:
        if not l["modalidade_v1"] and not l["modalidade_v1_inferida"]:
            erros.append(f"{l['codigo_submodalidade_v2']} {l['cliente']}: sem destino e sem inferência")
        if l["regra"] not in REGRAS:
            erros.append(f"{l['codigo_submodalidade_v2']}: regra inválida '{l['regra']}'")
        if l["ambiguidade"] not in AMBIGUIDADES:
            erros.append(f"{l['codigo_submodalidade_v2']}: ambiguidade inválida '{l['ambiguidade']}'")
    print(f"  1. estrutura: {len(seed)} linhas, {len(erros)} problemas")
    return erros


def checar_rotulos(seed: list[dict], w, wid: str) -> list[str]:
    from ingestion.databricks import executar_sql
    from ingestion.fontes import CATALOGO, SCHEMA

    sql = f"SELECT DISTINCT trim(modalidade) FROM {CATALOGO}.{SCHEMA}.bronze_scr_v1"
    no_dado = {linha[0] for linha in executar_sql(w, wid, sql)}
    no_seed = {l[c] for l in seed for c in ("modalidade_v1", "modalidade_v1_alternativa", "modalidade_v1_inferida") if l[c]}

    erros = [f"modalidade V1 do seed que não existe no dado: {r!r}" for r in sorted(no_seed - no_dado)]
    erros += [f"modalidade V1 do dado que o seed não cita: {r!r}" for r in sorted(no_dado - no_seed)]
    print(f"  2. rótulos: {len(no_dado)} no dado, {len(no_seed)} citados pelo seed, {len(erros)} problemas")
    return erros


def checar_cobertura(seed: list[dict], w, wid: str) -> list[str]:
    from ingestion.databricks import executar_sql
    from ingestion.fontes import CATALOGO, SCHEMA

    sql = f"""
        SELECT trim(modalidade), trim(submodalidade), trim(cliente), trim(origem),
               count(*), sum({VALOR})
        FROM {CATALOGO}.{SCHEMA}.bronze_scr_v2
        GROUP BY 1, 2, 3, 4"""
    dado = {
        (m, s, c, o): (int(n), float(v))
        for m, s, c, o, n, v in executar_sql(w, wid, sql)
    }
    por_chave = {(l["modalidade_v2"], l["submodalidade_v2"], l["cliente"], l["origem"]): l for l in seed}

    erros = [f"recorte do dado sem linha no seed: {k!r} ({dado[k][0]:,} linhas)" for k in sorted(set(dado) - set(por_chave))]

    total = sum(v for _, v in dado.values())
    def fatia(condicao) -> tuple[float, int]:
        alvo = [(k, v) for k, v in dado.items() if k in por_chave and condicao(por_chave[k])]
        return sum(v for _, (_, v) in alvo) / total * 100, sum(n for _, (n, _) in alvo)

    pct_ambigua, linhas_ambiguas = fatia(lambda l: l["ambiguidade"] == "natureza_nao_publicada")
    pct_ausente, linhas_ausentes = fatia(lambda l: l["ambiguidade"] == "ausente_na_planilha")
    print(f"  3. cobertura: {len(dado)} recortes no dado, {len(erros)} sem correspondência no seed")
    print(f"     ambíguas por Natureza não publicada: {pct_ambigua:.2f}% da carteira, {linhas_ambiguas:,} linhas")
    print(f"     sem correspondência oficial: {pct_ausente:.2f}% da carteira, {linhas_ausentes:,} linhas")
    return erros


def main() -> None:
    # PT: --estrutura roda só a camada 1, sem Databricks. É o que o CI usa.
    # EN: --estrutura runs layer 1 only, with no Databricks. Used by CI.
    so_estrutura = "--estrutura" in sys.argv[1:]

    seed = ler_seed()
    erros = checar_estrutura(seed)

    if not so_estrutura:
        # PT: import aqui dentro para a camada 1 rodar onde não há credencial.
        # EN: import inside so layer 1 can run where there is no credential.
        from ingestion.databricks import cliente, warehouse

        w = cliente()
        wid = warehouse(w)
        erros += checar_rotulos(seed, w, wid)
        erros += checar_cobertura(seed, w, wid)

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    if so_estrutura:
        print("\nEstrutura do seed está coerente / seed structure is coherent.")
    else:
        print("\nSeed de correspondência confere com o dado / correspondence seed matches the data.")


if __name__ == "__main__":
    main()
