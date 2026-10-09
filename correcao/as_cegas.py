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

EN: Blind grading in the terminal, one item at a time. Only what the script
    cannot decide and can still change a question's result is judged:
    caveat, abstention and declared reading. Items show the question, the
    rubric and the answer fields, never the model, condition, SQL or
    excerpts; citations are stripped; items are shuffled under opaque ids.
    Each judgment is saved at once and the command resumes where it stopped.

Uso / Usage:
    uv run python -m correcao.as_cegas
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path

from correcao.acerto import (
    PASTA_DA_SELECAO,
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


def sem_citacoes(texto: str) -> str:
    """PT: o texto sem as citações / EN: text without citations"""
    for padrao in _CITACOES:
        texto = padrao.sub("", texto)
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
    texto += ["  " + " | ".join("" if v is None else str(v) for v in l) for l in linhas[:LIMITE_DE_LINHAS]]
    if len(linhas) > LIMITE_DE_LINHAS:
        texto.append(f"  ... mais {len(linhas) - LIMITE_DE_LINHAS} linhas")
    return "\n".join(texto)


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
    parser.add_argument("--pasta", type=Path, default=PASTA_DA_SELECAO)
    args = parser.parse_args()

    g = carregar_gabarito()
    _, por_id = perguntas(VIGENTE)
    from scripts.selecionar_modelos import carregar_selecao

    candidatos = [c["nome"] for c in carregar_selecao()["candidatos"]]
    execucoes = execucoes_vigentes(ler_execucoes(args.pasta), candidatos, list(por_id))
    if not execucoes:
        raise SystemExit(f"ERRO nenhuma execução em {args.pasta / 'execucoes'}: rode scripts.selecionar_modelos")
    registros = {(r["candidato"], r["id_pergunta"], r["seed"]): r for r in execucoes}
    julgamentos = ler_julgamentos(args.pasta)
    # PT: a correção do script não muda com o julgamento: roda uma vez, e só
    #     a situação do item julgado é refeita.
    # EN: script grading does not change with judgments: run it once.
    corrigidas = corrigir_todas(execucoes, julgamentos, g)

    while True:
        fila = sorted(a_julgar(corrigidas), key=lambda c: ordem_embaralhada(c["item"]))
        if not fila:
            print("\nNada mais a julgar / nothing left to judge.")
            return
        c = fila[0]
        registro = registros[(c["candidato"], c["pergunta"], c["seed"])]
        mostrar(c, registro, por_id[c["pergunta"]]["pergunta"], g, len(fila))
        julgamento = dict(julgamentos.get(c["item"]) or {})
        for aspecto in c["correcao"]["julgar"]:
            if aspecto in julgamento:
                continue
            print("\n" + rubrica(aspecto, c["pergunta"], c["correcao"], g))
            resposta = perguntar(PERGUNTAS_DO_ASPECTO[aspecto])
            if resposta is None:
                print("Parado. Os julgamentos feitos estão gravados / stopped; judgments saved.")
                return
            julgamento[aspecto] = resposta
            julgamento["data"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            julgamentos[c["item"]] = julgamento
            gravar(julgamentos, args.pasta)
            c["julgamento"] = julgamento
            c["situacao"] = acerto_da_execucao(c["correcao"], julgamento)
            if not resposta:
                break


if __name__ == "__main__":
    main()
