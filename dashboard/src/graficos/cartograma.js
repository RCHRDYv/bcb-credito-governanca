/**
 * PT: Cartograma de grade: cada UF é um quadrado do mesmo tamanho.
 *
 *     É a alternativa ao mapa quando os estados pequenos precisam ser lidos
 *     (RF-103): no mapa, o Distrito Federal e Sergipe quase somem; aqui, têm
 *     o mesmo peso que o Amazonas. Usa as mesmas classes de cor do mapa, e
 *     cada quadrado traz a sigla, em texto que contrasta com o preenchimento.
 *     Não depende da malha do IBGE, então continua funcionando quando ela
 *     não carrega.
 *
 * EN: Tile-grid cartogram: every state is an equal square, with the same
 *     color classes as the map and the abbreviation in a contrasting color.
 *     It does not depend on the IBGE mesh.
 */

import { razaoDeContraste } from "../cor/contraste.js";
import { t } from "../textos/index.js";
import { classeDoValor } from "./escalas.js";
import { criarGrafico } from "./grafico.js";
import { legendaDeClasses } from "./legenda.js";
import { estiloDaMarca, MARCA } from "./marca.js";
import { destaque, semComparacao } from "./selecao.js";
import { hex } from "./tema.js";
import { UFS, ufPelaSigla } from "./ufs.js";

/** @typedef {import("./escalas.js").Classes} Classes */
/** @typedef {import("./grafico.js").Grafico} Grafico */
/** @typedef {import("../tokens.js").Tema} Tema */

const COLUNAS = Math.max(...UFS.map((uf) => uf.coluna)) + 1;
const LINHAS = Math.max(...UFS.map((uf) => uf.linha)) + 1;

/**
 * PT: O texto que mais contrasta com o preenchimento: o principal do tema
 *     claro ou o do tema escuro.
 * EN: The text color with the most contrast on the fill.
 *
 * @param {string} preenchimento
 * @returns {string}
 */
function textoSobre(preenchimento) {
  const escuro = hex("color.text.primary", "claro");
  const claro = hex("color.text.primary", "escuro");
  return razaoDeContraste(escuro, preenchimento) >= razaoDeContraste(claro, preenchimento)
    ? escuro
    : claro;
}

/**
 * @typedef {object} DadosDoCartograma
 * @property {Record<string, number | null>} valores Por sigla da UF / by state
 * @property {Classes} classes As mesmas do mapa / same as the map
 * @property {(v: number) => string} formatar Para a dica / for the tooltip
 * @property {(sigla: string) => string | null} [dica] Texto da dica no lugar do valor / tooltip override
 * @property {(sigla: string) => void} [aoSelecionar] Clique numa UF / state click
 * @property {string | null} [selecionada] A UF destacada no começo / initially selected state
 * @property {string} [rotuloSemValor] Item da legenda para as UFs sem valor, desenhadas com textura / legend item for value-less states
 * @property {import("./legenda.js").FazerLegenda} [legenda] Quem monta a legenda; o padrão é a lista de classes / legend builder, class list by default
 * @property {HTMLElement} [legendaPronta] A legenda já montada e posta na página por quem chama, para ela ocupar o lugar antes de o ECharts chegar (#92) / legend already in the page
 * @property {string[]} [marcadas] UFs com o marcador de alerta antecipado, ao lado da sigla (#70) / states with the early-warning marker
 */

/** @typedef {import("./selecao.js").GraficoDeUf<DadosDoCartograma>} GraficoDoCartograma */

/**
 * PT: Desenha o cartograma no elemento, com a legenda logo depois dele. A
 *     UF escolhida ganha a borda na cor do texto, e um clique avisa
 *     `aoSelecionar`, como no mapa (RF-102).
 * EN: Draws the cartogram; selection and clicks work as on the map.
 *
 * @param {HTMLElement} el
 * @param {DadosDoCartograma} inicial
 * @returns {Promise<GraficoDoCartograma>}
 */
export async function cartograma(el, inicial) {
  let dados = inicial;
  let escolhida = inicial.selecionada ?? null;
  // PT: a altura acompanha a largura na proporção da grade, pelo CSS
  // EN: height follows width in the grid proportion, via CSS
  el.style.setProperty("--linhas", String(LINHAS));
  el.style.setProperty("--colunas", String(COLUNAS));
  let legenda =
    dados.legendaPronta ??
    (dados.legenda ?? legendaDeClasses)(dados.classes("claro"), dados.rotuloSemValor);
  if (!legenda.isConnected) el.after(legenda);

  const grafico = await criarGrafico(el, (tema) => {
    const pedacos = dados.classes(tema);
    const semValor = semComparacao(tema);
    /**
     * PT: Uma célula da grade. A UF sem valor vai numa série própria, que a
     *     escala de cor não toca: o mapa de calor do ECharts não desenha
     *     célula sem número, e a UF sumiria da grade (revisão visual da #69).
     * EN: One grid cell; value-less states go in their own series, untouched
     *     by the color scale, since a heatmap skips cells with no number.
     *
     * @param {import("./ufs.js").Uf} uf
     * @param {number | null} valor
     */
    const celula = (uf, valor) => {
      const cor =
        valor === null ? semValor.cor : (classeDoValor(pedacos, valor)?.color ?? semValor.cor);
      return {
        sigla: uf.sigla,
        semValor: valor === null,
        value: [uf.coluna, uf.linha, valor ?? 0],
        label: {
          show: true,
          formatter: dados.marcadas?.includes(uf.sigla) ? `${uf.sigla} ${MARCA}` : uf.sigla,
          color: textoSobre(cor),
          fontSize: 12,
          rich: estiloDaMarca(tema),
        },
        itemStyle: {
          ...(valor === null ? { color: semValor.cor, decal: semValor.textura } : {}),
          ...(uf.sigla === escolhida ? destaque(tema) : {}),
        },
      };
    };
    const valorDe = (/** @type {string} */ sigla) => {
      const valor = dados.valores[sigla];
      return Number.isFinite(valor) ? /** @type {number} */ (valor) : null;
    };
    return {
      tooltip: {
        trigger: "item",
        formatter: (
          /** @type {{ data: { sigla: string, semValor: boolean, value: number[] } }} */ p,
        ) => {
          const texto =
            dados.dica?.(p.data.sigla) ??
            (p.data.semValor ? t("grafico.sem-dado") : dados.formatar(p.data.value[2]));
          return `${ufPelaSigla(p.data.sigla).nome}: ${texto}`;
        },
      },
      grid: { left: 0, right: 0, top: 0, bottom: 0 },
      xAxis: { type: "category", data: Array.from({ length: COLUNAS }, (_, i) => i), show: false },
      yAxis: {
        type: "category",
        data: Array.from({ length: LINHAS }, (_, i) => i),
        inverse: true,
        show: false,
      },
      // PT: o mapa de calor do ECharts exige uma escala de cor por série; a
      //     série das UFs sem valor tem a dela, de uma cor só
      // EN: every heatmap series needs a visualMap; the value-less one has a
      //     single-color one
      visualMap: [
        {
          type: "piecewise",
          pieces: pedacos,
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
          data: UFS.filter((uf) => valorDe(uf.sigla) !== null).map((uf) =>
            celula(uf, valorDe(uf.sigla)),
          ),
          emphasis: { itemStyle: destaque(tema) },
        },
        {
          type: "heatmap",
          data: UFS.filter((uf) => valorDe(uf.sigla) === null).map((uf) => celula(uf, null)),
          emphasis: { itemStyle: destaque(tema) },
        },
      ],
    };
  });

  grafico.instancia.on("click", (p) => {
    const dado = /** @type {{ sigla?: string } | null | undefined} */ (p.data);
    if (dado?.sigla) dados.aoSelecionar?.(dado.sigla);
  });

  return {
    ...grafico,
    selecionar(sigla) {
      escolhida = sigla;
      grafico.atualizar();
    },
    mudar(novos) {
      dados = { ...dados, ...novos };
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
