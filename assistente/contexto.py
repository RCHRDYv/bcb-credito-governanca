"""
PT: Montagem do prompt por condição (ADR 0013; evaluation/hipoteses.yml,
    condicoes). As quatro condições usam o mesmo texto de
    assistente/modelo_de_prompt.yml; só os blocos de contexto entram ou
    saem, sempre na ordem esquema, ontologia, trechos. Por construção:

    - A leva só o esquema cru: tabelas, colunas e tipos, sem descrição;
    - B é A mais a ontologia, e C é A mais os trechos;
    - D é exatamente B mais o mesmo bloco de trechos de C.

    Os trechos vêm de uma busca só, antes da geração, com o enunciado como
    está, sem reescrita; o modelo não chama a busca. Quem busca é quem chama
    o assistente, para que C e D da mesma pergunta recebam os mesmos
    trechos.

EN: Prompt assembly per condition. All four use the same template; only the
    context blocks go in or out, in the order schema, ontology, excerpts. By
    construction D is exactly B plus C's excerpts block. Excerpts come from
    one search before generation, with the question as is; the caller
    searches, so C and D of a question get the same excerpts.
"""

from __future__ import annotations

import json

from assistente import ontologia
from assistente.parametros import CONDICOES
from scripts.esquema_estrela_duckdb import esquema_esperado
from scripts.validar_gabarito import tipo_no_duckdb


def preencher(texto: str, **marcadores: str) -> str:
    """
    PT: Troca cada {nome} pelo valor. Não usa str.format porque o modelo de
        prompt traz chaves literais de JSON.
    EN: Replaces each {nome}; not str.format, the template has literal JSON
        braces.
    """
    for nome, valor in marcadores.items():
        texto = texto.replace("{" + nome + "}", valor)
    return texto


def texto_do_esquema() -> str:
    """
    PT: O esquema cru, uma linha por tabela, com os tipos do DuckDB, que é
        onde o SQL roda.
    EN: The raw schema, one line per table, with DuckDB types.
    """
    return "\n".join(
        f"{tabela}({', '.join(f'{nome} {tipo_no_duckdb(tipo)}' for nome, tipo in colunas)})"
        for tabela, colunas in esquema_esperado().items()
    )


def texto_dos_trechos(trechos: list[dict]) -> str:
    """
    PT: Os trechos com documento, título, seção e página, para o modelo
        poder citá-los.
    EN: Excerpts with document, title, section and page.
    """
    partes = []
    for t in trechos:
        onde = [t["documento"]]
        if t.get("titulo"):
            onde.append(t["titulo"])
        if t.get("secao"):
            onde.append(f"seção {t['secao']}")
        if t.get("pagina"):
            onde.append(f"página {t['pagina']}")
        partes.append(f"[trecho {t['trecho']}] {', '.join(onde)}\n{t['texto']}")
    return "\n\n".join(partes)


def sistema(condicao: str, modelo: dict[str, str], trechos: list[dict] | None = None) -> str:
    """
    PT: A mensagem de sistema da condição: as instruções comuns e os blocos.
    EN: The condition's system message: shared instructions and blocks.
    """
    blocos = CONDICOES[condicao]
    if "trechos" in blocos and trechos is None:
        raise ValueError(f"a condição {condicao} precisa dos trechos da busca")
    textos = {
        "esquema": lambda: preencher(modelo["bloco_esquema"], esquema=texto_do_esquema()),
        "ontologia": lambda: preencher(modelo["bloco_ontologia"], ontologia=ontologia.bloco()),
        "trechos": lambda: preencher(modelo["bloco_trechos"], trechos=texto_dos_trechos(trechos or [])),
    }
    return "\n\n".join([modelo["instrucoes"], *(textos[b]() for b in blocos)])


def primeira_chamada(condicao: str, pergunta: str, modelo: dict[str, str],
                     trechos: list[dict] | None = None) -> list[dict]:
    """PT: mensagens da primeira chamada / EN: first call messages"""
    return [
        {"role": "system", "content": sistema(condicao, modelo, trechos)},
        {"role": "user", "content": preencher(modelo["primeira_chamada"], pergunta=pergunta)},
    ]


def segunda_chamada(mensagens: list[dict], resposta_bruta: str, resultado: dict,
                    modelo: dict[str, str]) -> list[dict]:
    """
    PT: As mensagens da primeira chamada, a resposta do modelo como veio e o
        resultado do SQL, com o aviso de corte quando houver.
    EN: First call messages, the model's raw answer and the SQL result, with
        the cut notice when there is one.
    """
    aviso = ""
    if resultado["cortado"]:
        aviso = f" (resultado cortado em {len(resultado['linhas'])} de {resultado['total_de_linhas']} linhas)"
    tabela = json.dumps({"colunas": resultado["colunas"], "linhas": resultado["linhas"]}, ensure_ascii=False)
    return [
        *mensagens,
        {"role": "assistant", "content": resposta_bruta},
        {"role": "user", "content": preencher(modelo["segunda_chamada"], resultado=tabela,
                                              aviso_do_resultado=aviso)},
    ]


def buscar_trechos(pergunta: str) -> list[dict]:
    """
    PT: Os trechos do RAG para a pergunta, com o título da seção, que o
        rag.indice.buscar não devolve. Precisa do grupo rag do uv; o import
        fica aqui dentro para que A e B rodem sem o torch.
    EN: RAG excerpts for the question, with the section title. Needs the rag
        group; imported here so A and B run without torch.
    """
    from rag.indice import buscar, carregar_indice, modelo_escolhido

    titulos = dict(carregar_indice(modelo_escolhido())[0].select("trecho", "titulo").iter_rows())
    return [{**t, "titulo": titulos.get(t["trecho"])} for t in buscar(pergunta)]
