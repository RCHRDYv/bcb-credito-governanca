"""
PT: Valida os JSON do site do dashboard contra o contrato, sem precisar de
    credencial. Roda no CI (#66).

    O que é conferido:
    1. em dashboard/public/data/ estão os arquivos do contrato, e nenhum
       outro;
    2. em cada arquivo de dados: as colunas do contrato, com o mesmo nome e
       na mesma ordem, todas do mesmo tamanho; o tipo de cada valor, o nulo
       só onde o contrato deixa, os valores permitidos, o formato das datas e
       nenhum número inválido; as linhas na ordem do grão, sem grão repetido;
       a data-base e a faixa de meses que o contrato pede;
    3. nenhum dado pessoal: nenhuma coluna com nome de identificador de
       pessoa ou empresa, e nenhum texto no formato de CPF ou CNPJ;
    4. o ontologia.json e o manifesto.json iguais ao que a exportação monta
       a partir dos arquivos e da ontologia. Isso cobre o sha256 e as linhas
       de cada arquivo, os parâmetros da decisão e os conceitos citados;
    5. a malha das UFs, em dashboard/public/geo/ufs.json (#67): as 27 UFs
       com o par de código e sigla de dim_uf, a fonte e a licença, e cada
       anel fechado, dentro do Brasil e com as casas decimais do IBGE. A
       regra mora em scripts/gerar_malha_do_dashboard.py, junto de quem
       grava o arquivo.

    Com --autoteste, roda o controle negativo: estraga cópias dos arquivos
    em memória, um estrago por vez, e confere que a validação reprova cada
    um pelo motivo certo. Um validador que aprova tudo passaria em silêncio
    sem esse teste.

EN: Validates the dashboard site's JSON files against the contract with no
    credential; runs in CI. Checks the file set, each data file's columns,
    types, nulls, allowed values, dates, grain order and uniqueness, the
    data-base and month range, the absence of personal data, that the
    ontology and manifest equal what the export builds, and the state mesh.
    With --autoteste it
    runs the negative control: it breaks in-memory copies one way at a time
    and checks each one is rejected for the right reason.

Uso / usage:
    uv run python -m scripts.validar_dados_do_dashboard
    uv run python -m scripts.validar_dados_do_dashboard --autoteste
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys

from ingestion.baixar_malha import ufs_da_ontologia
from scripts.contrato_do_dashboard import (
    DATA,
    DESTINO,
    MANIFESTO,
    MES,
    ONTOLOGIA,
    arquivos_gerados,
    carregar_contrato,
    codigos_de_modalidade,
    montar_manifesto,
    montar_ontologia,
    parametros_da_decisao,
    texto_de_dados,
    texto_de_registro,
)
from scripts.gerar_malha_do_dashboard import DESTINO_DA_MALHA, texto_da_malha, validar_malha

# PT: Começos de nome de coluna que indicariam identificador de pessoa ou de
#     empresa. "retrato_do_cnpj" não entra: é o mês do retrato da base
#     aberta, e não um CNPJ.
# EN: Column name prefixes that would indicate a personal or company
#     identifier.
PREFIXOS_PESSOAIS = ("cpf", "cnpj", "nome", "razao_social", "email", "telefone", "endereco", "logradouro", "cep")

# PT: CPF, CNPJ e CNPJ básico, com ou sem pontuação, no texto inteiro.
# EN: CPF, CNPJ and base CNPJ, with or without punctuation.
IDENTIFICADORES = (
    re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"),
    re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}"),
    re.compile(r"\d{8}"),
)

TIPOS = {
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "string": lambda v: isinstance(v, str),
}


# -----------------------------------------------------------------------------
# PT: Arquivos de dados / EN: data files
# -----------------------------------------------------------------------------


def _problema_do_valor(valor, coluna: dict) -> str | None:
    """PT: o que há de errado com um valor, se houver / EN: what is wrong"""
    if valor is None:
        return None if coluna["nulo"] else "nulo onde o contrato não deixa"
    if not TIPOS[coluna["tipo"]](valor):
        return f"tipo errado, esperado {coluna['tipo']}: {valor!r}"
    if isinstance(valor, float) and not math.isfinite(valor):
        return f"número inválido: {valor!r}"
    if coluna["unidade"] == "data" and not DATA.fullmatch(valor):
        return f"data fora do formato AAAA-MM-DD: {valor!r}"
    if coluna["unidade"] == "mes" and not MES.fullmatch(valor):
        return f"mês fora do formato AAAA-MM: {valor!r}"
    if "valores" in coluna and valor not in coluna["valores"]:
        return f"valor fora da lista do contrato: {valor!r}"
    return None


def validar_dados(conteudo: dict, spec: dict) -> list[str]:
    """
    PT: Confere um arquivo de dados contra a especificação do contrato.
        Aponta só o primeiro valor errado de cada coluna, para o relatório não
        repetir o mesmo problema milhares de vezes.
    EN: Checks one data file against its contract spec; reports only the
        first bad value per column.
    """
    nome = spec["arquivo"]
    if set(conteudo) != {"arquivo", "data_base", "colunas"}:
        return [f"{nome}: chaves de topo fora do formato: {sorted(conteudo)}"]
    problemas = []
    if conteudo["arquivo"] != nome:
        problemas.append(f"{nome}: campo arquivo diz {conteudo['arquivo']!r}")
    data_base = conteudo["data_base"]
    if not isinstance(data_base, str) or not DATA.fullmatch(data_base):
        problemas.append(f"{nome}: data_base de topo fora do formato: {data_base!r}")

    colunas = conteudo["colunas"]
    esperadas = [coluna["nome"] for coluna in spec["colunas"]]
    if list(colunas) != esperadas:
        a_mais = [c for c in colunas if c not in esperadas]
        faltando = [c for c in esperadas if c not in colunas]
        problemas.append(
            f"{nome}: colunas diferentes do contrato (a mais: {a_mais}, faltando: {faltando}, "
            "ou fora da ordem)"
        )
        return problemas

    tamanhos = {len(valores) for valores in colunas.values() if isinstance(valores, list)}
    if len(tamanhos) != 1 or not all(isinstance(v, list) for v in colunas.values()):
        return [*problemas, f"{nome}: colunas com tamanhos diferentes: {sorted(tamanhos)}"]
    if tamanhos == {0}:
        return [*problemas, f"{nome}: arquivo sem linhas"]

    for coluna in spec["colunas"]:
        for indice, valor in enumerate(colunas[coluna["nome"]]):
            problema = _problema_do_valor(valor, coluna)
            if problema:
                problemas.append(f"{nome}, coluna {coluna['nome']}, linha {indice}: {problema}")
                break
    if problemas:
        return problemas

    problemas += _validar_grao(nome, colunas, spec)
    problemas += _validar_meses(nome, colunas, spec, data_base)
    return problemas


def _validar_grao(nome: str, colunas: dict, spec: dict) -> list[str]:
    """
    PT: As linhas precisam vir na ordem do grão, sem repetir o grão. Grão
        repetido quer dizer linha duplicada, e a soma do site sairia errada.
    EN: Rows must follow grain order with no repeated grain.
    """
    chaves = list(zip(*(colunas[c] for c in spec["ordem"]), strict=True))
    for indice in range(1, len(chaves)):
        if chaves[indice] == chaves[indice - 1]:
            return [f"{nome}: grão repetido na linha {indice}: {chaves[indice]}"]
        if chaves[indice] < chaves[indice - 1]:
            return [f"{nome}: linha {indice} fora da ordem do grão {spec['ordem']}"]
    return []


def _validar_meses(nome: str, colunas: dict, spec: dict, data_base: str) -> list[str]:
    """
    PT: Arquivo do último mês: toda linha na data-base da exportação.
        Arquivo com faixa de meses: nenhum mês depois da data-base, e no
        máximo os meses que o contrato pede.
    EN: Last-month files must sit on the export data-base; ranged files
        must not pass it or exceed the contract's month count.
    """
    datas = colunas.get("data_base", [])
    if spec.get("ultimo_mes") and any(d != data_base for d in datas):
        return [f"{nome}: há linha fora da data-base da exportação {data_base}"]
    if spec.get("meses"):
        meses = sorted(set(datas))
        if meses[-1] != data_base:
            return [f"{nome}: o último mês é {meses[-1]}, e não a data-base {data_base}"]
        if len(meses) > spec["meses"]:
            return [f"{nome}: {len(meses)} meses, mais que os {spec['meses']} do contrato"]
    return []


# -----------------------------------------------------------------------------
# PT: Dado pessoal / EN: personal data
# -----------------------------------------------------------------------------


def validar_sem_dado_pessoal(conteudos: dict[str, dict], contrato: dict) -> list[str]:
    """
    PT: Os marts de apresentação são agregados por UF e modalidade, e nenhum
        deveria trazer identificador. Esta conferência garante isso no
        arquivo que vai para o site, pelo nome da coluna e pelo formato dos
        textos.
    EN: Presentation marts are aggregated and should carry no identifier;
        this checks the shipped files by column name and text format.
    """
    problemas = []
    for spec in contrato["arquivos"]:
        conteudo = conteudos.get(spec["arquivo"])
        if not conteudo or not isinstance(conteudo.get("colunas"), dict):
            continue
        for nome_da_coluna, valores in conteudo["colunas"].items():
            if nome_da_coluna.lower().startswith(PREFIXOS_PESSOAIS):
                problemas.append(f"{spec['arquivo']}: coluna com nome de dado pessoal: {nome_da_coluna}")
            textos = [v for v in valores if isinstance(v, str)] if isinstance(valores, list) else []
            achado = next((v for v in textos if any(p.fullmatch(v) for p in IDENTIFICADORES)), None)
            if achado:
                problemas.append(f"{spec['arquivo']}, coluna {nome_da_coluna}: texto com formato de CPF ou CNPJ")
    return problemas


# -----------------------------------------------------------------------------
# PT: Ontologia e manifesto / EN: ontology and manifest
# -----------------------------------------------------------------------------


def validar_auxiliares(textos: dict[str, str], conteudos: dict[str, dict], contrato: dict) -> list[str]:
    """
    PT: O ontologia.json e o manifesto.json precisam ser exatamente o que a
        exportação monta. Um arquivo editado à mão, um dado trocado sem
        refazer o manifesto ou uma ontologia mudada sem nova exportação
        aparecem aqui.
    EN: The ontology and manifest must be exactly what the export builds.
    """
    problemas = []
    dados = {spec["arquivo"]: conteudos[spec["arquivo"]] for spec in contrato["arquivos"]}
    esperada = montar_ontologia(contrato, codigos_de_modalidade(dados))
    if conteudos[ONTOLOGIA] != esperada:
        problemas.append(
            f"{ONTOLOGIA}: difere do que a exportação monta da ontologia. "
            "Rode a exportação com --sem-databricks"
        )

    data_base = conteudos[contrato["arquivos"][0]["arquivo"]]["data_base"]
    esperado = montar_manifesto(contrato, data_base, {**textos, ONTOLOGIA: texto_de_registro(esperada)})
    atual = conteudos[MANIFESTO]
    for chave in ("arquivo", "versao_do_contrato", "data_base", "parametros_da_decisao", "visoes_do_manifesto"):
        if atual.get(chave) != esperado[chave]:
            problemas.append(f"{MANIFESTO}: {chave} difere: {atual.get(chave)!r}, esperado {esperado[chave]!r}")
    registrados = {item.get("arquivo"): item for item in atual.get("arquivos", [])}
    for item in esperado["arquivos"]:
        registrado = registrados.get(item["arquivo"], {})
        for campo in ("linhas", "sha256", "visoes"):
            if registrado.get(campo) != item[campo]:
                problemas.append(f"{MANIFESTO}: {campo} de {item['arquivo']} não bate com o arquivo")
    if set(registrados) != {item["arquivo"] for item in esperado["arquivos"]}:
        problemas.append(f"{MANIFESTO}: lista de arquivos diferente da do contrato")
    return problemas


# -----------------------------------------------------------------------------
# PT: As duas fontes da visão 1 / EN: the two sources of view 1
# -----------------------------------------------------------------------------


def _por_coluna(conteudo: dict, coluna: str) -> dict[str, list]:
    """PT: os valores da coluna, agrupados por UF / EN: column values by state"""
    grupos: dict[str, list] = {}
    for uf, valor in zip(conteudo["colunas"]["uf"], conteudo["colunas"][coluna], strict=True):
        grupos.setdefault(uf, []).append(valor)
    return grupos


def validar_visao_1(conteudos: dict[str, dict]) -> list[str]:
    """
    PT: A visão 1 lê o carteira_por_uf.json em "todas as modalidades" e o
        decisao.json numa modalidade (#69). Os dois saem de marts diferentes,
        e a tela só é coerente se eles concordarem, UF por UF:
        - as empresas são as mesmas, o denominador do ADR 0014;
        - a carteira PJ é a soma das modalidades, até o arredondamento de meio
          real por linha;
        - a mediana é a das UFs acima do corte de materialidade, e o índice
          de espaço é a carteira por empresa dividida por ela.
    EN: View 1 reads both files, which come from different marts; they must
        agree per state on companies, PJ portfolio and the median and index.
    """
    nome = "carteira_por_uf.json"
    uf = conteudos[nome]["colunas"]
    decisao = conteudos["decisao.json"]
    empresas_na_decisao = {u: set(v) for u, v in _por_coluna(decisao, "empresas").items()}
    carteira_na_decisao = _por_coluna(decisao, "carteira_ativa")

    problemas = []
    for indice, sigla in enumerate(uf["uf"]):
        if empresas_na_decisao.get(sigla) != {uf["empresas"][indice]}:
            problemas.append(f"{nome}, {sigla}: empresas diferentes das do decisao.json")
        parcelas = carteira_na_decisao.get(sigla, [])
        if abs(uf["carteira_pj"][indice] - sum(parcelas)) > 0.5 * (len(parcelas) + 1):
            problemas.append(f"{nome}, {sigla}: carteira PJ diferente da soma das modalidades do decisao.json")
    if problemas:
        return problemas

    corte = parametros_da_decisao()["decisao_carteira_minima"]
    acima = sorted(
        cpe for cpe, carteira in zip(uf["carteira_por_empresa"], uf["carteira_pj"], strict=True) if carteira >= corte
    )
    meio = len(acima) // 2
    mediana = acima[meio] if len(acima) % 2 else (acima[meio - 1] + acima[meio]) / 2
    if any(abs(m - mediana) > 1 for m in uf["mediana_carteira_por_empresa"]):
        return [f"{nome}: mediana diferente da mediana das UFs acima do corte ({mediana})"]
    for indice, sigla in enumerate(uf["uf"]):
        esperado = uf["carteira_por_empresa"][indice] / uf["mediana_carteira_por_empresa"][indice]
        if abs(uf["indice_de_espaco"][indice] - esperado) > 1e-4:
            return [f"{nome}, {sigla}: índice de espaço diferente da carteira por empresa sobre a mediana"]
    return []


# -----------------------------------------------------------------------------
# PT: Validação completa / EN: full validation
# -----------------------------------------------------------------------------


def validar(textos: dict[str, str], contrato: dict) -> list[str]:
    """
    PT: Valida o conjunto de arquivos da pasta de dados, pelo nome e texto.
    EN: Validates the data folder's file set, by name and text.
    """
    esperados = arquivos_gerados(contrato)
    problemas = [f"arquivo fora do contrato: {nome}" for nome in sorted(set(textos) - set(esperados))]
    problemas += [f"arquivo do contrato faltando: {nome}" for nome in esperados if nome not in textos]
    if problemas:
        return problemas

    conteudos = {}
    for nome in esperados:
        try:
            conteudos[nome] = json.loads(textos[nome])
        except json.JSONDecodeError as erro:
            problemas.append(f"{nome}: JSON inválido: {erro}")
    if problemas:
        return problemas

    for spec in contrato["arquivos"]:
        problemas += validar_dados(conteudos[spec["arquivo"]], spec)
    problemas += validar_sem_dado_pessoal(conteudos, contrato)
    if problemas:
        return problemas

    datas = {conteudos[spec["arquivo"]]["data_base"] for spec in contrato["arquivos"]}
    if len(datas) != 1:
        return [f"arquivos com datas-base de topo diferentes: {sorted(datas)}"]
    problemas = validar_visao_1(conteudos)
    if problemas:
        return problemas
    return validar_auxiliares(textos, conteudos, contrato)


def ler_pasta() -> dict[str, str]:
    """PT: todos os arquivos da pasta de dados / EN: every data folder file"""
    if not DESTINO.exists():
        return {}
    return {
        caminho.name: caminho.read_text(encoding="utf-8") for caminho in sorted(DESTINO.iterdir()) if caminho.is_file()
    }


def ler_malha() -> str | None:
    """PT: o texto da malha das UFs, se existir / EN: the state mesh text, if any"""
    return DESTINO_DA_MALHA.read_text(encoding="utf-8") if DESTINO_DA_MALHA.exists() else None


def validar_arquivo_da_malha(texto: str | None) -> list[str]:
    """
    PT: A malha das UFs fica em public/geo, fora da pasta de dados, porque
        não sai de um mart e não muda a cada mês (#67). Por isso é conferida
        à parte, pela regra de scripts/gerar_malha_do_dashboard.py.
    EN: The state mesh lives outside the data folder, since it comes from no
        mart and does not change monthly, so it is checked separately.
    """
    if texto is None:
        return ["arquivo do contrato faltando: geo/ufs.json"]
    return validar_malha(texto, ufs_da_ontologia())


# -----------------------------------------------------------------------------
# PT: Controle negativo / EN: negative control
# -----------------------------------------------------------------------------


def _com_estrago(textos: dict[str, str], contrato: dict, arquivo: str, estragar) -> dict[str, str]:
    """
    PT: Uma cópia dos textos com um arquivo de dados estragado. O manifesto é
        refeito em seguida, para o estrago ser pego pelo motivo certo, e não
        pelo sha256 que mudou junto.
    EN: A copy with one data file broken; the manifest is rebuilt so the
        breakage is caught for the right reason, not the changed sha256.
    """
    copia = dict(textos)
    conteudo = copy.deepcopy(json.loads(textos[arquivo]))
    estragar(conteudo)
    copia[arquivo] = texto_de_dados(conteudo["arquivo"], conteudo["data_base"], conteudo["colunas"])
    data_base = json.loads(textos[MANIFESTO])["data_base"]
    copia[MANIFESTO] = texto_de_registro(montar_manifesto(contrato, data_base, copia))
    return copia


def _definir(coluna: str, indice: int, valor):
    """PT: estrago que troca um valor / EN: breakage replacing one value"""
    return lambda conteudo: conteudo["colunas"][coluna].__setitem__(indice, valor)


def _somar(coluna: str, indice: int, parcela):
    """PT: estrago que desloca um valor / EN: breakage shifting one value"""
    def estragar(conteudo):
        conteudo["colunas"][coluna][indice] += parcela

    return estragar


def autoteste(textos: dict[str, str], contrato: dict) -> list[str]:
    """
    PT: Cada caso estraga uma coisa e diz o trecho que a reprovação precisa
        trazer. O caso falha se a validação aprovar o arquivo estragado, ou
        se reprovar por outro motivo.
    EN: Each case breaks one thing and names the fragment the rejection must
        carry; it fails if validation passes or rejects for another reason.
    """
    if validar(textos, contrato):
        return ["os arquivos versionados já falham na validação; o autoteste parte deles"]

    decisao = "decisao.json"
    linhas = len(json.loads(textos[decisao])["colunas"]["uf"])

    def com_manifesto(estragar):
        def aplicar(base):
            copia = dict(base)
            manifesto = json.loads(copia[MANIFESTO])
            estragar(manifesto)
            copia[MANIFESTO] = texto_de_registro(manifesto)
            return copia

        return aplicar

    def com_ontologia_editada(base):
        copia = dict(base)
        ontologia = json.loads(copia[ONTOLOGIA])
        ontologia["conceitos"][0]["definicao"] = "definição escrita à mão"
        copia[ONTOLOGIA] = texto_de_registro(ontologia)
        return copia

    def com_arquivo_a_mais(base):
        return {**base, "extra.json": "{}"}

    casos = [
        ("coluna a mais", decisao, lambda c: c["colunas"].__setitem__("observacao", ["x"] * linhas), "a mais: ['observacao']"),
        ("coluna faltando", decisao, lambda c: c["colunas"].pop("modalidade"), "faltando: ['modalidade']"),
        ("tipo errado", decisao, _definir("carteira_ativa", 0, "1000"), "tipo errado"),
        ("nulo proibido", decisao, _definir("uf", 0, None), "nulo onde o contrato não deixa"),
        ("valor fora da lista", decisao, _definir("quadrante", 0, "talvez"), "valor fora da lista"),
        ("data fora do formato", decisao, _definir("data_base", 0, "31/07/2026"), "data fora do formato"),
        ("número inválido", decisao, _definir("indice_de_espaco", 0, float("nan")), "número inválido"),
        ("grão repetido", decisao, lambda c: c["colunas"]["uf"].__setitem__(1, c["colunas"]["uf"][0]), "grão repetido"),
        ("dado pessoal", decisao, _definir("motivo_nao_avaliada", 0, "12.345.678/0001-90"), "formato de CPF ou CNPJ"),
        ("mês fora da data-base", "carteira_por_uf.json", _definir("data_base", 0, "2026-06-30"), "fora da data-base"),
        ("empresas diferentes entre as fontes da visão 1", "carteira_por_uf.json",
         _somar("empresas", 0, 1), "empresas diferentes das do decisao.json"),
        ("carteira PJ fora da soma das modalidades", "carteira_por_uf.json",
         _somar("carteira_pj", 0, 1000), "diferente da soma das modalidades"),
        ("mediana que não é a das UFs", "carteira_por_uf.json",
         _somar("mediana_carteira_por_empresa", 0, 100), "mediana diferente"),
        ("índice de espaço fora da razão", "carteira_por_uf.json",
         _somar("indice_de_espaco", 0, 0.01), "índice de espaço diferente"),
    ]
    falhas = []
    for descricao, arquivo, estragar, trecho in casos:
        problemas = validar(_com_estrago(textos, contrato, arquivo, estragar), contrato)
        if not any(trecho in p for p in problemas):
            falhas.append(f"{descricao}: esperava {trecho!r}, veio {problemas or 'aprovação'}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")

    casos_de_pasta = [
        ("sha256 errado", com_manifesto(lambda m: m["arquivos"][0].__setitem__("sha256", "0" * 64)), "sha256 de decisao.json"),
        ("ontologia editada à mão", com_ontologia_editada, "ontologia.json: difere"),
        ("arquivo fora do contrato", com_arquivo_a_mais, "arquivo fora do contrato: extra.json"),
    ]
    for descricao, estragar, trecho in casos_de_pasta:
        problemas = validar(estragar(textos), contrato)
        if not any(trecho in p for p in problemas):
            falhas.append(f"{descricao}: esperava {trecho!r}, veio {problemas or 'aprovação'}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    return falhas


def _primeiro_anel(malha: dict) -> list:
    """PT: o primeiro anel da primeira UF / EN: the first state's first ring"""
    geometria = malha["features"][0]["geometry"]
    return geometria["coordinates"][0] if geometria["type"] == "Polygon" else geometria["coordinates"][0][0]


def autoteste_da_malha(texto: str) -> list[str]:
    """
    PT: O controle negativo da malha: cada caso estraga uma cópia e diz o
        trecho que a reprovação precisa trazer. A cópia é regravada pelo
        mesmo gerador do arquivo, para o estrago ser a única diferença.
    EN: The mesh negative control: each case breaks a copy, rewritten by the
        same file writer, and names the fragment the rejection must carry.
    """
    if validar_arquivo_da_malha(texto):
        return ["a malha versionada já falha na validação; o autoteste parte dela"]

    def uf_faltando(malha):
        malha["features"].pop(0)

    def codigo_trocado(malha):
        malha["features"][0]["properties"]["codarea"] = "99"

    def sigla_trocada(malha):
        malha["features"][0]["properties"]["sigla"] = "AC"

    def casa_a_mais(malha):
        anel = _primeiro_anel(malha)
        anel[1] = [round(anel[1][0] + 0.00001, 5), anel[1][1]]

    def anel_aberto(malha):
        anel = _primeiro_anel(malha)
        anel[-1] = [round(anel[-1][0] + 0.1, 4), anel[-1][1]]

    def fora_do_brasil(malha):
        _primeiro_anel(malha)[1] = [10.0, 45.0]

    def sem_licenca(malha):
        malha["licenca"] = ""

    casos = [
        ("UF faltando", uf_faltando, "UF faltando: ['RO']"),
        ("código trocado", codigo_trocado, "código fora de dim_uf: '99'"),
        ("sigla trocada", sigla_trocada, "sigla 'AC', esperado 'RO'"),
        ("casa decimal a mais", casa_a_mais, "mais de 4 casas decimais"),
        ("anel aberto", anel_aberto, "anel aberto"),
        ("ponto fora do Brasil", fora_do_brasil, "fora do retângulo do Brasil"),
        ("licença ausente", sem_licenca, "licenca ausente"),
    ]
    falhas = []
    for descricao, estragar, trecho in casos:
        malha = json.loads(texto)
        estragar(malha)
        problemas = validar_arquivo_da_malha(texto_da_malha(malha))
        if not any(trecho in p for p in problemas):
            falhas.append(f"malha, {descricao}: esperava {trecho!r}, veio {problemas or 'aprovação'}")
        else:
            print(f"  reprovado, como devia / rejected as expected: malha, {descricao}")
    return falhas


# -----------------------------------------------------------------------------
# PT: Execução / EN: entry point
# -----------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="roda o controle negativo / run the negative control")
    argumentos = parser.parse_args()

    contrato = carregar_contrato()
    textos = ler_pasta()
    malha = ler_malha()
    if argumentos.autoteste:
        problemas = autoteste(textos, contrato)
        problemas += autoteste_da_malha(malha) if malha is not None else validar_arquivo_da_malha(None)
        sucesso = "Controle negativo em dia / negative control passes."
    else:
        problemas = validar(textos, contrato) + validar_arquivo_da_malha(malha)
        for spec in contrato["arquivos"]:
            if spec["arquivo"] in textos and not problemas:
                colunas = json.loads(textos[spec["arquivo"]])["colunas"]
                print(f"  {spec['arquivo']}: {len(colunas)} colunas, {len(next(iter(colunas.values())))} linhas")
        if not problemas:
            print(f"  geo/ufs.json: {len(json.loads(malha)['features'])} UFs")
        sucesso = "Dados do dashboard dentro do contrato / dashboard data within the contract."

    if problemas:
        print("\nFALHOU / FAILED:")
        for problema in problemas:
            print(f"  - {problema}")
        sys.exit(1)
    print(f"\n{sucesso}")


if __name__ == "__main__":
    main()
