"""
PT: Clientes do modelo. O ClienteOllama fala com a API nativa do Ollama
    local (/api/chat), que aceita num_ctx, seed, temperatura e o esquema
    JSON da resposta a cada requisição (decisão de 2026-10-08, ADR 0029). Usa
    só a biblioteca padrão, sem dependência nova.

    Prompt maior que o num_ctx conta como erro, sem corte em silêncio
    (evaluation/hipoteses.yml, execucao.contexto_do_modelo). O Ollama não
    recusa o prompt grande: ele corta. Por isso a conferência é depois da
    resposta, pelo prompt_eval_count: se o prompt avaliado mais o limite de
    tokens da resposta passa do num_ctx, a execução é erro de contexto.

    O ClienteFalso devolve respostas gravadas, em ordem, e guarda as
    mensagens recebidas. É o modelo dos testes no CI.

EN: Model clients. ClienteOllama talks to local Ollama's native /api/chat,
    which takes num_ctx, seed, temperature and the answer's JSON schema per
    request; standard library only. A prompt larger than num_ctx is an error,
    never silently cut: Ollama truncates instead of refusing, so the check
    runs after the answer, on prompt_eval_count. ClienteFalso replays
    recorded answers in order and keeps the messages it got; it is the CI
    test model.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from assistente.parametros import Parametros


class ErroDeGeracao(Exception):
    """
    PT: Falha do modelo: contexto (prompt maior que o num_ctx), tempo ou
        servidor. Vira o tipo do erro da execução, sem nova tentativa.
    EN: Model failure, typed contexto, tempo or servidor; no retry.
    """

    def __init__(self, tipo: str, mensagem: str):
        super().__init__(mensagem)
        self.tipo = tipo


@dataclass
class Geracao:
    """PT: uma resposta do modelo / EN: one model answer"""

    texto: str
    tokens_do_prompt: int | None = None
    tokens_da_resposta: int | None = None
    motivo_do_fim: str | None = None
    segundos: float | None = None


def conferir_contexto(geracao: Geracao, p: Parametros) -> None:
    """
    PT: Erro de contexto quando o prompt avaliado mais o limite da resposta
        passa do num_ctx: o prompt pode ter sido cortado, ou a resposta não
        caberia.
    EN: Context error when the evaluated prompt plus the answer limit exceeds
        num_ctx.
    """
    if geracao.tokens_do_prompt is not None and \
            geracao.tokens_do_prompt + p.limite_de_tokens_da_resposta > p.num_ctx:
        raise ErroDeGeracao("contexto", f"prompt de {geracao.tokens_do_prompt} tokens mais "
                                        f"{p.limite_de_tokens_da_resposta} da resposta passa do num_ctx {p.num_ctx}")


class ClienteOllama:
    """PT: o Ollama local, pela API nativa / EN: local Ollama, native API"""

    def __init__(self, p: Parametros):
        self.p = p

    def gerar(self, mensagens: list[dict], esquema: dict | None, seed: int) -> Geracao:
        """
        PT: Uma chamada ao /api/chat, sem streaming.
        EN: One /api/chat call, without streaming.
        """
        p = self.p
        corpo = {
            "model": p.modelo,
            "messages": mensagens,
            "stream": False,
            "think": p.think,
            "options": {"num_ctx": p.num_ctx, "temperature": p.temperatura, "seed": seed,
                        "num_predict": p.limite_de_tokens_da_resposta},
        }
        if p.esquema_json and esquema is not None:
            corpo["format"] = esquema
        pedido = urllib.request.Request(f"{p.endereco}/api/chat", data=json.dumps(corpo).encode("utf-8"),
                                        headers={"Content-Type": "application/json"})
        inicio = time.perf_counter()
        try:
            with urllib.request.urlopen(pedido, timeout=p.tempo_maximo_do_servidor) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except TimeoutError:
            raise ErroDeGeracao("tempo", f"o modelo passou de {p.tempo_maximo_do_servidor:g} s") from None
        except urllib.error.HTTPError as erro:
            raise ErroDeGeracao("servidor", f"HTTP {erro.code}: {erro.read().decode('utf-8', 'replace')[:300]}") from None
        except urllib.error.URLError as erro:
            if isinstance(erro.reason, TimeoutError):
                raise ErroDeGeracao("tempo", f"o modelo passou de {p.tempo_maximo_do_servidor:g} s") from None
            raise ErroDeGeracao("servidor", f"Ollama fora do ar em {p.endereco}: {erro.reason}") from None
        geracao = Geracao(
            texto=dados.get("message", {}).get("content", ""),
            tokens_do_prompt=dados.get("prompt_eval_count"),
            tokens_da_resposta=dados.get("eval_count"),
            motivo_do_fim=dados.get("done_reason"),
            segundos=round(time.perf_counter() - inicio, 3),
        )
        conferir_contexto(geracao, p)
        return geracao


class ClienteFalso:
    """
    PT: Devolve respostas gravadas, em ordem. Cada resposta é um texto ou uma
        Geracao. Guarda as chamadas recebidas.
    EN: Replays recorded answers in order and keeps the calls it got.
    """

    def __init__(self, respostas: list, p: Parametros | None = None):
        self.respostas = list(respostas)
        self.p = p
        self.chamadas: list[dict] = []

    def gerar(self, mensagens: list[dict], esquema: dict | None, seed: int) -> Geracao:
        self.chamadas.append({"mensagens": mensagens, "esquema": esquema, "seed": seed})
        if not self.respostas:
            raise AssertionError("o cliente falso não tem mais respostas gravadas")
        resposta = self.respostas.pop(0)
        geracao = resposta if isinstance(resposta, Geracao) else Geracao(texto=resposta)
        if self.p is not None:
            conferir_contexto(geracao, self.p)
        return geracao
