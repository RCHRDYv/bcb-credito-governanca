"""
PT: Gera o seed de correspondência de modalidades da V2 para a V1, a partir
    da planilha oficial Equivalencia_Modalidades.xlsx (ADR 0003).

    Decisões desta extração:

    1. **A chave é o código da submodalidade, não o nome.** Os nomes na
       planilha trazem chamadas de nota grudadas ("conta garantidaa2",
       "veículos automotores2") e estão desatualizados em relação ao leiaute
       atual (a 0902 aparece como "carteira hipotecária", hoje "exceto SFH").
       O código é estável, então o nome exibido vem de ontology/modalidades.yml.
    2. **As três abas dão a chave completa:** de-para_PF vale para cliente PF
       em qualquer origem; as duas abas PJ separam recursos livres (origem
       "Sem destinação específica") de direcionados ("Com destinação
       específica"), conforme o primeiro nível do Anexo 4 do leiaute.
    3. **Os dois tratamentos adicionais da planilha entram explicitamente,**
       pelo texto declarado na aba OutrasInformacoes, e não por interpretação
       das chamadas de nota:
       - tratamento 1: submodalidades 0202 e 0203 com cliente PJ usam a
         modalidade PF;
       - tratamento 2: submodalidades 0401, 0407, 0701, 1201, 1206 e 1207 com
         cliente PJ usam a modalidade PF **somente se a Natureza da operação
         for 4**. O SCR.data não publica a Natureza, então essas linhas ficam
         marcadas como ambíguas, com as duas modalidades candidatas.

EN: Generates the V2 to V1 modality correspondence seed from the BCB's
    official equivalence spreadsheet (ADR 0003). The key is the sub-modality
    code, not the label, because the sheet's labels carry glued footnote
    markers and are outdated. The two additional treatments declared in the
    sheet are applied explicitly; the second depends on a field (Natureza)
    that SCR.data does not publish, so those rows are flagged as ambiguous
    with both candidate V1 modalities.

Uso / Usage:
    uv run python -m scripts.gerar_seed_correspondencia
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
PLANILHA = RAIZ / "data" / "raw" / "Equivalencia_Modalidades.xlsx"
ONTOLOGIA = RAIZ / "ontology" / "modalidades.yml"
SEED = RAIZ / "dbt" / "seeds" / "correspondencia_modalidade_v2_v1.csv"

# PT: aba, quantas linhas de cabeçalho pular, cliente e origem que ela cobre.
# EN: sheet, header rows to skip, and the client and origin it covers.
ABAS = [
    ("de-para_PF", 2, "PF", None),
    ("de-para_PJ - Tipo Origem 1", 3, "PJ", "Sem destinação específica"),
    ("de-para_PJ - Tipo Origem 2", 3, "PJ", "Com destinação específica"),
]
ORIGENS = ("Sem destinação específica", "Com destinação específica")

# PT: Tratamentos adicionais, transcritos da aba OutrasInformacoes.
# EN: Additional treatments, transcribed from the OutrasInformacoes sheet.
TRATAMENTO_1 = {"0202", "0203"}
TRATAMENTO_2 = {"0401", "0407", "0701", "1201", "1206", "1207"}


def normalizar(texto: str) -> str:
    """PT: minúsculas, sem acento, espaços colapsados / EN: casefold, no accents"""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.casefold().split())


def rotulos_v1_do_dado() -> dict[str, str]:
    """
    PT: As 16 modalidades da V1 como aparecem no dado, indexadas pela forma
        normalizada. São fixas e ficam aqui para o script não depender de
        conexão com o Databricks. A validação confere contra o bronze.
    EN: The 16 V1 modalities as they appear in the data, indexed by their
        normalised form. Fixed here so the script needs no Databricks
        connection; the validation step checks them against bronze.
    """
    rotulos = [
        "PF - Cartão de crédito",
        "PF - Empréstimo com consignação em folha",
        "PF - Empréstimo sem consignação em folha",
        "PF - Habitacional",
        "PF - Outros créditos",
        "PF - Rural e agroindustrial",
        "PF - Veículos",
        "PJ - Capital de giro",
        "PJ - Cheque especial e conta garantida",
        "PJ - Comércio exterior",
        "PJ - Financiamento de infraestrutura/desenvolvimento/projeto e outros créditos",
        "PJ - Habitacional",
        "PJ - Investimento",
        "PJ - Operações com recebíveis",
        "PJ - Outros créditos",
        "PJ - Rural e agroindustrial",
    ]
    return {normalizar(r): r for r in rotulos}


def casar_modalidade_v1(nome_planilha: str, por_normal: dict[str, str]) -> str:
    """
    PT: Casa o nome da planilha com o rótulo do dado. Trata dois casos: a
        célula que empilha nome antigo e novo de uma renomeação, onde vale o
        último, e a chamada de nota grudada no fim do nome.
    EN: Matches the sheet's name to the data label, handling the cell that
        stacks a renaming's old and new names (the last one wins) and the
        footnote marker glued to the end.
    """
    nome = str(nome_planilha).strip()
    prefixo = nome[:4]  # PT: "PF -" ou "PJ -" / EN: "PF -" or "PJ -"
    if nome.count(prefixo) > 1:
        nome = prefixo + nome.rsplit(prefixo, 1)[1]

    for corte in (0, 1, 2):
        candidato = normalizar(nome[: len(nome) - corte] if corte else nome)
        if candidato in por_normal:
            return por_normal[candidato]
    raise ValueError(f"modalidade V1 sem correspondência no dado: {nome_planilha!r}")


def ler_aba(aba: str, pular: int) -> pd.DataFrame:
    """PT: lê uma aba de-para e devolve código e modalidade V1 / EN: reads one sheet"""
    df = pd.read_excel(PLANILHA, sheet_name=aba, header=None, skiprows=pular)
    df.columns = ["mod_v1", "dom_num", "dom_desc", "mod_cod", "sub_cod", "sub_desc"]
    df["mod_v1"] = df["mod_v1"].ffill()
    df = df.dropna(subset=["mod_cod", "sub_cod"]).copy()

    def codigo_de(coluna: str) -> pd.Series:
        """PT: '2' e '2.0' viram '02' / EN: '2' and '2.0' become '02'"""
        return df[coluna].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(2)

    df["codigo"] = codigo_de("mod_cod") + codigo_de("sub_cod")
    return df[["codigo", "mod_v1"]].drop_duplicates()


def conceitos_da_ontologia() -> dict[str, dict[str, str]]:
    """PT: código -> rótulos no dado / EN: code -> data labels"""
    dados = yaml.safe_load(ONTOLOGIA.read_text(encoding="utf-8"))["conceitos"]
    modalidades = {c["id"]: c["rotulo_no_dado"] for c in dados if c["tipo"] == "modalidade"}
    return {
        c["notation"]: {
            "modalidade_v2": modalidades[c["broader"]],
            "submodalidade_v2": c["rotulo_no_dado"],
        }
        for c in dados
        if c["tipo"] == "submodalidade"
    }


def montar_linhas() -> tuple[list[dict], list[str]]:
    """PT: monta o seed e os avisos / EN: builds the seed rows and warnings"""
    por_normal = rotulos_v1_do_dado()
    ontologia = conceitos_da_ontologia()

    # PT: mapa (cliente, origem, código) -> modalidade V1, direto das abas.
    # EN: map (client, origin, code) -> V1 modality, straight from the sheets.
    base: dict[tuple[str, str, str], str] = {}
    for aba, pular, cliente, origem in ABAS:
        df = ler_aba(aba, pular)
        for _, r in df.iterrows():
            v1 = casar_modalidade_v1(r["mod_v1"], por_normal)
            for org in (ORIGENS if origem is None else (origem,)):
                base[(cliente, org, r["codigo"])] = v1

    # PT: Percorre todas as combinações possíveis, e não só as que as abas
    #     listam. O tratamento 1 existe justamente porque as abas PJ não
    #     listam 0202 e 0203, embora o dado tenha cliente PJ nelas.
    # EN: Walks every possible combination, not only the ones the sheets list.
    #     Treatment 1 exists precisely because the PJ sheets omit 0202 and
    #     0203, even though the data has PJ clients in them.
    linhas, avisos, sem_regra = [], [], []
    for codigo in sorted(ontologia):
        for cliente in ("PF", "PJ"):
            for origem in ORIGENS:
                regra, alternativa, ambiguidade = "base", "", ""
                v1 = base.get((cliente, origem, codigo))

                if cliente == "PJ" and codigo in TRATAMENTO_1:
                    regra, alternativa = "tratamento_1", v1 or ""
                    v1 = base.get(("PF", origem, codigo))
                elif cliente == "PJ" and codigo in TRATAMENTO_2 and v1:
                    regra = "tratamento_2"
                    alternativa = base.get(("PF", origem, codigo), "")
                    ambiguidade = "natureza_nao_publicada"

                # PT: A planilha não cobre tudo. Para cliente PF, as
                #     submodalidades 1303 e 1399 não aparecem em nenhuma aba,
                #     e o dado tem linhas nelas. A linha entra no seed sem
                #     correspondência oficial, com a inferência em coluna
                #     separada, para o mart escolher e declarar.
                # EN: The sheet is incomplete. For PF clients, sub-modalities
                #     1303 and 1399 appear in no sheet, yet the data has rows
                #     for them. The row enters the seed with no official
                #     target and the inference in a separate column.
                inferida = ""
                if not v1:
                    regra, ambiguidade = "ausente_na_planilha", "ausente_na_planilha"
                    inferida = f"{cliente} - Outros créditos"
                    sem_regra.append((codigo, cliente, origem))

                linhas.append(
                    {
                        "codigo_submodalidade_v2": codigo,
                        "modalidade_v2": ontologia[codigo]["modalidade_v2"],
                        "submodalidade_v2": ontologia[codigo]["submodalidade_v2"],
                        "cliente": cliente,
                        "origem": origem,
                        "modalidade_v1": v1 or "",
                        "modalidade_v1_alternativa": alternativa,
                        "modalidade_v1_inferida": inferida,
                        "regra": regra,
                        "ambiguidade": ambiguidade,
                    }
                )

    faltando = sorted(set(ontologia) - {c for _, _, c in base})
    if faltando:
        avisos.append(f"códigos no dado e ausentes da planilha: {faltando}")
    if sem_regra:
        avisos.append(
            f"{len(sem_regra)} combinações sem correspondência oficial, com inferência declarada: {sem_regra}"
        )
    return linhas, avisos


def main() -> None:
    linhas, avisos = montar_linhas()
    SEED.parent.mkdir(parents=True, exist_ok=True)
    # PT: lineterminator LF explícito: o padrão do módulo csv é CRLF, e o seed
    #     precisa sair igual em qualquer sistema. Ver .gitattributes.
    # EN: explicit LF line terminator: the csv module defaults to CRLF, and the
    #     seed must come out identical on any operating system.
    with SEED.open("w", encoding="utf-8", newline="\n") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)

    por_regra = {r: sum(1 for l in linhas if l["regra"] == r) for r in ("base", "tratamento_1", "tratamento_2", "ausente_na_planilha")}
    print(f"  {len(linhas)} linhas em {SEED.relative_to(RAIZ)}")
    print(f"  regra base: {por_regra['base']}")
    print(f"  tratamento 1 (0202 e 0203 com cliente PJ): {por_regra['tratamento_1']}")
    print(f"  tratamento 2 (ambíguas por Natureza não publicada): {por_regra['tratamento_2']}")
    print(f"  sem correspondência oficial, com inferência declarada: {por_regra['ausente_na_planilha']}")
    for aviso in avisos:
        print(f"  aviso: {aviso}")


if __name__ == "__main__":
    main()
