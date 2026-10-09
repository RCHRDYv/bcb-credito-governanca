"""
PT: O fluxo de uma execução (evaluation/hipoteses.yml, execucao.fluxo):

    1. Primeira chamada: o modelo escreve um SQL ou se abstém, num JSON com
       interpretacao, sql e abstencao.
    2. Abstenção: não há segunda chamada. A resposta sai com sql e valores
       vazios, e a interpretação e a abstenção da primeira chamada.
    3. O SQL roda uma vez, só leitura, com os limites de linhas e de tempo.
    4. Segunda chamada: o modelo recebe o resultado e escreve interpretacao,
       valores, ressalva e abstencao. O sql da resposta é o executado, posto
       pelo código.

    A resposta final tem os cinco campos de comparacao.formato_da_resposta.
    Saída fora do formato, tempo esgotado, erro de SQL e prompt maior que o
    num_ctx viram erro, com o tipo e a etapa, sem nova tentativa.

    A proveniência é montada pelo código (decisão 2 do ADR 0029): o SQL
    executado, o resultado bruto, os trechos recebidos e os conceitos da
    ontologia achados no SQL e no resultado, com confiança e fonte.

EN: One run's flow: first call writes SQL or abstains; abstention ends the
    run with empty sql and values; the SQL runs once with limits; the second
    call gets the result and writes the answer. The final answer has the five
    registered fields. Out-of-format output, timeouts, SQL errors and prompts
    beyond num_ctx become typed errors, never retried. Provenance is built by
    code: executed SQL, raw result, received excerpts and ontology concepts
    found in the SQL and result.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import time
from dataclasses import asdict

from assistente import contexto, ontologia
from assistente.cliente import ErroDeGeracao, Geracao, conferir_contexto, conferir_estimativa, estimar_tokens
from assistente.parametros import CONDICOES, Parametros
from assistente.sql import ErroDeSQL, executar

_TEXTO = {"type": "string"}
_CELULA = {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "null"}]}

# PT: esquemas JSON das duas chamadas. A segunda não pede o sql: o da
#     resposta final é o executado.
# EN: JSON schemas of both calls. The second does not ask for sql.
ESQUEMA_DA_PRIMEIRA = {
    "type": "object",
    "properties": {"interpretacao": _TEXTO, "sql": _TEXTO, "abstencao": _TEXTO},
    "required": ["interpretacao", "sql", "abstencao"],
}
ESQUEMA_DA_SEGUNDA = {
    "type": "object",
    "properties": {
        "interpretacao": _TEXTO,
        "valores": {
            "type": "object",
            "properties": {"colunas": {"type": "array", "items": _TEXTO},
                           "linhas": {"type": "array", "items": {"type": "array", "items": _CELULA}}},
            "required": ["colunas", "linhas"],
        },
        "ressalva": _TEXTO,
        "abstencao": _TEXTO,
    },
    "required": ["interpretacao", "valores", "ressalva", "abstencao"],
}


class ErroDeFormato(Exception):
    """PT: saída fora do formato / EN: out-of-format output"""

    tipo = "formato"


def ler_json(geracao: Geracao, esquema: dict) -> dict:
    """
    PT: Lê a resposta do modelo e confere campos e tipos contra o esquema.
        Não conserta nada: cerca de código, texto em volta ou campo faltando
        é erro de formato.
    EN: Reads the model's answer and checks fields and types; repairs
        nothing.
    """
    if geracao.motivo_do_fim == "length":
        raise ErroDeFormato("resposta cortada no limite de tokens")
    try:
        dados = json.loads(geracao.texto)
    except json.JSONDecodeError as erro:
        raise ErroDeFormato(f"não é JSON: {erro}") from None
    if not isinstance(dados, dict):
        raise ErroDeFormato("não é um objeto JSON")
    faltando = [c for c in esquema["required"] if c not in dados]
    if faltando:
        raise ErroDeFormato(f"faltam campos: {', '.join(faltando)}")
    for campo, regra in esquema["properties"].items():
        if regra is _TEXTO and not isinstance(dados[campo], str):
            raise ErroDeFormato(f"{campo} não é texto")
    if "valores" in esquema["properties"]:
        valores = dados["valores"]
        if not (isinstance(valores, dict) and isinstance(valores.get("colunas"), list)
                and isinstance(valores.get("linhas"), list)):
            raise ErroDeFormato("valores não é {colunas, linhas}")
        if not all(isinstance(c, str) for c in valores["colunas"]):
            raise ErroDeFormato("valores.colunas tem item que não é texto")
        for linha in valores["linhas"]:
            if not isinstance(linha, list) or len(linha) != len(valores["colunas"]):
                raise ErroDeFormato("valores.linhas tem linha de tamanho diferente das colunas")
            if any(not (v is None or isinstance(v, (str, int, float))) or isinstance(v, bool) for v in linha):
                raise ErroDeFormato("valores.linhas tem célula que não é texto, número ou nulo")
    return dados


def celulas_de_texto(resultado: dict) -> set[str]:
    """
    PT: As células das colunas de texto do resultado. Só as de texto: um
        número como 12 não pode virar a modalidade de código 12.
    EN: Cells of the result's text columns only.
    """
    indices = [i for i, tipo in enumerate(resultado["tipos"]) if tipo == "VARCHAR"]
    return {linha[i] for linha in resultado["linhas"] for i in indices if linha[i] is not None}


def _chamada(mensagens: list[dict], geracao: Geracao, p: Parametros) -> dict:
    """
    PT: O registro de uma chamada. A mensagem de sistema, que leva a
        ontologia inteira em B e D, entra pelo sha256 e pelo tamanho: ela se
        refaz da condição, dos trechos e dos arquivos versionados.
    EN: One call's record; the system message goes in by sha256 and size.
    """
    sistema = mensagens[0]["content"]
    return {
        "sistema_sha256": hashlib.sha256(sistema.encode("utf-8")).hexdigest(),
        "sistema_caracteres": len(sistema),
        "mensagens": mensagens[1:],
        "caracteres_do_prompt": sum(len(m["content"]) for m in mensagens),
        "tokens_estimados": estimar_tokens(mensagens, p),
        "resposta": geracao.texto,
        "tokens_do_prompt": geracao.tokens_do_prompt,
        "tokens_da_resposta": geracao.tokens_da_resposta,
        "motivo_do_fim": geracao.motivo_do_fim,
        "segundos": geracao.segundos,
    }


def _gerar(cliente, mensagens: list[dict], esquema: dict, seed: int, p: Parametros, registro: dict) -> Geracao:
    """
    PT: Uma chamada ao modelo entre as duas conferências de contexto. A
        chamada entra no registro antes da segunda conferência, para que o
        prompt grande demais fique medido.
    EN: One model call between both context checks; it is recorded before
        the second check, so an oversized prompt stays measured.
    """
    conferir_estimativa(mensagens, p)
    geracao = cliente.gerar(mensagens, esquema, seed)
    registro["chamadas"].append(_chamada(mensagens, geracao, p))
    conferir_contexto(geracao, p)
    return geracao


def responder(pergunta: str, condicao: str, seed: int, *, cliente, banco, p: Parametros,
              modelo: dict[str, str], trechos: list[dict] | None = None) -> dict:
    """
    PT: Uma execução completa. Devolve o registro: parâmetros, trechos,
        chamadas, resultado do SQL, resposta nos cinco campos, proveniência e
        erro, quando houver. Em C e D, os trechos vêm de quem chama, de uma
        busca só antes da geração.
    EN: One full run; returns its record. In C and D the caller passes the
        excerpts, from a single search before generation.
    """
    if condicao not in CONDICOES:
        raise ValueError(f"condição desconhecida: {condicao}")
    usa_trechos = "trechos" in CONDICOES[condicao]
    if usa_trechos and trechos is None:
        raise ValueError(f"a condição {condicao} precisa dos trechos da busca")

    registro = {
        "pergunta": pergunta,
        "condicao": condicao,
        "seed": seed,
        "parametros": asdict(p),
        "inicio": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "trechos": trechos if usa_trechos else [],
        "chamadas": [],
        "resultado": None,
        "resposta": None,
        "proveniencia": None,
        "erro": None,
    }
    inicio = time.perf_counter()
    etapa = "primeira_chamada"
    try:
        mensagens = contexto.primeira_chamada(condicao, pergunta, modelo, registro["trechos"] if usa_trechos else None)
        geracao = _gerar(cliente, mensagens, ESQUEMA_DA_PRIMEIRA, seed, p, registro)
        primeira = ler_json(geracao, ESQUEMA_DA_PRIMEIRA)

        if primeira["abstencao"].strip():
            registro["resposta"] = {"interpretacao": primeira["interpretacao"], "sql": "",
                                    "valores": {"colunas": [], "linhas": []}, "ressalva": "",
                                    "abstencao": primeira["abstencao"]}
        else:
            if not primeira["sql"].strip():
                raise ErroDeFormato("sem sql e sem abstenção")
            etapa = "sql"
            resultado = executar(banco, primeira["sql"], p.limite_de_linhas, p.limite_de_tempo_do_sql)
            registro["resultado"] = resultado

            etapa = "segunda_chamada"
            mensagens = contexto.segunda_chamada(mensagens, geracao.texto, resultado, modelo)
            geracao = _gerar(cliente, mensagens, ESQUEMA_DA_SEGUNDA, seed, p, registro)
            segunda = ler_json(geracao, ESQUEMA_DA_SEGUNDA)
            registro["resposta"] = {"interpretacao": segunda["interpretacao"], "sql": primeira["sql"],
                                    "valores": segunda["valores"], "ressalva": segunda["ressalva"],
                                    "abstencao": segunda["abstencao"]}
    except (ErroDeGeracao, ErroDeSQL, ErroDeFormato) as erro:
        registro["erro"] = {"tipo": erro.tipo, "etapa": etapa, "mensagem": str(erro)}

    resultado = registro["resultado"]
    registro["proveniencia"] = {
        "sql": registro["resposta"]["sql"] if registro["resposta"] else None,
        "resultado": resultado,
        "trechos": registro["trechos"],
        "conceitos": ontologia.conceitos_usados(
            # PT: as colunas do resultado também, para que um select * conte.
            # EN: result columns too, so a select * counts.
            set(resultado["colunas_lidas"]) | set(resultado["colunas"]) if resultado else set(),
            set(resultado["literais"]) if resultado else set(),
            celulas_de_texto(resultado) if resultado else set(),
        ),
    }
    registro["segundos"] = round(time.perf_counter() - inicio, 3)
    return registro
