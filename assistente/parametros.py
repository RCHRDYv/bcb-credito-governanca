"""
PT: Parâmetros e modelo de prompt do assistente. A #48 fixa os dois
    arquivos e os congela por errata (ADR 0030); até lá, o parametros.yml
    marca provisorio. O parametros.yml lista os modelos, cada um com o
    próprio num_ctx e a própria razão de caracteres por token. A temperatura
    e as seeds repetem o bloco execucao do evaluation/hipoteses.yml,
    congelado no pré-registro (#47), e conferir_pre_registro() para se
    divergirem.

EN: Assistant parameters and prompt template, fixed and frozen by #48.
    parametros.yml lists the models, each with its own num_ctx and
    characters-per-token ratio. Temperature and seeds repeat the frozen
    execucao block, and conferir_pre_registro() stops if they diverge.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ingestion.fontes import RAIZ

PASTA = RAIZ / "assistente"
PARAMETROS = PASTA / "parametros.yml"
MODELO_DE_PROMPT = PASTA / "modelo_de_prompt.yml"
HIPOTESES = RAIZ / "evaluation" / "hipoteses.yml"
DIR_EXECUCOES = RAIZ / "data" / "assistente" / "execucoes"

# PT: as quatro condições do ADR 0013 e os blocos de cada uma, na ordem em
#     que entram no prompt (evaluation/hipoteses.yml, condicoes).
# EN: the four conditions and their blocks, in prompt order.
CONDICOES = {
    "A": ("esquema",),
    "B": ("esquema", "ontologia"),
    "C": ("esquema", "trechos"),
    "D": ("esquema", "ontologia", "trechos"),
}


@dataclass(frozen=True)
class Parametros:
    """PT: os valores de uma execução / EN: the values of one run"""

    provisorio: bool
    endereco: str
    tempo_maximo_do_servidor: float
    modelo: str
    temperatura: float
    seeds: tuple[int, ...]
    num_ctx: int
    limite_de_tokens_da_resposta: int
    caracteres_por_token_na_estimativa: float
    think: bool
    esquema_json: bool
    limite_de_linhas: int
    limite_de_tempo_do_sql: float


def modelos(arquivo: Path = PARAMETROS) -> list[str]:
    """PT: os nomes dos modelos do arquivo / EN: the file's model names"""
    return [m["nome"] for m in yaml.safe_load(arquivo.read_text(encoding="utf-8"))["modelos"]]


def carregar(arquivo: Path = PARAMETROS, modelo: str | None = None) -> Parametros:
    """
    PT: Lê o parametros.yml, com o modelo dado ou o primeiro da lista. O
        num_ctx e a razão de caracteres por token são do modelo.
    EN: Reads the parameters file, for the given model or the first one.
    """
    p = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    por_nome = {m["nome"]: m for m in p["modelos"]}
    if modelo is not None and modelo not in por_nome:
        raise SystemExit(f"ERRO modelo {modelo} fora do {arquivo.name}: {sorted(por_nome)}")
    m = por_nome[modelo] if modelo is not None else p["modelos"][0]
    return Parametros(
        provisorio=bool(p.get("provisorio", False)),
        endereco=p["servidor"]["endereco"],
        tempo_maximo_do_servidor=float(p["servidor"]["tempo_maximo_em_segundos"]),
        modelo=m["nome"],
        temperatura=float(p["geracao"]["temperatura"]),
        seeds=tuple(p["geracao"]["seeds"]),
        num_ctx=int(m["num_ctx"]),
        limite_de_tokens_da_resposta=int(p["geracao"]["limite_de_tokens_da_resposta"]),
        caracteres_por_token_na_estimativa=float(m["caracteres_por_token_na_estimativa"]),
        think=bool(p["geracao"]["think"]),
        esquema_json=bool(p["geracao"]["esquema_json"]),
        limite_de_linhas=int(p["sql"]["limite_de_linhas"]),
        limite_de_tempo_do_sql=float(p["sql"]["limite_de_tempo_em_segundos"]),
    )


def modelo_de_prompt(arquivo: Path = MODELO_DE_PROMPT) -> dict[str, str]:
    """PT: os textos do modelo de prompt / EN: the prompt template texts"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))


def divergencias_do_pre_registro(p: Parametros, hipoteses: dict) -> list[str]:
    """
    PT: Temperatura e seeds que não batem com o bloco execucao congelado.
    EN: Temperature and seeds that differ from the frozen execucao block.
    """
    execucao = hipoteses["execucao"]
    problemas = []
    if p.temperatura != execucao["temperatura"]:
        problemas.append(f"temperatura {p.temperatura} difere do pré-registro {execucao['temperatura']}")
    if list(p.seeds) != list(execucao["seeds"]):
        problemas.append(f"seeds {list(p.seeds)} diferem do pré-registro {execucao['seeds']}")
    return problemas


def conferir_pre_registro(p: Parametros) -> None:
    """
    PT: Para se os parâmetros daqui divergirem do bloco execucao congelado.
    EN: Stops if the parameters diverge from the frozen execucao block.
    """
    hipoteses = yaml.safe_load(HIPOTESES.read_text(encoding="utf-8"))
    if problemas := divergencias_do_pre_registro(p, hipoteses):
        raise SystemExit("ERRO parâmetros divergem do pré-registro / diverge from pre-registration: "
                         + "; ".join(problemas))
