"""
PT: O corretor por script (#48, ADR 0030; evaluation/hipoteses.yml,
    comparacao.correcao.por_script). Confere os valores de uma resposta do
    assistente contra o gabarito, pelo evaluation/comparacao.yml.

    O modelo dá nomes livres às colunas de valores. Por isso o corretor casa
    pelo valor, e não pelo nome (decisão de 2026-10-09):

    - Uma conferência de valor procura, na tabela da resposta, uma célula que
      bata dentro da tolerância da coluna do gabarito. Quando a linha do
      gabarito tem texto ou data (mês, janela, medida), a busca se restringe
      às linhas da resposta que trazem um desses, se houver alguma.
    - Numa lista, o item casa pela chave, pelo código ou pelo nome, e cada
      coluna de valores tem de bater numa mesma coluna da resposta, com a
      mesma escala, em todos os itens.
    - Ranking: os n primeiros do gabarito estão na resposta, com os valores
      certos, e nenhum outro item aparece com valor que o poria entre eles
      fora da tolerância. A ordem sai dos valores: com os valores certos, a
      ordem é a do gabarito, e a troca dentro da tolerância é aceita.
    - Conjunto: todos os itens do gabarito, sem item a mais. Vale a lista de
      itens que a resposta traz, ou a dos marcados como verdadeiros numa
      coluna booleana. Um item na zona de indiferença do limiar pode estar
      ou não. Linha que não se identifica com nenhum item do gabarito, como
      um total, não conta como item a mais.
    - Escala: em reais e contagens, a resposta pode vir em mil, milhão,
      bilhão ou trilhão; em percentual, como fração. O número é convertido
      antes da comparação (comparacao.tolerancia.escala).
    - Leituras e janelas: a resposta bate se cumprir todas as conferências
      de todas as consultas de uma leitura, numa janela. Q28 e Q30, com
      várias consultas, procuram tudo na tabela única da resposta.

    O que o script não decide fica para a correção às cegas: a ressalva, a
    abstenção e a leitura declarada (correcao.as_cegas).

EN: The script grader. Checks an assistant answer's values against the
    answer key through comparacao.yml. The model names its columns freely,
    so matching is by value, not by name: single values are searched in the
    answer table within the key column's tolerance; list items match by code
    or name and each value column must match one answer column with one
    scale for every item; rankings require the key's top n with the right
    values and no other item better than them beyond tolerance; sets require
    every key item and no extra one, either as listed rows or as rows flagged
    true in a boolean column, with indifference-zone items optional. Scale
    (thousand to trillion, fraction vs percent) is converted first. An answer
    matches a reading if it passes every check of every query of that reading
    in one window. Caveat, abstention and declared reading are left to blind
    grading.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache

import yaml

from correcao.tolerancia import banda_da_zona, dentro_da_banda
from scripts.validar_registro import COMPARACAO, GABARITO, HIPOTESES, RAIZ, classe_de_tolerancia, ler_respostas

# PT: os fatores de escala aceitos por classe: a resposta vezes o fator é
#     comparada ao gabarito.
# EN: accepted scale factors per class: answer times factor vs key.
FATORES = {
    "relativa": (Decimal(1), Decimal(10) ** 3, Decimal(10) ** 6, Decimal(10) ** 9, Decimal(10) ** 12),
    "pontos": (Decimal(1), Decimal(100)),
    "adimensional": (Decimal(1),),
    "exata": (Decimal(1),),
}

PALAVRAS_DE_ESCALA = {
    "mil": Decimal(10) ** 3,
    "milhao": Decimal(10) ** 6, "milhoes": Decimal(10) ** 6, "mi": Decimal(10) ** 6, "mm": Decimal(10) ** 6,
    "bilhao": Decimal(10) ** 9, "bilhoes": Decimal(10) ** 9, "bi": Decimal(10) ** 9,
    "trilhao": Decimal(10) ** 12, "trilhoes": Decimal(10) ** 12, "tri": Decimal(10) ** 12,
}

VERDADEIROS = {"true", "sim", "verdadeiro", "yes", "s", "v", "1"}
FALSOS = {"false", "nao", "falso", "no", "n", "f", "0"}
OPOSTOS = {"acima": "abaixo", "abaixo": "acima"}

UFS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


# -----------------------------------------------------------------------------
# PT: O gabarito carregado / EN: the loaded answer key
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Gabarito:
    """PT: o que o corretor lê do repositório / EN: what the grader reads"""

    comparacao: dict
    perguntas: dict
    respostas: dict
    regra: dict

    def tipo_de_acerto(self, id_: str) -> str:
        return self.perguntas[id_]["tipo_de_acerto"]

    def precisa_de_leitura_declarada(self, id_: str) -> bool:
        """
        PT: Mais de uma leitura, ou janela em aberto: o Yuri confere, às
            cegas, se a interpretação declarada é a que bateu.
        EN: More than one reading, or an open window: declared reading is
            checked blind.
        """
        entrada = self.comparacao[id_]
        if entrada == {"abstencao": "so_rubrica"}:
            return False
        return len(entrada) > 1 or any("janelas" in b for blocos in entrada.values() for b in blocos)


def _yaml(caminho: str) -> dict:
    return yaml.safe_load((RAIZ / caminho).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def carregar_gabarito() -> Gabarito:
    """PT: o gabarito do repositório, uma vez / EN: the repo answer key, once"""
    return Gabarito(
        comparacao=_yaml(COMPARACAO)["perguntas"],
        perguntas=_yaml(GABARITO)["perguntas"],
        respostas=ler_respostas(),
        regra=_yaml(HIPOTESES)["comparacao"]["tolerancia"],
    )


# -----------------------------------------------------------------------------
# PT: Leitura das células / EN: reading cells
# -----------------------------------------------------------------------------

def _sem_acento(texto) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c))


def normalizar(texto) -> str:
    """
    PT: Sem acento, sem caixa, com _ e - como espaço e espaços colapsados.
    EN: No accents, casefolded, _ and - as spaces, spaces collapsed.
    """
    return " ".join(re.sub(r"[_\-]", " ", _sem_acento(texto).casefold()).split())


def numero(celula) -> Decimal | None:
    """
    PT: A célula como número, ou None. Aceita número do JSON e texto em
        formato brasileiro ou inglês, com R$, %, p.p. e palavra de escala
        (mil, milhão, bilhão, trilhão), que já multiplica o número.
    EN: The cell as a number, or None. Accepts JSON numbers and text in
        Brazilian or English format, with currency, percent and scale words.
    """
    if celula is None or isinstance(celula, bool):
        return None
    if isinstance(celula, (int, float)):
        try:
            return Decimal(str(celula))
        except InvalidOperation:
            return None
    texto = _sem_acento(celula).casefold().replace("r$", "").replace("p.p.", "").replace("%", "")
    multiplicador = Decimal(1)
    palavras = texto.split()
    if len(palavras) > 1 and palavras[-1].rstrip(".") in PALAVRAS_DE_ESCALA:
        multiplicador = PALAVRAS_DE_ESCALA[palavras[-1].rstrip(".")]
        palavras = palavras[:-1]
    if len(palavras) > 1 and palavras[-1] == "pp":
        palavras = palavras[:-1]
    texto = "".join(palavras)
    if re.fullmatch(r"[+-]?\d+(\.\d+)?e[+-]?\d+", texto):
        return Decimal(texto) * multiplicador
    if not re.fullmatch(r"[+-]?[\d.,]*\d[\d.,]*", texto):
        return None
    if "," in texto and "." in texto:
        decimal = "," if texto.rindex(",") > texto.rindex(".") else "."
        milhar = "." if decimal == "," else ","
        texto = texto.replace(milhar, "").replace(decimal, ".")
    elif "," in texto:
        texto = texto.replace(",", ".") if texto.count(",") == 1 else texto.replace(",", "")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")
    try:
        return Decimal(texto) * multiplicador
    except InvalidOperation:
        return None


def mes(celula) -> tuple[int, int] | None:
    """PT: (ano, mês) de uma data ou mês em texto / EN: (year, month) of a date"""
    if celula is None:
        return None
    texto = _sem_acento(celula).casefold()
    if m := re.search(r"(\d{4})-(\d{1,2})", texto):
        return int(m.group(1)), int(m.group(2))
    if m := re.search(r"(\d{1,2})/(\d{4})", texto):
        return int(m.group(2)), int(m.group(1))
    if m := re.search(r"([a-z]{3})[a-z]*\.?(?:/| de | )(\d{4})", texto):
        if m.group(1) in MESES:
            return int(m.group(2)), MESES[m.group(1)]
    return None


def booleano(celula, coluna: str = "") -> bool | None:
    """
    PT: A célula como verdadeiro ou falso, ou None. Além de sim e não, a
        primeira palavra do nome da coluna do gabarito vale verdadeiro, e o
        oposto dela, falso (acima_da_media: "acima" e "abaixo").
    EN: The cell as a boolean, or None; the key column's first word counts
        as true and its opposite as false.
    """
    if celula is None:
        return None
    texto = normalizar(celula)
    if texto in VERDADEIROS:
        return True
    if texto in FALSOS:
        return False
    palavra = normalizar(coluna).split(" ")[0] if coluna else ""
    if palavra and texto.split(" ")[:1] == [palavra]:
        return True
    if palavra in OPOSTOS and texto.split(" ")[:1] == [OPOSTOS[palavra]]:
        return False
    return None


def identidades(valor: str, coluna: str) -> set[str]:
    """
    PT: As formas aceitas de um texto do gabarito: ele normalizado, o código
        sem zeros à esquerda e, para UF, o nome do estado.
    EN: Accepted forms of a key text: normalized, code without leading zeros
        and, for a state, its name.
    """
    formas = {normalizar(valor)}
    if str(valor).isdigit():
        formas.add(str(int(valor)))
    if coluna == "uf" and str(valor).upper() in UFS:
        formas.add(normalizar(UFS[str(valor).upper()]))
    return formas


def texto_casa(celula, valor: str, coluna: str) -> bool:
    if celula is None:
        return False
    forma = normalizar(celula)
    if forma.isdigit():
        forma = str(int(forma))
    return forma in identidades(valor, coluna)


def casa(classe: str, tipo: str, coluna: str, celula, esperado: str, fator: Decimal = Decimal(1)) -> bool:
    """
    PT: Uma célula da resposta bate com um valor do gabarito, na classe de
        tolerância da coluna e, nos números, com o fator de escala dado.
    EN: One answer cell matches one key value, in the column's tolerance
        class and, for numbers, with the given scale factor.
    """
    if esperado is None:
        return celula is None
    if classe == "classificacao":
        return booleano(celula, coluna) == (str(esperado).lower() == "true")
    if classe == "identidade":
        if tipo == "DATE":
            return mes(celula) is not None and mes(celula) == mes(esperado)
        return texto_casa(celula, esperado, coluna)
    obtido, alvo = numero(celula), numero(esperado)
    if obtido is None or alvo is None:
        return False
    return dentro_da_banda(classe, obtido * fator, alvo)


# -----------------------------------------------------------------------------
# PT: A resposta do gabarito / EN: the key's answer
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Consulta:
    """PT: a resposta de uma consulta do gabarito / EN: one key query result"""

    nome: str
    colunas: tuple[str, ...]
    tipos: tuple[str, ...]
    linhas: tuple[dict, ...]
    classes: dict

    @classmethod
    def de(cls, nome: str, resposta: dict, regra: dict) -> "Consulta":
        colunas = tuple(resposta["colunas"])
        return cls(
            nome=nome,
            colunas=colunas,
            tipos=tuple(resposta["tipos"]),
            linhas=tuple(dict(zip(colunas, linha)) for linha in resposta["linhas"]),
            classes={c: classe_de_tolerancia(c, t, regra) for c, t in zip(colunas, resposta["tipos"])},
        )

    def tipo(self, coluna: str) -> str:
        return self.tipos[self.colunas.index(coluna)]

    def linha(self, seletor) -> dict:
        """PT: a linha que o seletor aponta / EN: the row the selector picks"""
        if seletor is None or seletor == "primeira":
            return self.linhas[0]
        if seletor == "ultima":
            return self.linhas[-1]
        chave, valor = next(iter(seletor.items()))
        if chave in ("maior", "maior_em_modulo"):
            medida = abs if chave == "maior_em_modulo" else (lambda x: x)
            com_valor = [l for l in self.linhas if numero(l[valor]) is not None]
            return max(com_valor, key=lambda l: medida(numero(l[valor])))
        return next(l for l in self.linhas if str(l[chave]) == str(valor))

    def identidade_da_linha(self, linha: dict, exceto: str = "") -> list[tuple[str, str]]:
        """
        PT: Os textos e datas que distinguem a linha das outras: o mês de uma
            série, a janela, a medida. Um texto igual em todas as linhas não
            distingue nada.
        EN: Texts and dates that tell the row apart from the others.
        """
        return [(c, linha[c]) for c, t in zip(self.colunas, self.tipos)
                if t in ("STRING", "DATE") and c != exceto and linha[c] is not None
                and sum(l[c] == linha[c] for l in self.linhas) == 1]


@dataclass(frozen=True)
class Tabela:
    """PT: os valores da resposta do modelo / EN: the model answer's values"""

    linhas: tuple[tuple, ...]

    @classmethod
    def de(cls, valores) -> "Tabela":
        if not isinstance(valores, dict) or not isinstance(valores.get("linhas"), list):
            return cls(linhas=())
        return cls(linhas=tuple(tuple(l) for l in valores["linhas"] if isinstance(l, list)))

    @property
    def largura(self) -> int:
        return max((len(l) for l in self.linhas), default=0)

    def celula(self, i: int, j: int):
        linha = self.linhas[i]
        return linha[j] if j < len(linha) else None


# -----------------------------------------------------------------------------
# PT: Conferência de um valor / EN: checking one value
# -----------------------------------------------------------------------------

def _linhas_candidatas(tabela: Tabela, consulta: Consulta, linha: dict, coluna: str) -> list[int]:
    """
    PT: As linhas da resposta que trazem um texto ou data que distingue a
        linha do gabarito; todas, se nenhuma traz. Um valor igual em todas as
        linhas do gabarito (a mediana, a razão nacional) vale em qualquer
        linha.
    EN: Answer rows carrying a text or date distinguishing the key row; all
        if none does, or if the value is the same on every key row.
    """
    if len({l[coluna] for l in consulta.linhas}) == 1:
        return list(range(len(tabela.linhas)))
    marcas = consulta.identidade_da_linha(linha, exceto=coluna)
    escolhidas = [
        i for i in range(len(tabela.linhas))
        if any(casa("identidade", consulta.tipo(c), c, tabela.celula(i, j), v)
               for c, v in marcas for j in range(tabela.largura))
    ]
    return escolhidas or list(range(len(tabela.linhas)))


def _valor_na_tabela(tabela: Tabela, consulta: Consulta, linha: dict, coluna: str) -> bool:
    classe, tipo, esperado = consulta.classes[coluna], consulta.tipo(coluna), linha[coluna]
    fatores = FATORES.get(classe, (Decimal(1),))
    return any(
        casa(classe, tipo, coluna, tabela.celula(i, j), esperado, f)
        for i in _linhas_candidatas(tabela, consulta, linha, coluna)
        for j in range(tabela.largura)
        for f in fatores
    )


def conferir_valor(item: dict, consulta: Consulta, tabela: Tabela) -> list[str]:
    """PT: valor ou uma_de / EN: a single value or one of several"""
    linha = consulta.linha(item.get("linha"))
    colunas = [item["valor"]] if "valor" in item else list(item["uma_de"])
    if any(_valor_na_tabela(tabela, consulta, linha, c) for c in colunas):
        return []
    return [f"{consulta.nome}: {' ou '.join(colunas)} = "
            f"{' / '.join(str(linha[c]) for c in colunas)} não está na resposta"]


# -----------------------------------------------------------------------------
# PT: Limiar e zona de indiferença / EN: threshold and indifference zone
# -----------------------------------------------------------------------------

def situacao_no_filtro(linha: dict, condicoes: list[dict], consulta: Consulta) -> str:
    """
    PT: "dentro", "fora" ou "opcional" (na zona de indiferença de alguma
        condição, sem estar fora por outra).
    EN: "dentro", "fora" or "opcional" (in some condition's zone, and not
        out by another).
    """
    opcional = False
    for c in condicoes:
        x = numero(linha.get(c["coluna"]))
        ref = numero(linha.get(c["contra"])) if "contra" in c else numero(c.get("valor"))
        if x is None or ref is None:
            return "fora"
        if c["op"] == "modulo_maior_que":
            x = abs(x)
        zona = banda_da_zona(consulta.classes[c["coluna"]], x)
        if abs(x - ref) <= zona:
            opcional = True
            continue
        passa = x > ref if c["op"] in ("maior_que", "modulo_maior_que") else x < ref
        if not passa:
            return "fora"
    return "opcional" if opcional else "dentro"


def conferir_classificacao(item: dict, consulta: Consulta, tabela: Tabela) -> list[str]:
    """
    PT: A classificação booleana de uma linha (Q08). Na zona de indiferença,
        qualquer uma vale, desde que os números batam, o que as outras
        conferências cobrem.
    EN: A row's boolean classification; in the zone either holds.
    """
    linha = consulta.linha(item.get("linha"))
    if situacao_no_filtro(linha, item.get("onde") or [], consulta) == "opcional":
        return []
    if _valor_na_tabela(tabela, consulta, linha, item["classificacao"]):
        return []
    return [f"{consulta.nome}: classificação {item['classificacao']} = {linha[item['classificacao']]} "
            "não está na resposta"]


# -----------------------------------------------------------------------------
# PT: Listas / EN: lists
# -----------------------------------------------------------------------------

def _colunas_de_identidade(consulta: Consulta, chave: str) -> list[str]:
    """
    PT: A chave e os outros textos que identificam o item sozinhos (o nome
        ao lado do código).
    EN: The key plus other texts unique per row (the name next to the code).
    """
    outras = [
        c for c, t in zip(consulta.colunas, consulta.tipos)
        if t == "STRING" and c != chave and len({l[c] for l in consulta.linhas}) == len(consulta.linhas)
    ]
    return [chave, *outras]


def _identificar(tabela: Tabela, consulta: Consulta, chave: str) -> dict[int, set[int]]:
    """
    PT: Para cada linha do gabarito, as linhas da resposta que trazem o
        código ou o nome do item. A identidade vem de uma coluna só da
        resposta, a que identifica mais itens: assim a posição 1 não se
        confunde com o código 01.
    EN: For each key row, the answer rows carrying its code or name, read
        from the single answer column that identifies the most items, so
        position 1 is not taken for code 01.
    """
    colunas = _colunas_de_identidade(consulta, chave)
    numerica = consulta.tipo(chave) not in ("STRING", "DATE")

    def bate(celula, linha: dict) -> bool:
        if numerica:
            return numero(celula) is not None and numero(celula) == numero(linha[chave])
        return any(linha[c] is not None and texto_casa(celula, linha[c], c) for c in colunas)

    melhor: dict[int, set[int]] = {}
    for j in range(tabela.largura):
        achadas: dict[int, set[int]] = {}
        for k, linha in enumerate(consulta.linhas):
            linhas = {i for i in range(len(tabela.linhas)) if bate(tabela.celula(i, j), linha)}
            if linhas:
                achadas[k] = linhas
        if len(achadas) > len(melhor):
            melhor = achadas
    return melhor


def _alternativas(valores: list) -> list[list[str]]:
    """PT: cada coluna de valores, ou as de um uma_de / EN: value column groups"""
    return [v["uma_de"] if isinstance(v, dict) else [v] for v in valores or []]


def _coluna_que_bate(tabela: Tabela, consulta: Consulta, itens: list[int], linhas_por_item: dict[int, set[int]],
                     coluna: str) -> tuple[int, Decimal] | None:
    """
    PT: Uma coluna da resposta, com um fator de escala, em que o valor de
        todos os itens bate em alguma das linhas do item.
    EN: One answer column and scale factor matching every item's value.
    """
    classe, tipo = consulta.classes[coluna], consulta.tipo(coluna)
    for j in range(tabela.largura):
        for f in FATORES.get(classe, (Decimal(1),)):
            if all(
                any(casa(classe, tipo, coluna, tabela.celula(i, j), consulta.linhas[k][coluna], f)
                    for i in linhas_por_item.get(k, ()))
                for k in itens
            ):
                return j, f
    return None


def _valores_batem(tabela: Tabela, consulta: Consulta, itens: list[int], linhas_por_item: dict[int, set[int]],
                   valores: list) -> tuple[list[str], dict[str, tuple[int, Decimal]]]:
    falhas, achadas = [], {}
    if not itens:
        return falhas, achadas
    for grupo in _alternativas(valores):
        for coluna in grupo:
            if (achada := _coluna_que_bate(tabela, consulta, itens, linhas_por_item, coluna)) is not None:
                achadas[coluna] = achada
                break
        else:
            falhas.append(f"{consulta.nome}: {' ou '.join(grupo)} não bate em todos os itens")
    return falhas, achadas


def _ordem(consulta: Consulta, ordem: str) -> list[int]:
    """
    PT: As linhas do gabarito na ordem do ranking; as sem valor vão para o
        fim, nos dois sentidos.
    EN: Key rows in ranking order; rows without a value go last.
    """
    coluna = ordem.removeprefix("-")
    com_valor = [k for k in range(len(consulta.linhas)) if numero(consulta.linhas[k][coluna]) is not None]
    sem_valor = [k for k in range(len(consulta.linhas)) if k not in com_valor]
    ordenadas = sorted(com_valor, key=lambda k: numero(consulta.linhas[k][coluna]), reverse=ordem.startswith("-"))
    return ordenadas + sem_valor


def conferir_ranking(item: dict, consulta: Consulta, tabela: Tabela) -> list[str]:
    """PT: os n primeiros, com os valores / EN: the top n, with their values"""
    ordenados = _ordem(consulta, item["ordem"])
    n = len(ordenados) if item.get("n", "todas") == "todas" else item["n"]
    topo = ordenados[:n]
    achadas = _identificar(tabela, consulta, item["chave"])
    faltando = [consulta.linhas[k][item["chave"]] for k in topo if k not in achadas]
    if faltando:
        return [f"{consulta.nome}: faltam os itens {faltando} do ranking"]
    falhas, colunas = _valores_batem(tabela, consulta, topo, achadas, item.get("valores"))
    if falhas or n == len(ordenados):
        return falhas

    # PT: nenhum outro item com valor que o poria entre os n primeiros.
    # EN: no other item whose value would put it in the top n.
    primeira = _alternativas(item.get("valores"))[0][0]
    j, f = colunas[primeira]
    classe = consulta.classes[primeira]
    valores_do_topo = [numero(consulta.linhas[k][primeira]) for k in topo]
    if None in valores_do_topo or valores_do_topo[0] == valores_do_topo[-1]:
        return []
    decrescente = valores_do_topo[0] > valores_do_topo[-1]
    ultimo = valores_do_topo[-1]
    do_topo = set().union(*(achadas[k] for k in topo))
    for i in range(len(tabela.linhas)):
        if i in do_topo or (v := numero(tabela.celula(i, j))) is None:
            continue
        v *= f
        melhor = v > ultimo if decrescente else v < ultimo
        if melhor and not dentro_da_banda(classe, v, ultimo):
            return [f"{consulta.nome}: a linha {i + 1} da resposta traz um item fora do ranking do gabarito "
                    f"com valor {v} melhor que o do {n}º"]
    return []


def _booleanas(tabela: Tabela, linhas: set[int]) -> list[set[int]]:
    """
    PT: Para cada coluna da resposta que é booleana em todas as linhas dadas,
        as linhas marcadas como verdadeiras.
    EN: For each answer column boolean in all given rows, the rows flagged
        true.
    """
    marcadas = []
    for j in range(tabela.largura):
        lidas = {i: booleano(tabela.celula(i, j)) for i in linhas}
        if lidas and None not in lidas.values():
            marcadas.append({i for i, b in lidas.items() if b})
    return marcadas


def _filtro_pelos_valores(item: dict, consulta: Consulta, tabela: Tabela, achadas: dict[int, set[int]],
                          obrigatorios: set[int]) -> bool:
    """
    PT: A terceira leitura de um conjunto definido por limiar: a resposta é
        a tabela inteira, com todos os itens do gabarito, e os valores das
        colunas do filtro batem em todos. Então cada item está do lado certo
        do limiar pelos próprios números da resposta, como numa tabela com o
        ganho de cada modalidade (Q21). As colunas de valores também têm de
        bater. Uma resposta que traz só uma parte dos itens é uma seleção, e
        vale a regra do item a mais.
    EN: Third reading of a threshold set: the answer is the full table, with
        every key item, and the filter columns match on all of them, so each
        item sits on the right side of the threshold by the answer's own
        numbers. A partial answer is a selection, and the extra-item rule
        applies.
    """
    if set(achadas) != set(range(len(consulta.linhas))):
        return False
    itens = sorted(achadas)
    # PT: a coluna de comparação (a mediana, na Q14) é a mesma em todas as
    #     linhas, e tem conferência de valor própria.
    # EN: the comparison column is the same on every row and checked apart.
    colunas = {c["coluna"] for c in item["onde"]}
    if any(_coluna_que_bate(tabela, consulta, itens, achadas, c) is None for c in colunas):
        return False
    falhas, _ = _valores_batem(tabela, consulta, sorted(obrigatorios), achadas, item.get("valores"))
    return not falhas


def conferir_conjunto(item: dict, consulta: Consulta, tabela: Tabela) -> list[str]:
    """PT: todos os itens, sem item a mais / EN: every item, no extra one"""
    chave = item["chave"]
    situacao = {
        k: situacao_no_filtro(linha, item["onde"], consulta) if item.get("onde") else "dentro"
        for k, linha in enumerate(consulta.linhas)
    }
    obrigatorios = {k for k, s in situacao.items() if s == "dentro"}
    aceitos = obrigatorios | {k for k, s in situacao.items() if s == "opcional"}
    achadas = _identificar(tabela, consulta, chave)

    # PT: as leituras possíveis do que a resposta apresenta como o conjunto:
    #     as linhas listadas, ou as marcadas verdadeiras numa coluna booleana.
    # EN: possible readings of the answer's set: the listed rows, or the rows
    #     flagged true in a boolean column.
    todas = set().union(*achadas.values()) if achadas else set()
    if item.get("onde") and _filtro_pelos_valores(item, consulta, tabela, achadas, obrigatorios):
        return []
    leituras = [todas, *_booleanas(tabela, todas)]
    motivo = ""
    for linhas in leituras:
        apresentados = {k for k, ls in achadas.items() if ls & linhas}
        faltando = obrigatorios - apresentados
        a_mais = apresentados - aceitos
        if faltando or a_mais:
            motivo = motivo or (f"{consulta.nome}: faltam {sorted(consulta.linhas[k][chave] for k in faltando)}, "
                                f"sobram {sorted(consulta.linhas[k][chave] for k in a_mais)}")
            continue
        por_item = {k: achadas[k] & linhas for k in apresentados}
        falhas, _ = _valores_batem(tabela, consulta, sorted(apresentados), por_item, item.get("valores"))
        if not falhas:
            return []
        motivo = falhas[0]
    return [motivo or f"{consulta.nome}: conjunto não encontrado"]


def conferir(item: dict, consulta: Consulta, tabela: Tabela) -> list[str]:
    """PT: uma conferência do comparacao.yml / EN: one comparacao.yml check"""
    if "lista" in item:
        if item["lista"] == "ranking":
            return conferir_ranking(item, consulta, tabela)
        return conferir_conjunto(item, consulta, tabela)
    if "classificacao" in item:
        return conferir_classificacao(item, consulta, tabela)
    return conferir_valor(item, consulta, tabela)


# -----------------------------------------------------------------------------
# PT: Leituras e janelas / EN: readings and windows
# -----------------------------------------------------------------------------

def corrigir_valores(id_: str, valores, gabarito: Gabarito | None = None) -> list[dict]:
    """
    PT: Para cada leitura e janela da pergunta, se a tabela de valores bate,
        e as falhas quando não bate.
    EN: For each reading and window, whether the values table matches, and
        the failures when not.
    """
    g = gabarito or carregar_gabarito()
    tabela = Tabela.de(valores)
    resultados = []
    for leitura, blocos in g.comparacao[id_].items():
        janelas = sorted({j for b in blocos for j in (b.get("janelas") or {})}) or [""]
        for janela in janelas:
            falhas = []
            for bloco in blocos:
                consulta = Consulta.de(bloco["consulta"], g.respostas[bloco["consulta"]], g.regra)
                itens = bloco["verificar"] if "verificar" in bloco else bloco["janelas"].get(janela, [])
                for item in itens:
                    falhas += conferir(item, consulta, tabela)
            resultados.append({"leitura": leitura, "janela": janela, "bate": not falhas, "falhas": falhas})
    return resultados


def corrigir(id_: str, registro: dict, gabarito: Gabarito | None = None) -> dict:
    """
    PT: A parte por script da correção de uma execução. A situação é:

        - "errado", com o motivo: erro da execução (erro_<tipo>), resposta
          sem abstenção numa pergunta de abstenção, abstenção indevida numa
          pergunta de valor, valores que não batem com nenhuma leitura, ou
          ressalva vazia numa pergunta de valor com ressalva;
        - "certo": os valores batem e não há nada para julgar;
        - "pendente": falta o julgamento às cegas do que está em julgar
          (ressalva, abstencao, leitura_declarada).

    EN: The script part of grading one run: "errado" with a reason,
        "certo", or "pendente" with what blind grading must judge.
    """
    g = gabarito or carregar_gabarito()
    tipo = g.tipo_de_acerto(id_)
    saida = {"pergunta": id_, "tipo_de_acerto": tipo, "situacao": "errado", "motivo": "", "julgar": [],
             "leituras_que_batem": [], "falhas": []}
    if registro.get("erro"):
        saida["motivo"] = f"erro_{registro['erro']['tipo']}"
        return saida
    resposta = registro.get("resposta") or {}
    absteve = bool(str(resposta.get("abstencao") or "").strip())

    if tipo == "abstencao":
        if not absteve:
            saida["motivo"] = "sem_abstencao"
            return saida
        return {**saida, "situacao": "pendente", "julgar": ["abstencao"]}

    if absteve:
        saida["motivo"] = "abstencao_indevida"
        return saida
    resultados = corrigir_valores(id_, resposta.get("valores"), g)
    batem = [{"leitura": r["leitura"], "janela": r["janela"]} for r in resultados if r["bate"]]
    if not batem:
        saida["motivo"] = "valor"
        saida["falhas"] = [f for r in resultados for f in r["falhas"]][:10]
        return saida
    if tipo == "valor_com_ressalva" and not str(resposta.get("ressalva") or "").strip():
        return {**saida, "motivo": "sem_ressalva", "leituras_que_batem": batem}
    julgar = (["ressalva"] if tipo == "valor_com_ressalva" else []) + \
             (["leitura_declarada"] if g.precisa_de_leitura_declarada(id_) else [])
    return {**saida, "situacao": "pendente" if julgar else "certo", "julgar": julgar, "leituras_que_batem": batem}
