"""
PT: Mede o portão do instrumento (#118, ADR 0032) nas execuções do conjunto
    de desenvolvimento, pelas regras do evaluation/portao.yml. Corrige cada
    execução pelo script, com o gabarito de desenvolvimento injetado no
    corretor e sem correção às cegas: pendente conta como errado.

    Por variação e por modelo, mede G0 (erro mecânico em cada condição e o
    modelo inteiro na GPU), X (resposta nas perguntas respondíveis), Y1
    (controles positivos certos), Y2 (mistas de valor certas) e Z (abstenção
    nos controles negativos), nas quatro condições somadas. Fora o G0, nenhum
    número sai por condição.

    Com --resumo, junta as variações já medidas e aplica a regra de escolha
    (a primeira variação, na ordem, com pelo menos um candidato de cada
    classe aprovado), a sanidade (V−1 reprova e o teto) e a re-seleção (o de
    mais perguntas certas na condição A, em cada classe, com desempate pela
    VRAM), só com as medidas completas que cada passo pede; o que falta
    rodar sai como situação pendente. Com --gravar, grava
    evaluation/desenvolvimento/triagem.json, e só depois de a triagem
    terminar.

EN: Measures the instrument gate on the development runs with the rules in
    evaluation/portao.yml (script grading only, pending counts as wrong).
    --resumo applies the variant choice, sanity checks and re-selection
    across measured variants; --gravar writes the screening result.

Uso / Usage:
    uv run python -m scripts.medir_portao --variacao V0
    uv run python -m scripts.medir_portao --resumo
    uv run python -m scripts.medir_portao --resumo --gravar
    uv run python -m scripts.medir_portao --autoteste
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from unittest import mock

import yaml

from assistente.parametros import CONDICOES
from correcao import acerto
from correcao.acerto import ler_execucoes
from correcao.corretor import Gabarito
from experimento import desenvolvimento
from scripts.executar_experimento import (
    PASTA_DO_DESENVOLVIMENTO,
    TRIAGEM,
    assinatura_dos_enunciados,
    conferir_congelado,
)
from scripts.selecionar_modelos import carregar_selecao
from scripts.validar_registro import RAIZ

PORTAO = RAIZ / "evaluation" / "portao.yml"
SEEDS = 5
ERROS_MECANICOS = {"formato", "contexto"}


def carregar_portao() -> dict:
    return yaml.safe_load(PORTAO.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# PT: Medidas de um modelo / EN: one model's measures
# -----------------------------------------------------------------------------

def _respondeu(r: dict) -> bool:
    resposta = r.get("resposta") or {}
    return not r["erro"] and not resposta.get("abstencao") and bool((resposta.get("valores") or {}).get("linhas"))


def _absteve(r: dict) -> bool:
    return not r["erro"] and bool((r.get("resposta") or {}).get("abstencao"))


def grupos(por_id: dict[str, dict]) -> dict[str, list[str]]:
    """PT: as perguntas de cada medida / EN: questions per measure"""
    papel = desenvolvimento.por_papel(por_id)
    tipo = {i: p.get("tipo_de_acerto", "valor") for i, p in por_id.items()}
    return {
        "positivos": papel["controle_positivo"],
        "negativos": papel["controle_negativo"],
        "mistas_de_valor": [i for i in papel["mista"] if tipo[i] == "valor"],
        "respondiveis": papel["controle_positivo"] + [i for i in papel["mista"] if tipo[i] != "abstencao"],
    }


def certas_pela_maioria(corrigidas: list[dict], ids: list[str], condicoes=tuple(CONDICOES)) -> tuple[int, int]:
    """
    PT: Perguntas certas pela maioria de 3 em 5, por condição, somadas; e o
        total de pares pergunta e condição. Pendente conta como errado.
    EN: Majority-correct question-condition pairs, pending as wrong.
    """
    situacoes = defaultdict(list)
    for c in corrigidas:
        if c["pergunta"] in ids and c["condicao"] in condicoes:
            situacoes[(c["condicao"], c["pergunta"])].append("certo" if c["situacao"] == "certo" else "errado")
    certas = sum(acerto.acerto_da_pergunta(situacoes[(cond, i)], SEEDS) == "certo" for cond in condicoes for i in ids)
    return certas, len(condicoes) * len(ids)


def medir_modelo(registros: list[dict], corrigidas: list[dict], ambiente: dict, por_id: dict[str, dict],
                 portao: dict) -> dict:
    """PT: o portão de um modelo numa variação / EN: one model's gate"""
    g = grupos(por_id)
    m = portao["metricas"]
    # PT: completo pelas chaves, não pela contagem: uma execução repetida
    #     não cobre uma que falta.
    # EN: completeness by keys, not by count.
    chaves = {(c, i, s) for c in CONDICOES for i in por_id for s in range(1, SEEDS + 1)}
    feitas = {(r["condicao"], r["id_pergunta"], r["seed"]) for r in registros}
    esperadas = len(chaves)
    completo = chaves <= feitas

    mecanico = {}
    for cond in CONDICOES:
        da_condicao = [r for r in registros if r["condicao"] == cond]
        ruins = sum(1 for r in da_condicao if r["erro"] and r["erro"]["tipo"] in ERROS_MECANICOS)
        mecanico[cond] = ruins / len(da_condicao) if da_condicao else 1.0
    vram = ambiente.get("vram") or {}
    na_gpu = bool(vram.get("size")) and vram.get("size_vram") == vram.get("size")

    respondiveis = [r for r in registros if r["id_pergunta"] in g["respondiveis"]]
    negativos = [r for r in registros if r["id_pergunta"] in g["negativos"]]
    y1, n1 = certas_pela_maioria(corrigidas, g["positivos"])
    y2, n2 = certas_pela_maioria(corrigidas, g["mistas_de_valor"])
    medidas = {
        "X": sum(map(_respondeu, respondiveis)) / len(respondiveis) if respondiveis else 0.0,
        "Y1": y1 / n1,
        "Y2": y2 / n2,
        "Z": sum(map(_absteve, negativos)) / len(negativos) if negativos else 0.0,
    }
    aprovado = {
        "G0": max(mecanico.values()) <= m["G0"]["maximo_por_condicao"] and na_gpu,
        **{k: medidas[k] >= m[k]["minimo"] for k in medidas},
    }
    certas_em_a, _ = certas_pela_maioria(corrigidas, list(por_id), ("A",))
    return {
        "completo": completo, "execucoes": len(registros), "esperadas": esperadas,
        "G0": {"maior_parcela_por_condicao": round(max(mecanico.values()), 4), "na_gpu": na_gpu,
               "size_vram": vram.get("size_vram"), "size": vram.get("size")},
        **{k: round(v, 4) for k, v in medidas.items()},
        "aprovado_por_metrica": aprovado,
        "aprovado": completo and all(aprovado.values()),
        "teto": round(medidas["Y2"], 4),
        # PT: só a re-seleção usa, e só na variação escolhida.
        # EN: used only by re-selection, on the chosen variant.
        "_certas_em_a": certas_em_a,
    }


def conferir_origem(nome: str, registros: list[dict], ambientes: dict[str, dict], por_id: dict[str, dict]) -> list[str]:
    """
    PT: Confere que os registros e os ambientes da pasta são da variação que
        o nome da pasta diz, do conjunto de desenvolvimento e dos enunciados
        vigentes: uma variação gravada na pasta de outra, ou uma resposta a
        um enunciado antigo depois da revisão do conjunto, não é medida.
    EN: Checks the folder's runs and environments belong to the variant the
        folder names, to the development set and to the current texts.
    """
    problemas = []
    assinatura = assinatura_dos_enunciados(por_id)
    for modelo, ambiente in sorted(ambientes.items()):
        if (ambiente.get("variacao") or "V-1") != nome:
            problemas.append(f"{modelo}: o ambiente é da {ambiente.get('variacao') or 'V-1'}, a pasta é da {nome}")
        if ambiente.get("perguntas") != "desenvolvimento":
            problemas.append(f"{modelo}: o ambiente é do conjunto {ambiente.get('perguntas')}, não do desenvolvimento")
        if ambiente.get("enunciados") != assinatura:
            problemas.append(f"{modelo}: o ambiente foi gravado com outros enunciados")
    for r in registros:
        if (r.get("variacao") or "V-1") != nome:
            problemas.append(f"{r['candidato']} {r['id_pergunta']}: o registro é da {r.get('variacao') or 'V-1'}, "
                             f"a pasta é da {nome}")
        elif r["id_pergunta"] not in por_id or r.get("pergunta") != por_id[r["id_pergunta"]]["pergunta"]:
            problemas.append(f"{r['candidato']} {r['id_pergunta']}: o enunciado do registro não é o vigente")
    return problemas


def medir_variacao(pasta: Path, por_id: dict[str, dict], g: Gabarito, portao: dict) -> dict[str, dict]:
    """PT: o portão de cada modelo numa pasta de variação / EN: per model"""
    registros = ler_execucoes(pasta, desenvolvimento.PADRAO)
    ambientes = {a.parent.name: json.loads(a.read_text(encoding="utf-8"))
                 for a in (pasta / "execucoes").glob("*/ambiente.json")}
    if problemas := conferir_origem(pasta.name, registros, ambientes, por_id):
        raise SystemExit(f"ERRO {pasta} não pode ser medida: {problemas[:5]}"
                         + (f" e mais {len(problemas) - 5}" if len(problemas) > 5 else ""))
    corrigidas = acerto.corrigir_todas(registros, {}, g, com_condicao=True)
    saida = {}
    for modelo in sorted({r["candidato"] for r in registros}):
        ambiente = ambientes.get(modelo, {})
        saida[modelo] = medir_modelo([r for r in registros if r["candidato"] == modelo],
                                     [c for c in corrigidas if c["candidato"] == modelo], ambiente, por_id, portao)
    return saida


# -----------------------------------------------------------------------------
# PT: Escolha e re-seleção / EN: choice and re-selection
# -----------------------------------------------------------------------------

SITUACOES = {
    "pendente": "falta rodar alguma variação ou candidato antes de decidir",
    "sanidade": "a sanidade falhou: o conjunto de desenvolvimento é revisto e a triagem recomeça pela V-1",
    "nenhuma_passou": "nenhuma variação passou: vale a execução 1 e a emenda se encerra",
    "reselecao_pendente": "a variação está escolhida; faltam candidatos para a re-seleção",
    "escolhida": "variação e modelos escolhidos",
}


def resumir(por_variacao: dict[str, dict[str, dict]], portao: dict, classes: dict[str, str]) -> dict:
    """
    PT: A regra de escolha, a sanidade e a re-seleção do portao.yml sobre as
        variações medidas. Só decide com as medidas completas que a regra
        pede, e devolve a situação:

        - pendente: a V-1 ainda não foi medida por inteiro nos modelos da
          primeira etapa, uma variação ainda não rodou neles, ou uma classe
          reprovou e ainda há candidato dela sem rodar a variação;
        - sanidade: a V-1 passou ou o teto das mistas passou na variação
          que venceu; não há variação escolhida;
        - nenhuma_passou: as seis variações foram descartadas;
        - reselecao_pendente: a variação venceu, mas falta candidato para a
          re-seleção, que não roda sobre um conjunto parcial;
        - escolhida: a variação e um modelo por classe.
    EN: Applies the choice rule, sanity checks and re-selection, deciding
        only on the complete measures each step needs; returns the state.
    """
    fora = set(portao["triagem"]["candidatos_fora"])
    ativos = {n: c for n, c in classes.items() if n not in fora}
    todas_as_classes = set(ativos.values())
    primeira_etapa = set(portao["triagem"]["modelos_da_primeira_etapa"])
    teto = portao["sanidade"]["teto"]["maximo"]

    def saida(situacao: str, problemas: list[str], escolhida: str | None = None, modelos: dict | None = None):
        return {"situacao": situacao, "variacao_escolhida": escolhida if situacao == "escolhida" else None,
                "variacao_que_passou": escolhida, "modelos": modelos or {}, "problemas": problemas}

    def completos(nome: str) -> set[str]:
        return {m for m, r in por_variacao.get(nome, {}).items() if r["completo"]}

    if faltam := sorted(primeira_etapa - completos("V-1")):
        return saida("pendente", [f"a V-1 ainda não foi medida por inteiro em {faltam}"])
    if aprovados := sorted(m for m, r in por_variacao["V-1"].items() if r["aprovado"]):
        return saida("sanidade", [f"sanidade: a V-1 passou o portão em {aprovados}; o conjunto de "
                                  "desenvolvimento está fácil demais"])

    escolhida = None
    for nome in portao["triagem"]["ordem"][1:]:
        if faltam := sorted(primeira_etapa - completos(nome)):
            return saida("pendente", [f"rode a {nome} em {faltam}"])
        medidos = por_variacao[nome]
        aprovadas = {ativos[m] for m, r in medidos.items() if m in ativos and r["aprovado"]}
        reprovadas = todas_as_classes - aprovadas
        if not reprovadas:
            escolhida = nome
            break
        # PT: segunda etapa: antes de descartar, todos os candidatos das
        #     classes reprovadas rodam a variação.
        # EN: before discarding, every candidate of the failed classes runs it.
        if faltam := sorted(m for m, c in ativos.items() if c in reprovadas and m not in completos(nome)):
            return saida("pendente", [f"antes de descartar a {nome}, rode nela {faltam} (classes sem aprovado: "
                                      f"{sorted(reprovadas)})"])
    if escolhida is None:
        return saida("nenhuma_passou", ["nenhuma variação passou o portão com um candidato de cada classe"])

    medidos = por_variacao[escolhida]
    # PT: o teto olha os modelos da primeira etapa, aprovados ou não
    #     (decisão de 2026-10-15): os mesmos em todas as variações.
    # EN: the ceiling looks at the first-stage models only.
    if acima := sorted(m for m, r in medidos.items() if m in primeira_etapa and r["teto"] > teto):
        return saida("sanidade", [f"sanidade: o teto das mistas passou de {teto} na {escolhida} em {acima}"],
                     escolhida)
    if faltam := sorted(set(ativos) - completos(escolhida)):
        return saida("reselecao_pendente", [f"para a re-seleção, rode a {escolhida} em {faltam}"], escolhida)
    modelos = {}
    for classe in sorted(todas_as_classes):
        candidatos = [(m, r) for m, r in medidos.items() if ativos.get(m) == classe and r["aprovado"]]
        melhor = min(candidatos, key=lambda par: (-par[1]["_certas_em_a"], par[1]["G0"]["size_vram"] or 0))
        modelos[classe] = {"modelo": melhor[0], "certas_em_a": melhor[1]["_certas_em_a"]}
    return saida("escolhida", [], escolhida, modelos)


def publico(por_variacao: dict[str, dict[str, dict]], escolhida: str | None) -> dict:
    """PT: o que se publica; o acerto em A só da escolhida / EN: published view"""
    return {v: {m: {k: x for k, x in r.items() if not k.startswith("_") or v == escolhida}
                for m, r in medidos.items()} for v, medidos in por_variacao.items()}


# -----------------------------------------------------------------------------
# PT: Autoteste / EN: self-test
# -----------------------------------------------------------------------------

def _dobro(celula):
    """PT: o número dobrado; texto e data ficam / EN: doubles numbers only"""
    try:
        return str(2 * float(celula))
    except (TypeError, ValueError):
        return celula


def _registros_sinteticos(por_id: dict[str, dict], g: Gabarito, *, responde: bool, abstem_nos_negativos: bool,
                          acerta: bool = True) -> list[dict]:
    """PT: execuções inventadas de um modelo / EN: invented runs of one model"""
    registros = []
    for id_, p in por_id.items():
        tipo = p.get("tipo_de_acerto", "valor")
        consultas = [c for l in g.perguntas[id_].get("leituras", []) for c in l["consultas"]]
        tabela = g.respostas[consultas[0]] if consultas else None
        for cond in CONDICOES:
            for seed in range(1, SEEDS + 1):
                abstencao, valores = "", {"colunas": [], "linhas": []}
                if tipo == "abstencao":
                    if abstem_nos_negativos:
                        abstencao = "falta o dado"
                    else:
                        valores = {"colunas": ["n"], "linhas": [[1]]}
                elif responde and tabela:
                    linhas = tabela["linhas"] if acerta else [[_dobro(x) for x in l] for l in tabela["linhas"]]
                    valores = {"colunas": tabela["colunas"], "linhas": linhas}
                else:
                    abstencao = "não dá"
                registros.append({"candidato": "m", "id_pergunta": id_, "condicao": cond, "seed": seed, "erro": None,
                                  "resposta": {"interpretacao": "x", "sql": "", "valores": valores,
                                               "ressalva": "r" if tipo == "valor_com_ressalva" else "",
                                               "abstencao": abstencao}})
    return registros


def autoteste() -> list[str]:
    portao, (_, por_id), g = carregar_portao(), desenvolvimento.perguntas(), desenvolvimento.carregar_gabarito()
    ambiente = {"vram": {"size": 10, "size_vram": 10}}

    def medir(**kw):
        registros = _registros_sinteticos(por_id, g, **kw)
        return medir_modelo(registros, acerto.corrigir_todas(registros, {}, g, com_condicao=True), ambiente,
                            por_id, portao)

    falhas = []
    bom = medir(responde=True, abstem_nos_negativos=True)
    if not bom["aprovado"]:
        falhas.append(f"o modelo perfeito reprovou: {bom['aprovado_por_metrica']}")
    casos = [
        ("nunca se abstém", medir(responde=True, abstem_nos_negativos=False), "Z"),
        ("sempre se abstém", medir(responde=False, abstem_nos_negativos=True), "X"),
        ("responde sempre errado", medir(responde=True, abstem_nos_negativos=True, acerta=False), "Y1"),
    ]
    for descricao, r, metrica in casos:
        if r["aprovado_por_metrica"][metrica]:
            falhas.append(f"aprovou o estrago: {descricao} ({metrica})")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    fora_da_gpu = medir_modelo([], [], {"vram": {"size": 10, "size_vram": 8}}, por_id, portao)
    if fora_da_gpu["aprovado_por_metrica"]["G0"]:
        falhas.append("aprovou o estrago: modelo fora da GPU")
    else:
        print("  reprovado, como devia / rejected as expected: modelo fora da GPU")

    # PT: a regra de escolha com modelos inventados: a e b na primeira etapa,
    #     c outro candidato da classe de b, x fora da triagem.
    # EN: the choice rule with invented models.
    classes = {"a": "14b", "b": "8b", "c": "8b", "x": "14b"}
    regra = {**portao, "triagem": {**portao["triagem"], "modelos_da_primeira_etapa": ["a", "b"],
                                   "candidatos_fora": ["x"]}}
    aprovado = {"completo": True, "aprovado": True, "teto": 0.5, "_certas_em_a": 10, "G0": {"size_vram": 1}}
    reprovado = {**aprovado, "aprovado": False}
    incompleto = {**reprovado, "completo": False}
    v_menos_1 = {"a": reprovado, "b": reprovado}
    v0_ok = {"a": aprovado, "b": aprovado, "c": aprovado}
    resumos = [
        ("V-1 não medida", {"V0": v0_ok}, "pendente"),
        ("V-1 incompleta", {"V-1": {"a": reprovado, "b": incompleto}, "V0": v0_ok}, "pendente"),
        ("V-1 aprovada", {"V-1": {"a": aprovado, "b": reprovado}, "V0": v0_ok}, "sanidade"),
        ("teto passado", {"V-1": v_menos_1, "V0": {**v0_ok, "a": {**aprovado, "teto": 0.95}}}, "sanidade"),
        ("variação descartada sem a segunda etapa",
         {"V-1": v_menos_1, "V0": {"a": aprovado, "b": reprovado}, "V1": v0_ok}, "pendente"),
        ("re-seleção sobre um conjunto parcial", {"V-1": v_menos_1, "V0": {"a": aprovado, "b": aprovado}},
         "reselecao_pendente"),
        ("teto passado por modelo da primeira etapa reprovado",
         {"V-1": v_menos_1, "V0": {**v0_ok, "b": {**reprovado, "teto": 0.95}}}, "sanidade"),
    ]
    for descricao, por_variacao, esperada in resumos:
        r = resumir(por_variacao, regra, classes)
        if r["situacao"] != esperada or r["variacao_escolhida"] or r["modelos"]:
            falhas.append(f"aprovou o estrago: {descricao} deu {r['situacao']}, {r['variacao_escolhida']}, "
                          f"{r['modelos']} (esperado {esperada}, sem escolha)")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    # PT: casos que decidem: a V0 deixa a classe 8b sem modelo depois da
    #     segunda etapa, e a V1 vence com a re-seleção por acerto em A e VRAM.
    # EN: deciding cases: V0 discarded after stage two, V1 wins.
    r = resumir({"V-1": v_menos_1, "V0": {"a": aprovado, "b": reprovado, "c": reprovado},
                 "V1": {"a": aprovado, "b": {**aprovado, "_certas_em_a": 12, "G0": {"size_vram": 9}},
                        "c": {**aprovado, "_certas_em_a": 12, "G0": {"size_vram": 5}}}}, regra, classes)
    if (r["situacao"], r["variacao_escolhida"], r["modelos"].get("8b", {}).get("modelo")) != ("escolhida", "V1", "c"):
        falhas.append(f"a escolha deu {r}, esperado V1 com c na classe 8b (empate desfeito pela VRAM)")
    # PT: um candidato da re-seleção acima do teto não conta.
    # EN: a re-selection candidate above the ceiling does not count.
    r = resumir({"V-1": v_menos_1, "V0": {**v0_ok, "c": {**aprovado, "teto": 0.95}}}, regra, classes)
    if r["situacao"] != "escolhida":
        falhas.append(f"um candidato da re-seleção acima do teto deu {r['situacao']}, esperado escolhida")
    r = resumir({"V-1": v_menos_1, **{v: {"a": aprovado, "b": reprovado, "c": reprovado}
                                      for v in portao["triagem"]["ordem"][1:]}}, regra, classes)
    if r["situacao"] != "nenhuma_passou" or r["variacao_escolhida"]:
        falhas.append(f"seis variações reprovadas deram {r['situacao']}, esperado nenhuma_passou")
    # PT: a origem da pasta: variação trocada, conjunto trocado e enunciado
    #     antigo depois da revisão do conjunto.
    # EN: folder origin: wrong variant, wrong set, stale question text.
    id_ = next(iter(por_id))
    certo = {"variacao": "V0", "perguntas": "desenvolvimento", "enunciados": assinatura_dos_enunciados(por_id)}
    registro = {"candidato": "m", "id_pergunta": id_, "variacao": "V0", "pergunta": por_id[id_]["pergunta"]}
    if conferir_origem("V0", [registro], {"m": certo}, por_id):
        falhas.append("a origem certa foi recusada")
    origens = [
        ("variação gravada na pasta de outra", [{**registro, "variacao": "V1"}], {"m": {**certo, "variacao": "V1"}}),
        ("conjunto de teste na pasta do desenvolvimento", [registro], {"m": {**certo, "perguntas": "teste"}}),
        ("enunciado antigo depois da revisão", [{**registro, "pergunta": "texto antigo"}], {"m": certo}),
    ]
    for descricao, registros, ambientes in origens:
        if conferir_origem("V0", registros, ambientes, por_id):
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
        else:
            falhas.append(f"aprovou o estrago: {descricao}")
    with mock.patch.object(acerto, "acerto_da_execucao", lambda correcao, julgamento: "pendente"):
        pendente = medir(responde=True, abstem_nos_negativos=True)
    if pendente["Y1"] > 0:
        falhas.append("aprovou o estrago: pendente contado como certo")
    else:
        print("  reprovado, como devia / rejected as expected: pendente contado como certo")
    return falhas


# -----------------------------------------------------------------------------
# PT: Execução / EN: entry point
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variacao", help="mede uma variação")
    parser.add_argument("--pasta", type=Path, default=PASTA_DO_DESENVOLVIMENTO, help="pasta das variações")
    parser.add_argument("--resumo", action="store_true", help="escolha, sanidade e re-seleção")
    parser.add_argument("--gravar", action="store_true", help="grava evaluation/desenvolvimento/triagem.json")
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    args = parser.parse_args()

    if args.autoteste:
        falhas = autoteste()
        for falha in falhas:
            print(f"ERRO {falha}")
        sys.exit(1 if falhas else 0)

    # PT: o que decide a triagem tem de ser o congelado na errata 5.
    # EN: what decides screening must be what errata 5 froze.
    conferir_congelado()
    portao, (_, por_id), g = carregar_portao(), desenvolvimento.perguntas(), desenvolvimento.carregar_gabarito()
    nomes = [args.variacao] if args.variacao else [v for v in portao["triagem"]["ordem"]
                                                   if (args.pasta / v / "execucoes").exists()]
    por_variacao = {v: medir_variacao(args.pasta / v, por_id, g, portao) for v in nomes}
    for v, medidos in por_variacao.items():
        for modelo, r in medidos.items():
            estado = "aprovado" if r["aprovado"] else "reprovado"
            print(f"  {v} {modelo}: {estado}; G0 {r['G0']['maior_parcela_por_condicao']:.1%} "
                  f"(na GPU: {r['G0']['na_gpu']}), X {r['X']:.1%}, Y1 {r['Y1']:.1%}, Y2 {r['Y2']:.1%}, "
                  f"Z {r['Z']:.1%}, {r['execucoes']} de {r['esperadas']} execuções")
    if not args.resumo:
        return
    classes = {c["nome"]: c["classe"] for c in carregar_selecao()["candidatos"]}
    resumo = resumir(por_variacao, portao, classes)
    print(f"\n  situação: {resumo['situacao']} ({SITUACOES[resumo['situacao']]})")
    print(f"  variação escolhida: {resumo['variacao_escolhida']}; modelos: {resumo['modelos']}")
    for problema in resumo["problemas"]:
        print(f"  ATENÇÃO {problema}")
    if args.gravar and resumo["situacao"] in ("pendente", "reselecao_pendente"):
        raise SystemExit("ERRO a triagem ainda não terminou; nada gravado")
    if args.gravar:
        TRIAGEM.write_text(json.dumps({"portao": "evaluation/portao.yml", **resumo,
                                       "medidas": publico(por_variacao, resumo["variacao_escolhida"])},
                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"  gravado {TRIAGEM.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
