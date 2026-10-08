"""
PT: Exporta o esquema estrela do Databricks para Parquet (#45, ADR 0027).

    Roda na máquina local, com o login OAuth do Databricks (ADR 0001), e
    grava:
    - data/esquema_estrela/data/<tabela>.parquet, um por tabela dim_* e
      fct_*, ignorado pelo git;
    - esquema_estrela/manifesto.json, que fixa o retrato: mês de referência,
      e de cada tabela as colunas, as linhas, o sha256 do Parquet e os
      totais por período calculados no Databricks;
    - esquema_estrela/views.sql, as views do DuckDB com os nomes do dbt.

    O que pode sair é o evaluation/gabarito/esquema_estrela.json, que este
    script só lê: tabela, coluna e tipo. Se o Databricks tiver tabela ou
    coluna a mais, ou um tipo diferente, o script para, porque o retrato do
    gabarito ficou para trás. Nenhum nome de coluna de dado pessoal sai, e
    só o esquema dos marts é lido: o bronze do CNPJ nunca entra.

    Cada Parquet é ordenado por todas as colunas e comprimido com zstd, para
    que o mesmo dado produza os mesmos bytes. Se nenhum sha256 mudar, a
    revisão publicada no Hugging Face continua valendo; se algum mudar, ela
    é apagada do manifesto, e o retrato precisa ser publicado de novo.

    A conferência contra o DuckDB fica em scripts/analises/qa_esquema_estrela.py.

EN: Exports the star schema from Databricks to Parquet. Runs locally with
    the Databricks OAuth login and writes one Parquet per dim_*/fct_* table
    (git-ignored), the manifest pinning the snapshot (reference month, and
    per table the columns, rows, sha256 and per-period totals computed on
    Databricks), and the DuckDB views file. What may leave is the answer
    key's star schema snapshot, read-only here; any extra table or column, or
    a changed type, stops the script. Same data, same bytes. The DuckDB check
    lives in scripts/analises/qa_esquema_estrela.py.

Uso / Usage:
    uv run python -m scripts.exportar_esquema_estrela
"""

from __future__ import annotations

import sys

from ingestion.baixar import sha256
from ingestion.databricks import cliente, consultar, consultar_em_arrow, tipo_no_polars, warehouse
from scripts.esquema_estrela_duckdb import (
    ESQUEMA_NO_DATABRICKS,
    LOCAL,
    RAIZ,
    REPOSITORIO_HF,
    VIEWS,
    carregar_manifesto,
    checar_lista_permitida,
    esquema_esperado,
    gravar_manifesto,
    sql_dos_totais,
    texto_das_views,
)
from scripts.gerar_gabarito import exportar_esquema

# PT: nível do zstd: o máximo que o polars aceita, porque o arquivo é
#     escrito uma vez e baixado muitas.
# EN: zstd level: polars' maximum, written once and downloaded many times.
NIVEL_ZSTD = 22


def checar_contra_o_databricks(esperado: dict, no_databricks: dict) -> list[str]:
    """
    PT: O esquema dos marts tem de ser exatamente o retrato do gabarito.
    EN: The marts' schema must equal the answer key's snapshot exactly.
    """
    erros = [f"{t}: está no Databricks e não no retrato" for t in sorted(set(no_databricks) - set(esperado))]
    erros += [f"{t}: está no retrato e não no Databricks" for t in sorted(set(esperado) - set(no_databricks))]
    for tabela in sorted(set(esperado) & set(no_databricks)):
        if esperado[tabela] != no_databricks[tabela]:
            erros.append(f"{tabela}: colunas ou tipos diferentes do retrato do gabarito")
    return erros


def exportar_tabela(w, wid: str, tabela: str, colunas: list[list[str]]) -> dict:
    """
    PT: Uma tabela para Parquet, com o tipo de cada coluna conferido antes
        de gravar. Devolve linhas, sha256 e colunas para o manifesto.
    EN: One table to Parquet, each column's type checked before writing.
        Returns rows, sha256 and columns for the manifest.
    """
    nomes = [c for c, _ in colunas]
    tabela_df = consultar_em_arrow(w, wid, f"select {', '.join(nomes)} from {ESQUEMA_NO_DATABRICKS}.{tabela}")
    esperado = {c: tipo_no_polars(t) for c, t in colunas}
    if dict(tabela_df.schema) != esperado:
        raise SystemExit(f"{tabela}: tipos do Arrow diferentes do esperado / Arrow types differ\n"
                         f"  recebido: {dict(tabela_df.schema)}\n  esperado: {esperado}")

    tabela_df = tabela_df.sort(nomes, nulls_last=True, maintain_order=True)
    destino = LOCAL / "data" / f"{tabela}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabela_df.write_parquet(destino, compression="zstd", compression_level=NIVEL_ZSTD, statistics=True)
    return {
        "arquivo": f"data/{tabela}.parquet",
        "linhas": tabela_df.height,
        "bytes": destino.stat().st_size,
        "sha256": sha256(destino),
        "colunas": colunas,
    }


def totais_no_databricks(w, wid: str, tabela: str, colunas: list[list[str]]) -> dict:
    """
    PT: Totais por período, calculados no Databricks por consulta à parte,
        e não a partir do Parquet: é a referência da reconciliação.
    EN: Per-period totals computed on Databricks by a separate query, not
        from the Parquet: the reconciliation's reference.
    """
    resultado = consultar(w, wid, sql_dos_totais(tabela, colunas, f"{ESQUEMA_NO_DATABRICKS}."))
    return {"colunas": resultado.colunas, "linhas": resultado.linhas}


def main() -> None:
    esperado = esquema_esperado()
    erros = checar_lista_permitida(esperado)
    w = cliente()
    wid = warehouse(w)
    catalogo, esquema = ESQUEMA_NO_DATABRICKS.split(".")
    erros += checar_contra_o_databricks(esperado, exportar_esquema(w, wid, catalogo, esquema))
    if erros:
        print("\n".join(f"  ERRO {e}" for e in erros))
        sys.exit(1)

    anterior = carregar_manifesto()
    mes = consultar(w, wid, f"select cast(max(data_base) as string) from {ESQUEMA_NO_DATABRICKS}.fct_carteira")
    tabelas: dict[str, dict] = {}
    for tabela, colunas in esperado.items():
        tabelas[tabela] = exportar_tabela(w, wid, tabela, colunas)
        tabelas[tabela]["totais"] = totais_no_databricks(w, wid, tabela, colunas)
        print(f"  {tabela:24} {tabelas[tabela]['linhas']:>10} linhas {tabelas[tabela]['bytes']:>12} B")

    mesmos_arquivos = {t: d["sha256"] for t, d in (anterior.get("tabelas") or {}).items()} == {
        t: d["sha256"] for t, d in tabelas.items()
    }
    revisao = anterior.get("revisao_hf") if mesmos_arquivos else None
    gravar_manifesto(
        {
            "repositorio_hf": REPOSITORIO_HF,
            "revisao_hf": revisao,
            "mes_de_referencia": mes.linhas[0][0],
            "origem": ESQUEMA_NO_DATABRICKS,
            "tabelas": tabelas,
        }
    )
    VIEWS.write_text(texto_das_views(list(esperado)), encoding="utf-8", newline="\n")

    print(f"\nMês de referência / reference month: {mes.linhas[0][0]}")
    print(f"Total: {sum(d['bytes'] for d in tabelas.values()) / 2**20:.1f} MiB em {LOCAL.relative_to(RAIZ).as_posix()}/")
    if revisao:
        print(f"Arquivos iguais aos publicados: a revisão {revisao} continua valendo.")
    else:
        print("Retrato novo: rode o QA e publique / new snapshot: run the QA, then publish.")


if __name__ == "__main__":
    main()
