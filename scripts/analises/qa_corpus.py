"""
PT: QA do corpus e do índice do RAG (#46, ADR 0028), por um caminho
    diferente da construção e da avaliação.

    O que é conferido:

    1. **Extração contra a ontologia.** Para cada conceito verbatim do
       gabarito de recuperação, a definição da ontologia aparece no texto
       extraído do lugar citado (página ou seção): pelo menos 75% dos
       8-gramas de caracteres da definição estão lá. A comparação usa só
       letras e números, porque a extração do PDF insere espaços no meio
       das palavras (nota de transcrição do ontology/modalidades.yml) e a
       ontologia às vezes tira um travessão ou uma URL. Uma substring exata
       reprovaria a definição que começa no pé da página e termina na outra,
       com uma tabela no meio. Confere a extração e a citação sem
       embeddings. Medido em 2026-10-07: 86 definições com 78,5% ou mais, e
       três abaixo de 20%, listadas em PARAFRASES_MARCADAS_VERBATIM.
    2. **Trechos.** Para cada candidato: o sha256 dos trechos bate com o
       rag/manifesto.json; todo documento do manifesto tem trechos; nenhum
       trecho passa de 512 tokens de entrada, recontados com o tokenizador;
       e todo trecho é um recorte do texto da sua seção, montado de novo a
       partir de data/rag/secoes.parquet, o que prova que nenhum trecho
       cruza a fronteira de seção.
    3. **Acerto recalculado no DuckDB.** As consultas do gabarito são
       comparadas com os mesmos embeddings por list_cosine_similarity do
       DuckDB, os 5 primeiros saem de um ROW_NUMBER, e a posição do
       primeiro acerto de cada conceito tem de ser a do rag/avaliacao.json.
       O que muda é o cálculo da similaridade e do ranking; a regra de
       correspondência é a mesma (rag.avaliar.casa).
    4. **Escolha.** O escolhido do manifesto é o do avaliacao.json, e a
       revisão é a fixada em rag/parametros.py.

EN: QA of the RAG corpus and index by a different path: verbatim
    definitions appear in the extracted text at the cited place; chunk
    hashes, size and containment in their section are rechecked; hit@5 is
    recomputed with DuckDB's list_cosine_similarity and a ROW_NUMBER
    ranking; and the manifest's choice matches the evaluation.

Uso / Usage:
    uv run --group rag python -m scripts.analises.qa_corpus
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import duckdb
import numpy as np
import polars as pl
import yaml

from ingestion import manifesto
from ingestion.fontes import DOCUMENTOS_DO_CORPUS
from rag.avaliar import casa, casa_secao
from rag.construir import sha256_do_conteudo
from rag.indice import carregar_indice, embeddings_das_consultas
from rag.parametros import (AVALIACAO, CANDIDATOS, GABARITO_DE_RECUPERACAO, MANIFESTO_RAG, QUANTIDADE_DE_TRECHOS,
                            RAIZ, SECOES, TAMANHO_MAXIMO_EM_TOKENS)
from rag.trechos import secoes_em_ordem, tokens_de_entrada
from scripts.analises.qa_esquema_estrela import Conferencia
from scripts.gerar_gabarito_de_recuperacao import conceitos_da_ontologia
from scripts.gerar_seeds_da_ontologia import texto


# -----------------------------------------------------------------------------
# PT: 1. Extração contra a ontologia
# EN: 1. Extraction against the ontology
# -----------------------------------------------------------------------------

COBERTURA_MINIMA = 0.75
TAMANHO_DO_NGRAMA = 8

# PT: Conceitos marcados como verbatim na ontologia cuja definição resolve
#     uma referência do texto da fonte: a Metodologia V2 diz "Somatório dos
#     itens s e v", e a ontologia escreveu os nomes dos itens. A definição não
#     está na fonte palavra por palavra. Achado em 2026-10-07, na #46; a
#     correção da confiança na ontologia é decisão do Yuri. O QA confere que
#     continuam abaixo do limite, para a lista não ficar velha.
# EN: Concepts marked verbatim whose definition resolves a reference in the
#     source text ("items s and v"); not verbatim in the source.
PARAFRASES_MARCADAS_VERBATIM = {
    "metricas.carteira_a_vencer",
    "metricas.carteira_vencida",
    "metricas.carteira_ativa",
}


def compacto(valor: str) -> str:
    """PT: só letras e números, em minúsculas / EN: letters and digits only, casefolded"""
    return re.sub(r"[\W_]+", "", valor).casefold()


def cobertura(definicao: str, lugar: str) -> float:
    """PT: parcela dos 8-gramas da definição presentes no lugar / EN: share of 8-grams found"""
    ngramas = {definicao[i:i + TAMANHO_DO_NGRAMA] for i in range(len(definicao) - TAMANHO_DO_NGRAMA + 1)}
    return sum(n in lugar for n in ngramas) / len(ngramas) if ngramas else 0.0


def texto_no_lugar(secoes: pl.DataFrame, alvo: dict) -> str:
    """
    PT: Texto extraído do lugar citado. Para página, junta as páginas
        citadas e a seguinte, porque a definição pode começar no fim da
        página citada e terminar na outra.
    EN: Extracted text at the cited place.
    """
    do_documento = secoes.filter(pl.col("documento") == alvo["documento"])
    if alvo["granularidade"] == "pagina":
        paginas = {str(p) for p in alvo["paginas"]} | {str(p + 1) for p in alvo["paginas"]}
        partes = do_documento.filter(pl.col("pagina").is_in(sorted(paginas)))
    elif alvo["granularidade"] == "secao":
        partes = do_documento.filter(pl.col("secao").map_elements(
            lambda s: any(casa_secao(c, s) for c in alvo["secoes"]), return_dtype=pl.Boolean))
    else:
        partes = do_documento
    return "\n".join(partes.sort("ordem")["texto"].to_list())


def conferir_extracao(c: Conferencia, secoes: pl.DataFrame, gabarito: list[dict]) -> None:
    """PT: definições verbatim no texto extraído / EN: verbatim definitions in extracted text"""
    itens = dict(conceitos_da_ontologia())
    verbatim = [g for g in gabarito if itens[g["conceito"]].get("confianca") == "verbatim"]
    achados = 0
    for g in verbatim:
        definicao = compacto(texto(itens[g["conceito"]]["definition"]))
        medida = max(cobertura(definicao, compacto(texto_no_lugar(secoes, a))) for a in g["alvos"])
        if g["conceito"] in PARAFRASES_MARCADAS_VERBATIM:
            c.checar(medida < COBERTURA_MINIMA, f"{g['conceito']}: saiu da lista de paráfrases ({medida:.0%}); tire-o de lá")
            continue
        achados += medida >= COBERTURA_MINIMA
        c.checar(medida >= COBERTURA_MINIMA,
                 f"{g['conceito']}: só {medida:.0%} da definição verbatim está no texto extraído de {g['fonte']}")
    print(f"  extração: {achados} de {len(verbatim) - len(PARAFRASES_MARCADAS_VERBATIM)} definições verbatim no lugar "
          f"citado; {len(PARAFRASES_MARCADAS_VERBATIM)} paráfrases marcadas como verbatim, à parte")


# -----------------------------------------------------------------------------
# PT: 2. Trechos
# EN: 2. Chunks
# -----------------------------------------------------------------------------


def conferir_trechos(c: Conferencia, secoes: pl.DataFrame, manifesto_rag: dict) -> None:
    """PT: hash, cobertura, tamanho e contenção na seção / EN: hash, coverage, size, containment"""
    from transformers import AutoTokenizer
    from transformers.utils import logging as logging_do_transformers

    logging_do_transformers.set_verbosity_error()
    texto_da_secao = {(d, s): t for d, s, _titulo, t, _paginas in secoes_em_ordem(secoes)}
    documentos = {d.id for d in DOCUMENTOS_DO_CORPUS}
    c.checar(set(manifesto_rag["documentos"]) == documentos, "manifesto do RAG não lista exatamente o corpus")
    registrados = manifesto.carregar().get("documentos", {})
    for doc in DOCUMENTOS_DO_CORPUS:
        c.checar(manifesto_rag["documentos"].get(doc.id, {}).get("sha256") == registrados.get(doc.arquivo, {}).get("sha256"),
                 f"{doc.id}: sha256 do manifesto do RAG difere do manifesto da ingestão")

    for cand in CANDIDATOS:
        info = manifesto_rag["candidatos"].get(cand.nome)
        if info is None:
            c.checar(False, f"{cand.nome}: fora do rag/manifesto.json")
            continue
        trechos, vetores = carregar_indice(cand)
        c.checar(sha256_do_conteudo(trechos) == info["sha256_trechos"], f"{cand.nome}: sha256 dos trechos difere do manifesto")
        c.checar(vetores.shape == (trechos.height, info["dimensao"]), f"{cand.nome}: embeddings fora da forma dos trechos")
        c.checar(bool(np.allclose(np.linalg.norm(vetores, axis=1), 1, atol=1e-3)), f"{cand.nome}: embeddings não normalizados")
        sem_trecho = documentos - set(trechos["documento"].unique())
        c.checar(not sem_trecho, f"{cand.nome}: documentos sem trecho {sorted(sem_trecho)}")

        tokenizador = AutoTokenizer.from_pretrained(cand.repositorio, revision=cand.revisao)
        maior, fora = 0, 0
        for linha in trechos.iter_rows(named=True):
            n = tokens_de_entrada(tokenizador, cand.prefixo_trecho, linha["texto"])
            maior = max(maior, n)
            fora += linha["texto"] not in texto_da_secao.get((linha["documento"], linha["secao"]), "")
        c.checar(maior <= TAMANHO_MAXIMO_EM_TOKENS, f"{cand.nome}: trecho com {maior} tokens de entrada")
        c.checar(fora == 0, f"{cand.nome}: {fora} trechos fora do texto da própria seção")
        print(f"  {cand.nome}: {trechos.height} trechos, maior com {maior} tokens, {fora} fora da seção")


# -----------------------------------------------------------------------------
# PT: 3. Acerto recalculado no DuckDB
# EN: 3. Hit rate recomputed in DuckDB
# -----------------------------------------------------------------------------

RANKING = f"""
    with similaridade as (
        select q.consulta, t.trecho, list_cosine_similarity(q.vetor, t.vetor) as cosseno
        from consultas q cross join trechos t
    ), ordenado as (
        select consulta, trecho, row_number() over (partition by consulta order by cosseno desc, trecho) as posicao
        from similaridade
    )
    select consulta, trecho, posicao from ordenado where posicao <= {QUANTIDADE_DE_TRECHOS} order by consulta, posicao
"""


def conferir_acerto(c: Conferencia, gabarito: list[dict], avaliacao: dict) -> None:
    """PT: posição do primeiro acerto, pelo DuckDB / EN: first-hit rank via DuckDB"""
    for cand in CANDIDATOS:
        trechos, vetores = carregar_indice(cand)
        consultas = embeddings_das_consultas(cand, [g["consulta"] for g in gabarito])
        # PT: as tabelas entram por executemany, sem pyarrow, que o projeto não tem.
        # EN: tables are loaded with executemany, without pyarrow.
        banco = duckdb.connect()
        banco.execute("create table trechos (trecho integer, vetor float[])")
        banco.executemany("insert into trechos values (?, ?)", list(zip(trechos["trecho"].to_list(), vetores.tolist())))
        banco.execute("create table consultas (consulta integer, vetor float[])")
        banco.executemany("insert into consultas values (?, ?)", list(enumerate(consultas.tolist())))
        trazidos: dict[int, list[int]] = {}
        for consulta, trecho, _posicao in banco.execute(RANKING).fetchall():
            trazidos.setdefault(consulta, []).append(trecho)

        por_numero = {linha["trecho"]: linha for linha in trechos.iter_rows(named=True)}
        esperado = avaliacao["candidatos"][cand.nome]["posicao_por_conceito"]
        divergentes = []
        for i, g in enumerate(gabarito):
            posicao = next((p for p, t in enumerate(trazidos[i], 1) if any(casa(a, por_numero[t]) for a in g["alvos"])), None)
            if posicao != esperado.get(g["conceito"]):
                divergentes.append(f"{g['conceito']} ({posicao} contra {esperado.get(g['conceito'])})")
        acertos = sum(p is not None for p in esperado.values())
        c.checar(not divergentes, f"{cand.nome}: posição diverge do avaliacao.json em {divergentes}")
        print(f"  {cand.nome}: DuckDB reproduz {len(gabarito) - len(divergentes)} de {len(gabarito)} posições, "
              f"{acertos} acertos")


def conferir_escolha(c: Conferencia, manifesto_rag: dict, avaliacao: dict) -> None:
    """PT: escolhido coerente / EN: consistent choice"""
    escolhido = manifesto_rag.get("escolhido") or {}
    c.checar(escolhido == avaliacao.get("escolhido"), "escolhido do manifesto difere do avaliacao.json")
    fixada = {cand.nome: cand.revisao for cand in CANDIDATOS}
    c.checar(fixada.get(escolhido.get("nome")) == escolhido.get("revisao"), "revisão do escolhido difere da fixada")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    secoes = pl.read_parquet(SECOES)
    gabarito = yaml.safe_load(GABARITO_DE_RECUPERACAO.read_text(encoding="utf-8"))["alvos"]
    manifesto_rag = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8"))
    avaliacao = json.loads(AVALIACAO.read_text(encoding="utf-8"))
    print(f"Corpus de {len(manifesto_rag['documentos'])} documentos, gabarito com {len(gabarito)} alvos ({RAIZ.name})")

    c = Conferencia()
    print("\n1. Extração / extraction:")
    conferir_extracao(c, secoes, gabarito)
    print("\n2. Trechos / chunks:")
    conferir_trechos(c, secoes, manifesto_rag)
    print("\n3. Acerto no DuckDB / hit rate in DuckDB:")
    conferir_acerto(c, gabarito, avaliacao)
    conferir_escolha(c, manifesto_rag, avaliacao)

    print(f"\n{c.total} conferências, {len(c.falhas)} falhas / checks, failures")
    for falha in c.falhas:
        print(f"  ERRO {falha}")
    if c.falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
