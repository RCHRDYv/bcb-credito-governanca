/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes do aviso (#64).
 * EN: Notice tests.
 */

import { describe, expect, it } from "vitest";
import { aviso } from "../../../src/componentes/aviso.js";

describe("aviso()", () => {
  it("traz o ícone no círculo e o texto / icon in a circle and text", () => {
    const el = aviso({ tipo: "atencao", texto: "A série cruza jan/2025." });
    expect(el.classList.contains("aviso--atencao")).toBe(true);
    expect(el.querySelector(".aviso__icone svg.icone")).not.toBeNull();
    expect(el.textContent).toBe("A série cruza jan/2025.");
  });

  it("não é anunciado quando já nasce com a página / static by default", () => {
    expect(aviso({ tipo: "informacao", texto: "x" }).hasAttribute("role")).toBe(false);
  });

  it("vem em caixa por padrão, e em linha quando pedido / boxed by default, inline on request", () => {
    expect(aviso({ tipo: "informacao", texto: "x" }).classList.contains("aviso--linha")).toBe(
      false,
    );
    const linha = aviso({ tipo: "informacao", texto: "x", variante: "linha" });
    expect(linha.classList.contains("aviso--linha")).toBe(true);
    expect(linha.querySelector(".aviso__icone svg.icone")).not.toBeNull();
  });

  it("anuncia o erro com urgência e os outros com calma / alert for errors, status otherwise", () => {
    expect(aviso({ tipo: "erro", texto: "x", anunciar: true }).getAttribute("role")).toBe("alert");
    expect(aviso({ tipo: "informacao", texto: "x", anunciar: true }).getAttribute("role")).toBe(
      "status",
    );
  });
});
