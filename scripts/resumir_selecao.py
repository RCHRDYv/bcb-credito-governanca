"""
PT: O resultado da seleção dos modelos (#48, ADRs 0026 e 0030). Lê os
    registros de data/selecao/, corrige cada execução (correcao.corretor e
    os julgamentos às cegas), aplica a regra de escolha e de desempate do
    evaluation/selecao.yml e grava:

    - evaluation/selecao/resultado.json: por candidato, as execuções de cada
      pergunta (certo, errado ou não julgada, porque a pergunta já estava
      decidida), as perguntas certas, os erros por motivo, a VRAM e o
      ambiente; os escolhidos; e os julgamentos às cegas;
    - evaluation/selecao/execucoes.jsonl.gz: os registros completos;
    - docs/selecao-dos-modelos.md: a página gerada, sem número digitado;
    - assistente/parametros.yml: a lista de modelos troca pelos dois
      escolhidos, com o num_ctx e a razão medidos, e sai o provisorio.

    Para se faltar execução ou julgamento que ainda muda o acerto. Com
    --parcial, mostra o placar parcial e não grava nada.

EN: The model selection result. Grades every recorded run (script grader
    plus blind judgments), applies the choice and tie-break rules, and
    writes resultado.json, the compressed full records, the generated docs
    page and the final model list in parametros.yml. Stops if a run or a
    result-changing judgment is missing; --parcial prints a partial score.

Uso / Usage:
    uv run python -m scripts.resumir_selecao
    uv run python -m scripts.resumir_selecao --parcial
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
from collections import Counter
from pathlib import Path

from correcao.acerto import (
    EXECUCOES_POR_PERGUNTA,
    PASTA_DA_SELECAO,
    a_julgar,
    acerto_da_pergunta,
    corrigir_todas,
    execucoes_vigentes,
    ler_execucoes,
    ler_julgamentos,
    por_pergunta,
)
from correcao.corretor import carregar_gabarito
from scripts.selecionar_modelos import SELECAO, carregar_selecao
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import RAIZ

PASTA_DO_RESULTADO = RAIZ / "evaluation" / "selecao"
RESULTADO = PASTA_DO_RESULTADO / "resultado.json"
EXECUCOES = PASTA_DO_RESULTADO / "execucoes.jsonl.gz"
PAGINA = RAIZ / "docs" / "selecao-dos-modelos.md"
PARAMETROS = RAIZ / "assistente" / "parametros.yml"


# -----------------------------------------------------------------------------
# PT: Placar e escolha / EN: score and choice
# -----------------------------------------------------------------------------

def motivo_do_erro(c: dict) -> str:
    if c["correcao"]["situacao"] == "errado":
        return c["correcao"]["motivo"]
    negados = [a for a in c["correcao"]["julgar"] if (c["julgamento"] or {}).get(a) is False]
    return f"julgamento_{negados[0]}" if negados else ""


def ler_publicado() -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    """
    PT: Os registros, os julgamentos e os ambientes já publicados no
        repositório: refazem o resultado sem a pasta data/.
    EN: The published records, judgments and environments, to rebuild the
        result without data/.
    """
    with gzip.open(EXECUCOES, "rt", encoding="utf-8") as arquivo:
        execucoes = [json.loads(linha) for linha in arquivo]
    resultado = json.loads(RESULTADO.read_text(encoding="utf-8"))
    ambientes = {p["nome"]: p["ambiente"] for p in resultado["candidatos"]}
    return execucoes, resultado["julgamentos"], ambientes


def placar(candidato: dict, corrigidas: list[dict], ids: list[str], tipos: dict[str, str],
           ambiente: dict) -> dict:
    """PT: o resultado de um candidato / EN: one candidate's result"""
    grupos = por_pergunta([c for c in corrigidas if c["candidato"] == candidato["nome"]])
    por_pergunta_ = {}
    for id_ in ids:
        grupo = grupos.get((candidato["nome"], id_), [])
        situacoes = [c["situacao"] for c in grupo]
        por_pergunta_[id_] = {
            "execucoes": ["nao_julgada" if s == "pendente" else s for s in situacoes],
            "certas": situacoes.count("certo"),
            "acerto": acerto_da_pergunta(situacoes),
        }
    certas = [i for i, p in por_pergunta_.items() if p["acerto"] == "certo"]
    erros = Counter(m for c in corrigidas if c["candidato"] == candidato["nome"] and (m := motivo_do_erro(c)))
    return {
        **{k: candidato[k] for k in ("nome", "classe", "ollama", "repositorio", "revisao", "arquivo", "sha256",
                                     "quantizacao", "num_ctx", "caracteres_por_token")},
        "perguntas_certas": len(certas),
        "certas_por_tipo": dict(sorted(Counter(tipos[i] for i in certas).items())),
        "erros_por_motivo": dict(sorted(erros.items())),
        "vram": (ambiente.get("vram") or {}).get("size_vram"),
        "ambiente": {k: ambiente.get(k) for k in ("ollama", "digest_do_gguf", "variaveis", "vram", "inicio", "fim")},
        "perguntas": por_pergunta_,
    }


def escolher(placares: list[dict]) -> dict[str, str]:
    """
    PT: Em cada classe, mais perguntas certas; no empate, menor VRAM; e,
        persistindo, o primeiro da classe no selecao.yml (a ordem da lista).
    EN: Per class, most right questions; ties by lower VRAM, then list order.
    """
    escolhidos = {}
    for classe in dict.fromkeys(p["classe"] for p in placares):
        da_classe = [p for p in placares if p["classe"] == classe]
        melhor = min(enumerate(da_classe),
                     key=lambda par: (-par[1]["perguntas_certas"], par[1]["vram"] or float("inf"), par[0]))[1]
        escolhidos[classe] = melhor["nome"]
    return escolhidos


# -----------------------------------------------------------------------------
# PT: Gravação / EN: writing
# -----------------------------------------------------------------------------

def gravar_execucoes(execucoes: list[dict]) -> None:
    """PT: JSONL comprimido, determinístico / EN: deterministic gzipped JSONL"""
    ordenadas = sorted(execucoes, key=lambda r: (r["candidato"], r["id_pergunta"], r["seed"]))
    texto = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in ordenadas)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as arquivo:
        arquivo.write(texto.encode("utf-8"))
    EXECUCOES.write_bytes(buffer.getvalue())


def _gib(bytes_: int | None) -> str:
    """PT: bytes em GiB, com vírgula / EN: bytes as GiB"""
    return "—" if bytes_ is None else f"{bytes_ / 1024 ** 3:.1f}".replace(".", ",")


def pagina(resultado: dict, selecao: dict, ids: list[str]) -> str:
    """PT: docs/selecao-dos-modelos.md / EN: the generated docs page"""
    placares = resultado["candidatos"]
    escolhidos = set(resultado["escolhidos"].values())
    linhas = [
        "# Seleção dos modelos do experimento",
        "",
        "<!-- PT: gerado por scripts/resumir_selecao.py; não edite à mão. "
        "EN: generated by scripts/resumir_selecao.py; do not edit by hand. -->",
        "",
        "PT: O resultado da seleção dos dois modelos locais do experimento, um por classe, pelas 41 perguntas do "
        "`evaluation/questions_v3.yml` na condição A, só com o esquema ([ADR 0026](adr/0026-modelos-do-experimento-"
        "escolhidos-pela-condicao-a.md), [ADR 0030](adr/0030-selecao-dos-modelos-pelo-gabarito.md)). Cada pergunta "
        "rodou 5 vezes, com as seeds de 1 a 5 e temperatura de 0,2, e acerta quando 3 ou mais das 5 execuções "
        "acertam. Fica, em cada classe, o candidato com mais perguntas certas; o empate se resolve pela menor VRAM.",
        "",
        "EN: Result of selecting the experiment's two local models, one per class, on the 41 registered questions in "
        "condition A. Each question ran 5 times and is right when 3 or more runs are right; the candidate with most "
        "right questions wins its class, ties broken by lower VRAM.",
        "",
        f"Retrato do esquema estrela: `{resultado['metadata']['mes_de_referencia']}`. "
        f"Ollama: `{', '.join(sorted({p['ambiente']['ollama'] or '—' for p in placares}))}`. "
        f"Cache KV: `{selecao['servidor']['OLLAMA_KV_CACHE_TYPE']}`.",
        "",
        "## Placar",
        "",
        "| Classe | Candidato | Quantização | Perguntas certas | Valor | Com ressalva | Abstenção | Na GPU (GiB) "
        "| Total (GiB) | num_ctx |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in placares:
        nome = f"**{p['nome']}**" if p["nome"] in escolhidos else p["nome"]
        tipos = p["certas_por_tipo"]
        linhas.append(f"| {p['classe']} | {nome} | {p['quantizacao']} | {p['perguntas_certas']} de {len(ids)} | "
                      f"{tipos.get('valor', 0)} | {tipos.get('valor_com_ressalva', 0)} | {tipos.get('abstencao', 0)} | "
                      f"{_gib(p['vram'])} | {_gib((p['ambiente'].get('vram') or {}).get('size'))} | {p['num_ctx']} |")
    linhas += [
        "",
        "Em negrito, os escolhidos. \"Na GPU\" é o `size_vram` do `/api/ps`, que decide o empate; \"Total\" é o "
        "`size`, e a diferença entre os dois ficou na CPU. A versão exata de cada candidato (repositório, revisão e sha256 do GGUF) está "
        "em `evaluation/selecao.yml` e em `evaluation/selecao/resultado.json`.",
        "",
        "## Erros por motivo",
        "",
        f"Contagem de execuções erradas, de {len(ids) * EXECUCOES_POR_PERGUNTA} por candidato. "
        "`valor`: os números não batem com nenhuma leitura; "
        "`abstencao_indevida`: absteve-se numa pergunta com resposta; `sem_abstencao`: respondeu numa pergunta de "
        "abstenção; `sem_ressalva`: ressalva vazia numa pergunta de valor com ressalva; `erro_<tipo>`: a execução falhou (formato, sql, guarda, tempo, contexto, servidor); "
        "`julgamento_<aspecto>`: reprovada na correção às cegas.",
        "",
    ]
    motivos = sorted({m for p in placares for m in p["erros_por_motivo"]})
    linhas += ["| Candidato | " + " | ".join(f"`{m}`" for m in motivos) + " |",
               "|---|" + "---:|" * len(motivos)]
    for p in placares:
        linhas.append(f"| {p['nome']} | " + " | ".join(str(p["erros_por_motivo"].get(m, 0)) for m in motivos) + " |")
    linhas += [
        "",
        "## Execuções certas por pergunta",
        "",
        "De 0 a 5. Com `*`, a pergunta acerta. Execução não julgada conta como não certa: a pergunta já estava "
        "decidida, e o julgamento não mudaria o resultado.",
        "",
        "| Pergunta | " + " | ".join(p["nome"] for p in placares) + " |",
        "|---|" + "---:|" * len(placares),
    ]
    for id_ in ids:
        celulas = []
        for p in placares:
            q = p["perguntas"][id_]
            celulas.append(f"{q['certas']}{'*' if q['acerto'] == 'certo' else ''}")
        linhas.append(f"| {id_} | " + " | ".join(celulas) + " |")
    linhas += [
        "",
        "## Limites declarados",
        "",
        "- A seleção pela condição A é conservadora contra a H1 e a H2: o modelo que fica é o que se vira melhor "
        "sem contexto, e tem menos a ganhar com a ontologia e os documentos (ADR 0026, decisão 6).",
        "- A seleção usa as mesmas 41 perguntas do experimento. A execução da seleção não entra no experimento: a "
        "condição A roda de novo, com o modelo escolhido (ADR 0026, decisão 4).",
        "- A condição A não é só esquema: as `dim_*` trazem definição, confiança e fonte, que o modelo pode ler "
        "por SQL (ADR 0029, consequências).",
        "",
    ]
    return "\n".join(linhas)


CABECALHO_DOS_PARAMETROS = """\
# =============================================================================
# PT: Parâmetros do assistente de dados (#49, ADR 0029; #48, ADR 0030). O
#     pré-registro (evaluation/hipoteses.yml, execucao.fixado_antes_da_execucao)
#     manda fixar o modelo, o num_ctx, o limite de tokens da resposta e os
#     limites de linhas e de tempo antes do experimento.
#
#     Os modelos são os dois escolhidos pela seleção da #48
#     (evaluation/selecao/resultado.json), gravados por
#     scripts.resumir_selecao. A geração e os limites do SQL repetem o
#     evaluation/selecao.yml, com o qual a seleção rodou;
#     scripts.validar_selecao confere que batem. O arquivo está congelado por
#     errata no evaluation/registro.yml.
#
#     O num_ctx de cada modelo foi medido com o cache KV em 8 bits: o ollama
#     serve precisa de OLLAMA_KV_CACHE_TYPE=q8_0 e OLLAMA_FLASH_ATTENTION=1
#     (evaluation/selecao.yml, servidor), como na seleção.
#
#     A temperatura e as seeds já estão no pré-registro e são conferidas
#     contra ele por assistente.parametros.conferir_pre_registro().
#
# EN: Data assistant parameters. The models are the two chosen by the #48
#     selection; generation settings and SQL limits repeat
#     evaluation/selecao.yml. Frozen by errata. num_ctx was measured with an
#     8-bit KV cache: ollama serve needs OLLAMA_KV_CACHE_TYPE=q8_0 and
#     OLLAMA_FLASH_ATTENTION=1. Temperature and seeds are pre-registered.
# =============================================================================
"""


def atualizar_parametros(texto: str, selecao: dict, escolhidos: dict[str, str]) -> str:
    """
    PT: Troca a lista de modelos do parametros.yml pelos escolhidos, na
        ordem das classes, tira o provisorio e reescreve o cabeçalho, que
        deixa de falar em estado provisório.
    EN: Replaces parametros.yml's model list with the chosen ones, drops
        provisorio and rewrites the header.
    """
    por_nome = {c["nome"]: c for c in selecao["candidatos"]}
    blocos = []
    for classe, nome in escolhidos.items():
        c = por_nome[nome]
        blocos.append(
            f'  - nome: "{c["ollama"]}"\n'
            f'    classe: "{classe}"\n'
            f'    repositorio: "{c["repositorio"]}"\n'
            f'    revisao: "{c["revisao"]}"\n'
            f'    sha256: "{c["sha256"]}"\n'
            f"    num_ctx: {c['num_ctx']}\n"
            f"    caracteres_por_token_na_estimativa: {c['caracteres_por_token']}\n"
        )
    inicio = texto.index("modelos:\n")
    fim = texto.index("\ngeracao:\n")
    novo = ("modelos:\n"
            "  # PT: os dois modelos do experimento, escolhidos pela seleção da #48\n"
            "  #     (evaluation/selecao/resultado.json), gravados por\n"
            "  #     scripts.resumir_selecao. O primeiro é o padrão.\n"
            "  # EN: the experiment's two models, chosen by the #48 selection.\n"
            + "".join(blocos))
    texto = texto[:inicio] + novo + texto[fim:]
    texto = re.sub(r"(?m)^provisorio: true\n\n?", "", texto)
    return CABECALHO_DOS_PARAMETROS + "\n" + texto[texto.index("servidor:\n"):]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parcial", action="store_true", help="placar parcial, sem gravar")
    parser.add_argument("--pasta", type=Path, default=PASTA_DA_SELECAO)
    parser.add_argument("--do-publicado", action="store_true",
                        help="refaz a partir do execucoes.jsonl.gz e do resultado.json publicados, sem data/")
    args = parser.parse_args()

    selecao = carregar_selecao()
    _, por_id = perguntas(VIGENTE)
    ids = list(por_id)
    tipos = {i: p.get("tipo_de_acerto", "valor") for i, p in por_id.items()}
    if args.do_publicado:
        execucoes_lidas, julgamentos, ambientes_publicados = ler_publicado()
    else:
        execucoes_lidas, julgamentos, ambientes_publicados = ler_execucoes(args.pasta), ler_julgamentos(args.pasta), None
    execucoes = execucoes_vigentes(execucoes_lidas, [c["nome"] for c in selecao["candidatos"]], ids)
    g = carregar_gabarito()
    corrigidas = corrigir_todas(execucoes, julgamentos, g)

    problemas = []
    for c in selecao["candidatos"]:
        feitas = {(r["id_pergunta"], r["seed"]) for r in execucoes if r["candidato"] == c["nome"]}
        esperadas = {(i, s) for i in ids for s in range(1, EXECUCOES_POR_PERGUNTA + 1)}
        faltam = len(esperadas - feitas)
        if faltam:
            problemas.append(f"{c['nome']}: faltam {faltam} execuções")
    if pendentes := a_julgar(corrigidas):
        problemas.append(f"faltam {len(pendentes)} julgamentos às cegas (correcao.as_cegas)")

    ambientes = {}
    for c in selecao["candidatos"]:
        arquivo = args.pasta / "execucoes" / c["nome"] / "ambiente.json"
        if ambientes_publicados is not None:
            ambientes[c["nome"]] = ambientes_publicados.get(c["nome"], {})
        else:
            ambientes[c["nome"]] = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
        if not args.parcial and not (ambientes[c["nome"]].get("vram") or {}).get("size_vram"):
            problemas.append(f"{c['nome']}: VRAM não medida")

    placares = [placar(c, corrigidas, ids, tipos, ambientes[c["nome"]]) for c in selecao["candidatos"]]
    escolhidos = escolher(placares)
    for p in placares:
        marca = " <- escolhido" if p["nome"] in escolhidos.values() else ""
        print(f"  {p['classe']} {p['nome']}: {p['perguntas_certas']} perguntas certas, VRAM {_gib(p['vram'])} GiB{marca}")
    if args.parcial:
        print("\nParcial: nada gravado." + (f" Pendências: {problemas}" if problemas else ""))
        return
    if problemas:
        raise SystemExit("ERRO resultado incompleto: " + "; ".join(problemas))

    mes = {r["mes_de_referencia"] for r in g.respostas.values()}
    resultado = {
        "metadata": {
            # PT: a data da última execução, e não a de hoje: refazer o
            #     resultado com os mesmos dados dá o mesmo arquivo.
            # EN: the last run's date, not today's, so the output reproduces.
            "gerado_em": max((a.get("fim") or "")[:10] for a in ambientes.values()) or None,
            "issue": 48,
            "selecao": SELECAO,
            "condicao": "A",
            "mes_de_referencia": mes.pop() if len(mes) == 1 else sorted(mes),
            "regras": selecao["regras"],
        },
        "escolhidos": escolhidos,
        "candidatos": placares,
        "julgamentos": dict(sorted(julgamentos.items())),
    }
    PASTA_DO_RESULTADO.mkdir(parents=True, exist_ok=True)
    RESULTADO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not args.do_publicado:
        gravar_execucoes(execucoes)
    PAGINA.write_text(pagina(resultado, selecao, ids), encoding="utf-8", newline="\n")
    PARAMETROS.write_text(atualizar_parametros(PARAMETROS.read_text(encoding="utf-8"), selecao, escolhidos),
                          encoding="utf-8", newline="\n")
    print(f"\nGravados {RESULTADO.relative_to(RAIZ).as_posix()}, {EXECUCOES.relative_to(RAIZ).as_posix()}, "
          f"{PAGINA.relative_to(RAIZ).as_posix()} e {PARAMETROS.relative_to(RAIZ).as_posix()}.")
    print("Próximo passo: a errata 2 no evaluation/registro.yml (parametros.yml e resultado.json).")


if __name__ == "__main__":
    main()
