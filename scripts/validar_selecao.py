"""
PT: Valida a seleção dos modelos (#48, ADR 0030) sem modelo, sem rede e sem
    dado. Roda no workflow próprio .github/workflows/selecao.yml.

    O que é conferido:

    1. **selecao.yml.** Temperatura e seeds do pré-registro; duas classes,
       com pelo menos dois candidatos cada; todo candidato passa da regra de
       entrada, e todo excluído fica abaixo dela; nomes únicos; sha256 com
       64 hexadecimais e num_ctx múltiplo de 4.096, quando preenchidos; e
       nenhum campo nulo depois que o arquivo entra por errata no
       evaluation/registro.yml. Os limites do assistente/parametros.yml são
       os do selecao.yml, para o experimento rodar como a seleção.
    2. **Corretor, nas próprias respostas do gabarito.** Cada leitura, em
       cada janela, tem de bater quando a resposta é a tabela do gabarito
       disfarçada: colunas com outro nome e em outra ordem, reais em
       bilhões, percentuais como fração e números em formato brasileiro.
    3. **Corretor, contra estragos.** Tirar o valor que cada conferência
       olha, ou o primeiro item obrigatório de cada lista, faz a leitura
       deixar de bater. Item a mais num conjunto, item de fora com valor que
       o poria no ranking e item faltando reprovam; o item na zona de
       indiferença do limiar pode estar ou não (Q29 e Q21).
    4. **Situação da execução.** Erro da execução, abstenção indevida,
       resposta numa pergunta de abstenção, ressalva e leitura declarada a
       julgar, e o acerto de 3 em 5, com a fila de julgamento só do que
       ainda muda o acerto.
    5. **Cegamento.** O item da correção às cegas não mostra o candidato
       nem o SQL, e as citações saem do texto.
    6. **Resultado, quando existe.** Os escolhidos seguem a regra de
       escolha e de desempate; cada candidato tem as 41 perguntas com 5
       execuções; e o assistente/parametros.yml traz os escolhidos, sem
       provisorio. A troca da lista de modelos é conferida também numa
       cópia, antes de existir resultado.

    Com --autoteste, troca uma peça por vez por uma versão estragada e
    confere que a validação reprova cada uma pelo motivo certo.

EN: Validates the model selection with no model, network or data: the
    selection file's rules, the grader on disguised answer key tables and
    against breakages (removed values and items, extra items, outsiders in
    rankings, indifference zone), run situations and the 3-of-5 rule, blind
    grading display, and the result's consistency with the choice rule.
    --autoteste swaps one piece at a time for a broken version.

Uso / Usage:
    uv run python -m scripts.validar_selecao
    uv run python -m scripts.validar_selecao --autoteste
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import functools
import io
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable
from unittest import mock

import yaml

from assistente import parametros
from correcao import acerto, as_cegas, corretor
from correcao.corretor import Consulta, Gabarito, carregar_gabarito, corrigir, numero, situacao_no_filtro
from scripts import resumir_selecao
from scripts.selecionar_modelos import CAMPOS_MEDIDOS, SELECAO, carregar_selecao
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import HIPOTESES, REGISTRO, RAIZ, hashes_vigentes

HASH = re.compile(r"^[0-9a-f]{64}$")
_booleano_original = corretor.booleano


# -----------------------------------------------------------------------------
# PT: 1. selecao.yml / EN: the selection file
# -----------------------------------------------------------------------------

def checar_selecao(selecao: dict, hipoteses: dict, registrado: bool, parametros_yml: dict) -> list[str]:
    erros = []
    execucao, geracao = hipoteses["execucao"], selecao["geracao"]
    if geracao["temperatura"] != execucao["temperatura"] or list(geracao["seeds"]) != list(execucao["seeds"]):
        erros.append("selecao.yml: temperatura ou seeds diferentes do pré-registro")
    if execucao["execucoes_por_pergunta"] != acerto.EXECUCOES_POR_PERGUNTA:
        erros.append("acerto: execuções por pergunta diferentes do pré-registro")

    minimo = int(selecao["regras"]["contexto_minimo"])
    candidatos = selecao["candidatos"]
    nomes = [c["nome"] for c in candidatos]
    if len(set(nomes)) != len(nomes):
        erros.append("selecao.yml: nome de candidato repetido")
    classes = {}
    for c in candidatos:
        classes.setdefault(c["classe"], []).append(c["nome"])
        if int(c["contexto_publicado"]) < minimo:
            erros.append(f"selecao.yml: {c['nome']} abaixo da regra de entrada ({c['contexto_publicado']} < {minimo})")
        if c.get("sha256") is not None and not HASH.match(str(c["sha256"])):
            erros.append(f"selecao.yml: sha256 de {c['nome']} fora do formato")
        if c.get("num_ctx") is not None and int(c["num_ctx"]) % int(selecao["dimensionamento"]["multiplo"]):
            erros.append(f"selecao.yml: num_ctx de {c['nome']} não é múltiplo de {selecao['dimensionamento']['multiplo']}")
        if registrado and (nulos := [k for k in CAMPOS_MEDIDOS if c.get(k) is None]):
            erros.append(f"selecao.yml: congelado com campos nulos em {c['nome']}: {nulos}")
    if len(classes) != 2 or any(len(v) < 2 for v in classes.values()):
        erros.append(f"selecao.yml: são precisas duas classes com pelo menos dois candidatos: {classes}")
    for e in selecao.get("excluidos") or []:
        if int(e["contexto_publicado"]) >= minimo:
            erros.append(f"selecao.yml: excluído {e['nome']} passa da regra de entrada")

    g, s = parametros_yml["geracao"], parametros_yml["sql"]
    pares = [
        ("limite_de_tokens_da_resposta", g["limite_de_tokens_da_resposta"], geracao["limite_de_tokens_da_resposta"]),
        ("think", g["think"], geracao["think"]),
        ("esquema_json", g["esquema_json"], geracao["esquema_json"]),
        ("tempo do servidor", parametros_yml["servidor"]["tempo_maximo_em_segundos"],
         geracao["tempo_maximo_do_servidor_em_segundos"]),
        ("limite_de_linhas", s["limite_de_linhas"], selecao["sql"]["limite_de_linhas"]),
        ("limite de tempo do SQL", s["limite_de_tempo_em_segundos"], selecao["sql"]["limite_de_tempo_em_segundos"]),
    ]
    erros += [f"parametros.yml: {nome} {a} difere do selecao.yml {b}" for nome, a, b in pares if a != b]
    return erros


# -----------------------------------------------------------------------------
# PT: 2 e 3. Corretor / EN: grader
# -----------------------------------------------------------------------------

def _pt(numero_: Decimal) -> str:
    """PT: o número em formato brasileiro / EN: number in Brazilian format"""
    inteiro, _, fracao = f"{numero_:f}".partition(".")
    sinal = "-" if inteiro.startswith("-") else ""
    inteiro = inteiro.lstrip("-")
    grupos = []
    while inteiro:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    return sinal + ".".join(grupos or ["0"]) + ("," + fracao if fracao else "")


def disfarcar(g: Gabarito, id_: str, leitura: str, forma: str = "", mutar: Callable | None = None) -> dict:
    """
    PT: A tabela do gabarito de uma leitura como uma resposta do modelo:
        as consultas empilhadas numa tabela só, as colunas sem nome e em
        ordem invertida. forma: "bilhoes" (reais grandes em bilhões),
        "fracao" (percentuais como fração) ou "pt" (números em texto, no
        formato brasileiro). mutar(consulta, k, linha) muda ou tira (None)
        uma linha do gabarito.
    EN: A reading's key tables as a model answer: queries stacked in one
        table, columns unnamed and reversed, with an optional format and
        mutation.
    """
    blocos = g.comparacao[id_][leitura]
    colunas = list(dict.fromkeys((b["consulta"], c) for b in blocos for c in g.respostas[b["consulta"]]["colunas"]))
    linhas = []
    for b in blocos:
        r = g.respostas[b["consulta"]]
        consulta = Consulta.de(b["consulta"], r, g.regra)
        grandes = {c for c in r["colunas"] if consulta.classes[c] == "relativa"
                   and any((n := numero(l[r["colunas"].index(c)])) is not None and abs(n) > 10 ** 8 for l in r["linhas"])}
        for k, l in enumerate(r["linhas"]):
            linha = dict(zip(r["colunas"], l))
            if mutar:
                linha = mutar(b["consulta"], k, linha)
                if linha is None:
                    continue
            saida = []
            for q, c in colunas:
                v = linha.get(c) if q == b["consulta"] else None
                n = numero(v) if v is not None and consulta.classes.get(c) not in ("identidade", "classificacao") else None
                if n is not None and forma == "bilhoes" and c in grandes:
                    v = str(n / Decimal(10) ** 9)
                elif n is not None and forma == "fracao" and consulta.classes[c] == "pontos":
                    v = str(n / 100)
                elif n is not None and forma == "pt":
                    v = _pt(n)
                saida.append(v)
            linhas.append(list(reversed(saida)))
    return {"colunas": [f"coluna {i}" for i in range(len(colunas))], "linhas": linhas}


def _janelas(blocos: list[dict]) -> list[str]:
    return sorted({j for b in blocos for j in (b.get("janelas") or {})}) or [""]


def _bate(g: Gabarito, id_: str, leitura: str, janela: str, valores: dict) -> bool:
    return any(r["bate"] for r in corretor.corrigir_valores(id_, valores, g)
               if r["leitura"] == leitura and r["janela"] == janela)


def _leituras(g: Gabarito):
    for id_, entrada in g.comparacao.items():
        if entrada != {"abstencao": "so_rubrica"}:
            for leitura, blocos in entrada.items():
                yield id_, leitura, blocos


def checar_disfarces(g: Gabarito) -> tuple[list[str], int]:
    erros, casos = [], 0
    for id_, leitura, blocos in _leituras(g):
        for forma in ("", "bilhoes", "fracao", "pt"):
            tabela = disfarcar(g, id_, leitura, forma)
            for janela in _janelas(blocos):
                casos += 1
                if not _bate(g, id_, leitura, janela, tabela):
                    erros.append(f"corretor: a tabela do gabarito disfarçada ({forma or 'nomes'}) não bate em "
                                 f"{id_} {leitura} {janela}".rstrip())
    return erros, casos


def _longe(classe: str, valor) -> str:
    if classe == "classificacao":
        return "false" if str(valor).lower() == "true" else "true"
    n = numero(valor)
    return "zzz" if classe == "identidade" or n is None else str(n * 3 + 7)


def _ainda_aparece(tabela: dict, consulta: Consulta, item: dict) -> bool:
    """
    PT: Um valor igual em todas as linhas do gabarito (a mediana da Q14, a
        razão nacional da Q15) vale em qualquer linha da resposta. Se ele
        continua na tabela, dentro da tolerância, como valor legítimo de
        outra célula (a UF da mediana), o estrago não se aplica.
    EN: A value equal on every key row counts on any answer row; if it still
        shows within tolerance as another cell's own value, the breakage
        does not apply.
    """
    colunas = [item["valor"]] if "valor" in item else list(item.get("uma_de") or [item.get("classificacao")])
    linha = consulta.linha(item.get("linha"))
    for c in colunas:
        classe, alvo = consulta.classes[c], numero(linha[c])
        if classe in ("identidade", "classificacao") or alvo is None or len({l[c] for l in consulta.linhas}) > 1:
            continue
        for fator in corretor.FATORES[classe]:
            if any((n := numero(v)) is not None and corretor.dentro_da_banda(classe, n * fator, alvo)
                   for l in tabela["linhas"] for v in l):
                return True
    return False


def checar_estragos(g: Gabarito) -> tuple[list[str], int]:
    """
    PT: Para cada conferência, tira da tabela o que ela olha: o valor (em
        todas as linhas em que ele se repete) ou o primeiro item
        obrigatório da lista. A leitura, naquela janela, tem de deixar de
        bater.
    EN: For each check, remove what it looks at; the reading must stop
        matching.
    """
    erros, casos = [], 0
    for id_, leitura, blocos in _leituras(g):
        for janela in _janelas(blocos):
            for b in blocos:
                consulta = Consulta.de(b["consulta"], g.respostas[b["consulta"]], g.regra)
                for item in b["verificar"] if "verificar" in b else b["janelas"][janela]:
                    if "lista" in item:
                        if item["lista"] == "ranking":
                            alvo = corretor._ordem(consulta, item["ordem"])[0]
                        else:
                            obrigatorios = [k for k, l in enumerate(consulta.linhas) if not item.get("onde")
                                            or situacao_no_filtro(l, item["onde"], consulta) == "dentro"]
                            if not obrigatorios:
                                continue
                            alvo = obrigatorios[0]

                        def mutar(q, k, linha, alvo=alvo, q0=b["consulta"]):
                            return None if (q, k) == (q0, alvo) else linha
                    else:
                        colunas = [item["valor"]] if "valor" in item else list(item.get("uma_de") or [item["classificacao"]])
                        alvo_linha = consulta.linha(item.get("linha"))

                        # PT: o valor sai de toda célula da consulta em que aparece, em
                        #     qualquer coluna (a razão nacional da Q15 se repete).
                        # EN: the value leaves every cell of the query where it shows.
                        def mutar(q, k, linha, colunas=colunas, alvo_linha=alvo_linha, q0=b["consulta"], consulta=consulta):
                            if q != q0:
                                return linha
                            alvos = {alvo_linha[c]: consulta.classes[c] for c in colunas}
                            return {c: _longe(alvos[v], v) if v in alvos else v for c, v in linha.items()}
                    tabela = disfarcar(g, id_, leitura, mutar=mutar)
                    if "lista" not in item and _ainda_aparece(tabela, consulta, item):
                        continue
                    casos += 1
                    if _bate(g, id_, leitura, janela, tabela):
                        erros.append(f"corretor: aprovou {id_} {leitura} {janela} sem o que {item} confere".replace("  ", " "))
    return erros, casos


def checar_casos_de_lista(g: Gabarito) -> list[str]:
    erros = []

    def so(consulta_nome: str, manter: Callable[[dict, int], bool]) -> Callable:
        return lambda q, k, linha: linha if q != consulta_nome or manter(linha, k) else None

    # PT: conjunto por limiar, só os itens abaixo da mediana (Q14), com e sem um a mais.
    # EN: threshold set, only items below the median, with and without one extra.
    abaixo = lambda l, k: l["abaixo_da_mediana"] == "true"
    c14 = "Q14_todas_as_empresas.sql"
    if not _bate(g, "Q14", "todas_as_empresas", "", disfarcar(g, "Q14", "todas_as_empresas", mutar=so(c14, abaixo))):
        erros.append("corretor: Q14 só com os itens abaixo da mediana não bate")
    linhas14 = g.respostas[c14]["linhas"]
    i_flag = g.respostas[c14]["colunas"].index("abaixo_da_mediana")
    # PT: a última UF, longe da mediana; a UF da própria mediana fica na zona.
    # EN: the last state, far from the median.
    acima = max(k for k, l in enumerate(linhas14) if l[i_flag] == "false")

    def com_um_a_mais(q, k, linha):
        if q != c14:
            return linha
        if linha["abaixo_da_mediana"] == "true" or k == acima:
            return {**linha, "abaixo_da_mediana": None}
        return None
    if _bate(g, "Q14", "todas_as_empresas", "", disfarcar(g, "Q14", "todas_as_empresas", mutar=com_um_a_mais)):
        erros.append("corretor: aprovou a Q14 com um item a mais no conjunto")

    # PT: zona de indiferença na Q29: a carteira ativa, com z de −1,995, pode estar ou não.
    # EN: indifference zone in Q29: the item at z = −1.995 is optional.
    c29 = "Q29_12_meses.sql"
    r29 = g.respostas[c29]
    iz = r29["colunas"].index("z")
    zona = [k for k, l in enumerate(r29["linhas"]) if l[iz] is not None and Decimal("1.98") < abs(Decimal(l[iz])) < 2]
    if not zona:
        erros.append("corretor: a Q29 não tem mais o item na zona de indiferença que o teste usa")
    else:
        # PT: a resposta lista só os itens que dá como atípicos, sem a
        #     coluna booleana, que já resolveria o conjunto sozinha.
        # EN: the answer lists only the items it calls atypical, without the
        #     boolean column, which would settle the set alone.
        for com_ele in (True, False):
            def selecao_atipica(q, k, linha, com_ele=com_ele):
                if q != c29:
                    return linha
                if linha["atipica"] == "true" or (com_ele and k in zona):
                    return {**linha, "atipica": None}
                return None
            if not _bate(g, "Q29", "12_meses", "", disfarcar(g, "Q29", "12_meses", mutar=selecao_atipica)):
                erros.append(f"corretor: a Q29 {'com' if com_ele else 'sem'} o item da zona de indiferença não bate")

    # PT: ranking em que a última UF do gabarito aparece com valor maior que
    #     o da primeira (Q11): ela entraria no topo.
    # EN: ranking where the key's last state shows a value above the first.
    tabela = disfarcar(g, "Q11", "unica")
    r11 = g.respostas["Q11.sql"]
    valor = dict(zip(r11["colunas"], r11["linhas"][0]))["carteira_pj_por_habitante"]
    j = next(j for j, v in enumerate(tabela["linhas"][0]) if v == valor)
    linhas = [list(l) for l in tabela["linhas"]]
    linhas[-1][j] = str(Decimal(valor) * 2)
    if _bate(g, "Q11", "unica", "", {"colunas": tabela["colunas"], "linhas": linhas}):
        erros.append("corretor: aprovou o ranking da Q11 com um item de fora melhor que o primeiro")

    # PT: um total na coluna do valor do ranking não é item do ranking (Q11).
    # EN: a total in the ranking value column is not a ranking item.
    total = [None] * len(tabela["colunas"])
    total[j] = str(Decimal(valor) * 50)
    total[next(k for k, v in enumerate(tabela["linhas"][0]) if v == r11["linhas"][0][r11["colunas"].index("uf")])] = "Total"
    if not _bate(g, "Q11", "unica", "", {"colunas": tabela["colunas"], "linhas": [*tabela["linhas"], total]}):
        erros.append("corretor: reprovou o ranking da Q11 por causa de uma linha de total")

    # PT: Q21 em formato longo, "tipo | modalidade | ganho", com os dois
    #     conjuntos certos na mesma tabela.
    # EN: Q21 in long format with both correct sets in one table.
    c21 = Consulta.de("Q21.sql", g.respostas["Q21.sql"], g.regra)
    #     No recorte, um item do conjunto das fintechs fica fora do das IPs.
    # EN: in the full window, a fintech item is outside the IP set.
    onde = {"ip": [{"coluna": "ganho_ip_no_recorte_pp", "op": "maior_que", "valor": 0}],
            "fintech": [{"coluna": "ganho_fintech_no_recorte_pp", "op": "maior_que", "valor": 0}]}
    longa = [[tipo, l["codigo_modalidade"], l["modalidade"], l[f"ganho_{tipo}_no_recorte_pp"]]
             for tipo, condicao in onde.items() for l in c21.linhas
             if situacao_no_filtro(l, condicao, c21) == "dentro"]
    if not _bate(g, "Q21", "unica", "recorte", {"colunas": ["tipo", "codigo", "nome", "ganho"], "linhas": longa}):
        erros.append("corretor: reprovou a Q21 em formato longo, com os dois conjuntos certos")

    # PT: a classificação errada da Q08 não passa por causa de um 0 solto.
    # EN: a wrong Q08 classification does not pass on a stray 0.
    r08 = dict(zip(g.respostas["Q08.sql"]["colunas"], g.respostas["Q08.sql"]["linhas"][0]))
    errada = "acima" if r08["acima_da_media"] == "false" else "abaixo"
    q08 = {"colunas": ["mes", "taxa", "media", "situacao", "variacao"],
           "linhas": [[r08["mes"], r08["taxa_no_ultimo_mes_pct"], r08["media_das_taxas_mensais_pct"], errada, 0]]}
    if _bate(g, "Q08", "unica", "", q08):
        erros.append("corretor: aprovou a classificação errada da Q08 por causa de um 0")

    # PT: um inteiro pequeno, como um ano, não ganha escala (Q01).
    # EN: a small integer, like a year, gets no scale.
    r01 = dict(zip(g.respostas["Q01.sql"]["colunas"], g.respostas["Q01.sql"]["linhas"][0]))
    q01 = {"colunas": ["ano", "anterior", "variacao_pct"],
           "linhas": [[str(round(Decimal(r01["carteira_ativa"]) / Decimal(10) ** 9)),
                       r01["carteira_ativa_do_ano_anterior"], r01["variacao_pct"]]]}
    if _bate(g, "Q01", "unica", "", q01):
        erros.append("corretor: aprovou a Q01 com um inteiro pequeno escalado para a carteira")
    return erros


# -----------------------------------------------------------------------------
# PT: 4 e 5. Situação, acerto e cegamento / EN: situation, correctness, blinding
# -----------------------------------------------------------------------------

def _registro(id_: str, valores=None, abstencao: str = "", erro: dict | None = None, ressalva: str = "") -> dict:
    return {"candidato": "candidato-secreto", "id_pergunta": id_, "seed": 1, "erro": erro,
            "resposta": None if erro else {"interpretacao": "x", "sql": "select segredo", "ressalva": ressalva,
                                           "valores": valores or {"colunas": [], "linhas": []}, "abstencao": abstencao}}


def checar_situacoes(g: Gabarito) -> list[str]:
    erros = []
    q01 = disfarcar(g, "Q01", "unica")
    casos = [
        ("erro da execução", corrigir("Q01", _registro("Q01", erro={"tipo": "sql", "etapa": "sql", "mensagem": ""}), g),
         ("errado", "erro_sql")),
        ("abstenção indevida", corrigir("Q01", _registro("Q01", q01, abstencao="não dá"), g), ("errado", "abstencao_indevida")),
        ("valor certo", corrigir("Q01", _registro("Q01", q01), g), ("certo", "")),
        ("valor errado", corrigir("Q01", _registro("Q01", {"colunas": ["a"], "linhas": [[1]]}), g), ("errado", "valor")),
        ("resposta em pergunta de abstenção", corrigir("Q41", _registro("Q41", q01), g), ("errado", "sem_abstencao")),
        ("abstenção a julgar", corrigir("Q41", _registro("Q41", abstencao="falta a taxa"), g), ("pendente", "")),
        ("ressalva a julgar", corrigir("Q09", _registro("Q09", disfarcar(g, "Q09", "unica"), ressalva="r"), g),
         ("pendente", "")),
        ("ressalva vazia", corrigir("Q09", _registro("Q09", disfarcar(g, "Q09", "unica")), g), ("errado", "sem_ressalva")),
        ("leitura a julgar", corrigir("Q28", _registro("Q28", disfarcar(g, "Q28", "no_mes")), g), ("pendente", "")),
    ]
    for descricao, saida, (situacao, motivo) in casos:
        if (saida["situacao"], saida["motivo"]) != (situacao, motivo):
            erros.append(f"situação: {descricao} deu {saida['situacao']} {saida['motivo']}, esperado {situacao} {motivo}")
    if corrigir("Q09", _registro("Q09", disfarcar(g, "Q09", "unica"), ressalva="r"), g)["julgar"] != ["ressalva"]:
        erros.append("situação: a Q09 tem de julgar só a ressalva")
    if corrigir("Q28", _registro("Q28", disfarcar(g, "Q28", "no_mes")), g)["julgar"] != ["leitura_declarada"]:
        erros.append("situação: a Q28 tem de julgar só a leitura declarada")

    quadro = [
        (["certo", "certo", "certo"], "certo"), (["errado", "errado", "errado"], "errado"),
        (["certo", "certo", "errado", "errado"], "pendente"), (["certo", "certo", "errado", "errado", "errado"], "errado"),
        (["certo", "pendente", "certo", "errado", "pendente"], "pendente"), ([], "pendente"),
    ]
    for situacoes, esperado in quadro:
        if acerto.acerto_da_pergunta(situacoes) != esperado:
            erros.append(f"acerto: {situacoes} deu {acerto.acerto_da_pergunta(situacoes)}, esperado {esperado}")
    pend = {"situacao": "pendente", "julgar": ["ressalva", "leitura_declarada"]}
    for julgamento, esperado in [(None, "pendente"), ({"ressalva": True}, "pendente"),
                                 ({"ressalva": False}, "errado"), ({"ressalva": True, "leitura_declarada": True}, "certo")]:
        if acerto.acerto_da_execucao(pend, julgamento) != esperado:
            erros.append(f"acerto: julgamento {julgamento} deu {acerto.acerto_da_execucao(pend, julgamento)}")

    # PT: a fila só traz pergunta indecisa: três certas dispensam as pendentes.
    # EN: the queue holds only undecided questions.
    def item(seed, situacao):
        return {"candidato": "c", "pergunta": "Q09", "seed": seed, "situacao": situacao, "item": str(seed)}
    decidida = [item(1, "certo"), item(2, "certo"), item(3, "certo"), item(4, "pendente"), item(5, "pendente")]
    indecisa = [item(1, "certo"), item(2, "errado"), item(3, "pendente"), item(4, "pendente"), item(5, "errado")]
    if acerto.a_julgar(decidida) or len(acerto.a_julgar(indecisa)) != 2:
        erros.append("acerto: a fila de julgamento não segue só o que muda o acerto")
    return erros


def checar_cegamento(g: Gabarito) -> list[str]:
    erros = []
    texto = "Usei metricas.carteira_ativa (documento 3040, seção 2, página 7) [trecho 3] e p. 12."
    limpo = as_cegas.sem_citacoes(texto)
    if any(marca in limpo for marca in ("metricas.", "3040", "página", "trecho", "p. 12")):
        erros.append(f"cegamento: sobrou citação em '{limpo}'")
    registro = _registro("Q09", disfarcar(g, "Q09", "unica"), ressalva="ver metricas.ativo_problematico")
    c = acerto.corrigir_todas([registro], {}, g)[0]
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        as_cegas.mostrar(c, registro, "enunciado", g, 1)
        print(as_cegas.rubrica("ressalva", "Q09", c["correcao"], g))
    mostrado = saida.getvalue()
    if any(segredo in mostrado for segredo in ("candidato-secreto", "select segredo", "metricas.")):
        erros.append("cegamento: o item mostra o candidato, o SQL ou uma citação")
    return erros


# -----------------------------------------------------------------------------
# PT: 6. Resultado / EN: result
# -----------------------------------------------------------------------------

def checar_escolha() -> list[str]:
    """PT: a regra de escolha e de desempate, em placares inventados / EN: tie rules"""
    erros = []
    def p(nome, classe, certas, vram):
        return {"nome": nome, "classe": classe, "perguntas_certas": certas, "vram": vram}
    casos = [
        ([p("a", "x", 20, 9), p("b", "x", 22, 11)], {"x": "b"}),
        ([p("a", "x", 20, 9), p("b", "x", 20, 8)], {"x": "b"}),
        ([p("a", "x", 20, 9), p("b", "x", 20, 9)], {"x": "a"}),
        ([p("a", "x", 1, 1), p("b", "y", 2, 2), p("c", "y", 3, 3)], {"x": "a", "y": "c"}),
    ]
    for placares, esperado in casos:
        if resumir_selecao.escolher(placares) != esperado:
            erros.append(f"escolha: {placares} deu {resumir_selecao.escolher(placares)}, esperado {esperado}")
    return erros


def checar_troca_de_parametros(selecao: dict) -> list[str]:
    """
    PT: Numa cópia: a troca da lista de modelos pelos escolhidos dá um
        parametros.yml que carrega, sem provisorio, com o num_ctx do
        candidato.
    EN: On a copy, swapping in the chosen models yields a loadable file.
    """
    import tempfile
    from pathlib import Path

    copia = copy.deepcopy(selecao)
    for i, c in enumerate(copia["candidatos"]):
        c.update({"revisao": "r" * 40, "sha256": "a" * 64, "num_ctx": 49152 + 4096 * i, "caracteres_por_token": 2.9})
    escolhidos = {}
    for c in copia["candidatos"]:
        escolhidos.setdefault(c["classe"], c["nome"])
    texto = resumir_selecao.atualizar_parametros(resumir_selecao.PARAMETROS.read_text(encoding="utf-8"), copia, escolhidos)
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "parametros.yml"
        arquivo.write_text(texto, encoding="utf-8")
        nomes = parametros.modelos(arquivo)
        primeiro = next(c for c in copia["candidatos"] if c["nome"] == next(iter(escolhidos.values())))
        p = parametros.carregar(arquivo)
    erros = []
    if p.provisorio or "provisorio" in yaml.safe_load(texto):
        erros.append("parâmetros: a troca deixou o provisorio")
    if len(nomes) != len(escolhidos) or p.modelo != primeiro["ollama"] or p.num_ctx != primeiro["num_ctx"]:
        erros.append(f"parâmetros: a troca deu {nomes}, num_ctx {p.num_ctx}")
    return erros


def checar_resultado(resultado: dict, parametros_yml: dict, ids: list[str]) -> list[str]:
    erros = []
    placares = resultado["candidatos"]
    if resumir_selecao.escolher(placares) != resultado["escolhidos"]:
        erros.append(f"resultado: escolhidos {resultado['escolhidos']} não seguem a regra")
    for p in placares:
        if list(p["perguntas"]) != ids or any(len(q["execucoes"]) != acerto.EXECUCOES_POR_PERGUNTA
                                              for q in p["perguntas"].values()):
            erros.append(f"resultado: {p['nome']} sem as {len(ids)} perguntas com 5 execuções")
        if p["perguntas_certas"] != sum(q["acerto"] == "certo" for q in p["perguntas"].values()):
            erros.append(f"resultado: perguntas certas de {p['nome']} não batem com as perguntas")
    por_nome = {p["nome"]: p for p in placares}
    esperados = [(por_nome[n]["ollama"], por_nome[n]["num_ctx"]) for n in resultado["escolhidos"].values()]
    no_arquivo = [(m["nome"], m["num_ctx"]) for m in parametros_yml["modelos"]]
    if no_arquivo != esperados:
        erros.append(f"parametros.yml: modelos {no_arquivo}, escolhidos {esperados}")
    if parametros_yml.get("provisorio"):
        erros.append("parametros.yml: ainda provisório depois do resultado")
    return erros


# -----------------------------------------------------------------------------
# PT: Validação / EN: validation
# -----------------------------------------------------------------------------

@dataclass
class Dados:
    selecao: dict
    hipoteses: dict
    registro: dict
    parametros_yml: dict
    resultado: dict | None
    ids: list[str]


def ler() -> Dados:
    def y(caminho):
        return yaml.safe_load((RAIZ / caminho).read_text(encoding="utf-8"))
    arquivo = resumir_selecao.RESULTADO
    return Dados(
        selecao=carregar_selecao(), hipoteses=y(HIPOTESES), registro=y(REGISTRO),
        parametros_yml=yaml.safe_load(resumir_selecao.PARAMETROS.read_text(encoding="utf-8")),
        resultado=json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None,
        ids=list(perguntas(VIGENTE)[1]),
    )


def validar(d: Dados, g: Gabarito, contagem: dict | None = None, corretor_tambem: bool = True) -> list[str]:
    """
    PT: corretor_tambem=False pula as conferências do corretor, que não
        dependem dos arquivos: o autoteste usa isso nos estragos de arquivo.
    EN: corretor_tambem=False skips the file-independent grader checks.
    """
    registrado = SELECAO in hashes_vigentes(d.registro)
    erros = checar_selecao(d.selecao, d.hipoteses, registrado, d.parametros_yml)
    n_disfarces = n_estragos = 0
    if corretor_tambem:
        disfarces, n_disfarces = checar_disfarces(g)
        estragos, n_estragos = checar_estragos(g)
        erros += disfarces + estragos + checar_casos_de_lista(g) + checar_situacoes(g) + checar_cegamento(g)
    erros += checar_escolha() + checar_troca_de_parametros(d.selecao)
    if d.resultado is not None:
        erros += checar_resultado(d.resultado, d.parametros_yml, d.ids)
    if contagem is not None:
        contagem.update(disfarces=n_disfarces, estragos=n_estragos, registrado=registrado)
    return erros


def autoteste(d: Dados, g: Gabarito) -> list[str]:
    """
    PT: Cada caso estraga uma peça e diz o trecho que a reprovação precisa
        trazer.
    EN: Each case breaks one piece and names the expected fragment.
    """
    if problemas := validar(d, g):
        return [f"a validação já falha antes do autoteste: {problemas[:3]}"]

    def temperatura_errada():
        copia = copy.deepcopy(d)
        copia.selecao["geracao"]["temperatura"] = 0.7
        return copia

    def candidato_curto():
        copia = copy.deepcopy(d)
        copia.selecao["candidatos"][0]["contexto_publicado"] = 40960
        return copia

    def classe_sozinha():
        copia = copy.deepcopy(d)
        copia.selecao["candidatos"] = [c for c in copia.selecao["candidatos"] if c["nome"] != "ministral-3-14b"]
        return copia

    def congelado_com_nulos():
        copia = copy.deepcopy(d)
        copia.registro["erratas"] = [*copia.registro.get("erratas", []), {"arquivo": SELECAO, "sha256": "0" * 64}]
        return copia

    def limite_divergente():
        copia = copy.deepcopy(d)
        copia.parametros_yml["sql"]["limite_de_linhas"] = 500
        return copia

    def resultado_errado():
        copia = copy.deepcopy(d)
        placares = [
            {"nome": c["nome"], "classe": c["classe"], "ollama": c["ollama"], "num_ctx": 4096, "vram": 1,
             "perguntas_certas": 0, "perguntas": {i: {"execucoes": ["errado"] * 5, "acerto": "errado"} for i in d.ids}}
            for c in d.selecao["candidatos"]
        ]
        placares[1]["perguntas_certas"] = 1
        placares[1]["perguntas"][d.ids[0]] = {"execucoes": ["certo"] * 5, "acerto": "certo"}
        copia.resultado = {"escolhidos": {"14b": placares[0]["nome"], "8b": placares[2]["nome"]}, "candidatos": placares}
        return copia

    negativos = [
        ("temperatura fora do pré-registro", temperatura_errada, None, "temperatura ou seeds"),
        ("candidato abaixo da regra de entrada", candidato_curto, None, "abaixo da regra de entrada"),
        ("classe com um candidato só", classe_sozinha, None, "duas classes"),
        ("selecao.yml congelado com campos nulos", congelado_com_nulos, None, "congelado com campos nulos"),
        ("limite do parametros.yml diferente do selecao.yml", limite_divergente, None, "limite_de_linhas"),
        ("resultado com escolhido fora da regra", resultado_errado, None, "não seguem a regra"),
        ("corretor sem conversão de escala", lambda: d, mock.patch.dict(corretor.FATORES, {
            "relativa": (Decimal(1),), "pontos": (Decimal(1),)}), "disfarçada (bilhoes)"),
        ("corretor sem zona de indiferença", lambda: d, mock.patch.object(corretor, "banda_da_zona",
                                                                          lambda classe, valor: Decimal(0)), "zona de indiferença"),
        ("corretor que aceita qualquer número", lambda: d, mock.patch.object(corretor, "dentro_da_banda",
                                                                             lambda classe, a, b: True), "aprovou"),
        ("corretor que não restringe o conjunto", lambda: d, mock.patch.object(corretor, "situacao_no_filtro",
                                                                               lambda *a: "opcional"), "item a mais"),
        ("booleano que aceita qualquer 0 ou 1", lambda: d, mock.patch.object(
            corretor, "booleano", functools.partial(_booleano_original, curto=True)), "classificação errada da Q08"),
        ("conjunto sem os blocos do formato longo", lambda: d, mock.patch.object(corretor, "_grupos",
                                                                                 lambda *a: []), "formato longo"),
        ("fila que julga pergunta decidida", lambda: d, mock.patch.object(acerto, "acerto_da_pergunta",
                                                                          lambda s, total=5: "pendente"), "fila de julgamento"),
        ("cegamento que deixa citação", lambda: d, mock.patch.object(as_cegas, "_CITACOES", []), "cegamento"),
    ]
    falhas = []
    for descricao, montar, remendo, trecho in negativos:
        with remendo or contextlib.nullcontext():
            problemas = validar(montar(), g, corretor_tambem=remendo is not None)
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

    d, g = ler(), carregar_gabarito()
    if args.autoteste:
        falhas = autoteste(d, g)
    else:
        contagem = {}
        falhas = validar(d, g, contagem)
        print(f"  {len(d.selecao['candidatos'])} candidatos em {len({c['classe'] for c in d.selecao['candidatos']})} "
              f"classes; corretor: {contagem['disfarces']} disfarces e {contagem['estragos']} estragos; "
              f"selecao.yml {'congelado' if contagem['registrado'] else 'ainda sem errata'}; resultado "
              f"{'conferido' if d.resultado is not None else 'ainda não gerado'}")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
