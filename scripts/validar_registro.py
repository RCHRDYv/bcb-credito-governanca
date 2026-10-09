"""
PT: Valida o pré-registro do experimento (issue #47), sem precisar de
    credencial. Roda no CI.

    O que é conferido:

    1. **Nada mudou depois do registro sem errata.** O evaluation/registro.yml
       guarda o sha256 das hipóteses, da comparação, do gabarito.yml e de cada
       SQL do gabarito. O hash de cada arquivo precisa bater com o registrado,
       ou com o da última errata dele. Nenhum SQL a mais ou a menos. O hash é
       calculado sobre o texto sem BOM e com final de linha LF, para que o
       checkout em Windows não mude nada.
    2. **O registro original não foi reescrito.** O bloco de metadados e de
       arquivos do registro.yml tem um selo, o sha256 guardado neste script.
       Trocar um hash no registro, em vez de declarar uma errata, reprova.
    3. **Errata em forma.** Toda errata tem data no formato AAAA-MM-DD, igual
       ou posterior ao registro, o arquivo, o motivo e o hash novo.
    4. **Hipóteses coerentes.** H1 a H5, com condições de A a D, tipos de
       acerto do conjunto vigente, teste descrito e família válida, e a mesma
       data de registro do registro.yml.
    5. **Comparação completa.** Toda leitura e toda consulta do gabarito têm
       conferência, e as abstenções só a rubrica. Toda coluna citada existe na
       resposta da consulta, o N cabe nas linhas, e todo filtro com
       confere_com reproduz a coluna booleana do gabarito, linha por linha.

    Com --autoteste, roda o controle negativo: estraga cópias em memória, um
    estrago por vez, e confere que a validação reprova cada uma pelo motivo
    certo. Também confere que uma errata válida e uma cópia com CRLF e BOM
    passam.

    Com --gerar, grava o registro.yml a partir dos arquivos atuais e mostra o
    selo. Recusa sobrescrever um registro que já existe: depois do registro,
    mudança só por errata.

EN: Validates the experiment's pre-registration with no credential; runs in
    CI. Checks that no frozen file (hypotheses, comparison, answer key and its
    SQL) changed without a dated errata, that the original registry block
    still matches the seal kept in this script, that errata are well formed,
    that the hypotheses are coherent, and that the comparison spec covers
    every reading and cites only existing answer columns. With --autoteste it
    runs the negative control; with --gerar it writes the registry once.

Uso / Usage:
    uv run python -m scripts.validar_registro
    uv run python -m scripts.validar_registro --autoteste
    uv run python -m scripts.validar_registro --gerar
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from scripts.validar_perguntas import TIPOS_DE_ACERTO, VIGENTE, perguntas

RAIZ = Path(__file__).resolve().parents[1]
HIPOTESES = "evaluation/hipoteses.yml"
COMPARACAO = "evaluation/comparacao.yml"
GABARITO = "evaluation/gabarito.yml"
REGISTRO = "evaluation/registro.yml"
PASTA_SQL = "evaluation/gabarito"
PASTA_RESPOSTAS = RAIZ / PASTA_SQL / "respostas"

# PT: o sha256 do bloco original do registro.yml (metadados e arquivos), dado
#     pelo --gerar no dia do registro. Mudar esta linha é mudar o registro.
# EN: the sha256 of the registry's original block, printed by --gerar on
#     registration day. Changing this line changes the registration.
SELO = "1f1752ba23dd34da394fa3f51e5f528f4f1fc56eec53b5014743770aa036e361"

CONDICOES = {"A", "B", "C", "D"}
HIPOTESES_REGISTRADAS = ["H1", "H2", "H3", "H4", "H5"]
FAMILIAS = {"confirmatoria", "exploratoria"}
JANELAS = {"12_meses", "recorte", "ultimo_mes"}
OPERADORES = {"maior_que", "menor_que", "modulo_maior_que"}
DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH = re.compile(r"^[0-9a-f]{64}$")


# -----------------------------------------------------------------------------
# PT: Leitura e hash
# EN: Reading and hashing
# -----------------------------------------------------------------------------

def normalizado(texto: str) -> str:
    """PT: sem BOM e com LF / EN: no BOM, LF line endings"""
    return texto.removeprefix("﻿").replace("\r\n", "\n")


def sha256(texto: str) -> str:
    """PT: o sha256 do texto normalizado / EN: sha256 of the normalized text"""
    return hashlib.sha256(normalizado(texto).encode("utf-8")).hexdigest()


def carregar(texto: str) -> dict:
    return yaml.safe_load(normalizado(texto))


def caminhos_protegidos() -> list[str]:
    """PT: os arquivos que o registro congela / EN: the files the registry freezes"""
    sqls = sorted(p.relative_to(RAIZ).as_posix() for p in (RAIZ / PASTA_SQL).glob("*.sql"))
    return [HIPOTESES, COMPARACAO, GABARITO, *sqls]


def ler_textos() -> dict[str, str]:
    """
    PT: Os textos como estão no disco, com o final de linha e o BOM que
        tiverem. O hash é que normaliza.
    EN: The texts as on disk, line endings and BOM included; hashing
        normalizes.
    """
    def ler(caminho: str) -> None:
        arquivo = RAIZ / caminho
        if arquivo.exists():
            with arquivo.open(encoding="utf-8", newline="") as f:
                textos[caminho] = f.read()

    textos: dict[str, str] = {}
    for caminho in [*caminhos_protegidos(), REGISTRO]:
        ler(caminho)
    # PT: um arquivo que entrou por errata e continua valendo (como o gabarito
    #     de recuperação da #46) também é lido, para o hash dele ser conferido.
    #     O que uma errata tirou do registro não é lido.
    # EN: files added by errata and still in force are read too, so their
    #     hash is checked; files an errata removed are not.
    if REGISTRO in textos:
        for caminho in arquivos_de_errata(carregar(textos[REGISTRO])):
            if caminho not in textos:
                ler(caminho)
    return textos


def arquivos_de_errata(registro: dict) -> list[str]:
    """
    PT: Arquivos que valem por errata e não estavam no registro original.
    EN: Files in force through errata that were not in the original registry.
    """
    originais = set(registro.get("arquivos") or {})
    return [c for c in hashes_vigentes(registro) if c not in originais]


def ler_respostas() -> dict[str, dict]:
    """PT: colunas, tipos e linhas de cada consulta / EN: each query's answer"""
    return {
        arquivo.stem + ".sql": json.loads(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(PASTA_RESPOSTAS.glob("*.json"))
    }


def bloco_original(registro: dict) -> dict:
    return {"metadata": registro.get("metadata"), "arquivos": registro.get("arquivos")}


def selo(registro: dict) -> str:
    """PT: o sha256 do bloco original, em forma canônica / EN: canonical seal"""
    canonico = json.dumps(bloco_original(registro), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def montar_registro(textos: dict[str, str], data: str) -> str:
    """PT: o texto do registro.yml / EN: the registry file's text"""
    arquivos = {c: sha256(t) for c, t in sorted(textos.items()) if c != REGISTRO}
    corpo = yaml.safe_dump(
        {
            "metadata": {
                "registrado_em": data,
                "issue": 47,
                "normalizacao": "UTF-8 sem BOM, final de linha LF",
            },
            "arquivos": arquivos,
            "erratas": [],
        },
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )
    cabecalho = (
        "# =============================================================================\n"
        "# PT: Registro do pré-registro do experimento (issue #47). Guarda o sha256\n"
        "#     dos arquivos congelados. Não se edita à mão: depois do registro, uma\n"
        "#     mudança entra só como errata no fim da lista, com data, arquivo,\n"
        "#     motivo e o sha256 novo, e é declarada junto do resultado.\n"
        "#     Conferido por scripts/validar_registro.py.\n"
        "#\n"
        "# EN: Registry of the experiment's pre-registration. Holds the sha256 of\n"
        "#     the frozen files. After registration, a change enters only as an\n"
        "#     errata appended to the list, with date, file, reason and new sha256.\n"
        "# =============================================================================\n\n"
    )
    return cabecalho + corpo


# -----------------------------------------------------------------------------
# PT: Checagens do registro
# EN: Registry checks
# -----------------------------------------------------------------------------

def checar_erratas(registro: dict) -> list[str]:
    """PT: errata com data, motivo e hash / EN: well-formed errata"""
    erros = []
    registrado_em = str(registro.get("metadata", {}).get("registrado_em", ""))
    for i, errata in enumerate(registro.get("erratas") or [], start=1):
        data = str(errata.get("data") or "")
        if not DATA.match(data):
            erros.append(f"errata {i}: sem data no formato AAAA-MM-DD")
        elif data < registrado_em:
            erros.append(f"errata {i}: data {data} anterior ao registro, de {registrado_em}")
        if not str(errata.get("motivo") or "").strip():
            erros.append(f"errata {i}: sem motivo")
        if not errata.get("arquivo"):
            erros.append(f"errata {i}: sem arquivo")
        novo = errata.get("sha256")
        if novo is not None and not HASH.match(str(novo)):
            erros.append(f"errata {i}: sha256 novo inválido (use null para um arquivo removido)")
    return erros


def hashes_vigentes(registro: dict) -> dict[str, str]:
    """
    PT: O hash que vale para cada arquivo: o registrado, trocado pela última
        errata dele. Uma errata com sha256 nulo tira o arquivo do registro.
    EN: The hash in force per file: the registered one, replaced by its last
        errata; a null sha256 removes the file.
    """
    vigentes = dict(registro.get("arquivos") or {})
    for errata in registro.get("erratas") or []:
        arquivo = errata.get("arquivo")
        if not arquivo:
            continue
        if errata.get("sha256") is None:
            vigentes.pop(arquivo, None)
        else:
            vigentes[arquivo] = errata["sha256"]
    return vigentes


def checar_registro(textos: dict[str, str], selo_esperado: str) -> list[str]:
    """PT: hashes, selo e erratas / EN: hashes, seal and errata"""
    if REGISTRO not in textos:
        return [f"{REGISTRO} não existe; rode com --gerar no dia do registro"]
    registro = carregar(textos[REGISTRO])
    erros = []
    if selo(registro) != selo_esperado:
        erros.append("registro original alterado: o bloco de metadados e arquivos não bate com o selo; mudança só por errata")
    erros += checar_erratas(registro)

    vigentes = hashes_vigentes(registro)
    protegidos = {c for c in textos if c != REGISTRO}
    for caminho in sorted(protegidos - set(vigentes)):
        erros.append(f"{caminho}: fora do registro; um arquivo novo entra só por errata")
    for caminho in sorted(set(vigentes) - protegidos):
        erros.append(f"{caminho}: registrado, mas não existe; a remoção entra só por errata")
    for caminho in sorted(protegidos & set(vigentes)):
        if sha256(textos[caminho]) != vigentes[caminho]:
            erros.append(f"{caminho}: alterado depois do registro, sem errata")

    print(f"  registro: {len(vigentes)} arquivos congelados, {len(registro.get('erratas') or [])} erratas, "
          f"registrado em {registro.get('metadata', {}).get('registrado_em')}")
    return erros


# -----------------------------------------------------------------------------
# PT: Checagens das hipóteses
# EN: Hypothesis checks
# -----------------------------------------------------------------------------

def checar_hipoteses(hipoteses: dict, registro: dict | None, tipos: dict[str, str]) -> list[str]:
    """PT: H1 a H5 coerentes / EN: coherent H1 to H5"""
    erros = []
    por_id = hipoteses.get("hipoteses") or {}
    if list(por_id) != HIPOTESES_REGISTRADAS:
        erros.append(f"hipóteses registradas são {HIPOTESES_REGISTRADAS}, o arquivo traz {list(por_id)}")
    testes = set((hipoteses.get("estatistica") or {}).get("testes") or {})
    for id_, h in por_id.items():
        fora = set(h.get("comparacao") or []) - CONDICOES
        if fora or not h.get("comparacao"):
            erros.append(f"{id_}: condições inválidas {sorted(fora) or 'vazias'}")
        tipos_fora = set(h.get("tipos_de_acerto") or []) - TIPOS_DE_ACERTO
        if tipos_fora or not h.get("tipos_de_acerto"):
            erros.append(f"{id_}: tipos de acerto inválidos {sorted(tipos_fora) or 'vazios'}")
        if h.get("teste") not in testes:
            erros.append(f"{id_}: teste '{h.get('teste')}' não descrito em estatistica.testes")
        if h.get("familia") not in FAMILIAS:
            erros.append(f"{id_}: família '{h.get('familia')}' inválida")
        if not h.get("direcao"):
            erros.append(f"{id_}: sem direção")

    confirmatorias = [i for i, h in por_id.items() if h.get("familia") == "confirmatoria"]
    familia = (hipoteses.get("estatistica") or {}).get("correcao", {}).get("familia")
    if familia != confirmatorias:
        erros.append(f"a família do Holm {familia} não é a das hipóteses confirmatórias {confirmatorias}")

    if registro is not None:
        data_h = str(hipoteses.get("metadata", {}).get("registrado_em"))
        data_r = str(registro.get("metadata", {}).get("registrado_em"))
        if data_h != data_r:
            erros.append(f"data de registro das hipóteses ({data_h}) diferente da do registro.yml ({data_r})")

    contagem = {t: sum(1 for v in tipos.values() if v == t) for t in sorted(TIPOS_DE_ACERTO)}
    print(f"  hipóteses: {len(por_id)}, confirmatórias {confirmatorias}; perguntas por tipo de acerto {contagem}")
    return erros


# -----------------------------------------------------------------------------
# PT: Checagens da comparação
# EN: Comparison checks
# -----------------------------------------------------------------------------

def _numero(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _passa(linha: dict, condicoes: list[dict]) -> bool:
    """PT: a linha passa em todas as condições / EN: row meets all conditions"""
    for c in condicoes:
        x = _numero(linha.get(c["coluna"]))
        ref = _numero(linha.get(c["contra"])) if "contra" in c else _numero(c.get("valor"))
        if x is None or ref is None:
            return False
        if c["op"] == "maior_que" and not x > ref:
            return False
        if c["op"] == "menor_que" and not x < ref:
            return False
        if c["op"] == "modulo_maior_que" and not abs(x) > ref:
            return False
    return True


def checar_onde(rotulo: str, condicoes: list[dict], confere_com: str | None, resposta: dict) -> list[str]:
    """PT: filtro válido e coerente com o gabarito / EN: valid, consistent filter"""
    erros = []
    colunas = set(resposta["colunas"])
    for c in condicoes:
        if c.get("coluna") not in colunas:
            erros.append(f"{rotulo}: coluna '{c.get('coluna')}' do filtro não existe na resposta")
        if c.get("op") not in OPERADORES:
            erros.append(f"{rotulo}: operador '{c.get('op')}' inválido")
        if "contra" in c and c["contra"] not in colunas:
            erros.append(f"{rotulo}: coluna '{c['contra']}' do filtro não existe na resposta")
        if "contra" not in c and _numero(c.get("valor")) is None:
            erros.append(f"{rotulo}: filtro sem valor nem coluna de comparação")
    if erros or not confere_com:
        return erros
    if confere_com not in colunas:
        return [f"{rotulo}: confere_com '{confere_com}' não existe na resposta"]
    linhas = [dict(zip(resposta["colunas"], linha)) for linha in resposta["linhas"]]
    divergentes = [
        i for i, linha in enumerate(linhas, start=1)
        if _passa(linha, condicoes) != (str(linha.get(confere_com)).lower() == "true")
    ]
    if divergentes:
        erros.append(f"{rotulo}: o filtro não reproduz {confere_com} nas linhas {divergentes}")
    return erros


def checar_linha(rotulo: str, seletor, resposta: dict) -> list[str]:
    """PT: o seletor de linha aponta uma linha só / EN: row selector picks one row"""
    colunas = resposta["colunas"]
    if seletor is None:
        return [] if len(resposta["linhas"]) == 1 else [f"{rotulo}: a consulta tem {len(resposta['linhas'])} linhas e a conferência não diz qual"]
    if seletor in ("primeira", "ultima"):
        return []
    if not isinstance(seletor, dict) or len(seletor) != 1:
        return [f"{rotulo}: seletor de linha inválido {seletor}"]
    chave, valor = next(iter(seletor.items()))
    if chave in ("maior", "maior_em_modulo"):
        return [] if valor in colunas else [f"{rotulo}: coluna '{valor}' do seletor não existe na resposta"]
    if chave not in colunas:
        return [f"{rotulo}: coluna '{chave}' do seletor não existe na resposta"]
    achadas = sum(1 for linha in resposta["linhas"] if str(linha[colunas.index(chave)]) == str(valor))
    return [] if achadas == 1 else [f"{rotulo}: o seletor {seletor} acha {achadas} linhas, e não uma"]


def _colunas_de(valores: list) -> list[str]:
    """PT: as colunas de uma lista de valores com uma_de / EN: flatten uma_de"""
    colunas = []
    for v in valores or []:
        colunas += v["uma_de"] if isinstance(v, dict) else [v]
    return colunas


def checar_verificacao(rotulo: str, item: dict, resposta: dict) -> list[str]:
    """PT: uma conferência / EN: one check"""
    colunas = set(resposta["colunas"])
    erros = []
    if "lista" in item:
        if item["lista"] not in ("ranking", "conjunto"):
            erros.append(f"{rotulo}: lista '{item['lista']}' inválida")
        citadas = [item.get("chave"), *_colunas_de(item.get("valores"))]
        n = item.get("n", "todas")
        if item["lista"] == "ranking":
            if "n" not in item or "ordem" not in item:
                erros.append(f"{rotulo}: ranking sem n ou sem ordem")
            citadas.append(str(item.get("ordem", "")).removeprefix("-"))
        if n != "todas" and (not isinstance(n, int) or n < 1 or n > len(resposta["linhas"])):
            erros.append(f"{rotulo}: n={n} não cabe nas {len(resposta['linhas'])} linhas da resposta")
        erros += [f"{rotulo}: coluna '{c}' não existe na resposta" for c in citadas if c not in colunas]
        if "onde" in item:
            erros += checar_onde(rotulo, item["onde"], item.get("confere_com"), resposta)
    elif "classificacao" in item:
        if item["classificacao"] not in colunas:
            erros.append(f"{rotulo}: coluna '{item['classificacao']}' não existe na resposta")
        erros += checar_onde(rotulo, item.get("onde") or [], item["classificacao"], resposta)
        erros += checar_linha(rotulo, item.get("linha"), resposta)
    elif "valor" in item or "uma_de" in item:
        citadas = [item["valor"]] if "valor" in item else list(item["uma_de"])
        erros += [f"{rotulo}: coluna '{c}' não existe na resposta" for c in citadas if c not in colunas]
        erros += checar_linha(rotulo, item.get("linha"), resposta)
    else:
        erros.append(f"{rotulo}: conferência sem forma conhecida {sorted(item)}")
    return erros


def classe_de_tolerancia(coluna: str, tipo: str, regra: dict) -> str:
    """PT: a tolerância que a coluna recebe / EN: the tolerance class of a column"""
    if tipo == "BOOLEAN":
        return "classificacao"
    if tipo in ("STRING", "DATE"):
        return "identidade"
    if coluna in regra["exata"]["colunas"]:
        return "exata"
    if coluna in regra["adimensional"]["colunas"]:
        return "adimensional"
    if coluna.endswith(("_pct", "_pp")):
        return "pontos"
    return "relativa"


def checar_comparacao(comparacao: dict, gabarito: dict, respostas: dict[str, dict], regra: dict) -> list[str]:
    """PT: toda leitura conferida, com colunas que existem / EN: full coverage"""
    erros = []
    por_id = comparacao.get("perguntas") or {}
    esperadas = gabarito["perguntas"]
    erros += [f"{i}: pergunta do gabarito sem conferência na comparação" for i in sorted(set(esperadas) - set(por_id))]
    erros += [f"{i}: pergunta na comparação que não está no gabarito" for i in sorted(set(por_id) - set(esperadas))]

    for coluna in regra["exata"]["colunas"]:
        tipos = {r["tipos"][r["colunas"].index(coluna)] for r in respostas.values() if coluna in r["colunas"]}
        if tipos - {"INT", "LONG"}:
            erros.append(f"coluna exata '{coluna}' não é inteira nas respostas: {sorted(tipos)}")

    classes: dict[tuple[str, str], str] = {}
    conferidas_por_leitura = []
    for id_ in sorted(set(esperadas) & set(por_id)):
        entrada, gab = por_id[id_], esperadas[id_]
        if gab["tipo_de_acerto"] == "abstencao":
            if entrada != {"abstencao": "so_rubrica"}:
                erros.append(f"{id_}: abstenção se corrige só pela rubrica (abstencao: so_rubrica)")
            continue
        leituras = {l["id"]: l["consultas"] for l in gab.get("leituras", [])}
        if set(entrada) != set(leituras):
            erros.append(f"{id_}: leituras na comparação {sorted(entrada)}, no gabarito {sorted(leituras)}")
            continue
        com_janela = False
        for leitura, blocos in entrada.items():
            consultas = [b.get("consulta") for b in blocos]
            if sorted(consultas) != sorted(leituras[leitura]):
                erros.append(f"{id_} {leitura}: consultas {consultas}, no gabarito {leituras[leitura]}")
            for bloco in blocos:
                consulta = bloco.get("consulta")
                resposta = respostas.get(consulta)
                if resposta is None:
                    erros.append(f"{id_} {leitura}: sem resposta gerada para {consulta}")
                    continue
                if ("verificar" in bloco) == ("janelas" in bloco):
                    erros.append(f"{id_} {leitura} {consulta}: use verificar ou janelas, e só um dos dois")
                    continue
                listas = {"": bloco["verificar"]} if "verificar" in bloco else bloco["janelas"]
                com_janela |= "janelas" in bloco
                for janela, itens in listas.items():
                    if janela and janela not in JANELAS:
                        erros.append(f"{id_} {leitura}: janela '{janela}' inválida")
                    if not itens:
                        erros.append(f"{id_} {leitura} {consulta}: sem conferência")
                    for item in itens or []:
                        rotulo = " ".join(p for p in (id_, leitura, janela, consulta) if p)
                        erros += checar_verificacao(rotulo, item, resposta)
                for coluna, tipo in zip(resposta["colunas"], resposta["tipos"]):
                    classes[(consulta, coluna)] = classe_de_tolerancia(coluna, tipo, regra)
        if len(entrada) > 1 or com_janela:
            conferidas_por_leitura.append(id_)

    contagem = {c: list(classes.values()).count(c) for c in sorted(set(classes.values()))}
    print(f"  comparação: {len(por_id)} perguntas; colunas das respostas por tolerância {contagem}")
    print(f"     leitura declarada conferida pelo Yuri em {len(conferidas_por_leitura)}: {conferidas_por_leitura}")
    return erros


# -----------------------------------------------------------------------------
# PT: Validação completa
# EN: Full validation
# -----------------------------------------------------------------------------

def validar(textos: dict[str, str], respostas: dict[str, dict], selo_esperado: str) -> list[str]:
    erros = checar_registro(textos, selo_esperado)
    registro = carregar(textos[REGISTRO]) if REGISTRO in textos else None
    _, por_id = perguntas(VIGENTE)
    # PT: sem o campo, o tipo é valor, como no questions_v3.yml.
    # EN: with no field, the type is valor, as in questions_v3.yml.
    tipos = {i: p.get("tipo_de_acerto", "valor") for i, p in por_id.items()}
    hipoteses = carregar(textos[HIPOTESES])
    erros += checar_hipoteses(hipoteses, registro, tipos)
    erros += checar_comparacao(
        carregar(textos[COMPARACAO]), carregar(textos[GABARITO]), respostas, hipoteses["comparacao"]["tolerancia"]
    )
    return erros


# -----------------------------------------------------------------------------
# PT: Controle negativo
# EN: Negative control
# -----------------------------------------------------------------------------

def _trocar(caminho: str, antes: str, depois: str):
    """PT: estrago que troca um trecho / EN: breakage replacing a fragment"""
    def estragar(textos):
        if antes not in textos[caminho]:
            raise ValueError(f"o autoteste procura '{antes}' em {caminho}, e não acha")
        textos[caminho] = textos[caminho].replace(antes, depois, 1)
    return estragar


def _com_errata(caminho: str, **campos):
    """
    PT: Altera o arquivo e declara a errata dele, com os campos dados. Sem
        um campo, a errata fica sem ele.
    EN: Changes the file and declares its errata with the given fields.
    """
    def estragar(textos):
        textos[caminho] += "\n-- errata de teste\n"
        registro = carregar(textos[REGISTRO])
        errata = {"arquivo": caminho, "sha256": sha256(textos[caminho]), **campos}
        registro["erratas"] = [*(registro.get("erratas") or []), {k: v for k, v in errata.items() if v is not None}]
        textos[REGISTRO] = yaml.safe_dump(registro, allow_unicode=True, sort_keys=False)
    return estragar


def _reselar(textos: dict[str, str]) -> str:
    """
    PT: Refaz o registro e o selo de uma cópia, para que um estrago de
        estrutura seja pego pelo motivo certo, e não pelo hash que mudou junto.
    EN: Rebuilds a copy's registry and seal, so a structural breakage is
        caught for the right reason, not the changed hash.
    """
    data = carregar(textos[REGISTRO])["metadata"]["registrado_em"]
    textos[REGISTRO] = montar_registro(textos, data)
    return selo(carregar(textos[REGISTRO]))


def autoteste(textos: dict[str, str], respostas: dict[str, dict]) -> list[str]:
    """
    PT: Cada caso estraga uma coisa e diz o trecho que a reprovação precisa
        trazer. O caso falha se a validação aprovar a cópia estragada, ou se
        reprovar por outro motivo. Os casos positivos precisam passar.
    EN: Each case breaks one thing and names the fragment the rejection must
        carry; positive cases must pass.
    """
    if validar(textos, respostas, SELO):
        return ["os arquivos versionados já falham na validação; o autoteste parte deles"]

    sql = f"{PASTA_SQL}/Q01.sql"

    def sql_a_mais(t):
        t[f"{PASTA_SQL}/Q99.sql"] = "select 1\n"

    def sql_a_menos(t):
        del t[f"{PASTA_SQL}/Q34.sql"]

    def hash_trocado(t):
        _trocar(sql, "select", "select /* mudado */")(t)
        t[REGISTRO] = t[REGISTRO].replace(carregar(t[REGISTRO])["arquivos"][sql], sha256(t[sql]))

    def comparacao_sem_q34(t):
        inicio = t[COMPARACAO].index("  Q34:\n")
        fim = t[COMPARACAO].index("  Q35:\n")
        t[COMPARACAO] = t[COMPARACAO][:inicio] + t[COMPARACAO][fim:]

    # PT: (descrição, estrago, trecho esperado, refazer o registro)
    # EN: (description, breakage, expected fragment, rebuild the registry)
    negativos = [
        ("hipótese alterada", _trocar(HIPOTESES, "B acerta mais que A.", "B acerta muito mais que A."),
         f"{HIPOTESES}: alterado", False),
        ("gabarito.yml alterado", _trocar(GABARITO, "metadata:", "# nota\nmetadata:"), f"{GABARITO}: alterado", False),
        ("comparação alterada", _trocar(COMPARACAO, "n: 5", "n: 4"), f"{COMPARACAO}: alterado", False),
        ("SQL alterado", _trocar(sql, "select", "select /* mudado */"), f"{sql}: alterado", False),
        ("SQL a mais", sql_a_mais, "Q99.sql: fora do registro", False),
        ("SQL a menos", sql_a_menos, "Q34.sql: registrado, mas não existe", False),
        ("hash trocado no registro, sem errata", hash_trocado, "registro original alterado", False),
        ("errata sem data", _com_errata(sql, motivo="teste"), "sem data", False),
        ("errata sem motivo", _com_errata(sql, data="2099-01-01"), "sem motivo", False),
        ("errata anterior ao registro", _com_errata(sql, data="2000-01-01", motivo="teste"), "anterior ao registro", False),
        ("hipótese a menos", _trocar(HIPOTESES, "  H5:\n", "  H6:\n"), "hipóteses registradas são", True),
        ("coluna inexistente na comparação", _trocar(COMPARACAO, "valor: carteira_ativa_do_ano_anterior",
                                                     "valor: carteira_do_ano_anterior"), "'carteira_do_ano_anterior' não existe", True),
        ("leitura sem conferência", comparacao_sem_q34, "Q34: pergunta do gabarito sem conferência", True),
        ("filtro que não reproduz o gabarito", _trocar(COMPARACAO, "op: modulo_maior_que, valor: 2}",
                                                       "op: modulo_maior_que, valor: 1}"), "não reproduz atipica", True),
    ]

    # PT: um arquivo que entrou por errata (#46) também fica congelado.
    # EN: a file added by errata is frozen too.
    de_errata = [c for c in arquivos_de_errata(carregar(textos[REGISTRO])) if c in textos]
    if de_errata:
        def errata_alterada(t, caminho=de_errata[0]):
            t[caminho] += "\n"
        negativos.append(("arquivo que entrou por errata alterado", errata_alterada, f"{de_errata[0]}: alterado", False))

    def errata_valida(t):
        _com_errata(sql, data="2099-01-01", motivo="teste de errata válida")(t)

    def crlf_e_bom(t):
        for caminho in list(t):
            t[caminho] = "﻿" + normalizado(t[caminho]).replace("\n", "\r\n")

    positivos = [("errata válida", errata_valida), ("CRLF e BOM", crlf_e_bom)]

    falhas = []
    for descricao, estragar, trecho, reselar in negativos:
        copia = dict(textos)
        estragar(copia)
        selo_da_copia = _reselar(copia) if reselar else SELO
        problemas = validar(copia, respostas, selo_da_copia)
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    for descricao, aplicar in positivos:
        copia = dict(textos)
        aplicar(copia)
        problemas = validar(copia, respostas, SELO)
        if problemas:
            falhas.append(f"reprovou o caso que devia passar, {descricao}: {problemas}")
        else:
            print(f"  aprovado, como devia / accepted as expected: {descricao}")
    return falhas


# -----------------------------------------------------------------------------
# PT: Execução
# EN: Entry point
# -----------------------------------------------------------------------------

def gerar(textos: dict[str, str], data: str) -> None:
    """PT: grava o registro uma vez / EN: writes the registry once"""
    destino = RAIZ / REGISTRO
    if destino.exists():
        print(f"{REGISTRO} já existe. Depois do registro, mudança só por errata / registry exists; use errata.")
        sys.exit(1)
    texto = montar_registro({c: t for c, t in textos.items() if c != REGISTRO}, data)
    destino.write_text(texto, encoding="utf-8", newline="\n")
    print(f"{REGISTRO} gravado / written. Selo para a constante SELO / seal: {selo(carregar(texto))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="roda o controle negativo / run the negative control")
    parser.add_argument("--gerar", action="store_true", help="grava o registro.yml uma vez / write the registry once")
    argumentos = parser.parse_args()

    textos = ler_textos()
    if argumentos.gerar:
        gerar(textos, str(carregar(textos[HIPOTESES])["metadata"]["registrado_em"]))
        return

    respostas = ler_respostas()
    if argumentos.autoteste:
        problemas = autoteste(textos, respostas)
        sucesso = "Controle negativo em dia / negative control passes."
    else:
        problemas = validar(textos, respostas, SELO)
        sucesso = "Pré-registro íntegro / pre-registration intact."

    if problemas:
        print("\nFALHOU / FAILED:")
        for problema in problemas:
            print(f"  - {problema}")
        sys.exit(1)
    print(f"\n{sucesso}")


if __name__ == "__main__":
    main()
