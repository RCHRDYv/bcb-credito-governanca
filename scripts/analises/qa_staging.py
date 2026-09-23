"""
PT: QA da camada de staging, independente dos testes do dbt.

    Por que existe, se o `dbt build` já roda 65 testes: porque o modelo e o
    teste foram escritos pela mesma cabeça, na mesma hora. Se os dois tiverem o
    mesmo ponto cego, os dois passam juntos. Este script confere as mesmas
    propriedades por outros caminhos, e acrescenta duas coisas que os testes do
    dbt não podem fazer:

    1. **Conferência fora do Databricks.** A contagem de linhas é comparada com
       `ingestion/manifesto.json`, medido no CSV original na máquina local. Um
       teste que roda dentro do warehouse só pode comparar o warehouse consigo
       mesmo.
    2. **Varredura da série.** A cardinalidade de cada dimensão é impressa mês a
       mês. Foi assim que se descobriu que a coluna `tcb` da V1 deixou de ser
       publicada em julho de 2025, o que no total parecia dado faltante
       (`docs/desenvolvimento-com-ia.md`, erro 11).

    O que ele NÃO faz: substituir os testes do dbt. Aqueles rodam a cada build
    e barram o merge; este é uma conferência de quem revisa, que imprime número
    em vez de só passar ou falhar.

EN: Staging layer QA, independent from the dbt tests.

    Why it exists when `dbt build` already runs 65 tests: because model and test
    were written by the same head at the same time, and a shared blind spot
    passes both. This script checks the same properties by other paths and adds
    two things the dbt tests cannot do: it compares row counts against
    `ingestion/manifesto.json`, measured on the original CSV outside Databricks,
    and it sweeps the series month by month. The latter is how V1's `tcb` column
    was found to have stopped being published in July 2025, which in aggregate
    looked like missing data.

Uso / Usage:
    uv run python -m scripts.analises.qa_staging
"""

from __future__ import annotations

import json

from databricks.sdk import WorkspaceClient

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import CATALOGO, MANIFESTO, SCHEMA

# -----------------------------------------------------------------------------
# PT: Configuração. O staging do dbt cria as views no schema <schema>_staging,
#     conforme dbt/dbt_project.yml.
# EN: Configuration. dbt's staging creates the views in <schema>_staging.
# -----------------------------------------------------------------------------

BRONZE = f"{CATALOGO}.{SCHEMA}"
STAGING = f"{CATALOGO}.{SCHEMA}_staging"
SEED = f"{CATALOGO}.{SCHEMA}_marts.correspondencia_modalidade_v2_v1"

FAIXAS_A_VENCER = [
    "a_vencer_ate_90_dias",
    "a_vencer_de_91_ate_360_dias",
    "a_vencer_de_361_ate_1080_dias",
    "a_vencer_de_1081_ate_1800_dias",
    "a_vencer_de_1801_ate_5400_dias",
    "a_vencer_acima_de_5400_dias",
]

MEDIDAS = {
    "v2": FAIXAS_A_VENCER + [
        "carteira_a_vencer", "vencido_de_15_ate_90_dias", "vencido_acima_de_90_dias",
        "carteira_vencida", "carteira_ativa", "carteira_inadimplencia", "ativo_problematico",
    ],
    "v1": FAIXAS_A_VENCER + [
        "vencido_acima_de_15_dias", "carteira_ativa",
        "carteira_inadimplida_arrastada", "ativo_problematico",
    ],
}

# PT: O grão declarado de cada versão. / EN: Each version's declared grain.
GRAO = {
    "v2": ["data_base", "uf", "segmento", "cliente", "cnae_ocupacao", "porte",
           "modalidade", "submodalidade", "origem", "indexador"],
    "v1": ["data_base", "uf", "tcb", "sr", "cliente", "ocupacao", "cnae_secao",
           "cnae_subclasse", "porte", "modalidade", "origem", "indexador"],
}

# PT: O sentinela de supressão de contagem é diferente em cada versão.
# EN: The count-suppression sentinel differs per version.
SENTINELA = {"v2": "-1", "v1": "<= 15"}


class Relatorio:
    """
    PT: Acumula o resultado de cada verificação e imprime na hora, para uma
        execução longa não ficar muda.
    EN: Accumulates each check's result and prints as it goes, so a long run is
        not silent.
    """

    def __init__(self) -> None:
        self.falhas: list[str] = []
        self.total = 0

    def verifica(self, nome: str, ok: bool, detalhe: str) -> None:
        self.total += 1
        if not ok:
            self.falhas.append(f"{nome}: {detalhe}")
        print(f"  {'OK   ' if ok else 'FALHA'}  {nome}: {detalhe}")

    def observa(self, nome: str, detalhe: str) -> None:
        """PT: medida sem veredito / EN: measurement with no verdict"""
        print(f"  ....   {nome}: {detalhe}")

    def encerra(self) -> int:
        print(f"\n{'=' * 78}")
        print(f"{self.total} verificações, {len(self.falhas)} falhas")
        for falha in self.falhas:
            print(f"  FALHA  {falha}")
        return 1 if self.falhas else 0


def linhas_por_mes_no_manifesto() -> dict[str, dict[str, int]]:
    """
    PT: Linhas por mês medidas no CSV original, durante a conversão para
        Parquet, e gravadas no manifesto versionado. É a única referência do
        projeto que não passa pelo Databricks.
    EN: Rows per month measured on the original CSV during Parquet conversion
        and written to the versioned manifest. The project's only reference that
        does not go through Databricks.
    """
    dados = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    por_versao: dict[str, dict[str, int]] = {"v1": {}, "v2": {}}
    for registro in dados["arquivos"].values():
        for ano_mes, mes in registro["meses"].items():
            por_versao[registro["versao"]][ano_mes] = mes["linhas"]
    return por_versao


def valor_em_reais(coluna: str) -> str:
    """PT: mesma conversão do macro do dbt / EN: same conversion as the dbt macro"""
    return f"cast(replace(trim({coluna}), ',', '.') as decimal(18,2))"


# -----------------------------------------------------------------------------
# PT: A. Completude
# EN: A. Completeness
# -----------------------------------------------------------------------------

def conferir_completude(w: WorkspaceClient, wh: str, r: Relatorio) -> None:
    print("\nA. COMPLETUDE")
    manifesto = linhas_por_mes_no_manifesto()

    for versao in ("v2", "v1"):
        esperado = sum(manifesto[versao].values())
        bronze, staging = executar_sql(w, wh, f"""
            select (select count(*) from {BRONZE}.bronze_scr_{versao}) as bronze,
                   (select count(*) from {STAGING}.stg_scr_{versao}) as staging
        """)[0]
        r.verifica(
            f"{versao}: linhas no CSV, no bronze e no staging",
            int(bronze) == esperado and int(staging) == esperado,
            f"{esperado:,} no CSV, {int(bronze):,} no bronze, {int(staging):,} no staging",
        )

        # PT: por mês, para um mês a mais não compensar um mês a menos no total.
        # EN: per month, so a surplus month cannot cancel a missing one.
        medido = {
            linha[0]: int(linha[1])
            for linha in executar_sql(w, wh, f"""
                select date_format(data_base, 'yyyyMM') as ano_mes, count(*) as linhas
                from {STAGING}.stg_scr_{versao} group by all
            """)
        }
        divergentes = {
            mes: (manifesto[versao].get(mes), medido.get(mes))
            for mes in set(manifesto[versao]) | set(medido)
            if manifesto[versao].get(mes) != medido.get(mes)
        }
        r.verifica(
            f"{versao}: linhas por mês contra o manifesto",
            not divergentes,
            f"{len(medido)} meses conferidos, {len(divergentes)} divergentes "
            f"{divergentes if divergentes else ''}",
        )

        # PT: a data-base convertida precisa bater com o mês no nome do arquivo.
        # EN: the converted reference date must match the month in the filename.
        fora = executar_sql(w, wh, f"""
            select count(*) from (
              select distinct arquivo_origem, data_base from {STAGING}.stg_scr_{versao}
            ) where date_format(data_base, 'yyyyMM')
                  != regexp_extract(arquivo_origem, '([0-9]{{6}})\\\\.csv', 1)
        """)[0][0]
        r.verifica(f"{versao}: data-base coerente com o nome do arquivo",
                   int(fora) == 0, f"{fora} arquivos fora do mês")


# -----------------------------------------------------------------------------
# PT: B. Grão e fan-out
# EN: B. Grain and fan-out
# -----------------------------------------------------------------------------

def conferir_grao(w: WorkspaceClient, wh: str, r: Relatorio) -> None:
    print("\nB. GRÃO E FAN-OUT")

    for versao, dimensoes in GRAO.items():
        # PT: o coalesce é obrigatório: concat_ws salta nulo, e sem ele dois
        #     recortes diferentes podem gerar a mesma chave.
        # EN: the coalesce is mandatory: concat_ws skips nulls, and without it
        #     two different slices can produce the same key.
        chave = ", ".join(f"coalesce(cast({c} as string), '(nulo)')" for c in dimensoes)
        linhas, chaves = executar_sql(w, wh, f"""
            select count(*) as linhas,
                   count(distinct concat_ws('\\u0001', {chave})) as chaves
            from {STAGING}.stg_scr_{versao}
        """)[0]
        r.verifica(f"{versao}: uma linha por recorte, sem duplicata nem fan-out",
                   linhas == chaves, f"{int(linhas):,} linhas, {int(chaves):,} chaves")

    # PT: pré-checagem da camada intermediária. A junção com o seed será por
    #     rótulo, então a combinação de rótulos precisa ser única no seed. Se não
    #     for, a junção multiplica linha e todo total fica errado para cima.
    # EN: intermediate-layer pre-check. The join with the seed will be by label,
    #     so the label combination must be unique in the seed. Otherwise the join
    #     multiplies rows and every total comes out too high.
    repetidas = executar_sql(w, wh, f"""
        select count(*) from (
          select modalidade_v2, submodalidade_v2, cliente, origem
          from {SEED} group by all having count(*) > 1
        )
    """)[0][0]
    r.verifica("seed: chave por rótulo é única, então a junção não multiplica linha",
               int(repetidas) == 0, f"{repetidas} combinações repetidas")

    orfas = executar_sql(w, wh, f"""
        select count(*) as combinacoes, coalesce(sum(linhas), 0) as linhas from (
          select s.modalidade, s.submodalidade, s.cliente, s.origem, count(*) as linhas
          from {STAGING}.stg_scr_v2 s
          left join {SEED} c
            on c.modalidade_v2 = s.modalidade
           and c.submodalidade_v2 = s.submodalidade
           and c.cliente = s.cliente
           and c.origem = s.origem
          where c.codigo_submodalidade_v2 is null
          group by all
        )
    """)[0]
    r.verifica("v2 contra o seed: nenhuma linha sem correspondência",
               int(orfas[0]) == 0,
               f"{orfas[0]} combinações, {orfas[1]} linhas sem par")


# -----------------------------------------------------------------------------
# PT: C. Integridade dos valores
# EN: C. Value integrity
# -----------------------------------------------------------------------------

def conferir_valores(w: WorkspaceClient, wh: str, r: Relatorio) -> None:
    print("\nC. INTEGRIDADE DOS VALORES")

    for versao, medidas in MEDIDAS.items():
        # PT: escala publicada. Se o BCB passar a publicar três decimais, o cast
        #     para decimal(18,2) arredonda em silêncio, e é aqui que aparece.
        # EN: published scale. If the BCB starts publishing three decimals, the
        #     cast to decimal(18,2) rounds silently, and this is where it shows.
        fora_da_escala = executar_sql(w, wh, f"""
            select {' + '.join(f"count_if(trim({c}) not rlike '^-?[0-9]+,[0-9][0-9]$')" for c in medidas)}
            from {BRONZE}.bronze_scr_{versao}
        """)[0][0]
        r.verifica(f"{versao}: toda medida publicada com exatamente 2 decimais",
                   int(fora_da_escala) == 0,
                   f"{int(fora_da_escala):,} valores fora do padrão 'inteiro,dd'")

        # PT: ida e volta. Reconstrói o texto a partir do decimal e compara com o
        #     texto publicado. Pega truncamento, arredondamento e estouro de
        #     precisão de uma vez. Roda no bronze porque é lá que está o texto.
        # EN: round trip. Rebuilds the text from the decimal and compares with the
        #     published text, catching truncation, rounding and precision
        #     overflow at once. It runs on bronze because that is where the text is.
        volta = " + ".join(
            f"count_if(replace(cast({valor_em_reais(c)} as string), '.', ',') != trim({c}))"
            for c in medidas
        )
        perdidos = executar_sql(
            w, wh, f"select {volta} from {BRONZE}.bronze_scr_{versao}"
        )[0][0]
        r.verifica(f"{versao}: conversão é reversível, texto para decimal e de volta",
                   int(perdidos) == 0, f"{int(perdidos):,} valores que não voltam iguais")

        nulos, negativos, maior = executar_sql(w, wh, f"""
            select {' + '.join(f'count_if({c} is null)' for c in medidas)} as nulos,
                   {' + '.join(f'count_if({c} < 0)' for c in medidas)} as negativos,
                   max(greatest({', '.join(medidas)})) as maior
            from {STAGING}.stg_scr_{versao}
        """)[0]
        r.verifica(f"{versao}: nenhuma medida virou nula na conversão",
                   int(nulos) == 0, f"{int(nulos)} nulos")
        r.observa(f"{versao}: amplitude das medidas",
                  f"{int(negativos):,} valores negativos, maior valor em uma linha "
                  f"R$ {float(maior):,.2f}")


# -----------------------------------------------------------------------------
# PT: D. Sentinela de contagem
# EN: D. Count sentinel
# -----------------------------------------------------------------------------

def conferir_sentinela(w: WorkspaceClient, wh: str, r: Relatorio) -> None:
    print("\nD. SENTINELA DE CONTAGEM")

    for versao, sentinela in SENTINELA.items():
        staging, bronze = executar_sql(w, wh, f"""
            select (select sum(numero_de_operacoes) from {STAGING}.stg_scr_{versao}) as staging,
                   (select sum(cast(numero_de_operacoes as bigint))
                    from {BRONZE}.bronze_scr_{versao}
                    where trim(numero_de_operacoes) != '{sentinela}') as bronze
        """)[0]
        r.verifica(f"{versao}: soma das contagens divulgadas igual à do bronze",
                   staging == bronze,
                   f"{int(staging):,} no staging, {int(bronze):,} no bronze")

        menor = executar_sql(w, wh, f"""
            select min(numero_de_operacoes) from {STAGING}.stg_scr_{versao}
        """)[0][0]
        r.verifica(f"{versao}: nenhuma contagem menor que 1 sobrou",
                   int(menor) >= 1, f"menor contagem divulgada: {menor}")

    # PT: a regra da V1 está publicada e pode ser conferida: nenhuma contagem
    #     divulgada deve ser 15 ou menos, porque essas são exatamente as
    #     suprimidas. A V2 não tem regra, e divulga de 1 a 15 abertamente.
    # EN: V1's rule is published and checkable: no disclosed count should be 15
    #     or less, because those are exactly the suppressed ones. V2 has no rule
    #     and discloses 1 to 15 openly.
    v1_ate_15, v2_ate_15 = executar_sql(w, wh, f"""
        select (select count_if(numero_de_operacoes <= 15) from {STAGING}.stg_scr_v1),
               (select count_if(numero_de_operacoes <= 15) from {STAGING}.stg_scr_v2)
    """)[0]
    r.verifica("v1: a regra publicada do '<= 15' se confirma no dado",
               int(v1_ate_15) == 0,
               f"{int(v1_ate_15)} linhas com contagem divulgada de até 15")
    r.observa("v2: contagens de 1 a 15 divulgadas abertamente",
              f"{int(v2_ate_15):,} linhas, o que refuta a hipótese de que o -1 "
              f"seja o '<= 15' da V1")


# -----------------------------------------------------------------------------
# PT: E. Varredura da série
# EN: E. Series sweep
# -----------------------------------------------------------------------------

def varrer_serie(w: WorkspaceClient, wh: str, r: Relatorio) -> None:
    print("\nE. VARREDURA DA SÉRIE")

    for versao in ("v2", "v1"):
        meses, primeiro, ultimo, fora = executar_sql(w, wh, f"""
            select count(distinct data_base) as meses,
                   min(data_base) as primeiro, max(data_base) as ultimo,
                   count_if(data_base != last_day(data_base)) as fora_do_fim_do_mes
            from {STAGING}.stg_scr_{versao}
        """)[0]
        r.verifica(f"{versao}: data-base é sempre o último dia do mês",
                   int(fora) == 0, f"{meses} meses, de {primeiro} a {ultimo}")

    # PT: cardinalidade mês a mês. Uma dimensão que cai a zero num mês foi
    #     descontinuada, e no total isso parece dado faltante. O `tcb` da V1 é o
    #     caso conhecido, em jul/2025, e o teste
    #     dbt/tests/staging_dimensao_nao_fica_vazia.sql barra o próximo.
    # EN: month-by-month cardinality. A dimension dropping to zero in one month
    #     was discontinued, and in aggregate that looks like missing data. V1's
    #     `tcb` is the known case, in Jul/2025.
    for versao in ("v2", "v1"):
        dimensoes = [c for c in GRAO[versao] if c != "data_base"]
        distintos = ", ".join(f"count(distinct {c}) as {c}" for c in dimensoes)
        linhas = executar_sql(w, wh, f"""
            select date_format(data_base, 'yyyy-MM') as mes, {distintos}
            from {STAGING}.stg_scr_{versao} group by all order by mes
        """)
        print(f"\n  {versao}: valores distintos por mês")
        print("    mês      " + "  ".join(c[:10].rjust(10) for c in dimensoes))
        for linha in linhas:
            print("    " + linha[0] + "  " + "  ".join(str(v).rjust(10) for v in linha[1:]))

        # PT: resume a varredura num veredito, guardando o PRIMEIRO mês em que
        #     cada dimensão zerou, que é o mês da quebra.
        # EN: turns the sweep into a verdict, keeping the FIRST month each
        #     dimension hit zero, which is the month of the break.
        zerou: dict[str, str] = {}
        for linha in linhas:
            for i, coluna in enumerate(dimensoes, start=1):
                if int(linha[i]) == 0:
                    zerou.setdefault(coluna, linha[0])
        r.verifica(f"{versao}: nenhuma dimensão zerada em nenhum mês",
                   not zerou or set(zerou) == {"tcb"},
                   f"{zerou if zerou else 'nenhuma'}"
                   + (" (quebra conhecida e registrada)" if zerou else ""))


def main() -> int:
    w = cliente()
    wh = warehouse(w)
    r = Relatorio()

    conferir_completude(w, wh, r)
    conferir_grao(w, wh, r)
    conferir_valores(w, wh, r)
    conferir_sentinela(w, wh, r)
    varrer_serie(w, wh, r)

    return r.encerra()


if __name__ == "__main__":
    raise SystemExit(main())
