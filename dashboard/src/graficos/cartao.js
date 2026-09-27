/**
 * PT: O cartão de um gráfico, com o cabeçalho que o guia pede.
 *
 *     O cabeçalho tem duas partes, e só elas (decisão de 2026-09-26): o
 *     título, que diz o que o gráfico mostra, e a data-base com a fonte.
 *     Não há frase de conclusão: quem quiser uma conclusão pergunta ao chat.
 *     O cartão é uma superfície de vidro regular, como os painéis.
 *
 * EN: A chart card with the header the guide specifies: a descriptive title
 *     and the reference date with the source, never a written conclusion.
 */

import "./graficos.css";
import { elemento } from "../dom.js";

let contador = 0;

/**
 * @typedef {object} Cabecalho
 * @property {string} titulo O que o gráfico mostra / what the chart shows
 * @property {string} dataBase Já formatada, como "jul/2026" / formatted date
 * @property {string} fonte De onde vem o dado / data source
 * @property {"h2" | "h3" | "h4"} [nivel] Nível do título na página / heading level
 */

/**
 * PT: Monta o cartão. O corpo recebe o gráfico, o número de destaque ou o
 *     estado de erro.
 * EN: Builds the card; the body holds the chart, highlight or error state.
 *
 * @param {Cabecalho} cabecalho
 * @param {Node[]} corpo
 * @returns {HTMLElement}
 */
export function cartaoDeGrafico({ titulo, dataBase, fonte, nivel = "h3" }, corpo) {
  contador += 1;
  const id = `grafico-titulo-${contador}`;
  return elemento("section", { classe: "cartao-grafico", atributos: { "aria-labelledby": id } }, [
    elemento("header", { classe: "cartao-grafico__cabecalho" }, [
      elemento(nivel, { classe: "cartao-grafico__titulo", texto: titulo, atributos: { id } }),
      elemento("p", { classe: "cartao-grafico__origem", texto: `${dataBase} · ${fonte}` }),
    ]),
    elemento("div", { classe: "cartao-grafico__corpo" }, corpo),
  ]);
}

/**
 * PT: A área onde o ECharts desenha, com o rótulo acessível do gráfico.
 * EN: The drawing area, with the chart's accessible label.
 *
 * @param {string} classe Modificador de tamanho, como `grafico--mapa` / size modifier
 * @returns {HTMLDivElement}
 */
export function areaDoGrafico(classe) {
  return elemento("div", { classe: `grafico ${classe}` });
}

/**
 * PT: O estado de erro de um gráfico: diz o problema e o que continua
 *     funcionando, como o guia pede.
 * EN: A chart's error state: the problem and what still works.
 *
 * @param {string} texto
 * @returns {HTMLElement}
 */
export function erroDoGrafico(texto) {
  return elemento("p", { classe: "grafico-erro", texto, atributos: { role: "status" } });
}
