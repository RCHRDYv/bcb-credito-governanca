"""
PT: O contrato dos arquivos do site do dashboard, lido pela exportação e pela
    validação (#66).

    O contrato mora em dashboard/contrato-dos-dados.yml e é a fonte única do
    que cada JSON traz. Este módulo concentra o que a exportação e a
    validação precisam fazer igual:
    - ler o contrato;
    - converter cada valor pela unidade da coluna, com a precisão fixa;
    - gravar o JSON sempre do mesmo jeito, para a mesma entrada dar os mesmos
      bytes;
    - montar o ontologia.json e o manifesto.json, que não saem de um mart.

    Nada aqui fala com o Databricks. Por isso a validação roda no CI, sem
    credencial.

EN: The dashboard site's file contract, read by the export and by the
    validation. This module holds what both must do the same way: read the
    contract, convert values by column unit with fixed precision, write JSON
    deterministically, and build ontologia.json and manifesto.json. Nothing
    here talks to Databricks, so validation runs in CI with no credential.
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CONTRATO = RAIZ / "dashboard" / "contrato-dos-dados.yml"
DESTINO = RAIZ / "dashboard" / "public" / "data"
DBT_PROJECT = RAIZ / "dbt" / "dbt_project.yml"

ONTOLOGIA = "ontologia.json"
MANIFESTO = "manifesto.json"

# PT: Os parâmetros da decisão que o manifesto registra, pelo nome no dbt.
# EN: Decision parameters recorded in the manifest, by dbt var name.
PARAMETROS_DA_DECISAO = (
    "decisao_carteira_minima",
    "decisao_meses_de_tendencia",
    "decisao_minimo_de_ufs",
)

# PT: Precisão por unidade (ver `formato.precisao` no contrato).
# EN: Precision by unit.
UNIDADES_EM_REAIS = {"reais", "reais_por_empresa"}
UNIDADES_FRACIONARIAS = {"fracao", "diferenca_de_fracao", "variacao_relativa", "indice"}
UNIDADES_INTEIRAS = {"empresas", "contagem", "meses"}
UM_REAL = Decimal(1)
SEIS_CASAS = Decimal("0.000001")

# PT: Formato das datas / EN: date formats
DATA = re.compile(r"\d{4}-\d{2}-\d{2}")
MES = re.compile(r"\d{4}-\d{2}")

# PT: Em que lista da ontologia cada tipo de registro mora. As quebras da
#     série ficam aninhadas dentro da dimensão de data-base.
# EN: Which ontology list each record type lives in. Series breaks are
#     nested inside the data-base dimension.
TIPO_POR_LISTA = {
    "conceitos": "conceito",
    "dimensoes": "dimensao",
    "fontes": "fonte_de_dado",
    "avisos": "aviso",
    "quebras": "quebra",
}


# -----------------------------------------------------------------------------
# PT: Leitura / EN: reading
# -----------------------------------------------------------------------------


def carregar_contrato() -> dict:
    """PT: o contrato como dicionário / EN: the contract as a dict"""
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


def arquivos_gerados(contrato: dict) -> list[str]:
    """
    PT: Os nomes dos arquivos que a exportação grava em dashboard/public/data:
        os dos marts, o ontologia.json e o manifesto.json. A malha das UFs
        fica fora: mora em public/geo, é gravada por
        scripts/gerar_malha_do_dashboard.py e conferida à parte (#67).
    EN: File names the export writes: the marts', ontologia.json and
        manifesto.json. The state mesh lives in public/geo, is written by
        scripts/gerar_malha_do_dashboard.py and checked separately (#67).
    """
    return [spec["arquivo"] for spec in contrato["arquivos"]] + [ONTOLOGIA, MANIFESTO]


def visoes_de(contrato: dict, arquivo: str) -> list[int]:
    """PT: as visões que usam o arquivo / EN: views that use the file"""
    for spec in contrato["arquivos"] + contrato["auxiliares"]:
        if spec["arquivo"] == arquivo:
            return list(spec["visoes"])
    raise KeyError(arquivo)


def parametros_da_decisao() -> dict[str, int]:
    """
    PT: Os parâmetros da decisão, lidos do dbt_project.yml, que é onde o
        modelo os lê.
    EN: Decision parameters, read from dbt_project.yml, where the model reads
        them.
    """
    variaveis = yaml.safe_load(DBT_PROJECT.read_text(encoding="utf-8"))["vars"]
    return {nome: int(variaveis[nome]) for nome in PARAMETROS_DA_DECISAO}


# -----------------------------------------------------------------------------
# PT: Conversão / EN: conversion
# -----------------------------------------------------------------------------


def _arredondar(texto: str, passo: Decimal) -> Decimal:
    """
    PT: Arredonda a partir do texto que a API devolve, sem passar por float,
        para o resultado não depender da representação binária.
    EN: Rounds from the API text, without going through float.
    """
    return Decimal(texto).quantize(passo, rounding=ROUND_HALF_UP)


def converter(valor: str | None, coluna: dict):
    """
    PT: Converte um valor da API do Databricks, que chega como texto, para o
        tipo e a precisão que o contrato pede para a coluna.
    EN: Converts one Databricks API value, which arrives as text, to the
        column's contract type and precision.
    """
    if valor is None:
        return None
    unidade = coluna["unidade"]
    if unidade in UNIDADES_EM_REAIS:
        return int(_arredondar(valor, UM_REAL))
    if unidade in UNIDADES_FRACIONARIAS:
        numero = float(_arredondar(valor, SEIS_CASAS))
        # PT: sem "-0.0" no arquivo / EN: no negative zero in the file
        return 0.0 if numero == 0 else numero
    if unidade in UNIDADES_INTEIRAS:
        return int(valor)
    if unidade == "booleano":
        return valor == "true"
    if unidade == "data":
        return valor[:10]
    if unidade == "mes":
        return valor[:7]
    return valor


# -----------------------------------------------------------------------------
# PT: Gravação / EN: writing
# -----------------------------------------------------------------------------


def _json(valor, compacto: bool = False) -> str:
    """PT: JSON em UTF-8 legível / EN: readable UTF-8 JSON"""
    if compacto:
        return json.dumps(valor, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(valor, ensure_ascii=False, indent=2)


def texto_de_dados(arquivo: str, data_base: str, colunas: dict[str, list]) -> str:
    """
    PT: O texto de um arquivo de dados, com uma coluna por linha. Assim o
        diff da PR mostra qual coluna mudou, sem um arquivo de uma linha só.
    EN: A data file's text, one column per line, so the PR diff shows which
        column changed.
    """
    linhas = [
        "{",
        f'  "arquivo": {_json(arquivo)},',
        f'  "data_base": {_json(data_base)},',
        '  "colunas": {',
    ]
    nomes = list(colunas)
    for indice, nome in enumerate(nomes):
        virgula = "," if indice < len(nomes) - 1 else ""
        linhas.append(f"    {_json(nome)}: {_json(colunas[nome], compacto=True)}{virgula}")
    linhas += ["  }", "}"]
    return "\n".join(linhas) + "\n"


def texto_de_registro(conteudo: dict) -> str:
    """PT: ontologia e manifesto, indentados / EN: indented auxiliary files"""
    return _json(conteudo) + "\n"


def gravar(caminho: Path, texto: str) -> None:
    """PT: grava em UTF-8 com fim de linha \\n / EN: writes UTF-8 with LF"""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8", newline="\n")


def sha256(conteudo: bytes) -> str:
    """PT: o sha256 em hexadecimal / EN: hex sha256"""
    return hashlib.sha256(conteudo).hexdigest()


# -----------------------------------------------------------------------------
# PT: ontologia.json / EN: ontologia.json
# -----------------------------------------------------------------------------


def _itens_da_lista(lista: str, valores, arquivo: str, itens: dict) -> None:
    """
    PT: Guarda os itens com id de uma lista conhecida e desce nas listas
        conhecidas de dentro deles, como as quebras da data-base.
    EN: Keeps the items with an id and walks into known nested lists.
    """
    if lista not in TIPO_POR_LISTA or not isinstance(valores, list):
        return
    for item in valores:
        if isinstance(item, dict) and "id" in item:
            itens[f"ontology/{arquivo}#{item['id']}"] = (lista, item)
            for chave, aninhados in item.items():
                _itens_da_lista(chave, aninhados, arquivo, itens)


def _itens_da_ontologia() -> dict[str, tuple[str, dict]]:
    """
    PT: Todos os itens com id da ontologia, pela referência que o contrato
        usa ("ontology/arquivo.yml#id"), com a lista de onde vieram.
    EN: Every ontology item with an id, by the contract's reference.
    """
    itens: dict[str, tuple[str, dict]] = {}
    for caminho in sorted((RAIZ / "ontology").glob("*.yml")):
        documento = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        for lista, valores in documento.items():
            _itens_da_lista(lista, valores, caminho.name, itens)
    return itens


def _texto_limpo(texto: str | None) -> str | None:
    """PT: junta as linhas do YAML dobrado / EN: collapses folded YAML text"""
    return None if texto is None else " ".join(str(texto).split())


def _registro(referencia: str, lista: str, item: dict) -> dict:
    """
    PT: Um registro do ontologia.json. Nos avisos e nas quebras, a definição
        é a descrição, porque é o campo que eles têm. Na quebra, a nota de
        escopo é a consequência, e a data da quebra vai junto.
    EN: One ontologia.json record. Warnings and breaks use their description
        as the definition; a break's scope note is its consequence, and its
        date comes along.
    """
    registro = {
        "ref": referencia,
        "id": item["id"],
        "tipo": TIPO_POR_LISTA[lista],
        "rotulo": item.get("prefLabel_pt"),
        "definicao": _texto_limpo(item.get("definition") or item.get("descricao")),
        "fonte": _texto_limpo(item.get("fonte")),
        "confianca": item.get("confianca"),
        "nota_de_escopo": _texto_limpo(item.get("scopeNote") or item.get("consequencia")),
    }
    if lista == "quebras":
        registro["data"] = item["data"]
    if lista == "conceitos" and item.get("tipo") == "modalidade":
        registro["codigo"] = str(item["notation"])
    return registro


def montar_ontologia(contrato: dict, codigos_de_modalidade: set[str]) -> dict:
    """
    PT: O ontologia.json: um registro por conceito citado nas colunas do
        contrato, mais um por modalidade presente nos dados (decidido em
        2026-09-27), e o mapa de coluna para definição, que é o que deixa o
        site ir do número à definição (RF-G07). Coluna definida por ADR
        aponta para o ADR, como no contrato.
    EN: ontologia.json: one record per concept cited in the contract, one per
        modality present in the data, and the column to definition map that
        lets the site go from a number to its definition.
    """
    itens = _itens_da_ontologia()
    citadas = sorted(
        {
            coluna["definicao"]
            for spec in contrato["arquivos"]
            for coluna in spec["colunas"]
            if "#" in coluna["definicao"] and coluna["definicao"].startswith("ontology/")
        }
    )
    faltando = [ref for ref in citadas if ref not in itens]
    if faltando:
        raise ValueError(f"Conceitos citados que não existem na ontologia: {faltando}")

    modalidades = {
        str(item["notation"]): ref
        for ref, (lista, item) in itens.items()
        if lista == "conceitos" and item.get("tipo") == "modalidade"
    }
    sem_conceito = sorted(codigos_de_modalidade - set(modalidades))
    if sem_conceito:
        raise ValueError(f"Modalidades dos dados sem conceito na ontologia: {sem_conceito}")

    referencias = citadas + sorted(modalidades[codigo] for codigo in codigos_de_modalidade)
    return {
        "arquivo": ONTOLOGIA,
        "conceitos": [_registro(ref, *itens[ref]) for ref in referencias],
        "colunas": {
            spec["arquivo"]: {coluna["nome"]: coluna["definicao"] for coluna in spec["colunas"]}
            for spec in contrato["arquivos"]
        },
    }


def codigos_de_modalidade(conteudos: dict[str, dict]) -> set[str]:
    """
    PT: Os códigos de modalidade que aparecem em qualquer arquivo de dados.
    EN: Modality codes present in any data file.
    """
    return {
        codigo
        for conteudo in conteudos.values()
        for codigo in conteudo.get("colunas", {}).get("codigo_modalidade", [])
    }


# -----------------------------------------------------------------------------
# PT: manifesto.json / EN: manifesto.json
# -----------------------------------------------------------------------------


def montar_manifesto(contrato: dict, data_base: str, textos: dict[str, str]) -> dict:
    """
    PT: O manifesto: a data-base, os parâmetros da decisão e, por arquivo, as
        linhas, o sha256 e as visões que o usam. Não guarda data de geração,
        para a mesma entrada dar o mesmo arquivo. As visões servem ao
        orçamento de carga, que soma o peso por visão sem ler o YAML.
    EN: The manifest: data-base, decision parameters and, per file, rows,
        sha256 and the views using it. No generation date, so the same input
        gives the same file.
    """
    arquivos = []
    for nome in arquivos_gerados(contrato):
        if nome == MANIFESTO:
            continue
        conteudo = json.loads(textos[nome])
        colunas = conteudo.get("colunas")
        linhas = len(next(iter(colunas.values()))) if colunas else len(conteudo["conceitos"])
        arquivos.append(
            {
                "arquivo": nome,
                "linhas": linhas,
                "sha256": sha256(textos[nome].encode("utf-8")),
                "visoes": visoes_de(contrato, nome),
            }
        )
    return {
        "arquivo": MANIFESTO,
        "versao_do_contrato": contrato["versao"],
        "data_base": data_base,
        "parametros_da_decisao": parametros_da_decisao(),
        "visoes_do_manifesto": visoes_de(contrato, MANIFESTO),
        "arquivos": arquivos,
    }
