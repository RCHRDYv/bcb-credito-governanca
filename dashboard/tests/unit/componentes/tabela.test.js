/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes da tabela (#64).
 * EN: Table tests.
 */

import { describe, expect, it } from "vitest";
import { tabela } from "../../../src/componentes/tabela.js";

const LINHAS = [
  { uf: "SP", carteira: "R$ 459,0 bi" },
  { uf: "RJ", carteira: "R$ 137,0 bi" },
];

/** @param {number} [colunaDeTitulo] */
function montar(colunaDeTitulo) {
  return tabela({
    legenda: "Carteira PJ por UF",
    linhas: LINHAS,
    colunaDeTitulo,
    colunas: [
      { titulo: "UF", celula: (l) => l.uf },
      { titulo: "Carteira PJ", tipo: "numero", celula: (l) => l.carteira },
    ],
  });
}

describe("tabela()", () => {
  it("tem legenda e é uma região que recebe foco, nomeada pela legenda / captioned region", () => {
    const el = montar();
    const legenda = /** @type {HTMLElement} */ (el.querySelector("caption"));
    expect(legenda.textContent).toBe("Carteira PJ por UF");
    expect(el.getAttribute("role")).toBe("region");
    expect(el.getAttribute("tabindex")).toBe("0");
    expect(el.getAttribute("aria-labelledby")).toBe(legenda.id);
  });

  it("marca os cabeçalhos de coluna e de linha / column and row headers", () => {
    const el = montar();
    expect([...el.querySelectorAll("thead th")].map((th) => th.getAttribute("scope"))).toEqual([
      "col",
      "col",
    ]);
    const primeira = [...el.querySelectorAll("tbody tr")][0];
    expect(primeira.querySelector("th")?.getAttribute("scope")).toBe("row");
    expect(primeira.querySelector("th")?.textContent).toBe("SP");
  });

  it("alinha os números à direita pela classe / numeric columns", () => {
    const el = montar();
    expect(el.querySelectorAll("td.tabela__numero")).toHaveLength(2);
    expect(el.querySelector("thead th.tabela__numero")?.textContent).toBe("Carteira PJ");
  });

  it("aceita um nó como conteúdo da célula / accepts nodes in cells", () => {
    const el = tabela({
      legenda: "x",
      linhas: [1],
      colunas: [{ titulo: "Nó", celula: () => document.createElement("strong") }],
    });
    expect(el.querySelector("tbody strong")).not.toBeNull();
  });
});
