/**
 * PT: Contraste dos tokens de cor, nos dois temas (ADR 0018, decisão 5).
 *
 *     Cada par diz qual cor fica na frente, sobre qual fundo, e o mínimo da
 *     WCAG 2.2: 4,5:1 para texto e 3:1 para elemento gráfico, como borda,
 *     marca de quadrante e anel de foco. O vidro é transparente, então o
 *     texto sobre ele é medido contra o vidro composto sobre o fundo da
 *     página. As cores vêm do `tokens.json` gerado, e nunca de um valor
 *     digitado no teste.
 *
 * EN: Contrast of the color tokens in both themes. Each pair states the
 *     foreground, the background and the WCAG 2.2 minimum; text on glass is
 *     measured against the glass composited over the page background.
 */

import { describe, expect, it } from "vitest";
import { compor, luminancia, razaoDeContraste } from "../../src/cor/contraste.js";
import { cor as corDoToken } from "../../src/tokens.js";

/** @typedef {import("../../src/tokens.js").Tema} Tema */

const TEXTO = 4.5;
const GRAFICO = 3;

/**
 * PT: A cor opaca de um token num tema. Se ela for transparente, é composta
 *     sobre o fundo informado.
 * EN: A token's opaque color in a theme, composited when transparent.
 *
 * @param {string} caminho
 * @param {Tema} tema
 * @param {string} [sobre] Fundo opaco, para cor transparente / opaque background
 * @returns {string}
 */
function cor(caminho, tema, sobre) {
  const valor = corDoToken(caminho, tema);
  return valor.alpha < 1 && sobre ? compor(valor, sobre) : valor.hex;
}

/**
 * PT: O fundo onde o par é medido: a página, a camada sólida ou um vidro
 *     composto sobre a página.
 * EN: The background a pair is measured on.
 *
 * @param {string} fundo
 * @param {Tema} tema
 * @returns {string}
 */
function fundoOpaco(fundo, tema) {
  const pagina = cor("color.background.page", tema);
  return fundo.startsWith("material.") ? cor(fundo, tema, pagina) : cor(fundo, tema);
}

/** @type {[string, string, number][]} */
const PARES = [
  // PT: texto sobre a página, a camada e o vidro regular / EN: text on page, layer and glass
  ...[
    "color.text.primary",
    "color.text.secondary",
    "color.text.helper",
    "color.link.default",
  ].flatMap(
    (texto) =>
      /** @type {[string, string, number][]} */ ([
        [texto, "color.background.page", TEXTO],
        [texto, "color.background.layer", TEXTO],
        [texto, "material.vidro.regular.preenchimento", TEXTO],
      ]),
  ),
  ["color.text.primary", "material.vidro.claro.preenchimento", TEXTO],
  ["color.text.on-color", "color.background.brand.default", TEXTO],
  ["color.support.info", "color.background.page", TEXTO],
  ["color.support.error", "color.background.page", TEXTO],
  ["color.alerta-antecipado.texto", "color.alerta-antecipado.fundo", TEXTO],
  // PT: quadrantes: marca como gráfico, texto como texto / EN: quadrants
  ...["entrar", "observar", "nao-entrar", "manter"].flatMap(
    (quadrante) =>
      /** @type {[string, string, number][]} */ ([
        [`color.quadrante.${quadrante}.marca`, "color.background.page", GRAFICO],
        [`color.quadrante.${quadrante}.texto`, "color.background.page", TEXTO],
        [`color.quadrante.${quadrante}.texto`, "color.background.layer", TEXTO],
      ]),
  ),
  // PT: elementos gráficos / EN: graphical elements
  ["color.border.strong", "color.background.page", GRAFICO],
  ["color.interactive", "color.background.page", GRAFICO],
  ["color.focus", "color.background.page", GRAFICO],
  ["color.support.success", "color.background.page", GRAFICO],
];

describe("contraste.js", () => {
  it("dá 21:1 entre preto e branco / gives 21:1 for black and white", () => {
    expect(razaoDeContraste("#000000", "#ffffff")).toBeCloseTo(21, 5);
  });

  it("confere o valor do guia para o texto de ajuda / matches the guide's helper text value", () => {
    // PT: o guia registra 4,57:1 para #6f6f6f sobre #f4f4f4
    expect(razaoDeContraste("#6f6f6f", "#f4f4f4")).toBeCloseTo(4.57, 2);
  });

  it("compõe o vidro regular do guia sobre o fundo / composites the guide's regular glass", () => {
    // PT: o guia registra #fbfbfb para o branco a 62% sobre #f4f4f4
    expect(compor({ hex: "#ffffff", alpha: 0.62 }, "#f4f4f4")).toBe("#fbfbfb");
  });

  it("tem luminância 0 no preto e 1 no branco / has luminance 0 and 1", () => {
    expect(luminancia("#000000")).toBe(0);
    expect(luminancia("#ffffff")).toBe(1);
  });
});

for (const tema of /** @type {Tema[]} */ (["claro", "escuro"])) {
  describe(`tokens no tema ${tema}`, () => {
    it.each(PARES)("%s sobre %s passa de %d:1", (frente, fundo, minimo) => {
      const base = fundoOpaco(fundo, tema);
      const razao = razaoDeContraste(cor(frente, tema, base), base);
      expect(razao).toBeGreaterThanOrEqual(minimo);
    });
  });
}
