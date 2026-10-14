"""
PT: O resultado do experimento 2x2 (#50, ADRs 0013 e 0031). Lê os registros
    de data/experimento/, corrige cada execução (correcao.corretor e os
    julgamentos às cegas), conta as execuções certas de 0 a 5 por pergunta,
    condição e modelo, roda a estatística registrada
    (experimento.estatistica.analisar) e grava:

    - evaluation/experimento/resultado.json: por modelo, as contagens, as
      situações de cada execução, os erros por motivo, o ambiente e a
      análise inteira (condições, Q de Cochran, comparações com efeito,
      hipóteses, Holm e variância); as repetições por erro de servidor; o
      limite declarado; e os julgamentos às cegas;
    - evaluation/experimento/execucoes.jsonl.gz: os registros completos;
    - docs/experimento.md: a página gerada, sem número digitado.

    Para se faltar execução ou julgamento: a contagem de 0 a 5 só sai com
    tudo julgado (decisão 1 de 2026-10-14). Com --parcial, mostra o placar
    parcial e não grava nada. Com --do-publicado, refaz o resultado e a
    página a partir do que está publicado, sem a pasta data/.

EN: The 2x2 experiment result. Grades every run, counts right runs (0–5)
    per question, condition and model, runs the registered statistics and
    writes resultado.json, the compressed full records and the generated
    docs page. Stops if a run or a judgment is missing; --parcial prints a
    partial score; --do-publicado rebuilds from the published files.

Uso / Usage:
    uv run python -m scripts.resumir_experimento
    uv run python -m scripts.resumir_experimento --parcial
    uv run python -m scripts.resumir_experimento --do-publicado
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from assistente.parametros import CONDICOES
from correcao.acerto import (
    EXECUCOES_POR_PERGUNTA,
    PADRAO_DO_EXPERIMENTO,
    PASTA_DO_EXPERIMENTO,
    a_julgar,
    corrigir_todas,
    execucoes_vigentes,
    ler_execucoes,
    ler_julgamentos,
)
from correcao.corretor import carregar_gabarito
from experimento.contagem import contar
from experimento.estatistica import MAIORIA, MARGEM_DE_NAO_INFERIORIDADE, analisar
from scripts.executar_experimento import REPETICOES, SEED_DA_ORDEM, modelos_do_experimento
from scripts.resumir_selecao import gravar_execucoes as gravar_jsonl_gz
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import HIPOTESES, RAIZ

PASTA_DO_RESULTADO = RAIZ / "evaluation" / "experimento"
RESULTADO = PASTA_DO_RESULTADO / "resultado.json"
EXECUCOES = PASTA_DO_RESULTADO / "execucoes.jsonl.gz"
PAGINA = RAIZ / "docs" / "experimento.md"
RELATORIO = "experimento.pdf"
NOTEBOOK = "../notebooks/experimento.ipynb"


# -----------------------------------------------------------------------------
# PT: Contagem / EN: counting
# -----------------------------------------------------------------------------

def problemas_de_completude(execucoes: list[dict], corrigidas: list[dict], modelos: list[str],
                            ids: list[str]) -> list[str]:
    """PT: execuções ou julgamentos que faltam / EN: missing runs or judgments"""
    problemas = []
    esperadas = {(c, i, s) for c in CONDICOES for i in ids for s in range(1, EXECUCOES_POR_PERGUNTA + 1)}
    for m in modelos:
        feitas = {(r["condicao"], r["id_pergunta"], r["seed"]) for r in execucoes if r["candidato"] == m}
        if faltam := len(esperadas - feitas):
            problemas.append(f"{m}: faltam {faltam} execuções")
    if pendentes := a_julgar(corrigidas, todas=True):
        problemas.append(f"faltam {len(pendentes)} julgamentos às cegas (correcao.as_cegas --experimento)")
    return problemas


def montar(execucoes: list[dict], julgamentos: dict, ambientes: dict, repeticoes: list[dict],
           hipoteses: dict) -> tuple[dict, list[str]]:
    """
    PT: O resultado inteiro e as pendências. Sem pendência, a análise roda
        em cada modelo.
    EN: The full result and what is missing; analysis runs when complete.
    """
    _, por_id = perguntas(VIGENTE)
    ids = list(por_id)
    tipos = {i: p.get("tipo_de_acerto", "valor") for i, p in por_id.items()}
    modelos = [m["nome"] for m in modelos_do_experimento()]
    execucoes = execucoes_vigentes(execucoes, modelos, ids)
    g = carregar_gabarito()
    corrigidas = corrigir_todas(execucoes, julgamentos, g, com_condicao=True)
    problemas = problemas_de_completude(execucoes, corrigidas, modelos, ids)

    por_modelo = {}
    for m in modelos:
        situacoes, certas, erros = contar(corrigidas, m, ids)
        por_modelo[m] = {
            "ambiente": {k: (ambientes.get(m) or {}).get(k) for k in ("ollama", "digest_do_gguf", "variaveis",
                                                                       "inicio", "fim")},
            "erros_por_motivo": erros,
            "certas": certas,
            "execucoes": situacoes,
            "analise": None if problemas else analisar(certas, tipos, hipoteses),
        }
    mes = {r["mes_de_referencia"] for r in g.respostas.values()}
    fins = [(a.get("fim") or "")[:10] for a in ambientes.values()]
    resultado = {
        "metadata": {
            # PT: a data da última execução, e não a de hoje: refazer o
            #     resultado com os mesmos dados dá o mesmo arquivo.
            # EN: the last run's date, so the output reproduces.
            "gerado_em": max(fins, default="") or None,
            "issue": 50,
            "hipoteses": HIPOTESES,
            "mes_de_referencia": mes.pop() if len(mes) == 1 else sorted(mes),
            "perguntas": len(ids),
            "execucoes_por_pergunta": EXECUCOES_POR_PERGUNTA,
            "maioria": MAIORIA,
            "seed_da_ordem": SEED_DA_ORDEM,
            # PT: a permutação e o bootstrap da H5 dependem do fluxo do
            #     gerador do NumPy, que pode mudar entre versões.
            # EN: the H5 simulation depends on NumPy's generator stream.
            "numpy": np.__version__,
            "tipos_de_acerto": dict(sorted(Counter(tipos.values()).items())),
        },
        "limite_declarado": " ".join(hipoteses["estatistica"]["limite_declarado"].split()),
        "repeticoes_por_servidor": sorted(repeticoes, key=lambda r: (r["candidato"], r["inicio"])),
        "modelos": por_modelo,
        "julgamentos": dict(sorted(julgamentos.items())),
    }
    return resultado, problemas


# -----------------------------------------------------------------------------
# PT: Leitura e gravação / EN: reading and writing
# -----------------------------------------------------------------------------

def ler_publicado() -> tuple[list[dict], dict, dict, list[dict]]:
    """
    PT: Os registros, os julgamentos, os ambientes e as repetições já
        publicados: refazem o resultado sem a pasta data/.
    EN: The published records, judgments, environments and repetitions.
    """
    with gzip.open(EXECUCOES, "rt", encoding="utf-8") as arquivo:
        execucoes = [json.loads(linha) for linha in arquivo]
    resultado = json.loads(RESULTADO.read_text(encoding="utf-8"))
    ambientes = {m: p["ambiente"] for m, p in resultado["modelos"].items()}
    return execucoes, resultado["julgamentos"], ambientes, resultado["repeticoes_por_servidor"]


def ler_local(pasta: Path) -> tuple[list[dict], dict, dict, list[dict]]:
    """PT: o mesmo, da pasta data/experimento / EN: the same, from data/"""
    ambientes = {}
    for m in modelos_do_experimento():
        arquivo = pasta / "execucoes" / m["nome"] / "ambiente.json"
        ambientes[m["nome"]] = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    arquivo = pasta / REPETICOES
    repeticoes = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else []
    return ler_execucoes(pasta, PADRAO_DO_EXPERIMENTO), ler_julgamentos(pasta), ambientes, repeticoes


def gravar_execucoes(execucoes: list[dict]) -> None:
    """
    PT: Os registros num JSONL comprimido e determinístico, pelo mesmo
        gravador da seleção, com a condição na chave de ordenação.
    EN: Deterministic gzipped JSONL via the selection's writer, condition
        included in the sort key.
    """
    gravar_jsonl_gz(execucoes, EXECUCOES, chave=lambda r: (r["candidato"], r["condicao"], r["id_pergunta"], r["seed"]))


# -----------------------------------------------------------------------------
# PT: Página / EN: docs page
# -----------------------------------------------------------------------------

def _n(x: float, casas: int = 1) -> str:
    """PT: número com vírgula / EN: number with a decimal comma"""
    return f"{x:.{casas}f}".replace(".", ",").replace("-", "−")


def _p(p: float | None) -> str:
    if p is None:
        return "sem p"
    return "< 0,001" if p < 0.001 else _n(p, 3)


def _ic(ic: list[float]) -> str:
    return f"{_n(ic[0])} a {_n(ic[1])}"


DECISAO = {"sustentada": "sustentada", "nao_sustentada": "não sustentada"}


def linhas_das_hipoteses(analise: dict, hipoteses: dict) -> list[str]:
    """PT: a tabela das cinco hipóteses de um modelo / EN: one model's table"""
    linhas = ["| Hipótese | Comparação | Efeito (p.p.) | IC 95% (p.p.) | p | p ajustado (Holm) | Decisão |",
              "|---|---|---:|---|---:|---:|---|"]
    for nome, r in analise["hipoteses"].items():
        enunciado = hipoteses["hipoteses"][nome]["enunciado"].split(".")[0]
        if "comparacoes" in r:
            for i, (par, parte) in enumerate(r["comparacoes"].items()):
                rotulo = f"{nome}: {enunciado}" if i == 0 else ""
                ajustado = _p(r["p_ajustado"]) if i == 0 else ""
                decisao = DECISAO[r["decisao"]] if i == 0 else ""
                linhas.append(f"| {rotulo} | {par}, margem {_n(r['margem_pp'])} | {_n(parte['diferenca_pp'])} | "
                              f"{_ic(parte['ic95_pp'])} | {_p(parte['p'])} | {ajustado} | {decisao} |")
        elif "estatistica_pp" in r:
            linhas.append(f"| {nome}: {enunciado} (exploratória) | {r['comparacao']}, ressalva e abstenção menos "
                          f"valor | {_n(r['estatistica_pp'])} | {_ic(r['ic95_pp'])} | {_p(r['p'])} | fora do Holm | "
                          f"{DECISAO[r['decisao']]} |")
        else:
            linhas.append(f"| {nome}: {enunciado} | {r['comparacao']} ({r['perguntas']} perguntas) | "
                          f"{_n(r['diferenca_pp'])} | {_ic(r['ic95_pp'])} | {_p(r['p'])} | {_p(r['p_ajustado'])} | "
                          f"{DECISAO[r['decisao']]} |")
    return linhas


def pagina(resultado: dict, hipoteses: dict) -> str:
    """PT: docs/experimento.md / EN: the generated docs page"""
    meta, modelos = resultado["metadata"], resultado["modelos"]
    linhas = [
        "# Experimento 2x2: ontologia contra documentos",
        "",
        "<!-- PT: gerado por scripts/resumir_experimento.py; não edite à mão. "
        "EN: generated by scripts/resumir_experimento.py; do not edit by hand. -->",
        "",
        f"PT: O resultado do experimento registrado em `{meta['hipoteses']}` "
        "([ADR 0013](adr/0013-experimento-2x2-ontologia-contra-documentos.md), "
        "[ADR 0031](adr/0031-execucao-e-analise-do-experimento.md)). As "
        f"{meta['perguntas']} perguntas do `evaluation/questions_v3.yml` rodaram nas quatro condições (A só o "
        "esquema, B com a ontologia, C com os trechos dos documentos, D com os dois), nos dois modelos locais, "
        f"{meta['execucoes_por_pergunta']} vezes cada. Uma pergunta acerta numa condição quando {meta['maioria']} "
        "ou mais das 5 execuções acertam. O efeito é a diferença pareada de proporções, em pontos percentuais, com "
        "o intervalo de Newcombe de 95% (método 10).",
        "",
        "EN: Result of the pre-registered 2x2 experiment: 41 questions, four conditions, two local models, "
        "5 runs each; a question is right when 3 or more runs are right. Effects are paired differences in "
        "percentage points with Newcombe's 95% interval.",
        "",
        f"O relatório completo, com os gráficos e a memória de cálculo, está em [{RELATORIO}]({RELATORIO}), e o "
        f"notebook que o gera em [`notebooks/experimento.ipynb`]({NOTEBOOK}). Retrato do esquema estrela: "
        f"`{meta['mes_de_referencia']}`.",
        "",
        "## Limites",
        "",
        f"- {resultado['limite_declarado']}",
        "- A H5 é exploratória: fica fora do Holm, e o grupo de ressalva e abstenção tem "
        f"{meta['tipos_de_acerto'].get('valor_com_ressalva', 0) + meta['tipos_de_acerto'].get('abstencao', 0)} "
        "perguntas.",
        "- A seleção dos modelos ficou no piso na condição A (ADR 0030). Por isso o tamanho de efeito com o "
        "intervalo pesa mais que o p.",
        f"- Execuções repetidas por erro de servidor: {len(resultado['repeticoes_por_servidor'])} (ADR 0031).",
        "",
    ]
    for nome, m in modelos.items():
        a = m["analise"]
        linhas += [f"## {nome}", "", *linhas_das_hipoteses(a, hipoteses), ""]
        condicoes = a["condicoes"]
        linhas += [
            "Perguntas certas por condição, de " + str(a["perguntas"]) + ":",
            "",
            "| Condição | Certas | Valor | Com ressalva | Abstenção | As 5 execuções concordam "
            "| Abstenções indevidas (execuções) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for c, r in condicoes.items():
            t = r["por_tipo"]
            concordam = a["variancia"][c]["parcela_em_que_as_5_concordam"]
            indevidas = m["erros_por_motivo"][c].get("abstencao_indevida", 0)
            linhas.append(f"| {c} | {r['perguntas_certas']} | {t.get('valor', 0)} | {t.get('valor_com_ressalva', 0)} "
                          f"| {t.get('abstencao', 0)} | {_n(100 * concordam)}% | {indevidas} |")
        q = a["omnibus"]
        linhas += ["", "Q de Cochran nas quatro condições (descritivo): "
                   + (f"Q = {_n(q['q'], 2)}, {q['graus_de_liberdade']} graus de liberdade, p {_p(q['p'])}."
                      if q["q"] is not None else "não se define, sem variação dentro das perguntas."), ""]
    linhas += [
        "## Como ler",
        "",
        f"- Um efeito positivo quer dizer que a primeira condição acertou mais. A H4 é de não inferioridade: D "
        f"precisa ficar acima da margem de {_n(100 * MARGEM_DE_NAO_INFERIORIDADE)} p.p. contra B e contra C, e o "
        "p dela é o maior dos dois.",
        "- \"Não sustentada\" quer dizer que o dado não mostrou o efeito com o alfa de 0,05 depois do Holm. "
        "Não prova o contrário: o intervalo mostra o tamanho que o efeito pode ter.",
        "- Os números por pergunta, as tabelas pareadas e cada passo do Holm estão em "
        "`evaluation/experimento/resultado.json` e no relatório.",
        "",
    ]
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parcial", action="store_true", help="placar parcial, sem gravar")
    parser.add_argument("--pasta", type=Path, default=PASTA_DO_EXPERIMENTO)
    parser.add_argument("--do-publicado", action="store_true",
                        help="refaz a partir do execucoes.jsonl.gz e do resultado.json publicados, sem data/")
    args = parser.parse_args()

    hipoteses = yaml.safe_load((RAIZ / HIPOTESES).read_text(encoding="utf-8"))
    lidos = ler_publicado() if args.do_publicado else ler_local(args.pasta)
    resultado, problemas = montar(*lidos, hipoteses)
    for nome, m in resultado["modelos"].items():
        certas = {c: sum(n >= MAIORIA for n in por.values()) for c, por in m["certas"].items()}
        print(f"  {nome}: perguntas certas por condição {certas}")
    if args.parcial:
        print("\nParcial: nada gravado." + (f" Pendências: {problemas}" if problemas else ""))
        return
    if problemas:
        raise SystemExit("ERRO resultado incompleto: " + "; ".join(problemas))

    PASTA_DO_RESULTADO.mkdir(parents=True, exist_ok=True)
    RESULTADO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not args.do_publicado:
        gravar_execucoes(execucoes_vigentes(lidos[0], list(resultado["modelos"]), list(perguntas(VIGENTE)[1])))
    PAGINA.write_text(pagina(resultado, hipoteses), encoding="utf-8", newline="\n")
    print(f"\nGravados {RESULTADO.relative_to(RAIZ).as_posix()}, {EXECUCOES.relative_to(RAIZ).as_posix()} e "
          f"{PAGINA.relative_to(RAIZ).as_posix()}.")
    print("Próximo passo: o notebook, o relatório e a errata do resultado no evaluation/registro.yml.")


if __name__ == "__main__":
    main()
