"""
PT: Publica o retrato do esquema estrela no dataset público do Hugging Face
    (#45, ADRs 0016 e 0027). Roda só na máquina do Yuri, nunca no CI.

    Antes, uma vez: criar pela web o dataset vidayuri/bcb-credito-governanca,
    público, e um token de escopo fino com escrita só nele.

    O token é pedido na hora, por getpass, e fica só na memória deste
    processo: não é gravado em arquivo, em variável de ambiente nem em cofre.
    O `hf auth login` não é usado porque grava o token em texto puro.

    O que o script faz:
    1. confere o sha256 de cada Parquet local contra o manifesto, e que o
       cartão cita o mês de referência do retrato;
    2. monta um commit só, com a lista explícita do que sobe: os Parquets
       do manifesto e o cartão (esquema_estrela/README.md, com LF). Qualquer
       outro arquivo que esteja no dataset é apagado no mesmo commit, menos o
       .gitattributes. Nada de evaluation/ tem como subir;
    3. lista o dataset na revisão nova e confere que tem exatamente esses
       arquivos;
    4. grava a revisão no manifesto, para o experimento e o CI lerem o
       retrato fixado, e não o main, que muda.

EN: Publishes the star schema snapshot to the public Hugging Face dataset.
    Runs only on Yuri's machine, never in CI. The fine-grained token is read
    by getpass and lives only in this process's memory. One commit with an
    explicit file list (manifest Parquet files and the card); anything else
    in the dataset is deleted except .gitattributes. The new revision is
    listed and checked, then written to the manifest.

Uso / Usage:
    uv run python -m scripts.publicar_esquema_estrela
"""

from __future__ import annotations

import getpass
import re
import sys

from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

from ingestion.baixar import sha256
from scripts.esquema_estrela_duckdb import (
    CARTAO,
    LOCAL,
    REPOSITORIO_HF,
    carregar_manifesto,
    gravar_manifesto,
)

MANTIDOS = {".gitattributes"}

# PT: formato de um token do Hugging Face. Serve para reprovar, antes de
#     qualquer requisição, um token que o terminal colou com caractere de
#     controle: em 2026-10-07, um token colado no terminal do app chegou com
#     lixo, e o CloudFront recusou a requisição com 400, sem dizer por quê.
# EN: a Hugging Face token's shape, to reject before any request a token the
#     terminal pasted with control characters.
FORMATO_DO_TOKEN = re.compile(r"^hf_[A-Za-z0-9]{20,}$")
# PT: marcas de colagem que alguns terminais mandam em volta do texto colado.
# EN: bracketed-paste markers some terminals send around pasted text.
MARCAS_DE_COLAGEM = ("\x1b[200~", "\x1b[201~")


def conferir_antes(manifesto: dict) -> list[str]:
    """
    PT: Arquivos locais iguais ao manifesto, e o cartão no mês do retrato.
    EN: Local files match the manifest, and the card names the month.
    """
    erros = []
    for tabela, dados in manifesto["tabelas"].items():
        arquivo = LOCAL / dados["arquivo"]
        if not arquivo.exists() or sha256(arquivo) != dados["sha256"]:
            erros.append(f"{tabela}: Parquet local ausente ou diferente do manifesto; rode a exportação")
    if manifesto["mes_de_referencia"] not in CARTAO.read_text(encoding="utf-8"):
        erros.append(f"o cartão não cita o mês de referência {manifesto['mes_de_referencia']}")
    return erros


def ler_token() -> str:
    """
    PT: Lê o token por getpass e tira as marcas de colagem e os espaços. O
        getpass não mostra nada na tela, nem asterisco, e por isso é fácil
        colar mais de uma vez: em 2026-10-07 o token chegou colado seis
        vezes. Um token repetido inteiro vira um só. Se o que sobra não tem
        o formato de um token, o script para sem fazer nenhuma requisição, e
        nenhuma mensagem mostra caractere do token.
    EN: Reads the token by getpass and strips paste markers and whitespace.
        getpass echoes nothing, so pasting twice is easy; a token repeated
        whole collapses to one. If what remains is not token-shaped, stops
        before any request. No message shows any character of the token.
    """
    print("Cole o token uma vez só e tecle Enter. Nada aparece na tela, nem asterisco.")
    token = getpass.getpass("Token de escopo fino do Hugging Face: ")
    for marca in MARCAS_DE_COLAGEM:
        token = token.replace(marca, "")
    token = "".join(token.split())
    if repetido := re.fullmatch(r"(hf_[A-Za-z0-9]{20,}?)\1+", token):
        print(f"O token foi colado {len(token) // len(repetido.group(1))} vezes; uso uma.")
        token = repetido.group(1)
    if not FORMATO_DO_TOKEN.match(token):
        controles = sum(1 for c in token if not c.isprintable())
        raise SystemExit(
            f"O que foi lido não tem o formato de um token (hf_ seguido de letras e números): {len(token)} "
            f"caracteres, {controles} de controle. Confira se o que está copiado é o token e rode de novo."
        )
    print(f"Token lido: {len(token)} caracteres, no formato esperado.")
    return token


def main() -> None:
    manifesto = carregar_manifesto()
    if not manifesto:
        raise SystemExit("Sem manifesto: rode scripts.exportar_esquema_estrela / no manifest")
    if erros := conferir_antes(manifesto):
        print("\n".join(f"  ERRO {e}" for e in erros))
        sys.exit(1)

    arquivos = {dados["arquivo"]: LOCAL / dados["arquivo"] for dados in manifesto["tabelas"].values()}
    esperados = {*arquivos, "README.md", *MANTIDOS}
    print(f"Retrato de {manifesto['mes_de_referencia']}: {len(arquivos)} Parquets e o cartão para {REPOSITORIO_HF}")
    print("Rodou o QA local antes? uv run python -m scripts.analises.qa_esquema_estrela --com-databricks")

    api = HfApi(token=ler_token())
    try:
        no_dataset = set(api.list_repo_files(REPOSITORIO_HF, repo_type="dataset"))
        operacoes = [CommitOperationAdd(destino, origem) for destino, origem in sorted(arquivos.items())]
        operacoes.append(CommitOperationAdd("README.md", CARTAO.read_bytes().replace(b"\r\n", b"\n")))
        operacoes += [CommitOperationDelete(caminho) for caminho in sorted(no_dataset - esperados)]
        commit = api.create_commit(
            REPOSITORIO_HF,
            operacoes,
            repo_type="dataset",
            commit_message=f"Retrato do esquema estrela de {manifesto['mes_de_referencia']}",
        )
        publicados = set(api.list_repo_files(REPOSITORIO_HF, repo_type="dataset", revision=commit.oid))
    finally:
        # PT: o token sai da memória com o cliente / EN: drop the client and its token
        del api

    if publicados != esperados or any("evaluation" in p for p in publicados):
        print(f"  ERRO dataset com arquivos inesperados: a mais {sorted(publicados - esperados)}, a menos {sorted(esperados - publicados)}")
        sys.exit(1)

    manifesto["revisao_hf"] = commit.oid
    gravar_manifesto(manifesto)
    print(f"\nPublicado na revisão {commit.oid}, gravada no manifesto.")
    print("Confira a leitura direta: uv run python -m scripts.analises.qa_esquema_estrela --origem hf")


if __name__ == "__main__":
    main()
