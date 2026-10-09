"""
PT: A ontologia como bloco de contexto e como fonte da proveniência.

    Itens: todos os dicionários com id das listas de primeiro nível dos
    quatro YAML de ontology/ (conceitos, dimensões, avisos e fontes), mais as
    quebras aninhadas nas dimensões. O id é arquivo.id, o formato do
    gabarito. O cabeçalho esquema de cada arquivo é metadado do arquivo e
    fica de fora.

    Bloco de contexto das condições B e D (decisão de 2026-10-08): os
    itens inteiros, menos o rótulo em inglês e os metadados de acesso à
    fonte. As quebras saem como itens próprios, logo depois da dimensão a que
    pertencem, e não repetidas dentro dela.

    Proveniência (decisão 2 do ADR 0029): o código, e não o modelo, resolve
    os conceitos que a resposta usou, a partir do SQL e do resultado:

    - coluna lida pelo SQL igual à notation de uma métrica ou de um conceito
      das fontes externas, à coluna de uma dimensão, ou citada no afeta de
      uma quebra;
    - literal de texto do SQL, ou célula de texto do resultado, igual ao
      código (notation) ou ao rótulo no dado de uma modalidade, sempre o
      valor inteiro, nunca um pedaço.

    Os avisos que não têm campo de ligação com o dado não aparecem na
    proveniência. É consequência declarada da decisão, e não falha.

EN: The ontology as a context block and as the provenance source. Items are
    every dict with an id in the top-level lists of the four YAML files, plus
    the breaks nested in dimensions, with arquivo.id ids. The B and D block
    carries whole items minus the English label and source-access metadata.
    Provenance is resolved by code from the SQL and its result: columns
    matching a metric, external concept, dimension or break, and whole text
    literals or result cells matching a modality code or label. Warnings
    with no link to the data never appear in provenance, by design.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ingestion.fontes import RAIZ

ONTOLOGIA = RAIZ / "ontology"

# PT: campos que não entram no bloco: o rótulo em inglês e os metadados de
#     acesso à fonte (decisão de 2026-10-08).
# EN: fields left out of the block: English label and source-access metadata.
FORA_DO_BLOCO = {"prefLabel_en", "endereco", "licenca", "leiaute", "formato", "transporte", "publicador",
                 "periodicidade", "documentacao"}

# PT: sufixo das colunas do fato que desfazem a ambiguidade de uma dimensão
#     polimórfica (porte_desambiguado é a dimensão porte).
# EN: suffix of fact columns that disambiguate a polymorphic dimension.
SUFIXO_DESAMBIGUADO = "_desambiguado"


@lru_cache(maxsize=None)
def itens(pasta: Path = ONTOLOGIA) -> tuple[tuple[str, str, dict], ...]:
    """
    PT: (id arquivo.id, nome da lista, item) na ordem dos arquivos e, dentro
        de cada um, na ordem do YAML, com as quebras logo depois da dimensão.
    EN: (arquivo.id, list name, item) in file and YAML order, breaks right
        after their dimension.
    """
    resultado = []
    for arquivo in sorted(pasta.glob("*.yml")):
        conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        for lista, valor in conteudo.items():
            if not isinstance(valor, list):
                continue
            for item in valor:
                if not (isinstance(item, dict) and "id" in item):
                    continue
                resultado.append((f"{arquivo.stem}.{item['id']}", lista, item))
                for quebra in item.get("quebras") or []:
                    resultado.append((f"{arquivo.stem}.{quebra['id']}", "quebras", quebra))
    return tuple(resultado)


def _limpar(valor):
    """
    PT: Tira a quebra de linha que o YAML dobrado deixa no fim dos textos.
    EN: Strips the trailing newline folded YAML leaves at the end of texts.
    """
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, list):
        return [_limpar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items()}
    return valor


def item_do_bloco(id_: str, item: dict) -> dict:
    """
    PT: O item como entra no bloco: o id arquivo.id na frente, sem os campos
        de fora e sem as quebras, que saem como itens próprios.
    EN: The item as it enters the block.
    """
    corpo = {k: _limpar(v) for k, v in item.items() if k not in FORA_DO_BLOCO and k not in ("id", "quebras")}
    return {"id": id_, **corpo}


def bloco(pasta: Path = ONTOLOGIA) -> str:
    """
    PT: O bloco de contexto da ontologia, em YAML, um item por entrada.
    EN: The ontology context block, in YAML, one entry per item.
    """
    entradas = [item_do_bloco(id_, item) for id_, _, item in itens(pasta)]
    return yaml.safe_dump(entradas, allow_unicode=True, sort_keys=False, width=10_000).strip()


# -----------------------------------------------------------------------------
# PT: Proveniência / EN: provenance
# -----------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    return " ".join(str(texto).split()).casefold()


@lru_cache(maxsize=None)
def indices(pasta: Path = ONTOLOGIA) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    PT: Dois índices para resolver conceitos: coluna do dado para ids, e
        valor de texto (código ou rótulo de modalidade) para ids.
    EN: Two lookup tables: data column to ids, and text value (modality code
        or label) to ids.
    """
    por_coluna: dict[str, list[str]] = {}
    por_valor: dict[str, list[str]] = {}
    for id_, lista, item in itens(pasta):
        arquivo = id_.split(".", 1)[0]
        colunas = []
        if arquivo in ("metricas", "fontes_externas") and lista == "conceitos" and item.get("notation"):
            colunas.append(item["notation"])
        if arquivo == "dimensoes" and item.get("coluna"):
            colunas.append(item["coluna"])
        if lista == "quebras":
            colunas += [a for a in item.get("afeta") or [] if isinstance(a, str)]
        for coluna in colunas:
            por_coluna.setdefault(_normalizar(coluna), []).append(id_)
        if arquivo == "modalidades" and lista == "conceitos":
            for chave in ("notation", "rotulo_no_dado"):
                if item.get(chave):
                    por_valor.setdefault(_normalizar(item[chave]), []).append(id_)
    return por_coluna, por_valor


def conceitos_usados(colunas: set[str], literais: set[str], celulas: set[str],
                     pasta: Path = ONTOLOGIA) -> list[dict]:
    """
    PT: Os conceitos que a resposta usou, com rótulo, confiança e fonte lidos
        da ontologia, e onde cada um foi achado: coluna, filtro (literal do
        SQL) ou resultado (célula de texto). Em ordem de id, sem repetição.
    EN: Concepts the answer used, with label, confidence and source read from
        the ontology, and where each was found: column, filter or result.
    """
    por_coluna, por_valor = indices(pasta)
    por_id = {id_: item for id_, _, item in itens(pasta)}
    achados: dict[str, set[str]] = {}

    for coluna in colunas:
        nome = _normalizar(coluna)
        candidatos = por_coluna.get(nome, []) + por_coluna.get(nome.removesuffix(SUFIXO_DESAMBIGUADO), [])
        for id_ in candidatos:
            achados.setdefault(id_, set()).add("coluna")
    for onde, valores in (("filtro", literais), ("resultado", celulas)):
        for valor in valores:
            for id_ in por_valor.get(_normalizar(valor), []):
                achados.setdefault(id_, set()).add(onde)

    return [
        {"id": id_, "rotulo": por_id[id_].get("prefLabel_pt"),
         "confianca": por_id[id_].get("confianca"), "fonte": por_id[id_].get("fonte"),
         "onde": sorted(onde)}
        for id_, onde in sorted(achados.items())
    ]
