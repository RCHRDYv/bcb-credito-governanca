"""
PT: Gera dashboard/src/catalogo/exemplos.json, os dados reais que os gráficos
    do catálogo do design system mostram (#63).

    Nenhum número do arquivo é digitado à mão: tudo vem de consultas aos
    marts de apresentação no Databricks, pela máquina local e por OAuth
    (ADR 0016). O arquivo é pequeno de propósito: só o que cada exemplo usa.
    Com o mesmo dado, a saída é a mesma, byte a byte.

    Os exemplos são do catálogo, e não das visões. As visões leem os arquivos
    do contrato, que a exportação da #66 gera.

EN: Generates dashboard/src/catalogo/exemplos.json, the real data shown by
    the design system catalog's charts. Every number comes from a Databricks
    query on the presentation marts; same data, same bytes.

Uso / usage:
    uv run python -m scripts.gerar_exemplos_do_catalogo
"""

from __future__ import annotations

import json

import yaml

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import RAIZ

MARTS = "workspace.bcb_scr_marts"
SAIDA = RAIZ / "dashboard" / "src" / "catalogo" / "exemplos.json"

# PT: A modalidade dos exemplos por UF: Empréstimos (02) é avaliada nas 27 UFs.
# EN: The modality for the per-UF examples: evaluated in all 27 UFs.
MODALIDADE_POR_UF = "02"

# PT: Quantas modalidades ganham cor própria; as demais viram "Outros".
# EN: How many modalities get their own color; the rest become "Outros".
SERIES_COM_COR = 6

# PT: Casas decimais guardadas: reais em reais inteiros, frações com 6 casas.
# EN: Stored precision.
CASAS_FRACAO = 6


def nomes_das_modalidades() -> dict[str, str]:
    """
    PT: O nome oficial de cada modalidade (prefLabel da ontologia), pelo código.
    EN: Each modality's official name (ontology prefLabel), by code.
    """
    with open(RAIZ / "ontology" / "modalidades.yml", encoding="utf-8") as arquivo:
        ontologia = yaml.safe_load(arquivo)
    return {
        conceito["notation"]: conceito["prefLabel_pt"]
        for conceito in ontologia["conceitos"]
        if conceito.get("tipo") == "modalidade"
    }


def fracao(valor: str | None) -> float | None:
    """PT: fração com casas fixas / EN: fraction with fixed precision"""
    return None if valor is None else round(float(valor), CASAS_FRACAO)


def reais(valor: str | None) -> int | None:
    """PT: reais inteiros / EN: whole reais"""
    return None if valor is None else round(float(valor))


def carteira_por_modalidade(w, wid, nomes: dict[str, str]) -> dict:
    """
    PT: Carteira PJ do país por modalidade e mês, para o exemplo categórico.
        As seis maiores no último mês ganham cor; as outras somam "Outros".
    EN: Country PJ portfolio by modality and month; top six keep a color.
    """
    linhas = executar_sql(w, wid, f"""
        select data_base, codigo_modalidade, sum(carteira_ativa)
        from {MARTS}.mrt_carteira_mensal
        where cliente = 'PJ'
        group by data_base, codigo_modalidade
        order by data_base, codigo_modalidade""")
    meses = sorted({linha[0] for linha in linhas})
    ultimo = meses[-1]
    no_ultimo = {c: float(v) for d, c, v in linhas if d == ultimo}
    maiores = sorted(no_ultimo, key=lambda codigo: -no_ultimo[codigo])[:SERIES_COM_COR]

    valores: dict[str, dict[str, float]] = {}
    for data, codigo, valor in linhas:
        chave = codigo if codigo in maiores else "outros"
        valores.setdefault(chave, {}).setdefault(data, 0.0)
        valores[chave][data] += float(valor)

    series = [
        {"codigo": codigo, "nome": nomes[codigo], "valores": [reais(valores[codigo].get(m)) for m in meses]}
        for codigo in maiores
    ]
    series.append({"codigo": "outros", "nome": "Outros", "valores": [reais(valores["outros"].get(m)) for m in meses]})
    return {"meses": meses, "series": series}


def taxa_do_pais(w, wid) -> dict:
    """
    PT: Taxa de inadimplência PJ do país, mês a mês, como razão de somas.
    EN: Country PJ default rate by month, as a ratio of sums.
    """
    linhas = executar_sql(w, wid, f"""
        select data_base, sum(carteira_inadimplencia) / sum(carteira_ativa)
        from {MARTS}.mrt_carteira_mensal
        where cliente = 'PJ'
        group by data_base
        order by data_base""")
    return {"meses": [linha[0] for linha in linhas], "taxa": [fracao(linha[1]) for linha in linhas]}


def decisao(w, wid, nomes: dict[str, str]) -> tuple[dict, dict, dict]:
    """
    PT: As células da matriz, os valores por UF da modalidade escolhida e o
        número de destaque, todos do mrt_decisao.
    EN: Matrix cells, per-UF values and the highlight number, from mrt_decisao.
    """
    colunas = [
        "data_base", "uf", "codigo_modalidade", "carteira_ativa", "carteira_por_empresa",
        "mediana_carteira_por_empresa", "indice_de_espaco", "variacao_taxa_inadimplencia",
        "variacao_taxa_pais", "avaliada", "quadrante", "alerta_antecipado",
    ]
    linhas = [
        dict(zip(colunas, linha))
        for linha in executar_sql(w, wid, f"""
            select {", ".join(colunas)}
            from {MARTS}.mrt_decisao
            order by codigo_modalidade, uf""")
    ]

    avaliadas = [linha for linha in linhas if linha["avaliada"] == "true"]
    matriz = {
        "celulas": [
            {
                "uf": linha["uf"],
                "codigo_modalidade": linha["codigo_modalidade"],
                "modalidade": nomes[linha["codigo_modalidade"]],
                "carteira_ativa": reais(linha["carteira_ativa"]),
                "indice_de_espaco": fracao(linha["indice_de_espaco"]),
                "desvio_do_risco": fracao(
                    float(linha["variacao_taxa_inadimplencia"]) - float(linha["variacao_taxa_pais"])
                ),
                "quadrante": linha["quadrante"],
                "alerta_antecipado": linha["alerta_antecipado"] == "true",
            }
            for linha in avaliadas
        ]
    }

    da_modalidade = [linha for linha in linhas if linha["codigo_modalidade"] == MODALIDADE_POR_UF]
    por_uf = {
        "codigo_modalidade": MODALIDADE_POR_UF,
        "modalidade": nomes[MODALIDADE_POR_UF],
        "mediana_carteira_por_empresa": reais(da_modalidade[0]["mediana_carteira_por_empresa"]),
        "uf": [linha["uf"] for linha in da_modalidade],
        "carteira_por_empresa": [reais(linha["carteira_por_empresa"]) for linha in da_modalidade],
        "desvio_do_risco": [
            fracao(float(linha["variacao_taxa_inadimplencia"]) - float(linha["variacao_taxa_pais"]))
            for linha in da_modalidade
        ],
    }

    entrar = [linha for linha in avaliadas if linha["quadrante"] == "entrar"]
    destaque = {
        "quadrante": "entrar",
        "carteira_ativa": reais(sum(float(linha["carteira_ativa"]) for linha in entrar)),
        "celulas": len(entrar),
    }
    return matriz, por_uf, destaque


def main() -> None:
    w = cliente()
    wid = warehouse(w)
    nomes = nomes_das_modalidades()
    matriz, por_uf, destaque = decisao(w, wid, nomes)
    serie = carteira_por_modalidade(w, wid, nomes)
    exemplos = {
        "fonte": "SCR.data, do Banco Central, na camada gold do projeto",
        "data_base": serie["meses"][-1],
        "carteira_por_modalidade": serie,
        "taxa_do_pais": taxa_do_pais(w, wid),
        "por_uf": por_uf,
        "matriz": matriz,
        "destaque": destaque,
    }
    SAIDA.write_text(json.dumps(exemplos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gravado / written: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
