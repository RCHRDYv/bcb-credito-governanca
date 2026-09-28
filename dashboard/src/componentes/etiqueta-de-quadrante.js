/**
 * PT: Etiqueta de quadrante: cápsula com o ponto na cor do quadrante, o
 *     ícone e o nome, no tom de texto da mesma cor (ADR 0014).
 *
 *     - Entrar: seta para cima e para a direita;
 *     - Observar: olho;
 *     - Não entrar: sinal de proibido;
 *     - Manter: sinal de igual.
 *
 *     O quadrante nunca aparece só pela cor: o nome vai sempre junto do
 *     ícone. As cores dos quadrantes não aparecem com outro significado na
 *     mesma tela. A matriz da #63 usa esta etiqueta nos cantos.
 *
 * EN: Quadrant tag: dot, icon and name, never color alone.
 */

import { elemento } from "../dom.js";
import { t } from "../textos/index.js";
import { icone } from "./icones.js";

/** @typedef {"entrar" | "observar" | "nao-entrar" | "manter"} Quadrante */
/** @typedef {import("../textos/index.js").ChaveDeTexto} ChaveDeTexto */

/**
 * PT: Ícone e chave do nome de cada quadrante.
 * EN: Each quadrant's icon and name key.
 *
 * @type {Record<Quadrante, { icone: import("./icones.js").NomeDoIcone, nome: ChaveDeTexto }>}
 */
const QUADRANTES = {
  entrar: { icone: "arrow-up-right", nome: "quadrante.entrar" },
  observar: { icone: "eye", nome: "quadrante.observar" },
  "nao-entrar": { icone: "ban", nome: "quadrante.nao-entrar" },
  manter: { icone: "equal", nome: "quadrante.manter" },
};

/**
 * PT: O quadrante como o mart o escreve ("não entrar") vira a chave usada
 *     no código e nas classes ("nao-entrar").
 * EN: Converts the mart's spelling to the code key.
 *
 * @param {string} doMart
 * @returns {Quadrante}
 */
export function quadranteDoMart(doMart) {
  const chave = doMart
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/\s+/g, "-");
  if (!Object.hasOwn(QUADRANTES, chave)) {
    throw new Error(`Quadrante desconhecido: ${doMart}`);
  }
  return /** @type {Quadrante} */ (chave);
}

/**
 * PT: O nome do quadrante, no arquivo de tradução.
 * EN: The quadrant's name.
 *
 * @param {Quadrante} quadrante
 * @returns {string}
 */
export function nomeDoQuadrante(quadrante) {
  return t(QUADRANTES[quadrante].nome);
}

/**
 * PT: Monta a etiqueta.
 * EN: Builds the tag.
 *
 * @param {Quadrante} quadrante
 * @returns {HTMLSpanElement}
 */
export function etiquetaDeQuadrante(quadrante) {
  return elemento("span", { classe: `etiqueta etiqueta--${quadrante}` }, [
    elemento("span", { classe: "etiqueta__ponto", atributos: { "aria-hidden": "true" } }),
    icone(QUADRANTES[quadrante].icone),
    elemento("span", { texto: nomeDoQuadrante(quadrante) }),
  ]);
}
