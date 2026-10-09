"""
PT: Interface local do assistente, em Gradio (decisão 5 do ADR 0029). Uma
    pergunta, a condição e a seed; a resposta nos cinco campos e, ao lado, a
    proveniência montada pelo código: o SQL executado, o resultado, os
    conceitos da ontologia com confiança e fonte e os trechos recebidos.
    Cada execução é gravada em data/assistente/execucoes/, como na linha de
    comando.

    Roda só na máquina local (127.0.0.1). Não é o chat do Space (ADR 0019).
    Precisa do Ollama rodando, do retrato local do esquema estrela e, nas
    condições C e D, do índice do RAG.

EN: Local Gradio interface for the assistant: question, condition and seed
    in; the five-field answer and the code-built provenance out (executed
    SQL, result, ontology concepts with confidence and source, excerpts).
    Each run is recorded like the CLI does. Local only; not the Space chat.

Uso / Usage:
    uv run --group assistente --group rag python -m assistente.interface
"""

from __future__ import annotations

import sys
from typing import Callable

import gradio as gr
import pandas as pd

from assistente import parametros
from assistente.__main__ import gravar
from assistente.cliente import ClienteOllama
from assistente.contexto import buscar_trechos
from assistente.parametros import CONDICOES
from assistente.responder import responder
from assistente.sql import abrir_banco


def texto_da_resposta(registro: dict) -> str:
    """PT: a resposta em Markdown / EN: the answer as Markdown"""
    partes = []
    if erro := registro["erro"]:
        partes.append(f"**Erro** ({erro['tipo']}, na etapa {erro['etapa']}): {erro['mensagem']}")
    if resposta := registro["resposta"]:
        partes.append(f"**Interpretação:** {resposta['interpretacao']}")
        if resposta["abstencao"]:
            partes.append(f"**Abstenção:** {resposta['abstencao']}")
        valores = resposta["valores"]
        if valores["colunas"]:
            linhas = ["| " + " | ".join(valores["colunas"]) + " |", "|" + "---|" * len(valores["colunas"])]
            linhas += ["| " + " | ".join("" if v is None else str(v) for v in linha) + " |"
                       for linha in valores["linhas"]]
            partes.append("\n".join(linhas))
        if resposta["ressalva"]:
            partes.append(f"**Ressalva:** {resposta['ressalva']}")
    resultado = registro["proveniencia"]["resultado"]
    if resultado:
        corte = f", cortado em {len(resultado['linhas'])}" if resultado["cortado"] else ""
        partes.append(f"*Resultado do SQL: {resultado['total_de_linhas']} linhas{corte}, em {resultado['segundos']} s.*")
    return "\n\n".join(partes)


def tabela_do_resultado(registro: dict) -> pd.DataFrame:
    """PT: o resultado bruto do SQL / EN: the raw SQL result"""
    resultado = registro["proveniencia"]["resultado"]
    if not resultado:
        return pd.DataFrame()
    return pd.DataFrame(resultado["linhas"], columns=resultado["colunas"])


def tabela_dos_conceitos(registro: dict) -> pd.DataFrame:
    """PT: os conceitos da ontologia / EN: the ontology concepts"""
    return pd.DataFrame(
        [{"id": c["id"], "rótulo": c["rotulo"], "confiança": c["confianca"], "fonte": c["fonte"],
          "onde": ", ".join(c["onde"])} for c in registro["proveniencia"]["conceitos"]],
        columns=["id", "rótulo", "confiança", "fonte", "onde"],
    )


def texto_dos_trechos(registro: dict) -> str:
    """PT: os trechos recebidos, em Markdown / EN: received excerpts as Markdown"""
    trechos = registro["proveniencia"]["trechos"]
    if not trechos:
        return "*Sem trechos nesta condição.*"
    return "\n\n".join(
        f"**Trecho {t['trecho']}**, {t['documento']}{', ' + t['titulo'] if t.get('titulo') else ''}, "
        f"similaridade {t['similaridade']}\n\n> {' '.join(t['texto'].split())}"
        for t in trechos
    )


def montar(perguntar: Callable[[str, str, int], dict], seeds: tuple[int, ...]) -> gr.Blocks:
    """
    PT: Monta a tela. A função perguntar devolve o registro da execução;
        separada assim, a tela se monta sem o Ollama.
    EN: Builds the screen; perguntar returns the run record, so the screen
        builds without Ollama.
    """

    def ao_perguntar(pergunta: str, condicao: str, seed: float):
        if not pergunta.strip():
            raise gr.Error("Escreva uma pergunta.")
        registro = perguntar(pergunta.strip(), condicao, int(seed))
        resposta = registro["resposta"] or {}
        return (texto_da_resposta(registro), resposta.get("sql") or "", tabela_do_resultado(registro),
                tabela_dos_conceitos(registro), texto_dos_trechos(registro))

    with gr.Blocks(title="Assistente de dados do SCR.data") as tela:
        gr.Markdown("# Assistente de dados do SCR.data\n"
                    "Text-to-SQL sobre o esquema estrela, com a proveniência montada pelo código (ADR 0029).")
        with gr.Row():
            pergunta = gr.Textbox(label="Pergunta", lines=2, scale=4)
            with gr.Column(scale=1):
                condicao = gr.Radio(sorted(CONDICOES), value="B", label="Condição")
                seed = gr.Dropdown(list(seeds), value=seeds[0], label="Seed")
        botao = gr.Button("Perguntar", variant="primary")
        with gr.Row():
            with gr.Column():
                resposta = gr.Markdown(label="Resposta")
                sql = gr.Code(label="SQL executado", language="sql")
                resultado = gr.Dataframe(label="Resultado do SQL", interactive=False)
            with gr.Column():
                conceitos = gr.Dataframe(label="Conceitos da ontologia", interactive=False)
                trechos = gr.Markdown(label="Trechos")
        entradas, saidas = [pergunta, condicao, seed], [resposta, sql, resultado, conceitos, trechos]
        botao.click(ao_perguntar, entradas, saidas)
        pergunta.submit(ao_perguntar, entradas, saidas)
    return tela


def main() -> None:
    p = parametros.carregar()
    parametros.conferir_pre_registro(p)
    if p.provisorio:
        print("Aviso: parâmetros provisórios, até a #48 / provisional parameters, until #48", file=sys.stderr)
    banco, modelo, cliente = abrir_banco(), parametros.modelo_de_prompt(), ClienteOllama(p)

    def perguntar(pergunta: str, condicao: str, seed: int) -> dict:
        trechos = buscar_trechos(pergunta) if "trechos" in CONDICOES[condicao] else None
        registro = responder(pergunta, condicao, seed, cliente=cliente, banco=banco, p=p, modelo=modelo,
                             trechos=trechos)
        gravar(registro)
        return registro

    montar(perguntar, p.seeds).launch(server_name="127.0.0.1")


if __name__ == "__main__":
    main()
