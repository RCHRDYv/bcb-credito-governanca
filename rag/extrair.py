"""
PT: Extrai o texto dos documentos do corpus e o divide nas seções que o
    próprio documento declara (ADR 0028). Cada seção sai como uma lista de
    blocos (documento, seção, título, página, texto), na ordem do documento,
    e é dentro da seção que rag.trechos corta os trechos: um trecho nunca
    cruza a fronteira de uma seção (evaluation/hipoteses.yml, rag.trecho).

    Seção, por tipo de documento:
    - Metodologias do SCR.data: os títulos numerados ("2. Conceitos") e as
      alíneas ("d. Tipo de cliente"), que é como a ontologia os cita
      ("Metodologia V2, seção 2.d");
    - Instruções do 3040: as entradas do sumário da página 2 (A, A.1, ...,
      D.5, E, ..., I), achadas no corpo na página que o sumário indica;
    - leiaute do 3040: na aba Anexo, cada "Anexo N"; na aba Doc3040, cada
      bloco acima de um cabeçalho "Campo"; as outras abas, inteiras;
    - leiaute do CNPJ: cada tabela (EMPRESAS, ESTABELECIMENTOS, ...);
    - normativos: CAPÍTULO, Seção e Subseção, quando a norma os tem; senão,
      a norma inteira. O texto riscado é redação revogada e fica de fora;
    - PIX: a descrição do serviço e cada recurso, com as propriedades;
    - SGS: a descrição da série e cada recurso do portal.

    O texto antes do primeiro título vira a seção "preambulo". Página: a do
    PDF; o nome da aba na planilha; nula no HTML e no JSON (decisão de
    2026-10-07). Ruído de página (cabeçalho corrido, "Página N") sai, e o
    resto do texto fica como o documento traz.

EN: Extracts the corpus documents' text and splits it into the sections the
    document itself declares. Each section is a list of blocks (document,
    section, title, page, text) in document order; rag.trechos cuts chunks
    inside a section, so a chunk never crosses a section boundary. Page is
    the PDF page, the sheet name for the spreadsheet, and null for HTML and
    JSON. Running headers are dropped; struck-through (repealed) text in
    regulations is dropped.

Uso / Usage:
    uv run --group rag python -m rag.extrair
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import polars as pl
import xlrd
from pypdf import PdfReader

from ingestion.fontes import DIR_RAW_DOCUMENTOS, DOCUMENTOS_DO_CORPUS, DocumentoDoCorpus
from rag.parametros import DIR_RAG, SECOES

PREAMBULO = "preambulo"


@dataclass
class Bloco:
    """PT: um pedaço de seção numa página / EN: a piece of a section on one page"""

    documento: str
    secao: str
    titulo: str
    pagina: str | None
    texto: str


# -----------------------------------------------------------------------------
# PT: Limpeza de texto comum a todos os tipos.
# EN: Text cleanup shared by all types.
# -----------------------------------------------------------------------------

RUIDO_DE_PAGINA = (
    re.compile(r"^\s*SCR\s*[–-]\s*Sistema de Informações de Crédito\s*[–-]\s*Instruções de Preenchimento\s*$"),
    re.compile(r"^\s*Página\s+\d+(\s+de\s+\d+)?\s*$"),
)
PONTILHADO = re.compile(r"(?:\.\s?){4,}")


def limpar_linhas(texto: str) -> list[str]:
    """
    PT: Junta espaços repetidos, tira linhas vazias e o ruído de página.
    EN: Collapses repeated spaces, drops empty lines and page noise.
    """
    linhas = []
    for linha in texto.splitlines():
        linha = PONTILHADO.sub(" ... ", linha.replace("\xa0", " "))
        linha = re.sub(r"[ \t]+", " ", linha).strip()
        if linha and not any(r.match(linha) for r in RUIDO_DE_PAGINA):
            linhas.append(linha)
    return linhas


def normalizar(texto: str) -> str:
    """PT: forma para comparar títulos / EN: form used to compare titles"""
    return re.sub(r"\s+", " ", texto).strip().casefold()


# -----------------------------------------------------------------------------
# PT: Divisor genérico: percorre (página, linha) e abre seção nova quando uma
#     função reconhece um título.
# EN: Generic splitter: walks (page, line) and opens a new section whenever
#     a function recognizes a heading.
# -----------------------------------------------------------------------------


def dividir(documento: str, linhas: list[tuple[str | None, str]], titulo_de) -> list[Bloco]:
    """
    PT: titulo_de(indice, pagina, linha) devolve (secao, titulo) quando a
        linha abre seção, ou None. Linhas da mesma seção e página viram um
        bloco só.
    EN: titulo_de(index, page, line) returns (section, title) when the line
        opens a section, or None. Lines of the same section and page form
        one block.
    """
    blocos: list[Bloco] = []
    secao, titulo = PREAMBULO, ""
    for i, (pagina, linha) in enumerate(linhas):
        achado = titulo_de(i, pagina, linha)
        if achado:
            secao, titulo = achado
        atual = blocos[-1] if blocos else None
        if atual and atual.secao == secao and atual.pagina == pagina and not achado:
            atual.texto += "\n" + linha
        else:
            blocos.append(Bloco(documento, secao, titulo, pagina, linha))
    return blocos


def linhas_do_pdf(caminho: Path) -> list[tuple[str, str]]:
    """PT: (página, linha) de um PDF / EN: (page, line) from a PDF"""
    leitor = PdfReader(caminho)
    return [(str(n), linha) for n, pagina in enumerate(leitor.pages, 1) for linha in limpar_linhas(pagina.extract_text())]


# -----------------------------------------------------------------------------
# PT: Metodologias do SCR.data.
# EN: SCR.data methodologies.
# -----------------------------------------------------------------------------

TITULO_NUMERADO = re.compile(r"^(\d{1,2})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ].*)$")
TITULO_ALINEA = re.compile(r"^([a-z])\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ].*)$")


def extrair_metodologia(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: Seção "N" para o título numerado e "N.x" para a alínea. A alínea só
        conta se for a próxima letra da sequência, o que barra item de
        lista que pareça título.
    EN: Section "N" for numbered titles and "N.x" for lettered items, which
        only count when they are the next letter in sequence.
    """
    estado = {"numero": None, "letra": None}

    def titulo_de(_i, _pagina, linha):
        if m := TITULO_NUMERADO.match(linha):
            numero = int(m.group(1))
            if estado["numero"] is None or numero == estado["numero"] + 1:
                estado.update(numero=numero, letra=None)
                return str(numero), linha
        if (m := TITULO_ALINEA.match(linha)) and estado["numero"] is not None:
            letra = m.group(1)
            proxima = "a" if estado["letra"] is None else chr(ord(estado["letra"]) + 1)
            if letra == proxima:
                estado["letra"] = letra
                return f"{estado['numero']}.{letra}", linha
        return None

    return dividir(doc.id, linhas_do_pdf(caminho), titulo_de)


# -----------------------------------------------------------------------------
# PT: Instruções de Preenchimento do 3040, pelo sumário.
# EN: Doc 3040 filling instructions, by the table of contents.
# -----------------------------------------------------------------------------

# PT: o pontilhado até o número da página pode ter um ponto só ("(intramês) . 111").
# EN: the leader up to the page number may be a single dot.
ENTRADA_DO_SUMARIO = re.compile(r"^(?:([A-I])|(\d))\.\s+(.+?)[\s.]*\s(\d+)$")


def sumario_das_instrucoes(linhas: list[tuple[str, str]]) -> list[tuple[str, str, int]]:
    """
    PT: Lê o sumário da página 2 e devolve (seção, título, página). Uma
        entrada que quebra em duas linhas é juntada antes de ler.
    EN: Reads the table of contents on page 2 and returns (section, title,
        page). An entry broken over two lines is joined first.
    """
    da_pagina_2 = [linha for pagina, linha in linhas if pagina == "2"]
    juntas: list[str] = []
    for linha in da_pagina_2:
        if juntas and not re.match(r"^(?:[A-I]|\d)\.\s", linha):
            juntas[-1] += " " + linha
        else:
            juntas.append(linha)
    entradas, letra = [], None
    for linha in juntas:
        m = ENTRADA_DO_SUMARIO.match(linha)
        if not m:
            continue
        if m.group(1):
            letra = m.group(1)
            secao = letra
        else:
            secao = f"{letra}.{m.group(2)}"
        entradas.append((secao, m.group(3).strip(), int(m.group(4))))
    return entradas


def extrair_instrucoes(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: Cada entrada do sumário abre seção na primeira linha, da página
        indicada em diante (até duas páginas depois), que começa pelo título
        dela. Entrada que não se acha no corpo para a extração.
    EN: Each table-of-contents entry opens a section at the first line, from
        the stated page on (up to two pages later), that starts with its
        title. An entry not found in the body stops extraction.
    """
    linhas = linhas_do_pdf(caminho)
    entradas = sumario_das_instrucoes(linhas)
    if len(entradas) < 15:
        raise SystemExit(f"ERRO {doc.id}: sumário com {len(entradas)} entradas / table of contents too short")

    aberturas: dict[int, tuple[str, str]] = {}
    inicio_da_busca = 0
    for secao, titulo, pagina in entradas:
        prefixo = normalizar(f"{secao.split('.')[-1]}. {titulo}")[:30]
        for i in range(inicio_da_busca, len(linhas)):
            pagina_da_linha = int(linhas[i][0])
            if pagina_da_linha < pagina or pagina_da_linha > pagina + 2:
                continue
            candidata = normalizar(linhas[i][1] + " " + (linhas[i + 1][1] if i + 1 < len(linhas) else ""))
            if candidata.startswith(prefixo):
                aberturas[i] = (secao, linhas[i][1])
                inicio_da_busca = i + 1
                break
        else:
            raise SystemExit(f"ERRO {doc.id}: título do sumário não achado / heading not found: {secao} {titulo} (p. {pagina})")

    return dividir(doc.id, linhas, lambda i, _p, _l: aberturas.get(i))


# -----------------------------------------------------------------------------
# PT: Leiaute do CNPJ: tabelas em maiúsculas, acima de um cabeçalho "Campo".
# EN: CNPJ layout: upper-case table names above a "Campo" header.
# -----------------------------------------------------------------------------


def extrair_cnpj(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: O nome da tabela é a linha logo acima do cabeçalho "Campo". Quando
        ele quebra em duas linhas ("QUALIFICAÇÕES DE" / "SÓCIOS"), a linha
        de cima também está em maiúsculas e vem depois do separador ".", e
        as duas se juntam.
    EN: The table name is the line right above the "Campo" header. When it
        breaks over two lines, the upper one is also upper-case and follows
        the "." separator, and both are joined.
    """
    linhas = linhas_do_pdf(caminho)
    aberturas: dict[int, tuple[str, str]] = {}
    for i in range(1, len(linhas)):
        if not linhas[i][1].startswith("Campo"):
            continue
        inicio, nome = i - 1, linhas[i - 1][1]
        anterior = linhas[i - 2][1] if i >= 2 else ""
        if i >= 3 and anterior != "." and anterior == anterior.upper() and linhas[i - 3][1] == ".":
            inicio, nome = i - 2, f"{anterior} {nome}"
        aberturas[inicio] = (nome, nome)
    return dividir(doc.id, linhas, lambda i, _p, _l: aberturas.get(i))


# -----------------------------------------------------------------------------
# PT: Leiaute do 3040 (XLS).
# EN: Doc 3040 layout (XLS).
# -----------------------------------------------------------------------------


def celula(valor) -> str:
    """PT: texto de uma célula; 20.0 vira 20 / EN: cell text; 20.0 becomes 20"""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def extrair_leiaute(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: Cada linha da planilha vira uma linha de texto, com as células não
        vazias separadas por " | ". A página é o nome da aba.
    EN: Each sheet row becomes a text line, non-empty cells joined by " | ".
        The page is the sheet name.
    """
    livro = xlrd.open_workbook(caminho)
    blocos: list[Bloco] = []
    for aba in livro.sheets():
        linhas = []
        for r in range(aba.nrows):
            celulas = [celula(c.value) for c in aba.row(r)]
            celulas = [re.sub(r"\s+", " ", c) for c in celulas if c]
            if celulas:
                linhas.append((aba.name, " | ".join(celulas)))

        def titulo_de(i, _pagina, linha, aba=aba, linhas=linhas):
            # PT: o título pode vir com marca de nota: "(NR1) Anexo 12: Garantias".
            # EN: the title may carry a note mark.
            if aba.name == "Anexo" and (m := re.match(r"^(?:\(NR\d*\)?\s*)?Anexo (\d+)\s*:", linha)):
                return f"Anexo {m.group(1)}", linha
            if aba.name == "Doc3040" and i + 1 < len(linhas) and linhas[i + 1][1].startswith("Campo |"):
                return f"Doc3040: {linha.split(' | ')[0]}", linha
            if aba.name not in ("Anexo", "Doc3040") and i == 0:
                return aba.name, linha
            return None

        for bloco in dividir(doc.id, linhas, titulo_de):
            if bloco.secao == PREAMBULO:
                bloco.secao = f"{aba.name}: {PREAMBULO}"
            blocos.append(bloco)
    return blocos


# -----------------------------------------------------------------------------
# PT: Normativos: JSON da API de normativos, com o texto em HTML.
# EN: Regulations: JSON from the regulations API, with HTML text.
# -----------------------------------------------------------------------------


class ParagrafosHtml(HTMLParser):
    """
    PT: Junta o texto por parágrafo e pula o que está riscado (<s>, <strike>,
        <del>), que é redação revogada.
    EN: Collects text per paragraph and skips struck-through text, which is
        repealed wording.
    """

    QUEBRAS = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4"}
    RISCADOS = {"s", "strike", "del"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragrafos: list[str] = []
        self.atual: list[str] = []
        self.riscado = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.RISCADOS:
            self.riscado += 1
        elif tag in self.QUEBRAS:
            self.fechar()

    def handle_endtag(self, tag):
        if tag in self.RISCADOS:
            self.riscado = max(0, self.riscado - 1)
        elif tag in self.QUEBRAS:
            self.fechar()

    def handle_data(self, data):
        if not self.riscado:
            self.atual.append(data)

    def fechar(self) -> None:
        texto = re.sub(r"\s+", " ", "".join(self.atual).replace("​", "")).strip()
        if texto:
            self.paragrafos.append(texto)
        self.atual = []


def texto_do_html(trecho_html: str) -> list[str]:
    """PT: parágrafos de um HTML / EN: paragraphs of an HTML snippet"""
    leitor = ParagrafosHtml()
    leitor.feed(html.unescape(trecho_html.replace("&#58;", ":")))
    leitor.fechar()
    return leitor.paragrafos


# PT: Os rótulos podem vir entre aspas e com letra de inclusão, quando a norma
#     transcreve o texto que acrescenta a outra ("CAPÍTULO III-A, na CMN 5.255).
# EN: Labels may be quoted and carry an insertion letter when the regulation
#     transcribes text it adds to another one.
ROTULO = r'^["“]?{nome}\s+([IVXLC]+(?:-[A-Z])?)\b'
CAPITULO = re.compile(ROTULO.format(nome="CAP[ÍI]TULO"))
SECAO_DE_NORMA = re.compile(ROTULO.format(nome="Se[çc][ãa]o"))
SUBSECAO_DE_NORMA = re.compile(ROTULO.format(nome="Subse[çc][ãa]o"))


def extrair_normativo(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: A seção é o nível mais fino que a norma declara: "CAPÍTULO N",
        "CAPÍTULO N, Seção M" ou "CAPÍTULO N, Seção M, Subseção K". Norma sem
        nenhum desses rótulos vira uma seção só.
    EN: The section is the finest level the regulation declares: chapter,
        section or subsection. A regulation without them is one section.
    """
    norma = json.loads(caminho.read_text(encoding="utf-8"))["conteudo"][0]
    paragrafos = texto_do_html(norma["Texto"])
    estado: dict[str, str | None] = {"capitulo": None, "secao": None}

    def titulo_de(_i, _pagina, linha):
        if m := CAPITULO.match(linha):
            estado.update(capitulo=f"CAPÍTULO {m.group(1)}", secao=None)
            return estado["capitulo"], linha
        if m := SECAO_DE_NORMA.match(linha):
            estado["secao"] = ", ".join(filter(None, [estado["capitulo"], f"Seção {m.group(1)}"]))
            return estado["secao"], linha
        if m := SUBSECAO_DE_NORMA.match(linha):
            acima = estado["secao"] or estado["capitulo"]
            return ", ".join(filter(None, [acima, f"Subseção {m.group(1)}"])), linha
        return None

    blocos = dividir(doc.id, [(None, p) for p in paragrafos], titulo_de)
    if all(b.secao == PREAMBULO for b in blocos):
        for b in blocos:
            b.secao, b.titulo = "norma", norma["Titulo"]
    return blocos


# -----------------------------------------------------------------------------
# PT: Documentação do PIX (Olinda) e do SGS (portal de dados abertos).
# EN: PIX (Olinda) and SGS (open data portal) documentation.
# -----------------------------------------------------------------------------


def extrair_olinda(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: A especificação do serviço vem em JSON dentro do script da página.
        Uma seção para o serviço e uma por recurso, com cada propriedade em
        uma linha: nome, título e descrição.
    EN: The service specification is JSON inside the page script. One
        section for the service and one per resource.
    """
    pagina = caminho.read_text(encoding="utf-8")
    inicio = pagina.index("{", pagina.index("$scope.especificacao"))
    especificacao, _ = json.JSONDecoder().raw_decode(pagina[inicio:])
    servico = especificacao["servico"]["localizacao"]
    blocos = [Bloco(doc.id, servico["nome"], servico["titulo"], None, f"{servico['titulo']}\n{servico['descricao']}")]
    for recurso in especificacao["recursos"]:
        local = recurso["localizacao"]
        linhas = [f"{local['nome']}: {local['titulo']}", local.get("descricao") or ""]
        for prop in recurso["tipo"].get("propriedades", []):
            p = prop["localizacao"]
            linhas.append(f"{p['nome']} | {p.get('titulo', '')} | {p.get('descricao', '')} | {prop.get('tipo', '')}")
        texto = "\n".join(l for l in linhas if l.strip())
        blocos.append(Bloco(doc.id, local["nome"], local["titulo"], None, texto))
    return blocos


def extrair_ckan(doc: DocumentoDoCorpus, caminho: Path) -> list[Bloco]:
    """
    PT: Uma seção para a descrição da série e uma por recurso do portal.
    EN: One section for the series description and one per portal resource.
    """
    pacote = json.loads(caminho.read_text(encoding="utf-8"))["result"]
    blocos = [Bloco(doc.id, "descricao", pacote["title"], None, "\n".join(limpar_linhas(f"{pacote['title']}\n{pacote['notes']}")))]
    for recurso in pacote["resources"]:
        texto = "\n".join(limpar_linhas(f"{recurso['name']}\n{recurso.get('description') or ''}"))
        blocos.append(Bloco(doc.id, recurso["name"], recurso["name"], None, texto))
    return blocos


# -----------------------------------------------------------------------------
# PT: Despacho por documento e gravação.
# EN: Per-document dispatch and writing.
# -----------------------------------------------------------------------------


def extrair_documento(doc: DocumentoDoCorpus) -> list[Bloco]:
    """PT: blocos de um documento / EN: blocks of one document"""
    caminho = DIR_RAW_DOCUMENTOS / doc.arquivo
    if doc.id in ("metodologia_v1", "metodologia_v2"):
        return extrair_metodologia(doc, caminho)
    if doc.id == "instrucoes_3040":
        return extrair_instrucoes(doc, caminho)
    if doc.id == "cnpj_leiaute":
        return extrair_cnpj(doc, caminho)
    extratores = {"xls": extrair_leiaute, "normativo": extrair_normativo, "olinda": extrair_olinda, "ckan": extrair_ckan}
    return extratores[doc.tipo](doc, caminho)


def conferir_secoes_contiguas(documento: str, blocos: list[Bloco]) -> None:
    """
    PT: Cada seção é um trecho contínuo do documento. Uma seção que volta
        depois de outra teria a mesma chave em dois lugares, e o corte e o
        gabarito não saberiam qual é qual; a extração para.
    EN: Each section is one contiguous run. A section key that comes back
        after another would be ambiguous, so extraction stops.
    """
    vistas: list[str] = []
    for b in blocos:
        if not vistas or vistas[-1] != b.secao:
            if b.secao in vistas:
                raise SystemExit(f"ERRO {documento}: a seção '{b.secao}' aparece em dois lugares / section repeats")
            vistas.append(b.secao)


def extrair_tudo() -> pl.DataFrame:
    """
    PT: Extrai o corpus inteiro e grava data/rag/secoes.parquet, com a ordem
        dos blocos dentro de cada documento.
    EN: Extracts the whole corpus and writes data/rag/secoes.parquet.
    """
    linhas = []
    for doc in DOCUMENTOS_DO_CORPUS:
        blocos = extrair_documento(doc)
        conferir_secoes_contiguas(doc.id, blocos)
        for ordem, b in enumerate(blocos):
            linhas.append({"documento": b.documento, "ordem": ordem, "secao": b.secao, "titulo": b.titulo,
                           "pagina": b.pagina, "texto": b.texto})
    tabela = pl.DataFrame(linhas, schema={"documento": pl.String, "ordem": pl.Int64, "secao": pl.String,
                                          "titulo": pl.String, "pagina": pl.String, "texto": pl.String})
    DIR_RAG.mkdir(parents=True, exist_ok=True)
    tabela.write_parquet(SECOES, compression="zstd")
    return tabela


def main() -> None:
    tabela = extrair_tudo()
    resumo = (tabela.group_by("documento", maintain_order=True)
              .agg(pl.col("secao").n_unique().alias("secoes"), pl.len().alias("blocos"),
                   pl.col("texto").str.len_chars().sum().alias("caracteres")))
    for linha in resumo.iter_rows(named=True):
        print(f"  > {linha['documento']}: {linha['secoes']} seções, {linha['blocos']} blocos, {linha['caracteres']:,} caracteres")


if __name__ == "__main__":
    main()
