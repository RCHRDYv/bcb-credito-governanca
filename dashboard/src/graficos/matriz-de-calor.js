/**
 * PT: Matriz de calor: uma linha por item, uma coluna por categoria, e a cor
 *     de cada célula pela classe do valor.
 *
 *     Nasceu na revisão da Tela 1 (#69, 2026-10-01) para mostrar numa visão
 *     só a pergunta de duas dimensões do projeto: em quais UFs e em quais
 *     modalidades. Cada célula é uma UF numa modalidade, pintada pela
 *     distância até a mediana das UFs. As mesmas classes do mapa, para os
 *     dois se lerem igual.
 *
 *     - **Célula sem valor**, como a que fica fora da comparação, vai numa
 *       série própria, com a textura listrada: o mapa de calor do ECharts
 *       não desenha célula sem número.
 *     - **Célula que não existe**, como a UF sem carteira na modalidade, fica
 *       vazia.
 *     - **Clique** numa célula avisa `aoSelecionar`, com a linha e a coluna.
 *       A célula escolhida ganha o destaque, e o rótulo da linha e o da
 *       coluna dela ficam em negrito.
 *     - **Rótulos das colunas:** siglas curtas, como as das UFs, ficam
 *       retas enquanto cada coluna tiver pelo menos 20 px; abaixo disso,
 *       giram 90 graus para não se encostarem. Nomes longos, como os das
 *       modalidades, giram 30 graus, ou 90 em tela estreita, onde as dez
 *       colunas cabem em 360 px sem rolagem.
 *     - **Orientação:** quem chama escolhe o que vai nas linhas. Na Tela 1,
 *       no computador, as modalidades vão nas linhas e as UFs nas colunas,
 *       para a matriz caber deitada no cartão (ADR 0022); no celular, o
 *       contrário.
 *
 * EN: Heatmap: one row per item, one column per category, cells colored by
 *     value class. Built for Screen 1 to show states by modalities at once.
 *     Value-less cells get their own striped series; missing cells stay
 *     empty; clicks report row and column; the chosen cell is highlighted
 *     and its row and column labels go bold.
 */

import { t } from "../textos/index.js";
import { criarGrafico } from "./grafico.js";
import { legendaDeClasses } from "./legenda.js";
import { destaque, semComparacao } from "./selecao.js";
import { hex } from "./tema.js";

/** @typedef {import("./escalas.js").Classes} Classes */

/**
 * PT: A largura de coluna, em px, a partir da qual uma sigla de UF cabe reta
 *     sem encostar na vizinha.
 * EN: Column width from which a state abbreviation fits upright.
 */
const LARGURA_DA_SIGLA = 20;

/**
 * PT: Quanto uma letra do rótulo ocupa, em média, no corpo de 12 px.
 * EN: Average width of a label letter at 12 px.
 */
const PX_POR_LETRA = 7;

/**
 * @typedef {object} Eixo
 * @property {string} chave Identifica a linha ou a coluna / row or column key
 * @property {string} rotulo O texto no eixo / axis label
 */

/**
 * @typedef {object} CelulaDeCalor
 * @property {string} linha A chave da linha / row key
 * @property {string} coluna A chave da coluna / column key
 * @property {number | null} valor `null` quando fica sem cor de classe / null when value-less
 * @property {string} dica O texto da dica da célula / the cell's tooltip text
 */

/**
 * @typedef {object} DadosDaMatrizDeCalor
 * @property {Eixo[]} linhas
 * @property {Eixo[]} colunas
 * @property {CelulaDeCalor[]} celulas
 * @property {Classes} classes
 * @property {string} [rotuloSemValor] Item da legenda para as células sem valor / legend item
 * @property {import("./legenda.js").FazerLegenda} [legenda] Quem monta a legenda; o padrão é a lista de classes / legend builder, class list by default
 * @property {(linha: string, coluna: string) => void} [aoSelecionar]
 * @property {{ linha: string | null, coluna: string | null }} [selecionada]
 */

/**
 * @typedef {import("./grafico.js").Grafico & {
 *   selecionar: (selecao: { linha: string | null, coluna: string | null }) => void,
 *   mudar: (dados: Partial<DadosDaMatrizDeCalor>) => void,
 * }} GraficoDaMatrizDeCalor
 */

/**
 * PT: Desenha a matriz de calor, com a legenda logo depois dela.
 * EN: Draws the heatmap, with its legend right after.
 *
 * @param {HTMLElement} el
 * @param {DadosDaMatrizDeCalor} inicial
 * @returns {Promise<GraficoDaMatrizDeCalor>}
 */
export async function matrizDeCalor(el, inicial) {
  let dados = inicial;
  let escolhida = inicial.selecionada ?? { linha: null, coluna: null };
  el.style.setProperty("--linhas", String(dados.linhas.length));
  let legenda = (dados.legenda ?? legendaDeClasses)(dados.classes("claro"), dados.rotuloSemValor);
  el.after(legenda);

  const grafico = await criarGrafico(el, (tema, { estreito }) => {
    const semValor = semComparacao(tema);
    const indiceDaLinha = new Map(dados.linhas.map((linha, i) => [linha.chave, i]));
    const indiceDaColuna = new Map(dados.colunas.map((coluna, i) => [coluna.chave, i]));
    /** @param {CelulaDeCalor} celula */
    const ponto = (celula) => ({
      linha: celula.linha,
      coluna: celula.coluna,
      dica: celula.dica,
      semValor: celula.valor === null,
      value: [
        indiceDaColuna.get(celula.coluna),
        indiceDaLinha.get(celula.linha),
        celula.valor ?? 0,
      ],
      itemStyle: {
        ...(celula.valor === null ? { color: semValor.cor, decal: semValor.textura } : {}),
        ...(celula.linha === escolhida.linha && celula.coluna === escolhida.coluna
          ? destaque(tema)
          : {}),
      },
    });
    const validas = dados.celulas.filter(
      (c) => indiceDaLinha.has(c.linha) && indiceDaColuna.has(c.coluna),
    );
    const forte = { fontWeight: 600, color: hex("color.text.primary", tema) };
    const colunasCurtas = dados.colunas.every((coluna) => coluna.rotulo.length <= 3);
    // PT: a área das colunas é a largura menos a dos rótulos das linhas, que
    //     se estima pelo maior rótulo
    // EN: column area is the width minus the row labels, estimated
    const rotulosDasLinhas =
      Math.max(0, ...dados.linhas.map((linha) => linha.rotulo.length)) * PX_POR_LETRA;
    const largas =
      (el.clientWidth - rotulosDasLinhas) / Math.max(dados.colunas.length, 1) >= LARGURA_DA_SIGLA;
    return {
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ data: { dica: string } }} */ p) => p.data.dica,
      },
      grid: { left: 8, right: 8, top: 8, bottom: 8, containLabel: true },
      xAxis: {
        type: "category",
        position: "top",
        data: dados.colunas.map((coluna) => coluna.chave),
        splitArea: { show: false },
        axisTick: { show: false },
        axisLine: { show: false },
        axisLabel: {
          interval: 0,
          rotate: colunasCurtas ? (largas ? 0 : 90) : estreito ? 90 : 30,
          formatter: (/** @type {string} */ chave) => {
            const rotulo = dados.colunas.find((c) => c.chave === chave)?.rotulo ?? chave;
            return chave === escolhida.coluna ? `{forte|${rotulo}}` : rotulo;
          },
          rich: { forte },
        },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: dados.linhas.map((linha) => linha.chave),
        axisTick: { show: false },
        axisLine: { show: false },
        axisLabel: {
          formatter: (/** @type {string} */ chave) => {
            const rotulo = dados.linhas.find((l) => l.chave === chave)?.rotulo ?? chave;
            return chave === escolhida.linha ? `{forte|${rotulo}}` : rotulo;
          },
          rich: { forte },
        },
      },
      // PT: o mapa de calor exige uma escala de cor por série; a das células
      //     sem valor é de uma cor só
      // EN: every heatmap series needs a visualMap; the value-less one is
      //     single-color
      visualMap: [
        {
          type: "piecewise",
          pieces: dados.classes(tema),
          seriesIndex: 0,
          outOfRange: { color: semValor.cor },
          show: false,
        },
        {
          type: "piecewise",
          pieces: [{ value: 0, color: semValor.cor }],
          seriesIndex: 1,
          show: false,
        },
      ],
      series: [
        {
          type: "heatmap",
          data: validas.filter((c) => c.valor !== null).map(ponto),
          itemStyle: { borderColor: hex("color.chart.surface", tema), borderWidth: 1 },
          emphasis: { itemStyle: destaque(tema) },
        },
        {
          type: "heatmap",
          data: validas.filter((c) => c.valor === null).map(ponto),
          itemStyle: { borderColor: hex("color.chart.surface", tema), borderWidth: 1 },
          emphasis: { itemStyle: destaque(tema) },
        },
      ],
      aria: { enabled: true, label: { description: t("grafico.matriz-de-calor-aria") } },
    };
  });

  grafico.instancia.on("click", (p) => {
    const dado = /** @type {{ linha?: string, coluna?: string } | null | undefined} */ (p.data);
    if (dado?.linha && dado.coluna) dados.aoSelecionar?.(dado.linha, dado.coluna);
  });

  return {
    ...grafico,
    selecionar(selecao) {
      escolhida = selecao;
      grafico.atualizar();
    },
    mudar(novos) {
      dados = { ...dados, ...novos };
      el.style.setProperty("--linhas", String(dados.linhas.length));
      const nova = (dados.legenda ?? legendaDeClasses)(
        dados.classes("claro"),
        dados.rotuloSemValor,
      );
      legenda.replaceWith(nova);
      legenda = nova;
      grafico.atualizar();
    },
  };
}
