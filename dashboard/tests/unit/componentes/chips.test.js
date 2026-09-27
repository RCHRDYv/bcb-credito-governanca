/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes dos chips de filtro (#64).
 * EN: Filter chip tests.
 */

import { describe, expect, it, vi } from "vitest";
import { grupoDeChips } from "../../../src/componentes/chips.js";

const OPCOES = [
  { valor: "02", texto: "Empréstimos" },
  { valor: "04", texto: "Financiamentos" },
  { valor: "13", texto: "Outros créditos", titulo: "Outros créditos, com cartão" },
];

describe("grupoDeChips()", () => {
  it("é um grupo com nome, e marca os selecionados / named group with pressed chips", () => {
    const el = grupoDeChips({ rotulo: "Modalidades", opcoes: OPCOES, selecionados: ["04"] });
    const chips = [...el.querySelectorAll("button")];
    expect(el.getAttribute("role")).toBe("group");
    expect(el.getAttribute("aria-label")).toBe("Modalidades");
    expect(chips.map((c) => c.getAttribute("aria-pressed"))).toEqual(["false", "true", "false"]);
    expect(chips[2].title).toBe("Outros créditos, com cartão");
  });

  it("liga e desliga, e devolve na ordem das opções / toggles, in option order", () => {
    const aoMudar = vi.fn();
    const el = grupoDeChips({
      rotulo: "Modalidades",
      opcoes: OPCOES,
      selecionados: ["13"],
      aoMudar,
    });
    const chips = [...el.querySelectorAll("button")];
    chips[0].click();
    expect(aoMudar).toHaveBeenLastCalledWith(["02", "13"]);
    chips[2].click();
    expect(aoMudar).toHaveBeenLastCalledWith(["02"]);
    expect(chips[2].getAttribute("aria-pressed")).toBe("false");
  });

  it("todo chip traz o ícone de confirmação, que o CSS mostra só no selecionado", () => {
    const el = grupoDeChips({ rotulo: "Modalidades", opcoes: OPCOES });
    expect(el.querySelectorAll("button svg.icone")).toHaveLength(3);
  });
});
