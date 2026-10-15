"""
PT: Replay da V−1 contra a execução 1 (#118, ADR 0032), por outro caminho
    que o validar_variacoes. Passa cada uma das 1.640 execuções gravadas em
    data/experimento/ pelo assistente.responder com variacao="V-1", sobre o
    retrato local no DuckDB, com um cliente falso que devolve as respostas
    que o modelo deu (texto, tokens e motivo do fim) e os trechos gravados.

    Compara com o registro gravado: as mensagens de cada chamada, a
    resposta, o erro e o resultado do SQL. Uma diferença com o mesmo
    resultado do SQL é do código e reprova. Uma diferença em que o resultado
    do SQL mudou vem do banco: a ordem das linhas sem order by ou o tempo
    com uma thread só (a execução 1 rodou com várias threads). Essas saem
    contadas, sem reprovar.

    Roda na minha máquina, sem modelo, porque precisa de data/.

EN: Replays run 1 through the V−1 responder on the local DuckDB with a fake
    client fed the recorded model answers and excerpts, and compares
    messages, answer, error and SQL result. Differences with the same SQL
    result are code differences and fail; those where the SQL result moved
    come from the database and are only counted.

Uso / Usage:
    uv run python -m scripts.analises.replay_v_menos_1
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter

from assistente import parametros
from assistente.cliente import ClienteFalso, Geracao
from assistente.responder import responder
from assistente.sql import abrir_banco
from correcao.acerto import PADRAO_DO_EXPERIMENTO, ler_execucoes
from scripts.executar_experimento import PASTA_DO_EXPERIMENTO


def respostas_gravadas(registro: dict) -> list[Geracao]:
    """PT: o que o modelo respondeu em cada chamada / EN: recorded model answers"""
    return [Geracao(texto=c["resposta"], tokens_do_prompt=c.get("tokens_do_prompt"),
                    tokens_da_resposta=c.get("tokens_da_resposta"), motivo_do_fim=c.get("motivo_do_fim"))
            for c in registro["chamadas"] if c.get("resposta") is not None]


def _erro(registro: dict):
    erro = registro.get("erro")
    return None if erro is None else (erro.get("tipo"), erro.get("etapa"))


def _sem_tempo(resultado: dict | None) -> dict | None:
    """PT: o resultado sem o tempo do SQL, que muda a cada rodada / EN: result without timing"""
    return None if resultado is None else {k: v for k, v in resultado.items() if k != "segundos"}


def comparar(gravado: dict, refeito: dict, cliente: ClienteFalso) -> list[str]:
    """PT: as partes que diferem / EN: the parts that differ"""
    diferencas = []
    # PT: o registro guarda o sha256 da mensagem de sistema e as outras.
    # EN: the record keeps the system message's sha256 and the others.
    gravadas = [(c["sistema_sha256"], c["mensagens"]) for c in gravado["chamadas"]]
    refeitas = [(hashlib.sha256(c["mensagens"][0]["content"].encode("utf-8")).hexdigest(), c["mensagens"][1:])
                for c in cliente.chamadas]
    if gravadas != refeitas:
        diferencas.append("mensagens")
    if gravado.get("resposta") != refeito.get("resposta"):
        diferencas.append("resposta")
    if _erro(gravado) != _erro(refeito):
        diferencas.append("erro")
    if _sem_tempo(gravado.get("resultado")) != _sem_tempo(refeito.get("resultado")):
        diferencas.append("resultado")
    return diferencas


def main() -> None:
    registros = ler_execucoes(PASTA_DO_EXPERIMENTO, PADRAO_DO_EXPERIMENTO)
    if not registros:
        raise SystemExit("ERRO sem a execução 1 em data/experimento/")
    banco, modelo = abrir_banco(), parametros.modelo_de_prompt()
    do_banco, do_codigo, exemplos = Counter(), Counter(), []
    for i, gravado in enumerate(registros, 1):
        p = parametros.Parametros(**{**gravado["parametros"], "seeds": tuple(gravado["parametros"]["seeds"])})
        cliente = ClienteFalso(respostas_gravadas(gravado))
        try:
            refeito = responder(gravado["pergunta"], gravado["condicao"], gravado["seed"], cliente=cliente,
                                banco=banco, p=p, modelo=modelo, trechos=gravado["trechos"] or None,
                                variacao="V-1")
        except AssertionError:
            # PT: o fluxo pediu mais chamadas do que o modelo respondeu.
            # EN: the flow asked for more calls than were recorded.
            refeito = {"erro": {"tipo": "replay", "etapa": "chamadas"}}
        diferencas = comparar(gravado, refeito, cliente)
        if diferencas:
            chave = gravado["candidato"], gravado["condicao"], gravado["id_pergunta"], gravado["seed"]
            if "resultado" in diferencas:
                do_banco[tuple(diferencas)] += 1
            else:
                do_codigo[tuple(diferencas)] += 1
                exemplos.append((chave, diferencas))
        if i % 200 == 0:
            print(f"  {i} de {len(registros)}", flush=True)
    iguais = len(registros) - sum(do_banco.values()) - sum(do_codigo.values())
    print(f"\n  {iguais} de {len(registros)} iguais; diferenças vindas do resultado do SQL: {dict(do_banco)}; "
          f"do código: {dict(do_codigo)}")
    for chave, diferencas in exemplos[:10]:
        print(f"ERRO {chave}: {diferencas}")
    sys.exit(1 if do_codigo else 0)


if __name__ == "__main__":
    main()
