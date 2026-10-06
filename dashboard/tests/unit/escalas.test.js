/**
 * PT: Testes das classes de cor dos mapas e do cartograma (#63).
 * EN: Tests for map and cartogram color classes.
 */

import { describe, expect, it } from "vitest";
import {
  classeDoValor,
  classesEmCincoFaixas,
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

describe("classesEmCincoFaixas()", () => {
  const rotulos = {
    forteAbaixo: "forte abaixo",
    abaixo: "abaixo",
    meio: "meio",
    acima: "acima",
    forteAcima: "forte acima",
  };
  const seq = paletas("escuro").sequencial;

  it("usa só a rampa roxa, com o meio no degrau do meio / purple ramp only", () => {
    const classes = classesEmCincoFaixas([0.1, 0.3], rotulos)("escuro");
    expect(classes.map((c) => c.color).sort()).toEqual([...seq].sort());
    for (const valor of [0, 0.1, -0.1]) {
      expect(classeDoValor(classes, valor)?.color).toBe(seq[2]);
    }
  });

  it("põe o roxo mais forte acima, por padrão / strongest above by default", () => {
    const classes = classesEmCincoFaixas([0.1, 0.3], rotulos)("escuro");
    expect(classeDoValor(classes, 0.5)?.color).toBe(seq[4]);
    expect(classeDoValor(classes, 0.2)?.color).toBe(seq[3]);
    expect(classeDoValor(classes, -0.2)?.color).toBe(seq[1]);
    expect(classeDoValor(classes, -0.5)?.color).toBe(seq[0]);
    expect(classes[0].label).toBe("forte acima");
  });

  it("põe o roxo mais forte abaixo, quando pedido / strongest below on request", () => {
    const classes = classesEmCincoFaixas([0.1, 0.3], rotulos, { maisForteAbaixo: true })("escuro");
    expect(classeDoValor(classes, -0.5)?.color).toBe(seq[4]);
    expect(classeDoValor(classes, 0.5)?.color).toBe(seq[0]);
    expect(classes[0]).toMatchObject({
      label: "forte abaixo",
      variavel: "--color-chart-sequential-5",
    });
  });

  it("põe cada valor em exatamente uma faixa / each value in one band", () => {
    const classes = classesEmCincoFaixas([0.1, 0.3], rotulos)("claro");
    for (const valor of [-1, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 1]) {
      expect(classes.filter((c) => classeDoValor([c], valor)).length, `valor ${valor}`).toBe(1);
    }
  });
});
