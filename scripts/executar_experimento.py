"""
PT: A execução do experimento 2x2 (#50, ADRs 0013, 0029 e 0031). Roda as 41
    perguntas do evaluation/questions_v3.yml nas quatro condições, com as 5
    seeds registradas, nos dois modelos do assistente/parametros.yml, pelo
    assistente.responder.

    Antes de rodar, para se faltar alguma coisa:

    - no conjunto de teste, o código sem mudança fora de commit: o commit
      vai para o ambiente.json de cada modelo (ADR 0032, que trocou o
      congelamento por errata do ADR 0031 por isso);
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
    registered seeds, on both models, through assistente.responder. On the
    test set it refuses uncommitted code and records the commit; it also
    checks parameters against the pre-registration, the local snapshot and
    RAG index, and Ollama's KV cache settings and registered GGUF. One model
    at a time; per question, one RAG search, then the four conditions (5
    seeds each) in an order drawn per question and model by a hash. Server
    errors are not recorded: they are logged and the run stops, to be
    resumed. --ensaio runs offline; --ordem prints the order.

    A variação do instrumento (#118, ADR 0032, assistente/variacoes.py) é a
    do assistente/parametros.yml: a execução 1 rodou na V−1, em
    data/experimento/, e a execução 2 roda na V4, em
    data/experimento/execucao-2/. O conjunto de desenvolvimento
    (--perguntas desenvolvimento) roda qualquer variação nos modelos
    registrados, em data/desenvolvimento/<variação>/.

Uso / Usage:
    uv run --group rag python -m scripts.executar_experimento --perguntas teste
    uv run python -m scripts.executar_experimento --perguntas teste --ensaio
    uv run python -m scripts.executar_experimento --perguntas teste --ordem
    uv run --group rag python -m scripts.executar_experimento --perguntas desenvolvimento --variacao V4
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import duckdb
import numpy as np
import yaml

from assistente import parametros, variacoes
from assistente.cliente import ClienteFalso, ClienteOllama
from assistente.parametros import CONDICOES, PARAMETROS, Parametros
from assistente.responder import responder
from assistente.sql import abrir_banco, banco_vazio
from correcao.acerto import PASTA_DO_EXPERIMENTO
from experimento import desenvolvimento
from scripts.esquema_estrela_duckdb import esquema_esperado
from scripts.selecionar_modelos import (
    _get,
    carregar_e_medir_vram,
    carregar_selecao,
    conferir_candidato,
    conferir_retrato,
    conferir_variaveis,
    descarregar_todos,
    gravar_json,
    respostas_de_ensaio,
)
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import RAIZ

# PT: o Ollama com que as execuções rodaram; outra versão pode mudar a
#     gramática e a geração (ADR 0032).
# EN: the Ollama version the runs used.
VERSAO_DO_OLLAMA = "0.40.4"
PASTA_DO_DESENVOLVIMENTO = RAIZ / "data" / "desenvolvimento"
# PT: a execução 1 roda na V−1, em data/experimento; a execução 2, na
#     variação do parametros.yml, numa pasta própria.
# EN: run 1 (V−1) lives in data/experimento; run 2 in its own folder.
PASTA_DA_EXECUCAO_2 = PASTA_DO_EXPERIMENTO / "execucao-2"
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


def variacao_registrada(arquivo: Path = PARAMETROS) -> str:
    """PT: a variação do parametros.yml, ou V−1 / EN: the registered variant"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8")).get("variacao", "V-1")


def parametros_da_execucao(m: dict) -> Parametros:
    """
    PT: Os parâmetros de um modelo registrado, do assistente/parametros.yml.
        O num_ctx de 53.248 serve da V−1 à V4: o pior caso medido da V4 no
        Gemma é de 53.043 tokens (ADR 0032).
    EN: A registered model's parameters, from parametros.yml.
    """
    return parametros.carregar(modelo=m["ollama"])


# -----------------------------------------------------------------------------
# PT: Conferências antes de rodar / EN: pre-run checks
# -----------------------------------------------------------------------------

def conferir_teste(args, variacao: str) -> None:
    """
    PT: No conjunto de teste, só roda a variação registrada no
        parametros.yml, na pasta fixa da execução.
    EN: On the test set only the registered variant runs, in its fixed folder.
    """
    if variacao != variacao_registrada():
        raise SystemExit(f"ERRO a {variacao} não é a variação registrada ({variacao_registrada()}): no teste só roda "
                         "a variação do parametros.yml")
    if args.pasta:
        raise SystemExit("ERRO --pasta não vale no teste: cada execução tem a sua pasta fixa")


def commit_do_codigo() -> dict:
    """
    PT: O commit do código e se há mudança fora dele. Substitui o
        congelamento por errata (ADR 0032): o ambiente.json de cada modelo
        diz com que código a execução rodou.
    EN: The code commit and whether anything is uncommitted; replaces the
        errata freeze.
    """
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()

    return {"commit": git("rev-parse", "HEAD"), "mudancas_sem_commit": bool(git("status", "--porcelain"))}


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
                 variacao: str = "V-1", pasta_dos_trechos: Path | None = None, cego: bool = False) -> int:
    """
    PT: As perguntas de um modelo, na ordem registrada, pulando as execuções
        já gravadas. Devolve quantas rodaram agora. Um erro de servidor é
        anotado e para tudo, sem gravar a execução.
        Com cego (o conjunto de desenvolvimento), o progresso sai só como contagem, sem a
        condição, o desfecho nem o tempo de cada execução: fora o G0, nada
        aparece por condição.
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
    rodar_modelo(modelo, p, duas, pasta,
                 cliente_para=lambda id_, seed: ClienteFalso(respostas_de_ensaio_da_variacao(variacao, id_)),
                 banco=banco_vazio(), modelo_de_prompt=parametros.modelo_de_prompt(),
                 buscar=lambda pergunta: TRECHOS_DE_ENSAIO, indice=INDICE_DE_ENSAIO, variacao=variacao)
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
    parser.add_argument("--perguntas", choices=["teste", "desenvolvimento"], required=True)
    parser.add_argument("--variacao", choices=variacoes.ORDEM, help="sem ela, a do parametros.yml (ou V-1)")
    parser.add_argument("--pasta", type=Path, help="pasta de saída")
    parser.add_argument("--ensaio", action="store_true", help="sem Ollama, sem dado e sem RAG")
    parser.add_argument("--ordem", action="store_true", help="só mostra a ordem das condições")
    args = parser.parse_args()

    variacao = args.variacao or variacao_registrada()
    teste = args.perguntas == "teste"
    meta, por_id = perguntas(VIGENTE) if teste else desenvolvimento.perguntas()
    registrados = {m["nome"] for m in modelos_do_experimento()}
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

    codigo = commit_do_codigo()
    if teste:
        # PT: o resultado do teste tem de corresponder a um commit.
        # EN: test results must map to a commit.
        if codigo["mudancas_sem_commit"]:
            raise SystemExit("ERRO há mudanças sem commit: faça o commit antes de rodar o teste, para o resultado "
                             "corresponder a um código conhecido")
        pasta = PASTA_DO_EXPERIMENTO if variacao == "V-1" else PASTA_DA_EXECUCAO_2
        # PT: a execução 2 recebe os mesmos trechos da execução 1.
        # EN: run 2 reuses run 1's excerpts.
        pasta_dos_trechos = PASTA_DO_EXPERIMENTO
    else:
        pasta = args.pasta or PASTA_DO_DESENVOLVIMENTO / variacao
        pasta_dos_trechos = pasta.parent
    conferir_retrato()
    indice = conferir_indice()
    variaveis = conferir_variaveis(carregar_selecao())
    versao = conferir_versao_do_ollama(parametros.carregar().endereco)
    from assistente.contexto import buscar_trechos

    banco, modelo_de_prompt = abrir_banco(), parametros.modelo_de_prompt()
    assinatura = assinatura_dos_enunciados(por_id)
    for m in modelos:
        p = parametros_da_execucao(m)
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
                         "codigo": codigo, "duckdb": duckdb.__version__, "parametros": dataclasses.asdict(p)})
        ambiente.setdefault("codigo_no_inicio", codigo)
        ambiente.setdefault("inicio", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        if not (ambiente.get("vram") or {}).get("size_vram"):
            # PT: a VRAM com o num_ctx do modelo, antes das execuções.
            # EN: VRAM at the model's num_ctx, before the runs.
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
                                   variacao=variacao, pasta_dos_trechos=pasta_dos_trechos, cego=not teste)
        except ParadaPorServidor as erro:
            raise SystemExit(f"ERRO de servidor em {erro}. A execução não foi gravada e entrou no "
                             f"{(pasta / REPETICOES).relative_to(RAIZ).as_posix()}. Confira o ollama serve e "
                             "rode o mesmo comando de novo: ele retoma daí.") from None
        ambiente["fim"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        gravar_json(arquivo_do_ambiente, ambiente)
        print(f"  {rodadas} execuções agora")
    if teste:
        print(f"\nRodado. Próximo passo: uv run python -m correcao.as_cegas --experimento --execucao "
              f"{1 if variacao == 'V-1' else 2}")


if __name__ == "__main__":
    main()
