"""
PT: Parâmetros do RAG. Os do trecho e da busca repetem o bloco rag do
    evaluation/hipoteses.yml, congelado no pré-registro (#47), e
    conferir_pre_registro() para a construção se os dois divergirem. Os
    candidatos a modelo de embeddings e a regra de escolha foram decididos
    em 2026-10-07 (issue #46, ADR 0028).

EN: RAG parameters. Chunk and search values repeat the frozen rag block of
    evaluation/hipoteses.yml, and conferir_pre_registro() stops the build if
    they diverge. The embedding candidates and the selection rule were
    decided on 2026-10-07.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ingestion.fontes import RAIZ

# -----------------------------------------------------------------------------
# PT: Caminhos. O que é dado fica em data/rag (ignorado pelo git); o que é
#     identidade e medida fica em rag/, versionado.
# EN: Paths. Data lives in data/rag (gitignored); identity and measures in
#     rag/, versioned.
# -----------------------------------------------------------------------------

DIR_RAG = RAIZ / "data" / "rag"
SECOES = DIR_RAG / "secoes.parquet"
MANIFESTO_RAG = RAIZ / "rag" / "manifesto.json"
AVALIACAO = RAIZ / "rag" / "avaliacao.json"
HIPOTESES = RAIZ / "evaluation" / "hipoteses.yml"
GABARITO_DE_RECUPERACAO = RAIZ / "evaluation" / "recuperacao.yml"

# -----------------------------------------------------------------------------
# PT: Trecho e busca, como no pré-registro.
# EN: Chunk and search, as pre-registered.
# -----------------------------------------------------------------------------

TAMANHO_MAXIMO_EM_TOKENS = 512
SOBREPOSICAO_EM_TOKENS = 64
QUANTIDADE_DE_TRECHOS = 5


def conferir_pre_registro() -> None:
    """
    PT: Para se os parâmetros daqui divergirem do bloco rag congelado.
    EN: Stops if the parameters here diverge from the frozen rag block.
    """
    rag = yaml.safe_load(HIPOTESES.read_text(encoding="utf-8"))["condicoes"]["rag"]
    esperado = {
        "tamanho_maximo_em_tokens": TAMANHO_MAXIMO_EM_TOKENS,
        "sobreposicao_em_tokens": SOBREPOSICAO_EM_TOKENS,
        "quantidade_de_trechos": QUANTIDADE_DE_TRECHOS,
    }
    registrado = {
        "tamanho_maximo_em_tokens": rag["trecho"]["tamanho_maximo_em_tokens"],
        "sobreposicao_em_tokens": rag["trecho"]["sobreposicao_em_tokens"],
        "quantidade_de_trechos": rag["busca"]["quantidade_de_trechos"],
    }
    if esperado != registrado:
        raise SystemExit(f"ERRO parâmetros divergem do pré-registro / diverge from pre-registration: {registrado}")


# -----------------------------------------------------------------------------
# PT: Candidatos a modelo de embeddings, cada um fixado por revisão do
#     Hugging Face. O prefixo da consulta e o do trecho são o formato de
#     entrada que o próprio modelo pede (o e5 usa "query: " e "passage: ", o
#     Qwen3 usa o prompt "query" que vem no repositório dele), e não
#     reescrita da pergunta.
# EN: Embedding candidates, each pinned to a Hugging Face revision. Query and
#     passage prefixes are the input format the model itself requires, not
#     question rewriting.
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidato:
    """PT: um modelo de embeddings candidato / EN: one embedding candidate"""

    nome: str  # PT: nome curto, vira pasta em data/rag / EN: short name, folder in data/rag
    repositorio: str
    revisao: str
    prefixo_consulta: str = ""
    prefixo_trecho: str = ""
    prompt_consulta: str | None = None  # PT: nome do prompt do sentence-transformers / EN: sentence-transformers prompt name

    @property
    def pasta(self) -> Path:
        return DIR_RAG / self.nome


CANDIDATOS = (
    Candidato(nome="bge-m3", repositorio="BAAI/bge-m3", revisao="5617a9f61b028005a4858fdac845db406aefb181"),
    Candidato(
        nome="multilingual-e5-large",
        repositorio="intfloat/multilingual-e5-large",
        revisao="3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3",
        prefixo_consulta="query: ",
        prefixo_trecho="passage: ",
    ),
    Candidato(
        nome="qwen3-embedding-0.6b",
        repositorio="Qwen/Qwen3-Embedding-0.6B",
        revisao="97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        prompt_consulta="query",
    ),
)


def candidato(nome: str) -> Candidato:
    """PT: candidato pelo nome curto / EN: candidate by short name"""
    for c in CANDIDATOS:
        if c.nome == nome:
            return c
    raise SystemExit(f"ERRO candidato desconhecido / unknown candidate: {nome}")
