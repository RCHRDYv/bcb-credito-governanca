/**
 * PT: Botão em cápsula, em três variantes (guia do design system).
 *
 *     - **Primário:** azul 60 com brilho na borda, para a ação principal da
 *       área. Um só por área.
 *     - **Secundário:** vidro regular, para ações de apoio.
 *     - **Sutil:** só texto em azul, para ações de pouco peso, como "Ver o SQL".
 *
 *     Os estados são normal, com o mouse em cima, com foco, pressionado,
 *     desativado e carregando. Carregando mostra um indicador girando no
 *     lugar do texto, que fica invisível mas ocupa o mesmo espaço: a largura
 *     não muda e a tela não pula. Botão não troca de visão: isso é papel das
 *     abas e do controle segmentado.
 *
 * EN: Capsule button in three variants, with disabled and loading states.
 *     Loading keeps the label's width so the layout never jumps.
 */

import { elemento } from "../dom.js";
import { icone } from "./icones.js";

/** @typedef {import("./icones.js").NomeDoIcone} NomeDoIcone */

/**
 * @typedef {object} OpcoesDoBotao
 * @property {string} texto
 * @property {"primario" | "secundario" | "sutil"} [variante]
 * @property {NomeDoIcone} [icone] Ícone depois do texto / trailing icon
 * @property {boolean} [desativado]
 * @property {boolean} [carregando]
 * @property {"button" | "submit"} [tipo]
 * @property {(evento: MouseEvent) => void} [aoClicar]
 */

/**
 * PT: Liga ou desliga o estado carregando de um botão. Enquanto carrega, o
 *     botão fica ocupado para leitores de tela e não responde ao clique.
 * EN: Toggles a button's loading state.
 *
 * @param {HTMLButtonElement} botao
 * @param {boolean} carregando
 * @returns {void}
 */
export function definirCarregando(botao, carregando) {
  botao.classList.toggle("botao--carregando", carregando);
  botao.setAttribute("aria-busy", String(carregando));
  botao.setAttribute("aria-disabled", String(carregando || botao.disabled));
}

/**
 * PT: Monta o botão.
 * EN: Builds the button.
 *
 * @param {OpcoesDoBotao} opcoes
 * @returns {HTMLButtonElement}
 */
export function botao({
  texto,
  variante = "primario",
  icone: nomeDoIcone,
  desativado = false,
  carregando = false,
  tipo = "button",
  aoClicar,
}) {
  const conteudo = elemento("span", { classe: "botao__conteudo" }, [
    texto,
    ...(nomeDoIcone ? [icone(nomeDoIcone)] : []),
  ]);
  const giro = elemento("span", { classe: "botao__giro", atributos: { "aria-hidden": "true" } });
  const el = elemento("button", { classe: `botao botao--${variante}`, atributos: { type: tipo } }, [
    conteudo,
    giro,
  ]);
  el.disabled = desativado;
  definirCarregando(el, carregando);
  el.addEventListener("click", (evento) => {
    // PT: carregando, o clique não faz nada / EN: ignore clicks while loading
    if (el.getAttribute("aria-busy") === "true") {
      evento.preventDefault();
      return;
    }
    aoClicar?.(evento);
  });
  return el;
}
