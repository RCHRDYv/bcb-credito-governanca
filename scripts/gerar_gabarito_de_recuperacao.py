"""
PT: Gera evaluation/recuperacao.yml, o gabarito de recuperação do RAG
    (issue #46, ADR 0028): para cada conceito da ontologia, a consulta e o
    lugar do corpus de onde a definição saiu, para medir se a busca o traz.

    A consulta é "O que é <prefLabel_pt>?", decidida em
    2026-10-07. O alvo sai do campo fonte do conceito, que cita o documento
    por um apelido (ingestion/fontes.py, DOCUMENTOS_DO_CORPUS) e o lugar por
    página ("p. 20", "pp. 20 e 21", "pp. 20 a 22"), seção ("seção 3.x",
    "introdução"), anexo ou bloco do leiaute ("Anexo 12", "bloco c") ou
    tabela do CNPJ ("tabela Empresas"). Sem lugar, o alvo é o documento
    inteiro, e o arquivo diz isso no campo granularidade.

    Um conceito fica fora do denominador, com o motivo escrito, quando:
    - é uma lacuna (confianca: lacuna), sem definição na fonte;
    - a fonte é uma medição no dado ou numa API, e não um documento;
    - a fonte é método do projeto;
    - a fonte não está no corpus (IBGE, CONCLA, os .md do projeto).

    O arquivo não se edita à mão: o CI regera e compara
    (scripts/validar_recuperacao.py).

EN: Generates the RAG retrieval answer key: for each ontology concept, the
    query and the corpus location its definition came from. The query is
    "O que é <prefLabel_pt>?". The target comes from the concept's fonte
    field. Concepts whose source is a gap, a data measurement, the
    project's own method or outside the corpus are listed as excluded, with
    the reason. CI regenerates and compares this file.

Uso / Usage:
    uv run python -m scripts.gerar_gabarito_de_recuperacao
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ingestion.fontes import DOCUMENTOS_DO_CORPUS
from scripts.gerar_seeds_da_ontologia import texto

RAIZ = Path(__file__).resolve().parents[1]
ONTOLOGIA = RAIZ / "ontology"
SAIDA = RAIZ / "evaluation" / "recuperacao.yml"

# PT: Listas da ontologia que guardam conceitos. As dimensões removidas na V2
#     não entram: não existem no dado nem na pergunta.
# EN: Ontology lists that hold concepts. Dimensions removed in V2 stay out.
LISTAS_DE_CONCEITOS = ("conceitos", "dimensoes")
CONSULTA = "O que é {rotulo}?"

# PT: Partes da fonte que não são documento.
# EN: Parts of the source that are not a document.
MEDICAO = re.compile(r"^(dado\b|medição|resposta da api|api do sgs, consulta|nome dos arquivos|períodos publicados|metadados d)", re.I)
METODO_DO_PROJETO = re.compile(r"^(método do projeto|docs/|ver docs/)", re.I)
FORA_DO_CORPUS = re.compile(r"(ibge|sidra|concla)", re.I)

CABECALHO = """\
# =============================================================================
# PT: Gabarito de recuperação do RAG (issue #46, ADR 0028). GERADO por
#     scripts/gerar_gabarito_de_recuperacao.py a partir dos campos fonte da
#     ontologia. Não edite à mão: o CI regera e compara.
#
#     alvos: para cada conceito, a consulta e onde a definição está no
#     corpus. Um alvo acerta quando um dos 5 trechos trazidos é do documento
#     e cai na página ou na seção citada (ou em qualquer lugar do documento,
#     quando a granularidade é documento).
#     excluidos: conceitos fora do denominador, com o motivo.
#
# EN: RAG retrieval answer key. GENERATED from the ontology's fonte fields;
#     do not edit by hand. A target is hit when one of the 5 retrieved
#     chunks is from the document and falls on the cited page or section.
# =============================================================================

"""


def conceitos_da_ontologia() -> list[tuple[str, dict]]:
    """PT: (arquivo.id, item) de cada conceito / EN: (file.id, item) per concept"""
    conceitos = []
    for caminho in sorted(ONTOLOGIA.glob("*.yml")):
        documento = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        for lista in LISTAS_DE_CONCEITOS:
            for item in documento.get(lista) or []:
                if isinstance(item, dict) and "id" in item:
                    conceitos.append((f"{caminho.stem}.{item['id']}", item))
    return conceitos


# -----------------------------------------------------------------------------
# PT: Leitura da citação.
# EN: Reading the citation.
# -----------------------------------------------------------------------------


def documento_citado(parte: str) -> str | None:
    """
    PT: Id do documento cujo apelido abre a parte da citação. Vence o
        apelido mais longo, para "Instruções 3040" não virar "Instruções".
    EN: Id of the document whose alias opens the citation part; the longest
        alias wins.
    """
    melhor, tamanho = None, 0
    for doc in DOCUMENTOS_DO_CORPUS:
        for apelido in doc.apelidos:
            if parte.casefold().startswith(apelido.casefold()) and len(apelido) > tamanho:
                melhor, tamanho = doc.id, len(apelido)
    return melhor


def paginas_citadas(parte: str) -> list[int]:
    """
    PT: "p. 20", "pp. 20 e 21", "pp. 20 a 22, 27 a 28, 35" viram a lista de
        páginas.
    EN: Page citations become the list of pages.
    """
    m = re.search(r"\bpp?\.\s*([\d\s,ae]+)", parte)
    if not m:
        return []
    paginas: list[int] = []
    for pedaco in re.split(r",|\be\b", m.group(1)):
        numeros = [int(n) for n in re.findall(r"\d+", pedaco)]
        if len(numeros) == 2 and " a " in f" {pedaco} ":
            paginas.extend(range(numeros[0], numeros[1] + 1))
        else:
            paginas.extend(numeros)
    return sorted(set(paginas))


def secoes_citadas(documento: str, parte: str) -> list[str]:
    """
    PT: Seções no formato que rag.extrair dá a elas. A tabela do CNPJ sai
        como "tabela NOME" e o bloco do leiaute como "Doc3040, bloco x",
        porque o título no documento é mais longo ("DADOS DO SIMPLES",
        "(NR1) c. Informações de GARANTIAS"); rag.avaliar.casa_secao
        resolve a correspondência.
    EN: Sections in the format rag.extrair gives them; CNPJ tables and
        layout blocks are resolved by rag.avaliar.casa_secao.
    """
    secoes: list[str] = []
    if documento.startswith("metodologia"):
        if re.search(r"introdução", parte, re.I):
            secoes.append("1")
        if m := re.search(r"seç(?:ão|ões)\s+([\d.a-z,\se]+)", parte):
            secoes.extend(re.findall(r"\d+(?:\.[a-z])?", m.group(1)))
    elif documento == "leiaute_3040":
        secoes.extend(f"Anexo {n}" for n in re.findall(r"Anexo (\d+)", parte))
        secoes.extend(f"Doc3040, bloco {b}" for b in re.findall(r"bloco ([a-z])\b", parte))
        if "HistoricoAtualizacoes" in parte:
            secoes.append("HistoricoAtualizacoes")
    elif documento == "cnpj_leiaute":
        secoes.extend(f"tabela {t.upper()}" for t in re.findall(r"tabela (\w+)", parte))
    elif documento == "pix_api" and (m := re.search(r"recursos?\s+(.+)$", parte)):
        secoes.extend(re.findall(r"[A-Z]\w+", m.group(1)))
    return secoes


def alvo_da_parte(parte: str) -> dict | None:
    """PT: alvo de uma parte da citação, ou None / EN: target of one citation part, or None"""
    documento = documento_citado(parte)
    if documento is None:
        return None
    alvo: dict = {"documento": documento}
    if paginas := paginas_citadas(parte):
        alvo["paginas"] = paginas
    if secoes := secoes_citadas(documento, parte):
        alvo["secoes"] = secoes
    alvo["granularidade"] = "pagina" if "paginas" in alvo else "secao" if "secoes" in alvo else "documento"
    return alvo


def classificar(item: dict) -> tuple[list[dict], str | None]:
    """
    PT: Devolve os alvos do conceito, ou nenhum alvo e o motivo da exclusão.
        A fonte se divide por ";" e por "Ver ", e cada parte com documento
        do corpus vira um alvo. Acerta quem trouxer qualquer um deles.
    EN: Returns the concept's targets, or none and the exclusion reason.
    """
    if item.get("confianca") == "lacuna" or not item.get("definition"):
        return [], "lacuna: a fonte não traz a definição"
    fonte = texto(item.get("fonte"))
    partes = [p.strip(" .") for p in re.split(r";|\.\s+Ver\s+", fonte) if p.strip(" .")]

    # PT: "Anexo 3" e "HistoricoAtualizacoes" soltos herdam o leiaute.
    # EN: Bare "Anexo 3" and "HistoricoAtualizacoes" belong to the layout.
    alvos = []
    for parte in partes:
        alvo = alvo_da_parte(parte)
        if alvo and alvo not in alvos:
            alvos.append(alvo)
    if alvos:
        return alvos, None

    if all(METODO_DO_PROJETO.match(p) for p in partes):
        return [], "método do projeto, sem documento do corpus"
    if any(FORA_DO_CORPUS.search(p) for p in partes):
        return [], "fonte fora do corpus (IBGE, SIDRA, CONCLA)"
    if all(MEDICAO.match(p) or METODO_DO_PROJETO.match(p) for p in partes):
        return [], "medição no dado ou numa API, e não documento"
    return [], "citação sem documento do corpus reconhecível"


def consulta(item: dict) -> str:
    """PT: "O que é <prefLabel_pt>?", sem pontuação final no rótulo / EN: the query"""
    return CONSULTA.format(rotulo=texto(item["prefLabel_pt"]).rstrip(" .;:"))


def gerar() -> dict:
    """PT: conteúdo do gabarito / EN: answer-key content"""
    alvos, excluidos = [], []
    conceitos = conceitos_da_ontologia()
    for referencia, item in conceitos:
        encontrados, motivo = classificar(item)
        registro = {"conceito": referencia, "fonte": texto(item.get("fonte"))}
        if encontrados:
            alvos.append({**registro, "consulta": consulta(item), "alvos": encontrados})
        else:
            excluidos.append({**registro, "motivo": motivo})
    return {
        "metadata": {
            "issue": 46,
            "decidido_em": "2026-10-07",
            "consulta": CONSULTA.replace("{rotulo}", "<prefLabel_pt>"),
            "conceitos_na_ontologia": len(conceitos),
            "denominador": len(alvos),
            "excluidos": len(excluidos),
        },
        "alvos": alvos,
        "excluidos": excluidos,
    }


def como_texto(conteudo: dict) -> str:
    """PT: o YAML exato que vai para o arquivo / EN: the exact YAML written"""
    corpo = yaml.safe_dump(conteudo, allow_unicode=True, sort_keys=False, width=100, default_flow_style=None)
    return CABECALHO + corpo


def main() -> None:
    conteudo = gerar()
    SAIDA.write_text(como_texto(conteudo), encoding="utf-8", newline="\n")
    m = conteudo["metadata"]
    print(f"  > {SAIDA.relative_to(RAIZ)}: {m['denominador']} alvos, {m['excluidos']} excluídos, "
          f"de {m['conceitos_na_ontologia']} conceitos")


if __name__ == "__main__":
    main()
