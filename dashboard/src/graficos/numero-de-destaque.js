/**
 * PT: Número de destaque: um número só, grande, com o que ele mede.
 *
 *     Quando a resposta é um número, um gráfico só atrapalha. O número vai
 *     no `heading-07` do Carbon, com algarismos tabulares, e o rótulo diz o
 *     que ele é, numa frase que uma pessoa diria. Não usa o ECharts: é HTML,
 *     lido por qualquer leitor de tela como texto.
 *
 * EN: Highlight number: one large number and what it measures, as plain
 *     HTML rather than a chart.
 */

import { elemento } from "../dom.js";

/**
 * @typedef {object} Destaque
 * @property {string} valor Já formatado, como "R$ 485,5 bi" / formatted value
 * @property {string} rotulo O que o número mede / what it measures
 */

/**
 * PT: Monta o número de destaque.
 * EN: Builds the highlight number.
 *
 * @param {Destaque} destaque
 * @returns {HTMLElement}
 */
export function numeroDeDestaque({ valor, rotulo }) {
  return elemento("div", { classe: "destaque" }, [
    elemento("p", { classe: "destaque__numero", texto: valor }),
    elemento("p", { classe: "destaque__rotulo", texto: rotulo }),
  ]);
}
