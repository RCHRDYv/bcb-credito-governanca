"""
PT: A checagem das variações no conjunto de desenvolvimento (#120, ADR 0033):
    lê as execuções de data/desenvolvimento/<variação>/, corrige cada uma
    pelo script, com o gabarito de desenvolvimento injetado no corretor e
    sem correção às cegas, e mostra, por variação e modelo:

    - o total das quatro condições juntas: certas, erradas, pendentes (o
      que só a correção às cegas decidiria), abstenções e erros;
    - as certas por papel da pergunta (controle positivo, controle negativo
      e mista), também com as quatro condições juntas;
    - por condição, só os erros técnicos (formato, contexto, SQL, guarda e
      tempo), para pegar uma quebra em B ou D sem mostrar qual condição
      acerta mais (decisão de 2026-10-23);
    - um aviso quando a execução está incompleta, com as execuções que
      faltam pelas seeds do ambiente.

    A checagem informa e não barra (ADR 0032 tirou o portão). Com uma seed
    só, não há maioria de 3 em 5: o número conta execuções, e não se compara
    direto ao do teste.

EN: The variants' check on the development set: script-only grading, per
    variant and model, totals over the four conditions together (right,
    wrong, pending, abstentions, errors), right answers per question role,
    and only technical errors per condition, so the check never shows which
    condition does better. Informational, not a gate.

Uso / Usage:
    uv run python -m scripts.analises.medida_do_desenvolvimento
    uv run python -m scripts.analises.medida_do_desenvolvimento --variacao V4 --variacao V6
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from assistente.parametros import CONDICOES
from correcao import acerto
from correcao.acerto import ler_execucoes
from experimento import desenvolvimento
from scripts.executar_experimento import PASTA_DO_DESENVOLVIMENTO, assinatura_dos_enunciados

VARIACOES_DA_CHECAGEM = ["V4", "V5", "V6"]
ERROS_TECNICOS = ("formato", "contexto", "sql", "guarda", "tempo")


def conferir_origem(variacao: str, registros: list[dict], ambientes: dict[str, dict],
                    por_id: dict[str, dict]) -> list[str]:
    """
    PT: Os registros e os ambientes da pasta são da variação que o nome da
        pasta diz, do conjunto de desenvolvimento e dos enunciados vigentes.
    EN: The folder's runs belong to its variant, the dev set and the
        current question texts.
    """
    problemas = []
    for modelo, ambiente in sorted(ambientes.items()):
        if ambiente.get("variacao") != variacao or ambiente.get("perguntas") != "desenvolvimento":
            problemas.append(f"{modelo}: ambiente da {ambiente.get('variacao')} no conjunto {ambiente.get('perguntas')}")
        if ambiente.get("enunciados") != assinatura_dos_enunciados(por_id):
            problemas.append(f"{modelo}: ambiente gravado com outros enunciados")
    problemas += [f"{r['candidato']} {r['id_pergunta']}: registro da {r.get('variacao')}"
                  for r in registros if r.get("variacao") != variacao]
    return problemas


def medir(registros: list[dict], corrigidas: list[dict], por_id: dict[str, dict], seeds: list[int]) -> dict:
    """
    PT: As medidas de um modelo numa variação, sem nada por condição além
        dos erros técnicos. A completude vem pelas chaves (condição,
        pergunta e seed das seeds do ambiente), e não pela contagem: uma
        execução repetida não cobre uma que falta.
    EN: One model's measures in a variant; only technical errors by
        condition. Completeness is checked by keys, not by count.
    """
    esperadas = {(c, i, s) for c in CONDICOES for i in por_id for s in seeds}
    feitas = {(r["condicao"], r["id_pergunta"], r["seed"]) for r in registros}
    papel = {i: p["papel"] for i, p in por_id.items()}
    situacoes = Counter(c["situacao"] for c in corrigidas)
    certas_por_papel = Counter(papel[c["pergunta"]] for c in corrigidas if c["situacao"] == "certo")
    total_por_papel = Counter(papel[c["pergunta"]] for c in corrigidas)
    abstencoes = sum(1 for r in registros if not r["erro"] and (r.get("resposta") or {}).get("abstencao"))
    erros = Counter(r["erro"]["tipo"] for r in registros if r["erro"])
    tecnicos = {c: Counter(r["erro"]["tipo"] for r in registros
                           if r["condicao"] == c and r["erro"] and r["erro"]["tipo"] in ERROS_TECNICOS)
                for c in CONDICOES}
    return {"execucoes": len(registros), "esperadas": len(esperadas), "faltam": len(esperadas - feitas),
            "certas": situacoes["certo"], "erradas": situacoes["errado"],
            "pendentes": situacoes["pendente"], "abstencoes": abstencoes, "erros": dict(sorted(erros.items())),
            "certas_por_papel": {p: f"{certas_por_papel[p]} de {total_por_papel[p]}" for p in desenvolvimento.PAPEIS},
            "erros_tecnicos_por_condicao": {c: dict(sorted(t.items())) for c, t in tecnicos.items()}}


def medir_variacao(pasta: Path, variacao: str, por_id: dict[str, dict]) -> dict[str, dict]:
    """PT: as medidas de cada modelo numa pasta / EN: per model in a folder"""
    registros = ler_execucoes(pasta, desenvolvimento.PADRAO)
    ambientes = {a.parent.name: json.loads(a.read_text(encoding="utf-8"))
                 for a in (pasta / "execucoes").glob("*/ambiente.json")}
    if problemas := conferir_origem(variacao, registros, ambientes, por_id):
        raise SystemExit(f"ERRO {pasta} não pode ser medida: {problemas[:5]}")
    corrigidas = acerto.corrigir_todas(registros, {}, desenvolvimento.carregar_gabarito(), com_condicao=True)
    return {m: medir([r for r in registros if r["candidato"] == m], [c for c in corrigidas if c["candidato"] == m],
                     por_id, (ambientes.get(m, {}).get("parametros") or {}).get("seeds") or [])
            for m in sorted({r["candidato"] for r in registros})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variacao", action="append", help=f"sem ela, {VARIACOES_DA_CHECAGEM}")
    args = parser.parse_args()

    _, por_id = desenvolvimento.perguntas()
    for variacao in args.variacao or VARIACOES_DA_CHECAGEM:
        pasta = PASTA_DO_DESENVOLVIMENTO / variacao
        if not (pasta / "execucoes").exists():
            print(f"\n{variacao}: nada rodado em {pasta}")
            continue
        for modelo, m in medir_variacao(pasta, variacao, por_id).items():
            print(f"\n{variacao}, {modelo}: {m['execucoes']} execuções, as quatro condições juntas")
            if m["faltam"] or not m["esperadas"]:
                print(f"  ATENÇÃO execução incompleta: faltam {m['faltam']} de {m['esperadas']}; rode o mesmo "
                      "comando do executor de novo, que ele retoma, antes de comparar as variações")
            print(f"  certas {m['certas']}, erradas {m['erradas']}, pendentes {m['pendentes']}, "
                  f"abstenções {m['abstencoes']}, erros {m['erros']}")
            print(f"  certas por papel: {m['certas_por_papel']}")
            print(f"  erros técnicos por condição: {m['erros_tecnicos_por_condicao']}")


if __name__ == "__main__":
    main()
