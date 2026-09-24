"""
PT: Gera os seeds de dimensão a partir da ontologia.

    É a decisão de desenho central do projeto posta em prática: a dimensão do
    modelo dimensional **não é escrita à mão**, ela é gerada de
    `ontology/modalidades.yml` e `ontology/dimensoes.yml`. A ontologia é fonte
    do modelo, não documentação sobre ele, e por isso deriva entre o que está
    documentado e o que está no dado deixa de ser possível por construção.

    Dois seeds saem daqui:

    1. **ontologia_modalidade.csv**, um registro por par de modalidade e
       submodalidade, com o código do Anexo 3, os nomes oficiais, a definição
       normativa e o nível de confiança dela. O par é a chave, e não a
       submodalidade sozinha, porque cinco rótulos de submodalidade ocorrem em
       mais de uma modalidade.

    2. **ontologia_dimensao.csv**, um registro por valor de dimensão
       enumerada. Os valores das duas colunas polimórficas são expandidos por
       tipo de cliente e ganham um rótulo desambiguado no formato que a V1
       usava ("PF - Micro"), o que devolve ao dado a informação que a V2
       removeu. Ver avisos_gerais.colunas_polimorficas.

    Nada aqui interpreta texto. O nome da taxonomia de cada coluna polimórfica
    vem do campo `taxonomia_por_cliente` da ontologia, e não de uma leitura da
    frase da definição.

EN: Generates the dimension seeds from the ontology. This is the project's
    central design decision in practice: the dimensional model's dimensions are
    not hand-written, they are generated from the ontology files, which makes
    drift between documentation and data impossible by construction.

    Two seeds: one record per modality and sub-modality pair, with the Annex 3
    code, official names, normative definition and its confidence level; and
    one record per enumerated dimension value, with the polymorphic columns
    expanded per client type and given a disambiguated label in the format V1
    used ("PF - Micro"), restoring what V2 removed.

    Nothing here parses prose. Each polymorphic column's taxonomy name comes
    from the ontology's `taxonomia_por_cliente` field.

Uso / Usage:
    uv run python -m scripts.gerar_seeds_da_ontologia
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
ONTOLOGIA_MODALIDADES = RAIZ / "ontology" / "modalidades.yml"
ONTOLOGIA_DIMENSOES = RAIZ / "ontology" / "dimensoes.yml"
SEED_MODALIDADE = RAIZ / "dbt" / "seeds" / "ontologia_modalidade.csv"
SEED_DIMENSAO = RAIZ / "dbt" / "seeds" / "ontologia_dimensao.csv"

CLIENTES = ("PF", "PJ")


def carregar(caminho: Path) -> dict:
    """PT: lê um arquivo da ontologia / EN: reads one ontology file"""
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def texto(valor: object) -> str:
    """
    PT: Normaliza texto de YAML para CSV. As definições são escritas em bloco
        e chegam com quebras de linha, que viram espaço.
    EN: Normalises YAML text for CSV. Definitions are written as blocks and
        arrive with line breaks, which become spaces.
    """
    return " ".join(str(valor or "").split())


# -----------------------------------------------------------------------------
# PT: Seed 1, modalidades e submodalidades
# EN: Seed 1, modalities and sub-modalities
# -----------------------------------------------------------------------------

def linhas_de_modalidade(dados: dict) -> list[dict[str, str]]:
    """
    PT: Um registro por submodalidade, já com os dados da modalidade que a
        contém. A hierarquia vem do campo `broader` da ontologia.
    EN: One record per sub-modality, carrying its parent modality's data. The
        hierarchy comes from the ontology's `broader` field.
    """
    conceitos = dados["conceitos"]
    modalidades = {c["id"]: c for c in conceitos if c["tipo"] == "modalidade"}

    linhas = []
    for c in conceitos:
        if c["tipo"] != "submodalidade":
            continue
        mae = modalidades[c["broader"]]
        linhas.append(
            {
                "codigo_submodalidade": c["notation"],
                "codigo_modalidade": mae["notation"],
                "modalidade": mae["rotulo_no_dado"],
                "submodalidade": c["rotulo_no_dado"],
                "nome_oficial_modalidade": texto(mae.get("prefLabel_pt")),
                "nome_oficial_submodalidade": texto(c.get("prefLabel_pt")),
                "definicao": texto(c.get("definition")),
                "confianca": c.get("confianca", ""),
                "fonte": texto(c.get("fonte")),
            }
        )
    return sorted(linhas, key=lambda l: l["codigo_submodalidade"])


# -----------------------------------------------------------------------------
# PT: Seed 2, valores das dimensões enumeradas
# EN: Seed 2, enumerated dimension values
# -----------------------------------------------------------------------------

def clientes_do_valor(valor: dict) -> tuple[str, ...]:
    """
    PT: Em que tipos de cliente o valor ocorre, medido no dado e registrado na
        ontologia no campo aplica_a.
    EN: Which client types the value occurs with, measured in the data and
        recorded in the ontology's aplica_a field.
    """
    return CLIENTES if valor.get("aplica_a") == "PF e PJ" else (valor.get("aplica_a", ""),)


def linhas_de_dimensao(dados: dict) -> list[dict[str, str]]:
    """
    PT: Um registro por valor. Nas colunas polimórficas o valor é expandido em
        um registro por tipo de cliente, porque lá o par (cliente, valor) é que
        identifica a categoria. Nas demais, o cliente fica vazio de propósito:
        o valor vale para os dois.
    EN: One record per value. In polymorphic columns the value is expanded into
        one record per client type, because there the (client, value) pair is
        what identifies the category. Elsewhere the client is left empty on
        purpose: the value holds for both.
    """
    linhas = []
    for dimensao in dados["dimensoes"]:
        if not dimensao.get("valores"):
            continue

        polimorfica = dimensao.get("polimorfica_por") == "cliente"
        taxonomias = dimensao.get("taxonomia_por_cliente", {})

        for valor in dimensao["valores"]:
            rotulo = valor["rotulo_no_dado"]
            clientes = clientes_do_valor(valor) if polimorfica else ("",)

            for cliente in clientes:
                linhas.append(
                    {
                        "dimensao": dimensao["coluna"],
                        "cliente": cliente,
                        "valor": rotulo,
                        # PT: chave desambiguada, no formato que a V1 usava.
                        # EN: disambiguated key, in the format V1 used.
                        "valor_desambiguado": f"{cliente} - {rotulo}" if cliente else rotulo,
                        "taxonomia": taxonomias.get(cliente) or texto(dimensao["prefLabel_pt"]),
                        "aplica_a": valor.get("aplica_a", ""),
                        "significado": texto(valor.get("significado")),
                        "aviso": texto(valor.get("aviso")),
                    }
                )
    return linhas


# -----------------------------------------------------------------------------
# PT: Escrita e resumo
# EN: Writing and summary
# -----------------------------------------------------------------------------

def escrever(seed: Path, linhas: list[dict[str, str]]) -> None:
    """
    PT: Grava o CSV do seed com terminação de linha LF explícita. O padrão do
        módulo csv é CRLF, e isso tornaria o arquivo gerado diferente conforme o
        sistema em que o script roda. O CI regera o seed e compara com o que
        está versionado, então a terminação precisa ser a mesma em Windows e em
        Linux. O `.gitattributes` fixa o outro lado.
    EN: Writes the seed CSV with an explicit LF line ending. The csv module
        defaults to CRLF, which would make the generated file differ by
        operating system. CI regenerates the seed and compares it with what is
        committed, so the ending must match on Windows and Linux alike.
    """
    seed.parent.mkdir(parents=True, exist_ok=True)
    with seed.open("w", encoding="utf-8", newline="\n") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> None:
    modalidades = linhas_de_modalidade(carregar(ONTOLOGIA_MODALIDADES))
    escrever(SEED_MODALIDADE, modalidades)
    sem_definicao = [l["codigo_submodalidade"] for l in modalidades if not l["definicao"]]
    print(f"  {len(modalidades)} pares em {SEED_MODALIDADE.relative_to(RAIZ)}")
    print(f"  modalidades distintas: {len({l['codigo_modalidade'] for l in modalidades})}")
    if sem_definicao:
        # PT: são os conceitos marcados como lacuna, e a ausência é esperada.
        # EN: these are the concepts marked as a gap; the absence is expected.
        print(f"  sem definição normativa (lacuna): {sem_definicao}")

    dimensoes = linhas_de_dimensao(carregar(ONTOLOGIA_DIMENSOES))
    escrever(SEED_DIMENSAO, dimensoes)
    print(f"\n  {len(dimensoes)} valores em {SEED_DIMENSAO.relative_to(RAIZ)}")
    for coluna in dict.fromkeys(l["dimensao"] for l in dimensoes):
        do_grupo = [l for l in dimensoes if l["dimensao"] == coluna]
        expandidos = sum(1 for l in do_grupo if l["cliente"])
        print(f"    {coluna}: {len(do_grupo)} registros" + (f", expandidos por cliente" if expandidos else ""))


if __name__ == "__main__":
    main()
