/**
 * PT: Testes das classes de cor dos mapas e do cartograma (#63).
 * EN: Tests for map and cartogram color classes.
 */

import { describe, expect, it } from "vitest";
import {
  classeDoValor,
  classesDivergentes,
  classesSequenciais,
  quantis,
} from "../../src/graficos/escalas.js";
import { paletas } from "../../src/graficos/tema.js";

const formatar = (/** @type {number} */ v) => String(v);

describe("quantis()", () => {
  it("divide dez valores em cinco classes de dois / quintiles of ten values", () => {
    expect(quantis([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])).toEqual([3, 5, 6, 8]);
  });

  it("ignora valores que não são números / ignores non-numbers", () => {
    expect(quantis([Number.NaN, 1, 2, 3, 4, 5])).toHaveLength(4);
  });
});

describe("classesSequenciais()", () => {
  const classes = classesSequenciais([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], formatar)("claro");

  it("tem cinco classes, da mais alta para a mais baixa / five classes, highest first", () => {
    expect(classes).toHaveLength(5);
    expect(classes[0].color).toBe(paletas("claro").sequencial[4]);
    expect(classes[4].color).toBe(paletas("claro").sequencial[0]);
  });

  it("põe cada valor em exatamente uma classe / each value in one class", () => {
    for (let v = 1; v <= 10; v += 1) {
      expect(classes.filter((c) => classeDoValor([c], v)).length, `valor ${v}`).toBe(1);
    }
  });

  it("aponta a variável CSS do token / points to the token variable", () => {
    expect(classes[0].variavel).toBe("--color-chart-sequential-5");
  });
});

describe("classesDivergentes()", () => {
  const classes = classesDivergentes([0.1, 0.5, 1], formatar, {
    acima: "acima",
    abaixo: "abaixo",
    igual: "igual",
  })("escuro");

  it("tem o meio neutro entre −0,1 e 0,1 / neutral middle", () => {
    expect(classeDoValor(classes, 0)?.color).toBe(paletas("escuro").divergente.neutro);
    expect(classeDoValor(classes, 0.1)?.color).toBe(paletas("escuro").divergente.neutro);
    expect(classeDoValor(classes, -0.1)?.color).toBe(paletas("escuro").divergente.neutro);
  });

  it("é simétrica em torno de zero / symmetric around zero", () => {
    const { negativo, positivo } = paletas("escuro").divergente;
    for (const [valor, i] of /** @type {[number, number][]} */ ([
      [0.3, 0],
      [0.7, 1],
      [2, 2],
    ])) {
      expect(classeDoValor(classes, valor)?.color).toBe(positivo[i]);
      expect(classeDoValor(classes, -valor)?.color).toBe(negativo[i]);
    }
  });
});
