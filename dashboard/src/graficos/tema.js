/**
 * PT: O tema dos gráficos, montado a partir dos tokens do design system.
 *
 *     O ECharts não lê variáveis CSS, então o tema é montado em JavaScript
 *     (ADR 0017). Todas as cores vêm do `tokens.json` gerado, pela função
 *     `cor()`, e nenhum hex é digitado aqui: se um token muda, o gráfico
 *     muda junto. Existem dois temas, claro e escuro, com os mesmos papéis.
 *
 *     O gráfico é desenhado sobre o vidro regular. Como o vidro é
 *     transparente, a cor que o olho vê atrás das marcas é o vidro composto
 *     sobre o fundo da página, e é contra ela que o contraste é medido.
 *
 * EN: The chart theme, built from the design system tokens. ECharts cannot
 *     read CSS variables, so the theme is assembled here from the generated
 *     token list; no hex is typed in this file. Charts sit on the regular
 *     glass, so contrast is measured against the glass composited over the
 *     page background.
 */

import { compor } from "../cor/contraste.js";
import { cor, token } from "../tokens.js";

/** @typedef {import("../tokens.js").Tema} Tema */

/**
 * @typedef {object} Divergente
 * @property {string[]} negativo Do meio para a ponta / from the middle outwards
 * @property {string} neutro
 * @property {string[]} positivo Do meio para a ponta / from the middle outwards
 */

/**
 * @typedef {object} Paletas
 * @property {string[]} categorica Na ordem fixa das séries / fixed series order
 * @property {string[]} sequencial Do valor baixo ao alto / low to high
 * @property {Divergente} divergente
 * @property {string} outros Cinza da série "Outros" / gray for "Outros"
 */

/** PT: nomes com que os temas são registrados / EN: registered theme names */
export const NOMES_DOS_TEMAS = Object.freeze({
  claro: "credito-pj-claro",
  escuro: "credito-pj-escuro",
});

/**
 * PT: O hex opaco de um token de cor num tema. Se a cor for transparente, é
 *     composta sobre o fundo da página.
 * EN: A color token's opaque hex in a theme.
 *
 * @param {string} caminho
 * @param {Tema} tema
 * @returns {string}
 */
export function hex(caminho, tema) {
  const valor = cor(caminho, tema);
  return valor.alpha < 1 ? compor(valor, cor("color.background.page", tema).hex) : valor.hex;
}

/**
 * PT: As superfícies onde um gráfico pode ser desenhado: o vidro regular
 *     composto sobre a página, e a camada sólida que o substitui quando o
 *     navegador não tem `backdrop-filter` e na impressão.
 * EN: The surfaces a chart can sit on.
 *
 * @param {Tema} tema
 * @returns {{ vidro: string, solida: string }}
 */
export function superficies(tema) {
  return {
    vidro: hex("material.vidro.regular.preenchimento", tema),
    solida: hex("color.background.layer", tema),
  };
}

/**
 * PT: Quantos degraus cada paleta tem nos tokens.
 * EN: How many steps each palette has in the tokens.
 */
export const DEGRAUS = Object.freeze({ categorica: 6, sequencial: 5, divergente: 3 });

/**
 * PT: As paletas de gráfico de um tema, lidas dos tokens `color.chart.*`.
 * EN: A theme's chart palettes, read from the `color.chart.*` tokens.
 *
 * @param {Tema} tema
 * @returns {Paletas}
 */
export function paletas(tema) {
  const serie = (/** @type {string} */ prefixo, /** @type {number} */ n) =>
    Array.from({ length: n }, (_, i) => hex(`${prefixo}.${i + 1}`, tema));
  return {
    categorica: serie("color.chart.categorical", DEGRAUS.categorica),
    sequencial: serie("color.chart.sequential", DEGRAUS.sequencial),
    divergente: {
      negativo: serie("color.chart.diverging.negative", DEGRAUS.divergente),
      neutro: hex("color.chart.diverging.neutral", tema),
      positivo: serie("color.chart.diverging.positive", DEGRAUS.divergente),
    },
    outros: hex("color.chart.other", tema),
  };
}

/**
 * PT: Monta o objeto de tema do ECharts para um tema do design system.
 *     A paleta categórica pode ser trocada, o que só a página de revisão das
 *     paletas usa, para comparar candidatas com o mesmo tema.
 * EN: Builds the ECharts theme object. The categorical palette can be
 *     overridden, used only to compare candidate palettes.
 *
 * @param {Tema} tema
 * @param {{ categorica?: string[] }} [troca]
 * @returns {Record<string, unknown>}
 */
export function montarTema(tema, troca = {}) {
  const texto = hex("color.text.primary", tema);
  const textoSecundario = hex("color.text.secondary", tema);
  const bordaSutil = hex("color.border.subtle", tema);
  const bordaForte = hex("color.border.strong", tema);
  const fundo = hex("color.background.page", tema);
  const { vidro } = superficies(tema);
  const fonte = token("font.family.sans").css;
  const categorica = troca.categorica ?? paletas(tema).categorica;

  const rotulo = { color: textoSecundario, fontFamily: fonte, fontSize: 12 };
  const eixo = {
    axisLine: { show: true, lineStyle: { color: bordaForte, width: 1 } },
    axisTick: { show: false },
    axisLabel: { ...rotulo },
    splitLine: { show: true, lineStyle: { color: bordaSutil, width: 1 } },
    nameTextStyle: { ...rotulo },
  };

  return {
    color: categorica,
    backgroundColor: "transparent",
    textStyle: { color: texto, fontFamily: fonte, fontSize: 12 },
    legend: {
      textStyle: { ...rotulo },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 16,
      inactiveColor: bordaSutil,
    },
    tooltip: {
      backgroundColor: vidro,
      borderColor: bordaSutil,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: texto, fontFamily: fonte, fontSize: 12 },
      // PT: raio, sombra e algarismos tabulares pelas variáveis do CSS, que
      //     seguem o tema do painel onde a dica abre
      // EN: radius, shadow and tabular figures from CSS variables
      extraCssText:
        "border-radius: var(--radius-controle); box-shadow: var(--elevation-2); font-variant-numeric: tabular-nums;",
      axisPointer: {
        lineStyle: { color: bordaForte, width: 1 },
        crossStyle: { color: bordaForte, width: 1 },
      },
    },
    categoryAxis: { ...eixo, splitLine: { show: false } },
    valueAxis: { ...eixo, axisLine: { show: false } },
    logAxis: { ...eixo, axisLine: { show: false } },
    timeAxis: { ...eixo, splitLine: { show: false } },
    visualMap: { textStyle: { ...rotulo } },
    line: {
      lineStyle: { width: 2 },
      symbol: "circle",
      symbolSize: 8,
      showSymbol: false,
      emphasis: { focus: "series" },
    },
    bar: { itemStyle: { borderRadius: 4 }, barCategoryGap: "30%" },
    scatter: { symbolSize: 10, itemStyle: { borderColor: vidro, borderWidth: 2 } },
    // PT: fronteiras das UFs na cor do fundo: o espaço entre as áreas separa
    //     vizinhas de cores próximas
    // EN: state borders in the background color, as a gap between fills
    map: {
      itemStyle: { borderColor: fundo, borderWidth: 1 },
      label: { show: false },
      emphasis: { label: { show: false }, itemStyle: { borderColor: texto, borderWidth: 2 } },
      select: { disabled: true },
    },
    heatmap: { itemStyle: { borderColor: vidro, borderWidth: 2, borderRadius: 4 } },
  };
}
