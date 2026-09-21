"""
PT: Etapa 3. Garante o schema e o volume no Unity Catalog e envia os
    Parquets de data/landing/ para o volume, mantendo a mesma estrutura de
    pastas.

    É idempotente: um arquivo só é enviado se ainda não existe no volume, se
    o tamanho difere ou se a cópia local é mais nova que a remota.

EN: Step 3. Ensures the Unity Catalog schema and volume exist and uploads
    the Parquet files from data/landing/ to the volume, keeping the same
    folder layout. Idempotent: a file is uploaded only if missing remotely,
    if its size differs, or if the local copy is newer than the remote one.

Uso / Usage:
    uv run python -m ingestion.enviar_volume
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.catalog import VolumeType

from ingestion.databricks import cliente
from ingestion.fontes import CAMINHO_VOLUME, CATALOGO, DIR_LANDING, SCHEMA, VOLUME

ENVIOS_SIMULTANEOS = 6


def garantir_destino(w: WorkspaceClient) -> None:
    """PT: cria schema e volume se faltarem / EN: creates schema and volume if missing"""
    try:
        w.schemas.get(f"{CATALOGO}.{SCHEMA}")
    except NotFound:
        w.schemas.create(
            name=SCHEMA,
            catalog_name=CATALOGO,
            comment="SCR.data do Banco Central: bronze, staging, intermediate e marts do projeto bcb-credito-governanca",
        )
        print(f"  + schema {CATALOGO}.{SCHEMA} criado / created")

    try:
        w.volumes.read(f"{CATALOGO}.{SCHEMA}.{VOLUME}")
    except NotFound:
        w.volumes.create(
            catalog_name=CATALOGO,
            schema_name=SCHEMA,
            name=VOLUME,
            volume_type=VolumeType.MANAGED,
            comment="Parquet só texto convertido dos ZIPs oficiais. Linhagem em ingestion/manifesto.json",
        )
        print(f"  + volume {CAMINHO_VOLUME} criado / created")


def precisa_enviar(w: WorkspaceClient, local: Path, remoto: str) -> bool:
    """
    PT: Compara com a cópia remota. O tamanho sozinho não basta: uma
        republicação do BCB pode, em tese, gerar um Parquet de mesmo tamanho.
        Por isso a data de modificação também conta.
    EN: Compares with the remote copy. Size alone is not enough: a BCB
        republication could, in theory, yield a same-size Parquet, so the
        modification time counts too.
    """
    try:
        meta = w.files.get_metadata(remoto)
    except NotFound:
        return True
    if meta.content_length != local.stat().st_size:
        return True
    if not meta.last_modified:
        return False
    remoto_em = parsedate_to_datetime(meta.last_modified).timestamp()
    return local.stat().st_mtime > remoto_em


def enviar(w: WorkspaceClient, local: Path, remoto: str) -> str:
    """PT: envia um arquivo / EN: uploads one file"""
    with local.open("rb") as f:
        w.files.upload(remoto, f, overwrite=True)
    return f"  ^ {remoto} ({local.stat().st_size / 1e6:,.1f} MB)"


def main() -> None:
    w = cliente()
    garantir_destino(w)

    arquivos = sorted(DIR_LANDING.rglob("*.parquet"))
    if not arquivos:
        raise SystemExit("Nada em data/landing: rode ingestion.converter_parquet / nothing to upload")

    pendentes = {
        local: f"{CAMINHO_VOLUME}/{local.relative_to(DIR_LANDING).as_posix()}"
        for local in arquivos
    }
    pendentes = {l: r for l, r in pendentes.items() if precisa_enviar(w, l, r)}
    print(f"  {len(pendentes)} a enviar, {len(arquivos) - len(pendentes)} já no volume / already there", flush=True)

    # PT: Cada envio usa uma única conexão, que medida ficou em cerca de
    #     0,45 MB/s. Vários envios simultâneos aproveitam melhor a banda.
    # EN: Each upload uses a single connection, measured at about 0.45 MB/s.
    #     Several concurrent uploads make better use of the bandwidth.
    with ThreadPoolExecutor(max_workers=ENVIOS_SIMULTANEOS) as pool:
        futuros = [pool.submit(enviar, w, l, r) for l, r in pendentes.items()]
        for futuro in as_completed(futuros):
            print(futuro.result(), flush=True)


if __name__ == "__main__":
    main()
