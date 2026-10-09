"""
PT: As faixas de tolerância do pré-registro (evaluation/hipoteses.yml,
    comparacao.tolerancia), que lá estão escritas por extenso. A classe de
    cada coluna sai de scripts.validar_registro.classe_de_tolerancia; a
    largura da faixa, daqui. O QA do esquema estrela usa as mesmas faixas.

    relativa: 1% do valor do gabarito.
    pontos: 0,1 p.p. ou 10% do valor, o que for menor.
    adimensional: 0,01 ou 1% do valor, o que for maior.
    exata: igualdade.

    Na zona de indiferença de um limiar (comparacao.limiar), as colunas _pct
    e _pp têm piso de 0,01 ponto percentual.

EN: The pre-registered tolerance bands, written out in prose in
    hipoteses.yml. Column classes come from classe_de_tolerancia; band widths
    from here. The star schema QA uses the same bands.
"""

from __future__ import annotations

from decimal import Decimal

RELATIVA = Decimal("0.01")
PONTOS_ABSOLUTO = Decimal("0.1")
PONTOS_RELATIVO = Decimal("0.1")
ADIMENSIONAL_ABSOLUTO = Decimal("0.01")
ADIMENSIONAL_RELATIVO = Decimal("0.01")
PISO_DA_ZONA_EM_PONTOS = Decimal("0.01")

CLASSES_NUMERICAS = ("relativa", "pontos", "adimensional", "exata")


def banda(classe: str, esperado: Decimal) -> Decimal:
    """
    PT: A diferença absoluta aceita em torno do valor do gabarito.
    EN: The absolute difference accepted around the key's value.
    """
    if classe == "exata":
        return Decimal(0)
    if classe == "pontos":
        return min(PONTOS_ABSOLUTO, PONTOS_RELATIVO * abs(esperado))
    if classe == "adimensional":
        return max(ADIMENSIONAL_ABSOLUTO, ADIMENSIONAL_RELATIVO * abs(esperado))
    return RELATIVA * abs(esperado)


def banda_da_zona(classe: str, valor: Decimal) -> Decimal:
    """
    PT: A meia-largura da zona de indiferença em torno de um limiar, para um
        valor do gabarito: a banda da coluna, com o piso de 0,01 p.p. nas
        colunas em pontos.
    EN: Half-width of the indifference zone around a threshold: the column's
        band, floored at 0.01 p.p. for point columns.
    """
    if classe == "pontos":
        return max(banda(classe, valor), PISO_DA_ZONA_EM_PONTOS)
    return banda(classe, valor)


def dentro_da_banda(classe: str, obtido: Decimal, esperado: Decimal) -> bool:
    """PT: o número dentro da banda / EN: number within the band"""
    return abs(obtido - esperado) <= banda(classe, esperado)
