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
import { destaque } from "./selecao.js";
import { hex, paletas } from "./tema.js";

/** @typedef {import("./grafico.js").Grafico} Grafico */

/**
 * @typedef {object} ItemDoRanking
 * @property {string} rotulo O nome no eixo / axis label
 * @property {number} valor
 * @property {string} [chave] Identifica o item para a seleção, como a sigla da UF / selection key
 */

/**
 * @typedef {object} DadosDoRanking
 * @property {ItemDoRanking[]} itens
 * @property {(v: number) => string} formatar
 * @property {{ valor: number, rotulo: string }} [referencia]
 * @property {(chave: string) => void} [aoSelecionar] Clique numa barra / bar click
 * @property {string | null} [selecionada] A chave destacada no começo / initially selected key
 */

/**
 * @typedef {import("./selecao.js").GraficoDeUf<DadosDoRanking> & {
 *   posicaoDe: (chave: string) => number | null,
 * }} GraficoDoRanking
 */

// PT: as margens verticais da área de desenho, com e sem a linha de referência
// EN: the plot area's vertical margins, with and without the reference line
const MARGEM_DE_CIMA = { comReferencia: 24, semReferencia: 8 };
const MARGEM_DE_BAIXO = 8;

/**
 * PT: Desenha o ranking. A altura do elemento acompanha o número de itens,
 *     pela variável `--itens`, que o CSS usa. O item escolhido ganha a borda
 *     na cor do texto, e um clique numa barra avisa `aoSelecionar` (RF-102).
 * EN: Draws the ranking; element height follows the item count. The chosen
 *     item gets the highlight border, and bar clicks call `aoSelecionar`.
 *
 * @param {HTMLElement} el
 * @param {DadosDoRanking} inicial
 * @returns {Promise<GraficoDoRanking>}
 */
export async function ranking(el, inicial) {
  let dados = inicial;
  let escolhida = inicial.selecionada ?? null;
  const ordenados = () => [...dados.itens].sort((a, b) => b.valor - a.valor);
  el.style.setProperty("--itens", String(dados.itens.length));

  const grafico = await criarGrafico(el, (tema) => {
    const [cor] = paletas(tema).categorica;
    const secundario = hex("color.text.secondary", tema);
    const itens = ordenados();
    const { referencia, formatar } = dados;
    return {
      grid: {
        left: 8,
        right: 88,
        top: referencia ? MARGEM_DE_CIMA.comReferencia : MARGEM_DE_CIMA.semReferencia,
        bottom: MARGEM_DE_BAIXO,
        containLabel: true,
      },
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ name: string, value: number }} */ p) =>
          `${p.name}: ${formatar(p.value)}`,
      },
      xAxis: { type: "value", show: false, splitLine: { show: false } },
      yAxis: {
        type: "category",
        inverse: true,
        data: itens.map((item) => item.rotulo),
        axisLine: { show: false },
      },
      series: [
        {
          type: "bar",
          data: itens.map((item) => ({
            value: item.valor,
            chave: item.chave,
            ...(item.chave !== undefined && item.chave === escolhida
              ? { itemStyle: { color: cor, borderRadius: [0, 4, 4, 0], ...destaque(tema) } }
              : {}),
          })),
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

  grafico.instancia.on("click", (p) => {
    const dado = /** @type {{ chave?: string } | null | undefined} */ (p.data);
    if (dado?.chave) dados.aoSelecionar?.(dado.chave);
  });

  return {
    ...grafico,
    selecionar(chave) {
      escolhida = chave;
      grafico.atualizar();
    },
    mudar(novos) {
      dados = { ...dados, ...novos };
      el.style.setProperty("--itens", String(dados.itens.length));
      grafico.atualizar();
    },
    /**
     * PT: A posição vertical do centro da barra, em px a partir do topo do
     *     gráfico, pela ordem dos itens e pela altura da área de desenho.
     *     Serve para rolar a lista até o item escolhido.
     * EN: The bar center's vertical position, from item order and plot height.
     */
    posicaoDe(chave) {
      const itens = ordenados();
      const indice = itens.findIndex((item) => item.chave === chave);
      if (indice < 0) return null;
      const topo = dados.referencia ? MARGEM_DE_CIMA.comReferencia : MARGEM_DE_CIMA.semReferencia;
      const faixa = (el.clientHeight - topo - MARGEM_DE_BAIXO) / itens.length;
      return topo + (indice + 0.5) * faixa;
    },
  };
}
