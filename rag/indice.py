"""
PT: Embeddings e busca. Os embeddings rodam na CPU (decisão de 2026-10-07),
    normalizados, e a busca é exata: o produto interno entre vetores
    normalizados é a similaridade de cosseno, e os 5 maiores são os trechos
    trazidos (evaluation/hipoteses.yml, rag.busca). Empate se resolve pela
    ordem do trecho no corpus, para a busca ser determinística.

    A #49 usa buscar(pergunta), que lê o modelo escolhido no
    rag/manifesto.json.

EN: Embeddings and search. Embeddings run on CPU, normalized, and search is
    exact: the inner product of normalized vectors is the cosine
    similarity, and the top 5 are returned. Ties break by corpus order.
    #49 uses buscar(pergunta), which reads the chosen model from
    rag/manifesto.json.
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import polars as pl

from rag.parametros import MANIFESTO_RAG, QUANTIDADE_DE_TRECHOS, TAMANHO_MAXIMO_EM_TOKENS, Candidato, candidato

ARQUIVO_TRECHOS = "trechos.parquet"
ARQUIVO_EMBEDDINGS = "embeddings.npy"


@lru_cache(maxsize=None)
def carregar_modelo(c: Candidato):
    """
    PT: Modelo na revisão fixada, na CPU e em float32. Sem o float32 o Qwen3
        carrega em bfloat16, o tipo do config dele, e a normalização sai com
        erro na terceira casa (medido em 2026-10-08: normas de 0,998 a
        1,004); assim os três candidatos rodam na mesma precisão. O import
        fica aqui dentro para que quem só lê o manifesto não precise do torch.
    EN: Model at the pinned revision, on CPU, in float32, so all candidates
        run at the same precision (Qwen3 would load in bfloat16).
    """
    import torch
    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(c.repositorio, revision=c.revisao, device="cpu",
                                 model_kwargs={"dtype": torch.float32})
    modelo.max_seq_length = TAMANHO_MAXIMO_EM_TOKENS
    return modelo


def memoria_dos_pesos_em_mb(c: Candidato) -> float:
    """
    PT: Tamanho dos pesos e buffers do modelo carregado. Como tudo roda na
        CPU, é a medida de memória do desempate (ADR 0028).
    EN: Size of the loaded model's weights and buffers, the tie-break measure.
    """
    modelo = carregar_modelo(c)
    total = sum(t.numel() * t.element_size() for t in [*modelo.parameters(), *modelo.buffers()])
    return round(total / 2**20, 1)


def normalizar(vetores: np.ndarray) -> np.ndarray:
    """
    PT: Norma 1 em float32, para que o produto interno seja o cosseno.
    EN: Unit norm in float32, so the inner product is the cosine.
    """
    vetores = vetores.astype(np.float32)
    return vetores / np.linalg.norm(vetores, axis=1, keepdims=True)


def embeddings_dos_trechos(c: Candidato, textos: list[str]) -> np.ndarray:
    """PT: vetores normalizados dos trechos / EN: normalized chunk vectors"""
    modelo = carregar_modelo(c)
    entradas = [c.prefixo_trecho + t for t in textos]
    vetores = modelo.encode(entradas, batch_size=8, normalize_embeddings=True, show_progress_bar=True,
                            convert_to_numpy=True)
    return normalizar(vetores)


def embeddings_das_consultas(c: Candidato, consultas: list[str]) -> np.ndarray:
    """
    PT: Vetores normalizados das consultas, no formato de entrada do modelo:
        o prefixo do e5, ou o prompt "query" do Qwen3.
    EN: Normalized query vectors in the model's input format.
    """
    modelo = carregar_modelo(c)
    if c.prompt_consulta:
        vetores = modelo.encode(consultas, prompt_name=c.prompt_consulta, normalize_embeddings=True,
                                convert_to_numpy=True)
    else:
        vetores = modelo.encode([c.prefixo_consulta + q for q in consultas], normalize_embeddings=True,
                                convert_to_numpy=True)
    return normalizar(vetores)


def melhores(similaridades: np.ndarray, k: int = QUANTIDADE_DE_TRECHOS) -> np.ndarray:
    """
    PT: Índices dos k maiores, do maior para o menor. O sort estável sobre o
        negativo deixa o trecho de número menor na frente em caso de empate.
    EN: Indices of the k largest, in descending order, ties by corpus order.
    """
    return np.argsort(-similaridades, kind="stable")[:k]


@lru_cache(maxsize=None)
def carregar_indice(c: Candidato) -> tuple[pl.DataFrame, np.ndarray]:
    """
    PT: Trechos e embeddings gravados por rag.construir, lidos uma vez por
        processo: a #49 busca muitas perguntas no mesmo índice.
    EN: Chunks and vectors written by rag.construir, read once per process.
    """
    pasta = c.pasta
    if not (pasta / ARQUIVO_TRECHOS).exists():
        raise SystemExit(f"ERRO índice de {c.nome} não existe: rode rag.construir / index missing, run rag.construir")
    return pl.read_parquet(pasta / ARQUIVO_TRECHOS), np.load(pasta / ARQUIVO_EMBEDDINGS)


def modelo_escolhido() -> Candidato:
    """PT: o candidato escolhido em rag/manifesto.json / EN: the chosen candidate"""
    escolhido = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8")).get("escolhido")
    if not escolhido:
        raise SystemExit("ERRO nenhum modelo escolhido: rode rag.avaliar / no model chosen, run rag.avaliar")
    return candidato(escolhido["nome"])


def buscar(pergunta: str, k: int = QUANTIDADE_DE_TRECHOS, modelo: str | None = None) -> list[dict]:
    """
    PT: Os k trechos mais próximos da pergunta, com documento, seção, página,
        texto e similaridade. A pergunta entra como está, sem reescrita.
    EN: The k chunks closest to the question, with metadata and similarity.
        The question goes in as is, without rewriting.
    """
    c = candidato(modelo) if modelo else modelo_escolhido()
    trechos, vetores = carregar_indice(c)
    similaridades = vetores @ embeddings_das_consultas(c, [pergunta])[0]
    resultado = []
    for i in melhores(similaridades, k):
        linha = trechos.row(int(i), named=True)
        resultado.append({"trecho": linha["trecho"], "documento": linha["documento"], "secao": linha["secao"],
                          "pagina": linha["pagina"], "texto": linha["texto"],
                          "similaridade": round(float(similaridades[i]), 6)})
    return resultado
