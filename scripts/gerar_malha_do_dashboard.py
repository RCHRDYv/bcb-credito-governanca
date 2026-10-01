"""
PT: Etapa 2 da malha das UFs (issue #67). Monta, a partir da malha crua do
    IBGE baixada por ingestion/baixar_malha.py, o arquivo que o site lê, em
    dashboard/public/geo/ufs.json.

    A geometria vai como o IBGE publica, sem nenhuma alteração. A malha
    crua já é a qualidade mínima, generalizada pelo próprio IBGE, e cabe
    folgada no orçamento de carga: o arquivo do site fica com 28,9 KB
    comprimido, contra o limite de 100 KB do RNF-03. Arredondar as
    coordenadas para 3 casas economizaria só 4,5 KB e faria sumir um
    polígono do Paraná, por isso ficou de fora
    (decidido em 2026-10-01). Simplificar UF por UF, com Douglas-Peucker em
    cada feição, também fica de fora: a mesma fronteira sairia diferente nas
    duas UFs que a dividem, e o mapa ganharia frestas.

    O que o arquivo acrescenta à malha crua:
    - por UF, a sigla, tirada de dim_uf na ontologia, ao lado do código do
      IBGE (`codarea`);
    - no topo, a fonte, o endereço, a licença, a nota sobre a geometria e o
      sha256 da malha crua, como membros extras do GeoJSON, que o ECharts
      ignora.

    Antes de gravar, confere que a geometria de cada UF saiu idêntica à da
    malha crua, número por número. A saída é determinística: rodar de novo
    com a mesma malha crua produz o mesmo arquivo, byte a byte.

    A validação do arquivo, `validar_malha()`, mora aqui e é chamada também
    por scripts/validar_dados_do_dashboard.py, que roda no CI sem a malha
    crua.

EN: State mesh step 2. Builds the site's file from IBGE's raw mesh. The
    geometry ships exactly as IBGE publishes it: the raw mesh is already
    IBGE's minimum quality and fits the load budget (the site file is
    28.9 KB compressed, of 100 KB). Rounding to 3 decimals would save only
    4.5 KB and drop a polygon
    in Paraná, so it was left out; per-feature Douglas-Peucker would open gaps
    between states. The file adds each state's abbreviation from dim_uf and,
    at the top, source, address, license, a geometry note and the raw sha256.
    Before writing, it checks every state's geometry equals the raw one.
    Output is deterministic. `validar_malha()` is also called by the CI
    validator, which has no raw mesh.

Uso / Usage:
    uv run python -m ingestion.baixar_malha            # quando o IBGE republicar
    uv run python -m scripts.gerar_malha_do_dashboard
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

from ingestion import manifesto
from ingestion.baixar_malha import NOME, ufs_da_ontologia, validar
from ingestion.fontes import DIR_RAW_IBGE, MALHA_UFS

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = DIR_RAW_IBGE / NOME
DESTINO_DA_MALHA = RAIZ / "dashboard" / "public" / "geo" / "ufs.json"

# PT: A malha mínima do IBGE vem com até 4 casas decimais, cerca de 11 m.
#     Uma malha com mais casas seria de outra qualidade, mais pesada, e a
#     validação a reprova.
# EN: IBGE's minimum-quality mesh has up to 4 decimals; more would mean a
#     heavier quality, which validation rejects.
CASAS = 4

# PT: O retângulo que contém o Brasil, com folga, a partir da região
#     limítrofe que a própria API de malhas informa para o país (metadados
#     de paises/BR, consultados em 2026-10-01): longitude de -73,9904 a
#     -28,8476 e latitude de -33,7512 a 5,2718.
# EN: Brazil's bounding box with some margin, from the API's own country
#     metadata.
LONGITUDE = (-74.0, -28.8)
LATITUDE = (-34.0, 5.3)

FONTE = (
    "IBGE, API de malhas v3: malha territorial de 2022, na qualidade mínima, "
    "com o país dividido por unidade da federação"
)
LICENCA = (
    "Dado aberto do IBGE. A API de malhas não declara licença própria. O Plano "
    "de Dados Abertos do IBGE define licença aberta como a que permite usar, "
    "reutilizar e redistribuir o dado, exigindo no máximo o crédito da autoria "
    "e o compartilhamento pela mesma licença. O crédito é do IBGE, e este "
    "arquivo segue as mesmas condições. O IBGE avisa que os limites da malha são "
    "aproximados e não são a demarcação oficial da divisão político-administrativa."
)
GEOMETRIA = (
    "A da qualidade mínima do IBGE, sem alteração: a generalização é a do "
    "próprio IBGE, e nenhum polígono foi tirado ou mudado (issue #67)."
)
CHAVES_DE_TOPO = ["type", "fonte", "endereco", "licenca", "geometria", "sha256_da_origem", "features"]


# -----------------------------------------------------------------------------
# PT: Montagem / EN: building
# -----------------------------------------------------------------------------


def montar_malha(malha: dict, ufs: dict[str, str], sha256_da_origem: str) -> dict:
    """
    PT: A malha do site: as feições na ordem do código do IBGE, cada uma com
        o código e a sigla e a geometria da malha crua, e a fonte e a
        licença no topo.
    EN: The site's mesh: features by IBGE code, with code, abbreviation and
        the raw geometry, and source and license at the top.
    """
    feicoes = [
        {
            "type": "Feature",
            "properties": {"codarea": feicao["properties"]["codarea"], "sigla": ufs[feicao["properties"]["codarea"]]},
            "geometry": feicao["geometry"],
        }
        for feicao in sorted(malha["features"], key=lambda f: f["properties"]["codarea"])
    ]
    return {
        "type": "FeatureCollection",
        "fonte": FONTE,
        "endereco": MALHA_UFS,
        "licenca": LICENCA,
        "geometria": GEOMETRIA,
        "sha256_da_origem": sha256_da_origem,
        "features": feicoes,
    }


def texto_da_malha(malha: dict) -> str:
    """
    PT: O texto do arquivo, com uma UF por linha. Assim o diff da PR mostra
        qual UF mudou, sem um arquivo de uma linha só.
    EN: The file text, one state per line, so the PR diff shows which state
        changed.
    """
    linhas = ["{"]
    for chave in CHAVES_DE_TOPO[:-1]:
        linhas.append(f"  {json.dumps(chave)}: {json.dumps(malha[chave], ensure_ascii=False)},")
    linhas.append('  "features": [')
    feicoes = malha["features"]
    for indice, feicao in enumerate(feicoes):
        virgula = "," if indice < len(feicoes) - 1 else ""
        linhas.append(f"    {json.dumps(feicao, ensure_ascii=False, separators=(',', ':'))}{virgula}")
    linhas += ["  ]", "}"]
    return "\n".join(linhas) + "\n"


def geometrias_diferentes(texto: str, bruto: bytes) -> list[str]:
    """
    PT: As UFs cuja geometria no arquivo do site difere da malha crua. A
        comparação é feita em Decimal, a partir do texto dos dois arquivos,
        para nenhuma diferença se esconder num arredondamento de float.
    EN: States whose site geometry differs from the raw mesh, compared as
        Decimal from both texts so no difference hides in float rounding.
    """
    def por_codigo(conteudo: dict) -> dict:
        return {f["properties"]["codarea"]: f["geometry"] for f in conteudo["features"]}

    site = por_codigo(json.loads(texto, parse_float=Decimal))
    crua = por_codigo(json.loads(bruto, parse_float=Decimal))
    return sorted(codigo for codigo in crua if site.get(codigo) != crua[codigo])


# -----------------------------------------------------------------------------
# PT: Validação do arquivo do site / EN: site file validation
# -----------------------------------------------------------------------------


def _problema_do_anel(anel) -> str | None:
    """PT: o que há de errado com um anel, se houver / EN: what is wrong"""
    if not isinstance(anel, list) or len(anel) < 4:
        return "anel com menos de 4 pontos"
    formato = next((p for p in anel if not isinstance(p, list) or len(p) != 2), None)
    if formato is not None:
        return f"ponto fora do formato [longitude, latitude]: {formato!r}"
    if anel[0] != anel[-1]:
        return "anel aberto: o primeiro ponto difere do último"
    repetido = next((p for anterior, p in zip(anel, anel[1:], strict=False) if p == anterior), None)
    if repetido is not None:
        return f"ponto repetido em sequência: {repetido!r}"
    for longitude, latitude in anel:
        numeros = (longitude, latitude)
        if not all(isinstance(v, Decimal | int) and not isinstance(v, bool) for v in numeros):
            return f"coordenada que não é número: {[longitude, latitude]!r}"
        if any(Decimal(v).as_tuple().exponent < -CASAS for v in numeros):
            return f"coordenada com mais de {CASAS} casas decimais: {[str(v) for v in numeros]}"
        if not (LONGITUDE[0] <= longitude <= LONGITUDE[1] and LATITUDE[0] <= latitude <= LATITUDE[1]):
            return f"ponto fora do retângulo do Brasil: {[str(v) for v in numeros]}"
    return None


def aneis(geometria: dict) -> list:
    """PT: todos os anéis de uma geometria / EN: every ring of a geometry"""
    if geometria.get("type") == "Polygon":
        return geometria.get("coordinates", [])
    if geometria.get("type") == "MultiPolygon":
        return [anel for poligono in geometria.get("coordinates", []) for anel in poligono]
    return []


def validar_malha(texto: str, ufs: dict[str, str]) -> list[str]:
    """
    PT: Confere o arquivo do site sem precisar da malha crua: as chaves de
        topo, com fonte e licença; as 27 UFs, cada uma uma vez, com o par de
        código e sigla de dim_uf; e cada anel fechado, sem ponto repetido em
        sequência, com no máximo 4 casas e dentro do retângulo do Brasil.
        Aponta só o primeiro problema de cada UF.
    EN: Checks the site file without the raw mesh: top-level keys with source
        and license; the 27 states once each, with dim_uf's code and
        abbreviation; and every ring closed, with no repeated consecutive
        point, at most 4 decimals and inside Brazil's bounding box. Reports
        only the first problem per state.
    """
    nome = "geo/ufs.json"
    try:
        malha = json.loads(texto, parse_float=Decimal)
    except json.JSONDecodeError as erro:
        return [f"{nome}: JSON inválido: {erro}"]
    if list(malha) != CHAVES_DE_TOPO:
        return [f"{nome}: chaves de topo {list(malha)}, esperado {CHAVES_DE_TOPO}"]
    problemas = []
    if malha["type"] != "FeatureCollection":
        problemas.append(f"{nome}: tipo de topo {malha['type']!r}")
    for chave in CHAVES_DE_TOPO[1:-1]:
        if not isinstance(malha[chave], str) or not malha[chave].strip():
            problemas.append(f"{nome}: {chave} ausente")

    codigos = [f.get("properties", {}).get("codarea") for f in malha["features"]]
    problemas += [f"{nome}: código repetido: {c}" for c, n in Counter(codigos).items() if n > 1]
    faltando = sorted(set(ufs) - set(codigos))
    if faltando:
        problemas.append(f"{nome}: UF faltando: {[ufs[c] for c in faltando]}")

    for feicao in malha["features"]:
        propriedades = feicao.get("properties", {})
        codigo = propriedades.get("codarea")
        if set(propriedades) != {"codarea", "sigla"}:
            problemas.append(f"{nome}, {codigo}: propriedades {sorted(propriedades)}, esperado codarea e sigla")
            continue
        if codigo not in ufs:
            problemas.append(f"{nome}: código fora de dim_uf: {codigo!r}")
            continue
        if propriedades["sigla"] != ufs[codigo]:
            problemas.append(f"{nome}, {codigo}: sigla {propriedades['sigla']!r}, esperado {ufs[codigo]!r}")
            continue
        geometria = feicao.get("geometry", {})
        if geometria.get("type") not in {"Polygon", "MultiPolygon"}:
            problemas.append(f"{nome}, {ufs[codigo]}: geometria {geometria.get('type')!r}")
            continue
        for anel in aneis(geometria):
            problema = _problema_do_anel(anel)
            if problema:
                problemas.append(f"{nome}, {ufs[codigo]}: {problema}")
                break
    return problemas


# -----------------------------------------------------------------------------
# PT: Execução / EN: entry point
# -----------------------------------------------------------------------------


def main() -> None:
    if not ORIGEM.exists():
        sys.exit(f"Não achei {ORIGEM}. Rode antes: uv run python -m ingestion.baixar_malha")
    bruto = ORIGEM.read_bytes()
    sha256_da_origem = hashlib.sha256(bruto).hexdigest()
    registrado = manifesto.carregar().get("ibge", {}).get(NOME, {}).get("sha256")
    if registrado != sha256_da_origem:
        sys.exit(
            f"A malha crua em {ORIGEM} não é a registrada no manifesto. "
            "Rode de novo: uv run python -m ingestion.baixar_malha"
        )

    ufs = ufs_da_ontologia()
    crua = json.loads(bruto)
    erros = validar(crua, ufs)
    if erros:
        sys.exit("Malha crua fora do formato: " + "; ".join(erros))

    texto = texto_da_malha(montar_malha(crua, ufs, sha256_da_origem))
    diferentes = geometrias_diferentes(texto, bruto)
    if diferentes:
        sys.exit(f"A geometria mudou na montagem, nas UFs de código {diferentes}")
    problemas = validar_malha(texto, ufs)
    if problemas:
        sys.exit("A malha do site não passou na validação:\n  - " + "\n  - ".join(problemas))

    DESTINO_DA_MALHA.parent.mkdir(parents=True, exist_ok=True)
    DESTINO_DA_MALHA.write_text(texto, encoding="utf-8", newline="\n")
    gravado = texto.encode("utf-8")
    print(
        f"  > {DESTINO_DA_MALHA.relative_to(RAIZ).as_posix()}: 27 UFs, geometria igual à crua, "
        f"{len(gravado)} bytes, {len(gzip.compress(gravado, 9))} comprimido",
        flush=True,
    )


if __name__ == "__main__":
    main()
