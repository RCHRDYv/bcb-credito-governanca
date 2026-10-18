"""
PT: QA da correção de 2026-10-15 no corretor (#118, ADR 0032). O
    _identificar escolhia, no empate em itens achados, a primeira coluna da
    resposta, e uma coluna de posição (1, 2, 3) ganhava da coluna do código
    ("01", "02", "03"), trocando os itens. A correção desempata pelas células
    iguais ao texto do gabarito.

    Este script recorrige, com o _identificar de antes (copiado aqui, sem
    import do commit antigo) e com o de agora, os registros que já foram
    corrigidos:

    - as execuções publicadas da seleção (#48,
      evaluation/selecao/execucoes.jsonl.gz);
    - as da execução 1 do experimento (data/experimento/), quando a pasta
      existe na máquina.

    Antes, confere que a cópia de antes reproduz o defeito no caso de
    regressão do validar_selecao, e a de agora não. Mostra quantas
    correções mudam e em quais perguntas, e sai com erro se
    alguma situação (certo, errado, pendente) mudar: nesse caso a correção
    mexe num resultado já registrado e pede errata própria.

EN: QA of the 2026-10-15 grader fix. Re-grades the published selection runs
    and, when present, run 1 of the experiment with the old tie-break (copied
    here) and the new one, and fails if any run's situation changes.

Uso / Usage:
    uv run python -m scripts.analises.qa_corretor
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from unittest import mock

from correcao import corretor
from correcao.acerto import PADRAO_DO_EXPERIMENTO, ler_execucoes
from correcao.corretor import Consulta, Tabela, carregar_gabarito, corrigir
from scripts.executar_experimento import PASTA_DO_EXPERIMENTO
from scripts.validar_registro import RAIZ
from scripts.validar_selecao import checar_posicao_contra_codigo

SELECAO = RAIZ / "evaluation" / "selecao" / "execucoes.jsonl.gz"


def identificar_de_antes(tabela: Tabela, consulta: Consulta, chave: str) -> dict[int, set[int]]:
    """
    PT: O _identificar do commit b6023f1, sem o desempate: no empate em
        itens achados, fica a primeira coluna.
    EN: The b6023f1 version, without the tie-break.
    """
    colunas = corretor._colunas_de_identidade(consulta, chave)
    numerica = consulta.tipo(chave) not in ("STRING", "DATE")

    def bate(celula, linha: dict) -> bool:
        if numerica:
            return corretor.numero(celula) is not None and corretor.numero(celula) == corretor.numero(linha[chave])
        return any(linha[c] is not None and corretor.texto_casa(celula, linha[c], c) for c in colunas)

    melhor: dict[int, set[int]] = {}
    for j in range(tabela.largura):
        achadas = {}
        for k, linha in enumerate(consulta.linhas):
            linhas = {i for i in range(len(tabela.linhas)) if bate(tabela.celula(i, j), linha)}
            if linhas:
                achadas[k] = linhas
        if len(achadas) > len(melhor):
            melhor = achadas
    return melhor


def comparar(nome: str, registros: list[dict]) -> list[str]:
    """PT: recorrige com os dois e compara / EN: re-grades with both and compares"""
    g = carregar_gabarito()
    agora = [corrigir(r["id_pergunta"], r, g) for r in registros]
    with mock.patch.object(corretor, "_identificar", identificar_de_antes):
        antes = [corrigir(r["id_pergunta"], r, g) for r in registros]
    mudaram = Counter(r["id_pergunta"] for r, a, b in zip(registros, antes, agora) if a != b)
    situacao = Counter(r["id_pergunta"] for r, a, b in zip(registros, antes, agora)
                       if a.get("situacao") != b.get("situacao"))
    print(f"  {nome}: {len(registros)} registros; correção diferente em {sum(mudaram.values())} "
          f"({dict(sorted(mudaram.items()))}); situação diferente em {sum(situacao.values())}")
    return [f"{nome}: a situação mudou em {dict(sorted(situacao.items()))}"] if situacao else []


def main() -> None:
    problemas = []
    # PT: a cópia de antes tem de reproduzir o defeito, e a de agora não.
    # EN: the old copy must reproduce the defect, the current one must not.
    with mock.patch.object(corretor, "_identificar", identificar_de_antes):
        if not checar_posicao_contra_codigo():
            problemas.append("a cópia do _identificar de antes não reproduz o defeito da posição contra o código")
    problemas += checar_posicao_contra_codigo()
    with gzip.open(SELECAO, "rt", encoding="utf-8") as arquivo:
        problemas += comparar("seleção (#48)", [json.loads(linha) for linha in arquivo])
    if (PASTA_DO_EXPERIMENTO / "execucoes").exists():
        problemas += comparar("execução 1 (#50)", ler_execucoes(PASTA_DO_EXPERIMENTO, PADRAO_DO_EXPERIMENTO))
    else:
        print("  execução 1: data/experimento/ ausente, pulada")
    for problema in problemas:
        print(f"ERRO {problema}")
    if problemas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
