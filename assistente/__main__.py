"""
PT: Uma pergunta ao assistente, pela linha de comando. Imprime a resposta
    nos cinco campos e a proveniência, e grava o registro completo da
    execução em data/assistente/execucoes/, fora do git. Precisa do Ollama
    rodando com o modelo do assistente/parametros.yml; C e D precisam do
    grupo rag do uv, para a busca.

EN: One question to the assistant from the command line. Prints the answer
    and its provenance, and writes the full run record to
    data/assistente/execucoes/. Needs Ollama running; C and D need the rag
    group.

Uso / Usage:
    uv run python -m assistente "Qual a carteira ativa de PJ no Acre?" --condicao B
    uv run --group rag python -m assistente "..." --condicao D --seed 2
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from assistente import parametros
from assistente.cliente import ClienteOllama
from assistente.contexto import buscar_trechos
from assistente.parametros import CONDICOES, DIR_EXECUCOES
from assistente.responder import responder
from assistente.sql import abrir_banco


def gravar(registro: dict, pasta: Path = DIR_EXECUCOES) -> Path:
    """PT: grava o registro em JSON / EN: writes the record as JSON"""
    pasta.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    arquivo = pasta / f"{carimbo}_{registro['condicao']}_seed{registro['seed']}.json"
    arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return arquivo


def imprimir(registro: dict) -> None:
    """PT: a resposta e a proveniência, em texto / EN: answer and provenance as text"""
    if registro["erro"]:
        e = registro["erro"]
        print(f"ERRO ({e['tipo']}, na etapa {e['etapa']}): {e['mensagem']}")
    resposta = registro["resposta"]
    if resposta:
        print(f"\nInterpretação: {resposta['interpretacao']}")
        if resposta["abstencao"]:
            print(f"Abstenção: {resposta['abstencao']}")
        if resposta["sql"]:
            print(f"\nSQL:\n{resposta['sql']}")
        valores = resposta["valores"]
        if valores["colunas"]:
            print("\nValores:\n  " + " | ".join(valores["colunas"]))
            for linha in valores["linhas"]:
                print("  " + " | ".join("" if v is None else str(v) for v in linha))
        if resposta["ressalva"]:
            print(f"\nRessalva: {resposta['ressalva']}")
    resultado = registro["proveniencia"]["resultado"]
    if resultado:
        corte = f", cortado em {len(resultado['linhas'])}" if resultado["cortado"] else ""
        print(f"\nResultado do SQL: {resultado['total_de_linhas']} linhas{corte}, em {resultado['segundos']} s")
    for c in registro["proveniencia"]["conceitos"]:
        print(f"Conceito: {c['id']} ({c['rotulo']}), confiança {c['confianca']}, fonte: {c['fonte']} "
              f"[{', '.join(c['onde'])}]")
    for t in registro["proveniencia"]["trechos"]:
        print(f"Trecho {t['trecho']}: {t['documento']}, {t.get('titulo') or ''}, similaridade {t['similaridade']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pergunta")
    # PT: B é o padrão porque roda sem o grupo rag / EN: B runs without the rag group
    parser.add_argument("--condicao", choices=sorted(CONDICOES), default="B")
    parser.add_argument("--seed", type=int, default=None, help="padrão: a primeira seed registrada")
    args = parser.parse_args()

    p = parametros.carregar()
    parametros.conferir_pre_registro(p)
    if p.provisorio:
        print("Aviso: parâmetros provisórios, até a #48 / provisional parameters, until #48", file=sys.stderr)
    trechos = buscar_trechos(args.pergunta) if "trechos" in CONDICOES[args.condicao] else None
    registro = responder(args.pergunta, args.condicao, args.seed if args.seed is not None else p.seeds[0],
                         cliente=ClienteOllama(p), banco=abrir_banco(), p=p,
                         modelo=parametros.modelo_de_prompt(), trechos=trechos)
    imprimir(registro)
    print(f"\nRegistro / record: {gravar(registro)}")
    if registro["erro"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
