"""
PT: As execuções do experimento no conjunto de teste (#120), num lugar só:
    para cada número, a variação do instrumento (assistente/variacoes.py), a
    pasta local dos registros (data/, fora do git) e o título que a página
    dá a ela depois que uma execução mais nova a substitui. Usado pelo
    executor, pela correção às cegas, pelo resumo, pelo validador, pelo QA e
    pelo notebook.

    - Execução 1: V−1, em data/experimento/, com o instrumento falho
      (ADR 0032).
    - Execução 2: V4, em data/experimento/execucao-2/, com o esquema cru e a
      ontologia inteira em B e D.
    - Execução 3: V6, em data/experimento/execucao-3/, com a ontologia
      recuperada por pergunta e o esquema descrito (ADR 0033).

    Cada execução também registra a versão do Ollama com que roda, porque
    outra versão pode mudar a gramática e a geração (ADR 0032). As
    execuções 1 e 2 rodaram na 0.40.4; o app se atualizou sozinho, e decidi
    em 2026-10-24 adotar a 0.40.9 na execução 3 e na checagem do
    desenvolvimento que vem antes dela. As hipóteses comparam condições
    dentro de uma execução, na mesma versão.

    A confirmatória é a mais nova publicada; as anteriores saem como foram
    registradas.

EN: The experiment's test-set runs in one place: per number, the instrument
    variant, the local records folder, the Ollama version it runs on and the
    page title once a newer run supersedes it. Runs 1 and 2 used Ollama
    0.40.4; run 3 and its dev check use 0.40.9. The confirmatory run is the
    newest published one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from correcao.acerto import PASTA_DO_EXPERIMENTO


@dataclass(frozen=True)
class Execucao:
    """PT: uma execução do teste / EN: one test-set run"""

    numero: int
    variacao: str
    pasta: Path
    ollama: str
    titulo_registrado: str


EXECUCOES = {
    1: Execucao(1, "V-1", PASTA_DO_EXPERIMENTO, "0.40.4", "Execução 1: resultado registrado, com instrumento falho"),
    2: Execucao(2, "V4", PASTA_DO_EXPERIMENTO / "execucao-2", "0.40.4",
                "Execução 2: resultado registrado, com o esquema cru e a ontologia inteira"),
    3: Execucao(3, "V6", PASTA_DO_EXPERIMENTO / "execucao-3", "0.40.9",
                "Execução 3: resultado registrado, com a ontologia recuperada e o esquema descrito"),
}
# PT: a execução que roda agora; o conjunto de desenvolvimento roda na
#     versão do Ollama dela.
# EN: the run in progress; the dev set runs on its Ollama version.
ATUAL = EXECUCOES[max(EXECUCOES)]


def da_variacao(variacao: str) -> Execucao:
    """
    PT: A execução do teste que roda nesta variação. Uma variação sem
        execução no teste só roda no conjunto de desenvolvimento.
    EN: The test-set run for this variant; others run only on the dev set.
    """
    for e in EXECUCOES.values():
        if e.variacao == variacao:
            return e
    raise SystemExit(f"ERRO a {variacao} não tem execução no teste (experimento/execucoes.py): ela só roda no "
                     "conjunto de desenvolvimento")


def titulo(numero: int, confirmatoria: int) -> str:
    """
    PT: O título da seção na página: a confirmatória é a mais nova
        publicada; as outras levam o título de registrada, menos a 1, que
        sempre o leva.
    EN: The page section title; the newest published run is confirmatory.
    """
    if numero == confirmatoria and numero != 1:
        return f"Execução {numero}: resultado confirmatório"
    return EXECUCOES[numero].titulo_registrado
