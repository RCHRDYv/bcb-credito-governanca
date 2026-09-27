/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da etiqueta de quadrante (#64).
 * EN: Quadrant tag tests.
 */

import { describe, expect, it } from "vitest";
import {
  etiquetaDeQuadrante,
  nomeDoQuadrante,
  quadranteDoMart,
} from "../../../src/componentes/etiqueta-de-quadrante.js";

describe("quadranteDoMart()", () => {
  it("converte a grafia do mart na chave do código / mart spelling to key", () => {
    expect(quadranteDoMart("entrar")).toBe("entrar");
    expect(quadranteDoMart("não entrar")).toBe("nao-entrar");
  });

  it("falha com um quadrante desconhecido / throws on unknown", () => {
    expect(() => quadranteDoMart("não avaliada")).toThrow();
  });
});

describe("etiquetaDeQuadrante()", () => {
  it("traz o ponto, o ícone e o nome, nunca só a cor / dot, icon and name", () => {
    const el = etiquetaDeQuadrante("nao-entrar");
    expect(el.classList.contains("etiqueta--nao-entrar")).toBe(true);
    expect(el.querySelector(".etiqueta__ponto")).not.toBeNull();
    expect(el.querySelector("svg.icone")).not.toBeNull();
    expect(el.textContent).toBe("Não entrar");
  });

  it("tem um nome para cada quadrante / every quadrant is named", () => {
    const quadrantes = /** @type {const} */ (["entrar", "observar", "nao-entrar", "manter"]);
    expect(quadrantes.map(nomeDoQuadrante)).toEqual(["Entrar", "Observar", "Não entrar", "Manter"]);
  });
});
