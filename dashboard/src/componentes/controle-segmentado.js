/**
 * PT: Controle segmentado: opções exclusivas lado a lado, num trilho de
 *     vidro claro, com uma gota de vidro que desliza até a opção escolhida.
 *
 *     Serve para trocar de visão, de recorte ou de tema, com até cinco
 *     opções. Não serve para filtros que se combinam, que é papel dos chips.
 *
 *     Segue o padrão de grupo de rádio da WAI-ARIA: o Tab entra só na opção
 *     escolhida, as setas trocam a opção e movem o foco junto, e Home e End
 *     vão para a primeira e a última. A gota se move pela mola longa, e fica
 *     parada com movimento reduzido.
 *
 * EN: Segmented control: exclusive options on a clear-glass track, with a
 *     glass drop sliding to the chosen one. Follows the WAI-ARIA radio group
 *     pattern: Tab enters the chosen option, arrows move the selection.
 */

import { elemento } from "../dom.js";

/**
 * @typedef {object} Opcao
 * @property {string} valor
 * @property {string} texto
 */

/**
 * @typedef {object} OpcoesDoControle
 * @property {string} rotulo Nome do grupo, para leitores de tela / group name
 * @property {Opcao[]} opcoes De duas a cinco / two to five
 * @property {string} valor A opção escolhida no começo / initial value
 * @property {(valor: string) => void} [aoMudar]
 */

/** PT: o guia limita a cinco opções / EN: the guide caps it at five */
const MAXIMO_DE_OPCOES = 5;

/**
 * PT: Monta o controle segmentado.
 * EN: Builds the segmented control.
 *
 * @param {OpcoesDoControle} opcoes
 * @returns {HTMLDivElement}
 */
export function controleSegmentado({ rotulo, opcoes, valor, aoMudar }) {
  if (opcoes.length < 2 || opcoes.length > MAXIMO_DE_OPCOES) {
    throw new Error(`O controle segmentado aceita de 2 a ${MAXIMO_DE_OPCOES} opções`);
  }
  const gota = elemento("span", {
    classe: "segmentado__gota",
    atributos: { "aria-hidden": "true" },
  });
  const botoes = opcoes.map((opcao) =>
    elemento("button", {
      classe: "segmentado__opcao",
      texto: opcao.texto,
      atributos: { type: "button", role: "radio", "data-valor": opcao.valor },
    }),
  );
  const el = elemento(
    "div",
    { classe: "segmentado", atributos: { role: "radiogroup", "aria-label": rotulo } },
    [gota, ...botoes],
  );

  /**
   * PT: Põe a gota sob a opção escolhida, pela posição e largura dela.
   * EN: Places the drop under the chosen option.
   */
  const posicionarGota = () => {
    const escolhido = botoes.find((b) => b.getAttribute("aria-checked") === "true");
    if (!escolhido) return;
    el.style.setProperty("--gota-inicio", `${escolhido.offsetLeft}px`);
    el.style.setProperty("--gota-largura", `${escolhido.offsetWidth}px`);
    // PT: em tela estreita o controle rola; a opção escolhida fica sempre à vista
    // EN: on narrow screens the control scrolls; keep the chosen option visible
    const inicio = escolhido.offsetLeft;
    const fim = inicio + escolhido.offsetWidth;
    if (inicio < el.scrollLeft || fim > el.scrollLeft + el.clientWidth) {
      el.scrollLeft = fim - el.clientWidth;
    }
  };

  /**
   * @param {number} indice
   * @param {{ focar?: boolean, avisar?: boolean }} [modo]
   */
  const escolher = (indice, { focar = false, avisar = true } = {}) => {
    botoes.forEach((b, i) => {
      b.setAttribute("aria-checked", String(i === indice));
      b.tabIndex = i === indice ? 0 : -1;
    });
    if (focar) botoes[indice].focus();
    posicionarGota();
    if (avisar) aoMudar?.(opcoes[indice].valor);
  };

  botoes.forEach((b, i) => {
    b.addEventListener("click", () => escolher(i));
  });
  el.addEventListener("keydown", (evento) => {
    const atual = botoes.findIndex((b) => b.getAttribute("aria-checked") === "true");
    const ultimo = botoes.length - 1;
    /** @type {Record<string, number>} */
    const destinos = {
      ArrowRight: atual === ultimo ? 0 : atual + 1,
      ArrowDown: atual === ultimo ? 0 : atual + 1,
      ArrowLeft: atual === 0 ? ultimo : atual - 1,
      ArrowUp: atual === 0 ? ultimo : atual - 1,
      Home: 0,
      End: ultimo,
    };
    if (!(evento.key in destinos)) return;
    evento.preventDefault();
    escolher(destinos[evento.key], { focar: true });
  });

  const inicial = Math.max(
    0,
    opcoes.findIndex((opcao) => opcao.valor === valor),
  );
  escolher(inicial, { avisar: false });
  // PT: a posição da gota só existe com o controle na página, e muda com a
  //     fonte e a largura. Fora do navegador, como nos testes, não há o que medir
  // EN: re-place the drop on layout changes; nothing to measure outside a browser
  if ("ResizeObserver" in globalThis) {
    new ResizeObserver(posicionarGota).observe(el);
  }
  return el;
}
