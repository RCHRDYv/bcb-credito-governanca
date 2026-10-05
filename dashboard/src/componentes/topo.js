/**
 * PT: A barra de topo, comum a todas as páginas: o nome do produto, a
 *     navegação entre as visões (RF-G01), quando a página tem visões, e o
 *     controle de tema.
 *
 * EN: The shared top bar: product name, view navigation when the page has
 *     views, and the theme control.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { controleDeTema } from "./controle-de-tema.js";

/**
 * PT: Monta a barra de topo. O catálogo do design system não tem visões, e
 *     monta a barra sem navegação.
 * EN: Builds the top bar; the catalog has no views and passes none.
 *
 * @param {object} [opcoes]
 * @param {HTMLElement} [opcoes.navegacao] A navegação entre as visões / view navigation
 * @returns {HTMLElement}
 */
export function topo({ navegacao } = {}) {
  return elemento("header", { classe: "topo" }, [
    elemento("div", { classe: "topo__conteudo" }, [
      elemento("p", { classe: "topo__nome", texto: t("produto.nome") }),
      ...(navegacao ? [navegacao] : []),
      controleDeTema(),
    ]),
  ]);
}
