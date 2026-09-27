/**
 * PT: A matriz 2x2 de espaço contra risco (ADR 0014).
 *
 *     Cada ponto é uma célula de UF e modalidade. O eixo horizontal é a
 *     carteira por empresa em relação à mediana das UFs, em escala de base
 *     2: 1 é a mediana, 0,5 é metade e 2 é o dobro. O eixo vertical é quanto
 *     a inadimplência variou além da variação do país.
 *
 *     Os dois eixos são invertidos (decidido em 2026-09-27, na revisão
 *     visual da #63), para Entrar ficar no canto superior direito e Não
 *     entrar no inferior esquerdo: à direita do 1, a carteira por empresa é
 *     menor que a mediana e o espaço é alto; acima do zero, o risco da UF
 *     piorou menos que o do país.
 *
 *     Os quadrantes aparecem por três caminhos, e nunca só pela cor: a
 *     posição em relação às duas linhas de corte, a etiqueta com ícone e
 *     nome em cada canto, e a dica de cada ponto.
 *
 * EN: The space-versus-risk 2x2 matrix. X is portfolio per company relative
 *     to the state median (log base 2); Y is the default-rate change beyond
 *     the country's. Both axes are inverted so Entrar sits top right and
 *     Não entrar bottom left. Quadrants read by position, corner labels with
 *     icon and name, and tooltips, never by color alone.
 */

import { etiquetaDeQuadrante, nomeDoQuadrante } from "../componentes/etiqueta-de-quadrante.js";
import { elemento } from "../dom.js";
import { numero, pontos, vezes } from "../formatos.js";
import { t } from "../textos/index.js";
import { echarts } from "./echarts.js";
import { criarGrafico } from "./grafico.js";
import { hex } from "./tema.js";

/** @typedef {import("./grafico.js").Grafico} Grafico */
/** @typedef {import("../componentes/etiqueta-de-quadrante.js").Quadrante} Quadrante */

/**
 * @typedef {object} Celula
 * @property {string} uf
 * @property {string} modalidade
 * @property {number} indice_de_espaco Carteira por empresa sobre a mediana / ratio to median
 * @property {number} desvio_do_risco Fração: variação da UF menos a do país / fraction
 * @property {string} quadrante Como no mart: "entrar", "observar", "não entrar" ou "manter"
 */

/** PT: ordem fixa dos quadrantes / EN: fixed quadrant order */
const QUADRANTES = /** @type {const} */ ([
  ["entrar", "entrar"],
  ["observar", "observar"],
  ["não entrar", "nao-entrar"],
  ["manter", "manter"],
]);

/**
 * PT: Onde fica cada etiqueta: o canto do quadrante na área do gráfico.
 * EN: Where each label goes: the quadrant's corner of the plot area.
 *
 * @type {Record<Quadrante, string>}
 */
const CANTOS = {
  entrar: "superior-direito",
  manter: "superior-esquerdo",
  observar: "inferior-direito",
  "nao-entrar": "inferior-esquerdo",
};

/** PT: margens da área de desenho, em px / EN: plot margins */
const MARGENS = { esquerda: 64, direita: 16, topo: 16, base: 56 };

/**
 * PT: A etiqueta de quadrante do design system (#64), posta no canto do
 *     quadrante.
 * EN: The design system quadrant tag, placed at the quadrant corner.
 *
 * @param {Quadrante} quadrante
 * @returns {HTMLElement}
 */
function etiqueta(quadrante) {
  return elemento("span", { classe: `matriz__canto matriz__canto--${CANTOS[quadrante]}` }, [
    etiquetaDeQuadrante(quadrante),
  ]);
}

/**
 * PT: Monta a matriz: a área do gráfico com as quatro etiquetas por cima.
 *     Devolve o elemento, para ir no cartão, e o gráfico, que nasce quando
 *     o elemento já está na página.
 * EN: Builds the matrix element (plot plus corner labels) and its chart.
 *
 * @param {HTMLElement} el Um elemento vazio, já na página / empty element on the page
 * @param {{ celulas: Celula[] }} dados
 * @returns {Promise<Grafico>}
 */
export function matriz(el, { celulas }) {
  el.classList.add("matriz");
  for (const [lado, valor] of Object.entries(MARGENS)) {
    el.style.setProperty(`--matriz-${lado}`, `${valor}px`);
  }
  const area = elemento("div", { classe: "grafico grafico--matriz" });
  el.replaceChildren(area, ...QUADRANTES.map(([, chave]) => etiqueta(chave)));

  return criarGrafico(area, (tema, { estreito }) => {
    const corte = { color: hex("color.border.strong", tema), width: 1, type: "solid" };
    // PT: em tela estreita, as margens encolhem, os nomes dos eixos ficam
    //     curtos, o eixo de base 2 mostra só 0,25, 1 e 4, e as etiquetas
    //     descem para baixo do gráfico, pela consulta de contêiner do CSS
    // EN: narrow: smaller margins, short axis names, fewer ticks; the CSS
    //     container query moves the labels below the plot
    const marcas = (/** @type {number} */ v) =>
      !estreito || [0.25, 1, 4].includes(v)
        ? `${v.toLocaleString("pt-BR", { maximumFractionDigits: 3 })}×`
        : "";
    return {
      grid: estreito
        ? { left: 44, right: 12, top: 12, bottom: 44 }
        : {
            left: MARGENS.esquerda,
            right: MARGENS.direita,
            top: MARGENS.topo,
            bottom: MARGENS.base,
          },
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ data: { celula: Celula } }} */ p) => {
          const c = p.data.celula;
          const nome = QUADRANTES.find(([doMart]) => doMart === c.quadrante)?.[1];
          return [
            `<strong>${echarts.format.encodeHTML(`${c.uf} · ${c.modalidade}`)}</strong>`,
            `${t("matriz.eixo-espaco-curto")}: ${vezes(c.indice_de_espaco)}`,
            `${t("matriz.eixo-risco-curto")}: ${pontos(c.desvio_do_risco)}`,
            nome ? nomeDoQuadrante(nome) : "",
          ].join("<br>");
        },
      },
      xAxis: {
        type: "log",
        inverse: true,
        logBase: 2,
        min: 0.125,
        max: 8,
        name: t(estreito ? "matriz.eixo-espaco-estreito" : "matriz.eixo-espaco"),
        nameLocation: "middle",
        nameGap: estreito ? 28 : 32,
        axisLabel: { formatter: marcas },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        inverse: true,
        name: t(estreito ? "matriz.eixo-risco-estreito" : "matriz.eixo-risco"),
        nameLocation: "middle",
        nameGap: estreito ? 28 : 48,
        axisLabel: { formatter: (/** @type {number} */ v) => `${v > 0 ? "+" : ""}${numero(v, 0)}` },
        splitLine: { show: false },
      },
      series: QUADRANTES.map(([doMart, chave], i) => ({
        type: "scatter",
        name: nomeDoQuadrante(chave),
        itemStyle: { color: hex(`color.quadrante.${chave}.marca`, tema) },
        data: celulas
          .filter((c) => c.quadrante === doMart)
          .map((c) => ({ value: [c.indice_de_espaco, c.desvio_do_risco * 100], celula: c })),
        ...(i === 0
          ? {
              markLine: {
                silent: true,
                symbol: "none",
                label: { show: false },
                lineStyle: corte,
                data: [{ xAxis: 1 }, { yAxis: 0 }],
              },
            }
          : {}),
      })),
    };
  });
}
