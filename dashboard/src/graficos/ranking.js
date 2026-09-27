/**
 * PT: Ranking em barras horizontais, do maior para o menor.
 *
 *     Os itens são uma série só, então todas as barras têm a mesma cor, a
 *     primeira da paleta categórica: pintar cada barra de uma cor gastaria
 *     a cor para repetir o que o comprimento já mostra. Cada barra traz o
 *     valor na ponta, e uma linha de referência opcional, como a mediana,
 *     mostra onde cada item fica em relação a ela.
 *
 * EN: Horizontal bar ranking, largest first, in a single color with the
 *     value at each bar's end and an optional reference line.
 */

import { criarGrafico } from "./grafico.js";
import { hex, paletas } from "./tema.js";

/** @typedef {import("./grafico.js").Grafico} Grafico */

/**
 * @typedef {object} DadosDoRanking
 * @property {{ rotulo: string, valor: number }[]} itens
 * @property {(v: number) => string} formatar
 * @property {{ valor: number, rotulo: string }} [referencia]
 */

/**
 * PT: Desenha o ranking. A altura do elemento acompanha o número de itens,
 *     pela variável `--itens`, que o CSS usa.
 * EN: Draws the ranking; element height follows the item count.
 *
 * @param {HTMLElement} el
 * @param {DadosDoRanking} dados
 * @returns {Promise<Grafico>}
 */
export function ranking(el, { itens, formatar, referencia }) {
  const ordenados = [...itens].sort((a, b) => b.valor - a.valor);
  el.style.setProperty("--itens", String(ordenados.length));

  return criarGrafico(el, (tema) => {
    const [cor] = paletas(tema).categorica;
    const secundario = hex("color.text.secondary", tema);
    return {
      grid: { left: 8, right: 88, top: referencia ? 24 : 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ name: string, value: number }} */ p) =>
          `${p.name}: ${formatar(p.value)}`,
      },
      xAxis: { type: "value", show: false, splitLine: { show: false } },
      yAxis: {
        type: "category",
        inverse: true,
        data: ordenados.map((item) => item.rotulo),
        axisLine: { show: false },
      },
      series: [
        {
          type: "bar",
          data: ordenados.map((item) => item.valor),
          barWidth: 16,
          // PT: a ponta de dado arredondada, e a base reta, presa ao eixo
          // EN: rounded data end, square base
          itemStyle: { color: cor, borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: "right",
            color: secundario,
            formatter: (/** @type {{ value: number }} */ p) => formatar(p.value),
          },
          ...(referencia
            ? {
                markLine: {
                  silent: true,
                  symbol: "none",
                  lineStyle: { color: hex("color.border.strong", tema), type: [4, 4], width: 1 },
                  // PT: com o eixo invertido, o início da linha é o topo / EN: inverted axis: start is the top
                  label: { position: "start", formatter: referencia.rotulo, color: secundario },
                  data: [{ xAxis: referencia.valor }],
                },
              }
            : {}),
        },
      ],
    };
  });
}
