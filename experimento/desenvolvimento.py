"""
PT: O conjunto de desenvolvimento do instrumento (#118, ADR 0032): as
    perguntas, o gabarito e as respostas de evaluation/desenvolvimento/, e o
    Gabarito que o corretor recebe por injeção, sem mudar o
    correcao/corretor.py. A tolerância é a mesma do teste, lida do
    evaluation/hipoteses.yml.

EN: The instrument's development set: questions, answer key and answers
    under evaluation/desenvolvimento/, and the Gabarito injected into the
    grader without changing correcao/corretor.py. Same tolerance rules as
    the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from correcao.corretor import Gabarito
from scripts.validar_perguntas import perguntas as ler_perguntas
from scripts.validar_registro import HIPOTESES, RAIZ

PASTA = RAIZ / "evaluation" / "desenvolvimento"
PERGUNTAS = PASTA / "perguntas.yml"
GABARITO = PASTA / "gabarito.yml"
COMPARACAO = PASTA / "comparacao.yml"
PASTA_SQL = PASTA / "sql"
PASTA_RESPOSTAS = PASTA / "respostas"
PADRAO = "*/*/D*_seed*.json"

PAPEIS = ("controle_positivo", "controle_negativo", "mista")


def perguntas() -> tuple[dict, dict[str, dict]]:
    """PT: metadados e perguntas por id / EN: metadata and questions by id"""
    return ler_perguntas(PERGUNTAS)


def ler_respostas(pasta: Path = PASTA_RESPOSTAS) -> dict[str, dict]:
    """PT: as respostas por consulta, como no teste / EN: answers by query"""
    return {a.stem + ".sql": json.loads(a.read_text(encoding="utf-8")) for a in sorted(pasta.glob("D*.json"))}


def _yaml(caminho: Path) -> dict:
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def carregar_gabarito() -> Gabarito:
    """
    PT: O Gabarito do conjunto de desenvolvimento, para
        correcao.corretor.corrigir(..., gabarito=g).
    EN: The development Gabarito, for corrigir(..., gabarito=g).
    """
    return Gabarito(
        comparacao=_yaml(COMPARACAO)["perguntas"],
        perguntas=_yaml(GABARITO)["perguntas"],
        respostas=ler_respostas(),
        regra=_yaml(RAIZ / HIPOTESES)["comparacao"]["tolerancia"],
    )


def por_papel(por_id: dict[str, dict]) -> dict[str, list[str]]:
    """PT: os ids de cada papel / EN: ids by role"""
    return {papel: [i for i, p in por_id.items() if p["papel"] == papel] for papel in PAPEIS}
