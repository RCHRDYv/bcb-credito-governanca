/**
 * PT: O marcador de alerta antecipado dentro dos gráficos (#70).
 *
 *     A etiqueta de alerta antecipado, com sino e texto, não cabe sobre uma
 *     UF no mapa, na grade ou ao lado de uma barra. Nesses lugares, o alerta
 *     vira um marcador redondo, nas cores da etiqueta: o fundo e o anel do
 *     par de atenção do Carbon, que o design system reserva para o alerta
 *     (revisão do mockup da Tela 2, em 2026-10-06). O marcador nunca muda a
 *     cor da área nem o quadrante (ADR 0014, decisão 6).
 *
 *     É texto rico do ECharts: uma caixa vazia, com fundo, borda e cantos
 *     redondos, sem imagem, para a política de segurança não precisar de
 *     exceção.
 *
 * EN: The early-warning marker inside charts: a round marker in the
 *     early-warning tag's colors, drawn as ECharts rich text with no image.
 */

import { hex } from "./tema.js";

/** @typedef {import("../tokens.js").Tema} Tema */

/** PT: o lado do marcador, em px / EN: marker size, px */
const LADO = 10;

/**
 * PT: O estilo do marcador, para o `rich` de um rótulo do ECharts, com o
 *     nome `alerta`.
 * EN: The marker style, for an ECharts label `rich`, named `alerta`.
 *
 * @param {Tema} tema
 * @returns {{ alerta: Record<string, unknown> }}
 */
export function estiloDaMarca(tema) {
  return {
    alerta: {
      width: LADO,
      height: LADO,
      borderRadius: LADO / 2,
      backgroundColor: hex("color.alerta-antecipado.fundo", tema),
      borderColor: hex("color.alerta-antecipado.texto", tema),
      borderWidth: 2,
    },
  };
}

/** PT: o marcador num texto rico / EN: the marker in rich text */
export const MARCA = "{alerta|}";
