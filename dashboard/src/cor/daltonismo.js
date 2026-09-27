/**
 * PT: Simulação de daltonismo e distância percebida entre duas cores.
 *
 *     Usa as matrizes de Machado, Oliveira e Fernandes (2009) com severidade
 *     1,0, isto é, a forma completa de cada tipo: protanopia (sem o cone do
 *     vermelho), deuteranopia (sem o do verde) e tritanopia (sem o do azul).
 *     A matriz se aplica à cor em RGB linear, e a distância é medida em
 *     OKLab, multiplicada por 100.
 *
 *     Os limites da validação (alvo 8, piso 6) foram calibrados com este
 *     modelo de simulação. Trocar o modelo muda os pares no limite, então o
 *     modelo faz parte do critério, e não é detalhe de implementação.
 *
 * EN: Color vision deficiency simulation (Machado, Oliveira and Fernandes,
 *     2009, severity 1.0) and perceived distance in OKLab x100. The
 *     validation thresholds are calibrated to this model.
 *
 *     Fonte / source: G. M. Machado, M. M. Oliveira e L. A. F. Fernandes,
 *     "A Physiologically-based Model for Simulation of Color Vision
 *     Deficiency", IEEE TVCG 15(6), 2009.
 *     https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html
 */

import { linear } from "./contraste.js";
import { distancia, oklabDeLinear } from "./oklab.js";

/** @typedef {import("./oklab.js").Trio} Trio */
/** @typedef {"protanopia" | "deuteranopia" | "tritanopia"} TipoDeDaltonismo */

/** @type {TipoDeDaltonismo[]} */
export const TIPOS = ["protanopia", "deuteranopia", "tritanopia"];

/**
 * PT: As matrizes de severidade 1,0 da tabela do artigo, em RGB linear.
 * EN: Severity 1.0 matrices from the paper, in linear RGB.
 *
 * @type {Record<TipoDeDaltonismo, [Trio, Trio, Trio]>}
 */
const MATRIZES = {
  protanopia: [
    [0.152286, 1.052583, -0.204868],
    [0.114503, 0.786281, 0.099216],
    [-0.003882, -0.048116, 1.051998],
  ],
  deuteranopia: [
    [0.367322, 0.860646, -0.227968],
    [0.280085, 0.672501, 0.047413],
    [-0.01182, 0.04294, 0.968881],
  ],
  tritanopia: [
    [1.255528, -0.076749, -0.178779],
    [-0.078411, 0.930809, 0.147602],
    [0.004733, 0.691367, 0.3039],
  ],
};

/**
 * PT: A cor como uma pessoa com o tipo de daltonismo a vê, em RGB linear.
 *     O resultado é limitado a 0 e 1, porque a matriz pode sair do gamut.
 * EN: The color as seen with the given deficiency, in linear RGB, clamped.
 *
 * @param {string} hex
 * @param {TipoDeDaltonismo} tipo
 * @returns {Trio}
 */
export function simularLinear(hex, tipo) {
  const [r, g, b] = linear(hex);
  const limitar = (/** @type {number} */ c) => Math.min(1, Math.max(0, c));
  return /** @type {Trio} */ (
    MATRIZES[tipo].map(([mr, mg, mb]) => limitar(mr * r + mg * g + mb * b))
  );
}

/**
 * PT: A cor simulada em `#rrggbb`, para mostrar na tela.
 * EN: The simulated color as `#rrggbb`, for display.
 *
 * @param {string} hex
 * @param {TipoDeDaltonismo} tipo
 * @returns {string}
 */
export function simular(hex, tipo) {
  const paraSrgb = (/** @type {number} */ c) =>
    c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055;
  const canais = simularLinear(hex, tipo).map((c) =>
    Math.round(paraSrgb(c) * 255)
      .toString(16)
      .padStart(2, "0"),
  );
  return `#${canais.join("")}`;
}

/**
 * PT: Distância percebida entre duas cores, em OKLab x100. Sem o tipo, é a
 *     visão sem daltonismo; com o tipo, as duas cores são simuladas antes.
 * EN: Perceived distance in OKLab x100, with or without simulation.
 *
 * @param {string} hexA
 * @param {string} hexB
 * @param {TipoDeDaltonismo} [tipo]
 * @returns {number}
 */
export function diferenca(hexA, hexB, tipo) {
  const lab = (/** @type {string} */ hex) =>
    oklabDeLinear(tipo ? simularLinear(hex, tipo) : linear(hex));
  return distancia(lab(hexA), lab(hexB));
}
