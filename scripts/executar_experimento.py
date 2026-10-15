"""
PT: A execução do experimento 2x2 (#50, ADRs 0013, 0029 e 0031). Roda as 41
    perguntas do evaluation/questions_v3.yml nas quatro condições, com as 5
    seeds registradas, nos dois modelos do assistente/parametros.yml, pelo
    assistente.responder.

    Antes de rodar, para se faltar alguma coisa:

    - a errata que congela este executor, a contagem, a estatística, o
      corretor, o assistente, a busca do RAG e as conferências (decisões 4
      e 9 de 2026-10-14): nada roda contra o gabarito antes dela;
    - a temperatura e as seeds iguais às do pré-registro;
    - o retrato local do esquema estrela no mesmo mês das respostas do
      gabarito;
    - o índice local do RAG igual ao do rag/manifesto.json (sha256 dos
      trechos e dos embeddings do modelo escolhido);
    - o Ollama no ar, com as variáveis do cache KV do evaluation/selecao.yml,
      e o modelo puxado, com o digest do GGUF igual ao sha256 registrado.

    A ordem (decisão 5 de 2026-10-14): um modelo de cada vez. Dentro dele,
    pergunta por pergunta, na ordem do questions_v3.yml: a busca do RAG roda
    uma vez, e então as quatro condições, cada uma com as 5 seeds, na ordem
    sorteada para aquela pergunta e aquele modelo por um hash com a
    SEED_DA_ORDEM. Assim as condições se intercalam no tempo, e uma deriva da
    máquina não se alinha com nenhuma delas.

    Os trechos de cada pergunta ficam em data/experimento/trechos/, e C e D
    recebem os mesmos, nos dois modelos. Cada execução vai para
    data/experimento/execucoes/<modelo>/<condição>/<pergunta>_seed<n>.json,
    fora do git, e o comando retoma de onde parou.

    Erro de servidor (decisão 2 de 2026-10-14): o Ollama caiu ou respondeu
    fora do protocolo. A execução não é gravada, entra no
    data/experimento/repeticoes.json, e o comando para. Rodar de novo
    retoma pela mesma pergunta, seed e condição. Formato, tempo, SQL e
    contexto continuam contando como erro, como o registro manda.

    Com --ensaio, roda sem Ollama, sem dado, sem RAG e sem errata: duas
    perguntas, as quatro condições, a seed 1, o cliente falso e o banco
    vazio, em data/experimento/ensaio/. Com --ordem, só mostra a ordem.

EN: Runs the 41 registered questions in the four conditions, with the 5
    registered seeds, on both models, through assistente.responder. Refuses
    to run unless this runner, the statistics and the grader are frozen by
    errata, parameters match the pre-registration, the local snapshot and
    RAG index match what was registered, and Ollama runs with the KV cache
    settings and the registered GGUF. One model at a time; per question,
    one RAG search, then the four conditions (5 seeds each) in an order
    drawn per question and model by a hash. Server errors are not recorded:
    they are logged and the run stops, to be resumed. --ensaio runs offline;
    --ordem prints the order.

    Para a emenda do instrumento (#118, ADR 0032), roda também o conjunto de
    desenvolvimento (--perguntas desenvolvimento), com uma variação do
    instrumento (--variacao, assistente/variacoes.py) e qualquer candidato
    da seleção (--candidato). Fora da V−1 e dos modelos registrados, o
    num_ctx de cada variação e candidato vem de
    evaluation/desenvolvimento/dimensionamento.json. A VRAM entra no
    ambiente, e a versão do Ollama é conferida. Sem --pasta, o
    desenvolvimento grava em data/desenvolvimento/<variação>/, com os
    trechos em data/desenvolvimento/trechos/.

Uso / Usage:
    uv run --group rag python -m scripts.executar_experimento --perguntas teste --modelo gemma-4-12b
    uv run --group rag python -m scripts.executar_experimento --perguntas teste --modelo qwen3.5-9b
    uv run python -m scripts.executar_experimento --perguntas teste --ensaio
    uv run python -m scripts.executar_experimento --perguntas teste --ordem
    uv run --group rag python -m scripts.executar_experimento --perguntas desenvolvimento --variacao V0 --candidato gemma-4-12b
    uv run python -m scripts.executar_experimento --ensaio --perguntas desenvolvimento --variacao V3
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import shutil
import time
from pathlib import Path

import duckdb
import numpy as np
import yaml

from assistente import parametros, variacoes
from assistente.cliente import ClienteFalso, ClienteOllama
from experimento import desenvolvimento, hipoteses_por_variacao
from assistente.parametros import CONDICOES, PARAMETROS, Parametros
from assistente.responder import responder
from assistente.sql import abrir_banco, banco_vazio
from correcao.acerto import PASTA_DO_EXPERIMENTO
from scripts.selecionar_modelos import (
    _get,
    carregar_e_medir_vram,
    carregar_selecao,
    conferir_candidato,
    descarregar_todos,
    conferir_congelamento,
    conferir_retrato,
    conferir_variaveis,
    gravar_json,
    parametros_do_candidato,
    respostas_de_ensaio,
)
from scripts.esquema_estrela_duckdb import LOCAL, carregar_manifesto, esquema_esperado
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import REGISTRO, RAIZ, hashes_vigentes
from scripts.validar_registro import sha256 as sha256_do_registro

# PT: o que a errata congela antes da primeira execução (decisão 4 de
#     2026-10-14): o executor, a contagem, a estatística e o corretor; e,
#     pela decisão 9 do mesmo dia, todo o código que muda o que o modelo vê
#     (o assistente e a busca do RAG) ou se as conferências rodam.
# EN: what the errata freezes before the first run: runner, counting,
#     statistics and grader, plus every module that shapes what the model
#     sees (assistant, RAG search) or runs the pre-run checks.
CONGELADOS_ANTES_DO_EXPERIMENTO = (
    "scripts/executar_experimento.py",
    "experimento/__init__.py",
    "experimento/contagem.py",
    "experimento/estatistica.py",
    "correcao/__init__.py",
    "correcao/acerto.py",
    "correcao/as_cegas.py",
    "correcao/corretor.py",
    "correcao/tolerancia.py",
    "assistente/__init__.py",
    "assistente/cliente.py",
    "assistente/contexto.py",
    "assistente/ontologia.py",
    "assistente/parametros.py",
    "assistente/responder.py",
    "assistente/sql.py",
    "rag/indice.py",
    "scripts/selecionar_modelos.py",
    "scripts/validar_registro.py",
    # PT: a emenda do instrumento (#118, ADR 0032, errata 5): só o núcleo,
    #     o que muda o resultado. As variações, o conjunto de
    #     desenvolvimento, o portão, o medir_portao, o retrato e tudo o que
    #     forma o prompt. Os validadores e os scripts que geram ou
    #     dimensionam ficam fora (decisão de 2026-10-15): o CI os confere, e
    #     consertá-los não muda o que o modelo vê nem como a resposta conta.
    # EN: the amendment freezes only the core, what changes the result;
    #     validators and generating or sizing scripts stay out.
    "assistente/variacoes.py",
    "assistente/variacoes.yml",
    "experimento/desenvolvimento.py",
    "evaluation/portao.yml",
    "evaluation/hipoteses_por_variacao.yml",
    "experimento/hipoteses_por_variacao.py",
    "esquema_estrela/views.sql",
    "esquema_estrela/manifesto.json",
    "evaluation/desenvolvimento/perguntas.yml",
    "evaluation/desenvolvimento/gabarito.yml",
    "evaluation/desenvolvimento/comparacao.yml",
    "evaluation/desenvolvimento/dimensionamento.json",
    *sorted(a.relative_to(RAIZ).as_posix() for a in (RAIZ / "evaluation" / "desenvolvimento").glob("sql/D*.sql")),
    *sorted(a.relative_to(RAIZ).as_posix() for a in (RAIZ / "evaluation" / "desenvolvimento").glob("respostas/D*.json")),
    "scripts/medir_portao.py",
    "evaluation/gabarito/esquema_estrela.json",
    *sorted(a.relative_to(RAIZ).as_posix() for a in (RAIZ / "ontology").glob("*.yml")),
    "scripts/esquema_estrela_duckdb.py",
    "scripts/validar_gabarito.py",
    "scripts/analises/qa_esquema_estrela.py",
    "rag/parametros.py",
    "assistente/modelo_de_prompt.yml",
    "assistente/parametros.yml",
    "evaluation/selecao.yml",
    "scripts/validar_perguntas.py",
    "evaluation/experimento/execucao-1/limite_declarado.txt",
)
# PT: o Ollama com que a execução 1 rodou; outra versão pode mudar a
#     gramática e a geração (ADR 0032).
# EN: the Ollama version run 1 used.
VERSAO_DO_OLLAMA = "0.40.4"
PASTA_DO_DESENVOLVIMENTO = RAIZ / "data" / "desenvolvimento"
# PT: a execução 1 roda na V−1, em data/experimento; a execução 2, na
#     variação registrada no parametros.yml pela errata 6, numa pasta própria.
# EN: run 1 (V−1) lives in data/experimento; run 2 in its own folder.
PASTA_DA_EXECUCAO_2 = PASTA_DO_EXPERIMENTO / "execucao-2"
# PT: o resultado da triagem, gravado pelo medir_portao; a execução 2 só roda
#     com a variação e os modelos que ele escolheu.
# EN: the screening result; run 2 only runs what it chose.
TRIAGEM = RAIZ / "evaluation" / "desenvolvimento" / "triagem.json"
DIMENSIONAMENTO = RAIZ / "evaluation" / "desenvolvimento" / "dimensionamento.json"
# PT: a seed do sorteio da ordem das condições, registrada com o código.
# EN: seed of the condition order draw, frozen with the code.
SEED_DA_ORDEM = 50
REPETICOES = "repeticoes.json"


class ParadaPorServidor(Exception):
    """PT: o Ollama falhou; a execução não foi gravada / EN: server failure"""


# -----------------------------------------------------------------------------
# PT: Os modelos / EN: the models
# -----------------------------------------------------------------------------

def modelos_do_experimento(arquivo: Path = PARAMETROS) -> list[dict]:
    """
    PT: Os dois modelos do assistente/parametros.yml, com o nome curto da
        seleção (evaluation/selecao.yml), que nomeia as pastas.
    EN: Both models from parametros.yml, with the selection's short name.
    """
    curtos = {c["ollama"]: c["nome"] for c in carregar_selecao()["candidatos"]}
    modelos = yaml.safe_load(arquivo.read_text(encoding="utf-8"))["modelos"]
    return [{"nome": curtos[m["nome"]], "ollama": m["nome"], "classe": m["classe"], "sha256": m["sha256"],
             "repositorio": m["repositorio"], "revisao": m["revisao"]} for m in modelos]


def candidatos_da_selecao() -> list[dict]:
    """
    PT: Os candidatos do evaluation/selecao.yml, no formato de
        modelos_do_experimento, para a triagem e a re-seleção.
    EN: The selection candidates, in modelos_do_experimento's shape.
    """
    return [{"nome": c["nome"], "ollama": c["ollama"], "classe": c["classe"], "sha256": c["sha256"],
             "repositorio": c["repositorio"], "revisao": c["revisao"], "candidato": c}
            for c in carregar_selecao()["candidatos"]]


def variacao_registrada(arquivo: Path = PARAMETROS) -> str:
    """PT: a variação do parametros.yml, ou V−1 / EN: the registered variant"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8")).get("variacao", "V-1")


def parametros_da_execucao(m: dict, variacao: str, registrados: set[str]) -> Parametros:
    """
    PT: Os parâmetros de um modelo numa variação. Um modelo registrado na V−1
        usa o parametros.yml; fora disso, o num_ctx e a razão vêm do
        dimensionamento da variação.
    EN: A model's parameters in a variant: parametros.yml for a registered
        model in V−1, else num_ctx and ratio from the variant's sizing.
    """
    if m["nome"] in registrados:
        p = parametros.carregar(modelo=m["ollama"])
    else:
        p = parametros_do_candidato(parametros.carregar(), carregar_selecao(), m["candidato"])
    if variacao == "V-1" and m["nome"] in registrados:
        return p
    medidas = json.loads(DIMENSIONAMENTO.read_text(encoding="utf-8")) if DIMENSIONAMENTO.exists() else {}
    medida = medidas.get("variacoes", {}).get(variacao, {}).get(m["nome"])
    if medida is None:
        raise SystemExit(f"ERRO sem dimensionamento de {m['nome']} na {variacao}: rode "
                         "uv run --group rag python -m scripts.dimensionar_variacoes")
    # PT: o modelo registrado na variação registrada (depois da errata 6) usa
    #     o parametros.yml, que tem de bater com o dimensionamento.
    # EN: after errata 6, parametros.yml must match the sizing.
    if m["nome"] in registrados and variacao == variacao_registrada() and p.num_ctx != int(medida["num_ctx"]):
        raise SystemExit(f"ERRO num_ctx de {m['nome']}: {p.num_ctx} no parametros.yml e {medida['num_ctx']} no "
                         "dimensionamento da variação; as duas fontes têm de bater")
    return dataclasses.replace(p, num_ctx=int(medida["num_ctx"]),
                               caracteres_por_token_na_estimativa=float(medida["caracteres_por_token"]))


# -----------------------------------------------------------------------------
# PT: Conferências antes de rodar / EN: pre-run checks
# -----------------------------------------------------------------------------

def conferir_teste(args, variacao: str) -> None:
    """
    PT: No conjunto de teste, só roda a variação registrada no parametros.yml,
        com os modelos registrados: candidato e variação de triagem ficam no
        conjunto de desenvolvimento.
    EN: On the test set only the registered variant and models may run.
    """
    if args.candidato:
        raise SystemExit("ERRO --candidato só vale com --perguntas desenvolvimento")
    if variacao != variacao_registrada():
        raise SystemExit(f"ERRO a {variacao} não é a variação registrada ({variacao_registrada()}): no teste só roda "
                         "a variação que a errata registrou no parametros.yml")
    if args.pasta:
        raise SystemExit("ERRO --pasta não vale no teste: cada execução tem a sua pasta fixa")
    if variacao == "V-1":
        return
    # PT: a execução 2 só roda o que a triagem escolheu, e só quando ela
    #     terminou em escolha (nem pendente, nem sanidade, nem parada).
    # EN: run 2 only runs what the finished screening chose.
    if not TRIAGEM.exists():
        raise SystemExit(f"ERRO falta {TRIAGEM.relative_to(RAIZ).as_posix()}: rode scripts.medir_portao --resumo --gravar")
    triagem = json.loads(TRIAGEM.read_text(encoding="utf-8"))
    if triagem.get("situacao") != "escolhida":
        raise SystemExit(f"ERRO a triagem terminou em {triagem.get('situacao')}: a execução 2 não roda")
    if triagem.get("variacao_escolhida") != variacao:
        raise SystemExit(f"ERRO a triagem escolheu a {triagem.get('variacao_escolhida')}, e o parametros.yml registra "
                         f"a {variacao}")
    escolhidos = sorted(m["modelo"] for m in triagem.get("modelos", {}).values())
    registrados = sorted(m["nome"] for m in modelos_do_experimento())
    if escolhidos != registrados:
        raise SystemExit(f"ERRO a triagem escolheu {escolhidos}, e o parametros.yml registra {registrados}")
    # PT: a errata 6 inteira: o triagem.json e o hipoteses.yml congelados
    #     como estão, e o hipoteses.yml com os valores prontos da variação.
    # EN: the whole errata 6: triage and hipoteses frozen as they are, and
    #     hipoteses holding the variant's prepared values.
    vigentes = hashes_vigentes(carregar_registro())
    for arquivo in (TRIAGEM, RAIZ / "evaluation" / "hipoteses.yml"):
        caminho = arquivo.relative_to(RAIZ).as_posix()
        if vigentes.get(caminho) != sha256_do_registro(arquivo.read_text(encoding="utf-8")):
            raise SystemExit(f"ERRO {caminho} sem errata vigente: a errata 6 congela o que a execução 2 usa")
    if problemas := hipoteses_por_variacao.conferir(registrada=variacao):
        raise SystemExit(f"ERRO {problemas[0]}")


def assinatura_dos_enunciados(por_id: dict[str, dict]) -> str:
    """
    PT: O sha256 dos ids e enunciados: uma revisão do conjunto que mantém o
        id e muda o texto muda a assinatura.
    EN: sha256 of ids and question texts.
    """
    texto = json.dumps({i: p["pergunta"] for i, p in por_id.items()}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def conferir_pasta(pasta: Path, modelo: str, variacao: str, p: Parametros, perguntas_: str = "teste",
                   assinatura: str | None = None) -> None:
    """
    PT: Uma pasta que já tem execuções de outra variação, de outro conjunto
        de perguntas, de outros enunciados ou com outros parâmetros não
        recebe execuções novas. O ambiente sem variação conta como V−1, e
        sem conjunto, como o teste (é o da execução 1).
    EN: A folder holding runs of another variant, question set, question
        texts or parameters is refused.
    """
    arquivo = pasta / "execucoes" / modelo / "ambiente.json"
    if not arquivo.exists():
        return
    ambiente = json.loads(arquivo.read_text(encoding="utf-8"))
    if (ambiente.get("variacao") or "V-1") != variacao:
        raise SystemExit(f"ERRO {arquivo} é da {ambiente.get('variacao') or 'V-1'}, não da {variacao}")
    if (ambiente.get("perguntas") or "teste") != perguntas_:
        raise SystemExit(f"ERRO {arquivo} é do conjunto {ambiente.get('perguntas') or 'teste'}, não do {perguntas_}")
    if assinatura and ambiente.get("enunciados") and ambiente["enunciados"] != assinatura:
        raise SystemExit(f"ERRO {arquivo} foi gravado com outros enunciados: depois de revisar o conjunto, rode numa "
                         "pasta nova (--pasta)")
    anteriores = ambiente.get("parametros") or {}
    # PT: compara na forma do JSON gravado (tupla vira lista).
    # EN: compare in the stored JSON form (tuples become lists).
    atuais = json.loads(json.dumps(dataclasses.asdict(p)))
    diferentes = [k for k, v in atuais.items() if k in anteriores and anteriores[k] != v]
    if diferentes:
        raise SystemExit(f"ERRO {arquivo} foi gravado com outros parâmetros: {diferentes}")


def faltam_execucoes(modelo: dict, p: Parametros, por_id: dict[str, dict], pasta: Path) -> int:
    """PT: quantas execuções ainda não estão gravadas / EN: runs still missing"""
    return sum(not arquivo_da_execucao(pasta, modelo["nome"], c, id_, s).exists()
               for id_ in por_id for c in CONDICOES for s in p.seeds)


def descarregar_e_esperar(endereco: str, limite: float = 60.0) -> None:
    """
    PT: Tira os modelos da memória e espera o /api/ps ficar vazio. O executor
        chama antes de cada execução (decisão de 2026-10-15, #118): na
        fumaça, o Gemma só repetiu a resposta com a mesma seed partindo do
        modelo recém-carregado, e qualquer chamada anterior mudava a saída.
    EN: Unloads all models and waits until /api/ps is empty; called before
        every run, since Gemma only reproduced from a fresh load.
    """
    descarregar_todos(endereco)
    fim = time.monotonic() + limite
    while _get(endereco, "/api/ps").get("models"):
        if time.monotonic() > fim:
            raise SystemExit(f"ERRO o Ollama não descarregou o modelo em {limite:g} s")
        time.sleep(0.2)


def conferir_retrato_local() -> None:
    """
    PT: Os Parquets de data/esquema_estrela/ são os do manifesto congelado
        (sha256 de cada um), e as respostas do conjunto de desenvolvimento
        são do mesmo mês do retrato. Um retrato regerado num mês novo, sem
        errata, para tudo.
    EN: Local Parquets match the frozen manifest, and development answers
        are from the snapshot's month.
    """
    manifesto = carregar_manifesto()
    for tabela, dados in sorted(manifesto.get("tabelas", {}).items()):
        arquivo = LOCAL / dados["arquivo"]
        if not arquivo.exists() or hashlib.sha256(arquivo.read_bytes()).hexdigest() != dados["sha256"]:
            raise SystemExit(f"ERRO {arquivo} não é o do esquema_estrela/manifesto.json ({tabela}): o retrato "
                             "local mudou sem errata")
    meses = {r["mes_de_referencia"] for r in desenvolvimento.ler_respostas().values()}
    if meses != {manifesto.get("mes_de_referencia")}:
        raise SystemExit(f"ERRO respostas do desenvolvimento de {sorted(meses)} e retrato de "
                         f"{manifesto.get('mes_de_referencia')}")


def carregar_registro() -> dict:
    """PT: o evaluation/registro.yml / EN: the registry"""
    return yaml.safe_load((RAIZ / REGISTRO).read_text(encoding="utf-8"))


def conferir_congelado() -> None:
    """
    PT: Tudo o que a errata 5 congela, antes de rodar ou de decidir: os
        hashes da lista, o retrato local e os arquivos lidos por glob. O
        executor e o medir_portao chamam esta mesma função.
    EN: Everything errata 5 freezes; shared by the runner and the gate.
    """
    conferir_congelamento(CONGELADOS_ANTES_DO_EXPERIMENTO)
    conferir_retrato_local()
    if sumiram := conferir_globs(carregar_registro()):
        raise SystemExit(f"ERRO arquivos congelados que sumiram: {sumiram}")


PASTAS_POR_GLOB = ("evaluation/desenvolvimento/sql/", "evaluation/desenvolvimento/respostas/", "ontology/")


def conferir_globs(registro: dict, congelados: tuple[str, ...] = CONGELADOS_ANTES_DO_EXPERIMENTO) -> list[str]:
    """
    PT: Nas pastas que a lista lê por glob, um arquivo congelado que sumiu
        não entra no glob e passaria sem aviso. Ele aparece aqui: está no
        registro e não está na lista. Tirar um arquivo pede errata com
        sha256 nulo.
    EN: In globbed folders, a frozen file that disappeared would pass
        silently; it shows up here as registered but not listed.
    """
    vigentes = hashes_vigentes(registro)
    return sorted(c for c in vigentes if c.startswith(PASTAS_POR_GLOB) and c not in congelados)


def conferir_versao_do_ollama(endereco: str) -> str:
    versao = _get(endereco, "/api/version").get("version")
    if versao != VERSAO_DO_OLLAMA:
        raise SystemExit(f"ERRO Ollama {versao}, registrado {VERSAO_DO_OLLAMA}: instale a versão registrada")
    return versao


def conferir_indice() -> dict[str, str]:
    """
    PT: O índice local do RAG (trechos e embeddings do modelo escolhido)
        tem de ser o do rag/manifesto.json. Devolve a assinatura do índice
        (modelo e os dois sha256), que vai em cada arquivo de trechos.
        Precisa do grupo rag do uv.
    EN: The local RAG index must match rag/manifesto.json; returns the
        index signature stored with every excerpts file.
    """
    try:
        from rag.construir import sha256_do_conteudo
        from rag.indice import carregar_indice, modelo_escolhido
        from rag.parametros import MANIFESTO_RAG
    except ModuleNotFoundError as erro:
        raise SystemExit(f"ERRO falta o grupo rag do uv ({erro.name}): rode com "
                         "uv run --group rag python -m scripts.executar_experimento") from None

    escolhido = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8"))["escolhido"]
    trechos, vetores = carregar_indice(modelo_escolhido())
    medidos = {"sha256_trechos": sha256_do_conteudo(trechos),
               "sha256_embeddings": hashlib.sha256(np.ascontiguousarray(vetores).tobytes()).hexdigest()}
    if divergentes := [k for k, v in medidos.items() if v != escolhido[k]]:
        raise SystemExit(f"ERRO índice do RAG diverge do rag/manifesto.json em {divergentes}: "
                         "rode uv run --group rag python -m rag.construir")
    return {"modelo": escolhido["nome"], **medidos}


# -----------------------------------------------------------------------------
# PT: Ordem, trechos e gravação / EN: order, excerpts and writing
# -----------------------------------------------------------------------------

def ordem_das_condicoes(modelo: str, pergunta: str) -> list[str]:
    """
    PT: As quatro condições na ordem sorteada para a pergunta e o modelo:
        ordenadas por sha256 de "ordem|SEED_DA_ORDEM|modelo|pergunta|condição".
        É determinística e não depende da ordem em que o código roda.
    EN: The four conditions in the order drawn for this question and model,
        sorted by a sha256; deterministic.
    """
    def chave(condicao: str) -> str:
        return hashlib.sha256(f"ordem|{SEED_DA_ORDEM}|{modelo}|{pergunta}|{condicao}".encode("utf-8")).hexdigest()
    return sorted(CONDICOES, key=chave)


def arquivo_da_execucao(pasta: Path, modelo: str, condicao: str, pergunta: str, seed: int) -> Path:
    return pasta / "execucoes" / modelo / condicao / f"{pergunta}_seed{seed}.json"


def trechos_da_pergunta(pasta: Path, id_: str, pergunta: str, buscar, indice: dict[str, str]) -> list[dict]:
    """
    PT: Os trechos da pergunta, buscados uma vez e gravados com a assinatura
        do índice; dali em diante, lidos do arquivo, para C e D e para os
        dois modelos receberem os mesmos. Um arquivo gravado com outro
        índice, ou com outro enunciado, para tudo: misturar dois índices na
        mesma execução não pode passar em silêncio.
    EN: The question's excerpts, searched once and stored with the index
        signature, then read back so C, D and both models get the same ones.
        A file from another index or question text stops the run.
    """
    arquivo = pasta / "trechos" / f"{id_}.json"
    if arquivo.exists():
        gravado = json.loads(arquivo.read_text(encoding="utf-8"))
        if gravado.get("indice") != indice or gravado.get("pergunta") != pergunta:
            raise SystemExit(f"ERRO {arquivo} veio de outro índice ou de outro enunciado ({gravado.get('indice')}, "
                             f"agora {indice}): as execuções já gravadas usaram esses trechos")
        return gravado["trechos"]
    trechos = buscar(pergunta)
    gravar_json(arquivo, {"id_pergunta": id_, "pergunta": pergunta, "indice": indice, "trechos": trechos})
    return trechos


def registrar_repeticao(pasta: Path, registro: dict) -> None:
    """PT: anota um erro de servidor / EN: logs a server error"""
    arquivo = pasta / REPETICOES
    lista = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else []
    lista.append({k: registro[k] for k in ("candidato", "condicao", "id_pergunta", "seed", "inicio")}
                 | {"mensagem": registro["erro"]["mensagem"]})
    gravar_json(arquivo, lista)


def rodar_modelo(modelo: dict, p: Parametros, por_id: dict[str, dict], pasta: Path, *,
                 cliente_para, banco, modelo_de_prompt: dict, buscar, indice: dict[str, str],
                 variacao: str = "V-1", pasta_dos_trechos: Path | None = None, cego: bool = False,
                 antes_de_cada=None) -> int:
    """
    PT: As perguntas de um modelo, na ordem registrada, pulando as execuções
        já gravadas. Devolve quantas rodaram agora. Um erro de servidor é
        anotado e para tudo, sem gravar a execução.
        Com cego (a triagem), o progresso sai só como contagem, sem a
        condição, o desfecho nem o tempo de cada execução: fora o G0, nada
        aparece por condição durante a triagem.
        antes_de_cada roda antes de cada execução (o executor recarrega o
        modelo, para a execução partir sempre do mesmo estado).
    EN: One model's questions in the registered order, skipping recorded
        runs. A server error is logged and stops the run unrecorded. With
        cego, progress shows neither condition nor outcome.
    """
    rodadas = 0
    total = len(por_id) * len(CONDICOES) * len(p.seeds)
    ja_feitas = total - faltam_execucoes(modelo, p, por_id, pasta)
    for id_, pergunta in por_id.items():
        ordem = ordem_das_condicoes(modelo["nome"], id_)
        faltam = [(c, s) for c in ordem for s in p.seeds
                  if not arquivo_da_execucao(pasta, modelo["nome"], c, id_, s).exists()]
        if not faltam:
            continue
        trechos = trechos_da_pergunta(pasta_dos_trechos or pasta, id_, pergunta["pergunta"], buscar, indice)
        for condicao, seed in faltam:
            if antes_de_cada:
                antes_de_cada()
            registro = responder(pergunta["pergunta"], condicao, seed, cliente=cliente_para(id_, seed), banco=banco,
                                 p=p, modelo=modelo_de_prompt,
                                 trechos=trechos if "trechos" in CONDICOES[condicao] else None,
                                 variacao=variacao)
            registro = {"candidato": modelo["nome"], "id_pergunta": id_, **registro}
            if registro["erro"] and registro["erro"]["tipo"] == "servidor":
                registrar_repeticao(pasta, registro)
                raise ParadaPorServidor(f"{modelo['nome']} {condicao} {id_} seed {seed}: "
                                        f"{registro['erro']['mensagem']}")
            gravar_json(arquivo_da_execucao(pasta, modelo["nome"], condicao, id_, seed), registro)
            rodadas += 1
            if cego:
                # PT: sem o tempo: a abstenção é mais rápida e o denunciaria.
                # EN: no timing, since abstentions are faster and would show.
                print(f"  {modelo['nome']}: {ja_feitas + rodadas} de {total}", flush=True)
                continue
            situacao = f"erro {registro['erro']['tipo']}" if registro["erro"] else \
                ("abstenção" if registro["resposta"]["abstencao"] else "respondeu")
            print(f"  {modelo['nome']} {id_} {condicao} seed {seed}: {situacao}, {registro['segundos']} s",
                  flush=True)
    return rodadas


# -----------------------------------------------------------------------------
# PT: Ensaio / EN: dry run
# -----------------------------------------------------------------------------

TRECHOS_DE_ENSAIO = [{"trecho": 1, "documento": "ensaio", "titulo": None, "secao": None, "pagina": None,
                      "texto": "trecho de ensaio, sem RAG", "similaridade": 1.0}]
INDICE_DE_ENSAIO = {"modelo": "ensaio", "sha256_trechos": "ensaio", "sha256_embeddings": "ensaio"}


def respostas_de_ensaio_da_variacao(variacao: str, id_: str) -> list[str]:
    """
    PT: As respostas de ensaio no formato de uma variação (chaves com
        prefixo): uma abstenção e um SQL que roda no banco vazio. Na V3 e na
        V4, o SQL vem primeiro com uma coluna que não existe, para o ensaio
        passar pela nova tentativa.
    EN: Dry-run answers in a variant's prefixed format; in V3/V4 a failing
        SQL comes first so the dry run exercises the retry.
    """
    if variacao == "V-1":
        return respostas_de_ensaio(id_)
    v = variacoes.VARIACOES[variacao]
    primeira, segunda = variacoes.campos_da_primeira(v), variacoes.campos_da_segunda(v)
    tabela = next(iter(esquema_esperado()))

    def json_de(campos: list[str], valores: dict) -> str:
        return json.dumps(dict(zip(variacoes.prefixadas(campos), (valores[c] for c in campos))), ensure_ascii=False)

    if id_.endswith("1"):
        return [json_de(primeira, {"interpretacao": "ensaio", "plano": "", "sql": "", "abstem": True,
                                   "motivo": "ensaio sem modelo"})]
    falha = [json_de(primeira, {"interpretacao": "ensaio", "plano": "coluna errada",
                                "sql": f"select coluna_que_nao_existe from {tabela}", "abstem": False,
                                "motivo": ""})] if v.nova_tentativa else []
    return [*falha,
            json_de(primeira, {"interpretacao": "ensaio", "plano": "contar linhas",
                               "sql": f"select count(*) as linhas from {tabela}", "abstem": False, "motivo": ""}),
            json_de(segunda, {"interpretacao": "ensaio", "valores": {"colunas": ["linhas"], "linhas": [[0]]},
                              "ressalva": "", "abstem": False, "motivo": ""})]


def ensaio(por_id: dict[str, dict], pasta: Path = PASTA_DO_EXPERIMENTO / "ensaio", variacao: str = "V-1") -> Path:
    """
    PT: O executor sem modelo, sem dado e sem RAG, numa pasta zerada antes.
        O ensaio nunca grava ambiente.json; uma pasta que tem um, em
        qualquer nível, guarda execução de verdade, e o ensaio se recusa a
        apagá-la.
    EN: Offline dry run in a folder emptied first; a folder holding an
        ambiente.json holds real runs and is never deleted.
    """
    if pasta.exists() and any(pasta.rglob("ambiente.json")):
        raise SystemExit(f"ERRO {pasta} tem execuções de verdade em algum nível; o ensaio não apaga essa pasta")
    shutil.rmtree(pasta, ignore_errors=True)
    modelo = modelos_do_experimento()[0]
    p = dataclasses.replace(parametros.carregar(modelo=modelo["ollama"]), seeds=(1,))
    duas = dict(list(por_id.items())[:2])
    recargas = []
    rodadas = rodar_modelo(modelo, p, duas, pasta,
                           cliente_para=lambda id_, seed: ClienteFalso(respostas_de_ensaio_da_variacao(variacao, id_)),
                           banco=banco_vazio(), modelo_de_prompt=parametros.modelo_de_prompt(),
                           buscar=lambda pergunta: TRECHOS_DE_ENSAIO, indice=INDICE_DE_ENSAIO, variacao=variacao,
                           antes_de_cada=lambda: recargas.append(1))
    if len(recargas) != rodadas:
        raise SystemExit(f"ERRO o ensaio recarregou {len(recargas)} vezes em {rodadas} execuções")
    if variacao != "V-1" and variacoes.VARIACOES[variacao].nova_tentativa:
        # PT: a pergunta com SQL tem de ter passado pela nova tentativa.
        # EN: the SQL question must have gone through the retry.
        id_ = list(duas)[1]
        for c in CONDICOES:
            registro = json.loads(arquivo_da_execucao(pasta, modelo["nome"], c, id_, 1).read_text(encoding="utf-8"))
            if registro.get("novas_tentativas") != 1 or registro.get("erro"):
                raise SystemExit(f"ERRO o ensaio da {variacao} não passou pela nova tentativa em {id_} {c}")
        print(f"Nova tentativa exercida em {id_} nas quatro condições / retry exercised.")
    return pasta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", action="append", help="só estes modelos registrados, pelo nome curto (repetível)")
    parser.add_argument("--candidato", action="append", help="candidatos da seleção, pelo nome (repetível)")
    parser.add_argument("--perguntas", choices=["teste", "desenvolvimento"], required=True)
    parser.add_argument("--variacao", choices=variacoes.ORDEM, help="sem ela, a do parametros.yml (ou V-1)")
    parser.add_argument("--pasta", type=Path, help="pasta de saída")
    parser.add_argument("--ensaio", action="store_true", help="sem Ollama, sem dado, sem RAG e sem errata")
    parser.add_argument("--ordem", action="store_true", help="só mostra a ordem das condições")
    args = parser.parse_args()

    variacao = args.variacao or variacao_registrada()
    teste = args.perguntas == "teste"
    meta, por_id = perguntas(VIGENTE) if teste else desenvolvimento.perguntas()
    registrados = {m["nome"] for m in modelos_do_experimento()}
    if args.candidato:
        todos = {m["nome"]: m for m in candidatos_da_selecao()}
        if desconhecidos := [n for n in args.candidato if n not in todos]:
            raise SystemExit(f"ERRO candidato desconhecido {desconhecidos}: {sorted(todos)}")
        modelos = [todos[n] for n in args.candidato]
    else:
        modelos = [m for m in modelos_do_experimento() if not args.modelo or m["nome"] in args.modelo]
        if args.modelo and len(modelos) != len(set(args.modelo)):
            raise SystemExit(f"ERRO modelo desconhecido em {args.modelo}: {sorted(registrados)}")

    if teste and not args.ensaio and not args.ordem:
        conferir_teste(args, variacao)
    if args.ensaio:
        padrao = PASTA_DO_EXPERIMENTO / "ensaio" if teste else PASTA_DO_DESENVOLVIMENTO / "ensaio" / variacao
        pasta = ensaio(por_id, pasta=args.pasta or padrao, variacao=variacao)
        print(f"Ensaio gravado em {pasta} / dry run written.")
        return
    if args.ordem:
        for m in modelos:
            print(f"\n{m['nome']}")
            for id_ in por_id:
                print(f"  {id_}: {' '.join(ordem_das_condicoes(m['nome'], id_))}")
        return

    if teste:
        pasta = args.pasta or (PASTA_DO_EXPERIMENTO if variacao == "V-1" else PASTA_DA_EXECUCAO_2)
        # PT: a execução 2 recebe os mesmos trechos da execução 1.
        # EN: run 2 reuses run 1's excerpts.
        pasta_dos_trechos = PASTA_DO_EXPERIMENTO
    else:
        pasta = args.pasta or PASTA_DO_DESENVOLVIMENTO / variacao
        # PT: os trechos ficam ao lado das pastas das variações, e uma
        #     revisão do conjunto, numa pasta nova, ganha os seus.
        # EN: excerpts sit next to the variant folders; a revision gets its own.
        pasta_dos_trechos = pasta.parent
    conferir_congelado()
    conferir_retrato()
    indice = conferir_indice()
    variaveis = conferir_variaveis(carregar_selecao())
    versao = conferir_versao_do_ollama(parametros.carregar().endereco)
    from assistente.contexto import buscar_trechos

    banco, modelo_de_prompt = abrir_banco(), parametros.modelo_de_prompt()
    assinatura = assinatura_dos_enunciados(por_id)
    for m in modelos:
        p = parametros_da_execucao(m, variacao, registrados)
        parametros.conferir_pre_registro(p)
        if p.provisorio:
            raise SystemExit("ERRO assistente/parametros.yml ainda provisório")
        conferir_pasta(pasta, m["nome"], variacao, p, args.perguntas, assinatura)
        if not faltam_execucoes(m, p, por_id, pasta):
            print(f"\n{m['nome']}: nada a rodar em {pasta}")
            continue
        digest = conferir_candidato(p.endereco, m)
        arquivo_do_ambiente = pasta / "execucoes" / m["nome"] / "ambiente.json"
        ambiente = json.loads(arquivo_do_ambiente.read_text(encoding="utf-8")) if arquivo_do_ambiente.exists() else {}
        ambiente.update({"candidato": m["nome"], "ollama": versao, "digest_do_gguf": digest, "variaveis": variaveis,
                         "variacao": variacao, "perguntas": args.perguntas, "enunciados": assinatura,
                         "versao_do_conjunto": None if teste else meta["versao"],
                         "duckdb": duckdb.__version__, "recarrega_a_cada_execucao": True,
                         "parametros": dataclasses.asdict(p)})
        ambiente.setdefault("inicio", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        if not (ambiente.get("vram") or {}).get("size_vram"):
            # PT: a VRAM com o num_ctx da variação, antes das execuções; o
            #     portão exige o modelo inteiro na GPU.
            # EN: VRAM at the variant's num_ctx; the gate needs a full fit.
            #     A carga da medida não serve à primeira execução: a recarga
            #     antes de cada uma a refaz, e custa só uma carga a mais por
            #     modelo e variação.
            # EN: the measuring load is discarded by the per-run reload.
            descarregar_todos(p.endereco)
            ambiente["vram"] = carregar_e_medir_vram(p.endereco, p.modelo, p.num_ctx)
        gravar_json(arquivo_do_ambiente, ambiente)
        vram = ambiente["vram"] or {}
        print(f"\n{m['nome']} ({m['ollama']}), {variacao}, num_ctx {p.num_ctx}, "
              f"na GPU {vram.get('size_vram')} de {vram.get('size')} bytes")
        cliente = ClienteOllama(p)
        try:
            rodadas = rodar_modelo(m, p, por_id, pasta, cliente_para=lambda id_, seed: cliente, banco=banco,
                                   modelo_de_prompt=modelo_de_prompt, buscar=buscar_trechos, indice=indice,
                                   variacao=variacao, pasta_dos_trechos=pasta_dos_trechos, cego=not teste,
                                   antes_de_cada=lambda: descarregar_e_esperar(p.endereco))
        except ParadaPorServidor as erro:
            raise SystemExit(f"ERRO de servidor em {erro}. A execução não foi gravada e entrou no "
                             f"{(pasta / REPETICOES).relative_to(RAIZ).as_posix()}. Confira o ollama serve e "
                             "rode o mesmo comando de novo: ele retoma daí.") from None
        ambiente["fim"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        gravar_json(arquivo_do_ambiente, ambiente)
        print(f"  {rodadas} execuções agora")
    proximo = f"uv run python -m correcao.as_cegas --experimento --execucao {1 if variacao == 'V-1' else 2}" if teste else \
        f"uv run python -m scripts.medir_portao --variacao {variacao}"
    print(f"\nRodado. Próximo passo: {proximo}")


if __name__ == "__main__":
    main()
