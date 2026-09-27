/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da etiqueta de alerta antecipado (#64).
 * EN: Early-warning tag tests.
 */

import { describe, expect, it } from "vitest";
import { alertaAntecipado } from "../../../src/componentes/alerta-antecipado.js";

describe("alertaAntecipado()", () => {
  it("traz o sino e o nome / bell and name", () => {
    const el = alertaAntecipado();
    expect(el.classList.contains("etiqueta--alerta")).toBe(true);
    expect(el.querySelector("svg.icone")).not.toBeNull();
    expect(el.textContent).toBe("Alerta antecipado");
  });
});
