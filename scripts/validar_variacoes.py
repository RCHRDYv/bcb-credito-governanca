"""
PT: Valida as variações do instrumento (#118, ADR 0032) sem modelo, com o
    cliente falso e o banco vazio. Roda no workflow experimento.yml.

    O que é conferido:

    1. **Cardápio.** As variações são as do plano, nesta ordem, cumulativas:
       cada uma liga tudo o que a anterior liga e mais uma coisa.
    2. **V−1 é a execução 1.** Com os registros da execução 1 (data/ ou o
       arquivo publicado em evaluation/experimento/execucao-1/), a mensagem
       de sistema e as mensagens da primeira chamada da V−1, re-renderizadas,
       batem com as gravadas. Sem os registros, a checagem é pulada e o
       resumo diz isso.
    3. **Mesmo texto nas quatro condições.** Em cada variação, a mensagem do
       usuário é igual em A, B, C e D, e a mensagem de sistema de D é a de B
       mais o bloco de trechos. As junções só aparecem na V4, nas quatro.
    4. **Fluxo de cada variação.** Chaves fora da ordem são erro de formato
       (da V0 em diante; a V−1 aceita a ordem alfabética); com SQL não vazio
       o SQL roda mesmo com o booleano de abstenção; sem SQL e sem abstenção
       é erro de formato; na V3, erro de SQL e resultado vazio pedem uma
       nova tentativa, uma só, e a segunda chamada vê só a tentativa válida;
       antes da V3, não há nova tentativa; a resposta final tem os cinco
       campos registrados.
    5. **Textos do hipoteses.yml por variação.** O
       evaluation/hipoteses_por_variacao.yml cobre da V0 à V4, e cada
       caminho dele existe no hipoteses.yml. Com uma variação registrada no
       assistente/parametros.yml (errata 6), o hipoteses.yml traz
       exatamente os valores dela, e fora desses caminhos não muda nada
       (experimento/hipoteses_por_variacao.py).

    Com --autoteste, estraga uma peça por vez e confere que a validação
    reprova cada uma.

EN: Validates the instrument variants offline: menu order, V−1 reproducing
    run 1's prompts, the same text across conditions, and each variant's
    flow (key order, SQL precedence, retry semantics, five final fields).

Uso / Usage:
    uv run python -m scripts.validar_variacoes
    uv run python -m scripts.validar_variacoes --autoteste
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import json
import sys
from dataclasses import replace
from unittest import mock

from assistente import contexto, parametros, responder as modulo_responder, variacoes
from assistente.cliente import ClienteFalso
from assistente.parametros import CONDICOES
from assistente.responder import responder
from assistente.sql import banco_vazio
from experimento import hipoteses_por_variacao
from scripts import executar_experimento
from scripts.esquema_estrela_duckdb import esquema_esperado
from scripts.validar_registro import RAIZ

CARDAPIO = ["V-1", "V0", "V1", "V2", "V3", "V4"]
CAMPOS_REGISTRADOS = {"interpretacao", "sql", "valores", "ressalva", "abstencao"}
EXECUCAO_1 = [RAIZ / "data" / "experimento" / "execucoes",
              RAIZ / "evaluation" / "experimento" / "execucao-1" / "execucoes.jsonl.gz"]
TRECHOS = [{"trecho": 1, "documento": "doc", "titulo": None, "secao": "1", "pagina": 1, "texto": "texto",
            "similaridade": 1.0}]
PERGUNTA = "Qual era a carteira ativa total de Rondônia no último mês disponível?"


# -----------------------------------------------------------------------------
# PT: 1. Cardápio / EN: menu
# -----------------------------------------------------------------------------

def checar_cardapio() -> list[str]:
    erros = []
    if variacoes.ORDEM != CARDAPIO:
        erros.append(f"cardápio: {variacoes.ORDEM}, esperado {CARDAPIO}")
    ligados = [{k for k, val in vars(variacoes.VARIACOES[n]).items() if val is True} for n in variacoes.ORDEM]
    for anterior, atual, nome in zip(ligados, ligados[1:], variacoes.ORDEM[1:]):
        if not (anterior < atual and len(atual - anterior) == 1):
            erros.append(f"cardápio: {nome} não é a anterior mais uma coisa ({sorted(atual - anterior)})")
    return erros


# -----------------------------------------------------------------------------
# PT: 2. V−1 é a execução 1 / EN: V−1 is run 1
# -----------------------------------------------------------------------------

def registros_da_execucao_1() -> list[dict] | None:
    pasta, arquivo = EXECUCAO_1
    if pasta.exists():
        return [json.loads(a.read_text(encoding="utf-8")) for a in sorted(pasta.glob("*/*/Q*_seed1.json"))]
    if arquivo.exists():
        with gzip.open(arquivo, "rt", encoding="utf-8") as f:
            return [r for r in map(json.loads, f) if r["seed"] == 1]
    return None


def checar_v_menos_1(registros: list[dict] | None) -> tuple[list[str], int]:
    """
    PT: A primeira chamada da V−1, re-renderizada, contra a gravada.
    EN: V−1's first call, re-rendered, against the recorded one.
    """
    if registros is None:
        return [], 0
    modelo, erros, conferidos = parametros.modelo_de_prompt(), [], 0
    for r in registros:
        if not r["chamadas"]:
            continue
        trechos = r["trechos"] if "trechos" in CONDICOES[r["condicao"]] else None
        mensagens = contexto.primeira_chamada(r["condicao"], r["pergunta"], modelo, trechos)
        gravada = r["chamadas"][0]
        if hashlib.sha256(mensagens[0]["content"].encode("utf-8")).hexdigest() != gravada["sistema_sha256"] \
                or mensagens[1:] != gravada["mensagens"][:1]:
            erros.append(f"V-1: {r['candidato']} {r['condicao']} {r['id_pergunta']} difere da execução 1")
        conferidos += 1
    return erros[:5], conferidos


# -----------------------------------------------------------------------------
# PT: 3. Mesmo texto nas quatro condições / EN: same text in all conditions
# -----------------------------------------------------------------------------

def _mensagens_da_primeira(nome: str, condicao: str) -> list[dict]:
    cliente = ClienteFalso(["{}"])
    responder(PERGUNTA, condicao, 1, cliente=cliente, banco=banco_vazio(), p=_p(), modelo=parametros.modelo_de_prompt(),
              trechos=TRECHOS if "trechos" in CONDICOES[condicao] else None, variacao=nome)
    return cliente.chamadas[0]["mensagens"]


def checar_condicoes() -> list[str]:
    erros = []
    juncoes = variacoes.juncoes(esquema_esperado())
    for nome in variacoes.ORDEM:
        por_condicao = {c: _mensagens_da_primeira(nome, c) for c in CONDICOES}
        usuarios = {c: m[1]["content"] for c, m in por_condicao.items()}
        if len(set(usuarios.values())) != 1:
            erros.append(f"{nome}: a mensagem do usuário muda entre as condições")
        sistema_b, sistema_d = por_condicao["B"][0]["content"], por_condicao["D"][0]["content"]
        if not sistema_d.startswith(sistema_b):
            erros.append(f"{nome}: o sistema de D não é o de B mais os trechos")
        com_juncoes = {c: juncoes in m[0]["content"] for c, m in por_condicao.items()}
        if set(com_juncoes.values()) != {variacoes.VARIACOES[nome].juncoes}:
            erros.append(f"{nome}: junções {com_juncoes}, esperado só na V4 e nas quatro condições")
    return erros


# -----------------------------------------------------------------------------
# PT: 4. Fluxo / EN: flow
# -----------------------------------------------------------------------------

def _p():
    return replace(parametros.carregar(), seeds=(1,))


def _primeira(nome: str, sql: str, abstem: bool, motivo: str = "", ordem_alfabetica: bool = False) -> str:
    v = variacoes.VARIACOES[nome]
    campos = variacoes.campos_da_primeira(v)
    valores = {"interpretacao": "x", "plano": "p", "sql": sql, "abstem": abstem, "motivo": motivo}
    pares = list(zip(variacoes.prefixadas(campos), [valores[c] for c in campos]))
    if ordem_alfabetica:
        pares = sorted(pares, key=lambda par: par[0].split("_", 1)[1])
    return json.dumps(dict(pares), ensure_ascii=False)


def _segunda(nome: str) -> str:
    campos = variacoes.campos_da_segunda(variacoes.VARIACOES[nome])
    valores = {"interpretacao": "x", "valores": {"colunas": ["n"], "linhas": [[0]]}, "ressalva": "", "abstem": False,
               "motivo": ""}
    return json.dumps(dict(zip(variacoes.prefixadas(campos), [valores[c] for c in campos])), ensure_ascii=False)


SQL_BOM = "select count(*) as n from fct_carteira"
SQL_VAZIO = "select uf from fct_carteira"
SQL_RUIM = "select coluna_que_nao_existe from fct_carteira"


def _rodar(nome: str, respostas: list[str]) -> tuple[dict, ClienteFalso]:
    cliente = ClienteFalso(respostas)
    registro = responder(PERGUNTA, "A", 1, cliente=cliente, banco=banco_vazio(), p=_p(),
                         modelo=parametros.modelo_de_prompt(), variacao=nome)
    return registro, cliente


def checar_fluxo() -> list[str]:
    erros = []
    for nome in variacoes.ORDEM[1:]:
        v = variacoes.VARIACOES[nome]
        r, _ = _rodar(nome, [_primeira(nome, SQL_BOM, False, ordem_alfabetica=True), _segunda(nome)])
        if not r["erro"] or r["erro"]["tipo"] != "formato":
            erros.append(f"{nome}: chaves fora da ordem não deram erro de formato")
        # PT: um array de pares no lugar do objeto tem a mesma ordem, mas não é
        #     o formato pedido.
        # EN: an array of pairs instead of the object is a format error.
        pares = list(json.loads(_primeira(nome, SQL_BOM, False)).items())
        r, _ = _rodar(nome, [json.dumps(pares, ensure_ascii=False), _segunda(nome)])
        if not r["erro"] or r["erro"]["tipo"] != "formato":
            erros.append(f"{nome}: um array de pares no lugar do objeto não deu erro de formato")
        r, _ = _rodar(nome, [_primeira(nome, SQL_BOM, True, "não dá"), _segunda(nome)])
        if r["erro"] or r["resultado"] is None:
            erros.append(f"{nome}: com SQL e abstem verdadeiro, o SQL não rodou ({r['erro']})")
        elif set(r["resposta"]) != CAMPOS_REGISTRADOS:
            erros.append(f"{nome}: a resposta final tem {sorted(r['resposta'])}")
        r, _ = _rodar(nome, [_primeira(nome, "", False)])
        if not r["erro"] or r["erro"]["tipo"] != "formato":
            erros.append(f"{nome}: sem SQL e sem abstenção não deu erro de formato")
        r, _ = _rodar(nome, [_primeira(nome, "", True, "falta o dado")])
        if r["erro"] or (r["resposta"] or {}).get("abstencao") != "falta o dado":
            erros.append(f"{nome}: a abstenção não saiu com o motivo")
        # PT: abstem verdadeiro com SQL que falha (na V3 e na V4, duas vezes):
        #     vale a abstenção, e o SQL fica no registro (decisão de 2026-10-15).
        # EN: abstem true with a failing SQL keeps the abstention.
        falhas = [_primeira(nome, SQL_RUIM, True, "falta o dado")] * (2 if v.nova_tentativa else 1)
        r, _ = _rodar(nome, falhas)
        if r["erro"] or (r["resposta"] or {}).get("abstencao") != "falta o dado" or "sql_da_abstencao" not in r:
            erros.append(f"{nome}: abstem verdadeiro com SQL que falha não virou abstenção ({r['erro']})")

        com_erro = [_primeira(nome, SQL_RUIM, False), _primeira(nome, SQL_BOM, False), _segunda(nome)]
        r, cliente = _rodar(nome, com_erro)
        if v.nova_tentativa:
            segunda = cliente.chamadas[-1]["mensagens"] if len(cliente.chamadas) == 3 else []
            if r["erro"] or r["novas_tentativas"] != 1:
                erros.append(f"{nome}: erro de SQL não pediu a nova tentativa ({r['erro']})")
            elif any("coluna_que_nao_existe" in m["content"] for m in segunda):
                erros.append(f"{nome}: a segunda chamada vê a tentativa que falhou")
            r, _ = _rodar(nome, [_primeira(nome, SQL_VAZIO, False), _primeira(nome, SQL_BOM, False), _segunda(nome)])
            if r["novas_tentativas"] != 1 or r["erro"]:
                erros.append(f"{nome}: resultado vazio não pediu a nova tentativa")
            elif (r.get("tentativa_substituida") or {}).get("sql") != SQL_VAZIO:
                erros.append(f"{nome}: o registro não guardou a tentativa substituída")
            r, _ = _rodar(nome, [_primeira(nome, SQL_RUIM, False), _primeira(nome, SQL_RUIM, False)])
            if not r["erro"] or r["erro"]["tipo"] != "sql" or r["novas_tentativas"] != 1:
                erros.append(f"{nome}: a segunda falha de SQL não virou erro de SQL depois de uma tentativa só")
        elif r["erro"] is None or r["erro"]["tipo"] != "sql" or r.get("novas_tentativas"):
            erros.append(f"{nome}: sem nova tentativa, erro de SQL tinha de ser erro de SQL")

    r, _ = _rodar("V-1", [json.dumps({"abstencao": "", "interpretacao": "x", "sql": SQL_BOM}),
                          json.dumps({"abstencao": "", "interpretacao": "x", "ressalva": "",
                                      "valores": {"colunas": ["n"], "linhas": [[0]]}})])
    if r["erro"] or "variacao" in r:
        erros.append(f"V-1: o fluxo da execução 1 mudou ({r['erro']}, chaves {sorted(r)})")
    return erros


# -----------------------------------------------------------------------------
# PT: 5. Textos do hipoteses.yml por variação / EN: per-variant registry texts
# -----------------------------------------------------------------------------

def checar_hipoteses(hipoteses: dict | None = None) -> list[str]:
    """
    PT: Ver experimento/hipoteses_por_variacao.py. Também confere que, para
        cada variação, copiar os valores prontos basta para passar.
    EN: See that module; also checks that copying each variant's values passes.
    """
    erros = hipoteses_por_variacao.conferir(hipoteses, executar_experimento.variacao_registrada())
    textos, vigentes = hipoteses_por_variacao.carregar(), hipoteses_por_variacao.hipoteses_vigentes()
    for v in hipoteses_por_variacao.VARIACOES:
        aplicado = hipoteses_por_variacao.aplicar(vigentes, textos, v)
        if problemas := hipoteses_por_variacao.conferir(aplicado, v, textos):
            erros.append(f"hipoteses_por_variacao: copiar os valores da {v} não basta: {problemas[:2]}")
    return erros


# -----------------------------------------------------------------------------
# PT: Validação / EN: validation
# -----------------------------------------------------------------------------

def validar(registros: list[dict] | None) -> tuple[list[str], int]:
    v_menos_1, conferidos = checar_v_menos_1(registros)
    return checar_cardapio() + v_menos_1 + checar_condicoes() + checar_fluxo() + checar_hipoteses(), conferidos


def _leitura_tolerante(geracao, campos: list[str]) -> dict:
    """PT: lê o JSON tirando o prefixo, sem conferir a ordem / EN: order-blind reader"""
    dados = json.loads(geracao.texto)
    if not isinstance(dados, dict):
        raise modulo_responder.ErroDeFormato("não é um objeto JSON")
    dados = {k.split("_", 1)[1]: v for k, v in dados.items()}
    if faltam := [c for c in campos if c not in dados]:
        raise modulo_responder.ErroDeFormato(f"faltam {faltam}")
    return {c: dados[c] for c in campos}


_LER_JSON_PREFIXADO = modulo_responder.ler_json_prefixado


def _leitura_que_aceita_array(geracao, campos: list[str]) -> dict:
    """PT: aceita um array de pares no topo / EN: accepts a top-level array of pairs"""
    dados = json.loads(geracao.texto)
    if isinstance(dados, list):
        geracao = dataclasses.replace(geracao, texto=json.dumps(dict(dados), ensure_ascii=False))
    return _LER_JSON_PREFIXADO(geracao, campos)


_HIPOTESES = hipoteses_por_variacao.hipoteses_vigentes()


def autoteste(registros: list[dict] | None) -> list[str]:
    if problemas := validar(registros)[0]:
        return [f"a validação já falha antes do autoteste: {problemas[:3]}"]
    negativos = [
        ("variação que não acrescenta nada", mock.patch.dict(variacoes.VARIACOES, {
            "V1": variacoes.Variacao("V1", chaves_prefixadas=True)}), "cardápio"),
        ("leitura que aceita qualquer ordem", mock.patch.object(modulo_responder, "ler_json_prefixado",
                                                                 _leitura_tolerante), "fora da ordem"),
        ("leitura que aceita array no topo", mock.patch.object(modulo_responder, "ler_json_prefixado",
                                                                _leitura_que_aceita_array), "array de pares"),
        ("nova tentativa que não olha o vazio", mock.patch.object(modulo_responder, "resultado_vazio",
                                                                   lambda r: False), "vazio"),
        ("variação registrada sem os textos dela no hipoteses.yml",
         mock.patch.object(executar_experimento, "variacao_registrada", lambda: "V2"), "texto pronto"),
        ("errata 6 que muda o hipoteses.yml fora dos caminhos", mock.patch.object(
            hipoteses_por_variacao, "hipoteses_vigentes", lambda: {**_HIPOTESES, "estatistica": {
                **_HIPOTESES["estatistica"], "alfa": 0.10}}), "fora dos caminhos"),
        ("critério que muda com a condição", mock.patch.object(
            variacoes, "mensagem_da_primeira",
            side_effect=lambda v, p, _n=[0]: (_n.__setitem__(0, _n[0] + 1), f"{p} {_n[0]}")[1]), "muda entre"),
    ]
    falhas = []
    for descricao, remendo, trecho in negativos:
        with remendo:
            try:
                problemas = validar(registros)[0]
            except Exception as erro:  # noqa: BLE001 - estrago que quebra também reprova
                problemas = [f"quebrou: {erro!r}"]
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas[:3]}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    args = parser.parse_args()

    registros = registros_da_execucao_1()
    if args.autoteste:
        falhas = autoteste(registros)
    else:
        falhas, conferidos = validar(registros)
        fonte = "sem os registros da execução 1, pulada" if registros is None else f"{conferidos} primeiras chamadas"
        print(f"  cardápio {variacoes.ORDEM}; V-1 contra a execução 1: {fonte}; condições e fluxo conferidos")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
