"""
PT: A seleção dos modelos do experimento (#48, ADRs 0026 e 0030). Roda as 41
    perguntas do evaluation/questions_v3.yml na condição A, com as 5 seeds
    registradas, em cada candidato do evaluation/selecao.yml, pelo mesmo
    assistente.responder do experimento.

    Antes de rodar, para se faltar alguma coisa:

    - o selecao.yml completo (revisão, sha256, num_ctx e razão de cada
      candidato) e congelado, junto do modelo de prompt, por errata no
      evaluation/registro.yml: nada roda contra o gabarito antes disso;
    - a temperatura e as seeds iguais às do pré-registro;
    - o retrato local do esquema estrela no mesmo mês das respostas do
      gabarito (hipoteses.yml, comparacao.respostas_do_gabarito);
    - o Ollama no ar, com as variáveis do cache KV do selecao.yml, e cada
      candidato puxado, com o digest da camada do modelo igual ao sha256
      registrado.

    Grava um registro por execução em data/selecao/execucoes/<candidato>/,
    fora do git, e retoma de onde parou: execução gravada não roda de novo.
    O ambiente de cada candidato (versão do Ollama, digest, VRAM pelo
    /api/ps e parâmetros) vai para o ambiente.json da mesma pasta.

    Com --ensaio, roda sem Ollama, sem dado e sem errata: um candidato, duas
    perguntas, o cliente falso e o banco vazio, em data/selecao/ensaio/.
    Serve para conferir o formato dos registros.

EN: Runs the 41 registered questions in condition A, with the 5 registered
    seeds, on every candidate in selecao.yml, through the experiment's own
    responder. Refuses to run unless selecao.yml is complete and frozen by
    errata together with the prompt template, temperature and seeds match
    the pre-registration, the local snapshot matches the answer key month,
    and Ollama runs with the KV cache settings and each candidate's model
    layer digest equals the registered sha256. Writes one record per run
    (resumable) plus each candidate's environment. --ensaio runs offline
    with the fake client and empty database.

Uso / Usage:
    uv run python -m scripts.selecionar_modelos
    uv run python -m scripts.selecionar_modelos --candidato gemma-4-12b
    uv run python -m scripts.selecionar_modelos --ensaio
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from assistente import parametros
from assistente.cliente import ClienteFalso, ClienteOllama
from assistente.parametros import Parametros
from assistente.responder import responder
from assistente.sql import abrir_banco, banco_vazio
from correcao.acerto import PASTA_DA_SELECAO
from scripts.esquema_estrela_duckdb import MANIFESTO, esquema_esperado
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import REGISTRO, RAIZ, hashes_vigentes, ler_respostas, sha256

SELECAO = "evaluation/selecao.yml"
MODELO_DE_PROMPT = "assistente/modelo_de_prompt.yml"
CONGELADOS_ANTES_DA_SELECAO = (SELECAO, MODELO_DE_PROMPT)
CAMPOS_MEDIDOS = ("revisao", "sha256", "revisao_do_tokenizador", "num_ctx", "caracteres_por_token")
CONDICAO = "A"


# -----------------------------------------------------------------------------
# PT: O selecao.yml / EN: the selection file
# -----------------------------------------------------------------------------

def carregar_selecao(arquivo: Path = RAIZ / SELECAO) -> dict:
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))


def candidatos_incompletos(selecao: dict) -> list[str]:
    """PT: candidatos com campo medido ainda nulo / EN: candidates with null fields"""
    return [f"{c['nome']}: {campo}" for c in selecao["candidatos"] for campo in CAMPOS_MEDIDOS if c.get(campo) is None]


def parametros_do_candidato(base: Parametros, selecao: dict, candidato: dict) -> Parametros:
    """
    PT: Os parâmetros do assistente com os valores do selecao.yml: o modelo,
        o num_ctx e a razão do candidato, a geração e os limites do SQL.
    EN: Assistant parameters with the selection file's values.
    """
    g, s = selecao["geracao"], selecao["sql"]
    return dataclasses.replace(
        base,
        provisorio=False,
        modelo=candidato["ollama"],
        num_ctx=int(candidato["num_ctx"] or base.num_ctx),
        caracteres_por_token_na_estimativa=float(candidato["caracteres_por_token"]
                                                 or base.caracteres_por_token_na_estimativa),
        temperatura=float(g["temperatura"]),
        seeds=tuple(g["seeds"]),
        limite_de_tokens_da_resposta=int(g["limite_de_tokens_da_resposta"]),
        think=bool(g["think"]),
        esquema_json=bool(g["esquema_json"]),
        tempo_maximo_do_servidor=float(g["tempo_maximo_do_servidor_em_segundos"]),
        limite_de_linhas=int(s["limite_de_linhas"]),
        limite_de_tempo_do_sql=float(s["limite_de_tempo_em_segundos"]),
    )


# -----------------------------------------------------------------------------
# PT: Conferências antes de rodar / EN: pre-run checks
# -----------------------------------------------------------------------------

def nao_congelados(registro: dict, textos: dict[str, str]) -> list[str]:
    """
    PT: Os arquivos que deviam estar congelados por errata antes da seleção
        e não estão, ou mudaram depois.
    EN: Files that should be frozen by errata before selection and are not,
        or changed since.
    """
    vigentes = hashes_vigentes(registro)
    return [c for c in CONGELADOS_ANTES_DA_SELECAO if vigentes.get(c) != sha256(textos[c])]


def conferir_congelamento() -> None:
    registro = yaml.safe_load((RAIZ / REGISTRO).read_text(encoding="utf-8"))
    textos = {c: (RAIZ / c).read_text(encoding="utf-8") for c in CONGELADOS_ANTES_DA_SELECAO}
    if faltam := nao_congelados(registro, textos):
        raise SystemExit(f"ERRO sem errata vigente no {REGISTRO} para {faltam}: congele antes de rodar "
                         "contra o gabarito / freeze by errata first")


def conferir_retrato() -> None:
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    meses = {r["mes_de_referencia"] for r in ler_respostas().values()}
    if meses != {manifesto["mes_de_referencia"]}:
        raise SystemExit(f"ERRO respostas do gabarito de {sorted(meses)} e retrato de "
                         f"{manifesto['mes_de_referencia']}: regere o gabarito no mesmo mês")


def conferir_variaveis(selecao: dict) -> dict[str, str]:
    """
    PT: As variáveis do cache KV neste terminal. O ollama serve precisa ter
        sido aberto com elas, e o executor só vê as próprias: rode os dois
        no mesmo ambiente.
    EN: KV cache variables in this shell; ollama serve must share them.
    """
    esperadas = {k: str(v) for k, v in selecao["servidor"].items() if k.startswith("OLLAMA_")}
    erradas = {k: os.environ.get(k) for k, v in esperadas.items() if os.environ.get(k) != v}
    if erradas:
        raise SystemExit(f"ERRO variáveis do servidor {erradas}, esperado {esperadas}: abra o ollama serve com "
                         "elas, no mesmo ambiente deste comando")
    return esperadas


def _get(endereco: str, rota: str) -> dict:
    try:
        with urllib.request.urlopen(f"{endereco}{rota}", timeout=10) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as erro:
        raise SystemExit(f"ERRO Ollama fora do ar em {endereco} ({erro}): rode `ollama serve`") from None


def _post(endereco: str, rota: str, corpo: dict) -> dict:
    pedido = urllib.request.Request(f"{endereco}{rota}", data=json.dumps(corpo).encode("utf-8"),
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def pasta_de_modelos() -> Path:
    return Path(os.environ.get("OLLAMA_MODELS") or Path.home() / ".ollama" / "models")


def digest_do_gguf(nome: str, pasta: Path | None = None) -> str | None:
    """
    PT: O sha256 da camada do modelo no manifesto local do Ollama, que é o
        sha256 do arquivo GGUF. O manifesto de hf.co/<dono>/<repo>:<tag>
        fica em manifests/hf.co/<dono>/<repo>/<tag>; a busca ignora a caixa.
    EN: The model layer sha256 in Ollama's local manifest, i.e. the GGUF
        file's sha256.
    """
    caminho, _, tag = nome.partition(":")
    alvo = [*caminho.lower().split("/"), (tag or "latest").lower()]
    raiz = (pasta or pasta_de_modelos()) / "manifests"
    for arquivo in raiz.rglob("*"):
        if arquivo.is_file() and [p.lower() for p in arquivo.relative_to(raiz).parts] == alvo:
            manifesto = json.loads(arquivo.read_text(encoding="utf-8"))
            for camada in manifesto.get("layers", []):
                if camada.get("mediaType") == "application/vnd.ollama.image.model":
                    return camada["digest"].removeprefix("sha256:")
    return None


def conferir_candidato(endereco: str, candidato: dict) -> str:
    nomes = {m["name"] for m in _get(endereco, "/api/tags").get("models", [])}
    if candidato["ollama"] not in nomes:
        raise SystemExit(f"ERRO o Ollama não tem {candidato['ollama']}: rode `ollama pull {candidato['ollama']}`")
    digest = digest_do_gguf(candidato["ollama"])
    if digest != candidato["sha256"]:
        raise SystemExit(f"ERRO {candidato['nome']}: digest do GGUF {digest}, registrado {candidato['sha256']}. "
                         "O arquivo no Hugging Face mudou, ou o pull trouxe outro")
    return digest


def descarregar_todos(endereco: str) -> None:
    """PT: tira os modelos da memória, para medir a VRAM de um só / EN: unload all"""
    for m in _get(endereco, "/api/ps").get("models", []):
        _post(endereco, "/api/generate", {"model": m["name"], "keep_alive": 0})


def vram(endereco: str, nome: str) -> dict | None:
    """PT: o modelo carregado no /api/ps / EN: the loaded model in /api/ps"""
    for m in _get(endereco, "/api/ps").get("models", []):
        if m["name"] == nome:
            return {k: m.get(k) for k in ("size", "size_vram", "context_length", "expires_at")}
    return None


# -----------------------------------------------------------------------------
# PT: Execução / EN: running
# -----------------------------------------------------------------------------

def arquivo_da_execucao(pasta: Path, candidato: str, pergunta: str, seed: int) -> Path:
    return pasta / "execucoes" / candidato / f"{pergunta}_seed{seed}.json"


def gravar_json(arquivo: Path, dados: dict) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rodar_candidato(candidato: dict, p: Parametros, por_id: dict[str, dict], pasta: Path, *,
                    cliente_para, banco, modelo_de_prompt: dict, depois_da_primeira=None) -> int:
    """
    PT: As perguntas e seeds de um candidato, pulando as já gravadas.
        Devolve quantas rodaram agora.
    EN: One candidate's questions and seeds, skipping recorded ones.
    """
    rodadas = 0
    for id_, pergunta in por_id.items():
        for seed in p.seeds:
            arquivo = arquivo_da_execucao(pasta, candidato["nome"], id_, seed)
            if arquivo.exists():
                continue
            registro = responder(pergunta["pergunta"], CONDICAO, seed, cliente=cliente_para(id_, seed), banco=banco,
                                 p=p, modelo=modelo_de_prompt)
            registro = {"candidato": candidato["nome"], "id_pergunta": id_, **registro}
            gravar_json(arquivo, registro)
            rodadas += 1
            situacao = f"erro {registro['erro']['tipo']}" if registro["erro"] else \
                ("abstenção" if registro["resposta"]["abstencao"] else "respondeu")
            print(f"  {candidato['nome']} {id_} seed {seed}: {situacao}, {registro['segundos']} s")
            if depois_da_primeira and rodadas == 1:
                depois_da_primeira()
    return rodadas


def respostas_de_ensaio(id_: str) -> list[str]:
    """
    PT: Respostas gravadas do ensaio: uma abstenção e um SQL que roda no
        banco vazio, com a segunda chamada.
    EN: Recorded dry-run answers: one abstention, one SQL run on the empty db.
    """
    if id_.endswith("1"):
        return [json.dumps({"interpretacao": "ensaio", "sql": "", "abstencao": "ensaio sem modelo"})]
    tabela = next(iter(esquema_esperado()))
    return [
        json.dumps({"interpretacao": "ensaio", "sql": f"select count(*) as linhas from {tabela}", "abstencao": ""}),
        json.dumps({"interpretacao": "ensaio", "valores": {"colunas": ["linhas"], "linhas": [[0]]},
                    "ressalva": "", "abstencao": ""}),
    ]


def ensaio(selecao: dict, por_id: dict[str, dict]) -> Path:
    """PT: o executor sem modelo e sem dado / EN: offline dry run"""
    pasta = PASTA_DA_SELECAO / "ensaio"
    candidato = selecao["candidatos"][0]
    p = dataclasses.replace(parametros_do_candidato(parametros.carregar(), selecao, candidato), seeds=(1,))
    duas = dict(list(por_id.items())[:2])
    rodar_candidato(candidato, p, duas, pasta, cliente_para=lambda id_, seed: ClienteFalso(respostas_de_ensaio(id_)),
                    banco=banco_vazio(), modelo_de_prompt=parametros.modelo_de_prompt())
    return pasta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidato", action="append", help="só estes candidatos (repetível)")
    parser.add_argument("--ensaio", action="store_true", help="sem Ollama, sem dado e sem errata")
    args = parser.parse_args()

    selecao = carregar_selecao()
    _, por_id = perguntas(VIGENTE)
    base = parametros.carregar()
    if args.ensaio:
        pasta = ensaio(selecao, por_id)
        print(f"Ensaio gravado em {pasta} / dry run written.")
        return

    if faltam := candidatos_incompletos(selecao):
        raise SystemExit(f"ERRO {SELECAO} incompleto, rode scripts.dimensionar_contexto: {faltam}")
    conferir_congelamento()
    conferir_retrato()
    variaveis = conferir_variaveis(selecao)
    candidatos = [c for c in selecao["candidatos"] if not args.candidato or c["nome"] in args.candidato]
    if args.candidato and len(candidatos) != len(set(args.candidato)):
        raise SystemExit(f"ERRO candidato desconhecido em {args.candidato}")

    versao = _get(base.endereco, "/api/version").get("version")
    banco, modelo_de_prompt = abrir_banco(), parametros.modelo_de_prompt()
    for candidato in candidatos:
        p = parametros_do_candidato(base, selecao, candidato)
        parametros.conferir_pre_registro(p)
        digest = conferir_candidato(p.endereco, candidato)
        descarregar_todos(p.endereco)
        arquivo_do_ambiente = PASTA_DA_SELECAO / "execucoes" / candidato["nome"] / "ambiente.json"
        ambiente = json.loads(arquivo_do_ambiente.read_text(encoding="utf-8")) if arquivo_do_ambiente.exists() else {}
        ambiente.update({"candidato": candidato["nome"], "ollama": versao, "digest_do_gguf": digest,
                         "variaveis": variaveis, "parametros": dataclasses.asdict(p)})
        ambiente.setdefault("inicio", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))

        def medir_vram(ambiente=ambiente, p=p):
            ambiente["vram"] = vram(p.endereco, p.modelo)
            gravar_json(arquivo_do_ambiente, ambiente)

        gravar_json(arquivo_do_ambiente, ambiente)
        cliente = ClienteOllama(p)
        print(f"\n{candidato['nome']} ({candidato['ollama']}), num_ctx {p.num_ctx}")
        rodadas = rodar_candidato(candidato, p, por_id, PASTA_DA_SELECAO, cliente_para=lambda id_, seed: cliente,
                                  banco=banco, modelo_de_prompt=modelo_de_prompt,
                                  depois_da_primeira=None if ambiente.get("vram") else medir_vram)
        if not ambiente.get("vram"):
            print(f"  aviso: VRAM de {candidato['nome']} não medida; apague o ambiente.json e rode uma "
                  "execução para medir", file=sys.stderr)
        ambiente["fim"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        gravar_json(arquivo_do_ambiente, ambiente)
        print(f"  {rodadas} execuções agora")
    print("\nSeleção rodada. Próximo passo: uv run python -m correcao.as_cegas")


if __name__ == "__main__":
    main()
