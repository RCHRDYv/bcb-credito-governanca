/**
 * PT: Contraste do texto sobre o vidro no pior ponto do campo de luz (#64).
 *
 *     O vidro é transparente, então a cor atrás do texto depende do que está
 *     atrás do vidro. O pior caso é o centro de uma mancha do campo de luz,
 *     onde a cor da mancha está com a opacidade do token. O teste compõe, em
 *     ordem, a mancha sobre o fundo da página e o vidro sobre a mancha, e
 *     confere o texto em cima. Foi esta conta que levou, em 2026-09-27, a
 *     fechar o vidro regular de 62% para 82% com as manchas na cor cheia.
 *
 * EN: Text contrast on glass at the light field's worst point: a blob's
 *     centre composited under the glass, in both themes.
 */

import { describe, expect, it } from "vitest";
import { compor, razaoDeContraste } from "../../src/cor/contraste.js";
import { cor, token } from "../../src/tokens.js";

/** @typedef {import("../../src/tokens.js").Tema} Tema */

const TEXTO = 4.5;
const MANCHAS = ["azul", "roxo", "verde-azulado"];
const OPACIDADE = Number(token("material.campo-de-luz.opacidade").css);

/**
 * PT: O vidro composto sobre o centro de uma mancha, sobre a página.
 * EN: The glass composited over a blob centre over the page.
 *
 * @param {string} vidro Caminho do preenchimento do vidro / glass fill path
 * @param {string} mancha
 * @param {Tema} tema
 * @returns {string}
 */
function vidroSobreAMancha(vidro, mancha, tema) {
  const pagina = cor("color.background.page", tema).hex;
  const fundo = compor(
    { hex: cor(`color.campo-de-luz.${mancha}`, tema).hex, alpha: OPACIDADE },
    pagina,
  );
  return compor(cor(vidro, tema), fundo);
}

/**
 * PT: Os textos que aparecem sobre cada vidro. O vermelho de erro não entra:
 *     sobre o vidro ele só aparece em ícone, que pede 3:1, e a mensagem de
 *     erro do campo fica sobre o fundo da página.
 * EN: Texts that sit on each glass; error red appears only as an icon there.
 *
 * @type {[string, string[]][]}
 */
const PARES = [
  [
    "material.vidro.regular.preenchimento",
    [
      "color.text.primary",
      "color.text.secondary",
      "color.text.helper",
      "color.text.placeholder",
      "color.link.default",
    ],
  ],
  ["material.vidro.claro.preenchimento", ["color.text.primary", "color.text.secondary"]],
];

for (const tema of /** @type {Tema[]} */ (["claro", "escuro"])) {
  describe(`texto sobre o vidro no campo de luz, tema ${tema}`, () => {
    for (const [vidro, textos] of PARES) {
      for (const mancha of MANCHAS) {
        it.each(textos)(`%s passa de 4,5:1 no ${vidro} sobre a mancha ${mancha}`, (texto) => {
          const fundo = vidroSobreAMancha(vidro, mancha, tema);
          expect(razaoDeContraste(cor(texto, tema).hex, fundo)).toBeGreaterThanOrEqual(TEXTO);
        });
      }
    }
  });
}
