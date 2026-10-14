"""
PT: A correção às cegas (evaluation/hipoteses.yml, comparacao.correcao),
    no terminal, um item por vez (decisão de 2026-10-09).

    Julgo só o que o script não decide e que ainda pode mudar o acerto da
    pergunta (correcao.acerto.a_julgar):

    - ressalva: a ressalva declara o fato da ressalva obrigatória do
      gabarito, com paráfrase permitida;
    - abstencao: a resposta se abstém e diz o que faltaria, como a
      explicação e o o_que_faltaria do gabarito;
    - leitura_declarada: a interpretação declarada é a leitura, ou a janela,
      que bateu.

    Cegamento: o item mostra a pergunta, a rubrica, a interpretação, os
    valores, a ressalva e a abstenção, e nada do modelo, da condição, do SQL
    ou dos trechos. Citações no texto (id da ontologia, documento, seção,
    página, trecho) são retiradas antes. Os itens vêm embaralhados entre
    candidatos e perguntas, por um identificador opaco.

    Cada julgamento é gravado na hora em data/selecao/julgamentos.json, e o
    comando retoma de onde parou. Depois de cada julgamento, uma pergunta
    que ficou decidida sai da fila.

    Com --experimento (#50, ADR 0031), lê data/experimento/ e julga todas
    as execuções pendentes, decididas ou não, para a contagem de 0 a 5 sair
    exata (decisão 1 de 2026-10-14). Execuções com a mesma visão cega (o que
    o item mostra, mais os aspectos a julgar e as leituras que bateram)
    viram um item só, e o julgamento vale para todas elas. A visão não tem
    modelo nem condição, e os itens vêm embaralhados por ela.

EN: Blind grading in the terminal, one item at a time. Only what the script
    cannot decide and can still change a question's result is judged:
    caveat, abstention and declared reading. Items show the question, the
    rubric and the answer fields, never the model, condition, SQL or
    excerpts; citations are stripped; items are shuffled under opaque ids.
    Each judgment is saved at once and the command resumes where it stopped.
    --experimento judges every pending run of the experiment, merging runs
    with the same blind view into one item.

Uso / Usage:
    uv run python -m correcao.as_cegas
    uv run python -m correcao.as_cegas --experimento
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path

from correcao.acerto import (
    PADRAO_DA_SELECAO,
    PADRAO_DO_EXPERIMENTO,
    PASTA_DA_SELECAO,
    PASTA_DO_EXPERIMENTO,
    a_julgar,
    acerto_da_execucao,
    corrigir_todas,
    execucoes_vigentes,
    ler_execucoes,
    ler_julgamentos,
)
from correcao.corretor import Gabarito, carregar_gabarito
from scripts.validar_perguntas import VIGENTE, perguntas

LIMITE_DE_LINHAS = 30
JANELAS = {"12_meses": "12 meses", "recorte": "o recorte inteiro", "ultimo_mes": "o último mês"}

PERGUNTAS_DO_ASPECTO = {
    "ressalva": "A ressalva declara o fato da ressalva obrigatória, com paráfrase permitida?",
    "abstencao": "A resposta se abstém e diz o que faltaria, como a rubrica?",
    "leitura_declarada": "A interpretação declarada é a leitura (e a janela) que bateu?",
}

# PT: citações que entregariam a condição: id da ontologia no formato
#     arquivo.id, marcas de trecho e referências a documento, seção e página.
# EN: citations that would reveal the condition.
_CITACOES = [
    re.compile(r"\b(?:metricas|modalidades|dimensoes|fontes_externas)\.[A-Za-z0-9_]+"),
    re.compile(r"\[[^\]]*\b(?:trecho|seção|secao|página|pagina|documento|fonte)\b[^\]]*\]", re.IGNORECASE),
    re.compile(r"\([^)]*\b(?:trecho|seção|secao|página|pagina|documento|fonte)\b[^)]*\)", re.IGNORECASE),
    re.compile(r"\b(?:página|pagina|p\.)\s*\d+", re.IGNORECASE),
    re.compile(r"\btrecho\s*\d+", re.IGNORECASE),
]


# PT: referências à fonte do contexto, que também entregam a condição ("a
#     ontologia indica", "o documento de metodologia menciona", "nos trechos
#     recuperados"). Viram "o contexto", com a contração do artigo original;
#     o conteúdo da frase fica (decisão 11 de 2026-10-14, ADR 0031).
# EN: references to the context source, which also reveal the condition;
#     replaced by "o contexto", keeping the article's contraction.
_FONTES = re.compile(
    r"\b(o|a|os|as|no|na|nos|nas|do|da|dos|das|pelo|pela|pelos|pelas)\s+"
    r"(?:ontologia(?:\s+do\s+projeto)?|documenta[cç][aã]o|"
    r"documentos?(?:\s+(?:de|da|do)\s+metodologia)?(?:\s+\d{3,4})?|"
    r"trechos?(?:\s+(?:recuperados?|fornecidos?|de\s+documentos?))?)\b",
    re.IGNORECASE,
)
_CONTRACAO = {"o": "o", "a": "o", "os": "o", "as": "o", "no": "no", "na": "no", "nos": "no", "nas": "no",
              "do": "do", "da": "do", "dos": "do", "das": "do", "pelo": "pelo", "pela": "pelo", "pelos": "pelo",
              "pelas": "pelo"}


def _contexto(achado: re.Match) -> str:
    artigo = achado.group(1)
    troca = f"{_CONTRACAO[artigo.lower()]} contexto"
    return troca[0].upper() + troca[1:] if artigo[0].isupper() else troca


def sem_citacoes(texto: str) -> str:
    """
    PT: O texto sem as citações e com a fonte do contexto neutralizada.
    EN: Text without citations, with the context source neutralized.
    """
    for padrao in _CITACOES:
        texto = padrao.sub("", texto)
    texto = _FONTES.sub(_contexto, texto)
    return re.sub(r"[ \t]{2,}", " ", texto).strip()


def ordem_embaralhada(item: str) -> str:
    """
    PT: Chave de ordem estável e sem relação com o candidato.
    EN: Stable order key unrelated to the candidate.
    """
    return hashlib.sha256(f"embaralhar|{item}".encode("utf-8")).hexdigest()


def rubrica(aspecto: str, pergunta: str, correcao: dict, g: Gabarito) -> str:
    """PT: o texto da rubrica do aspecto / EN: the aspect's rubric text"""
    gabarito = g.perguntas[pergunta]
    if aspecto == "ressalva":
        return "Ressalva obrigatória:\n" + "\n".join(f"  - {r.strip()}" for r in gabarito["ressalva_obrigatoria"])
    if aspecto == "abstencao":
        return (f"Explicação: {gabarito['explicacao'].strip()}\n"
                f"O que faltaria: {gabarito['o_que_faltaria'].strip()}")
    descricoes = {l["id"]: " ".join(l["descricao"].split()) for l in gabarito.get("leituras", [])}
    linhas = []
    for b in correcao["leituras_que_batem"]:
        janela = f", na janela de {JANELAS.get(b['janela'], b['janela'])}" if b["janela"] else ""
        linhas.append(f"  - {descricoes.get(b['leitura'], b['leitura'])}{janela}")
    return "Leituras que bateram com os valores:\n" + "\n".join(linhas)


def tabela(valores: dict) -> str:
    """PT: os valores em texto, cortados / EN: values as text, truncated"""
    colunas, linhas = valores.get("colunas") or [], valores.get("linhas") or []
    if not colunas:
        return "  (sem valores)"
    texto = ["  " + " | ".join(sem_citacoes(str(c)) for c in colunas)]
    texto += ["  " + " | ".join("" if v is None else sem_citacoes(str(v)) for v in l) for l in linhas[:LIMITE_DE_LINHAS]]
    if len(linhas) > LIMITE_DE_LINHAS:
        texto.append(f"  ... mais {len(linhas) - LIMITE_DE_LINHAS} linhas")
    return "\n".join(texto)


def visao_cega(c: dict, registro: dict) -> str:
    """
    PT: Identificador da visão cega de uma execução: o que o item mostra
        (pergunta, interpretação, valores, ressalva e abstenção, sem
        citações e com o mesmo corte de linhas), os aspectos a julgar e as
        leituras que bateram, que formam a rubrica. Duas execuções com a
        mesma visão recebem o mesmo julgamento. Nada do modelo, da condição,
        do SQL ou dos trechos entra.
    EN: Id of a run's blind view: what the item shows plus the aspects to
        judge and the matching readings; never model, condition, SQL or
        excerpts.
    """
    resposta = registro.get("resposta") or {}
    visao = {
        "pergunta": c["pergunta"],
        "julgar": c["correcao"]["julgar"],
        "leituras_que_batem": c["correcao"]["leituras_que_batem"],
        "interpretacao": sem_citacoes(resposta.get("interpretacao") or ""),
        "valores": tabela(resposta.get("valores") or {}),
        "ressalva": sem_citacoes(resposta.get("ressalva") or ""),
        "abstencao": sem_citacoes(resposta.get("abstencao") or ""),
    }
    texto = json.dumps(visao, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(f"visao|{texto}".encode("utf-8")).hexdigest()[:16]


def mostrar(c: dict, registro: dict, enunciado: str, g: Gabarito, faltam: int) -> None:
    resposta = registro.get("resposta") or {}
    print("\n" + "=" * 78)
    print(f"Item {c['item']}  (faltam {faltam})")
    print(f"\nPergunta: {enunciado}")
    print(f"\nInterpretação: {sem_citacoes(resposta.get('interpretacao') or '')}")
    print(f"\nValores:\n{tabela(resposta.get('valores') or {})}")
    print(f"\nRessalva: {sem_citacoes(resposta.get('ressalva') or '') or '(vazia)'}")
    print(f"Abstenção: {sem_citacoes(resposta.get('abstencao') or '') or '(vazia)'}")


def perguntar(texto: str) -> bool | None:
    """PT: s, n ou q / EN: yes, no or quit"""
    while True:
        escolha = input(f"\n{texto} [s/n, q para sair] ").strip().lower()
        if escolha in ("s", "n"):
            return escolha == "s"
        if escolha == "q":
            return None


def gravar(julgamentos: dict, pasta: Path) -> None:
    arquivo = pasta / "julgamentos.json"
    arquivo.write_text(json.dumps(julgamentos, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experimento", action="store_true",
                        help="julga as execuções do experimento (#50), todas as pendentes")
    parser.add_argument("--pasta", type=Path, default=None)
    args = parser.parse_args()

    g = carregar_gabarito()
    _, por_id = perguntas(VIGENTE)
    if args.experimento:
        from scripts.executar_experimento import modelos_do_experimento

        pasta = args.pasta or PASTA_DO_EXPERIMENTO
        candidatos = [m["nome"] for m in modelos_do_experimento()]
        lidas, comando = ler_execucoes(pasta, PADRAO_DO_EXPERIMENTO), "scripts.executar_experimento"
    else:
        from scripts.selecionar_modelos import carregar_selecao

        pasta = args.pasta or PASTA_DA_SELECAO
        candidatos = [c["nome"] for c in carregar_selecao()["candidatos"]]
        lidas, comando = ler_execucoes(pasta, PADRAO_DA_SELECAO), "scripts.selecionar_modelos"
    execucoes = execucoes_vigentes(lidas, candidatos, list(por_id))
    if not execucoes:
        raise SystemExit(f"ERRO nenhuma execução em {pasta / 'execucoes'}: rode {comando}")

    def chave(candidato: str, condicao: str | None, pergunta: str, seed: int) -> tuple:
        return (candidato, condicao if args.experimento else None, pergunta, seed)

    registros = {chave(r["candidato"], r.get("condicao"), r["id_pergunta"], r["seed"]): r for r in execucoes}
    julgamentos = ler_julgamentos(pasta)
    # PT: a correção do script não muda com o julgamento: roda uma vez, e só
    #     a situação dos itens julgados é refeita.
    # EN: script grading does not change with judgments: run it once.
    corrigidas = corrigir_todas(execucoes, julgamentos, g, com_condicao=args.experimento)

    def registro_de(c: dict) -> dict:
        return registros[chave(c["candidato"], c.get("condicao"), c["pergunta"], c["seed"])]

    # PT: a visão de uma execução não muda com os julgamentos: calcula uma
    #     vez por item.
    # EN: a run's blind view never changes: computed once per item.
    visoes: dict[str, str] = {}

    def visao_de(c: dict) -> str:
        if c["item"] not in visoes:
            visoes[c["item"]] = visao_cega(c, registro_de(c))
        return visoes[c["item"]]

    while True:
        fila = a_julgar(corrigidas, todas=args.experimento)
        if not fila:
            print("\nNada mais a julgar / nothing left to judge.")
            return
        if args.experimento:
            # PT: um item por visão cega; o julgamento vale para o grupo.
            # EN: one item per blind view; the judgment applies to the group.
            grupos: dict[str, list[dict]] = {}
            for c in fila:
                grupos.setdefault(visao_de(c), []).append(c)
            rotulo = min(grupos, key=ordem_embaralhada)
            itens, faltam = grupos[rotulo], len(grupos)
        else:
            primeiro = min(fila, key=lambda c: ordem_embaralhada(c["item"]))
            rotulo, itens, faltam = primeiro["item"], [primeiro], len(fila)
        c = itens[0]
        mostrar({**c, "item": rotulo}, registro_de(c), por_id[c["pergunta"]]["pergunta"], g, faltam)
        for aspecto in c["correcao"]["julgar"]:
            if all(aspecto in (julgamentos.get(i["item"]) or {}) for i in itens):
                continue
            print("\n" + rubrica(aspecto, c["pergunta"], c["correcao"], g))
            resposta = perguntar(PERGUNTAS_DO_ASPECTO[aspecto])
            if resposta is None:
                print("Parado. Os julgamentos feitos estão gravados / stopped; judgments saved.")
                return
            agora = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            for i in itens:
                julgamento = dict(julgamentos.get(i["item"]) or {})
                julgamento[aspecto] = resposta
                julgamento["data"] = agora
                if args.experimento:
                    julgamento["visao"] = rotulo
                julgamentos[i["item"]] = julgamento
                i["julgamento"] = julgamento
                i["situacao"] = acerto_da_execucao(i["correcao"], julgamento)
            gravar(julgamentos, pasta)
            if not resposta:
                break


if __name__ == "__main__":
    main()
