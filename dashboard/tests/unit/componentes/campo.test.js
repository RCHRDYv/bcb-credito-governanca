/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes do campo de texto (#64).
 * EN: Text field tests.
 */

import { describe, expect, it } from "vitest";
import { campo } from "../../../src/componentes/campo.js";

describe("campo()", () => {
  it("liga o rótulo ao campo, fora dele / label outside, linked", () => {
    const el = campo({ rotulo: "Estado", exemplo: "Ex.: SP" });
    const rotulo = /** @type {HTMLLabelElement} */ (el.querySelector("label"));
    const entrada = /** @type {HTMLInputElement} */ (el.querySelector("input"));
    expect(rotulo.htmlFor).toBe(entrada.id);
    expect(rotulo.textContent).toBe("Estado");
    expect(entrada.placeholder).toBe("Ex.: SP");
    expect(entrada.hasAttribute("aria-invalid")).toBe(false);
  });

  it("descreve o campo pela ajuda e pelo erro / described by help and error", () => {
    const el = campo({
      rotulo: "Estado",
      valor: "XX",
      ajuda: "Duas letras.",
      erro: "Não existe UF XX.",
    });
    const entrada = /** @type {HTMLInputElement} */ (el.querySelector("input"));
    const ids = (entrada.getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids.map((id) => el.querySelector(`#${id}`)?.textContent)).toEqual([
      "Duas letras.",
      "Não existe UF XX.",
    ]);
    expect(entrada.getAttribute("aria-invalid")).toBe("true");
    expect(entrada.value).toBe("XX");
    expect(el.classList.contains("campo--erro")).toBe(true);
    expect(el.querySelector(".campo__erro svg.icone")).not.toBeNull();
  });

  it("desativa quando pedido / disabled", () => {
    const el = campo({ rotulo: "Pergunta", desativado: true });
    expect(/** @type {HTMLInputElement} */ (el.querySelector("input")).disabled).toBe(true);
  });

  it("dá um id diferente a cada campo / unique ids", () => {
    const a = campo({ rotulo: "A" }).querySelector("input")?.id;
    const b = campo({ rotulo: "B" }).querySelector("input")?.id;
    expect(a).not.toBe(b);
  });
});
