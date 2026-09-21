"""
PT: Etapa 1. Baixa os ZIPs anuais do SCR.data para data/raw/ e registra a
    identidade de cada um no manifesto.

    É idempotente: se o servidor informa a mesma data de publicação e o
    arquivo local tem o mesmo tamanho e o mesmo sha256 registrados, nada é
    baixado. Se o BCB republicou, o arquivo é baixado de novo, e as contagens
    mensais do manifesto são descartadas para forçar a reconversão.

EN: Step 1. Downloads the yearly SCR.data ZIPs into data/raw/ and records
    each file's identity in the manifest.

    It is idempotent: if the server reports the same publication date and
    the local file has the recorded size and sha256, nothing is downloaded.
    If the BCB republished, the file is downloaded again, and the manifest's
    monthly counts are dropped to force reconversion.

Uso / Usage:
    uv run python -m ingestion.baixar
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

from ingestion import manifesto
from ingestion.fontes import ANOS, DIR_RAW, FONTES, Fonte

# PT: O portal do BCB recusa requisições sem User-Agent identificável.
# EN: The BCB portal rejects requests without an identifiable User-Agent.
CABECALHOS = {"User-Agent": "bcb-credito-governanca/0.1 (+https://github.com/RCHRDYv/bcb-credito-governanca)"}
BLOCO = 1024 * 1024


def consultar_servidor(url: str) -> tuple[str, int]:
    """
    PT: Pergunta ao servidor a data de publicação e o tamanho, sem baixar.
    EN: Asks the server for publication date and size, without downloading.
    """
    req = urllib.request.Request(url, method="HEAD", headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.headers["Last-Modified"], int(resp.headers["Content-Length"])


def sha256(caminho: Path) -> str:
    """PT: hash do arquivo em blocos / EN: file hash in chunks"""
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(BLOCO), b""):
            h.update(bloco)
    return h.hexdigest()


def baixar(url: str, destino: Path, tamanho_esperado: int) -> None:
    """
    PT: Baixa para um arquivo temporário e só renomeia se o tamanho bater,
        para que uma queda de conexão nunca deixe um ZIP truncado no lugar
        do bom.
    EN: Downloads to a temporary file and renames only if the size matches,
        so a dropped connection never leaves a truncated ZIP in place of a
        good one.
    """
    parcial = destino.with_suffix(".part")
    req = urllib.request.Request(url, headers=CABECALHOS)
    with urllib.request.urlopen(req, timeout=600) as resp, parcial.open("wb") as f:
        shutil.copyfileobj(resp, f, length=BLOCO)
    if parcial.stat().st_size != tamanho_esperado:
        parcial.unlink()
        raise RuntimeError(f"Download incompleto / incomplete download: {url}")
    parcial.replace(destino)


def processar(fonte: Fonte, ano: int, registro: dict) -> dict:
    """
    PT: Garante que o ZIP local corresponde à versão publicada hoje, e
        devolve a entrada atualizada do manifesto.
    EN: Ensures the local ZIP matches today's published version, and returns
        the updated manifest entry.
    """
    nome = fonte.nome_zip(ano)
    url = fonte.url(ano)
    destino = DIR_RAW / nome
    publicado_em, tamanho = consultar_servidor(url)

    em_dia = (
        destino.exists()
        and destino.stat().st_size == tamanho
        and registro.get("last_modified") == publicado_em
        and registro.get("sha256") == sha256(destino)
    )
    if em_dia:
        print(f"  = {nome}: em dia / up to date ({publicado_em})")
        return registro

    if destino.exists() and destino.stat().st_size == tamanho and not registro:
        # PT: arquivo já baixado antes do manifesto existir; só registra.
        # EN: file downloaded before the manifest existed; just record it.
        print(f"  + {nome}: registrando arquivo local / recording local file")
    else:
        print(f"  v {nome}: baixando / downloading ({tamanho / 1e6:,.0f} MB)")
        baixar(url, destino, tamanho)

    novo_hash = sha256(destino)
    if registro and registro.get("sha256") != novo_hash:
        print(f"  ! {nome}: REPUBLICADO pelo BCB / REPUBLISHED by the BCB")

    return {
        "versao": fonte.versao,
        "ano": ano,
        "url": url,
        "last_modified": publicado_em,
        "bytes": tamanho,
        "sha256": novo_hash,
        # PT: contagens mensais só valem para este sha256; a conversão refaz.
        # EN: monthly counts are only valid for this sha256; conversion redoes them.
        "meses": registro.get("meses", {}) if registro.get("sha256") == novo_hash else {},
    }


def main() -> None:
    DIR_RAW.mkdir(parents=True, exist_ok=True)
    dados = manifesto.carregar()
    for fonte in FONTES:
        for ano in ANOS:
            nome = fonte.nome_zip(ano)
            dados["arquivos"][nome] = processar(fonte, ano, dados["arquivos"].get(nome, {}))
    manifesto.salvar(dados)


if __name__ == "__main__":
    main()
