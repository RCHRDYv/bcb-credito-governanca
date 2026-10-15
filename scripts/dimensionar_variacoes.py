"""
PT: Dimensiona o num_ctx de cada variação do instrumento (#118, ADR 0032)
    para cada candidato do evaluation/selecao.yml, sem rodar modelo, pela
    mesma regra do scripts/dimensionar_contexto.py: o menor múltiplo de 4.096
    que comporta a segunda chamada de D no pior caso, contada pelo
    tokenizer.json da revisão fixada, e que também comporta a estimativa em
    caracteres que o cliente confere antes do envio.

    As mensagens são as da variação, montadas por
    assistente.responder.mensagens_da_primeira e
    assistente.variacoes.mensagem_da_segunda: o critério e os exemplos da V1,
    o campo de plano da V2 (que cabe no limite de tokens da resposta) e as
    junções da V4. A nova tentativa da V3 substitui a anterior; a chamada
    dela (o prompt, a resposta anterior no limite, o pedido com o erro no
    corte e a nova resposta) também é contada, e o pior caso é a maior das
    duas chamadas. Os prompts de D cobrem as 41
    perguntas do teste e as 30 do desenvolvimento, com os trechos da busca do
    RAG. A razão de caracteres por token é a menor medida, com a margem do
    selecao.yml.

    Grava evaluation/desenvolvimento/dimensionamento.json, que o executor lê
    fora da V−1. Roda na minha máquina, com o grupo rag.

EN: Sizes num_ctx per instrument variant and selection candidate, with the
    same rule as dimensionar_contexto, using each variant's messages over
    the 41 test and 30 development questions. Writes
    evaluation/desenvolvimento/dimensionamento.json.

Uso / Usage:
    uv run --group rag python -m scripts.dimensionar_variacoes
"""

from __future__ import annotations

import json
import math
from decimal import ROUND_FLOOR, Decimal

from huggingface_hub import hf_hub_download

from assistente import parametros, variacoes
from assistente.responder import mensagens_da_primeira
from experimento import desenvolvimento
from scripts.dimensionar_contexto import contar
from scripts.selecionar_modelos import carregar_selecao
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import RAIZ, ler_respostas

SAIDA = RAIZ / "evaluation" / "desenvolvimento" / "dimensionamento.json"


def resultado_no_limite(tokenizador, limite: int) -> dict:
    """
    PT: O pior resultado: a linha com mais tokens entre as respostas do
        gabarito do teste e do desenvolvimento, repetida até o limite.
    EN: Worst-case result over test and development answer keys.
    """
    def custo(colunas, linha):
        return len(tokenizador.encode(json.dumps({"colunas": colunas, "linhas": [linha]}, ensure_ascii=False)).ids)

    respostas = [*ler_respostas().values(), *desenvolvimento.ler_respostas().values()]
    colunas, linha = max(((r["colunas"], l) for r in respostas for l in r["linhas"]), key=lambda par: custo(*par))
    return {"colunas": colunas, "linhas": [linha] * limite, "cortado": True, "total_de_linhas": 10 ** 6}


def main() -> None:
    from tokenizers import Tokenizer

    from assistente.contexto import buscar_trechos

    selecao = carregar_selecao()
    dim, geracao = selecao["dimensionamento"], selecao["geracao"]
    limite_da_resposta = int(geracao["limite_de_tokens_da_resposta"])
    por_mensagem = int(dim["tokens_por_mensagem"])
    modelo = parametros.modelo_de_prompt()
    perguntas_ = {**perguntas(VIGENTE)[1], **desenvolvimento.perguntas()[1]}
    print(f"Trechos da busca para {len(perguntas_)} perguntas")
    trechos = {id_: buscar_trechos(p["pergunta"]) for id_, p in perguntas_.items()}

    medidas: dict[str, dict] = {}
    for c in selecao["candidatos"]:
        tokenizador = Tokenizer.from_file(hf_hub_download(c["tokenizador"], "tokenizer.json",
                                                          revision=c["revisao_do_modelo_base"]))
        resultado = resultado_no_limite(tokenizador, int(selecao["sql"]["limite_de_linhas"]))
        tabela = json.dumps({"colunas": resultado["colunas"], "linhas": resultado["linhas"]}, ensure_ascii=False)
        aviso = f" (resultado cortado em {len(resultado['linhas'])} de {resultado['total_de_linhas']} linhas)"
        for nome in variacoes.ORDEM[1:]:
            v = variacoes.VARIACOES[nome]
            prompts = {id_: mensagens_da_primeira(v, "D", p["pergunta"], modelo, trechos[id_])
                       for id_, p in perguntas_.items()}
            tokens = {id_: contar(tokenizador, m, por_mensagem) for id_, m in prompts.items()}
            caracteres = {id_: sum(len(x["content"]) for x in m) for id_, m in prompts.items()}
            maior = max(tokens, key=tokens.get)
            segunda = {"role": "user", "content": variacoes.mensagem_da_segunda(v, tabela, aviso)}
            tokens_do_resultado = contar(tokenizador, [segunda], por_mensagem)
            segunda_chamada = tokens[maior] + limite_da_resposta + por_mensagem + tokens_do_resultado + limite_da_resposta
            # PT: a chamada da nova tentativa, com o erro no tamanho do corte.
            # EN: the retry call, with an error as long as the cut.
            pedido = {"role": "user", "content": variacoes.mensagem_da_nova_tentativa("x" * variacoes.CORTE_DO_ERRO)}
            tentativa = (tokens[maior] + limite_da_resposta + por_mensagem + contar(tokenizador, [pedido], por_mensagem)
                         + limite_da_resposta) if v.nova_tentativa else 0
            pior_caso = max(segunda_chamada, tentativa)
            razao = min(caracteres[i] / tokens[i] for i in tokens) * float(dim["margem_da_razao"])
            razao = float(Decimal(str(razao)).quantize(Decimal("0.1"), rounding=ROUND_FLOOR))
            # PT: o cliente confere o contexto antes do envio por uma
            #     estimativa em caracteres (assistente.cliente.estimar_tokens).
            #     O num_ctx também cobre essa estimativa na pior segunda
            #     chamada, para ela não acusar um erro de contexto que não
            #     existe (achado da revisão de 2026-10-15).
            # EN: num_ctx also covers the client's character-based estimate
            #     of the worst second call, so it raises no false context error.
            estimada = max(math.ceil((caracteres[i] + len(segunda["content"])) / razao) for i in caracteres)                 + 2 * limite_da_resposta
            num_ctx = math.ceil(max(pior_caso, estimada) / int(dim["multiplo"])) * int(dim["multiplo"])
            medidas.setdefault(nome, {})[c["nome"]] = {
                "num_ctx": num_ctx, "caracteres_por_token": razao, "pior_caso": pior_caso,
                "chamada_da_nova_tentativa": tentativa, "segunda_chamada_estimada_pelo_cliente": estimada,
                "maior_prompt_de_d": {"pergunta": maior, "tokens": tokens[maior]},
                "tokens_da_mensagem_do_resultado": tokens_do_resultado,
            }
            print(f"  {c['nome']} {nome}: maior prompt de D {tokens[maior]} ({maior}), pior caso {pior_caso}, "
                  f"estimativa do cliente {estimada}, "
                  f"num_ctx {num_ctx}, razão {razao}")

    # PT: a regra desta medida, que não é só a da seleção (dimensionar_contexto).
    # EN: this measure's rule, which extends the selection's.
    dim = {**dim, "componentes": [
        "o maior prompt da primeira chamada de D entre as 41 perguntas do teste e as 30 do desenvolvimento, com os "
        "trechos da busca, nas mensagens da variação",
        "o limite de tokens da resposta, pela resposta da primeira chamada (o SQL)",
        "a mensagem com o resultado no limite de linhas, pela resposta dos dois gabaritos com mais tokens por linha",
        "o limite de tokens da resposta, pela segunda chamada",
        "16 tokens por mensagem, pelo modelo de chat",
        "na V3 e na V4, a chamada da nova tentativa, com o erro no tamanho do corte; vale a maior das duas chamadas",
        "a estimativa em caracteres que o cliente confere antes do envio, na pior segunda chamada",
    ]}
    SAIDA.write_text(json.dumps({"dimensionamento": dim, "variacoes": medidas}, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"\nMedidas em {SAIDA.relative_to(RAIZ).as_posix()}.")


if __name__ == "__main__":
    main()
