/**
 * PT: As cores da Tela 2 (#70): quanto a inadimplência da UF subiu a mais
 *     que a do país, em cinco faixas da rampa roxa, com o roxo mais forte na
 *     piora maior (ADR 0021, revisto em 2026-10-05; revisão do mockup da
 *     Tela 2, em 2026-10-06).
 *
 *     As faixas param em 0,1 e 0,5 ponto percentual, as mesmas marcas da
 *     escala de desvio do catálogo. A escala vai de melhor que o país, à
 *     esquerda, a pior que o país, à direita.
 *
 * EN: Screen 2 colors: the state's delinquency change minus the country's,
 *     in five purple bands, darkest for the largest worsening, from better
 *     than the country on the left to worse on the right.
 */

import { pontos } from "../../formatos.js";
import { classesEmCincoFaixas } from "../../graficos/escalas.js";
import { legendaEmEscala } from "../../graficos/legenda.js";
import { t } from "../../textos/index.js";

/** @typedef {import("../../graficos/escalas.js").Classes} Classes */
/** @typedef {import("../../graficos/escalas.js").Classe} Classe */

/**
 * PT: Até 0,1 p.p. de diferença é "perto do país"; a classe forte de cada
 *     lado começa em 0,5 p.p. Em fração, como no mart.
 * EN: Up to 0.1 p.p. is "near the country"; strong classes start at 0.5 p.p.
 */
export const LIMITES_DO_PAIS = /** @type {[number, number]} */ ([0.001, 0.005]);

/**
 * PT: Uma diferença em pontos percentuais, sem sinal e com uma casa: "0,1 p.p.".
 * EN: An unsigned difference in percentage points, one decimal.
 *
 * @param {number} fracao
 * @returns {string}
 */
function semSinal(fracao) {
  return pontos(Math.abs(fracao), 1);
}

/**
 * PT: As classes do território e da matriz, com os rótulos de sentido.
 * EN: Territory and heatmap classes, with meaning labels.
 *
 * @returns {Classes}
 */
export function classesDoRisco() {
  const [a, b] = LIMITES_DO_PAIS;
  return classesEmCincoFaixas(LIMITES_DO_PAIS, {
    forteAbaixo: t("tela2.legenda-forte-abaixo", { b: semSinal(b) }),
    abaixo: t("tela2.legenda-abaixo", { a: semSinal(a), b: semSinal(b) }),
    meio: t("tela2.legenda-meio", { a: semSinal(a) }),
    acima: t("tela2.legenda-acima", { a: semSinal(a), b: semSinal(b) }),
    forteAcima: t("tela2.legenda-forte-acima", { b: semSinal(b) }),
  });
}

/**
 * PT: As divisas das faixas, da esquerda para a direita: "−0,5", "−0,1",
 *     "+0,1" e "+0,5", em pontos percentuais.
 * EN: The band boundaries, left to right, in percentage points.
 *
 * @returns {string[]}
 */
export function marcasDaEscala() {
  const [a, b] = LIMITES_DO_PAIS;
  const divisa = (/** @type {number} */ v) => pontos(v, 1).replace(" p.p.", "");
  return [divisa(-b), divisa(-a), divisa(a), divisa(b)];
}

/**
 * PT: A legenda do território e da matriz: a escala em degradê, de melhor
 *     que o país, à esquerda, a pior, à direita, e o marcador de alerta
 *     antecipado quando o desenho o usa. As classes chegam da mais forte
 *     para a mais fraca, e a escala as inverte.
 * EN: The territory and heatmap legend: the gradient scale from better than
 *     the country on the left to worse on the right, plus the early-warning
 *     marker item when the drawing uses it.
 *
 * @param {{ comMarca: boolean }} opcoes
 * @returns {(classes: Classe[], rotuloSemValor?: string) => HTMLElement}
 */
export function legendaDoRisco({ comMarca }) {
  return (classes, rotuloSemValor) =>
    legendaEmEscala({
      classes: [...classes].reverse(),
      marcas: marcasDaEscala(),
      extremos: [t("tela2.escala-melhor"), t("tela2.escala-pior")],
      titulo: t("tela2.escala-titulo"),
      rotuloSemValor,
      rotuloDaMarca: comMarca ? t("alerta-antecipado.nome") : undefined,
    });
}
