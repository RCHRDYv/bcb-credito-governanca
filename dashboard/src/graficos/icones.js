/**
 * PT: Os ícones dos quadrantes, desenhados em SVG pelo DOM.
 *
 *     O guia pede que o quadrante nunca apareça só pela cor: cada um tem um
 *     ícone e o nome. Entrar é uma seta para cima e para a direita, Observar
 *     é um olho, Não entrar é o sinal de proibido e Manter é o sinal de
 *     igual. Os traços usam `currentColor`, então o ícone herda a cor do
 *     texto de quem o contém. A etiqueta de quadrante da #64 usa os mesmos.
 *
 * EN: Quadrant icons, built as DOM SVG. Strokes use `currentColor`.
 */

const SVG = "http://www.w3.org/2000/svg";

/** @typedef {"entrar" | "observar" | "nao-entrar" | "manter"} Quadrante */

/**
 * PT: Os traços de cada ícone, numa grade de 24 por 24.
 * EN: Each icon's strokes, on a 24 by 24 grid.
 *
 * @type {Record<Quadrante, string[]>}
 */
const TRACOS = {
  entrar: ["M7 17 17 7", "M9 7h8v8"],
  observar: [
    "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z",
    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z",
  ],
  "nao-entrar": ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z", "m5.6 5.6 12.8 12.8"],
  manter: ["M5 9h14", "M5 15h14"],
};

/**
 * PT: O ícone de um quadrante, decorativo: o nome ao lado é que é lido.
 * EN: A quadrant's icon, decorative; the adjacent name is what gets read.
 *
 * @param {Quadrante} quadrante
 * @returns {SVGSVGElement}
 */
export function iconeDoQuadrante(quadrante) {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  svg.setAttribute("class", "icone");
  for (const d of TRACOS[quadrante]) {
    const traco = document.createElementNS(SVG, "path");
    traco.setAttribute("d", d);
    svg.append(traco);
  }
  return svg;
}
