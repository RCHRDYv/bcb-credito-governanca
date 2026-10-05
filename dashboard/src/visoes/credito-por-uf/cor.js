/**
 * PT: A cor e as frases de posição da Tela 1.
 *
 *     A cor mostra a distância de cada UF até a mediana das UFs, em cinco
 *     faixas da rampa roxa, e a legenda diz o que cada faixa significa pela
 *     regra do ADR 0014: quanto mais abaixo da mediana, mais espaço para
 *     crescer e mais forte o roxo (revisões da Tela 1, em 2026-10-01 e
 *     2026-10-05). O mapa, a grade e a matriz usam as mesmas classes, para
 *     se lerem igual.
 *
 * EN: Screen 1 color and position phrases: distance to the median in five
 *     purple bands, strongest where there is most room under ADR 0014. Map,
 *     grid and heatmap share the classes.
 */

import { numero } from "../../formatos.js";
import { classesEmCincoFaixas } from "../../graficos/escalas.js";
import { legendaEmEscala } from "../../graficos/legenda.js";
import { t } from "../../textos/index.js";

/** @typedef {import("../../graficos/escalas.js").Classes} Classes */
/** @typedef {import("../../graficos/escalas.js").Classe} Classe */

/**
 * PT: Até 10% de diferença é "perto da mediana"; a classe forte de cada
 *     lado começa em 30%.
 * EN: Up to 10% is "near the median"; the strong class starts at 30%.
 */
export const LIMITES_DA_MEDIANA = /** @type {[number, number]} */ ([0.1, 0.3]);

/**
 * PT: Uma fração como porcentagem inteira, sem sinal.
 * EN: A fraction as a whole percentage, unsigned.
 *
 * @param {number} fracao
 * @returns {string}
 */
function porcento(fracao) {
  return `${numero(Math.abs(fracao) * 100, 0)}%`;
}

/**
 * PT: As classes do território e da matriz, com os rótulos de sentido.
 * EN: Territory and heatmap classes, with meaning labels.
 *
 * @returns {Classes}
 */
export function classesDeEspaco() {
  const [a, b] = LIMITES_DA_MEDIANA;
  return classesEmCincoFaixas(
    LIMITES_DA_MEDIANA,
    {
      forteAbaixo: t("tela1.legenda-forte-abaixo", { b: porcento(b) }),
      abaixo: t("tela1.legenda-abaixo", { a: porcento(a), b: porcento(b) }),
      meio: t("tela1.legenda-meio", { a: porcento(a) }),
      acima: t("tela1.legenda-acima", { a: porcento(a), b: porcento(b) }),
      forteAcima: t("tela1.legenda-forte-acima", { b: porcento(b) }),
    },
    { maisForteAbaixo: true },
  );
}

/**
 * PT: As divisas das faixas, como a escala as marca, da esquerda para a
 *     direita: "+30%", "+10%", "−10%" e "−30%" em relação à mediana. A
 *     escala vai de menos espaço, à esquerda, a mais espaço, à direita,
 *     porque cresce para a direita o que importa à pergunta da tela
 *     (revisão de 2026-10-05).
 * EN: The band boundaries as the scale marks them, left to right, from less
 *     room on the left to more room on the right.
 *
 * @returns {string[]}
 */
export function marcasDaEscala() {
  const [a, b] = LIMITES_DA_MEDIANA;
  return [`+${porcento(b)}`, `+${porcento(a)}`, `−${porcento(a)}`, `−${porcento(b)}`];
}

/**
 * PT: A legenda do território e da matriz: a escala em degradê, com as
 *     divisas em porcentagem e o sentido de cada ponta, de menos espaço, à
 *     esquerda, a mais espaço, à direita. As classes chegam na ordem da
 *     mais abaixo da mediana para a mais acima, e a escala as inverte.
 * EN: The territory and heatmap legend: the gradient scale from less room
 *     on the left to more room on the right; classes arrive from most below
 *     the median to most above, and the scale reverses them.
 *
 * @param {Classe[]} classes
 * @param {string} [rotuloSemValor]
 * @returns {HTMLElement}
 */
export function legendaDeEspaco(classes, rotuloSemValor) {
  return legendaEmEscala({
    classes: [...classes].reverse(),
    marcas: marcasDaEscala(),
    extremos: [t("tela1.escala-menos-espaco"), t("tela1.escala-mais-espaco")],
    titulo: t("tela1.escala-titulo"),
    rotuloSemValor,
  });
}

/**
 * PT: O valor que pinta a célula: a distância até a mediana, em fração.
 * EN: The value that colors a cell: distance to the median, as a fraction.
 *
 * @param {number} indice Carteira por empresa sobre a mediana / room index
 * @returns {number}
 */
export function distancia(indice) {
  return indice - 1;
}

/**
 * PT: A posição em relação à mediana, numa frase curta: "31% abaixo da
 *     mediana", "12% acima da mediana" ou "na mediana".
 * EN: The position against the median, in a short phrase.
 *
 * @param {number} indice
 * @returns {string}
 */
export function posicao(indice) {
  const valor = porcento(distancia(indice));
  if (Math.abs(distancia(indice)) < 0.005) return t("tela1.na-mediana");
  return indice < 1
    ? t("tela1.abaixo-da-mediana-em", { valor })
    : t("tela1.acima-da-mediana-em", { valor });
}
