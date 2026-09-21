"""
PT: Leitura e escrita do manifesto da ingestão.

    O manifesto registra a identidade de cada arquivo anual baixado (data de
    publicação informada pelo servidor, tamanho e sha256) e, depois da
    conversão, quantas linhas cada mês tem. Não contém dado, por isso é
    versionado. Ele cumpre dois papéis:

    1. Detectar republicação. O BCB reescreve arquivos antigos sem aviso
       (planilha_2024.zip foi republicado em 2026-09-15). Quando isso
       acontece, o sha256 muda e o diff do manifesto no git mostra.
    2. Servir de gabarito para a verificação no Databricks: a contagem de
       linhas por mês no bronze precisa bater com a registrada aqui.

EN: Reading and writing the ingestion manifest.

    The manifest records the identity of each yearly file downloaded (the
    publication date reported by the server, size and sha256) and, after
    conversion, how many rows each month has. It holds no data, so it is
    versioned. It serves two purposes:

    1. Detecting republication. The BCB rewrites old files without notice
       (planilha_2024.zip was republished on 2026-09-15). When that happens,
       the sha256 changes and the manifest diff in git shows it.
    2. Acting as the answer key for the Databricks check: the row count per
       month in bronze must match the one recorded here.
"""

from __future__ import annotations

import json

from ingestion.fontes import MANIFESTO


def carregar() -> dict:
    """PT: lê o manifesto, ou devolve um vazio / EN: loads the manifest, or an empty one"""
    if MANIFESTO.exists():
        return json.loads(MANIFESTO.read_text(encoding="utf-8"))
    return {"arquivos": {}}


def salvar(manifesto: dict) -> None:
    """
    PT: grava com chaves ordenadas, para que o diff no git mostre só o que
        mudou de fato.
    EN: writes with sorted keys, so the git diff shows only real changes.
    """
    texto = json.dumps(manifesto, ensure_ascii=False, indent=2, sort_keys=True)
    MANIFESTO.write_text(texto + "\n", encoding="utf-8", newline="\n")
