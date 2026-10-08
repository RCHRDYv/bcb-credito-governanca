"""
PT: O comando único que reconstrói o índice do RAG do zero, a partir do
    manifesto (issue #46, ADR 0028):

    1. confere que os parâmetros batem com o pré-registro;
    2. confere o sha256 de cada documento de data/raw/documentos/ contra a
       seção documentos do ingestion/manifesto.json. Arquivo que falta ou
       diverge para a construção, com a instrução de rodar
       ingestion.baixar_documentos;
    3. extrai as seções (rag.extrair);
    4. para cada candidato, corta os trechos no tokenizador dele, calcula os
       embeddings na CPU e grava data/rag/<candidato>/;
    5. grava rag/manifesto.json: os documentos com sha256, os parâmetros, e
       para cada candidato a revisão, o número de trechos, o sha256 dos
       trechos e dos embeddings e a memória dos pesos.

    O sha256 dos trechos é calculado sobre o conteúdo (JSON canônico de cada
    linha), e não sobre os bytes do Parquet, para não depender da versão da
    biblioteca. A escolha do modelo é do rag.avaliar, que a grava no mesmo
    manifesto; reconstruir mantém a escolha só se os trechos e os
    embeddings do escolhido não mudaram.

EN: The single command that rebuilds the RAG index from scratch, from the
    manifest: checks pre-registration parameters and document sha256s,
    extracts sections, cuts chunks and embeds them on CPU for each
    candidate, and writes rag/manifesto.json. The chunk sha256 is computed
    over content, not Parquet bytes. Rebuilding keeps the model choice only
    if the chosen candidate's chunks and vectors did not change.

Uso / Usage:
    uv run --group rag python -m rag.construir
    uv run --group rag python -m rag.construir --modelo bge-m3
"""

from __future__ import annotations

import argparse
import hashlib
import json

import numpy as np
import polars as pl

from ingestion import manifesto
from ingestion.baixar import sha256
from ingestion.fontes import DIR_RAW_DOCUMENTOS, DOCUMENTOS_DO_CORPUS
from rag import extrair, trechos
from rag.indice import ARQUIVO_EMBEDDINGS, ARQUIVO_TRECHOS, carregar_modelo, embeddings_dos_trechos, memoria_dos_pesos_em_mb
from rag.parametros import (CANDIDATOS, MANIFESTO_RAG, QUANTIDADE_DE_TRECHOS, SOBREPOSICAO_EM_TOKENS,
                            TAMANHO_MAXIMO_EM_TOKENS, Candidato, candidato, conferir_pre_registro)


def sha256_do_conteudo(tabela: pl.DataFrame) -> str:
    """
    PT: sha256 do conteúdo da tabela: uma linha de JSON canônico por linha.
    EN: sha256 of the table content: one canonical JSON line per row.
    """
    h = hashlib.sha256()
    for linha in tabela.iter_rows(named=True):
        h.update(json.dumps(linha, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    return h.hexdigest()


def conferir_documentos() -> dict:
    """
    PT: Confere cada documento do corpus contra o manifesto da ingestão e
        devolve {id: {arquivo, sha256}}.
    EN: Checks each corpus document against the ingestion manifest.
    """
    registrados = manifesto.carregar().get("documentos", {})
    documentos, erros = {}, []
    for doc in DOCUMENTOS_DO_CORPUS:
        caminho = DIR_RAW_DOCUMENTOS / doc.arquivo
        esperado = registrados.get(doc.arquivo, {}).get("sha256")
        if esperado is None:
            erros.append(f"{doc.arquivo}: fora do manifesto")
        elif not caminho.exists():
            erros.append(f"{doc.arquivo}: não está em {DIR_RAW_DOCUMENTOS}")
        elif sha256(caminho) != esperado:
            erros.append(f"{doc.arquivo}: sha256 diverge do manifesto")
        else:
            documentos[doc.id] = {"arquivo": doc.arquivo, "sha256": esperado}
    if erros:
        for erro in erros:
            print(f"  ERRO {erro}")
        raise SystemExit("Rode / run: uv run python -m ingestion.baixar_documentos")
    return documentos


def construir_candidato(c: Candidato, secoes: pl.DataFrame) -> dict:
    """
    PT: Trechos e embeddings de um candidato, gravados em data/rag/<nome>/.
    EN: One candidate's chunks and vectors, written to data/rag/<name>/.
    """
    modelo = carregar_modelo(c)
    tabela = trechos.cortar(secoes, modelo.tokenizer, c.prefixo_trecho)
    print(f"  > {c.nome}: {tabela.height} trechos, até {tabela['tokens_de_entrada'].max()} tokens de entrada", flush=True)
    vetores = embeddings_dos_trechos(c, tabela["texto"].to_list())
    c.pasta.mkdir(parents=True, exist_ok=True)
    tabela.write_parquet(c.pasta / ARQUIVO_TRECHOS, compression="zstd")
    np.save(c.pasta / ARQUIVO_EMBEDDINGS, vetores)
    return {
        "repositorio": c.repositorio,
        "revisao": c.revisao,
        "prefixo_consulta": c.prefixo_consulta,
        "prefixo_trecho": c.prefixo_trecho,
        "prompt_consulta": c.prompt_consulta,
        "dimensao": int(vetores.shape[1]),
        "trechos": tabela.height,
        "sha256_trechos": sha256_do_conteudo(tabela),
        "sha256_embeddings": hashlib.sha256(vetores.tobytes()).hexdigest(),
        "memoria_dos_pesos_em_mb": memoria_dos_pesos_em_mb(c),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", help="só este candidato / only this candidate")
    args = parser.parse_args()

    from transformers.utils import logging as logging_do_transformers

    # PT: o aviso de "sequence length" vem de tokenizar a seção inteira antes do corte.
    # EN: the "sequence length" warning comes from tokenizing a whole section before cutting.
    logging_do_transformers.set_verbosity_error()

    conferir_pre_registro()
    documentos = conferir_documentos()
    print(f"  = {len(documentos)} documentos conferidos com o manifesto / checked against the manifest")
    secoes = extrair.extrair_tudo()
    print(f"  > {secoes['secao'].n_unique()} seções em {secoes.height} blocos")

    anterior = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8")) if MANIFESTO_RAG.exists() else {}
    sha_secoes = sha256_do_conteudo(secoes)

    # PT: candidato que não é refeito agora só fica no manifesto se o índice
    #     dele veio dos mesmos documentos e das mesmas seções.
    # EN: a candidate not rebuilt now stays only if its index came from the
    #     same documents and sections.
    mesmo_corpus = anterior.get("documentos") == documentos and anterior.get("secoes", {}).get("sha256") == sha_secoes
    modelos = dict(anterior.get("candidatos", {})) if mesmo_corpus else {}
    if anterior and not mesmo_corpus and args.modelo:
        print("  ! documentos ou seções mudaram: os outros candidatos saem do manifesto; refaça-os")
    escolha = [candidato(args.modelo)] if args.modelo else list(CANDIDATOS)
    for c in escolha:
        modelos[c.nome] = construir_candidato(c, secoes)

    # PT: a escolha vale para o índice exato em que foi medida.
    # EN: the choice holds only for the exact index it was measured on.
    escolhido = anterior.get("escolhido")
    if escolhido:
        atual = modelos.get(escolhido["nome"], {})
        if (atual.get("sha256_trechos"), atual.get("sha256_embeddings")) != \
                (escolhido.get("sha256_trechos"), escolhido.get("sha256_embeddings")):
            print(f"  ! índice de {escolhido['nome']} mudou: a escolha cai, rode rag.avaliar")
            escolhido = None

    saida = {
        "issue": 46,
        "adr": "0028",
        "parametros": {
            "tamanho_maximo_em_tokens": TAMANHO_MAXIMO_EM_TOKENS,
            "sobreposicao_em_tokens": SOBREPOSICAO_EM_TOKENS,
            "quantidade_de_trechos": QUANTIDADE_DE_TRECHOS,
            "busca": "exata, por cosseno entre embeddings normalizados, na CPU",
        },
        "documentos": documentos,
        "secoes": {"blocos": secoes.height, "sha256": sha_secoes},
        "candidatos": modelos,
        "escolhido": escolhido,
    }
    MANIFESTO_RAG.write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  > {MANIFESTO_RAG.name}: {len(modelos)} candidatos")


if __name__ == "__main__":
    main()
