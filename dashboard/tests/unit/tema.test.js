/**
 * PT: Testes do tema dos gráficos (#63).
 *
 *     O tema do ECharts precisa sair dos tokens, e nunca de um hex digitado:
 *     cada cor conferida aqui é comparada com o token de onde deveria vir.
 *     O texto do gráfico precisa de 4,5:1 sobre o cartão, como qualquer
 *     texto da interface.
 *
 * EN: Chart theme tests: every color must come from the tokens, and chart
 *     text needs 4.5:1 on the glass.
 */

import { describe, expect, it } from "vitest";
import { razaoDeContraste } from "../../src/cor/contraste.js";
import { DEGRAUS, hex, montarTema, paletas, superficies } from "../../src/graficos/tema.js";
import { cor } from "../../src/tokens.js";

/** @typedef {import("../../src/tokens.js").Tema} Tema */

const TEMAS = /** @type {Tema[]} */ (["claro", "escuro"]);
const TEXTO = 4.5;

for (const tema of TEMAS) {
  describe(`tema ${tema}`, () => {
    const objeto = /** @type {Record<string, any>} */ (montarTema(tema));
    const { grafico } = superficies(tema);

    it("usa a paleta categórica dos tokens / uses the token palette", () => {
      expect(objeto.color).toEqual(paletas(tema).categorica);
      expect(objeto.color[0]).toBe(cor("color.chart.categorical.1", tema).hex);
    });

    it("usa o texto principal e o secundário dos tokens / uses token text colors", () => {
      expect(objeto.textStyle.color).toBe(hex("color.text.primary", tema));
      expect(objeto.categoryAxis.axisLabel.color).toBe(hex("color.text.secondary", tema));
    });

    it("tem texto com pelo menos 4,5:1 sobre o cartão / chart text contrast", () => {
      for (const texto of [objeto.textStyle.color, objeto.categoryAxis.axisLabel.color]) {
        expect(razaoDeContraste(texto, grafico)).toBeGreaterThanOrEqual(TEXTO);
      }
    });

    it("tem o número de degraus combinado em cada paleta / step counts", () => {
      const p = paletas(tema);
      expect(p.categorica).toHaveLength(DEGRAUS.categorica);
      expect(p.sequencial).toHaveLength(DEGRAUS.sequencial);
      expect(p.divergente.negativo).toHaveLength(DEGRAUS.divergente);
      expect(p.divergente.positivo).toHaveLength(DEGRAUS.divergente);
    });
  });
}

describe("os dois temas / both themes", () => {
  it("desenham o gráfico no cartão sólido: branco no claro e cinza 100 no escuro", () => {
    expect(superficies("claro").grafico).toBe("#ffffff");
    expect(superficies("escuro").grafico).toBe("#161616");
  });

  it("trocam as cores de texto / swap text colors", () => {
    expect(hex("color.text.primary", "claro")).not.toBe(hex("color.text.primary", "escuro"));
  });
});
