/**
 * PT: O que os gráficos por UF têm em comum para a seleção sincronizada
 *     (RF-102) e para as UFs sem valor: o tipo do gráfico que aceita trocar
 *     a UF escolhida e o dado sem recriar a instância, o estilo do destaque e
 *     o estilo de quem fica fora da comparação.
 *
 *     - **Destaque:** borda de 3 px na cor do texto principal do tema. Ela
 *       não muda o preenchimento: a cor continua dizendo só a classe do
 *       valor. No mapa, a UF escolhida ganha também a sigla numa etiqueta,
 *       que aparece em qualquer cor de fundo (revisão visual da #69).
 *     - **Sem comparação:** a superfície do cartão com listras diagonais, a
 *       mesma textura da projeção na série temporal. Assim ela não se
 *       confunde com o degrau mais claro da rampa roxa, que é um valor
 *       (decidido em 2026-10-01).
 *
 * EN: Shared pieces for synchronized selection and value-less states: the
 *     chart type that swaps selection and data in place, a 3 px highlight in
 *     the primary text color (plus an abbreviation tag on the map), and a
 *     striped surface for states left out of the comparison, distinct from
 *     the lightest step of the purple ramp.
 */

import { hex } from "./tema.js";

/** @typedef {import("../tokens.js").Tema} Tema */

/**
 * @template D
 * @typedef {import("./grafico.js").Grafico & {
 *   selecionar: (sigla: string | null) => void,
 *   mudar: (dados: Partial<D>) => void,
 * }} GraficoDeUf
 */

/**
 * PT: O estilo do item escolhido, no tema pedido.
 * EN: The chosen item's style, in the given theme.
 *
 * @param {Tema} tema
 * @returns {{ borderColor: string, borderWidth: number }}
 */
export function destaque(tema) {
  return { borderColor: hex("color.text.primary", tema), borderWidth: 3 };
}

/**
 * PT: A etiqueta com a sigla da UF escolhida no mapa.
 * EN: The chosen state's abbreviation tag on the map.
 *
 * @param {Tema} tema
 * @param {string} sigla
 * @returns {Record<string, unknown>}
 */
export function etiquetaDaEscolhida(tema, sigla) {
  return {
    show: true,
    formatter: sigla,
    color: hex("color.text.primary", tema),
    backgroundColor: hex("color.chart.surface", tema),
    borderColor: hex("color.text.primary", tema),
    borderWidth: 1,
    borderRadius: 4,
    padding: [2, 6],
    fontSize: 12,
    fontWeight: 600,
  };
}

/**
 * PT: O preenchimento de quem fica fora da comparação: a superfície do
 *     cartão com listras diagonais na cor da borda forte.
 * EN: The fill for states outside the comparison: striped card surface.
 *
 * @param {Tema} tema
 * @returns {{ cor: string, textura: Record<string, unknown> }}
 */
export function semComparacao(tema) {
  return {
    cor: hex("color.chart.surface", tema),
    textura: {
      symbol: "rect",
      dashArrayX: [1, 0],
      dashArrayY: [1, 6],
      rotation: -Math.PI / 4,
      color: hex("color.border.strong", tema),
    },
  };
}
