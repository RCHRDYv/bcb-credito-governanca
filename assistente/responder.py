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
from functools import partial

from assistente import contexto, ontologia, variacoes
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
        _conferir_valores(dados["valores"])
    return dados


def _conferir_valores(valores) -> None:
    """PT: a forma de valores, {colunas, linhas} / EN: the shape of valores"""
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


class _Pares(list):
    """PT: os pares de um objeto JSON, na ordem / EN: a JSON object's ordered pairs"""


def _como_dict(valor):
    """PT: objetos lidos como pares voltam a dict / EN: pairs back to dicts"""
    if isinstance(valor, _Pares):
        return {k: _como_dict(v) for k, v in valor}
    if isinstance(valor, list):
        return [_como_dict(v) for v in valor]
    return valor


def ler_json_prefixado(geracao: Geracao, campos: list[str]) -> dict:
    """
    PT: Lê a resposta de uma variação com chaves prefixadas (V0 em diante):
        confere que as chaves vieram todas, na ordem pedida, e os tipos, e
        devolve os nomes registrados (a_interpretacao vira interpretacao).
        Não conserta nada.
    EN: Reads a prefixed-key answer (V0 on): checks all keys came, in the
        requested order, and their types; returns the registered names.
    """
    if geracao.motivo_do_fim == "length":
        raise ErroDeFormato("resposta cortada no limite de tokens")
    try:
        pares = json.loads(geracao.texto, object_pairs_hook=_Pares)
    except json.JSONDecodeError as erro:
        raise ErroDeFormato(f"não é JSON: {erro}") from None
    # PT: um array no topo não é objeto, mesmo que tenha cara de pares.
    # EN: a top-level array is not an object, even if it looks like pairs.
    if not isinstance(pares, _Pares):
        raise ErroDeFormato("não é um objeto JSON")
    esperadas = variacoes.prefixadas(campos)
    recebidas = [k for k, _ in pares]
    if recebidas != esperadas:
        raise ErroDeFormato(f"chaves {recebidas}, esperado {esperadas} nesta ordem")
    dados = {}
    for (_, valor), campo in zip(pares, campos):
        if campo == "valores":
            if not isinstance(valor, _Pares):
                raise ErroDeFormato("valores não é um objeto")
            valor = _como_dict(valor)
            _conferir_valores(valor)
        elif campo == "abstem":
            if not isinstance(valor, bool):
                raise ErroDeFormato("abstem não é booleano")
        elif not isinstance(valor, str):
            raise ErroDeFormato(f"{campo} não é texto")
        dados[campo] = valor
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
        ontologia em B e D, entra pelo sha256 e pelo tamanho: ela se refaz
        da condição, dos trechos, dos itens recuperados (da V5 em diante) e
        dos arquivos versionados.
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


def resultado_vazio(resultado: dict) -> bool:
    """PT: nenhuma linha, ou só células nulas / EN: no rows, or only nulls"""
    return resultado["total_de_linhas"] == 0 or all(v is None for linha in resultado["linhas"] for v in linha)


def _abstencao(interpretacao: str, motivo: str) -> dict:
    return {"interpretacao": interpretacao, "sql": "", "valores": {"colunas": [], "linhas": []}, "ressalva": "",
            "abstencao": motivo.strip() or "(sem motivo)"}


def _fluxo_da_v_menos_1(registro: dict, estado: dict, pergunta: str, condicao: str, seed: int, cliente, banco,
                        p: Parametros, modelo: dict[str, str], trechos) -> None:
    """
    PT: O fluxo da V−1, o instrumento da execução 1, como foi registrado: a
        abstenção da primeira chamada encerra a execução, e o SQL roda uma
        vez, sem nova tentativa.
    EN: V−1's flow, run 1's instrument as registered.
    """
    mensagens = contexto.primeira_chamada(condicao, pergunta, modelo, trechos)
    geracao = _gerar(cliente, mensagens, ESQUEMA_DA_PRIMEIRA, seed, p, registro)
    primeira = ler_json(geracao, ESQUEMA_DA_PRIMEIRA)

    if primeira["abstencao"].strip():
        registro["resposta"] = {"interpretacao": primeira["interpretacao"], "sql": "",
                                "valores": {"colunas": [], "linhas": []}, "ressalva": "",
                                "abstencao": primeira["abstencao"]}
        return
    if not primeira["sql"].strip():
        raise ErroDeFormato("sem sql e sem abstenção")
    estado["etapa"] = "sql"
    resultado = executar(banco, primeira["sql"], p.limite_de_linhas, p.limite_de_tempo_do_sql)
    registro["resultado"] = resultado

    estado["etapa"] = "segunda_chamada"
    mensagens = contexto.segunda_chamada(mensagens, geracao.texto, resultado, modelo)
    geracao = _gerar(cliente, mensagens, ESQUEMA_DA_SEGUNDA, seed, p, registro)
    segunda = ler_json(geracao, ESQUEMA_DA_SEGUNDA)
    registro["resposta"] = {"interpretacao": segunda["interpretacao"], "sql": primeira["sql"],
                            "valores": segunda["valores"], "ressalva": segunda["ressalva"],
                            "abstencao": segunda["abstencao"]}


def mensagens_da_primeira(v: variacoes.Variacao, condicao: str, pergunta: str, modelo: dict[str, str],
                          trechos, itens_da_ontologia: list[str] | None = None) -> list[dict]:
    """
    PT: As mensagens da primeira chamada de uma variação: o sistema da
        condição e a mensagem do usuário da variação. No sistema, a V4
        acrescenta as junções ao bloco do esquema; a V5 troca a ontologia
        inteira de B e D pelos itens recuperados; e a V6 troca o esquema cru
        pelo descrito, nas quatro condições (#120). Cada ligação age sozinha,
        e um bloco que não aparece na mensagem para a execução. O
        dimensionamento conta estas mesmas mensagens.
    EN: A variant's first call messages: V4 adds joins to the schema block,
        V5 swaps B and D's full ontology for the retrieved items, V6 the raw
        schema for the described one. The sizing counts these same ones.
    """
    mensagens = contexto.primeira_chamada(condicao, pergunta, modelo, trechos)
    sistema = mensagens[0]["content"]
    if v.ontologia_recuperada and "ontologia" in CONDICOES[condicao]:
        if itens_da_ontologia is None:
            raise ValueError(f"a condição {condicao} da {v.nome} precisa dos itens recuperados da ontologia")
        inteira = contexto.preencher(modelo["bloco_ontologia"], ontologia=ontologia.bloco())
        recuperada = contexto.preencher(modelo["bloco_ontologia"], ontologia=ontologia.bloco(ids=itens_da_ontologia))
        sistema = _trocar_bloco(sistema, inteira, recuperada, f"ontologia de {condicao} na {v.nome}")
    if v.juncoes or v.esquema_descrito:
        cru = contexto.preencher(modelo["bloco_esquema"], esquema=contexto.texto_do_esquema())
        esquema = (variacoes.esquema_descrito(contexto.esquema_esperado()) if v.esquema_descrito
                   else contexto.texto_do_esquema())
        novo = contexto.preencher(modelo["bloco_esquema"], esquema=esquema)
        if v.juncoes:
            novo += "\n\n" + variacoes.juncoes(contexto.esquema_esperado())
        sistema = _trocar_bloco(sistema, cru, novo, f"esquema de {condicao} na {v.nome}")
    mensagens[0]["content"] = sistema
    mensagens[1]["content"] = variacoes.mensagem_da_primeira(v, pergunta)
    return mensagens


def _trocar_bloco(sistema: str, antes: str, depois: str, onde: str) -> str:
    """
    PT: Troca um bloco da mensagem de sistema, que tem de aparecer uma vez
        só. Um bloco que não aparece não pode virar uma troca que não faz
        nada: a execução levaria o instrumento antigo sem erro (#120).
    EN: Swaps one system message block, which must appear exactly once; a
        missing block must not become a silent no-op.
    """
    if (vezes := sistema.count(antes)) != 1:
        raise ValueError(f"o bloco a trocar ({onde}) aparece {vezes} vezes na mensagem de sistema, e não uma")
    return sistema.replace(antes, depois, 1)


def _fluxo_da_variacao(v: variacoes.Variacao, registro: dict, estado: dict, pergunta: str, condicao: str,
                       seed: int, cliente, banco, p: Parametros, modelo: dict[str, str], trechos,
                       itens_da_ontologia: list[str] | None = None) -> None:
    """
    PT: O fluxo de uma variação da V0 em diante (#118, ADR 0032):

        1. primeira chamada com as chaves prefixadas; com SQL não vazio, o
           SQL roda, qualquer que seja o booleano de abstenção; se ele falha
           com o booleano verdadeiro, vale a abstenção;
        2. na V3 e na V4, uma nova tentativa só, quando o SQL dá erro, para
           na guarda ou volta vazio: o modelo recebe a resposta anterior
           e o problema, e a nova resposta substitui a anterior;
        3. segunda chamada sobre a primeira chamada e a tentativa válida.

        A resposta final tem os cinco campos registrados; abstencao recebe o
        motivo quando o booleano é verdadeiro.
    EN: A variant's flow: prefixed first call (non-empty SQL runs), at most
        one retry in V3/V4 on SQL error, guard or empty result (the new
        answer replaces the old), then the second call on the valid attempt.
    """
    mensagens = mensagens_da_primeira(v, condicao, pergunta, modelo, trechos, itens_da_ontologia)
    campos = variacoes.campos_da_primeira(v)
    esquema = variacoes.esquema_json(campos)
    geracao = _gerar(cliente, mensagens, esquema, seed, p, registro)
    primeira = ler_json_prefixado(geracao, campos)

    while True:
        if not primeira["sql"].strip():
            if not primeira["abstem"]:
                raise ErroDeFormato("sem sql e sem abstenção")
            registro["resposta"] = _abstencao(primeira["interpretacao"], primeira["motivo"])
            return
        estado["etapa"] = "sql"
        erro_de_sql = None
        try:
            resultado = executar(banco, primeira["sql"], p.limite_de_linhas, p.limite_de_tempo_do_sql)
        except ErroDeSQL as erro:
            if not (v.nova_tentativa and not registro["novas_tentativas"] and erro.tipo in ("sql", "guarda")):
                # PT: com abstem verdadeiro, o SQL que falha (na V3 e na V4,
                #     depois da nova tentativa) deixa a abstenção valer
                #     (decisão de 2026-10-15); o SQL e o erro ficam no registro.
                # EN: with abstem true, a failing SQL leaves the abstention.
                if primeira["abstem"]:
                    registro["sql_da_abstencao"] = {"sql": primeira["sql"], "tipo": erro.tipo,
                                                    "mensagem": str(erro)}
                    registro["resposta"] = _abstencao(primeira["interpretacao"], primeira["motivo"])
                    return
                raise
            erro_de_sql, resultado = erro, None
        if v.nova_tentativa and not registro["novas_tentativas"] and (erro_de_sql or resultado_vazio(resultado)):
            estado["etapa"] = "nova_tentativa"
            registro["novas_tentativas"] = 1
            # PT: a tentativa substituída fica no registro, com o problema.
            # EN: the replaced attempt stays in the record, with its problem.
            registro["tentativa_substituida"] = {
                "sql": primeira["sql"], "erro": {"tipo": erro_de_sql.tipo, "mensagem": str(erro_de_sql)}
                if erro_de_sql else None, "resultado": None if erro_de_sql else resultado}
            pedido = [*mensagens,
                      {"role": "assistant", "content": geracao.texto},
                      {"role": "user", "content": variacoes.mensagem_da_nova_tentativa(
                          str(erro_de_sql) if erro_de_sql else None)}]
            geracao = _gerar(cliente, pedido, esquema, seed, p, registro)
            primeira = ler_json_prefixado(geracao, campos)
            continue
        break
    registro["resultado"] = resultado

    estado["etapa"] = "segunda_chamada"
    aviso = ""
    if resultado["cortado"]:
        aviso = f" (resultado cortado em {len(resultado['linhas'])} de {resultado['total_de_linhas']} linhas)"
    tabela = json.dumps({"colunas": resultado["colunas"], "linhas": resultado["linhas"]}, ensure_ascii=False)
    segunda_mensagens = [*mensagens, {"role": "assistant", "content": geracao.texto},
                         {"role": "user", "content": variacoes.mensagem_da_segunda(v, tabela, aviso)}]
    campos = variacoes.campos_da_segunda(v)
    geracao = _gerar(cliente, segunda_mensagens, variacoes.esquema_json(campos), seed, p, registro)
    segunda = ler_json_prefixado(geracao, campos)
    registro["resposta"] = {
        "interpretacao": segunda["interpretacao"], "sql": primeira["sql"], "valores": segunda["valores"],
        "ressalva": segunda["ressalva"],
        "abstencao": (segunda["motivo"].strip() or "(sem motivo)") if segunda["abstem"] else "",
    }


def responder(pergunta: str, condicao: str, seed: int, *, cliente, banco, p: Parametros,
              modelo: dict[str, str], trechos: list[dict] | None = None, variacao: str = "V-1",
              itens_da_ontologia: list[str] | None = None) -> dict:
    """
    PT: Uma execução completa. Devolve o registro: parâmetros, trechos,
        chamadas, resultado do SQL, resposta nos cinco campos, proveniência e
        erro, quando houver. Em C e D, os trechos vêm de quem chama, de uma
        busca só antes da geração; da V5 em diante, os itens recuperados da
        ontologia de B e D também (#120), e os ids vão para o registro, para
        a mensagem de sistema se refazer dos arquivos. A variacao escolhe o
        instrumento (assistente/variacoes.py); a V−1, o padrão, é o da
        execução 1, e o registro dela não muda.
    EN: One full run; returns its record. In C and D the caller passes the
        excerpts, from a single search before generation; from V5 on, B and
        D's retrieved ontology items too, recorded by id. variacao picks
        the instrument; V−1, the default, is run 1's and its record is
        unchanged.
    """
    if condicao not in CONDICOES:
        raise ValueError(f"condição desconhecida: {condicao}")
    if variacao not in variacoes.VARIACOES:
        raise ValueError(f"variação desconhecida: {variacao}")
    v = variacoes.VARIACOES[variacao]
    usa_trechos = "trechos" in CONDICOES[condicao]
    if usa_trechos and trechos is None:
        raise ValueError(f"a condição {condicao} precisa dos trechos da busca")
    usa_itens = v.ontologia_recuperada and "ontologia" in CONDICOES[condicao]
    if usa_itens and itens_da_ontologia is None:
        raise ValueError(f"a condição {condicao} da {v.nome} precisa dos itens recuperados da ontologia")

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
    if v.nome != "V-1":
        registro["variacao"] = v.nome
        registro["novas_tentativas"] = 0
    if v.ontologia_recuperada:
        registro["itens_da_ontologia"] = list(itens_da_ontologia) if usa_itens else []
    inicio = time.perf_counter()
    estado = {"etapa": "primeira_chamada"}
    fluxo = (_fluxo_da_v_menos_1 if v.nome == "V-1"
             else partial(_fluxo_da_variacao, v, itens_da_ontologia=itens_da_ontologia if usa_itens else None))
    try:
        fluxo(registro, estado, pergunta, condicao, seed, cliente, banco, p, modelo,
              registro["trechos"] if usa_trechos else None)
    except (ErroDeGeracao, ErroDeSQL, ErroDeFormato) as erro:
        registro["erro"] = {"tipo": erro.tipo, "etapa": estado["etapa"], "mensagem": str(erro)}

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
