"""
PT: Valida o gabarito (evaluation/gabarito.yml), sem precisar de credencial.
    Roda no CI.

    O que é conferido:

    1. **Completude.** As 41 perguntas do conjunto vigente estão no gabarito, e as
       pendentes são exatamente as que a cobertura.yml bloqueia, pela mesma
       issue.
    2. **Tipo de acerto.** É o mesmo do conjunto de perguntas vigente. Toda
       valor_com_ressalva tem ressalva obrigatória, e toda abstencao tem a
       explicação e o que faltaria.
    3. **Leituras.** De 1 a 3 por pergunta respondível, com id único,
       descrição e consultas. Todo SQL citado existe, e nenhum SQL da pasta
       fica sem pergunta.
    4. **O SQL é só leitura e só do esquema estrela.** Uma instrução, que
       começa com select ou with, sem comando de escrita, e que só lê tabelas
       dim_* e fct_*, sem prefixo de catálogo, e só as que a cobertura.yml
       lista para a pergunta. Assim a matriz de cobertura deixa de ser só
       declaração.
    5. **Fonte.** Todo id no formato arquivo.id existe na ontologia, e todo
       documento citado existe.
    6. **Respostas.** Toda consulta tem resposta gerada, e todas do mesmo mês
       de referência.
    7. **Portabilidade.** Todo SQL é planejado pelo DuckDB sobre tabelas
       vazias com as colunas e os tipos do esquema estrela exportado. É o que
       garante que o mesmo gabarito vale quando o experimento rodar no DuckDB
       (#45).

EN: Validates the answer key with no credential; runs in CI. Checks
    completeness against the current question set and the coverage matrix, answer
    types and mandatory caveats, readings and SQL files, that every SQL is a
    read-only query on star schema tables listed in the coverage matrix, that
    every cited ontology id and document exists, that every query has a
    generated answer for the same reference month, and that every SQL plans
    on DuckDB over empty tables with the exported star schema.

Uso / Usage:
    uv run python -m scripts.validar_gabarito
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import duckdb
import yaml

from scripts.validar_perguntas import VIGENTE, perguntas

RAIZ = Path(__file__).resolve().parents[1]
GABARITO = RAIZ / "evaluation" / "gabarito.yml"
COBERTURA = RAIZ / "evaluation" / "cobertura.yml"
PASTA_SQL = RAIZ / "evaluation" / "gabarito"
PASTA_RESPOSTAS = PASTA_SQL / "respostas"
ESQUEMA_ESTRELA = PASTA_SQL / "esquema_estrela.json"
ONTOLOGIA = RAIZ / "ontology"

MAXIMO_DE_LEITURAS = 3
TABELA_DO_ESQUEMA_ESTRELA = re.compile(r"^(dim|fct)_[a-z0-9_]+$")
COMANDO_DE_ESCRITA = re.compile(
    r"\b(insert|update|delete|drop|create|alter|merge|grant|revoke|truncate|attach|copy|pragma|install)\b"
)
DEFINICAO_DE_CTE = re.compile(r"(?:\bwith|,)\s*([a-z_][a-z0-9_]*)\s+as\s*\(")
LEITURA_DE_TABELA = re.compile(r"\b(?:from|join)\s+([a-z_][a-z0-9_.]*)")


# -----------------------------------------------------------------------------
# PT: Leitura dos arquivos
# EN: Reading the files
# -----------------------------------------------------------------------------

def carregar(arquivo: Path) -> dict:
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))


def ids_da_ontologia() -> dict[str, set[str]]:
    """
    PT: Ids de cada arquivo da ontologia, de todas as listas de primeiro
        nível: conceitos, avisos, dimensões e fontes.
    EN: Ids of each ontology file, from every top-level list.
    """
    ids: dict[str, set[str]] = {}
    for arquivo in sorted(ONTOLOGIA.glob("*.yml")):
        conteudo = carregar(arquivo)
        ids[arquivo.stem] = {
            item["id"]
            for valor in conteudo.values()
            if isinstance(valor, list)
            for item in valor
            if isinstance(item, dict) and "id" in item
        }
    return ids


def sql_sem_comentarios(arquivo: Path) -> str:
    """PT: SQL em minúsculas, sem comentários de linha / EN: lowercased SQL"""
    linhas = [linha.split("--", 1)[0] for linha in arquivo.read_text(encoding="utf-8").splitlines()]
    return "\n".join(linhas).strip().lower()


# -----------------------------------------------------------------------------
# PT: Checagens
# EN: Checks
# -----------------------------------------------------------------------------

def checar_completude(gabarito: dict, por_id: dict, cobertura: dict) -> list[str]:
    """PT: todas as perguntas, e as pendentes certas / EN: all ids, right pending ones"""
    ids = set(gabarito["perguntas"])
    erros = [f"pergunta fora do gabarito: {i}" for i in sorted(set(por_id) - ids)]
    erros += [f"id no gabarito que não existe no conjunto de perguntas: {i}" for i in sorted(ids - set(por_id))]
    for id_ in sorted(ids & set(por_id)):
        bloqueio = sorted(cobertura["perguntas"][id_].get("depende_de", []))
        pendente = sorted(gabarito["perguntas"][id_].get("pendente", {}).get("depende_de", []))
        if bloqueio != pendente:
            erros.append(f"{id_}: pendente no gabarito por {pendente or 'nada'}, bloqueada na cobertura por {bloqueio or 'nada'}")
    return erros


def checar_entrada(id_: str, entrada: dict, pergunta: dict) -> list[str]:
    """PT: tipo, ressalva, abstenção e leituras / EN: type, caveat and readings"""
    erros = []
    tipo = pergunta.get("tipo_de_acerto", "valor")
    if entrada.get("tipo_de_acerto") != tipo:
        erros.append(f"{id_}: tipo_de_acerto '{entrada.get('tipo_de_acerto')}', o conjunto de perguntas diz '{tipo}'")
    if "pendente" in entrada:
        if not entrada["pendente"].get("motivo"):
            erros.append(f"{id_}: pendente sem motivo")
        return erros

    if not entrada.get("fonte"):
        erros.append(f"{id_}: sem fonte da definição")
    if tipo == "valor_com_ressalva" and not entrada.get("ressalva_obrigatoria"):
        erros.append(f"{id_}: valor_com_ressalva sem ressalva_obrigatoria")
    if tipo == "abstencao" and not (entrada.get("explicacao") and entrada.get("o_que_faltaria")):
        erros.append(f"{id_}: abstencao sem explicacao ou sem o_que_faltaria")

    leituras = entrada.get("leituras", [])
    minimo = 0 if tipo == "abstencao" else 1
    if not minimo <= len(leituras) <= MAXIMO_DE_LEITURAS:
        erros.append(f"{id_}: {len(leituras)} leituras, o permitido é de {minimo} a {MAXIMO_DE_LEITURAS}")
    ids_de_leitura = [leitura.get("id") for leitura in leituras]
    if len(set(ids_de_leitura)) != len(ids_de_leitura):
        erros.append(f"{id_}: id de leitura repetido")
    for leitura in leituras:
        if not leitura.get("descricao") or not leitura.get("consultas"):
            erros.append(f"{id_} leitura '{leitura.get('id')}': sem descrição ou sem consultas")
    return erros


def checar_sql(id_: str, arquivo: Path, modelos_da_pergunta: set[str]) -> list[str]:
    """
    PT: Só leitura, uma instrução, e só tabelas do esquema estrela que a
        cobertura lista para a pergunta.
    EN: Read-only, one statement, and only star schema tables the coverage
        matrix lists for the question.
    """
    if not arquivo.exists():
        return [f"{id_}: SQL inexistente {arquivo.name}"]
    sql = sql_sem_comentarios(arquivo)
    erros = []
    if not sql.startswith(("select", "with")):
        erros.append(f"{arquivo.name}: não começa com select nem with")
    if ";" in sql:
        erros.append(f"{arquivo.name}: tem ponto e vírgula; o gabarito aceita uma instrução só")
    if comando := COMANDO_DE_ESCRITA.search(sql):
        erros.append(f"{arquivo.name}: comando proibido '{comando.group(1)}'")

    ctes = set(DEFINICAO_DE_CTE.findall(sql))
    tabelas = {t for t in LEITURA_DE_TABELA.findall(sql) if t not in ctes}
    for tabela in sorted(tabelas):
        if not TABELA_DO_ESQUEMA_ESTRELA.match(tabela):
            erros.append(f"{arquivo.name}: lê '{tabela}', fora do esquema estrela ou com prefixo")
        elif tabela not in modelos_da_pergunta:
            erros.append(f"{arquivo.name}: lê '{tabela}', que a cobertura.yml não lista para {id_}")
    return erros


def checar_fontes(id_: str, fontes: list[str], ontologia: dict[str, set[str]]) -> list[str]:
    """PT: id da ontologia ou documento que existe / EN: existing id or document"""
    erros = []
    for fonte in fontes:
        if "/" in fonte:
            if not (RAIZ / fonte).exists():
                erros.append(f"{id_}: documento citado não existe: {fonte}")
            continue
        arquivo, _, conceito = fonte.partition(".")
        if conceito not in ontologia.get(arquivo, set()):
            erros.append(f"{id_}: fonte '{fonte}' não existe na ontologia")
    return erros


def checar_respostas(consultas: list[str]) -> tuple[list[str], set[str]]:
    """PT: toda consulta respondida, no mesmo mês / EN: every query answered"""
    erros, meses = [], set()
    for consulta in consultas:
        arquivo = PASTA_RESPOSTAS / Path(consulta).with_suffix(".json").name
        if not arquivo.exists():
            erros.append(f"{consulta}: sem resposta gerada; rode scripts.gerar_gabarito")
            continue
        resposta = json.loads(arquivo.read_text(encoding="utf-8"))
        if resposta.get("consulta") != consulta:
            erros.append(f"{arquivo.name}: diz ser de '{resposta.get('consulta')}'")
        meses.add(resposta.get("mes_de_referencia"))
    if len(meses) > 1:
        erros.append(f"respostas de meses de referência diferentes: {sorted(meses)}")
    return erros, meses


def tipo_no_duckdb(tipo: str) -> str:
    """PT: tipo do Databricks para o DuckDB / EN: Databricks type to DuckDB"""
    return {"string": "VARCHAR"}.get(tipo, tipo.upper())


def checar_portabilidade(consultas: list[str]) -> list[str]:
    """
    PT: Cada SQL precisa ser planejado pelo DuckDB sobre tabelas vazias com o
        esquema exportado: função, tipo ou sintaxe que só o Databricks aceita
        falha aqui.
    EN: Every SQL must plan on DuckDB over empty tables with the exported
        schema: Databricks-only functions, types or syntax fail here.
    """
    if not ESQUEMA_ESTRELA.exists():
        return ["esquema_estrela.json não existe; rode scripts.gerar_gabarito"]
    banco = duckdb.connect()
    for tabela, colunas in json.loads(ESQUEMA_ESTRELA.read_text(encoding="utf-8")).items():
        definicao = ", ".join(f"{nome} {tipo_no_duckdb(tipo)}" for nome, tipo in colunas)
        banco.execute(f"create table {tabela} ({definicao})")

    erros = []
    for consulta in consultas:
        arquivo = PASTA_SQL / consulta
        if not arquivo.exists():
            continue
        try:
            banco.execute("explain " + arquivo.read_text(encoding="utf-8"))
        except duckdb.Error as erro:
            erros.append(f"{consulta}: não roda no DuckDB: {str(erro).splitlines()[0]}")
    return erros


# -----------------------------------------------------------------------------
# PT: Execução
# EN: Entry point
# -----------------------------------------------------------------------------

def main() -> None:
    gabarito = carregar(GABARITO)
    cobertura = carregar(COBERTURA)
    _, por_id = perguntas(VIGENTE)
    ontologia = ids_da_ontologia()

    erros = checar_completude(gabarito, por_id, cobertura)
    consultas: list[str] = []
    for id_, entrada in gabarito["perguntas"].items():
        if id_ not in por_id:
            continue
        erros += checar_entrada(id_, entrada, por_id[id_])
        erros += checar_fontes(id_, entrada.get("fonte", []), ontologia)
        modelos = set(cobertura["perguntas"].get(id_, {}).get("modelos", []))
        for leitura in entrada.get("leituras", []):
            for consulta in leitura.get("consultas", []):
                erros += checar_sql(id_, PASTA_SQL / consulta, modelos)
                if consulta not in consultas:
                    consultas.append(consulta)

    orfaos = sorted({p.name for p in PASTA_SQL.glob("*.sql")} - set(consultas))
    erros += [f"SQL sem pergunta no gabarito: {o}" for o in orfaos]

    erros_de_resposta, meses = checar_respostas(consultas)
    erros += erros_de_resposta
    erros += checar_portabilidade(consultas)

    pendentes = [i for i, e in gabarito["perguntas"].items() if "pendente" in e]
    leituras = sum(len(e.get("leituras", [])) for e in gabarito["perguntas"].values())
    print(f"  perguntas: {len(gabarito['perguntas'])}, {len(gabarito['perguntas']) - len(pendentes)} respondíveis, "
          f"{len(pendentes)} pendentes ({', '.join(pendentes)})")
    print(f"  leituras: {leituras}, consultas: {len(consultas)}, mês de referência: {', '.join(sorted(m for m in meses if m))}")

    if erros:
        print("\nFALHOU / FAILED:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print("\nGabarito completo, coerente e portátil / answer key complete, consistent and portable.")


if __name__ == "__main__":
    main()
