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
 *     A projeção também pode partir de um mês no meio da série, a origem.
 *     É o gráfico do teste da Tela 3 (#72): o realizado continua depois da
 *     origem, e a linha tracejada mostra o que a projeção dizia naqueles
 *     meses, para comparar as duas. A origem pode ganhar uma linha vertical.
 *
 * EN: Time series with a projection in IBCS notation: actuals as a solid
 *     line, the projection dashed with a hatched interval, told apart by
 *     form; both in the first categorical color, 3 px wide. The projection
 *     may start mid-series (an origin), so actuals and the old projection
 *     overlap, as in Screen 3's backtest chart.
 */

import { mesCurto } from "../formatos.js";
import { t } from "../textos/index.js";
import { criarGrafico } from "./grafico.js";
import { hex, paletas } from "./tema.js";

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
 * @property {string} [origem] `aaaa-mm-dd`: o mês realizado de onde a projeção parte; o padrão é o último / start month, default the last actual
 * @property {string} [rotuloDaOrigem] O rótulo da linha vertical na origem; sem ele, não há linha / label of the vertical line at the origin
 * @property {(de: string, ate: string) => string} [intervalo] Como a dica escreve o intervalo / how the tooltip writes the interval
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
  const futuros = (projecao?.meses ?? []).filter((mes) => !meses.includes(mes));
  const todos = [...meses, ...futuros];
  const categorias = todos.map(mesCurto);
  const origem = projecao?.origem ? meses.indexOf(projecao.origem) : valores.length - 1;
  if (origem < 0) throw new Error(`Origem fora da série: ${projecao?.origem}`);

  /**
   * PT: Uma coluna da projeção na posição de cada mês, nula fora dela, com
   *     o valor da origem, para a linha sair do realizado.
   * EN: A projection column placed by month, null elsewhere, with the
   *     origin's value so the line leaves from the actuals.
   *
   * @param {number[]} coluna
   * @param {number} naOrigem
   * @returns {(number | null)[]}
   */
  const naPosicao = (coluna, naOrigem) => {
    /** @type {(number | null)[]} */
    const linha = todos.map(() => null);
    linha[origem] = naOrigem;
    for (const [k, mes] of (projecao?.meses ?? []).entries()) {
      linha[todos.indexOf(mes)] = coluna[k];
    }
    return linha;
  };
  const intervalo =
    projecao?.intervalo ??
    ((/** @type {string} */ de, /** @type {string} */ ate) => t("grafico.intervalo", { de, ate }));

  return criarGrafico(el, (tema, { estreito }) => {
    const [cor] = paletas(tema).categorica;
    /** @type {Record<string, unknown>[]} */
    const series = [
      {
        type: "line",
        name: nome,
        data: [...valores, ...futuros.map(() => null)],
        itemStyle: { color: cor },
        lineStyle: { color: cor, width: LARGURA_DA_LINHA },
        symbol: "none",
      },
    ];
    if (projecao) {
      const forte = hex("color.text.primary", tema);
      series.push(
        {
          type: "line",
          name: projecao.rotulo,
          data: naPosicao(projecao.valor, valores[origem]),
          itemStyle: { color: cor },
          lineStyle: { color: cor, width: LARGURA_DA_LINHA, type: [6, 4] },
          symbol: "none",
          ...(projecao.rotuloDaOrigem
            ? {
                markLine: {
                  silent: true,
                  symbol: "none",
                  lineStyle: { color: forte, type: [3, 3], width: 1 },
                  label: { position: "end", formatter: projecao.rotuloDaOrigem, color: forte },
                  data: [{ xAxis: categorias[origem] }],
                },
              }
            : {}),
        },
        // PT: o intervalo é a diferença entre o limite superior e o inferior,
        //     empilhada sobre o inferior, que fica invisível
        // EN: the interval is upper minus lower, stacked on an invisible lower
        {
          type: "line",
          name: "inferior",
          stack: "intervalo",
          data: naPosicao(projecao.inferior, valores[origem]),
          lineStyle: { opacity: 0 },
          symbol: "none",
          silent: true,
          tooltip: { show: false },
        },
        {
          type: "line",
          name: "intervalo",
          stack: "intervalo",
          data: naPosicao(
            projecao.superior.map((s, i) => s - projecao.inferior[i]),
            0,
          ),
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
          const k = projecao ? projecao.meses.indexOf(todos[i]) : -1;
          const realizado = i < valores.length ? formatar(valores[i]) : null;
          if (!projecao || k < 0) return `${categorias[i]}: ${realizado}`;
          const faixa = intervalo(formatar(projecao.inferior[k]), formatar(projecao.superior[k]));
          if (realizado === null) {
            return `${categorias[i]}: ${formatar(projecao.valor[k])}<br>${faixa}`;
          }
          // PT: no gráfico do teste, o mês tem o realizado e a projeção
          // EN: in the backtest chart, the month has both
          const projetado = formatar(projecao.valor[k]);
          return `${categorias[i]}<br>${nome}: ${realizado}<br>${projecao.rotulo}: ${projetado}<br>${faixa}`;
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
      // PT: em gráfico estreito, menos marcas no eixo, para os valores não se amontoarem
      // EN: fewer axis ticks on narrow charts
      yAxis: {
        type: "value",
        scale: true,
        splitNumber: estreito ? 3 : 5,
        axisLabel: { formatter: formatar },
      },
      series,
    };
  });
}
