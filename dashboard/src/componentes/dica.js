/**
 * PT: Dica flutuante: vidro regular, raio de controle e elevação 2.
 *
 *     Traz o nome do item e os números dele, e nunca esconde informação que
 *     não esteja também na tela ou na tabela. Segue a WCAG 2.2, critério
 *     1.4.13, para conteúdo que aparece com o mouse ou o foco:
 *     - abre com o mouse em cima e com o foco do teclado;
 *     - dá para passar o mouse sobre a própria dica sem ela sumir;
 *     - fecha com o Esc, sem mover o foco.
 *
 *     Os gráficos têm a dica do próprio ECharts, com o mesmo visual. Esta é
 *     para o resto da interface, como um número numa tabela.
 *
 * EN: Floating tooltip on regular glass, following WCAG 2.2 SC 1.4.13:
 *     opens on hover and focus, stays while hovered, closes on Escape.
 */

import { elemento } from "../dom.js";

let contador = 0;

/** PT: tempo para o mouse chegar do gatilho à dica / EN: hover grace time */
const TOLERANCIA_MS = 120;

/**
 * PT: O corpo da dica, sem comportamento. O catálogo usa para mostrar a
 *     dica aberta, e `comDica` usa para montar a de verdade.
 * EN: The tooltip body alone.
 *
 * @param {(Node | string)[]} conteudo
 * @returns {HTMLDivElement}
 */
export function corpoDaDica(conteudo) {
  return elemento("div", { classe: "dica" }, conteudo);
}

/**
 * PT: Liga uma dica a um gatilho que recebe foco, como um botão. Devolve o
 *     elemento que envolve os dois, para ir na página.
 * EN: Attaches a tooltip to a focusable trigger; returns the wrapper.
 *
 * @param {HTMLElement} gatilho
 * @param {(Node | string)[]} conteudo
 * @returns {HTMLSpanElement}
 */
export function comDica(gatilho, conteudo) {
  contador += 1;
  const id = `dica-${contador}`;
  const dica = corpoDaDica(conteudo);
  dica.id = id;
  dica.setAttribute("role", "tooltip");
  dica.hidden = true;
  gatilho.setAttribute("aria-describedby", id);

  const envoltorio = elemento("span", { classe: "com-dica" }, [gatilho, dica]);
  /** @type {ReturnType<typeof setTimeout> | undefined} */
  let fechamento;

  const abrir = () => {
    clearTimeout(fechamento);
    dica.hidden = false;
  };
  const fechar = () => {
    clearTimeout(fechamento);
    dica.hidden = true;
  };
  const fecharDepois = () => {
    clearTimeout(fechamento);
    fechamento = setTimeout(fechar, TOLERANCIA_MS);
  };

  envoltorio.addEventListener("mouseenter", abrir);
  envoltorio.addEventListener("mouseleave", fecharDepois);
  gatilho.addEventListener("focus", abrir);
  gatilho.addEventListener("blur", fechar);
  envoltorio.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !dica.hidden) {
      evento.stopPropagation();
      fechar();
    }
  });
  return envoltorio;
}
