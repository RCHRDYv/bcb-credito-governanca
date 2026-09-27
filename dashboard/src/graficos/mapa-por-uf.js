/**
 * PT: Mapa por UF, pintado por classes de valor (coroplético).
 *
 *     Mostra onde um número é alto ou baixo no território. A malha das UFs é
 *     a do IBGE, simplificada e versionada pela #67, e o site nunca a busca
 *     em tempo de execução fora do próprio endereço (ADR 0017). Os estados
 *     pequenos ficam difíceis de ler no mapa, por isso o cartograma de grade,
 *     com as mesmas classes, é a alternativa (RF-103).
 *
 * EN: Choropleth map by state. The IBGE mesh is versioned in the repository
 *     (#67); the tile cartogram, with the same classes, is the alternative
 *     for small states.
 */

import { t } from "../textos/index.js";
import { echarts } from "./echarts.js";
import { criarGrafico } from "./grafico.js";
import { legendaDeClasses } from "./legenda.js";
import { hex } from "./tema.js";
import { UFS, ufPelaSigla, ufPeloCodigo } from "./ufs.js";

/** @typedef {import("./escalas.js").Classes} Classes */
/** @typedef {import("./grafico.js").Grafico} Grafico */

const NOME_DO_MAPA = "ufs";

/**
 * @typedef {object} Malha
 * @property {"FeatureCollection"} type
 * @property {{ properties: Record<string, string> }[]} features
 */

/**
 * PT: Carrega a malha e a registra no ECharts, com a sigla da UF como nome
 *     de cada área. A malha do IBGE identifica a UF pelo código (`codarea`).
 * EN: Loads the mesh and registers it, naming each area by abbreviation.
 *
 * @param {string} endereco
 * @returns {Promise<void>}
 */
export async function carregarMalha(endereco) {
  const resposta = await fetch(endereco);
  if (!resposta.ok) {
    throw new Error(`A malha das UFs não carregou: ${resposta.status}`);
  }
  const malha = /** @type {Malha} */ (await resposta.json());
  for (const feicao of malha.features) {
    feicao.properties.name = ufPeloCodigo(feicao.properties.codarea).sigla;
  }
  echarts.registerMap(NOME_DO_MAPA, /** @type {never} */ (malha));
}

/**
 * @typedef {object} DadosDoMapa
 * @property {Record<string, number | null>} valores Por sigla da UF / by state
 * @property {Classes} classes As classes de cor / color classes
 * @property {(v: number) => string} formatar Para a dica / for the tooltip
 */

/**
 * PT: Desenha o mapa no elemento, com a legenda logo depois dele. A malha
 *     precisa ter sido carregada antes, por `carregarMalha()`.
 * EN: Draws the map; the mesh must be loaded first.
 *
 * @param {HTMLElement} el
 * @param {DadosDoMapa} dados
 * @returns {Promise<Grafico>}
 */
export function mapaPorUf(el, { valores, classes, formatar }) {
  el.after(legendaDeClasses(classes("claro")));
  return criarGrafico(el, (tema) => ({
    tooltip: {
      trigger: "item",
      formatter: (/** @type {{ name: string, value: number }} */ p) =>
        `${ufPelaSigla(p.name).nome}: ${Number.isFinite(p.value) ? formatar(p.value) : t("grafico.sem-dado")}`,
    },
    visualMap: {
      type: "piecewise",
      pieces: classes(tema),
      outOfRange: { color: hex("color.border.subtle", tema) },
      show: false,
    },
    series: [
      {
        type: "map",
        map: NOME_DO_MAPA,
        // PT: o Brasil fica perto do equador, e a escala horizontal real é
        //     o cosseno da latitude média, cerca de 15 graus sul
        // EN: horizontal scale is the cosine of the mean latitude (~15° S)
        aspectScale: Math.cos((15 * Math.PI) / 180),
        layoutCenter: ["50%", "50%"],
        layoutSize: "100%",
        data: UFS.map((uf) => ({ name: uf.sigla, value: valores[uf.sigla] ?? null })),
      },
    ],
  }));
}
