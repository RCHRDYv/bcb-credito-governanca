"""
PT: Corta as seções extraídas em trechos, no tokenizador de cada candidato
    (evaluation/hipoteses.yml, rag.trecho):
    - no máximo 512 tokens de entrada do modelo, contando o prefixo do
      trecho e os tokens especiais, para que nada seja truncado em silêncio;
    - 64 tokens de sobreposição entre trechos vizinhos da mesma seção;
    - um trecho nunca cruza a fronteira de uma seção.

    O texto do trecho é um recorte exato do texto da seção, pelos offsets do
    tokenizador, e não o texto decodificado dos tokens. Cada trecho leva
    documento, seção, título da seção e as páginas que cobre.

EN: Cuts the extracted sections into chunks with each candidate's tokenizer:
    at most 512 model input tokens (prefix and special tokens included), 64
    tokens of overlap between neighbours, never crossing a section. The
    chunk text is an exact slice of the section text, by tokenizer offsets.
"""

from __future__ import annotations

import polars as pl

from rag.parametros import SOBREPOSICAO_EM_TOKENS, TAMANHO_MAXIMO_EM_TOKENS

ESQUEMA_DOS_TRECHOS = {
    "trecho": pl.Int64,
    "documento": pl.String,
    "secao": pl.String,
    "titulo": pl.String,
    "pagina": pl.String,
    "pagina_inicial": pl.String,
    "pagina_final": pl.String,
    "tokens_de_entrada": pl.Int64,
    "texto": pl.String,
}


def tokens_de_entrada(tokenizador, prefixo: str, texto: str) -> int:
    """
    PT: Tamanho da entrada que o modelo vê: prefixo, texto e tokens especiais.
    EN: Size of the input the model sees: prefix, text and special tokens.
    """
    return len(tokenizador(prefixo + texto, add_special_tokens=True)["input_ids"])


def secoes_em_ordem(secoes: pl.DataFrame) -> list[tuple[str, str, str, str, list[tuple[int, str | None]]]]:
    """
    PT: Junta os blocos de cada seção, na ordem do documento, e guarda onde
        começa cada página dentro do texto da seção.
    EN: Joins each section's blocks in document order and records where each
        page starts within the section text.
    """
    resultado = []
    chave_atual, titulo, texto, paginas = None, "", "", []
    for linha in secoes.sort(["documento", "ordem"], maintain_order=True).iter_rows(named=True):
        chave = (linha["documento"], linha["secao"])
        if chave != chave_atual:
            if chave_atual:
                resultado.append((*chave_atual, titulo, texto, paginas))
            chave_atual, texto, paginas, titulo = chave, "", [], linha["titulo"]
        if texto:
            texto += "\n"
        paginas.append((len(texto), linha["pagina"]))
        texto += linha["texto"]
    if chave_atual:
        resultado.append((*chave_atual, titulo, texto, paginas))
    return resultado


def paginas_do_intervalo(paginas: list[tuple[int, str | None]], inicio: int, fim: int) -> tuple[str | None, str | None]:
    """PT: primeira e última página que o recorte [inicio, fim) toca / EN: first and last page touched"""
    tocadas = [p for i, (comeco, p) in enumerate(paginas)
               if comeco < fim and (paginas[i + 1][0] if i + 1 < len(paginas) else float("inf")) > inicio]
    return (tocadas[0], tocadas[-1]) if tocadas else (None, None)


def cortar_secao(tokenizador, prefixo: str, texto: str) -> list[tuple[int, int, int]]:
    """
    PT: Devolve (início, fim, tokens de entrada) de cada trecho da seção. A
        janela começa com o espaço que sobra depois do prefixo e dos tokens
        especiais, e encolhe se o recorte, tokenizado de novo, passar do
        limite. O próximo trecho começa 64 tokens antes do fim do anterior.
    EN: Returns (start, end, input tokens) for each chunk of the section.
    """
    codificado = tokenizador(texto, add_special_tokens=False, return_offsets_mapping=True)
    offsets = codificado["offset_mapping"]
    total = len(offsets)
    if total == 0:
        return []
    custo_fixo = tokens_de_entrada(tokenizador, prefixo, "")
    janela = TAMANHO_MAXIMO_EM_TOKENS - custo_fixo

    trechos, inicio = [], 0
    while True:
        fim = min(inicio + janela, total)
        while True:
            a, b = offsets[inicio][0], offsets[fim - 1][1]
            n = tokens_de_entrada(tokenizador, prefixo, texto[a:b])
            if n <= TAMANHO_MAXIMO_EM_TOKENS:
                break
            fim -= 1
            if fim <= inicio:
                raise SystemExit(f"ERRO nenhum token cabe em {TAMANHO_MAXIMO_EM_TOKENS} com o prefixo / no token fits")
        trechos.append((a, b, n))
        if fim >= total:
            return trechos
        inicio = max(fim - SOBREPOSICAO_EM_TOKENS, inicio + 1)


def cortar(secoes: pl.DataFrame, tokenizador, prefixo: str) -> pl.DataFrame:
    """
    PT: Trechos do corpus inteiro para um tokenizador, numerados na ordem do
        documento e da seção.
    EN: Chunks of the whole corpus for one tokenizer, numbered in order.
    """
    linhas = []
    for documento, secao, titulo, texto, paginas in secoes_em_ordem(secoes):
        for a, b, n in cortar_secao(tokenizador, prefixo, texto):
            primeira, ultima = paginas_do_intervalo(paginas, a, b)
            pagina = primeira if primeira == ultima else f"{primeira}-{ultima}"
            linhas.append({"trecho": len(linhas), "documento": documento, "secao": secao, "titulo": titulo,
                           "pagina": pagina, "pagina_inicial": primeira, "pagina_final": ultima,
                           "tokens_de_entrada": n, "texto": texto[a:b]})
    return pl.DataFrame(linhas, schema=ESQUEMA_DOS_TRECHOS)
