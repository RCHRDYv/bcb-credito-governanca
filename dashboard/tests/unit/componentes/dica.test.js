/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da dica flutuante (#64), pelo critério 1.4.13 da WCAG 2.2:
 *     abre com o mouse e com o foco, continua aberta com o mouse sobre ela,
 *     e fecha com o Esc.
 * EN: Tooltip tests, per WCAG 2.2 SC 1.4.13.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { comDica, corpoDaDica } from "../../../src/componentes/dica.js";

function montar() {
  const gatilho = document.createElement("button");
  gatilho.textContent = "SP · Empréstimos";
  const envoltorio = comDica(gatilho, ["Carteira por empresa: 1,71×"]);
  document.body.replaceChildren(envoltorio);
  const dica = /** @type {HTMLElement} */ (envoltorio.querySelector('[role="tooltip"]'));
  return { gatilho, envoltorio, dica };
}

describe("comDica()", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("começa fechada e descreve o gatilho / starts hidden and describes the trigger", () => {
    const { gatilho, dica } = montar();
    expect(dica.hidden).toBe(true);
    expect(gatilho.getAttribute("aria-describedby")).toBe(dica.id);
  });

  it("abre com o foco e fecha ao perder o foco / focus opens, blur closes", () => {
    const { gatilho, dica } = montar();
    gatilho.focus();
    expect(dica.hidden).toBe(false);
    gatilho.blur();
    expect(dica.hidden).toBe(true);
  });

  it("fecha com o Esc, sem tirar o foco / Escape closes without moving focus", () => {
    const { gatilho, dica } = montar();
    gatilho.focus();
    gatilho.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(dica.hidden).toBe(true);
    expect(document.activeElement).toBe(gatilho);
  });

  it("abre com o mouse e fecha pouco depois que ele sai / hover opens, closes after leaving", () => {
    const { envoltorio, dica } = montar();
    envoltorio.dispatchEvent(new MouseEvent("mouseenter"));
    expect(dica.hidden).toBe(false);
    envoltorio.dispatchEvent(new MouseEvent("mouseleave"));
    expect(dica.hidden).toBe(false);
    vi.runAllTimers();
    expect(dica.hidden).toBe(true);
  });

  it("continua aberta se o mouse volta a tempo / stays open when the pointer returns", () => {
    const { envoltorio, dica } = montar();
    envoltorio.dispatchEvent(new MouseEvent("mouseenter"));
    envoltorio.dispatchEvent(new MouseEvent("mouseleave"));
    envoltorio.dispatchEvent(new MouseEvent("mouseenter"));
    vi.runAllTimers();
    expect(dica.hidden).toBe(false);
  });
});

describe("corpoDaDica()", () => {
  it("monta só o corpo, sem comportamento / body only", () => {
    const el = corpoDaDica(["texto"]);
    expect(el.classList.contains("dica")).toBe(true);
    expect(el.hasAttribute("role")).toBe(false);
  });
});
