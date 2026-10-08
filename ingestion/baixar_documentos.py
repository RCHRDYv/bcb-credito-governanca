"""
PT: Baixa os documentos do corpus do RAG (issue #46, ADR 0028) para
    data/raw/documentos/ e registra a identidade de cada um na seção
    documentos do manifesto: URL, tamanho, sha256 e data de extração.

    Os arquivos são pequenos, então cada execução baixa tudo de novo, como o
    SGS e o IBGE, e confere a forma antes de gravar: um PDF começa por %PDF,
    o leiaute é um XLS, o normativo traz o texto, e as páginas do Olinda e
    do portal de dados abertos trazem a documentação. A data de extração só
    muda quando o sha256 muda, então rodar de novo sem republicação deixa o
    manifesto igual. Uma republicação aparece no diff do manifesto e obriga a
    reconstruir o índice (rag.construir confere os sha256).

EN: Downloads the RAG corpus documents into data/raw/documentos/ and records
    each one's identity in the manifest's documentos section: URL, size,
    sha256 and extraction date.

    The files are small, so each run downloads everything again and checks
    its shape before writing. The extraction date only changes when the
    sha256 does, so a rerun without republication leaves the manifest as is.

Uso / Usage:
    uv run python -m ingestion.baixar_documentos
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.request

from ingestion import manifesto
from ingestion.baixar import CABECALHOS
from ingestion.fontes import DIR_RAW_DOCUMENTOS, DOCUMENTOS_DO_CORPUS, DocumentoDoCorpus

# PT: Assinatura de um arquivo OLE2, o formato do .xls antigo.
# EN: OLE2 file signature, the old .xls format.
ASSINATURA_XLS = bytes.fromhex("D0CF11E0A1B11AE1")


def baixar_bytes(url: str) -> tuple[bytes, str | None]:
    """PT: corpo da resposta e Last-Modified / EN: response body and Last-Modified"""
    req = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read(), resp.headers.get("Last-Modified")


def validar(doc: DocumentoDoCorpus, bruto: bytes) -> dict:
    """
    PT: Confere a forma do arquivo pelo tipo e devolve os campos extras do
        manifesto. Erro aqui para a ingestão antes de gravar.
    EN: Checks the file's shape by type and returns extra manifest fields.
        An error here stops ingestion before writing.
    """
    if doc.tipo == "pdf":
        if not bruto.startswith(b"%PDF"):
            raise ValueError(f"{doc.id}: não é PDF / not a PDF")
        return {}
    if doc.tipo == "xls":
        if not bruto.startswith(ASSINATURA_XLS):
            raise ValueError(f"{doc.id}: não é XLS / not an XLS")
        return {}
    if doc.tipo == "normativo":
        conteudo = json.loads(bruto).get("conteudo") or []
        if len(conteudo) != 1 or not (conteudo[0].get("Texto") or "").strip():
            raise ValueError(f"{doc.id}: normativo sem texto / regulation without text")
        norma = conteudo[0]
        return {"titulo_na_fonte": norma.get("Titulo"), "versao_na_fonte": norma.get("VersaoNormativo")}
    if doc.tipo == "olinda":
        if b"$scope.especificacao" not in bruto:
            raise ValueError(f"{doc.id}: página sem a especificação / page without the specification")
        return {}
    if doc.tipo == "ckan":
        pacote = json.loads(bruto)
        if not pacote.get("success") or not pacote["result"].get("notes"):
            raise ValueError(f"{doc.id}: pacote sem descrição / package without description")
        return {}
    raise ValueError(f"{doc.id}: tipo desconhecido / unknown type {doc.tipo}")


def ingerir(doc: DocumentoDoCorpus, registro: dict, extracao: dt.date) -> dict:
    """PT: baixa, valida, grava e devolve a entrada do manifesto / EN: download, validate, store"""
    bruto, publicado_em = baixar_bytes(doc.url)
    extras = validar(doc, bruto)
    novo_hash = hashlib.sha256(bruto).hexdigest()
    (DIR_RAW_DOCUMENTOS / doc.arquivo).write_bytes(bruto)

    if registro.get("sha256") == novo_hash:
        print(f"  = {doc.arquivo}: em dia / up to date")
        data_extracao = registro.get("data_extracao", extracao.isoformat())
    else:
        if registro:
            print(f"  ! {doc.arquivo}: REPUBLICADO / REPUBLISHED")
        print(f"  > {doc.arquivo}: {len(bruto):,} bytes")
        data_extracao = extracao.isoformat()

    entrada = {
        "titulo": doc.titulo,
        "tipo": doc.tipo,
        "url": doc.url,
        "bytes": len(bruto),
        "sha256": novo_hash,
        "data_extracao": data_extracao,
        **extras,
    }
    if publicado_em:
        entrada["last_modified"] = publicado_em
    return entrada


def main() -> None:
    DIR_RAW_DOCUMENTOS.mkdir(parents=True, exist_ok=True)
    dados = manifesto.carregar()
    secao = dados.setdefault("documentos", {})
    extracao = dt.date.today()
    for doc in DOCUMENTOS_DO_CORPUS:
        secao[doc.arquivo] = ingerir(doc, secao.get(doc.arquivo, {}), extracao)
    # PT: documento que saiu da lista sai do manifesto. / EN: dropped documents leave the manifest.
    for nome in sorted(set(secao) - {d.arquivo for d in DOCUMENTOS_DO_CORPUS}):
        print(f"  - {nome}: fora da lista / no longer listed")
        del secao[nome]
    manifesto.salvar(dados)


if __name__ == "__main__":
    main()
