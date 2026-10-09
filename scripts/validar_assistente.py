"""
PT: Valida o assistente de dados (#49, ADR 0029) sem rede, sem modelo e sem
    dado. O modelo é o ClienteFalso, de respostas gravadas; o banco são
    tabelas vazias com as colunas e os tipos do esquema estrela
    (evaluation/gabarito/esquema_estrela.json); e os trechos são inventados.
    Roda no workflow próprio .github/workflows/assistente.yml.

    O que é conferido:

    1. **Parâmetros.** A temperatura e as seeds batem com o bloco execucao
       do evaluation/hipoteses.yml, congelado no pré-registro.
    2. **Montagem por condição** (ADR 0013). A leva só o esquema, sem
       ontologia e sem trechos; as quatro começam pelas mesmas instruções;
       B traz todos os itens da ontologia; C é A mais o bloco de trechos; e
       D é exatamente B mais o mesmo bloco de trechos de C.
    3. **Guarda do SQL.** Recusa escrita, dois comandos, tabela fora do
       esquema estrela, prefixo de esquema, leitura de arquivo, função de
       tabela, ATTACH, PRAGMA e SET; aceita SELECT e CTE sobre dim_* e
       fct_*.
    4. **Limites.** O tempo esgotado interrompe a consulta perto do limite,
       e o resultado acima do limite de linhas é cortado com o aviso
       "cortado em N de M linhas" na segunda chamada.
    5. **Fluxo** (hipoteses.yml, execucao.fluxo e falhas). A abstenção não
       executa SQL nem faz a segunda chamada; saída fora do formato, prompt
       maior que o num_ctx e erro de SQL viram erro tipado, sem nova
       tentativa; a resposta tem os cinco campos de
       comparacao.formato_da_resposta.
    6. **Proveniência.** Os conceitos resolvidos pelo código a partir do SQL
       trazem rótulo, confiança e fonte, e a modalidade do filtro aparece.
    7. **Fumaça fora do teste.** Nenhuma pergunta de
       scripts/analises/fumaca_assistente.py coincide com uma das
       registradas, nem a repete com outras palavras (sobreposição de
       palavras de 60% ou mais).

    Com --autoteste, troca uma peça por vez por uma versão estragada e
    confere que a validação reprova cada uma pelo motivo certo.

EN: Validates the data assistant with no network, model or data: a fake
    model, empty star schema tables and invented excerpts. Checks
    parameters against the pre-registration, prompt assembly per condition,
    the SQL guard, time and row limits, the run flow (abstention, typed
    errors without retry, the five answer fields), code-built provenance,
    and that smoke questions are not registered ones. --autoteste swaps one
    piece at a time for a broken version and checks each is rejected for
    the right reason.

Uso / Usage:
    uv run python -m scripts.validar_assistente
    uv run python -m scripts.validar_assistente --autoteste
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, replace
from typing import Callable
from unittest import mock

import yaml

import assistente.responder

from assistente import contexto, ontologia, parametros
from assistente.cliente import ClienteFalso, Geracao
from assistente.parametros import CONDICOES, HIPOTESES
from assistente.responder import responder
from assistente.sql import Analise, ErroDeSQL, analisar, banco_vazio, executar
from scripts.analises.fumaca_assistente import PERGUNTAS_DE_FUMACA
from scripts.validar_perguntas import VIGENTE, perguntas

TRECHOS = [
    {"trecho": 7, "documento": "metodologia_v2", "titulo": "Carteira ativa", "secao": "3.w", "pagina": 4,
     "similaridade": 0.81, "texto": "Trecho inventado para o teste da montagem."},
    {"trecho": 12, "documento": "instrucoes_3040", "titulo": None, "secao": None, "pagina": 21,
     "similaridade": 0.77, "texto": "Outro trecho inventado."},
]

# PT: (SQL, aprovado?) para a guarda.
# EN: (SQL, accepted?) for the guard.
CASOS_DA_GUARDA = [
    ("select sum(carteira_ativa) from fct_carteira where uf = 'AC'", True),
    ("with t as (select uf, sum(carteira_ativa) v from fct_carteira group by 1) select * from t join dim_uf using (uf)",
     True),
    ("insert into fct_carteira select * from fct_carteira", False),
    ("delete from dim_uf", False),
    ("create table x as select 1", False),
    ("select 1; select 2", False),
    ("select * from tabela_qualquer", False),
    ("select * from main.fct_carteira", False),
    ("select * from information_schema.tables", False),
    ("select * from read_parquet('data/esquema_estrela/data/fct_carteira/*.parquet')", False),
    ("select * from 'arquivo.csv'", False),
    ("select * from query('select 1')", False),
    ("select * from duckdb_settings()", False),
    ("attach 'outro.duckdb' as outro", False),
    ("pragma version", False),
    ("set threads = 1", False),
    ("copy (select 1) to 'saida.csv'", False),
]

LENTO = "with recursive t(n) as (select 1 union all select n + 1 from t where n < 1000000000) select count(*) from t"
LIMITE_DE_TEMPO = 0.5
FOLGA_DE_TEMPO = 2.0

PROVENIENCIA_SQL = ("select sum(c.carteira_ativa) from fct_carteira c join dim_modalidade m "
                    "using (codigo_submodalidade) where c.uf = 'AC' and m.codigo_submodalidade = '0203'")
CONCEITOS_ESPERADOS = {"metricas.carteira_ativa": "coluna", "dimensoes.dim_uf": "coluna",
                       "modalidades.sub_0203": "filtro"}


@dataclass(frozen=True)
class Pecas:
    """
    PT: As peças conferidas. O autoteste troca uma de cada vez.
    EN: The pieces under test; the self-test swaps one at a time.
    """

    sistema: Callable = contexto.sistema
    analisar: Callable = analisar
    executar: Callable = executar
    responder: Callable = responder
    perguntas_de_fumaca: tuple[str, ...] = PERGUNTAS_DE_FUMACA


def _json(**campos) -> str:
    return json.dumps(campos, ensure_ascii=False)


def primeira(sql: str = "", abstencao: str = "") -> str:
    """PT: resposta gravada da primeira chamada / EN: recorded first answer"""
    return _json(interpretacao="interpretação de teste", sql=sql, abstencao=abstencao)


def segunda() -> str:
    """PT: resposta gravada da segunda chamada / EN: recorded second answer"""
    return _json(interpretacao="interpretação de teste", valores={"colunas": ["total"], "linhas": [[1]]},
                 ressalva="", abstencao="")


# -----------------------------------------------------------------------------
# PT: Conferências / EN: checks
# -----------------------------------------------------------------------------

def checar_parametros(p: parametros.Parametros, hipoteses: dict) -> list[str]:
    """PT: conferência 1 / EN: check 1"""
    return [f"parâmetros: {d}" for d in parametros.divergencias_do_pre_registro(p, hipoteses)]


def checar_montagem(pecas: Pecas, modelo: dict[str, str]) -> list[str]:
    """PT: conferência 2 / EN: check 2"""
    problemas = []
    textos = {c: pecas.sistema(c, modelo, TRECHOS if "trechos" in CONDICOES[c] else None) for c in CONDICOES}
    cabecalho = {nome: modelo[f"bloco_{nome}"].splitlines()[0] for nome in ("esquema", "ontologia", "trechos")}
    for condicao, texto in textos.items():
        if not texto.startswith(modelo["instrucoes"]):
            problemas.append(f"montagem: {condicao} não começa pelas instruções comuns")
        for nome, linha in cabecalho.items():
            dentro = linha in texto
            if dentro != (nome in CONDICOES[condicao]):
                problemas.append(f"montagem: {condicao} {'leva' if dentro else 'não leva'} o bloco {nome}")
    faltando = [id_ for id_, _, _ in ontologia.itens() if f"id: {id_}\n" not in textos["B"] + "\n"]
    if faltando:
        problemas.append(f"montagem: B sem {len(faltando)} itens da ontologia, como {faltando[0]}")
    bloco_de_trechos = textos["C"].removeprefix(textos["A"])
    if not bloco_de_trechos.startswith("\n\n"):
        problemas.append("montagem: C não é A mais o bloco de trechos")
    if textos["D"] != textos["B"] + bloco_de_trechos:
        problemas.append("montagem: D difere de B mais o bloco de trechos de C")
    return problemas


def checar_guarda(pecas: Pecas) -> list[str]:
    """PT: conferência 3 / EN: check 3"""
    problemas = []
    for sql, aprovado in CASOS_DA_GUARDA:
        recusas = pecas.analisar(sql).problemas
        if aprovado and recusas:
            problemas.append(f"guarda: recusou um SQL válido ({sql}): {recusas}")
        elif not aprovado and not recusas:
            problemas.append(f"guarda: aprovou {sql}")
    return problemas


def checar_tempo(pecas: Pecas, banco) -> list[str]:
    """PT: conferência 4, tempo / EN: check 4, time"""
    inicio = time.perf_counter()
    try:
        pecas.executar(banco, LENTO, 100, LIMITE_DE_TEMPO)
    except ErroDeSQL as erro:
        segundos = time.perf_counter() - inicio
        if erro.tipo != "tempo":
            return [f"tempo: a consulta lenta deu erro {erro.tipo} e não de tempo"]
        if segundos > LIMITE_DE_TEMPO + FOLGA_DE_TEMPO:
            return [f"tempo: a interrupção levou {segundos:.1f} s para um limite de {LIMITE_DE_TEMPO} s"]
        return []
    return ["tempo: a consulta lenta terminou sem interrupção"]


def _rodar(pecas: Pecas, banco, p, modelo, respostas: list, pergunta: str = "pergunta de teste",
           condicao: str = "A") -> tuple[dict, ClienteFalso]:
    # PT: o responder chama o executar do próprio módulo; a peça entra ali.
    # EN: responder calls its module's executar; the piece goes there.
    cliente = ClienteFalso(respostas)
    with mock.patch.object(assistente.responder, "executar", pecas.executar):
        registro = pecas.responder(pergunta, condicao, p.seeds[0], cliente=cliente, banco=banco, p=p,
                                   modelo=modelo, trechos=TRECHOS if "trechos" in CONDICOES[condicao] else None)
    return registro, cliente


def checar_fluxo(pecas: Pecas, banco, p, modelo, formato: dict) -> list[str]:
    """PT: conferências 4 (corte) e 5 / EN: checks 4 (cut) and 5"""
    problemas = []

    # PT: resposta completa, nos cinco campos registrados.
    # EN: full answer, with the five registered fields.
    registro, cliente = _rodar(pecas, banco, p, modelo, [primeira("select count(*) from fct_carteira"), segunda()])
    if registro["erro"] or len(cliente.chamadas) != 2:
        problemas.append(f"fluxo: a execução normal falhou ou não fez duas chamadas: {registro['erro']}")
    elif set(registro["resposta"]) != set(formato):
        problemas.append(f"fluxo: a resposta tem {sorted(registro['resposta'])}, e não os campos registrados "
                         f"{sorted(formato)}")
    elif registro["resposta"]["sql"] != "select count(*) from fct_carteira":
        problemas.append("fluxo: o sql da resposta não é o executado")

    # PT: corte: um resultado acima do limite avisa N de M na segunda chamada.
    # EN: cut: a result above the limit tells N of M in the second call.
    total = p.limite_de_linhas + 50
    sql = f"with recursive t(n) as (select 1 union all select n + 1 from t where n < {total}) select n from t"
    registro, cliente = _rodar(pecas, banco, p, modelo, [primeira(sql), segunda()])
    aviso = f"cortado em {p.limite_de_linhas} de {total} linhas"
    if len(cliente.chamadas) < 2 or aviso not in cliente.chamadas[1]["mensagens"][-1]["content"]:
        problemas.append(f"corte: a segunda chamada não avisa '{aviso}'")
    elif len(registro["resultado"]["linhas"]) != p.limite_de_linhas:
        problemas.append("corte: o resultado guardado não tem o limite de linhas")

    # PT: abstenção: sem SQL executado e sem segunda chamada. O SQL que vem
    #     junto daria erro se fosse executado.
    # EN: abstention: no SQL run and no second call.
    registro, cliente = _rodar(pecas, banco, p, modelo,
                               [primeira("select * from tabela_que_nao_existe", "faltaria o dado X"), segunda()])
    if registro["resultado"] is not None or registro["erro"] or len(cliente.chamadas) != 1:
        problemas.append("abstenção: executou o SQL ou fez a segunda chamada")
    elif registro["resposta"]["sql"] or registro["resposta"]["valores"]["linhas"]:
        problemas.append("abstenção: a resposta traz sql ou valores")

    # PT: falhas tipadas, sem nova tentativa: o cliente ainda tem respostas
    #     gravadas, e só a primeira pode ter sido pedida.
    # EN: typed failures without retry.
    grande = Geracao(texto=primeira("select 1"), tokens_do_prompt=p.num_ctx)
    falhas = [
        ("formato", "isto não é JSON"),
        ("formato", "```json\n" + primeira("select 1") + "\n```"),
        ("contexto", grande),
        ("sql", primeira("select coluna_inexistente from fct_carteira")),
        ("guarda", primeira("select * from read_csv('x.csv')")),
    ]
    for tipo, resposta in falhas:
        registro, cliente = _rodar(pecas, banco, p, modelo, [resposta, primeira("select 1"), segunda(), segunda()])
        erro = registro["erro"] or {}
        if len(cliente.chamadas) != 1:
            problemas.append(f"falha: erro {tipo} com nova tentativa ({len(cliente.chamadas)} chamadas)")
        elif erro.get("tipo") != tipo:
            problemas.append(f"falha: esperava erro {tipo}, veio {erro.get('tipo')}")
        elif len(registro["chamadas"]) != 1:
            problemas.append(f"falha: a chamada do erro {tipo} não ficou no registro")

    # PT: estimativa antes do envio: com um num_ctx pequeno, nada é enviado.
    # EN: pre-send estimate: with a small num_ctx nothing is sent.
    registro, cliente = _rodar(pecas, banco, replace(p, num_ctx=p.limite_de_tokens_da_resposta + 100), modelo,
                               [primeira("select 1"), segunda()])
    if (registro["erro"] or {}).get("tipo") != "contexto" or cliente.chamadas:
        problemas.append("contexto: o prompt estimado acima do num_ctx foi enviado ao modelo")
    return problemas


def checar_proveniencia(pecas: Pecas, banco, p, modelo) -> list[str]:
    """PT: conferência 6 / EN: check 6"""
    registro, _ = _rodar(pecas, banco, p, modelo, [primeira(PROVENIENCIA_SQL), segunda()], condicao="D")
    conceitos = {c["id"]: c for c in registro["proveniencia"]["conceitos"]}
    problemas = []
    for id_, onde in CONCEITOS_ESPERADOS.items():
        if id_ not in conceitos:
            problemas.append(f"proveniência: {id_} não foi resolvido do SQL")
        elif onde not in conceitos[id_]["onde"]:
            problemas.append(f"proveniência: {id_} sem a origem {onde}")
    for c in conceitos.values():
        if not (c.get("rotulo") and c.get("confianca") and c.get("fonte")):
            problemas.append(f"proveniência: {c['id']} sem rótulo, confiança ou fonte")
    if registro["proveniencia"]["trechos"] != TRECHOS:
        problemas.append("proveniência: os trechos recebidos não estão no registro")

    # PT: select * não cita a coluna, mas a coluna volta no resultado.
    # EN: select * names no column, but the column comes back in the result.
    registro, _ = _rodar(pecas, banco, p, modelo, [primeira("select * from fct_carteira"), segunda()])
    if "metricas.carteira_ativa" not in {c["id"] for c in registro["proveniencia"]["conceitos"]}:
        problemas.append("proveniência: select * não resolveu as métricas do resultado")
    return problemas


def _palavras(texto: str) -> set[str]:
    return set(re.findall(r"\w+", texto.casefold()))


def checar_fumaca(pecas: Pecas, registradas: list[str]) -> list[str]:
    """PT: conferência 7 / EN: check 7"""
    problemas = []
    for pergunta in pecas.perguntas_de_fumaca:
        for registrada in registradas:
            a, b = _palavras(pergunta), _palavras(registrada)
            sobreposicao = len(a & b) / len(a | b)
            if sobreposicao >= 0.6:
                problemas.append(f"fumaça: '{pergunta}' repete a registrada '{registrada}' "
                                 f"({sobreposicao:.0%} das palavras)")
    return problemas


def validar(pecas: Pecas, p, modelo, hipoteses: dict, registradas: list[str]) -> list[str]:
    """PT: lista de problemas; vazia quando está tudo certo / EN: list of problems"""
    banco = banco_vazio()
    formato = hipoteses["comparacao"]["formato_da_resposta"]
    return [
        *checar_parametros(p, hipoteses),
        *checar_montagem(pecas, modelo),
        *checar_guarda(pecas),
        *checar_tempo(pecas, banco),
        *checar_fluxo(pecas, banco, p, modelo, formato),
        *checar_proveniencia(pecas, banco, p, modelo),
        *checar_fumaca(pecas, registradas),
    ]


# -----------------------------------------------------------------------------
# PT: Autoteste / EN: self-test
# -----------------------------------------------------------------------------

def autoteste(p, modelo, hipoteses: dict, registradas: list[str]) -> list[str]:
    """
    PT: Cada caso troca uma peça por uma versão estragada e diz o trecho que
        a reprovação precisa trazer. O caso falha se a validação aprovar, ou
        se reprovar por outro motivo.
    EN: Each case swaps in a broken piece and names the fragment the
        rejection must carry.
    """
    base = Pecas()
    if validar(base, p, modelo, hipoteses, registradas):
        return ["as peças versionadas já falham na validação; o autoteste parte delas"]

    def ontologia_em_a(condicao, m, trechos=None):
        texto = contexto.sistema(condicao, m, trechos)
        return texto + "\n\n" + contexto.preencher(m["bloco_ontologia"], ontologia="") if condicao == "A" else texto

    def d_sem_um_trecho(condicao, m, trechos=None):
        return contexto.sistema(condicao, m, trechos[:1] if condicao == "D" else trechos)

    def responder_que_tenta_de_novo(*args, **kwargs):
        registro = responder(*args, **kwargs)
        return responder(*args, **kwargs) if registro["erro"] else registro

    def responder_que_ignora_abstencao(pergunta, condicao, seed, *, cliente, **kwargs):
        gerar = cliente.gerar

        def gerar_sem_abstencao(mensagens, esquema, seed):
            geracao = gerar(mensagens, esquema, seed)
            try:
                dados = json.loads(geracao.texto)
            except json.JSONDecodeError:
                return geracao
            if "sql" in dados:
                dados["abstencao"] = ""
            return replace(geracao, texto=json.dumps(dados))

        cliente.gerar = gerar_sem_abstencao
        return responder(pergunta, condicao, seed, cliente=cliente, **kwargs)

    def responder_sem_confianca(*args, **kwargs):
        registro = responder(*args, **kwargs)
        for c in registro["proveniencia"]["conceitos"]:
            c["confianca"] = None
        return registro

    negativos = [
        ("ontologia na condição A", Pecas(sistema=ontologia_em_a), "A leva o bloco ontologia"),
        ("D com trechos diferentes de C", Pecas(sistema=d_sem_um_trecho), "D difere de B mais o bloco de trechos"),
        ("guarda que aprova tudo", Pecas(analisar=lambda sql: Analise()), "guarda: aprovou"),
        ("sem limite de tempo", Pecas(executar=lambda b, s, n, t: executar(b, s, n, t * 10)), "tempo: a interrupção"),
        ("sem corte de linhas", Pecas(executar=lambda b, s, n, t: executar(b, s, n * 10, t)), "corte:"),
        ("nova tentativa depois do erro", Pecas(responder=responder_que_tenta_de_novo), "com nova tentativa"),
        ("abstenção ignorada", Pecas(responder=responder_que_ignora_abstencao), "abstenção:"),
        ("proveniência sem confiança", Pecas(responder=responder_sem_confianca), "sem rótulo, confiança ou fonte"),
        ("fumaça com pergunta registrada", Pecas(perguntas_de_fumaca=(*PERGUNTAS_DE_FUMACA, registradas[0])),
         "fumaça:"),
    ]
    falhas = []
    for descricao, pecas, trecho in negativos:
        problemas = validar(pecas, p, modelo, hipoteses, registradas)
        if not problemas:
            falhas.append(f"aprovou o estrago: {descricao}")
        elif not any(trecho in problema for problema in problemas):
            falhas.append(f"reprovou '{descricao}' pelo motivo errado: {problemas}")
        else:
            print(f"  reprovado, como devia / rejected as expected: {descricao}")

    estragado = replace(p, temperatura=0.7)
    if not any("temperatura" in problema for problema in checar_parametros(estragado, hipoteses)):
        falhas.append("aprovou o estrago: temperatura fora do pré-registro")
    else:
        print("  reprovado, como devia / rejected as expected: temperatura fora do pré-registro")
    return falhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--autoteste", action="store_true", help="controle negativo / negative control")
    args = parser.parse_args()

    p = parametros.carregar()
    modelo = parametros.modelo_de_prompt()
    hipoteses = yaml.safe_load(HIPOTESES.read_text(encoding="utf-8"))
    registradas = [q["pergunta"] for q in perguntas(VIGENTE)[1].values()]

    if args.autoteste:
        falhas = autoteste(p, modelo, hipoteses, registradas)
    else:
        falhas = validar(Pecas(), p, modelo, hipoteses, registradas)
        print(f"  {len(CONDICOES)} condições, {len(ontologia.itens())} itens da ontologia, "
              f"{len(CASOS_DA_GUARDA)} casos da guarda, {len(PERGUNTAS_DE_FUMACA)} perguntas de fumaça "
              f"contra {len(registradas)} registradas; parâmetros "
              f"{'provisórios até a #48' if p.provisorio else 'fixados'}")
    for falha in falhas:
        print(f"ERRO {falha}")
    if falhas:
        sys.exit(1)
    print("  ok")


if __name__ == "__main__":
    main()
