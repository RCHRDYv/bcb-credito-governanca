/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes dos estados de carregamento e de exceção (#64).
 * EN: Loading and exception state tests.
 */

import { describe, expect, it, vi } from "vitest";
import { carregando, chatAcordando, erro, vazio } from "../../../src/componentes/estados.js";

describe("estados", () => {
  it("carregando está ocupado, com texto para leitores de tela / busy with hidden text", () => {
    const el = carregando("Carregando o mapa");
    expect(el.getAttribute("role")).toBe("status");
    expect(el.getAttribute("aria-busy")).toBe("true");
    expect(el.querySelector(".visualmente-oculto")?.textContent).toBe("Carregando o mapa");
    expect(el.querySelectorAll(".carregando__barra")).toHaveLength(3);
  });

  it("vazio diz o porquê e a saída / empty explains and offers a way out", () => {
    const el = vazio({ titulo: "Nada neste filtro", texto: "Tire um filtro." });
    expect(el.textContent).toBe("Nada neste filtroTire um filtro.");
  });

  it("erro é anunciado e tenta de novo pelo botão / error is announced and retries", () => {
    const aoTentarDeNovo = vi.fn();
    const el = erro({ titulo: "Não carregou", texto: "Tente de novo.", aoTentarDeNovo });
    expect(el.getAttribute("role")).toBe("alert");
    /** @type {HTMLButtonElement} */ (el.querySelector("button")).click();
    expect(aoTentarDeNovo).toHaveBeenCalledOnce();
  });

  it("chat acordando é um status, com o orbe decorativo / status with a decorative orb", () => {
    const el = chatAcordando();
    expect(el.getAttribute("role")).toBe("status");
    expect(el.querySelector(".estado__orbe")?.getAttribute("aria-hidden")).toBe("true");
    expect(el.textContent).toContain("acordando");
  });
});
