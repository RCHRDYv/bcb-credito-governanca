"""
PT: Etapa 1 do CNPJ. Baixa os ZIPs do CNPJ aberto da Receita Federal para
    data/raw/cnpj/{retrato}/ e registra a identidade de cada um no
    manifesto, na seção "cnpj".

    A fonte é a Receita, e o transporte é o espelho da Casa dos Dados
    (ESPELHO_CNPJ em ingestion/fontes.py, e ADR 0009). Por isso cada arquivo
    passa por duas conferências:
    1. **Contra o espelho:** o tamanho baixado bate com o anunciado, e o
       sha256 fica registrado no manifesto.
    2. **Contra a Receita:** quando o servidor oficial responde, a listagem
       dele por WebDAV dá o tamanho de cada arquivo, que precisa bater com o
       do espelho. Se o servidor oficial não responde, a conferência fica
       marcada como pendente no manifesto e é refeita na próxima execução.
       Tamanho divergente interrompe a ingestão.

    Um download interrompido continua de onde parou, pelo cabeçalho Range, e
    o arquivo só troca de nome quando está completo. É idempotente como o
    download do SCR (ingestion/baixar.py).

EN: CNPJ step 1. Downloads Receita Federal's open CNPJ ZIPs and records each
    file's identity in the manifest's "cnpj" section. Receita is the source
    and the Casa dos Dados mirror is the transport, so every file is checked
    twice: against the mirror (size and sha256) and, when the official
    server answers, against Receita's WebDAV listing (size). If the official
    server is down, the check is marked pending and redone next run; a size
    mismatch stops ingestion. Interrupted downloads resume through Range.

Uso / Usage:
    uv run python -m ingestion.baixar_cnpj
"""

from __future__ import annotations

import base64
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from ingestion import manifesto
from ingestion.baixar import BLOCO, CABECALHOS, sha256
from ingestion.fontes import (
    DIR_RAW_CNPJ,
    ESPELHO_CNPJ,
    RECEITA_COMPARTILHAMENTO,
    RECEITA_WEBDAV,
    RETRATO_DO_MODELO,
    RETRATOS_DE_VALIDACAO,
    TABELAS_CNPJ,
)

# PT: Três conexões com o espelho, que é servido por CDN e aguenta bem.
# EN: Three connections to the mirror, which is CDN-backed.
DOWNLOADS_SIMULTANEOS = 3

# PT: Uma leitura parada por mais que isso conta como falha, e o download
#     retoma pelo Range. Desiste só depois de FALHAS_SEM_PROGRESSO falhas
#     seguidas sem nenhum byte novo.
# EN: A read stalled longer than this counts as a failure and resumes
#     through Range. Gives up after FALHAS_SEM_PROGRESSO consecutive failures
#     with no new byte.
ESPERA_MAXIMA_POR_LEITURA = 60
FALHAS_SEM_PROGRESSO = 5

# PT: Quanto esperar pelo servidor oficial antes de marcar a conferência
#     como pendente. Ele não é necessário para baixar, então não vale travar.
# EN: How long to wait for the official server before marking the check
#     pending. It is not needed for downloading.
ESPERA_PELO_OFICIAL = 30

# PT: O WebDAV público identifica o link, e não uma pessoa: o usuário é o
#     identificador do compartilhamento e a senha é vazia.
# EN: Public WebDAV identifies the link, not a person: the user is the share
#     identifier and the password is empty.
AUTENTICACAO_DO_LINK = {
    "Authorization": "Basic " + base64.b64encode(f"{RECEITA_COMPARTILHAMENTO}:".encode()).decode()
}


@dataclass(frozen=True)
class ArquivoRemoto:
    """PT: um ZIP de um retrato / EN: one ZIP of a snapshot"""

    retrato: str  # PT: "2026-09" / EN: same
    pasta_no_espelho: str  # PT: "2026-09-14", o dia da extração / EN: extraction day
    nome: str
    bytes: int
    last_modified: str

    @property
    def chave(self) -> str:
        """PT: chave no manifesto / EN: manifest key"""
        return f"{self.retrato}/{self.nome}"

    @property
    def url(self) -> str:
        return f"{ESPELHO_CNPJ}/{self.pasta_no_espelho}/{self.nome}"

    @property
    def url_oficial(self) -> str:
        return f"{RECEITA_WEBDAV}/{self.retrato}/{self.nome}"

    @property
    def destino(self) -> Path:
        return DIR_RAW_CNPJ / self.retrato / self.nome


# -----------------------------------------------------------------------------
# PT: Listagens
# EN: Listings
# -----------------------------------------------------------------------------

def ler(url: str, metodo: str = "GET", cabecalhos: dict | None = None, espera: int = 120):
    """PT: requisição com o User-Agent do projeto / EN: request with the project's User-Agent"""
    req = urllib.request.Request(url, method=metodo, headers={**CABECALHOS, **(cabecalhos or {})})
    return urllib.request.urlopen(req, timeout=espera)


def pasta_do_retrato(retrato: str) -> str:
    """
    PT: O espelho nomeia as pastas pelo dia da extração. Cada mês tem uma só,
        e ela é encontrada pelo prefixo "AAAA-MM".
    EN: The mirror names folders by extraction day; each month has one.
    """
    with ler(f"{ESPELHO_CNPJ}/") as resp:
        pastas = re.findall(r'href="(\d{4}-\d{2}-\d{2})/"', resp.read().decode())
    do_mes = [p for p in pastas if p.startswith(retrato)]
    if len(do_mes) != 1:
        raise RuntimeError(f"Espelho: esperado uma pasta para {retrato}, há {do_mes}")
    return do_mes[0]


def listar_no_espelho(retrato: str) -> list[ArquivoRemoto]:
    """
    PT: Lista os ZIPs do retrato no espelho e pega tamanho e data de cada um
        por HEAD, porque o índice HTML mostra o tamanho arredondado.
    EN: Lists the snapshot's ZIPs on the mirror and gets exact size and date
        through HEAD, since the HTML index rounds sizes.
    """
    pasta = pasta_do_retrato(retrato)
    with ler(f"{ESPELHO_CNPJ}/{pasta}/") as resp:
        nomes = sorted(set(re.findall(r'href="([A-Za-z]+\d?\.zip)"', resp.read().decode())))

    arquivos = []
    for nome in nomes:
        with ler(f"{ESPELHO_CNPJ}/{pasta}/{nome}", metodo="HEAD") as resp:
            arquivos.append(
                ArquivoRemoto(
                    retrato=retrato,
                    pasta_no_espelho=pasta,
                    nome=nome,
                    bytes=int(resp.headers["Content-Length"]),
                    last_modified=resp.headers["Last-Modified"],
                )
            )
    return arquivos


def tamanhos_oficiais(retrato: str) -> dict[str, int] | None:
    """
    PT: Tamanho de cada arquivo no servidor da Receita, por PROPFIND. Devolve
        None se o servidor não responde, o que não impede o download.
    EN: Each file's size on Receita's server, via PROPFIND. Returns None if
        the server does not answer, which does not block the download.
    """
    try:
        with ler(
            f"{RECEITA_WEBDAV}/{retrato}/",
            metodo="PROPFIND",
            cabecalhos={**AUTENTICACAO_DO_LINK, "Depth": "1"},
            espera=ESPERA_PELO_OFICIAL,
        ) as resp:
            raiz = ET.fromstring(resp.read())
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None

    ns = {"d": "DAV:"}
    tamanhos = {}
    for item in raiz.findall("d:response", ns):
        tamanho = item.find(".//d:getcontentlength", ns)
        if tamanho is not None:
            nome = item.find("d:href", ns).text.rstrip("/").split("/")[-1]
            tamanhos[nome] = int(tamanho.text)
    return tamanhos


def selecionar(arquivos: list[ArquivoRemoto]) -> list[ArquivoRemoto]:
    """
    PT: Fica só com as tabelas que o projeto usa, e só nos retratos em que
        cada uma é necessária (ingestion/fontes.py).
    EN: Keeps only the tables the project uses, in the snapshots where each
        is needed.
    """
    return [
        a for a in arquivos
        for t in TABELAS_CNPJ
        if t.e_desta_tabela(a.nome) and a.retrato in t.retratos()
    ]


# -----------------------------------------------------------------------------
# PT: Download
# EN: Download
# -----------------------------------------------------------------------------

def baixar_com_retomada(arquivo: ArquivoRemoto) -> None:
    """
    PT: Baixa para um .part e continua de onde parou se ele já existir. Só
        renomeia quando o tamanho bate com o anunciado, para que um ZIP
        truncado nunca ocupe o lugar do bom.
    EN: Downloads into a .part file and resumes if it exists. Renames only
        when the size matches, so a truncated ZIP never replaces a good one.
    """
    parcial = arquivo.destino.with_suffix(".part")
    parcial.parent.mkdir(parents=True, exist_ok=True)

    falhas_seguidas = 0
    while falhas_seguidas < FALHAS_SEM_PROGRESSO:
        ja_tem = parcial.stat().st_size if parcial.exists() else 0
        if ja_tem == arquivo.bytes:
            break
        cabecalhos = {"Range": f"bytes={ja_tem}-"} if ja_tem else {}
        erro = None
        try:
            with ler(arquivo.url, cabecalhos=cabecalhos, espera=ESPERA_MAXIMA_POR_LEITURA) as resp, parcial.open("ab") as f:
                # PT: 200 em vez de 206 quer dizer que o servidor ignorou o
                #     Range e mandou tudo: recomeça o arquivo.
                # EN: 200 instead of 206 means Range was ignored: restart.
                if ja_tem and resp.status == 200:
                    f.truncate(0)
                while bloco := resp.read(BLOCO):
                    f.write(bloco)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as falha:
            erro = falha

        # PT: O progresso é medido depois de toda tentativa, com ou sem erro:
        #     o servidor também pode fechar a conexão cedo sem acusar nada.
        # EN: Progress is measured after every attempt, error or not.
        agora = parcial.stat().st_size if parcial.exists() else 0
        if agora < arquivo.bytes:
            falhas_seguidas = 0 if agora > ja_tem else falhas_seguidas + 1
            motivo = erro or "conexão encerrada antes do fim / connection closed early"
            print(f"  ! {arquivo.chave}: parou em {agora / 1e6:,.0f} MB, retomando / resuming ({motivo})", flush=True)

    if not parcial.exists() or parcial.stat().st_size != arquivo.bytes:
        raise RuntimeError(f"Download incompleto / incomplete download: {arquivo.chave}")
    parcial.replace(arquivo.destino)


def conferencia_oficial(arquivo: ArquivoRemoto, oficiais: dict[str, int] | None) -> str:
    """
    PT: "conferido" se o tamanho bate com o da Receita, "pendente" se o
        servidor oficial não respondeu. Tamanho diferente interrompe tudo:
        o espelho estaria servindo outro arquivo.
    EN: "conferido" if the size matches Receita's, "pendente" if the official
        server did not answer. A different size stops everything.
    """
    if oficiais is None:
        return "pendente"
    if arquivo.nome not in oficiais:
        raise RuntimeError(f"{arquivo.chave}: não existe no servidor da Receita / not on Receita's server")
    if oficiais[arquivo.nome] != arquivo.bytes:
        raise RuntimeError(
            f"{arquivo.chave}: espelho tem {arquivo.bytes:,} bytes, a Receita tem {oficiais[arquivo.nome]:,}"
        )
    return "conferido"


def processar(arquivo: ArquivoRemoto, registro: dict, oficiais: dict[str, int] | None) -> dict:
    """
    PT: Garante que o ZIP local é o publicado e devolve a entrada do
        manifesto. A conversão registrada só vale para o mesmo sha256.
    EN: Ensures the local ZIP is the published one and returns the manifest
        entry. The recorded conversion only holds for the same sha256.
    """
    situacao = conferencia_oficial(arquivo, oficiais)
    # PT: uma conferência feita antes continua valendo se o arquivo é o mesmo.
    # EN: an earlier check still holds if the file is the same.
    if situacao == "pendente" and registro.get("conferencia_com_a_receita") == "conferido":
        situacao = "conferido"

    em_dia = (
        arquivo.destino.exists()
        and arquivo.destino.stat().st_size == arquivo.bytes
        and registro.get("bytes") == arquivo.bytes
        and registro.get("sha256") == sha256(arquivo.destino)
    )
    if em_dia:
        return {**registro, "conferencia_com_a_receita": situacao}

    if not (arquivo.destino.exists() and arquivo.destino.stat().st_size == arquivo.bytes):
        baixar_com_retomada(arquivo)

    novo_hash = sha256(arquivo.destino)
    if registro and registro.get("sha256") != novo_hash:
        print(f"  ! {arquivo.chave}: REPUBLICADO / REPUBLISHED", flush=True)
        situacao = "pendente" if oficiais is None else situacao

    mesmo_arquivo = registro.get("sha256") == novo_hash
    return {
        "retrato": arquivo.retrato,
        "url": arquivo.url,
        "url_oficial": arquivo.url_oficial,
        "last_modified": arquivo.last_modified,
        "bytes": arquivo.bytes,
        "sha256": novo_hash,
        "conferencia_com_a_receita": situacao,
        "conversao": registro.get("conversao", {}) if mesmo_arquivo else {},
    }


def main() -> None:
    dados = manifesto.carregar()
    secao = dados.setdefault("cnpj", {})

    retratos = (*RETRATOS_DE_VALIDACAO, RETRATO_DO_MODELO)
    arquivos = selecionar([a for r in retratos for a in listar_no_espelho(r)])
    oficiais = {r: tamanhos_oficiais(r) for r in retratos}
    fora_do_ar = [r for r, t in oficiais.items() if t is None]
    total = sum(a.bytes for a in arquivos)
    print(f"  {len(arquivos)} arquivos, {total / 1e9:,.2f} GB, em {len(retratos)} retratos", flush=True)
    if fora_do_ar:
        print(f"  ! servidor da Receita sem resposta para {fora_do_ar}: conferência pendente", flush=True)

    with ThreadPoolExecutor(max_workers=DOWNLOADS_SIMULTANEOS) as pool:
        futuros = {
            pool.submit(processar, a, secao.get(a.chave, {}), oficiais[a.retrato]): a
            for a in arquivos
        }
        for futuro in as_completed(futuros):
            arquivo = futuros[futuro]
            secao[arquivo.chave] = futuro.result()
            print(f"  ok {arquivo.chave} ({arquivo.bytes / 1e6:,.0f} MB, "
                  f"{secao[arquivo.chave]['conferencia_com_a_receita']})", flush=True)
            # PT: grava a cada arquivo, para o progresso sobreviver a uma falha.
            # EN: saves after each file, so progress survives a failure.
            manifesto.salvar(dados)

    pendentes = sum(1 for r in secao.values() if r.get("conferencia_com_a_receita") == "pendente")
    if pendentes:
        print(f"\n  {pendentes} arquivos com conferência pendente: rode de novo quando a Receita voltar.")


if __name__ == "__main__":
    main()
