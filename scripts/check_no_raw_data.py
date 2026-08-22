#!/usr/bin/env python3
"""
PT: Barreira de pre-commit que impede dado bruto de entrar no repositório.
EN: Pre-commit guardrail that keeps raw data out of the repository.

PT: O .gitignore já cobre o caso normal, mas ele é contornável por engano
    (`git add -f`) e não protege contra alguém clonar o projeto e recriar o
    ignore de forma diferente. Este script é a segunda linha de defesa, e roda
    também no CI, onde não depende de configuração local.
EN: The .gitignore already covers the normal case, but it can be bypassed by
    mistake (`git add -f`) and does not protect against someone cloning the
    project and recreating the ignore file differently. This script is the
    second line of defence, and also runs in CI, where it does not depend on
    local configuration.

PT: A regra: nenhum .csv ou .zip é versionado, com uma exceção deliberada.
    dbt/seeds/ contém tabelas de referência pequenas e curadas, geradas a
    partir da ontologia, que precisam ser versionadas para o modelo ser
    reprodutível.
EN: The rule: no .csv or .zip is versioned, with one deliberate exception.
    dbt/seeds/ holds small curated reference tables, generated from the
    ontology, which must be versioned for the model to be reproducible.
"""

from __future__ import annotations

import sys
from pathlib import Path

# PT: Extensões que caracterizam dado bruto neste projeto.
# EN: Extensions that characterise raw data in this project.
EXTENSOES_BLOQUEADAS = {".csv", ".zip", ".parquet", ".xlsx"}

# PT: Único diretório onde arquivo tabular versionado é legítimo.
# EN: The only directory where a versioned tabular file is legitimate.
DIRETORIO_PERMITIDO = Path("dbt/seeds")


def eh_excecao_permitida(caminho: Path) -> bool:
    """
    PT: Retorna True se o arquivo está no diretório de seeds do dbt, onde
        tabelas de referência pequenas são versionadas de propósito.
    EN: Returns True if the file lives in the dbt seeds directory, where small
        reference tables are versioned on purpose.
    """
    try:
        caminho.relative_to(DIRETORIO_PERMITIDO)
        return True
    except ValueError:
        return False


def main(argv: list[str]) -> int:
    """
    PT: Recebe os arquivos em stage do pre-commit e falha se algum for dado
        bruto fora da exceção. Falhar aqui é barato; limpar histórico do git
        depois de um commit acidental não é.
    EN: Takes the staged files from pre-commit and fails if any is raw data
        outside the exception. Failing here is cheap; rewriting git history
        after an accidental commit is not.
    """
    violacoes: list[Path] = []

    for nome in argv:
        caminho = Path(nome)
        if caminho.suffix.lower() in EXTENSOES_BLOQUEADAS and not eh_excecao_permitida(caminho):
            violacoes.append(caminho)

    if not violacoes:
        return 0

    print("Commit bloqueado: dado bruto nao entra no repositorio.\n")
    print("Blocked commit: raw data does not belong in the repository.\n")
    for caminho in violacoes:
        print(f"  - {caminho}")
    print(
        "\nPT: O pipeline baixa esses arquivos da fonte oficial a cada execucao.\n"
        "    Se precisar versionar uma tabela de referencia pequena, coloque em "
        f"{DIRETORIO_PERMITIDO}/.\n"
        "EN: The pipeline downloads these files from the official source on every run.\n"
        "    To version a small reference table, place it under "
        f"{DIRETORIO_PERMITIDO}/."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
