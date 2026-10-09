"""
PT: Teste de fumaça do assistente (#49, ADR 0029) com o Ollama local.
    Roda as perguntas inventadas abaixo nas quatro condições, com a primeira
    seed registrada, e grava o relatório em data/assistente/, fora do git.

    As perguntas são inventadas e ficam fora das 41 do
    evaluation/questions_v3.yml: o prompt não se afina no conjunto de teste,
    porque a #48 é a primeira execução contra ele (ADR 0026). O
    scripts.validar_assistente confere que nenhuma coincide com uma
    registrada.

    O relatório traz o prompt_eval_count medido e os caracteres de cada
    chamada, para a #48 dimensionar o num_ctx e calibrar a razão de
    caracteres por token da estimativa por um número medido.

    Fica fora do CI: precisa do Ollama rodando com o modelo do
    assistente/parametros.yml, do retrato local do esquema estrela
    (scripts.exportar_esquema_estrela) e do índice do RAG (grupo rag).

EN: Assistant smoke test against local Ollama. Runs the invented questions
    below in all four conditions with the first registered seed and writes
    the report to data/assistente/. The questions are not among the 41
    registered ones (checked by scripts.validar_assistente). The report has
    the measured prompt_eval_count of each call, so #48 can size num_ctx.
    Outside CI: needs Ollama, the local snapshot and the RAG index.

Uso / Usage:
    uv run --group rag python -m scripts.analises.fumaca_assistente
"""

from __future__ import annotations

import datetime
import json
import sys
import urllib.error
import urllib.request

# PT: perguntas inventadas, de leitura simples, e uma que pede abstenção
#     (a base não identifica o cliente). Ficam aqui no topo, sem import
#     pesado, para o validador ler sem o Ollama e sem o grupo rag.
# EN: invented questions, two simple reads and one that calls for
#     abstention. Kept at the top, with no heavy import, for the validator.
PERGUNTAS_DE_FUMACA = (
    "Qual era a carteira ativa de crédito de pessoa jurídica no Acre na data-base mais recente?",
    "Qual foi a taxa Selic média do ano de 2024?",
    "Quantos clientes distintos tomaram crédito no Amapá no último mês?",
)


def conferir_servidor(endereco: str, modelo: str) -> None:
    """
    PT: Para com mensagem clara se o Ollama não responde ou não tem o modelo.
    EN: Stops with a clear message if Ollama is down or lacks the model.
    """
    try:
        with urllib.request.urlopen(f"{endereco}/api/tags", timeout=5) as resposta:
            modelos = {m["name"] for m in json.loads(resposta.read().decode("utf-8")).get("models", [])}
    except (urllib.error.URLError, TimeoutError) as erro:
        raise SystemExit(f"ERRO Ollama fora do ar em {endereco} ({erro}): instale e rode `ollama serve` / "
                         "Ollama is not running") from None
    if modelo not in modelos:
        raise SystemExit(f"ERRO o Ollama não tem o modelo {modelo}: rode `ollama pull {modelo}` / model missing")


def main() -> None:
    from assistente import parametros
    from assistente.__main__ import gravar
    from assistente.cliente import ClienteOllama
    from assistente.contexto import buscar_trechos
    from assistente.parametros import CONDICOES
    from assistente.responder import responder
    from assistente.sql import abrir_banco
    from ingestion.fontes import RAIZ

    p = parametros.carregar()
    parametros.conferir_pre_registro(p)
    conferir_servidor(p.endereco, p.modelo)
    banco, modelo, cliente = abrir_banco(), parametros.modelo_de_prompt(), ClienteOllama(p)
    seed = p.seeds[0]

    execucoes = []
    for pergunta in PERGUNTAS_DE_FUMACA:
        # PT: uma busca só por pergunta: C e D recebem os mesmos trechos.
        # EN: one search per question: C and D get the same excerpts.
        trechos = buscar_trechos(pergunta)
        for condicao, blocos in CONDICOES.items():
            registro = responder(pergunta, condicao, seed, cliente=cliente, banco=banco, p=p, modelo=modelo,
                                 trechos=trechos if "trechos" in blocos else None)
            arquivo = gravar(registro)
            tokens = [c["tokens_do_prompt"] for c in registro["chamadas"]]
            caracteres = [c["caracteres_do_prompt"] for c in registro["chamadas"]]
            erro = registro["erro"]
            situacao = f"erro {erro['tipo']} em {erro['etapa']}" if erro else \
                ("abstenção" if registro["resposta"]["abstencao"] else "respondeu")
            print(f"  {condicao} | {situacao} | tokens do prompt {tokens} | {registro['segundos']} s | {pergunta}")
            execucoes.append({"pergunta": pergunta, "condicao": condicao, "seed": seed, "situacao": situacao,
                              "tokens_do_prompt": tokens, "caracteres_do_prompt": caracteres, "segundos": registro["segundos"],
                              "registro": arquivo.relative_to(RAIZ).as_posix()})

    medidos = [t for e in execucoes for t in e["tokens_do_prompt"] if t is not None]
    relatorio = {
        "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "modelo": p.modelo,
        "provisorio": p.provisorio,
        "num_ctx": p.num_ctx,
        "maior_prompt_medido": max(medidos, default=None),
        "execucoes": execucoes,
    }
    saida = RAIZ / "data" / "assistente" / f"fumaca-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
    saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\n  maior prompt medido: {relatorio['maior_prompt_medido']} tokens, num_ctx {p.num_ctx}")
    print(f"  relatório / report: {saida}")
    if any(e["situacao"].startswith("erro") for e in execucoes):
        sys.exit(1)


if __name__ == "__main__":
    main()
