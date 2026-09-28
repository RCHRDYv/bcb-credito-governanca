/**
 * PT: Chips de filtro: cápsulas de vidro que se ligam e desligam, para
 *     filtros que se combinam entre si, como várias modalidades ao mesmo
 *     tempo.
 *
 *     O chip selecionado ganha fundo azul translúcido, borda azul, texto azul
 *     e o ícone de confirmação, então a seleção não depende só da cor. Não
 *     servem para disparar ações, que é papel dos botões, nem para opções
 *     exclusivas, que é papel do controle segmentado.
 *
 * EN: Filter chips: glass capsules toggled on and off, for combinable
 *     filters. Selection shows a check icon, not color alone.
 */

import { elemento } from "../dom.js";
import { icone } from "./icones.js";

/**
 * @typedef {object} OpcaoDeChip
 * @property {string} valor
 * @property {string} texto
 * @property {string} [titulo] Nome completo, quando o texto é abreviado / full name
 */

/**
 * @typedef {object} OpcoesDosChips
 * @property {string} rotulo Nome do grupo, para leitores de tela / group name
 * @property {OpcaoDeChip[]} opcoes
 * @property {string[]} [selecionados]
 * @property {(selecionados: string[]) => void} [aoMudar]
 */

/**
 * PT: Monta o grupo de chips.
 * EN: Builds the chip group.
 *
 * @param {OpcoesDosChips} opcoes
 * @returns {HTMLDivElement}
 */
export function grupoDeChips({ rotulo, opcoes, selecionados = [], aoMudar }) {
  const escolhidos = new Set(selecionados);
  const chips = opcoes.map((opcao) => {
    const chip = elemento(
      "button",
      {
        classe: "chip",
        atributos: {
          type: "button",
          "aria-pressed": String(escolhidos.has(opcao.valor)),
          ...(opcao.titulo ? { title: opcao.titulo } : {}),
        },
      },
      [icone("check"), elemento("span", { texto: opcao.texto })],
    );
    chip.addEventListener("click", () => {
      if (escolhidos.has(opcao.valor)) escolhidos.delete(opcao.valor);
      else escolhidos.add(opcao.valor);
      chip.setAttribute("aria-pressed", String(escolhidos.has(opcao.valor)));
      // PT: a ordem devolvida é a das opções, e não a dos cliques
      // EN: returned in option order, not click order
      aoMudar?.(opcoes.map((o) => o.valor).filter((v) => escolhidos.has(v)));
    });
    return chip;
  });
  return elemento(
    "div",
    { classe: "chips", atributos: { role: "group", "aria-label": rotulo } },
    chips,
  );
}
