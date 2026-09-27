/**
 * PT: A legenda das classes de cor de um mapa ou cartograma, em HTML.
 *
 *     A legenda fica fora do SVG do ECharts por três motivos: quebra linha
 *     sozinha em tela estreita, é lida como texto por leitor de tela, e pinta
 *     cada amostra pela variável CSS do token, que já segue o tema do lugar
 *     onde a legenda está, sem precisar redesenhar nada.
 *
 * EN: HTML legend for a map's color classes: wraps on narrow screens, reads
 *     as text, and paints swatches with the token CSS variable.
 */

import { elemento } from "../dom.js";

/** @typedef {import("./escalas.js").Classe} Classe */

/**
 * PT: Monta a legenda, da classe mais alta para a mais baixa.
 * EN: Builds the legend, highest class first.
 *
 * @param {Classe[]} classes
 * @returns {HTMLUListElement}
 */
export function legendaDeClasses(classes) {
  return elemento(
    "ul",
    { classe: "legenda" },
    classes.map((classe) => {
      const amostra = elemento("span", {
        classe: "legenda__cor",
        atributos: { "aria-hidden": "true" },
      });
      amostra.style.setProperty("background-color", `var(${classe.variavel})`);
      return elemento("li", { classe: "legenda__item" }, [amostra, classe.label]);
    }),
  );
}
