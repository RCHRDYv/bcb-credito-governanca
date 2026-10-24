"""
PT: As variações do instrumento (#118, ADR 0032), cumulativas. A V−1 é o
    instrumento da execução 1, intocado, e a V4, o da execução 2. Da V0 em
    diante:

    - V0: chaves com prefixo de letra, para a gramática do Ollama gerar a
      interpretação e o SQL antes da abstenção; a abstenção vira um booleano
      mais o motivo; com SQL não vazio, o SQL roda;
    - V1: a V0 mais o critério de abstenção e dois exemplos num esquema de
      brinquedo, na mensagem do usuário, depois da pergunta;
    - V2: a V1 mais um campo de plano antes do SQL;
    - V3: a V2 mais uma nova tentativa quando o SQL dá erro, para na guarda
      ou volta vazio;
    - V4: a V3 mais as chaves de junção no bloco do esquema;
    - V5: a V4 com a ontologia recuperada em B e D: só os itens mais
      próximos da pergunta (rag/ontologia.py), no lugar da ontologia
      inteira (#120);
    - V6: a V5 com o esquema descrito nas quatro condições: uma frase por
      tabela e por coluna, de assistente/esquema_descrito.yml (#120).

    A mensagem de sistema é a mesma da V−1 nas quatro condições até a V4 (a
    V4 só acrescenta as junções ao bloco do esquema, igual em todas). A
    resposta final mantém os cinco campos registrados em
    comparacao.formato_da_resposta.

EN: The cumulative instrument variants. V−1 is run 1's instrument and V4
    run 2's; V0 prefixes keys so Ollama's grammar emits
    interpretation and SQL before abstaining, with a boolean abstention and
    SQL taking precedence; V1 adds the criterion and toy examples after the
    question; V2 a plan field; V3 one retry on SQL error, guard or empty
    result; V4 join keys in the schema block; V5 the retrieved ontology
    items in B and D; V6 the described schema in all four conditions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from ingestion.fontes import RAIZ
from scripts.validar_gabarito import tipo_no_duckdb

ARQUIVO = RAIZ / "assistente" / "variacoes.yml"
ESQUEMA_DESCRITO = RAIZ / "assistente" / "esquema_descrito.yml"
LETRAS = "abcdefgh"
# PT: os itens da ontologia recuperados por pergunta em B e D, da V5 em
#     diante (#120, decisão de 2026-10-23). Pela cobertura no conjunto de
#     desenvolvimento (scripts/analises/cobertura_da_ontologia.py), a curva
#     fica plana de 5 a 12 itens, em 69,6% dos ids do fonte; o 5 iguala B
#     aos 5 trechos de C.
# EN: ontology items retrieved per question in B and D from V5 on; the
#     dev-set coverage is flat from 5 to 12, and 5 matches C's 5 excerpts.
ITENS_DA_ONTOLOGIA = 5
# PT: corte do erro na mensagem da nova tentativa, em caracteres. A
#     resposta anterior vai inteira: o limite de tokens da resposta já a
#     limita, e o dimensionamento conta essa chamada.
# EN: error cut in the retry message, in characters. The previous answer
#     goes whole; the response token limit bounds it and sizing counts it.
CORTE_DO_ERRO = 600
MAXIMO_DO_PLANO = 1500


@dataclass(frozen=True)
class Variacao:
    """PT: o que uma variação liga / EN: what a variant turns on"""

    nome: str
    chaves_prefixadas: bool = False
    criterio: bool = False
    plano: bool = False
    nova_tentativa: bool = False
    juncoes: bool = False
    ontologia_recuperada: bool = False
    esquema_descrito: bool = False


_V4 = dict(chaves_prefixadas=True, criterio=True, plano=True, nova_tentativa=True, juncoes=True)
VARIACOES = {
    "V-1": Variacao("V-1"),
    "V0": Variacao("V0", chaves_prefixadas=True),
    "V1": Variacao("V1", chaves_prefixadas=True, criterio=True),
    "V2": Variacao("V2", chaves_prefixadas=True, criterio=True, plano=True),
    "V3": Variacao("V3", chaves_prefixadas=True, criterio=True, plano=True, nova_tentativa=True),
    "V4": Variacao("V4", **_V4),
    "V5": Variacao("V5", **_V4, ontologia_recuperada=True),
    "V6": Variacao("V6", **_V4, ontologia_recuperada=True, esquema_descrito=True),
}
ORDEM = list(VARIACOES)


@lru_cache(maxsize=1)
def textos(arquivo: Path = ARQUIVO) -> dict:
    """PT: o variacoes.yml / EN: the variants' texts"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# PT: Chaves e esquemas JSON / EN: keys and JSON schemas
# -----------------------------------------------------------------------------

def campos_da_primeira(v: Variacao) -> list[str]:
    return ["interpretacao", *(["plano"] if v.plano else []), "sql", "abstem", "motivo"]


def campos_da_segunda(v: Variacao) -> list[str]:
    return ["interpretacao", "valores", "ressalva", "abstem", "motivo"]


def prefixadas(campos: list[str]) -> list[str]:
    """
    PT: Os campos com prefixo de letra, na ordem: a_interpretacao, b_sql...
        Em ordem alfabética, ficam na ordem pedida.
    EN: Letter-prefixed fields, alphabetical in the intended order.
    """
    return [f"{LETRAS[i]}_{c}" for i, c in enumerate(campos)]


_TEXTO = {"type": "string"}
_CELULA = {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "null"}]}
_TIPOS = {
    "interpretacao": _TEXTO,
    "plano": {"type": "string", "maxLength": MAXIMO_DO_PLANO},
    "sql": _TEXTO,
    "abstem": {"type": "boolean"},
    "motivo": _TEXTO,
    "ressalva": _TEXTO,
    "valores": {
        "type": "object",
        "properties": {"colunas": {"type": "array", "items": _TEXTO},
                       "linhas": {"type": "array", "items": {"type": "array", "items": _CELULA}}},
        "required": ["colunas", "linhas"],
    },
}


def esquema_json(campos: list[str]) -> dict:
    """PT: o esquema JSON com as chaves prefixadas / EN: prefixed JSON schema"""
    chaves = prefixadas(campos)
    return {"type": "object", "properties": {k: _TIPOS[c] for k, c in zip(chaves, campos)}, "required": chaves}


# -----------------------------------------------------------------------------
# PT: Mensagens / EN: messages
# -----------------------------------------------------------------------------

def _preencher(texto: str, **marcadores: str) -> str:
    for nome, valor in marcadores.items():
        texto = texto.replace("{" + nome + "}", valor)
    return texto


def lista_de_campos(campos: list[str], descricoes: dict[str, str]) -> str:
    return "\n".join(f'- "{k}": {descricoes[c]};' for k, c in zip(prefixadas(campos), campos))


def exemplos(v: Variacao) -> str:
    """
    PT: Os exemplos do esquema de brinquedo, com o JSON nos campos e
        prefixos da variação.
    EN: Toy-schema examples rendered with the variant's fields.
    """
    campos = campos_da_primeira(v)
    partes = []
    for e in textos()["exemplos"]:
        resposta = {k: e[c] for k, c in zip(prefixadas(campos), campos)}
        partes.append(f"Pergunta: {e['pergunta']}\nResposta: {json.dumps(resposta, ensure_ascii=False)}")
    return "\n\n".join(partes)


def mensagem_da_primeira(v: Variacao, pergunta: str) -> str:
    """
    PT: A mensagem do usuário da primeira chamada: a pergunta, os campos e,
        da V1 em diante, o critério com os exemplos, depois da pergunta, e o
        fecho que repete a pergunta.
    EN: First call user message: question, fields and, from V1, criterion,
        examples and a closing line repeating the question.
    """
    t = textos()
    campos = campos_da_primeira(v)
    texto = _preencher(t["primeira_chamada"], pergunta=pergunta,
                       campos=lista_de_campos(campos, t["campos_da_primeira"]))
    if v.criterio:
        texto += "\n\n" + _preencher(t["criterio"], exemplos=exemplos(v))
        texto += "\n\n" + _preencher(t["fecho"], pergunta=pergunta)
    return texto


def mensagem_da_segunda(v: Variacao, resultado: str, aviso: str) -> str:
    t = textos()
    return _preencher(t["segunda_chamada"], resultado=resultado, aviso_do_resultado=aviso,
                      campos=lista_de_campos(campos_da_segunda(v), t["campos_da_segunda"]))


def mensagem_da_nova_tentativa(erro: str | None) -> str:
    """PT: o pedido de nova tentativa, com o erro cortado / EN: retry request"""
    t = textos()
    problema = t["problema_de_vazio"] if erro is None else _preencher(t["problema_de_erro"],
                                                                        erro=erro[:CORTE_DO_ERRO])
    return _preencher(t["nova_tentativa"], problema=problema)


def juncoes(esquema: dict[str, list]) -> str:
    """
    PT: As junções de cada fato com as dimensões, pela chave da dimensão,
        que é a primeira coluna dela no esquema (data_base na dim_tempo,
        codigo_submodalidade na dim_modalidade, uf na dim_uf). Coluna de
        mesmo nome que não é a chave, como cliente na dim_porte, fica fora.
    EN: Each fact's joins to the dimensions by the dimension key, its first
        column; same-name non-key columns stay out.
    """
    colunas = {t: [c for c, _ in cols] for t, cols in esquema.items()}
    chaves = {t: cols[0] for t, cols in colunas.items() if t.startswith("dim_")}
    linhas = [f"{fato}.{chave} = {dim}.{chave}"
              for fato in (t for t in colunas if t.startswith("fct_"))
              for dim, chave in chaves.items() if chave in colunas[fato]]
    return _preencher(textos()["bloco_juncoes"], juncoes="\n".join(linhas))


@lru_cache(maxsize=1)
def descricoes(arquivo: Path = ESQUEMA_DESCRITO) -> dict[str, dict]:
    """PT: as frases de cada tabela e coluna / EN: table and column sentences"""
    return yaml.safe_load(arquivo.read_text(encoding="utf-8"))["tabelas"]


def esquema_descrito(esquema: dict[str, list]) -> str:
    """
    PT: O esquema descrito da V6 (#120): cada tabela com o que uma linha
        representa e cada coluna com o tipo do DuckDB e o que guarda, na
        ordem do esquema. Uma tabela ou coluna sem frase para tudo (KeyError):
        o validar_variacoes confere a cobertura.
    EN: V6's described schema, per table and column, in schema order.
    """
    d = descricoes()
    partes = []
    for tabela, colunas in esquema.items():
        linhas = [f"{tabela}: {d[tabela]['descricao']}"]
        linhas += [f"- {nome} {tipo_no_duckdb(tipo)}: {d[tabela]['colunas'][nome]}" for nome, tipo in colunas]
        partes.append("\n".join(linhas))
    return _preencher(textos()["esquema_descrito"], esquema="\n\n".join(partes))
