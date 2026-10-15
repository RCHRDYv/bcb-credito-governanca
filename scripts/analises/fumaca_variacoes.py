"""
PT: Fumaça ao vivo das variações do instrumento (#118, ADR 0032), com o
    Ollama local e só as perguntas inventadas da fumaça do assistente.
    Confere duas coisas que o cliente falso não alcança:

    1. **A ordem das chaves.** Na variação pedida, cada resposta do modelo
       tem de trazer as chaves com prefixo na ordem pedida
       (a_interpretacao, b_sql...). Na V−1, a ordem é a alfabética, e o
       relatório mostra isso.
    2. **A reprodução da seed.** Como no executor, o modelo recarrega antes
       de cada execução (decisão de 2026-10-15). A mesma pergunta, na mesma
       condição e com a mesma seed, roda três vezes, com outra condição e
       outra pergunta no meio. As três execuções inteiras têm de sair
       iguais.

    Grava o relatório em data/desenvolvimento/, fora do git.

EN: Live smoke test of the instrument variants on the local Ollama, with the
    invented smoke questions only: checks the generated key order and
    whether the same seed reproduces whole runs, reloading the model before
    each run as the runner does.

Uso / Usage:
    uv run --group rag python -m scripts.analises.fumaca_variacoes --variacao V0 --candidato gemma-4-12b
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys

from assistente import parametros, variacoes
from assistente.cliente import ClienteOllama
from assistente.parametros import CONDICOES
from assistente.responder import responder
from assistente.sql import abrir_banco
from scripts.analises.fumaca_assistente import PERGUNTAS_DE_FUMACA
from scripts.executar_experimento import (
    PASTA_DO_DESENVOLVIMENTO,
    candidatos_da_selecao,
    conferir_versao_do_ollama,
    descarregar_e_esperar,
    modelos_do_experimento,
    parametros_da_execucao,
)
from scripts.selecionar_modelos import carregar_selecao, conferir_candidato, conferir_variaveis


def chaves(texto: str) -> list[str]:
    """PT: as chaves de primeiro nível, na ordem em que vieram / EN: top keys in order"""
    try:
        return [k for k, _ in json.loads(texto, object_pairs_hook=lambda p: p)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return re.findall(r'"(\w+)"\s*:', texto)[:6]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variacao", choices=variacoes.ORDEM, default="V0")
    parser.add_argument("--candidato", default="gemma-4-12b")
    args = parser.parse_args()

    from assistente.contexto import buscar_trechos

    v = variacoes.VARIACOES[args.variacao]
    todos = {m["nome"]: m for m in candidatos_da_selecao()}
    m = todos[args.candidato]
    p = parametros_da_execucao(m, args.variacao, {x["nome"] for x in modelos_do_experimento()})
    p = parametros.Parametros(**{**p.__dict__, "seeds": (1,)})
    # PT: o mesmo ambiente da triagem: variáveis do ollama serve, versão e
    #     digest do modelo. Sem isso, a reprodução não vale como evidência.
    # EN: same environment as screening, or reproduction proves nothing.
    variaveis = conferir_variaveis(carregar_selecao())
    versao = conferir_versao_do_ollama(p.endereco)
    digest = conferir_candidato(p.endereco, m)
    cliente, banco, modelo = ClienteOllama(p), abrir_banco(), parametros.modelo_de_prompt()
    esperadas = {"primeira": variacoes.prefixadas(variacoes.campos_da_primeira(v)),
                 "segunda": variacoes.prefixadas(variacoes.campos_da_segunda(v))}

    def rodar(pergunta: str, condicao: str, trechos):
        descarregar_e_esperar(p.endereco)
        return responder(pergunta, condicao, 1, cliente=cliente, banco=banco, p=p, modelo=modelo,
                         trechos=trechos if "trechos" in CONDICOES[condicao] else None, variacao=args.variacao)

    execucoes, fora_de_ordem = [], 0
    for pergunta in PERGUNTAS_DE_FUMACA:
        trechos = buscar_trechos(pergunta)
        for condicao in CONDICOES:
            r = rodar(pergunta, condicao, trechos)
            ordens = [chaves(c["resposta"]) for c in r["chamadas"]]
            if v.chaves_prefixadas:
                # PT: a primeira chamada (e a nova tentativa) com as chaves da
                #     primeira; a segunda, quando houve resultado, com as dela.
                # EN: first call and retry use the first keys; the second its own.
                segunda = 1 if r.get("resultado") is not None and len(ordens) > 1 else 0
                certas = [o == esperadas["primeira"] for o in ordens[:len(ordens) - segunda]]
                certas += [o == esperadas["segunda"] for o in ordens[len(ordens) - segunda:]]
                fora_de_ordem += certas.count(False)
            situacao = f"erro {r['erro']['tipo']}" if r["erro"] else \
                ("abstenção" if r["resposta"]["abstencao"] else "respondeu")
            print(f"  {condicao} | {situacao} | chaves {ordens} | {r['segundos']} s | {pergunta}", flush=True)
            execucoes.append({"pergunta": pergunta, "condicao": condicao, "situacao": situacao, "chaves": ordens,
                              "novas_tentativas": r.get("novas_tentativas"), "segundos": r["segundos"]})

    # PT: reprodução: a mesma execução três vezes, com outra condição e outra
    #     pergunta no meio; o modelo recarrega antes de cada uma.
    # EN: reproduction: the same run three times with others in between.
    pergunta, outra = PERGUNTAS_DE_FUMACA[0], PERGUNTAS_DE_FUMACA[1]
    trechos, trechos_da_outra = buscar_trechos(pergunta), buscar_trechos(outra)
    primeira = rodar(pergunta, "D", trechos)
    rodar(pergunta, "A", trechos)
    segunda = rodar(pergunta, "D", trechos)
    rodar(outra, "B", trechos_da_outra)
    terceira = rodar(pergunta, "D", trechos)
    respostas = [[c["resposta"] for c in r["chamadas"]] for r in (primeira, segunda, terceira)]
    reproduz = respostas[0] == respostas[1] == respostas[2]
    print(f"\n  chaves fora da ordem: {fora_de_ordem}; a mesma seed reproduz a execução inteira: {reproduz}")

    relatorio = {
        "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "variacao": args.variacao, "candidato": args.candidato, "modelo": p.modelo, "num_ctx": p.num_ctx,
        "ollama": versao, "digest_do_gguf": digest, "variaveis": variaveis, "recarrega_a_cada_execucao": True,
        "chaves_esperadas": esperadas, "chaves_fora_da_ordem": fora_de_ordem, "a_mesma_seed_reproduz": reproduz,
        "respostas_da_reproducao": respostas, "execucoes": execucoes,
    }
    saida = PASTA_DO_DESENVOLVIMENTO / f"fumaca-{args.variacao}-{args.candidato}-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  relatório / report: {saida}")
    if fora_de_ordem or not reproduz:
        sys.exit(1)


if __name__ == "__main__":
    main()
