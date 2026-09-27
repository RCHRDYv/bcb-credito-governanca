/**
 * PT: Série temporal com projeção, na notação IBCS.
 *
 *     A notação IBCS separa o que aconteceu do que se espera pela forma, e
 *     não pela cor: o realizado é uma linha sólida, e a projeção é uma
 *     linha tracejada com o intervalo hachurado em volta. As duas usam a
 *     primeira cor da paleta categórica, a mesma das barras do ranking, com
 *     linha de 3 px (decidido em 2026-09-27, na revisão visual da #63). A
 *     projeção começa no último mês realizado, para a linha não ter um salto.
 *
 * EN: Time series with a projection in IBCS notation: actuals as a solid
 *     line, the projection dashed with a hatched interval, told apart by
 *     form; both in the first categorical color, 3 px wide.
 */

import { mesCurto } from "../formatos.js";
import { t } from "../textos/index.js";
import { criarGrafico } from "./grafico.js";
import { paletas } from "./tema.js";

/** @typedef {import("./grafico.js").Grafico} Grafico */

/** PT: espessura das linhas, em px / EN: line width */
const LARGURA_DA_LINHA = 3;

/**
 * @typedef {object} Projecao
 * @property {string[]} meses `aaaa-mm-dd`, depois do último realizado / after the last actual
 * @property {number[]} valor O valor projetado / projected value
 * @property {number[]} inferior Limite inferior do intervalo / lower bound
 * @property {number[]} superior Limite superior do intervalo / upper bound
 * @property {string} rotulo O que a projeção é, como "Projeção ilustrativa" / label
 */

/**
 * @typedef {object} DadosDaSerie
 * @property {string} nome O nome da série, para a dica / series name
 * @property {string[]} meses `aaaa-mm-dd`
 * @property {number[]} valores
 * @property {(v: number) => string} formatar
 * @property {Projecao} [projecao]
 */

/**
 * PT: Converte `#rrggbb` em `rgba()`, para a textura da hachura.
 * EN: `#rrggbb` to `rgba()`, for the hatch texture.
 *
 * @param {string} cor
 * @param {number} alpha
 * @returns {string}
 */
function comAlpha(cor, alpha) {
  const [r, g, b] = [1, 3, 5].map((i) => Number.parseInt(cor.slice(i, i + 2), 16));
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * PT: Desenha a série no elemento.
 * EN: Draws the series.
 *
 * @param {HTMLElement} el
 * @param {DadosDaSerie} dados
 * @returns {Promise<Grafico>}
 */
export function serieTemporal(el, { nome, meses, valores, formatar, projecao }) {
  const ultimo = valores.length - 1;
  const futuros = projecao?.meses.length ?? 0;
  const vazio = Array.from({ length: ultimo }, () => null);
  const categorias = [...meses, ...(projecao?.meses ?? [])].map(mesCurto);

  return criarGrafico(el, (tema, { estreito }) => {
    const [cor] = paletas(tema).categorica;
    /** @type {Record<string, unknown>[]} */
    const series = [
      {
        type: "line",
        name: nome,
        data: [...valores, ...Array.from({ length: futuros }, () => null)],
        itemStyle: { color: cor },
        lineStyle: { color: cor, width: LARGURA_DA_LINHA },
        symbol: "none",
      },
    ];
    if (projecao) {
      series.push(
        {
          type: "line",
          name: projecao.rotulo,
          data: [...vazio, valores[ultimo], ...projecao.valor],
          itemStyle: { color: cor },
          lineStyle: { color: cor, width: LARGURA_DA_LINHA, type: [6, 4] },
          symbol: "none",
        },
        // PT: o intervalo é a diferença entre o limite superior e o inferior,
        //     empilhada sobre o inferior, que fica invisível
        // EN: the interval is upper minus lower, stacked on an invisible lower
        {
          type: "line",
          name: "inferior",
          stack: "intervalo",
          data: [...vazio, valores[ultimo], ...projecao.inferior],
          lineStyle: { opacity: 0 },
          symbol: "none",
          silent: true,
          tooltip: { show: false },
        },
        {
          type: "line",
          name: "intervalo",
          stack: "intervalo",
          data: [...vazio, 0, ...projecao.superior.map((s, i) => s - projecao.inferior[i])],
          lineStyle: { opacity: 0 },
          symbol: "none",
          silent: true,
          tooltip: { show: false },
          areaStyle: { color: cor, opacity: 0.1 },
          itemStyle: {
            decal: {
              symbol: "rect",
              dashArrayX: [1, 0],
              dashArrayY: [2, 5],
              rotation: -Math.PI / 4,
              color: comAlpha(cor, 0.5),
            },
          },
        },
      );
    }
    return {
      // PT: a legenda mostra a forma de cada linha: sólida é o realizado e
      //     tracejada é a projeção. Sem projeção, o título já diz o que é a linha
      // EN: the legend shows each line's form; none without a projection
      legend: projecao
        ? {
            top: 0,
            left: 0,
            itemWidth: 32,
            // PT: sem o ponto no ícone, para a linha tracejada aparecer
            // EN: no marker in the icon, so the dash shows
            itemStyle: { opacity: 0 },
            data: [nome, projecao.rotulo],
          }
        : { show: false },
      // PT: em tela estreita, a legenda quebra em duas linhas e pede mais espaço
      // EN: narrow: the legend wraps into two lines
      grid: {
        left: 8,
        right: 16,
        top: projecao ? (estreito ? 64 : 40) : 16,
        bottom: 8,
        containLabel: true,
      },
      tooltip: {
        trigger: "axis",
        formatter: (/** @type {{ dataIndex: number, name: string }[]} */ pontos) => {
          const i = pontos[0]?.dataIndex ?? 0;
          if (!projecao || i <= ultimo) return `${categorias[i]}: ${formatar(valores[i])}`;
          const k = i - ultimo - 1;
          return `${categorias[i]}: ${formatar(projecao.valor[k])}<br>${t("grafico.intervalo", {
            de: formatar(projecao.inferior[k]),
            ate: formatar(projecao.superior[k]),
          })}`;
        },
      },
      xAxis: {
        type: "category",
        data: categorias,
        boundaryGap: false,
        // PT: o primeiro e o último mês alinham para dentro, sem cortar na borda
        // EN: first and last labels align inwards
        axisLabel: { hideOverlap: true, alignMinLabel: "left", alignMaxLabel: "right" },
      },
      yAxis: { type: "value", scale: true, axisLabel: { formatter: formatar } },
      series,
    };
  });
}
