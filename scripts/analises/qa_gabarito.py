"""
PT: QA do gabarito (issue #16), independente dos SQL do gabarito.

    Confere as respostas versionadas em evaluation/gabarito/respostas/
    contra números que o projeto já publicou por outro caminho:

    - os marts de apresentação, que agregam o fato por outra consulta:
      mrt_limites_do_dado (Q01, Q28, Q36, Q37, Q39, Q40),
      mrt_carteira_mensal (Q03, Q06, Q07), mrt_decisao (Q14) e
      mrt_reconciliacao_versoes (Q30);
    - o outro lado do PIX, que precisa fechar com o lado usado (Q22);
    - os documentos do projeto, com o arredondamento com que foram escritos:
      docs/cadeia-normativa.md (Q38), ontology/metricas.yml (Q36) e o
      ADR 0003 (Q40).

    Uma divergência é investigada, e não ajustada para bater.

EN: Answer key QA, independent from the key's SQL. Checks the versioned
    answers against numbers the project already published another way:
    presentation marts, the other PIX side, and project documents at the
    rounding they were written with.

Uso / Usage:
    uv run python -m scripts.analises.qa_gabarito
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal

from ingestion.databricks import cliente, consultar, warehouse
from ingestion.fontes import RAIZ

MARTS = "workspace.bcb_scr_marts"
RESPOSTAS = RAIZ / "evaluation" / "gabarito" / "respostas"

# PT: as respostas guardam ponto flutuante com 10 algarismos significativos.
# EN: answers store floating point with 10 significant digits.
TOLERANCIA_RELATIVA = Decimal("1e-8")


class Conferencia:
    """
    PT: Acumula comparações e divergências, e imprime o resumo no fim.
    EN: Accumulates comparisons and mismatches, printing a summary at the end.
    """

    def __init__(self) -> None:
        self.total = 0
        self.falhas: list[str] = []

    def valor(self, nome: str, obtido, esperado, tolerancia: Decimal = TOLERANCIA_RELATIVA) -> None:
        """PT: igualdade com tolerância relativa / EN: relative-tolerance equality"""
        self.total += 1
        a, b = Decimal(str(obtido)), Decimal(str(esperado))
        if abs(a - b) > tolerancia * max(abs(a), abs(b), Decimal(1)):
            self.falhas.append(f"{nome}: gabarito {a}, esperado {b}")

    def arredondado(self, nome: str, obtido, esperado: str, escala: Decimal = Decimal(1)) -> None:
        """
        PT: Compara com um número de documento, arredondado nas casas em que
            ele foi escrito. A escala converte a unidade, como reais em bi.
        EN: Compares with a document's number at the decimals it was written.
        """
        self.total += 1
        casas = len(esperado.split(".")[1]) if "." in esperado else 0
        arredondado = round(Decimal(str(obtido)) / escala, casas)
        if arredondado != Decimal(esperado):
            self.falhas.append(f"{nome}: gabarito {arredondado}, documento {esperado}")


def resposta(consulta: str) -> list[dict]:
    """PT: linhas de uma resposta como dicionários / EN: answer rows as dicts"""
    dados = json.loads((RESPOSTAS / f"{consulta}.json").read_text(encoding="utf-8"))
    return [dict(zip(dados["colunas"], linha)) for linha in dados["linhas"]]


def por_chave(linhas: list[dict], chave: str) -> dict:
    return {linha[chave]: linha for linha in linhas}


# -----------------------------------------------------------------------------
# PT: Contra os marts de apresentação
# EN: Against the presentation marts
# -----------------------------------------------------------------------------

def contra_limites_do_dado(c: Conferencia, w, wid: str) -> None:
    """PT: Q01, Q28, Q36, Q37, Q39 e Q40 / EN: monthly data-limits mart"""
    mart = {
        linha[0]: dict(zip(("carteira_v1", "carteira_v2", "diferenca", "supr_carteira", "supr_recortes",
                            "operacoes", "ambigua", "inferida"), linha[1:]))
        for linha in consultar(w, wid, f"""
            select cast(data_base as string), carteira_v1_publicada, carteira_v2, diferenca_v2_sobre_v1,
                   parcela_carteira_contagem_suprimida, parcela_recortes_contagem_suprimida,
                   operacoes_limite_inferior, parcela_carteira_conformacao_ambigua,
                   parcela_carteira_conformacao_inferida
            from {MARTS}.mrt_limites_do_dado""").linhas
    }

    q01 = resposta("Q01")[0]
    c.valor("Q01 carteira no último mês", q01["carteira_ativa"], mart[q01["mes"]]["carteira_v2"])
    c.valor("Q01 carteira um ano antes", q01["carteira_ativa_do_ano_anterior"],
            mart[q01["mes_do_ano_anterior"]]["carteira_v2"])

    q28 = resposta("Q28_totais")[0]
    c.valor("Q28 carteira total", q28["carteira_ativa"], mart[q28["mes"]]["carteira_v2"])

    ultimo = q01["mes"]
    q36 = resposta("Q36")[0]
    c.valor("Q36 carteira sem contagem no último mês",
            Decimal(q36["carteira_sem_contagem_no_ultimo_mes_pct"]) / 100, mart[ultimo]["supr_carteira"])
    c.valor("Q36 linhas sem contagem no último mês",
            Decimal(q36["linhas_sem_contagem_no_ultimo_mes_pct"]) / 100, mart[ultimo]["supr_recortes"])

    q37 = resposta("Q37")[0]
    c.valor("Q37 operações, limite inferior", q37["operacoes_limite_inferior"], mart[ultimo]["operacoes"])

    for linha in resposta("Q39"):
        m = mart[linha["mes"]]
        c.valor(f"Q39 V1 em {linha['mes']}", linha["carteira_v1"], m["carteira_v1"])
        c.valor(f"Q39 V2 em {linha['mes']}", linha["carteira_v2"], m["carteira_v2"])
        c.valor(f"Q39 diferença em {linha['mes']}", Decimal(linha["diferenca_pct"]) / 100, m["diferenca"])

    q40 = resposta("Q40")[0]
    c.valor("Q40 ambígua no último mês", Decimal(q40["ambigua_no_ultimo_mes_pct"]) / 100, mart[ultimo]["ambigua"])
    c.valor("Q40 inferida no último mês", Decimal(q40["inferida_no_ultimo_mes_pct"]) / 100, mart[ultimo]["inferida"])


def contra_carteira_mensal(c: Conferencia, w, wid: str) -> None:
    """
    PT: Q03, Q06 e Q07, refeitas das somas do mart, e não das taxas dele.
    EN: Q03, Q06 and Q07, rebuilt from the mart's sums, not its rates.
    """
    por_cliente = {
        (d, cl): Decimal(v)
        for d, cl, v in consultar(w, wid, f"""
            select cast(data_base as string), cliente, sum(carteira_ativa)
            from {MARTS}.mrt_carteira_mensal group by 1, 2""").linhas
    }
    for linha in resposta("Q03"):
        total = por_cliente[(linha["mes"], "PF")] + por_cliente[(linha["mes"], "PJ")]
        c.valor(f"Q03 participação PJ em {linha['mes']}",
                Decimal(linha["participacao_pj_pct"]) / 100, por_cliente[(linha["mes"], "PJ")] / total)

    por_modalidade = {
        (d, mod): (Decimal(car), Decimal(ina))
        for d, mod, car, ina in consultar(w, wid, f"""
            select cast(data_base as string), codigo_modalidade, sum(carteira_ativa), sum(carteira_inadimplencia)
            from {MARTS}.mrt_carteira_mensal group by 1, 2""").linhas
    }
    ultimo = resposta("Q01")[0]["mes"]
    seis_antes = max(d for d, _ in por_modalidade if d < ultimo and _meses_entre(d, ultimo) == 6)

    def taxa(data: str, modalidade: str) -> Decimal:
        carteira, inadimplida = por_modalidade[(data, modalidade)]
        return inadimplida / carteira

    for linha in resposta("Q06"):
        c.valor(f"Q06 taxa da modalidade {linha['codigo_modalidade']}",
                Decimal(linha["taxa_inadimplencia_pct"]) / 100, taxa(ultimo, linha["codigo_modalidade"]))
    for linha in resposta("Q07_pontos"):
        mod = linha["codigo_modalidade"]
        c.valor(f"Q07 variação da modalidade {mod}", Decimal(linha["variacao_pp"]) / 100,
                taxa(ultimo, mod) - taxa(seis_antes, mod))


def _meses_entre(inicio: str, fim: str) -> int:
    """PT: meses entre duas datas AAAA-MM-DD / EN: months between two dates"""
    return (int(fim[:4]) - int(inicio[:4])) * 12 + int(fim[5:7]) - int(inicio[5:7])


def contra_decisao(c: Conferencia, w, wid: str) -> None:
    """
    PT: Q14, leitura sem MEI: a carteira PJ por UF e o denominador do
        mrt_decisao, que usa as mesmas empresas por outra consulta.
    EN: Q14 without MEI, against mrt_decisao's portfolio and denominator.
    """
    mart = {
        uf: (Decimal(car), Decimal(emp))
        for uf, car, emp in consultar(w, wid, f"""
            select uf, sum(carteira_ativa), max(empresas)
            from {MARTS}.mrt_decisao group by uf""").linhas
    }
    for linha in resposta("Q14_empresariais_sem_mei"):
        carteira, empresas = mart[linha["uf"]]
        c.valor(f"Q14 carteira PJ de {linha['uf']}", linha["carteira_pj"], carteira)
        c.valor(f"Q14 empresas de {linha['uf']}", linha["empresas_ativas"], empresas)


def contra_reconciliacao(c: Conferencia, w, wid: str) -> None:
    """PT: Q30, parte 2 / EN: Q30, part 2"""
    ultimo = resposta("Q01")[0]["mes"]
    mart = {
        mod: (v1, v2)
        for mod, v1, v2 in consultar(w, wid, f"""
            select modalidade_v1, sum(carteira_v1_publicada), sum(carteira_v2_conformada)
            from {MARTS}.mrt_reconciliacao_versoes
            where data_base = date'{ultimo}'
            group by modalidade_v1""").linhas
    }
    for linha in resposta("Q30_comparabilidade"):
        v1, v2 = mart[linha["modalidade_v1"]]
        c.valor(f"Q30 V1 de {linha['modalidade_v1']}", linha["carteira_v1_publicada"], v1)
        c.valor(f"Q30 V2 conformada de {linha['modalidade_v1']}", linha["carteira_v2_conformada"], v2)


def contra_o_outro_lado_do_pix(c: Conferencia, w, wid: str) -> None:
    """
    PT: Q22 usa o lado pagador. No total do país o recebedor precisa dar o
        mesmo, com a diferença conhecida de cerca de R$ 1 milhão em dois meses
        de 2025 (ADR 0011), bem abaixo de uma parte por milhão.
    EN: Q22 uses the payer side; nationally the receiver side must match,
        within the known ~R$ 1 million gap in two 2025 months.
    """
    recebedor = {
        d: v
        for d, v in consultar(w, wid, f"""
            select cast(data_base as string), sum(valor) from {MARTS}.fct_pix
            where lado = 'recebedor' group by 1""").linhas
    }
    for linha in resposta("Q22"):
        c.valor(f"Q22 pagador contra recebedor em {linha['mes']}", linha["volume"], recebedor[linha["mes"]],
                tolerancia=Decimal("1e-6"))


# -----------------------------------------------------------------------------
# PT: Contra os documentos do projeto
# EN: Against the project's documents
# -----------------------------------------------------------------------------

def contra_documentos(c: Conferencia) -> None:
    """
    PT: Números escritos em documentos antes do gabarito existir.
    EN: Numbers written in documents before the answer key existed.
    """
    bi = Decimal(10**9)

    # PT: docs/cadeia-normativa.md, seção 6, medido na V1
    # EN: docs/cadeia-normativa.md, section 6, measured on V1
    q38 = por_chave(resposta("Q38_v1"), "medida")
    documento = {
        "carteira_ativa": ("6397.9", "6395.6", "0.0"),
        "carteira_inadimplida": ("195.4", "214.4", "9.7"),
        "ativo_problematico": ("421.0", "452.6", "7.5"),
        "ativo_problematico_sem_atraso_acima_de_90_dias": ("225.7", "238.2", "5.5"),
    }
    for medida, (antes, depois, variacao) in documento.items():
        linha = q38[medida]
        c.arredondado(f"Q38 {medida} em dez/2024", linha["valor_no_mes_anterior"], antes, bi)
        c.arredondado(f"Q38 {medida} em jan/2025", linha["valor_no_mes_da_quebra"], depois, bi)
        c.arredondado(f"Q38 {medida}, variação", abs(Decimal(linha["variacao_na_quebra_pct"])), variacao)

    # PT: ontology/metricas.yml, aviso do numero_de_operacoes
    # EN: ontology/metricas.yml, numero_de_operacoes warning
    q36 = resposta("Q36")[0]
    c.arredondado("Q36 carteira sem contagem no recorte", q36["carteira_sem_contagem_no_recorte_pct"], "6.71")
    c.arredondado("Q36 linhas sem contagem no recorte", q36["linhas_sem_contagem_no_recorte_pct"], "26.7")

    # PT: ADR 0003, conformação ambígua
    # EN: ADR 0003, ambiguous conformance
    q40 = resposta("Q40")[0]
    c.arredondado("Q40 ambígua no recorte", q40["ambigua_no_recorte_pct"], "2.71")
    c.valor("Q40 linhas ambíguas", q40["linhas_ambiguas_no_recorte"], 295134)


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    c = Conferencia()
    contra_limites_do_dado(c, w, wid)
    contra_carteira_mensal(c, w, wid)
    contra_decisao(c, w, wid)
    contra_reconciliacao(c, w, wid)
    contra_o_outro_lado_do_pix(c, w, wid)
    contra_documentos(c)

    print(f"  {c.total} conferências, {len(c.falhas)} divergências")
    if c.falhas:
        print("\nFALHOU / FAILED:")
        for f in c.falhas[:40]:
            print(f"  - {f}")
        sys.exit(1)
    print("  as respostas do gabarito batem com os marts, o outro lado do PIX e os documentos")


if __name__ == "__main__":
    main()
