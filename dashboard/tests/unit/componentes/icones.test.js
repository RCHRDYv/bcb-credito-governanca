/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes dos ícones do Tabler (#64).
 * EN: Tabler icon tests.
 */

import { describe, expect, it } from "vitest";
import { icone } from "../../../src/componentes/icones.js";

describe("icone()", () => {
  it("devolve um SVG decorativo, com a classe do tamanho / decorative SVG", () => {
    const svg = icone("eye");
    expect(svg.tagName.toLowerCase()).toBe("svg");
    expect(svg.getAttribute("class")).toBe("icone");
    expect(svg.getAttribute("aria-hidden")).toBe("true");
    expect(svg.getAttribute("focusable")).toBe("false");
    expect(svg.hasAttribute("width")).toBe(false);
    expect(svg.querySelectorAll("path").length).toBeGreaterThan(0);
  });

  it("devolve uma cópia nova a cada chamada / returns a fresh copy", () => {
    expect(icone("check")).not.toBe(icone("check"));
  });

  it("falha com um nome fora da lista / throws on unknown names", () => {
    // @ts-expect-error nome que não existe, de propósito / unknown name, on purpose
    expect(() => icone("nao-existe")).toThrow(/nao-existe/);
  });
});
