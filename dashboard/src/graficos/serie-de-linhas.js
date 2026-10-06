/**
 * PT: Série mensal com duas medidas, um marco e uma janela (#70).
 *
 *     Feita para o painel da UF na Tela 2: a taxa de inadimplência e a de
 *     ativo problemático, mês a mês, para o leitor ver as duas andarem
 *     juntas ou se afastarem. A primeira linha é a medida principal, sólida,
 *     na primeira cor da paleta categórica, como a série temporal; a
 *     segunda é a de comparação, tracejada e no cinza do texto secundário,
 *     para a diferença vir também da forma, e não só da cor. As duas têm
 *     legenda e o último valor escrito na ponta.
 *
 *     - **O marco** é uma linha vertical num mês, com um rótulo curto, como a
 *       mudança de critério do ativo problemático em jan/2025 (RF-203).
 *     - **A janela** é uma faixa clara entre dois meses, como os 6 meses que
 *       a decisão compara (ADR 0014, decisão 3).
 *
 * EN: Monthly series with two measures, a milestone and a window: the main
 *     measure solid in the first categorical color, the comparison dashed in
 *     secondary-text gray; a vertical milestone line and a shaded window.
 */

import { mesCurto } from "../formatos.js";
import { criarGrafico } from "./grafico.js";
import { hex, paletas } from "./tema.js";

/** @typedef {import("./grafico.js").Grafico} Grafico */

/** PT: espessura das linhas, em px, a mesma da série temporal / EN: line width */
const LARGURA_DA_LINHA = 3;

/**
 * @typedef {object} LinhaDaSerie
 * @property {string} nome Na legenda e na dica / legend and tooltip name
 * @property {(number | null)[]} valores Um por mês / one per month
 */

/**
 * @typedef {object} DadosDasLinhas
 * @property {string[]} meses `aaaa-mm-dd`
 * @property {[LinhaDaSerie, LinhaDaSerie]} linhas A principal e a de comparação / main and comparison
 * @property {(v: number) => string} formatar Na dica e na ponta das linhas / tooltip and line ends
 * @property {(v: number) => string} [formatarEixo] No eixo; o padrão é `formatar` / axis labels
 * @property {{ mes: string, rotulo: string }} [marco] Linha vertical num mês / vertical line
 * @property {{ de: string, ate: string, rotulo: string }} [janela] Faixa entre dois meses / shaded span
 */

/**
 * PT: Desenha a série no elemento.
 * EN: Draws the series.
 *
 * @param {HTMLElement} el
 * @param {DadosDasLinhas} dados
 * @returns {Promise<Grafico>}
 */
export function serieDeLinhas(el, { meses, linhas, formatar, formatarEixo, marco, janela }) {
  const categorias = meses.map(mesCurto);
  const posicao = (/** @type {string} */ mes) => categorias[meses.indexOf(mes)];
  const [principal, comparacao] = linhas;

  return criarGrafico(el, (tema) => {
    const [cor] = paletas(tema).categorica;
    const cinza = hex("color.text.secondary", tema);
    const forte = hex("color.text.primary", tema);
    /**
     * @param {LinhaDaSerie} linha
     * @param {string} corDaLinha
     * @param {boolean} tracejada
     */
    const serie = (linha, corDaLinha, tracejada) => ({
      type: "line",
      name: linha.nome,
      data: linha.valores,
      itemStyle: { color: corDaLinha },
      lineStyle: {
        color: corDaLinha,
        width: LARGURA_DA_LINHA,
        ...(tracejada ? { type: [6, 4] } : {}),
      },
      symbol: "none",
      // PT: o último valor na ponta, na cor da linha, sem precisar da dica
      // EN: the last value at the line end, in the line's color
      endLabel: {
        show: true,
        formatter: (/** @type {{ value: number }} */ p) => formatar(p.value),
        color: corDaLinha,
        fontWeight: 600,
      },
    });
    const primeira = serie(principal, cor, false);
    return {
      legend: {
        top: 0,
        left: 0,
        itemWidth: 32,
        // PT: sem o ponto no ícone, para a linha tracejada aparecer
        // EN: no marker in the icon, so the dash shows
        itemStyle: { opacity: 0 },
        data: [principal.nome, comparacao.nome],
      },
      grid: { left: 8, right: 48, top: 56, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        valueFormatter: (/** @type {number | null} */ v) => (v === null ? "–" : formatar(v)),
      },
      xAxis: {
        type: "category",
        data: categorias,
        boundaryGap: false,
        axisLabel: { hideOverlap: true, alignMinLabel: "left", alignMaxLabel: "right" },
      },
      yAxis: {
        type: "value",
        scale: true,
        axisLabel: { formatter: formatarEixo ?? formatar },
      },
      series: [
        {
          ...primeira,
          ...(marco
            ? {
                markLine: {
                  silent: true,
                  symbol: "none",
                  lineStyle: { color: forte, type: [3, 3], width: 1 },
                  label: { position: "end", formatter: marco.rotulo, color: forte },
                  data: [{ xAxis: posicao(marco.mes) }],
                },
              }
            : {}),
          ...(janela
            ? {
                markArea: {
                  silent: true,
                  itemStyle: { color: cor, opacity: 0.08 },
                  label: { position: "insideTop", formatter: janela.rotulo, color: cor },
                  data: [[{ xAxis: posicao(janela.de) }, { xAxis: posicao(janela.ate) }]],
                },
              }
            : {}),
        },
        serie(comparacao, cinza, true),
      ],
    };
  });
}
