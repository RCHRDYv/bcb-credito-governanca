"""
PT: Valida o gabarito de recuperação do RAG (evaluation/recuperacao.yml,
    issue #46, ADR 0028), sem rede e sem as dependências do RAG. Roda no
    workflow próprio .github/workflows/recuperacao.yml.

    O que é conferido:

    1. **O arquivo é o gerado.** Regerar com
       scripts/gerar_gabarito_de_recuperacao.py dá o mesmo texto, sem BOM e
       com final de linha LF. Uma mudança na ontologia que mexa numa fonte
       obriga a regerar, e a edição à mão reprova.
    2. **Todo conceito da ontologia está lá uma vez**, como alvo ou como
       excluído, e nenhum id é estranho à ontologia.
    3. **Alvo em forma.** A consulta é "O que é <rótulo>?", o documento é do
       corpus (ingestion/fontes.py), alvo de página traz páginas, alvo de
       seção traz seções, e o excluído traz motivo.
    4. **Contagens.** O denominador e o número de excluídos do metadata
       batem com as listas.
    5. **Manifesto e avaliação coerentes.** O rag/manifesto.json lista
       exatamente o corpus, com o sha256 da seção documentos do
       ingestion/manifesto.json; os candidatos são os de rag/parametros.py,
       nas revisões fixadas; e o escolhido é o mesmo no manifesto e no
       rag/avaliacao.json, que mediu o gabarito versionado.

    Com --autoteste, estraga cópias em memória, uma por vez, e confere que a
    validação reprova cada uma pelo motivo certo, e que uma cópia com CRLF e
    BOM passa. Faz o mesmo com o manifesto e a avaliação.

EN: Validates the RAG retrieval answer key with no network and no RAG
    dependencies: the file equals the generated one, every ontology concept
    appears once, targets are well formed and counts match. --autoteste
    runs the negative control.

Uso / Usage:
    uv run python -m scripts.validar_recuperacao
    uv run python -m scripts.validar_recuperacao --autoteste
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import yaml

from ingestion import manifesto
from ingestion.fontes import DOCUMENTOS_DO_CORPUS
from rag.parametros import AVALIACAO, CANDIDATOS, MANIFESTO_RAG
from scripts.gerar_gabarito_de_recuperacao import SAIDA, como_texto, conceitos_da_ontologia, gerar
from scripts.validar_registro import normalizado

CONSULTA = re.compile(r"^O que é \S.*\?$")
GRANULARIDADES = {"pagina": "paginas", "secao": "secoes", "documento": None}


def validar(texto: str, esperado: str, conceitos: set[str], documentos: set[str]) -> list[str]:
    """PT: lista de problemas; vazia quando está tudo certo / EN: list of problems"""
    problemas = []
    if normalizado(texto) != esperado:
        problemas.append("recuperacao.yml difere do gerado: rode scripts.gerar_gabarito_de_recuperacao")
    try:
        conteudo = yaml.safe_load(normalizado(texto))
    except yaml.YAMLError as erro:
        return [*problemas, f"YAML inválido: {erro}"]

    alvos, excluidos = conteudo.get("alvos") or [], conteudo.get("excluidos") or []
    vistos: dict[str, int] = {}
    for registro in [*alvos, *excluidos]:
        vistos[registro.get("conceito")] = vistos.get(registro.get("conceito"), 0) + 1
    problemas += [f"{c}: aparece {n} vezes" for c, n in sorted(vistos.items(), key=str) if n > 1]
    problemas += [f"{c}: conceito da ontologia ausente" for c in sorted(conceitos - set(vistos))]
    problemas += [f"{c}: não é conceito da ontologia" for c in sorted(set(vistos) - conceitos, key=str)]

    for registro in alvos:
        conceito = registro.get("conceito")
        if not CONSULTA.match(str(registro.get("consulta") or "")):
            problemas.append(f"{conceito}: consulta fora do formato 'O que é <rótulo>?'")
        if not registro.get("alvos"):
            problemas.append(f"{conceito}: alvo vazio")
        for alvo in registro.get("alvos") or []:
            if alvo.get("documento") not in documentos:
                problemas.append(f"{conceito}: documento {alvo.get('documento')} fora do corpus")
            granularidade = alvo.get("granularidade")
            if granularidade not in GRANULARIDADES:
                problemas.append(f"{conceito}: granularidade {granularidade} desconhecida")
            elif GRANULARIDADES[granularidade] and not alvo.get(GRANULARIDADES[granularidade]):
                problemas.append(f"{conceito}: alvo de {granularidade} sem {GRANULARIDADES[granularidade]}")
    for registro in excluidos:
        if not str(registro.get("motivo") or "").strip():
            problemas.append(f"{registro.get('conceito')}: excluído sem motivo")

    metadata = conteudo.get("metadata") or {}
    if metadata.get("denominador") != len(alvos):
        problemas.append(f"denominador {metadata.get('denominador')} não bate com {len(alvos)} alvos")
    if metadata.get("excluidos") != len(excluidos):
        problemas.append(f"excluidos {metadata.get('excluidos')} não bate com {len(excluidos)} excluídos")
    return problemas


def validar_manifesto(manifesto_rag: dict, avaliacao: dict, ingestao: dict, metadata: dict) -> list[str]:
    """
    PT: Coerência do rag/manifesto.json e do rag/avaliacao.json entre si,
        com a ingestão e com os parâmetros.
    EN: Consistency of the RAG manifest and evaluation.
    """
    problemas = []
    registrados = ingestao.get("documentos", {})
    corpus = {d.id: d.arquivo for d in DOCUMENTOS_DO_CORPUS}
    if set(manifesto_rag.get("documentos", {})) != set(corpus):
        problemas.append("rag/manifesto.json não lista exatamente o corpus")
    for id_, arquivo in corpus.items():
        sha = manifesto_rag.get("documentos", {}).get(id_, {}).get("sha256")
        if sha != registrados.get(arquivo, {}).get("sha256"):
            problemas.append(f"{id_}: sha256 do rag/manifesto.json difere do ingestion/manifesto.json")
    fixadas = {c.nome: (c.repositorio, c.revisao) for c in CANDIDATOS}
    candidatos = manifesto_rag.get("candidatos", {})
    if set(candidatos) != set(fixadas):
        problemas.append("candidatos do rag/manifesto.json diferem dos de rag/parametros.py")
    for nome, info in candidatos.items():
        if (info.get("repositorio"), info.get("revisao")) != fixadas.get(nome):
            problemas.append(f"{nome}: repositório ou revisão difere da fixada")
    escolhido = manifesto_rag.get("escolhido")
    if not escolhido:
        problemas.append("rag/manifesto.json sem modelo escolhido")
    elif escolhido != avaliacao.get("escolhido"):
        problemas.append("escolhido do rag/manifesto.json difere do rag/avaliacao.json")
    else:
        indice = candidatos.get(escolhido.get("nome"), {})
        if (escolhido.get("sha256_trechos"), escolhido.get("sha256_embeddings")) != \
                (indice.get("sha256_trechos"), indice.get("sha256_embeddings")):
            problemas.append("o escolhido foi avaliado sobre outro índice: rode rag.avaliar")
    medido = {k: v for k, v in (avaliacao.get("gabarito") or {}).items() if k != "arquivo"}
    if medido != metadata:
        problemas.append("rag/avaliacao.json mediu outro gabarito de recuperação: rode rag.avaliar")
    return problemas


def autoteste(texto: str, esperado: str, conceitos: set[str], documentos: set[str]) -> list[str]:
    """
    PT: Cada caso estraga uma coisa e diz o trecho que a reprovação precisa
        trazer. O caso falha se a validação aprovar a cópia estragada, ou se
        reprovar por outro motivo.
    EN: Each case breaks one thing and names the fragment the rejection must
        carry.
    """
    if validar(texto, esperado, conceitos, documentos):
        return ["o arquivo versionado já falha na validação; o autoteste parte dele"]

    def editar(funcao):
        def estragar(t):
            conteudo = yaml.safe_load(t)
            funcao(conteudo)
            return como_texto(conteudo)
        return estragar

    primeiro = yaml.safe_load(texto)["alvos"][0]["conceito"]
    negativos = [
        ("edição à mão", lambda t: t.replace("O que é", "O que significa", 1), "difere do gerado"),
        ("conceito ausente", editar(lambda c: c["alvos"].pop(0)), f"{primeiro}: conceito da ontologia ausente"),
        ("conceito repetido", editar(lambda c: c["alvos"].append(dict(c["alvos"][0]))), f"{primeiro}: aparece 2 vezes"),
        ("conceito estranho", editar(lambda c: c["excluidos"].append({"conceito": "metricas.inventado", "motivo": "x"})),
         "metricas.inventado: não é conceito da ontologia"),
        ("documento fora do corpus", editar(lambda c: c["alvos"][0]["alvos"][0].update(documento="tutorial")),
         "documento tutorial fora do corpus"),
        ("página sem páginas", editar(lambda c: c["alvos"][0]["alvos"][0].update(granularidade="pagina", paginas=[])),
         "alvo de pagina sem paginas"),
        ("consulta reescrita", editar(lambda c: c["alvos"][0].update(consulta="Defina data-base")), "consulta fora do formato"),
        ("excluído sem motivo", editar(lambda c: c["excluidos"][0].update(motivo="")), "excluído sem motivo"),
        ("denominador errado", editar(lambda c: c["metadata"].update(denominador=1)), "denominador 1 não bate"),
    ]
    falhas = []
    for descricao, estragar, trecho in negativos:
        problemas = validar(estragar(texto), esperado, conceitos, documentos)
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")

    crlf_e_bom = "﻿" + texto.replace("\n", "\r\n")
    if problemas := validar(crlf_e_bom, esperado, conceitos, documentos):
        falhas.append(f"reprovou o caso que devia passar, CRLF e BOM: {problemas}")
    else:
        print("  aprovado, como devia / accepted as expected: CRLF e BOM")
    return falhas


def autoteste_do_manifesto(manifesto_rag: dict, avaliacao: dict, ingestao: dict, metadata: dict) -> list[str]:
    """
    PT: Controle negativo da conferência 5: estraga cópias do manifesto, da
        avaliação e da ingestão, uma por vez.
    EN: Negative control for check 5.
    """
    if validar_manifesto(manifesto_rag, avaliacao, ingestao, metadata):
        return ["o manifesto versionado já falha na validação; o autoteste parte dele"]
    nome = manifesto_rag["escolhido"]["nome"]
    primeiro = next(iter(ingestao["documentos"]))

    def outro_escolhido(m, a, i):
        a["escolhido"] = {**a["escolhido"], "acerto_em_5": 0}

    def revisao_trocada(m, a, i):
        m["candidatos"][nome]["revisao"] = "0" * 40

    def documento_republicado(m, a, i):
        i["documentos"][primeiro]["sha256"] = "f" * 64

    negativos = [
        ("escolhido diverge da avaliação", outro_escolhido, "escolhido do rag/manifesto.json difere"),
        ("revisão trocada", revisao_trocada, f"{nome}: repositório ou revisão difere"),
        ("documento republicado", documento_republicado, "difere do ingestion/manifesto.json"),
    ]
    falhas = []
    for descricao, estragar, trecho in negativos:
        copias = [json.loads(json.dumps(x)) for x in (manifesto_rag, avaliacao, ingestao)]
        estragar(*copias)
        problemas = validar_manifesto(*copias, metadata)
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in p for p in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")
    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    args = parser.parse_args()

    texto = SAIDA.read_text(encoding="utf-8")
    esperado = como_texto(gerar())
    conceitos = {referencia for referencia, _ in conceitos_da_ontologia()}
    documentos = {d.id for d in DOCUMENTOS_DO_CORPUS}

    metadata = yaml.safe_load(normalizado(texto))["metadata"]
    manifesto_rag = json.loads(MANIFESTO_RAG.read_text(encoding="utf-8"))
    avaliacao = json.loads(AVALIACAO.read_text(encoding="utf-8"))
    if args.autoteste:
        falhas = autoteste(normalizado(texto), esperado, conceitos, documentos)
        falhas += autoteste_do_manifesto(manifesto_rag, avaliacao, manifesto.carregar(), metadata)
    else:
        falhas = validar(texto, esperado, conceitos, documentos)
        print(f"  recuperacao.yml: {metadata['denominador']} alvos e {metadata['excluidos']} excluídos, "
              f"de {len(conceitos)} conceitos")
        falhas += validar_manifesto(manifesto_rag, avaliacao, manifesto.carregar(), metadata)
        escolhido = manifesto_rag.get("escolhido") or {}
        print(f"  rag/manifesto.json: {len(manifesto_rag.get('documentos', {}))} documentos, "
              f"{len(manifesto_rag.get('candidatos', {}))} candidatos, escolhido {escolhido.get('nome')}")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
