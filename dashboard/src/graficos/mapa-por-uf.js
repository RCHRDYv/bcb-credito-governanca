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
import { estiloDaMarca, MARCA } from "./marca.js";
import { destaque, etiquetaDaEscolhida, semComparacao } from "./selecao.js";
import { UFS, ufPelaSigla } from "./ufs.js";

/** @typedef {import("./escalas.js").Classes} Classes */
/** @typedef {import("./grafico.js").Grafico} Grafico */
/** @typedef {import("./malha.js").Malha} Malha */

const NOME_DO_MAPA = "ufs";

/**
 * PT: Registra no ECharts a malha buscada por `carregarMalha()`, de
 *     `malha.js`. Registrar de novo não refaz o trabalho.
 * EN: Registers the mesh fetched by `carregarMalha()`; idempotent.
 *
 * @param {Malha} malha
 * @returns {void}
 */
export function registrarMalha(malha) {
  if (echarts.getMap(NOME_DO_MAPA)) return;
  echarts.registerMap(NOME_DO_MAPA, /** @type {never} */ (malha));
}

/**
 * PT: O rótulo de uma área: a sigla da UF escolhida, numa etiqueta, e o
 *     marcador de alerta, no centro da área. As demais ficam sem rótulo.
 * EN: An area's label: the chosen state's tag and the early-warning marker.
 *
 * @param {import("../tokens.js").Tema} tema
 * @param {string} sigla
 * @param {boolean} escolhida
 * @param {boolean} marcada
 * @returns {{ label?: Record<string, unknown> }}
 */
function rotuloDaUf(tema, sigla, escolhida, marcada) {
  const rich = estiloDaMarca(tema);
  if (escolhida) {
    const etiqueta = etiquetaDaEscolhida(tema, sigla);
    if (!marcada) return { label: etiqueta };
    // PT: com o marcador, a sigla também vai em texto rico, com o estilo da
    //     etiqueta; misturar texto comum e rico desalinhava os dois
    // EN: with the marker, the abbreviation is rich text too, so both align
    const estiloDaSigla = {
      color: etiqueta.color,
      fontSize: etiqueta.fontSize,
      fontWeight: etiqueta.fontWeight,
      padding: [0, 4, 0, 0],
    };
    return {
      label: {
        ...etiqueta,
        formatter: `{sigla|${sigla}} ${MARCA}`,
        rich: { ...rich, sigla: estiloDaSigla },
      },
    };
  }
  return marcada ? { label: { show: true, formatter: MARCA, rich } } : {};
}

/**
 * @typedef {object} DadosDoMapa
 * @property {Record<string, number | null>} valores Por sigla da UF / by state
 * @property {Classes} classes As classes de cor / color classes
 * @property {(v: number) => string} formatar Para a dica / for the tooltip
 * @property {(sigla: string) => string | null} [dica] Texto da dica no lugar do valor, como o motivo de a UF ficar fora da comparação / tooltip override
 * @property {(sigla: string) => void} [aoSelecionar] Clique numa UF / state click
 * @property {string | null} [selecionada] A UF destacada no começo / initially selected state
 * @property {string} [rotuloSemValor] Item da legenda para as UFs sem valor, desenhadas com textura / legend item for value-less states
 * @property {import("./legenda.js").FazerLegenda} [legenda] Quem monta a legenda; o padrão é a lista de classes / legend builder, class list by default
 * @property {HTMLElement} [legendaPronta] A legenda já montada e posta na página por quem chama, para ela ocupar o lugar antes de o ECharts chegar (#92) / legend already in the page
 * @property {string[]} [marcadas] UFs com o marcador de alerta antecipado (#70) / states with the early-warning marker
 */

/** @typedef {import("./selecao.js").GraficoDeUf<DadosDoMapa>} GraficoDoMapa */

/**
 * PT: Desenha o mapa no elemento, com a legenda logo depois dele. A malha
 *     precisa ter sido registrada antes, por `registrarMalha()`.
 *
 *     A UF escolhida ganha a borda na cor do texto, e um clique numa UF
 *     avisa `aoSelecionar` (RF-102). Trocar a UF escolhida ou o dado atualiza
 *     a mesma instância do ECharts, sem recriar o gráfico.
 * EN: Draws the map; the mesh must be loaded first. The chosen state gets a
 *     text-colored border, clicks call `aoSelecionar`, and changing the
 *     selection or data updates the same ECharts instance.
 *
 * @param {HTMLElement} el
 * @param {DadosDoMapa} inicial
 * @returns {Promise<GraficoDoMapa>}
 */
export async function mapaPorUf(el, inicial) {
  let dados = inicial;
  let escolhida = inicial.selecionada ?? null;
  let legenda =
    dados.legendaPronta ??
    (dados.legenda ?? legendaDeClasses)(dados.classes("claro"), dados.rotuloSemValor);
  if (!legenda.isConnected) el.after(legenda);

  const grafico = await criarGrafico(el, (tema) => {
    const vazio = semComparacao(tema);
    return {
      tooltip: {
        trigger: "item",
        formatter: (/** @type {{ name: string, value: number }} */ p) =>
          `${ufPelaSigla(p.name).nome}: ${
            dados.dica?.(p.name) ??
            (Number.isFinite(p.value) ? dados.formatar(p.value) : t("grafico.sem-dado"))
          }`,
      },
      visualMap: {
        type: "piecewise",
        pieces: dados.classes(tema),
        outOfRange: { color: vazio.cor },
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
          data: UFS.map((uf) => {
            const valor = dados.valores[uf.sigla] ?? null;
            const escolhidaAqui = uf.sigla === escolhida;
            const marcada = dados.marcadas?.includes(uf.sigla) ?? false;
            return {
              name: uf.sigla,
              value: valor,
              itemStyle: {
                ...(valor === null ? { areaColor: vazio.cor, decal: vazio.textura } : {}),
                ...(escolhidaAqui ? destaque(tema) : {}),
              },
              ...rotuloDaUf(tema, uf.sigla, escolhidaAqui, marcada),
            };
          }),
        },
      ],
    };
  });

  grafico.instancia.on("click", (/** @type {{ name?: string }} */ p) => {
    if (p.name) dados.aoSelecionar?.(p.name);
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
