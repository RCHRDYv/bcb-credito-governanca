/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes do controle de tema (#64): automático é o padrão, claro e
 *     escuro fixam o `data-tema`, e a escolha fica guardada no navegador.
 * EN: Theme control tests.
 */

import { beforeEach, describe, expect, it } from "vitest";
import {
  aplicarTema,
  CHAVE_DO_TEMA,
  controleDeTema,
  escolhaGuardada,
} from "../../../src/componentes/controle-de-tema.js";

beforeEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.tema;
});

describe("escolhaGuardada()", () => {
  it("é automático sem escolha, ou com valor estranho / automatic by default", () => {
    expect(escolhaGuardada()).toBe("automatico");
    localStorage.setItem(CHAVE_DO_TEMA, "roxo");
    expect(escolhaGuardada()).toBe("automatico");
  });
});

describe("aplicarTema()", () => {
  it("claro e escuro fixam o atributo e ficam guardados / sets and stores", () => {
    aplicarTema("escuro");
    expect(document.documentElement.dataset.tema).toBe("escuro");
    expect(localStorage.getItem(CHAVE_DO_TEMA)).toBe("escuro");
  });

  it("automático tira o atributo e a escolha guardada / automatic clears both", () => {
    aplicarTema("claro");
    aplicarTema("automatico");
    expect(document.documentElement.hasAttribute("data-tema")).toBe(false);
    expect(localStorage.getItem(CHAVE_DO_TEMA)).toBeNull();
  });
});

describe("controleDeTema()", () => {
  it("começa na escolha guardada / starts on the stored choice", () => {
    localStorage.setItem(CHAVE_DO_TEMA, "escuro");
    const el = controleDeTema();
    const marcada = el.querySelector('[aria-checked="true"]');
    expect(marcada?.getAttribute("data-valor")).toBe("escuro");
  });

  it("troca o tema da página pelo clique / clicking changes the page theme", () => {
    const el = controleDeTema();
    document.body.replaceChildren(el);
    /** @type {HTMLButtonElement} */ (el.querySelector('[data-valor="claro"]')).click();
    expect(document.documentElement.dataset.tema).toBe("claro");
    expect(escolhaGuardada()).toBe("claro");
  });
});
