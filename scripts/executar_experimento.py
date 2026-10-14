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

Uso / Usage:
    uv run --group rag python -m scripts.executar_experimento --modelo gemma-4-12b
    uv run --group rag python -m scripts.executar_experimento --modelo qwen3.5-9b
    uv run python -m scripts.executar_experimento --ensaio
    uv run python -m scripts.executar_experimento --ordem
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import yaml

from assistente import parametros
from assistente.cliente import ClienteFalso, ClienteOllama
from assistente.parametros import CONDICOES, PARAMETROS, Parametros
from assistente.responder import responder
from assistente.sql import abrir_banco, banco_vazio
from correcao.acerto import PASTA_DO_EXPERIMENTO
from scripts.selecionar_modelos import (
    _get,
    carregar_selecao,
    conferir_candidato,
    conferir_congelamento,
    conferir_retrato,
    conferir_variaveis,
    gravar_json,
    respostas_de_ensaio,
)
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import RAIZ

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
)
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


# -----------------------------------------------------------------------------
# PT: Conferências antes de rodar / EN: pre-run checks
# -----------------------------------------------------------------------------

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
                 cliente_para, banco, modelo_de_prompt: dict, buscar, indice: dict[str, str]) -> int:
    """
    PT: As perguntas de um modelo, na ordem registrada, pulando as execuções
        já gravadas. Devolve quantas rodaram agora. Um erro de servidor é
        anotado e para tudo, sem gravar a execução.
    EN: One model's questions in the registered order, skipping recorded
        runs. A server error is logged and stops the run unrecorded.
    """
    rodadas = 0
    for id_, pergunta in por_id.items():
        ordem = ordem_das_condicoes(modelo["nome"], id_)
        faltam = [(c, s) for c in ordem for s in p.seeds
                  if not arquivo_da_execucao(pasta, modelo["nome"], c, id_, s).exists()]
        if not faltam:
            continue
        trechos = trechos_da_pergunta(pasta, id_, pergunta["pergunta"], buscar, indice)
        for condicao, seed in faltam:
            registro = responder(pergunta["pergunta"], condicao, seed, cliente=cliente_para(id_, seed), banco=banco,
                                 p=p, modelo=modelo_de_prompt,
                                 trechos=trechos if "trechos" in CONDICOES[condicao] else None)
            registro = {"candidato": modelo["nome"], "id_pergunta": id_, **registro}
            if registro["erro"] and registro["erro"]["tipo"] == "servidor":
                registrar_repeticao(pasta, registro)
                raise ParadaPorServidor(f"{modelo['nome']} {condicao} {id_} seed {seed}: "
                                        f"{registro['erro']['mensagem']}")
            gravar_json(arquivo_da_execucao(pasta, modelo["nome"], condicao, id_, seed), registro)
            rodadas += 1
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


def ensaio(por_id: dict[str, dict], pasta: Path = PASTA_DO_EXPERIMENTO / "ensaio") -> Path:
    """
    PT: O executor sem modelo, sem dado e sem RAG, numa pasta zerada antes.
    EN: Offline dry run in a folder emptied first.
    """
    shutil.rmtree(pasta, ignore_errors=True)
    modelo = modelos_do_experimento()[0]
    p = dataclasses.replace(parametros.carregar(modelo=modelo["ollama"]), seeds=(1,))
    duas = dict(list(por_id.items())[:2])
    rodar_modelo(modelo, p, duas, pasta, cliente_para=lambda id_, seed: ClienteFalso(respostas_de_ensaio(id_)),
                 banco=banco_vazio(), modelo_de_prompt=parametros.modelo_de_prompt(),
                 buscar=lambda pergunta: TRECHOS_DE_ENSAIO, indice=INDICE_DE_ENSAIO)
    return pasta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", action="append", help="só estes modelos, pelo nome curto (repetível)")
    parser.add_argument("--ensaio", action="store_true", help="sem Ollama, sem dado, sem RAG e sem errata")
    parser.add_argument("--ordem", action="store_true", help="só mostra a ordem das condições")
    args = parser.parse_args()

    _, por_id = perguntas(VIGENTE)
    modelos = [m for m in modelos_do_experimento() if not args.modelo or m["nome"] in args.modelo]
    if args.modelo and len(modelos) != len(set(args.modelo)):
        raise SystemExit(f"ERRO modelo desconhecido em {args.modelo}: "
                         f"{[m['nome'] for m in modelos_do_experimento()]}")
    if args.ensaio:
        pasta = ensaio(por_id)
        print(f"Ensaio gravado em {pasta} / dry run written.")
        return
    if args.ordem:
        for m in modelos:
            print(f"\n{m['nome']}")
            for id_ in por_id:
                print(f"  {id_}: {' '.join(ordem_das_condicoes(m['nome'], id_))}")
        return

    conferir_congelamento(CONGELADOS_ANTES_DO_EXPERIMENTO)
    conferir_retrato()
    indice = conferir_indice()
    variaveis = conferir_variaveis(carregar_selecao())
    from assistente.contexto import buscar_trechos

    banco, modelo_de_prompt = abrir_banco(), parametros.modelo_de_prompt()
    pasta = PASTA_DO_EXPERIMENTO
    for m in modelos:
        p = parametros.carregar(modelo=m["ollama"])
        parametros.conferir_pre_registro(p)
        if p.provisorio:
            raise SystemExit("ERRO assistente/parametros.yml ainda provisório")
        digest = conferir_candidato(p.endereco, m)
        arquivo_do_ambiente = pasta / "execucoes" / m["nome"] / "ambiente.json"
        ambiente = json.loads(arquivo_do_ambiente.read_text(encoding="utf-8")) if arquivo_do_ambiente.exists() else {}
        ambiente.update({"candidato": m["nome"], "ollama": _get(p.endereco, "/api/version").get("version"),
                         "digest_do_gguf": digest, "variaveis": variaveis, "parametros": dataclasses.asdict(p)})
        ambiente.setdefault("inicio", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        gravar_json(arquivo_do_ambiente, ambiente)
        print(f"\n{m['nome']} ({m['ollama']}), num_ctx {p.num_ctx}")
        cliente = ClienteOllama(p)
        try:
            rodadas = rodar_modelo(m, p, por_id, pasta, cliente_para=lambda id_, seed: cliente, banco=banco,
                                   modelo_de_prompt=modelo_de_prompt, buscar=buscar_trechos, indice=indice)
        except ParadaPorServidor as erro:
            raise SystemExit(f"ERRO de servidor em {erro}. A execução não foi gravada e entrou no "
                             f"{(pasta / REPETICOES).relative_to(RAIZ).as_posix()}. Confira o ollama serve e "
                             "rode o mesmo comando de novo: ele retoma daí.") from None
        ambiente["fim"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        gravar_json(arquivo_do_ambiente, ambiente)
        print(f"  {rodadas} execuções agora")
    print("\nExperimento rodado. Próximo passo: uv run python -m correcao.as_cegas --experimento")


if __name__ == "__main__":
    main()
