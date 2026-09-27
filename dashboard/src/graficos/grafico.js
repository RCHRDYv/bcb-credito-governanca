/**
 * PT: O ciclo de vida de um gráfico: criar, seguir o tema, redimensionar e
 *     destruir.
 *
 *     Todo componente de gráfico nasce por `criarGrafico()`. Ele cuida de
 *     quatro coisas que nenhum componente precisa repetir:
 *     1. **Tema.** O tema de cada gráfico é o do lugar onde ele está: o
 *        `color-scheme` calculado do elemento. Na página, isso segue o
 *        sistema do visitante ou o atributo `data-tema`; num painel do
 *        catálogo, segue o painel. Na impressão, é sempre o claro.
 *     2. **Troca de tema sem recriar o gráfico.** Quando o tema muda, a
 *        mesma instância recebe o tema novo (`setTheme`) e as cores do tema
 *        novo (`setOption`). O gráfico não é destruído nem criado de novo.
 *     3. **Fonte e tamanho.** O desenho espera a IBM Plex carregar, porque o
 *        ECharts mede o texto ao desenhar, e acompanha o tamanho do elemento.
 *     4. **Movimento reduzido.** Com a preferência ligada, não há animação.
 *     5. **Largura.** A opção sabe se o gráfico está estreito (abaixo de
 *        480 px), e é montada de novo só quando ele cruza esse limite.
 *
 * EN: A chart's lifecycle. The theme comes from the element's computed
 *     `color-scheme` (light when printing); a theme change updates the same
 *     instance with `setTheme` and `setOption`, never recreating it. Drawing
 *     waits for the webfont, follows the element size, honours reduced
 *     motion and rebuilds the option when the chart crosses the narrow width.
 */

import { echarts } from "./echarts.js";
import { montarTema, NOMES_DOS_TEMAS } from "./tema.js";

/** @typedef {import("../tokens.js").Tema} Tema */
/** @typedef {Record<string, unknown>} Opcao */
/**
 * @typedef {object} Contexto
 * @property {boolean} estreito Largura abaixo de `LARGURA_ESTREITA` / narrow chart
 */
/** @typedef {(tema: Tema, contexto: Contexto) => Opcao} MontarOpcao */

/**
 * PT: Largura, em px, abaixo da qual um gráfico é estreito. O CSS usa o
 *     mesmo número nas consultas de contêiner dos gráficos.
 * EN: Width below which a chart is narrow; the CSS container queries match.
 */
export const LARGURA_ESTREITA = 480;

/**
 * @typedef {object} Grafico
 * @property {import("echarts/core").EChartsType} instancia A instância do ECharts / ECharts instance
 * @property {() => Tema} tema O tema em uso / current theme
 * @property {(montar?: MontarOpcao) => void} atualizar Redesenha, com dado novo ou não / redraws
 * @property {() => void} destruir Libera a instância e os observadores / disposes
 */

for (const tema of /** @type {Tema[]} */ (["claro", "escuro"])) {
  echarts.registerTheme(NOMES_DOS_TEMAS[tema], montarTema(tema));
}

const escuroNoSistema = window.matchMedia("(prefers-color-scheme: dark)");
const movimentoReduzido = window.matchMedia("(prefers-reduced-motion: reduce)");

/** @type {Set<() => void>} */
const sincronizadores = new Set();
let imprimindo = false;
let observando = false;

/**
 * PT: Liga, uma vez só, os avisos de mudança de tema: a preferência do
 *     sistema, o atributo `data-tema` da página e a impressão.
 * EN: Wires theme-change signals once.
 */
function observarMudancas() {
  if (observando) return;
  observando = true;
  const sincronizarTodos = () => {
    for (const sincronizar of sincronizadores) sincronizar();
  };
  escuroNoSistema.addEventListener("change", sincronizarTodos);
  movimentoReduzido.addEventListener("change", sincronizarTodos);
  new MutationObserver(sincronizarTodos).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-tema"],
  });
  window.addEventListener("beforeprint", () => {
    imprimindo = true;
    sincronizarTodos();
  });
  window.addEventListener("afterprint", () => {
    imprimindo = false;
    sincronizarTodos();
  });
}

/**
 * PT: O tema do lugar onde o elemento está.
 * EN: The theme where the element sits.
 *
 * @param {Element} el
 * @returns {Tema}
 */
export function temaDoElemento(el) {
  if (imprimindo) return "claro";
  const esquema = getComputedStyle(el).colorScheme.trim();
  if (esquema === "light" || esquema === "only light") return "claro";
  if (esquema === "dark" || esquema === "only dark") return "escuro";
  return escuroNoSistema.matches ? "escuro" : "claro";
}

/**
 * PT: A opção completa: a do componente, com animação e acessibilidade.
 * EN: The full option: the component's, plus animation and accessibility.
 *
 * @param {MontarOpcao} montar
 * @param {Tema} tema
 * @param {boolean} estreito
 * @returns {Opcao}
 */
function opcaoCompleta(montar, tema, estreito) {
  return {
    animation: !movimentoReduzido.matches,
    aria: { enabled: true },
    ...montar(tema, { estreito }),
  };
}

/**
 * PT: Cria um gráfico no elemento. A opção é montada por tema, para as cores
 *     acompanharem a troca de tema.
 * EN: Creates a chart in the element; the option is built per theme.
 *
 * @param {HTMLElement} el
 * @param {MontarOpcao} montar
 * @returns {Promise<Grafico>}
 */
export async function criarGrafico(el, montar) {
  observarMudancas();
  await document.fonts.ready;

  let tema = temaDoElemento(el);
  let estreito = el.clientWidth < LARGURA_ESTREITA;
  let montarAtual = montar;
  const instancia = echarts.init(el, NOMES_DOS_TEMAS[tema], { renderer: "svg" });
  instancia.setOption(opcaoCompleta(montarAtual, tema, estreito));

  const sincronizar = () => {
    const novo = temaDoElemento(el);
    if (novo === tema) {
      instancia.setOption({ animation: !movimentoReduzido.matches });
      return;
    }
    tema = novo;
    instancia.setTheme(NOMES_DOS_TEMAS[tema]);
    instancia.setOption(opcaoCompleta(montarAtual, tema, estreito));
  };
  sincronizadores.add(sincronizar);

  const tamanho = new ResizeObserver(() => {
    const agora = el.clientWidth < LARGURA_ESTREITA;
    if (agora !== estreito) {
      estreito = agora;
      instancia.setOption(opcaoCompleta(montarAtual, tema, estreito), { notMerge: true });
    }
    instancia.resize();
  });
  tamanho.observe(el);

  return {
    instancia,
    tema: () => tema,
    atualizar(novoMontar) {
      if (novoMontar) montarAtual = novoMontar;
      instancia.setOption(opcaoCompleta(montarAtual, tema, estreito), { notMerge: true });
    },
    destruir() {
      sincronizadores.delete(sincronizar);
      tamanho.disconnect();
      instancia.dispose();
    },
  };
}
