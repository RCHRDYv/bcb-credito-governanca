"""
PT: Os valores do evaluation/hipoteses.yml que mudam com a variação do
    instrumento (#118, ADR 0032), escritos e congelados antes da triagem em
    evaluation/hipoteses_por_variacao.yml.

    A conferência garante que a errata 6 só copia:
    - o arquivo cobre da V0 à V4, e cada caminho existe no hipoteses.yml;
    - fora desses caminhos, o hipoteses.yml é o registrado: o sha256 do
      resto (o YAML lido, sem os caminhos, em JSON canônico) é o que o
      arquivo guarda;
    - com uma variação registrada no assistente/parametros.yml, cada
      caminho traz exatamente o valor dela (o bloco comum e o da variação).

    O validar_variacoes confere isso no CI, e o executor, antes da
    execução 2.

EN: The hipoteses.yml values that change with the instrument variant,
    frozen before screening. The check guarantees errata 6 only copies: full
    variant coverage, every path present, the rest of hipoteses.yml
    unchanged (canonical-JSON sha256) and, once a variant is registered,
    each path holding exactly its prepared value.
"""

from __future__ import annotations

import copy
import hashlib
import json

import yaml

from scripts.validar_registro import HIPOTESES, RAIZ

ARQUIVO = RAIZ / "evaluation" / "hipoteses_por_variacao.yml"
VARIACOES = ["V0", "V1", "V2", "V3", "V4"]


def carregar() -> dict:
    return yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))


def hipoteses_vigentes() -> dict:
    return yaml.safe_load((RAIZ / HIPOTESES).read_text(encoding="utf-8"))


def caminhos(textos: dict) -> list[str]:
    """PT: todos os caminhos que alguma variação muda / EN: every variable path"""
    blocos = [textos.get("comum", {}), *textos.get("variacoes", {}).values()]
    return sorted({c for b in blocos for c in b})


def _partes(caminho: str) -> list[str]:
    return caminho.split(".")


def no_caminho(dados: dict, caminho: str):
    for parte in _partes(caminho):
        if not isinstance(dados, dict) or parte not in dados:
            return None
        dados = dados[parte]
    return dados


def resto_sha256(hipoteses: dict, variaveis: list[str]) -> str:
    """
    PT: O sha256 do hipoteses.yml sem os caminhos variáveis, em JSON canônico.
    EN: sha256 of hipoteses.yml without the variable paths, canonical JSON.
    """
    resto = copy.deepcopy(hipoteses)
    for caminho in variaveis:
        *pais, folha = _partes(caminho)
        dados = resto
        for parte in pais:
            dados = dados.get(parte, {})
        dados.pop(folha, None)
    texto = json.dumps(resto, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _normalizado(valor):
    if isinstance(valor, str):
        return " ".join(valor.split())
    if isinstance(valor, list):
        return [_normalizado(v) for v in valor]
    return valor


def esperados(textos: dict, variacao: str) -> dict:
    """PT: os valores de uma variação / EN: one variant's values"""
    return {**textos.get("comum", {}), **textos.get("variacoes", {}).get(variacao, {})}


def aplicar(hipoteses: dict, textos: dict, variacao: str) -> dict:
    """
    PT: O hipoteses.yml com os valores de uma variação, como a errata 6 o
        deixa. Serve para conferir que copiar basta.
    EN: hipoteses.yml with one variant's values, as errata 6 leaves it.
    """
    novo = copy.deepcopy(hipoteses)
    for caminho, valor in esperados(textos, variacao).items():
        *pais, folha = _partes(caminho)
        dados = novo
        for parte in pais:
            dados = dados[parte]
        dados[folha] = valor
    return novo


def conferir(hipoteses: dict | None = None, registrada: str = "V-1", textos: dict | None = None) -> list[str]:
    """PT: os problemas, ou lista vazia / EN: the problems, or empty"""
    hipoteses = hipoteses_vigentes() if hipoteses is None else hipoteses
    textos = carregar() if textos is None else textos
    erros = []
    if sorted(textos.get("variacoes", {})) != VARIACOES:
        erros.append(f"hipoteses_por_variacao: variações {sorted(textos.get('variacoes', {}))}, esperado {VARIACOES}")
    variaveis = caminhos(textos)
    for caminho in variaveis:
        if no_caminho(hipoteses, caminho) is None:
            erros.append(f"hipoteses_por_variacao: o caminho {caminho} não existe no hipoteses.yml")
    if resto_sha256(hipoteses, variaveis) != textos.get("resto_sha256"):
        erros.append("hipoteses.yml: fora dos caminhos de hipoteses_por_variacao.yml, o arquivo mudou; a errata 6 "
                     "só pode copiar os valores prontos")
    if registrada != "V-1":
        for caminho, valor in sorted(esperados(textos, registrada).items()):
            if _normalizado(no_caminho(hipoteses, caminho)) != _normalizado(valor):
                erros.append(f"hipoteses.yml: {caminho} não traz o texto pronto da {registrada}")
    return erros
