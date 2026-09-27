/**
 * PT: A barra de topo, comum a todas as páginas: o nome do produto e o
 *     controle de tema. A navegação entre as visões (RF-G01) entra aqui
 *     quando as visões chegarem.
 *
 * EN: The shared top bar: product name and theme control.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { controleDeTema } from "./controle-de-tema.js";

/**
 * PT: Monta a barra de topo.
 * EN: Builds the top bar.
 *
 * @returns {HTMLElement}
 */
export function topo() {
  return elemento("header", { classe: "topo" }, [
    elemento("div", { classe: "topo__conteudo" }, [
      elemento("p", { classe: "topo__nome", texto: t("produto.nome") }),
      controleDeTema(),
    ]),
  ]);
}
