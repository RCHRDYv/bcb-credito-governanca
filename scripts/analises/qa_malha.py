"""
PT: QA da malha das UFs do site (issue #67), independente do gerador.

    Por que existe: o gerador e a validação do CI foram escritos juntos, e os
    dois leem o código e a sigla da mesma ontologia. Se a malha tivesse a
    geometria de uma UF sob o código de outra, os dois passariam. Este script
    confere a malha do site contra os metadados que a própria API de malhas
    publica para cada UF, que são outra fonte: o centroide, o retângulo
    limítrofe e a área oficial.

    O que confere:
    1. **A geometria é a da malha crua.** Número por número, em Decimal, como
       o IBGE publicou.
    2. **Cada geometria é da UF certa.** O centroide oficial de cada UF cai
       dentro do polígono que o arquivo dá para ela.
    3. **O desenho tem o tamanho certo.** O retângulo de cada UF difere do
       retângulo oficial em menos de 0,1 grau de cada lado, e a fatia de cada
       UF na área do país difere da oficial em menos de 0,5 ponto percentual.
       A área é calculada na projeção sinusoidal, que preserva área, o que
       basta para comparar fatias.

    Exceção declarada: a qualidade mínima não traz as ilhas oceânicas, e o
    retângulo oficial de duas UFs se estende até elas. Fernando de Noronha
    leva o de PE até -32,38 de longitude e -3,80 de latitude, e Trindade e
    Martim Vaz levam o do ES até -28,85 de longitude (metadados de
    2026-10-01; a qualidade intermediária de PE traz Noronha como segundo
    anel). Nessas duas, o retângulo do arquivo precisa estar dentro do
    oficial, em vez de coincidir com ele.

EN: Site state mesh QA, independent from the generator. It checks the site
    mesh against the metadata IBGE's mesh API publishes for each state: the
    geometry equals the raw mesh; each state's official centroid falls inside
    the polygon filed under its code; each bounding box is within 0.1 degree
    of the official one; and each state's share of the country's area, in the
    equal-area sinusoidal projection, is within 0.5 percentage point of the
    official share. Declared exception: the minimum quality omits the oceanic
    islands that stretch the official boxes of PE and ES, so there the file's
    box must lie inside the official one.

Uso / Usage:
    uv run python -m scripts.analises.qa_malha
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import time
import urllib.request

from ingestion.baixar import CABECALHOS
from ingestion.baixar_malha import NOME
from ingestion.fontes import DIR_RAW_IBGE
from scripts.gerar_malha_do_dashboard import DESTINO_DA_MALHA, aneis, geometrias_diferentes

METADADOS = "https://servicodados.ibge.gov.br/api/v3/malhas/estados/{codigo}/metadados"
FOLGA_DO_RETANGULO = 0.1
FOLGA_DA_FATIA = 0.5

# PT: As UFs cujo retângulo oficial vai até ilhas oceânicas que a qualidade
#     mínima não traz (ver o cabeçalho).
# EN: States whose official box reaches oceanic islands absent from the
#     minimum quality.
ILHAS_OCEANICAS = {"PE": "Fernando de Noronha", "ES": "Trindade e Martim Vaz"}


def metadados(codigo: str, tentativas: int = 3) -> dict:
    """
    PT: Centroide, retângulo e área oficiais da UF. A API não aceita várias
        UFs numa consulta, e em 2026-10-01 deixou de responder no meio das 27
        consultas seguidas. Por isso cada consulta tem três tentativas, com
        espera crescente.
    EN: Official centroid, bounding box and area. The API takes one state per
        request and dropped a connection mid-run on 2026-10-01, so each
        request gets three attempts with growing waits.
    """
    req = urllib.request.Request(METADADOS.format(codigo=codigo), headers=CABECALHOS)
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                corpo = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    corpo = gzip.decompress(corpo)
            return json.loads(corpo)[0]
        except OSError:
            if tentativa == tentativas:
                raise
            time.sleep(5 * tentativa)
    raise AssertionError("inalcançável / unreachable")


def poligonos(geometria: dict) -> list[list[list[list[float]]]]:
    """PT: a geometria como lista de polígonos / EN: geometry as polygon list"""
    if geometria["type"] == "Polygon":
        return [geometria["coordinates"]]
    return geometria["coordinates"]


def dentro_do_anel(x: float, y: float, anel: list[list[float]]) -> bool:
    """PT: ponto no anel, pelo traçado de raio / EN: ray-casting point in ring"""
    dentro = False
    for (x1, y1), (x2, y2) in zip(anel, anel[1:], strict=False):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            dentro = not dentro
    return dentro


def dentro(x: float, y: float, geometria: dict) -> bool:
    """
    PT: Ponto dentro de algum polígono: no anel externo e fora dos buracos.
    EN: Point inside some polygon: in the outer ring and outside its holes.
    """
    return any(
        dentro_do_anel(x, y, poligono[0]) and not any(dentro_do_anel(x, y, buraco) for buraco in poligono[1:])
        for poligono in poligonos(geometria)
    )


def area_sinusoidal(geometria: dict) -> float:
    """
    PT: Área na projeção sinusoidal, em que cada ponto vai para longitude
        vezes o cosseno da latitude, e latitude. A projeção preserva área,
        então as fatias de cada UF saem comparáveis às oficiais. Os buracos
        descontam.
    EN: Area in the sinusoidal projection (x = lon * cos(lat), y = lat), which
        preserves area, so state shares compare with official ones. Holes
        subtract.
    """
    def do_anel(anel):
        projetado = [(x * math.cos(math.radians(y)), y) for x, y in anel]
        soma = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(projetado, projetado[1:], strict=False))
        return abs(soma) / 2

    return sum(do_anel(p[0]) - sum(do_anel(b) for b in p[1:]) for p in poligonos(geometria))


def retangulo(geometria: dict) -> tuple[float, float, float, float]:
    """PT: oeste, sul, leste e norte / EN: west, south, east, north"""
    pontos = [p for anel in aneis(geometria) for p in anel]
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    return min(xs), min(ys), max(xs), max(ys)


def main() -> None:
    texto = DESTINO_DA_MALHA.read_text(encoding="utf-8")
    falhas = []

    diferentes = geometrias_diferentes(texto, (DIR_RAW_IBGE / NOME).read_bytes())
    print(f"1. Geometria igual à da malha crua: {'sim' if not diferentes else diferentes}")
    if diferentes:
        falhas.append(f"geometria diferente da crua nas UFs {diferentes}")

    malha = json.loads(texto)
    oficiais = {f["properties"]["codarea"]: metadados(f["properties"]["codarea"]) for f in malha["features"]}
    areas = {f["properties"]["codarea"]: area_sinusoidal(f["geometry"]) for f in malha["features"]}
    total_calculado = sum(areas.values())
    total_oficial = sum(float(m["area"]["dimensao"]) for m in oficiais.values())

    print("\n2 e 3. Por UF: centroide oficial dentro, maior diferença do retângulo, fatia da área")
    for feicao in malha["features"]:
        codigo, sigla = feicao["properties"]["codarea"], feicao["properties"]["sigla"]
        oficial = oficiais[codigo]
        centroide = oficial["centroide"]
        no_poligono = dentro(centroide["longitude"], centroide["latitude"], feicao["geometry"])

        oeste, sul, leste, norte = retangulo(feicao["geometry"])
        canto_no, canto_se = oficial["regiao-limitrofe"]
        if sigla in ILHAS_OCEANICAS:
            # PT: sem as ilhas, o retângulo do arquivo fica dentro do oficial
            # EN: without the islands, the file's box lies inside the official one
            folga = FOLGA_DO_RETANGULO
            dentro_do_oficial = (
                oeste >= canto_no["longitude"] - folga
                and norte <= canto_no["latitude"] + folga
                and leste <= canto_se["longitude"] + folga
                and sul >= canto_se["latitude"] - folga
            )
            diferenca = 0.0 if dentro_do_oficial else float("inf")
            nota_do_retangulo = f"dentro do oficial, sem {ILHAS_OCEANICAS[sigla]}"
        else:
            diferenca = max(
                abs(oeste - canto_no["longitude"]),
                abs(norte - canto_no["latitude"]),
                abs(leste - canto_se["longitude"]),
                abs(sul - canto_se["latitude"]),
            )
            nota_do_retangulo = f"{diferenca:.3f}°"

        fatia = 100 * areas[codigo] / total_calculado
        fatia_oficial = 100 * float(oficial["area"]["dimensao"]) / total_oficial
        print(
            f"  {sigla} ({codigo}): centroide {'dentro' if no_poligono else 'FORA'}, "
            f"retângulo {nota_do_retangulo}, fatia {fatia:.2f}% contra {fatia_oficial:.2f}% oficial"
        )
        if not no_poligono:
            falhas.append(f"{sigla}: o centroide oficial cai fora do polígono")
        if diferenca >= FOLGA_DO_RETANGULO:
            falhas.append(f"{sigla}: retângulo difere do oficial ({nota_do_retangulo})")
        if abs(fatia - fatia_oficial) >= FOLGA_DA_FATIA:
            falhas.append(f"{sigla}: fatia da área {fatia:.2f}%, oficial {fatia_oficial:.2f}%")

    if falhas:
        print("\nFALHOU / FAILED:")
        for falha in falhas:
            print(f"  - {falha}")
        sys.exit(1)
    print("\nMalha do site confere com os metadados oficiais do IBGE / site mesh matches IBGE metadata.")


if __name__ == "__main__":
    main()
