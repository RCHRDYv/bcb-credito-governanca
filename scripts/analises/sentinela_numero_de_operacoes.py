"""
PT: Teste empírico do valor -1 em numero_de_operacoes, sobre a camada
    bronze no Databricks (docs/triagem-ontologia.md, decisão 1.1).

    Hipótese herdada da V1: o -1 da V2 substitui o rótulo "<= 15" da V1, ou
    seja, marca recortes com até 15 operações. O teste mede:

    1. Que valores pequenos ou não numéricos aparecem em cada versão.
    2. O tamanho típico das linhas com -1 comparado com o das linhas com
       contagem divulgada.
    3. Onde o -1 se concentra: cliente, modalidade, segmento e UF.
    4. Se o mesmo recorte alterna entre -1 e contagem ao longo dos meses, e
       qual a maior contagem já vista em um recorte que também teve -1.

    Resultado e leitura em docs/sentinela-numero-de-operacoes.md.

EN: Empirical test of the -1 value in numero_de_operacoes, over the bronze
    layer on Databricks. The inherited hypothesis (from V1) is that V2's -1
    replaces V1's "<= 15" label. The test measures value distributions, the
    typical size of -1 rows, where -1 concentrates, and whether the same
    cell alternates between -1 and a published count over time.

Uso / Usage:
    uv run python -m scripts.analises.sentinela_numero_de_operacoes
"""

from __future__ import annotations

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import CATALOGO, SCHEMA

V1 = f"{CATALOGO}.{SCHEMA}.bronze_scr_v1"
V2 = f"{CATALOGO}.{SCHEMA}.bronze_scr_v2"
CONTAGEM = "try_cast(trim(numero_de_operacoes) AS BIGINT)"
EH_MENOS_UM = f"CASE WHEN {CONTAGEM} = -1 THEN 1 ELSE 0 END"
DIMENSOES = "uf, segmento, cliente, cnae_ocupacao, porte, modalidade, submodalidade, origem, indexador"


def valor(coluna: str) -> str:
    """PT: texto com vírgula decimal para número / EN: decimal-comma text to number"""
    return f"cast(replace(trim({coluna}), ',', '.') AS DOUBLE)"


def taxa_por(dimensao: str) -> str:
    """PT: % de linhas com -1 por valor de uma dimensão / EN: % of -1 rows per value"""
    return f"""
        SELECT trim({dimensao}), count(*), round(avg({EH_MENOS_UM}) * 100, 1) AS pct
        FROM {V2} GROUP BY 1 ORDER BY pct DESC"""


CONSULTAS = {
    "1a. V2: valores até 20 ou não numéricos (valor, linhas)": f"""
        SELECT trim(numero_de_operacoes) AS v, count(*)
        FROM {V2}
        WHERE {CONTAGEM} IS NULL OR {CONTAGEM} <= 20
        GROUP BY 1 ORDER BY try_cast(v AS BIGINT) NULLS FIRST""",

    "1b. V1: valores até 20 ou não numéricos (valor, linhas)": f"""
        SELECT trim(numero_de_operacoes) AS v, count(*)
        FROM {V1}
        WHERE {CONTAGEM} IS NULL OR {CONTAGEM} <= 20
        GROUP BY 1 ORDER BY try_cast(v AS BIGINT) NULLS FIRST""",

    "2. V2 por faixa de contagem (linhas, carteira média e mediana por linha em R$ mil, % da carteira)": f"""
        SELECT CASE WHEN {CONTAGEM} = -1 THEN 'a: -1' WHEN {CONTAGEM} = 1 THEN 'b: 1'
                    WHEN {CONTAGEM} <= 15 THEN 'c: 2 a 15' WHEN {CONTAGEM} <= 100 THEN 'd: 16 a 100'
                    ELSE 'e: acima de 100' END AS faixa,
               count(*),
               round(avg({valor('carteira_ativa')}) / 1e3, 1),
               round(percentile_approx({valor('carteira_ativa')}, 0.5) / 1e3, 1),
               round(sum({valor('carteira_ativa')}) / sum(sum({valor('carteira_ativa')})) OVER () * 100, 2)
        FROM {V2} GROUP BY 1 ORDER BY 1""",

    "3a. V2: % de linhas com -1 por cliente": taxa_por("cliente"),
    "3b. V2: % de linhas com -1 por modalidade": taxa_por("modalidade"),
    "3c. V2: % de linhas com -1 por segmento": taxa_por("segmento"),
    "3d. V2: % de linhas com -1 por UF": taxa_por("uf"),
    "3e. V2: % de linhas com -1 por mês": f"""
        SELECT trim(data_base), count(*), round(avg({EH_MENOS_UM}) * 100, 1)
        FROM {V2} GROUP BY 1 ORDER BY 1""",

    "4. V2: recortes ao longo dos meses (recortes, com -1, alternam, mediana e máximo da maior contagem dos que alternam)": f"""
        WITH recorte AS (
            SELECT {DIMENSOES},
                   max({EH_MENOS_UM}) AS teve_menos_um,
                   max(CASE WHEN {CONTAGEM} > 0 THEN 1 ELSE 0 END) AS teve_contagem,
                   max(CASE WHEN {CONTAGEM} > 0 THEN {CONTAGEM} END) AS maior_contagem
            FROM {V2} GROUP BY ALL
        )
        SELECT count(*),
               sum(teve_menos_um),
               sum(teve_menos_um * teve_contagem),
               percentile_approx(CASE WHEN teve_menos_um = 1 AND teve_contagem = 1 THEN maior_contagem END, 0.5),
               max(CASE WHEN teve_menos_um = 1 AND teve_contagem = 1 THEN maior_contagem END)
        FROM recorte""",
}


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    for titulo, sql in CONSULTAS.items():
        print(f"\n=== {titulo}")
        for linha in executar_sql(w, wid, sql):
            print("   ", linha)


if __name__ == "__main__":
    main()
