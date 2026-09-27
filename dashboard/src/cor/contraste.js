/**
 * PT: Contraste de cor pela WCAG 2.2.
 *
 *     A razão de contraste compara a luminância relativa de duas cores
 *     opacas. Uma cor transparente, como o preenchimento do vidro, precisa
 *     antes ser composta sobre o que está atrás dela: é a cor que o olho vê.
 *     O teste de contraste dos tokens e o catálogo usam estas funções, e o
 *     tema dos gráficos da #63 vai usar também.
 *
 * EN: Color contrast per WCAG 2.2. A transparent color, such as the glass
 *     fill, is first composited over what is behind it. Used by the token
 *     contrast test, the catalog and, later, the chart theme.
 */

/**
 * @typedef {object} Cor
 * @property {string} hex Cor em `#rrggbb` / color as `#rrggbb`
 * @property {number} alpha Opacidade de 0 a 1 / opacity from 0 to 1
 */

/**
 * PT: Os três canais de `#rrggbb`, de 0 a 255.
 * EN: The three channels of `#rrggbb`, from 0 to 255.
 *
 * @param {string} hex
 * @returns {[number, number, number]}
 */
function canais(hex) {
  const limpo = hex.replace("#", "");
  if (!/^[0-9a-f]{6}$/i.test(limpo)) {
    throw new Error(`Cor fora do formato #rrggbb: ${hex}`);
  }
  return /** @type {[number, number, number]} */ (
    [0, 2, 4].map((i) => Number.parseInt(limpo.slice(i, i + 2), 16))
  );
}

/**
 * PT: Luminância relativa, pela fórmula da WCAG.
 * EN: Relative luminance, per the WCAG formula.
 *
 * @param {string} hex
 * @returns {number}
 */
export function luminancia(hex) {
  const [r, g, b] = canais(hex).map((canal) => {
    const c = canal / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * PT: Razão de contraste entre duas cores opacas, de 1 a 21.
 * EN: Contrast ratio between two opaque colors, from 1 to 21.
 *
 * @param {string} hexA
 * @param {string} hexB
 * @returns {number}
 */
export function razaoDeContraste(hexA, hexB) {
  const [clara, escura] = [luminancia(hexA), luminancia(hexB)].sort((a, b) => b - a);
  return (clara + 0.05) / (escura + 0.05);
}

/**
 * PT: A cor que se vê quando uma cor transparente está sobre um fundo opaco.
 * EN: The color seen when a transparent color sits on an opaque background.
 *
 * @param {Cor} frente
 * @param {string} fundoHex
 * @returns {string}
 */
export function compor(frente, fundoHex) {
  const f = canais(frente.hex);
  const b = canais(fundoHex);
  const mistura = f.map((canal, i) => Math.round(canal * frente.alpha + b[i] * (1 - frente.alpha)));
  return `#${mistura.map((canal) => canal.toString(16).padStart(2, "0")).join("")}`;
}
