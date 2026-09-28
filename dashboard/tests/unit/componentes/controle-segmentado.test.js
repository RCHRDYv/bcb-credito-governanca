/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes do controle segmentado (#64): o padrão de grupo de rádio da
 *     WAI-ARIA, com o foco só na opção escolhida e as setas trocando a opção.
 * EN: Segmented control tests, WAI-ARIA radio group pattern.
 */

import { describe, expect, it, vi } from "vitest";
import { controleSegmentado } from "../../../src/componentes/controle-segmentado.js";

const OPCOES = [
  { valor: "credito", texto: "Onde está o crédito" },
  { valor: "risco", texto: "Onde o risco piora" },
  { valor: "recomendacao", texto: "Recomendação" },
];

/**
 * PT: Monta o controle na página e devolve as peças.
 * EN: Mounts the control and returns its parts.
 *
 * @param {string} valor
 * @param {(v: string) => void} [aoMudar]
 */
function montar(valor, aoMudar) {
  const el = controleSegmentado({ rotulo: "Visão", opcoes: OPCOES, valor, aoMudar });
  document.body.replaceChildren(el);
  const opcoes = /** @type {HTMLButtonElement[]} */ ([...el.querySelectorAll('[role="radio"]')]);
  const escolhida = () => opcoes.findIndex((o) => o.getAttribute("aria-checked") === "true");
  return { el, opcoes, escolhida };
}

/**
 * @param {HTMLElement} el
 * @param {string} key
 */
function tecla(el, key) {
  el.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
}

describe("controleSegmentado()", () => {
  it("é um grupo de rádio com nome, e começa na opção pedida / named radio group", () => {
    const { el, opcoes, escolhida } = montar("risco");
    expect(el.getAttribute("role")).toBe("radiogroup");
    expect(el.getAttribute("aria-label")).toBe("Visão");
    expect(escolhida()).toBe(1);
    expect(opcoes.map((o) => o.tabIndex)).toEqual([-1, 0, -1]);
  });

  it("troca a opção no clique e avisa / click selects and notifies", () => {
    const aoMudar = vi.fn();
    const { opcoes, escolhida } = montar("credito", aoMudar);
    opcoes[2].click();
    expect(escolhida()).toBe(2);
    expect(aoMudar).toHaveBeenCalledWith("recomendacao");
  });

  it("as setas trocam a opção, dão a volta e movem o foco / arrows wrap and move focus", () => {
    const { el, opcoes, escolhida } = montar("recomendacao");
    tecla(el, "ArrowRight");
    expect(escolhida()).toBe(0);
    expect(document.activeElement).toBe(opcoes[0]);
    tecla(el, "ArrowLeft");
    expect(escolhida()).toBe(2);
    tecla(el, "Home");
    expect(escolhida()).toBe(0);
    tecla(el, "End");
    expect(escolhida()).toBe(2);
  });

  it("não avisa na montagem, só na escolha / no notification on build", () => {
    const aoMudar = vi.fn();
    montar("credito", aoMudar);
    expect(aoMudar).not.toHaveBeenCalled();
  });

  it("aceita de duas a cinco opções / two to five options", () => {
    const seis = Array.from({ length: 6 }, (_, i) => ({ valor: String(i), texto: String(i) }));
    expect(() =>
      controleSegmentado({ rotulo: "x", opcoes: [OPCOES[0]], valor: "credito" }),
    ).toThrow();
    expect(() => controleSegmentado({ rotulo: "x", opcoes: seis, valor: "0" })).toThrow();
  });
});
