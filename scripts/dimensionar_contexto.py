"""
PT: Preenche os campos medidos de cada candidato do evaluation/selecao.yml
    (#48, ADR 0030), sem rodar modelo nenhum:

    1. a revisão do Hugging Face e o sha256 do GGUF, pela API do Hub;
    2. a revisão do repositório do tokenizador, e o contexto publicado no
       config.json dela, que precisa passar da regra de entrada;
    3. o num_ctx: o menor múltiplo de 4.096 que comporta a segunda chamada
       de D no pior caso, contada pelo tokenizer.json da revisão fixada. Os
       componentes estão no bloco dimensionamento do selecao.yml;
    4. a razão de caracteres por token da estimativa feita antes do envio:
       a menor medida nos prompts de D, com a margem do selecao.yml.

    Os prompts de D usam os trechos da busca do RAG para as 41 perguntas,
    como o experimento vai usar. Buscar não é rodar o modelo: nenhuma
    resposta é gerada. As medidas vão para evaluation/selecao/
    dimensionamento.json.

    Roda na minha máquina, com o grupo rag (tokenizers e o índice do RAG).
    Depois, o selecao.yml e o modelo de prompt entram por errata no
    evaluation/registro.yml, antes da seleção.

EN: Fills each candidate's measured fields in selecao.yml without running
    any model: HF revision and GGUF sha256, tokenizer revision and its
    published context (checked against the entry rule), num_ctx as the
    smallest multiple of 4,096 fitting D's second call in the worst case,
    counted with the pinned tokenizer.json, and the characters-per-token
    ratio. D prompts use the RAG excerpts for the 41 questions; searching
    generates no answer. Runs locally with the rag group.

Uso / Usage:
    uv run --group rag python -m scripts.dimensionar_contexto
"""

from __future__ import annotations

import json
import math
import re
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from assistente import contexto, parametros
from scripts.selecionar_modelos import SELECAO, carregar_selecao
from scripts.validar_perguntas import VIGENTE, perguntas
from scripts.validar_registro import RAIZ, ler_respostas

SAIDA = RAIZ / "evaluation" / "selecao" / "dimensionamento.json"


def contexto_publicado(config: dict) -> int:
    """PT: o max_position_embeddings, no topo ou no text_config / EN: published context"""
    return int(config.get("max_position_embeddings") or config["text_config"]["max_position_embeddings"])


def contar(tokenizador, mensagens: list[dict], por_mensagem: int) -> int:
    return sum(len(tokenizador.encode(m["content"], add_special_tokens=False).ids) + por_mensagem for m in mensagens)


def resultado_no_limite(tokenizador, limite: int) -> dict:
    """
    PT: O resultado do pior caso: a linha com mais tokens entre as respostas
        do gabarito, repetida até o limite de linhas, com o aviso de corte.
    EN: Worst-case result: the key's densest row repeated up to the limit.
    """
    def custo(colunas, linha):
        return len(tokenizador.encode(json.dumps({"colunas": colunas, "linhas": [linha]}, ensure_ascii=False)).ids)

    colunas, linha = max(((r["colunas"], l) for r in ler_respostas().values() for l in r["linhas"]),
                         key=lambda par: custo(*par))
    return {"colunas": colunas, "linhas": [linha] * limite, "cortado": True, "total_de_linhas": 10 ** 6}


def preencher(texto: str, nome: str, campos: dict) -> str:
    """
    PT: Troca os campos do bloco de um candidato no texto do selecao.yml,
        preservando os comentários.
    EN: Replaces a candidate block's fields in the YAML text, keeping
        comments.
    """
    inicio = texto.index(f"  - nome: {nome}\n")
    fim = texto.find("\n  - nome:", inicio + 1)
    fim = texto.find("\n# ---", inicio) if fim == -1 else fim
    bloco = texto[inicio:fim]
    for campo, valor in campos.items():
        literal = f'"{valor}"' if isinstance(valor, str) else str(valor)
        bloco, trocas = re.subn(rf"(?m)^    {campo}: .*$", f"    {campo}: {literal}", bloco)
        if trocas != 1:
            raise SystemExit(f"ERRO campo {campo} de {nome} não achado no {SELECAO}")
    return texto[:inicio] + bloco + texto[fim:]


def main() -> None:
    from tokenizers import Tokenizer

    selecao = carregar_selecao()
    regras, dim, geracao = selecao["regras"], selecao["dimensionamento"], selecao["geracao"]
    limite_da_resposta = int(geracao["limite_de_tokens_da_resposta"])
    por_mensagem = int(dim["tokens_por_mensagem"])
    modelo = parametros.modelo_de_prompt()
    _, por_id = perguntas(VIGENTE)

    print("Prompts de D, com os trechos da busca, para as 41 perguntas")
    prompts = {id_: contexto.primeira_chamada("D", p["pergunta"], modelo, contexto.buscar_trechos(p["pergunta"]))
               for id_, p in por_id.items()}

    api = HfApi()
    texto = (RAIZ / SELECAO).read_text(encoding="utf-8")
    medidas = {}
    for c in selecao["candidatos"]:
        info = api.model_info(c["repositorio"], files_metadata=True)
        arquivo = next((s for s in info.siblings if s.rfilename == c["arquivo"]), None)
        if arquivo is None or arquivo.lfs is None:
            raise SystemExit(f"ERRO {c['repositorio']} não tem {c['arquivo']} no LFS")
        revisao_do_modelo_base = api.model_info(c["tokenizador"]).sha
        config = json.loads(Path(hf_hub_download(c["tokenizador"], "config.json",
                                                 revision=revisao_do_modelo_base)).read_text(encoding="utf-8"))
        publicado = contexto_publicado(config)
        if publicado < int(regras["contexto_minimo"]) or publicado != int(c["contexto_publicado"]):
            raise SystemExit(f"ERRO {c['nome']}: contexto publicado {publicado}, no selecao.yml "
                             f"{c['contexto_publicado']}, mínimo {regras['contexto_minimo']}")
        tokenizador = Tokenizer.from_file(hf_hub_download(c["tokenizador"], "tokenizer.json",
                                                          revision=revisao_do_modelo_base))

        tokens = {id_: contar(tokenizador, m, por_mensagem) for id_, m in prompts.items()}
        caracteres = {id_: sum(len(x["content"]) for x in m) for id_, m in prompts.items()}
        maior = max(tokens, key=tokens.get)
        segunda = contexto.segunda_chamada([], "", resultado_no_limite(tokenizador, int(selecao["sql"]["limite_de_linhas"])),
                                           modelo)[-1]
        tokens_do_resultado = contar(tokenizador, [segunda], por_mensagem)
        pior_caso = tokens[maior] + limite_da_resposta + por_mensagem + tokens_do_resultado + limite_da_resposta
        num_ctx = math.ceil(pior_caso / int(dim["multiplo"])) * int(dim["multiplo"])
        razao = min(caracteres[i] / tokens[i] for i in tokens) * float(dim["margem_da_razao"])
        razao = float(Decimal(str(razao)).quantize(Decimal("0.1"), rounding=ROUND_FLOOR))

        texto = preencher(texto, c["nome"], {
            "revisao": info.sha, "sha256": arquivo.lfs.sha256, "revisao_do_modelo_base": revisao_do_modelo_base,
            "num_ctx": num_ctx, "caracteres_por_token": razao,
        })
        medidas[c["nome"]] = {
            "contexto_publicado": publicado, "tamanho_do_gguf": arquivo.size,
            "maior_prompt_de_d": {"pergunta": maior, "tokens": tokens[maior], "caracteres": caracteres[maior]},
            "tokens_da_mensagem_do_resultado": tokens_do_resultado, "pior_caso": pior_caso, "num_ctx": num_ctx,
            "razao_medida_minima": round(min(caracteres[i] / tokens[i] for i in tokens), 4),
            "caracteres_por_token": razao, "tokens_de_d_por_pergunta": tokens,
        }
        print(f"  {c['nome']}: maior prompt de D {tokens[maior]} ({maior}), pior caso {pior_caso}, "
              f"num_ctx {num_ctx}, razão {razao}")

    (RAIZ / SELECAO).write_text(texto, encoding="utf-8", newline="\n")
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({"dimensionamento": dim, "candidatos": medidas}, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"\n{SELECAO} preenchido e medidas em {SAIDA.relative_to(RAIZ).as_posix()}.")
    print("Próximo passo: a errata no evaluation/registro.yml (selecao.yml e modelo de prompt), antes da seleção.")


if __name__ == "__main__":
    main()
