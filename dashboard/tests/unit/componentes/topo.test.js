/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da barra de topo (#64).
 * EN: Top bar tests.
 */

import { describe, expect, it } from "vitest";
import { topo } from "../../../src/componentes/topo.js";

describe("topo()", () => {
  it("traz o nome do produto e o controle de tema / product name and theme control", () => {
    const el = topo();
    expect(el.tagName).toBe("HEADER");
    expect(el.querySelector(".topo__nome")?.textContent).toBe("Crédito PJ");
    expect(el.querySelector('[role="radiogroup"]')?.getAttribute("aria-label")).toBe("Tema");
  });
});
