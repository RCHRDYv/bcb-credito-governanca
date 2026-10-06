/**
 * @vitest-environment jsdom
 */
/**
 * PT: Testes das legendas de cor: a lista de classes e a escala (#63 e #69).
 * EN: Color legend tests: the class list and the scale.
 */

import { describe, expect, it } from "vitest";
import { classesEmCincoFaixas } from "../../src/graficos/escalas.js";
import { legendaDeClasses, legendaEmEscala } from "../../src/graficos/legenda.js";

const classes = classesEmCincoFaixas(
  [0.1, 0.3],
  {
    forteAbaixo: "Mais espaço: mais de 30% abaixo",
    abaixo: "Mais espaço: de 10% a 30% abaixo",
    meio: "Perto da mediana",
    acima: "Menos espaço: de 10% a 30% acima",
    forteAcima: "Menos espaço: mais de 30% acima",
  },
  { maisForteAbaixo: true },
)("claro");

describe("legendaDeClasses()", () => {
  it("lista uma amostra por classe, com o rótulo / one swatch per class", () => {
    const el = legendaDeClasses(classes);
    expect(el.querySelectorAll(".legenda__item")).toHaveLength(5);
    expect(el.textContent).toContain("Perto da mediana");
  });

  it("ganha o item com textura de quem fica sem valor / value-less item", () => {
    const el = legendaDeClasses(classes, "Sem comparação");
    expect(el.querySelector(".legenda__cor--sem-valor")).not.toBeNull();
  });
});

describe("legendaEmEscala()", () => {
  const opcoes = {
    classes,
    marcas: ["−30%", "−10%", "+10%", "+30%"],
    extremos: /** @type {[string, string]} */ (["Mais espaço", "Menos espaço"]),
    titulo: "Carteira por empresa em relação à mediana",
  };

  it("pinta a barra num degradê que passa por cada classe no meio da faixa dela / gradient through each class at its band centre", () => {
    const barra = /** @type {HTMLElement} */ (
      legendaEmEscala(opcoes).querySelector(".escala__barra")
    );
    const degrade = barra.style.backgroundImage;
    expect(degrade).toContain("linear-gradient(to right");
    expect(degrade).toContain("var(--color-chart-sequential-5) 10%");
    expect(degrade).toContain("var(--color-chart-sequential-3) 50%");
    expect(degrade).toContain("var(--color-chart-sequential-1) 90%");
  });

  it("marca cada divisa na fronteira entre duas faixas / boundaries at band edges", () => {
    const marcas = [...legendaEmEscala(opcoes).querySelectorAll(".escala__marca")].map(
      (el) => /** @type {HTMLElement} */ (el),
    );
    expect(marcas.map((el) => el.textContent)).toEqual(["−30%", "−10%", "+10%", "+30%"]);
    expect(marcas.map((el) => el.style.getPropertyValue("--posicao"))).toEqual([
      "20%",
      "40%",
      "60%",
      "80%",
    ]);
  });

  it("dá a leitor de tela cada classe por extenso, e esconde a barra / full labels for screen readers", () => {
    const el = legendaEmEscala(opcoes);
    expect(el.querySelector(".escala__barra")?.getAttribute("aria-hidden")).toBe("true");
    const itens = [...el.querySelectorAll(".visualmente-oculto li")].map((li) => li.textContent);
    expect(itens).toEqual(classes.map((classe) => classe.label));
  });

  it("traz o item sem valor só quando pedido / value-less item only on request", () => {
    expect(legendaEmEscala(opcoes).querySelector(".escala__sem-valor")).toBeNull();
    const com = legendaEmEscala({ ...opcoes, rotuloSemValor: "Sem comparação" });
    expect(com.querySelector(".escala__sem-valor")?.textContent).toBe("Sem comparação");
  });
});
