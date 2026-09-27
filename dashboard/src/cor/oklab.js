/**
 * PT: Cor no espaço OKLab e na forma polar dele, o OKLCH.
 *
 *     O OKLab foi desenhado para que a distância entre duas cores acompanhe
 *     a diferença que o olho percebe. Por isso a validação das paletas mede
 *     luminosidade, croma e distância nele, e não em RGB. As matrizes são as
 *     publicadas por Björn Ottosson, autor do espaço.
 *
 * EN: Color in OKLab and its polar form, OKLCH. OKLab distances track
 *     perceived difference, so palette checks measure lightness, chroma and
 *     distance here. Matrices as published by Björn Ottosson.
 *
 *     Fonte / source: https://bottosson.github.io/posts/oklab/
 */

import { linear } from "./contraste.js";

/** @typedef {[number, number, number]} Trio */

/**
 * @typedef {object} Oklch
 * @property {number} L Luminosidade, de 0 a 1 / lightness, 0 to 1
 * @property {number} C Croma: 0 é cinza / chroma, 0 is gray
 * @property {number} h Matiz em graus / hue in degrees
 */

/**
 * PT: RGB linear para OKLab.
 * EN: Linear RGB to OKLab.
 *
 * @param {Trio} rgbLinear
 * @returns {Trio} `[L, a, b]`
 */
export function oklabDeLinear([r, g, b]) {
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

/**
 * PT: A cor `#rrggbb` em OKLab.
 * EN: A `#rrggbb` color in OKLab.
 *
 * @param {string} hex
 * @returns {Trio}
 */
export function oklab(hex) {
  return oklabDeLinear(linear(hex));
}

/**
 * PT: A cor `#rrggbb` em OKLCH: luminosidade, croma e matiz.
 * EN: A `#rrggbb` color in OKLCH.
 *
 * @param {string} hex
 * @returns {Oklch}
 */
export function oklch(hex) {
  const [L, a, b] = oklab(hex);
  const h = (((Math.atan2(b, a) * 180) / Math.PI) % 360) + 360;
  return { L, C: Math.hypot(a, b), h: h % 360 };
}

/**
 * PT: Distância entre duas cores em OKLab, multiplicada por 100, que é a
 *     escala em que os limites da validação são escritos.
 * EN: Distance between two OKLab colors, times 100.
 *
 * @param {Trio} a
 * @param {Trio} b
 * @returns {number}
 */
export function distancia(a, b) {
  return 100 * Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}
