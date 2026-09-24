"""
PT: Etapa 2 do CNPJ. Converte cada ZIP do CNPJ aberto em Parquet só texto,
    em data/landing/cnpj/{tabela}/{retrato}/.

    A conversão segue as regras da do SCR (ingestion/converter_parquet.py):
    sem perda e sem interpretação, todas as colunas como texto, sem trim e
    sem conversão de tipo. O que muda vem do formato da Receita:
    - **sem cabeçalho:** os nomes das colunas vêm do leiaute oficial
      (TabelaCnpj em ingestion/fontes.py);
    - **latin-1, e não UTF-8:** o texto é recodificado para UTF-8, o que é
      sem perda, porque todo byte latin-1 tem um caractere correspondente;
    - **arquivos grandes:** o maior ZIP tem 2,2 GB compactado. O CSV é lido
      em fluxo e cortado em partes de até PARTE registros, cada uma um
      Parquet. Isso mantém a memória baixa e deixa o envio ao volume correr
      em paralelo. O corte só acontece em fim de registro, nunca dentro de
      um campo entre aspas que contenha quebra de linha.

    Cada parte é validada antes de ser aceita: o número de colunas do
    primeiro registro bate com o leiaute, e o número de linhas do Parquet
    bate com o de registros contados no fluxo, de forma independente do
    leitor de CSV.

    Quatro colunas de linhagem são acrescentadas: arquivo_origem, retrato,
    data_extracao (lida do nome do arquivo interno, como "D60912", que é
    12/09/2026) e sha256_zip.

EN: CNPJ step 2. Converts each open CNPJ ZIP into text-only Parquet, under
    data/landing/cnpj/{table}/{snapshot}/. Same rules as the SCR conversion:
    lossless, every column as untrimmed, uncast text. Column names come from
    the official layout (the files have no header); latin-1 is re-encoded as
    UTF-8, which is lossless; large CSVs are streamed and cut into parts of
    up to PARTE records, only at record boundaries, never inside a quoted
    field. Each part is validated (column count, and Parquet rows against an
    independent record count) and gets four lineage columns.

Uso / Usage:
    uv run python -m ingestion.converter_cnpj
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path

import polars as pl

from ingestion import manifesto
from ingestion.fontes import DIR_LANDING_CNPJ, DIR_RAW_CNPJ, TABELAS_CNPJ, TabelaCnpj

# PT: 3 milhões de registros de estabelecimentos dão cerca de 250 MB em
#     Parquet, que sobem ao volume em poucos minutos.
# EN: 3 million establishment records make about 250 MB of Parquet.
PARTE = 3_000_000

# PT: "K3241.K03200Y0.D60912.ESTABELE": D, último dígito do ano, mês e dia.
#     No Simples a data fecha o nome ("F.K03200$W.SIMPLES.CSV.D60912"), então
#     depois dela pode vir um ponto ou o fim.
# EN: D, the year's last digit, month and day. In Simples the date ends the
#     name, so it may be followed by a dot or by the end.
PADRAO_DATA_EXTRACAO = re.compile(r"\.D(\d)(\d{2})(\d{2})(?:\.|$)")


def tabela_do_arquivo(nome_zip: str) -> TabelaCnpj:
    """PT: qual tabela um ZIP carrega / EN: which table a ZIP holds"""
    for tabela in TABELAS_CNPJ:
        if tabela.e_desta_tabela(nome_zip):
            return tabela
    raise ValueError(f"ZIP sem tabela conhecida / unknown table: {nome_zip}")


def data_extracao(interno: str, retrato: str) -> str:
    """
    PT: A Receita grava só o último dígito do ano. A década vem do retrato,
        e a data precisa cair no mês do retrato ou no anterior, o que
        confere a leitura.
    EN: Receita writes only the year's last digit. The decade comes from the
        snapshot, and the date must fall in the snapshot month or the one
        before, which checks the reading.
    """
    achado = PADRAO_DATA_EXTRACAO.search(interno)
    if not achado:
        raise ValueError(f"Nome interno sem data / internal name without date: {interno}")
    digito, mes, dia = achado.groups()
    ano = int(retrato[:3] + digito)
    data = f"{ano}-{mes}-{dia}"
    ano_r, mes_r = int(retrato[:4]), int(retrato[5:7])
    anterior = (ano_r, mes_r - 1) if mes_r > 1 else (ano_r - 1, 12)
    if (ano, int(mes)) not in {(ano_r, mes_r), anterior}:
        raise ValueError(f"Data de extração {data} fora do retrato {retrato}")
    return data


def registros(fluxo: io.TextIOBase) -> Iterator[str]:
    """
    PT: Devolve registros completos. Um registro termina numa quebra de
        linha com as aspas fechadas: se a contagem de aspas acumulada é
        ímpar, a quebra está dentro de um campo e o registro continua na
        linha seguinte. Aspas escapadas ("") não mudam a paridade.
    EN: Yields complete records. A record ends at a newline with quotes
        closed: an odd running quote count means the newline is inside a
        field. Escaped quotes ("") do not change parity.
    """
    pendente = ""
    for linha in fluxo:
        pendente += linha
        if pendente.count('"') % 2 == 0:
            yield pendente
            pendente = ""
    if pendente:
        yield pendente


def colunas_do_registro(registro: str) -> int:
    """PT: colunas de um registro, pelo leitor csv / EN: columns in one record"""
    return len(next(csv.reader(io.StringIO(registro), delimiter=";", quotechar='"')))


def converter_parte(
    texto: list[str], tabela: TabelaCnpj, destino: Path, linhagem: dict[str, str]
) -> int:
    """
    PT: Grava uma parte e confere as contagens. Devolve o número de linhas.
    EN: Writes one part and checks the counts. Returns the row count.
    """
    if colunas_do_registro(texto[0]) != len(tabela.colunas):
        raise ValueError(f"{destino.name}: {colunas_do_registro(texto[0])} colunas, leiaute tem {len(tabela.colunas)}")

    df = pl.read_csv(
        io.BytesIO("".join(texto).encode("utf-8")),
        has_header=False,
        new_columns=list(tabela.colunas),
        separator=";",
        quote_char='"',
        infer_schema=False,
        encoding="utf8",
    ).with_columns(pl.lit(v).alias(k) for k, v in linhagem.items())

    if df.height != len(texto):
        raise ValueError(f"{destino.name}: {df.height} linhas lidas, {len(texto)} registros no fluxo")
    df.write_parquet(destino, compression="zstd")
    return df.height


def ja_convertido(registro: dict) -> bool:
    """
    PT: A conversão registrada vale se as partes existem e vieram do mesmo
        ZIP. Se a Receita republicou, o sha256 muda e tudo é refeito.
    EN: The recorded conversion holds if the parts exist and came from the
        same ZIP.
    """
    conversao = registro.get("conversao") or {}
    partes = [Path(p) for p in conversao.get("partes", {})]
    if not partes or not all((DIR_LANDING_CNPJ / p).exists() for p in partes):
        return False
    marca = pl.read_parquet(DIR_LANDING_CNPJ / partes[0], columns=["sha256_zip"], n_rows=1)
    return marca["sha256_zip"][0] == registro["sha256"]


def converter_zip(chave: str, registro: dict) -> None:
    """PT: converte um ZIP em uma ou mais partes / EN: converts one ZIP into parts"""
    retrato, nome_zip = chave.split("/")
    tabela = tabela_do_arquivo(nome_zip)
    pasta = DIR_LANDING_CNPJ / tabela.nome / retrato
    pasta.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(DIR_RAW_CNPJ / retrato / nome_zip) as z:
        internos = z.namelist()
        if len(internos) != 1:
            raise ValueError(f"{chave}: esperado um arquivo no ZIP, há {len(internos)}")
        interno = internos[0]
        linhagem = {
            "arquivo_origem": f"{chave}/{interno}",
            "retrato": retrato,
            "data_extracao": data_extracao(interno, retrato),
            "sha256_zip": registro["sha256"],
        }

        # PT: Apaga partes de uma conversão anterior, que podem ser mais
        #     numerosas que as de agora.
        # EN: Removes parts from an earlier conversion.
        for velha in pasta.glob(f"{Path(nome_zip).stem}-parte*.parquet"):
            velha.unlink()

        partes: dict[str, int] = {}
        with z.open(interno) as bruto:
            fluxo = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
            lote: list[str] = []
            for reg in registros(fluxo):
                lote.append(reg)
                if len(lote) == PARTE:
                    destino = pasta / f"{Path(nome_zip).stem}-parte{len(partes):02d}.parquet"
                    partes[destino.relative_to(DIR_LANDING_CNPJ).as_posix()] = converter_parte(lote, tabela, destino, linhagem)
                    lote = []
            if lote:
                destino = pasta / f"{Path(nome_zip).stem}-parte{len(partes):02d}.parquet"
                partes[destino.relative_to(DIR_LANDING_CNPJ).as_posix()] = converter_parte(lote, tabela, destino, linhagem)

    registro["conversao"] = {
        "tabela": tabela.nome,
        "arquivo_interno": interno,
        "data_extracao": linhagem["data_extracao"],
        "linhas": sum(partes.values()),
        "partes": partes,
    }
    print(f"  > {chave}: {sum(partes.values()):,} linhas em {len(partes)} partes", flush=True)


def main() -> None:
    dados = manifesto.carregar()
    secao = dados.get("cnpj", {})
    if not secao:
        raise SystemExit("Sem CNPJ no manifesto: rode ingestion.baixar_cnpj antes / run ingestion.baixar_cnpj first")

    for chave, registro in sorted(secao.items()):
        if ja_convertido(registro):
            print(f"  = {chave}: já convertido / already converted", flush=True)
            continue
        converter_zip(chave, registro)
        # PT: grava a cada ZIP, para o progresso sobreviver a uma falha.
        # EN: saves after each ZIP, so progress survives a failure.
        manifesto.salvar(dados)


if __name__ == "__main__":
    main()
