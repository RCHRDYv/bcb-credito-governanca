/**
 * PT: Cartograma de grade: cada UF é um quadrado do mesmo tamanho.
 *
 *     É a alternativa ao mapa quando os estados pequenos precisam ser lidos
 *     (RF-103): no mapa, o Distrito Federal e Sergipe quase somem; aqui, têm
 *     o mesmo peso que o Amazonas. Usa as mesmas classes de cor do mapa, e
 *     cada quadrado traz a sigla, em texto que contrasta com o preenchimento.
 *     Não depende da malha do IBGE, então continua funcionando quando ela
 *     não carrega.
 *
 * EN: Tile-grid cartogram: every state is an equal square, with the same
 *     color classes as the map and the abbreviation in a contrasting color.
 *     It does not depend on the IBGE mesh.
 */

import { razaoDeContraste } from "../cor/contraste.js";
import { t } from "../textos/index.js";
import { classeDoValor } from "./escalas.js";
import { criarGrafico } from "./grafico.js";
import { legendaDeClasses } from "./legenda.js";
import { hex } from "./tema.js";
import { UFS, ufPelaSigla } from "./ufs.js";

/** @typedef {import("./escalas.js").Classes} Classes */
/** @typedef {import("./grafico.js").Grafico} Grafico */
/** @typedef {import("../tokens.js").Tema} Tema */

const COLUNAS = Math.max(...UFS.map((uf) => uf.coluna)) + 1;
const LINHAS = Math.max(...UFS.map((uf) => uf.linha)) + 1;

/**
 * PT: O texto que mais contrasta com o preenchimento: o principal do tema
 *     claro ou o do tema escuro.
 * EN: The text color with the most contrast on the fill.
 *
 * @param {string} preenchimento
 * @returns {string}
 */
function textoSobre(preenchimento) {
  const escuro = hex("color.text.primary", "claro");
  const claro = hex("color.text.primary", "escuro");
  return razaoDeContraste(escuro, preenchimento) >= razaoDeContraste(claro, preenchimento)
    ? escuro
    : claro;
}

/**
 * @typedef {object} DadosDoCartograma
 * @property {Record<string, number | null>} valores Por sigla da UF / by state
 * @property {Classes} classes As mesmas do mapa / same as the map
 * @property {(v: number) => string} formatar Para a dica / for the tooltip
 */

/**
 * PT: Desenha o cartograma no elemento, com a legenda logo depois dele.
 * EN: Draws the cartogram.
 *
 * @param {HTMLElement} el
 * @param {DadosDoCartograma} dados
 * @returns {Promise<Grafico>}
 */
export function cartograma(el, { valores, classes, formatar }) {
  // PT: a altura acompanha a largura na proporção da grade, pelo CSS
  // EN: height follows width in the grid proportion, via CSS
  el.style.setProperty("--linhas", String(LINHAS));
  el.style.setProperty("--colunas", String(COLUNAS));
  el.after(legendaDeClasses(classes("claro")));
  return criarGrafico(el, (tema) => {
    const pedacos = classes(tema);
    const vazio = hex("color.border.subtle", tema);
    return {
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ data: { sigla: string, value: number[] } }} */ p) => {
          const valor = p.data.value[2];
          return `${ufPelaSigla(p.data.sigla).nome}: ${Number.isFinite(valor) ? formatar(valor) : t("grafico.sem-dado")}`;
        },
      },
      grid: { left: 0, right: 0, top: 0, bottom: 0 },
      xAxis: { type: "category", data: Array.from({ length: COLUNAS }, (_, i) => i), show: false },
      yAxis: {
        type: "category",
        data: Array.from({ length: LINHAS }, (_, i) => i),
        inverse: true,
        show: false,
      },
      visualMap: {
        type: "piecewise",
        pieces: pedacos,
        outOfRange: { color: vazio },
        show: false,
      },
      series: [
        {
          type: "heatmap",
          data: UFS.map((uf) => {
            const valor = valores[uf.sigla];
            const cor = Number.isFinite(valor)
              ? (classeDoValor(pedacos, /** @type {number} */ (valor))?.color ?? vazio)
              : vazio;
            return {
              sigla: uf.sigla,
              value: [uf.coluna, uf.linha, valor ?? Number.NaN],
              label: { show: true, formatter: uf.sigla, color: textoSobre(cor), fontSize: 12 },
            };
          }),
          emphasis: { itemStyle: { borderColor: hex("color.text.primary", tema), borderWidth: 2 } },
        },
      ],
    };
  });
}
