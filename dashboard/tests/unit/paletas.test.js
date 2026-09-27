/**
 * PT: Validação automatizada das paletas de gráfico (#63, ADR 0021).
 *
 *     As paletas são lidas dos tokens gerados, nos dois temas, e passam pelos
 *     mesmos critérios da revisão: contraste de 3:1 para elemento gráfico
 *     (WCAG 2.2), faixa de luminosidade, croma, e distância entre cores com
 *     e sem daltonismo. As cores são medidas contra as duas superfícies em
 *     que um gráfico pode estar: o vidro regular composto sobre a página e a
 *     camada sólida que o substitui.
 *
 *     Os controles negativos garantem que o teste reprova de verdade: a
 *     paleta oficial do Carbon, que motivou a #63, e uma paleta clara demais
 *     para o fundo precisam reprovar. Se um deles passar, o validador
 *     quebrou, e não a paleta.
 *
 * EN: Automated chart palette validation, read from the generated tokens in
 *     both themes. Negative controls (Carbon's official palette and a
 *     too-light palette) must fail, proving the check can fail.
 */

import { describe, expect, it } from "vitest";
import { razaoDeContraste } from "../../src/cor/contraste.js";
import {
  validarCategorica,
  validarDivergente,
  validarSequencial,
} from "../../src/cor/validacao.js";
import { paletas, superficies } from "../../src/graficos/tema.js";

/** @typedef {import("../../src/tokens.js").Tema} Tema */
/** @typedef {import("../../src/cor/validacao.js").Resultado} Resultado */

const TEMAS = /** @type {Tema[]} */ (["claro", "escuro"]);
const GRAFICO = 3;

/**
 * PT: Os critérios reprovados, para a mensagem de erro dizer o motivo.
 * EN: Failing criteria, so the error message says why.
 *
 * @param {Resultado} resultado
 * @returns {string[]}
 */
function reprovados(resultado) {
  return resultado.criterios
    .filter(({ estado }) => estado === "reprova")
    .map(({ nome, detalhe }) => `${nome}: ${detalhe}`);
}

for (const tema of TEMAS) {
  describe(`paletas de gráfico no tema ${tema}`, () => {
    const p = paletas(tema);
    const { vidro, solida } = superficies(tema);

    it.each([
      ["vidro", vidro],
      ["camada sólida", solida],
    ])("cada cor categórica passa de 3:1 sobre o %s", (_nome, superficie) => {
      for (const cor of [...p.categorica, p.outros]) {
        expect(razaoDeContraste(cor, superficie), cor).toBeGreaterThanOrEqual(GRAFICO);
      }
    });

    it("a categórica passa nos pares vizinhos, para barras e linhas", () => {
      const resultado = validarCategorica(p.categorica, { tema, superficie: vidro });
      expect(reprovados(resultado)).toEqual([]);
    });

    it("as quatro primeiras categóricas passam em todos os pares, para dispersão e mapa", () => {
      const resultado = validarCategorica(p.categorica.slice(0, 4), {
        tema,
        superficie: vidro,
        pares: "todos",
      });
      expect(reprovados(resultado)).toEqual([]);
    });

    it("a quinta categórica não serve para dispersão e mapa, como registra o ADR 0021", () => {
      // PT: o ciano 50 e o azul 50 ficam próximos demais quando se encostam
      // EN: cyan 50 and blue 50 are too close when they touch
      const resultado = validarCategorica(p.categorica.slice(0, 5), {
        tema,
        superficie: vidro,
        pares: "todos",
      });
      expect(resultado.aprovada).toBe(false);
    });

    // PT: sobre o vidro, que é a superfície de sempre. Na camada sólida do
    //     escuro, a ponta fica em 1,96:1, exceção aceita no ADR 0021
    // EN: on the glass; the dark solid layer is an accepted exception
    it("a sequencial é uma rampa válida sobre o vidro", () => {
      const resultado = validarSequencial(p.sequencial, { tema, superficie: vidro });
      expect(reprovados(resultado)).toEqual([]);
    });

    it("a divergente é válida sobre o vidro", () => {
      const resultado = validarDivergente(p.divergente, { tema, superficie: vidro });
      expect(reprovados(resultado)).toEqual([]);
    });
  });
}

describe("controles negativos: o validador reprova paleta ruim", () => {
  const { vidro } = superficies("claro");

  it("reprova a categórica oficial do Carbon, pela faixa e pelo croma", () => {
    const oficial = ["#6929c4", "#1192e8", "#005d5d", "#9f1853", "#fa4d56", "#520408"];
    const resultado = validarCategorica(oficial, { tema: "claro", superficie: vidro });
    expect(resultado.aprovada).toBe(false);
    const ids = resultado.criterios.filter((c) => c.estado === "reprova").map((c) => c.id);
    expect(ids).toEqual(expect.arrayContaining(["faixa", "croma"]));
  });

  it("reprova uma paleta abaixo do contraste", () => {
    // PT: os degraus 20 do Carbon, claros demais para um fundo quase branco
    // EN: Carbon's 20 steps, too light for a near-white background
    const clara = ["#e8daff", "#bae6ff", "#9ef0f0", "#ffd6e8"];
    const resultado = validarCategorica(clara, { tema: "claro", superficie: vidro });
    expect(resultado.aprovada).toBe(false);
    expect(resultado.criterios.find((c) => c.id === "contraste")?.estado).toBe("reprova");
  });

  it("reprova uma rampa fora de ordem", () => {
    const resultado = validarSequencial(["#8a3ffc", "#be95ff", "#491d8b"], {
      tema: "claro",
      superficie: vidro,
    });
    expect(resultado.criterios.find((c) => c.id === "monotonica")?.estado).toBe("reprova");
  });

  it("reprova uma divergente com o meio colorido", () => {
    const resultado = validarDivergente(
      { negativo: ["#08bdba"], neutro: "#ffd6e8", positivo: ["#be95ff"] },
      { tema: "claro", superficie: vidro },
    );
    expect(resultado.criterios.find((c) => c.id === "neutro")?.estado).toBe("reprova");
  });
});
