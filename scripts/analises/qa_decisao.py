"""
PT: QA da camada de decisão (issue #26), independente do mart.

    Refaz a matriz de espaço contra risco por outro caminho: busca no
    Databricks só os totais dos fatos (fct_carteira, dim_modalidade e
    fct_empresas_ativas), sem passar pelo mrt_carteira_mensal nem pelo
    mrt_decisao, e aplica a regra do ADR 0014 em Python. Depois compara,
    célula a célula, o quadrante, o motivo de não avaliar, os dois custos de
    errar e o alerta antecipado.

    Os parâmetros são lidos do mesmo dbt_project.yml que o mart usa, para os
    dois caminhos aplicarem exatamente a mesma regra.

EN: Decision layer QA, independent from the mart. Rebuilds the room-to-grow
    versus risk matrix from the fact totals alone, applies the ADR 0014 rule
    in Python and compares quadrant, unrated reason, both costs and the early
    warning cell by cell. Parameters come from the same dbt_project.yml.

Uso / Usage:
    uv run python -m scripts.analises.qa_decisao
"""

from __future__ import annotations

import statistics
import sys
from decimal import Decimal

import yaml

from ingestion.databricks import cliente, executar_sql, warehouse
from ingestion.fontes import RAIZ

MARTS = "workspace.bcb_scr_marts"
# PT: tolerância relativa: o mart calcula as razões em double, e o QA em
#     Decimal exato; a diferença esperada é de arredondamento de ponto
#     flutuante, muito abaixo de um centavo por real.
# EN: relative tolerance: the mart computes ratios in double, the QA in exact
#     Decimal; the expected gap is floating-point rounding.
TOLERANCIA_RELATIVA = Decimal("1e-9")


def parametros() -> dict:
    """PT: as vars da decisão, do dbt_project.yml / EN: decision vars"""
    projeto = yaml.safe_load((RAIZ / "dbt" / "dbt_project.yml").read_text(encoding="utf-8"))
    return projeto["vars"]


def buscar(w, wid: str, sql: str) -> list[list[str]]:
    return executar_sql(w, wid, sql)


def totais(w, wid: str, meses: int) -> tuple[str, dict]:
    """
    PT: Carteira, inadimplida e ativo problemático por UF e modalidade, PJ,
        no último mês e no mês da comparação, direto do fato.
    EN: Portfolio, default and problem assets by state and modality, PJ, in
        the latest month and the comparison month, straight from the fact.
    """
    atual = buscar(w, wid, f"select cast(max(data_base) as string) from {MARTS}.fct_carteira")[0][0]
    linhas = buscar(w, wid, f"""
        select cast(f.data_base as string), f.uf, m.codigo_modalidade,
               sum(f.carteira_ativa), sum(f.carteira_inadimplencia), sum(f.ativo_problematico)
        from {MARTS}.fct_carteira f
        join {MARTS}.dim_modalidade m on m.codigo_submodalidade = f.codigo_submodalidade
        where f.cliente = 'PJ'
          and f.data_base in (date'{atual}', last_day(add_months(date'{atual}', -{meses})))
        group by 1, 2, 3""")
    celulas: dict = {}
    for data, uf, mod, car, ina, ap in linhas:
        lado = "atual" if data == atual else "anterior"
        celulas.setdefault((uf, mod), {})[lado] = (Decimal(car), Decimal(ina), Decimal(ap))
    return atual, celulas


def empresas(w, wid: str, data: str, grupo: str) -> dict[str, int]:
    """PT: denominador por UF / EN: denominator by state"""
    linhas = buscar(w, wid, f"""
        select uf, sum(empresas_ativas) from {MARTS}.fct_empresas_ativas
        where data_base = date'{data}' and grupo_natureza_juridica = '{grupo}' and not mei
        group by uf""")
    return {uf: int(n) for uf, n in linhas}


def classificar(celulas: dict, denominador: dict, p: dict) -> dict:
    """PT: a regra do ADR 0014, escrita de novo / EN: the rule, written again"""
    corte = Decimal(p["decisao_carteira_minima"])

    # PT: referência do país por modalidade, com todas as UFs
    # EN: national reference by modality, all states
    pais: dict = {}
    for (uf, mod), c in celulas.items():
        if "atual" not in c:
            continue
        soma = pais.setdefault(mod, [Decimal(0)] * 6)
        car, ina, ap = c["atual"]
        car0, ina0, ap0 = c.get("anterior", (Decimal(0),) * 3)
        for i, v in enumerate((car, ina, ap, car0, ina0, ap0)):
            soma[i] += v
    ref = {
        mod: {
            "var_taxa": s[1] / s[0] - s[4] / s[3],
            "var_dist": (s[2] - s[1]) / s[0] - (s[5] - s[4]) / s[3],
        }
        for mod, s in pais.items()
    }

    # PT: mediana da carteira por empresa, só entre as células acima do corte
    # EN: median portfolio per company, only over cells above the cut
    por_empresa: dict = {}
    for (uf, mod), c in celulas.items():
        if "atual" in c and c["atual"][0] >= corte:
            por_empresa.setdefault(mod, []).append(c["atual"][0] / denominador[uf])
    medianas = {mod: statistics.median(v) for mod, v in por_empresa.items()}

    resultado = {}
    for (uf, mod), c in celulas.items():
        if "atual" not in c:
            continue
        car, ina, ap = c["atual"]
        cpe = car / denominador[uf]
        if car < corte:
            motivo = "carteira abaixo do corte de materialidade"
        elif len(por_empresa.get(mod, [])) < p["decisao_minimo_de_ufs"]:
            motivo = "modalidade com poucas UFs acima do corte"
        elif "anterior" not in c:
            motivo = "sem o mês de comparação"
        else:
            motivo = None

        if motivo:
            resultado[(uf, mod)] = {"quadrante": "não avaliada", "motivo": motivo,
                                    "custo_nao_entrar": None, "custo_risco": None, "alerta": False}
            continue

        car0, ina0, ap0 = c["anterior"]
        var_taxa = ina / car - ina0 / car0
        var_dist = (ap - ina) / car - (ap0 - ina0) / car0
        espaco_alto = cpe < medianas[mod]
        piorando = var_taxa > ref[mod]["var_taxa"]
        quadrante = {(True, False): "entrar", (True, True): "observar",
                     (False, False): "manter", (False, True): "não entrar"}[(espaco_alto, piorando)]
        resultado[(uf, mod)] = {
            "quadrante": quadrante,
            "motivo": None,
            "custo_nao_entrar": (medianas[mod] - cpe) * denominador[uf] if espaco_alto else None,
            "custo_risco": car * max(var_taxa, Decimal(0)),
            "alerta": var_dist > 0 and var_dist > ref[mod]["var_dist"],
        }
    return resultado


def comparar(local: dict, w, wid: str) -> list[str]:
    """PT: célula a célula contra o mrt_decisao / EN: cell by cell against the mart"""
    mart = {
        (uf, mod): {"quadrante": q, "motivo": mot,
                    "custo_nao_entrar": Decimal(cn) if cn is not None else None,
                    "custo_risco": Decimal(cr) if cr is not None else None,
                    "alerta": al == "true"}
        for uf, mod, q, mot, cn, cr, al in buscar(w, wid, f"""
            select uf, codigo_modalidade, quadrante, motivo_nao_avaliada,
                   custo_de_nao_entrar, custo_do_risco, alerta_antecipado
            from {MARTS}.mrt_decisao""")
    }
    falhas = [f"{k}: só em um dos lados" for k in set(local) ^ set(mart)]
    for k in set(local) & set(mart):
        a, b = local[k], mart[k]
        for campo in ("quadrante", "motivo", "alerta"):
            if a[campo] != b[campo]:
                falhas.append(f"{k} {campo}: QA {a[campo]}, mart {b[campo]}")
        for campo in ("custo_nao_entrar", "custo_risco"):
            if (a[campo] is None) != (b[campo] is None) or (
                a[campo] is not None
                and abs(a[campo] - b[campo]) > TOLERANCIA_RELATIVA * max(abs(a[campo]), Decimal(1))
            ):
                falhas.append(f"{k} {campo}: QA {a[campo]}, mart {b[campo]}")
    return falhas


def main() -> None:
    p = parametros()
    w = cliente()
    wid = warehouse(w)
    atual, celulas = totais(w, wid, p["decisao_meses_de_tendencia"])
    local = classificar(celulas, empresas(w, wid, atual, p["decisao_grupo_natureza_juridica"]), p)

    contagem: dict = {}
    for r in local.values():
        contagem[r["quadrante"]] = contagem.get(r["quadrante"], 0) + 1
    print(f"  {atual}: {len(local)} células, " + ", ".join(f"{k} {v}" for k, v in sorted(contagem.items())))

    falhas = comparar(local, w, wid)
    if falhas:
        print("\nFALHOU / FAILED:")
        for f in falhas[:30]:
            print(f"  - {f}")
        sys.exit(1)
    print("  quadrante, motivo, custos e alerta idênticos ao mrt_decisao em todas as células")


if __name__ == "__main__":
    main()
