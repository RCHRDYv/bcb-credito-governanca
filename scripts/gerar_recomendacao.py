"""
PT: Gera docs/recomendacao.md a partir do mrt_decisao (issue #26, ADR 0014).

    A recomendação é o produto final da v0.1, e por isso nenhum número dela é
    digitado à mão: o texto fixo explica a regra e declara a fronteira do
    dado, e todo número, inclusive os da fronteira, sai de uma consulta ao
    Databricks. Rodar de novo com o mesmo dado produz o mesmo arquivo, byte a
    byte, porque o documento não carrega data de geração, só a data-base.

    A fronteira do dado vem no começo, e não no fim (ADR 0005): quem lê a
    recomendação lê primeiro o que ela não pode afirmar.

EN: Generates docs/recomendacao.md from mrt_decisao. No number is typed by
    hand: fixed text explains the rule and states the data's limits, and
    every number, limits included, comes from a Databricks query. Same data,
    same file, byte for byte. The limits come first, not last (ADR 0005).

Uso / Usage:
    uv run python -m scripts.gerar_recomendacao
"""

from __future__ import annotations

from decimal import Decimal

import yaml

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import RAIZ

MARTS = "workspace.bcb_scr_marts"
DESTINO = RAIZ / "docs" / "recomendacao.md"
QUADRANTES = ("entrar", "observar", "não entrar", "manter")
MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


# -----------------------------------------------------------------------------
# PT: Formatação em português
# EN: Portuguese formatting
# -----------------------------------------------------------------------------

def numero(valor: float | Decimal, casas: int = 1) -> str:
    """PT: 1.234,5 / EN: Brazilian number format"""
    texto = f"{float(valor):,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def bilhoes(valor) -> str:
    return "" if valor is None else numero(Decimal(valor) / Decimal(10**9), 1)


def milhoes(valor) -> str:
    return "" if valor is None else numero(Decimal(valor) / Decimal(10**6), 1)


def pontos(valor) -> str:
    """
    PT: Fração em pontos percentuais, com sinal. Arredonda antes de decidir o
        sinal, para uma variação ínfima não aparecer como "-0,00".
    EN: Fraction as signed percentage points, rounded before choosing the sign.
    """
    v = round(float(valor) * 100, 2)
    if v == 0:
        return "0,00"
    return ("+" if v > 0 else "") + numero(v, 2)


def maiuscula(texto: str) -> str:
    """PT: só a primeira letra, sem mexer em siglas como UFs / EN: first letter only"""
    return texto[:1].upper() + texto[1:]


def mes(data: str) -> str:
    """PT: 2026-07-31 vira jul/2026 / EN: 2026-07-31 becomes jul/2026"""
    return f"{MESES[int(data[5:7]) - 1]}/{data[:4]}"


# -----------------------------------------------------------------------------
# PT: Consultas
# EN: Queries
# -----------------------------------------------------------------------------

def consultar(w, wid: str) -> dict:
    """PT: tudo o que o documento cita / EN: everything the document cites"""
    colunas = (
        "cast(data_base as string), cast(data_base_anterior as string), uf, modalidade, quadrante, "
        "carteira_ativa, empresas, carteira_por_empresa, indice_de_espaco, taxa_inadimplencia, "
        "variacao_taxa_inadimplencia, variacao_taxa_pais, custo_de_nao_entrar, custo_do_risco, "
        "alerta_antecipado, avaliada, motivo_nao_avaliada"
    )
    nomes = [c.split(" as ")[-1].split(".")[-1].strip(" ,()") for c in colunas.split(", ")]
    nomes[0], nomes[1] = "data_base", "data_base_anterior"
    linhas = [dict(zip(nomes, l)) for l in executar_sql(w, wid, f"select {colunas} from {MARTS}.mrt_decisao")]

    suprimida = executar_sql(w, wid, f"select avg(case when contagem_suprimida then 1.0 else 0 end) from {MARTS}.fct_carteira")[0][0]
    erro = executar_sql(w, wid, f"""
        select retrato, max(abs(erro_relativo)), sum(empresas_ativas_reconstruida) / sum(empresas_ativas_real) - 1
        from {MARTS}.mrt_erro_da_reconstrucao group by retrato order by retrato""")
    return {"celulas": linhas, "suprimida": Decimal(suprimida), "erro": erro}


# -----------------------------------------------------------------------------
# PT: Seções
# EN: Sections
# -----------------------------------------------------------------------------

def secao_fronteira(dados: dict) -> str:
    antigo = dados["erro"][0]
    return f"""## O que este dado não permite afirmar

Esta lista vem antes da recomendação de propósito. Uma recomendação sem ela é palpite com gráfico.

- **Rentabilidade, spread e custo de captação.** O SCR.data não tem taxa de juros nem receita. "Entrar" quer dizer que há espaço de carteira e que o risco não piora mais que no país, e não que a operação dá lucro.
- **Instituição específica.** O dado é agregado por segmento, e não diz como um banco ou uma financeira em particular se comporta.
- **Risco de um cliente ou de uma safra.** Não há dado por operação nem por data de contratação.
- **Local da operação.** A UF é a do domicílio da pessoa ou da sede da empresa, e não onde o crédito foi usado.
- **Número exato de empresas por mês.** O denominador é reconstruído de um único retrato do cadastro da Receita (ADR 0009). O erro medido chegou a {numero(Decimal(antigo[1]) * 100, 2)}% por UF no retrato mais antigo ({mes(antigo[0] + '-01')}).
- **Número de operações em parte do dado.** A contagem aparece suprimida em {numero(dados['suprimida'] * 100, 1)}% das linhas do SCR, e por isso a matriz não usa contagem de operações.
- **O custo de errar é ordem de grandeza, e não perda.** O custo do risco mede o aumento da carteira inadimplida atribuível à piora da taxa. Sem taxa de recuperação, não dá para dizer quanto disso vira prejuízo.
"""


def secao_regra(dados: dict, p: dict) -> str:
    c = dados["celulas"][0]
    return f"""## A regra

Cada célula é uma UF e uma modalidade de crédito, só para pessoa jurídica, em {mes(c['data_base'])}, comparada com {mes(c['data_base_anterior'])}. A regra completa, com as alternativas descartadas, está no [ADR 0014](adr/0014-matriz-de-decisao-espaco-contra-risco.md).

- **Espaço:** a carteira PJ da modalidade na UF, dividida pelo número de empresas ativas de natureza empresarial, sem MEI, da UF. Abaixo da mediana das UFs na mesma modalidade, o espaço é alto.
- **Risco:** a variação da taxa de inadimplência em {p['decisao_meses_de_tendencia']} meses. Se sobe mais que a da mesma modalidade no país inteiro, o risco está piorando.
- **Materialidade:** só entram células com carteira PJ de pelo menos R$ {bilhoes(p['decisao_carteira_minima'])} bi, em modalidades com pelo menos {p['decisao_minimo_de_ufs']} UFs acima desse corte.

| | Risco estável ou melhorando | Risco piorando |
|---|---|---|
| **Espaço alto** | **Entrar** | **Observar:** há espaço, mas o risco pede espera |
| **Espaço baixo** | **Manter** | **Não entrar** |

**O custo de errar vai nas duas direções.** Deixar de entrar onde havia espaço custa a carteira que faltaria para a UF chegar à mediana. Entrar onde o risco piora custa o aumento da carteira inadimplida atribuível à piora.

**O alerta antecipado** marca a célula em que a distância entre ativo problemático e carteira inadimplida abriu mais que a do país. É a piora que o atraso ainda não mostra, e não muda o quadrante.
"""


def secao_resumo(dados: dict) -> str:
    linhas = ["## Resumo", "", "| Quadrante | Células | Carteira PJ (R$ bi) | Custo de não entrar (R$ bi) | Custo do risco (R$ bi) | Com alerta antecipado |", "|---|---|---|---|---|---|"]
    for q in (*QUADRANTES, "não avaliada"):
        cel = [c for c in dados["celulas"] if c["quadrante"] == q]
        soma = lambda campo: sum(Decimal(c[campo]) for c in cel if c[campo] is not None)
        alerta = sum(1 for c in cel if c["alerta_antecipado"] == "true")
        linhas.append(
            f"| {maiuscula(q)} | {len(cel)} | {bilhoes(soma('carteira_ativa'))} | "
            f"{bilhoes(soma('custo_de_nao_entrar')) if q in ('entrar', 'observar') else ''} | "
            f"{bilhoes(soma('custo_do_risco')) if q != 'não avaliada' else ''} | {alerta if q != 'não avaliada' else ''} |"
        )
    return "\n".join(linhas) + "\n"


def tabela(celulas: list[dict], ordem: str) -> str:
    cabecalho = (
        "| UF | Modalidade | Carteira PJ (R$ bi) | Carteira por empresa (R$ mil) | Índice de espaço | "
        "Taxa de inadimplência | Variação da taxa (p.p.) | Variação no país (p.p.) | "
        "Custo de não entrar (R$ bi) | Custo do risco (R$ mi) | Alerta |\n|---|---|---|---|---|---|---|---|---|---|---|"
    )
    ordenadas = sorted(celulas, key=lambda c: Decimal(c[ordem] or 0), reverse=True)
    linhas = [
        f"| {c['uf']} | {' '.join(c['modalidade'].split())} | {bilhoes(c['carteira_ativa'])} | "
        f"{numero(Decimal(c['carteira_por_empresa']) / 1000, 1)} | {numero(Decimal(c['indice_de_espaco']), 2)} | "
        f"{numero(Decimal(c['taxa_inadimplencia']) * 100, 2)}% | {pontos(c['variacao_taxa_inadimplencia'])} | "
        f"{pontos(c['variacao_taxa_pais'])} | {bilhoes(c['custo_de_nao_entrar'])} | {milhoes(c['custo_do_risco'])} | "
        f"{'sim' if c['alerta_antecipado'] == 'true' else ''} |"
        for c in ordenadas
    ]
    return cabecalho + "\n" + "\n".join(linhas) + "\n"


def secao_quadrantes(dados: dict) -> str:
    textos = {
        "entrar": ("Onde entrar", "Espaço acima da mediana e risco que não piora mais que o país. Ordenado pelo custo de não entrar: o topo da lista é onde deixar de crescer custa mais.", "custo_de_nao_entrar"),
        "observar": ("Onde observar", "Há espaço, mas a inadimplência sobe mais que no país. Ordenado pelo custo do risco: o topo é onde entrar agora pesaria mais.", "custo_do_risco"),
        "não entrar": ("Onde não entrar", "Carteira por empresa já acima da mediana e risco piorando mais que o país. Ordenado pelo custo do risco.", "custo_do_risco"),
        "manter": ("Onde manter", "Carteira por empresa já acima da mediana e risco que não piora mais que o país. Ordenado pela carteira.", "carteira_ativa"),
    }
    partes = []
    for q in QUADRANTES:
        titulo, texto, ordem = textos[q]
        cel = [c for c in dados["celulas"] if c["quadrante"] == q]
        partes.append(f"## {titulo} ({len(cel)} células)\n\n{texto}\n\n{tabela(cel, ordem)}")
    return "\n".join(partes)


def secao_nao_avaliadas(dados: dict) -> str:
    motivos: dict = {}
    for c in dados["celulas"]:
        if c["avaliada"] == "false":
            n, s = motivos.get(c["motivo_nao_avaliada"], (0, Decimal(0)))
            motivos[c["motivo_nao_avaliada"]] = (n + 1, s + Decimal(c["carteira_ativa"]))
    linhas = ["## Fora da matriz", "", "Células que ficam de fora, com o motivo. Continuam no `mrt_decisao`, marcadas como não avaliadas.", "", "| Motivo | Células | Carteira PJ (R$ bi) |", "|---|---|---|"]
    linhas += [f"| {maiuscula(m)} | {n} | {bilhoes(s)} |" for m, (n, s) in sorted(motivos.items())]
    return "\n".join(linhas) + "\n"


def main() -> None:
    projeto = yaml.safe_load((RAIZ / "dbt" / "dbt_project.yml").read_text(encoding="utf-8"))
    p = projeto["vars"]
    w = cliente()
    dados = consultar(w, warehouse(w))

    c = dados["celulas"][0]
    cabecalho = f"""# Recomendação: onde crescer em crédito para empresas, e onde o risco pesa

**Data-base:** {mes(c['data_base'])}. Gerado por `scripts/gerar_recomendacao.py` a partir do `mrt_decisao`. Nenhum número deste documento é digitado à mão: para atualizar, rode o script de novo.

A pergunta de negócio (ADR 0005): uma financeira quer crescer em crédito para pessoa jurídica. Em quais estados e modalidades vale aumentar a exposição, e onde o risco está piorando rápido demais para isso?
"""
    texto = "\n".join([cabecalho, secao_fronteira(dados), secao_regra(dados, p), secao_resumo(dados), secao_quadrantes(dados), secao_nao_avaliadas(dados)])
    DESTINO.write_text(texto, encoding="utf-8", newline="\n")
    print(f"  > {DESTINO.relative_to(RAIZ)}: {len(dados['celulas'])} células")


if __name__ == "__main__":
    main()
