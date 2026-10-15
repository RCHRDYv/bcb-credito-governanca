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
from scripts.validar_registro import HIPOTESES, RAIZ, REGISTRO

PASTA = RAIZ / "evaluation" / "desenvolvimento"
PERGUNTAS = PASTA / "perguntas.yml"
GABARITO = PASTA / "gabarito.yml"
COMPARACAO = PASTA / "comparacao.yml"
PASTA_SQL = PASTA / "sql"
PASTA_RESPOSTAS = PASTA / "respostas"
PADRAO = "*/*/D*_seed*.json"

PAPEIS = ("controle_positivo", "controle_negativo", "mista")


def revisoes_registradas() -> int:
    """
    PT: Quantas erratas do perguntas.yml são revisões do conjunto, marcadas
        com revisao_do_conjunto: true. Uma errata que só corrige um
        comentário não conta.
    EN: How many perguntas.yml errata are set revisions (flagged
        revisao_do_conjunto: true); comment fixes do not count.
    """
    registro = yaml.safe_load((RAIZ / REGISTRO).read_text(encoding="utf-8"))
    caminho = PERGUNTAS.relative_to(RAIZ).as_posix()
    return sum(1 for e in registro.get("erratas") or [] if e.get("arquivo") == caminho and e.get("revisao_do_conjunto"))


def conferir_versao(metadata: dict, revisoes: int | None = None) -> int:
    """
    PT: A versão do conjunto, que não passa de 1 mais as revisões que o
        evaluation/portao.yml permite e é 1 mais o número de revisões
        registradas por errata. Assim uma revisão não passa sem subir a
        versão nem sem errata.
    EN: The set version: at most 1 plus the allowed revisions, and 1 plus
        the revisions registered by errata.
    """
    portao = yaml.safe_load((RAIZ / "evaluation" / "portao.yml").read_text(encoding="utf-8"))
    maxima = 1 + int(portao["sanidade"]["revisoes_permitidas"])
    versao = metadata.get("versao")
    if not isinstance(versao, int) or not 1 <= versao <= maxima:
        raise SystemExit(f"ERRO versão do conjunto de desenvolvimento {versao!r}: vai de 1 a {maxima} (portao.yml)")
    revisoes = revisoes_registradas() if revisoes is None else revisoes
    if versao != 1 + revisoes:
        raise SystemExit(f"ERRO versão {versao} do conjunto de desenvolvimento com {revisoes} revisões registradas: "
                         "cada revisão sobe a versão e entra por errata com revisao_do_conjunto: true")
    return versao


def perguntas() -> tuple[dict, dict[str, dict]]:
    """
    PT: Metadados e perguntas por id, com a versão do conjunto conferida.
    EN: Metadata and questions by id, with the set version checked.
    """
    meta, por_id = ler_perguntas(PERGUNTAS)
    conferir_versao(meta)
    return meta, por_id


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
