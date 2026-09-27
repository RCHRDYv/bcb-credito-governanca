/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes do botão (#64).
 * EN: Button tests.
 */

import { describe, expect, it, vi } from "vitest";
import { botao, definirCarregando } from "../../../src/componentes/botao.js";

describe("botao()", () => {
  it("monta a variante pedida, com o texto e o ícone / variant, text and icon", () => {
    const el = botao({ texto: "Exportar PDF", variante: "secundario", icone: "download" });
    expect(el.tagName).toBe("BUTTON");
    expect(el.type).toBe("button");
    expect(el.classList.contains("botao--secundario")).toBe(true);
    expect(el.textContent).toBe("Exportar PDF");
    expect(el.querySelector("svg.icone")).not.toBeNull();
  });

  it("é primário quando a variante não é dita / primary by default", () => {
    expect(botao({ texto: "Aplicar" }).classList.contains("botao--primario")).toBe(true);
  });

  it("chama a ação no clique / calls the action on click", () => {
    const aoClicar = vi.fn();
    botao({ texto: "Aplicar", aoClicar }).click();
    expect(aoClicar).toHaveBeenCalledOnce();
  });

  it("desativado não chama a ação / disabled ignores clicks", () => {
    const aoClicar = vi.fn();
    const el = botao({ texto: "Aplicar", desativado: true, aoClicar });
    el.click();
    expect(el.disabled).toBe(true);
    expect(aoClicar).not.toHaveBeenCalled();
  });

  it("carregando fica ocupado e ignora o clique / loading is busy and ignores clicks", () => {
    const aoClicar = vi.fn();
    const el = botao({ texto: "Aplicar", carregando: true, aoClicar });
    el.click();
    expect(el.getAttribute("aria-busy")).toBe("true");
    expect(el.getAttribute("aria-disabled")).toBe("true");
    expect(el.classList.contains("botao--carregando")).toBe(true);
    expect(aoClicar).not.toHaveBeenCalled();
  });

  it("definirCarregando liga e desliga o estado / toggles loading", () => {
    const aoClicar = vi.fn();
    const el = botao({ texto: "Aplicar", aoClicar });
    definirCarregando(el, true);
    el.click();
    definirCarregando(el, false);
    el.click();
    expect(el.getAttribute("aria-busy")).toBe("false");
    expect(aoClicar).toHaveBeenCalledOnce();
  });
});
