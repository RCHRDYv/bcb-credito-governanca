"""
PT: Valida o conjunto de desenvolvimento do instrumento (#118, ADR 0032) sem
    modelo, sem rede e sem dado. Roda no workflow experimento.yml.

    O que é conferido:

    1. **Perguntas.** 30 perguntas, de D01 a D30, com enunciado em português
       e em inglês, dependência e tipo válidos, papel e tabelas. A
       composição é de 8 controles positivos, 6 controles negativos e 16
       mistas (11 de valor, 4 de valor com ressalva e 1 de abstenção). Os
       controles positivos são de valor, dependência baixa, uma leitura e
       sem janela. Os negativos são de abstenção.
    2. **Nada repete o teste.** O enunciado tem Jaccard de palavras abaixo de
       0,6 contra cada uma das 41 perguntas registradas (a mesma regra do
       validar_assistente), e o SQL normalizado tem Jaccard de pares de
       tokens abaixo do limite contra cada um dos 56 SQL do teste. Com
       --embeddings (grupo rag do uv, fora do CI), confere também o cosseno
       dos embeddings do modelo do RAG.
    3. **Gabarito.** Cada entrada passa no checar_entrada e no checar_fontes
       do validar_gabarito; cada SQL passa no checar_sql, só com as tabelas
       da pergunta, e é planejado pelo DuckDB sobre tabelas vazias.
    4. **Respostas e comparação.** Toda consulta tem resposta, todas do mesmo
       mês do retrato; a comparação passa no checar_comparacao do
       validar_registro.
    5. **O corretor no próprio gabarito.** A resposta do gabarito, dada como
       resposta do modelo, sai certa nas perguntas de valor, pendente de
       ressalva nas de valor com ressalva e pendente de abstenção nas de
       abstenção. Com um número estragado, sai errada.

    Com --autoteste, estraga uma peça por vez e confere que a validação
    reprova cada uma pelo motivo certo.

EN: Validates the development set with no model, network or data: shape and
    composition, no overlap with the registered test (word Jaccard on the
    text, token-pair Jaccard on normalized SQL, optional embeddings), answer
    key entries, SQL and portability, answers and comparison spec, and the
    grader on the key's own answers. --autoteste breaks one piece at a time.

Uso / Usage:
    uv run python -m scripts.validar_desenvolvimento
    uv run python -m scripts.validar_desenvolvimento --autoteste
    uv run --group rag python -m scripts.validar_desenvolvimento --embeddings
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from unittest import mock

import duckdb
import yaml

from correcao.corretor import Gabarito, corrigir
from experimento import desenvolvimento as dev
from scripts.validar_gabarito import (
    ESQUEMA_ESTRELA,
    checar_entrada,
    checar_fontes,
    checar_sql,
    ids_da_ontologia,
    tipo_no_duckdb,
)
from scripts.validar_perguntas import DEPENDENCIAS, TIPOS_DE_ACERTO, VIGENTE, perguntas
from scripts.validar_registro import HIPOTESES, PASTA_SQL, RAIZ, checar_comparacao

TOTAL = 30
COMPOSICAO = {"controle_positivo": 8, "controle_negativo": 6, "mista": 16}
MISTAS_POR_TIPO = {"valor": 11, "valor_com_ressalva": 4, "abstencao": 1}
LIMITE_DO_ENUNCIADO = 0.6
LIMITE_DO_SQL = 0.6
# PT: acima deste cosseno, a pergunta vai para revisão humana e precisa
#     estar em metadata.revisadas_por_embeddings, com a justificativa.
#     Calibrado em 2026-10-15: uma paráfrase real da Q01 dá 0,801, e a D06,
#     que mede outra coisa, dá 0,787. Os embeddings não separam os dois
#     casos sozinhos.
# EN: above this cosine a question needs a recorded human review.
LIMITE_DOS_EMBEDDINGS = 0.78
# PT: pisos de estrutura dos SQL das mistas (decisão de 2026-10-15). No teste,
#     51 de 56 SQL têm junção, 49 têm CTE e 34 comparam períodos; as mistas
#     não precisam igualar, mas não podem ser só consultas de um passo.
# EN: structural floors for the mixed questions' SQL.
PISOS_DAS_MISTAS = {"juncao": 5, "cte": 8, "comparacao_no_tempo": 6}
# PT: literais aceitos no SQL de controle positivo: sigla de UF e número.
# EN: literals allowed in a positive control's SQL.
SIGLA_DE_UF = re.compile(r"^[A-Z]{2}$")
# PT: paráfrase real da Q01, que calibra o limite dos embeddings. O Jaccard
#     de palavras dela com a Q01 é 0,41: só os embeddings a pegam.
# EN: real paraphrase of Q01 that calibrates the embedding threshold.
PARAFRASE_DE_CALIBRACAO = ("No mês mais recente da base, qual foi o total da carteira ativa de crédito do país, "
                           "comparado com o mesmo mês um ano antes?")


# -----------------------------------------------------------------------------
# PT: Leitura / EN: reading
# -----------------------------------------------------------------------------

@dataclass
class Dados:
    por_id: dict[str, dict]
    metadata: dict
    gabarito: dict
    comparacao: dict
    respostas: dict[str, dict]
    sql: dict[str, str]
    registradas: dict[str, str]
    sql_do_teste: dict[str, str]
    regra: dict


def ler() -> Dados:
    metadata, por_id = dev.perguntas()
    _, registradas = perguntas(VIGENTE)
    return Dados(
        por_id=por_id,
        metadata=metadata,
        gabarito=yaml.safe_load(dev.GABARITO.read_text(encoding="utf-8")),
        comparacao=yaml.safe_load(dev.COMPARACAO.read_text(encoding="utf-8")),
        respostas=dev.ler_respostas(),
        sql={a.name: a.read_text(encoding="utf-8") for a in sorted(dev.PASTA_SQL.glob("D*.sql"))},
        registradas={i: p["pergunta"] for i, p in registradas.items()},
        sql_do_teste={a.name: a.read_text(encoding="utf-8") for a in sorted((RAIZ / PASTA_SQL).glob("Q*.sql"))},
        regra=yaml.safe_load((RAIZ / HIPOTESES).read_text(encoding="utf-8"))["comparacao"]["tolerancia"],
    )


# -----------------------------------------------------------------------------
# PT: 1. Perguntas / EN: questions
# -----------------------------------------------------------------------------

def checar_perguntas(d: Dados) -> list[str]:
    erros = []
    esperados = [f"D{n:02d}" for n in range(1, TOTAL + 1)]
    if list(d.por_id) != esperados or d.metadata.get("total") != TOTAL:
        erros.append(f"perguntas: os ids têm de ser D01 a D{TOTAL} e o total {TOTAL}")
    for id_, p in d.por_id.items():
        if not p.get("pergunta") or not p.get("question"):
            erros.append(f"{id_}: falta enunciado em português ou em inglês")
        if p.get("dependencia_semantica") not in DEPENDENCIAS:
            erros.append(f"{id_}: dependencia_semantica inválida")
        if p.get("tipo_de_acerto", "valor") not in TIPOS_DE_ACERTO:
            erros.append(f"{id_}: tipo_de_acerto inválido")
        if p.get("papel") not in dev.PAPEIS:
            erros.append(f"{id_}: papel inválido '{p.get('papel')}'")
        if not isinstance(p.get("modelos"), list):
            erros.append(f"{id_}: sem a lista de tabelas (modelos)")
    papeis = dev.por_papel(d.por_id)
    if {k: len(v) for k, v in papeis.items()} != COMPOSICAO:
        erros.append(f"composição: {{{', '.join(f'{k}: {len(v)}' for k, v in papeis.items())}}}, esperado {COMPOSICAO}")
    tipos_das_mistas = {t: sum(d.por_id[i].get("tipo_de_acerto", "valor") == t for i in papeis["mista"])
                        for t in MISTAS_POR_TIPO}
    if tipos_das_mistas != MISTAS_POR_TIPO:
        erros.append(f"composição: mistas por tipo {tipos_das_mistas}, esperado {MISTAS_POR_TIPO}")
    for id_ in papeis["controle_positivo"]:
        p, entrada = d.por_id[id_], d.comparacao["perguntas"].get(id_, {})
        blocos = [b for bs in entrada.values() if isinstance(bs, list) for b in bs]
        if (p.get("tipo_de_acerto", "valor") != "valor" or p["dependencia_semantica"] != "baixa"
                or len(entrada) != 1 or any("janelas" in b for b in blocos)):
            erros.append(f"{id_}: controle positivo tem de ser de valor, dependência baixa, uma leitura e sem janela")
    for id_ in papeis["controle_negativo"]:
        if d.por_id[id_].get("tipo_de_acerto") != "abstencao":
            erros.append(f"{id_}: controle negativo tem de ser de abstenção")
    return erros


# -----------------------------------------------------------------------------
# PT: 2. Sobreposição com o teste / EN: overlap with the test
# -----------------------------------------------------------------------------

def _palavras(texto: str) -> set[str]:
    return set(re.findall(r"\w+", texto.casefold()))


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def pares_do_sql(sql: str) -> set[tuple[str, str]]:
    """
    PT: Os pares de tokens consecutivos do SQL sem comentários, em
        minúsculas, com texto entre aspas, números e datas trocados por
        marcadores e apelidos de coluna fora. Dois SQL com a mesma estrutura
        e as mesmas colunas dão quase os mesmos pares.
    EN: Consecutive token pairs of the normalized SQL (no comments,
        lowercase, literals replaced, column aliases dropped).
    """
    texto = "\n".join(l.split("--", 1)[0] for l in sql.splitlines()).lower()
    texto = re.sub(r"'[^']*'", " lit ", texto)
    texto = re.sub(r"\b\d+(\.\d+)?\b", " num ", texto)
    texto = re.sub(r"\bas\s+\w+", " ", texto)
    tokens = re.findall(r"[a-z_]+|[(),*=<>+/-]", texto)
    return set(zip(tokens, tokens[1:]))


def checar_sobreposicao(d: Dados) -> tuple[list[str], dict]:
    erros, maximos = [], {}
    for id_, p in d.por_id.items():
        palavras = _palavras(p["pergunta"])
        rid, valor = max(((r, jaccard(palavras, _palavras(t))) for r, t in d.registradas.items()),
                         key=lambda par: par[1])
        maximos[id_] = {"enunciado": (rid, round(valor, 3))}
        if valor >= LIMITE_DO_ENUNCIADO:
            erros.append(f"{id_}: o enunciado repete a {rid} (Jaccard {valor:.2f})")
    # PT: o clone de SQL só se confere nas mistas. Um controle positivo é,
    #     de propósito, uma consulta de um passo, e se parece com qualquer
    #     soma do último mês do teste.
    # EN: SQL clones are checked on mixed questions only.
    teste = {nome: pares_do_sql(sql) for nome, sql in d.sql_do_teste.items()}
    papel_da_consulta = {c: d.por_id[i]["papel"] for i, e in d.gabarito["perguntas"].items() if i in d.por_id
                         for c in consultas_de(e)}
    for nome, sql in d.sql.items():
        if papel_da_consulta.get(nome) != "mista":
            continue
        pares = pares_do_sql(sql)
        rnome, valor = max(((t, jaccard(pares, ps)) for t, ps in teste.items()), key=lambda par: par[1])
        maximos.setdefault(Path(nome).stem, {})["sql"] = (rnome, round(valor, 3))
        if valor >= LIMITE_DO_SQL:
            erros.append(f"{nome}: o SQL repete o {rnome} (Jaccard de pares {valor:.2f})")
    return erros, maximos


def estrutura(sql: str) -> dict[str, bool]:
    """
    PT: Traços de estrutura de um SQL: junção, CTE e comparação no tempo
        (duas ou mais datas literais, um ano em lista, uma série de meses
        pela dim_tempo, LAG ou intervalo).
    EN: Structural traits of a SQL: join, CTE, time comparison.
    """
    texto = "\n".join(l.split("--", 1)[0] for l in sql.splitlines()).lower()
    datas = set(re.findall(r"date\s*'(\d{4}-\d{2}-\d{2})'", texto))
    return {
        "juncao": bool(re.search(r"\bjoin\b", texto)),
        "cte": texto.lstrip().startswith("with"),
        "comparacao_no_tempo": len(datas) >= 2 or bool(re.search(r"\bano\s+in\s*\(|\blag\s*\(|\binterval\b|"
                                                                 r"\bt\.mes\s*<=", texto)),
    }


def checar_estrutura(d: Dados) -> tuple[list[str], dict]:
    """
    PT: Os pisos de estrutura das mistas, com a proporção do teste ao lado.
    EN: Structural floors for mixed questions, next to the test's shares.
    """
    papel_da_consulta = {c: d.por_id[i]["papel"] for i, e in d.gabarito["perguntas"].items() if i in d.por_id
                         for c in consultas_de(e)}
    mistas = [estrutura(sql) for nome, sql in d.sql.items() if papel_da_consulta.get(nome) == "mista"]
    teste = [estrutura(sql) for sql in d.sql_do_teste.values()]
    contagem = {t: sum(e[t] for e in mistas) for t in PISOS_DAS_MISTAS}
    resumo = {t: f"{contagem[t]} de {len(mistas)} (teste: {sum(e[t] for e in teste)} de {len(teste)})"
              for t in PISOS_DAS_MISTAS}
    erros = [f"estrutura das mistas: {t} em {contagem[t]} SQL, o piso é {piso}"
             for t, piso in PISOS_DAS_MISTAS.items() if contagem[t] < piso]
    return erros, resumo


def checar_literais_dos_controles(d: Dados) -> list[str]:
    """
    PT: No SQL de controle positivo, os únicos literais são números (ano,
        trimestre) e siglas de UF. Data fixa e rótulo de categoria ficam de
        fora, porque a condição A não os vê.
    EN: Positive controls' SQL may only use numbers and state codes.
    """
    erros = []
    for id_ in dev.por_papel(d.por_id)["controle_positivo"]:
        for consulta in consultas_de(d.gabarito["perguntas"].get(id_, {})):
            texto = "\n".join(l.split("--", 1)[0] for l in d.sql.get(consulta, "").splitlines())
            if re.search(r"\bdate\s*'", texto, re.IGNORECASE):
                erros.append(f"{id_}: controle positivo com data fixa no SQL")
            for literal in re.findall(r"'([^']*)'", re.sub(r"\bdate\s*'[^']*'", "", texto, flags=re.IGNORECASE)):
                if not SIGLA_DE_UF.match(literal):
                    erros.append(f"{id_}: controle positivo com o rótulo '{literal}' no SQL")
    return erros


def checar_embeddings(d: Dados) -> list[str]:
    """
    PT: Cosseno dos embeddings do modelo do RAG entre cada enunciado e as 41.
        Precisa do grupo rag do uv; fica fora do CI.
    EN: RAG model embedding cosine against the 41; needs the rag group.
    """
    from rag.indice import embeddings_das_consultas, modelo_escolhido

    c = modelo_escolhido()
    ids = list(d.registradas)
    vetores_teste = embeddings_das_consultas(c, [d.registradas[i] for i in ids])
    vetores_dev = embeddings_das_consultas(c, [p["pergunta"] for p in d.por_id.values()])
    erros = []
    # PT: calibração: uma paráfrase real da Q01 tem de passar do limite, ou
    #     o limite não pega paráfrase nenhuma.
    # EN: calibration: a real paraphrase of Q01 must exceed the threshold.
    calibracao = float(embeddings_das_consultas(c, [PARAFRASE_DE_CALIBRACAO])[0] @ vetores_teste[ids.index("Q01")])
    print(f"  calibração: paráfrase da Q01 com cosseno {calibracao:.3f} (limite {LIMITE_DOS_EMBEDDINGS})")
    if calibracao <= LIMITE_DOS_EMBEDDINGS:
        erros.append(f"embeddings: a paráfrase de calibração deu {calibracao:.3f}, abaixo do limite; ajuste o limite")
    revisadas = d.metadata.get("revisadas_por_embeddings") or {}
    for id_, v in zip(d.por_id, vetores_dev):
        cossenos = vetores_teste @ v
        k = int(cossenos.argmax())
        marca = " (revisada)" if id_ in revisadas else ""
        print(f"  {id_}: mais próxima {ids[k]}, cosseno {cossenos[k]:.3f}{marca}")
        if cossenos[k] > LIMITE_DOS_EMBEDDINGS and id_ not in revisadas:
            erros.append(f"{id_}: cosseno {cossenos[k]:.3f} com a {ids[k]}, acima de {LIMITE_DOS_EMBEDDINGS}, "
                         "sem revisão registrada em metadata.revisadas_por_embeddings")
    return erros


# -----------------------------------------------------------------------------
# PT: 3 e 4. Gabarito, SQL, respostas e comparação / EN: key, SQL, answers
# -----------------------------------------------------------------------------

def consultas_de(entrada: dict) -> list[str]:
    return [c for l in entrada.get("leituras", []) for c in l["consultas"]]


def checar_gabarito(d: Dados) -> list[str]:
    erros = []
    entradas = d.gabarito["perguntas"]
    if set(entradas) != set(d.por_id):
        erros.append(f"gabarito: ids {sorted(set(entradas) ^ set(d.por_id))} sem par entre perguntas e gabarito")
    ontologia = ids_da_ontologia()
    esquema = json.loads(ESQUEMA_ESTRELA.read_text(encoding="utf-8"))
    banco = duckdb.connect()
    for tabela, colunas in esquema.items():
        banco.execute(f"create table {tabela} ({', '.join(f'{n} {tipo_no_duckdb(t)}' for n, t in colunas)})")
    usadas = set()
    for id_ in sorted(set(entradas) & set(d.por_id)):
        entrada = entradas[id_]
        erros += checar_entrada(id_, entrada, d.por_id[id_])
        erros += checar_fontes(id_, entrada.get("fonte", []), ontologia)
        for consulta in consultas_de(entrada):
            usadas.add(consulta)
            erros += checar_sql(id_, dev.PASTA_SQL / consulta, set(d.por_id[id_]["modelos"]))
            if consulta in d.sql:
                try:
                    banco.execute("explain " + d.sql[consulta])
                except duckdb.Error as erro:
                    erros.append(f"{consulta}: não roda no DuckDB: {str(erro).splitlines()[0]}")
    erros += [f"{c}: SQL sem pergunta no gabarito" for c in sorted(set(d.sql) - usadas)]
    return erros


def checar_respostas(d: Dados) -> list[str]:
    usadas = {c for e in d.gabarito["perguntas"].values() for c in consultas_de(e)}
    erros = [f"{c}: sem resposta gerada; rode scripts.gerar_gabarito_de_desenvolvimento"
             for c in sorted(usadas - set(d.respostas))]
    meses = {r["mes_de_referencia"] for r in d.respostas.values()}
    manifesto = json.loads((RAIZ / "esquema_estrela" / "manifesto.json").read_text(encoding="utf-8"))
    if meses != {manifesto["mes_de_referencia"]}:
        erros.append(f"respostas de {sorted(meses)}, retrato de {manifesto['mes_de_referencia']}")
    with contextlib.redirect_stdout(io_nulo()):
        erros += checar_comparacao(d.comparacao, d.gabarito, d.respostas, d.regra)
    return erros


def io_nulo():
    import io
    return io.StringIO()


# -----------------------------------------------------------------------------
# PT: 5. O corretor no próprio gabarito / EN: the grader on the key itself
# -----------------------------------------------------------------------------

def _registro(id_: str, valores: dict | None, ressalva: str = "", abstencao: str = "") -> dict:
    return {"candidato": "c", "id_pergunta": id_, "seed": 1, "erro": None,
            "resposta": {"interpretacao": "x", "sql": "", "ressalva": ressalva, "abstencao": abstencao,
                         "valores": valores or {"colunas": [], "linhas": []}}}


def _estragar(valores: dict) -> dict:
    """
    PT: Multiplica por 1,5 todo número e, com mais de uma linha, tira a
        primeira: some o primeiro item de um ranking ou de um conjunto.
    EN: Multiplies every number by 1.5 and, with several rows, drops the
        first one, so ranking and set items go missing too.
    """
    linhas = []
    for linha in valores["linhas"]:
        nova = []
        for v in linha:
            try:
                nova.append(str(Decimal(str(v)) * Decimal("1.5")))
            except Exception:
                nova.append(v)
        linhas.append(nova)
    return {"colunas": valores["colunas"], "linhas": linhas[1:] if len(linhas) > 1 else linhas}


def checar_corretor(d: Dados, g: Gabarito) -> list[str]:
    erros = []
    for id_, entrada in d.gabarito["perguntas"].items():
        tipo = entrada["tipo_de_acerto"]
        if tipo == "abstencao":
            saida = corrigir(id_, _registro(id_, None, abstencao="falta o dado"), g)
            if (saida["situacao"], saida["julgar"]) != ("pendente", ["abstencao"]):
                erros.append(f"{id_}: abstenção deu {saida['situacao']} {saida['julgar']}")
            continue
        consulta = consultas_de(entrada)[0]
        resposta = d.respostas.get(consulta)
        if resposta is None:
            continue
        valores = {"colunas": resposta["colunas"], "linhas": resposta["linhas"]}
        ressalva = "r" if tipo == "valor_com_ressalva" else ""
        saida = corrigir(id_, _registro(id_, valores, ressalva=ressalva), g)
        esperado = ("pendente", ["ressalva"]) if tipo == "valor_com_ressalva" else ("certo", [])
        if (saida["situacao"], saida["julgar"]) != esperado:
            erros.append(f"{id_}: o próprio gabarito deu {saida['situacao']} {saida['julgar']} {saida['motivo']}")
        estragada = corrigir(id_, _registro(id_, _estragar(valores), ressalva=ressalva), g)
        if estragada["situacao"] != "errado":
            erros.append(f"{id_}: a resposta estragada deu {estragada['situacao']}, devia dar errado")
        # PT: formas legítimas do mesmo dado têm de dar o mesmo resultado.
        # EN: legitimate forms of the same data must grade the same.
        for forma, outra in (("mês AAAA-MM", _mes_curto(valores)), ("mês por extenso", _mes_por_extenso(valores)),
                             ("UF pelo nome", _uf_pelo_nome(valores)),
                             ("coluna de posição na frente", _com_posicao(valores))):
            if outra is None:
                continue
            saida = corrigir(id_, _registro(id_, outra, ressalva=ressalva), g)
            if (saida["situacao"], saida["julgar"]) != esperado:
                erros.append(f"{id_}: com {forma}, a resposta certa deu {saida['situacao']} {saida['motivo']}")
        if trocado := _primeiro_item_trocado(id_, g, valores):
            if corrigir(id_, _registro(id_, trocado, ressalva=ressalva), g)["situacao"] != "errado":
                erros.append(f"{id_}: o ranking com o primeiro item trocado não deu errado")
    return erros


_MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
          "novembro", "dezembro"]
_DATA = re.compile(r"^(\d{4})-(\d{2})-\d{2}$")


def _trocar_celulas(valores: dict, troca) -> dict | None:
    linhas = [[troca(v) for v in linha] for linha in valores["linhas"]]
    return None if linhas == valores["linhas"] else {"colunas": valores["colunas"], "linhas": linhas}


def _mes_curto(valores: dict) -> dict | None:
    return _trocar_celulas(valores, lambda v: _DATA.sub(r"\1-\2", v) if isinstance(v, str) else v)


def _mes_por_extenso(valores: dict) -> dict | None:
    def troca(v):
        if isinstance(v, str) and (m := _DATA.match(v)):
            return f"{_MESES[int(m.group(2)) - 1]} de {m.group(1)}"
        return v
    return _trocar_celulas(valores, troca)


def _com_posicao(valores: dict) -> dict | None:
    """
    PT: Uma coluna de posição (1, 2, 3...) na frente: a posição não pode se
        passar pelo código do item (02 contra 2).
    EN: A leading position column must not pass for the item code.
    """
    if "posicao" in valores["colunas"] or len(valores["linhas"]) < 2:
        return None
    return {"colunas": ["posicao", *valores["colunas"]],
            "linhas": [[str(i + 1), *l] for i, l in enumerate(valores["linhas"])]}


def _uf_pelo_nome(valores: dict) -> dict | None:
    from correcao.corretor import UFS
    if "uf" not in valores["colunas"]:
        return None
    j = valores["colunas"].index("uf")
    linhas = [[UFS.get(v, v) if k == j else v for k, v in enumerate(l)] for l in valores["linhas"]]
    return {"colunas": valores["colunas"], "linhas": linhas}


def _primeiro_item_trocado(id_: str, g: Gabarito, valores: dict) -> dict | None:
    """
    PT: Num ranking, troca a chave do primeiro item pela de um item de fora
        do topo: tem de dar errado.
    EN: In a ranking, swaps the first item's key for one outside the top.
    """
    for blocos in g.comparacao[id_].values():
        for bloco in blocos:
            for item in bloco.get("verificar", []):
                if item.get("lista") == "ranking" and len(valores["linhas"]) > item["n"]:
                    j = valores["colunas"].index(item["chave"])
                    linhas = [list(l) for l in valores["linhas"]]
                    linhas[0][j] = linhas[item["n"]][j]
                    return {"colunas": valores["colunas"], "linhas": linhas[:item["n"]]}
    return None


# -----------------------------------------------------------------------------
# PT: Validação / EN: validation
# -----------------------------------------------------------------------------

def gabarito_de(d: Dados) -> Gabarito:
    return Gabarito(comparacao=d.comparacao["perguntas"], perguntas=d.gabarito["perguntas"],
                    respostas=d.respostas, regra=d.regra)


def validar(d: Dados) -> tuple[list[str], dict]:
    sobreposicao, maximos = checar_sobreposicao(d)
    estrutura_, resumo = checar_estrutura(d)
    maximos["_estrutura"] = resumo
    erros = checar_perguntas(d) + sobreposicao + estrutura_ + checar_literais_dos_controles(d) + checar_gabarito(d)
    respostas = checar_respostas(d)
    # PT: o corretor só roda sobre uma comparação íntegra; com coluna que não
    #     existe na resposta, ele nem chega a corrigir.
    # EN: the grader only runs on a sound comparison spec.
    erros += respostas or checar_corretor(d, gabarito_de(d))
    return erros, maximos


def autoteste(d: Dados) -> list[str]:
    """
    PT: Cada caso estraga uma peça e diz o trecho que a reprovação precisa
        trazer.
    EN: Each case breaks one piece and names the expected fragment.
    """
    if problemas := validar(d)[0]:
        return [f"a validação já falha antes do autoteste: {problemas[:3]}"]

    def parafrase():
        c = copy.deepcopy(d)
        c.por_id["D15"]["pergunta"] = d.registradas["Q05"]
        return c

    def clone_de_sql():
        c = copy.deepcopy(d)
        c.sql["D19.sql"] = d.sql_do_teste["Q05.sql"]
        return c

    def tabela_fora_da_lista():
        c = copy.deepcopy(d)
        c.por_id["D04"]["modelos"] = ["fct_pix"]
        return c

    def controle_com_janela():
        c = copy.deepcopy(d)
        bloco = c.comparacao["perguntas"]["D04"]["unica"][0]
        bloco["janelas"] = {"ultimo_mes": bloco.pop("verificar")}
        return c

    def resposta_adulterada():
        c = copy.deepcopy(d)
        c.respostas["D04.sql"]["colunas"] = ["outra_coluna"]
        return c

    def composicao_errada():
        c = copy.deepcopy(d)
        c.por_id["D01"]["papel"] = "mista"
        return c

    def controle_com_data_fixa():
        c = copy.deepcopy(d)
        c.sql["D04.sql"] = c.sql["D04.sql"].replace("(select max(data_base) from fct_carteira)", "date '2026-07-31'")
        return c

    def mistas_de_um_passo():
        c = copy.deepcopy(d)
        for nome in ("D19.sql", "D20.sql", "D21.sql", "D23.sql", "D25.sql"):
            c.sql[nome] = "select sum(carteira_ativa) as carteira_ativa from fct_carteira"
        return c

    negativos = [
        ("enunciado que repete uma pergunta do teste", parafrase, None, "o enunciado repete"),
        ("SQL clonado do teste", clone_de_sql, None, "o SQL repete"),
        ("SQL que lê tabela fora da lista", tabela_fora_da_lista, None, "não lista"),
        ("controle positivo com janela", controle_com_janela, None, "controle positivo"),
        ("resposta adulterada", resposta_adulterada, None, "não existe na resposta"),
        ("composição fora do registrado", composicao_errada, None, "composição"),
        ("controle positivo com data fixa", controle_com_data_fixa, None, "data fixa"),
        ("mistas de um passo só", mistas_de_um_passo, None, "estrutura das mistas"),
        ("corretor que aceita qualquer número", lambda: d, mock.patch(
            "correcao.corretor.dentro_da_banda", lambda classe, a, b: True), "estragada"),
    ]
    falhas = []
    for descricao, montar, remendo, trecho in negativos:
        with remendo or contextlib.nullcontext():
            problemas = validar(montar())[0]
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas[:3]}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")

    try:
        from scripts.gerar_gabarito_de_desenvolvimento import tipo_do_gabarito
        tipo_do_gabarito("INTERVAL")
        falhas.append("aprovou o estrago: tipo do DuckDB desconhecido")
    except SystemExit:
        print("  reprovado, como devia / rejected as expected: tipo do DuckDB desconhecido")

    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    parser.add_argument("--embeddings", action="store_true", help="cosseno dos embeddings (grupo rag)")
    args = parser.parse_args()

    d = ler()
    if args.autoteste:
        falhas = autoteste(d)
    else:
        falhas, maximos = validar(d)
        if args.embeddings:
            falhas += checar_embeddings(d)
        resumo = maximos.pop("_estrutura")
        maior_enunciado = max(m["enunciado"][1] for m in maximos.values() if "enunciado" in m)
        maior_sql = max((m["sql"][1] for m in maximos.values() if "sql" in m), default=0.0)
        print(f"  {len(d.por_id)} perguntas, {len(d.sql)} SQL, {len(d.respostas)} respostas; maior Jaccard com o "
              f"teste: enunciado {maior_enunciado:.2f} (limite {LIMITE_DO_ENUNCIADO}), SQL das mistas "
              f"{maior_sql:.2f} (limite {LIMITE_DO_SQL})")
        print(f"  estrutura das mistas: {resumo}")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
