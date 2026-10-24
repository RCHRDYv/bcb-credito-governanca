"""
PT: A busca dos itens da ontologia por pergunta (#120, ADR 0033), para B e
    D da V5 em diante. Os 147 itens viram embeddings uma vez por processo,
    na CPU, com o modelo escolhido do RAG (rag/manifesto.json). O texto de
    cada item é o mesmo YAML que vai no prompt (assistente/ontologia.py), e
    o modelo o corta no TAMANHO_MAXIMO_EM_TOKENS, que guarda o começo: o id,
    os rótulos e a definição. Nada é gravado: o índice se refaz em segundos,
    e o rag/manifesto.json, congelado, não muda.

    A busca é a mesma dos trechos (rag/indice.py): cosseno exato entre
    vetores normalizados, a pergunta como está e empate pela ordem do item
    nos arquivos.

EN: Per-question ontology item search for B and D from V5 on. The 147
    items are embedded once per process on CPU with the chosen RAG model,
    from the same YAML the prompt carries (cut at the model's token limit,
    which keeps id, labels and definition). Nothing is written, so the
    frozen rag/manifesto.json stays. Same exact cosine search as the chunks.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

import numpy as np
import yaml

from assistente import ontologia
from rag.indice import embeddings_das_consultas, embeddings_dos_trechos, melhores, modelo_escolhido


def texto_do_item(id_: str, item: dict) -> str:
    """PT: o item como vai no prompt, em YAML / EN: the item as prompted"""
    return yaml.safe_dump(ontologia.item_do_bloco(id_, item), allow_unicode=True, sort_keys=False,
                          width=10_000).strip()


def textos_dos_itens() -> dict[str, str]:
    """PT: id e texto de cada item, na ordem dos arquivos / EN: id to text"""
    return {id_: texto_do_item(id_, item) for id_, _, item in ontologia.itens()}


@lru_cache(maxsize=1)
def indice() -> tuple[list[str], np.ndarray]:
    """
    PT: Os ids e os vetores normalizados dos itens, calculados uma vez por
        processo.
    EN: Item ids and normalized vectors, computed once per process.
    """
    textos = textos_dos_itens()
    return list(textos), embeddings_dos_trechos(modelo_escolhido(), list(textos.values()))


def assinatura(k: int) -> dict[str, str | int]:
    """
    PT: O que define a busca: o modelo, o k e o sha256 dos textos dos itens.
        Vai em cada arquivo de itens recuperados, como a assinatura do índice
        vai nos trechos.
    EN: What defines the search: model, k and the items' text sha256.
    """
    textos = textos_dos_itens()
    conteudo = "\n\n".join(f"{id_}\n{texto}" for id_, texto in textos.items())
    return {"modelo": modelo_escolhido().nome, "k": k,
            "sha256_itens": hashlib.sha256(conteudo.encode("utf-8")).hexdigest()}


def buscar_itens(pergunta: str, k: int) -> list[dict]:
    """
    PT: Os k itens da ontologia mais próximos da pergunta, com a
        similaridade, do mais próximo para o menos.
    EN: The k ontology items closest to the question, with similarity.
    """
    ids, vetores = indice()
    similaridades = vetores @ embeddings_das_consultas(modelo_escolhido(), [pergunta])[0]
    return [{"id": ids[int(i)], "similaridade": round(float(similaridades[i]), 6)} for i in melhores(similaridades, k)]
