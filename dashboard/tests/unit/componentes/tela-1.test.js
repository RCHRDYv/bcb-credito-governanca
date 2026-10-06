/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes dos componentes que nasceram com a Tela 1 (#69): o painel de
 *     detalhe, a definição do número e o campo de seleção.
 * EN: Tests for the components born with Screen 1: detail panel, number
 *     definition and select field.
 */

import { describe, expect, it } from "vitest";
import { campoDeSelecao } from "../../../src/componentes/campo-de-selecao.js";
import { definicao } from "../../../src/componentes/definicao.js";
import { painelDeDetalhe } from "../../../src/componentes/painel-de-detalhe.js";

describe("painelDeDetalhe()", () => {
  it("começa com a dica de como escolher, sem o botão de fechar / starts with the hint", () => {
    const painel = painelDeDetalhe({ dica: "Escolha uma UF." });
    expect(painel.elemento.textContent).toContain("Escolha uma UF.");
    expect(
      /** @type {HTMLButtonElement} */ (painel.elemento.querySelector(".detalhe__fechar")).hidden,
    ).toBe(true);
    expect(painel.elemento.classList.contains("detalhe--aberto")).toBe(false);
  });

  it("mostra a lista de chave e valor e abre a folha / shows the key-value list", () => {
    const painel = painelDeDetalhe({ dica: "x" });
    painel.mostrar({
      titulo: "Minas Gerais",
      subtitulo: "Todas as modalidades",
      itens: [{ chave: "Carteira PJ", valor: "R$ 226,1 bi" }],
      nota: "Ressalva",
    });
    expect(painel.elemento.querySelector(".detalhe__titulo")?.textContent).toBe("Minas Gerais");
    expect(painel.elemento.querySelector(".detalhe__valor")?.textContent).toBe("R$ 226,1 bi");
    expect(painel.elemento.querySelector(".detalhe__nota")?.textContent).toBe("Ressalva");
    expect(painel.elemento.classList.contains("detalhe--aberto")).toBe(true);
  });

  it("fecha pelo botão, volta à dica e avisa quem escuta / closes and notifies", () => {
    let fechou = false;
    const painel = painelDeDetalhe({ dica: "Escolha uma UF.", aoFechar: () => (fechou = true) });
    painel.mostrar({ titulo: "MG", itens: [] });
    /** @type {HTMLButtonElement} */ (painel.elemento.querySelector(".detalhe__fechar")).click();
    expect(fechou).toBe(true);
    expect(painel.elemento.textContent).toContain("Escolha uma UF.");
  });

  it("anuncia a troca com calma a leitores de tela / polite announcements", () => {
    const painel = painelDeDetalhe({ dica: "x" });
    expect(painel.elemento.querySelector(".detalhe__corpo")?.getAttribute("aria-live")).toBe(
      "polite",
    );
  });
});

describe("definicao()", () => {
  it("liga o botão ao popover com a explicação, a definição e a fonte / button opens the popover", () => {
    const el = definicao({
      rotulo: "Carteira PJ",
      definicao: {
        tipo: "conceito",
        rotulo: "Carteira ativa",
        explicacao: "O saldo do crédito em dia.",
        explicacaoFonte: null,
        definicao: "Saldo das operações de crédito.",
        fonte: "SCR.data",
        confianca: "verbatim",
      },
    });
    const botao = /** @type {HTMLButtonElement} */ (el.querySelector(".definicao__botao"));
    const caixa = /** @type {HTMLElement} */ (el.querySelector(".definicao__caixa"));
    expect(botao.getAttribute("popovertarget")).toBe(caixa.id);
    expect(botao.getAttribute("aria-label")).toContain("Carteira PJ");
    expect(caixa.textContent).toContain("O saldo do crédito em dia.");
    expect(caixa.textContent).toContain("Saldo das operações de crédito.");
  });

  it("aponta o ADR quando a regra é do projeto / links the ADR for project rules", () => {
    const el = definicao({
      rotulo: "Crédito que faltaria",
      definicao: { tipo: "adr", rotulo: "ADR 0014, decisão 5", endereco: "https://exemplo/adr" },
    });
    expect(el.querySelector(".definicao__link")?.getAttribute("href")).toBe("https://exemplo/adr");
  });
});

describe("campoDeSelecao()", () => {
  it("liga o rótulo ao select, marca o valor e avisa a troca / label, value and change", () => {
    /** @type {string[]} */
    const valores = [];
    const el = campoDeSelecao({
      rotulo: "Modalidade",
      opcoes: [
        { valor: "todas", texto: "Todas as modalidades" },
        { valor: "04", texto: "Financiamentos" },
      ],
      valor: "todas",
      aoMudar: (valor) => valores.push(valor),
    });
    const selecao = /** @type {HTMLSelectElement} */ (el.querySelector("select"));
    expect(el.querySelector("label")?.getAttribute("for")).toBe(selecao.id);
    expect(selecao.value).toBe("todas");
    selecao.value = "04";
    selecao.dispatchEvent(new Event("change"));
    expect(valores).toEqual(["04"]);
  });
});
