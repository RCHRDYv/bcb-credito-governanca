/**
 * PT: Testes do OKLab e da simulação de daltonismo (#63).
 *
 *     Os valores esperados vêm do validador de referência do método de
 *     visualização de dados usado no projeto, medidos na paleta oficial do
 *     Carbon durante a revisão das paletas. Se a conversão ou a matriz de
 *     simulação mudarem, estes números mudam, e o teste avisa.
 *
 * EN: OKLab and color vision deficiency simulation tests, with expected
 *     values from the reference validator.
 */

import { describe, expect, it } from "vitest";
import { diferenca, simular } from "../../src/cor/daltonismo.js";
import { oklch } from "../../src/cor/oklab.js";

describe("oklch()", () => {
  it("dá luminosidade 0 no preto e 1 no branco / black and white lightness", () => {
    expect(oklch("#000000").L).toBeCloseTo(0, 5);
    expect(oklch("#ffffff").L).toBeCloseTo(1, 3);
  });

  it("dá croma zero no cinza / zero chroma on gray", () => {
    expect(oklch("#8d8d8d").C).toBeLessThan(0.001);
  });

  it("confere a luminosidade e o croma que reprovaram a oficial do Carbon", () => {
    // PT: vermelho 90 fora da faixa e verde-azulado 70 sem croma
    expect(oklch("#520408").L).toBeCloseTo(0.28, 2);
    expect(oklch("#005d5d").C).toBeCloseTo(0.074, 3);
  });
});

describe("diferenca()", () => {
  it("é zero entre uma cor e ela mesma / zero for identical colors", () => {
    expect(diferenca("#6929c4", "#6929c4")).toBe(0);
    expect(diferenca("#6929c4", "#6929c4", "deuteranopia")).toBe(0);
  });

  it("reproduz o pior par da oficial do Carbon na deuteranopia: 6,3", () => {
    expect(diferenca("#005d5d", "#9f1853", "deuteranopia")).toBeCloseTo(6.3, 1);
  });

  it("reproduz a distância sem daltonismo entre magenta 70 e vermelho 50: 21,6", () => {
    expect(diferenca("#9f1853", "#fa4d56")).toBeCloseTo(21.6, 1);
  });
});

describe("simular()", () => {
  it("mantém preto e branco / keeps black and white", () => {
    for (const tipo of /** @type {const} */ (["protanopia", "deuteranopia", "tritanopia"])) {
      expect(simular("#000000", tipo)).toBe("#000000");
      expect(simular("#ffffff", tipo)).toBe("#ffffff");
    }
  });

  it("aproxima vermelho e verde na deuteranopia / red and green converge", () => {
    const normal = diferenca("#da1e28", "#24a148");
    const simulada = diferenca("#da1e28", "#24a148", "deuteranopia");
    expect(simulada).toBeLessThan(normal / 2);
  });
});
