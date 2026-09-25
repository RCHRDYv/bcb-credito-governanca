"""
PT: Gera as respostas do gabarito (issue #16, ADR 0015).

    Lê evaluation/gabarito.yml, roda cada SQL no esquema estrela do
    Databricks e grava três coisas:

    1. evaluation/gabarito/respostas/<consulta>.json: o resultado de cada
       consulta, com o mês de referência. É o que o experimento compara com
       a resposta da IA.
    2. evaluation/gabarito/esquema_estrela.json: colunas e tipos das tabelas
       dim_* e fct_*. O validador do CI usa esse retrato para conferir, sem
       credencial, que todo SQL do gabarito também roda no DuckDB.
    3. docs/gabarito.md: o gabarito para leitura humana, pergunta por
       pergunta, com leituras, respostas, ressalvas e fontes.

    Nenhum número é digitado à mão. Rodar de novo com o mesmo dado produz os
    mesmos arquivos, porque nenhum deles carrega data de geração, e os
    valores em ponto flutuante são gravados com 10 algarismos significativos,
    para que a ordem de soma do Spark não mude o último dígito.

EN: Generates the answer key's answers. Reads evaluation/gabarito.yml, runs
    each SQL on the Databricks star schema, and writes the per-query JSON
    answers, a snapshot of the star schema's columns and types (used by the
    CI validator to check, credential-free, that every SQL also runs on
    DuckDB), and docs/gabarito.md for human reading. No number is typed by
    hand, and the same data yields the same files.

Uso / Usage:
    uv run python -m scripts.gerar_gabarito
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import yaml

from ingestion.databricks import Resultado, cliente, consultar, warehouse
from ingestion.fontes import RAIZ
from scripts.gerar_recomendacao import maiuscula, mes, numero

GABARITO = RAIZ / "evaluation" / "gabarito.yml"
PERGUNTAS = RAIZ / "evaluation" / "questions_v2.yml"
PASTA_SQL = RAIZ / "evaluation" / "gabarito"
PASTA_RESPOSTAS = PASTA_SQL / "respostas"
ESQUEMA_ESTRELA = PASTA_SQL / "esquema_estrela.json"
DOCUMENTO = RAIZ / "docs" / "gabarito.md"

# PT: tabelas maiores que isto vão para um bloco recolhido no documento.
# EN: tables longer than this go into a collapsed block in the document.
LINHAS_VISIVEIS = 13

# PT: colunas em reais, reconhecidas pelo nome. As terminadas em _pct e _pp
#     são testadas antes, e por isso "carteira_12_meses_pct" é percentual.
# EN: money columns, recognised by name; _pct and _pp suffixes win first.
DINHEIRO = re.compile(
    r"^(carteira|volume|valor|ativo_problematico|total_do_cartao|maior_carteira|mediana_das_ufs"
    r"|ticket_medio|consignado|nao_consignado|diferenca$|variacao_em_reais|crescimento_em_reais"
    r"|crescimento_por_habitante_em_reais|distancia_em_reais)"
)
# PT: grafia das palavras dos nomes de coluna no título das tabelas.
# EN: spelling of column-name words in table headers.
GRAFIA = {
    "ambigua": "ambígua", "atipica": "atípica", "atribuida": "atribuída", "codigo": "código",
    "correlacao": "correlação", "criterio": "critério", "definicao": "definição",
    "distancia": "distância", "historico": "histórico", "hhi": "HHI", "inadimplencia": "inadimplência",
    "inicio": "início", "ip": "IP", "maxima": "máxima", "media": "média", "mes": "mês",
    "metrica": "métrica", "minima": "mínima", "nao": "não", "ocorrencia": "ocorrência",
    "operacoes": "operações", "padrao": "padrão", "participacao": "participação", "pf": "PF",
    "pix": "PIX", "pj": "PJ", "populacao": "população", "posicao": "posição",
    "problematico": "problemático", "razao": "razão", "selic": "Selic", "uf": "UF", "ufs": "UFs",
    "ultimo": "último", "v1": "V1", "v2": "V2", "variacao": "variação", "variacoes": "variações",
}
# PT: colunas que precisam de três casas, porque o valor perto de um limiar
#     (o z da Q29 perto de 2) não pode parecer do outro lado dele.
# EN: columns shown with three decimals, so a value near a threshold does not
#     look like it is on the other side of it.
TRES_CASAS = {"z", "correlacao", "razao_pix_sobre_carteira"}
TIPOS_INTEIROS = {"INT", "LONG", "SHORT", "BYTE"}
TIPOS_FLUTUANTES = {"DOUBLE", "FLOAT"}


# -----------------------------------------------------------------------------
# PT: Leitura do gabarito
# EN: Reading the answer key
# -----------------------------------------------------------------------------

def carregar(arquivo: Path) -> dict:
    """PT: YAML como dicionário / EN: YAML as a dict"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))


def consultas_do_gabarito(gabarito: dict) -> list[str]:
    """
    PT: Todas as consultas citadas, na ordem em que aparecem e sem repetir,
        porque uma consulta pode servir a mais de uma leitura.
    EN: Every cited query, in order of appearance and without repeats.
    """
    vistas: list[str] = []
    for entrada in gabarito["perguntas"].values():
        for leitura in entrada.get("leituras", []):
            for consulta in leitura["consultas"]:
                if consulta not in vistas:
                    vistas.append(consulta)
    return vistas


# -----------------------------------------------------------------------------
# PT: Consultas ao Databricks
# EN: Databricks queries
# -----------------------------------------------------------------------------

def mes_de_referencia(w, wid: str, catalogo: str, esquema: str) -> str:
    """PT: o último mês do fato principal / EN: the main fact's latest month"""
    resultado = consultar(w, wid, "select cast(max(data_base) as string) from fct_carteira", catalogo, esquema)
    return resultado.linhas[0][0]


def exportar_esquema(w, wid: str, catalogo: str, esquema: str) -> dict[str, list[list[str]]]:
    """
    PT: Colunas e tipos das tabelas do esquema estrela, na ordem do dbt.
    EN: Columns and types of the star schema tables, in dbt order.
    """
    resultado = consultar(
        w,
        wid,
        f"""
        select table_name, column_name, full_data_type
        from {catalogo}.information_schema.columns
        where table_schema = '{esquema}'
          and left(table_name, 4) in ('dim_', 'fct_')
        order by table_name, ordinal_position
        """,
    )
    tabelas: dict[str, list[list[str]]] = {}
    for tabela, coluna, tipo in resultado.linhas:
        tabelas.setdefault(tabela, []).append([coluna, tipo])
    return tabelas


def normalizar(valor: str | None, tipo: str) -> str | None:
    """
    PT: Ponto flutuante com 10 algarismos significativos, para o arquivo não
        mudar por causa da ordem de soma. Decimal e inteiro ficam exatos.
    EN: Floating point to 10 significant digits so summation order does not
        change the file; decimals and integers stay exact.
    """
    if valor is None or tipo not in TIPOS_FLUTUANTES:
        return valor
    return f"{float(valor):.10g}"


def rodar(w, wid: str, catalogo: str, esquema: str, consulta: str) -> Resultado:
    """PT: roda um SQL do gabarito / EN: runs one answer-key SQL"""
    sql = (PASTA_SQL / consulta).read_text(encoding="utf-8")
    resultado = consultar(w, wid, sql, catalogo, esquema)
    linhas = [[normalizar(v, t) for v, t in zip(linha, resultado.tipos)] for linha in resultado.linhas]
    return Resultado(resultado.colunas, resultado.tipos, linhas)


# -----------------------------------------------------------------------------
# PT: Gravação das respostas
# EN: Writing the answers
# -----------------------------------------------------------------------------

def gravar_json(destino: Path, conteudo: dict) -> None:
    """PT: JSON legível e estável / EN: readable, stable JSON"""
    destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def gravar_respostas(respostas: dict[str, Resultado], referencia: str) -> None:
    """
    PT: Um JSON por consulta. Apaga respostas de consultas que saíram do
        gabarito, para não sobrar resposta sem SQL.
    EN: One JSON per query; removes answers whose query left the key.
    """
    PASTA_RESPOSTAS.mkdir(parents=True, exist_ok=True)
    esperadas = {Path(c).with_suffix(".json").name for c in respostas}
    for antiga in PASTA_RESPOSTAS.glob("*.json"):
        if antiga.name not in esperadas:
            antiga.unlink()
    for consulta, resultado in respostas.items():
        gravar_json(
            PASTA_RESPOSTAS / Path(consulta).with_suffix(".json").name,
            {
                "consulta": consulta,
                "mes_de_referencia": referencia,
                "colunas": resultado.colunas,
                "tipos": resultado.tipos,
                "linhas": resultado.linhas,
            },
        )


# -----------------------------------------------------------------------------
# PT: Formatação em português
# EN: Portuguese formatting
# -----------------------------------------------------------------------------

def reais(valor: Decimal) -> str:
    """
    PT: R$ em bi, mi ou unidades, pelo tamanho, com o sinal antes do símbolo.
    EN: R$ scaled by size, with the sign before the symbol.
    """
    sinal = "-" if valor < 0 else ""
    valor = abs(valor)
    if valor >= 10**9:
        return f"{sinal}R$ {numero(valor / 10**9, 1)} bi"
    if valor >= 10**6:
        return f"{sinal}R$ {numero(valor / 10**6, 1)} mi"
    return f"{sinal}R$ {numero(valor, 2)}"


def formatar(coluna: str, tipo: str, valor: str | None) -> str:
    """
    PT: Um valor para a tabela do documento, pela ordem: vazio, booleano,
        data, percentual, pontos percentuais, reais, inteiro e número.
    EN: One value for the document's table, by type and column name.
    """
    if valor is None:
        return ""
    if tipo == "BOOLEAN":
        return "sim" if valor == "true" else "não"
    if tipo == "DATE":
        return mes(valor)
    if tipo == "STRING":
        return valor.replace("|", "\\|")
    if coluna.endswith("_pct"):
        return f"{numero(Decimal(valor), 2)}%"
    if coluna.endswith("_pp"):
        return f"{numero(Decimal(valor), 2)} p.p."
    if DINHEIRO.match(coluna):
        return reais(Decimal(valor))
    if tipo in TIPOS_INTEIROS:
        return numero(Decimal(valor), 0)
    return numero(Decimal(valor), 3 if coluna in TRES_CASAS else 2)


def titulo_da_coluna(coluna: str) -> str:
    """
    PT: Nome legível, sem o sufixo de unidade e com a grafia do português,
        porque os nomes de coluna do SQL não levam acento.
    EN: Readable name, without the unit suffix and with Portuguese spelling,
        since SQL column names carry no accents.
    """
    for sufixo in ("_pct", "_pp"):
        coluna = coluna.removesuffix(sufixo)
    palavras = [GRAFIA.get(p, p) for p in coluna.split("_")]
    return maiuscula(" ".join(palavras))


def tabela(resultado: Resultado) -> str:
    """PT: tabela em Markdown, recolhida se for longa / EN: Markdown table"""
    linhas = [
        "| " + " | ".join(titulo_da_coluna(c) for c in resultado.colunas) + " |",
        "|" + "---|" * len(resultado.colunas),
    ]
    linhas += [
        "| " + " | ".join(formatar(c, t, v) for c, t, v in zip(resultado.colunas, resultado.tipos, linha)) + " |"
        for linha in resultado.linhas
    ]
    texto = "\n".join(linhas)
    if len(resultado.linhas) > LINHAS_VISIVEIS:
        return f"<details><summary>{len(resultado.linhas)} linhas</summary>\n\n{texto}\n\n</details>"
    return texto


# -----------------------------------------------------------------------------
# PT: O documento
# EN: The document
# -----------------------------------------------------------------------------

def lista(itens: list[str]) -> str:
    return "\n".join(f"- {' '.join(i.split())}" for i in itens)


def secao_pergunta(id_: str, pergunta: dict, entrada: dict, respostas: dict[str, Resultado]) -> str:
    """PT: uma pergunta do gabarito / EN: one question of the key"""
    partes = [f"### {id_}. {pergunta['pergunta']}", "", f"**Tipo de acerto:** `{entrada['tipo_de_acerto']}`"]

    if "pendente" in entrada:
        pendente = entrada["pendente"]
        partes += ["", f"**Pendente:** depende de {', '.join(pendente['depende_de'])}. {pendente['motivo']}"]
        return "\n".join(partes) + "\n"

    partes.append("")
    partes.append("**Fonte da definição:** " + ", ".join(f"`{f}`" for f in entrada["fonte"]))

    if entrada["tipo_de_acerto"] == "abstencao":
        partes += [
            "",
            f"**A resposta certa é reconhecer o limite.** {' '.join(entrada['explicacao'].split())}",
            "",
            f"**O que faltaria:** {' '.join(entrada['o_que_faltaria'].split())}",
        ]

    varias = len(entrada.get("leituras", [])) > 1
    for leitura in entrada.get("leituras", []):
        rotulo = f"**Leitura `{leitura['id']}`:**" if varias else "**Como se responde:**"
        partes += ["", f"{rotulo} {' '.join(leitura['descricao'].split())}"]
        for consulta in leitura["consultas"]:
            partes += ["", f"[`{consulta}`](../evaluation/gabarito/{consulta})", "", tabela(respostas[consulta])]

    if entrada.get("ressalva_obrigatoria"):
        partes += ["", "**Ressalva obrigatória:**", "", lista(entrada["ressalva_obrigatoria"])]
    if entrada.get("observacao"):
        partes += ["", f"**Observação:** {' '.join(entrada['observacao'].split())}"]
    return "\n".join(partes) + "\n"


def documento(gabarito: dict, respostas: dict[str, Resultado], referencia: str) -> str:
    """PT: docs/gabarito.md inteiro / EN: the whole docs/gabarito.md"""
    blocos = carregar(PERGUNTAS)["blocos"]
    entradas = gabarito["perguntas"]
    respondiveis = [e for e in entradas.values() if "pendente" not in e]
    leituras = sum(len(e.get("leituras", [])) for e in respondiveis)

    cabecalho = f"""# Gabarito das perguntas do experimento

**Mês de referência:** {mes(referencia)}. Gerado por `scripts/gerar_gabarito.py` a partir de [`evaluation/gabarito.yml`](../evaluation/gabarito.yml) e dos SQL em [`evaluation/gabarito/`](../evaluation/gabarito/). Nenhum número deste documento é digitado à mão: para atualizar, rode o script de novo.

São {len(entradas)} perguntas, do conjunto v2 registrado antes de qualquer execução ([`questions_v2.yml`](../evaluation/questions_v2.yml)). {len(respondiveis)} têm resposta nesta versão, com {leituras} leituras e {len(respostas)} consultas, e {len(entradas) - len(respondiveis)} dependem de fonte ou modelo que ainda não está no projeto.

## Como ler

- **Tipo de acerto.** Em `valor`, acerta quem chega ao número ou à lista. Em `valor_com_ressalva`, acerta quem chega ao número e declara a ressalva obrigatória. Em `abstencao`, acerta quem reconhece que o dado não responde e diz o que faltaria.
- **Leituras aceitas.** Quando a pergunta admite mais de uma interpretação razoável, cada uma tem o próprio SQL e vale como acerto, desde que a resposta diga qual usou. As leituras foram registradas antes de qualquer execução do experimento ([ADR 0015](adr/0015-gabarito-com-leituras-aceitas-em-sql-portatil.md)).
- **Janelas.** Quando a pergunta não diz o período, a mesma consulta traz 12 meses e o recorte inteiro, e vale a janela que a resposta declarar.
- **Unidades.** Taxas e participações em percentual; variações de taxa em pontos percentuais (p.p.); valores em reais.
- **Fonte.** Os ids no formato `arquivo.id` são conceitos e avisos da ontologia, em [`ontology/`](../ontology/).
"""
    secoes = [cabecalho]
    for bloco in blocos:
        secoes.append(f"## {bloco['nome']}\n")
        for pergunta in bloco["perguntas"]:
            secoes.append(secao_pergunta(pergunta["id"], pergunta, entradas[pergunta["id"]], respostas))
    return "\n".join(secoes)


# -----------------------------------------------------------------------------
# PT: Execução
# EN: Entry point
# -----------------------------------------------------------------------------

def main() -> None:
    gabarito = carregar(GABARITO)
    catalogo, esquema = gabarito["metadata"]["catalogo"], gabarito["metadata"]["esquema"]
    w = cliente()
    wid = warehouse(w)

    referencia = mes_de_referencia(w, wid, catalogo, esquema)
    gravar_json(ESQUEMA_ESTRELA, exportar_esquema(w, wid, catalogo, esquema))

    respostas: dict[str, Resultado] = {}
    for consulta in consultas_do_gabarito(gabarito):
        respostas[consulta] = rodar(w, wid, catalogo, esquema, consulta)
        print(f"  {consulta}: {len(respostas[consulta].linhas)} linhas")

    gravar_respostas(respostas, referencia)
    DOCUMENTO.write_text(documento(gabarito, respostas, referencia), encoding="utf-8", newline="\n")
    print(f"  > {DOCUMENTO.relative_to(RAIZ)}: {len(respostas)} consultas, mês de referência {referencia}")


if __name__ == "__main__":
    main()
