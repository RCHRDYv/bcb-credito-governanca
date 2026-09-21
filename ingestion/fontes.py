"""
PT: Configuração única da ingestão: quais arquivos buscar, onde guardar e
    para onde enviar. Todo módulo da ingestão lê daqui, para que mudar o
    recorte temporal ou o destino seja uma alteração em um lugar só.
EN: Single source of ingestion configuration: which files to fetch, where
    to store them and where to send them. Every ingestion module reads from
    here, so changing the time scope or the destination is a one-place edit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# -----------------------------------------------------------------------------
# PT: Fontes oficiais
# EN: Official sources
# -----------------------------------------------------------------------------

URL_BASE = "https://www.bcb.gov.br/pda/desig"

# PT: Recorte do projeto: 2024 em diante (docs/cadeia-normativa.md, decisão 1.3).
# EN: Project scope: 2024 onwards (docs/cadeia-normativa.md, decision 1.3).
ANOS = (2024, 2025, 2026)


@dataclass(frozen=True)
class Fonte:
    """
    PT: Uma versão do SCR.data. A V2 é a fonte principal; a V1 é a fonte
        legada, mantida para reconciliação e para a conformação do ADR 0003.
    EN: One SCR.data version. V2 is the main source; V1 is the legacy
        source, kept for reconciliation and for the ADR 0003 conformance.
    """

    versao: str  # PT: "v1" ou "v2" / EN: "v1" or "v2"
    prefixo: str  # PT: prefixo do arquivo no portal / EN: file prefix on the portal
    colunas_esperadas: int  # PT: contrato mínimo de esquema / EN: minimal schema contract

    def nome_zip(self, ano: int) -> str:
        return f"{self.prefixo}_{ano}.zip"

    def url(self, ano: int) -> str:
        return f"{URL_BASE}/{self.nome_zip(ano)}"


FONTES = (
    Fonte(versao="v2", prefixo="scrdata", colunas_esperadas=24),
    Fonte(versao="v1", prefixo="planilha", colunas_esperadas=23),
)

# -----------------------------------------------------------------------------
# PT: Caminhos locais. data/ inteiro está no .gitignore.
# EN: Local paths. The whole data/ folder is gitignored.
# -----------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ / "data" / "raw"
DIR_LANDING = RAIZ / "data" / "landing"

# PT: O manifesto é versionado: não contém dado, só a identidade de cada
#     arquivo baixado. O histórico do git mostra quando o BCB republicou.
# EN: The manifest is versioned: it holds no data, only the identity of each
#     downloaded file. Git history shows when the BCB republished one.
MANIFESTO = RAIZ / "ingestion" / "manifesto.json"

# -----------------------------------------------------------------------------
# PT: Destino no Databricks. Nenhum identificador do workspace fica no código:
#     o perfil vem do ~/.databrickscfg e o warehouse é descoberto em tempo de
#     execução, ou informado por variável de ambiente.
# EN: Databricks destination. No workspace identifier lives in the code: the
#     profile comes from ~/.databrickscfg and the warehouse is discovered at
#     runtime, or given through an environment variable.
# -----------------------------------------------------------------------------

PERFIL = os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID")  # PT: opcional / EN: optional
CATALOGO = "workspace"
SCHEMA = "bcb_scr"
VOLUME = "raw"
CAMINHO_VOLUME = f"/Volumes/{CATALOGO}/{SCHEMA}/{VOLUME}"
